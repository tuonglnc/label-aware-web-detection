# Phân Tích Kỹ Thuật: Mục Đích Và Cơ Chế Vận Hành 5 Giai Đoạn (5 Stages) Trong Kiến Trúc IDS–RAG

Báo cáo phân tích chuyên sâu dựa trên bài báo nghiên cứu: **"From Detection to Response: A Deep Learning and Retrieval-Augmented Generation Framework for Network Intrusion Mitigation"** (Islam & Saha, 2026).

---

## Tổng Quan Kiến Trúc Khung (Overall Architecture)

Khung làm việc IDS–RAG được thiết kế gồm 5 giai đoạn nối tiếp nhau nhằm khép kín khoảng cách từ **Phát hiện đe dọa (Threat Detection)** đến **Khuyến nghị ứng phó sự cố (Actionable Response Generation)**.

```
 [ Raw Traffic ] ──► [ Stage 1: Preprocessing ] ──► [ Stage 2: Ensemble DNN Classifier ]
                                                                  │
 [ Structured Report ] ◄── [ Stage 5: LLaMA 3 ] ◄── [ Stage 4: Hybrid RAG + Cross-Reranker ] ◄── [ Stage 3: Prompt Construction ]
```

---

## Stage 1: Data Acquisition and Preprocessing (Thu Thập & Tiền Xử Lý Dữ Liệu)

* **Mục đích**: Chuyển đổi dữ liệu lưu lượng mạng thô (raw flow records) từ các tập dữ liệu benchmark khác nhau thành một **không gian đặc trưng biểu diễn đồng nhất 66 chiều**, phục vụ cho việc huấn luyện mô hình học sâu.
* **Cách thức hoạt động**:
  1. **Đồng nhất sơ đồ phân loại**: Áp dụng trên 2 bộ dữ liệu **CICIDS2018** (66 thuộc tính) và **UNSW-NB15** (49 thuộc tính). Chuẩn hóa các danh mục tấn công về sơ đồ 3 lớp: `Benign` (Lành tính), `DoS` (Từ chối dịch vụ đơn nguồn), `DDoS` (Từ chối dịch vụ phân tán). Bộ dữ liệu UNSW-NB15 được bổ sung đệm số 0 (Zero-padding) để mở rộng từ 49 lên 66 chiều.
  2. **Chuẩn hóa dữ liệu**: Các thuộc tính định danh (categorical) được mã hóa One-Hot. Các thuộc tính định lượng được áp dụng chuẩn hóa Z-score trên tập train:
     
     x_hat_j = (x_j - mu_j) / sigma_j

  3. **Xây dựng Từ điển Diễn giải Đặc trưng (Feature Interpretation Dictionary)**: Ánh xạ từng thuộc tính mạng thô (như `sttl`, `dload`, `Flow Bytes/s`) sang mô tả ngôn ngữ tự nhiên và ý nghĩa an ninh mạng (Security Implication).
  4. **Phân chia tập dữ liệu**: Phân chia theo phương pháp Stratified Split 70/15/15 (train/validation/test) để bảo toàn tỷ lệ các lớp.

---

## Stage 2: Confidence-Calibrated DNN Classification (Phân Loại & Hiệu Chỉnh Độ Tin Cậy)

* **Mục đích**: Phân loại luồng truy cập mạng với độ chính xác cao và tính toán điểm tin cậy (Confidence Score) được hiệu chỉnh phục vụ phân cấp xử lý sự cố trong SOC.
* **Cách thức hoạt động**:
  1. **Kiến trúc Ensemble (One-vs-Rest)**: Huấn luyện một **Ensemble gồm 3 mạng nơ-ron phân loại nhị phân (DNN) độc lập**: *Benign-vs-Rest*, *DoS-vs-Rest*, và *DDoS-vs-Rest*.
  2. **Xử lý mất cân bằng lớp (Class Imbalance)**: Với dữ liệu lệch nặng như UNSW-NB15 (DoS chỉ chiếm 0.64%), tác giả áp dụng hàm tổn thất trọng số nghịch đảo tần suất **Class-Weighted Binary Cross-Entropy Loss**:
     
     L_WBCE(y, y_hat) = - [ w1 * y * log(y_hat) + w0 * (1-y) * log(1-y_hat) ]
     
     với trọng số lớp: w_c = N / (2 * N_c). Kết hợp cùng Random Oversampling (tỷ lệ 1:5) và Controlled Undersampling.
  3. **Tổng hợp kết quả & Phân cấp độ tin cậy (Triage Tier)**:
     
     c_hat = argmax_c (p_c),   Confidence = max_c (p_c)

     Điểm tin cậy được quy đổi thành các cấp độ ưu tiên cho SOC: *Very High (>= 0.95)*, *High ([0.70, 0.95))*, *Medium ([0.50, 0.70))*, *Low (< 0.50)*.

---

## Stage 3: Explanation-Aware Prompt Construction (Xây Dựng Prompt Giàu Bằng Chứng)

* **Mục đích**: Trích xuất các bằng chứng kỹ thuật quan trọng nhất từ kết quả DNN để đóng gói thành một prompt có cấu trúc chuẩn, binding lý luận của LLM với bằng chứng thực tế.
* **Cách thức hoạt động**:
  1. **Trích chọn Top-5 đặc trưng ảnh hưởng nhất (Gradient-based Attribution)**: Tính toán độ ảnh hưởng của từng đặc trưng đầu vào tới quyết định phân loại:
     
     Importance(j) = | d(y_hat_c) / d(x_j) |

     Sắp xếp và trích chọn K = 5 đặc trưng có trọng số đạo hàm cao nhất.
  2. **Diễn giải đặc trưng**: Tra cứu 5 đặc trưng này qua *Feature Interpretation Dictionary* (từ Stage 1) để dịch thành chuỗi câu diễn giải tự nhiên (VD: `sttl = 245` -> *"Source TTL of 245 is elevated and irregular; may indicate packet spoofing..."*).
  3. **Tổ hợp cấu trúc Prompt**: Ghép 4 khối thông tin: *Detection Context* (Lớp dự đoán, điểm tin cậy), *Flow Metadata* (IP, Port, Protocol), *Anomalous Indicators* (Top-5 đặc trưng + diễn giải), và *Retrieved Knowledge* (sẽ nạp từ Stage 4).

---

## Stage 4: Hybrid RAG Retrieval Pipeline & Cross-Encoder Reranking (Truy Xuất Tri Thức)

* **Mục đích**: Tìm kiếm và trích chọn đúng **Top-5 đoạn tri thức uy tín nhất** (từ 5,234 semantic chunks trích xuất từ 14 tài liệu chuẩn như NIST SP 800-61, SP 800-94, MITRE ATT&CK T1498...) để cung cấp ngữ cảnh cho LLM.

### Sơ Đồ Tiến Trình Truy Xuất Hỗn Hợp & Reranking:

```
  [ Query Expanded ] ──┬──► BM25 (Lexical)   ──────┐
                       │                           ├─► Fusion Score ──► Top 20-30 ──► [ CROSS-ENCODER ] ──► Top 5 Chunks
                       └──► FAISS (Semantic) ──────┘    (60% + 40%)     Candidates      (ms-marco-MiniLM)
```

### Chi Tiết Kỹ Thuật 3 Bước Triển Khai:

#### 1. Chuẩn bị dữ liệu & Mở rộng truy vấn (Semantic Chunking & Query Expansion)
* Tài liệu an ninh mạng được cắt thành các chunks theo đơn vị ngữ nghĩa (overlap 200 tokens), đính kèm metadata (`traffic relevance label`, `NIST/MITRE reference`).
* Truy vấn đầu vào được mở rộng qua từ điển đồng nghĩa an ninh mạng (VD: `DoS` mở rộng thành *"denial of service"*, *"resource exhaustion"*, *"flooding"*).

#### 2. Tầng 1: Tìm kiếm hỗn hợp sơ bộ (Hybrid Retrieval & Score Fusion)
* **BM25 (Lexical Search)**: Đo độ liên quan dựa trên tần suất từ khóa chính xác ($k_1 = 1.5, b = 0.75$).
* **FAISS (Dense Semantic Search)**: Mã hóa chuỗi thành vector 768 chiều bằng `all-mpnet-base-v2` để đo Cosine Similarity (bắt ngữ nghĩa đồng nghĩa).
* **Dung hợp điểm số (Score Fusion)**:
  
  Score_fusion(D, Q) = 0.60 * Sim_sem(D, Q) + 0.40 * Score_BM25(D, Q)

* Trích chọn tập ứng viên sơ bộ $C_{30}$ gồm **Top 20–30 chunks tốt nhất**.

#### 3. Tầng 2: Cơ chế CROSS-ENCODER RERANKING (Trọng Tâm Kỹ Thuật)
* **Tại sao cần Cross-Encoder sau Bi-Encoder (FAISS)?**
  * Các mô hình Bi-Encoder (như FAISS) mã hóa Query $q$ và Chunk $d$ thành 2 vector riêng biệt $\mathbf{q}$ và $\mathbf{d}$ rồi mới tính Cosine Similarity. Phương pháp này có tốc độ truy xuất rất nhanh, nhưng nhược điểm là **Query và Document được biểu diễn hoàn toàn độc lập**, không có sự tương tác chéo ở cấp độ từ vựng trong quá trình tạo vector.
* **Cơ chế hoạt động của Cross-Encoder (`ms-marco-MiniLM-L-6-v2`)**:
  * Cross-Encoder nhận đầu vào là **một chuỗi ghép cặp trực tiếp** giữa Query và Chunk:
    
    Input = [CLS] + q + [SEP] + d + [SEP]

  * Chuỗi này được đưa qua các lớp Transformer. Lúc này, cơ chế **Full Cross Self-Attention** hoạt động: **mọi token trong Query $q$ được tính toán chú ý trực tiếp với tất cả các token trong Chunk $d$ ở mọi lớp ẩn**.
  * Nhờ tương tác từ-nối-từ (token-level interaction) mịn này, Cross-Encoder đánh giá được chính xác mức độ liên quan về ngữ cảnh mà Bi-Encoder bỏ sót.
* **Chấm điểm & Trích chọn**:
  * Cross-Encoder tính ra điểm số độ liên quan $s_{\text{rr}} \in [0, 1]$ cho từng cặp $(q, d)$ trong 20–30 ứng viên.
  * Hệ thống sắp xếp lại toàn bộ và trích ra **Top k = 5 chunks có điểm $s_{\text{rr}}$ cao nhất** ($C^*$).
* **Cơ chế Dự phòng (Quality Fallback Mechanism)**:
  * Nếu sau khi rerank, số lượng chunks đạt điểm $s_{\text{rr}} > 0.5$ ít hơn 3 chunks, hệ thống sẽ tự động chèn thêm tri thức dự phòng chuẩn từ **NIST SP 800-61** (về nguyên tắc ứng phó sự cố chung) để đảm bảo độ đầy đủ cho LLM.

---

## Stage 5: LLM-Based Report Generation (Sinh Báo Cáo Bằng LLM)

* **Mục đích**: Tổng hợp toàn bộ thông tin đã trích xuất thành một báo cáo ứng phó sự cố an ninh mạng có cấu trúc 5 phần chuẩn hóa cho các chuyên viên SOC.
* **Cách thức hoạt động**:
  1. Sử dụng mô hình **LLaMA 3:8B** (chạy cục bộ qua khung Ollama để đảm bảo an toàn dữ liệu lưu lượng mạng).
  2. LLM nhận Prompt từ Stage 3 (chứa kết quả DNN, 5 đặc trưng quan trọng, metadata gói tin và 5 tri thức chunks đã rerank từ Stage 4).
  3. Sinh ra báo cáo chuẩn hóa 5 phần cho SOC:
     * **1. Rationale**: Lý giải bản chất đe dọa, dẫn chiếu NIST SP & MITRE ATT&CK.
     * **2. Key Indicators**: Liệt kê 5 đặc trưng bất thường kèm giải thích ý nghĩa an ninh.
     * **3. Confidence Assessment**: Đánh giá độ tin cậy và cấp độ ưu tiên xử lý (Triage Tier).
     * **4. Threat Assessment**: Đánh giá tác động theo nguyên tắc rủi ro NIST SP 800-30.
     * **5. Recommendations**: Khuyến nghị các hành động khắc phục cụ thể trích từ Top-5 chunks (kèm trích dẫn nguồn).
