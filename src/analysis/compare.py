"""Bước 4: so sánh nhiều run trên cùng một split và xuất bảng/hình cho báo cáo.

Chạy:

    python -m src.analysis.compare --split validation --reference B_semantic_k4 \
        --runs src/artifacts/runs/validation/* --output src/artifacts/reports/validation

Đầu ra:
- `comparison.md` / `comparison.json`: bảng Macro-F1, Accuracy, FPR Normal,
  coverage, LCR@k, chi phí cho từng run; chênh lệch so với run tham chiếu
  (thường là B) kèm khoảng tin cậy bootstrap 95% và p-value McNemar.
- Bảng "prior đúng/sai" cho mọi run C: C sửa được bao nhiêu lỗi của B và làm
  hỏng bao nhiêu câu B đã đúng, tách theo prior đúng hay sai.
- `confusion_<run>.png`: ma trận nhầm lẫn của từng run.

Chỉ các run cùng split và cùng danh sách query mới được so sánh với nhau.
"""

import argparse
from collections import defaultdict
import glob
import json
from pathlib import Path

from src.experiments.data_io import LABELS, load_jsonl, load_split, write_json

from .metrics import classification_metrics, mcnemar, paired_bootstrap


def load_run(run_dir):
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    records = {r["request_id"]: r for r in load_jsonl(run_dir / "predictions.jsonl")}
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    return {"dir": str(run_dir), "name": manifest["experiment"].get("name", run_dir.name),
            "manifest": manifest, "records": records, "metrics": metrics}


def prior_breakdown(c_run, ref_run, truth):
    """Bảng chéo cho Pipeline C so với run tham chiếu (B).

    Với mỗi nhóm prior đúng / prior sai / không có prior, đếm:
    - fixed:  B sai, C đúng (C sửa được lỗi)
    - broken: B đúng, C sai (C làm hỏng)
    - both_correct, both_wrong.
    """
    table = defaultdict(lambda: {"fixed": 0, "broken": 0, "both_correct": 0, "both_wrong": 0, "n": 0})
    for qid, label in truth.items():
        rc, rb = c_run["records"][qid], ref_run["records"][qid]
        prior = rc.get("prior")
        group = "no_prior" if prior is None else ("prior_correct" if prior == label else "prior_wrong")
        c_ok = rc["status"] == "ok" and rc["predicted_label"] == label
        b_ok = rb["status"] == "ok" and rb["predicted_label"] == label
        key = {(False, True): "fixed", (True, False): "broken", (True, True): "both_correct",
               (False, False): "both_wrong"}[(b_ok, c_ok)]
        table[group][key] += 1
        table[group]["n"] += 1
    return dict(table)


def plot_confusion(metrics, title, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    counts = metrics["confusion_matrix"]["counts"]
    cols = metrics["confusion_matrix"]["columns"]
    short = [c.replace("HTTP_RESPONSE_SPLITTING", "RESP_SPLIT").replace("OS_COMMAND_INJECTION", "OS_CMD")
              .replace("_INJECTION", "_INJ").replace("__INVALID_OR_ERROR__", "ERROR") for c in cols]
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.imshow(counts, cmap="Blues")
    ax.set_xticks(range(len(cols)), short, rotation=40, ha="right")
    ax.set_yticks(range(len(LABELS)), short[:len(LABELS)])
    peak = max(max(row) for row in counts) or 1
    for i, row in enumerate(counts):
        for j, value in enumerate(row):
            ax.text(j, i, value, ha="center", va="center", color="white" if value > peak / 2 else "black", fontsize=9)
    ax.set_xlabel("Nhãn dự đoán")
    ax.set_ylabel("Nhãn thật")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def compare(split, run_dirs, reference, output, n_resamples=2000, data_dir=None):
    kwargs = {} if data_dir is None else {"data_dir": data_dir}
    rows = load_split(split, **kwargs)
    runs = [load_run(d) for d in run_dirs]
    if not runs:
        raise ValueError("no runs given")
    ids = set(runs[0]["records"])
    for run in runs:
        if run["manifest"]["split"] != split:
            raise ValueError(f"{run['name']} was run on split {run['manifest']['split']}, not {split}")
        if not run["metrics"].get("complete", True):
            raise ValueError(f"{run['name']} is not finished yet; rerun its command to complete it")
        if set(run["records"]) != ids:
            raise ValueError(f"{run['name']} has a different set of queries; compare only identical query sets")
    truth = {r["request_id"]: r["label"] for r in rows if r["request_id"] in ids}
    order = sorted(truth)
    y = [truth[q] for q in order]

    def preds(run):
        return [run["records"][q]["predicted_label"] if run["records"][q]["status"] == "ok" else None for q in order]

    ref = next((r for r in runs if r["name"] == reference), None)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    table = []
    for run in runs:
        m = classification_metrics(y, preds(run), LABELS)
        entry = {"name": run["name"], "pipeline": run["manifest"]["experiment"]["pipeline"],
                 "kind": run["manifest"]["experiment_kind"], "n": m["n"], "macro_f1": m["macro_f1"],
                 "accuracy": m["accuracy"], "normal_fpr": m["normal_false_positive_rate"], "coverage": m["coverage"],
                 "lcr_at_k": run["metrics"].get("lcr_at_k"), "cost": run["metrics"].get("cost"),
                 "per_class_f1": {l: v["f1"] for l, v in m["per_class"].items()}}
        if ref is not None and run is not ref:
            entry["vs_reference"] = {"bootstrap": paired_bootstrap(y, preds(run), preds(ref), LABELS, n_resamples),
                                     "mcnemar": mcnemar(y, preds(run), preds(ref))}
        if ref is not None and entry["pipeline"] == "C":
            entry["prior_breakdown_vs_reference"] = prior_breakdown(run, ref, truth)
        table.append(entry)
        plot_confusion(m, run["name"], output / f"confusion_{run['name']}.png")
    result = {"split": split, "reference": reference, "n_queries": len(order), "runs": table}
    write_json(output / "comparison.json", result)
    (output / "comparison.md").write_text(to_markdown(result), encoding="utf-8")
    return result


def to_markdown(result):
    lines = [f"# So sánh pipeline trên `{result['split']}` ({result['n_queries']} query)", "",
             "Tự sinh bởi `src/analysis/compare.py`. Run có kind `mock` dùng LLM giả: chỉ để kiểm tra luồng, "
             "không phải kết quả thực nghiệm.", "",
             "| Run | Pipeline | Kind | Macro-F1 | Accuracy | FPR Normal | Coverage | LCR@k | Lượt LLM/query | Token TB |",
             "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    fmt = lambda v, p=3: "–" if v is None else f"{v:.{p}f}"
    for r in result["runs"]:
        cost = r["cost"] or {}
        lines.append(f"| {r['name']} | {r['pipeline']} | {r['kind']} | {fmt(r['macro_f1'])} | {fmt(r['accuracy'])} | "
                     f"{fmt(r['normal_fpr'])} | {fmt(r['coverage'])} | {fmt(r['lcr_at_k'])} | "
                     f"{cost.get('llm_calls_per_query', '–')} | {fmt(cost.get('mean_total_tokens'), 0)} |")
    if any("vs_reference" in r for r in result["runs"]):
        lines += ["", f"## Chênh lệch Macro-F1 so với `{result['reference']}`", "",
                  "| Run | Δ Macro-F1 | CI 95% (bootstrap) | Chỉ run đúng | Chỉ tham chiếu đúng | p McNemar |",
                  "| --- | ---: | --- | ---: | ---: | ---: |"]
        for r in result["runs"]:
            if "vs_reference" in r:
                b, m = r["vs_reference"]["bootstrap"], r["vs_reference"]["mcnemar"]
                lines.append(f"| {r['name']} | {b['observed_diff']:+.3f} | [{b['ci95'][0]:+.3f}; {b['ci95'][1]:+.3f}] | "
                             f"{m['a_only_correct']} | {m['b_only_correct']} | {m['p_value']:.3f} |")
    for r in result["runs"]:
        if "prior_breakdown_vs_reference" in r:
            lines += ["", f"## Prior đúng/sai: `{r['name']}` so với `{result['reference']}`", "",
                      "| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
            for group, v in sorted(r["prior_breakdown_vs_reference"].items()):
                lines.append(f"| {group} | {v['n']} | {v['fixed']} | {v['broken']} | {v['both_correct']} | {v['both_wrong']} |")
    lines += ["", "## F1 từng lớp", "", "| Run | " + " | ".join(LABELS) + " |", "| --- |" + " ---: |" * len(LABELS)]
    for r in result["runs"]:
        lines.append(f"| {r['name']} | " + " | ".join(f"{r['per_class_f1'][l]:.2f}" for l in LABELS) + " |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", required=True, choices=["development", "validation", "test"])
    parser.add_argument("--runs", nargs="+", required=True, help="các thư mục run (chấp nhận wildcard)")
    parser.add_argument("--reference", default="B_semantic_k4", help="tên run làm mốc so sánh")
    parser.add_argument("--output", required=True)
    parser.add_argument("--resamples", type=int, default=2000)
    args = parser.parse_args()
    dirs = sorted({d for pattern in args.runs for d in glob.glob(pattern) if (Path(d) / "manifest.json").exists()})
    result = compare(args.split, dirs, args.reference, args.output, args.resamples)
    print(to_markdown(result))


if __name__ == "__main__":
    main()
