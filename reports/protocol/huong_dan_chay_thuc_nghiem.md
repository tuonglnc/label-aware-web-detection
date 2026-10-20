# Hướng dẫn chạy thực nghiệm và đọc hiểu code

Bản ngắn gọn các lệnh. Mọi lệnh chạy từ **thư mục gốc repo**. Các lệnh `python -m ...` chạy được ở cả PowerShell lẫn Git Bash. Lệnh cài đặt, tải dữ liệu và tạo `.env` riêng cho từng terminal có ở mục 1 của [hướng dẫn đọc và chạy code](huong_dan_doc_va_chay_code.md).

## 0. Bức tranh tổng thể

```text
 (1) prepare.py            (2) build_retrieval.py       (3) eval_retrieval.py
 CSV gốc ──► split ──────► vector pool + top-N ──────► RQ1, kNN, LCR@k   (không cần LLM)
                                     │
                                     ▼
                           (4) run_llm.py  ×  {A0, A1, B, BAL, C}        (cần API LLM)
                                     │
                                     ▼
                           (5) compare.py ──► bảng, bootstrap, McNemar, hình
```

| Bước | Lệnh | Cần LLM? | Thời gian (CPU 8 nhân) |
| --- | --- | --- | --- |
| 1. Chuẩn bị dữ liệu | `python -m src.preprocessing.prepare` | Không | ~5 phút |
| 2. Dựng retrieval | `python -m src.experiments.build_retrieval` | Không | ~6 phút |
| 3. Đánh giá retrieval + kNN | `python -m src.experiments.eval_retrieval` | Không | vài giây |
| 4. Chạy pipeline LLM | `python -m src.experiments.run_llm` | **Có** | tùy API |
| 5. So sánh | `python -m src.analysis.compare` | Không | vài giây |

## 1. Cài đặt

```bash
python -m venv .venv
```

Kích hoạt venv: PowerShell `.venv\Scripts\Activate.ps1`; Git Bash `source .venv/Scripts/activate`; Linux/macOS `source .venv/bin/activate`. Sau đó:

```bash
pip install -r src/requirements-experiments.txt
```

```bash
python -m unittest discover -s src/tests
```

Bộ test phải đạt toàn bộ trước khi chạy thật. Lần đầu dùng, model embedding (~90 MB) được tải tự động.

## 2. Chuẩn bị dữ liệu (đã có từ Task 1)

Tải CSV gốc vào `src/data/raw/data_capec_multilabel.csv`. Lệnh tải cho PowerShell và Git Bash nằm ở mục 1.2 của [hướng dẫn đọc và chạy code](huong_dan_doc_va_chay_code.md). Sau đó chạy:

```bash
python -m src.preprocessing.prepare --config src/configs/data.json
```

Kết quả nằm trong `src/data/processed/sr_bh_v1/`. Thực nghiệm chỉ dùng 4 file:

| File | Số mẫu | Vai trò |
| --- | ---: | --- |
| `pool_subset.jsonl` | 3.000 (500/lớp) | Kho ví dụ có nhãn để retrieve |
| `development.jsonl` | 30 | Chạy thử, sửa lỗi |
| `validation_subset.jsonl` | 200 | Chọn k, λ, nguồn prior |
| `test_subset.jsonl` | 600 | **Chỉ chạy một lần** sau khi khóa cấu hình |

## 3. Dựng retrieval

```bash
python -m src.experiments.build_retrieval --output src/artifacts/retrieval/minilm
```

**Code liên quan:**

- `src/retrieval/views.py`: `request_text` gốc xếp header trước uri. Embedding model chỉ đọc khoảng 256 token đầu, nên `embedding_view` đưa method, uri và body lên đầu để không cắt mất payload. Payload không bị decode hay sửa.
- `src/retrieval/embedding.py`: dùng `all-MiniLM-L6-v2` (pretrained, không train), vector chuẩn hóa độ dài 1.
- `src/retrieval/index.py`: `similarity = query @ pool.T` (cosine). Lấy N ứng viên lớn nhất; hòa điểm thì xếp theo `request_id` để kết quả ổn định.

**Đầu ra:** file `neighbors_<split>.jsonl` chứa top-50 ứng viên cho mỗi query, gồm id, **nhãn của ứng viên** và similarity. File không chứa nhãn của query.

## 4. Đánh giá retrieval và kNN (không cần LLM)

```bash
python -m src.experiments.eval_retrieval --retrieval src/artifacts/retrieval/minilm --split validation
```

Kết quả nằm trong `src/artifacts/retrieval/minilm/eval_validation/retrieval_metrics.md`:

- **RQ1:** tỷ lệ query mà ví dụ giống nhất lại khác nhãn.
- **kNN vote** (`src/retrieval/knn.py`): Macro-F1 khi chỉ đếm nhãn k hàng xóm, có trọng số theo similarity. Hòa thì chọn nhãn của hàng xóm gần nhất.
- **LCR@k** của B, BAL, C (prior từ kNN) và C-oracle: tỷ lệ ví dụ cùng nhãn với query. Đây chỉ là chỉ số chẩn đoán.

## 5. Chạy các pipeline LLM

### 5.1. Cấu hình API

Tạo key miễn phí tại console.groq.com (mỗi người tự tạo, không chia sẻ key), rồi tạo file `.env` từ mẫu:
- PowerShell: `Copy-Item env.example .env`
- Git Bash: `cp env.example .env`

Mở `.env`, điền `A0_API_KEY`. Có thể đổi `A0_MODEL` nếu model mặc định không có trong tài khoản. Không commit `.env`.

### 5.2. Thử bằng LLM giả (không tốn quota)

```bash
python -m src.experiments.run_llm --config src/configs/experiments/B_k4.json --llm src/configs/llm/mock.json --split development --output src/artifacts/runs_mock/development/B_k4
```

LLM giả (`DemoMajorityMock`) trả nhãn chiếm đa số trong các ví dụ. Nó chỉ dùng để kiểm tra luồng, **không** được đưa vào báo cáo như kết quả.

### 5.3. Chạy thật cả bộ

Cấu hình đã chốt: **k = 4**, ví dụ cắt ở **500 ký tự**, **λ = 0,1**. Bộ chính gồm A0, B, BAL, C (prior kNN), C (prior LLM). Dùng **một** key trong `.env` (một tài khoản Groq gói trả theo mức dùng; điều khoản của Groq không cho dùng nhiều tài khoản để vượt giới hạn). Chạy trong Git Bash:

```bash
bash src/experiments/run_suite.sh validation
```

- Gặp giới hạn thì script tự dừng gọn; **chạy lại đúng lệnh** để tiếp tục.
- Có chốt ngân sách 4,5 USD (giá gấp đôi giá tham khảo) trong `src/configs/llm/budget.json`: script dừng **trước khi** chi phí ước tính có thể vượt ngưỡng; tổng đã dùng ở `src/artifacts/api_spend_ledger.json`.
- Sau bộ chính, chạy thêm C-oracle và A1: `EXTRA=1 bash src/experiments/run_suite.sh validation`.
- Muốn chạy riêng một pipeline (dùng được cả trong PowerShell):

```bash
python -m src.experiments.run_llm --config src/configs/experiments/B_k4.json --llm src/configs/llm/groq.json --env-file .env --split validation --output src/artifacts/runs/validation/B_k4 --retry-errors
```

**Code liên quan:**

- `src/experiments/prompting.py`: một khung prompt chung cho mọi pipeline. Ví dụ tốt nhất đặt cuối, sát request cần phân loại. Request cần phân loại không bao giờ bị cắt; ví dụ mẫu bị cắt theo `max_demo_chars` (500) và có đánh dấu `…[truncated]`.
- `src/retrieval/selectors.py`: 4 chiến lược chọn ví dụ. Công thức C nằm trong `label_aware_rerank`.
- `src/experiments/run_llm.py`:
  - Tách nhãn query ra ngay từ đầu (`truth`); phần chọn ví dụ và prompt chỉ thấy `public`.
  - Ghi từng prediction ngay để có thể resume; hết quota ngày thì dừng mà không ghi lỗi.
  - Từ chối chạy khi config, dữ liệu hoặc code thay đổi mà vẫn dùng thư mục cũ.
  - Khóa split test nếu không có cờ `--allow-test`.
- `src/pipeline_a0/core.py`: client API; khi gặp 429 thì tự chờ theo `retry-after` (giới hạn token/phút).

### 5.4. Các file cấu hình

| File | Pipeline | Ghi chú |
| --- | --- | --- |
| `A0.json` | Zero-shot | Chạy trước; là prior của `C_llm_k4` |
| `B_k4.json` | Semantic top-4 | Mốc so sánh chính |
| `BAL_k4.json` | Cân bằng lớp | Đối chứng |
| `C_knn_k4.json` | C, prior kNN (k=5), λ = 0,1 | 1 lượt gọi LLM mỗi query |
| `C_llm_k4.json` | C, prior từ A0, λ = 0,1 | 2 lượt gọi mỗi query (tính cả A0) |
| `C_oracle_k4.json` | C, prior = nhãn thật | **Chỉ phân tích mức trần**, tùy chọn |
| `A1_k4.json` | 4 ví dụ cố định | Tùy chọn |

Ảnh hưởng của λ được phân tích offline bằng bảng quét λ trong `retrieval_metrics.md`, không tốn API.

## 6. So sánh và xuất bảng

```bash
python -m src.analysis.compare --split validation --reference B_semantic_k4 --runs "src/artifacts/runs/validation/*" --output src/artifacts/reports/validation
```

Chỉ so sánh các run đã chạy xong. `comparison.md` gồm:
- Bảng Macro-F1, Accuracy, FPR Normal, coverage, LCR@k, số lượt gọi và token.
- Chênh lệch so với B: khoảng tin cậy 95% bootstrap và p-value McNemar.
- Bảng **prior đúng/sai**: C sửa được bao nhiêu lỗi của B, làm hỏng bao nhiêu câu.
- F1 từng lớp và hình ma trận nhầm lẫn của từng run.

## 7. Chạy test (sau khi khóa cấu hình ngày 28/10)

1. Ghi cấu hình và commit hash vào `reports/protocol/cau_hinh_khoa.md`.
2. Dựng neighbors cho test: `python -m src.experiments.build_retrieval --output src/artifacts/retrieval/minilm --include-test`.
3. Chạy bộ chính trên **300 mẫu đầu** của `test_subset.jsonl` (50/lớp), mỗi ngày đến khi xong:

```bash
bash src/experiments/run_suite.sh test --locked
```

4. kNN trên cùng 300 mẫu: `python -m src.experiments.eval_retrieval --retrieval src/artifacts/retrieval/minilm --split test --limit 300`.
5. So sánh: lệnh ở mục 6 với `--split test`.

Không sửa prompt, k hay λ sau khi đã xem kết quả test.

## 8. Câu hỏi hay gặp khi bảo vệ

| Câu hỏi | Trả lời ngắn | Xem code |
| --- | --- | --- |
| Có dùng nhãn thật của query để chọn ví dụ không? | Không, trừ C-oracle (đã ghi rõ chỉ để phân tích) | `run_llm.py`: biến `public` và `truth` |
| Ví dụ mẫu có thể là chính query không? | Không, pool và các tập đánh giá được chia theo nhóm, không giao nhau | `prepare.py: audit_splits`, test `test_query_labels_and_metadata_never_reach_the_prompt` |
| LLM trả sai định dạng thì sao? | Ghi `invalid_output`, tính là sai, không bị loại | `prompting.parse_label`, `metrics.classification_metrics` |
| Vì sao có kNN? | Nếu đếm nhãn hàng xóm đã đủ tốt thì LLM phải chứng minh giá trị thêm | `knn.py` |
| λ = 0 thì sao? | C trùng hoàn toàn với B, có test kiểm tra | `test_lambda_zero_and_missing_prior_equal_semantic` |
