import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest

from src.preprocessing.prepare import (
    audit_splits, balanced_subset, build_request, group_key, prepare,
)
from src.preprocessing.verify import verify


ROOT = Path(__file__).resolve().parents[2]


class DataTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "src/configs/data.json").read_text())
        self.config["source"] = {"description": "synthetic test fixture; not benchmark data"}
        self.config["min_groups_per_class"] = 1
        self.config["development_per_class"] = 1
        self.config["subset_sizes"] = {"pool": 12, "validation": 6, "test": 6}
        self.columns = (list(self.config["headers"]) + ["request_http_method", "request_http_request",
                        "request_http_protocol", "request_body", "response_http_status_code", "timestamp"]
                        + list(self.config["labels"]) + ["310 - Scanning for Vulnerable Software"])

    def row(self, label="000 - Normal", uri="/example", body=""):
        row = {c: "" for c in self.columns}
        row.update({c: "0" for c in self.columns if " - " in c})
        row.update(request_http_method="GET", request_http_request=uri,
                   request_http_protocol="HTTP/1.1", request_body=body,
                   response_http_status_code="200", timestamp="ignored")
        if label:
            row[label] = "1"
        return row

    def run_fixture(self, directory, rows, config=None, columns=None, name="run"):
        path = Path(directory) / f"{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns or self.columns)
            writer.writeheader()
            writer.writerows(rows)
        return prepare(path, config or self.config, Path(directory) / name, Path(directory) / f"{name}_audit")

    def test_request_preserves_encoding_unicode_boundaries_and_empty(self):
        row = self.row(uri="/?q=%27%20OR%201%3D1", body="Tiếng Việt\nHeader: injected")
        text = build_request(row, self.config)
        request = json.loads(text)
        self.assertEqual(request["uri"], row["request_http_request"])
        self.assertEqual(request["body"], row["request_body"])
        self.assertEqual(request["headers"]["Cookie"], "")
        self.assertNotIn("nan", text)
        row["response_http_status_code"] = "canary_response"
        row["timestamp"] = "canary_timestamp"
        row["000 - Normal"] = "canary_label"
        self.assertEqual(build_request(row, self.config), text)

    def test_grouping_numeric_variants_without_changing_model_input(self):
        a, b = self.row(uri="/item/123?q=45"), self.row(uri="/item/456?q=67")
        self.assertNotEqual(build_request(a, self.config), build_request(b, self.config))
        self.assertEqual(group_key(build_request(a, self.config)), group_key(build_request(b, self.config)))
        a, b = self.row(uri="/?q=%27"), self.row(uri="/?q=%28")
        self.assertNotEqual(group_key(build_request(a, self.config)), group_key(build_request(b, self.config)))
        a, b = self.row(body="union select"), self.row(body="normal body")
        self.assertNotEqual(group_key(build_request(a, self.config)), group_key(build_request(b, self.config)))

    def test_full_taxonomy_filter_conflicts_duplicates_and_missing(self):
        rows = [self.row(uri="/duplicate"), self.row(uri="/duplicate"),
                self.row(uri="/conflict"), self.row("66 - SQL Injection", uri="/conflict"),
                self.row(uri="/multiconflict"), self.row(uri="/multiconflict"),
                self.row(uri="/multi"), self.row(None, uri="/zero"),
                self.row("310 - Scanning for Vulnerable Software", uri="/other"),
                self.row(uri=""), self.row(uri="/bad-label")]
        rows[5]["310 - Scanning for Vulnerable Software"] = "1"
        rows[6]["310 - Scanning for Vulnerable Software"] = "1"
        rows[10]["000 - Normal"] = "2"
        with tempfile.TemporaryDirectory() as d:
            summary = self.run_fixture(d, rows)
            c = summary["counts"]
            self.assertEqual(c["total_rows"], 11)
            self.assertEqual(c["duplicate_rows_removed"], 1)
            self.assertEqual(c["retained_unique_requests"], 1)
            self.assertEqual(c["conflict_unique_requests"], 2)
            self.assertEqual(c["conflict_rows"], 4)
            self.assertEqual(c["multi_label"], 2)
            self.assertEqual(c["zero_label"], 1)
            self.assertEqual(c["out_of_scope"], 1)
            self.assertEqual(c["missing_essential"], 1)
            self.assertEqual(c["invalid_label"], 1)
            self.assertEqual(len(summary["label_columns"]), 7)

    def test_missing_schema_fails_and_checksum_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as d:
            columns = [c for c in self.columns if c != "request_body"]
            row = self.row()
            del row["request_body"]
            with self.assertRaisesRegex(ValueError, "Missing columns"):
                self.run_fixture(d, [row], columns=columns)
            config = copy.deepcopy(self.config)
            config["source"]["expected_md5"] = "incorrect"
            with self.assertRaisesRegex(ValueError, "MD5 mismatch"):
                self.run_fixture(d, [self.row()], config=config, name="checksum")

    def test_oversize_is_excluded_without_truncation(self):
        config = copy.deepcopy(self.config)
        config["max_request_chars"] = len(build_request(self.row(), config)) + 10
        with tempfile.TemporaryDirectory() as d:
            summary = self.run_fixture(d, [self.row(), self.row(uri="/long", body="x" * 1000)], config=config)
            self.assertEqual(summary["counts"]["oversize_unique_requests"], 1)
            self.assertEqual(summary["counts"]["retained_unique_requests"], 1)

    def test_group_disjoint_reproducible_splits_and_review_not_test(self):
        # Alphabetic variation yields distinct groups; numeric variants stay together.
        rows = []
        for label in self.config["labels"]:
            for i in range(30):
                word = chr(97 + i // 26) + chr(97 + i % 26)
                for variant in (123, 456):
                    rows.append(self.row(label, uri=f"/{self.config['labels'][label]}/{word}/{variant}"))
        with tempfile.TemporaryDirectory() as d:
            a = self.run_fixture(d, rows, name="first")
            b = self.run_fixture(d, rows, name="second")
            for name in ("pool", "development", "validation", "test"):
                self.assertEqual((Path(d) / "first" / f"{name}.jsonl").read_bytes(),
                                 (Path(d) / "second" / f"{name}.jsonl").read_bytes())
                self.assertEqual(len(a["class_distribution"][name]), 6)
            self.assertEqual(a["split_sizes"], b["split_sizes"])
            audit = json.loads((Path(d) / "first_audit/leakage_audit.json").read_text())
            self.assertTrue(audit["passed"])
            reviews = [json.loads(x) for x in (Path(d) / "first_audit/manual_review.jsonl").read_text().splitlines()]
            test_ids = {json.loads(x)["request_id"] for x in (Path(d) / "first/test.jsonl").read_text().splitlines()}
            self.assertFalse(test_ids & {r["request_id"] for r in reviews})
            self.assertFalse(a["ready_for_task_2"])
            self.assertTrue(verify(Path(d) / "first")["passed"])
            subset_path = Path(d) / "second/pool_subset.jsonl"
            subset_path.write_text(subset_path.read_text() + "\n")
            with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
                verify(Path(d) / "second")
            with self.assertRaisesRegex(ValueError, "Output must be empty"):
                self.run_fixture(d, rows, name="first")

    def test_audit_detects_shared_groups_even_with_distinct_ids(self):
        a = {"request_id": "a", "exact_hash": "a", "group_id": "same", "endpoint_hash": "p"}
        b = {"request_id": "b", "exact_hash": "b", "group_id": "same", "endpoint_hash": "p"}
        audit = audit_splits({"pool": [a], "validation": [b]})
        self.assertFalse(audit["passed"])
        self.assertEqual(audit["overlaps"]["pool/validation"]["group_id"], 1)

    def test_balanced_sampling_shortfall_is_explicit(self):
        rows = [{"request_id": str(i), "label": "A" if i < 4 else "B"} for i in range(6)]
        sample = balanced_subset(rows, 4, 42)
        self.assertEqual(sum(r["label"] == "A" for r in sample), 2)
        self.assertEqual(len(balanced_subset(rows, 100, 42)), 6)


if __name__ == "__main__":
    unittest.main()
