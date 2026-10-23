"""Kiểm thử client LLM (src/llm/client.py): parser, gọi API, thử lại, chờ rate limit, cấu hình."""

import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error

from src.llm import client as core

PROMPT = [{"role": "system", "content": core.SYSTEM},
          {"role": "user", "content": json.dumps({"request_to_classify": "GET /"})}]
API_CONFIG = {"backend": "chat_completions", "model": "test-model", "base_url": "https://provider.example/v1",
              "timeout_seconds": 30, "max_retries": 2, "max_request_chars": 32768, "temperature": 0,
              "max_tokens": 128}
NO_ENV = {k: v for k, v in os.environ.items() if k not in ("A0_MODEL", "A0_BASE_URL")}


def response(payload):
    resp = Mock()
    resp.__enter__ = Mock(return_value=resp)
    resp.__exit__ = Mock(return_value=False)
    resp.read.return_value = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    return resp


class LLMClientTests(unittest.TestCase):
    def test_system_prompt_warns_about_untrusted_request(self):
        self.assertIn("untrusted data", core.SYSTEM)
        for label in core.LABELS:
            self.assertIn(label, core.SYSTEM)

    def test_parser_strict_taxonomy_and_shape(self):
        for label in core.LABELS:
            self.assertEqual(core.parse_output(json.dumps({"label": label})), label)
        for raw in (None, "", "NORMAL", "[]", "null", '{"label":null}', '{"label":[]}',
                    '{"label":"XSS"}', '{"label":"normal"}', '{"label":"NORMAL","explain":"x"}',
                    '{"label":"NORMAL","label":"NORMAL"}', '```json\n{"label":"NORMAL"}\n```'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                core.parse_output(raw)

    def test_recover_predictions_drops_partial_tail_but_rejects_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.jsonl"
            path.write_bytes(b'{"request_id":"a"}\n{"request_id":"par')
            self.assertEqual(core.recover_predictions(path), [{"request_id": "a"}])
            self.assertEqual(path.read_bytes(), b'{"request_id":"a"}\n')
            path.write_bytes(b"broken\n")
            with self.assertRaises(ValueError):
                core.recover_predictions(path)

    def test_http_payload_timeout_retry_and_usage(self):
        opener = Mock()
        success = response({"choices": [{"message": {"content": '{"label":"NORMAL"}'}}],
                            "usage": {"prompt_tokens": 10, "completion_tokens": 5,
                                      "total_tokens": 15, "secret_extra": "do not persist"}})
        opener.open.side_effect = [urllib.error.HTTPError("safe", 429, "rate limit", {}, io.BytesIO()), success]
        with patch.dict("os.environ", {"A0_API_KEY": "synthetic-key-not-real"}), \
                patch("urllib.request.build_opener", return_value=opener), patch("time.sleep") as sleep:
            result = core.ChatClient(API_CONFIG)(PROMPT)
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["usage"]["total_tokens"], 15)
        self.assertNotIn("secret_extra", result["usage"])
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://provider.example/v1/chat/completions")
        self.assertEqual(request.get_header("User-agent"), core.USER_AGENT)  # tránh lỗi 403 của Cloudflare
        body = json.loads(request.data)
        self.assertEqual((body["model"], body["messages"]), ("test-model", PROMPT))
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 30)
        self.assertEqual(sleep.call_count, 1)

    def test_rate_limit_waits_follow_retry_after_without_using_retries(self):
        opener = Mock()
        limited = lambda: urllib.error.HTTPError("safe", 429, "rate limit", {"retry-after": "7"}, io.BytesIO())
        opener.open.side_effect = [limited(), limited(),
                                   response({"choices": [{"message": {"content": '{"label":"NORMAL"}'}}]})]
        config = dict(API_CONFIG, max_retries=0, max_rate_limit_waits=5, reasoning_effort="low")
        with patch.dict("os.environ", {"A0_API_KEY": "synthetic-key-not-real"}), \
                patch("urllib.request.build_opener", return_value=opener), patch("time.sleep") as sleep:
            result = core.ChatClient(config)(PROMPT)
        self.assertEqual(result["attempts"], 3)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [7.0, 7.0])
        self.assertEqual(json.loads(opener.open.call_args.args[0].data)["reasoning_effort"], "low")

    def test_long_retry_after_means_quota_exhausted(self):
        opener = Mock()
        opener.open.side_effect = urllib.error.HTTPError("safe", 429, "quota", {"retry-after": "3600"}, io.BytesIO())
        config = dict(API_CONFIG, max_rate_limit_waits=5)
        with patch.dict("os.environ", {"A0_API_KEY": "synthetic-key-not-real"}), \
                patch("urllib.request.build_opener", return_value=opener), patch("time.sleep") as sleep, \
                self.assertRaises(core.BackendError) as caught:
            core.ChatClient(config)(PROMPT)
        self.assertEqual(str(caught.exception), core.QUOTA_EXHAUSTED)
        sleep.assert_not_called()

    def test_transport_retry_bound_and_nonretryable_http(self):
        for error, count, code in ((TimeoutError(), 3, "transport_error"),
                                   (urllib.error.HTTPError("safe", 401, "unauthorized", {}, None), 1, "http_401")):
            opener = Mock()
            opener.open.side_effect = error
            with patch.dict("os.environ", {"A0_API_KEY": "synthetic-key-not-real"}), \
                    patch("urllib.request.build_opener", return_value=opener), patch("time.sleep"), \
                    self.assertRaises(core.BackendError) as caught:
                core.ChatClient(API_CONFIG)(PROMPT)
            self.assertEqual(str(caught.exception), code)
            self.assertEqual(caught.exception.attempts, count)
            self.assertEqual(opener.open.call_count, count)

    def test_malformed_provider_envelope_is_error_without_retry(self):
        opener = Mock()
        opener.open.return_value = response(b'{"choices":[]}')
        with patch.dict("os.environ", {"A0_API_KEY": "synthetic-key-not-real"}), \
                patch("urllib.request.build_opener", return_value=opener), \
                self.assertRaises(core.BackendError) as caught:
            core.ChatClient(API_CONFIG)(PROMPT)
        self.assertEqual(str(caught.exception), "malformed_backend_response")
        self.assertEqual(opener.open.call_count, 1)

    def test_missing_api_key_is_rejected(self):
        with patch.dict("os.environ", {k: v for k, v in os.environ.items() if k != "A0_API_KEY"}, clear=True):
            with self.assertRaises(ValueError):
                core.ChatClient(API_CONFIG)

    def test_config_validation_and_no_credentials_in_config(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", NO_ENV, clear=True):
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps(API_CONFIG))
            self.assertEqual(core.load_config(path)["model"], "test-model")
            for field, value in (("max_retries", 100), ("max_tokens", 1.2), ("timeout_seconds", float("nan")),
                                 ("temperature", 4), ("api_key", "never-store-secrets"),
                                 ("reasoning_effort", "extreme"), ("base_url", "https://user:pass@x.example/v1")):
                path.write_text(json.dumps(dict(API_CONFIG, **{field: value})))
                with self.subTest(field=field), self.assertRaises(ValueError):
                    core.load_config(path)


if __name__ == "__main__":
    unittest.main()
