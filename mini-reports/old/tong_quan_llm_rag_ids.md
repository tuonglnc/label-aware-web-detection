# Báo Cáo Tổng Quan: Kiến Trúc LLM/Transformer, Mô Hình RAG và Hệ Thống Phát Hiện Xâm Nhập Mạng (IDS)

Báo cáo tổng hợp lý thuyết nền tảng về **Transformer/LLM**, cơ chế **Retrieval-Augmented Generation (RAG)** và phân tích so sánh các phương pháp **Phát hiện Xâm nhập Mạng (Rule-Based vs ML-Based IDS)**.

---

## 1. Nguyên Lý Hoạt Động Của Mô Hình Ngôn Ngữ Lớn (LLM) Và Kiến Trúc Transformer

Các **Mô hình Ngôn ngữ Lớn (LLMs)** hiện đại dựa trên kiến trúc **Transformer** (Vaswani et al., 2017). Nguyên lý xử lý thông tin được thực hiện qua các giai đoạn kỹ thuật chính:

### a. Mã hóa Từ vựng và Nhúng Vector (Tokenization & Embedding)
* Văn bản đầu vào được phân tách thành các đơn vị rời rạc gọi là **Tokens** (từ, từ phụ hoặc ký tự).
* Mỗi Token được ánh toán vào không gian không gian nhiều chiều để tạo thành **Vector Nhúng (Word/Token Embedding)** biểu diễn thông tin cú pháp và ngữ nghĩa ban đầu.
* **Mã hóa Vị trí (Positional Encoding)** được cộng vào vector nhúng để duy trì thông tin thứ tự tuần tự của các token trong chuỗi.

### b. Cơ chế Tự Chú Ý Đa Đầu (Multi-Head Self-Attention)
* Cơ chế Self-Attention cho phép mô hình tính toán mối quan hệ phụ thuộc giữa mọi cặp token trong chuỗi đầu vào mà không phụ thuộc vào khoảng cách vị trí.
* Cho một ma trận đầu vào, mô hình tính toán 3 ma trận chiếu: **Query ($Q$)**, **Key ($K$)**, và **Value ($V$)**. Trọng số chú ý được tính theo công thức Scaled Dot-Product Attention:

  Attention(Q, K, V) = Softmax( (Q * K^T) / sqrt(d_k) ) * V

* **Multi-Head Attention** cho phép mô hình đồng thời học các mối quan hệ ngữ nghĩa ở nhiều không gian biểu diễn khác nhau.

### c. Dự đoán Token Tiếp theo (Autoregressive Next-Token Prediction)
* Sau khi đi qua các lớp Transformer bao gồm Self-Attention và Feed-Forward Neural Networks (FFN), lớp đầu ra Softmax tính toán phân bố xác suất trên toàn bộ từ vựng ($V$).
* Mô hình tiến hành chọn lọc token có xác suất tối ưu và lặp lại quá trình này theo cơ chế tự hồi quy (Autoregressive) để tạo ra chuỗi văn bản hoàn chỉnh.

---

## 2. Mô Hình RAG (Retrieval-Augmented Generation) Và Các Vấn Đề Kỹ Thuật Được Giải Quyết

### a. Định nghĩa Kiến trúc RAG
**Retrieval-Augmented Generation (RAG)** là mô hình kết hợp giữa **Bộ truy xuất tri thức (Retriever)** và **Bộ sinh ngôn ngữ (Generator)**:
1. **Retriever**: Sử dụng phương pháp truy xuất từ vựng (BM25) hoặc truy xuất ngữ nghĩa dense vector (FAISS, ChromaDB) để trích xuất các đoạn văn bản (chunks) có độ liên quan cao nhất từ một Cơ sở Tri thức bên ngoài (External Knowledge Base).
2. **Generator**: Sử dụng LLM để tổng hợp thông tin được trích xuất từ Retriever và câu hỏi đầu vào nhằm tạo ra câu trả lời cuối cùng.

```
[User Query] 
     │
     ▼
 ┌───────────┐        ┌───────────────────────────────┐
 │ Retriever │ ───►  │ Relevant Knowledge Chunks (D) │
 └───────────┘        └───────────────────────────────┘
       │                              │
       └──────────────┬───────────────┘
                      ▼
            ┌───────────────────┐
            │   LLM Generator   │
            └───────────────────┘
                      │
                      ▼
            [Grounded Response]
```

### b. Các vấn đề kỹ thuật của LLM đơn lẻ được giải quyết bởi RAG

| Vấn đề của LLM thuần (Vanilla LLM) | Cơ chế khắc phục của RAG |
|---|---|
| **Hiện tượng Ảo giác (Hallucination)**: Mô hình tự sinh thông tin sai thực tế do bản chất dự đoán xác suất ngẫu nhiên. | **Gắn kết Thực nghiệm (Factual Grounding)**: RAG buộc LLM chỉ tổng hợp câu trả lời dựa trên bằng chứng minh thị được trích xuất từ dữ liệu nguồn đáng tin cậy. |
| **Giới hạn Thời gian Dữ liệu (Temporal Knowledge Cutoff)**: Kiến thức của LLM bị cố định tại thời điểm kết thúc huấn luyện. | **Cập nhật Tri thức Động (Dynamic Knowledge Update)**: Cho phép cập nhật thông tin mới nhất bằng cách bổ sung dữ liệu vào Knowledge Base mà không cần tái huấn luyện (Fine-tuning) LLM. |
| **Thiếu Kiến thức Chuyên ngành / Nội bộ**: LLM không có quyền truy cập vào dữ liệu riêng của tổ chức hoặc tài liệu kỹ thuật hẹp. | **Tích hợp Cơ sở Tri thức Chuyên biệt (Domain-Specific KB)**: Cho phép nạp các tập tài liệu chuẩn mực (NIST, MITRE ATT&CK, RFC, ISO) làm ngữ cảnh trực tiếp. |
| **Thiếu Tính Thẩm định (Verifiability)**: Không thể truy xuất nguồn gốc của thông tin được sinh ra. | **Trích dẫn Nguồn Nguồn (Source Attribution & Citations)**: RAG cung cấp tham chiếu chính xác đến đoạn văn bản, tài liệu và mục tương ứng. |

---

## 3. Phân Biệt Các Hệ Thống Phát Hiện Xâm Nhập Mạng (Rule-Based vs ML-Based IDS)

Hệ thống Phát hiện Xâm nhập Mạng (**IDS**) được phân loại dựa trên cơ chế phân tích lưu lượng:

```
                          HỆ THỐNG IDS
                               │
         ┌─────────────────────┴─────────────────────┐
         ▼                                           ▼
Rule-Based / Signature-Based             ML-Based / DL-Based
(Snort, Suricata, RegEx)              (Random Forest, DNN, CNN-LSTM)
```

### So Sánh Chi Tiết Phương Pháp:

| Tiêu chí phân tích | IDS Dựa trên Quy tắc / Chữ ký (Rule-Based) | IDS Dựa trên Học máy (ML/DL-Based) |
|---|---|---|
| **Cơ chế phân tích** | So khớp lưu lượng mạng với tập quy tắc (Rules) hoặc dấu hiệu (Signatures) được thiết lập cố định bởi chuyên gia. | Học các đặc trưng thống kê và mối quan hệ phi tuyến từ dữ liệu lịch sử để thiết lập ranh giới quyết định (Decision Boundaries). |
| **Khả năng phát hiện Tấn công Mới (Zero-Day)** | **Hạn chế**: Không thể phát hiện các dạng tấn công chưa có chữ ký trong cơ sở dữ liệu. | **Tốt**: Có khả năng tổng quát hóa (Generalization) để nhận diện các biến thể hoặc dạng bất thường mới. |
| **Độ chính xác với mẫu đã biết** | **Rất cao**: Tỷ lệ báo động giả cực thấp đối với các chuỗi chữ ký đã được định nghĩa chuẩn xác. | Phụ thuộc vào phân bố dữ liệu huấn luyện, có xác suất phát sinh âm tính/dương tính giả. |
| **Tính Giải thích (Explainability)** | **Minh bạch**: Xác định rõ quy tắc vi phạm và trường dữ liệu liên quan. | **Hộp đen (Black-box)**: Khó giải thích cơ chế ra quyết định của các tham số ẩn trong mạng nơ-ron. |

### Đánh Giá Ưu Điểm Và Hạn Chế Kỹ Thuật:

#### 1. IDS Rule-Based (Ví dụ: Snort, Suricata):
* **Ưu điểm**:
  * Tốc độ tính toán cao, chi phí tài nguyên phần cứng thấp.
  * Tỷ lệ dương tính giả (False Positive) rất thấp đối với các mối đe dọa đã biết.
  * Logic vận hành rõ ràng, thuận tiện cho việc kiểm toán và quản trị hệ thống.
* **Hạn chế**:
  * Đòi hỏi chi phí nhân lực cao để duy trì và viết lại quy tắc cho các lỗ hổng mới.
  * Dễ bị vượt qua bởi các kỹ thuật xáo trộn mã (Obfuscation) hoặc mã hóa lưu lượng.
  * Không có khả năng tự thích ứng với các mối đe dọa Zero-Day.

#### 2. IDS ML/DL-Based (Ví dụ: Random Forest, DNN, CNN-LSTM):
* **Ưu điểm**:
  * Khả năng phát hiện các dạng tấn công biến thể phức tạp và hành vi tấn công Zero-Day.
  * Tự động trích xuất đặc trưng (Feature Extraction) từ dữ liệu lưu lượng mạng nhiều chiều.
  * Thích ứng tốt với việc phân tích chuỗi hành vi bất thường theo thời gian.
* **Hạn chế**:
  * Tỷ lệ dương tính giả (False Positive) có thể cao, gây ra hiện tượng quá tải cảnh báo (Alert Fatigue) trong SOC.
  * Nhạy cảm với sự mất cân bằng dữ liệu (Class Imbalance) và hiện tượng dịch chuyển phân bố dữ liệu (Data Drift).
  * Đòi hỏi tài nguyên tính toán lớn cho quá trình huấn luyện và yêu cầu các phương pháp XAI (SHAP, LIME) để giải thích mô hình.
