# Khảo sát dataset thứ hai cho đề tài (nghiên cứu trên giấy, không tải dữ liệu, không gọi API)

Ngày khảo sát: 02/11/2026 (còn 12 ngày đến hạn 14/11/2026). Mục tiêu: trả lời "có thể thêm một dataset HTTP có nhãn thứ hai trước hạn hay không" để kiểm tra kết luận B > zero-shot và C/biến thể không thắng B có còn đúng ngoài SR-BH 2020 hay không.

Quy ước: câu nào không có link kèm là suy luận của người khảo sát. Mục "Chưa xác minh được" ở cuối liệt kê những gì phiên này không kiểm chứng được. **Chưa tải file dữ liệu nào** (đúng yêu cầu: tải file lớn phải hỏi trước).

## Kết luận ngắn

**GO có điều kiện, phạm vi thu hẹp:** dùng **ECML/PKDD 2007** với **4 lớp trùng** (NORMAL, SQL_INJECTION, PATH_TRAVERSAL, OS_COMMAND_INJECTION), chạy bộ rút gọn. Điều kiện là bước kiểm "Ngày 1" (tải ~20 MB, đếm số mẫu từng lớp) phải đạt, nếu không thì **NO-GO** và ghi vào báo cáo là hạn chế ("chỉ kiểm chứng trên một dataset"). Chi phí API không phải rào cản (khoảng 0,3–0,55 USD thực); rào cản là thời gian, độ tin cậy nhãn, và việc nhãn/thông tin bị làm mờ (xem mục 1.4).

## 1. ECML/PKDD 2007 Discovery Challenge ("Analyzing Web Traffic")

### 1.1 Nguồn chính thức và tình trạng tải

- Trang thử thách của LIRMM (Montpellier): [www.lirmm.fr/pkdd2007-challenge](https://www.lirmm.fr/pkdd2007-challenge/index.html). Trang này còn truy cập được.
- Mục "Data" trên trang đó trỏ tới `http://www.lirmm.fr/pkdd2007-challenge/Donnees/index.html`. **Ngày 02/11/2026 địa chỉ này trả HTTP 500** (đã thử `https` và `http`, cả đường dẫn thư mục; hai công cụ khác nhau cho cùng kết quả). Archive.org [không có snapshot](https://archive.org/wayback/available?url=lirmm.fr/pkdd2007-challenge/Donnees/index.html) cho URL này. **Vậy nguồn chính thức hiện không tải được.**
- Trang [đăng ký](https://www.lirmm.fr/pkdd2007-challenge/inscription.html) chỉ có form tham gia thử thách (mở từ 10/04/2007); không nêu điều khoản dữ liệu, và link "Data" ở đó là placeholder.
- Bản sao còn tải được: repo GitHub [msudol/Web-Application-Attack-Datasets](https://github.com/msudol/Web-Application-Attack-Datasets) (thư mục [`OriginalDataSets/ecml_pkdd`](https://github.com/msudol/Web-Application-Attack-Datasets/tree/master/OriginalDataSets/ecml_pkdd)) có hai file, kích thước theo [GitHub API](https://api.github.com/repos/msudol/Web-Application-Attack-Datasets/contents/OriginalDataSets/ecml_pkdd): `learning_dataset_xml.zip` (19.954.936 byte) và `dataset_ecml_pkdd_train_test.tar.gz` (33.462.529 byte). [README của thư mục](https://raw.githubusercontent.com/msudol/Web-Application-Attack-Datasets/master/OriginalDataSets/ecml_pkdd/README.md) mô tả `learning_dataset.xml` là dữ liệu gốc của thử thách. README cấp trên ghi dữ liệu "cloned from" một GitLab của Đại học Cộng hòa (Uruguay) mà phiên này **không truy cập được** (`gitlab.fing.edu.uy`, không phản hồi). Đây là bản mirror của bên thứ ba, chưa đối chiếu byte với bản gốc.

### 1.2 Giấy phép / điều khoản sử dụng

- Hai trang chính thức đọc được ([index](https://www.lirmm.fr/pkdd2007-challenge/index.html), [đăng ký](https://www.lirmm.fr/pkdd2007-challenge/inscription.html)) **không nêu giấy phép hay điều khoản**. Trang "Data" (nơi có thể có điều khoản) không đọc được.
- Repo mirror hiển thị giấy phép GPL-3.0 (theo [trang repo](https://github.com/msudol/Web-Application-Attack-Datasets)), nhưng đó là giấy phép của repo/mã chuyển đổi, **không chứng minh** được điều khoản của chính dữ liệu ECML.
- Hệ quả: dùng cho đồ án học thuật và trích dẫn bài [Raissi et al. 2007](https://hal-lirmm.ccsd.cnrs.fr/lirmm-00168955) là hợp lý, nhưng **không được viết "CC0/open licence"** như SR-BH. Báo cáo phải ghi "điều khoản chưa xác minh".

### 1.3 Định dạng, lớp, số lượng

- Bài mô tả thử thách: Raissi, Brissaud, Dray, Poncelet, Roche, Teisseire, [*Web Analyzing Traffic Challenge: Description and Results*](https://www.lirmm.fr/~poncelet/publications/papers/awt_raissi.pdf), ECML/PKDD 2007 Discovery Challenge, tr. 47–52 ([HAL](https://hal-lirmm.ccsd.cnrs.fr/lirmm-00168955)).
- **Định dạng:** XML; mỗi mẫu có id, `Context`, `Class`, và `Query` gồm **Method, Protocol, Uri, Query, Headers, Body** (cùng bài báo, mục 3, và [trang thử thách](https://www.lirmm.fr/pkdd2007-challenge/index.html)). Tức là **có đủ method/URI/header/body**. Mẫu thô trong [README repo mirror](https://raw.githubusercontent.com/msudol/Web-Application-Attack-Datasets/master/README.md) cho thấy bản chuyển sang dạng text có `class:` và request đầy đủ nhiều header.
- **8 lớp** (trường `type`): Valid, XSS, SqlInjection, LdapInjection, XPathInjection, PathTransversal, OsCommanding, SSI (cùng nguồn). Mỗi mẫu có thêm cờ `inContext` và `attackIntervall` (vị trí tấn công). Bài báo nói **một mẫu có thể thuộc nhiều lớp**.
- **Số lượng, các nguồn mâu thuẫn nhau:**
  - Trang thử thách: dự kiến 50.000 mẫu, 20% tấn công ([index](https://www.lirmm.fr/pkdd2007-challenge/index.html)).
  - Bài Raissi, bảng 1: tập learning 50.000 mẫu với 70% tấn công; tập test 70.000 mẫu với 60% tấn công.
  - Mirror: train 24.504 Valid; test 10.502 Valid + 15.110 tấn công, tức 35.006 Valid + 15.110 tấn công ([README mirror](https://raw.githubusercontent.com/msudol/Web-Application-Attack-Datasets/master/OriginalDataSets/ecml_pkdd/README.md); cùng con số ở [Betarte et al.](https://arxiv.org/pdf/1803.05529), bảng II).
  - Ba bộ số này không khớp nhau và tôi không giải thích được sự khác biệt khi chưa mở file.
- **Số mẫu theo từng lớp tấn công: KHÔNG xác minh được.** Không bài nào tôi đọc được in bảng đầy đủ. Một bài khác nêu SQL injection 2221 và XSS 6900 trong bảng của họ nhưng đó có thể là tập con (kết quả tìm kiếm, chưa đọc bài gốc) nên không dùng. Bảng 1 trong báo cáo kỹ thuật [Gallagher & Eliassi-Rad, LLNL 2009](https://www.osti.gov/biblio/1113394) có thể có số này; trang OSTI từ chối kết nối trong phiên này. **Cách duy nhất chắc chắn: tải và đếm** (bước Ngày 1).
- Vị trí tấn công (bảng 1 Raissi): ở tập learning khoảng 4%+3%+6%+5% = 18% tấn công nằm ở cookie/header, ở tập test 7%+5%+8%+7% = 27%. Do đó danh sách 11 header cố định trong [`data.json`](../../src/configs/data.json) sẽ làm mất tín hiệu ở nhiều mẫu ECML; phải giữ **toàn bộ** header.

### 1.4 Hạn chế đã được công bố

- **Dữ liệu bị làm mờ:** URL, tên tham số và giá trị được thay bằng chuỗi ngẫu nhiên, gần như không giá trị nào xuất hiện hai lần ([Betarte et al., mục B](https://arxiv.org/pdf/1803.05529); [README mirror](https://raw.githubusercontent.com/msudol/Web-Application-Attack-Datasets/master/OriginalDataSets/README.md) nói cùng việc). Hệ quả cho đề tài: truy hồi ngữ nghĩa (MiniLM) trên chuỗi ngẫu nhiên có thể kém khác SR-BH; vừa là rủi ro vừa là một phép thử độ bền thú vị, nhưng phải nói rõ khi diễn giải.
- **Tấn công do ban tổ chức dựng:** "trông như thật nhưng không có khả năng thành công vì dựng mù, không nhắm đúng thực thể" (Raissi, mục 3). Nhãn do chuyên gia gán (cùng mục).
- Các lớp như OsCommanding và SSI được nhóm tham gia ghi nhận là khó nhận diện (Raissi, mục 5). Bài báo cũng cho biết chỉ có hai đội nộp kết quả.

## 2. Các dataset khác đã xem xét

| Dataset | Nguồn / bài giới thiệu | Có method/URI/header/body? | Lớp | Đánh giá |
| --- | --- | --- | --- | --- |
| **CSIC 2010** | [IMPACT](https://www.impactcybertrust.org/dataset_view?idDataset=940); đã khảo sát riêng ở [khao_sat_csic_2010.md](khao_sat_csic_2010.md) | Có | Chỉ Normal/Anomalous | **Loại** cho bài toán 6 lớp (không có nhãn loại tấn công). Bài báo gốc của CSIC chưa xác minh trong phiên này |
| **SR-BH 2020** | Dataset đang dùng, [Harvard Dataverse](https://dataverse.harvard.edu/api/access/datafile/6319496) | Có | Nhiều nhãn CAPEC | Dataset chính, không phải "thứ hai" |
| **HttpParamsDataset** | [GitHub Morzeux](https://github.com/Morzeux/HttpParamsDataset), giấy phép MIT; làm cho luận văn tốt nghiệp, không phải bài bình duyệt | **Không**, chỉ giá trị tham số | norm 19.304; sqli 10.852; xss 532; cmdi 89; path-traversal 290 | **Loại**: không phải request đầy đủ, lớp nhỏ (cmdi 89) |
| **30 ngày request bị ModSecurity chặn** | Lucz & Forstner, *Data* 10(11):186, 2025, [DOI](https://doi.org/10.3390/data10110186); dữ liệu ở [Zenodo](https://zenodo.org/records/17178461), CC BY 4.0, `owasp.zip` 29,5 MB | Chưa xác minh (trang MDPI trả 403; trang Zenodo không nêu trường dữ liệu) | Chưa xác minh | **Loại cho lần này**: là request bị chặn nên không có lớp Normal, nhãn gắn theo luật CRS (dễ vòng tròn); chưa xác minh được số lượng |
| DarkSegmentsIDS | [IEEE DataPort](https://ieee-dataport.org/documents/darksegmentsids) | Chưa xác minh | Theo kết quả tìm kiếm: SQLi, XSS, command injection | Không đọc được chi tiết, không phải bài bình duyệt: **bỏ** |

Không tìm thấy dataset nào khác vừa là request HTTP đầy đủ, vừa có nhãn đa lớp gồm HTTP response splitting hoặc CODE_INJECTION, vừa có nguồn bình duyệt đọc được trong phiên này. Đây là kết quả của vài lượt tìm kiếm, không phải khảo sát tài liệu có hệ thống.

## 3. Ánh xạ nhãn ECML/PKDD → 6 nhãn của đề tài

Nhãn đề tài lấy từ [`data.json`](../../src/configs/data.json).

| Nhãn đề tài (CAPEC) | Lớp ECML tương ứng | Ghi chú |
| --- | --- | --- |
| NORMAL | Valid | Trùng. Khác SR-BH: nhãn Normal ở SR-BH nhiễu, ECML do chuyên gia gán |
| SQL_INJECTION (66) | SqlInjection | Trùng |
| PATH_TRAVERSAL (126) | PathTransversal | Trùng |
| OS_COMMAND_INJECTION (88) | OsCommanding | Trùng |
| CODE_INJECTION (242) | *(không có lớp riêng)* | Thiếu. Theo [MITRE](https://capec.mitre.org/data/definitions/242.html), XSS (CAPEC-63) là con của CAPEC-242 nên có thể lập luận XSS ⊂ Code Injection, nhưng chưa kiểm xem lớp CODE_INJECTION của SR-BH chứa loại payload nào; **không nên gộp tùy tiện** |
| HTTP_RESPONSE_SPLITTING (34) | *(không có)* | Thiếu |
| *(ngoài 6 lớp)* | XSS, LdapInjection, XPathInjection, SSI | Thừa. [CAPEC-101 (SSI)](https://capec.mitre.org/data/definitions/101.html) là con của Remote Code Inclusion, không phải 242 |

**Kết luận ánh xạ:** trùng **4/6 nhãn** (kể cả NORMAL), thiếu 2, thừa 4. Cần **bộ nhãn rút gọn 4 lớp**: NORMAL, SQL_INJECTION, PATH_TRAVERSAL, OS_COMMAND_INJECTION. Các mẫu ECML thuộc XSS/LDAP/XPath/SSI bị bỏ (hoặc, nếu muốn, đưa vào làm lớp ngoài tập để xem mô hình phản ứng thế nào, nhưng đây là thiết kế khác, không nằm trong phạm vi đề xuất). Mẫu đa lớp bị loại, giống cách [`prepare.py`](../../src/preprocessing/prepare.py) loại mẫu multi-label (hàm `scan_csv`). Thang điểm 4 lớp **không so sánh trực tiếp** với 6 lớp của SR-BH; chỉ so được hướng và thứ hạng phương pháp (B so với zero-shot, C so với B).

## 4. Công sức tích hợp vào pipeline hiện có

Đã đọc: [`prepare.py`](../../src/preprocessing/prepare.py), [`data_io.py`](../../src/experiments/data_io.py), [`data.json`](../../src/configs/data.json). **Chưa đọc** prompt, `run_llm.py`, retrieval, nên mục 4 là ước lượng.

| Việc | Lý do (theo mã đã đọc) | Công sức |
| --- | --- | --- |
| Bộ chuyển ECML XML → JSONL `request_text` chuẩn | `prepare.py` chỉ đọc CSV có cột `request_http_method`, `request_http_request`... và cột nhãn kiểu `66 - SQL Injection` (`scan_csv`); không dùng lại được nguyên trạng. Cần module mới xuất cùng schema (`method/uri/protocol/headers/body`, hàm `build_request`) | 0,5–1 ngày |
| Giữ **toàn bộ** header thay vì 11 header cố định | Xem mục 1.3 (18–27% tấn công nằm ở cookie/header) | gộp vào dòng trên |
| Chia train/val/test không rò rỉ | Có thể dùng lại `group_key`/`assign_groups`. **Rủi ro:** vì URL/giá trị bị ngẫu nhiên hóa, quy tắc nhóm "che số và hex dài" sẽ cho gần như mỗi request một nhóm, khiến kiểm tra rò rỉ yếu hơn SR-BH; phải ghi rõ là hạn chế | 0,5 ngày |
| Tổng quát hóa `data_io.py` | `DATA_DIR` và `LABELS` cố định từ `data.json`; `load_split` từ chối nhãn ngoài `LABELS`. Cần tham số hóa theo dataset | 0,5 ngày |
| Prompt / tập nhãn 4 lớp, dựng lại chỉ mục MiniLM | Chưa đọc; giả định chỉ cần đổi danh sách nhãn. Chỉ mục chạy cục bộ, không tốn API | 0,5 ngày |
| Chạy, phân tích, đưa vào báo cáo | | xem kế hoạch |

Tổng công sức viết mã: khoảng **2–3 ngày làm việc**. Lưu ý quan trọng: phiên khác đang chạy thực nghiệm có phí ngay trong checkout này ở nhánh `test/c-improvements` và sửa `src/`; việc tổng quát hóa `data_io.py` nên làm **sau khi phiên đó xong** hoặc ở nhánh/worktree riêng để không đè lên nhau.

### Chi phí API

Giả định theo yêu cầu: ~1.500 token/lần gọi (toàn bộ tính là input), gpt-oss-20b 0,075 / 0,30 USD mỗi triệu token input/output, một bộ = 7 lượt × 300 request = 2.100 lần gọi. Output chưa biết nên thử hai mức:

| Output/lần gọi | Chi phí thực | Chi phí theo sổ cái (giá gấp đôi, như quy ước dự án) |
| --- | ---: | ---: |
| 100 token | ≈ 0,30 USD | ≈ 0,60 USD |
| 500 token (mô hình suy luận dài) | ≈ 0,55 USD | ≈ 1,10 USD |

Công thức: 2.100 × (1.500 × 0,075 + output × 0,30) / 10⁶. Với ~1,3 USD đã chi và trần 5 USD, còn đủ chỗ, kể cả khi mỗi request ECML dài hơn 1.500 token (request ECML có nhiều header, xem [mẫu](https://raw.githubusercontent.com/msudol/Web-Application-Attack-Datasets/master/README.md); chưa đo token thật). Bộ rút gọn (ví dụ chỉ A0, B, C-knn, C-gated = 4 lượt) chỉ tốn khoảng 57% mức trên. Giá lấy từ đề bài, chưa kiểm lại với bảng giá Groq hiện hành.

## 5. Kế hoạch từng ngày (nếu GO)

Giả định bắt đầu thứ Ba 03/11; hạn 14/11 là thứ Bảy.

| Ngày | Việc | Cổng kiểm |
| --- | --- | --- |
| 03/11 | **Cổng 0:** xin phép tải `learning_dataset_xml.zip` (~20 MB) vào thư mục riêng ngoài `src/`, tính checksum, đếm số mẫu từng lớp và mẫu đa lớp, đọc ~20 mẫu/lớp, đọc điều khoản nếu tìm thấy | **NO-GO** nếu một trong 4 lớp có ít hơn khoảng 60 mẫu đơn lớp (cần 50/lớp ở test + pool + validation), hoặc chữ ký tấn công bị ngẫu nhiên hóa đến mức đọc không ra |
| 04/11 | Viết bộ chuyển XML → JSONL, chia nhóm, kiểm rò rỉ (nhánh/worktree riêng) | Test đơn vị đạt |
| 05/11 | Tham số hóa `data_io.py`, nhãn 4 lớp, dựng chỉ mục MiniLM, chạy thử giả (mock) | Không gọi API thật |
| 06/11 | Khóa cấu hình **giữ nguyên** từ SR-BH (k=4 v.v.), không dò lại tham số; ghi file khóa trước khi chạy test; chạy validation nhỏ | File khóa có commit trước |
| 07–08/11 (cuối tuần) | Chạy bộ test 300 request, các lượt đã chọn (tối đa 7) | Chi phí ≤ 1,1 USD theo sổ cái |
| 09–10/11 | Phân tích: macro-F1, kiểm định, so với SR-BH; nói rõ lớp thiếu và dữ liệu bị làm mờ | |
| 11–12/11 | Đưa kết quả vào báo cáo cuối (một mục "Kiểm tra trên dataset thứ hai") | |
| 13/11 | Dự phòng, kiểm tra tái lập | |
| 14/11 | Nộp | |

Nếu Cổng 0 không đạt: ghi hạn chế vào báo cáo cuối và dùng 3 ngày đó cho phần còn lại; không tốn đồng API nào.

## 6. Chưa xác minh được

1. Số mẫu từng lớp của ECML/PKDD (không bảng nào tìm được; cần tải file).
2. Trang "Data" chính thức bị lỗi 500 ngày 02/11/2026; không rõ có điều khoản dữ liệu hay không. Mirror chưa đối chiếu byte với bản gốc; GitLab nguồn của mirror không truy cập được.
3. Cách ba bộ số lượng (50.000/70% tấn công; 70.000/60%; 35.006 + 15.110) liên hệ với nhau.
4. Có bao nhiêu mẫu ECML đa lớp, và `learning_dataset_xml.zip` có đúng 8 lớp trên mọi mẫu hay không.
5. Bài báo gốc của CSIC 2010, các trường dữ liệu của bộ Lucz & Forstner, nội dung DarkSegmentsIDS.
6. Lớp CODE_INJECTION của SR-BH thực tế chứa loại payload nào (cần đối chiếu nếu muốn gộp XSS).
7. Prompt, `run_llm.py`, retrieval chưa đọc nên ước lượng công sức mục 4 có thể lệch.
8. Số token thực của request ECML và token output thực của gpt-oss-20b.

## Bổ sung 02/11/2026: tìm dataset mới hơn ECML/PKDD 2007

Lý do tìm thêm: dữ liệu năm 2007 (và cả SR-BH 2020) không có các dạng payload mới như Log4Shell hay tấn công vào API JSON.

| Dataset | Năm, nguồn | Nội dung | Nhãn | Phù hợp với đề tài? |
| --- | --- | --- | --- | --- |
| open-appsec WAF Comparison Project | Cập nhật hằng năm, bản 2026; [GitHub](https://github.com/openappsec/waf-comparison-project), [tài liệu](https://docs.openappsec.io/references/waf-comparison-project) | 1.040.242 request **hợp lệ thật** (JSON, Apache 2.0) và 73.924 **payload** tấn công lấy từ [mgm WAF Payload Collection](https://github.com/mgm-sp/WAF-Payload-Collection) (phần lớn MIT) | Payload chia theo loại: SQL Injection, XSS, XXE, Path Traversal, Command Execution, Log4Shell, Shellshock | **Tốt nhất cho câu hỏi "payload hiện đại"**: trùng 4 lớp (Normal, SQLi, Path Traversal, OS Command). Hạn chế: do nhà cung cấp WAF công bố, không qua bình duyệt; phía tấn công là chuỗi payload, phải tự ghép vào request nên là dữ liệu bán tổng hợp |
| 30 ngày request bị ModSecurity chặn | 2025; Lucz & Forstner, *Data* 10(11):186, [DOI](https://doi.org/10.3390/data10110186), [Zenodo](https://zenodo.org/records/17178461), CC BY 4.0 | Request thật trên máy chủ thật năm 2025 | Theo loại tấn công, do luật OWASP CRS gán | Payload mới và thật, nhưng **không có lớp Normal** và nhãn do luật WAF gán (dễ thành vòng tròn). Chỉ dùng được như bộ thử độ nhạy theo loại tấn công |
| HttpParamsDataset | Khoảng 2015–2019; [GitHub](https://github.com/Morzeux/HttpParamsDataset/) | Chỉ có **giá trị tham số**, không phải request đầy đủ | sqli 10.852, xss 532, cmdi 89, path-traversal 290 và norm | Kém: lớp nhỏ quá ít mẫu, thiếu ngữ cảnh request |
| Biblio-US17 | Thu năm 2017, công bố 2023 (Díaz-Verdejo và cộng sự, *Computers & Security*); [README](https://dtstc.ugr.es/neus-cslab/wp-content/uploads/2023/08/README.txt), CC BY-NC | Hơn 47 triệu request **thật** của thư viện Đại học Sevilla, đã ẩn danh; chỉ có method/URI/protocol | Mức độ tấn công 1–4, **không có loại tấn công** | Không hợp với bài toán phân loại 6 lớp |
| WEB-IDS23 | 2025; Lanfer và cộng sự, [arXiv:2502.03909](https://arxiv.org/abs/2502.03909) | Hơn 12 triệu mẫu, 82 đặc trưng **mức flow**, sinh trong testbed | 21 nhãn | Không hợp: không phải nội dung HTTP request |
| ECML/PKDD 2007 (Electronics 2025 vẫn dùng: [MDPI](https://www.mdpi.com/2079-9292/14/21/4172)) | 2007 | Request bị làm mờ | 7 loại tấn công và Normal | Cũ, nguồn tải đang lỗi (xem phần trên) |

**Kết luận bổ sung:** chưa tìm thấy dataset nào vừa **mới**, vừa là **lưu lượng thật**, vừa có **nhãn theo loại tấn công** và có cả lớp Normal. Đây là khoảng trống đã được nhắc trong các khảo sát.

Nếu muốn kiểm tra với payload hiện đại, hướng khả thi nhất là ghép **request hợp lệ thật của open-appsec** với **payload theo loại của mgm**. Phải ghi rõ đây là dữ liệu bán tổng hợp. Tập này chỉ dùng làm bộ thử, không thay SR-BH làm benchmark chính.
