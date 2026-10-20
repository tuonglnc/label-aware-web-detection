"""kNN vote: đoán nhãn bằng cách "hỏi k hàng xóm gần nhất".

Cách làm:
1. Lấy k ứng viên giống query nhất (đã có sẵn từ bước retrieval của B).
2. Mỗi hàng xóm "bỏ phiếu" cho nhãn của nó.
   - `weighted=True`: phiếu nặng bằng độ giống (similarity), hàng xóm càng
     giống thì tiếng nói càng lớn.
   - `weighted=False`: mỗi hàng xóm 1 phiếu (đa số đơn giản).
3. Nhãn nhiều phiếu nhất thắng. Nếu hòa, chọn nhãn của hàng xóm giống nhất
   trong số các nhãn đang hòa.

Không gọi LLM, không cần huấn luyện. Dùng cho hai việc:
- Làm baseline: LLM phải vượt được mức này mới chứng tỏ có giá trị.
- Làm "prior" cho Pipeline C thay cho LLM zero-shot (rẻ hơn 1 lần gọi LLM).
"""

from collections import defaultdict


def knn_vote(candidates, k, weighted=True):
    """`candidates`: danh sách Candidate đã sắp xếp giảm dần theo similarity.

    Trả về (nhãn dự đoán, dict điểm từng nhãn). Danh sách rỗng trả về (None, {}).
    """
    neighbors = candidates[:k]
    if not neighbors:
        return None, {}
    scores = defaultdict(float)
    best_rank = {}
    for position, cand in enumerate(neighbors):
        scores[cand["label"]] += max(cand["similarity"], 0.0) if weighted else 1.0
        best_rank.setdefault(cand["label"], position)
    # Sắp xếp: điểm cao trước; hòa điểm thì nhãn có hàng xóm đứng trước thắng.
    winner = min(scores, key=lambda label: (-round(scores[label], 9), best_rank[label]))
    return winner, {label: round(score, 6) for label, score in scores.items()}
