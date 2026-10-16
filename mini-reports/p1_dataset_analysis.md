# P1: Dataset Survey — `data_capec_multilabel.csv`

> **Loại tài liệu:** Kết quả Phase 1 — Dataset Survey
> **Dataset:** `data_capec_multilabel.csv` (436 MB)
> **Trạng thái:** Phân tích sơ bộ hoàn tất — đang chờ kết quả deduplication analysis
> **Phân biệt:** 🔵 THỰC TẾ đo được | 🟡 GIẢ THUYẾT | 🟢 Đề xuất | ⚠️ VẤN ĐỀ cần xử lý

---

## 1. Thông Tin Cơ Bản

| Thuộc tính | Giá trị |
|---|---|
| **File** | `data_capec_multilabel.csv` |
| **Kích thước** | 436 MB |
| **Tổng rows** | 907,815 |
| **Tổng cột** | 38 |
| **Nguồn** | HTTP access logs với CAPEC annotation (July 2020) |
| **Format label** | Multi-label binary (mỗi cột là 1 CAPEC category, giá trị 0/1) |

---

## 2. Cấu Trúc Dataset

### 2.1. Các cột HTTP Request (Input cho LLM)

| Cột | Mô tả | Null count |
|---|---|---|
| `request_http_method` | GET / POST / PUT... | **2** (gần như đầy đủ) |
| `request_http_request` | URL path + query string | **2** (gần như đầy đủ) |
| `request_http_protocol` | HTTP/1.1 | ít null |
| `request_user_agent` | Browser/tool identifier | có null |
| `request_host` | Target hostname | có null |
| `request_referer` | Referrer URL | nhiều null |
| `request_cookie` | Cookie header | nhiều null |
| `request_body` | POST body | **881,072 null (97.1%!)** |

> ⚠️ **Vấn đề 1 — Body chủ yếu NULL:** 97.1% rows không có body → dataset này chủ yếu là **GET requests**. Phần lớn attack payload nằm ở URL path/query string, không phải POST body.

### 2.2. Các cột Label (Output)

Dataset dùng **multi-label binary** với 13 attack category:

| CAPEC Label | Count (tổng) | % (tổng) |
|---|---|---|
| `000 - Normal` | 525,195 | 57.85% |
| `66 - SQL Injection` | 250,311 | 27.57% |
| `194 - Fake the Source of Data` | 56,145 | 6.18% |
| `34 - HTTP Response Splitting` | 19,738 | 2.17% |
| `126 - Path Traversal` | 20,992 | 2.31% |
| `242 - Code Injection` | 15,827 | 1.74% |
| `272 - Protocol Manipulation` | 9,153 | 1.01% |
| `274 - HTTP Verb Tampering` | 5,437 | 0.60% |
| `88 - OS Command Injection` | 7,482 | 0.82% |
| `310 - Scanning for Vulnerable Software` | 2,718 | 0.30% |
| `153 - Input Data Manipulation` | 2,272 | 0.25% |
| `16 - Dictionary-based Password Attack` | 1,847 | 0.20% |
| `248 - Command Injection` | **1** | **0.0001%** |

---

## 3. Phân Tích Multi-Label

🔵 **Thực tế đo được:**

| Số label per row | Count | % |
|---|---|---|
| 1 label (single-label) | **898,577** | **99.0%** |
| 2 labels | 8,132 | 0.90% |
| 3 labels | 1,088 | 0.12% |
| 4 labels | 18 | 0.002% |

🟢 **Kết luận:** 99% rows có đúng 1 label → **có thể dùng trực tiếp** cho bài toán single-label classification của đề tài. Multi-label rows (1%) cần xử lý (loại bỏ hoặc assign label chính).

### Distribution single-label rows (898,577 rows):

| Label | Count | % |
|---|---|---|
| **000 - Normal** | 525,195 | **58.45%** |
| **66 - SQL Injection** | 248,093 | **27.61%** |
| **194 - Fake the Source of Data** | 55,983 | 6.23% |
| **34 - HTTP Response Splitting** | 19,134 | 2.13% |
| **126 - Path Traversal** | 17,595 | 1.96% |
| **242 - Code Injection** | 13,793 | 1.53% |
| **272 - Protocol Manipulation** | 7,019 | 0.78% |
| **274 - HTTP Verb Tampering** | 4,055 | 0.45% |
| **88 - OS Command Injection** | 3,074 | 0.34% |
| **310 - Scanning for Vulnerable Software** | 2,413 | 0.27% |
| **153 - Input Data Manipulation** | 1,387 | 0.15% |
| **16 - Dictionary-based Password Attack** | 836 | 0.09% |
| **248 - Command Injection** | ~1 | ~0% |

---

## 4. Phân Tích Duplicate

🔵 **Thực tế đo được:**

| Loại duplicate | Count |
|---|---|
| Exact duplicate rows | 2,746 |
| Duplicate `request_http_request` paths | **557,474** (61.4%!) |
| **Same path, different label combination** | **1,517** |

> ⚠️ **Vấn đề 2 — Duplicate paths cực nhiều (61.4%):** Dataset capture HTTP logs theo thời gian thực → cùng một URL xuất hiện hàng trăm lần với cùng label. Ví dụ: `000 - Normal` có 525K rows nhưng chỉ 87,520 unique paths (16.7% unique!). Nếu không dedup, retrieval database sẽ chứa hàng nghìn near-identical demonstrations → làm giảm diversity.

> 🟢 **Hard cases thực tế:** 1,430 paths có multiple label combinations → đây chính là loại dữ liệu quan trọng để chứng minh giá trị của Label-Aware Retrieval.

### Unique paths per label (single-label rows):

| Label | Total rows | Unique paths | % unique |
|---|---|---|---|
| `000 - Normal` | 525,195 | 87,520 | **16.7%** — rất nhiều repeat |
| `66 - SQL Injection` | 248,093 | 175,515 | 70.7% |
| `194 - Fake the Source of Data` | 55,983 | 40,478 | 72.3% |
| `34 - HTTP Response Splitting` | 19,134 | 17,528 | 91.6% |
| `126 - Path Traversal` | 17,595 | 10,838 | 61.6% |
| `242 - Code Injection` | 13,793 | 9,340 | 67.7% |
| `272 - Protocol Manipulation` | 7,019 | 2,930 | 41.7% |
| `274 - HTTP Verb Tampering` | 4,055 | 915 | 22.6% |
| `88 - OS Command Injection` | 3,074 | 1,283 | 41.7% |
| `310 - Scanning for Vulnerable Software` | 2,413 | 2,351 | 97.4% |
| `153 - Input Data Manipulation` | 1,387 | **12** | **0.9%** — gần như toàn bộ là repeat! |
| `16 - Dictionary-based Password Attack` | 836 | 96 | 11.5% |

---

## 5. Sample Requests Per Label

```
[000 - Normal]
  Method: GET
  Path:   /

[66 - SQL Injection]
  Method: GET
  Path:   /blog/wp-admin/load-styles.php?c=0&dir=ltr&load%5B%5D=dashicons,...

[126 - Path Traversal]
  Method: GET
  Path:   /.svn/entries

[88 - OS Command Injection]
  Method: GET
  Path:   /index.php?s=/module/action/param1/${@die(sha1(xyzt))}

[242 - Code Injection]
  Method: GET
  Path:   /index.php?s=/Index/\x5Cthink\x5Capp/invokefunction&function=call_user_func_array&...
```

> ⚠️ **Nhận xét label noise:** SQLi sample `/blog/wp-admin/load-styles.php?...` trông như WordPress admin request bình thường → đây là annotation noise nghiêm trọng cần kiểm tra.

### HTTP Method Distribution:

| Method | Count | % |
|---|---|---|
| GET | 866,236 | **95.4%** |
| POST | 23,582 | 2.6% |
| TRACE | 2,340 | 0.26% |
| OPTIONS | 1,280 | 0.14% |
| HEAD | 1,082 | 0.12% |
| TRACK | 886 | 0.10% |
| COPY/LOCK/MKCOL/MOVE | 449 each | HTTP Verb Tampering attacks |

### Sample Hard Cases (cùng path, khác label):

```
Path: /
  Labels: ['000 - Normal', '272 - Protocol Manipulation',
           '310 - Scanning', '194 - Fake Source', '274 - HTTP Verb', '242 - Code Injection']
  → Root path '/' được label bởi 6 class khác nhau!

Path: /%22
  Labels: ['66 - SQL Injection', '272 - Protocol Manipulation']
  → URL-encoded '"' vừa là SQLi vừa là Protocol Manipulation

Path: /%22%27/wp-login.php
  Labels: ['66 - SQL Injection', '16 - Dictionary-based Password Attack']
  → WordPress login với SQL chars = SQLi + BruteForce

Path: /%22%3E%3C%21--%23EXEC+cmd%3D%22ls+%2F%22--%3E%3C/index.php/my-account
  Labels: ['000 - Normal', '66 - SQL Injection']
  → Command injection in URL labeled cả Normal lẫn SQLi!
```

> 🔴 **Cảnh báo annotation quality:** Root path `/` được gán 6 nhãn khác nhau trong các rows khác nhau — đây không phải genuine ambiguity mà nhiều khả năng là **annotation noise** (cùng root path, tùy context khác nhau bị gán nhãn khác nhau). Cần kiểm tra kỹ trước khi dùng.

---

## 6. Đánh Giá Theo Tiêu Chí Đề Cương

| Tiêu chí | Kết quả | Đánh giá |
|---|---|---|
| Có label rõ ràng cho từng request | ✓ 13 CAPEC categories, binary | ✅ Đạt |
| HTTP request đủ thông tin | Có method + path, body 97% null | ⚠️ Chấp nhận được (GET-heavy) |
| Có ≥ 3–4 attack classes | 12 attack classes + Normal | ✅ Đạt (nhiều hơn cần) |
| Đủ mẫu mỗi class | Normal 525K, SQLi 248K; nhưng CMDi chỉ 1 row | ⚠️ Imbalance nghiêm trọng |
| Có hard cases (same semantic, different label) | 1,517 paths với multi-label | ✅ Có — cần phân tích kỹ hơn |
| Có thể split retrieval/test | ✓ nhưng cần dedup trước | ⚠️ Phải dedup 61% duplicate paths |
| Không có quá nhiều duplicate | 61.4% duplicate paths | ❌ Vấn đề nghiêm trọng — phải xử lý |

---

## 7. Vấn Đề Cần Giải Quyết Trước Khi Dùng

### 7.1. ⚠️ Loại nhãn không phù hợp

Không phải tất cả CAPEC labels đều phù hợp cho bài toán **Web Attack Detection từ HTTP request**:

| Label | Phù hợp? | Lý do |
|---|---|---|
| `000 - Normal` | ✅ | Benign traffic |
| `66 - SQL Injection` | ✅ | Core web attack |
| `126 - Path Traversal` | ✅ | Core web attack |
| `242 - Code Injection` | ✅ | PHP/template injection |
| `88 - OS Command Injection` | ✅ | Relevant, có enough samples |
| `34 - HTTP Response Splitting` | ✅ | HTTP header injection |
| `272 - Protocol Manipulation` | 🟡 Cần xem | Có thể network-level |
| `274 - HTTP Verb Tampering` | ✅ | HTTP method abuse |
| `194 - Fake the Source of Data` | ⚠️ Mờ | CAPEC khá generic, cần xem samples |
| `153 - Input Data Manipulation` | 🟡 Cần xem | Overlap với Code Injection? |
| `310 - Scanning for Vulnerable Software` | 🟡 Cần xem | Scanner traffic |
| `16 - Dictionary-based Password Attack` | ⚠️ Ít samples (836) | Brute-force, khác với payload injection |
| `248 - Command Injection` | ❌ | Chỉ 1 row — vô dụng |

### 7.2. ⚠️ Duplicate paths phải được xử lý

Kết quả sau khi dedup by path (first occurrence per path, bất kể label):

| Metric | Giá trị |
|---|---|
| **Tổng unique paths** | **346,239** (giảm từ 907,815) |
| SQLi | 174,714 |
| Normal | 87,314 |
| Fake Source of Data | 40,040 |
| HTTP Response Splitting | 17,516 |
| Path Traversal | 10,762 |
| Code Injection | 9,327 |
| Protocol Manipulation | 2,509 |
| Scanning | 2,346 |
| OS Command Injection | 1,204 |
| HTTP Verb Tampering | 483 |
| Password Attack | **24** |
| `153 - Input Data Manipulation` | **0** (hoàn toàn bị đè bởi label khác khi dedup!) |

> 🔴 **Phát hiện quan trọng:** `153 - Input Data Manipulation` có 1,387 rows nhưng chỉ có **12 unique paths**. Sau dedup first-occurrence, toàn bộ 12 paths này đều bị label khác chiếm mất trước → **class này hoàn toàn không dùng được**.

Chiến lược dedup đề xuất:
1. **Bước 1 — Exact dedup:** Loại 2,746 exact duplicate rows
2. **Bước 2 — Path-level dedup per label:** Giữ 1 đại diện per `(path, label)` pair (không phải per path)
3. **Bước 3 — Hard cases (1,430 paths):** Tách riêng làm **hard case analysis set** — không loại bỏ vì có giá trị phân tích

### 7.3. ⚠️ Class imbalance nghiêm trọng

Sau dedup, size thực của mỗi class sẽ khác. Cần đo lại sau khi dedup.

---

## 8. Đề Xuất Attack Taxonomy Cho Đề Tài

🟢 **Dựa trên unique paths thực tế sau dedup, đề xuất scope 5–6 classes:**

```
1. Normal (Benign)            → 87,314 unique paths   ✔ đủ nhiều
2. SQL Injection               → 175,515 unique paths  ✔ lại nhất
3. Path Traversal              → 10,762 unique paths   ✔ được
4. Code Injection              → 9,327 unique paths    ✔ được
5. HTTP Response Splitting     → 17,516 unique paths   ✔ được
6. OS Command Injection        → 1,204 unique paths    ⚠️ tương đối ít
```

> **Lý do loại bỏ:**
> - `248 - Command Injection`: 1 row → loại
> - `153 - Input Data Manipulation`: 12 unique paths, after dedup = 0 rows usable → loại
> - `16 - Dictionary-based Password Attack`: chỉ 24 unique paths sau dedup + khác bản chất (brute-force) → loại
> - `194 - Fake the Source of Data`: 40K unique paths nhưng cần xem samples xác nhận đây là HTTP payload attack
> - `272 - Protocol Manipulation`: 2,509 unique paths, cần xem semantics
> - `274 - HTTP Verb Tampering`: 483 unique paths, tương đối ít
> - `310 - Scanning for Vulnerable Software`: 2,346 unique paths, scanner traffic (không phải payload attack)

---

## 9. Bước Tiếp Theo

| Bước | Nội dung | Ưu tiên |
|---|---|---|
| **9.1** | Xem samples của các nhãn nghi ngờ (`194`, `272`, `153`) để quyết định include/exclude | 🔴 Cao |
| **9.2** | Chạy deduplication: exact → path-level → đo lại distribution | 🔴 Cao |
| **9.3** | Phân tích 1,517 hard cases: cùng path nhưng khác label → tại sao? annotation error hay genuine ambiguity? | 🔴 Cao |
| **9.4** | Sau dedup: kiểm tra unique path count per label để xác nhận đủ samples | 🟡 Trung bình |
| **9.5** | Tạo preprocessed version: single-label only + deduped + 5–6 class scope | 🟡 Trung bình |
| **9.6** | Thiết kế split: Retrieval DB (80%) vs Test Set (20%) — stratified split | 🟡 Trung bình |

---

## 10. Đánh Giá Tổng Thể

**Dataset có thể dùng được cho đề tài, nhưng cần preprocessing đáng kể.**

✅ **Điểm mạnh:**
- HTTP request thực (method + path) — phù hợp với LLM input
- 99% single-label — dùng được cho single-label classification
- Đủ samples cho core classes (SQLi 175K unique, Normal 87K unique paths)
- 1,430 hard cases (same path, khác label) — tốt cho motivation và hard case analysis
- Có full HTTP fields (host, user-agent, cookie) nếu cần thêm context

⚠️ **Điểm cần xử lý:**
- 61.4% duplicate paths — phải dedup nghiêm túc
- Class imbalance nặng (Normal 58%, nhiều class <1%)
- 97% request body null — chỉ dùng URL path + query
- Một số CAPEC labels không rõ ràng về HTTP payload signature

❌ **Điểm yếu:**
- Dataset từ 2020 — có thể có các attack pattern cũ
- Annotation theo CAPEC (không phải standard web attack taxonomy như OWASP)
- `248 - Command Injection` chỉ có 1 row — unusable
