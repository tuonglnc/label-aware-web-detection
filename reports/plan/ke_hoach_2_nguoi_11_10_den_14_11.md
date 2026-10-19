# Kế hoạch 2 người: 11/10 – 14/11/2026

**Đề tài:** Label-Aware Retrieval for LLM-Based Web Attack Detection
**Sản phẩm cuối (14/11):** repo chạy lại được từ đầu đến cuối và cuốn báo cáo nộp khoa.
**Mốc giữa kỳ:** báo cáo giữa kỳ nộp thầy, dự kiến cuối tháng 10 (ngày cụ thể theo khoa).
**Ngày lập:** 19/10/2026. Giai đoạn 11–19/10 đã qua, được ghi lại theo thực tế để báo cáo cho trung thực.

> Kế hoạch này thay cho các bản ngày 16/10 và 19/10 ở cùng thư mục. Những bản đó giữ lại làm lịch sử.

## 0. Quyết định đã chốt

- Giữ nguyên ý tưởng gốc: chọn ví dụ có tính đến nhãn, dùng prior để xếp hạng lại (Pipeline C).
- **Thêm kNN vote** làm baseline không dùng LLM, đồng thời làm một nguồn prior cho C. **Không làm TF-IDF.**
- Một dataset (SR-BH 2020, 6 lớp), một embedding model (all-MiniLM-L6-v2), một LLM: Groq `openai/gpt-oss-20b`, temperature 0, `reasoning_effort` low.
- **Giữ gói Groq miễn phí** (quyết định ngày 19/10, sau khi đo thực tế: khoảng 200.000 token/ngày/key, 8.000 token/phút, 1.000 request/ngày). Để vừa quota:
  - dùng **key của cả hai thành viên**, luân phiên tự động (`.env`, `.env.tv2`);
  - **k = 4** ví dụ, mỗi ví dụ **cắt ở 500 ký tự** (khoảng 1.300 token mỗi request, thay vì 2.600);
  - **chỉ chạy bộ chính**: A0, B, BAL, C prior kNN, C prior LLM, với **λ = 0,1** cố định trước. C-oracle và A1 chỉ chạy nếu còn quota. Không chạy ablation λ bằng LLM; thay bằng bảng quét λ offline (không tốn API) trong `eval_retrieval`;
  - **test 300 mẫu** (300 mẫu đầu của `test_subset.jsonl`, đúng 50/lớp), cố định trước khi xem kết quả.
- Lý do chọn λ = 0,1: độ chênh similarity giữa ứng viên số 1 và số 30 có trung vị 0,075, nên λ = 0,1 đủ đưa hầu hết ứng viên trùng prior lên trước, nhưng không hoàn toàn là lọc cứng.

## 1. Phân vai

| Người | Phụ trách chính | Phần báo cáo |
| --- | --- | --- |
| **TV1** | Dữ liệu, nhãn, retrieval, kNN, reranker C, phân tích retrieval | Chương Dữ liệu, Phương pháp (retrieval), phân tích case |
| **TV2** | API LLM, chạy các pipeline, metrics, thống kê, bảng/hình | Chương Thực nghiệm, Kết quả, Tổng quan nghiên cứu |
| **Cả hai** | Review nhãn, đọc hiểu toàn bộ code, review chéo, viết Mở đầu/Kết luận, slide | Review chéo toàn bộ báo cáo |

Giả định mỗi người 15–20 giờ/tuần. Hằng ngày cập nhật 10 phút: đã xong gì, vướng gì, làm gì tiếp.

**Lưu ý quan trọng:** code đã được viết sẵn (xem mục 6). Phần việc còn lại của nhóm chủ yếu là **đọc hiểu code, chạy thực nghiệm thật, review nhãn, phân tích và viết**. Cả hai phải giải thích được mọi module, vì hội đồng sẽ hỏi.

## 2. Giai đoạn 0 — 11/10 đến 15/10: Khởi động lại (đã qua)

| Việc | Thực tế |
| --- | --- |
| Rà soát đề tài, đọc paper (KATE, EPR, CLL-RetICL, ICL Noisy Labels, DemoShapley, CyberRAG) | Đã có danh mục papers và mô tả đề tài |
| Lập kế hoạch, mô tả đề tài | Đã có, nhưng nhiều bản viết rồi xóa, chưa có code |
| Nhìn nhận | Chậm khoảng 6 tuần, cần trao đổi thẳng với thầy |

## 3. Tuần 1 — 16/10 đến 25/10: Dữ liệu, baseline, chạy validation

| Ngày | TV1 | TV2 | Trạng thái / đầu ra |
| --- | --- | --- | --- |
| 16–19/10 | Tải SR-BH, preprocessing, bỏ trùng, chia tập theo nhóm, kiểm tra leakage, khảo sát | Pipeline A0, kiểm thử, smoke API | **Đã xong:** 466.267 request, split v1 |
| 19/10 | — | — | **Đã xong:** sửa lỗi 403, chạy được trên Windows, code đầy đủ (55 test), RQ1 + kNN thật, **A0 thật trên validation: Macro-F1 0,835** |
| 20/10 | Trình bày dữ liệu, cặp request 99,5%, vấn đề nhãn | Trình bày RQ, pipeline, kết quả A0/kNN, kế hoạch | Báo cáo hướng đi với thầy, ghi lại quyết định |
| 20/10 | Tạo key Groq của mình, lưu vào `.env.tv2` ở máy chạy | Kiểm tra key của mình trong `.env` | Hai key đều liệt kê được model `openai/gpt-oss-20b` |
| 20–22/10 | Đọc hiểu `src/retrieval/`, `eval_retrieval.py` theo hướng dẫn | **Mỗi ngày chạy `bash src/experiments/run_suite.sh validation`** đến khi hết quota cả hai key | B, BAL, C_knn, C_llm đủ 200 query (khoảng 1,1 triệu token, ~3 ngày) |
| 22–23/10 | **Review nhãn:** hai người đọc độc lập 60 mẫu (10/lớp) trong `manual_review.jsonl`, ghi bất đồng | (như TV1) | Bảng đồng thuận + quyết định xử lý nhãn với thầy |
| 23–25/10 | Viết chương Dữ liệu và Phương pháp | Nếu còn quota: `EXTRA=1 bash src/experiments/run_suite.sh validation` (C-oracle, A1) | Bản nháp 2 chương; run tùy chọn |

**Điều kiện xong tuần 1:** đủ 5 run bộ chính trên validation, có quyết định về nhãn.

## 4. Tuần 2 — 26/10 đến 01/11: Phân tích validation, báo cáo giữa kỳ, khóa cấu hình

| Ngày | TV1 | TV2 | Đầu ra |
| --- | --- | --- | --- |
| 26/10 | Kiểm tra log retrieval: chọn 5–10 query điển hình (B lấy ví dụ khác nhãn, C làm hỏng khi prior sai) | `python -m src.analysis.compare --split validation ...` | `comparison.md`: Macro-F1, bootstrap, McNemar, bảng prior đúng/sai |
| 27/10 | Phân tích bảng prior đúng/sai, bảng quét λ | Viết Kết quả validation (bảng, thống kê, chi phí) | Kết quả validation trong báo cáo |
| **28/10** | Ghi `reports/protocol/cau_hinh_khoa.md`: commit hash, config, model, 300 mẫu test | Review và ký nhận cùng TV1 | **Khóa cấu hình**, không sửa code/prompt/k/λ sau mốc này |
| 28/10 | `build_retrieval --include-test` | — | Neighbors cho test |
| 29–31/10 | Viết Thảo luận, Hạn chế | **Mỗi ngày chạy `bash src/experiments/run_suite.sh test --locked`** | Bắt đầu chạy test (cần ~4–5 ngày quota) |
| 31/10 | Cả hai review, nộp **báo cáo giữa kỳ** (dựng bằng `reports/word/build_bao_cao_giua_ky.py`) | | Báo cáo giữa kỳ |

## 5. Tuần 3 — 02/11 đến 08/11: Hoàn tất test và phân tích

| Ngày | TV1 | TV2 | Đầu ra |
| --- | --- | --- | --- |
| 01–03/11 | Giám sát lỗi, kiểm tra log retrieval trên test | Tiếp tục `run_suite.sh test --locked` mỗi ngày | Đủ 300 query cho A0, B, BAL, C_knn, C_llm |
| 04/11 | kNN trên test: `eval_retrieval --split test` | `compare --split test` | Bảng kết quả cuối |
| 05–08/11 | Phân tích lỗi theo lớp, prior sai, ví dụ cụ thể | Bảng/hình cuối, kiểm định | Bộ kết quả cuối; 07–08/11 là thời gian dự phòng nếu quota chậm |

## 6. Tuần 4 — 09/11 đến 14/11: Viết báo cáo và đóng gói

| Ngày | TV1 | TV2 | Đầu ra |
| --- | --- | --- | --- |
| 09–10/11 | Hoàn thiện Dữ liệu, Phương pháp, Thảo luận, Hạn chế | Hoàn thiện Tổng quan, Thực nghiệm, Kết quả | Bản thảo đầy đủ |
| 11/11 | Chạy lại toàn bộ từ README trên máy sạch (kiểm tra tái lập) | Kiểm tra mọi số trong báo cáo khớp với file kết quả | Danh sách sửa |
| 12/11 | Gửi thầy bản thảo | | Góp ý của thầy |
| 13/11 | Sửa theo góp ý; slide | Sửa theo góp ý; xuất PDF | Bản cuối |
| **14/11** | **Nộp báo cáo + link repo** | | |

## 7. Mốc quyết định

| Mốc | Điều kiện | Nếu không đạt |
| --- | --- | --- |
| 20/10 | Có key thứ hai (`.env.tv2`) | Chạy bằng một key: validation mất khoảng 6 ngày, lùi ngày khóa cấu hình |
| 22/10 | Đủ 5 run bộ chính trên validation | Ưu tiên B, BAL, C_knn; C_llm chạy sau |
| 23/10 | Quyết định cách xử lý nhãn nhiễu | Giữ nhãn gốc, ghi rõ hạn chế |
| 28/10 | Đã khóa cấu hình | Không chạy test cho đến khi khóa |
| 04/11 | Đủ kết quả test 300 mẫu | Báo phần thiếu (ghi rõ số query đã chạy), không thay bằng số ước tính |

## 8. Ngân sách API (gói miễn phí, 2 key)

Số đo thật: A0 khoảng 640 token/request; pipeline có ví dụ (k = 4, cắt 500 ký tự) khoảng 1.360 token/request. Mỗi key khoảng 200.000 token/ngày, nên hai key được khoảng 400.000 token/ngày.

| Phần việc | Token | Ngày (2 key) |
| --- | ---: | ---: |
| Validation: A0 | đã xong (~128.000) | — |
| Validation: B, BAL, C_knn, C_llm (4 × 200 × 1.360) | ~1,09 triệu | ~3 |
| Validation tùy chọn: C-oracle, A1 | ~0,54 triệu | ~1,5 |
| Test 300: A0 (300 × 640) + 4 pipeline (4 × 300 × 1.360) | ~1,82 triệu | ~4,5 |
| **Tổng bộ chính** | **~2,9 triệu** | **~7,5** |

- Giới hạn 8.000 token/phút khiến mỗi pipeline có ví dụ chạy khoảng 5–6 request/phút; runner tự chờ theo `retry-after`.
- Khi hết quota ngày, runner tự dừng gọn, không ghi lỗi; chạy lại đúng lệnh hôm sau để tiếp tục.
- Không tự tạo nhiều tài khoản cho một người; mỗi thành viên dùng đúng tài khoản của mình.

## 9. Danh sách kiểm tra cuối (14/11)

- [ ] `python -m unittest discover -s src/tests` đạt toàn bộ.
- [ ] README có đủ lệnh chạy lại từ tải dữ liệu đến bảng kết quả.
- [ ] Kết quả test của A0, B, BAL, C_knn, C_llm và kNN trên cùng 300 query, có cấu hình đã khóa.
- [ ] Bảng Macro-F1, F1 từng lớp, FPR Normal, bootstrap CI, McNemar, chi phí.
- [ ] Bảng prior đúng/sai, bảng quét λ offline, phân tích lỗi (C-oracle nếu đã chạy).
- [ ] Báo cáo đủ chương, mọi số liệu truy được về file trong `src/artifacts/`.
- [ ] Phần Hạn chế: một dataset, nhãn nhiễu, endpoint chồng lấn, chỉ offline, quy mô thí nghiệm bị giới hạn bởi quota miễn phí (k = 4, test 300).
