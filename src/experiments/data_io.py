"""Đọc/ghi dữ liệu và quy ước tên file cho các thực nghiệm.

Dữ liệu do `src.preprocessing.prepare` tạo ra nằm ở `src/data/processed/sr_bh_v1/`.
Thực nghiệm dùng các tập con (subset) đã cố định từ trước:

| Tên split    | File                     | Vai trò                                         |
|--------------|--------------------------|-------------------------------------------------|
| pool         | pool_subset.jsonl        | Kho ví dụ có nhãn (3.000, 500/lớp)               |
| development  | development.jsonl        | Thử nhanh, sửa lỗi (30 mẫu)                      |
| validation   | validation_subset.jsonl  | Chọn cấu hình k, λ, … (200 mẫu)                  |
| test         | test_subset.jsonl        | Chỉ chạy MỘT lần sau khi đã khóa cấu hình (600) |
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "src/data/processed/sr_bh_v1"
SPLIT_FILES = {
    "pool": "pool_subset.jsonl",
    "development": "development.jsonl",
    "validation": "validation_subset.jsonl",
    "test": "test_subset.jsonl",
}
LABELS = tuple(json.loads((ROOT / "src/configs/data.json").read_text(encoding="utf-8"))["labels"].values())


def load_jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def split_path(split, data_dir=DATA_DIR):
    if split not in SPLIT_FILES:
        raise ValueError(f"unknown split {split!r}; choose one of {sorted(SPLIT_FILES)}")
    return Path(data_dir) / SPLIT_FILES[split]


def load_split(split, data_dir=DATA_DIR):
    rows = load_jsonl(split_path(split, data_dir))
    for row in rows:
        if row.get("label") not in LABELS or not row.get("request_id") or not isinstance(row.get("request_text"), str):
            raise ValueError(f"invalid row in {split}: {row.get('request_id')}")
    if len({r["request_id"] for r in rows}) != len(rows):
        raise ValueError(f"duplicate request_id in {split}")
    return rows


def sha256_of(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
