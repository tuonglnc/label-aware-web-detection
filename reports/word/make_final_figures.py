"""Vẽ các hình mới cho báo cáo cuối kỳ từ kết quả đã lưu (không gọi LLM).

Chạy: python reports/word/make_final_figures.py  ->  reports/word/figures/final_*.png
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "src/artifacts/reports"
OUT = ROOT / "reports/word/figures"

SHORT = {
    "A0_zero_shot": "A0 (không ví dụ)", "A1_fixed_k4": "A1 (ví dụ cố định)", "B_semantic_k4": "B (giống nhất)",
    "BAL_class_balanced_k4": "BAL (luân phiên lớp)", "C_knn_prior_k4_lambda0.1": "C-kNN",
    "C_llm_prior_k4_lambda0.1": "C-LLM", "C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY": "C-oracle*",
    "C_gated_knn_prior_k4_lambda0.1_share0.7": "C-gated", "B_mmr_lambda0.5_k4": "B-MMR",
    "B_cll_w1.0_k4": "B-CLL", "B_enn_k4": "B-ENN", "C_knn_prior_enn_k4_lambda0.1": "C-kNN-ENN",
    "C_iter_Bprior_k4_lambda0.1": "C-iter", "ENS_vote_B_BAL_Cknn": "ENS (bỏ phiếu)",
}
NOISE = 0.011  # chênh lệch Macro-F1 khi chạy lại B với cùng prompt (validation và test_fresh)


def load(name):
    return json.loads((REPORTS / name / "comparison.json").read_text(encoding="utf-8"))


def f1_across_sets():
    sets = [("validation", "Validation (200)", "o"), ("test", "Test 1–300", "s"),
            ("test_301_600", "Test 301–600", "^"), ("test_fresh", "Test mới (300)", "D")]
    order = ["A0_zero_shot", "A1_fixed_k4", "BAL_class_balanced_k4", "B_semantic_k4", "C_knn_prior_k4_lambda0.1",
             "C_llm_prior_k4_lambda0.1", "C_gated_knn_prior_k4_lambda0.1_share0.7",
             "C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY"]
    knn = {"Validation (200)": 0.800, "Test 1–300": 0.742, "Test mới (300)": 0.747}
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for k, (folder, label, marker) in enumerate(sets):
        runs = {r["name"]: r["macro_f1"] for r in load(folder)["runs"]}
        xs = [i + (k - 1.5) * 0.12 for i, n in enumerate(order) if n in runs]
        ys = [runs[n] for n in order if n in runs]
        ax.scatter(xs, ys, marker=marker, s=46, label=label, zorder=3)
    ax.set_xticks(range(len(order)), [SHORT[n] for n in order], rotation=20, ha="right")
    for label, value in knn.items():
        ax.axhline(value, color="grey", lw=0.6, ls=":")
    ax.text(len(order) - 0.6, 0.745, "kNN (không LLM) ≈ 0,74–0,80", fontsize=8, color="grey", ha="right")
    ax.set_ylabel("Macro-F1 (càng cao càng tốt)")
    ax.set_ylim(0.72, 0.92)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=8, ncol=4, loc="lower right")
    ax.set_title("Macro-F1 của các pipeline trên bốn tập đánh giá (* chỉ để phân tích)")
    fig.tight_layout()
    fig.savefig(OUT / "final_f1_across_sets.png", dpi=170)
    plt.close(fig)


def forest(rows, title, path, xlabel="Chênh lệch Macro-F1 so với B (khoảng tin cậy 95%)"):
    fig, ax = plt.subplots(figsize=(9, 0.42 * len(rows) + 1.4))
    ax.axvspan(-NOISE, NOISE, color="#f2d7a6", alpha=0.6, label="Vùng dao động khi chạy lại (±0,011)")
    ax.axvline(0, color="black", lw=0.8)
    for i, (label, diff, lo, hi, strong) in enumerate(rows):
        color = "#1f6fb4" if strong else "#555555"
        ax.plot([lo, hi], [i, i], color=color, lw=2)
        ax.plot(diff, i, "o", color=color, ms=6)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlabel(xlabel)
    ax.set_title(title, fontsize=11)
    ax.grid(axis="x", alpha=0.3)
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


def fresh_forest():
    comp = load("test_fresh")
    rows = []
    for r in comp["runs"]:
        if "vs_reference" not in r:
            continue
        b = r["vs_reference"]["bootstrap"]
        rows.append((SHORT.get(r["name"], r["name"]), b["observed_diff"], b["ci95"][0], b["ci95"][1],
                     b["ci95"][0] > 0 or b["ci95"][1] < 0))
    rows.sort(key=lambda x: -x[1])
    forest(rows, "Tập test mới (300 request): mỗi phương pháp so với B", OUT / "final_fresh_forest.png")


def pooled_forest():
    names = [("C_oracle_k4", "C-oracle* (600)"), ("C_gated_k4", "C-gated (600)"), ("C_knn_k4", "C-kNN (900)"),
             ("C_llm_k4", "C-LLM (600)"), ("BAL_k4", "BAL (600)"), ("A1_k4", "A1 (600)"), ("A0", "A0 (600)")]
    rows = []
    for folder, label in names:
        r = json.loads((REPORTS / "pooled" / f"{folder}.json").read_text(encoding="utf-8"))["pooled"]["bootstrap"]
        rows.append((label, r["observed_diff"], r["ci95"][0], r["ci95"][1], r["ci95"][0] > 0 or r["ci95"][1] < 0))
    forest(rows, "Gộp các tập test độc lập (số request trong ngoặc)", OUT / "final_pooled_forest.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    f1_across_sets()
    fresh_forest()
    pooled_forest()
    print("done")
