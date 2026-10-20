"""Các chiến lược chọn k demonstrations (ví dụ mẫu) đưa vào prompt.

Đây là phần cốt lõi của đề tài: mọi pipeline dùng CHUNG LLM, prompt và k,
chỉ khác nhau ở cách chọn ví dụ.

| Pipeline | Hàm                  | Cách chọn                                                   |
|----------|----------------------|-------------------------------------------------------------|
| A0       | (không có ví dụ)     | Zero-shot                                                   |
| A1       | `fixed_examples`     | Một bộ ví dụ cố định cho mọi query, chia đều các lớp        |
| B        | `semantic_top_k`     | k ứng viên giống nhất                                        |
| BAL      | `class_balanced`     | Từ top-N, lấy luân phiên theo lớp để các lớp đều có mặt      |
| C        | `label_aware_rerank` | Từ top-N, cộng điểm cho ứng viên có nhãn trùng prior         |

Công thức của C (label-aware reranking):

    score(d) = similarity(q, d) + λ · 1[label(d) == prior(q)]

- `prior(q)` là nhãn ĐOÁN TRƯỚC cho query q (từ LLM zero-shot, kNN vote, hoặc
  nhãn thật nếu chạy "oracle" chỉ để phân tích). Không bao giờ là nhãn thật
  trong thí nghiệm chính.
- λ = 0 thì C trùng hoàn toàn với B (dùng để kiểm tra code).
- λ lớn (ví dụ ≥ 1) thì mọi ứng viên trùng prior đứng trước ("lọc cứng").
- Nếu prior không có (LLM trả lỗi) thì C quay về thứ tự của B.
"""

from collections import defaultdict, deque
import random


def semantic_top_k(candidates, k):
    """Pipeline B: giữ nguyên thứ tự similarity, lấy k ứng viên đầu."""
    return [dict(c, score=c["similarity"]) for c in candidates[:k]]


def class_balanced(candidates, k):
    """Pipeline BAL (đối chứng cân bằng lớp).

    Quy tắc (cố định trước, không chỉnh theo kết quả):
    1. Gom ứng viên trong top-N theo nhãn, mỗi nhóm giữ thứ tự similarity.
    2. Xếp các lớp theo similarity cao nhất của lớp đó.
    3. Lấy luân phiên: mỗi vòng lấy 1 ứng viên tốt nhất còn lại của từng lớp,
       cho đến khi đủ k hoặc hết ứng viên.

    Ví dụ k = 4, top-N có 2 lớp thì mỗi lớp được 2 ví dụ, thay vì 4 ví dụ
    cùng một lớp như B có thể chọn.
    """
    by_label = defaultdict(deque)
    for cand in candidates:
        by_label[cand["label"]].append(cand)
    order = sorted(by_label, key=lambda label: by_label[label][0]["rank"])
    selected = []
    while len(selected) < k and any(by_label.values()):
        for label in order:
            if by_label[label] and len(selected) < k:
                cand = by_label[label].popleft()
                selected.append(dict(cand, score=cand["similarity"]))
    return selected


def label_aware_rerank(candidates, k, prior, lam):
    """Pipeline C: xếp hạng lại top-N theo công thức ở đầu file."""
    if prior is None or lam == 0:
        return semantic_top_k(candidates, k)
    rescored = [dict(c, score=round(c["similarity"] + (lam if c["label"] == prior else 0.0), 6))
                for c in candidates]
    # Điểm giảm dần; hòa điểm thì giữ thứ hạng similarity ban đầu.
    rescored.sort(key=lambda c: (-c["score"], c["rank"]))
    return rescored[:k]


def fixed_examples(pool_rows, k, seed, labels):
    """Pipeline A1: chọn MỘT bộ ví dụ dùng chung cho mọi query.

    Chia đều theo lớp (luân phiên theo thứ tự `labels`), ngẫu nhiên trong lớp
    với `seed` cố định, nên chạy lại vẫn ra đúng bộ ví dụ đó.
    """
    rng = random.Random(seed)
    by_label = {label: sorted((r for r in pool_rows if r["label"] == label), key=lambda r: r["request_id"])
                for label in labels}
    for rows in by_label.values():
        rng.shuffle(rows)
    selected = []
    while len(selected) < k and any(by_label.values()):
        for label in labels:
            if by_label[label] and len(selected) < k:
                row = by_label[label].pop()
                selected.append({"request_id": row["request_id"], "label": row["label"],
                                 "similarity": None, "rank": None, "score": None})
    return selected
