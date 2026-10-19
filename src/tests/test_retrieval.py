"""Kiểm thử các khối retrieval: view, index, kNN và chiến lược chọn ví dụ."""

import json
import unittest

import numpy as np

from src.retrieval.index import VectorIndex
from src.retrieval.knn import knn_vote
from src.retrieval.selectors import class_balanced, fixed_examples, label_aware_rerank, semantic_top_k
from src.retrieval.views import embedding_view, endpoint_of, prompt_view
from src.tests.helpers import make_rows, request_text


def cand(rid, label, sim, rank):
    return {"request_id": rid, "label": label, "similarity": sim, "rank": rank}


CANDS = [cand("a", "NORMAL", 0.99, 1), cand("b", "SQL_INJECTION", 0.98, 2), cand("c", "NORMAL", 0.97, 3),
         cand("d", "PATH_TRAVERSAL", 0.90, 4), cand("e", "SQL_INJECTION", 0.85, 5), cand("f", "NORMAL", 0.80, 6)]


class ViewTests(unittest.TestCase):
    def test_embedding_view_puts_uri_before_headers(self):
        view = embedding_view(request_text("/a?id=1+AND+1%3D1"))
        self.assertTrue(view.startswith("GET /a?id=1+AND+1%3D1 HTTP/1.1"))
        self.assertIn("User-Agent: Mozilla/5.0", view)

    def test_prompt_view_keeps_payload_and_truncates_only_when_asked(self):
        text = request_text("/a?q=" + "x" * 300)
        full = json.loads(prompt_view(text))
        self.assertEqual(list(full)[:2], ["method", "uri"])
        self.assertEqual(full["uri"], "/a?q=" + "x" * 300)
        self.assertTrue(prompt_view(text, 50).endswith("…[truncated]"))

    def test_raw_text_fallback_and_endpoint(self):
        self.assertEqual(embedding_view("GET /x HTTP/1.1"), "GET /x HTTP/1.1")
        self.assertEqual(endpoint_of(request_text("/shop/item?id=3")), "GET /shop/item")


class IndexTests(unittest.TestCase):
    def test_search_sorted_by_similarity_with_deterministic_ties(self):
        index = VectorIndex(["z", "y", "x"], ["NORMAL", "SQL_INJECTION", "NORMAL"],
                            np.array([[1, 0], [1, 0], [0, 1]], dtype=np.float32))
        result = index.search(np.array([[1, 0]], dtype=np.float32), 3)[0]
        self.assertEqual([c["request_id"] for c in result], ["y", "z", "x"])  # y, z hòa → id nhỏ trước
        self.assertEqual([c["rank"] for c in result], [1, 2, 3])
        self.assertAlmostEqual(result[0]["similarity"], 1.0)

    def test_rejects_duplicate_ids(self):
        with self.assertRaises(ValueError):
            VectorIndex(["a", "a"], ["NORMAL", "NORMAL"], np.eye(2))


class KnnTests(unittest.TestCase):
    def test_weighted_vote(self):
        label, scores = knn_vote(CANDS, 3)
        self.assertEqual(label, "NORMAL")
        self.assertAlmostEqual(scores["NORMAL"], 1.96)

    def test_tie_goes_to_most_similar_label(self):
        self.assertEqual(knn_vote(CANDS, 2, weighted=False)[0], "NORMAL")
        self.assertEqual(knn_vote([], 3), (None, {}))


class SelectorTests(unittest.TestCase):
    def test_semantic_is_plain_top_k(self):
        self.assertEqual([d["request_id"] for d in semantic_top_k(CANDS, 3)], ["a", "b", "c"])

    def test_class_balanced_round_robin(self):
        picked = [d["request_id"] for d in class_balanced(CANDS, 4)]
        self.assertEqual(picked, ["a", "b", "d", "c"])

    def test_lambda_zero_and_missing_prior_equal_semantic(self):
        b = semantic_top_k(CANDS, 4)
        self.assertEqual(label_aware_rerank(CANDS, 4, "SQL_INJECTION", 0), b)
        self.assertEqual(label_aware_rerank(CANDS, 4, None, 0.5), b)

    def test_prior_matching_candidates_move_up(self):
        picked = label_aware_rerank(CANDS, 3, "SQL_INJECTION", 0.5)
        self.assertEqual([d["request_id"] for d in picked], ["b", "e", "a"])
        self.assertAlmostEqual(picked[0]["score"], 1.48)

    def test_small_lambda_only_reorders_close_candidates(self):
        picked = label_aware_rerank(CANDS, 3, "SQL_INJECTION", 0.05)
        self.assertEqual([d["request_id"] for d in picked], ["b", "a", "c"])

    def test_fixed_examples_balanced_and_reproducible(self):
        labels = ("NORMAL", "SQL_INJECTION", "PATH_TRAVERSAL", "CODE_INJECTION",
                  "HTTP_RESPONSE_SPLITTING", "OS_COMMAND_INJECTION")
        pool = make_rows("pool", 0, 4)
        first = fixed_examples(pool, 6, 42, labels)
        self.assertEqual(first, fixed_examples(pool, 6, 42, labels))
        self.assertEqual(sorted(d["label"] for d in first), sorted(labels))


if __name__ == "__main__":
    unittest.main()
