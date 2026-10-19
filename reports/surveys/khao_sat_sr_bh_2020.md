# Khảo sát SR-BH 2020 trên dữ liệu thật — trả lời 7 câu hỏi của giảng viên

Ngày thực hiện: 19/10/2026. Báo cáo này được tạo bằng cách đọc **toàn bộ CSV thật**, không lấy số liệu từ mô tả website. Số liệu ở câu 1–4 là dữ liệu gốc trước lọc single-label, khác số liệu 466.267 request của pipeline v1.

Nguồn: [Harvard Dataverse, DOI 10.7910/DVN/OGOIXX](https://doi.org/10.7910/DVN/OGOIXX), dataset version 1.2, file ID 6319496, giấy phép CC0 1.0 theo metadata nguồn. File local: `src/data/raw/data_capec_multilabel.csv`, **436.437.661 byte**.

- MD5: `173ec515308bdce5aec19cfd5b792596`, đã khớp checksum nguồn.
- SHA-256: `9c73c90ce6564ae48b14f7179cd864d037a6a130ef69c68c1626ec5d7ce4a910`.
- [Thống kê máy đọc được](../../src/artifacts/data/sr_bh_survey/stats.json), [record gốc của các ví dụ](../../src/artifacts/data/sr_bh_survey/examples.json), [kiểm chứng](../../src/artifacts/data/sr_bh_survey/verification.json).
- Raw index là thứ tự record CSV bắt đầu từ 0, không tính header. CSV record = raw index + 2; không bảo đảm bằng số dòng vật lý nếu một field chứa newline.

## 1. Tổng số bản ghi (request) là bao nhiêu?

**907.815 record CSV**, không tính header. Trong đó **525.195** record có nhãn Normal và **382.620** record có ít nhất một nhãn attack; không có record đồng thời Normal và attack.

Có **2 record thiếu method/URI**, raw indices `[14410, 163884]`; vì vậy có 907.813 record có đủ hai trường HTTP thiết yếu này. Không âm thầm loại hai record đó khi báo tổng CSV.

Mô tả nguồn ghi 907.814; file tải thực tế đã khớp checksum có 907.815. Chưa xác định nguyên nhân chênh một record với mô tả; không tự suy diễn là do header hoặc duplicate.

## 2. Có bao nhiêu nhãn/lớp tấn công? Tên và số lượng từng lớp?

**13 lớp tấn công + 1 nhãn Normal = 14 cột nhãn binary.** Không có nhãn XSS riêng. CAPEC-248 Command Injection và CAPEC-88 OS Command Injection là hai cột khác nhau, không gộp khi thống kê.

| Nhãn gốc | Số record có nhãn = 1 | % trên tổng 907.815 record |
| --- | ---: | ---: |
| 000 - Normal | 525.195 | 57,853% |
| 66 - SQL Injection | 250.311 | 27,573% |
| 194 - Fake the Source of Data | 56.145 | 6,185% |
| 126 - Path Traversal | 20.992 | 2,312% |
| 34 - HTTP Response Splitting | 19.738 | 2,174% |
| 242 - Code Injection | 15.827 | 1,743% |
| 272 - Protocol Manipulation | 9.153 | 1,008% |
| 88 - OS Command Injection | 7.482 | 0,824% |
| 274 - HTTP Verb Tampering | 5.437 | 0,599% |
| 310 - Scanning for Vulnerable Software | 2.718 | 0,299% |
| 153 - Input Data Manipulation | 2.272 | 0,250% |
| 16 - Dictionary-based Password Attack | 1.847 | 0,203% |
| 33 - HTTP Request Smuggling | 1.059 | 0,117% |
| 248 - Command Injection | 1 | 0,000110% |

Đây là dữ liệu **multi-label**: một request có thể đóng góp vào nhiều hàng. Phân bố số nhãn active trên record: 1 nhãn: 898.577; 2 nhãn: 8.132; 3 nhãn: 1.088; 4 nhãn: 18. Tổng số lượt gán nhãn không phải tổng số request; không cộng bảng lớp rồi coi là số record độc lập.

![Phân bố lớp với trục log](figures/sr_bh_class_distribution.png)

[SVG](figures/sr_bh_class_distribution.svg) · [PDF](figures/sr_bh_class_distribution.pdf). Trục log giúp nhìn thấy lớp singleton; chiều dài thanh không phải tỷ lệ tuyến tính.

## 3. Dữ liệu có mất cân bằng nghiêm trọng không? Lớp lớn nhất gấp bao nhiêu lần lớp nhỏ nhất?

**Có, ở bài toán phân loại loại tấn công.**

- Chỉ xét attack classes: SQL Injection 250.311 / Command Injection 1 = **250.311 lần**.
- Nếu tính cả Normal: Normal 525.195 / Command Injection 1 = **525.195 lần**.
- Bỏ riêng lớp singleton CAPEC-248, lớp attack nhỏ nhất còn lại là HTTP Request Smuggling 1.059: 250.311 / 1.059 ≈ **236.37 lần**. Mất cân bằng vẫn rất lớn.
- Nếu chỉ chuyển sang bài toán binary Normal/Attack thì tỷ lệ là 525.195 / 382.620 ≈ **1.373 lần**. Không dùng tỷ lệ binary này để kết luận bài toán 13 attack classes cân bằng.

Lớp một mẫu không đủ để chia pool/validation/test có ý nghĩa. Phạm vi single-label v1 hiện giữ Normal, SQL Injection, Path Traversal, Code Injection, HTTP Response Splitting và OS Command Injection; đây là quyết định thu hẹp phạm vi, không phải phân bố của nguồn gốc. Cần báo support từng lớp và Macro-F1/per-class metrics khi chạy model; không dựa vào Accuracy đơn lẻ.

## 4. Mỗi bản ghi gồm những trường nào?

**38 cột = 5 metadata + 15 request fields + 4 response fields + 14 nhãn.** Dưới đây là đủ 24 cột không phải nhãn; 14 tên cột nhãn đã liệt kê nguyên văn ở câu 2.

| Tên cột nguyên văn | Nhóm | Nội dung | Record có giá trị rỗng (`""`) |
| --- | --- | --- | ---: |
| `timestamp` | Metadata | Thời điểm request; chuỗi có timezone | 2 |
| `src_ip` | Metadata | IP nguồn đã ghi trong log | 2 |
| `src_port` | Metadata | Port nguồn | 2 |
| `dst_ip` | Metadata | IP đích | 2 |
| `dst_port` | Metadata | Port đích | 2 |
| `request_http_method` | Request line | HTTP method | 2 |
| `request_http_request` | Request line | Request-target: path và query, không phải lúc nào cũng là URL đầy đủ | 2 |
| `request_http_protocol` | Request line | HTTP protocol/version | 2 |
| `request_user_agent` | Request header | User-Agent | 3.834 |
| `request_referer` | Request header | Referer | 616.421 |
| `request_host` | Request header | Host | 34 |
| `request_origin` | Request header | Origin | 906.206 |
| `request_cookie` | Request header | Cookie | 462.553 |
| `request_content_type` | Request header | Content-Type | 879.271 |
| `request_accept` | Request header | Accept | 526.032 |
| `request_accept_language` | Request header | Accept-Language | 891.955 |
| `request_accept_encoding` | Request header | Accept-Encoding | 541.515 |
| `request_do_not_track` | Request header | DNT | 907.110 |
| `request_connection` | Request header | Connection | 424.955 |
| `request_body` | Body | Request body thô; có thể là form-urlencoded | 881.072 |
| `response_http_protocol` | Response | Protocol của response | 2 |
| `response_http_status_code` | Response | HTTP status code | 2 |
| `response_http_status_message` | Response | HTTP status message | 2 |
| `response_content_length` | Response | Độ dài response theo log | 3.292 |

`request_body` rỗng ở **881.072/907.815 record (97.054%)**; còn **26.743** record có body không rỗng. Rỗng trong CSV có thể là request không có body hoặc body không được ghi lại; không thể phân biệt hai trường hợp chỉ từ field rỗng. Không bỏ body khỏi input vì nhiều payload POST nằm ở đó.

Các header chỉ là các trường đã được log, không phải bản wire capture đầy đủ hoặc toàn bộ header có thể có. URL thường ở dạng path/query; muốn dựng absolute URL còn cần Host và thông tin scheme mà CSV không luôn cung cấp. Response/status là thông tin sau request, không đưa vào input phát hiện tấn công của Pipeline A để tránh shortcut/leakage. Các cột nhãn không có giá trị rỗng trong file này.

## 5. Trích 3 ví dụ: benign, SQLi và XSS — payload nguyên văn

Các block URI bên dưới chép nguyên giá trị field CSV, giữ percent-encoding và ký tự gốc, không dùng `...`. Block HTTP là bản dựng lại từ các field được log; thứ tự/tên header do trình bày lại, không khẳng định đây là raw HTTP bytes trên đường truyền. Giá trị header/body không bị sửa. Toàn bộ 38 trường của từng record nằm trong [evidence JSON](../../src/artifacts/data/sr_bh_survey/examples.json).

### 5.1. Request mang nhãn Normal

- Raw index (0-based): **175088**; số thứ tự record CSV tính header: **175090**.
- Timestamp nguyên văn: `18/Jul/2020:01:28:11 +0200`.
- Nhãn nguồn đang active: `000 - Normal`.
- Request ID: `a1bee81b02e901fef38abc8f5c71fdbe405bce9248e4bf4b2701d34cabc095fe`.
- `request_body` nguyên văn là chuỗi rỗng (`""`).

`request_http_request` nguyên văn, không decode/rút gọn:

```text
/blog/index.php/wp-json/oembed/1.0/embed?format=xml&url=http%3A%2F%2Ftest-site.com%2Fblog%2Findex.php%2Fvitae-dolores-quidem-possimus-aut-voluptatibus%2F
```

Request dựng lại từ các trường CSV, giữ nguyên giá trị các header có dữ liệu:

```http
GET /blog/index.php/wp-json/oembed/1.0/embed?format=xml&url=http%3A%2F%2Ftest-site.com%2Fblog%2Findex.php%2Fvitae-dolores-quidem-possimus-aut-voluptatibus%2F HTTP/1.1
Host: test-site.com
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0
Referer: http://test-site.com/blog/index.php/vitae-dolores-quidem-possimus-aut-voluptatibus/
Cookie: comment_author_url_1aefbe2f76edd740f8e362f39da3353b=http%3A%2F%2Fwww.example.com; comment_author_email_1aefbe2f76edd740f8e362f39da3353b=foo-bar%40example.com; wordpress_test_cookie=WP+Cookie+check; comment_author_1aefbe2f76edd740f8e362f39da3353b=discussion; wordpress_logged_in_1aefbe2f76edd740f8e362f39da3353b=rafael%7C1595199372%7CN6zlSHC7AOeZ7WSCeWHts6pI6PHkGPqAU9z7L3v9kn3%7Cb2e4133dac569bbcb9b7eebd612e17638e7800de514c2e46f69da14d8722c007


```

Request truy vấn oEmbed với `format=xml`; không thấy attack token rõ trong URI, headers hoặc body được ghi lại. Đây là đánh giá nội dung cùng nhãn nguồn, chưa phải xác nhận chuyên gia hoặc bằng chứng server an toàn tuyệt đối.
### 5.2. Request mang nhãn SQL Injection

- Raw index (0-based): **174425**; số thứ tự record CSV tính header: **174427**.
- Timestamp nguyên văn: `18/Jul/2020:01:27:17 +0200`.
- Nhãn nguồn đang active: `66 - SQL Injection`.
- Request ID: `17f06954139192efe06cbbeaf9e8b8303dcf0b68b59a6888b2c76ec1e8cb178d`.
- `request_body` nguyên văn là chuỗi rỗng (`""`).

`request_http_request` nguyên văn, không decode/rút gọn:

```text
/blog/index.php/wp-json/oembed/1.0/embed?format=xml+AND+1%3D1&url=http%3A%2F%2Ftest-site.com%2Fblog%2Findex.php%2Fvitae-dolores-quidem-possimus-aut-voluptatibus%2F
```

Request dựng lại từ các trường CSV, giữ nguyên giá trị các header có dữ liệu:

```http
GET /blog/index.php/wp-json/oembed/1.0/embed?format=xml+AND+1%3D1&url=http%3A%2F%2Ftest-site.com%2Fblog%2Findex.php%2Fvitae-dolores-quidem-possimus-aut-voluptatibus%2F HTTP/1.1
Host: test-site.com
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0
Referer: http://test-site.com/blog/index.php/vitae-dolores-quidem-possimus-aut-voluptatibus/
Cookie: comment_author_url_1aefbe2f76edd740f8e362f39da3353b=http%3A%2F%2Fwww.example.com; comment_author_email_1aefbe2f76edd740f8e362f39da3353b=foo-bar%40example.com; wordpress_test_cookie=WP+Cookie+check; comment_author_1aefbe2f76edd740f8e362f39da3353b=discussion; wordpress_logged_in_1aefbe2f76edd740f8e362f39da3353b=rafael%7C1595199372%7CN6zlSHC7AOeZ7WSCeWHts6pI6PHkGPqAU9z7L3v9kn3%7Cb2e4133dac569bbcb9b7eebd612e17638e7800de514c2e46f69da14d8722c007


```

Tham số format chứa nguyên văn `xml+AND+1%3D1`. Khi giải thích percent-encoding/form notation, phần thêm có dạng ` AND 1=1`, phù hợp cú pháp kiểm tra SQL injection. Đây là request có dấu hiệu thử SQLi, không chứng minh khai thác thành công. Dataset ghi response 200 cho cả request này và request Normal.
### 5.3. Request có payload XSS; không có lớp XSS riêng

- Raw index (0-based): **7195**; số thứ tự record CSV tính header: **7197**.
- Timestamp nguyên văn: `17/Jul/2020:20:05:55 +0200`.
- Nhãn nguồn đang active: `242 - Code Injection`, `310 - Scanning for Vulnerable Software`.
- Request ID: `7fd765bf73fe327449d440f502e5c260d395c3bc758538d35c75823ed53f1369`.
- `request_body` nguyên văn là chuỗi rỗng (`""`).

`request_http_request` nguyên văn, không decode/rút gọn:

```text
/?p4yl04d3=<script>alert(document.cookie)</script>
```

Request dựng lại từ các trường CSV, giữ nguyên giá trị các header có dữ liệu:

```http
GET /?p4yl04d3=<script>alert(document.cookie)</script> HTTP/1.1
Host: 249.network5-175-62-15.static.network5.net
User-Agent: Mozilla/5.0 (compatible; Nmap Scripting Engine; https://nmap.org/book/nse.html)
Connection: close


```

Payload `<script>alert(document.cookie)</script>` nằm trực tiếp trong URI. Dataset gán Code Injection và Scanning for Vulnerable Software; không được đổi thành một nhãn XSS vốn không tồn tại. User-Agent ghi Nmap Scripting Engine. Chỉ xác nhận có payload XSS trong request; không có browser execution trace để kết luận reflected/stored XSS thành công. Record này multi-label, vì vậy không nằm trong benchmark single-label v1.

Không thể suy ra tổng số mẫu XSS từ ví dụ này: payload có thể encoded/obfuscated và taxonomy không có cột XSS. Không coi một regex tìm `<script>` là bộ gán nhãn hoặc thống kê XSS đầy đủ.

## 6. Dataset đã chia sẵn train/test chưa? Nếu chưa, dự định chia theo tỷ lệ nào?

**Không thấy split train/test được tác giả cung cấp trong dataset version đã tải.** Metadata version 1.2 có các file: `['data_capec_multilabel.csv']`; CSV không có cột chỉ định train/test/split/fold/partition. Kết luận này dựa trên cả danh sách file của nguồn và schema thật, không suy ra từ tên cột `HTTP Response Splitting`.

Protocol inference-only của repo dùng **pool/validation/test khoảng 70/15/15 theo nhóm**, không coi pool là dữ liệu fine-tune. Group exact/near-duplicates trước khi chia. Dành development từ pool theo trọn nhóm để sửa prompt, không lấy demonstrations từ development/validation/test.

Split v1 đã được tạo trên phần sáu lớp single-label sau xử lý:

| Split | Request unique | Vai trò |
| --- | ---: | --- |
| Pool sau khi dành development | 326.595 | Demonstrations/retrieval pool |
| Development | 30 | Smoke test và sửa prompt |
| Validation đầy đủ | 69.950 | Chọn cấu hình |
| Test đầy đủ | 69.692 | Benchmark cuối khi protocol được khóa |

Seed 42; pilot subsets pool 3.000, validation 200, test dự kiến 600. Mọi nhóm phải nằm trọn một split; tỷ lệ row có thể lệch tỷ lệ group. Manifest và checksum nằm ở `src/data/processed/sr_bh_v1`. Test mới được audit cấu trúc, chưa chạy LLM/chỉnh prompt. Cặp minh họa ở câu 7 lấy từ pool.

Quy tắc grouping v1 mới mask số/hex trên request đầy đủ. Audit đạt theo quy tắc đó, nhưng endpoint/campaign/semantic near-duplicates có thể còn giao nhau; cần rà lại protocol trước final benchmark. Chưa chốt benchmark cuối cùng vì review trước đó cũng phát hiện một số nhãn Normal chứa payload đáng nghi.

## 7. Cặp benign/attack rất giống nhau và Figure motivating example

**Đã tìm được một cặp có thể kiểm tra trực tiếp**, dùng hai record chính là ví dụ Normal và SQLi ở câu 5:

| Thuộc tính | Normal theo nhãn nguồn | SQL Injection theo nhãn nguồn |
| --- | --- | --- |
| Raw index | 175088 | 174425 |
| CSV record tính header | 175090 | 174427 |
| Timestamp | `18/Jul/2020:01:28:11 +0200` | `18/Jul/2020:01:27:17 +0200` |
| Split | pool | pool |
| Method / protocol | GET / HTTP/1.1 | GET / HTTP/1.1 |
| Body | Rỗng | Rỗng |
| 11 header fields được log | Giống hoàn toàn phía SQLi | Giống hoàn toàn phía Normal |
| Tham số khác biệt | `format=xml` | `format=xml+AND+1%3D1` |

**Toàn bộ URI nguyên văn của Normal:**

```text
/blog/index.php/wp-json/oembed/1.0/embed?format=xml&url=http%3A%2F%2Ftest-site.com%2Fblog%2Findex.php%2Fvitae-dolores-quidem-possimus-aut-voluptatibus%2F
```

**Toàn bộ URI nguyên văn của SQLi:**

```text
/blog/index.php/wp-json/oembed/1.0/embed?format=xml+AND+1%3D1&url=http%3A%2F%2Ftest-site.com%2Fblog%2Findex.php%2Fvitae-dolores-quidem-possimus-aut-voluptatibus%2F
```

Khác biệt duy nhất trong representation request là chuỗi chèn **`+AND+1%3D1`** vào giá trị `format`. Khi diễn giải query notation, đó là ` AND 1=1`. Method, protocol, cả 11 header fields (gồm Cookie/User-Agent/Referer) và body đều giống nhau. Xét toàn record CSV, các cột khác nhau là `['timestamp', 'src_port', 'request_http_request', 'response_content_length', '000 - Normal', '66 - SQL Injection']`; metadata/response/labels không nằm trong similarity request đang báo.

- URI character similarity: **96.8354%**.
- Full serialized request character similarity: **99.4970%**.
- Công thức: `difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() = 2M / (len(a) + len(b))`, với M là tổng độ dài matching blocks. Đây là character similarity, **không phải embedding cosine similarity**. Score full request cao một phần do headers dài giống nhau; báo cả score URI để tránh che yếu tố này.
- Nhãn nguồn là Normal và SQL Injection; không có bằng chứng request SQLi đã được server thực thi thành công. Normal không có attack token rõ trong dữ liệu quan sát, nhưng chưa có chuyên gia adjudicate cặp này.

![Motivating example từ hai record thật](figures/sr_bh_motivating_pair.png)

[SVG để biên tập](figures/sr_bh_motivating_pair.svg) · [PDF vector](figures/sr_bh_motivating_pair.pdf).

**Caption đề xuất:** Two real SR-BH 2020 requests share the method, protocol, recorded headers and empty body, but differ by the insertion `+AND+1%3D1` into the `format` query parameter. The source labels are Normal and SQL Injection, respectively. Their URI character similarity is 96.84%. The example motivates testing whether label-aware demonstration selection can distinguish superficially similar requests; it does not establish a semantic-retrieval failure or a performance gain.

### Cách tìm và giới hạn của bằng chứng

Script `src/preprocessing/find_pair.py` chỉ đọc development/pool. Giữ Normal GET có URI tương đối đơn giản và không có một số attack tokens rõ; xét SQLi có cú pháp SQL trong URI. Ghép theo method/protocol/headers/body giống hoàn toàn, xếp theo similarity URI, tối đa 30 URI Normal ngắn nhất mỗi context. Search có 64.522 Normal candidates, 25.910 SQLi cùng context, và 5.897 cặp qua quick filter. Đây là tìm kiếm có giới hạn, không tuyên bố tìm được cặp gần nhất toàn dataset. Các heuristics chỉ hỗ trợ chọn ví dụ để đọc, không thay nhãn nguồn.

Cặp này là bằng chứng trực quan rằng **request rất giống về chuỗi/cấu trúc vẫn có thể mang nhãn khác nhau**, đủ làm motivating illustration. Nó **chưa chứng minh** semantic embedding/top-k retrieval chọn sai demonstrations, cũng chưa chứng minh label-aware retrieval tốt hơn. Để kiểm chứng gap thực nghiệm, Pipeline B cần log similarity/rank/labels của top-k trên nhiều query và so sánh B/C trên cùng protocol; prior của C phải độc lập ground truth query.

## Kiểm chứng và lệnh tái lập

Bộ kiểm thử hiện tại **11/11 đạt**, gồm ba test mới kiểm tra multi-label accounting, payload/source provenance, từ chối cặp không thuộc pool/development và ngăn đổi nhãn ví dụ XSS thành SQLi. Kết quả ở `src/artifacts/data/sr_bh_survey/test_results.txt`.

```bash
python3 -m unittest discover -s src/tests -v
python3 -m src.preprocessing.find_pair
python3 -m src.preprocessing.survey
MPLCONFIGDIR=/tmp/sr-bh-mpl python3 -m src.preprocessing.survey_report
```

`find_pair` có thể mất vài phút. `survey` đọc lại mọi record trong CSV thật, kiểm checksum, label cardinality, tổng số lượt nhãn, lấy ví dụ theo raw index, đối chiếu nhãn, xác nhận cặp chỉ khác URI và thuộc pool/development. `verification.json` ghi kết quả. Khảo sát và tìm cặp dùng Python standard library; xuất hình dùng matplotlib, phiên bản kiểm chứng trong `src/requirements-survey.txt`.

Các thống kê và ví dụ không phụ thuộc website mô tả; metadata nguồn chỉ dùng cho provenance/version/license/danh sách file. Không thay đổi nhãn, split hoặc benchmark manifests trong quá trình khảo sát này.
