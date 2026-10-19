# Label-Aware Retrieval for LLM-Based Web Attack Detection

Dự án nghiên cứu việc sử dụng **Label-Aware Retrieval** để chọn **demonstrations** cho **Large Language Model (LLM)**, phục vụ phát hiện và phân loại **Web Attack** từ **HTTP request** thông qua **In-Context Learning (ICL)**.

**Câu hỏi nghiên cứu:** Việc kết hợp thông tin nhãn khi chọn demonstrations có cải thiện chất lượng phân loại so với **Standard Semantic Retrieval** chỉ dựa trên **embedding similarity** hay không?

Đây là giả thuyết cần kiểm chứng bằng thực nghiệm. Repository có code chuẩn bị dữ liệu, notebook **Exploratory Data Analysis (EDA)** và báo cáo khảo sát; chưa có kết quả benchmark cho phương pháp đề xuất. Bắt đầu tại [trang hướng dẫn đọc repository](README.md).

## Mục tiêu và phạm vi

- So sánh LLM baseline, Standard Semantic Retrieval + LLM và Label-Aware Retrieval + LLM trên cùng dữ liệu đánh giá.
- Phân tích ảnh hưởng của demonstration selection đến chất lượng phân loại, đặc biệt ở minority classes và các request dễ nhầm lẫn.
- Đánh giá chất lượng retrieval bằng **Label Consistency Rate@k (LCR@k)**, kết hợp classification metrics và chi phí inference.
- Thực hiện **ablation study** để xác định tác động của prior, reranking, số lượng demonstrations và kích thước retrieval pool.

Hướng triển khai được chọn là **inference-only**, không train hoặc fine-tune model. Pipeline đề xuất dùng **LLM zero-shot prior** kết hợp **label-aware reranking**; các model và tham số cụ thể vẫn cần được chốt khi triển khai.

## Ý tưởng phương pháp

Các HTTP request có thể chia sẻ endpoint, cấu trúc và nhiều token nhưng mang nhãn khác nhau. Vì vậy, semantic similarity cao chưa đủ để xác định một demonstration có hữu ích cho việc phân loại request đang xét hay không.

Thiết kế thực nghiệm gồm ba pipeline:

| Pipeline | Cách hoạt động | Vai trò |
| --- | --- | --- |
| **A — LLM baseline** | Phân loại bằng zero-shot hoặc fixed few-shot, không dùng retrieval | Đo năng lực ban đầu của LLM |
| **B — Standard Semantic Retrieval** | Encode request, tìm top-k demonstrations theo similarity, đưa vào prompt cho LLM | Baseline có retrieval |
| **C — Label-Aware Retrieval** | Retrieve top-N candidates, lấy zero-shot prior, rerank theo similarity và thông tin nhãn, chọn top-k cho LLM | Phương pháp đề xuất |

Luồng xử lý dự kiến của Pipeline C:

```text
HTTP request
    ├── Embedding + Semantic Search ──> Top-N labeled candidates
    └── LLM zero-shot ───────────────> Predicted prior label
                                              │
                    Candidates + Prior ───────┘
                              │
                    Label-Aware Reranking
                              │
                    Top-k demonstrations
                              │
                       Prompt + LLM
                              │
                       Predicted label
```

Nhãn của demonstrations có sẵn trong retrieval pool. Nhãn của request cần phân loại được ước lượng bằng zero-shot prior; **ground-truth test label chỉ dùng để đánh giá**, không dùng để chọn demonstrations. Các lựa chọn như contrastive examples, label diversity và trọng số reranking sẽ được kiểm chứng qua ablation study.

## Hiện trạng repository

| Thành phần | Hiện trạng |
| --- | --- |
| Mô tả và thiết kế nghiên cứu | Đã có mô tả đề tài và kế hoạch 4 tuần |
| Literature review | Có danh mục papers; cần xác minh và tổng hợp khi triển khai |
| Dataset EDA | Đã có notebook khảo sát dữ liệu CAPEC |
| Dataset chính thức, preprocessing và data split | Đã xử lý SR-BH 2020 và tạo split v1; quyết định benchmark còn mở do annotation đáng nghi |
| Pipeline A, B, C | Chưa có implementation trong repository |
| Benchmark, ablation và báo cáo kết quả | Chưa có kết quả thực nghiệm pipeline |
| Môi trường tái lập | Module dữ liệu dùng Python standard library; môi trường LLM/retrieval chưa triển khai |

Theo dõi [kế hoạch 4 tuần cho 2 người](plan/ke_hoach_trien_khai_4_tuan.md) để triển khai. Các mốc là mục tiêu dự kiến, không phải xác nhận công việc đã hoàn tất.

## Dữ liệu khảo sát

Dataset đang được khảo sát là **SR-BH 2020 / `data_capec_multilabel.csv`**, gồm HTTP logs với nhãn **CAPEC**. CSV local nằm ở `src/data/raw/` và được gitignore. [Khảo sát bổ sung CSIC 2010](surveys/khao_sat_csic_2010.md) được lưu riêng.

**Cập nhật Task 1 ngày 19/10/2026:** đã tải file gốc vào thư mục local được gitignore, xác minh checksum và đọc lại schema: **907.815 record, 38 cột, 14 cột nhãn gồm Normal và 13 CAPEC**. Sau lọc sáu lớp single-label, cách ly conflict và exact-dedup còn **466.267 request**. Review có phát hiện Normal chứa payload đáng nghi; chưa chốt dataset cho benchmark cuối cùng. Xem [báo cáo Task 1](progress/task_1_dataset_va_protocol.md) và [hướng dẫn chạy preprocessing/test](protocol/README.md). Bảng dưới đây là thống kê khảo sát cũ, không thay thế artifact mới.

Các thống kê đã được ghi nhận trong khảo sát trước đây gồm:

| Thuộc tính | Giá trị đã ghi nhận |
| --- | --- |
| Số bản ghi | 907.815 |
| Số cột | 38 |
| Số cột nhãn | 14, gồm `000 - Normal` và 13 attack categories; đã xác minh lại trong Task 1 |
| Định dạng nhãn | Multi-label binary |
| Bản ghi có đúng một nhãn | 898.577, khoảng 99% |
| Duplicate URL paths | 557.474, khoảng 61,4% |
| `request_body` bị thiếu | Khoảng 97,1% |

Các số liệu trên chưa được chạy kiểm chứng lại trong lần cập nhật README này. Dùng [notebook khảo sát](../src/notebooks/sr_bh_2020_khao_sat.ipynb) để kiểm tra lại trên dataset thực tế.

Những vấn đề cần xử lý trước thực nghiệm:

- **Class imbalance:** Normal và SQL Injection chiếm tỷ trọng lớn; một số lớp có rất ít mẫu.
- **Duplicates và data leakage:** cần kiểm tra exact duplicates và near-duplicates trước khi tách retrieval pool, validation set và test set.
- **Multi-label và attack taxonomy:** cần thống nhất cách xử lý multi-label rows và tập nhãn dùng cho classification.
- **Annotation quality và ngữ cảnh:** cùng URL path có thể có nhãn khác nhau do method, headers, body hoặc annotation noise; cần kiểm tra đầy đủ request trước khi kết luận.

Các lớp đang được cân nhắc cho phạm vi ban đầu gồm **Normal/Benign, SQL Injection, Path Traversal, Code Injection, HTTP Response Splitting** và **OS Command Injection**. Dataset và taxonomy cuối cùng chưa được chốt.

## Cấu trúc repository

```text
.
├── src/                           # Code, dữ liệu, configs, tests, notebooks, artifacts
│   ├── preprocessing/
│   ├── data/                      # raw/ và processed/
│   ├── configs/
│   ├── tests/
│   ├── notebooks/
│   └── artifacts/
└── reports/                       # Tài liệu để đọc lại
    ├── README.md
    ├── project_overview.md
    ├── mo_ta_de_tai.md
    ├── surveys/                   # Khảo sát và figures/
    ├── progress/
    ├── protocol/
    ├── plan/
    └── references/                # Papers và PDF
```

## Chạy notebook EDA

Các bước dưới đây dành cho notebook hiện có. Repository chưa có lệnh chạy pipeline end-to-end.

### 1. Chuẩn bị môi trường

Kế hoạch dự án hướng đến **Python 3.10**. Tại thư mục gốc repository, tạo virtual environment và cài các thư viện dùng trong notebook:

```bash
python3 -m venv src/.venv
source src/.venv/bin/activate
python -m pip install pandas matplotlib seaborn jupyterlab
```

Trên Windows PowerShell, thay lệnh kích hoạt bằng:

```powershell
src\.venv\Scripts\Activate.ps1
```

Danh sách trên chỉ phục vụ EDA, chưa phải dependency set được khóa phiên bản cho toàn bộ dự án.

### 2. Chuẩn bị dataset

Đặt file `data_capec_multilabel.csv` trong `src/data/raw/`. Hai notebook tự tìm thư mục gốc repo từ working directory của kernel và dùng cùng đường dẫn này:

- [sr_bh_2020_khao_sat.ipynb](../src/notebooks/sr_bh_2020_khao_sat.ipynb).
- [sr_bh_eda.ipynb](../src/notebooks/sr_bh_eda.ipynb).

Output đã lưu trong notebook thuộc lần EDA trước; lần sắp xếp thư mục này chỉ cập nhật đường dẫn, chưa chạy lại notebook.

### 3. Mở notebook

```bash
jupyter lab
```

Chọn kernel của virtual environment vừa tạo và chạy lần lượt các cell. Một số cell khảo sát truy cập mẫu cụ thể trong dataset, vì vậy cần kiểm tra lại điều kiện chọn mẫu nếu dùng dữ liệu khác.

Script [examples/eda_dataset.py](../src/notebooks/examples/eda_dataset.py) là ví dụ cho file `dataset.csv` có hai cột `request` và `label`. Muốn dùng với CAPEC cần điều chỉnh đường dẫn và schema; script chưa đọc trực tiếp các cột multi-label của CAPEC.

## Kế hoạch thực nghiệm

1. Chốt dataset, attack taxonomy và protocol đánh giá.
2. Hoàn thiện preprocessing, deduplication và data split; kiểm tra leakage giữa các tập.
3. Xây dựng embedding module, FAISS index, LLM client, prompt builder và output parser; chạy Pipeline A và B.
4. Đo chất lượng retrieval của Pipeline B, triển khai zero-shot prior và label-aware reranker cho Pipeline C.
5. So sánh các pipeline trên cùng test set; thực hiện ablation và phân tích per-class, hard cases, latency và token usage.

Các metrics dự kiến gồm **Accuracy, Macro-F1, Weighted-F1, Precision/Recall/F1 per class** và **LCR@k**. LCR@k đo tỷ lệ demonstrations có nhãn trùng với ground-truth query label khi đánh giá offline; cần đọc cùng classification metrics vì mức độ trùng nhãn không tự bảo đảm demonstrations hữu ích hơn.

Các công nghệ trong thiết kế gồm **Sentence Transformers**, **FAISS** và LLM qua **Ollama** hoặc API. Đây là lựa chọn dự kiến; repository chưa tích hợp các thành phần này.

## Tài liệu dự án

Bắt đầu từ [trang hướng dẫn tập trung công việc](README.md).

| Tài liệu | Nội dung |
| --- | --- |
| [Kế hoạch chính](plan/ke_hoach_trien_khai_4_tuan.md) | Phân công 2 người, lịch 4 tuần và các mốc thực nghiệm |
| [Báo cáo với giảng viên](progress/bao_cao_dinh_huong_va_mau_hang_tuan.md) | Khung báo cáo định hướng và mẫu cập nhật hằng tuần |
| [Mô tả đề tài](mo_ta_de_tai.md) | Tổng quan, phương pháp và phạm vi nghiên cứu |
| [Danh mục papers](references/link_papers.md) | Các paper tham khảo |
