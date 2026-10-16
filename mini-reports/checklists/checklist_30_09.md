# ✅ CHECKLIST HÔM NAY — 30/09/2026 (Thứ Tư)

> **Bạn đang ở đâu?** Giai đoạn 0 (Setup) gần xong, Giai đoạn 1 (Khảo sát Dataset) đang dở dang.
> **Mục tiêu hôm nay:** Hoàn tất khảo sát dataset + bắt đầu setup môi trường code.

---

## 🧭 TÓM TẮT: BẠN ĐÃ LÀM ĐƯỢC GÌ RỒI?

| Việc | Trạng thái |
|:---|:---:|
| Khảo sát 11 bài báo, xác nhận Research Gap | ✅ Xong |
| Thiết kế 3 Pipeline (A, B, C) | ✅ Xong |
| Phân tích sơ bộ dataset CAPEC 907K dòng | ✅ Xong |
| Lập checklist tổng thể A-Z | ✅ Xong |
| Systematic search log (tìm thêm papers) | ✅ Xong |
| Viết báo cáo tiến độ + script trình bày | ✅ Xong |
| **Chốt dataset chính thức** | ❌ Chưa |
| **Setup môi trường Python + thư viện** | ❌ Chưa |
| **Code bất kỳ pipeline nào** | ❌ Chưa |

---

## 📋 VIỆC CẦN LÀM HÔM NAY (theo thứ tự)

### 🔴 Việc 0: Đọc kỹ lại 8 bài báo liên quan (~2–3 tiếng)

**Tại sao?** Bạn đã khảo sát sơ bộ 11 bài, nhưng chưa đọc kỹ chi tiết. Đọc kỹ giúp bạn:
- Hiểu rõ method của người ta làm gì → thiết kế Pipeline C tốt hơn
- Biết họ dùng dataset nào → giúp chọn dataset cho mình
- Viết Related Work (Chương 2 khóa luận) sẽ nhanh hơn nhiều

**Cụ thể làm gì — đọc từng bài, ghi lại 4 ý chính:**

> Mỗi bài chỉ cần ghi **4 dòng** vào file note, không cần viết dài.

- [ ] **0a. [5] CLL-RetICL** ⭐ *(Quan trọng nhất — cùng ý tưởng label-aware)*
  - Họ làm gì? (method)
  - Họ dùng dataset nào?
  - Kết quả chính (số liệu)?
  - Khác đề tài mình ở chỗ nào?

- [ ] **0b. [6] BFAD** ⭐ *(Closest competitor — cybersecurity + ICL)*
  - Họ làm gì? (3 components: Filter, Extraction, WBFP)
  - Họ dùng dataset nào?
  - Kết quả chính?
  - Khác mình: WebShell (PHP code) vs Web Attack (HTTP payload)

- [ ] **0c. [1] CyberRAG**
  - Method? Dataset? Kết quả? Khác mình?

- [ ] **0d. [2] Detection-to-Response**
  - Method? Dataset? Kết quả? Khác mình?

- [ ] **0e. [3] ICL Noisy Labels**
  - Method? Dataset? Kết quả? Khác mình?

- [ ] **0f. [4] DemoShapley**
  - Method? Dataset? Kết quả? Khác mình?

- [ ] **0g. [7] RDES** *(RL-based — đọc lướt, hiểu ý tưởng là đủ)*
  - Method? Kết quả? Tại sao quá phức tạp cho scope mình?

- [ ] **0h. [9] Comparative Analysis** *(Survey — đọc lướt)*
  - Họ so sánh những method nào? Kết luận chính?

- [ ] **0i.** Ghi note vào file → Lưu `mini-reports/p1_literature_review_notes.md`

**💡 Mẹo đọc nhanh:** Mỗi bài chỉ cần đọc **Abstract → Method (Section 3) → Experiments (bảng kết quả) → Conclusion**. Không cần đọc hết từ đầu tới cuối.

---

### 🔵 Việc 1: Khảo sát chi tiết 3 ứng viên dataset (~2 tiếng)

**Tại sao?** Bạn chưa chốt dùng dataset nào. Đây là bước **phải xong trước** mọi thứ khác.

**Cụ thể làm gì:**

- [ ] **1a.** Tải dataset **CSIC 2010** (từ Kaggle) về máy
  - Mở xem cấu trúc: có bao nhiêu dòng, mỗi dòng gồm gì, nhãn ra sao?
  - Ghi lại: Có đủ HTTP method, path, query params, body không?

- [ ] **1b.** Tải dataset **Web Application Payloads** (Kaggle) về máy
  - Kiểm tra tương tự: số dòng, nhãn (SQLi, XSS, SSRF...), chất lượng

- [ ] **1c.** Lập bảng so sánh 3 dataset theo 5 tiêu chí:

  | Tiêu chí | CAPEC (đã có) | CSIC 2010 | Web App Payloads |
  |:---|:---|:---|:---|
  | Số lượng mẫu | 907K | ? | ? |
  | Số loại tấn công | 13 | ? | ? |
  | Nhãn rõ ràng? | Có (CAPEC) | ? | ? |
  | Có HTTP đầy đủ? | Chỉ URL path | ? | ? |
  | Dễ chia train/test? | Khó (trùng lặp cao) | ? | ? |

- [ ] **1d.** Viết kết luận ngắn: **"Tôi chọn dataset X vì lý do Y"** → Lưu vào file `mini-reports/p1_dataset_selection_report.md`

---

### 🟢 Việc 2: Setup môi trường Python cơ bản (~30 phút)

**Tại sao?** Cần có môi trường sẵn sàng để tuần tới code Pipeline A, B ngay.

**Cụ thể làm gì:**

- [ ] **2a.** Tạo môi trường ảo (virtual environment):
  ```bash
  conda create -n itp python=3.10 -y
  conda activate itp
  ```

- [ ] **2b.** Cài các thư viện cơ bản (chưa cần LLM nặng):
  ```bash
  pip install pandas numpy scikit-learn matplotlib seaborn
  pip install faiss-cpu sentence-transformers
  ```

- [ ] **2c.** Kiểm tra nhanh: Mở Python, chạy `import pandas, faiss, sentence_transformers` không lỗi là OK

---

### 🟡 Việc 3: Tạo cấu trúc thư mục dự án (~15 phút)

**Tại sao?** Bạn cần chỗ để sắp xếp code sau này. Làm sớm, code sẽ gọn gàng.

**Cụ thể làm gì:**

- [ ] **3a.** Tạo các thư mục sau trong `src/`:
  ```
  src/
  ├── data/           ← Chứa dataset đã xử lý (parquet/jsonl)
  ├── retrieval/      ← Code vector search, FAISS index
  ├── llm/            ← Code gọi LLM, prompt templates
  ├── eval/           ← Code tính metrics (F1, Accuracy, LCR@k)
  ├── experiments/    ← Config file cho từng thí nghiệm
  └── notebooks/      ← Jupyter notebooks phân tích
  ```

- [ ] **3b.** Tạo file `requirements.txt` ghi lại các thư viện đã cài

---

### 🟠 Việc 4 (NẾU CÒN THỜI GIAN): EDA sơ bộ dataset mới tải (~1 tiếng)

**Tại sao?** Giúp bạn hiểu rõ hơn dataset trước khi quyết định chọn.

- [ ] **4a.** Mở notebook, load CSIC 2010 lên → xem 10 dòng đầu, đếm label
- [ ] **4b.** Mở notebook, load Web App Payloads → tương tự
- [ ] **4c.** So sánh nhanh với CAPEC: bộ nào sạch hơn, nhãn rõ hơn?

---

## 🚫 KHÔNG CẦN LÀM HÔM NAY

| Việc | Lý do chưa cần |
|:---|:---|
| Cài LLM (Qwen, Llama) | Chưa có dataset sạch → chạy LLM cũng vô nghĩa |
| Code Pipeline A, B, C | Phải có dataset + môi trường hoàn chỉnh trước đã |
| Viết khóa luận | Còn quá sớm, chưa có kết quả thực nghiệm |
| Huấn luyện Fast Classifier | Đây là giai đoạn 3, bạn mới ở giai đoạn 1 |

---

## 🎯 KẾT QUẢ MONG ĐỢI CUỐI NGÀY HÔM NAY

Nếu bạn hoàn thành Việc 0 + Việc 1 + Việc 2, bạn đã có:
1. ✅ **Note đọc paper** — hiểu rõ 8 bài, biết mình khác họ chỗ nào
2. ✅ **Biết rõ** mình sẽ dùng dataset nào (có lý do rõ ràng)
3. ✅ **Môi trường Python** sẵn sàng, chạy được các thư viện cơ bản
4. ✅ **Thư mục dự án** gọn gàng, sẵn sàng nhận code

→ **Tuần tới bạn có thể bắt tay code Pipeline A, B ngay lập tức** mà không bị kẹt ở khâu chuẩn bị nữa.
