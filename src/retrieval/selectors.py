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
| C-gated  | `gated_label_aware_rerank` | Như C khi prior kNN đủ tự tin, ngược lại dùng B          |
| B-MMR    | `mmr_select`         | Từ top-N, cân bằng độ giống query và độ đa dạng (MMR)        |
| B-CLL    | `label_term_rerank`  | Từ top-N, cộng điểm ví dụ "điển hình" cho nhãn của nó         |
| *-ENN    | `drop_flagged`       | Bỏ ví dụ pool có nhãn trái với láng giềng (Wilson, 1972)     |

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


def gated_label_aware_rerank(candidates, k, prior, lam, confidence, min_confidence):
    """Pipeline C-gated: chỉ dùng C khi prior đủ tự tin, còn lại quay về B.

    `confidence` là độ tự tin của prior (với prior kNN: `knn.vote_share`).
    Khi `confidence >= min_confidence` thì chọn như C; khi thấp hơn hoặc không
    có thì chọn như B. Lý do: C chủ yếu làm hỏng các câu mà prior sai, và prior
    hay sai đúng ở những query mà các hàng xóm bất đồng.
    """
    if confidence is None or confidence < min_confidence:
        return semantic_top_k(candidates, k)
    return label_aware_rerank(candidates, k, prior, lam)


def mmr_select(candidates, k, pair_similarity, lam=0.5):
    """Chọn k ví dụ bằng Maximal Marginal Relevance (MMR).

    Nguồn: Carbonell & Goldstein (SIGIR 1998); dùng cho chọn ví dụ ICL bởi
    Ye và cộng sự (Findings of ACL 2023, phương trình 1, λ = 0,5):

        chọn d = argmax  λ · sim(q, d) − (1 − λ) · max_{d' đã chọn} sim(d, d')

    Ý nghĩa: vẫn ưu tiên ví dụ giống query, nhưng phạt ví dụ trùng lặp với ví
    dụ đã chọn, để 4 ví dụ đa dạng hơn. `pair_similarity(id_a, id_b)` trả về
    cosine giữa hai ví dụ trong pool. λ = 1 thì trùng B.
    """
    remaining = list(candidates)
    selected = []
    while remaining and len(selected) < k:
        def mmr(cand):
            redundancy = max((pair_similarity(cand["request_id"], s["request_id"]) for s in selected), default=0.0)
            return lam * cand["similarity"] - (1 - lam) * redundancy
        best = max(remaining, key=lambda c: (round(mmr(c), 9), -c["rank"]))
        remaining.remove(best)
        selected.append(dict(best, score=round(mmr(best), 6)))
    return selected


def label_term_rerank(candidates, k, label_term, weight=1.0):
    """Xếp hạng lại theo CLL-RetICL (Lin và cộng sự, Findings of IJCNLP-AACL 2025, phương trình 2):

        score(s_i) = sim(q, s_i) + w1 · log( exp(sim(s_i, y_i)) / mean_{y ≠ y_i} exp(sim(s_i, y)) )

    Số hạng thứ hai chỉ phụ thuộc vào ví dụ s_i và nhãn của nó (không phụ thuộc
    query), nên được tính sẵn một lần cho cả pool (`label_term[request_id]`):
    ví dụ "giống tên nhãn của chính nó hơn các nhãn khác" được cộng điểm. Khác C,
    cách này KHÔNG cần đoán trước nhãn của query.
    """
    rescored = [dict(c, score=round(c["similarity"] + weight * label_term[c["request_id"]], 6)) for c in candidates]
    rescored.sort(key=lambda c: (-c["score"], c["rank"]))
    return rescored[:k]


def drop_flagged(candidates, flagged_ids):
    """Bỏ khỏi danh sách ứng viên các ví dụ pool bị đánh dấu nhiễu nhãn (giữ nguyên thứ tự)."""
    return [c for c in candidates if c["request_id"] not in flagged_ids]


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
