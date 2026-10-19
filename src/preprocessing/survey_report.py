"""Render the evidence-backed Vietnamese survey report and exportable figures.

The CSV survey itself has no third-party dependencies. Figures require
matplotlib; see src/requirements-survey.txt for the validated plotting version.
"""

import argparse
import json
from pathlib import Path
import textwrap


def number(value):
    return f"{value:,}".replace(",", ".")


def percent(value):
    precision = 6 if 0 < value < .001 else 3
    return f"{value:.{precision}f}".replace(".", ",")


def raw_http(example, headers):
    row = example["row"]
    lines = [f"{row['request_http_method']} {row['request_http_request']} {row['request_http_protocol']}"]
    lines.extend(f"{name}: {row[col]}" for col, name in headers.items() if row[col] != "")
    lines.extend(["", row["request_body"]])
    return "\n".join(lines)


def make_figures(stats, examples, pair, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "pdf.fonttype": 42})
    fig = plt.figure(figsize=(11, 6), facecolor="white")
    fig.text(.05, .94, "Nearly identical requests, different source labels", fontsize=17, weight="bold")
    for name, title, y, color in [("pair_normal", "Normal — source label 000", .55, "#147d64"), ("pair_attack", "SQL Injection — CAPEC-66", .22, "#a4332a")]:
        e = examples[name]
        fig.add_artist(FancyBboxPatch((.045, y), .91, .27, boxstyle="round,pad=0.012", transform=fig.transFigure,
                                    facecolor="#f5f7fa", edgecolor=color, linewidth=1.3))
        fig.text(.065, y + .215, title, color=color, weight="bold", fontsize=13)
        fig.text(.67, y + .218, f"CSV index {e['raw_index']} | pool", fontsize=10, color="#435366")
        uri = e["row"]["request_http_request"]
        wrapped = "\n".join(textwrap.wrap(uri, width=105, break_long_words=True, break_on_hyphens=False))
        fig.text(.065, y + .165, "GET " + wrapped + "\nHTTP/1.1", fontfamily="DejaVu Sans Mono", fontsize=9.4, va="top", color=color)
    fig.text(.065, .16, "Only request-target differs:  format=xml  →  format=xml+AND+1%3D1", fontsize=12, weight="bold", color="#a4332a")
    fig.text(.065, .11, f"URI character similarity: {pair['uri_similarity'] * 100:.2f}% | Same method, protocol, headers and empty body", fontsize=11)
    fig.text(.065, .065, "Display wraps URI lines. Full original field values are in the report and evidence JSON.", fontsize=9, color="#435366")
    fig.text(.065, .035, "Motivating illustration; embedding similarity and retrieval errors have not been measured.", fontsize=9, color="#435366")
    for extension in ("png", "svg", "pdf"):
        fig.savefig(output / f"sr_bh_motivating_pair.{extension}", dpi=240)
    plt.close(fig)

    values = sorted(stats["class_distribution"], key=lambda r: r["samples"], reverse=True)
    fig, ax = plt.subplots(figsize=(12, 7.5))
    fig.subplots_adjust(left=.35, right=.92, top=.90, bottom=.11)
    positions = list(range(len(values)))
    colors = ["#2674a8" if r["label"].startswith("000") else "#c56545" for r in values]
    ax.barh(positions, [r["samples"] for r in values], color=colors)
    ax.set_yticks(positions, [r["label"] for r in values], fontsize=9)
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlim(.6, 2000000)
    for i, row in enumerate(values):
        ax.text(row["samples"] * 1.13, i, f"{row['samples']:,}", va="center", fontsize=9)
    ax.set_xlabel("Requests with active label (log scale; labels may co-occur)")
    ax.set_title("SR-BH 2020: class distribution from the actual CSV", pad=18, fontsize=14)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=.2)
    ax.set_axisbelow(True)
    for extension in ("png", "svg", "pdf"):
        fig.savefig(output / f"sr_bh_class_distribution.{extension}", dpi=220)
    plt.close(fig)


def render(stats, examples, pair, config, summary, metadata, search):
    total = stats["totals"]["records"]
    rows = sorted(stats["class_distribution"], key=lambda r: r["samples"], reverse=True)
    table = "\n".join(f"| {r['label']} | {number(r['samples'])} | {percent(r['percent_of_records'])}% |" for r in rows)
    categories = {
        "timestamp": ("Metadata", "Thời điểm request; chuỗi có timezone"),
        "src_ip": ("Metadata", "IP nguồn đã ghi trong log"), "src_port": ("Metadata", "Port nguồn"),
        "dst_ip": ("Metadata", "IP đích"), "dst_port": ("Metadata", "Port đích"),
        "request_http_method": ("Request line", "HTTP method"),
        "request_http_request": ("Request line", "Request-target: path và query, không phải lúc nào cũng là URL đầy đủ"),
        "request_http_protocol": ("Request line", "HTTP protocol/version"),
        "request_body": ("Body", "Request body thô; có thể là form-urlencoded"),
        "response_http_protocol": ("Response", "Protocol của response"),
        "response_http_status_code": ("Response", "HTTP status code"),
        "response_http_status_message": ("Response", "HTTP status message"),
        "response_content_length": ("Response", "Độ dài response theo log"),
    }
    categories.update({c: ("Request header", h) for c, h in config["headers"].items()})
    fields = "\n".join(f"| `{c}` | {categories[c][0]} | {categories[c][1]} | {number(stats['empty_fields'][c])} |" for c in stats["columns"] if c not in stats["label_columns"])
    hist = "; ".join(f"{k} nhãn: {number(v)}" for k, v in stats["label_cardinality"].items())
    example_blocks = []
    for name, title in [("benign", "5.1. Request mang nhãn Normal"), ("sqli", "5.2. Request mang nhãn SQL Injection"), ("xss", "5.3. Request có payload XSS; không có lớp XSS riêng")]:
        e = examples[name]
        labels = ", ".join(f"`{label}`" for label in e["labels"])
        explanation = {
            "benign": "Request truy vấn oEmbed với `format=xml`; không thấy attack token rõ trong URI, headers hoặc body được ghi lại. Đây là đánh giá nội dung cùng nhãn nguồn, chưa phải xác nhận chuyên gia hoặc bằng chứng server an toàn tuyệt đối.",
            "sqli": "Tham số format chứa nguyên văn `xml+AND+1%3D1`. Khi giải thích percent-encoding/form notation, phần thêm có dạng ` AND 1=1`, phù hợp cú pháp kiểm tra SQL injection. Đây là request có dấu hiệu thử SQLi, không chứng minh khai thác thành công. Dataset ghi response 200 cho cả request này và request Normal.",
            "xss": "Payload `<script>alert(document.cookie)</script>` nằm trực tiếp trong URI. Dataset gán Code Injection và Scanning for Vulnerable Software; không được đổi thành một nhãn XSS vốn không tồn tại. User-Agent ghi Nmap Scripting Engine. Chỉ xác nhận có payload XSS trong request; không có browser execution trace để kết luận reflected/stored XSS thành công. Record này multi-label, vì vậy không nằm trong benchmark single-label v1.",
        }[name]
        example_blocks.append(f"""### {title}

- Raw index (0-based): **{e['raw_index']}**; số thứ tự record CSV tính header: **{e['csv_record']}**.
- Timestamp nguyên văn: `{e['row']['timestamp']}`.
- Nhãn nguồn đang active: {labels}.
- Request ID: `{e['request_id']}`.
- `request_body` nguyên văn là chuỗi rỗng (`""`).

`request_http_request` nguyên văn, không decode/rút gọn:

```text
{e['row']['request_http_request']}
```

Request dựng lại từ các trường CSV, giữ nguyên giá trị các header có dữ liệu:

```http
{raw_http(e, config['headers'])}
```

{explanation}
""")
    normal = examples["pair_normal"]
    attack = examples["pair_attack"]
    raw_differences = [c for c in stats["columns"] if normal["row"][c] != attack["row"][c]]
    source_files = [x["dataFile"]["filename"] for x in metadata["data"]["latestVersion"]["files"]]
    return f"""# Khảo sát SR-BH 2020 trên dữ liệu thật — trả lời 7 câu hỏi của giảng viên

Ngày thực hiện: 19/10/2026. Báo cáo này được tạo bằng cách đọc **toàn bộ CSV thật**, không lấy số liệu từ mô tả website. Số liệu ở câu 1–4 là dữ liệu gốc trước lọc single-label, khác số liệu 466.267 request của pipeline v1.

Nguồn: [Harvard Dataverse, DOI 10.7910/DVN/OGOIXX](https://doi.org/10.7910/DVN/OGOIXX), dataset version 1.2, file ID 6319496, giấy phép CC0 1.0 theo metadata nguồn. File local: `src/data/raw/data_capec_multilabel.csv`, **{number(stats['input']['bytes'])} byte**.

- MD5: `{stats['input']['md5']}`, đã khớp checksum nguồn.
- SHA-256: `{stats['input']['sha256']}`.
- [Thống kê máy đọc được](../../src/artifacts/data/sr_bh_survey/stats.json), [record gốc của các ví dụ](../../src/artifacts/data/sr_bh_survey/examples.json), [kiểm chứng](../../src/artifacts/data/sr_bh_survey/verification.json).
- Raw index là thứ tự record CSV bắt đầu từ 0, không tính header. CSV record = raw index + 2; không bảo đảm bằng số dòng vật lý nếu một field chứa newline.

## 1. Tổng số bản ghi (request) là bao nhiêu?

**{number(total)} record CSV**, không tính header. Trong đó **{number(stats['totals']['normal_records'])}** record có nhãn Normal và **{number(stats['totals']['attack_records'])}** record có ít nhất một nhãn attack; không có record đồng thời Normal và attack.

Có **{len(stats['missing_method_or_uri_indices'])} record thiếu method/URI**, raw indices `{stats['missing_method_or_uri_indices']}`; vì vậy có {number(total - len(stats['missing_method_or_uri_indices']))} record có đủ hai trường HTTP thiết yếu này. Không âm thầm loại hai record đó khi báo tổng CSV.

Mô tả nguồn ghi 907.814; file tải thực tế đã khớp checksum có 907.815. Chưa xác định nguyên nhân chênh một record với mô tả; không tự suy diễn là do header hoặc duplicate.

## 2. Có bao nhiêu nhãn/lớp tấn công? Tên và số lượng từng lớp?

**13 lớp tấn công + 1 nhãn Normal = 14 cột nhãn binary.** Không có nhãn XSS riêng. CAPEC-248 Command Injection và CAPEC-88 OS Command Injection là hai cột khác nhau, không gộp khi thống kê.

| Nhãn gốc | Số record có nhãn = 1 | % trên tổng {number(total)} record |
| --- | ---: | ---: |
{table}

Đây là dữ liệu **multi-label**: một request có thể đóng góp vào nhiều hàng. Phân bố số nhãn active trên record: {hist}. Tổng số lượt gán nhãn không phải tổng số request; không cộng bảng lớp rồi coi là số record độc lập.

![Phân bố lớp với trục log](figures/sr_bh_class_distribution.png)

[SVG](figures/sr_bh_class_distribution.svg) · [PDF](figures/sr_bh_class_distribution.pdf). Trục log giúp nhìn thấy lớp singleton; chiều dài thanh không phải tỷ lệ tuyến tính.

## 3. Dữ liệu có mất cân bằng nghiêm trọng không? Lớp lớn nhất gấp bao nhiêu lần lớp nhỏ nhất?

**Có, ở bài toán phân loại loại tấn công.**

- Chỉ xét attack classes: SQL Injection 250.311 / Command Injection 1 = **250.311 lần**.
- Nếu tính cả Normal: Normal 525.195 / Command Injection 1 = **525.195 lần**.
- Bỏ riêng lớp singleton CAPEC-248, lớp attack nhỏ nhất còn lại là HTTP Request Smuggling 1.059: 250.311 / 1.059 ≈ **{stats['imbalance']['attack_ratio_excluding_singletons']:.2f} lần**. Mất cân bằng vẫn rất lớn.
- Nếu chỉ chuyển sang bài toán binary Normal/Attack thì tỷ lệ là 525.195 / 382.620 ≈ **{stats['imbalance']['binary_normal_attack_ratio']:.3f} lần**. Không dùng tỷ lệ binary này để kết luận bài toán 13 attack classes cân bằng.

Lớp một mẫu không đủ để chia pool/validation/test có ý nghĩa. Phạm vi single-label v1 hiện giữ Normal, SQL Injection, Path Traversal, Code Injection, HTTP Response Splitting và OS Command Injection; đây là quyết định thu hẹp phạm vi, không phải phân bố của nguồn gốc. Cần báo support từng lớp và Macro-F1/per-class metrics khi chạy model; không dựa vào Accuracy đơn lẻ.

## 4. Mỗi bản ghi gồm những trường nào?

**38 cột = 5 metadata + 15 request fields + 4 response fields + 14 nhãn.** Dưới đây là đủ 24 cột không phải nhãn; 14 tên cột nhãn đã liệt kê nguyên văn ở câu 2.

| Tên cột nguyên văn | Nhóm | Nội dung | Record có giá trị rỗng (`""`) |
| --- | --- | --- | ---: |
{fields}

`request_body` rỗng ở **{number(stats['empty_fields']['request_body'])}/{number(total)} record ({stats['empty_fields']['request_body'] / total * 100:.3f}%)**; còn **{number(total - stats['empty_fields']['request_body'])}** record có body không rỗng. Rỗng trong CSV có thể là request không có body hoặc body không được ghi lại; không thể phân biệt hai trường hợp chỉ từ field rỗng. Không bỏ body khỏi input vì nhiều payload POST nằm ở đó.

Các header chỉ là các trường đã được log, không phải bản wire capture đầy đủ hoặc toàn bộ header có thể có. URL thường ở dạng path/query; muốn dựng absolute URL còn cần Host và thông tin scheme mà CSV không luôn cung cấp. Response/status là thông tin sau request, không đưa vào input phát hiện tấn công của Pipeline A để tránh shortcut/leakage. Các cột nhãn không có giá trị rỗng trong file này.

## 5. Trích 3 ví dụ: benign, SQLi và XSS — payload nguyên văn

Các block URI bên dưới chép nguyên giá trị field CSV, giữ percent-encoding và ký tự gốc, không dùng `...`. Block HTTP là bản dựng lại từ các field được log; thứ tự/tên header do trình bày lại, không khẳng định đây là raw HTTP bytes trên đường truyền. Giá trị header/body không bị sửa. Toàn bộ 38 trường của từng record nằm trong [evidence JSON](../../src/artifacts/data/sr_bh_survey/examples.json).

{''.join(example_blocks)}
Không thể suy ra tổng số mẫu XSS từ ví dụ này: payload có thể encoded/obfuscated và taxonomy không có cột XSS. Không coi một regex tìm `<script>` là bộ gán nhãn hoặc thống kê XSS đầy đủ.

## 6. Dataset đã chia sẵn train/test chưa? Nếu chưa, dự định chia theo tỷ lệ nào?

**Không thấy split train/test được tác giả cung cấp trong dataset version đã tải.** Metadata version 1.2 có các file: `{source_files}`; CSV không có cột chỉ định train/test/split/fold/partition. Kết luận này dựa trên cả danh sách file của nguồn và schema thật, không suy ra từ tên cột `HTTP Response Splitting`.

Protocol inference-only của repo dùng **pool/validation/test khoảng 70/15/15 theo nhóm**, không coi pool là dữ liệu fine-tune. Group exact/near-duplicates trước khi chia. Dành development từ pool theo trọn nhóm để sửa prompt, không lấy demonstrations từ development/validation/test.

Split v1 đã được tạo trên phần sáu lớp single-label sau xử lý:

| Split | Request unique | Vai trò |
| --- | ---: | --- |
| Pool sau khi dành development | {number(summary['split_sizes']['pool'])} | Demonstrations/retrieval pool |
| Development | {number(summary['split_sizes']['development'])} | Smoke test và sửa prompt |
| Validation đầy đủ | {number(summary['split_sizes']['validation'])} | Chọn cấu hình |
| Test đầy đủ | {number(summary['split_sizes']['test'])} | Benchmark cuối khi protocol được khóa |

Seed 42; pilot subsets pool 3.000, validation 200, test dự kiến 600. Mọi nhóm phải nằm trọn một split; tỷ lệ row có thể lệch tỷ lệ group. Manifest và checksum nằm ở `src/data/processed/sr_bh_v1`. Test mới được audit cấu trúc, chưa chạy LLM/chỉnh prompt. Cặp minh họa ở câu 7 lấy từ pool.

Quy tắc grouping v1 mới mask số/hex trên request đầy đủ. Audit đạt theo quy tắc đó, nhưng endpoint/campaign/semantic near-duplicates có thể còn giao nhau; cần rà lại protocol trước final benchmark. Chưa chốt benchmark cuối cùng vì review trước đó cũng phát hiện một số nhãn Normal chứa payload đáng nghi.

## 7. Cặp benign/attack rất giống nhau và Figure motivating example

**Đã tìm được một cặp có thể kiểm tra trực tiếp**, dùng hai record chính là ví dụ Normal và SQLi ở câu 5:

| Thuộc tính | Normal theo nhãn nguồn | SQL Injection theo nhãn nguồn |
| --- | --- | --- |
| Raw index | {normal['raw_index']} | {attack['raw_index']} |
| CSV record tính header | {normal['csv_record']} | {attack['csv_record']} |
| Timestamp | `{normal['row']['timestamp']}` | `{attack['row']['timestamp']}` |
| Split | pool | pool |
| Method / protocol | GET / HTTP/1.1 | GET / HTTP/1.1 |
| Body | Rỗng | Rỗng |
| 11 header fields được log | Giống hoàn toàn phía SQLi | Giống hoàn toàn phía Normal |
| Tham số khác biệt | `format=xml` | `format=xml+AND+1%3D1` |

**Toàn bộ URI nguyên văn của Normal:**

```text
{normal['row']['request_http_request']}
```

**Toàn bộ URI nguyên văn của SQLi:**

```text
{attack['row']['request_http_request']}
```

Khác biệt duy nhất trong representation request là chuỗi chèn **`+AND+1%3D1`** vào giá trị `format`. Khi diễn giải query notation, đó là ` AND 1=1`. Method, protocol, cả 11 header fields (gồm Cookie/User-Agent/Referer) và body đều giống nhau. Xét toàn record CSV, các cột khác nhau là `{raw_differences}`; metadata/response/labels không nằm trong similarity request đang báo.

- URI character similarity: **{pair['uri_similarity'] * 100:.4f}%**.
- Full serialized request character similarity: **{pair['request_text_similarity'] * 100:.4f}%**.
- Công thức: `difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() = 2M / (len(a) + len(b))`, với M là tổng độ dài matching blocks. Đây là character similarity, **không phải embedding cosine similarity**. Score full request cao một phần do headers dài giống nhau; báo cả score URI để tránh che yếu tố này.
- Nhãn nguồn là Normal và SQL Injection; không có bằng chứng request SQLi đã được server thực thi thành công. Normal không có attack token rõ trong dữ liệu quan sát, nhưng chưa có chuyên gia adjudicate cặp này.

![Motivating example từ hai record thật](figures/sr_bh_motivating_pair.png)

[SVG để biên tập](figures/sr_bh_motivating_pair.svg) · [PDF vector](figures/sr_bh_motivating_pair.pdf).

**Caption đề xuất:** Two real SR-BH 2020 requests share the method, protocol, recorded headers and empty body, but differ by the insertion `+AND+1%3D1` into the `format` query parameter. The source labels are Normal and SQL Injection, respectively. Their URI character similarity is {pair['uri_similarity'] * 100:.2f}%. The example motivates testing whether label-aware demonstration selection can distinguish superficially similar requests; it does not establish a semantic-retrieval failure or a performance gain.

### Cách tìm và giới hạn của bằng chứng

Script `src/preprocessing/find_pair.py` chỉ đọc development/pool. Giữ Normal GET có URI tương đối đơn giản và không có một số attack tokens rõ; xét SQLi có cú pháp SQL trong URI. Ghép theo method/protocol/headers/body giống hoàn toàn, xếp theo similarity URI, tối đa 30 URI Normal ngắn nhất mỗi context. Search có {number(search['normal_candidates'])} Normal candidates, {number(search['attacks_with_matching_context'])} SQLi cùng context, và {number(search['pairs_compared_after_quick_filter'])} cặp qua quick filter. Đây là tìm kiếm có giới hạn, không tuyên bố tìm được cặp gần nhất toàn dataset. Các heuristics chỉ hỗ trợ chọn ví dụ để đọc, không thay nhãn nguồn.

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
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", default="src/artifacts/data/sr_bh_survey")
    parser.add_argument("--report", default="reports/surveys/khao_sat_sr_bh_2020.md")
    parser.add_argument("--figures", default="reports/surveys/figures")
    args = parser.parse_args()
    root = Path(args.artifacts)
    load = lambda path: json.loads(Path(path).read_text(encoding="utf-8"))
    stats, examples, pair = [load(root / name) for name in ("stats.json", "examples.json", "motivating_pair.json")]
    config, summary, metadata = [load(path) for path in ("src/configs/data.json", "src/artifacts/data/summary.json", "src/artifacts/data/source_metadata.json")]
    search = load(root / "pair_search.json")
    make_figures(stats, examples, pair, Path(args.figures))
    Path(args.report).write_text(render(stats, examples, pair, config, summary, metadata, search), encoding="utf-8")
    print(f"Report: {args.report}; figures: {args.figures}")


if __name__ == "__main__":
    main()
