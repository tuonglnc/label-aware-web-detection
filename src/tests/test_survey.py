"""Evidence accounting/provenance tests, using a clearly synthetic CSV."""

import csv
import json
from pathlib import Path
import tempfile
import unittest

from src.preprocessing.prepare import build_request, digest, file_hashes
from src.preprocessing.survey import survey


class SurveyTests(unittest.TestCase):
    def fixture(self, directory):
        config = json.loads(Path("src/configs/data.json").read_text())
        labels = list(config["labels"]) + ["310 - Scanning for Vulnerable Software"]
        fields = ["request_http_method", "request_http_request", "request_http_protocol", "request_body"] + list(config["headers"]) + labels
        rows = []
        for uri, active in [("/?format=xml", ["000 - Normal"]),
                            ("/?format=xml+AND+1%3D1", ["66 - SQL Injection"]),
                            ("/?q=<script>alert(document.cookie)</script>", ["242 - Code Injection", "310 - Scanning for Vulnerable Software"])]:
            row = {c: "" for c in fields}
            row.update({c: "1" if c in active else "0" for c in labels})
            row.update(request_http_method="GET", request_http_protocol="HTTP/1.1", request_http_request=uri)
            rows.append(row)
        raw = Path(directory) / "synthetic.csv"
        with raw.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        config["source"]["expected_md5"] = file_hashes(raw)["md5"]
        ids = [digest(build_request(row, config)) for row in rows]
        Path(directory, "pool_manifest.json").write_text(json.dumps([{"request_id": rid} for rid in ids[:2]]))
        Path(directory, "development_manifest.json").write_text("[]")
        selection = {"benign": 0, "sqli": 1, "xss": 2, "pair_normal": 0, "pair_attack": 1}
        return raw, config, selection, rows

    def test_counts_multilabel_and_original_payload_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            raw, config, selection, rows = self.fixture(d)
            stats, examples, pair = survey(raw, config, selection, d)
            self.assertEqual(stats["totals"]["records"], 3)
            self.assertEqual(stats["totals"]["attack_records"], 2)
            self.assertEqual(stats["label_cardinality"], {1: 2, 2: 1})
            self.assertEqual(sum(r["samples"] for r in stats["class_distribution"]), 4)
            self.assertEqual(examples["xss"]["row"], rows[2])
            self.assertEqual(examples["xss"]["csv_record"], 4)
            self.assertEqual(pair["different_request_fields"], ["uri"])
            self.assertEqual(pair["uri_changes"][0]["attack"], "+AND+1%3D1")
            self.assertFalse(pair["establishes_retrieval_failure"])
            self.assertFalse(stats["predefined_split_columns"])

    def test_pair_not_in_pool_or_development_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            raw, config, selection, _ = self.fixture(d)
            Path(d, "pool_manifest.json").write_text("[]")
            with self.assertRaisesRegex(AssertionError, "Illustration"):
                survey(raw, config, selection, d)

    def test_cannot_relabel_xss_example_as_sqli(self):
        with tempfile.TemporaryDirectory() as d:
            raw, config, selection, _ = self.fixture(d)
            selection["sqli"] = 2
            with self.assertRaises(AssertionError):
                survey(raw, config, selection, d)


if __name__ == "__main__":
    unittest.main()
