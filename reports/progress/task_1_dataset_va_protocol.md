# Báo cáo Task 1 — Dataset và protocol cho Pipeline A

Ngày thực hiện: 19/10/2026. **Đã có implementation, dữ liệu thật và split v1; việc xác nhận dataset làm benchmark cuối cùng còn mở vì annotation đáng nghi.** Task 2 chưa được triển khai trong phiên này.

## Sản phẩm và nguồn

- [Dataset decision](../protocol/dataset_decision.md): nguồn gốc, phiên bản, giấy phép, checksum, taxonomy và phát hiện chất lượng.
- [Hướng dẫn tái lập](../protocol/README.md): lệnh tải, preprocessing, test và hợp đồng dữ liệu.
- `src/configs/data.json`: seed 42, sáu lớp, request fields, grouping và subset budgets.
- `src/preprocessing/prepare.py`: xác minh checksum, đọc CSV, lọc nhãn, exact-dedup, cách ly conflict, group split và xuất artifact.
- `src/preprocessing/verify.py`: kiểm tra độc lập checksum, representation/hash, manifests, subset membership và group disjointness.
- `src/tests/test_data.py`: kiểm thử bằng fixture; dữ liệu fixture không được dùng làm kết quả benchmark.
- `src/artifacts/data/`: metadata nguồn, summary, leakage audit, kết quả test và các review candidates.
- `src/data/processed/sr_bh_v1/`: full splits/manifests, config snapshot, checksums và subsets cho các bước sau; dữ liệu lớn được gitignore.

Dataset SR-BH 2020 được tải từ [Harvard Dataverse](https://doi.org/10.7910/DVN/OGOIXX), dataset version 1.2, file ID 6319496, giấy phép CC0 1.0 xác minh từ metadata dataset. File 436.437.661 byte khớp MD5 nguồn. SHA-256: `9c73c90ce6564ae48b14f7179cd864d037a6a130ef69c68c1626ec5d7ce4a910`.

CSV thực tế có **907.815 record, 38 cột, 14 cột nhãn gồm Normal và 13 CAPEC**. Đây là kết quả đọc lại, thay cho số cột nhãn chưa chính xác trong README cũ.

## Kết quả lọc và deduplication

| Chỉ số | Số lượng |
| --- | ---: |
| Record gốc | 907.815 |
| Đúng một nhãn thuộc sáu lớp dự kiến, trước kiểm tra nội dung/conflict | 826.884 |
| Multi-label trên toàn taxonomy gốc | 9.238 |
| Single-label ngoài phạm vi sáu lớp | 71.693 |
| Zero-label / invalid-label / malformed row | 0 / 0 / 0 |
| Thiếu method hoặc URI | 2 |
| Request unique mâu thuẫn tập nhãn, trên toàn dữ liệu có annotation hợp lệ | 288 |
| Record thuộc các request mâu thuẫn trên | 2.331 |
| Record thuộc request hợp lệ còn giữ, trước bỏ exact duplicate | 824.987 |
| Exact duplicate rows bỏ trong phần giữ lại | 358.720 |
| Request unique cuối cùng | **466.267** |

Các chỉ số conflict và thiếu dữ liệu có thể giao với multi-label/ngoài phạm vi; không cộng tất cả các dòng trong bảng thành một chuỗi loại trừ độc lập. `summary.json` ghi rõ các counters theo từng giai đoạn. Không coi mọi request cùng URL là trùng: body và headers vẫn tham gia exact hash.

## Phân bố sau xử lý

| Lớp | Pool | Development | Validation đầy đủ | Test đầy đủ | Nhóm độc lập trên toàn phần giữ lại |
| --- | ---: | ---: | ---: | ---: | ---: |
| Normal | 120.184 | 5 | 25.700 | 25.459 | 155.443 |
| SQL Injection | 170.406 | 5 | 36.513 | 36.497 | 240.589 |
| Path Traversal | 10.868 | 5 | 2.349 | 2.352 | 15.167 |
| Code Injection | 9.604 | 5 | 2.057 | 2.054 | 13.664 |
| HTTP Response Splitting | 13.386 | 5 | 2.870 | 2.869 | 19.112 |
| OS Command Injection | 2.147 | 5 | 461 | 461 | 3.074 |
| **Tổng** | **326.595** | **30** | **69.950** | **69.692** | **447.049** |

Pool đã loại toàn bộ development groups. Tỷ lệ chia mục tiêu 70/15/15 tính theo group; tỷ lệ record thực tế có thể khác do kích thước nhóm. Không có lớp thiếu support theo ngưỡng kỹ thuật đã cấu hình; điều này không xác nhận annotation đúng.

Ngân sách subsets đã cố định trước inference: pool 3.000 (500/lớp), validation 200 (33–34/lớp), test 600 (100/lớp). Đây là subset cân bằng lớp cho pilot/benchmark dự kiến, không phản ánh tỷ lệ traffic tự nhiên. Final test chưa dùng để tinh chỉnh.

## Kiểm tra leakage và giới hạn

Audit cho mọi cặp development/pool/validation/test đều ghi **0 request ID, 0 exact hash và 0 group ID giao nhau**.

Grouping dùng full request, mask số độc lập và hex dài trên bản sao để tạo key. Payload model vẫn giữ nguyên. Quy tắc này chưa bao phủ mọi biến thể semantic hoặc campaign; không khẳng định không còn mọi dạng leakage.

Endpoint overlap vẫn có: pool/validation 18.160, pool/test 18.328, validation/test 5.185 endpoint hashes. Endpoint hash ở đây là method + URI trước query, không phải parser route/template hoàn chỉnh. Cùng endpoint không tự động là exact duplicate, nhưng số overlap này cho thấy benchmark hiện tại chưa đánh giá khả năng tổng quát sang endpoint mới. Chưa có split theo thời gian hoặc campaign.

Spot-check 16 nhóm development/pool: tám nhóm Normal và hai nhóm mỗi lớp Path Traversal, SQL Injection, Code Injection, HTTP Response Splitting, tối đa ba request/nhóm. Các mẫu được xem khác nhau ở phiên bản browser/OS hoặc thành phần ngày trong URI/Referer, phù hợp quy tắc mask. Không có nhóm nhiều thành viên của OS Command Injection dưới quy tắc hiện tại trong development/pool; điều này không chứng minh lớp này không có semantic near-duplicates. Chi tiết nằm ở `src/artifacts/data/group_review_assessment.json`.

## Review annotation

Đã đọc 60 request được chọn bằng seed từ development/pool, 10 request mỗi lớp, xét cả method, URI, headers và body. Đây là review kỹ thuật của Codex; chưa có chuyên gia/hai annotator độc lập adjudicate.

- Code Injection: mẫu có payload `print(chr(...))`, phù hợp dấu hiệu code injection.
- SQL Injection: nhiều mẫu có `UNION ALL SELECT`, `ORDER BY`, `SELECT SLEEP`; có một mẫu `sleep` encoded có thể mơ hồ với command injection.
- Path Traversal: đa số mẫu có chuỗi `../` hoặc biến thể encoded; một mẫu truy cập `.git/index` cần kiểm tra taxonomy chi tiết.
- OS Command Injection: có `sleep`, Shellshock ở URI/body hoặc User-Agent; một mẫu biểu thức `${...}` cần chuyên gia phân biệt taxonomy.
- HTTP Response Splitting: có CR/LF và `Set-cookie`; các mẫu chỉ có newline kèm `sleep` cần phân biệt với command injection.
- **Normal: 5/10 mẫu có payload đáng nghi**, gồm hai mẫu `sleep(...)`, hai mẫu `cat /etc/passwd` và một mẫu `<script>alert(1)</script>` encoded. Không thể coi đây là tỷ lệ noise của toàn dataset từ mẫu nhỏ này.

Các ID và ghi chú review được lưu riêng để truy vết. Giữ nguyên nhãn nguồn; không xóa riêng các mẫu đáng nghi đã thấy, không tự relabel bằng regex/LLM. Trước mắt, điểm số trên nhãn nguồn chỉ thể hiện mức độ đồng thuận với annotation nguồn.

`src/artifacts/data/manual_review_assessment.json` lưu đủ 60 IDs, đánh giá và ghi chú: 43 mẫu có tín hiệu tương thích nhãn, 5 Normal không thấy attack rõ, 5 Normal đáng nghi và 7 mẫu cần xem lại taxonomy. Các đánh giá này không thay thế ground truth adjudication.

## Kiểm thử và tái lập

Bộ 8 test tự động đã đạt: schema/checksum, lọc toàn taxonomy, conflict với multi-label, exact duplicate, missing/Unicode/encoding, request dài, grouping, split disjointness, balanced sampling, manifest verification, phát hiện file bị thay đổi và tái lập trên fixture. Một test có thể kiểm tra nhiều trường hợp.

**Kiểm tra độc lập toàn bộ export thật đã đạt**, lưu ở `src/artifacts/data/export_verification.json`. **Hai lần chạy toàn dataset tạo 12 file dữ liệu/config/manifest có SHA-256 giống hệt nhau**, không có file khác biệt; `src/artifacts/data/reproducibility.json` ghi `passed: true`. Hash module preprocessing của lần chạy mới nhất được lưu trong `summary.json`.

```bash
python3 -m unittest discover -s src/tests -v
python3 -m src.preprocessing.prepare --config src/configs/data.json --output src/data/processed/sr_bh_new_run --artifacts src/artifacts/data/new_run
python3 -m src.preprocessing.verify --output src/data/processed/sr_bh_new_run --input src/data/raw/data_capec_multilabel.csv --report src/artifacts/data/new_run/export_verification.json
```

Output preprocessing phải là thư mục mới/rỗng. Không có dependency Python bên thứ ba; runtime thực tế là Python 3.12.3 và được lưu trong summary. Chi tiết representation/grouping và cách so checksum ở hướng dẫn dữ liệu.

## Trả lời câu hỏi của giảng viên

**Đã nhận đủ 7 câu hỏi thực tế và đọc lại toàn bộ CSV để trả lời.** [Báo cáo khảo sát SR-BH 2020](../surveys/khao_sat_sr_bh_2020.md) là bản chi tiết: đủ bảng 14 nhãn, toàn bộ schema, 3 payload nguyên văn, source record IDs, cặp minh họa và Figure PNG/SVG/PDF.

| Câu hỏi của giảng viên | Trả lời đã kiểm chứng trên file thật |
| --- | --- |
| 1. Tổng số request? | **907.815 record CSV**, gồm 525.195 Normal và 382.620 có ít nhất một nhãn attack. Hai record thiếu method/URI; không âm thầm bỏ khi báo tổng. |
| 2. Bao nhiêu nhãn/lớp và phân bố? | **13 attack classes + 1 Normal**, không có XSS riêng. Bảng tên nguyên văn và support từng lớp nằm ở câu 2 của báo cáo khảo sát; số liệu là nguồn gốc trước lọc sáu lớp. |
| 3. Mất cân bằng đến mức nào? | SQL Injection 250.311 / Command Injection 1 = **250.311 lần** giữa attack classes. Nếu tính Normal: **525.195 lần**. Bỏ singleton vẫn khoảng **236,37 lần** giữa attack classes. |
| 4. Những trường nào? | **38 cột: 5 metadata + 15 request + 4 response + 14 nhãn**. Request gồm method, URI/query, protocol, 11 header fields và body. Body rỗng 881.072/907.815 record, khoảng 97,054%. Câu 4 liệt kê đủ tên trường và missing counts. |
| 5. Ví dụ benign/SQLi/XSS nguyên văn? | Câu 5 có ba record raw indices **175088, 174425, 7195**, đầy đủ URI và headers/body được log. XSS có payload `<script>alert(document.cookie)</script>`, mang nhãn Code Injection + Scanning, không tự gán nhãn XSS. |
| 6. Có train/test sẵn không? | Version nguồn có một CSV, không có split columns/file train/test. Protocol repo: **pool/validation/test ~70/15/15 theo group**, dành development trọn nhóm từ pool; đã có split v1 và seed/manifests. |
| 7. Có cặp Normal/Attack rất giống nhau không? | **Có**: raw indices **175088 và 174425**, đều thuộc pool. Method, protocol, 11 headers và body giống hoàn toàn; chỉ thêm `+AND+1%3D1` vào `format=xml`. URI character similarity **96,8354%**, full request **99,4970%**. Figure và caption nằm ở câu 7. |

Cặp minh họa chứng tỏ nội dung rất giống nhau có thể mang nhãn nguồn khác nhau; chưa chứng minh embedding/top-k retrieval thất bại hoặc label-aware retrieval cải thiện. Cần kiểm chứng bằng Pipeline B/C. Khảo sát không thay đổi annotation hoặc split hiện có; vấn đề chất lượng nhãn trước đây vẫn cần adjudication.

Khảo sát bổ sung có `src/preprocessing/find_pair.py`, `src/preprocessing/survey.py`, `src/preprocessing/survey_report.py` và evidence trong `src/artifacts/data/sr_bh_survey/`. Bộ test hiện tại **11/11 đạt** (gồm 8 test dữ liệu trước đó và 3 test khảo sát/provenance); kết quả mới ở `src/artifacts/data/sr_bh_survey/test_results.txt`.

## Checklist và bàn giao

- [x] Tải dữ liệu thật; xác minh nguồn, giấy phép, phiên bản và checksum.
- [x] Đọc schema, phát hiện toàn bộ cột nhãn; ghi nhận chênh lệch tài liệu cũ.
- [x] Triển khai preprocessing, conflict quarantine, exact dedup, group split và subsets.
- [x] Có config, full manifests, source linkage và audit leakage theo quy tắc đã công bố.
- [x] Test tự động đạt; đã đọc 60 mẫu annotation và phát hiện vấn đề cần giải quyết.
- [x] Kiểm tra độc lập export thật và tái lập toàn dataset đạt; 12 file có checksum giống nhau.
- [x] Spot-check 16 nhóm near-duplicate và công bố giới hạn của quy tắc grouping.
- [ ] Chốt hướng xử lý annotation với người dùng/giảng viên và xác nhận dataset/taxonomy cho bước tiếp theo.
- [x] Nhận đủ 7 câu hỏi thật; đọc lại toàn bộ CSV và hoàn thiện báo cáo khảo sát, payload nguyên văn và Figure minh họa.

**Trạng thái bàn giao:** phần kỹ thuật dữ liệu v1 đã có; chưa đánh dấu toàn bộ Task 1 hoàn tất về lựa chọn benchmark cuối cùng. Có thể chuẩn bị code Task 2 độc lập; việc chạy pilot trên nhãn nguồn hay khảo sát nguồn khác chờ quyết định đang hỏi người dùng. Không chạy final benchmark trong phiên này.
