# Task 1 — Chọn dataset, xử lý dữ liệu và khóa protocol cho Pipeline A

Ngày lập: 19/10/2026. Đây là kế hoạch thực hiện, chưa xác nhận các bước đã hoàn thành.

**Cập nhật thực hiện 19/10:** đã có code, dữ liệu thật, split v1 và kiểm thử; review phát hiện annotation đáng nghi nên quyết định dataset cho benchmark cuối cùng còn mở. Xem [báo cáo Task 1 và mục Trả lời câu hỏi của giảng viên](../progress/task_1_dataset_va_protocol.md) để biết kết quả và checklist hiện tại.

Mục tiêu trong ngày: hoàn thành task này trước, sau đó thực hiện [Task 2 — Pipeline A0/A1 và kiểm thử](task_2_pipeline_a_va_kiem_thu.md). Hai task dự kiến tổng cộng khoảng 8 giờ khi có hai người phối hợp, dataset tải được và backend LLM sẵn sàng. Nếu thực hiện tuần tự bởi một người, cần điều chỉnh thời lượng theo thực tế.

## Kết quả cần đạt

Chọn được một dataset HTTP request có nhãn, khóa taxonomy và tạo dữ liệu có thể tái lập để Pipeline A0 zero-shot và A1 fixed few-shot dùng chung. Giữ final test riêng cho benchmark A/B/C về sau.

Repo hiện có notebook EDA và tài liệu; chưa có implementation pipeline. File CSV không được lưu trong repository. Các thống kê EDA cũ cần kiểm tra lại trên file thực tế.

## Trình tự thực hiện — dự kiến 3–4 giờ

### 1. Xác minh và chọn dataset — tối đa 1 giờ

- Ưu tiên **SR-BH 2020/CAPEC**, file `data_capec_multilabel.csv`, vì repo đã có notebook khảo sát và nhãn phù hợp đề tài.
- Xác minh nguồn tải, phiên bản, điều kiện sử dụng, checksum SHA-256, schema và số bản ghi thực tế. Không suy ra giấy phép dataset từ giấy phép bài báo.
- Đối chiếu notebook `src/notebooks/sr_bh_2020_khao_sat.ipynb`: output cũ ghi 14 cột nhãn gồm Normal, trong khi README ghi 13; phát hiện nhãn từ schema thực tế, không hard-code số cột.
- Taxonomy dự kiến: Normal, SQL Injection, Path Traversal, Code Injection, HTTP Response Splitting và OS Command Injection. Không tự bổ sung nhãn XSS hoặc đồng nhất các nhãn command injection khác nhau.
- Kiểm tra khoảng 10 request mỗi lớp và các trường hợp mâu thuẫn. Xem đủ method, URI, headers và body trước khi đánh giá annotation.
- Chốt lớp theo số nhóm độc lập và chất lượng annotation. Nếu không đủ support cho validation/test thì giảm lớp trước khi chạy model; ghi lý do và số lượng thực tế.
- Nếu không lấy được CSV, ghi rõ nguồn đã thử và thông tin cần người dùng cung cấp. Có thể tiếp tục xây fixture và code, nhưng chưa đánh dấu dataset đã được chọn/xác minh xong.

Nguồn tham khảo: [bài báo gốc của tác giả](https://reunir.unir.net/entities/publication/e6af07db-49fd-4521-8581-4776826a4a72/full). Khi triển khai, xác minh đường dẫn dữ liệu từ nguồn gốc và ghi vào dataset decision.

### 2. Chuẩn hóa và lọc dữ liệu

- Với phạm vi single-label hôm nay, chỉ giữ bản ghi có đúng một nhãn trên **toàn bộ taxonomy gốc**, rồi lọc các lớp được chọn. Không biến lớp ngoài phạm vi thành Normal.
- Báo riêng số bản ghi không nhãn, đa nhãn, nhãn không hợp lệ, ngoài phạm vi và thiếu dữ liệu thiết yếu.
- Tạo `request_text` từ method, URI/query, các request headers được chọn và body. Chốt danh sách trường, thứ tự serialization, xử lý missing và giới hạn độ dài.
- Giữ payload encoding; không tự động URL-decode hoặc xóa ký tự có thể mang tín hiệu tấn công. Giữ liên kết tới dữ liệu gốc.
- Không đưa label, response hoặc metadata gán nhãn vào input. Timestamp/IP chỉ dùng cho audit nếu cần, không mặc định đưa vào prompt.
- Xác định request trùng theo nội dung đầy đủ đã chuẩn hóa. Loại riêng các request giống hệt nhưng mâu thuẫn nhãn; không coi cùng URL khác nhãn là mâu thuẫn ngay lập tức.

### 3. Deduplication và split theo nhóm

- Group exact duplicates và near-duplicates theo quy tắc ghi rõ trước khi split. Không chỉ random split theo row hoặc chỉ hash URL.
- Xây quy tắc near-duplicate phù hợp dữ liệu; audit mẫu nhóm thủ công để tránh gộp các payload tấn công khác nhau quá mạnh. Ghi giới hạn của quy tắc.
- Mục tiêu pool/validation/test khoảng **70/15/15 theo nhóm**, ưu tiên giữ support mỗi lớp. Ghi tỷ lệ thực tế nếu không thể đạt tỷ lệ mục tiêu.
- Tách một development subset khỏi pool để smoke test và sửa prompt; loại các nhóm development khỏi demonstration pool còn lại. Development, demonstration pool, validation và test phải tách biệt theo nhóm.
- Seed cố định, ví dụ `42`; lưu manifest IDs và hash dữ liệu. Giữ split này cho A/B/C.
- Ngân sách ban đầu: pool 2.000–5.000 mẫu; development khoảng 20–50; validation pilot 100–200; final test dự kiến 500–1.000 nếu support cho phép. Đây là mục tiêu, không tạo mẫu giả hoặc phá group để đủ số lượng.
- Chọn subset theo seed trước khi chạy; lưu phân bố lớp và quy tắc lấy mẫu. Tách rõ tập split đầy đủ và subset dùng cho pilot.
- Không dùng nhãn final test để sửa prompt/chọn cấu hình; chỉ audit cấu trúc và support dữ liệu theo protocol.

## Hợp đồng bàn giao cho Task 2

Định dạng JSONL hoặc Parquet phải được thống nhất và ghi lại. Mỗi bản ghi gồm:

| Trường | Ý nghĩa |
| --- | --- |
| `request_id` | ID ổn định, duy nhất |
| `group_id` | Nhóm dùng chống leakage |
| `request_text` | Nội dung HTTP đã chuẩn hóa |
| `label` | Nhãn chuẩn hóa theo mapping đã khóa; chỉ evaluator được đọc nhãn query |

Các đường dẫn dưới đây là **đề xuất để triển khai**, chưa phải artifact đã tồn tại:

- `reports/protocol/dataset_decision.md`: nguồn, quyền sử dụng, taxonomy, chính sách lọc và giới hạn.
- `src/configs/data.yaml`: seed, trường input, normalization, grouping và sampling.
- `src/preprocessing/`: code preprocessing, deduplication và split.
- `src/data/processed/`: dữ liệu và split manifests; không mặc định commit dữ liệu thô hoặc dữ liệu lớn.
- `src/artifacts/data/`: class distribution, filter counts và leakage audit.
- Dependency specification và hướng dẫn chạy preprocessing từ repo root.

## Kiểm thử và điều kiện hoàn thành

| Kiểm thử | Điều kiện đạt |
| --- | --- |
| Schema/labels | Phát hiện thiếu cột, nhãn ngoài 0/1, zero-label và multi-label; đếm đúng các nhóm bị loại |
| Request builder | Missing không thành chuỗi `nan`; giữ Unicode, payload encoded; xử lý request dài theo quy tắc |
| Trùng lặp/mâu thuẫn | Fixture kiểm chứng request giống hệt khác nhãn được cách ly; cùng URL khác body không bị coi là giống hệt |
| Split/leakage | Không giao nhau về ID, exact hash hoặc group giữa development, pool, validation và test |
| Near-duplicate audit | Có quy tắc, kiểm tra nhóm mẫu và báo cáo giới hạn; không tuyên bố hết leakage chỉ vì exact hashes khác nhau |
| Tái lập | Cùng input, config và seed tạo lại cùng IDs và split manifests |

Task hoàn thành khi có dataset decision, dữ liệu thật được xác minh, taxonomy và schema đã khóa, các split và báo cáo audit, các test đạt, cùng lệnh chạy lại. Nếu thiếu dữ liệu thật thì ghi trạng thái còn thiếu; fixture chỉ chứng minh code hoạt động.

Báo cáo cuối Task 1 phải có mục **Trả lời câu hỏi của giảng viên**, dựa trên câu hỏi nguyên văn người dùng cung cấp. Nếu chưa có câu hỏi, ghi rõ đang thiếu; các câu hỏi chuẩn bị do Codex đề xuất không được trình bày như câu hỏi thực tế của giảng viên.

## Prompt cho phiên Codex tiếp theo

```text
Hãy cùng tôi thực hiện Task 1 trong reports/plan/task_1_dataset_va_protocol_pipeline_a.md.
Đọc AGENTS.md nếu có, kế hoạch này và notebook EDA liên quan; kiểm tra hiện trạng trước khi sửa.
Mục tiêu là chọn/xác minh dataset, khóa taxonomy, triển khai preprocessing và split chống leakage,
chạy các kiểm thử có ý nghĩa và xuất đủ artifact bàn giao cho Task 2.
Trao đổi bằng tiếng Việt. Hỏi sớm thông tin thực sự còn thiếu và tiếp tục các phần độc lập trong lúc chờ.
Tiến hành các bước đã được cho phép; giữ các thay đổi hiện có của tôi. Không chỉ trả về một kế hoạch mới.
Không chạy final benchmark hoặc dùng final test để chỉnh prompt. Không đánh dấu hoàn thành bằng dữ liệu giả.
Cuối phiên báo rõ artifact, lệnh tái lập, kết quả test và phần còn thiếu.
```
