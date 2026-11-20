"""Bảng so sánh có hiệu chỉnh Holm cho các phương pháp đã đăng ký trước (đọc `comparison.json`).

    python -m src.analysis.holm_table --comparison src/artifacts/reports/test_fresh/comparison.json \
        --methods C_gated_knn_prior_k4_lambda0.1_share0.7 B_mmr_lambda0.5_k4 ... \
        --output src/artifacts/reports/test_fresh/holm.md
"""

import argparse
import json
from pathlib import Path

from .metrics import holm


def holm_table(comparison, methods):
    runs = {r["name"]: r for r in comparison["runs"]}
    missing = [m for m in methods if m not in runs or "vs_reference" not in runs[m]]
    if missing:
        raise ValueError(f"missing comparisons for {missing}")
    raw = [runs[m]["vs_reference"]["mcnemar"]["p_value"] for m in methods]
    rows = []
    for name, p_raw, p_adj in zip(methods, raw, holm(raw)):
        b = runs[name]["vs_reference"]["bootstrap"]
        mc = runs[name]["vs_reference"]["mcnemar"]
        rows.append({"name": name, "macro_f1": runs[name]["macro_f1"], "diff": b["observed_diff"], "ci95": b["ci95"],
                     "only_method_correct": mc["a_only_correct"], "only_reference_correct": mc["b_only_correct"],
                     "p_mcnemar": p_raw, "p_holm": p_adj, "significant": p_adj < 0.05})
    return rows


def to_markdown(rows, reference):
    lines = [f"| Phương pháp | Macro-F1 | Δ so với {reference} | CI 95% | Chỉ PP đúng | Chỉ {reference} đúng | p McNemar | p Holm |",
             "| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |"]
    for r in rows:
        lines.append(f"| {r['name']} | {r['macro_f1']:.3f} | {r['diff']:+.3f} | [{r['ci95'][0]:+.3f}; {r['ci95'][1]:+.3f}] | "
                     f"{r['only_method_correct']} | {r['only_reference_correct']} | {r['p_mcnemar']:.3f} | "
                     f"{r['p_holm']:.3f}{' *' if r['significant'] else ''} |")
    return "\n".join(lines) + "\n\n`*`: có ý nghĩa ở mức 0,05 sau hiệu chỉnh Holm.\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--comparison", required=True)
    parser.add_argument("--methods", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    comparison = json.loads(Path(args.comparison).read_text(encoding="utf-8"))
    rows = holm_table(comparison, args.methods)
    Path(args.output).write_text(to_markdown(rows, comparison["reference"]), encoding="utf-8")
    print(to_markdown(rows, comparison["reference"]))


if __name__ == "__main__":
    main()
