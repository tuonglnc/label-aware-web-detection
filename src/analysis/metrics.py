"""Metrics phân loại và kiểm định thống kê, chỉ dùng numpy và thư viện chuẩn.

Giải thích nhanh các chỉ số:
- Precision của lớp X: trong các request bị đoán là X, bao nhiêu % đúng là X.
- Recall của lớp X: trong các request thật sự là X, bao nhiêu % được đoán ra.
- F1 = trung bình điều hòa của precision và recall.
- Macro-F1 (metric CHÍNH): trung bình F1 của 6 lớp, mỗi lớp có trọng số như
  nhau, nên lớp ít mẫu (như OS Command Injection) không bị lấn át.
- FPR Normal (false positive rate): tỷ lệ request Normal bị báo nhầm là tấn công.

Dự đoán lỗi (LLM trả sai định dạng, API lỗi) được ghi là `None` và LUÔN tính
là sai, không bị loại ra khỏi mẫu số.
"""

import math
import random

import numpy as np

INVALID = "__INVALID_OR_ERROR__"


def confusion(y_true, y_pred, labels):
    """Ma trận nhầm lẫn: dòng = nhãn thật, cột = nhãn đoán (+1 cột cho lỗi)."""
    index = {label: i for i, label in enumerate(labels)}
    matrix = np.zeros((len(labels), len(labels) + 1), dtype=int)
    for truth, pred in zip(y_true, y_pred, strict=True):
        matrix[index[truth], index.get(pred, len(labels))] += 1
    return matrix


def classification_metrics(y_true, y_pred, labels):
    matrix = confusion(y_true, y_pred, labels)
    per_class = {}
    for i, label in enumerate(labels):
        tp, support, predicted = matrix[i, i], matrix[i].sum(), matrix[:, i].sum()
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"precision": float(precision), "recall": float(recall), "f1": float(f1),
                            "support": int(support)}
    n = len(y_true)
    present = [label for label in labels if per_class[label]["support"] > 0]
    result = {
        "n": n,
        "accuracy": float(np.trace(matrix[:, :len(labels)]) / n) if n else 0.0,
        "macro_f1": float(np.mean([per_class[label]["f1"] for label in present])) if present else 0.0,
        "weighted_f1": float(sum(per_class[l]["f1"] * per_class[l]["support"] for l in labels) / n) if n else 0.0,
        "coverage": float(sum(p in labels for p in y_pred) / n) if n else 0.0,
        "per_class": per_class,
        "confusion_matrix": {"rows": list(labels), "columns": [*labels, INVALID], "counts": matrix.tolist()},
    }
    if "NORMAL" in labels:
        normal = labels.index("NORMAL")
        normal_total = matrix[normal].sum()
        # Normal bị đoán thành một lớp tấn công (không tính dự đoán lỗi).
        attacked = normal_total - matrix[normal, normal] - matrix[normal, len(labels)]
        result["normal_false_positive_rate"] = float(attacked / normal_total) if normal_total else None
    return result


def macro_f1(y_true, y_pred, labels):
    return classification_metrics(y_true, y_pred, labels)["macro_f1"]


def paired_bootstrap(y_true, pred_a, pred_b, labels, n_resamples=2000, seed=42, groups=None):
    """Khoảng tin cậy 95% cho chênh lệch Macro-F1 (A − B) trên CÙNG bộ query.

    Mỗi lần lặp: rút ngẫu nhiên có hoàn lại n query (hoặc n nhóm nếu truyền
    `groups`), tính Macro-F1 của A và B trên mẫu đó rồi lấy hiệu. Lặp 2.000 lần
    được phân phối của chênh lệch. Nếu cả khoảng [2,5%; 97,5%] nằm trên 0 thì
    A tốt hơn B một cách đáng tin.
    """
    rng = random.Random(seed)
    n = len(y_true)
    if groups is None:
        units = [[i] for i in range(n)]
    else:
        by_group = {}
        for i, g in enumerate(groups):
            by_group.setdefault(g, []).append(i)
        units = list(by_group.values())
    diffs = []
    for _ in range(n_resamples):
        idx = [i for _ in units for i in units[rng.randrange(len(units))]]
        t = [y_true[i] for i in idx]
        diffs.append(macro_f1(t, [pred_a[i] for i in idx], labels) - macro_f1(t, [pred_b[i] for i in idx], labels))
    diffs.sort()
    observed = macro_f1(y_true, pred_a, labels) - macro_f1(y_true, pred_b, labels)
    return {"observed_diff": observed,
            "ci95": [diffs[int(0.025 * n_resamples)], diffs[int(0.975 * n_resamples) - 1]],
            "p_diff_le_0": sum(d <= 0 for d in diffs) / n_resamples,
            "n_resamples": n_resamples, "unit": "query" if groups is None else "group"}


def mcnemar(y_true, pred_a, pred_b):
    """Kiểm định McNemar (bản chính xác, nhị thức) cho hai hệ thống trên cùng query.

    Chỉ xét các query mà đúng/sai KHÁC nhau:
    - b = số query A đúng còn B sai; c = số query A sai còn B đúng.
    Nếu A và B ngang nhau thì b ≈ c. p-value nhỏ (< 0,05) nghĩa là chênh lệch
    khó do ngẫu nhiên.
    """
    b = sum(a == t and p != t for t, a, p in zip(y_true, pred_a, pred_b))
    c = sum(a != t and p == t for t, a, p in zip(y_true, pred_a, pred_b))
    n = b + c
    if n == 0:
        return {"a_only_correct": 0, "b_only_correct": 0, "p_value": 1.0}
    tail = sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n
    return {"a_only_correct": b, "b_only_correct": c, "p_value": min(1.0, 2 * tail)}


def label_consistency_rate(demo_labels, query_label):
    """LCR@k: tỷ lệ ví dụ mẫu có cùng nhãn với query (chỉ tính khi đánh giá offline)."""
    return sum(label == query_label for label in demo_labels) / len(demo_labels) if demo_labels else None
