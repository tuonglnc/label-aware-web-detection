"""Dựng báo cáo giữa kỳ (Word) theo mẫu của Khoa, dùng lại bộ công cụ của bài DA-CK.

Không tính lại thực nghiệm: mọi số liệu được đọc từ các file kết quả trong src/artifacts/.
Chạy từ thư mục gốc repo (cần python-docx, lxml, matplotlib và Microsoft Office cho công thức):

    python reports/word/make_figures.py
    python reports/word/build_bao_cao_giua_ky.py
    python reports/word/export_word.py reports/progress/Bao_cao_giua_ky_LabelAware.docx   # cập nhật mục lục + xuất PDF
"""
from pathlib import Path
import copy
import json
import sys

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from report_lib import Report, set_text, mi, mn, mo, row, sub  # noqa: E402
from src.analysis.compare import plot_confusion  # noqa: E402
from src.analysis.metrics import classification_metrics, label_consistency_rate, mcnemar, paired_bootstrap  # noqa: E402
from src.retrieval.knn import knn_vote  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
WORD = ROOT / "reports" / "word"
BASE = WORD / "tpl" / "base.docx"
OUT_DOC = ROOT / "reports" / "progress" / "Bao_cao_giua_ky_LabelAware.docx"
ART = ROOT / "src" / "artifacts"
RET = ART / "retrieval" / "minilm"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


S = load(ART / "data" / "summary.json")
AUD = load(ART / "data" / "leakage_audit.json")
PAIR = load(ART / "data" / "sr_bh_survey" / "motivating_pair.json")
REV = load(ART / "data" / "manual_review_assessment.json")
EV = load(RET / "eval_validation" / "retrieval_metrics.json")
EVD = load(RET / "eval_development" / "retrieval_metrics.json")
RM = load(RET / "manifest.json")
A0M = load(ART / "runs" / "validation" / "A0" / "metrics.json")


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


# So sánh từng cặp A0 với kNN (k = 5) trên cùng 200 request validation.
VAL = {r["request_id"]: r["label"] for r in jsonl(ROOT / "src/data/processed/sr_bh_v1/validation_subset.jsonl")}
A0P = {r["request_id"]: (r["predicted_label"] if r["status"] == "ok" else None)
       for r in jsonl(ART / "runs" / "validation" / "A0" / "predictions.jsonl")}
KNNP = {r["request_id"]: knn_vote(r["candidates"][:30], 5)[0] for r in jsonl(RET / "neighbors_validation.jsonl")}
QIDS = sorted(VAL)
Y = [VAL[q] for q in QIDS]
ALL_LABELS = ("NORMAL", "SQL_INJECTION", "PATH_TRAVERSAL", "CODE_INJECTION", "HTTP_RESPONSE_SPLITTING",
              "OS_COMMAND_INJECTION")
BOOT = paired_bootstrap(Y, [A0P[q] for q in QIDS], [KNNP[q] for q in QIDS], ALL_LABELS)
MCN = mcnemar(Y, [A0P[q] for q in QIDS], [KNNP[q] for q in QIDS])

# Kết quả TẠM của B và BAL: các run chưa xong, nên so sánh trên đúng các request mà A0, B, BAL đều đã chạy.
INTERIM = {}
for _name in ("B_k4", "BAL_k4"):
    _dir = ART / "runs" / "validation" / _name
    if (_dir / "predictions.jsonl").exists():
        INTERIM[_name] = {r["request_id"]: r for r in jsonl(_dir / "predictions.jsonl")}
A0R = {r["request_id"]: r for r in jsonl(ART / "runs" / "validation" / "A0" / "predictions.jsonl")}
COMMON = sorted(set(A0R).intersection(*[set(x) for x in INTERIM.values()])) if INTERIM else []


def _preds(recs):
    return [recs[q]["predicted_label"] if recs[q]["status"] == "ok" else None for q in COMMON]


YC = [VAL[q] for q in COMMON]
IPRED = {"A0": _preds(A0R), **{n: _preds(r) for n, r in INTERIM.items()}}
C = S["counts"]
LCR = EV["lcr_at_k"]
KNN = EV["knn_vote"]
SHORT = {"NORMAL": "Normal", "SQL_INJECTION": "SQL Injection", "PATH_TRAVERSAL": "Path Traversal",
         "CODE_INJECTION": "Code Injection", "HTTP_RESPONSE_SPLITTING": "HTTP Response Splitting",
         "OS_COMMAND_INJECTION": "OS Command Injection"}
LABELS = list(SHORT)


def n(x):
    """Số nguyên kiểu Việt Nam: 466.267."""
    return f"{int(x):,}".replace(",", ".")


def v(x, d=3):
    s = f"{float(x):.{d}f}"
    if float(s) == 0:
        s = s.lstrip("-")  # tránh hiện "-0,000"
    return s.replace(".", ",")


def pct(x, d=1):
    return f"{100 * float(x):.{d}f}".replace(".", ",") + "%"


# Các nhận xét trong báo cáo dựa trên kết quả này; nếu kết quả đổi thì dừng để viết lại phần nhận xét.
assert EV["n_queries"] == 200 and EV["k"] == 4 and EV["n_candidates"] == 30 and EV["lambda"] == 0.1
assert A0M["complete"] and A0M["n"] == 200 and A0M["macro_f1"] > KNN["k=5"]["macro_f1"]
assert set(A0P) == set(VAL) == set(KNNP)
assert set(INTERIM) == {"B_k4", "BAL_k4"} and len(COMMON) >= 100
assert LCR["C_oracle_prior (analysis only)"]["mean"] > LCR["C_knn_prior"]["mean"] > LCR["B_semantic"]["mean"]
assert LCR["C_knn_prior"]["zero_match_rate"] > LCR["B_semantic"]["zero_match_rate"]
assert max(EV["rq1_top1_mismatch_by_class"], key=EV["rq1_top1_mismatch_by_class"].get) == "NORMAL"
assert 0.7 < KNN["k=5"]["macro_f1"] < 0.9

# ---------------------------------------------------------------------------
# Mở template, giữ phần bìa/lời cảm ơn/cam đoan/tóm tắt/mục lục, xóa phần thân cũ
# ---------------------------------------------------------------------------
R = Report(BASE)
body = list(R.body)
start = next(i for i, e in enumerate(body) if "".join(e.xpath(".//w:t/text()")) == "MỞ ĐẦU")
R.eq_template = copy.deepcopy(next(e for e in body[start:] if e.tag == qn("w:tbl")
                                   and e.find(".//" + qn("m:oMathPara")) is not None))
for extra in R.eq_template.findall(qn("w:tr"))[1:]:
    R.eq_template.remove(extra)
for e in body[start:-1]:
    R.body.remove(e)

TITLE = "CHỌN VÍ DỤ CÓ TÍNH ĐẾN NHÃN CHO MÔ HÌNH NGÔN NGỮ LỚN TRONG PHÂN LOẠI TẤN CÔNG WEB"
TITLE_EN = "LABEL-AWARE RETRIEVAL FOR LLM-BASED WEB ATTACK DETECTION"
ADVISOR = "[Học hàm, học vị và họ tên giảng viên hướng dẫn]"
MAJOR = "MẠNG MÁY TÍNH VÀ TRUYỀN THÔNG DỮ LIỆU"
b_lcr, c_lcr, o_lcr = (LCR[k]["mean"] for k in ("B_semantic", "C_knn_prior", "C_oracle_prior (analysis only)"))
summary = (
    "Đề tài nghiên cứu cách chọn ví dụ có nhãn (demonstrations) cho mô hình ngôn ngữ lớn (LLM) khi phân loại "
    "HTTP request thành sáu lớp: Normal, SQL Injection, Path Traversal, Code Injection, HTTP Response "
    "Splitting và OS Command Injection, theo hướng chỉ suy luận, không huấn luyện mô hình. Phương pháp đề "
    "xuất lấy top-N ứng viên giống request nhất rồi cộng điểm cho ứng viên có nhãn trùng với một dự đoán sơ bộ "
    "(prior) lấy từ LLM zero-shot hoặc kNN. Trên dữ liệu SR-BH 2020 (907.815 bản ghi, còn "
    f"{n(C['retained_unique_requests'])} request duy nhất sau tiền xử lý), nhóm đã chia tập theo nhóm request "
    "gần trùng, không có request nào trùng giữa các tập, và cài đặt toàn bộ hệ thống với 55 bài kiểm thử tự "
    f"động. Kết quả giữa kỳ trên 200 request validation cho thấy {pct(EV['rq1_top1_mismatch_rate'])} request có "
    f"ví dụ giống nhất mang nhãn khác, riêng lớp Normal là {pct(EV['rq1_top1_mismatch_by_class']['NORMAL'])}. "
    f"kNN vote không dùng LLM đạt Macro-F1 {v(KNN['k=5']['macro_f1'])}, còn LLM zero-shot (gpt-oss-20b) đạt "
    f"{v(A0M['macro_f1'])}. Xếp hạng lại theo prior kNN nâng tỷ lệ ví dụ cùng nhãn từ {v(b_lcr)} lên {v(c_lcr)}, "
    f"nhưng làm {pct(LCR['C_knn_prior']['zero_match_rate'])} request không còn ví dụ đúng lớp nào khi prior sai. "
    f"Kết quả tạm trên {len(COMMON)} request cho thấy đưa 4 ví dụ giống nhất vào prompt (B) giúp LLM tốt hơn "
    "zero-shot một cách có ý nghĩa thống kê. Các pipeline còn lại đang được chạy trong giới hạn quota API miễn phí.")
summary_en = (
    "This project studies how to select labeled demonstrations for a large language model (LLM) that "
    "classifies HTTP requests into six classes without any training. The proposed method retrieves the top-N "
    "most similar labeled requests and boosts candidates whose label matches a preliminary prediction (prior) "
    "from zero-shot LLM inference or kNN voting. On the SR-BH 2020 dataset (907,815 records; "
    f"{C['retained_unique_requests']:,} unique requests after preprocessing) the data were split by groups of "
    "near-duplicate requests with no overlap between splits, and the full system was implemented with 55 "
    f"automated tests. On 200 validation requests, {100 * EV['rq1_top1_mismatch_rate']:.1f}% of queries have a "
    f"nearest neighbour with a different label ({100 * EV['rq1_top1_mismatch_by_class']['NORMAL']:.1f}% for "
    f"Normal). kNN voting without an LLM reaches a macro-F1 of {KNN['k=5']['macro_f1']:.3f}, and zero-shot "
    f"gpt-oss-20b reaches {A0M['macro_f1']:.3f}. Prior-based "
    f"reranking raises the share of same-label demonstrations from {b_lcr:.3f} to {c_lcr:.3f}, but leaves "
    f"{100 * LCR['C_knn_prior']['zero_match_rate']:.1f}% of queries without any correct-class example when the "
    f"prior is wrong. Interim results on {len(COMMON)} requests show that adding the 4 most similar examples (B) "
    "significantly improves over zero-shot; the remaining pipelines are being run within the free API quota.")
thanks = [
    f"Chúng em xin chân thành cảm ơn {ADVISOR} đã định hướng đề tài, góp ý về phương pháp và theo dõi tiến độ "
    "của nhóm trong học phần Dự án Công nghệ Thông tin. Những câu hỏi của thầy/cô về dữ liệu và cách đánh giá đã "
    "giúp nhóm nhìn lại các giả định và làm phần thực nghiệm cẩn thận hơn.",
    "Chúng em cũng xin cảm ơn Khoa Công nghệ thông tin, Trường Đại học Tôn Đức Thắng đã tạo điều kiện về chương "
    "trình học và tài liệu, và cảm ơn các tác giả bộ dữ liệu SR-BH 2020 đã công bố dữ liệu với giấy phép mở.",
    "Đây là báo cáo giữa kỳ nên còn nhiều phần chưa hoàn thiện. Chúng em mong nhận được nhận xét và góp ý của "
    "thầy/cô để hoàn thiện đề tài ở giai đoạn cuối kỳ."]
for par in R.doc.paragraphs:
    text = par.text
    if text.startswith("PHÂN TÍCH ĐẶC ĐIỂM HÌNH THÁI"):
        set_text(par._p, TITLE)
    elif text.startswith("BÁO CÁO CUỐI KỲ MÔN"):
        set_text(par._p, "BÁO CÁO GIỮA KỲ MÔN DỰ ÁN CÔNG NGHỆ THÔNG TIN")
    elif text.strip() == "TS. Hồ Thị Linh":
        set_text(par._p, ADVISOR)
    elif text.strip() == "KHOA HỌC MÁY TÍNH":
        set_text(par._p, MAJOR)
        for run in par.runs:  # tên ngành dài hơn mẫu: giảm cỡ chữ để bìa vẫn nằm gọn trong một trang
            run.font.size = Pt(14)
    elif text.startswith("Chúng em xin chân thành cảm ơn"):
        set_text(par._p, thanks[0])
    elif text.startswith("Chúng em cũng xin cảm ơn Khoa"):
        set_text(par._p, thanks[1])
    elif text.startswith("Do kiến thức và thời gian còn hạn chế"):
        set_text(par._p, thanks[2])
    elif text.startswith("Chúng tôi xin cam đoan"):
        set_text(par._p, text.replace("TS. Hồ Thị Linh", ADVISOR))
    elif text.startswith("ANALYSIS OF ABALONE"):
        set_text(par._p, TITLE_EN)
    elif text.startswith("Báo cáo phân tích mối liên hệ"):
        set_text(par._p, summary)
    elif text.startswith("This report examines"):
        set_text(par._p, summary_en)

abbr = [("API", "Application Programming Interface, giao diện lập trình ứng dụng"),
        ("CAPEC", "Common Attack Pattern Enumeration and Classification, danh mục mẫu tấn công"),
        ("CI", "Confidence Interval, khoảng tin cậy"),
        ("FPR", "False Positive Rate, tỷ lệ báo động nhầm"),
        ("HTTP", "Hypertext Transfer Protocol"),
        ("ICL", "In-Context Learning, học trong ngữ cảnh"),
        ("kNN", "k-Nearest Neighbors, k láng giềng gần nhất"),
        ("LCR@k", "Label Consistency Rate at k, tỷ lệ ví dụ cùng nhãn trong top-k"),
        ("LLM", "Large Language Model, mô hình ngôn ngữ lớn"),
        ("RAG", "Retrieval-Augmented Generation, sinh văn bản có truy hồi"),
        ("RQ", "Research Question, câu hỏi nghiên cứu"),
        ("SQLi", "SQL Injection, chèn câu lệnh SQL"),
        ("WAF", "Web Application Firewall, tường lửa ứng dụng web")]
tbl = R.doc.tables[0]._tbl
row_tpl = copy.deepcopy(tbl.findall(qn("w:tr"))[0])
for tr in list(tbl.findall(qn("w:tr"))):
    tbl.remove(tr)
for short, full in abbr:
    tr = copy.deepcopy(row_tpl)
    cells = tr.findall(qn("w:tc"))
    set_text(cells[0], short)
    set_text(cells[1], full)
    tbl.append(tr)

APPENDIX = {"members": ("A", 1), "commands": ("B", 1)}


def table(key, caption, headers, rows, widths, size=11):
    result = R.table("tab:" + key, caption, headers, rows, widths, size=size)
    if key in APPENDIX:
        letter, number = APPENDIX[key]
        cap = result._tbl.getprevious()
        for child in list(cap):
            if child.tag != qn("w:pPr"):
                cap.remove(child)
        from docx.text.paragraph import Paragraph
        par = Paragraph(cap, R.doc)
        par.add_run(f"Bảng {letter}.")
        R._field(par, f" SEQ Bảng \\r {number} ", str(number))
        par.add_run(": " + caption)
    return result


def figure(key, path, caption, width=15.5):
    R.fig("fig:" + key, path, caption, width_cm=width)


def p(text, **kw):
    return R.p(text, **kw)


# ======================= CHƯƠNG 1 =======================
R.h1("MỞ ĐẦU", page_break=False)
R.h2("Đặt vấn đề")
p("Mỗi thao tác trên một website, từ tìm kiếm sản phẩm đến đăng nhập, tạo ra một HTTP request gửi đến máy chủ. "
  "Kẻ tấn công lợi dụng chính các request này để chèn câu lệnh SQL, đường dẫn truy cập file trái phép hay lệnh hệ "
  "điều hành. Vì vậy, đọc nội dung request là một cách phát hiện dấu hiệu tấn công web. Tường lửa ứng dụng web "
  "(WAF) truyền thống như ModSecurity dựa trên luật so khớp mẫu, hiệu quả nhưng phải được viết và bảo trì thủ công.")
p("Mô hình ngôn ngữ lớn (LLM) có thể đọc văn bản bán cấu trúc và phân loại theo hướng dẫn mà không cần huấn luyện "
  "lại, nhờ kỹ thuật học trong ngữ cảnh (In-Context Learning, ICL): đưa vào prompt một vài ví dụ đã có nhãn. Chất "
  "lượng dự đoán phụ thuộc mạnh vào các ví dụ này [1]. Cách phổ biến là chọn ví dụ giống request nhất theo "
  "embedding. Tuy nhiên, trong miền HTTP, hai request có thể giống gần như hoàn toàn mà mang nhãn khác nhau.")
p(f"<<fig:pair>> là một cặp request thật trong SR-BH 2020: giống hệt nhau về method, protocol, 11 header và body, "
  f"chỉ khác chuỗi [code]+AND+1%3D1[/code] trong tham số. Độ tương đồng ký tự của toàn request là "
  f"{pct(PAIR['request_text_similarity'], 2)}, nhưng một request mang nhãn Normal, request kia là SQL Injection. "
  "Nếu ví dụ giống nhất lại mang nhãn khác, LLM có thể bị dẫn sai. Đây là động cơ của đề tài.")
figure("pair", ROOT / "reports/surveys/figures/sr_bh_motivating_pair.png",
       "Cặp request Normal và SQL Injection gần giống hệt nhau trong SR-BH 2020", 15.5)
R.h2("Mục tiêu và câu hỏi nghiên cứu")
p("Đề tài kiểm chứng việc dùng thông tin nhãn khi chọn ví dụ có giúp LLM phân loại tốt hơn so với chỉ chọn theo "
  "độ tương đồng hay không. Nhóm đặt ba câu hỏi nghiên cứu (<<tab:rq>>) trước khi chạy thực nghiệm.")
table("rq", "Ba câu hỏi nghiên cứu và cách trả lời", ["Câu hỏi", "Cách trả lời", "Trạng thái"], [
    ["RQ1. Semantic retrieval thường xuyên lấy về ví dụ khác nhãn với request cần phân loại đến mức nào?",
     "Tỷ lệ top-1 khác nhãn, LCR@k; không cần LLM", "Đã có kết quả (Chương 6)"],
    ["RQ2. Label-aware reranking (C) có cải thiện Macro-F1 so với semantic retrieval (B) và đối chứng cân bằng "
     "lớp (BAL) không?", "So sánh trên cùng tập query, bootstrap và McNemar", "A0 xong; B, BAL có kết quả tạm; C đang chạy"],
    ["RQ3. C giúp hay gây hại trong trường hợp nào: prior đúng, prior sai, lớp ít mẫu?",
     "Bảng prior đúng/sai, C-oracle, F1 từng lớp", "Đã có phân tích sơ bộ trên retrieval"]],
      [7.5, 5.0, 3.0])
R.h2("Phạm vi và đóng góp dự kiến")
p("Đề tài dùng một bộ dữ liệu (SR-BH 2020) với sáu lớp đơn nhãn, đánh giá offline, không huấn luyện hay tinh "
  "chỉnh mô hình và không xây WAF chạy thời gian thực. Hệ thống chỉ phân loại dựa trên nội dung request, không "
  "xác minh tấn công có khai thác thành công hay không.")
p("Đóng góp dự kiến gồm ba phần. Thứ nhất, một pipeline chỉ suy luận có thể tái lập, so sánh công bằng năm cách "
  "chọn ví dụ trên cùng LLM, prompt và tập đánh giá. Thứ hai, số liệu định lượng về hiện tượng giống nhưng khác "
  "nhãn trong dữ liệu HTTP. Thứ ba, phân tích khi nào thông tin nhãn giúp hoặc gây hại, gồm cả mức trần khi biết "
  "nhãn thật (C-oracle). Ý tưởng dùng nhãn khi chọn ví dụ đã có trong xử lý ngôn ngữ tự nhiên [3]; nhóm không "
  "khẳng định đây là phương pháp đầu tiên.")
R.h2("Bố cục báo cáo")
p("Chương 2 trình bày cơ sở lý thuyết và các nghiên cứu liên quan. Chương 3 mô tả dữ liệu và tiền xử lý. Chương 4 "
  "trình bày phương pháp. Chương 5 mô tả cài đặt và kiểm thử. Chương 6 báo cáo kết quả giữa kỳ. Chương 7 tổng kết "
  "và nêu kế hoạch cuối kỳ.")

# ======================= CHƯƠNG 2 =======================
R.h1("CƠ SỞ LÝ THUYẾT VÀ NGHIÊN CỨU LIÊN QUAN")
R.h2("HTTP request và các loại tấn công trong phạm vi")
p("Một HTTP request gồm dòng yêu cầu (method, đường dẫn kèm tham số, phiên bản giao thức), các header và phần "
  "thân (body). Payload tấn công thường nằm trong tham số của URI hoặc trong body, đôi khi trong header như "
  "User-Agent. <<tab:classes>> tóm tắt sáu lớp đề tài phân loại, theo danh mục CAPEC mà bộ dữ liệu sử dụng.")
table("classes", "Sáu lớp trong phạm vi đề tài", ["Lớp (mã CAPEC)", "Dấu hiệu điển hình"], [
    ["Normal (000)", "Request bình thường, không có payload tấn công trong phạm vi"],
    ["SQL Injection (66)", "Chèn cú pháp SQL vào tham số, ví dụ AND 1=1, UNION SELECT, SLEEP()"],
    ["Path Traversal (126)", "Chuỗi ../ hoặc dạng mã hóa để truy cập file ngoài thư mục cho phép"],
    ["Code Injection (242)", "Chèn mã của ngôn ngữ phía máy chủ để thực thi, ví dụ print(chr(...))"],
    ["HTTP Response Splitting (34)", "Chèn ký tự CR/LF (%0d%0a) và header giả để tách phản hồi HTTP"],
    ["OS Command Injection (88)", "Chèn lệnh hệ điều hành, ví dụ ;cat /etc/passwd, Shellshock trong header"]],
      [5.0, 10.5])
R.h2("Mô hình ngôn ngữ lớn và học trong ngữ cảnh")
p("ICL cho LLM thực hiện nhiệm vụ bằng cách đưa vào prompt phần hướng dẫn và một số ví dụ có lời giải. Trọng số "
  "mô hình không thay đổi; các ví dụ chỉ có tác dụng trong lần gọi đó. Không có ví dụ gọi là zero-shot, có k ví dụ "
  "gọi là k-shot. Vì không cần huấn luyện, ICL phù hợp khi muốn thay đổi bộ ví dụ hoặc tập nhãn mà không xây lại "
  "mô hình, đổi lại mỗi lần phân loại tốn một lượt gọi LLM.")
R.h2("Embedding và tìm kiếm theo độ tương đồng")
p("Mô hình embedding biến mỗi đoạn văn bản thành một vector số sao cho văn bản giống nhau có vector gần nhau. Đề "
  "tài dùng all-MiniLM-L6-v2 thuộc họ Sentence-BERT [7], cho vector 384 chiều. Độ tương đồng giữa hai request là "
  "cosine của góc giữa hai vector; khi vector đã chuẩn hóa độ dài 1, cosine chính là tích vô hướng.")
R.eq("eq:cos", row(mi("sim"), mo("("), mi("q"), mo(","), mi("d"), mo(")"), mo("="),
                   mi("q"), mo("·"), mi("d"), mo(","), mo("&#x2003;"), mo("‖"), mi("q"), mo("‖"), mo("="),
                   mo("‖"), mi("d"), mo("‖"), mo("="), mn("1")))
p("Thuật toán k láng giềng gần nhất (kNN) dự đoán nhãn bằng cách lấy k ví dụ có độ tương đồng cao nhất và chọn "
  "nhãn chiếm ưu thế. Đề tài dùng kNN vừa làm đối chứng không dùng LLM, vừa làm nguồn prior rẻ cho phương pháp đề xuất.")
R.h2("Các nghiên cứu về chọn ví dụ cho ICL")
p("<<tab:related>> tóm tắt các công trình gần với đề tài. Điểm chung là ví dụ được chọn ảnh hưởng mạnh đến kết quả "
  "ICL; điểm khác của đề tài là miền dữ liệu HTTP, nơi các request rất giống nhau về hình thức.")
table("related", "Các nghiên cứu liên quan", ["Công trình", "Ý tưởng chính", "Liên hệ với đề tài"], [
    ["KATE [1]", "Chọn ví dụ gần nhất theo embedding thường tốt hơn chọn ngẫu nhiên", "Cơ sở của Pipeline B"],
    ["EPR [2]", "Huấn luyện bộ retriever để chọn ví dụ hữu ích", "Có huấn luyện; đề tài không dùng"],
    ["CLL-RetICL [3]", "Dùng thông tin ngữ nghĩa của nhãn khi truy hồi ví dụ cho phân loại văn bản",
     "Gần nhất về ý tưởng; đề tài dùng prior dự đoán thay cho embedding nhãn"],
    ["ICL with Noisy Labels [4]", "Ảnh hưởng của nhãn sai trong ví dụ đến ICL", "SR-BH có dấu hiệu nhãn nhiễu"],
    ["DemoShapley [5]", "Định giá đóng góp của từng ví dụ", "Hướng mở rộng, ngoài phạm vi"],
    ["CyberRAG [6]", "RAG kết hợp bộ phân loại để phân loại và báo cáo tấn công web",
     "Cùng miền; đề tài không huấn luyện bộ phân loại riêng"]],
      [3.3, 6.4, 5.8], 10.5)
R.h2("Chỉ số đánh giá và kiểm định")
p("Precision của một lớp là tỷ lệ request đoán đúng trong số request bị đoán là lớp đó; recall là tỷ lệ request "
  "của lớp được đoán ra; F1 là trung bình điều hòa của hai giá trị. Macro-F1 là trung bình F1 của sáu lớp với trọng "
  "số bằng nhau, nên lớp ít mẫu không bị lấn át; đây là chỉ số chính của đề tài. Tỷ lệ báo động nhầm (FPR) trên lớp "
  "Normal đo phần request bình thường bị báo là tấn công.")
p("LCR@k (Label Consistency Rate) là tỷ lệ ví dụ trong top-k cùng nhãn với request cần phân loại. Chỉ số này chỉ "
  "tính được khi đánh giá vì cần nhãn thật, và chỉ dùng để chẩn đoán: ví dụ cùng nhãn nhiều hơn chưa chắc giúp LLM "
  "đúng hơn. Để so sánh hai pipeline trên cùng tập request, đề tài dùng paired bootstrap 2.000 lần cho khoảng tin "
  "cậy 95% của chênh lệch Macro-F1 [8] và kiểm định McNemar trên các request mà hai pipeline đúng sai khác nhau [9].")

# ======================= CHƯƠNG 3 =======================
R.h1("DỮ LIỆU VÀ TIỀN XỬ LÝ")
R.h2("Nguồn dữ liệu")
p("Đề tài dùng bộ SR-BH 2020 multi-label trên Harvard Dataverse, phiên bản 1.2, giấy phép CC0 1.0 [10]. File "
  "data_capec_multilabel.csv dung lượng 436.437.661 byte, mã MD5 khớp với nguồn. Theo mô tả của tác giả, dữ liệu "
  "là traffic của một website WordPress trong 12 ngày tháng 7/2020, được ModSecurity ghi nhận và gán nhãn theo "
  "CAPEC, có xử lý thủ công hoặc bán tự động.")
raw = S["raw_class_counts"]
p(f"File gồm {n(C['total_rows'])} bản ghi và 38 cột: 5 cột metadata, 15 trường request, 4 trường response và 14 cột "
  f"nhãn (Normal và 13 lớp CAPEC). Dữ liệu mất cân bằng nặng: Normal có {n(raw['000 - Normal'])} bản ghi, SQL "
  f"Injection {n(raw['66 - SQL Injection'])}, trong khi lớp nhỏ nhất chỉ có {n(min(raw.values()))} bản ghi "
  "(<<fig:dist>>). Khoảng 97% bản ghi không có body.")
figure("dist", ROOT / "reports/surveys/figures/sr_bh_class_distribution.png",
       "Phân bố 14 nhãn gốc của SR-BH 2020 trên trục logarit", 14.5)
R.h2("Tiền xử lý")
p("Đầu vào của mô hình là chuỗi request_text: một JSON gồm method, URI, protocol, 11 header và body. Payload được "
  "giữ nguyên, không giải mã URL và không cắt bớt. Các bước lọc được trình bày ở <<tab:prep>>.")
table("prep", "Các bước tiền xử lý và số lượng", ["Bước", "Quy tắc", "Kết quả"], [
    ["Chọn lớp", "Bản ghi có đúng một nhãn trên 14 cột và thuộc sáu lớp", n(C["eligible_single_label"]) + " bản ghi"],
    ["Loại đa nhãn", "Bản ghi có từ hai nhãn trở lên", n(C["multi_label"]) + " bản ghi"],
    ["Cách ly mâu thuẫn", "Request trùng nội dung nhưng khác nhãn",
     f"{n(C['conflict_unique_requests'])} request ({n(C['conflict_rows'])} bản ghi)"],
    ["Bỏ trùng", "Trùng toàn bộ nội dung thì giữ một", n(C["duplicate_rows_removed"]) + " bản ghi bị bỏ"],
    ["Kết quả", "Request duy nhất còn lại", n(C["retained_unique_requests"]) + " request"]],
      [3.2, 8.3, 4.0])
R.h2("Chia tập và kiểm tra rò rỉ dữ liệu")
p("Nếu chia ngẫu nhiên theo dòng, các request cùng khuôn (chỉ khác số thứ tự hay mã phiên) sẽ rơi vào cả kho ví dụ "
  "lẫn tập kiểm tra, khiến kết quả đẹp giả tạo. Vì vậy, nhóm che các con số và chuỗi hex dài, băm phần còn lại để "
  f"gom request thành {n(S['split_groups']['pool'] + S['split_groups']['validation'] + S['split_groups']['test'] + S['split_groups']['development'])} "
  "nhóm, rồi chia theo nhóm với tỷ lệ xấp xỉ 70/15/15 và seed 42. Thực nghiệm dùng các tập con cân bằng lớp (<<tab:split>>).")
sd = S["subset_distribution"]
table("split", "Kích thước các tập và tập con dùng trong thực nghiệm",
      ["Tập", "Đầy đủ", "Tập con", "Vai trò"], [
          ["Pool", n(S["split_sizes"]["pool"]), f"{n(sum(sd['pool'].values()))} (500/lớp)", "Kho ví dụ có nhãn"],
          ["Development", n(S["split_sizes"]["development"]), "30 (5/lớp)", "Chạy thử, sửa lỗi"],
          ["Validation", n(S["split_sizes"]["validation"]), f"{n(sum(sd['validation'].values()))} (33–34/lớp)",
           "Chọn tham số k, λ, nguồn prior"],
          ["Test", n(S["split_sizes"]["test"]), f"{n(sum(sd['test'].values()))} (100/lớp)",
           "Chỉ chạy một lần sau khi khóa cấu hình"]],
      [2.8, 2.9, 3.6, 6.2])
ov = AUD["overlaps"]
p("Kiểm tra cho mọi cặp tập đều có [b]0[/b] request ID, 0 mã băm nội dung và 0 nhóm trùng nhau. Chạy lại toàn bộ "
  "tiền xử lý hai lần (một lần trên Linux, một lần trên Windows) cho cùng số lượng và cùng phân bố. Hạn chế còn lại "
  f"là có {n(AUD['endpoint_overlaps']['pool/test'])} endpoint (method và đường dẫn) xuất hiện ở cả pool và test, nên "
  "kết quả chưa đo khả năng tổng quát sang endpoint mới.")
R.h2("Chất lượng nhãn")
cnt = REV["counts"]
p("Đọc kỹ 60 request (10 mỗi lớp) từ development và pool cho thấy 5 trong 10 mẫu Normal chứa payload đáng nghi như "
  "[code]sleep(...)[/code], [code]cat /etc/passwd[/code] hay [code]<script>[/code]. Lượt đọc này do công cụ hỗ trợ "
  "thực hiện, chưa phải đánh giá độc lập của hai người, và mẫu quá nhỏ để ước lượng tỷ lệ nhãn sai toàn bộ dữ liệu. "
  "Hệ quả là điểm số tính trên nhãn gốc thể hiện mức đồng thuận với nhãn nguồn. Nhóm giữ nguyên nhãn gốc, không tự "
  "sửa nhãn, và sẽ cùng đọc lại độc lập 60 mẫu này ở giai đoạn sau.")

# ======================= CHƯƠNG 4 =======================
R.h1("PHƯƠNG PHÁP")
R.h2("Tổng quan hệ thống")
p("<<fig:pipeline>> mô tả luồng xử lý. Mọi pipeline dùng cùng LLM, cùng khung prompt, cùng pool và cùng số ví dụ "
  "k = 4; chỉ cách chọn ví dụ thay đổi. Nhờ vậy chênh lệch kết quả giữa các pipeline đến từ cách chọn ví dụ.")
figure("pipeline", WORD / "figures" / "pipeline.png", "Kiến trúc hệ thống và vị trí của prior trong Pipeline C", 15.5)
R.h2("Biểu diễn request cho embedding")
p("Trong request_text, các khóa JSON sắp theo thứ tự chữ cái nên 11 header đứng trước URI. Mô hình embedding chỉ đọc "
  "256 token đầu nên có thể cắt mất payload trong URI. Nhóm tạo một cách trình bày khác cho embedding: đặt method, "
  "URI, protocol và body lên đầu, các header không rỗng ở sau. Nội dung không bị sửa hay giải mã, chỉ đổi thứ tự.")
R.h2("Truy hồi ứng viên")
p(f"Mỗi request được mã hóa thành vector 384 chiều đã chuẩn hóa. Với mỗi query, hệ thống tính độ tương đồng với "
  f"{n(RM['pool_size'])} ví dụ trong pool bằng một phép nhân ma trận và giữ N = 30 ứng viên giống nhất. Khi hai ứng "
  "viên bằng điểm, ứng viên có mã nhỏ hơn đứng trước để kết quả luôn giống nhau giữa các lần chạy. Kết quả truy hồi "
  "chỉ chứa nhãn của ứng viên, không chứa nhãn của query.")
R.h2("Các chiến lược chọn ví dụ")
p("<<tab:pipes>> liệt kê các pipeline. Phương pháp đề xuất C xếp lại top-N theo công thức <<eq:score>>.")
table("pipes", "Các pipeline và cách chọn k ví dụ", ["Pipeline", "Cách chọn ví dụ", "Vai trò"], [
    ["kNN vote", "Không gọi LLM; đếm nhãn k láng giềng có trọng số theo độ tương đồng", "Đối chứng không LLM"],
    ["A0", "Không có ví dụ (zero-shot)", "Năng lực ban đầu; nguồn prior"],
    ["A1", "Một bộ 4 ví dụ cố định, chia đều theo lớp (seed 42)", "Few-shot không truy hồi (tùy chọn)"],
    ["B", "k ứng viên đầu của top-N", "Đối chứng truy hồi chính"],
    ["BAL", "Gom top-N theo lớp, lấy luân phiên mỗi lớp một ví dụ đến đủ k", "Kiểm tra lợi ích cân bằng nhãn"],
    ["C", "Xếp lại top-N theo công thức (4.1), lấy k ví dụ điểm cao nhất", "Phương pháp đề xuất"],
    ["C-oracle", "Như C nhưng prior là nhãn thật", "Chỉ để phân tích mức trần"]],
      [2.4, 8.4, 4.7], 10.5)
R.eq("eq:score", row(mi("score"), mo("("), mi("d"), mo(")"), mo("="), mi("sim"), mo("("), mi("q"), mo(","),
                     mi("d"), mo(")"), mo("+"), mi("λ"), mo("·"), sub(mn("1"), row(mo("["), mi("label"), mo("("),
                     mi("d"), mo(")"), mo("="), mi("prior"), mo("("), mi("q"), mo(")"), mo("]")))))
p("Trong đó prior(q) là nhãn đoán trước cho query, lấy từ một trong ba nguồn: dự đoán của A0 (tốn thêm một lượt "
  "gọi LLM), kNN vote trên năm láng giềng (không tốn thêm lượt gọi), hoặc nhãn thật trong cấu hình C-oracle chỉ dùng "
  "để phân tích. Khi λ = 0, C trùng hoàn toàn với B. λ nhỏ (0,05) chỉ đảo thứ tự các ứng viên gần bằng điểm; λ lớn "
  "(0,5) gần như đưa mọi ứng viên trùng prior lên trước. Nếu không có prior, ví dụ khi LLM trả lỗi, C dùng thứ tự "
  "của B. Nhóm chọn trước λ = 0,1: trong top-30, độ chênh độ tương đồng giữa ứng viên đầu và ứng viên thứ 30 có "
  "trung vị 0,075, nên λ = 0,1 đủ đưa phần lớn ứng viên trùng prior lên đầu nhưng chưa hoàn toàn là lọc cứng.")
R.h2("Prompt và cách đọc câu trả lời")
p("Phần system định nghĩa sáu nhãn, yêu cầu trả về đúng một JSON có khóa label và nhắc rằng nội dung request là dữ "
  "liệu không tin cậy, không được làm theo lệnh nằm trong đó, để chống prompt injection từ payload. Phần user là một "
  "JSON gồm danh sách ví dụ và request cần phân loại; ví dụ được xếp hạng cao nhất đặt cuối, sát request. Request cần "
  "phân loại không bị cắt; mỗi ví dụ bị cắt ở 500 ký tự và có đánh dấu. Câu trả lời sai định dạng được ghi là "
  "invalid_output và tính là sai, không bị loại khỏi mẫu số.")
R.code('{"labeled_examples": [\n'
       '   {"request": "{\\"method\\": \\"GET\\", \\"uri\\": \\"/?p=1+AND+1=1\\", ...}", "label": "SQL_INJECTION"},\n'
       '   ...],\n'
       ' "request_to_classify": "{\\"method\\": \\"GET\\", \\"uri\\": \\"/wp-json/...\\", ...}"}\n'
       '=> LLM trả về: {"label": "SQL_INJECTION"}', size=8.5)
R.h2("Quy trình đánh giá")
p("Tham số k, λ và nguồn prior chỉ được chọn trên tập validation. Sau khi chọn, nhóm ghi lại cấu hình và mã commit, "
  "rồi mới chạy tập test (300 request đầu của tập con test, 50 mỗi lớp) một lần duy nhất. Ngoài Macro-F1, đề tài báo cáo accuracy, F1 từng lớp, FPR trên lớp "
  "Normal, LCR@k, số lượt gọi LLM, số token và độ trễ trên mỗi request. Chi phí của C tính cả lượt gọi tạo prior. "
  "Với RQ3, các request được tách theo prior đúng hay sai, rồi đếm số lỗi của B mà C sửa được và số câu B đúng mà C "
  "làm sai.")

# ======================= CHƯƠNG 5 =======================
R.h1("CÀI ĐẶT VÀ KIỂM THỬ")
R.h2("Cấu trúc mã nguồn")
p("Mã nguồn viết bằng Python, chia thành các module nhỏ có chú thích tiếng Việt (<<tab:modules>>).")
table("modules", "Các module chính", ["Module", "Chức năng"], [
    ["src/preprocessing/", "Tiền xử lý, chia tập, kiểm tra rò rỉ, khảo sát dữ liệu"],
    ["src/retrieval/views.py, embedding.py, index.py", "Cách trình bày request, embedding, tìm top-N"],
    ["src/retrieval/knn.py, selectors.py", "kNN vote; các chiến lược A1, B, BAL, C"],
    ["src/experiments/build_retrieval.py", "Dựng vector pool và top-N cho mỗi query"],
    ["src/experiments/eval_retrieval.py", "Đánh giá RQ1, kNN, LCR@k (không cần LLM)"],
    ["src/experiments/prompting.py, run_llm.py", "Prompt, gọi LLM, lưu kết quả, chạy tiếp khi gián đoạn"],
    ["src/analysis/metrics.py, compare.py", "Chỉ số, bootstrap, McNemar, bảng và hình so sánh"]],
      [7.0, 8.5], 10.5)
p("Môi trường: Python 3.11.9 trên Windows 11, CPU 8 nhân; numpy, sentence-transformers 5.1.0. LLM gọi qua API tương "
  "thích OpenAI (Groq, mô hình openai/gpt-oss-20b, temperature 0, reasoning_effort low); khóa API đặt trong file .env, không đưa "
  f"vào mã nguồn hay cấu hình. Mã hóa {n(RM['pool_size'])} request của pool mất khoảng "
  f"{v(RM['timings']['pool_encode_seconds'] / 60, 1)} phút trên CPU.")
R.h2("Kiểm thử")
p("Bộ kiểm thử gồm 55 bài, đều đạt trên Windows 11, trong đó có kiểm thử từ đầu đến cuối cho mọi pipeline bằng một "
  "LLM giả (trả về nhãn chiếm đa số trong các ví dụ). <<tab:tests>> nêu các tính chất quan trọng được kiểm tra.")
table("tests", "Các tính chất được kiểm thử tự động", ["Tính chất", "Ý nghĩa"], [
    ["Nhãn và metadata của query không lọt vào prompt", "Không rò rỉ đáp án sang LLM"],
    ["Ví dụ luôn lấy từ pool, không phải từ tập đánh giá", "Không dùng chính query làm ví dụ"],
    ["λ = 0 cho kết quả trùng B; thiếu prior thì C dùng thứ tự của B", "Công thức C cài đặt đúng"],
    ["Tập test bị khóa nếu không có cờ --allow-test", "Không vô tình dùng test để chỉnh tham số"],
    ["Đổi cấu hình, dữ liệu hoặc mã thì phải dùng thư mục mới", "Kết quả luôn khớp với cấu hình"],
    ["Lỗi API được ghi lại và tính là sai", "Không âm thầm loại các dự đoán thất bại"],
    ["Chạy lại cùng lệnh thì tiếp tục từ chỗ dừng", "Không mất kết quả khi mất mạng hoặc hết quota"]],
      [8.5, 7.0], 10.5)
R.h2("Các sự cố đã xử lý")
table("issues", "Sự cố kỹ thuật và cách xử lý", ["Sự cố", "Nguyên nhân", "Cách xử lý"], [
    ["API Groq trả HTTP 403",
     "Cloudflare chặn User-Agent mặc định Python-urllib (error code 1010). Đã kiểm chứng: không có khóa, UA mặc "
     "định nhận 403, UA tùy chỉnh nhận 401", "Thêm header User-Agent riêng"],
    ["Không chạy được trên Windows", "Dùng fcntl chỉ có trên Linux; file SQLite tạm chưa đóng khi lỗi; đọc file "
     "không chỉ định UTF-8", "Khóa thư mục đa nền tảng (msvcrt), đóng file trước khi dọn, thêm encoding UTF-8"],
    ["Giới hạn quota API miễn phí", "Khoảng 8.000 token/phút và 200.000 token/ngày cho mỗi khóa",
     "Tự chờ theo retry-after; hết quota thì dừng gọn và chạy tiếp sau; từ 20/10 dùng một tài khoản gói trả theo mức dùng, có chốt ngân sách"]],
      [3.5, 7.5, 4.5], 10.5)

# ======================= CHƯƠNG 6 =======================
R.h1("KẾT QUẢ GIỮA KỲ")
p("Mục 6.1 đến 6.3 không cần LLM; Mục 6.4 là kết quả LLM zero-shot (A0); Mục 6.5 là kết quả tạm của B và BAL. Tất cả tính trên 200 request của tập "
  "validation, với pool 3.000 ví dụ, N = 30, k = 4, λ = 0,1. Mọi số liệu được đọc từ các file kết quả trong thư mục "
  "src/artifacts của repository (danh sách lệnh ở Phụ lục B).")
R.h2("RQ1: ví dụ giống nhất có khác nhãn không")
mm = EV["rq1_top1_mismatch_by_class"]
p(f"Có [b]{pct(EV['rq1_top1_mismatch_rate'])}[/b] request mà ví dụ giống nhất trong pool mang nhãn khác, dù độ tương "
  f"đồng trung bình của ví dụ đó rất cao ({v(EV['mean_top1_similarity'])}). Hiện tượng tập trung ở lớp Normal "
  f"({pct(mm['NORMAL'])}) và SQL Injection ({pct(mm['SQL_INJECTION'])}), là hai lớp có payload ngắn chèn vào URI "
  f"bình thường; các lớp có dấu hiệu rõ như OS Command Injection chỉ {pct(mm['OS_COMMAND_INJECTION'])} "
  "(<<fig:overview>>a). Kết quả xác nhận động cơ của đề tài: với gần một phần tư request, semantic retrieval đưa "
  "cho LLM ví dụ gần nhất mang nhãn khác.")
figure("overview", RET / "eval_validation" / "retrieval_overview.png",
       "(a) Tỷ lệ top-1 khác nhãn theo lớp; (b) LCR@4 theo lớp của các chiến lược chọn ví dụ", 15.5)
R.h2("Đối chứng kNN không dùng LLM")
p("<<tab:knn>> cho thấy kNN vote đạt Macro-F1 khoảng 0,80 và ổn định khi k từ 3 đến 10. Như vậy bài toán không tầm "
  "thường với phương pháp chỉ dựa trên độ tương đồng, và LLM có dư địa để cải thiện. Điểm yếu lớn nhất là FPR trên "
  f"lớp Normal: khoảng {pct(KNN['k=5']['normal_fpr'], 0)} request Normal bị đoán là tấn công. Ma trận nhầm lẫn "
  "(<<fig:knncm>>) cho thấy Normal và SQL Injection hay bị nhầm sang OS Command Injection và HTTP Response "
  "Splitting, phù hợp với việc các payload kiểu sleep hay ký tự xuống dòng xuất hiện ở nhiều lớp.")
table("knn", "Kết quả kNN vote trên validation (200 request)", ["k", "Macro-F1", "Accuracy", "FPR Normal"],
      [[kk[2:], v(m["macro_f1"]), v(m["accuracy"]), pct(m["normal_fpr"])] for kk, m in KNN.items()],
      [2.5, 4.0, 4.0, 4.0])
figure("knncm", RET / "eval_validation" / "confusion_knn.png", "Ma trận nhầm lẫn của kNN vote (k = 5) trên validation", 12)
p("Trên tập development (30 request), Macro-F1 của kNN với k = 5 là "
  f"{v(EVD['knn_vote']['k=5']['macro_f1'])}, nhưng tỷ lệ top-1 khác nhãn chỉ {pct(EVD['rq1_top1_mismatch_rate'])}, "
  "thấp hơn nhiều so với validation. Với 30 request (5 mỗi lớp), mỗi request chiếm hơn 3 điểm phần trăm, nên con số "
  "trên development dao động lớn và chỉ dùng để chạy thử; kết luận giữa kỳ dựa trên validation.")
R.h2("Ảnh hưởng của prior lên các ví dụ được chọn")
p(f"<<tab:lcr>> so sánh LCR@4 của bốn cách chọn ví dụ, với λ = 0,1. Prior kNN đúng {pct(EV['knn_prior_accuracy'])} "
  "số request.")
names = {"B_semantic": "B (semantic top-k)", "BAL_class_balanced": "BAL (cân bằng lớp)",
         "C_knn_prior": "C, prior kNN", "C_oracle_prior (analysis only)": "C-oracle (chỉ phân tích)"}
table("lcr", "LCR@4 của các chiến lược chọn ví dụ trên validation",
      ["Chiến lược", "LCR@4 trung bình", "Request không có ví dụ cùng nhãn"],
      [[names[k], v(x["mean"]), pct(x["zero_match_rate"])] for k, x in LCR.items()], [6.0, 4.5, 5.0])
p(f"Ba nhận xét. Thứ nhất, xếp lại theo prior kNN nâng LCR từ {v(b_lcr)} lên {v(c_lcr)}, và mức trần khi biết nhãn "
  f"thật là {v(o_lcr)}, cho thấy pool thường có ví dụ đúng lớp trong top-30 nhưng không nằm ở đầu danh sách. Thứ "
  f"hai, cái giá của C là khi prior sai: tỷ lệ request không còn ví dụ đúng lớp nào tăng từ "
  f"{pct(LCR['B_semantic']['zero_match_rate'])} ở B lên {pct(LCR['C_knn_prior']['zero_match_rate'])} ở C. Đây là "
  "rủi ro tự xác nhận mà RQ3 cần đo bằng LLM thật: với những request này, LLM chỉ thấy ví dụ của lớp sai. Thứ ba, "
  f"BAL có LCR thấp nhất ({v(LCR['BAL_class_balanced']['mean'])}) nhưng không request nào thiếu ví dụ đúng lớp, nên "
  "là đối chứng quan trọng để tách lợi ích của việc có đủ các lớp khỏi lợi ích của việc có nhiều ví dụ cùng lớp.")
SWEEP = EV["lambda_sweep_knn_prior"]
p("Để chọn λ mà không tốn lượt gọi LLM, nhóm quét λ trên chính phần truy hồi (<<tab:sweep>>). λ càng lớn thì tỷ lệ "
  "ví dụ cùng nhãn càng cao, nhưng số request mất hết ví dụ đúng lớp cũng tăng; từ λ = 0,25 trở lên kết quả không "
  "đổi vì mọi ứng viên trùng prior đã được đưa lên đầu. Giá trị λ = 0,1 nằm giữa hai thái cực này.")
table("sweep", "Quét λ cho C với prior kNN (k = 4, validation)",
      ["λ", "LCR@4 trung bình", "Request không có ví dụ cùng nhãn"],
      [[v(float(lam), 2), v(x["lcr_mean"]), pct(x["zero_match_rate"])] for lam, x in SWEEP.items()], [3.0, 5.0, 6.0])
R.h2("Kết quả LLM zero-shot (A0)")
a0pc = A0M["per_class"]
p(f"A0 dùng openai/gpt-oss-20b qua Groq, không có ví dụ trong prompt. Cả 200 request đều nhận được câu trả lời hợp lệ "
  f"(coverage {pct(A0M['coverage'], 0)}), trung bình {n(A0M['cost']['mean_total_tokens'])} token và "
  f"{v(A0M['cost']['mean_latency_seconds'], 1)} giây mỗi request. <<tab:a0>> so sánh A0 với kNN vote trên cùng 200 "
  "request.")
table("a0", "So sánh LLM zero-shot (A0) với kNN vote (k = 5) trên validation", ["Lớp", "F1 của A0", "F1 của kNN"],
      [[SHORT[l], v(a0pc[l]["f1"], 2), v(KNN["k=5"]["per_class_f1"][l], 2)] for l in LABELS]
      + [["[b]Macro-F1[/b]", f"[b]{v(A0M['macro_f1'])}[/b]", v(KNN["k=5"]["macro_f1"])],
         ["FPR Normal", pct(A0M["normal_false_positive_rate"]), pct(KNN["k=5"]["normal_fpr"])]], [6.5, 4.0, 4.0])
plot_confusion(A0M, "A0 zero-shot (gpt-oss-20b) trên validation", WORD / "figures" / "confusion_a0.png")
significant = BOOT["ci95"][0] > 0
p(f"A0 cao hơn kNN {v(BOOT['observed_diff'])} điểm Macro-F1, với khoảng tin cậy 95% bootstrap "
  f"[{v(BOOT['ci95'][0])}; {v(BOOT['ci95'][1])}] và p McNemar = {v(MCN['p_value'])} "
  f"({MCN['a_only_correct']} request chỉ A0 đúng, {MCN['b_only_correct']} request chỉ kNN đúng). Vì khoảng tin cậy "
  + ("không chứa 0, chênh lệch này có ý nghĩa thống kê" if significant
     else "vẫn chứa 0, chênh lệch này chưa đủ để khẳng định LLM tốt hơn kNN")
  + " với 200 request. Điểm mạnh rõ nhất của A0 là lớp Normal: FPR giảm từ "
  + f"{pct(KNN['k=5']['normal_fpr'])} xuống {pct(A0M['normal_false_positive_rate'])}. Ngược lại, A0 hay đoán nhầm "
  "sang OS Command Injection: ma trận nhầm lẫn (<<fig:a0cm>>) cho thấy nhiều request Normal, SQL Injection và HTTP "
  "Response Splitting bị đoán thành lớp này, có thể do các payload kiểu sleep hay ký tự xuống dòng mà định nghĩa nhãn "
  "trong prompt chưa phân biệt rõ. Đây là chỗ các ví dụ trong prompt (B, BAL, C) có thể giúp.")
figure("a0cm", WORD / "figures" / "confusion_a0.png", "Ma trận nhầm lẫn của A0 trên validation", 12)
R.h2("Kết quả tạm của B và BAL")
_m = {n: classification_metrics(YC, pr, ALL_LABELS) for n, pr in IPRED.items()}


def _lcr(name):
    if name == "A0":
        return "–"
    vals = [label_consistency_rate(INTERIM[name][q]["demo_labels"], VAL[q]) for q in COMMON]
    return v(sum(vals) / len(vals))


p(f"Đến thời điểm viết báo cáo, B đã chạy {len(INTERIM['B_k4'])}/200 và BAL {len(INTERIM['BAL_k4'])}/200 request "
  f"validation (dừng do hết quota trong ngày). <<tab:interim>> so sánh A0, B và BAL trên đúng {len(COMMON)} request mà "
  "cả ba đã chạy, mỗi lớp 24–25 request. Đây là [b]kết quả tạm[/b]: con số sẽ thay đổi khi các run chạy đủ 200 request. "
  f"Lưu ý A0 trên tập con này đạt {v(_m['A0']['macro_f1'])}, khác với {v(A0M['macro_f1'])} trên đủ 200 request, nên "
  "chỉ so sánh các pipeline trên cùng một tập.")
_names = {"A0": "A0 (zero-shot)", "B_k4": "B (top-4)", "BAL_k4": "BAL (cân bằng lớp)"}
table("interim", f"Kết quả tạm trên {len(COMMON)} request validation chung", ["Chỉ số", *[_names[n] for n in IPRED]],
      [[SHORT[l], *[v(_m[n]["per_class"][l]["f1"], 2) for n in IPRED]] for l in LABELS]
      + [["[b]Macro-F1[/b]", *[f"[b]{v(_m[n]['macro_f1'])}[/b]" for n in IPRED]],
         ["FPR Normal", *[pct(_m[n]["normal_false_positive_rate"]) for n in IPRED]],
         ["LCR@4", *[_lcr(n) for n in IPRED]]], [5.5, 3.3, 3.3, 3.4], 10.5)
_pairs = [("B_k4", "A0"), ("BAL_k4", "A0"), ("BAL_k4", "B_k4")]
_rows = []
_stats = {}
for a, b in _pairs:
    bt = paired_bootstrap(YC, IPRED[a], IPRED[b], ALL_LABELS)
    mc = mcnemar(YC, IPRED[a], IPRED[b])
    _stats[(a, b)] = (bt, mc)
    _rows.append([f"{_names[a]} so với {_names[b]}", ("+" if bt["observed_diff"] >= 0 else "") + v(bt["observed_diff"]),
                  f"[{v(bt['ci95'][0])}; {v(bt['ci95'][1])}]", f"{mc['a_only_correct']} / {mc['b_only_correct']}",
                  v(mc["p_value"])])
table("interimdiff", "Chênh lệch Macro-F1 từng cặp (kết quả tạm)",
      ["So sánh", "Chênh lệch", "CI 95% bootstrap", "Chỉ bên trái đúng / chỉ bên phải đúng", "p McNemar"],
      _rows, [4.6, 2.2, 3.4, 3.3, 2.0], 10)
_bA = _stats[("B_k4", "A0")][0]
# Nhận xét bên dưới dựa trên các con số này; nếu kết quả đổi, script dừng để viết lại nhận xét.
assert all(_m["B_k4"]["per_class"][l]["f1"] - _m["A0"]["per_class"][l]["f1"] > 0.05
           for l in ("PATH_TRAVERSAL", "HTTP_RESPONSE_SPLITTING", "OS_COMMAND_INJECTION"))
assert _m["B_k4"]["normal_false_positive_rate"] > _m["A0"]["normal_false_positive_rate"]
assert _stats[("BAL_k4", "B_k4")][0]["observed_diff"] < 0
_sig = _bA["ci95"][0] > 0
p(f"Kết quả tạm có ba điểm. Thứ nhất, B cao hơn A0 {v(_bA['observed_diff'])} điểm Macro-F1"
  + (", và khoảng tin cậy không chứa 0: đưa 4 ví dụ giống nhất vào prompt giúp LLM phân loại tốt hơn zero-shot một "
     "cách có ý nghĩa thống kê." if _sig else "; khoảng tin cậy còn chứa 0 nên chưa kết luận được.")
  + " Cải thiện rõ nhất ở Path Traversal, HTTP Response Splitting và OS Command Injection, là các lớp A0 hay nhầm. "
  f"Thứ hai, BAL thấp hơn B {v(-_stats[('BAL_k4', 'B_k4')][0]['observed_diff'])} điểm nhưng chênh lệch chưa có ý nghĩa "
  "thống kê; việc ép đủ các lớp trong ví dụ (LCR thấp hơn nhiều) chưa cho thấy lợi ích. Thứ ba, ví dụ mẫu làm tăng "
  f"báo động nhầm trên lớp Normal (FPR từ {pct(_m['A0']['normal_false_positive_rate'])} ở A0 lên "
  f"{pct(_m['B_k4']['normal_false_positive_rate'])} ở B), phù hợp với RQ1: hàng xóm gần nhất của request Normal "
  "thường là request tấn công. Đây chính là chỗ Pipeline C được thiết kế để cải thiện; kết quả của C sẽ có ở cuối kỳ.")
R.h2("Giới hạn quota và điều chỉnh quy mô thí nghiệm")
p("Khi chạy thật, nhóm đo được giới hạn của gói Groq miễn phí cho gpt-oss-20b: khoảng 8.000 token mỗi phút và "
  "200.000 token mỗi ngày cho mỗi khóa API. Với 6 ví dụ cắt ở 1.500 ký tự, mỗi request có ví dụ tốn khoảng 2.600 "
  "token, nên một pipeline trên 200 request validation cần hơn hai ngày quota. Nhóm dừng lần chạy thử B với cấu hình "
  "này sau 34 request và không dùng kết quả đó. Để vừa quota mà vẫn giữ đủ các đối chứng chính, nhóm điều chỉnh "
  "trước khi chạy các pipeline có ví dụ:")
R.bullets(["k = 4 ví dụ, mỗi ví dụ cắt ở 500 ký tự: khoảng 1.300 token mỗi request (A0 không bị ảnh hưởng vì không "
           "có ví dụ).",
           "Chỉ chạy bộ chính A0, B, BAL, C prior kNN, C prior LLM với λ = 0,1 cố định; ảnh hưởng của λ được phân "
           "tích bằng bảng quét λ ở Mục 6.3; C-oracle và A1 chạy thêm sau bộ chính.",
           "Tập test dùng 300 request đầu của tập con test (50 mỗi lớp), cố định trước khi xem kết quả."])
p("Để hoàn thành đúng hạn và tuân thủ điều khoản sử dụng của Groq (không dùng nhiều tài khoản để vượt giới hạn), từ "
  "20/10 nhóm chạy phần còn lại bằng một tài khoản gói trả theo mức dùng, với chốt ngân sách trong code để tổng chi "
  "phí không vượt 5 USD. Cấu hình thí nghiệm giữ nguyên như trên, nên các run đã chạy trên gói miễn phí vẫn so sánh "
  "được với các run sau. Phần còn lại cần khoảng 3,3 triệu token, chi phí ước tính dưới 1 USD.")

# ======================= CHƯƠNG 7 =======================
R.h1("KẾT LUẬN GIỮA KỲ VÀ KẾ HOẠCH")
R.h2("Kết quả đạt được")
R.bullets([
    f"Xử lý xong SR-BH 2020: {n(C['retained_unique_requests'])} request duy nhất, chia tập theo nhóm, không rò rỉ giữa "
    "các tập, tái lập được trên Linux và Windows.",
    "Cài đặt toàn bộ hệ thống: truy hồi, kNN, năm chiến lược chọn ví dụ, chạy LLM có khả năng chạy tiếp, so sánh "
    "có kiểm định; 55 bài kiểm thử tự động đều đạt.",
    f"Trả lời RQ1 bằng số liệu thật: {pct(EV['rq1_top1_mismatch_rate'])} request có ví dụ giống nhất mang nhãn khác.",
    f"Có đối chứng kNN (Macro-F1 {v(KNN['k=5']['macro_f1'])}) và kết quả LLM zero-shot thật (Macro-F1 "
    f"{v(A0M['macro_f1'])}), cùng bằng chứng sơ bộ cho cả lợi ích lẫn rủi ro của C.",
    f"Kết quả tạm trên {len(COMMON)} request: B (top-4) tốt hơn A0 có ý nghĩa thống kê; BAL chưa hơn B."])
R.h2("Hạn chế")
R.bullets([
    "Chỉ một bộ dữ liệu, là traffic của một website WordPress trong 12 ngày.",
    "Nhãn có dấu hiệu nhiễu; điểm số đo mức đồng thuận với nhãn nguồn.",
    "Có endpoint chung giữa pool và tập đánh giá; chưa đo khả năng tổng quát sang endpoint mới.",
    "Tập con cân bằng lớp, không phản ánh tỷ lệ traffic thật; tập validation chỉ 200 request.",
    "Mỗi request tốn một đến hai lượt gọi LLM, chỉ phù hợp phân tích log offline.",
    "B và BAL mới có kết quả tạm, C chưa có kết quả; quy mô thí nghiệm (k = 4, test 300 request) được chốt khi còn "
    "dùng gói API miễn phí."])
R.h2("Kế hoạch giai đoạn cuối kỳ")
table("plan", "Kế hoạch đến khi nộp báo cáo cuối kỳ", ["Thời gian", "Công việc"], [
    ["20–21/10", "Chạy nốt B, BAL và chạy C prior kNN, C prior LLM, C-oracle, A1 trên validation"],
    ["22–25/10", "Hai thành viên đọc lại độc lập các mẫu nhãn và các request Normal bị đoán sai"],
    ["26–27/10", "So sánh, bootstrap, McNemar, bảng prior đúng/sai trên validation"],
    ["28/10", "Khóa cấu hình (ghi commit, config, model)"],
    ["29–31/10", "Chạy tập test 300 request một lần cho bộ chính"],
    ["01–08/11", "Phân tích lỗi theo lớp, prior sai, nhãn nhiễu"],
    ["09–14/11", "Hoàn thiện báo cáo cuối kỳ, kiểm tra tái lập, nộp"]], [3.0, 12.5])
p("Phần còn lại cần khoảng 3,3 triệu token (validation và test), chạy bằng một tài khoản gói trả theo mức dùng. Nếu C "
  "không tốt hơn B, đó vẫn là kết quả có giá trị: nhóm sẽ dùng bảng prior đúng/sai, bảng quét λ và "
  "C-oracle (nếu có) để giải thích nguyên nhân.")

# ======================= TÀI LIỆU THAM KHẢO =======================
R.h1("TÀI LIỆU THAM KHẢO", numbered=False)
refs = [
    "[1] Liu, J., Shen, D., Zhang, Y., Dolan, B., Carin, L., và Chen, W. (2022). What Makes Good In-Context Examples "
    "for GPT-3? Proceedings of DeeLIO 2022: Deep Learning Inside Out, 100–114.",
    "[2] Rubin, O., Herzig, J., và Berant, J. (2022). Learning To Retrieve Prompts for In-Context Learning. "
    "Proceedings of NAACL 2022, 2655–2671.",
    "[3] Lin et al. (2025). CLL-RetICL: Contrastive Linguistic Label Retrieval-based In-Context Learning for Text "
    "Classification via Large Language Models. Findings of IJCNLP 2025. (Cần đối chiếu số trang trước bản cuối.)",
    "[4] In-Context Learning with Noisy Labels (2024). arXiv:2411.19581.",
    "[5] DemoShapley: Valuation of Demonstrations for In-Context Learning (2024). arXiv:2410.07523.",
    "[6] Blefari, F. et al. (2025). CyberRAG: An Agentic RAG Cyber Attack Classification and Reporting Tool. "
    "arXiv:2507.02424.",
    "[7] Reimers, N., và Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. "
    "Proceedings of EMNLP-IJCNLP 2019, 3982–3992.",
    "[8] Efron, B., và Tibshirani, R. J. (1993). An Introduction to the Bootstrap. Chapman & Hall.",
    "[9] McNemar, Q. (1947). Note on the sampling error of the difference between correlated proportions or "
    "percentages. Psychometrika, 12(2), 153–157.",
    "[10] SR-BH 2020 multi-label dataset, phiên bản 1.2 [Bộ dữ liệu]. Harvard Dataverse. "
    "https://doi.org/10.7910/DVN/OGOIXX. Giấy phép CC0 1.0."]
for text in refs:
    par = R.p(text, indent=False)
    par.paragraph_format.left_indent = Pt(36)
    par.paragraph_format.first_line_indent = Pt(-36)
    par.paragraph_format.space_after = Pt(6)
    par.alignment = 0
    par.paragraph_format.keep_together = True

# ======================= PHỤ LỤC =======================
R.h1("PHỤ LỤC A. PHÂN CÔNG CÔNG VIỆC", numbered=False)
p("Nhóm điền thông tin đúng với phần việc thực tế trước khi nộp. Tổng tỷ lệ đóng góp cần bằng 100%.", indent=False)
table("members", "Phân công và mức độ hoàn thành",
      ["Họ tên", "MSSV", "Nội dung thực hiện", "Đóng góp %", "Hoàn thành %"],
      [["", "", "Dữ liệu, truy hồi, kNN, reranker C", "", ""],
       ["", "", "API LLM, chạy pipeline, chỉ số, thống kê", "", ""]], [3.5, 2.5, 5, 2.25, 2.25], 11)
R.h1("PHỤ LỤC B. LỆNH TÁI LẬP", numbered=False)
p("Chạy từ thư mục gốc của repository. Hướng dẫn đầy đủ nằm ở reports/protocol/huong_dan_doc_va_chay_code.md.",
  indent=False)
R.code("pip install -r src/requirements-experiments.txt\n"
       "python -m unittest discover -s src/tests\n"
       "python -m src.preprocessing.prepare --config src/configs/data.json\n"
       "python -m src.experiments.build_retrieval --output src/artifacts/retrieval/minilm\n"
       "python -m src.experiments.eval_retrieval --retrieval src/artifacts/retrieval/minilm --split validation\n"
       "bash src/experiments/run_suite.sh validation   # A0, B, BAL, C; khóa API trong .env\n"
       "python -m src.experiments.run_llm --config src/configs/experiments/B_k4.json \\\n"
       "    --llm src/configs/llm/groq.json --env-file .env --split validation \\\n"
       "    --output src/artifacts/runs/validation/B_k4\n"
       "python -m src.analysis.compare --split validation --reference B_semantic_k4 --runs \"src/artifacts/runs/validation/*\" \\\n"
       "    --output src/artifacts/reports/validation", size=8)

missing = R.resolve_refs()
assert not missing, missing
settings = R.doc.settings.element
update = settings.find(qn("w:updateFields"))
if update is None:
    update = OxmlElement("w:updateFields")
    settings.append(update)
update.set(qn("w:val"), "true")
OUT_DOC.parent.mkdir(exist_ok=True)
R.doc.core_properties.author = "Nhóm đề tài Label-Aware Retrieval"
R.doc.core_properties.title = TITLE
R.doc.save(OUT_DOC)
print("Saved", OUT_DOC, "figures", len([k for k in R.refs if k.startswith("fig:")]),
      "tables", len([k for k in R.refs if k.startswith("tab:")]))
