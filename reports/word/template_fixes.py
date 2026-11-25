"""Chỉnh các điểm lệch so với mẫu của Khoa CNTT (TemplateCacMonDuAnVaThucTap_KhoaCNTT.dotx).

- Trích dẫn dùng "et al." như mẫu: "(Vaswani et al., 2023)", không dùng "và cộng sự".
- Chú thích hình/bảng dùng dấu hai chấm ("Hình 2.1: ..."), nguồn của hình nằm ở dòng riêng "(Nguồn: ...)".
Chạy một lần sau khi toàn bộ nội dung đã được dựng.
"""
import copy
import re

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


def _paragraphs(doc):
    return [Paragraph(el, doc._body) for el in doc.element.body.iter(qn("w:p"))]


def _runs_text(par):
    return "".join(r.text for r in par.runs)


def _edit(par, start, end, new):
    """Thay đoạn [start, end) của văn bản ghép từ các run, giữ định dạng của run đầu tiên bị chạm tới."""
    pos, first = 0, True
    for run in par.runs:
        t = run.text
        rs, re_ = pos, pos + len(t)
        pos = re_
        if re_ <= start or rs >= end:
            continue
        a, b = max(start, rs) - rs, min(end, re_) - rs
        run.text = t[:a] + (new if first else "") + t[b:]
        first = False


def use_et_al(doc):
    """"Liu và cộng sự (2022)" -> "Liu et al. (2022)". Trả về số chỗ đã đổi."""
    count = 0
    for par in _paragraphs(doc):
        text = _runs_text(par)
        for m in reversed(list(re.finditer(r" và cộng sự", text))):
            _edit(par, m.start(), m.end(), " et al.")
            count += 1
    return count


def fix_captions(doc):
    """Đổi ". " sau số thứ tự chú thích thành ": " và tách "Nguồn: ..." thành dòng riêng dưới chú thích."""
    changed = split = 0
    for par in _paragraphs(doc):
        if par.style.name != "Caption":
            continue
        for run in par.runs:
            if run.text.startswith(". "):
                run.text = ": " + run.text[2:]
                changed += 1
                break
        text = _runs_text(par)
        m = re.search(r"\.? ?Nguồn: (.+)$", text)
        if m and text.lstrip().startswith(("Hình", "Bảng")):
            source = m.group(1).rstrip(".")
            # Giữ phần trước "Nguồn:" trong chú thích (kết thúc không có dấu chấm thừa).
            _edit(par, m.start(), len(text), "")
            new_p = copy.deepcopy(par._p)
            for child in list(new_p):
                if child.tag != qn("w:pPr"):
                    new_p.remove(child)
            par.paragraph_format.keep_with_next = True
            par._p.addnext(new_p)
            src = Paragraph(new_p, par._parent)
            src.style = doc.styles["Normal"]
            src.alignment = WD_ALIGN_PARAGRAPH.CENTER
            src.add_run(f"(Nguồn: {source})")
            split += 1
    return changed, split
