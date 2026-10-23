"""Phân tích C-gated (C chỉ dùng khi prior kNN đủ tự tin), KHÔNG gọi LLM.

Chạy (validation, dùng để CHỌN ngưỡng):

    python -m src.experiments.analyze_gating --split validation \
        --runs-dir src/artifacts/runs/validation --output src/artifacts/reports/gating/validation

Chạy trên 300 test đã dùng (CHỈ để tham khảo, không được dùng để chọn ngưỡng):

    python -m src.experiments.analyze_gating --split test --limit 300 \
        --runs-dir src/artifacts/runs/test --output src/artifacts/reports/gating/test_1_300_exploratory

Với mỗi ngưỡng t của độ tự tin (tỷ lệ phiếu kNN dồn cho nhãn thắng, `knn.vote_share`):
- query có độ tự tin >= t được "gate vào" (chọn ví dụ như C), còn lại chọn như B;
- t = 0 trùng với C (prior kNN), t > 1 trùng với B.

Bảng 1 (chỉ retrieval): độ phủ, độ chính xác của prior ở nhóm gate vào / gate ra,
tỷ lệ query mà bộ ví dụ thật sự khác B, LCR@k và tỷ lệ không có ví dụ nào cùng nhãn.

Bảng 2 (phản thực tế, không tốn tiền): mỗi query của C-gated có prompt GIỐNG HỆT
prompt của B (gate ra) hoặc của C prior kNN (gate vào), nên lấy dự đoán đã có của
hai run đó ghép lại sẽ ra dự đoán của C-gated (chỉ sai khác nếu LLM không tất định
ở temperature 0). Báo Macro-F1, chênh lệch so với B kèm CI bootstrap 95%, và số
câu C-gated sửa được / làm hỏng so với B.
"""

import argparse
import json
from pathlib import Path

from src.analysis.metrics import classification_metrics, label_consistency_rate, paired_bootstrap
from src.retrieval.knn import knn_vote, vote_share
from src.retrieval.selectors import gated_label_aware_rerank, semantic_top_k

from .data_io import LABELS, load_jsonl, load_split, write_json

THRESHOLDS = (0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.01)


def threshold_name(t):
    return {0.0: "0 (= C prior kNN)", 1.0: "1.0 (5/5 cùng nhãn)", 1.01: "> 1 (= B)"}.get(t, str(t))


def gating_table(queries, neighbors, runs=None, k=4, n_candidates=30, lam=0.1, prior_k=5,
                 thresholds=THRESHOLDS, n_resamples=2000):
    """`runs`: None hoặc {"B": {request_id: nhãn đoán hoặc None}, "C": {...}} của hai run LLM đã có."""
    truth = [q["label"] for q in queries]
    cands = [neighbors[q["request_id"]][:n_candidates] for q in queries]
    votes = [knn_vote(c, prior_k) for c in cands]
    priors = [winner for winner, _ in votes]
    shares = [vote_share(scores, winner) for winner, scores in votes]
    b_demos = [[d["request_id"] for d in semantic_top_k(c, k)] for c in cands]
    ids = [q["request_id"] for q in queries]
    if runs is not None:
        y_b = [runs["B"][i] for i in ids]
        b_metrics = classification_metrics(truth, y_b, LABELS)

    def accuracy(idx):
        return sum(priors[i] == truth[i] for i in idx) / len(idx) if idx else None

    rows = []
    for t in thresholds:
        gated_in = [i for i, s in enumerate(shares) if s is not None and s >= t]
        gated_out = [i for i in range(len(queries)) if i not in set(gated_in)]
        picked = [gated_label_aware_rerank(c, k, priors[i], lam, shares[i], t) for i, c in enumerate(cands)]
        changed = [i for i, p in enumerate(picked) if [d["request_id"] for d in p] != b_demos[i]]
        lcr = [label_consistency_rate([d["label"] for d in p], truth[i]) for i, p in enumerate(picked)]
        row = {"threshold": t, "name": threshold_name(t), "n": len(queries),
               "coverage": len(gated_in) / len(queries),
               "prior_accuracy_gated_in": accuracy(gated_in), "prior_accuracy_gated_out": accuracy(gated_out),
               "changed_vs_B": len(changed) / len(queries), "n_changed": len(changed),
               "prior_accuracy_changed": accuracy(changed),
               "lcr_at_k": sum(lcr) / len(lcr), "zero_match_rate": sum(v == 0 for v in lcr) / len(lcr)}
        if runs is not None:
            gated = set(gated_in)
            y_g = [runs["C"][q] if i in gated else runs["B"][q] for i, q in enumerate(ids)]
            m = classification_metrics(truth, y_g, LABELS)
            fixed = sum(g == y != b for g, y, b in zip(y_g, truth, y_b))
            broken = sum(b == y != g for g, y, b in zip(y_g, truth, y_b))
            boot = paired_bootstrap(truth, y_g, y_b, LABELS, n_resamples) if y_g != y_b else None
            row["counterfactual"] = {"macro_f1": m["macro_f1"], "accuracy": m["accuracy"],
                                     "diff_vs_B": m["macro_f1"] - b_metrics["macro_f1"],
                                     "ci95_vs_B": boot["ci95"] if boot else [0.0, 0.0],
                                     "fixed_vs_B": fixed, "broken_vs_B": broken}
        rows.append(row)
    return {"n_queries": len(queries), "k": k, "n_candidates": n_candidates, "lambda": lam, "prior_k": prior_k,
            "knn_prior_accuracy": accuracy(range(len(queries))),
            "B_macro_f1": b_metrics["macro_f1"] if runs is not None else None, "rows": rows}


def to_markdown(result, title):
    pct = lambda v: "–" if v is None else f"{v:.1%}"
    lines = [f"# {title}", "", "Số liệu tự sinh bởi `src/experiments/analyze_gating.py`; không gọi LLM.", "",
             f"{result['n_queries']} query, k = {result['k']}, N = {result['n_candidates']}, λ = {result['lambda']}, "
             f"prior kNN k = {result['prior_k']} (đúng {result['knn_prior_accuracy']:.1%}).", "",
             "Độ tự tin = tỷ lệ phiếu (có trọng số similarity) dồn cho nhãn thắng trong 5 hàng xóm.", "",
             "## 1. Retrieval (không cần LLM)", "",
             "| Ngưỡng | Gate vào | Prior đúng (gate vào) | Prior đúng (gate ra) | Bộ ví dụ khác B | Prior đúng (ở câu khác B) | LCR@k | Không ví dụ nào cùng nhãn |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in result["rows"]:
        lines.append(f"| {r['name']} | {pct(r['coverage'])} | {pct(r['prior_accuracy_gated_in'])} | "
                     f"{pct(r['prior_accuracy_gated_out'])} | {pct(r['changed_vs_B'])} ({r['n_changed']}) | "
                     f"{pct(r['prior_accuracy_changed'])} | {r['lcr_at_k']:.3f} | {pct(r['zero_match_rate'])} |")
    if result["B_macro_f1"] is not None:
        lines += ["", "## 2. Phản thực tế từ các run LLM đã có (B cho câu gate ra, C prior kNN cho câu gate vào)", "",
                  f"B: Macro-F1 = {result['B_macro_f1']:.3f}.", "",
                  "| Ngưỡng | Macro-F1 | Chênh lệch so với B | CI 95% bootstrap | Sửa được lỗi của B | Làm hỏng câu B đúng |",
                  "| --- | ---: | ---: | --- | ---: | ---: |"]
        for r in result["rows"]:
            c = r["counterfactual"]
            lines.append(f"| {r['name']} | {c['macro_f1']:.3f} | {c['diff_vs_B']:+.3f} | "
                         f"[{c['ci95_vs_B'][0]:+.3f}; {c['ci95_vs_B'][1]:+.3f}] | {c['fixed_vs_B']} | {c['broken_vs_B']} |")
    lines += ["", "Ghi chú: khi 5/5 hàng xóm cùng nhãn thì 4 ví dụ của B đã cùng nhãn prior, nên C không đổi gì; "
              "C chỉ thay ví dụ ở những query mà hàng xóm bất đồng.", ""]
    return "\n".join(lines)


def load_predictions(run_dir):
    return {r["request_id"]: (r["predicted_label"] if r["status"] == "ok" else None)
            for r in load_jsonl(Path(run_dir) / "predictions.jsonl")}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--retrieval", default="src/artifacts/retrieval/minilm")
    parser.add_argument("--split", default="validation", choices=["development", "validation", "test"])
    parser.add_argument("--limit", type=int, help="chỉ phân tích N query đầu (test: 300)")
    parser.add_argument("--offset", type=int, default=0, help="bỏ qua M query đầu (nửa sau test: --offset 300)")
    parser.add_argument("--runs-dir", help="thư mục chứa B_k4/ và C_knn_k4/ (bỏ trống = chỉ phân tích retrieval)")
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", help="tiêu đề bảng markdown")
    args = parser.parse_args()
    neighbors = {r["request_id"]: r["candidates"]
                 for r in load_jsonl(Path(args.retrieval) / f"neighbors_{args.split}.jsonl")}
    queries = load_split(args.split)[args.offset:]
    queries = queries[:args.limit] if args.limit else queries
    runs = None
    if args.runs_dir:
        runs = {"B": load_predictions(Path(args.runs_dir) / "B_k4"), "C": load_predictions(Path(args.runs_dir) / "C_knn_k4")}
        missing = [q["request_id"] for q in queries if q["request_id"] not in runs["B"] or q["request_id"] not in runs["C"]]
        if missing:
            parser.exit(2, f"{len(missing)} queries lack a B or C_knn prediction\n")
    result = gating_table(queries, neighbors, runs)
    title = args.title or f"C-gated: phân tích ngưỡng trên `{args.split}`"
    output = Path(args.output)
    write_json(output / "gating.json", result)
    (output / "gating.md").write_text(to_markdown(result, title), encoding="utf-8")
    print(to_markdown(result, title))


if __name__ == "__main__":
    main()
