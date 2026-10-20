"""Biến mỗi HTTP request thành một vector số (embedding).

Ý tưởng: hai request "giống nhau" sẽ có vector gần nhau. Độ gần được đo bằng
cosine similarity, nằm trong khoảng [-1, 1]; càng gần 1 thì càng giống.

Nhóm dùng model có sẵn (pretrained) của thư viện sentence-transformers và
KHÔNG huấn luyện lại (inference-only). Vector được chuẩn hóa về độ dài 1, nên
cosine similarity chỉ là tích vô hướng (dot product), tính rất nhanh bằng numpy.
"""

import numpy as np

from .views import embedding_view

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class SentenceTransformerEncoder:
    """Bọc model sentence-transformers.

    - `model_name`: tên model trên Hugging Face, tải tự động lần đầu (~90 MB).
    - `max_seq_length`: số token tối đa model đọc; phần dư bị bỏ qua. Vì vậy
      `embedding_view` đưa uri/body lên đầu.
    """

    def __init__(self, model_name=DEFAULT_MODEL, max_seq_length=256, batch_size=64, device="cpu"):
        from sentence_transformers import SentenceTransformer  # import muộn để test không cần thư viện này

        self.name = model_name
        self.model = SentenceTransformer(model_name, device=device)
        self.model.max_seq_length = max_seq_length
        self.batch_size = batch_size
        self.max_seq_length = max_seq_length

    def describe(self):
        return {"encoder": "sentence-transformers", "model": self.name,
                "max_seq_length": self.max_seq_length, "view": "embedding_view-v1"}

    def encode(self, texts):
        vectors = self.model.encode(list(texts), batch_size=self.batch_size, show_progress_bar=len(texts) > 500,
                                    convert_to_numpy=True, normalize_embeddings=True)
        return vectors.astype(np.float32)


def encode_requests(encoder, rows):
    """Encode danh sách bản ghi dữ liệu (dict có `request_text`).

    Lưu ý: hàm chỉ đọc `request_text`, không bao giờ đọc nhãn `label`.
    """
    return encoder.encode([embedding_view(row["request_text"]) for row in rows])


def normalize(matrix):
    """Chuẩn hóa từng dòng về độ dài 1 (an toàn với vector toàn số 0)."""
    matrix = np.asarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms
