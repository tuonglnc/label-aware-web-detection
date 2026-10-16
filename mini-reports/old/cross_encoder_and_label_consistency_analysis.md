# Phân Tích Kỹ Thuật: Cross-Encoder Reranking Và Tính Nhất Quán Nhãn (Label Consistency)

Báo cáo trả lời 2 câu hỏi nghiên cứu dựa trên bài báo: **"From Detection to Response: A Deep Learning and Retrieval-Augmented Generation Framework for Network Intrusion Mitigation"** (Islam & Saha, arXiv:2605.17960).

---

## CÂU HỎI 1: Họ dùng Cross-Encoder Reranking thế nào?

### 🎯 Mục đích ngắn gọn
Cross-Encoder Reranking nằm ở **Stage 4 (Hybrid RAG Pipeline)**. Mục đích là để **đánh giá lại và chọn lọc chính xác Top-5 đoạn tri thức (chunks) tốt nhất** từ tập 20–30 đoạn ứng viên sơ bộ trước khi đưa vào LLM sinh báo cáo.

---

### ⚙️ Cách thức hoạt động theo 3 bước trực quan

```
 [ Query Expanded ] ──┬──► BM25 (Từ khóa)     ──────┐
                      │                             ├─► Fusion Score ──► Top 20-30 ──► [ CROSS-ENCODER ] ──► Top 5 Chunks
                      └──► FAISS (Ý nghĩa Vector) ──┘    (60% + 40%)     Ứng viên        (ms-marco-MiniLM)
```

#### Bước 1: Lọc ứng viên sơ bộ (Hybrid Search & Score Fusion)
* Kết hợp 2 phương pháp tìm kiếm:
  * **BM25**: Tìm theo từ khóa chính xác.
  * **FAISS + `all-mpnet-base-v2`**: Tìm theo ý nghĩa vector (Dense Semantic Search).
* Trộn điểm số tìm kiếm theo tỷ lệ 60/40:
  
  Score_fusion(D, Q) = 0.60 * Sim_sem(D, Q) + 0.40 * Score_BM25(D, Q)

* Trích ra danh sách **Top 20–30 chunks ứng viên** có điểm cao nhất.

#### Bước 2: Chấm điểm lại chi tiết bằng Cross-Encoder (Cross-Encoder Reranking)
* Mô hình sử dụng: **`ms-marco-MiniLM-L-6-v2`**.
* **Điểm khác biệt cốt lõi so với FAISS (Bi-Encoder)**:
  * FAISS mã hóa Query và Document thành 2 vector riêng biệt rồi mới so sánh (không cho từ trong Query tương tác với từ trong Document).
  * **Cross-Encoder ghép trực tiếp Query và Document thành 1 chuỗi duy nhất**:
    
    Input = [CLS] + Query + [SEP] + Document + [SEP]

  * Khi đi qua các lớp Transformer, cơ chế **Self-Attention** cho phép **mọi từ trong Query chú ý (attend) trực tiếp đến mọi từ trong Document**. Nhờ đó, mô hình bắt được sự tương tác ngữ nghĩa mịn (fine-grained interactions) mà FAISS bỏ sót.
* Cross-Encoder chấm điểm độ liên quan s_rr trong khoảng [0, 1] cho từng ứng viên, sau đó sắp xếp lại và trích chọn **Top-5 chunks có điểm cao nhất**.

#### Bước 3: Cơ chế dự phòng kiểm soát chất lượng (Quality Fallback)
* Nếu sau khi rerank, số lượng chunks đạt điểm s_rr > 0.5 **ít hơn 3 chunks**, hệ thống sẽ tự động chèn thêm ngữ cảnh chuẩn từ **NIST SP 800-61** (nguyên tắc ứng phó sự cố chung) để đảm bảo LLM không bị thiếu thông tin.

---

## CÂU HỎI 2: Họ có xét tính nhất quán nhãn (Label Consistency) không?

### 🎯 Trả lời trực diện
**CÓ XÉT, nhưng được thực hiện một cách GIÁN TIẾP (implicit) thông qua việc nhúng nhãn vào Query, chứ KHÔNG dùng bộ lọc cứng (hard filter) hay chỉ số đo đạc nhất quán nhãn riêng.**

---

### 💡 Giải thích chi tiết & Trực quan nhất về Câu 2

#### 1. "Nhất quán nhãn" (Label Consistency) là gì trong ngữ cảnh bài này?
Giả sử mô hình Phân loại ở **Stage 2 (DNN)** phán đoán gói tin mạng này là **`DoS`** (Từ chối dịch vụ).
* **Nhất quán nhãn**: Bước RAG ở **Stage 4** phải tìm đúng các tài liệu hướng dẫn khắc phục **`DoS`**, chứ **không được lấy nhầm** sang tài liệu của `DDoS` hay `SQL Injection`.

#### 2. Tác giả ĐÃ LÀM gì để xử lý việc này? (Cơ chế Gián tiếp - Implicit Mechanism)
Tác giả xử lý bằng cách **chèn chữ nhãn vào câu hỏi**:
* **Bước A (Dán nhãn tài liệu)**: Trong CSDL 5,234 đoạn tri thức (chunks), mỗi đoạn được dán sẵn thẻ thông tin metadata (ví dụ: `traffic relevance label = DoS`).
* **Bước B (Ghép nhãn vào Query)**: Khi mô hình DNN đoán ra `attack_class = DoS`, tác giả **chèn luôn từ `DoS` vào chuỗi Query đầu vào**.
  *(Ví dụ Query: "Attack class: DoS | Anomalous features: Flow Bytes/s...")*.
* **Bước C (Khớp tự nhiên)**: Khi đem câu Query có chứa từ **`DoS`** đi tìm kiếm (BM25, FAISS, Cross-Encoder), thuật toán thấy từ `DoS` xuất hiện trong Query nên sẽ **tự động chấm điểm cao hơn** cho các đoạn tài liệu có chứa chữ hoặc metadata `DoS`.

=> **Tại sao gọi là GIÁN TIẾP?** 
Vì sự ưu tiên này dựa vào **xác suất chấm điểm** của bộ tìm kiếm, chứ hệ thống không có lệnh ép buộc 100%.

#### 3. Tác giả CHƯA LÀM gì (Hạn chế về mặt kiến trúc & Thực nghiệm)?

* **KHÔNG có Bộ lọc cứng (Hard Filter)**:
  * *Nếu có Bộ lọc cứng*: Hệ thống sẽ chạy lệnh `IF predicted_class == DoS THEN ONLY search in chunks WHERE label == DoS`. Lệnh này triệt tiêu 100% nguy cơ lấy nhầm nhãn khác.
  * *Trong bài báo*: Tác giả **không dùng bộ lọc cứng**, mà cho RAG tìm kiếm trên toàn bộ 5,234 chunks cùng lúc. 
  * *Rủi ro*: Nếu một đoạn tài liệu về `DDoS` chứa nhiều từ khóa về ngữ cảnh ("packet rate", "flooding") trùng với Query `DoS`, thuật toán vector/Cross-Encoder vẫn có thể chấm đoạn `DDoS` này điểm cao hơn đoạn `DoS` -> Dẫn đến **lấy nhầm tài liệu khác nhãn**.

* **KHÔNG có Chỉ số đo đạc nhất quán nhãn (Label Consistency Metric)**:
  * Trong toàn bộ phần đánh giá thực nghiệm (Section IV), tác giả chỉ đo:
    * Độ chính xác tìm kiếm: *Precision@5, Recall@5, MRR*.
    * Chất lượng văn bản sinh ra: *BERTScore, ROUGE, BLEU*.
  * Tác giả **không hề định nghĩa hay đo chỉ số "Tỷ lệ nhất quán nhãn" (Label Consistency Rate - LCR)** để kiểm tra xem trong số các chunks tìm về có mấy % khớp hoàn toàn nhãn với kết quả DNN.
