"""Kiểm thử C-gated (C chỉ dùng khi prior kNN đủ tự tin) và tùy chọn --offset của runner."""

import json
from pathlib import Path
import tempfile
import unittest

from src.experiments.analyze_gating import gating_table
from src.experiments.build_retrieval import build
from src.experiments.data_io import load_jsonl, load_split
from src.experiments.run_llm import load_experiment, run_experiment
from src.retrieval.knn import knn_vote, vote_share
from src.retrieval.selectors import gated_label_aware_rerank, label_aware_rerank, semantic_top_k
from src.tests.helpers import HashingEncoder, write_fixture_dataset

MOCK = {"backend": "mock_demo_majority", "model": "mock-demo-majority", "max_request_chars": 32768}
ROOT = Path(__file__).resolve().parents[2]


def cand(rid, label, sim, rank):
    return {"request_id": rid, "label": label, "similarity": sim, "rank": rank}


# 5 hàng xóm gần nhất: 3 NORMAL, 2 SQLi (share của NORMAL ≈ 0,6); ứng viên SQLi ở hạng 5 có thể lên top-4.
MIXED = [cand("a", "NORMAL", 0.99, 1), cand("b", "SQL_INJECTION", 0.98, 2), cand("c", "NORMAL", 0.97, 3),
         cand("d", "SQL_INJECTION", 0.96, 4), cand("e", "NORMAL", 0.95, 5), cand("f", "NORMAL", 0.94, 6)]
UNANIMOUS = [cand(str(i), "NORMAL", 0.99 - i / 100, i + 1) for i in range(5)] + [cand("x", "SQL_INJECTION", 0.9, 6)]


class GatedSelectorTests(unittest.TestCase):
    def test_vote_share(self):
        label, scores = knn_vote(UNANIMOUS, 5)
        self.assertEqual(vote_share(scores, label), 1.0)
        label, scores = knn_vote(MIXED, 5)
        self.assertEqual(label, "NORMAL")
        self.assertAlmostEqual(vote_share(scores, label), (0.99 + 0.97 + 0.95) / (0.99 + 0.98 + 0.97 + 0.96 + 0.95), 6)
        self.assertIsNone(vote_share({}, None))

    def test_low_confidence_falls_back_to_semantic(self):
        b = semantic_top_k(MIXED, 4)
        self.assertEqual(gated_label_aware_rerank(MIXED, 4, "NORMAL", 0.1, 0.6, 0.7), b)
        self.assertEqual(gated_label_aware_rerank(MIXED, 4, "NORMAL", 0.1, None, 0.7), b)

    def test_high_confidence_uses_label_aware_rerank(self):
        c = label_aware_rerank(MIXED, 4, "NORMAL", 0.1)
        self.assertEqual(gated_label_aware_rerank(MIXED, 4, "NORMAL", 0.1, 0.7, 0.7), c)  # bằng ngưỡng: gate vào
        self.assertNotEqual([d["request_id"] for d in c], [d["request_id"] for d in semantic_top_k(MIXED, 4)])

    def test_unanimous_neighbors_change_nothing(self):
        # 5/5 hàng xóm cùng nhãn: top-4 của B đã cùng nhãn prior, nên C-gated chọn y hệt B.
        picked = gated_label_aware_rerank(UNANIMOUS, 4, "NORMAL", 0.1, 1.0, 0.7)
        self.assertEqual([d["request_id"] for d in picked], [d["request_id"] for d in semantic_top_k(UNANIMOUS, 4)])


class GatedRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.data = self.root / "data"
        write_fixture_dataset(self.data)
        self.retrieval = self.root / "retrieval"
        build(HashingEncoder(), str(self.retrieval), ["development", "validation", "test"], 20, data_dir=self.data)

    def tearDown(self):
        self.tmp.cleanup()

    def experiment(self, **overrides):
        path = self.root / "exp.json"
        base = {"name": "x", "k": 4, "n_candidates": 10, "retrieval_dir": str(self.retrieval)}
        path.write_text(json.dumps({**base, **overrides}))
        return load_experiment(path)

    def test_gate_validation(self):
        ok = self.experiment(pipeline="C", prior_source="knn", prior_min_share=0.7, **{"lambda": 0.1})
        self.assertEqual(ok["prior_min_share"], 0.7)
        for bad in ({"pipeline": "C", "prior_source": "llm", "prior_run": "x", "lambda": 0.1, "prior_min_share": 0.7},
                    {"pipeline": "C", "prior_source": "knn", "lambda": 0.1, "prior_min_share": 0},
                    {"pipeline": "C", "prior_source": "knn", "lambda": 0.1, "prior_min_share": 1.5},
                    {"pipeline": "B", "prior_min_share": 0.7}):
            with self.assertRaises(ValueError):
                self.experiment(**bad)
        # Cấu hình C cũ không bị thêm khóa mới (giữ nguyên run_key của các run đã có).
        self.assertNotIn("prior_min_share", self.experiment(pipeline="C", prior_source="knn", **{"lambda": 0.1}))

    def test_gated_run_matches_b_or_c_per_query(self):
        runs = {}
        for name, extra in (("B", {"pipeline": "B"}),
                            ("C", {"pipeline": "C", "prior_source": "knn", "lambda": 0.5}),
                            ("G", {"pipeline": "C", "prior_source": "knn", "lambda": 0.5, "prior_min_share": 0.7})):
            out = self.root / "runs" / name
            run_experiment(self.experiment(name=name, **extra), MOCK, "validation", out, data_dir=self.data)
            runs[name] = {r["request_id"]: r for r in load_jsonl(out / "predictions.jsonl")}
        rate = json.loads((self.root / "runs" / "G" / "metrics.json").read_text())["gated_in_rate"]
        self.assertTrue(0 < rate < 1)  # dữ liệu giả có cả câu gate vào lẫn gate ra
        self.assertNotIn("gated_in", next(iter(runs["C"].values())))
        for qid, g in runs["G"].items():
            self.assertEqual(g["gated_in"], g["prior_confidence"] >= 0.7)
            self.assertEqual(g["demo_ids"], runs["C" if g["gated_in"] else "B"][qid]["demo_ids"])

    def test_offset_selects_second_half_and_is_recorded(self):
        exp = self.experiment(pipeline="B")
        with self.assertRaises(ValueError):
            run_experiment(exp, MOCK, "test", self.root / "locked", offset=6, limit=6, data_dir=self.data)
        out = self.root / "second_half"
        result = run_experiment(exp, MOCK, "test", out, offset=6, limit=6, allow_test=True, data_dir=self.data)
        self.assertEqual(result["selected"], 6)
        expected = [r["request_id"] for r in load_split("test", self.data)[6:12]]
        self.assertEqual([r["request_id"] for r in load_jsonl(out / "predictions.jsonl")], expected)
        self.assertEqual(json.loads((out / "manifest.json").read_text())["offset"], 6)
        self.assertEqual(json.loads((out / "metrics.json").read_text())["offset"], 6)
        # offset khác trên cùng thư mục bị chặn; không có offset thì manifest không có khóa này.
        with self.assertRaises(ValueError):
            run_experiment(exp, MOCK, "test", out, offset=0, limit=6, allow_test=True, data_dir=self.data)
        first = self.root / "first_half"
        run_experiment(exp, MOCK, "test", first, limit=6, allow_test=True, data_dir=self.data)
        self.assertNotIn("offset", json.loads((first / "manifest.json").read_text()))
        with self.assertRaises(ValueError):
            run_experiment(exp, MOCK, "test", self.root / "empty", offset=12, allow_test=True, data_dir=self.data)

    def test_gating_table_endpoints_equal_c_and_b(self):
        queries = load_split("validation", self.data)
        neighbors = {r["request_id"]: r["candidates"] for r in load_jsonl(self.retrieval / "neighbors_validation.jsonl")}
        preds = {q["request_id"]: q["label"] for q in queries}
        result = gating_table(queries, neighbors, {"B": preds, "C": preds}, n_resamples=20)
        rows = {r["threshold"]: r for r in result["rows"]}
        self.assertEqual(rows[0.0]["coverage"], 1.0)
        self.assertEqual(rows[1.01]["coverage"], 0.0)
        self.assertEqual(rows[1.01]["n_changed"], 0)
        self.assertEqual(rows[1.0]["n_changed"], 0)  # 5/5 cùng nhãn thì C không đổi gì
        self.assertEqual(rows[0.5]["counterfactual"]["diff_vs_B"], 0.0)


class GatedConfigTests(unittest.TestCase):
    def test_locked_config_differs_from_c_knn_only_by_gate(self):
        gated = json.loads((ROOT / "src/configs/experiments/C_gated_k4.json").read_text(encoding="utf-8"))
        c_knn = json.loads((ROOT / "src/configs/experiments/C_knn_k4.json").read_text(encoding="utf-8"))
        diff = {k for k in set(gated) | set(c_knn) if gated.get(k) != c_knn.get(k)}
        self.assertEqual(diff, {"name", "prior_min_share"})
        self.assertEqual(load_experiment(ROOT / "src/configs/experiments/C_gated_k4.json")["prior_min_share"], 0.7)


if __name__ == "__main__":
    unittest.main()
