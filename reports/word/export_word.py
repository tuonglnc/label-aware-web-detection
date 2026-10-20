"""Mở báo cáo trong một phiên Word riêng, cập nhật mục lục và số trang, rồi xuất PDF.

Dùng: python export_word.py duong_dan.docx   (cần pywin32 và Microsoft Word)
"""
import sys
import time
from pathlib import Path
import pythoncom
import win32com.client

source = Path(sys.argv[1]).resolve()
pdf = source.with_suffix('.pdf')
pythoncom.CoInitialize()
app = win32com.client.DispatchEx('Word.Application')
app.Visible = False
app.DisplayAlerts = 0
doc = None
try:
    doc = app.Documents.Open(str(source), ReadOnly=False, AddToRecentFiles=False)
    time.sleep(1)
    doc.Fields.Update()
    for coll in (doc.TablesOfContents, doc.TablesOfFigures):
        for i in range(1, coll.Count + 1):
            coll.Item(i).Update()
    doc.Fields.Update()
    # Word có thể gán kiểu của tiêu đề cho đoạn cuối của mục lục; đặt lại cho đúng.
    for i in range(1, doc.TablesOfContents.Count + 1):
        paras = doc.TablesOfContents.Item(i).Range.Paragraphs
        last, prev = paras.Item(paras.Count), paras.Item(paras.Count - 1)
        last.Range.Style = prev.Range.Style
        last.Format.PageBreakBefore = False
        last.Format.KeepWithNext = False
    doc.Repaginate()
    for coll in (doc.TablesOfContents, doc.TablesOfFigures):
        for i in range(1, coll.Count + 1):
            coll.Item(i).UpdatePageNumbers()
    doc.Save()
    doc.ExportAsFixedFormat(str(pdf), 17)
    print('pages', doc.ComputeStatistics(2), 'pdf', pdf)
finally:
    if doc is not None:
        doc.Close(0)
    app.Quit()
