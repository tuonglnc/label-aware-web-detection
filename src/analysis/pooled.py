"""Gộp nhiều tập test độc lập để so hai pipeline trên nhiều query hơn (không gọi LLM).

    python -m src.analysis.pooled --method C_knn_k4 --reference B_k4 \
        --sets test:src/artifacts/runs/test test:src/artifacts/runs/test_301_600 test_fresh:src/artifacts/runs/test_fresh

Mỗi phần tử `--sets` có dạng `split:thư_mục_chứa_các_run`. Các tập phải không
trùng query; hàm sẽ kiểm tra. Gộp lại thì khoảng tin cậy hẹp hơn (độ rộng giảm
theo căn bậc hai của số query), giúp phân biệt chênh lệch thật với dao động do
chọn mẫu. Chỉ gộp các run ĐÃ CÓ; không chỉnh gì trên test.
"""

import argparse
import json
from pathlib import Path

from src.experiments.data_io import LABELS, load_jsonl, load_split

from .metrics import macro_f1, mcnemar, paired_bootstrap


def pooled(method, reference, sets, n_resamples=2000):
    y, pm, pr, groups, per_set, seen = [], [], [], [], [], set()
    for split, root in sets:
        truth = {r["request_id"]: r["label"] for r in load_split(split)}
        a = {r["request_id"]: r for r in load_jsonl(Path(root) / method / "predictions.jsonl")}
        b = {r["request_id"]: r for r in load_jsonl(Path(root) / reference / "predictions.jsonl")}
        if set(a) != set(b):
            raise ValueError(f"{root}: {method} and {reference} cover different queries")
        if seen & set(a):
            raise ValueError(f"{root}: overlapping queries with an earlier set")
        seen |= set(a)
        ids = sorted(a)
        ys = [truth[q] for q in ids]
        ps = [a[q]["predicted_label"] if a[q]["status"] == "ok" else None for q in ids]
        rs = [b[q]["predicted_label"] if b[q]["status"] == "ok" else None for q in ids]
        per_set.append({"set": f"{split}:{root}", "n": len(ids), "method": macro_f1(ys, ps, LABELS),
                        "reference": macro_f1(ys, rs, LABELS), "mcnemar": mcnemar(ys, ps, rs)})
        y += ys
        pm += ps
        pr += rs
        groups += [len(per_set)] * len(ids)
    return {"method": method, "reference": reference, "n": len(y), "per_set": per_set,
            "pooled": {"method": macro_f1(y, pm, LABELS), "reference": macro_f1(y, pr, LABELS),
                       "bootstrap": paired_bootstrap(y, pm, pr, LABELS, n_resamples),
                       "mcnemar": mcnemar(y, pm, pr)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--method", required=True, help="tên thư mục run của phương pháp, ví dụ C_knn_k4")
    parser.add_argument("--reference", default="B_k4")
    parser.add_argument("--sets", nargs="+", required=True, help="split:thư_mục")
    parser.add_argument("--output", help="ghi kết quả JSON")
    args = parser.parse_args()
    result = pooled(args.method, args.reference, [s.split(":", 1) for s in args.sets])
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
