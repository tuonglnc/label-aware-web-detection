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
- **API:** từ 20/10 dùng **một tài khoản Groq gói trả theo mức dùng** (Developer tier), key trong `.env`. Điều khoản của Groq cấm vượt giới hạn bằng cách dùng nhiều tài khoản hoặc điều phối giữa nhiều tổ chức, nên **không dùng key của người khác**. Các run trước 20/10 chạy trên gói miễn phí (khoảng 200.000 token/ngày, 8.000 token/phút); cấu hình thí nghiệm giữ nguyên nên kết quả đã có vẫn dùng được.
- Cấu hình thí nghiệm (chốt 19/10, giữ nguyên khi chuyển gói để mọi run so sánh được với nhau):
  - **k = 4** ví dụ, mỗi ví dụ **cắt ở 500 ký tự** (khoảng 1.300 token mỗi request, thay vì 2.600);
  - **chỉ chạy bộ chính**: A0, B, BAL, C prior kNN, C prior LLM, với **λ = 0,1** cố định trước. C-oracle và A1 chạy thêm sau bộ chính (`EXTRA=1`). Không chạy ablation λ bằng LLM; thay bằng bảng quét λ offline (không tốn API) trong `eval_retrieval`;
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
| 20/10 | Nộp báo cáo giữa kỳ (Word/PDF, có kết quả tạm của B/BAL) | Nâng tài khoản Groq lên gói trả theo mức dùng; xóa `.env.tv2` | Một key duy nhất trong `.env` |
| 20–21/10 | Đọc hiểu `src/retrieval/`, `eval_retrieval.py` theo hướng dẫn | Chạy `bash src/experiments/run_suite.sh validation` rồi `EXTRA=1 bash src/experiments/run_suite.sh validation` | Đủ 200 query cho A0, B, BAL, C_knn, C_llm, C-oracle, A1 (vài giờ chạy) |
| 22–23/10 | **Review nhãn:** hai người đọc độc lập 60 mẫu (10/lớp) trong `manual_review.jsonl`, ghi bất đồng | (như TV1) | Bảng đồng thuận + quyết định xử lý nhãn với thầy |
| 22–25/10 | Viết chương Dữ liệu và Phương pháp; review các request Normal bị đoán sai | `compare` trên validation, bảng prior đúng/sai | Bản nháp 2 chương; kết quả validation đầy đủ |

**Điều kiện xong tuần 1:** đủ 5 run bộ chính trên validation, có quyết định về nhãn.

## 4. Tuần 2 — 26/10 đến 01/11: Phân tích validation, báo cáo giữa kỳ, khóa cấu hình

| Ngày | TV1 | TV2 | Đầu ra |
| --- | --- | --- | --- |
| 26/10 | Kiểm tra log retrieval: chọn 5–10 query điển hình (B lấy ví dụ khác nhãn, C làm hỏng khi prior sai) | `python -m src.analysis.compare --split validation ...` | `comparison.md`: Macro-F1, bootstrap, McNemar, bảng prior đúng/sai |
| 27/10 | Phân tích bảng prior đúng/sai, bảng quét λ | Viết Kết quả validation (bảng, thống kê, chi phí) | Kết quả validation trong báo cáo |
| **28/10** | Ghi `reports/protocol/cau_hinh_khoa.md`: commit hash, config, model, 300 mẫu test | Review và ký nhận cùng TV1 | **Khóa cấu hình**, không sửa code/prompt/k/λ sau mốc này |
| 28/10 | `build_retrieval --include-test` | — | Neighbors cho test |
| 29/10 | Viết Thảo luận, Hạn chế | Chạy `bash src/experiments/run_suite.sh test --locked` | Đủ 300 query test cho bộ chính (vài giờ chạy) |
| 30–31/10 | kNN trên test: `eval_retrieval --split test --limit 300` | `compare --split test` | Bảng kết quả cuối |

## 5. Tuần 3 — 02/11 đến 08/11: Hoàn tất test và phân tích

| Ngày | TV1 | TV2 | Đầu ra |
| --- | --- | --- | --- |
| 02–05/11 | Phân tích lỗi theo lớp, prior sai, nhãn nhiễu, ví dụ cụ thể | Bảng/hình cuối, kiểm định, chi phí | Bộ kết quả cuối |
| 06–08/11 | Dự phòng | Dự phòng | — |

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
| 20/10 | Tài khoản Groq đã nâng gói trả theo mức dùng | Chạy bằng gói miễn phí của một tài khoản (~200.000 token/ngày): validation ~4 ngày, test ~10 ngày, giảm test còn 240 mẫu |
| 21/10 | Đủ các run validation (bộ chính + C-oracle, A1) | Kiểm tra lỗi trong log, chạy lại đúng lệnh |
| 23/10 | Quyết định cách xử lý nhãn nhiễu | Giữ nhãn gốc, ghi rõ hạn chế |
| 28/10 | Đã khóa cấu hình | Không chạy test cho đến khi khóa |
| 31/10 | Đủ kết quả test 300 mẫu | Báo phần thiếu (ghi rõ số query đã chạy), không thay bằng số ước tính |

## 8. Ngân sách API (một tài khoản, gói trả theo mức dùng)

Số đo thật: A0 khoảng 640 token/request; pipeline có ví dụ (k = 4, cắt 500 ký tự) khoảng 1.490 token/request.

| Phần việc | Token (ước tính) |
| --- | ---: |
| Validation còn lại: B (43), BAL (51), C_knn (200), C_llm (200) | ~0,74 triệu |
| Validation thêm: C-oracle, A1 (2 × 200) | ~0,6 triệu |
| Test 300: A0 (300 × 640) + 4 pipeline (4 × 300 × 1.490) | ~2,0 triệu |
| **Tổng** | **~3,3 triệu** |

- Theo giá tham khảo khoảng 0,075 USD/1 triệu token đầu vào và 0,30 USD/1 triệu token đầu ra cho `openai/gpt-oss-20b` (kiểm tra lại trên console Groq), tổng chi phí **dưới 1 USD**.
- **Trần chi phí: 5 USD.** Hai lớp bảo vệ: (1) giới hạn chi tiêu trong console Groq (nếu có tùy chọn); (2) chốt ngân sách trong code (`src/configs/llm/budget.json`, ngưỡng 4,5 USD tính với giá gấp đôi), runner dừng trước khi có thể vượt ngưỡng.
- Runner vẫn tự chờ khi bị giới hạn theo phút, và dừng gọn nếu gặp giới hạn dài; chạy lại đúng lệnh để tiếp tục.
- Chỉ dùng một tài khoản, một key; không dùng key của người khác.

## 9. Danh sách kiểm tra cuối (14/11)

- [ ] `python -m unittest discover -s src/tests` đạt toàn bộ.
- [ ] README có đủ lệnh chạy lại từ tải dữ liệu đến bảng kết quả.
- [ ] Kết quả test của A0, B, BAL, C_knn, C_llm và kNN trên cùng 300 query, có cấu hình đã khóa.
- [ ] Bảng Macro-F1, F1 từng lớp, FPR Normal, bootstrap CI, McNemar, chi phí.
- [ ] Bảng prior đúng/sai, bảng quét λ offline, phân tích lỗi (C-oracle nếu đã chạy).
- [ ] Báo cáo đủ chương, mọi số liệu truy được về file trong `src/artifacts/`.
- [ ] Phần Hạn chế: một dataset, nhãn nhiễu, endpoint chồng lấn, chỉ offline, quy mô thí nghiệm (k = 4, ví dụ cắt 500 ký tự, test 300) được chốt khi còn dùng gói miễn phí.
