# Quyết định dataset cho Pipeline A

Ngày xác minh: 19/10/2026. Trạng thái: **đã xác minh nguồn và xử lý dữ liệu thật; SR-BH 2020 là ứng viên pilot, chưa xác nhận phù hợp làm benchmark cuối cùng do phát hiện annotation đáng nghi**. Chưa nhận quyết định của người dùng về việc giữ dataset cho pilot hoặc khảo sát nguồn khác.

## Nguồn và khả năng sử dụng

| Thuộc tính | Giá trị xác minh |
| --- | --- |
| Dataset | SR-BH 2020 multi-label dataset |
| Nguồn gốc | [Harvard Dataverse, DOI 10.7910/DVN/OGOIXX](https://doi.org/10.7910/DVN/OGOIXX) |
| Dataset version | 1.2; phát hành 06/06/2022 |
| File | `data_capec_multilabel.csv`, file ID 6319496, không restricted |
| Download | [Dataverse datafile API](https://dataverse.harvard.edu/api/access/datafile/6319496) |
| Giấy phép dataset | CC0 1.0, lấy từ metadata dataset; không suy ra từ giấy phép bài báo |
| Dung lượng | 436.437.661 byte |
| MD5 | `173ec515308bdce5aec19cfd5b792596`, khớp metadata gốc |
| SHA-256 | `9c73c90ce6564ae48b14f7179cd864d037a6a130ef69c68c1626ec5d7ce4a910` |
| Schema thực tế | 907.815 record, 38 cột; 14 cột nhãn gồm Normal và 13 CAPEC |

Metadata nguồn được lưu tại `src/artifacts/data/source_metadata.json`. Mô tả nguồn ghi 907.814 request và cách đếm nhãn không nhất quán với CSV; kết quả báo cáo dùng file có checksum ở trên. README cũ ghi 13 cột nhãn gồm Normal nên không dùng số này để lập trình.

Theo mô tả do tác giả cung cấp trong metadata, dữ liệu được thu từ WordPress trong 12 ngày tháng 7/2020; ModSecurity 2.9.2/CRS 3.3.0 hoạt động ở detection-only, sau đó tác giả xử lý annotation thủ công/bán tự động. Điều này không bảo đảm từng nhãn đều đúng đối với mục tiêu nhận diện attack intent của nghiên cứu hiện tại. [Bài báo gốc](https://reunir.unir.net/entities/publication/e6af07db-49fd-4521-8581-4776826a4a72/full).

## Lý do ưu tiên và phạm vi

Dataset có HTTP request với nhãn loại tấn công, phù hợp thiết kế so sánh demonstrations có nhãn; repo đã có EDA, giúp giảm thời gian tích hợp. Chưa khẳng định đây là dataset tốt nhất. [CSIC 2010 đã được khảo sát trên file thật](../surveys/khao_sat_csic_2010.md), nhưng bản raw đó chỉ cung cấp nhãn Normal/Anomalous, nên không thay trực tiếp taxonomy CAPEC multiclass bằng nhãn gốc.

Giữ sáu lớp dự kiến dưới đây cho bản xử lý kỹ thuật v1 vì tất cả có đủ support độc lập theo quy tắc grouping hiện tại. Đây chưa phải quyết định xác nhận chất lượng annotation của sáu lớp.

| Nhãn gốc | Nhãn chuẩn hóa |
| --- | --- |
| 000 - Normal | `NORMAL` |
| 66 - SQL Injection | `SQL_INJECTION` |
| 126 - Path Traversal | `PATH_TRAVERSAL` |
| 242 - Code Injection | `CODE_INJECTION` |
| 34 - HTTP Response Splitting | `HTTP_RESPONSE_SPLITTING` |
| 88 - OS Command Injection | `OS_COMMAND_INJECTION` |

Không bổ sung XSS thành lớp riêng, không gộp CAPEC-248 vào CAPEC-88. Chỉ giữ request đúng một nhãn trên toàn bộ 14 cột gốc, sau đó lọc sáu lớp; không biến lớp ngoài phạm vi thành Normal. Request trùng đầy đủ nhưng khác tập nhãn bị cách ly, kể cả một phía là multi-label hoặc lớp ngoài phạm vi. Không tự sửa nhãn theo regex hoặc theo dự đoán LLM.

## Phát hiện cần giải quyết trước khi khóa benchmark

Khảo sát bổ sung theo 7 câu hỏi giảng viên đã hoàn tất trên toàn CSV: [báo cáo chi tiết và payload nguyên văn](../surveys/khao_sat_sr_bh_2020.md). Đã tìm được cặp Normal/SQLi cùng method/protocol/headers/body, chỉ khác chuỗi `+AND+1%3D1` trong URI; đây là motivating example, không phải kết quả retrieval hoặc bằng chứng đã giải quyết annotation noise.

Review 60 request từ development/pool, 10 mẫu mỗi lớp, cho thấy **5/10 mẫu Normal chứa payload đáng nghi**; ví dụ có `sleep`, `cat /etc/passwd`, hoặc `<script>`. Đây là đánh giá kỹ thuật của Codex, không phải kết quả adjudication của chuyên gia và không phải ước lượng noise rate toàn dataset. Một số payload của các lớp attack cũng có thể phù hợp nhiều taxonomy khác nhau.

Vì vậy, metric dựa trên annotation nguồn trước mắt đo mức độ đồng thuận với nhãn nguồn. Chưa thể xem mọi sai khác của model là lỗi phát hiện tấn công thực tế. Không loại riêng các mẫu đáng nghi vừa đọc để làm đẹp kết quả, không dùng final test để quyết định relabel.

Hai hướng cần thống nhất với người dùng/giảng viên:

1. Giữ SR-BH cho pilot vận hành A0/A1 theo nhãn gốc, báo noise và giới hạn rõ; thiết kế annotation audit/adjudication độc lập trước khi khóa benchmark.
2. Khảo sát dataset khác trước Task 2 nếu yêu cầu nghiên cứu cần ground truth attack intent đáng tin hơn. Chưa chọn dataset thay thế khi chưa kiểm tra nguồn/schema/quyền sử dụng.

## Protocol kỹ thuật v1

Chi tiết thực thi nằm trong [hướng dẫn dữ liệu](README.md) và `src/configs/data.json`. Config JSON thay cho YAML để chỉ cần Python standard library.

- Input chỉ gồm request fields; response, timestamp, IP và label không được serialize vào `request_text`.
- Giữ payload encoding, Unicode và ranh giới các trường bằng JSON serialization. Không cắt âm thầm; loại và đếm request vượt 32.768 ký tự serialized.
- Exact hash theo toàn bộ representation. Near-duplicate grouping dùng mask số độc lập và hex dài trên bản sao representation, không đổi input model.
- Group split khoảng 70/15/15; dành development từ pool theo trọn nhóm. Không giao nhau về IDs/exact hash/group theo quy tắc đã định nghĩa.
- Endpoint và semantic near-duplicates có thể còn giao nhau. Đây là giới hạn cần công bố, không gọi audit hiện tại là bảo đảm hết mọi leakage.
- Subsets cố định: pool 3.000, validation 200, test 600; lấy cân bằng lớp, random trong lớp bằng seed 42. Development thực tế 30 mẫu.
- Final test mới được tạo và audit cấu trúc; chưa chạy inference hoặc chỉnh prompt/model.

Các kết quả đếm, kiểm thử và checklist được ghi trong [báo cáo Task 1](../progress/task_1_dataset_va_protocol.md).
