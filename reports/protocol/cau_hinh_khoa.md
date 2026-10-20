# Khóa cấu hình trước khi chạy tập test

**Ngày khóa:** 20/10/2026.
**Mốc code:** commit chứa file này trên nhánh `feat/validation-results-and-lock`; sau khi merge, là commit merge tương ứng trên `main`. Mã băm bên dưới chỉ để đối chiếu nhanh. Nguồn chuẩn là commit git, vì mã băm file có thể đổi khi Git chuyển ký tự xuống dòng (LF/CRLF) trên Windows.

Từ mốc này, **không sửa** prompt, cấu hình thí nghiệm, cấu hình LLM, cách chọn ví dụ, dữ liệu hoặc code ảnh hưởng đến dự đoán, cho đến khi chạy xong tập test. Nếu buộc phải sửa lỗi, phải chạy lại các pipeline bị ảnh hưởng vào **thư mục output mới**, và ghi rõ trong báo cáo rằng tập test đã được xem trước khi sửa.

## 1. Những gì được chạy trên test

| Nhóm | Run | File cấu hình | Vai trò |
| --- | --- | --- | --- |
| Bộ chính | A0 | `A0.json` | Zero-shot; là prior của C_llm |
| | B | `B_k4.json` | Semantic top-4 (mốc so sánh chính) |
| | BAL | `BAL_k4.json` | Cân bằng lớp |
| | C, prior kNN | `C_knn_k4.json` | Phương pháp đề xuất, λ = 0,1 |
| | C, prior LLM | `C_llm_k4.json` | Phương pháp đề xuất, prior từ A0, λ = 0,1 |
| Phân tích | C-oracle | `C_oracle_k4.json` | Mức trần khi prior là nhãn thật (không phải phương pháp) |
| | A1 | `A1_k4.json` | 4 ví dụ cố định |
| Không gọi LLM | kNN vote (k = 5) | `eval_retrieval` | Đối chứng không dùng LLM |

**Tập test:** 300 dòng đầu của `src/data/processed/sr_bh_v1/test_subset.jsonl`, đúng 50 request mỗi lớp. Tập này được cố định trước khi xem bất kỳ kết quả test nào. Runner chọn đúng tập này bằng `--allow-test --limit 300`.

## 2. Cấu hình bị khóa

| Thành phần | Giá trị |
| --- | --- |
| LLM | Groq `openai/gpt-oss-20b`, `temperature` 0, `max_tokens` 1024, `reasoning_effort` low, tối đa 3 lần thử lại |
| Khung prompt | `icl-v1` (`src/experiments/prompting.py`); ví dụ cắt ở 500 ký tự; request cần phân loại không cắt |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2`, `max_seq_length` 256, `embedding_view-v1` |
| Truy hồi | Pool 3.000 request (500/lớp), N = 30 ứng viên, k = 4 ví dụ |
| Pipeline C | `score = similarity + 0,1 · 1[nhãn ứng viên = prior]` |
| Prior kNN | Bỏ phiếu có trọng số trên 5 láng giềng gần nhất |
| Ngân sách | `src/configs/llm/budget.json`: dừng trước khi chi phí ước tính (giá gấp đôi) vượt 4,5 USD |

Không có tham số nào được điều chỉnh dựa trên kết quả validation: k, λ và N đều được chọn trước khi chạy LLM (xem `reports/plan/ke_hoach_2_nguoi_11_10_den_14_11.md`, mục 0).

## 3. Mã băm tại thời điểm khóa (16 ký tự đầu của SHA-256)

| File | SHA-256 |
| --- | --- |
| `src/experiments/run_llm.py` | `994e2bef27711108` |
| `src/experiments/prompting.py` | `8e4923f4f7a0ca0c` |
| `src/retrieval/selectors.py` | `54c10a9e6ce28086` |
| `src/retrieval/knn.py` | `d83143ef54c5ff15` |
| `src/retrieval/views.py` | `d36740d8f3b07396` |
| `src/pipeline_a0/core.py` | `6aca8ff1f262636b` |
| `src/configs/llm/groq.json` | `37a620716bcfac4a` |
| `src/configs/experiments/A0.json` | `e4d04740c480f57a` |
| `src/configs/experiments/B_k4.json` | `e7a65111c5a57d9e` |
| `src/configs/experiments/BAL_k4.json` | `31003fbba70c27e1` |
| `src/configs/experiments/C_knn_k4.json` | `e27bb60c6dd78bb0` |
| `src/configs/experiments/C_llm_k4.json` | `a2849a810d55df58` |
| `src/configs/experiments/C_oracle_k4.json` | `0aa7bcf19ca754ca` |
| `src/configs/experiments/A1_k4.json` | `014190476f867203` |
| `src/data/processed/sr_bh_v1/test_subset.jsonl` | `64c009b41a370ab9` |
| `src/data/processed/sr_bh_v1/pool_subset.jsonl` | `6dd9ad930e6286bc` |
| `src/artifacts/retrieval/minilm/neighbors_test.jsonl` | `0a54ae10ec80dc01` |

## 4. Kết quả validation làm căn cứ (200 request)

| Run | Macro-F1 | So với B (CI 95% bootstrap) |
| --- | ---: | --- |
| B (top-4) | **0,893** | — |
| C-oracle (chỉ phân tích) | 0,888 | −0,005 [−0,032; +0,022] |
| C, prior kNN | 0,882 | −0,010 [−0,034; +0,009] |
| C, prior LLM | 0,874 | −0,019 [−0,047; +0,008] |
| BAL | 0,869 | −0,024 [−0,048; −0,004] |
| A0 (zero-shot) | 0,835 | −0,057 [−0,098; −0,018] |
| A1 (4 ví dụ cố định) | 0,814 | −0,078 [−0,124; −0,038] |

Chi tiết: `src/artifacts/reports/validation/comparison.md`.

Giả thuyết cần kiểm chứng trên test, được ghi **trước** khi chạy test:
1. B tốt hơn A0 và A1 (đưa ví dụ giống nhất vào prompt có ích).
2. C, cả prior kNN lẫn prior LLM, **không** tốt hơn B một cách có ý nghĩa thống kê.
3. Ngay cả C-oracle cũng không tốt hơn B rõ rệt, nghĩa là label-aware reranking có rất ít dư địa trên dữ liệu này.

## 5. Lệnh chạy test

Chạy trong Git Bash, ở thư mục gốc repo, trên code của commit đã khóa:

```bash
source .venv/Scripts/activate && bash src/experiments/run_suite.sh test --locked
```

```bash
EXTRA=1 bash src/experiments/run_suite.sh test --locked
```

```bash
python -m src.experiments.eval_retrieval --retrieval src/artifacts/retrieval/minilm --split test --limit 300
```

```bash
python -m src.analysis.compare --split test --reference B_semantic_k4 --runs "src/artifacts/runs/test/*" --output src/artifacts/reports/test
```

Neighbors cho test đã được dựng sẵn bằng `build_retrieval --add-split test`, dùng lại pool đã mã hóa và không đổi neighbors của validation.

**Chi phí dự kiến:** khoảng 300 × (640 + 6 × 1.500) ≈ 2,9 triệu token, tức khoảng 0,25 USD theo giá tham khảo. Tính cả validation, tổng vẫn dưới 0,5 USD, thấp hơn nhiều so với trần 5 USD.
