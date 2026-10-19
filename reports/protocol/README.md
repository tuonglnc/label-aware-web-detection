# Chuẩn bị dữ liệu cho Pipeline A

Xem [khảo sát dữ liệu thật trả lời 7 câu hỏi giảng viên](../surveys/khao_sat_sr_bh_2020.md) để có bảng lớp, schema, payload gốc và motivating Figure. Các script khảo sát và lệnh tái lập nằm cuối báo cáo đó.

Chạy từ thư mục gốc repo với Python >= 3.10. Module dữ liệu chỉ dùng standard library, không cần pip install. Phiên bản runtime thực tế được lưu trong `src/artifacts/data/summary.json`.

## Tải dữ liệu gốc

```bash
mkdir -p src/data/raw
curl -fL --retry 2 'https://dataverse.harvard.edu/api/access/datafile/6319496' -o src/data/raw/data_capec_multilabel.csv
```

Nguồn: [Harvard Dataverse, DOI 10.7910/DVN/OGOIXX](https://doi.org/10.7910/DVN/OGOIXX). Metadata gốc được lưu ở `src/artifacts/data/source_metadata.json`; dataset version 1.2, file ID 6319496. File khoảng 436 MB. Preprocessor kiểm MD5 từ metadata trước khi xử lý, đồng thời tính SHA-256 để truy vết.

## Test và chạy preprocessing

```bash
python3 -m unittest discover -s src/tests -v
python3 -m src.preprocessing.prepare --config src/configs/data.json
python3 -m src.preprocessing.verify --input src/data/raw/data_capec_multilabel.csv
```

Mặc định ghi dữ liệu vào `src/data/processed/sr_bh_v1` và audit vào `src/artifacts/data`. Output dữ liệu phải là thư mục mới/rỗng để không vô tình thay split đã khóa. Để chạy lại và so checksum:

```bash
python3 -m src.preprocessing.prepare --config src/configs/data.json --output src/data/processed/sr_bh_reproduce --artifacts src/artifacts/data/reproduce
```

So sánh hai file `checksums.json`; các hash phải giống nhau nếu code, input và config không đổi. Config dùng JSON để không cần dependency YAML; nội dung bao gồm seed, mapping, headers, grouping và ngân sách subset.

## Hợp đồng dữ liệu

- Các file `pool.jsonl`, `development.jsonl`, `validation.jsonl`, `test.jsonl` chứa request đã exact-dedup, group-disjoint. `pool` đã trừ development.
- Mỗi dòng có `request_id`, `group_id`, `request_text`, `label`; bổ sung `exact_hash`, `endpoint_hash`, `source_row`, `source_occurrences` để audit. `source_row` là số thứ tự record CSV cộng dòng header, không nhất thiết là số dòng vật lý nếu field chứa newline.
- `request_text` là JSON string gồm method, URI, protocol, headers và body. Đây là cách giữ ranh giới trường khi payload chứa newline; Task 2 phải dùng nguyên representation này.
- `request_id`/`exact_hash` là SHA-256 của `request_text`, không phụ thuộc label. Giữ trường trống dưới dạng chuỗi rỗng. Không URL-decode, đổi chữ hoa/thường hoặc cắt request; request serialized dài hơn 32.768 ký tự bị loại và được đếm.
- Các manifest đầy đủ lưu IDs/group/label/source record. `*_subset.jsonl` là subset cân bằng theo lớp ở mức có thể, random trong lớp với seed cố định. Đây là pilot có kiểm soát, không đại diện tỷ lệ traffic tự nhiên. Không bắt buộc số record development đúng 30 vì phải dành trọn nhóm.
- Các label query chỉ dành cho evaluator; Task 2 không truyền nguyên record chứa label vào prompt/model.
- `test_subset.jsonl` được tạo để khóa ngân sách benchmark tương lai; chưa được chạy inference hoặc dùng chỉnh prompt.

## Quy tắc grouping và giới hạn

Group key được tính từ **toàn bộ request representation**, thay chuỗi hex dài >=16 ký tự và số thập phân độc lập bằng marker. Ký tự số ngay sau `%` không được mask như decimal, không decode URL. Chỉ group key bị biến đổi; model input giữ nguyên.

Quy tắc này gộp các biến thể ID/nonce/số đơn giản, không phải bộ phát hiện mọi semantic near-duplicate. Nó có thể gộp quá mức khi con số mang ý nghĩa attack; group lớn vẫn phải nằm trọn một split. Nó cũng có thể bỏ sót request tương tự nhưng khác User-Agent/cookie hoặc cách viết payload. Audit có thống kê endpoint overlap giữa các split để nêu giới hạn; endpoint overlap không đồng nghĩa exact leakage.

Split stratify theo tập nhãn xuất hiện trong mỗi group, shuffle bằng seed và chia khoảng 70/15/15 theo **số nhóm trong từng stratum**. Tỷ lệ record có thể khác do kích thước nhóm. Nhóm chứa nhiều lớp không bị tách. Development dành trọn các nhóm từ pool cho đến khi đủ tối thiểu cấu hình mỗi lớp; không giữ lại thành viên cùng nhóm trong pool.

## Review trước Task 2

- `src/artifacts/data/manual_review.jsonl`: khoảng 10 mẫu/lớp từ development/pool để đọc đầy đủ request và ghi nhận annotation; không lấy final test.
- `src/artifacts/data/group_review.jsonl`: tám nhóm lớn nhất cộng tối đa hai nhóm mỗi lớp từ development/pool (tối đa 20 nhóm), tối đa ba ví dụ mỗi nhóm để rà quy tắc grouping. Đây chỉ là spot-check, không phải chứng nhận toàn bộ nhóm.
- `src/artifacts/data/quarantine.jsonl`: IDs và số record của request mâu thuẫn annotation, kể cả mâu thuẫn với bản ghi đa nhãn hoặc ngoài phạm vi.
- `summary.json`: số lượng lọc, schema, class/group support, warnings, checksum. Preprocessor luôn để trạng thái review pending; kết luận và quyết định bàn giao được ghi riêng trong báo cáo Task 1, không giả lập human approval.

Dữ liệu thô, dữ liệu processed và review có payload được gitignore. Giữ summary/audit/config để review code; không commit các file dữ liệu lớn.
