"""Kho ví dụ có nhãn (retrieval pool) và phép tìm kiếm top-N.

Pool chỉ có vài nghìn request nên không cần FAISS: nhân ma trận bằng numpy
là đủ nhanh và dễ hiểu hơn.

    similarity = query_vectors @ pool_vectors.T     # (số query, số pool)

Mỗi dòng của ma trận kết quả là độ giống giữa một query và mọi ví dụ trong
pool; lấy N giá trị lớn nhất là có top-N ứng viên.
"""

import json
from pathlib import Path

import numpy as np

from .embedding import normalize


class Candidate(dict):
    """Một ứng viên lấy từ pool: {"request_id", "label", "similarity", "rank"}.

    Dùng dict để ghi thẳng ra JSON log; `rank` bắt đầu từ 1 (giống nhất).
    """


class VectorIndex:
    def __init__(self, ids, labels, vectors):
        if len(ids) != len(labels) or len(ids) != len(vectors):
            raise ValueError("ids, labels and vectors must have the same length")
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate request_id in pool")
        self.ids = list(ids)
        self.labels = list(labels)
        self.vectors = normalize(vectors)

    def search(self, query_vectors, n):
        """Trả về, cho mỗi query, danh sách n Candidate giống nhất (giảm dần).

        Khi hai ứng viên có cùng similarity, ứng viên có request_id nhỏ hơn
        đứng trước, để kết quả luôn giống nhau giữa các lần chạy.
        """
        n = min(n, len(self.ids))
        sims = normalize(query_vectors) @ self.vectors.T
        results = []
        for row in sims:
            # argpartition lấy nhanh n phần tử lớn nhất (chưa sắp xếp)...
            top = np.argpartition(-row, n - 1)[:n] if n < len(row) else np.arange(len(row))
            # ...rồi sắp xếp: similarity giảm dần, hòa thì theo request_id.
            top = sorted(top, key=lambda i: (-float(row[i]), self.ids[i]))
            results.append([Candidate(request_id=self.ids[i], label=self.labels[i],
                                      similarity=round(float(row[i]), 6), rank=r + 1)
                            for r, i in enumerate(top)])
        return results

    def save(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        np.save(directory / "pool_vectors.npy", self.vectors)
        with (directory / "pool_meta.jsonl").open("w", encoding="utf-8") as stream:
            for rid, label in zip(self.ids, self.labels):
                stream.write(json.dumps({"request_id": rid, "label": label}) + "\n")

    @classmethod
    def load(cls, directory):
        directory = Path(directory)
        meta = [json.loads(line) for line in (directory / "pool_meta.jsonl").read_text(encoding="utf-8").splitlines()]
        vectors = np.load(directory / "pool_vectors.npy")
        return cls([m["request_id"] for m in meta], [m["label"] for m in meta], vectors)
