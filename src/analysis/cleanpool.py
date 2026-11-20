"""Phân tích B-cleanpool so với B theo tiêu chí đã khóa (không gọi LLM).

    python -m src.analysis.cleanpool --output src/artifacts/reports/cleanpool

Tiêu chí H1–H3 nằm trong reports/experiments/cau_hinh_khoa_pool_sach.md. Chạy trên hai tập
test độc lập (test_fresh và test 301–600) và gộp 600 query. Ngoài ra ghi các số mô tả: Macro-F1
khi bỏ Normal đáng ngờ khỏi tập đánh giá, và riêng nhóm query bị đổi bộ ví dụ.
"""

import argparse
import json
from pathlib import Path

from src.experiments.data_io import LABELS, load_jsonl, load_split, write_json

from .label_noise import suspicious_rules
from .metrics import macro_f1, mcnemar, paired_bootstrap

METHOD, REFERENCE = "B_cleanpool_k4", "B_k4"
SETS = (("test_fresh", "test_fresh", 0, "src/artifacts/runs/test_fresh"),
        ("test 301-600", "test", 300, "src/artifacts/runs/test_301_600"))


def _load(root, name):
    return {r["request_id"]: r for r in load_jsonl(Path(root) / name / "predictions.jsonl")}


def _pred(rec):
    return rec["predicted_label"] if rec["status"] == "ok" else None


def analyze(n_resamples=2000):
    groups = {}
    pooled = {"y": [], "m": [], "r": []}
    for name, split, _, root in SETS:
        truth = {r["request_id"]: r for r in load_split(split)}
        a, b = _load(root, METHOD), _load(root, REFERENCE)
        if set(a) != set(b):
            raise ValueError(f"{root}: runs cover different queries")
        ids = sorted(a)
        y = [truth[q]["label"] for q in ids]
        pm, pr = [_pred(a[q]) for q in ids], [_pred(b[q]) for q in ids]
        keep = [i for i, q in enumerate(ids) if not (truth[q]["label"] == "NORMAL"
                                                     and suspicious_rules(truth[q]["request_text"]))]
        changed = [i for i, q in enumerate(ids) if a[q]["demo_ids"] != b[q]["demo_ids"]]
        pick = lambda xs, idx: [xs[i] for i in idx]
        groups[name] = {
            "n": len(ids), "B": macro_f1(y, pr, LABELS), "cleanpool": macro_f1(y, pm, LABELS),
            "bootstrap": paired_bootstrap(y, pm, pr, LABELS, n_resamples), "mcnemar": mcnemar(y, pm, pr),
            "attack_pred_normal": {"B": sum(t != "NORMAL" and p == "NORMAL" for t, p in zip(y, pr)),
                                   "cleanpool": sum(t != "NORMAL" and p == "NORMAL" for t, p in zip(y, pm))},
            "eval_without_suspicious_normal": {
                "n": len(keep), "B": macro_f1(pick(y, keep), pick(pr, keep), LABELS),
                "cleanpool": macro_f1(pick(y, keep), pick(pm, keep), LABELS)},
            "changed_demos": {"n": len(changed),
                              "fixed": sum(pm[i] == y[i] and pr[i] != y[i] for i in changed),
                              "broken": sum(pr[i] == y[i] and pm[i] != y[i] for i in changed)},
            # Prompt giống hệt nhau (cùng ví dụ, cùng thứ tự): chênh lệch ở đây chỉ có thể do LLM dao động.
            "same_demos": {"n": len(ids) - len(changed),
                           "fixed": sum(pm[i] == y[i] and pr[i] != y[i] for i in range(len(ids)) if i not in changed),
                           "broken": sum(pr[i] == y[i] and pm[i] != y[i] for i in range(len(ids)) if i not in changed),
                           "answer_changed": sum(pm[i] != pr[i] for i in range(len(ids)) if i not in changed)},
        }
        pooled["y"] += y
        pooled["m"] += pm
        pooled["r"] += pr
    y, pm, pr = pooled["y"], pooled["m"], pooled["r"]
    total = {"n": len(y), "B": macro_f1(y, pr, LABELS), "cleanpool": macro_f1(y, pm, LABELS),
             "bootstrap": paired_bootstrap(y, pm, pr, LABELS, n_resamples), "mcnemar": mcnemar(y, pm, pr),
             "attack_pred_normal": {"B": sum(t != "NORMAL" and p == "NORMAL" for t, p in zip(y, pr)),
                                    "cleanpool": sum(t != "NORMAL" and p == "NORMAL" for t, p in zip(y, pm))}}
    return {"sets": groups, "pooled": total}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", required=True)
    parser.add_argument("--resamples", type=int, default=2000)
    args = parser.parse_args()
    result = analyze(args.resamples)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "cleanpool.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
