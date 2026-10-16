# 📑 BÁO CÁO TIẾN ĐỘ NGHIÊN CỨU (WEEKLY PROGRESS REPORT)

> **Họ và tên sinh viên:** [Họ và tên của bạn]  
> **Giảng viên hướng dẫn:** [Tên Giảng viên hướng dẫn]  
> **Đề tài:** Truy Hồi Nhận Biết Nhãn cho Phát Hiện Tấn Công Web Dựa Trên Mô Hình Ngôn Ngữ Lớn  
> *(Label-Aware Retrieval for LLM-Based Web Attack Detection)*  
> **Thời gian báo cáo:** Tuần [X] — Tháng 09/2026  

---

## 1. TỔNG QUAN ĐỀ TÀI & VẤN ĐỀ CỐT LÕI (CONTEXT & RESEARCH PROBLEM)

### 🎯 Mục tiêu nghiên cứu
Đề tài nghiên cứu giải pháp **In-Context Learning (ICL) kết hợp RAG** để phát hiện và phân loại các cuộc tấn công ứng dụng Web (SQLi, Path Traversal, Code Injection,...) từ các HTTP request.

### ❓ Vấn đề kỹ thuật cần giải quyết (Core Problem)
- **Hạn chế của Semantic Retrieval thông thường (Vanilla RAG):** Khi tìm kiếm các ví dụ mẫu (demonstrations) từ cơ sở dữ liệu dựa thuần túy vào khoảng cách vector ngữ nghĩa (Cosine Similarity), hệ thống dễ bị **"nhiễm nhãn sai" (Label Contamination)**.
- *Ví dụ thực tế:* Một HTTP request bình thường (Benign) có chứa cú pháp tìm kiếm `/search?q=select+from+users` có biểu diễn embedding rất gần với một payload tấn công SQL Injection thực sự. Nếu retriever kéo nhầm mẫu Benign gán vào prompt phân loại SQLi, LLM sẽ bị nhiễu ngữ cảnh và suy giảm độ chính xác nghiêm trọng.

### 💡 Giải pháp đề xuất (Proposed Method)
- Đề xuất cơ chế **Label-Aware Retrieval**: Dùng chính **LLM zero-shot** (inference only, không train) để dự đoán nhãn sơ bộ (`ŷ_prior`), kết hợp thuật toán **Reranking / Filtering** để đảm bảo các demonstrations được chọn vào prompt vừa có ngữ nghĩa tương đồng, vừa **chuẩn xác về mặt nhãn** trước khi đưa vào LLM. **Không train bất kỳ model nào.**

---

## 2. KẾT QUẢ ĐÃ THỰC HIỆN ĐƯỢC (COMPLETED WORK)

### ✅ Task 1: Khảo sát tài liệu có hệ thống & Xác nhận khoảng trống nghiên cứu (Research Gap)
- Đã khảo sát và lập bảng đối sánh chi tiết **11 công trình liên quan** (CyberRAG, Detection-to-Response, CLL-RetICL, BFAD, DemoShapley, Kang et al. 2024...).
- **Xác nhận Research Gap:** Các nghiên cứu trước hoặc chỉ tập trung sinh báo cáo (CyberRAG), hoặc dùng cho mã nguồn WebShell (BFAD), hoặc NLP tổng quát (CLL-RetICL). Chưa có công trình nào thực hiện **nghiên cứu thực nghiệm có kiểm soát (Ablation study)** để so sánh trực tiếp *Vanilla vs. Label-Aware Retrieval* trên HTTP payload attacks và sử dụng chỉ số **Label Consistency Rate ($\text{LCR@}k$)** để định lượng chất lượng retrieval.

### ✅ Task 2: Hoàn thiện Đề cương & Thiết kế kiến trúc 3 Pipeline thực nghiệm
Đã chuẩn hóa thiết kế thực nghiệm gồm 3 pipeline chạy trên cùng một tập Test Set:
1. **Pipeline A (Baseline):** LLM Zero-shot / Fixed Few-shot (không dùng retrieval).
2. **Pipeline B (Standard RAG):** Standard Semantic Retrieval (FAISS Cosine Top-$k$) + LLM.
3. **Pipeline C (Proposed):** Fast Prior Classifier + Label-Aware Scoring/Reranking + LLM.

### ✅ Task 3: Phân tích thăm dò dữ liệu sơ bộ (Initial Dataset EDA)
- Đã phân tích dataset `data_capec_multilabel.csv` (907k rows log HTTP gán nhãn CAPEC):
  - *Tín hiệu tích cực:* 99% dữ liệu là single-label; phát hiện được **~1,430 URL paths có cùng cú pháp nhưng khác nhãn (Hard Cases)** — đây là minh chứng thực nghiệm sống động chứng minh sự cần thiết của cơ chế Label-Aware.
  - *Thách thức cần xử lý:* Dữ liệu lặp lại cao (61.4% duplicate paths) và mất cân bằng lớp $\to$ Cần quy trình lọc sạch và khảo sát thêm các nguồn dataset chuẩn khác.

### ✅ Task 4: Xây dựng Kế hoạch thực thi toàn diện (Master Checklist A – Z)
- Đã đóng gói lộ trình thực hiện gồm 6 giai đoạn rõ ràng: *Chuẩn bị $\to$ Khảo sát/Tuyển chọn Dataset $\to$ Tiền xử lý & Split $\to$ Cài đặt Pipeline $\to$ Benchmark & Ablation $\to$ Phân tích Hard Cases $\to$ Viết Khóa luận*.

---

## 3. KẾ HOẠCH DỰ KIẾN TRONG TUẦN TỚI (NEXT STEPS)

| STT | Nhiệm vụ cụ thể | Sản phẩm / Kết quả mong đợi |
| :---: | :--- | :--- |
| **1** | **Khảo sát & Chốt Dataset chính thức** | So sánh đối sánh 3 ứng viên (`data_capec`, `CSIC 2010`, `CIC-IDS Web Attack subset`) theo ma trận tiêu chí để chốt bộ dữ liệu chuẩn mực nhất. |
| **2** | **Xây dựng Script Tiền xử lý & Data Splitting** | Thực hiện Deduplication đa tầng, phân tầng nhãn $5 - 6$ classes, chia tách tập **Retrieval Database Pool (80%)** và **Test Set (20%)** độc lập chống data leakage. |
| **3** | **Cài đặt Pipeline A & Pipeline B cơ sở** | Dựng Vector DB (FAISS), kết nối LLM local (Ollama `qwen2.5:7b-instruct` hoặc `llama3.1:8b-instruct`), chạy thử nghiệm phân loại trên 100 mẫu đầu tiên. |
| **4** | **Thiết kế LLM Zero-shot Prior Module (Pipeline C, Thành phần 1)** | Cài đặt module gọi LLM zero-shot để lấy `ŷ_prior`, tích hợp vào công thức reranking. **Không train model** — chỉ dùng LLM inference (Ollama local hoặc Gemini Flash free API). |

---

## 4. VẤN ĐỀ CẦN XIN Ý KIẾN THẦY / CÔ (QUESTIONS FOR ADVISOR)

1. **Về phạm vi Attack Taxonomy:** Em dự kiến thu hẹp bài toán vào $5 - 6$ lớp tấn công phổ biến nhất (Benign, SQL Injection, Path Traversal, Code Injection, HTTP Response Splitting, OS Command Injection) để đảm bảo mẫu dữ liệu sạch và phân bố đồng đều. Thầy/Cô thấy phạm vi này đã đủ bao quát cho khóa luận chưa ạ?
2. **Về phương án Dataset:** Em đang cân nhắc giữa:
   - *Phương án 1:* Dùng bộ log HTTP thực tế lớn (`data_capec` sau khi khử trùng lặp kỹ lưỡng).
   - *Phương án 2:* Kết hợp bộ log thực tế làm tập huấn luyện/retrieval và dùng thêm bộ benchmark kinh điển (`CSIC 2010`) để kiểm thử khả năng tổng quát hóa (Out-of-Distribution).
3. **Về chỉ số đánh giá mới:** Đề tài dự kiến đưa thêm chỉ số **$\text{LCR@}k$ (Label Consistency Rate @ $k$)** để đo trực tiếp tỷ lệ mẫu đúng nhãn được retriever lấy về làm đóng góp chính về mặt đo lường retrieval. Thầy/Cô có góp ý thêm về công thức hay cách đánh giá này không ạ?

---
*Tài liệu đính kèm:* [Bảng tổng hợp 11 Papers liên quan](file:///d:/PERSONAL/Research/ITP/src/link_papers.md) | [Kế hoạch thực thi A-Z](file:///d:/PERSONAL/Research/ITP/src/mini-reports/checklist_thuc_thi_nghien_cuu.md)
