"""Kiểm thử vòng cải tiến Pipeline C: MMR, CLL-RetICL, Wilson-ENN, prior từ B (IDS), ensemble, tập test mới."""

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from src.analysis.ensemble import ensemble, majority
from src.experiments.build_pool_aux import build as build_aux
from src.experiments.build_retrieval import build
from src.experiments.data_io import load_jsonl
from src.experiments.run_llm import load_experiment, run_experiment
from src.preprocessing.make_fresh_test import fresh_subset
from src.retrieval.pool_aux import PoolSpace, cll_label_terms, enn_flags
from src.retrieval.selectors import drop_flagged, label_term_rerank, mmr_select, semantic_top_k
from src.tests.helpers import HashingEncoder, write_fixture_dataset

MOCK = {"backend": "mock_demo_majority", "model": "mock-demo-majority", "max_request_chars": 32768}


def cand(rid, label, sim, rank):
    return {"request_id": rid, "label": label, "similarity": sim, "rank": rank}


class SelectorTests(unittest.TestCase):
    CANDS = [cand("a", "NORMAL", 0.99, 1), cand("a2", "NORMAL", 0.98, 2), cand("b", "SQL_INJECTION", 0.90, 3),
             cand("c", "PATH_TRAVERSAL", 0.85, 4), cand("d", "NORMAL", 0.80, 5)]

    def pair(self, x, y):
        # a và a2 gần như trùng nhau; các cặp khác ít giống nhau.
        return 0.99 if {x, y} == {"a", "a2"} else 0.2

    def test_mmr_with_lambda_one_equals_semantic(self):
        self.assertEqual([d["request_id"] for d in mmr_select(self.CANDS, 4, self.pair, 1.0)],
                         [d["request_id"] for d in semantic_top_k(self.CANDS, 4)])

    def test_mmr_skips_near_duplicate(self):
        chosen = [d["request_id"] for d in mmr_select(self.CANDS, 3, self.pair, 0.5)]
        self.assertEqual(chosen[0], "a")  # ví dụ đầu tiên luôn là ví dụ giống query nhất
        self.assertNotIn("a2", chosen)    # bản gần trùng của "a" bị phạt

    def test_label_term_rerank(self):
        term = {"a": -0.2, "a2": 0.0, "b": 0.1, "c": 0.0, "d": 0.0}
        self.assertEqual([d["request_id"] for d in label_term_rerank(self.CANDS, 2, term, 0.0)], ["a", "a2"])
        self.assertEqual([d["request_id"] for d in label_term_rerank(self.CANDS, 2, term, 1.0)], ["b", "a2"])

    def test_drop_flagged_keeps_order(self):
        self.assertEqual([c["request_id"] for c in drop_flagged(self.CANDS, {"a2", "c"})], ["a", "b", "d"])


class PoolAuxTests(unittest.TestCase):
    def space(self):
        # Ba điểm NORMAL gần nhau, ba điểm SQLi gần nhau, và một điểm SQLi nằm giữa đám NORMAL (nghi sai nhãn).
        vecs = np.array([[1, 0], [0.99, 0.1], [0.98, 0.15], [0, 1], [0.1, 0.99], [0.15, 0.98], [0.97, 0.12]])
        labels = ["NORMAL"] * 3 + ["SQL_INJECTION"] * 4
        return PoolSpace([f"p{i}" for i in range(7)], labels, vecs)

    def test_enn_flags_mislabelled_point(self):
        self.assertEqual(enn_flags(self.space(), 3), ["p6"])

    def test_cll_term_rewards_points_near_their_label(self):
        label_vectors = {"NORMAL": np.array([1.0, 0.0]), "SQL_INJECTION": np.array([0.0, 1.0])}
        terms = cll_label_terms(self.space(), label_vectors)
        self.assertGreater(terms["p0"], 0)   # NORMAL nằm sát vector "Normal"
        self.assertGreater(terms["p3"], 0)
        self.assertLess(terms["p6"], 0)      # SQLi nằm giữa đám NORMAL bị trừ điểm

    def test_pair_similarity(self):
        space = self.space()
        self.assertAlmostEqual(space.pair_similarity("p0", "p0"), 1.0, places=5)
        self.assertAlmostEqual(space.pair_similarity("p0", "p3"), 0.0, places=5)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.data = self.root / "data"
        write_fixture_dataset(self.data)
        self.retrieval = self.root / "retrieval"
        encoder = HashingEncoder()
        build(encoder, str(self.retrieval), ["development", "validation", "test"], 20, data_dir=self.data)
        build_aux(self.retrieval, encoder)

    def tearDown(self):
        self.tmp.cleanup()

    def experiment(self, **overrides):
        path = self.root / "exp.json"
        base = {"name": "x", "k": 4, "n_candidates": 10, "retrieval_dir": str(self.retrieval)}
        path.write_text(json.dumps({**base, **overrides}))
        return load_experiment(path)

    def test_config_validation(self):
        for bad in ({"pipeline": "C", "prior_source": "knn", "lambda": 0.1, "selector": "mmr", "mmr_lambda": 0.5},
                    {"pipeline": "B", "selector": "mmr"}, {"pipeline": "B", "selector": "mmr", "mmr_lambda": 0},
                    {"pipeline": "B", "selector": "cll"}, {"pipeline": "B", "selector": "other"},
                    {"pipeline": "A0", "pool_filter": "enn"}, {"pipeline": "B", "pool_filter": "other"}):
            with self.assertRaises(ValueError):
                self.experiment(**bad)
        self.assertNotIn("selector", self.experiment(pipeline="B"))

    def run_mock(self, name, **cfg):
        out = self.root / "runs" / name
        run_experiment(self.experiment(name=name, **cfg), MOCK, "validation", out, data_dir=self.data)
        return out, {r["request_id"]: r for r in load_jsonl(out / "predictions.jsonl")}

    def test_new_selectors_run_and_differ_from_b_where_expected(self):
        _, b = self.run_mock("B", pipeline="B")
        out_mmr, mmr = self.run_mock("MMR", pipeline="B", selector="mmr", mmr_lambda=1.0)
        self.assertEqual({q: r["demo_ids"] for q, r in mmr.items()}, {q: r["demo_ids"] for q, r in b.items()})
        self.assertIn("pool_aux_sha256", json.loads((out_mmr / "manifest.json").read_text())["retrieval"])
        _, cll = self.run_mock("CLL", pipeline="B", selector="cll", cll_w1=0.0)
        self.assertEqual({q: r["demo_ids"] for q, r in cll.items()}, {q: r["demo_ids"] for q, r in b.items()})
        _, enn = self.run_mock("ENN", pipeline="B", pool_filter="enn")
        flagged = set(json.loads((self.retrieval / "pool_aux.json").read_text())["enn"]["flagged"])
        for r in enn.values():
            self.assertFalse(flagged & set(r["demo_ids"]))
        self.assertNotIn("pool_aux_sha256", json.loads((self.root / "runs" / "B" / "manifest.json").read_text())["retrieval"])

    def test_prior_from_b_run(self):
        b_out, b = self.run_mock("B", pipeline="B")
        _, it = self.run_mock("IT", pipeline="C", prior_source="llm", prior_run=str(b_out), **{"lambda": 0.1})
        for qid, r in it.items():
            self.assertEqual(r["prior"], b[qid]["predicted_label"])
        bal_out, _ = self.run_mock("BAL", pipeline="BAL")
        with self.assertRaises(ValueError):
            self.run_mock("BAD", pipeline="C", prior_source="llm", prior_run=str(bal_out), **{"lambda": 0.1})

    def test_ensemble_majority_and_tie_break(self):
        self.assertEqual(majority(["A", "B", "B"]), "B")
        self.assertEqual(majority(["A", "B", None]), "A")
        self.assertIsNone(majority([None, None]))
        outs = [self.run_mock(n, pipeline=p)[0] for n, p in (("B", "B"), ("BAL", "BAL"), ("A0", "A0"))]
        result = ensemble("validation", outs, "ENS", self.root / "ens", data_dir=self.data)
        self.assertEqual(result["name"], "ENS")
        metrics = json.loads((self.root / "ens" / "metrics.json").read_text())
        self.assertTrue(metrics["complete"])
        self.assertEqual(metrics["cost"]["llm_calls_per_query"], 3)


class HolmTests(unittest.TestCase):
    def test_holm_adjustment(self):
        from src.analysis.metrics import holm
        # Ví dụ chuẩn: p = (0,01; 0,04; 0,03) -> (0,03; 0,06; 0,06).
        self.assertEqual([round(p, 6) for p in holm([0.01, 0.04, 0.03])], [0.03, 0.06, 0.06])
        self.assertEqual(holm([0.9, 0.8]), [1.0, 1.0])
        self.assertEqual(holm([]), [])


class FreshTestTests(unittest.TestCase):
    def test_fresh_subset_is_balanced_and_disjoint(self):
        labels = ["NORMAL", "SQL_INJECTION"]
        rows = [{"request_id": f"r{i}", "group_id": f"g{i // 2}", "label": labels[i % 2]} for i in range(40)]
        used = rows[:4]
        fresh = fresh_subset(rows, used, per_class=5)
        self.assertEqual(len(fresh), 10)
        used_groups = {r["group_id"] for r in used}
        self.assertFalse(used_groups & {r["group_id"] for r in fresh})
        self.assertEqual(len({r["group_id"] for r in fresh}), len(fresh))  # mỗi nhóm tối đa 1 request
        self.assertEqual(fresh, fresh_subset(rows, used, per_class=5))      # tất định


if __name__ == "__main__":
    unittest.main()
