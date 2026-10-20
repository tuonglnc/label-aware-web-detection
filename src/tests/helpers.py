"""Dữ liệu và encoder giả cho test: nhỏ, chạy nhanh, không cần tải model."""

import hashlib
import json
from pathlib import Path

import numpy as np

PAYLOADS = {
    "NORMAL": ["/shop/item?id={i}", "/blog/post?page={i}", "/index.php?lang=en&p={i}"],
    "SQL_INJECTION": ["/shop/item?id={i}+AND+1%3D1", "/shop/item?id={i}+UNION+SELECT+1", "/blog/post?page={i}'+OR+'1'='1"],
    "PATH_TRAVERSAL": ["/download?file=../../etc/passwd{i}", "/static/..%2f..%2fwin.ini{i}", "/img?src=../../../boot{i}"],
    "CODE_INJECTION": ["/eval?code=print(chr({i}))", "/run?x=${{{i}*7}}", "/page?tpl=<?php+echo+{i};?>"],
    "HTTP_RESPONSE_SPLITTING": ["/redir?url=%0d%0aSet-Cookie:a={i}", "/go?to=x%0d%0aLocation:{i}", "/r?u=%0aX-H:{i}"],
    "OS_COMMAND_INJECTION": ["/ping?host=1;cat+/etc/passwd{i}", "/cgi?cmd=|id{i}", "/x?q=$(sleep+{i})"],
}


def request_text(uri, method="GET"):
    """Cùng dạng `request_text` canonical của preprocessing (JSON, sort_keys)."""
    return json.dumps({"body": "", "headers": {"Host": "example.test", "User-Agent": "Mozilla/5.0"},
                       "method": method, "protocol": "HTTP/1.1", "uri": uri},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def make_rows(prefix, start, per_label):
    rows = []
    for label, templates in PAYLOADS.items():
        for j in range(per_label):
            uri = templates[j % len(templates)].format(i=start + j)
            text = request_text(uri)
            rows.append({"request_id": f"{prefix}-{hashlib.sha256(text.encode()).hexdigest()[:12]}",
                         "request_text": text, "label": label, "private_metadata": "GROUND_TRUTH_CANARY"})
    return rows


def write_fixture_dataset(directory):
    """Tạo pool/development/validation/test nhỏ với tên file giống dữ liệu thật."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    splits = {"pool_subset.jsonl": make_rows("pool", 0, 6), "development.jsonl": make_rows("dev", 100, 1),
              "validation_subset.jsonl": make_rows("val", 200, 3), "test_subset.jsonl": make_rows("test", 300, 2)}
    for name, rows in splits.items():
        with (directory / name).open("w", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row) + "\n")
    return splits


class HashingEncoder:
    """Encoder giả: đếm các cụm 3 ký tự, băm vào 128 chiều. Đủ để request giống
    nhau có vector gần nhau; chỉ dùng trong test, không dùng cho thực nghiệm."""

    def describe(self):
        return {"encoder": "test-hashing", "dims": 128}

    def encode(self, texts):
        out = np.zeros((len(texts), 128), dtype=np.float32)
        for i, text in enumerate(texts):
            for j in range(len(text) - 2):
                out[i, int(hashlib.md5(text[j:j + 3].encode()).hexdigest(), 16) % 128] += 1
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return out / norms
