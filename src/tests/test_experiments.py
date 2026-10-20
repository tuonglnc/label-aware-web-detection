"""Kiểm thử end-to-end trên dữ liệu giả: dựng retrieval → đánh giá kNN →
chạy A0/A1/B/BAL/C bằng LLM giả → so sánh. Không cần mạng hay API key."""

import json
from pathlib import Path
import tempfile
import unittest

from src.analysis.compare import compare
from src.analysis.metrics import classification_metrics, mcnemar, paired_bootstrap
from src.experiments.build_retrieval import build
from src.experiments.eval_retrieval import evaluate_retrieval
from src.experiments.data_io import load_jsonl, load_split
from src.experiments.prompting import build_messages, parse_label
from src.experiments.run_llm import load_experiment, run_experiment
from src.tests.helpers import HashingEncoder, write_fixture_dataset

MOCK = {"backend": "mock_demo_majority", "model": "mock-demo-majority", "max_request_chars": 32768}


class MetricsTests(unittest.TestCase):
    LABELS = ("NORMAL", "SQL_INJECTION")

    def test_errors_count_as_wrong_and_macro_f1(self):
        m = classification_metrics(["NORMAL", "NORMAL", "SQL_INJECTION", "SQL_INJECTION"],
                                   ["NORMAL", "SQL_INJECTION", "SQL_INJECTION", None], self.LABELS)
        self.assertAlmostEqual(m["accuracy"], 0.5)
        self.assertAlmostEqual(m["coverage"], 0.75)
        self.assertAlmostEqual(m["per_class"]["NORMAL"]["f1"], 2 / 3)
        self.assertAlmostEqual(m["per_class"]["SQL_INJECTION"]["f1"], 0.5)
        self.assertAlmostEqual(m["normal_false_positive_rate"], 0.5)
        self.assertEqual(m["confusion_matrix"]["counts"][1], [0, 1, 1])

    def test_mcnemar_and_bootstrap(self):
        y = ["NORMAL"] * 10 + ["SQL_INJECTION"] * 10
        a = list(y)
        b = ["NORMAL"] * 20
        self.assertEqual(mcnemar(y, a, b)["a_only_correct"], 10)
        self.assertLess(mcnemar(y, a, b)["p_value"], 0.01)
        boot = paired_bootstrap(y, a, b, self.LABELS, n_resamples=200)
        self.assertGreater(boot["ci95"][0], 0)
        self.assertEqual(paired_bootstrap(y, a, a, self.LABELS, n_resamples=50)["ci95"], [0.0, 0.0])


class PromptTests(unittest.TestCase):
    def test_prompt_contains_examples_before_query_and_best_last(self):
        demos = [{"request_text": "GET /best", "label": "SQL_INJECTION"},
                 {"request_text": "GET /second", "label": "NORMAL"}]
        payload = json.loads(build_messages("GET /q", demos, 100)[-1]["content"])
        self.assertEqual([e["request"] for e in payload["labeled_examples"]], ["GET /second", "GET /best"])
        self.assertEqual(payload["request_to_classify"], "GET /q")
        self.assertNotIn("labeled_examples", json.loads(build_messages("GET /q", [], 100)[-1]["content"]))

    def test_parser_accepts_fenced_json_only(self):
        self.assertEqual(parse_label('```json\n{"label":"NORMAL"}\n```'), "NORMAL")
        for bad in ('{"label":"XSS"}', "NORMAL", '{"label":"NORMAL","why":1}'):
            with self.assertRaises(ValueError):
                parse_label(bad)


class EndToEndTests(unittest.TestCase):
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

    def run_pipeline(self, name, split="validation", **overrides):
        out = self.root / "runs" / split / name
        exp = self.experiment(name=name, **overrides)
        return out, run_experiment(exp, MOCK, split, out, data_dir=self.data)

    def test_add_split_reuses_pool_and_keeps_existing_neighbors(self):
        from src.experiments.build_retrieval import add_split
        out = self.root / "retrieval_dev_val"
        build(HashingEncoder(), str(out), ["development", "validation"], 20, data_dir=self.data)
        before = (out / "neighbors_validation.jsonl").read_bytes()
        manifest = add_split(HashingEncoder(), out, "test", data_dir=self.data)
        self.assertEqual(manifest["query_sizes"]["test"], 12)
        self.assertEqual((out / "neighbors_validation.jsonl").read_bytes(), before)
        self.assertEqual(load_jsonl(out / "neighbors_test.jsonl")[0]["candidates"][0].keys(),
                         {"request_id", "label", "similarity", "rank"})
        with self.assertRaises(ValueError):
            add_split(HashingEncoder(), out, "test", data_dir=self.data)  # không ghi đè

    def test_neighbors_never_contain_query_labels_and_come_from_pool(self):
        pool_ids = {r["request_id"] for r in load_split("pool", self.data)}
        rows = load_jsonl(self.retrieval / "neighbors_validation.jsonl")
        self.assertEqual(set(rows[0]), {"request_id", "candidates"})
        self.assertTrue(all(c["request_id"] in pool_ids for r in rows for c in r["candidates"]))

    def test_retrieval_evaluation_reports_rq1_and_knn(self):
        neighbors = {r["request_id"]: r["candidates"] for r in load_jsonl(self.retrieval / "neighbors_validation.jsonl")}
        result = evaluate_retrieval(load_split("validation", self.data), neighbors, k=4, n_candidates=10)
        self.assertEqual(result["n_queries"], 18)
        self.assertIn("k=5", result["knn_vote"])
        sweep = result["lambda_sweep_knn_prior"]
        self.assertEqual(sweep["0.0"]["lcr_mean"], result["lcr_at_k"]["B_semantic"]["mean"])  # λ = 0 là B
        from src.experiments.eval_retrieval import plot
        plot(result, self.root)
        self.assertTrue((self.root / "retrieval_overview.png").exists())
        self.assertGreaterEqual(result["lcr_at_k"]["C_oracle_prior (analysis only)"]["mean"],
                                result["lcr_at_k"]["B_semantic"]["mean"])

    def test_all_pipelines_run_resume_and_compare(self):
        out_a0, first = self.run_pipeline("A0", pipeline="A0")
        self.assertEqual(first["processed_now"], 18)
        self.assertEqual(self.run_pipeline("A0", pipeline="A0")[1]["processed_now"], 0)  # resume
        out_b, _ = self.run_pipeline("B", pipeline="B")
        self.run_pipeline("A1", pipeline="A1")
        self.run_pipeline("BAL", pipeline="BAL")
        out_c, _ = self.run_pipeline("C_llm", pipeline="C", prior_source="llm", **{"lambda": 0.5},
                                     prior_run=str(self.root / "runs" / "{split}" / "A0"))
        self.run_pipeline("C_knn", pipeline="C", prior_source="knn", **{"lambda": 0.5})
        out_oracle, _ = self.run_pipeline("C_oracle", pipeline="C", prior_source="oracle", **{"lambda": 0.5})

        c_records = load_jsonl(out_c / "predictions.jsonl")
        self.assertTrue(all(r["prior"] == "NORMAL" for r in c_records))  # mock A0 luôn đoán NORMAL
        self.assertEqual(json.loads((out_c / "metrics.json").read_text())["cost"]["llm_calls_per_query"], 2)
        self.assertIn("oracle_analysis", json.loads((out_oracle / "manifest.json").read_text())["experiment_kind"])
        a0 = load_jsonl(out_a0 / "predictions.jsonl")[0]
        self.assertEqual(a0["demo_ids"], [])

        result = compare("validation", sorted(str(p) for p in (self.root / "runs" / "validation").iterdir()),
                         "B", self.root / "report", n_resamples=50, data_dir=self.data)
        names = {r["name"] for r in result["runs"]}
        self.assertEqual(names, {"A0", "A1", "B", "BAL", "C_llm", "C_knn", "C_oracle"})
        c_llm = next(r for r in result["runs"] if r["name"] == "C_llm")
        self.assertEqual(sum(v["n"] for v in c_llm["prior_breakdown_vs_reference"].values()), 18)
        self.assertTrue((self.root / "report" / "confusion_B.png").exists())
        self.assertIn("Prior đúng/sai", (self.root / "report" / "comparison.md").read_text(encoding="utf-8"))

    def test_query_labels_and_metadata_never_reach_the_prompt(self):
        seen = []

        def spy(messages):
            seen.append(messages[-1]["content"])
            return {"raw_output": '{"label":"NORMAL"}', "usage": {"total_tokens": 10}, "attempts": 1}

        exp = self.experiment(pipeline="B")
        run_experiment(exp, MOCK, "validation", self.root / "spy", client=spy, data_dir=self.data)
        queries = {r["request_id"] for r in load_split("validation", self.data)}
        for content in seen:
            self.assertNotIn("GROUND_TRUTH_CANARY", content)
            self.assertNotIn("private_metadata", content)
        records = load_jsonl(self.root / "spy" / "predictions.jsonl")
        self.assertFalse(any(d in queries for r in records for d in r["demo_ids"]))

    def test_test_split_is_locked_and_config_changes_need_new_directory(self):
        with self.assertRaises(ValueError):
            run_experiment(self.experiment(pipeline="A0"), MOCK, "test", self.root / "t", data_dir=self.data)
        out = self.root / "changed"
        run_experiment(self.experiment(pipeline="B"), MOCK, "development", out, data_dir=self.data)
        with self.assertRaises(ValueError):
            run_experiment(self.experiment(pipeline="B", k=3), MOCK, "development", out, data_dir=self.data)

    def test_backend_errors_are_recorded_not_dropped(self):
        def broken(messages):
            from src.pipeline_a0.core import BackendError
            raise BackendError("http_429", attempts=3)

        exp = self.experiment(pipeline="A0")
        result = run_experiment(exp, MOCK, "development", self.root / "err", client=broken, data_dir=self.data)
        self.assertEqual(result["status_counts"], {"backend_error": 6})
        self.assertEqual(result["coverage"], 0.0)
        # Chạy lại không có cờ: giữ nguyên lỗi. Có --retry-errors: gọi lại và ghi đè bằng kết quả mới.
        self.assertEqual(run_experiment(exp, MOCK, "development", self.root / "err", client=broken,
                                        data_dir=self.data)["processed_now"], 0)
        fixed = run_experiment(exp, MOCK, "development", self.root / "err", data_dir=self.data, retry_errors=True)
        self.assertEqual(fixed["processed_now"], 6)
        self.assertEqual(fixed["status_counts"], {"ok": 6})

    def test_daily_quota_stops_cleanly_and_resumes(self):
        from src.pipeline_a0.core import QUOTA_EXHAUSTED, BackendError
        calls = []

        def quota_after_two(messages):
            calls.append(1)
            if len(calls) > 2:
                raise BackendError(QUOTA_EXHAUSTED)
            return {"raw_output": '{"label":"NORMAL"}', "usage": None, "attempts": 1}

        exp = self.experiment(pipeline="A0")
        out = self.root / "quota"
        first = run_experiment(exp, MOCK, "development", out, client=quota_after_two, data_dir=self.data)
        self.assertEqual(first["processed_now"], 2)
        self.assertIn("quota_exhausted", first["stopped"])
        self.assertFalse(json.loads((out / "metrics.json").read_text())["complete"])
        self.assertEqual(len(load_jsonl(out / "predictions.jsonl")), 2)  # no error lines written
        second = run_experiment(exp, MOCK, "development", out, data_dir=self.data)
        self.assertEqual((second["resumed"], second["processed_now"]), (2, 4))
        self.assertTrue(json.loads((out / "metrics.json").read_text())["complete"])

    def test_code_version_change_skips_finished_and_resumes_partial_runs(self):
        exp = self.experiment(pipeline="B")
        out = self.root / "codever"
        run_experiment(exp, MOCK, "development", out, data_dir=self.data)

        def set_code_version(value):
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            manifest["code_sha256"]["src/experiments/run_llm.py"] = value
            (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        set_code_version("older-version")
        self.assertIn("skipped", run_experiment(exp, MOCK, "development", out, data_dir=self.data))
        # Run còn dở và chỉ khác phiên bản code: được chạy tiếp, phiên bản cũ được ghi lại.
        lines = (out / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
        (out / "predictions.jsonl").write_text("\n".join(lines[:2]) + "\n", encoding="utf-8")
        metrics = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
        metrics["complete"] = False
        (out / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
        set_code_version("older-version-2")
        result = run_experiment(exp, MOCK, "development", out, data_dir=self.data)
        self.assertEqual((result["resumed"], result["processed_now"]), (2, 4))
        history = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["code_sha256_history"]
        self.assertEqual(history[-1]["src/experiments/run_llm.py"], "older-version-2")
        # Cấu hình đổi thì vẫn bị chặn.
        with self.assertRaises(ValueError):
            run_experiment(self.experiment(pipeline="B", k=3), MOCK, "development", out, data_dir=self.data)

    def test_budget_stops_before_exceeding_limit(self):
        from src.common.budget import SpendLedger
        calls = []

        def paid(messages):
            calls.append(1)
            return {"raw_output": '{"label":"NORMAL"}', "attempts": 1,
                    "usage": {"prompt_tokens": 1000, "completion_tokens": 100, "total_tokens": 1100}}

        real_llm = {"backend": "chat_completions", "model": "x", "max_tokens": 100, "max_request_chars": 32768}
        # Mỗi call thật tốn ~0,0011 USD (giá 1 USD / 1 triệu token); ngưỡng 0,004 USD chỉ đủ vài call.
        ledger = SpendLedger(self.root / "ledger.json", 0.004, 1.0, 1.0)
        exp = self.experiment(pipeline="A0")
        result = run_experiment(exp, real_llm, "development", self.root / "budget", client=paid,
                                data_dir=self.data, budget=ledger)
        self.assertIn("budget_exhausted", result["stopped"])
        self.assertLessEqual(ledger.spent_usd, 0.004)
        self.assertEqual(len(calls), result["processed_now"])
        # Sổ được lưu và đọc lại đúng, cộng dồn qua các lần chạy.
        again = SpendLedger(self.root / "ledger.json", 0.004, 1.0, 1.0)
        self.assertAlmostEqual(again.spent_usd, ledger.spent_usd)

    def test_llm_config_model_wins_over_env(self):
        import os
        from unittest.mock import patch
        from src.experiments.run_llm import load_llm
        root = Path(__file__).resolve().parents[2]
        with patch.dict(os.environ, {"A0_MODEL": "openai/gpt-oss-20b", "A0_BASE_URL": "https://other.example/v1"}):
            cfg = load_llm(root / "src/configs/llm/groq_120b.json")
            self.assertEqual(cfg["model"], "openai/gpt-oss-120b")
            self.assertEqual(cfg["base_url"], "https://api.groq.com/openai/v1")
            self.assertEqual(load_llm(root / "src/configs/llm/groq.json")["model"], "openai/gpt-oss-20b")

    def test_120b_experiment_configs_match_20b_except_name_and_prior_run(self):
        root = Path(__file__).resolve().parents[2]
        for f in (root / "src/configs/experiments_120b").glob("*.json"):
            a = json.loads((root / "src/configs/experiments" / f.name).read_text(encoding="utf-8"))
            b = json.loads(f.read_text(encoding="utf-8"))
            diff = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
            self.assertTrue(diff <= {"name", "prior_run"}, (f.name, diff))
            if "prior_run" in diff:
                self.assertIn("runs_120b", b["prior_run"])

    def test_invalid_configs_rejected(self):
        for bad in ({"pipeline": "Z"}, {"pipeline": "C", "prior_source": "truth", "lambda": 1},
                    {"pipeline": "C", "prior_source": "llm", "lambda": 1}, {"pipeline": "B", "k": 40}):
            with self.assertRaises(ValueError):
                self.experiment(**bad)


if __name__ == "__main__":
    unittest.main()
