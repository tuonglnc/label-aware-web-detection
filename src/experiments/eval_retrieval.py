"""Bước 2: đánh giá phần retrieval và kNN, KHÔNG cần gọi LLM.

Chạy:

    python -m src.experiments.eval_retrieval --retrieval src/artifacts/retrieval/minilm --split validation

Trả lời các câu hỏi sau bằng số liệu thật:

RQ1. Semantic retrieval (B) có hay lấy về ví dụ "giống nhưng khác nhãn" không?
     - top1_mismatch_rate: % query mà ví dụ giống nhất lại khác nhãn với query.
     - LCR@k của B: trung bình % ví dụ trong top-k cùng nhãn với query.

Baseline kNN vote: Macro-F1 khi chỉ đếm nhãn của k hàng xóm (k = 1, 3, 5, 7, 10).

Retrieval của các chiến lược (LCR@k, chưa cần LLM):
     - B (semantic), BAL (cân bằng lớp),
     - C với prior từ kNN vote (dùng được thật),
     - C-oracle với prior = nhãn thật (CHỈ để biết mức trần, không phải phương pháp).

Nhãn thật của query CHỈ được dùng ở đây để chấm điểm (và cho C-oracle được
ghi rõ là oracle).
"""

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from src.analysis.metrics import classification_metrics, label_consistency_rate
from src.retrieval.knn import knn_vote
from src.retrieval.selectors import class_balanced, label_aware_rerank, semantic_top_k

from .data_io import LABELS, load_jsonl, load_split, write_json


def evaluate_retrieval(queries, neighbors, k=4, n_candidates=30, lam=0.1, knn_ks=(1, 3, 5, 7, 10), prior_k=5,
                       lam_sweep=(0.0, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0)):
    """`queries`: bản ghi có nhãn (để chấm). `neighbors`: {request_id: candidates}."""
    truth = [q["label"] for q in queries]
    cands = [neighbors[q["request_id"]][:n_candidates] for q in queries]

    # --- Baseline kNN vote ---
    knn = {}
    for kk in knn_ks:
        preds = [knn_vote(c, kk)[0] for c in cands]
        m = classification_metrics(truth, preds, LABELS)
        knn[f"k={kk}"] = {"macro_f1": m["macro_f1"], "accuracy": m["accuracy"],
                          "normal_fpr": m["normal_false_positive_rate"],
                          "per_class_f1": {l: v["f1"] for l, v in m["per_class"].items()}}
    knn_prior = [knn_vote(c, prior_k)[0] for c in cands]
    prior_metrics = classification_metrics(truth, knn_prior, LABELS)

    # --- RQ1: ví dụ giống nhất có khác nhãn không? ---
    top1_mismatch = [c[0]["label"] != t for c, t in zip(cands, truth)]
    mismatch_by_class = defaultdict(list)
    for t, miss in zip(truth, top1_mismatch):
        mismatch_by_class[t].append(miss)

    # --- LCR@k cho từng chiến lược chọn ví dụ ---
    strategies = {
        "B_semantic": lambda c, i: semantic_top_k(c, k),
        "BAL_class_balanced": lambda c, i: class_balanced(c, k),
        "C_knn_prior": lambda c, i: label_aware_rerank(c, k, knn_prior[i], lam),
        "C_oracle_prior (analysis only)": lambda c, i: label_aware_rerank(c, k, truth[i], lam),
    }
    lcr = {}
    for name, select in strategies.items():
        per_query = [label_consistency_rate([d["label"] for d in select(c, i)], t)
                     for i, (c, t) in enumerate(zip(cands, truth))]
        by_class = defaultdict(list)
        for t, v in zip(truth, per_query):
            by_class[t].append(v)
        lcr[name] = {"mean": sum(per_query) / len(per_query),
                     "zero_match_rate": sum(v == 0 for v in per_query) / len(per_query),
                     "by_class": {l: sum(v) / len(v) for l, v in by_class.items()}}

    # Quét λ cho C (prior kNN) không cần LLM: λ lớn thì nhiều ví dụ cùng prior hơn,
    # nhưng khi prior sai thì càng nhiều query mất hết ví dụ đúng lớp.
    sweep = {}
    for value in lam_sweep:
        per_query = [label_consistency_rate([d["label"] for d in label_aware_rerank(c, k, knn_prior[i], value)], t)
                     for i, (c, t) in enumerate(zip(cands, truth))]
        sweep[str(value)] = {"lcr_mean": sum(per_query) / len(per_query),
                             "zero_match_rate": sum(v == 0 for v in per_query) / len(per_query)}

    prior_correct = [p == t for p, t in zip(knn_prior, truth)]
    return {
        "n_queries": len(queries), "k": k, "n_candidates": n_candidates, "lambda": lam, "prior_k": prior_k,
        "class_distribution": dict(Counter(truth)),
        "rq1_top1_mismatch_rate": sum(top1_mismatch) / len(top1_mismatch),
        "rq1_top1_mismatch_by_class": {l: sum(v) / len(v) for l, v in mismatch_by_class.items()},
        "mean_top1_similarity": sum(c[0]["similarity"] for c in cands) / len(cands),
        "knn_vote": knn,
        "knn_prior_accuracy": sum(prior_correct) / len(prior_correct),
        "knn_prior_confusion": prior_metrics["confusion_matrix"],
        "lcr_at_k": lcr,
        "lambda_sweep_knn_prior": sweep,
    }


def to_markdown(result, split):
    lines = [f"# Kết quả retrieval và kNN trên `{split}` ({result['n_queries']} query)", "",
             "Số liệu tự sinh bởi `src/experiments/eval_retrieval.py`; không gọi LLM.", "",
             "## RQ1: ví dụ giống nhất có khác nhãn không?", "",
             f"- Tỷ lệ query có ví dụ top-1 KHÁC nhãn: **{result['rq1_top1_mismatch_rate']:.1%}**",
             f"- Similarity trung bình của top-1: {result['mean_top1_similarity']:.3f}", "",
             "| Lớp | Top-1 khác nhãn |", "| --- | ---: |"]
    lines += [f"| {l} | {v:.1%} |" for l, v in sorted(result["rq1_top1_mismatch_by_class"].items())]
    lines += ["", "## Baseline kNN vote (không dùng LLM)", "",
              "| k | Macro-F1 | Accuracy | FPR Normal |", "| ---: | ---: | ---: | ---: |"]
    for kk, m in result["knn_vote"].items():
        fpr = "–" if m["normal_fpr"] is None else f"{m['normal_fpr']:.1%}"
        lines.append(f"| {kk[2:]} | {m['macro_f1']:.3f} | {m['accuracy']:.3f} | {fpr} |")
    lines += ["", f"## LCR@{result['k']} của các chiến lược chọn ví dụ (N = {result['n_candidates']}, λ = {result['lambda']})", "",
              f"Prior kNN (k={result['prior_k']}) đúng {result['knn_prior_accuracy']:.1%} số query.", "",
              "| Chiến lược | LCR@k trung bình | % query không có ví dụ nào cùng nhãn |", "| --- | ---: | ---: |"]
    for name, v in result["lcr_at_k"].items():
        lines.append(f"| {name} | {v['mean']:.3f} | {v['zero_match_rate']:.1%} |")
    lines += ["", f"## Quét λ cho C (prior kNN), k = {result['k']}", "",
              "| λ | LCR@k trung bình | % query không có ví dụ nào cùng nhãn |", "| ---: | ---: | ---: |"]
    for lam, v in result["lambda_sweep_knn_prior"].items():
        lines.append(f"| {lam} | {v['lcr_mean']:.3f} | {v['zero_match_rate']:.1%} |")
    lines += ["", "LCR@k chỉ là chỉ số chẩn đoán: ví dụ cùng nhãn nhiều hơn chưa chắc giúp LLM đoán đúng hơn.", ""]
    return "\n".join(lines)


def plot(result, output):
    """Hai hình cho báo cáo: (a) top-1 khác nhãn theo lớp, (b) LCR@k theo lớp của từng chiến lược."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    short = {"NORMAL": "Normal", "SQL_INJECTION": "SQLi", "PATH_TRAVERSAL": "Path Trav.", "CODE_INJECTION": "Code Inj.",
             "HTTP_RESPONSE_SPLITTING": "Resp. Split", "OS_COMMAND_INJECTION": "OS Cmd"}
    labels = [l for l in LABELS if l in result["rq1_top1_mismatch_by_class"]]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].bar([short[l] for l in labels], [100 * result["rq1_top1_mismatch_by_class"][l] for l in labels], color="#4C72B0")
    axes[0].set_ylabel("% query có ví dụ top-1 khác nhãn")
    axes[0].set_title("(a) RQ1: top-1 semantic khác nhãn")
    axes[0].tick_params(axis="x", rotation=30)
    width = 0.8 / len(result["lcr_at_k"])
    for i, (name, value) in enumerate(result["lcr_at_k"].items()):
        xs = [j + i * width for j in range(len(labels))]
        axes[1].bar(xs, [value["by_class"].get(l, 0) for l in labels], width, label=name.replace(" (analysis only)", "*"))
    axes[1].set_xticks([j + 0.4 - width / 2 for j in range(len(labels))], [short[l] for l in labels], rotation=30)
    axes[1].set_ylabel(f"LCR@{result['k']}")
    axes[1].set_ylim(0, 1.05)
    axes[1].set_title(f"(b) LCR@{result['k']} theo lớp (*: chỉ phân tích)")
    axes[1].legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(Path(output) / "retrieval_overview.png", dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--retrieval", required=True, help="thư mục output của build_retrieval")
    parser.add_argument("--split", default="validation", choices=["development", "validation", "test"])
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--n-candidates", type=int, default=30)
    parser.add_argument("--lam", type=float, default=0.1)
    parser.add_argument("--limit", type=int, help="chỉ đánh giá N query đầu (test: 300, khớp với phần LLM)")
    parser.add_argument("--output", help="mặc định: <retrieval>/eval_<split>")
    args = parser.parse_args()
    neighbors = {r["request_id"]: r["candidates"]
                 for r in load_jsonl(Path(args.retrieval) / f"neighbors_{args.split}.jsonl")}
    queries = load_split(args.split)[:args.limit] if args.limit else load_split(args.split)
    result = evaluate_retrieval(queries, neighbors, args.k, args.n_candidates, args.lam)
    output = Path(args.output or Path(args.retrieval) / f"eval_{args.split}")
    write_json(output / "retrieval_metrics.json", result)
    (output / "retrieval_metrics.md").write_text(to_markdown(result, args.split), encoding="utf-8")
    plot(result, output)
    from src.analysis.compare import plot_confusion
    plot_confusion({"confusion_matrix": result["knn_prior_confusion"]},
                   f"kNN vote (k={result['prior_k']}) trên {args.split}", output / "confusion_knn.png")
    print(to_markdown(result, args.split))


if __name__ == "__main__":
    main()
