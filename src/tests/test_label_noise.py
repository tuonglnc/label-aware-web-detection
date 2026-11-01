"""Kiểm thử phân tích nhãn nhiễu lớp Normal (quy tắc payload, độ nhạy, nhiễm bẩn ví dụ)."""

import json
import unittest

from src.analysis.label_noise import demo_contamination, noise_summary, sensitivity, suspicious_rules
from src.tests.helpers import request_text


def row(rid, label, uri):
    return {"request_id": rid, "label": label, "request_text": request_text(uri)}


def rec(pred, demos=()):
    return {"predicted_label": pred, "status": "ok", "demo_ids": list(demos)}


class RuleTests(unittest.TestCase):
    def test_encoded_payloads_are_flagged(self):
        cases = {"/blog%22+%2F+sleep%2815%29+%2F+%22/page": "time_delay",
                 "/blog/index.php%3Bcat+%2Fetc%2Fpasswd%3B/feed": "sensitive_file",
                 "/%27%22%3Cscript%3Ealert%281%29%3B%3C%2Fscript%3E/oembed": "script_tag",
                 "/blog/%28%29+%7B+%3A%3B%7D%3B+%2Fbin%2Fsleep+15/x": "shell_command",
                 "/wp-includes/Set-cookie%3A+Tamper%3D1/a.css": "header_injection",
                 "/c%3A%5C/wp-includes/js/jquery.js": "path_traversal",
                 "/item?id=1%2BAND%2B1%3D1": "sql_keywords"}
        for uri, rule in cases.items():
            self.assertIn(rule, suspicious_rules(request_text(uri)), uri)

    def test_ordinary_requests_are_not_flagged(self):
        for uri in ("/blog/index.php/2020/04/04/hic-porro-nihil", "/wp-content/plugins/user-registration/a.css?ver=1.8",
                    "/cgi-bin/status", "/shop/item?id=12&sort=asc", "/blog/wp-comments-post.php"):
            self.assertEqual(suspicious_rules(request_text(uri)), [], uri)

    def test_header_values_scanned_but_not_for_newlines(self):
        text = json.dumps({"body": "", "headers": {"Referer": "http://x/../../etc/passwd", "Accept": "a"},
                           "method": "GET", "protocol": "HTTP/1.1", "uri": "/ok"})
        self.assertEqual(set(suspicious_rules(text)), {"sensitive_file", "path_traversal"})


class SensitivityTests(unittest.TestCase):
    ROWS = [row("n1", "NORMAL", "/a"), row("n2", "NORMAL", "/a;cat+/etc/passwd;"), row("n3", "NORMAL", "/b"),
            row("s1", "SQL_INJECTION", "/x?id=1+UNION+SELECT+1"), row("s2", "SQL_INJECTION", "/x?id=2+OR+1=1")]

    def test_summary_counts_flagged_per_label(self):
        summary = noise_summary(self.ROWS)
        self.assertEqual(summary["by_label"]["NORMAL"], {"n": 3, "flagged": 1, "rate": 1 / 3})
        self.assertEqual(summary["by_label"]["SQL_INJECTION"]["flagged"], 2)
        self.assertIn("sensitive_file", summary["normal_rules"])

    def test_dropping_flagged_normal_removes_its_false_positive(self):
        b = {"n1": rec("NORMAL"), "n2": rec("OS_COMMAND_INJECTION"), "n3": rec("NORMAL"),
             "s1": rec("SQL_INJECTION"), "s2": rec("SQL_INJECTION")}
        c = dict(b, s2=rec("NORMAL"))
        result = sensitivity(self.ROWS, {"B": b, "C": c}, "B", n_resamples=50)
        self.assertEqual((result["n_flagged_normal"], result["n_normal"]), (1, 3))
        by_name = {r["name"]: r for r in result["runs"]}
        self.assertAlmostEqual(by_name["B"]["normal_fpr"], 1 / 3)
        self.assertEqual(by_name["B"]["normal_fpr_kept"], 0.0)
        self.assertEqual(by_name["B"]["n_kept"], 4)
        self.assertEqual((by_name["B"]["normal_false_positives"], by_name["B"]["normal_false_positives_flagged"]), (1, 1))
        self.assertLess(by_name["C"]["kept_vs_reference"]["diff"], 0)
        self.assertNotIn("kept_vs_reference", by_name["B"])

    def test_demo_contamination_splits_attack_queries(self):
        records = {"n1": rec("NORMAL", ["p1"]), "n2": rec("NORMAL"), "n3": rec("NORMAL"),
                   "s1": rec("NORMAL", ["bad"]), "s2": rec("SQL_INJECTION", ["p2"])}
        result = demo_contamination(self.ROWS, records, {"bad"})
        self.assertAlmostEqual(result["queries_with_flagged_normal_demo"], 0.2)
        self.assertEqual(result["with_flagged_demo"], {"attack_queries": 1, "predicted_normal": 1, "miss_rate": 1.0})
        self.assertEqual(result["without_flagged_demo"]["miss_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
