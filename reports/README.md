# Bắt đầu đọc repository từ đây

**Pipeline A0:** [Bàn giao, cấu hình và lệnh chạy mock/API](docs/handoff/pipeline_a0_handoff.md).

**Đọc lại công việc và setup:** [Hướng dẫn từ đầu, .venv, .env và API miễn phí để smoke test](reports/setup_va_doc_lai.md). Template công khai: [env.example](env.example); sao chép sang `.env` và chỉ điền key ở máy mình. CLI không tự nạp `.env`; hướng dẫn có lệnh nạp trước khi chạy.

Repository được chia thành hai phần: **`src/` chứa code và dữ liệu**, **`reports/` chứa tài liệu để đọc lại**. Các lệnh trong tài liệu chạy từ thư mục gốc repo, nơi có cả hai thư mục này.

## Thứ tự đọc đề xuất

| Thứ tự | Tài liệu | Nội dung |
| --- | --- | --- |
| 1 | [Tổng quan đề tài](reports/project_overview.md) | Câu hỏi nghiên cứu, phạm vi và A/B/C |
| 2 | [Khảo sát SR-BH 2020](reports/surveys/khao_sat_sr_bh_2020.md) | Đủ 7 câu hỏi giảng viên, dữ liệu thật và payload |
| 3 | [Khảo sát CSIC 2010](reports/surveys/khao_sat_csic_2010.md) | Nhãn, split nguồn và tính phù hợp với bài toán |
| 4 | [Kết quả Task 1](reports/progress/task_1_dataset_va_protocol.md) | Việc đã làm, kiểm thử và vấn đề còn mở |
| 5 | [Protocol và cách chạy dữ liệu](reports/protocol/README.md) | Lệnh tái lập, representation, grouping và manifests |
| 6 | [Quyết định dataset](reports/protocol/dataset_decision.md) | Nguồn, taxonomy và giới hạn annotation |
| 7 | [Kế hoạch Task 1](reports/plan/task_1_dataset_va_protocol_pipeline_a.md) / [Task 2](reports/plan/task_2_pipeline_a_va_kiem_thu.md) | Checklist và prompt tiếp tục với Codex |
| 8 | [Danh mục papers](reports/references/link_papers.md) | Tài liệu tham khảo và các PDF cùng thư mục |

## Cây thư mục

```text
.
├── src/
│   ├── preprocessing/       # Module xử lý dữ liệu, khảo sát và tạo báo cáo
│   ├── pipeline_a0/          # Zero-shot runner, backend, parser, resume và metrics
│   ├── data/
│   │   ├── raw/             # CSV/HTTP gốc, không track Git
│   │   └── processed/       # Dữ liệu đã xử lý, splits và manifests
│   ├── configs/             # Cấu hình, nguồn tải và lựa chọn ví dụ
│   ├── tests/               # Kiểm thử tự động
│   ├── notebooks/           # EDA notebooks và script ví dụ
│   ├── artifacts/           # JSON evidence, audit, checksum và logs
│   ├── requirements-data.txt
│   └── requirements-survey.txt
├── docs/handoff/             # Checkpoint A0 theo yêu cầu bàn giao
├── env.example               # Template công khai, không có key thật
└── reports/
    ├── setup_va_doc_lai.md  # Đọc lại, môi trường và API smoke test
    ├── project_overview.md  # Tổng quan nghiên cứu
    ├── mo_ta_de_tai.md      # Mô tả để gửi lên hệ thống
    ├── surveys/             # Khảo sát dataset; hình trong figures/
    ├── progress/            # Báo cáo tiến độ và kết quả Task 1
    ├── protocol/            # Quyết định dataset và hướng dẫn tái lập
    ├── plan/                # Kế hoạch và task tiếp theo
    └── references/          # Papers, PDF và danh mục tham khảo
```

Các file quản lý Git và cấu hình hệ thống ẩn giữ ở gốc repo. Dữ liệu và split manifests được chuyển vị trí, giữ nguyên nội dung/hash; các đường dẫn trong tài liệu và metadata được cập nhật. Hash mã nguồn trong evidence cũ vẫn là hash của lần chạy lịch sử, trước khi đổi vị trí module. Nhật ký chuyển thư mục: `src/artifacts/layout_migration.json`.

## Lệnh kiểm tra nhanh

```bash
python3 -m unittest discover -s src/tests -v
python3 -m src.preprocessing.prepare --help
python3 -m src.preprocessing.csic_2010 --help
```

## Theo dõi công việc

**Khảo sát dữ liệu thật:** [SR-BH 2020 — trả lời đủ 7 câu hỏi giảng viên, payload nguyên văn và Figure minh họa](reports/surveys/khao_sat_sr_bh_2020.md). Kết quả triển khai preprocessing/split nằm trong [báo cáo Task 1](reports/progress/task_1_dataset_va_protocol.md).

**Khảo sát bổ sung:** [CSIC 2010 — ba file HTTP thật, nhãn nguồn, split, payload và motivating example](reports/surveys/khao_sat_csic_2010.md).

Dùng kế hoạch 4 tuần bên dưới để theo dõi mốc chung; hai task Pipeline A chia nhỏ công việc thực hiện. Các khảo sát, kết quả và protocol được liên kết ở đầu trang.

## Ba tài liệu cần dùng

| Thứ tự | Tài liệu | Khi nào dùng |
| --- | --- | --- |
| 1 | [Kế hoạch 4 tuần cho 2 người](plan/ke_hoach_trien_khai_4_tuan.md) | Theo dõi phân công, deadline và sản phẩm mỗi tuần; đây là kế hoạch chính |
| 2 | [Báo cáo định hướng và mẫu hằng tuần](reports/progress/bao_cao_dinh_huong_va_mau_hang_tuan.md) | Chuẩn bị buổi gặp thầy tuần này và cập nhật mỗi tuần |
| 3 | [Mô tả đề tài](reports/mo_ta_de_tai.md) | Gửi mô tả lên hệ thống hoặc giới thiệu ngắn gọn hướng nghiên cứu |

## Việc cần làm trước tiên

- [ ] Hai người thống nhất vai trò TV1/TV2 và quỹ thời gian 20–25 giờ/người/tuần.
- [ ] Chuẩn bị báo cáo định hướng, xin lịch gặp thầy và trao đổi kế hoạch thực nghiệm.
- [ ] Xác nhận dataset, kiểm tra annotation và chốt taxonomy.
- [ ] Setup môi trường, thử LLM trên 20–50 request development và đo latency.
- [ ] Chốt interface module; chia task tuần 1 với deadline và sản phẩm cụ thể.

## Các mốc chính

| Hạn nội bộ | Sản phẩm |
| --- | --- |
| 22/10/2026 | Dataset/protocol, split và baseline A0 đầu tiên |
| 29/10/2026 | Baselines và Pipeline C chạy trên validation |
| 05/11/2026 | Validation, ablation và cấu hình cuối đã khóa |
| 12/11/2026 | Final benchmark và phân tích kết quả chính |

Nếu chậm, giảm các thực nghiệm mở rộng theo kế hoạch chính; giữ kiểm tra leakage, các đối chứng cần thiết và thời gian giảng viên review.
