# Khóa cấu hình vòng cải tiến Pipeline C (trước khi chạy `test_fresh`)

Ngày khóa: 02/11/2026. File này được commit **trước** khi gọi LLM trên `test_fresh`. Không đổi phương pháp, tham số hay cách đánh giá sau khi xem kết quả test.

## 1. Tập đánh giá

- `test_fresh`: 300 request, 50/lớp, tạo bằng `python -m src.preprocessing.make_fresh_test` (seed `test_fresh-v1-42`).
- Lấy từ `test.jsonl`. Không trùng request, cũng không trùng `group_id`, với 600 request của `test_subset.jsonl`. Mỗi nhóm lấy tối đa 1 request. Không trùng nhóm với pool (đã kiểm tra: 0 nhóm chung).
- Danh sách id: `src/artifacts/data/test_fresh/request_ids.json`; mã băm trong `src/artifacts/data/test_fresh/manifest.json`.

## 2. Các run sẽ chạy (toàn bộ, không bỏ run nào sau khi xem kết quả)

| Nhóm | Cấu hình |
| --- | --- |
| Pipeline cũ | A0, A1_k4, B_k4, BAL_k4, C_knn_k4, C_llm_k4, C_oracle_k4 (chỉ phân tích); kNN vote (không LLM) |
| Cải tiến | C_gated_k4, B_mmr_k4, B_cll_k4, B_enn_k4, C_knn_enn_k4, C_iter_k4 |
| Gộp | ENS_vote_B_BAL_Cknn = đa số của B_k4, BAL_k4, C_knn_k4; hòa thì theo B |
| Đo dao động | B_k4 chạy lại lần 2 vào thư mục riêng (cùng prompt) |

Lệnh: `EXTRA=1 IMPROVE=1 bash src/experiments/run_suite.sh test_fresh --locked`, sau đó chạy ensemble, chạy lại B, kNN (`eval_retrieval --split test_fresh`) và `compare`.

## 3. Tham số đã chốt (không chỉnh trên test)

Chung cho mọi pipeline: `openai/gpt-oss-20b`, temperature 0, reasoning_effort low, k = 4, N = 30, mỗi ví dụ tối đa 500 ký tự, λ = 0,1 cho C.

| Phương pháp | Tham số | Lý do chọn |
| --- | --- | --- |
| C-gated | tỷ lệ phiếu kNN ≥ 0,7 | Đã khóa trên validation (`cau_hinh_khoa_c_gated.md`) |
| B-MMR | λ_MMR = 0,5 | Mặc định của Ye và cộng sự (2023) |
| B-CLL | w1 = 1,0 | Mặc định của Lin và cộng sự (2025) |
| ENN | k = 3, bỏ phiếu đa số | Wilson (1972); 724/3.000 ví dụ pool bị đánh dấu |
| C-iter | prior = nhãn do B trả về | IDS (Qin và cộng sự, 2024), rút gọn còn 2 vòng |
| ENS | B, BAL, C-kNN; hòa theo B | Chọn trước, đúng 3 run 1 lượt gọi có sẵn trong bộ chính |

## 4. Kết quả validation làm căn cứ (200 request)

| Run | Macro-F1 |
| --- | ---: |
| B (tham chiếu) | 0,893 |
| ENS | 0,893 |
| C-gated | 0,888 |
| C-kNN | 0,882 |
| B chạy lại lần 2 (cùng prompt) | 0,882 |
| C-iter | 0,868 |
| B-ENN | 0,869 |
| B-MMR | 0,857 |
| C-kNN-ENN | 0,849 |
| B-CLL | 0,809 |

Chạy lại B với **cùng prompt** cho 6/200 câu trả lời khác và Macro-F1 lệch 0,011: LLM không hoàn toàn tất định dù temperature = 0. Chênh lệch dưới khoảng 0,01 vì vậy không nên đọc như khác biệt thật.

## 5. Giả thuyết và cách đánh giá (ghi trước khi có dữ liệu)

- **Chỉ số chính:** Macro-F1 trên 300 request `test_fresh`. **Tham chiếu:** B_k4 (lần chạy chính).
- **Kiểm định:**
  - McNemar ghép cặp cho từng phương pháp so với B, hiệu chỉnh Holm cho 7 phép so (C-gated, B-MMR, B-CLL, B-ENN, C-kNN-ENN, C-iter, ENS), mức 0,05;
  - kèm khoảng tin cậy bootstrap 95% của chênh lệch Macro-F1.
- **H1:** Không phương pháp cải tiến nào vượt B có ý nghĩa thống kê sau hiệu chỉnh Holm. Căn cứ: không phương pháp nào vượt B trên validation, và độ dao động giữa hai lần chạy cỡ 0,01.
- **H2:** B-CLL kém B. Căn cứ: trên validation, LCR@4 giảm từ 0,726 xuống 0,430 và Macro-F1 thấp hơn 0,08.
- **H3:** B vẫn hơn A0 có ý nghĩa (lặp lại kết quả chính trên dữ liệu mới).
- Kết quả được báo cáo **dù đúng hay sai** so với các giả thuyết trên.

## 6. Mã băm tại thời điểm khóa (16 ký tự đầu của SHA-256)

Commit nền: `b1d38f5` (nhánh `refactor/repo-structure`), cộng các thay đổi trên nhánh `test/c-improvements`.

| File | SHA-256 |
| --- | --- |
| `src/experiments/run_llm.py` | `b1c4aca472674ca6` |
| `src/experiments/prompting.py` | `f63100ab21d9460c` |
| `src/retrieval/selectors.py` | `34eca10d31467c0e` |
| `src/retrieval/knn.py` | `b3c90a3978c24b1f` |
| `src/retrieval/pool_aux.py` | `fd58405d67e8e990` |
| `src/analysis/ensemble.py` | `c11aad02b4f87dce` |
| `src/artifacts/retrieval/minilm/pool_aux.json` | `385e3fdf5e070e1e` |
| `src/artifacts/retrieval/minilm/neighbors_test_fresh.jsonl` | `2a49d14b9f5480f6` |
| `src/data/processed/sr_bh_v1/test_fresh_subset.jsonl` | `a3dab67a59cb226b` |
| `src/configs/experiments/B_mmr_k4.json` | `5f69db585c01aaea` |
| `src/configs/experiments/B_cll_k4.json` | `87338b14b4b60fda` |
| `src/configs/experiments/B_enn_k4.json` | `60b48e4ef3b457d8` |
| `src/configs/experiments/C_knn_enn_k4.json` | `1cbd5a03e399067a` |
| `src/configs/experiments/C_iter_k4.json` | `6545774a2bed82f7` |
| `src/configs/experiments/C_gated_k4.json` | `ba014dcedbc218db` |
