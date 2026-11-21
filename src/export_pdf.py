"""Update the contents, figure and table lists in Word and export report/Phase2_Report.pdf (Word via pywin32).

The PDF is tagged (image alt text is carried over for screen readers) and has bookmarks for every heading.
Note: driving Word from PowerShell left the PowerShell host spinning and the export stalled on this machine;
pywin32 waits without spinning and the full export takes seconds.

  python src/export_pdf.py
"""
import os
import time

import pythoncom
import win32com.client

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCX = os.path.join(ROOT, "report", "Phase2_Report.docx")
PDF = os.path.join(ROOT, "report", "Phase2_Report.pdf")


def word():
    pythoncom.CoInitialize()
    w = win32com.client.DispatchEx("Word.Application")  # a new, separate instance (never the user's open Word)
    w.Visible = False
    w.DisplayAlerts = 0
    return w


def main():
    t0 = time.time()
    w = word()
    try:
        d = w.Documents.Open(DOCX, False, False, False)
        for i in range(1, d.TablesOfContents.Count + 1):
            d.TablesOfContents(i).Update()
        d.Repaginate()
        for i in range(1, d.TablesOfContents.Count + 1):
            d.TablesOfContents(i).UpdatePageNumbers()
        d.Save()
        pages = d.ComputeStatistics(2)
        # PDF, no viewer, optimise for print, whole document, content only, document properties, keep IRM,
        # bookmarks from headings, structure tags (alt text), bitmap missing fonts, not PDF/A
        d.ExportAsFixedFormat(PDF, 17, False, 0, 0, 1, 1, 0, True, True, 1, True, True, False)
        d.Close(0)
    finally:
        w.Quit()
    print(f"lists updated and {PDF} exported ({pages} pages, {time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
