"""Thông tin tính sẵn trên pool cho các cách chọn ví dụ cải tiến.

Ba thứ, đều chỉ dùng pool (không đụng tới query hay nhãn của query):

1. **ENN – Edited Nearest Neighbor** (Wilson, IEEE Trans. SMC, 1972): một ví dụ
   pool bị đánh dấu "nghi nhiễu nhãn" nếu luật kNN (k = 3 láng giềng gần nhất
   trong pool, không tính chính nó) đoán ra nhãn khác nhãn của nó. Nhãn của
   SR-BH có nhiễu (xem phân tích nhãn Normal), mà ví dụ sai nhãn trong prompt
   làm LLM sai theo (Kang và cộng sự, 2024), nên bỏ các ví dụ này khỏi ứng viên.

2. **Số hạng nhãn của CLL-RetICL** (Lin và cộng sự, 2025, phương trình 2):

       term(s_i) = log( exp(sim(s_i, y_i)) / mean_{y ≠ y_i} exp(sim(s_i, y)) )

   với `sim(s_i, y)` là cosine giữa embedding của ví dụ và embedding của TÊN
   nhãn y ("SQL Injection", ...). Bài gốc dùng cùng encoder MiniLM và cosine.

3. **Cosine giữa hai ví dụ pool**, cần cho MMR (`PoolSpace.pair_similarity`).
"""

from collections import Counter
import json
import math
from pathlib import Path

import numpy as np

from .embedding import normalize

# Tên nhãn dạng ngôn ngữ tự nhiên ("linguistic label") dùng cho CLL-RetICL.
LABEL_WORDS = {
    "NORMAL": "Normal",
    "SQL_INJECTION": "SQL Injection",
    "PATH_TRAVERSAL": "Path Traversal",
    "CODE_INJECTION": "Code Injection",
    "HTTP_RESPONSE_SPLITTING": "HTTP Response Splitting",
    "OS_COMMAND_INJECTION": "OS Command Injection",
}
AUX_FILE = "pool_aux.json"


class PoolSpace:
    """Vector của pool (đã chuẩn hóa) kèm id và nhãn, đọc từ thư mục retrieval."""

    def __init__(self, ids, labels, vectors):
        self.ids = list(ids)
        self.labels = list(labels)
        self.vectors = normalize(vectors)
        self.index = {rid: i for i, rid in enumerate(self.ids)}

    @classmethod
    def load(cls, retrieval_dir):
        retrieval_dir = Path(retrieval_dir)
        meta = [json.loads(line) for line in
                (retrieval_dir / "pool_meta.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        return cls([m["request_id"] for m in meta], [m["label"] for m in meta],
                   np.load(retrieval_dir / "pool_vectors.npy"))

    def pair_similarity(self, id_a, id_b):
        return float(self.vectors[self.index[id_a]] @ self.vectors[self.index[id_b]])


def enn_flags(space, k=3):
    """Danh sách id bị Wilson-ENN đánh dấu (nhãn khác dự đoán kNN của các láng giềng trong pool).

    Bỏ phiếu đa số không trọng số như bài gốc; nếu hòa (ví dụ 3 nhãn khác nhau),
    lấy nhãn của láng giềng gần nhất trong số các nhãn hòa.
    """
    sims = space.vectors @ space.vectors.T
    np.fill_diagonal(sims, -np.inf)
    flagged = []
    for i, rid in enumerate(space.ids):
        top = sorted(np.argpartition(-sims[i], k)[:k], key=lambda j: (-float(sims[i, j]), space.ids[j]))
        votes = Counter(space.labels[j] for j in top)
        best = max(votes.values())
        winner = next(space.labels[j] for j in top if votes[space.labels[j]] == best)
        if winner != space.labels[i]:
            flagged.append(rid)
    return sorted(flagged)


def cll_label_terms(space, label_vectors):
    """term(s_i) của CLL-RetICL cho mọi ví dụ pool; `label_vectors`: {nhãn: vector đã chuẩn hóa}."""
    labels = list(label_vectors)
    matrix = normalize(np.stack([label_vectors[label] for label in labels]))
    sims = space.vectors @ matrix.T  # (pool, số nhãn)
    terms = {}
    for i, rid in enumerate(space.ids):
        own = labels.index(space.labels[i])
        others = [float(sims[i, j]) for j in range(len(labels)) if j != own]
        mean_exp = sum(math.exp(s) for s in others) / len(others)
        terms[rid] = round(float(sims[i, own]) - math.log(mean_exp), 6)
    return terms


def load_aux(retrieval_dir):
    path = Path(retrieval_dir) / AUX_FILE
    if not path.exists():
        raise ValueError(f"{path} not found; build it with python -m src.experiments.build_pool_aux")
    return json.loads(path.read_text(encoding="utf-8"))
