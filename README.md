# Label-Aware Web Attack Detection

Nghiên cứu phát hiện và phân loại tấn công web từ HTTP request bằng Large Language Model (LLM). Dự án kiểm chứng việc dùng thông tin nhãn khi chọn ví dụ cho In-Context Learning có cải thiện kết quả so với chọn ví dụ chỉ theo độ tương đồng ngữ nghĩa hay không.

Hướng triển khai là **inference-only**, không huấn luyện hoặc fine-tune model. Các kết luận về chất lượng phương pháp cần được kiểm chứng bằng thực nghiệm.

## Các pipeline

| Pipeline | Phương pháp | Trạng thái |
| --- | --- | --- |
| **A0** | LLM zero-shot, không có ví dụ trong prompt | Đã triển khai; chạy end-to-end bằng mock |
| **A1** | LLM fixed few-shot | Chưa triển khai |
| **B** | Semantic retrieval → top-k ví dụ → LLM | Chưa triển khai |
| **C** | Semantic retrieval → rerank bằng zero-shot prior và thông tin nhãn → LLM | Chưa triển khai |

Luồng A0 hiện có:

```text
Request JSONL → Prompt zero-shot → Backend → Parse JSON
                                               │
                         Predictions JSONL ←───┘
                                │
                      Metrics + Confusion matrix
```

A0 có kiểm tra nhãn đầu ra, timeout/retry giới hạn, lưu từng prediction và hỗ trợ resume. Ground truth chỉ dùng để đánh giá, không được đưa vào prompt.

**Hiện trạng kiểm chứng:** bộ kiểm thử gần nhất đạt 28/28 test, trong đó 12 test cho A0. Mock có fixture riêng để kiểm tra cả output hợp lệ, output sai và lỗi backend. Artifact smoke Groq hiện có chứa một mẫu lỗi backend; chưa xác nhận smoke API thật thành công và chưa có kết quả benchmark. Không dùng số liệu mock để đánh giá năng lực LLM.

## Cấu trúc repo

```text
.
├── README.md
├── env.example                  # Template cấu hình công khai, key để trống
├── src/
│   ├── pipeline_a0/             # Prompt, client, parser, runner và metrics
│   ├── preprocessing/           # Chuẩn bị dữ liệu và khảo sát dataset
│   ├── configs/                 # Cấu hình JSON và thông tin nguồn dữ liệu
│   ├── tests/                   # Unit tests và fixture tổng hợp
│   ├── data/
│   │   ├── raw/                 # Dữ liệu gốc, không track Git
│   │   └── processed/           # Splits/manifests, không track Git
│   ├── artifacts/              # Predictions, metrics, audit và logs
│   ├── notebooks/              # Khảo sát dữ liệu
│   └── requirements-*.txt
└── reports/
    ├── project_overview.md       # Thiết kế nghiên cứu
    ├── surveys/                 # Khảo sát SR-BH và CSIC; hình minh họa
    ├── protocol/                # Schema, chính sách nhãn và data split
    ├── progress/                # Kết quả xử lý dữ liệu và báo cáo tiến độ
    ├── plan/                    # Kế hoạch triển khai
    └── references/              # Tài liệu tham khảo
```

Chạy các lệnh dưới đây từ thư mục gốc repo. Dữ liệu lớn và credential được giữ ở máy local.

## Bắt đầu bằng mock — không cần API key

Yêu cầu **Python >=3.10 trên Linux/POSIX**; đã kiểm chứng với Python 3.12.3. A0 dùng thư viện chuẩn, không cần cài SDK hoặc package bên ngoài. Resume sử dụng `fcntl` nên chưa hỗ trợ Windows native; trên Windows có thể dùng WSL.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m unittest discover -s src/tests -v
```

Nếu đã có `.venv`, chỉ cần activate. Mỗi terminal mới cần chạy lại `source .venv/bin/activate`; thoát bằng `deactivate`. Dependency A0 được ghi tại [src/requirements-a0.txt](src/requirements-a0.txt). Các dependency tạo hình khảo sát được tách riêng, không cần cho mock A0.

Chạy sáu request tổng hợp:

```bash
python -m src.pipeline_a0 \
  --config src/configs/pipeline_a0_mock.json \
  --input src/tests/fixtures/a0_requests.jsonl \
  --output src/artifacts/pipeline_a0/mock_quickstart \
  --limit 6
```

Lần đầu với thư mục output mới: `selected=6`, `processed_now=6`. Chạy lại nguyên lệnh: `resumed=6`, `processed_now=0`. Fixture cố ý có output lỗi và prediction sai để kiểm tra luồng đánh giá.

Xem kết quả:

```bash
python -m json.tool src/artifacts/pipeline_a0/mock_quickstart/last_invocation.json
python -m json.tool src/artifacts/pipeline_a0/mock_quickstart/metrics.json
```

## Dữ liệu và taxonomy

Đã khảo sát dữ liệu thật của hai nguồn:

| Dataset | Kết quả khảo sát | Vai trò hiện tại |
| --- | --- | --- |
| **SR-BH 2020 v1.2** | 907.815 bản ghi, 38 cột; Normal và 13 nhãn tấn công | Nguồn cho development pilot A0 |
| **CSIC 2010** | 97.065 request trong ba file đã tải; nhãn nguồn Normal/Anomalous | Khảo sát độc lập, chưa thay nguồn A0 |

Preprocessing SR-BH chỉ giữ request có đúng một nhãn hoạt động trong toàn bộ nhãn nguồn, sau đó chọn sáu lớp. Các request trùng nội dung nhưng mâu thuẫn nhãn được cách ly trước dedup và group split với seed 42. Không tự ép các mẫu multi-label thành single-label.

Taxonomy hiện tại, theo [src/configs/data.json](src/configs/data.json):

```text
NORMAL
SQL_INJECTION
PATH_TRAVERSAL
CODE_INJECTION
HTTP_RESPONSE_SPLITTING
OS_COMMAND_INJECTION
```

Schema tối thiểu của mỗi dòng JSONL gồm `request_id`, `request_text`, `label`. `request_text` là chuỗi JSON canonical chứa method, URI, protocol, headers và body; giữ nguyên encoding của payload. Nhãn nằm ngoài nội dung đưa vào model.

Development hiện có tại `src/data/processed/sr_bh_v1/development.jsonl`: 30 mẫu, 5 mẫu mỗi lớp. File raw/processed không đi kèm bản clone Git. Nếu máy chưa có dữ liệu, xem [hướng dẫn tải, preprocessing và kiểm chứng](reports/protocol/README.md); nếu đã có split thì dùng lại, không ghi đè hoặc tạo lại để chạy smoke.

Chất lượng annotation còn điểm cần làm rõ; dataset benchmark chưa được chốt. Xem [quyết định dataset và giới hạn](reports/protocol/dataset_decision.md). Giữ final test riêng, không dùng để sửa prompt hoặc chọn cấu hình.

## Cấu hình API bằng .env

Client hiện hỗ trợ endpoint **chat completions tương thích OpenAI**. Template [env.example](env.example) dùng Groq làm ví dụ cấu hình; đây chưa phải model được chốt cho benchmark. Kiểm tra quyền truy cập model và quota trong tài khoản của mình trước khi gọi.

Tạo file local, giữ nguyên nếu đã có:

```bash
cp -n env.example .env
chmod 600 .env
```

Mở `.env` bằng editor, điền `A0_API_KEY`. Không điền key thật vào `env.example`.

| Biến | Ý nghĩa |
| --- | --- |
| `A0_API_KEY` | API key của backend đã chọn |
| `A0_BASE_URL` | URL gốc API; ví dụ trong template là `https://api.groq.com/openai/v1` |
| `A0_MODEL` | Model ID backend hỗ trợ; ví dụ trong template là `openai/gpt-oss-20b` |

Runner tự nối `/chat/completions` vào base URL. CLI **không tự đọc `.env`**; nạp file do mình quản lý vào môi trường Bash trước khi chạy:

```bash
set -a
source .env
set +a
```

`.env`, `.env.*` và `.venv/` đã được Git bỏ qua; `env.example` công khai chỉ chứa cấu hình mẫu. Không đưa key vào code, log hay artifact. Không cần cài `python-dotenv`, SDK Groq hoặc SDK OpenAI cho cách chạy này.

## Smoke API thật trên development

Sau khi cấu hình env và có development file, thử **một mẫu** trước:

```bash
python -m src.pipeline_a0 \
  --config src/configs/pipeline_a0_groq_smoke.json \
  --input src/data/processed/sr_bh_v1/development.jsonl \
  --output src/artifacts/pipeline_a0/groq_quickstart_01 \
  --limit 1
```

Cấu hình Groq smoke dùng timeout 60 giây, không retry, output budget 2048 token và temperature 0. Config API chung ở `src/configs/pipeline_a0_api.json` có cấu hình khác: timeout 30 giây, tối đa 2 retries và output budget 128 token. Chọn config phù hợp với model, ghi nhận thay đổi và dùng run directory mới.

Runner API thật chỉ nhận đúng file development hiện có, giới hạn 1–10 mẫu mỗi lệnh. Mẫu được chọn từ đầu file, không cân bằng lớp. Smoke nhỏ kiểm tra kết nối và luồng xử lý; chưa đủ để kết luận chất lượng phân loại. Giữ tổng ngân sách tối đa 10 mẫu cho một phiên smoke, tính cả các lần gọi lại ở run khác.

**Kiểm tra `status_counts` trong `metrics.json` sau mỗi lần chạy.** Runner có thể kết thúc bình thường dù toàn bộ prediction là lỗi, vì lỗi cũng phải được lưu lại. Khi gặp 401/403, kiểm tra credential/quyền model; 429 là giới hạn quota; `invalid_output` là JSON hoặc nhãn không hợp lệ. Không tự đổi câu trả lời lỗi thành nhãn dự đoán.

## Output và resume

| File trong mỗi thư mục run | Nội dung |
| --- | --- |
| `manifest.json` | Cấu hình, model, prompt, taxonomy và hash để truy vết |
| `predictions.jsonl` | Kết quả từng mẫu, status, raw output, latency, usage nếu có |
| `metrics.json` | Macro-F1, Accuracy, Weighted-F1, per-class precision/recall/F1, confusion matrix, coverage và error rates |
| `last_invocation.json` | Số mẫu chọn, số resume và số xử lý mới |

Mỗi prediction được flush/fsync ngay sau xử lý. Resume giữ cả kết quả lỗi và không tự gọi lại chúng. Cache phân biệt model, endpoint, prompt/config và nội dung request. Khi đổi config, model, input, `--limit` hoặc implementation, dùng thư mục output mới; không sửa manifest để ép dùng cache cũ. Run mới có thể gọi lại các mẫu trước đó và tiêu thụ quota.

Metrics tính mẫu lỗi là dự đoán sai, giữ chúng trong confusion matrix ở cột riêng. Token usage chỉ được ghi khi backend cung cấp; không thay dữ liệu thiếu bằng số đo giả. Latency lưu trong prediction là latency inference gốc, không phải thời gian cache hit.

## Tài liệu đọc tiếp

| Tài liệu | Nội dung |
| --- | --- |
| [Tổng quan nghiên cứu](reports/project_overview.md) | Câu hỏi nghiên cứu và thiết kế A/B/C |
| [Khảo sát SR-BH 2020](reports/surveys/khao_sat_sr_bh_2020.md) | Phân bố lớp, payload thật và cặp request minh họa |
| [Khảo sát CSIC 2010](reports/surveys/khao_sat_csic_2010.md) | Schema, nhãn nguồn, split và các ví dụ thực tế |
| [Protocol dữ liệu](reports/protocol/README.md) | Tải dữ liệu, representation, split và audit |
| [Kết quả Task 1](reports/progress/task_1_dataset_va_protocol.md) | Các kiểm tra dữ liệu đã làm và vấn đề annotation |
| [Kế hoạch triển khai](reports/plan/ke_hoach_trien_khai_4_tuan.md) | Phạm vi và các mốc thực nghiệm |
| [Task 2](reports/plan/task_2_pipeline_a_va_kiem_thu.md) | Checklist tổng thể Pipeline A; A1 và validation vẫn là phần tiếp theo |

Các tài liệu kế hoạch mô tả công việc dự kiến; dùng code, artifact và trạng thái ở README này để phân biệt phần đã chạy với phần chưa triển khai.
