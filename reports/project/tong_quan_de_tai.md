# Tổng quan đề tài: Label-Aware Retrieval for LLM-Based Web Attack Detection

Đề tài dùng **In-Context Learning (ICL)**: đưa cho **Large Language Model (LLM)** vài **demonstrations** (ví dụ có nhãn) rồi yêu cầu phân loại một **HTTP request** mới thành Normal hoặc một loại **Web Attack**.

**Câu hỏi nghiên cứu:** chọn demonstrations có xét đến nhãn (**label-aware**) có cải thiện chất lượng phân loại so với **Standard Semantic Retrieval**, vốn chỉ dựa trên **embedding similarity**, hay không?

Kết quả thực nghiệm và cách chạy nằm ở [README của repo](../../README.md). Tài liệu này giải thích ý tưởng và thiết kế thí nghiệm.

## 1. Ý tưởng

Nhiều HTTP request có cùng endpoint, cấu trúc và phần lớn token nhưng khác nhãn. Ví dụ: một request Normal và một request SQL Injection chỉ khác nhau chuỗi `+AND+1%3D1` trong URI ([cặp minh họa](../dataset/khao_sat_sr_bh_2020.md)). Vì vậy, ví dụ giống nhất về nội dung chưa chắc có nhãn hữu ích cho request đang xét.

Ý tưởng label-aware: trước tiên đoán sơ bộ nhãn của request (**prior**), rồi ưu tiên các ứng viên có nhãn khớp với prior khi chọn ví dụ. Nhãn thật của request cần phân loại **không bao giờ** được dùng để chọn ví dụ; chỉ dùng để đánh giá. Ngoại lệ duy nhất là C-oracle, được đánh dấu rõ là "chỉ để phân tích".

## 2. Thiết kế thí nghiệm

Mọi pipeline dùng chung một LLM, một khung prompt và cùng số ví dụ k = 4. Chỉ cách chọn ví dụ khác nhau, nên chênh lệch kết quả là do cách chọn ví dụ.

| Pipeline | Cách chọn ví dụ | Câu hỏi trả lời |
| --- | --- | --- |
| kNN vote | Không gọi LLM, bỏ phiếu nhãn của 5 láng giềng | Retrieval đơn thuần làm được tới đâu? |
| A0 | Zero-shot | LLM tự biết tới đâu? |
| A1 | 4 ví dụ cố định | Có ví dụ đã đủ, hay ví dụ phải liên quan? |
| B | Top-4 theo similarity | Baseline retrieval |
| BAL | Từ top-30, lấy luân phiên theo lớp | Cân bằng nhãn có giúp không? |
| C | Từ top-30, `score = similarity + λ·1[nhãn ứng viên = prior]`, λ = 0,1 | Label-aware rerank có giúp không? |
| C-oracle | Như C, prior = nhãn thật | Mức trần nếu prior luôn đúng |

Luồng của pipeline C:

```text
HTTP request
    ├── Embedding + tìm kiếm ngữ nghĩa ──> 30 ứng viên có nhãn (từ pool)
    └── kNN vote hoặc LLM zero-shot ────> prior
                                              │
                    Ứng viên + prior ─────────┘
                              │
                    Xếp lại theo similarity và nhãn
                              │
                    4 ví dụ ──> prompt ──> LLM ──> nhãn dự đoán
```

Cấu hình đã khóa trước khi chạy test (model, prompt, k, λ, N, pool, giả thuyết đăng ký trước): [cau_hinh_khoa.md](../experiments/cau_hinh_khoa.md).

## 3. Đánh giá

- **Macro-F1** (chỉ số chính), Accuracy, Precision/Recall/F1 theo lớp, **FPR của lớp Normal** (tỷ lệ báo động nhầm).
- **Label Consistency Rate@k (LCR@k):** tỷ lệ ví dụ được chọn có cùng nhãn với nhãn thật của request. LCR cao chưa chắc giúp phân loại tốt hơn, nên luôn đọc cùng Macro-F1.
- So sánh từng cặp pipeline trên cùng các request: **paired bootstrap** (khoảng tin cậy 95% của chênh lệch Macro-F1) và **McNemar**.
- Tách theo prior đúng/sai: C sửa được bao nhiêu lỗi của B, làm hỏng bao nhiêu câu B đúng.
- Chi phí: số lượt gọi LLM và số token mỗi request.

## 4. Dữ liệu

**SR-BH 2020** (Harvard Dataverse, CC0): 907.815 bản ghi HTTP, 38 cột, 14 nhãn (Normal và 13 nhóm tấn công CAPEC), định dạng multi-label.

Xử lý:

- Chỉ giữ bản ghi có đúng một nhãn thuộc 6 lớp: Normal, SQL Injection, Path Traversal, Code Injection, HTTP Response Splitting, OS Command Injection.
- Cách ly các request trùng nội dung nhưng mâu thuẫn nhãn, rồi bỏ trùng. Còn **466.267 request**.
- Chia theo nhóm 70/15/15 (seed 42) để các request gần giống nhau không rơi vào hai tập khác nhau.

Chi tiết: [huong_dan_xu_ly_du_lieu.md](../dataset/huong_dan_xu_ly_du_lieu.md), [ket_qua_xu_ly_du_lieu.md](../dataset/ket_qua_xu_ly_du_lieu.md). Giới hạn quan trọng: nhiều request mang nhãn Normal nhưng chứa payload tấn công (nhiễu nhãn); xem [quyet_dinh_dataset.md](../dataset/quyet_dinh_dataset.md).

Hai notebook khảo sát dữ liệu ban đầu: [sr_bh_2020_khao_sat.ipynb](../../src/notebooks/sr_bh_2020_khao_sat.ipynb), [sr_bh_eda.ipynb](../../src/notebooks/sr_bh_eda.ipynb). Notebook cần file `data_capec_multilabel.csv` trong `src/data/raw/` và các thư viện pandas, matplotlib, seaborn, jupyterlab. Output lưu trong notebook là của lần chạy khảo sát đầu tiên.

## 5. Công nghệ

- Embedding: Sentence Transformers `all-MiniLM-L6-v2`; tìm kiếm bằng tích vô hướng trên numpy (pool nhỏ nên không cần FAISS).
- LLM: Groq API (tương thích OpenAI), `openai/gpt-oss-20b`; kiểm tra thêm với `openai/gpt-oss-120b`.
- Python ≥ 3.10; kiểm thử bằng `unittest`.

Tài liệu tham khảo: [link_papers.md](../references/link_papers.md).
