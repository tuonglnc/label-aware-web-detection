"""Gộp dự đoán của nhiều run bằng bỏ phiếu đa số (không gọi thêm LLM).

    python -m src.analysis.ensemble --split validation --name ENS_vote_B_BAL_Cknn \
        --runs src/artifacts/runs/validation/B_k4 src/artifacts/runs/validation/BAL_k4 \
               src/artifacts/runs/validation/C_knn_k4 \
        --output src/artifacts/runs/validation/ENS_vote

Ý tưởng: mỗi run là cùng một LLM nhưng xem một bộ ví dụ khác; gộp nhiều bộ ví
dụ thường ổn định hơn một bộ (ensemble: Dietterich, MCS 2000; ensemble theo các
nhóm ví dụ khác nhau: Khalifa và cộng sự, ME-FoMo @ ICLR 2023; bỏ phiếu đa số
trên nhiều lần suy luận: Wang và cộng sự, ICLR 2023). Groq không trả xác suất
của nhãn, nên dùng bỏ phiếu đa số; hòa phiếu thì theo run đứng ĐẦU danh sách.

Đầu ra là một thư mục run bình thường (manifest, predictions, metrics) để
`src.analysis.compare` so sánh được như mọi run khác. Chi phí = tổng chi phí của
các run thành viên.
"""

import argparse
from collections import Counter
import json
from pathlib import Path

from src.experiments.data_io import LABELS, load_jsonl, load_split, sha256_of, write_json
from src.experiments.run_llm import summarize


def majority(labels):
    """Nhãn nhiều phiếu nhất trong các nhãn hợp lệ; hòa thì nhãn xuất hiện sớm nhất trong danh sách."""
    valid = [label for label in labels if label is not None]
    if not valid:
        return None
    counts = Counter(valid)
    best = max(counts.values())
    return next(label for label in valid if counts[label] == best)


def ensemble(split, run_dirs, name, output, data_dir=None):
    kwargs = {} if data_dir is None else {"data_dir": data_dir}
    runs = []
    for d in run_dirs:
        d = Path(d)
        manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        metrics = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
        if manifest["split"] != split or not metrics.get("complete"):
            raise ValueError(f"{d} is not a complete run on split {split}")
        records = {r["request_id"]: r for r in load_jsonl(d / "predictions.jsonl")}
        runs.append({"manifest": manifest, "records": records})
    ids = list(runs[0]["records"])
    if any(set(r["records"]) != set(ids) for r in runs):
        raise ValueError("member runs cover different queries")
    truth = {r["request_id"]: r["label"] for r in load_split(split, **kwargs)}
    out_records = []
    for qid in ids:
        members = [r["records"][qid] for r in runs]
        votes = [m["predicted_label"] if m["status"] == "ok" else None for m in members]
        label = majority(votes)
        usage = {key: sum((m.get("usage") or {}).get(key, 0) for m in members)
                 for key in ("prompt_tokens", "completion_tokens", "total_tokens")}
        out_records.append({"request_id": qid, "pipeline": "ENS", "votes": votes, "predicted_label": label,
                            "status": "ok" if label in LABELS else "invalid_output", "usage": usage,
                            "demo_labels": [], "attempts": 0, "prior": None})
    experiment = {"name": name, "pipeline": "ENS", "members": [r["manifest"]["experiment"]["name"] for r in runs],
                  "tie_break": "first member"}
    manifest = {"run_key": sha256_of({"experiment": experiment, "members": [r["manifest"]["run_key"] for r in runs]}),
                "experiment": experiment, "split": split, "experiment_kind": "llm",
                "member_run_keys": [r["manifest"]["run_key"] for r in runs]}
    metrics = summarize(out_records, [truth[q] for q in ids])
    # Mỗi thành viên 1 lượt gọi, cộng thêm 1 lượt nếu nó cần prior từ một run LLM khác.
    calls = sum(1 + (r["manifest"].get("prior_run") is not None) for r in runs)
    metrics.setdefault("cost", {})["llm_calls_per_query"] = calls
    metrics.update(experiment_kind="llm", run_key=manifest["run_key"], pipeline="ENS", split=split,
                   complete=True, n_selected=len(ids))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "manifest.json", manifest)
    with (output / "predictions.jsonl").open("w", encoding="utf-8") as stream:
        for rec in out_records:
            stream.write(json.dumps(rec, ensure_ascii=False) + "\n")
    write_json(output / "metrics.json", metrics)
    return {"name": name, "macro_f1": metrics["macro_f1"], "n": len(ids)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", required=True, choices=["development", "validation", "test", "test_fresh"])
    parser.add_argument("--runs", nargs="+", required=True, help="các run thành viên; run đầu tiên thắng khi hòa phiếu")
    parser.add_argument("--name", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(ensemble(args.split, args.runs, args.name, args.output))


if __name__ == "__main__":
    main()
