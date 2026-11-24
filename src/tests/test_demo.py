"""Kiểm thử phần lõi của demo (src/demo/core.py) trên dữ liệu giả, LLM giả, không cần mạng."""

import json
from pathlib import Path
import tempfile
import unittest

from src.common.budget import SpendLedger
from src.demo.core import (DemoEngine, HEADER_NAMES, build_request_text, load_examples, load_retrieval,
                           parse_raw_http, request_fields)
from src.experiments.build_retrieval import build
from src.experiments.run_llm import load_experiment
from src.llm.client import BackendError
from src.retrieval.embedding import encode_requests
from src.retrieval.selectors import label_aware_rerank, semantic_top_k
from src.tests.helpers import HashingEncoder, request_text, write_fixture_dataset

MOCK = {"backend": "mock_demo_majority", "model": "mock-demo-majority", "max_request_chars": 32768}
REAL = {"backend": "chat_completions", "model": "fake-model", "max_tokens": 64, "max_request_chars": 32768}


class FakeClient:
    """Thay ChatClient: đếm số lần gọi, trả về nhãn cố định kèm usage."""

    def __init__(self, label="SQL_INJECTION", error=None):
        self.calls, self.label, self.error = 0, label, error

    def __call__(self, messages):
        self.calls += 1
        if self.error:
            raise BackendError(self.error)
        return {"raw_output": json.dumps({"label": self.label}),
                "usage": {"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110}, "attempts": 1}


class RequestTextTests(unittest.TestCase):
    def test_build_matches_canonical_format(self):
        text = build_request_text("get", "/shop/item?id=1", "host: example.test\nUser-Agent: Mozilla/5.0\nX-Test: 1")
        request = json.loads(text)
        self.assertEqual(request["method"], "GET")
        self.assertEqual(set(HEADER_NAMES) - set(request["headers"]), set())
        self.assertEqual(request["headers"]["Host"], "example.test")
        self.assertEqual(request["headers"]["X-Test"], "1")
        self.assertEqual(request["headers"]["Cookie"], "")
        self.assertEqual(text, json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":")))

    def test_raw_http_and_round_trip(self):
        fields = parse_raw_http("POST /login HTTP/1.1\r\nHost: a.test\r\nContent-Type: x\r\n\r\nuser=a'--")
        self.assertEqual((fields["method"], fields["uri"], fields["body"]), ("POST", "/login", "user=a'--"))
        self.assertEqual(fields["headers"], {"Host": "a.test", "Content-Type": "x"})
        text = build_request_text(**fields)
        self.assertEqual(build_request_text(**request_fields(text)), text)
        with self.assertRaises(ValueError):
            parse_raw_http("garbage")

    def test_bundled_examples_are_validation_requests(self):
        examples = load_examples()
        self.assertGreaterEqual(len(examples), 6)
        for example in examples:
            self.assertEqual(build_request_text(**request_fields(example["request_text"])), example["request_text"])
        self.assertEqual(len({e["label"] for e in examples}), 6)


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.data_dir = root / "data"
        write_fixture_dataset(cls.data_dir)
        cls.retrieval_dir = root / "retrieval"
        cls.encoder = HashingEncoder()
        build(cls.encoder, cls.retrieval_dir, ["development"], 30, data_dir=cls.data_dir)
        configs = root / "configs"
        configs.mkdir()
        for name, extra in (("B", {}), ("C", {"lambda": 0.1, "prior_source": "knn", "prior_knn_k": 5})):
            config = dict({"pipeline": name, "k": 4, "n_candidates": 30, "max_demo_chars": 500,
                           "retrieval_dir": str(cls.retrieval_dir)}, **extra)
            (configs / f"{name}.json").write_text(json.dumps(config), encoding="utf-8")
        cls.b_config, cls.c_config = configs / "B.json", configs / "C.json"
        cls.query = request_text("/download?file=../../etc/passwd999")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def engine(self, llm=MOCK, **kwargs):
        pool, index = load_retrieval(self.encoder, self.retrieval_dir, data_dir=self.data_dir)
        return DemoEngine(self.encoder, pool, index, llm, b_config=self.b_config, c_config=self.c_config, **kwargs)

    def test_selection_reuses_pipeline_selectors(self):
        engine = self.engine()
        result = engine.analyze(self.query, with_a0=True)
        cands = engine.index.search(encode_requests(self.encoder, [{"request_text": self.query}]), 30)[0]
        self.assertEqual(result["neighbors"], cands[:5])
        self.assertAlmostEqual(sum(result["prior_votes"].values()), sum(c["similarity"] for c in cands[:5]), places=4)
        self.assertEqual([d["request_id"] for d in result["B"]["demos"]],
                         [d["request_id"] for d in semantic_top_k(cands, 4)])
        self.assertEqual([d["request_id"] for d in result["C"]["demos"]],
                         [d["request_id"] for d in label_aware_rerank(cands, 4, result["prior"], 0.1)])
        self.assertEqual(result["prior"], "PATH_TRAVERSAL")
        self.assertEqual(result["B"]["status"], "ok")
        self.assertEqual(result["A0"]["label"], "NORMAL")  # mock không có ví dụ → NORMAL
        self.assertEqual(result["A0"]["demos"], [])
        # Prompt dùng đúng build_messages: query nằm nguyên vẹn trong request_to_classify.
        payload = json.loads(result["C"]["messages"][-1]["content"])
        self.assertEqual(len(payload["labeled_examples"]), 4)
        self.assertNotIn("GROUND_TRUTH_CANARY", result["C"]["messages"][-1]["content"])

    def test_locked_configs_load(self):
        from src.demo.core import B_CONFIG, C_CONFIG
        self.assertEqual(load_experiment(B_CONFIG)["k"], 4)
        self.assertEqual((load_experiment(C_CONFIG)["lambda"], load_experiment(C_CONFIG)["prior_source"]), (0.1, "knn"))

    def test_cache_avoids_repeated_calls_and_budget_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.json"
            client = FakeClient()
            engine = self.engine(REAL, client=client, budget=lambda: SpendLedger(ledger_path, 5, 0.15, 0.6))
            first = engine.analyze(self.query)
            calls = client.calls
            self.assertIn(calls, (1, 2))  # B và C có prompt trùng nhau thì chỉ 1 lần gọi
            second = engine.analyze(self.query)
            self.assertEqual(client.calls, calls)
            self.assertTrue(second["B"]["cached"] and second["C"]["cached"])
            self.assertEqual(first["B"]["label"], "SQL_INJECTION")
            self.assertEqual(json.loads(ledger_path.read_text())["calls"], calls)

    def test_budget_stop_and_backend_error_are_not_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = FakeClient()
            engine = self.engine(REAL, client=client,
                                 budget=lambda: SpendLedger(Path(tmp) / "l.json", 1e-9, 0.15, 0.6))
            result = engine.analyze(self.query)
            self.assertEqual(client.calls, 0)
            self.assertEqual(result["B"]["status"], "budget_exhausted")
            self.assertEqual(engine.cache, {})
        failing = FakeClient(error="http_503")
        with tempfile.TemporaryDirectory() as tmp:
            engine = self.engine(REAL, client=failing, budget=lambda: SpendLedger(Path(tmp) / "l.json", 5, 0.15, 0.6))
            self.assertEqual(engine.analyze(self.query)["B"]["status"], "backend_error")
            engine.analyze(self.query)
            self.assertGreaterEqual(failing.calls, 2)

    def test_missing_pool_vectors_are_rebuilt(self):
        _, index = load_retrieval(self.encoder, self.retrieval_dir, data_dir=self.data_dir)
        vectors = self.retrieval_dir / "pool_vectors.npy"
        vectors.unlink()
        _, rebuilt = load_retrieval(self.encoder, self.retrieval_dir, data_dir=self.data_dir)
        self.assertTrue(vectors.exists())
        self.assertEqual(rebuilt.ids, index.ids)
        self.assertTrue((abs(rebuilt.vectors - index.vectors) < 1e-6).all())

    def test_real_mode_requires_budget(self):
        with self.assertRaises(ValueError):
            self.engine(REAL, client=FakeClient())


if __name__ == "__main__":
    unittest.main()
