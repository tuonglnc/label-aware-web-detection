"""Tạo tập test MỚI cho vòng cải tiến Pipeline C (không gọi LLM).

    python -m src.preprocessing.make_fresh_test

Vì sao cần: 600 request của `test_subset.jsonl` đều đã được dùng (300 đầu cho thí
nghiệm chính, 300 sau cho C-gated). Muốn so các phương pháp mới một cách công
bằng thì cần dữ liệu chưa ai nhìn thấy. Tập mới lấy từ `test.jsonl` (cùng phía
test của phép chia theo nhóm, nên vẫn không trùng nhóm với pool):

- bỏ mọi request có `group_id` đã xuất hiện trong `test_subset.jsonl`;
- mỗi nhóm lấy tối đa 1 request (tránh nhiều request gần trùng nhau);
- cân bằng 50 request/lớp, lấy luân phiên theo lớp, ngẫu nhiên trong lớp với
  seed cố định, giống cách `prepare.balanced_subset` tạo các tập con cũ.
"""

import argparse
from collections import Counter, defaultdict
import random

from src.experiments.data_io import DATA_DIR, file_sha256, load_jsonl, write_json, write_jsonl

SEED = "test_fresh-v1-42"


def fresh_subset(test_rows, used_rows, per_class, seed=SEED):
    used_groups = {r["group_id"] for r in used_rows}
    by_label = defaultdict(list)
    for row in sorted(test_rows, key=lambda r: r["request_id"]):
        if row["group_id"] not in used_groups:
            by_label[row["label"]].append(row)
    rng = random.Random(seed)
    for label in sorted(by_label):
        rng.shuffle(by_label[label])
    taken_groups, result, counts = set(), [], Counter()
    while True:
        progressed = False
        for label in sorted(by_label):
            while by_label[label] and counts[label] < per_class:
                row = by_label[label].pop()
                if row["group_id"] in taken_groups:
                    continue
                taken_groups.add(row["group_id"])
                result.append(row)
                counts[label] += 1
                progressed = True
                break
        if not progressed:
            break
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--per-class", type=int, default=50)
    args = parser.parse_args()
    test_path, used_path = DATA_DIR / "test.jsonl", DATA_DIR / "test_subset.jsonl"
    rows = fresh_subset(load_jsonl(test_path), load_jsonl(used_path), args.per_class)
    out = DATA_DIR / "test_fresh_subset.jsonl"
    if out.exists():
        raise SystemExit(f"{out} already exists; refusing to overwrite")
    write_jsonl(out, rows)
    write_json(DATA_DIR / "test_fresh_manifest.json", {
        "seed": SEED, "per_class": args.per_class, "size": len(rows),
        "distribution": dict(sorted(Counter(r["label"] for r in rows).items())),
        "source_sha256": {"test.jsonl": file_sha256(test_path), "test_subset.jsonl": file_sha256(used_path)},
        "output_sha256": file_sha256(out)})
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
