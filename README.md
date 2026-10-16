# Label-Aware Retrieval for LLM-Based Web Attack Detection

Dự án nghiên cứu việc sử dụng **Label-Aware Retrieval** để chọn **demonstrations** cho **Large Language Model (LLM)**, phục vụ phát hiện và phân loại **Web Attack** từ **HTTP request** thông qua **In-Context Learning (ICL)**.

**Câu hỏi nghiên cứu:** Việc kết hợp thông tin nhãn khi chọn demonstrations có cải thiện chất lượng phân loại so với **Standard Semantic Retrieval** chỉ dựa trên **embedding similarity** hay không?

Đây là giả thuyết cần kiểm chứng bằng thực nghiệm. Repository hiện lưu tài liệu nghiên cứu, kế hoạch triển khai và các notebook **Exploratory Data Analysis (EDA)**; chưa có kết quả benchmark cho phương pháp đề xuất.

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
| Đề cương và thiết kế nghiên cứu | Đã có tài liệu |
| Literature review và systematic search log | Đã có bản khảo sát sơ bộ |
| Dataset EDA | Đã có notebook và báo cáo sơ bộ cho dữ liệu CAPEC |
| Dataset chính thức, preprocessing và data split | Cần hoàn thiện và chốt |
| Pipeline A, B, C | Chưa có implementation trong repository |
| Benchmark, ablation và báo cáo kết quả | Chưa có kết quả thực nghiệm pipeline |
| Môi trường tái lập | Chưa có `requirements.txt` hoặc cấu hình đóng gói |

Các mốc trong kế hoạch tháng 10 là mục tiêu dự kiến, không phải xác nhận rằng công việc đã hoàn tất.

## Dữ liệu khảo sát

Dataset đang được khảo sát là **SR-BH 2020 / `data_capec_multilabel.csv`**, gồm HTTP logs với nhãn **CAPEC**. File CSV không được lưu trong repository hiện tại.

Theo [báo cáo Dataset Survey](mini-reports/p1_dataset_analysis.md), các thống kê sơ bộ gồm:

| Thuộc tính | Giá trị đã ghi nhận |
| --- | --- |
| Số bản ghi | 907.815 |
| Số cột | 38 |
| Số cột nhãn | 13, gồm `000 - Normal` và các attack categories |
| Định dạng nhãn | Multi-label binary |
| Bản ghi có đúng một nhãn | 898.577, khoảng 99% |
| Duplicate URL paths | 557.474, khoảng 61,4% |
| `request_body` bị thiếu | Khoảng 97,1% |

Đây là số liệu từ báo cáo đã có, chưa được chạy kiểm chứng lại trong lần cập nhật README này.

Những vấn đề cần xử lý trước thực nghiệm:

- **Class imbalance:** Normal và SQL Injection chiếm tỷ trọng lớn; một số lớp có rất ít mẫu.
- **Duplicates và data leakage:** cần kiểm tra exact duplicates và near-duplicates trước khi tách retrieval pool, validation set và test set.
- **Multi-label và attack taxonomy:** cần thống nhất cách xử lý multi-label rows và tập nhãn dùng cho classification.
- **Annotation quality và ngữ cảnh:** cùng URL path có thể có nhãn khác nhau do method, headers, body hoặc annotation noise; cần kiểm tra đầy đủ request trước khi kết luận.

Các lớp đang được cân nhắc cho phạm vi ban đầu gồm **Normal/Benign, SQL Injection, Path Traversal, Code Injection, HTTP Response Splitting** và **OS Command Injection**. Dataset và taxonomy cuối cùng chưa được chốt.

## Cấu trúc repository

```text
.
├── README.md
├── label-aware-retrieval-roadmap.md   # Lộ trình nghiên cứu tổng thể
├── october_plan.md                   # Kế hoạch tháng 10/2026
├── link_papers.md                    # Danh mục papers tham khảo
├── sr_bh_2020_khao_sat.ipynb          # Notebook khảo sát SR-BH 2020
├── data_overview/
│   └── sr_bh_eda.ipynb               # Notebook EDA cơ bản
├── examples/
│   └── eda_dataset.py                # Script EDA mẫu cho schema request/label
├── mini-reports/                     # Đề cương, khảo sát và báo cáo tiến độ
│   ├── checklists/                   # Checklist thực thi
│   └── old/                          # Tài liệu phân tích trước đây
└── papers/                           # Các paper PDF đã lưu
```

## Chạy notebook EDA

Các bước dưới đây dành cho notebook hiện có. Repository chưa có lệnh chạy pipeline end-to-end.

### 1. Chuẩn bị môi trường

Kế hoạch dự án hướng đến **Python 3.10**. Tại thư mục gốc repository, tạo virtual environment và cài các thư viện dùng trong notebook:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pandas matplotlib seaborn jupyterlab
```

Trên Windows PowerShell, thay lệnh kích hoạt bằng:

```powershell
.venv\Scripts\Activate.ps1
```

Danh sách trên chỉ phục vụ EDA, chưa phải dependency set được khóa phiên bản cho toàn bộ dự án.

### 2. Chuẩn bị dataset

Tự chuẩn bị file `data_capec_multilabel.csv`, sau đó sửa đường dẫn đọc dữ liệu trong notebook tương ứng:

- [sr_bh_2020_khao_sat.ipynb](sr_bh_2020_khao_sat.ipynb): sửa biến `DATA_PATH`; giá trị hiện tại là `../dataset/SR-BH 2020/data_capec_multilabel.csv`.
- [data_overview/sr_bh_eda.ipynb](data_overview/sr_bh_eda.ipynb): sửa đường dẫn trong `pd.read_csv("data_capec_multilabel.csv")` theo vị trí file và working directory của kernel.

### 3. Mở notebook

```bash
jupyter lab
```

Chọn kernel của virtual environment vừa tạo và chạy lần lượt các cell. Một số cell khảo sát truy cập mẫu cụ thể trong dataset, vì vậy cần kiểm tra lại điều kiện chọn mẫu nếu dùng dữ liệu khác.

Script [examples/eda_dataset.py](examples/eda_dataset.py) là ví dụ cho file `dataset.csv` có hai cột `request` và `label`. Muốn dùng với CAPEC cần điều chỉnh đường dẫn và schema; script chưa đọc trực tiếp các cột multi-label của CAPEC.

## Kế hoạch thực nghiệm

1. Chốt dataset, attack taxonomy và protocol đánh giá.
2. Hoàn thiện preprocessing, deduplication và data split; kiểm tra leakage giữa các tập.
3. Xây dựng embedding module, FAISS index, LLM client, prompt builder và output parser; chạy Pipeline A và B.
4. Đo chất lượng retrieval của Pipeline B, triển khai zero-shot prior và label-aware reranker cho Pipeline C.
5. So sánh các pipeline trên cùng test set; thực hiện ablation và phân tích per-class, hard cases, latency và token usage.

Các metrics dự kiến gồm **Accuracy, Macro-F1, Weighted-F1, Precision/Recall/F1 per class** và **LCR@k**. LCR@k đo tỷ lệ demonstrations có nhãn trùng với ground-truth query label khi đánh giá offline; cần đọc cùng classification metrics vì mức độ trùng nhãn không tự bảo đảm demonstrations hữu ích hơn.

Các công nghệ trong thiết kế gồm **Sentence Transformers**, **FAISS** và LLM qua **Ollama** hoặc API. Đây là lựa chọn dự kiến; repository chưa tích hợp các thành phần này.

## Tài liệu dự án

| Tài liệu | Nội dung |
| --- | --- |
| [Đề cương nghiên cứu](mini-reports/de_cuong_nghien_cuu_label_aware_retrieval.md) | Bối cảnh, research questions và thiết kế thực nghiệm |
| [Roadmap tổng thể](label-aware-retrieval-roadmap.md) | Các phase, milestones và tiêu chí kiểm tra |
| [Kế hoạch tháng 10/2026](october_plan.md) | Mục tiêu và công việc theo tuần |
| [Kế hoạch tháng 10 chi tiết](mini-reports/october_plan_chi_tiet.md) | Hướng dẫn triển khai chi tiết |
| [Dataset Survey](mini-reports/p1_dataset_analysis.md) | Thống kê và các vấn đề chất lượng dữ liệu CAPEC |
| [Related Work](mini-reports/p1_related_work.md) | Tổng hợp các hướng nghiên cứu liên quan |
| [Systematic Search Log](mini-reports/p1_systematic_search_log.md) | Nhật ký khảo sát tài liệu |
| [Danh mục papers](link_papers.md) | Các paper tham khảo |
| [Checklist nghiên cứu](mini-reports/checklists/checklist_thuc_thi_nghien_cuu.md) | Các bước thực thi nghiên cứu |

Một số tài liệu giai đoạn đầu còn đề cập phương án khác. Khi triển khai, cần thống nhất lại với phạm vi inference-only và LLM zero-shot prior đã nêu trong kế hoạch.
