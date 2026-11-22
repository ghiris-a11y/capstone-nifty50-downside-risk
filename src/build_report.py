"""P9: assemble report/Phase2_Report.docx from report/chapters/*.md (Phase 1 look: Times New Roman, centred bold cover with
the ITM logo, contents, lists of figures and tables, numbered captions, page numbers bottom right).

Markup in the chapter files
  # / ## / ###             headings (H1 = chapter, new page)
  {{key}}                  number from src/report_numbers.py (value and source in outputs/tables/report/report_numbers.csv)
  {{fig:id}} {{tab:id}}    cross-references, replaced by "Figure 5.3" / "Table 5.2"
  [[FIG:id|path|caption|source|alt text]]
  [[TABLE:key|id]]         table built from outputs by report_numbers.build()
  [[MDTABLE:id|caption|source]] followed by a pipe table
  [[MEANS]] text           "What this means" paragraph
  [[IMG:path|width_cm|alt]]                      unnumbered image (e.g. the QR code)
  [[PHONES:id|p1|p2|p3|caption|source|alt]]      three phone screenshots side by side (one numbered figure)
  [[LANDSCAPE]] / [[PORTRAIT]]                   section break to landscape / back to portrait A4 (page numbers continue)
  [[SHOWS]] text           one-line "What this shows" under a screenshot
  [text](https://...)      clickable hyperlink; bare https:// links are made clickable too
  - item / 1. item         lists;  **bold**, *italic*
Captions: the lists of figures and tables show a short caption (first sentence, at most 12 words); the full caption is
printed under the figure or above the table.

QA (written to report/qa_phase2.md): unresolved placeholders, figures or tables never referenced in the text, missing
image files, [FILL]/[UNVERIFIED] left in printed text, and literal numbers in Chapters 5-7 that do not come from a placeholder.

  python src/build_report.py      ->  report/Phase2_Report.docx (+ report/qa_phase2.md, report/build_registry.json)
"""
import glob
import json
import os
import re
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from report_numbers import GARCH, ML, build  # noqa: E402

CH = os.path.join(ROOT, "report", "chapters")
OUT = os.path.join(ROOT, "report", "Phase2_Report.docx")
FONT = "Times New Roman"
MAX_W, MAX_H = 15.5, 11.0  # cm (figures at most 11 cm high so text can flow on the same page)
TEXT_W = {"portrait": 16.0, "landscape": 24.7}  # cm of text width
TABLE_PT = 9.5
FONT_FILES = {False: "C:/Windows/Fonts/times.ttf", True: "C:/Windows/Fonts/timesbd.ttf"}
COVER = dict(title="Comparative Predictive Analytics of Downside Risk in NSE Nifty 50 Stocks: Machine Learning vs. GARCH Models "
                   "Using Secondary Historical and Macroeconomic Data",
             guide="Dr. Aarti Pardeshi", designation="HoD BTech", student="Ghiri S", roll="021331025144", program="MBA",
             spec="MBA Business Analytics", batch="2025-27", semester="III")


# ------------------------------------------------------------------ docx helpers
def set_font(run, size=12, bold=None, italic=None, color=None):
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def add_field(par, instr, placeholder="Right-click and choose Update Field"):
    r = par.add_run()
    for tag, attr in (("w:fldChar", {"w:fldCharType": "begin"}), ("w:instrText", None), ("w:fldChar", {"w:fldCharType": "separate"})):
        el = OxmlElement(tag)
        if attr:
            for k, v in attr.items():
                el.set(qn(k), v)
        else:
            el.set(qn("xml:space"), "preserve")
            el.text = instr
        r._r.append(el)
    t = par.add_run(placeholder)
    set_font(t, 11, italic=True)
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    par.add_run()._r.append(end)


def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hex_fill)
    tcPr.append(sh)


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    h = OxmlElement("w:tblHeader"); h.set(qn("w:val"), "true"); trPr.append(h)


def keep_next(par):
    par.paragraph_format.keep_with_next = True


def hyperlink(par, url, text, size=12):
    """Clickable external link (blue, underlined)."""
    r_id = par.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), r_id)
    r = OxmlElement("w:r"); rPr = OxmlElement("w:rPr")
    for tag, val in (("w:rFonts", None), ("w:color", "0563C1"), ("w:u", "single"), ("w:sz", str(int(size * 2)))):
        e = OxmlElement(tag)
        if tag == "w:rFonts":
            for a in ("w:ascii", "w:hAnsi", "w:eastAsia"):
                e.set(qn(a), FONT)
        else:
            e.set(qn("w:val"), val)
        rPr.append(e)
    r.append(rPr)
    tx = OxmlElement("w:t"); tx.text = text; tx.set(qn("xml:space"), "preserve"); r.append(tx)
    h.append(r); par._p.append(h)


LINK = re.compile(r"(\[[^\]]+\]\(https?://[^)\s]+\)|https?://[^\s)]+[^\s).,;:])")


def inline(par, text, size=12, base_bold=False, color=None):
    """Write text with **bold**, *italic* and links into a paragraph."""
    for chunk in LINK.split(text):
        if not chunk:
            continue
        m = re.match(r"\[([^\]]+)\]\((https?://[^)\s]+)\)$", chunk)
        if m:
            hyperlink(par, m.group(2), m.group(1), size); continue
        if re.match(r"https?://", chunk):
            hyperlink(par, chunk, chunk, size); continue
        _inline(par, chunk, size, base_bold, color)


def _inline(par, text, size=12, base_bold=False, color=None):
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not part:
            continue
        if part.startswith("**"):
            set_font(par.add_run(part[2:-2]), size, bold=True, color=color)
        elif part.startswith("*") and len(part) > 2:
            set_font(par.add_run(part[1:-1]), size, italic=True, bold=base_bold, color=color)
        else:
            set_font(par.add_run(part), size, bold=base_bold, color=color)


def styles(doc):
    st = doc.styles
    st["Normal"].font.name = FONT
    st["Normal"].font.size = Pt(12)
    st["Normal"].element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    pf = st["Normal"].paragraph_format
    pf.space_after = Pt(6); pf.line_spacing = 1.15
    for name, size in (("Heading 1", 16), ("Heading 2", 13.5), ("Heading 3", 12)):
        s = st[name]
        s.font.name = FONT; s.font.size = Pt(size); s.font.bold = True; s.font.color.rgb = RGBColor(0, 0, 0)
        s.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        s.element.rPr.rFonts.set(qn("w:ascii"), FONT); s.element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
        for att in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            s.element.rPr.rFonts.attrib.pop(qn(att), None)
        s.paragraph_format.space_before = Pt(12 if name != "Heading 1" else 0); s.paragraph_format.space_after = Pt(6 if name != "Heading 1" else 12)
        s.paragraph_format.keep_with_next = True
    for name in ("Figure Caption", "Table Caption"):
        s = st.add_style(name, 1)
        s.base_style = st["Normal"]; s.font.size = Pt(11); s.font.bold = False
        s.paragraph_format.space_before = Pt(4); s.paragraph_format.space_after = Pt(2)


def page_number_footer(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_field(p, "PAGE", "1")


# ------------------------------------------------------------------ cover and front matter
def cover(doc):
    def line(text, size, bold=True, space=6):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(space)
        set_font(p.add_run(text), size, bold=bold)
        return p
    line("Capstone Project 2025-27", 16, space=4)
    line("Phase 2 Report", 16, space=4)
    line(f"Semester – {COVER['semester']}", 14, space=24)
    line(COVER["title"], 18, space=24)
    logo = os.path.join(ROOT, "report", "template", "itm_logo.png")
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if os.path.exists(logo):
        p.add_run().add_picture(logo, width=Cm(4.5))
        alt(doc.inline_shapes[-1], "ITM Skills University logo")
    line("Submitted by:", 13, space=8)
    rows = [("Name of Faculty Guide:", COVER["guide"], "Name of the Student:", COVER["student"]),
            ("Designation:", COVER["designation"], "Roll No.:", COVER["roll"]),
            ("", "", "Program:", COVER["program"]),
            ("", "", "Specialisation:", COVER["spec"]),
            ("", "", "Batch:", COVER["batch"]),
            ("", "", "Semester:", COVER["semester"])]
    t = doc.add_table(rows=len(rows), cols=4); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            c = t.cell(i, j); c.width = Cm([4.2, 4.0, 4.2, 4.0][j])
            par = c.paragraphs[0]; par.paragraph_format.space_after = Pt(2)
            set_font(par.add_run(v), 12, bold=j in (0, 2))
    doc.add_paragraph()
    line("ITM Skills University · ITM Business School", 13, space=2)
    line("Plot No. 25/26, Institutional Area, Sector-4, Kharghar, Navi Mumbai", 12, bold=False, space=2)


def front(doc):
    for title, instr in (("TABLE OF CONTENTS", 'TOC \\o "1-2" \\h \\z \\u'),
                         ("LIST OF FIGURES", 'TOC \\h \\z \\t "Figure Caption,1"'),
                         ("LIST OF TABLES", 'TOC \\h \\z \\t "Table Caption,1"')):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(p.add_run(title), 14, bold=True)
        add_field(doc.add_paragraph(), instr)
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def alt(shape, text):
    docPr = shape._inline.docPr
    docPr.set("descr", text); docPr.set("title", text[:120])


# ------------------------------------------------------------------ chapter parsing
def chapters():
    return sorted(f for f in glob.glob(os.path.join(CH, "[0-9][0-9]_*.md")))


def register(files):
    """First pass: number figures and tables per chapter, in order of appearance."""
    reg = {}
    for f in files:
        ch = int(os.path.basename(f)[:2])
        nf = nt = 0
        for line in open(f, encoding="utf-8"):
            m = re.match(r"\[\[(FIG|TABLE|MDTABLE|PHONES):([^|\]]+)\|?([^|\]]*)", line.strip())
            if not m:
                continue
            kind, a, b = m.groups()
            if kind in ("FIG", "PHONES"):
                nf += 1; reg[("fig", a)] = f"Figure {ch}.{nf}"
            else:
                nt += 1; reg[("tab", b if kind == "TABLE" else a)] = f"Table {ch}.{nt}"
    return reg


def fill(text, N, reg, used, refs):
    def rep(m):
        k = m.group(1)
        if k.startswith("fig:") or k.startswith("tab:"):
            kind, i = k.split(":", 1)
            refs.add((kind, i))
            return reg.get((kind, i), f"[[MISSING {k}]]")
        if k in N:
            used.add(k)
            return N[k][0]
        return f"[[MISSING {k}]]"
    return re.sub(r"\{\{([^}]+)\}\}", rep, text)


_FONTS = {}


def text_cm(s, bold=False, pt=TABLE_PT):
    """Printed width of a string in Times New Roman at pt points, in cm (measured with the real font file)."""
    from PIL import ImageFont
    key = (bold, pt)
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(FONT_FILES[bold], 200)
    return _FONTS[key].getlength(s) / 200 * pt / 72 * 2.54


NUMERIC = re.compile(r"^[−\-+]?[\d.,]+%?$|^[−\-+]?[\d.,]+ ?/ ?[\d.,]+( ?/ ?[\d.,]+)?$|^–$|^n/a$")
CELL_PAD = 0.50  # cm: Word's left + right cell margins (0.38) plus a safety margin


def col_widths(head, rows, avail):
    """Column widths (cm) so that no word or number breaks: each column is at least as wide as its longest word (or
    whole number), header words included; spare width goes to the columns with the longest text."""
    cols = list(zip(*([head] + rows)))
    mins, prefs = [], []
    for j, c in enumerate(cols):
        words = []
        for i, cell in enumerate(c):
            s = str(cell)
            parts = [s] if NUMERIC.match(s.strip()) else s.split()
            words += [(w, i == 0) for w in parts]
        mins.append(max(text_cm(w, b) for w, b in words) * 1.04 + CELL_PAD)
        prefs.append(max(text_cm(str(cell), i == 0) for i, cell in enumerate(c)) * 1.04 + CELL_PAD)
    tot_min = sum(mins)
    if tot_min > avail:
        return None, tot_min
    extra = avail - tot_min
    want = [max(p - m, 0) for p, m in zip(prefs, mins)]
    sw = sum(want)
    widths = [m + (extra * w / sw if sw else extra / len(mins)) for m, w in zip(mins, want)]
    # do not stretch columns far beyond their longest text: hand surplus to the text-heavy columns
    return widths, tot_min


def cell_text(par, s, size, bold=False, color=None):
    """Write cell text; hyphens become non-breaking hyphens so names like GARCH-normal never split."""
    s = str(s)
    if re.match(r"^-\d", s):
        s = "\u2212" + s[1:]  # minus sign, kept with the number
    for k, piece in enumerate(s.split("-")):
        if k:
            r = par.add_run(); r._r.append(OxmlElement("w:noBreakHyphen")); set_font(r, size, bold=bold, color=color)
        if piece:
            set_font(par.add_run(piece), size, bold=bold, color=color)


def short_caption(cap):
    """First sentence of a caption, at most 12 words (for the lists of figures and tables)."""
    s = re.split(r"(?<=[a-z0-9)])\. |; |: (?=[a-z])", cap.strip())[0].rstrip(".")
    w = s.split()
    if len(w) > 12:
        s = " ".join(w[:12])
        s = re.sub(r"[,;:(]+$", "", s) + "…"
    return s


def caption_paras(doc, style, number, caption, keep=True):
    short = short_caption(caption)
    c = doc.add_paragraph(style=style); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; keep_next(c) if keep else None
    set_font(c.add_run(f"{number}: "), 11, bold=True); set_font(c.add_run(short), 11)
    if short.rstrip("…") != caption.strip().rstrip("."):
        rest = caption.strip()
        if rest.startswith(short.rstrip("…")):
            rest = rest[len(short.rstrip("…")):].lstrip(" .;:,")
        if rest:
            d = doc.add_paragraph(); d.alignment = WD_ALIGN_PARAGRAPH.CENTER
            d.paragraph_format.space_before = Pt(0); d.paragraph_format.space_after = Pt(2)
            set_font(d.add_run(rest[0].upper() + rest[1:]), 10)
            if keep:
                keep_next(d)
    return c


STATE = {"orient": "portrait"}


def set_orientation(doc, orient):
    """Section break to landscape or portrait A4 with the same margins; page numbers continue (footer linked)."""
    from docx.enum.section import WD_ORIENT
    if STATE["orient"] == orient:
        return
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    sec.orientation = WD_ORIENT.LANDSCAPE if orient == "landscape" else WD_ORIENT.PORTRAIT
    sec.page_width, sec.page_height = (Cm(29.7), Cm(21.0)) if orient == "landscape" else (Cm(21.0), Cm(29.7))
    sec.left_margin = sec.right_margin = Cm(2.5); sec.top_margin = sec.bottom_margin = Cm(2.3)
    sec.different_first_page_header_footer = False
    STATE["orient"] = orient


def add_table(doc, number, caption, source, head, rows, widths=None, family_col=0, small=False, qa=None):
    head = [str(h) for h in head]
    rows = [["Bench." if str(v) == "Benchmark" else str(v) for v in r] for r in rows]
    avail = TEXT_W[STATE["orient"]]
    w, need = col_widths(head, rows, avail)
    switched = False
    if w is None and STATE["orient"] == "portrait":  # only if it still breaks: put this table on a landscape page
        set_orientation(doc, "landscape"); switched = True
        avail = TEXT_W["landscape"]; w, need = col_widths(head, rows, avail)
    if w is None:
        w = [x * avail / need for x in col_widths(head, rows, 10 ** 6)[0]]
        if qa is not None:
            qa.setdefault("tight_tables", []).append(number)
    caption_paras(doc, "Table Caption", number, caption)
    size = TABLE_PT
    tb = doc.add_table(rows=1, cols=len(head)); tb.style = "Table Grid"; tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    tb.autofit = False
    tblPr = tb._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    tw = OxmlElement("w:tblW"); tw.set(qn("w:w"), str(int(sum(w) / 2.54 * 1440))); tw.set(qn("w:type"), "dxa"); tblPr.append(tw)
    numeric = [all(NUMERIC.match(str(r[j]).strip()) for r in rows if str(r[j]).strip()) and any(str(r[j]).strip() for r in rows) for j in range(len(head))]
    for j, h in enumerate(head):
        c = tb.rows[0].cells[j]; shade(c, "333333")
        par = c.paragraphs[0]; par.paragraph_format.space_after = Pt(0); par.paragraph_format.line_spacing = 1.0; keep_next(par)
        if numeric[j]:
            par.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        cell_text(par, h, size, bold=True, color="FFFFFF")
    repeat_header(tb.rows[0])
    for r in rows:
        cells = tb.add_row().cells
        model = str(r[0])
        fill_hex = "FEE0D2" if model in GARCH else "DEEBF7" if model in ML else None
        for j, v in enumerate(r):
            par = cells[j].paragraphs[0]; par.paragraph_format.space_after = Pt(0); par.paragraph_format.line_spacing = 1.0
            if numeric[j]:
                par.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            cell_text(par, v, size)
            if fill_hex and family_col is not None:
                shade(cells[j], fill_hex)
    grid = tb._tbl.tblGrid
    for j, gc in enumerate(grid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(w[j] / 2.54 * 1440)))
    for row in tb.rows:
        cs = OxmlElement("w:cantSplit"); row._tr.get_or_add_trPr().append(cs)
        for j, c in enumerate(row.cells):
            c.width = Cm(w[j])
    s = doc.add_paragraph(); s.paragraph_format.space_after = Pt(8); s.paragraph_format.space_before = Pt(2)
    set_font(s.add_run(f"Source: {source}"), 9.5, italic=True)
    if switched:
        set_orientation(doc, "portrait")


def trimmed(full, pad=12):
    """Copy of the image with uniform white margins removed (kept in report/figures/_trimmed)."""
    from PIL import ImageChops
    im = Image.open(full).convert("RGB")
    box = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    if not box:
        return full
    box = (max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, im.width), min(box[3] + pad, im.height))
    out = os.path.join(ROOT, "report", "figures", "_trimmed", os.path.basename(os.path.dirname(full)) + "__" + os.path.basename(full))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.crop(box).save(out, dpi=(300, 300))
    return out


def add_figure(doc, number, path, caption, source, alt_text, qa, width_cm=None):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        qa["missing_images"].append(path)
        return
    full = trimmed(full)
    w, h = Image.open(full).size
    dpi_w = w / (MAX_W / 2.54)
    max_w = 25.0 if STATE["orient"] == "landscape" else MAX_W
    max_h = 14.7 if STATE["orient"] == "landscape" else MAX_H
    width = min(max_w, max_h * w / h)
    if width_cm:  # fixed print width (dashboard screenshots)
        width = float(width_cm)
    qa["images"].append(dict(number=number, path=path, px=f"{w}x{h}", width_cm=round(width, 1), effective_dpi=round(w / (width / 2.54))))
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; keep_next(p)
    p.paragraph_format.space_before = Pt(6)
    p.add_run().add_picture(full, width=Cm(width))
    alt(doc.inline_shapes[-1], alt_text)
    caption_paras(doc, "Figure Caption", number, caption)
    s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER; s.paragraph_format.space_after = Pt(6)
    set_font(s.add_run(f"Source: {source}"), 9.5, italic=True)
    del dpi_w


def add_image(doc, path, width_cm, alt_text):
    full = os.path.join(ROOT, path)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(full, width=Cm(float(width_cm)))
    alt(doc.inline_shapes[-1], alt_text)


def add_phones(doc, number, paths, caption, source, alt_text, qa):
    """Three phone screenshots side by side (about 5.5 cm each) as one numbered figure."""
    tb = doc.add_table(rows=1, cols=len(paths)); tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, pth in enumerate(paths):
        full = os.path.join(ROOT, pth)
        if not os.path.exists(full):
            qa["missing_images"].append(pth); continue
        c = tb.rows[0].cells[j]; c.width = Cm(5.6)
        par = c.paragraphs[0]; par.alignment = WD_ALIGN_PARAGRAPH.CENTER; keep_next(par)
        par.add_run().add_picture(full, width=Cm(5.4))
        alt(doc.inline_shapes[-1], f"{alt_text} ({j + 1} of {len(paths)})")
        w, h = Image.open(full).size
        qa["images"].append(dict(number=number, path=pth, px=f"{w}x{h}", width_cm=5.4, effective_dpi=round(w / (5.4 / 2.54))))
    cs = OxmlElement("w:cantSplit"); tb.rows[0]._tr.get_or_add_trPr().append(cs)
    caption_paras(doc, "Figure Caption", number, caption)
    s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER; s.paragraph_format.space_after = Pt(6)
    set_font(s.add_run(f"Source: {source}"), 9.5, italic=True)


def means(doc, text):
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]; shade(c, "F4F4F4"); c.width = Cm(16)
    cs = OxmlElement("w:cantSplit"); t.rows[0]._tr.get_or_add_trPr().append(cs)
    p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(2); p.paragraph_format.space_before = Pt(2)
    set_font(p.add_run("What this means. "), 11.5, bold=True)
    inline(p, text, 11.5)
    tblPr = t._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "6"); e.set(qn("w:color"), "999999")
        borders.append(e)
    tblPr.append(borders)
    sp = doc.add_paragraph(); sp.paragraph_format.space_after = Pt(0); sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.line_spacing = Pt(6)


def render(doc, f, N, T, reg, qa, used, refs):
    ch = int(os.path.basename(f)[:2])
    lines = open(f, encoding="utf-8").read().split("\n")
    i = 0
    printed = []
    while i < len(lines):
        raw = lines[i].rstrip()
        line = fill(raw, N, reg, used, refs)
        i += 1
        if not line.strip():
            continue
        printed.append(line)
        if line.startswith("# "):
            if STATE["orient"] != "portrait":
                set_orientation(doc, "portrait")
                h = doc.add_heading(line[2:].strip(), level=1)
            else:
                h = doc.add_heading(line[2:].strip(), level=1)
                h.paragraph_format.page_break_before = True
        elif line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
        elif line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
        elif line.startswith("[[FIG:"):
            a = line[6:-2].split("|")
            add_figure(doc, reg[("fig", a[0])], a[1], a[2], a[3], a[4], qa, a[5] if len(a) > 5 else None)
            qa["placed"].add(("fig", a[0]))
        elif line.startswith("[[IMG:"):
            pth, wcm, alt_text = line[6:-2].split("|")
            add_image(doc, pth, wcm, alt_text)
        elif line.startswith("[[PHONES:"):
            a = line[9:-2].split("|")
            add_phones(doc, reg[("fig", a[0])], a[1:4], a[4], a[5], a[6], qa)
            qa["placed"].add(("fig", a[0]))
        elif line.strip() == "[[LANDSCAPE]]":
            set_orientation(doc, "landscape")
        elif line.strip() == "[[PORTRAIT]]":
            set_orientation(doc, "portrait")
        elif line.startswith("[[SHOWS]]"):
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(4)
            set_font(p.add_run("What this shows. "), 11, bold=True); inline(p, line[9:].strip(), 11)
        elif line.startswith("[[TABLE:"):
            key, tid = line[8:-2].split("|")
            t = T[key]
            add_table(doc, reg[("tab", tid)], t["caption"], t["source"], t["head"], t["rows"], t.get("widths"),
                      t.get("family_col", 0), t.get("small", False), qa)
            qa["placed"].add(("tab", tid))
        elif line.startswith("[[MDTABLE:"):
            tid, cap, src = line[10:-2].split("|")
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [fill(c.strip(), N, reg, used, refs) for c in lines[i].strip().strip("|").split("|")]
                if not set("".join(cells)) <= set("-: "):
                    rows.append(cells)
                i += 1
            add_table(doc, reg[("tab", tid)], cap, src, rows[0], rows[1:], family_col=None, qa=qa)
            qa["placed"].add(("tab", tid))
        elif line.startswith("[[MEANS]]"):
            means(doc, line[9:].strip())
        elif line.startswith("- "):
            p = doc.add_paragraph(style="List Bullet"); p.paragraph_format.space_after = Pt(3)
            inline(p, line[2:])
        elif re.match(r"^\d+\. ", line):
            num, rest = line.split(" ", 1)
            p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.9); p.paragraph_format.first_line_indent = Cm(-0.6)
            p.paragraph_format.space_after = Pt(3)
            set_font(p.add_run(num + " "), 12); inline(p, rest)
        else:
            p = doc.add_paragraph()
            # justified, except lines with a URL, a file path or a long model name (they leave wide gaps when justified)
            ragged = re.search(r"https?://|\w+/\w+|\.(py|csv|md|json|yml|parquet)\b|GARCH-normal|EGARCH-|GJR-GARCH|_\w", line)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if ragged else WD_ALIGN_PARAGRAPH.JUSTIFY
            if ch == 8 and not line.startswith("#"):
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.left_indent = Cm(1.27); p.paragraph_format.first_line_indent = Cm(-1.27)
                p.paragraph_format.space_after = Pt(4)
                inline(p, line, 11)
                continue
            inline(p, line)
    return printed


# ------------------------------------------------------------------ QA of literal numbers
ALLOWED = re.compile(r"^(19|20)\d\d$|^\d{1,2}$|^(95|99|100|250|1600|900|5\.50)$")


def literal_numbers(text):
    t = re.sub(r"\{\{[^}]+\}\}", "", text)
    t = re.sub(r"\[\[(FIG|TABLE|MDTABLE)[^\]]*\]\]", "", t)
    t = re.sub(r"(Figure|Table|Section|Chapter|Appendix|RQ|H)\s?\d+(\.\d+)?", "", t)
    t = re.sub(r"\d{4}-\d{2}-\d{2}", "", t)
    out = []
    for m in re.finditer(r"(?<![\w.])\d+(?:[.,]\d+)?%?", t):
        v = m.group(0).rstrip("%")
        if not ALLOWED.match(v):
            out.append(m.group(0))
    return out


def main():
    N, T = build()
    files = chapters()
    reg = register(files)
    doc = Document()
    styles(doc)
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    for side in ("left_margin", "right_margin"):
        setattr(sec, side, Cm(2.5))
    sec.top_margin = sec.bottom_margin = Cm(2.3)
    sec.different_first_page_header_footer = True
    cover(doc)
    new = doc.add_section(WD_SECTION.NEW_PAGE)
    new.different_first_page_header_footer = False
    page_number_footer(new)
    front(doc)
    qa = dict(missing_images=[], images=[], placed=set(), literal={})
    used, refs = set(), set()
    per_chapter = {}
    printed_all = []
    for f in files:
        printed = render(doc, f, N, T, reg, qa, used, refs)
        ch = int(os.path.basename(f)[:2])
        per_chapter[ch] = dict(figures=sum(1 for k, v in reg.items() if k[0] == "fig" and v.startswith(f"Figure {ch}.")),
                               tables=sum(1 for k, v in reg.items() if k[0] == "tab" and v.startswith(f"Table {ch}.")))
        if ch in (5, 6, 7):
            raw = chr(10).join(l for l in open(f, encoding="utf-8").read().split(chr(10)) if not l.startswith("#"))
            qa["literal"][ch] = sorted(set(literal_numbers(raw)))
        printed_all += printed
    doc.save(OUT)

    text = "\n".join(printed_all)
    missing = sorted(set(re.findall(r"\[\[MISSING [^\]]+\]\]", text)))
    markers = sorted(set(re.findall(r"\[(?:FILL|UNVERIFIED)[^\]]*\]", text)))
    unref = sorted(f"{reg[k]} ({k[1]})" for k in reg if k not in refs and not k[1].startswith(("dash_", "desk_")))
    lines = ["# Phase 2 report: build QA", "",
             f"- Placeholders filled: {len(used)} distinct numbers, each traced to a file in outputs/ (outputs/tables/report/report_numbers.csv)",
             f"- Unresolved placeholders: {missing or 'none'}",
             f"- [FILL] / [UNVERIFIED] markers in printed text: {markers or 'none'}",
             f"- Figures or tables never referenced in the text: {unref or 'none'}",
             f"- Missing image files: {qa['missing_images'] or 'none'}",
             f"- Tables whose words could not all fit their columns: {qa.get('tight_tables') or 'none'}", "",
             "## Figures and tables per chapter", "", "| Chapter | Figures | Tables |", "|---|---|---|"]
    lines += [f"| {c} | {v['figures']} | {v['tables']} |" for c, v in per_chapter.items()]
    lines += ["", "## Images (width in the report and effective resolution)", "", "| Figure | File | Pixels | Width (cm) | Effective DPI |", "|---|---|---|---|---|"]
    lines += [f"| {x['number']} | {x['path']} | {x['px']} | {x['width_cm']} | {x['effective_dpi']} |" for x in qa["images"]]
    lines += ["", "## Literal numbers in Chapters 5-7 not filled from outputs (for review)", ""]
    lines += [f"- Chapter {c}: {', '.join(v) if v else 'none'}" for c, v in qa["literal"].items()]
    open(os.path.join(ROOT, "report", "qa_phase2.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    json.dump(dict(per_chapter=per_chapter, registry={f"{k[0]}:{k[1]}": v for k, v in reg.items()},
                   headings=[l[2:].strip() for l in printed_all if l.startswith("# ")]),
              open(os.path.join(ROOT, "report", "build_registry.json"), "w", encoding="utf-8"), indent=1)
    print("\n".join(lines[:8]))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
