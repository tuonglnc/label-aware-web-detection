"""Vẽ các hình sơ đồ cho báo cáo (không phải hình kết quả).

Chạy: python reports/word/make_figures.py  ->  reports/word/figures/*.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent / "figures"


def box(ax, x, y, w, h, text, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                linewidth=1.2, edgecolor="#333333", facecolor=color))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9.5, wrap=True)


def arrow(ax, x1, y1, x2, y2, text=None):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13,
                                 linewidth=1.1, color="#333333"))
    if text:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.08, text, ha="center", fontsize=8, color="#444444")


def pipeline():
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 5.8)
    ax.axis("off")
    blue, green, orange, grey = "#DCE9F7", "#DFF2E1", "#FCE9D2", "#EEEEEE"
    box(ax, 0.1, 2.25, 1.6, 0.8, "HTTP request\ncần phân loại", grey)
    box(ax, 2.3, 3.6, 2.0, 0.8, "Embedding\n(all-MiniLM-L6-v2)", blue)
    box(ax, 4.9, 3.6, 2.2, 0.8, "Top-N ứng viên\n(kèm nhãn ứng viên)", blue)
    box(ax, 2.3, 0.9, 2.0, 0.8, "Prior: LLM zero-shot\nhoặc kNN vote", orange)
    box(ax, 7.6, 2.25, 1.6, 0.8, "Chọn k ví dụ\nB / BAL / C", green)
    box(ax, 9.45, 3.6, 1.45, 0.8, "Prompt\n+ LLM", green)
    box(ax, 9.45, 0.9, 1.45, 0.8, "Nhãn\ndự đoán", grey)
    box(ax, 4.9, 4.85, 2.2, 0.75, "Pool 3.000 ví dụ\ncó nhãn (500/lớp)", grey)
    arrow(ax, 1.7, 2.85, 2.3, 3.8)
    arrow(ax, 1.7, 2.45, 2.3, 1.3)
    arrow(ax, 4.3, 4.0, 4.9, 4.0, "cosine")
    arrow(ax, 6.0, 4.85, 6.0, 4.4)
    arrow(ax, 7.1, 3.8, 7.75, 3.05)
    arrow(ax, 4.3, 1.3, 7.75, 2.3)
    ax.text(6.3, 1.45, "prior (chỉ dùng cho C)", ha="center", fontsize=8, color="#444444", rotation=16)
    arrow(ax, 9.2, 2.85, 9.7, 3.6)
    arrow(ax, 10.17, 3.6, 10.17, 1.7)
    ax.text(5.5, 0.25, "C: score(d) = sim(q, d) + λ · 1[nhãn(d) = prior(q)]   |   λ = 0 ⇒ C trùng B",
            ha="center", fontsize=9.5, style="italic")
    fig.tight_layout()
    fig.savefig(OUT / "pipeline.png", dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    pipeline()
    print("saved", OUT / "pipeline.png")
