"""Dựng báo cáo CUỐI KỲ trên nền bản Word giữa kỳ (bản nhóm đã chỉnh tay).

    python reports/word/build_bao_cao_cuoi_ky.py
    python reports/word/export_word.py reports/final/Bao_cao_cuoi_ky_LabelAware.docx   # cập nhật mục lục + PDF

Giữ nguyên bìa, lời cảm ơn, cam đoan, Chương 1–2 của bản giữa kỳ. Thay tóm tắt/abstract,
bổ sung Chương 3 (công trình liên quan, C-gated), viết mới Chương 4 (toàn bộ thực nghiệm),
Chương 5 (kết luận) và danh mục tài liệu tham khảo. Mọi con số lấy từ src/artifacts/.
"""
import copy
from pathlib import Path

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from report_lib import Report, set_text

ROOT = Path(__file__).resolve().parents[2]
WORD = ROOT / "reports/word"
BASE = WORD / "tpl" / "giua_ky_ban_sua.docx"
OUT = ROOT / "reports" / "final" / "Bao_cao_cuoi_ky_LabelAware.docx"
FIG = WORD / "figures"
ART = ROOT / "src/artifacts"


class FinalReport(Report):
    """Chú thích theo đúng kiểu của bản Word nhóm ("Hình 4.1. ...") và thêm ô "Nói ngắn gọn"."""

    def caption(self, kind, key, text, keep=False):
        self.count[kind] += 1
        self.refs[key] = f"{kind} {self.chapter}.{self.count[kind]}"
        par = self.doc.add_paragraph(style="Caption")
        par.paragraph_format.keep_with_next = keep
        par.add_run(f"{kind} ")
        self._field(par, " STYLEREF 1 \\s ", str(self.chapter))
        par.add_run(".")
        self._field(par, f" SEQ {kind} \\* ARABIC \\s 1 ", str(self.count[kind]))
        par.add_run(". " + text)
        return par

    def box(self, text, title="Nói ngắn gọn"):
        """Ô nền nhạt tóm tắt ý chính cho người đọc không chuyên."""
        table = self.doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        self._borders(table, color="9DC3E6")
        table.autofit = False
        tblpr = table._tbl.tblPr
        for tag, attrs in (("w:tblW", {"w:w": "8788", "w:type": "dxa"}), ("w:tblLayout", {"w:type": "fixed"})):
            el = tblpr.find(qn(tag))
            if el is None:
                el = OxmlElement(tag); tblpr.append(el)
            for k, v in attrs.items():
                el.set(qn(k), v)
        for col in table._tbl.tblGrid.findall(qn("w:gridCol")):
            col.set(qn("w:w"), "8788")
        cell = table.cell(0, 0)
        cell.width = Cm(15.5)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "EAF2FA")
        cell._tc.get_or_add_tcPr().append(shd)
        par = cell.paragraphs[0]
        par.style = self.doc.styles["Normal"]
        fmt = par.paragraph_format
        fmt.space_before = Pt(4); fmt.space_after = Pt(4); fmt.line_spacing = 1.15
        self.runs(par, f"[b]{title}:[/b] {text}", size=12)
        self.gap()

    def page_break(self):
        par = self.doc.add_paragraph(style="Nội dung văn bản")
        run = par.add_run()
        br = OxmlElement("w:br"); br.set(qn("w:type"), "page")
        run._r.append(br)


def text_of(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def find(body, start_text, after=0):
    for i, el in enumerate(body):
        if i >= after and el.tag == qn("w:p") and text_of(el).strip().startswith(start_text):
            return i
    raise KeyError(start_text)


def move_new_after(rep, anchor, build):
    """Gọi build() (thêm phần tử vào cuối thân văn bản) rồi chuyển các phần tử mới tới sau `anchor`."""
    before = len(rep.children())
    build()
    new = rep.children()[before - 1:-1]  # phần tử cuối là sectPr
    for el in reversed(new):
        anchor.addnext(el)
    return new[-1] if new else anchor


def add_row(table_el, values):
    rows = table_el.findall(qn("w:tr"))
    new = copy.deepcopy(rows[-1])
    for tc, value in zip(new.findall(qn("w:tc")), values):
        set_text(tc, value)
    rows[-1].addnext(new)
    return new


def insert_row_after(table_el, first_cell_prefix, values):
    for tr in table_el.findall(qn("w:tr")):
        if text_of(tr.findall(qn("w:tc"))[0]).strip().startswith(first_cell_prefix):
            new = copy.deepcopy(tr)
            for tc, value in zip(new.findall(qn("w:tc")), values):
                set_text(tc, value)
            tr.addnext(new)
            return new
    raise KeyError(first_cell_prefix)


rep = FinalReport(BASE)
body = rep.children()

# ---------------------------------------------------------------------------
# 1. Phần đầu: ngày ký, tóm tắt, abstract, chữ viết tắt
# ---------------------------------------------------------------------------
for el in body:
    if el.tag == qn("w:p") and "ngày 20 tháng 10 năm 2026" in text_of(el):
        set_text(el, text_of(el).replace("ngày 20 tháng 10 năm 2026", "ngày 14 tháng 11 năm 2026"))

TOM_TAT = [
    "Mỗi ngày, máy chủ web nhận rất nhiều yêu cầu HTTP; một số trong đó chứa mã tấn công. Mô hình ngôn ngữ lớn (LLM) "
    "có thể đọc một yêu cầu và cho biết nó bình thường hay thuộc loại tấn công nào, chỉ cần đưa cho nó vài ví dụ mẫu có "
    "đáp án ngay trong câu lệnh (học trong ngữ cảnh, ICL), không cần huấn luyện lại. Câu hỏi của đề tài là: chọn ví dụ "
    "mẫu như thế nào thì LLM phân loại đúng nhất, và việc ưu tiên ví dụ có nhãn trùng với một dự đoán sơ bộ có giúp ích không.",
    "Trên bộ dữ liệu SR-BH 2020 (sáu lớp, 466.267 yêu cầu sau xử lý), nhóm so sánh có đối chứng 15 cách chọn ví dụ với "
    "cùng một LLM (gpt-oss-20b, kiểm tra thêm gpt-oss-120b), trên bốn tập đánh giá độc lập. Cấu hình được khóa và lưu "
    "trên GitHub trước mỗi lần chạy tập test. Kết quả: chọn bốn ví dụ giống yêu cầu nhất (B) tốt hơn hẳn không dùng ví dụ "
    "và dùng ví dụ cố định (gộp 600 yêu cầu: hơn 0,058 và 0,052 Macro-F1, p < 0,001). Ưu tiên ví dụ theo nhãn dự đoán "
    "(C) cho kết quả ngang B khi nhãn dự đoán lấy từ kNN hay LLM (gộp 900 yêu cầu), nhưng hơn B có ý nghĩa khi nhãn dự "
    "đoán luôn đúng (+0,026, p = 0,004). Sáu cách chọn ví dụ đã công bố (MMR, CLL-RetICL, ENN, IDS, bỏ phiếu) không vượt "
    "B sau hiệu chỉnh Holm.",
    "Đóng góp của đề tài: (1) bằng chứng rằng ví dụ phải giống yêu cầu mới có ích, kèm số đo hiện tượng “giống nhưng khác "
    "nhãn” (khoảng 24% yêu cầu); (2) chỉ ra nút thắt của cách chọn ví dụ theo nhãn là chất lượng nhãn dự đoán, bổ sung "
    "bằng chứng cho tranh luận về vai trò của nhãn trong ICL; (3) một quy trình đánh giá tái lập được, có đo độ dao động "
    "của chính LLM (khoảng 0,01 Macro-F1 giữa hai lần chạy cùng câu lệnh). Toàn bộ chi phí API khoảng 1,5 USD.",
]
ABSTRACT = [
    "Web servers receive large volumes of HTTP requests, some of which carry attack payloads. A large language model (LLM) "
    "can label a request as normal or as a specific attack type when a few labelled examples are placed in its prompt "
    "(in-context learning), without any training. This project asks how those examples should be chosen, and whether "
    "preferring examples whose label matches a preliminary prediction helps.",
    "On the SR-BH 2020 dataset (six classes, 466,267 requests after preprocessing) we run a controlled comparison of 15 "
    "selection strategies with the same LLM (gpt-oss-20b, checked with gpt-oss-120b) on four independent evaluation sets, "
    "locking every configuration on GitHub before touching test data. Choosing the four most similar examples (B) clearly "
    "beats zero-shot and fixed examples (pooled n = 600: +0.058 and +0.052 macro-F1, p < 0.001). Label-aware reranking "
    "with a kNN or LLM prior is on par with B (pooled n = 900), yet with an always-correct prior it beats B significantly "
    "(+0.026, p = 0.004). Six published selection methods (MMR, CLL-RetICL, ENN, IDS-style iteration, voting) do not beat "
    "B after Holm correction.",
    "Contributions: evidence that demonstrations must resemble the query, with a measured rate of similar-but-differently-"
    "labelled neighbours (about 24%); evidence that the bottleneck of label-aware selection is prior quality; and a "
    "reproducible evaluation protocol that also measures the LLM's own run-to-run variation (about 0.01 macro-F1). Total "
    "API cost was about 1.5 USD.",
]
for heading, paragraphs in (("TÓM TẮT", TOM_TAT), ("ABSTRACT", ABSTRACT)):
    i = find(body, heading)
    targets = [el for el in body[i + 1:i + 6] if el.tag == qn("w:p") and text_of(el).strip()][:3]
    for el, text in zip(targets, paragraphs):
        set_text(el, text)

abbr = next(el for el in body if el.tag == qn("w:tbl") and "Application Programming Interface" in text_of(el))
insert_row_after(abbr, "CI", ["ENN", "Edited Nearest Neighbor, lọc ví dụ sai nhãn"])
insert_row_after(abbr, "LLM", ["MMR", "Maximal Marginal Relevance"])

# ---------------------------------------------------------------------------
# 2. Chương 3: thêm công trình liên quan, hàng trong bảng 3.1 và 3.2, mô tả C-gated
# ---------------------------------------------------------------------------
body = rep.children()
i_xie = find(body, "Xie và cộng sự (2025) đề xuất DemoShapley")


def related_extra():
    rep.p("Gần nhất với Pipeline C là hướng dùng chính dự đoán của LLM cho yêu cầu cần phân loại để chọn ví dụ. "
          "Gao và cộng sự (2023) đề xuất ICL nhận biết sự mơ hồ: LLM đưa ra các nhãn ứng viên cho đầu vào, rồi hệ thống "
          "chọn ví dụ quanh ranh giới giữa các nhãn đó. MarginSel (Ambati và cộng sự, 2025) cũng dùng nhãn dự đoán "
          "zero-shot để chọn ví dụ khó, cùng nhãn ứng viên. Như vậy ý tưởng “đoán trước nhãn rồi chọn ví dụ theo nhãn” "
          "không phải do nhóm nghĩ ra đầu tiên; đóng góp của đề tài là kiểm chứng nó có đối chứng trong miền yêu cầu "
          "HTTP, nơi các công trình trên chưa thử.")
    rep.p("Vai trò của nhãn trong ví dụ vẫn đang được tranh luận. Min và cộng sự (2022) thấy thay nhãn đúng bằng nhãn "
          "ngẫu nhiên gần như không làm giảm kết quả; Yoo và cộng sự (2022) phản bác rằng nhãn đúng vẫn quan trọng khi "
          "đo kỹ hơn. Kết quả “nhãn dự đoán chỉ có lợi khi đủ chính xác” ở Chương 4 là một bằng chứng bổ sung cho tranh "
          "luận này.")
    rep.p("Cuối cùng, nhiều nghiên cứu cho thấy LLM gọi qua API không hoàn toàn tất định dù đặt temperature = 0: cùng "
          "một câu lệnh có thể cho câu trả lời khác nhau giữa các lần gọi (Ouyang và cộng sự, 2025; Atil và cộng sự, 2024). "
          "Vì vậy đề tài đo độ dao động này trực tiếp (mục 4.7) trước khi diễn giải các chênh lệch nhỏ.")


move_new_after(rep, body[i_xie], related_extra)
body = rep.children()
t31 = next(el for el in body if el.tag == qn("w:tbl") and "DemoShapley" in text_of(el))
add_row(t31, ["Ambiguity-aware ICL (Gao và cộng sự, 2023); MarginSel (Ambati và cộng sự, 2025)",
              "Dùng nhãn LLM dự đoán cho đầu vào để chọn ví dụ",
              "Gần nhất với C; đề tài kiểm chứng trong miền HTTP."])
add_row(t31, ["Min và cộng sự (2022); Yoo và cộng sự (2022)", "Vai trò của nhãn trong ví dụ",
              "Bằng chứng trái chiều; đề tài bổ sung bằng chứng có kiểm định."])
add_row(t31, ["Ouyang và cộng sự (2025); Atil và cộng sự (2024)", "LLM không tất định ở temperature 0",
              "Cơ sở để đo độ dao động khi chạy lại."])

t32 = next(el for el in body if el.tag == qn("w:tbl") and "C-oracle" in text_of(el) and "kNN (k = 5)" in text_of(el))
insert_row_after(t32, "C-LLM", ["C-gated", "Như C-kNN nhưng chỉ xếp hạng lại khi ít nhất 70% phiếu kNN cùng một nhãn; "
                                "ngược lại chọn như B.", "1"])
i_oracle = find(body, "C-oracle dùng nhãn nguồn")


def gated_text():
    rep.p("Sau giữa kỳ, nhóm bổ sung [b]C-gated[/b]. Phân tích giữa kỳ cho thấy C chủ yếu làm hỏng những câu mà nhãn dự "
          "đoán sai, và nhãn dự đoán của kNN hay sai đúng ở những yêu cầu mà các láng giềng bất đồng với nhau. C-gated "
          "vì vậy chỉ cộng điểm theo nhãn khi kNN đủ tự tin (tỷ lệ phiếu của nhãn thắng ≥ 0,7), còn lại chọn ví dụ như "
          "B. Ý tưởng “chỉ quyết định khi đủ chắc chắn” mượn từ phân loại có lựa chọn (Geifman & El-Yaniv, 2017). "
          "Ngưỡng 0,7 được chọn trên validation và khóa trước khi chạy test.")


move_new_after(rep, body[i_oracle], gated_text)

# ---------------------------------------------------------------------------
# 3. Xóa Chương 4 cũ trở đi, viết lại Chương 4, 5 và tài liệu tham khảo
# ---------------------------------------------------------------------------
body = rep.children()
i_ch4 = find(body, "THỰC NGHIỆM")
start = i_ch4 - 1 if text_of(body[i_ch4 - 1]).strip() == "" else i_ch4
for el in body[start:-1]:
    if el.find(".//" + qn("w:sectPr")) is not None:
        raise RuntimeError("unexpected section break inside chapter 4+")
    rep.body.remove(el)
rep.chapter = 3

from chapter4 import write_chapter4  # noqa: E402
from chapter5 import write_chapter5, write_references  # noqa: E402

write_chapter4(rep, FIG, ART)
write_chapter5(rep)
write_references(rep)

missing = rep.resolve_refs()
if missing:
    raise RuntimeError(f"unresolved references: {missing}")
OUT.parent.mkdir(parents=True, exist_ok=True)
rep.doc.save(OUT)
print("Saved", OUT)
