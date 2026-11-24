"""Chuyển trích dẫn "(Tác giả, năm)" trong báo cáo sang kiểu đánh số [n] theo thứ tự xuất hiện lần đầu.

Kiểu này giống báo cáo mẫu (Baocao.docx): trong bài ghi "[3]", danh mục tham khảo xếp theo số thứ tự.
Chạy một lần sau khi toàn bộ nội dung đã được dựng và trước khi viết danh mục tham khảo.
"""
import re

from docx.oxml.ns import qn

LB = "⟦"  # dấu tạm đánh dấu một tài liệu chưa có số
RB = "⟧"
NAME_TAIL = r"(?: (?:&|và) [A-ZÀ-Ỹ][\w\-’']+)?(?: và cộng sự)?"


def ref_key(text):
    """Họ tác giả đầu (hoặc tên tổ chức) và năm của một mục trong danh sách tham khảo."""
    m = re.search(r"\((\d{4}[ab]?|n\.d\.)\)", text)
    surname = text[:m.start()].split(",")[0].strip().rstrip(".")
    return surname, m.group(1)


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


def _substitute(par, pattern, repl):
    text = _runs_text(par)
    for m in reversed(list(re.finditer(pattern, text))):
        _edit(par, m.start(), m.end(), repl(m))


def convert_citations(doc, references):
    """Đổi toàn bộ trích dẫn trong `doc` sang [n]. Trả về (thứ tự, chưa dùng, còn sót).

    thứ tự: danh sách chỉ số mục trong `references`, theo lần xuất hiện đầu tiên; chưa dùng: các mục không được trích.
    """
    keys = [ref_key(t) for t in references]
    # Mọi đoạn văn theo đúng thứ tự xuất hiện trong tài liệu (thân văn bản, gồm cả ô bảng).
    from docx.text.paragraph import Paragraph
    paragraphs = [Paragraph(el, doc._body) for el in doc.element.body.iter(qn("w:p"))]

    for i, (surname, year) in enumerate(keys):
        name = r"(?<![\w])" + re.escape(surname) + NAME_TAIL
        yr = re.escape(year)
        token = f"{LB}{i}{RB}"
        for par in paragraphs:
            # Dạng kể: "Liu và cộng sự (2022)" -> "Liu và cộng sự ⟦i⟧"
            _substitute(par, name + r" \(" + yr + r"\)",
                        lambda m, t=token: m.group(0).rsplit(" (", 1)[0].replace(" & ", " và ") + " " + t)
            # Dạng trong ngoặc: "Liu và cộng sự, 2022" -> "⟦i⟧"
            _substitute(par, name + r", " + yr, lambda m, t=token: t)

    # "(⟦1⟧; ⟦2⟧)" -> "⟦1⟧, ⟦2⟧"
    group = r"\(" + LB + r"\d+" + RB + r"(?:; " + LB + r"\d+" + RB + r")*\)"
    for par in paragraphs:
        _substitute(par, group, lambda m: m.group(0)[1:-1].replace("; ", ", "))

    order = []
    for par in paragraphs:
        for m in re.finditer(LB + r"(\d+)" + RB, _runs_text(par)):
            i = int(m.group(1))
            if i not in order:
                order.append(i)
    number = {i: n for n, i in enumerate(order, 1)}
    for par in paragraphs:
        _substitute(par, LB + r"(\d+)" + RB, lambda m: f"[{number[int(m.group(1))]}]")

    unused = [i for i in range(len(references)) if i not in number]
    leftover = []
    for par in paragraphs:
        text = _runs_text(par)
        for m in re.finditer(r"\((?:[^()]*?, )?(?:19|20)\d\d[ab]?\)|[A-Z][\w]+ và cộng sự(?! \[)", text):
            leftover.append(m.group(0))
    return order, unused, leftover


def format_reference(text):
    """Dạng hiển thị một mục tham khảo: "và" trước tác giả cuối, năm không còn hậu tố a/b."""
    m = re.search(r"\((\d{4}[ab]?|n\.d\.)\)", text)
    authors, rest = text[:m.start()], text[m.start():]
    authors = authors.replace(", & ", ", và ").replace(" & ", " và ")
    rest = re.sub(r"^\((\d{4})[ab]\)", r"(\1)", rest)
    return authors + rest
