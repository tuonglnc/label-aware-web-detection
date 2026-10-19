import unittest

from src.preprocessing.csic_2010 import find_pair, parse_bytes, screen


class CsicTests(unittest.TestCase):
    def test_get_post_boundaries_lengths_and_original_bytes(self):
        get = b"GET http://localhost/a?q=%27 HTTP/1.1\nHost: localhost\nCookie: a=1\n\n\n"
        post = b"POST http://localhost/a HTTP/1.1\nHost: localhost\nContent-Length: 3\n\nx=1\n\n"
        records = parse_bytes(get + post, "fixture.txt", "NORMAL", "source_train")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["request"]["uri"], "http://localhost/a?q=%27")
        self.assertEqual(records[0]["request"]["body"], "")
        self.assertEqual(records[1]["request"]["body"], "x=1")
        self.assertFalse(records[1]["content_length_issue"])
        self.assertEqual(records[1]["byte_start"], len(get))
        self.assertEqual(records[1]["source_line"], get.count(b"\n") + 1)
        self.assertEqual("".join(r["raw_http"] for r in records).encode(), get + post)

    def test_crlf_and_duplicate_headers_preserved(self):
        data = b"GET http://localhost/ HTTP/1.1\r\nX-Test: a\r\nX-Test: b\r\n\r\n"
        r = parse_bytes(data, "fixture", "NORMAL", "source_train")[0]
        self.assertEqual(r["request"]["headers"], [["X-Test", "a"], ["X-Test", "b"]])
        self.assertEqual(r["raw_http"].encode(), data)

    def test_bad_content_length_is_reported_not_silently_truncated(self):
        data = b"POST http://localhost/ HTTP/1.1\nContent-Length: 99\n\nx=1\n\n"
        r = parse_bytes(data, "fixture", "ANOMALOUS", "source_test_anomalous")[0]
        self.assertTrue(r["content_length_issue"])
        self.assertEqual(r["request"]["body"], "x=1")

    def test_screening_does_not_relabel_anomalous_as_sqli(self):
        data = b"GET http://localhost/?q=UNION+SELECT+x+FROM+y HTTP/1.1\nHost: localhost\n\n"
        r = parse_bytes(data, "fixture", "ANOMALOUS", "source_test_anomalous")[0]
        self.assertTrue(screen(r)["sql_pattern"])
        self.assertEqual(r["label"], "ANOMALOUS")

    def test_pair_has_actual_parameter_change_and_discloses_cookie(self):
        a = b"GET http://localhost/?id=1&item=2 HTTP/1.1\nCookie: a\n\n"
        b = b"GET http://localhost/?id=1+AND+1%3D1&item=2 HTTP/1.1\nCookie: b\n\n"
        normal = parse_bytes(a, "normal", "NORMAL", "source_train")
        attack = parse_bytes(b, "anomalous", "ANOMALOUS", "source_test_anomalous")
        pair = find_pair(normal, attack)
        self.assertEqual(pair["changed_parameter"], "id")
        self.assertLess(pair["payload_similarity"], 1)
        self.assertEqual(pair["header_differences"], [[["Cookie", "a"], ["Cookie", "b"]]])
        self.assertFalse(pair["embedding_similarity_measured"])


if __name__ == "__main__":
    unittest.main()
