"""
Audit Booklet Generator — generates a .docx working paper booklet
for a given engagement. Called from /api/booklet/generate/<eid>
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import datetime


def _set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def _add_heading(doc, text, level=1, color="003366"):
    p = doc.add_heading(text, level=level)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in p.runs:
        run.font.color.rgb = RGBColor(
            int(color[0:2], 16),
            int(color[2:4], 16),
            int(color[4:6], 16)
        )
    return p


def _add_kv(doc, label, value, bold_label=True):
    p = doc.add_paragraph()
    r1 = p.add_run(f"{label}: ")
    r1.bold = bold_label
    r1.font.size = Pt(10)
    r2 = p.add_run(str(value) if value else "—")
    r2.font.size = Pt(10)
    return p


def _add_table_header(table, headers, bg="003366", fg="DAA520"):
    hdr_row = table.rows[0]
    for i, (cell, header) in enumerate(zip(hdr_row.cells, headers)):
        cell.text = header
        _set_cell_bg(cell, bg)
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.bold = True
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(
                    int(fg[0:2], 16),
                    int(fg[2:4], 16),
                    int(fg[4:6], 16)
                )


def generate_booklet(eng, tasks, comments_by_task, reviews_by_task,
                     queries, team, filepath,
                     firm_name="", firm_reg_no=""):
    doc = Document()

    # ── Page margins ──────────────────────────────────────────
    for section in doc.sections:
        section.top_margin    = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin   = Cm(2.5)
        section.right_margin  = Cm(2.5)

    # ══════════════════════════════════════════════════════════
    #  COVER PAGE
    # ══════════════════════════════════════════════════════════
    doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("AUDIT WORKING PAPERS BOOKLET")
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(0, 51, 102)

    doc.add_paragraph()
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub.add_run(eng.get("client_name") or "")
    r.bold = True
    r.font.size = Pt(16)

    sub2 = doc.add_paragraph()
    sub2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = sub2.add_run(f"{eng.get('engagement_type','')} — FY {eng.get('financial_year','')}")
    r2.font.size = Pt(13)
    r2.font.color.rgb = RGBColor(80, 80, 80)

    doc.add_paragraph()

    # Firm details box
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.style = 'Table Grid'
    tbl.rows[0].cells[0].text = "Prepared by"
    tbl.rows[0].cells[1].text = firm_name or "CA Firm"
    if firm_reg_no:
        row = tbl.add_row()
        row.cells[0].text = "Firm Reg. No."
        row.cells[1].text = firm_reg_no
    row2 = tbl.add_row()
    row2.cells[0].text = "Generated on"
    row2.cells[1].text = datetime.now().strftime("%d %B %Y, %I:%M %p")
    row3 = tbl.add_row()
    row3.cells[0].text = "Period"
    row3.cells[1].text = f"{eng.get('period_from','—')} to {eng.get('period_to','—')}"

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    #  SECTION 1: ENGAGEMENT DETAILS
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "1. Engagement Details")
    _add_kv(doc, "Client",           eng.get("client_name",""))
    _add_kv(doc, "PAN",              eng.get("pan",""))
    _add_kv(doc, "GSTIN",            eng.get("gstin",""))
    _add_kv(doc, "Engagement Type",  eng.get("engagement_type",""))
    _add_kv(doc, "Financial Year",   eng.get("financial_year",""))
    _add_kv(doc, "Period",           f"{eng.get('period_from','—')} to {eng.get('period_to','—')}")
    _add_kv(doc, "Status",           eng.get("status",""))
    _add_kv(doc, "Notes",            eng.get("notes",""))

    doc.add_paragraph()

    # ══════════════════════════════════════════════════════════
    #  SECTION 2: AUDIT TEAM
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "2. Audit Team")
    if team:
        tbl = doc.add_table(rows=1, cols=3)
        tbl.style = 'Table Grid'
        _add_table_header(tbl, ["Name", "Role", "Email"])
        for m in team:
            row = tbl.add_row()
            row.cells[0].text = m.get("full_name","")
            row.cells[1].text = m.get("role","")
            row.cells[2].text = m.get("email","")
    else:
        doc.add_paragraph("No team members assigned.")

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    #  SECTION 3: TASK WORKING PAPERS
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "3. Task-wise Working Papers")

    # Group tasks by area
    areas = {}
    for t in tasks:
        area = t.get("area") or "General"
        areas.setdefault(area, []).append(t)

    for area, area_tasks in areas.items():
        _add_heading(doc, area, level=2, color="1a4d80")

        for t in area_tasks:
            tid = t["id"]

            # Task header
            p = doc.add_paragraph()
            r = p.add_run(f"  {t.get('title','')}")
            r.bold = True
            r.font.size = Pt(10)
            r.font.color.rgb = RGBColor(0, 51, 102)

            # Task details table
            tbl = doc.add_table(rows=1, cols=4)
            tbl.style = 'Table Grid'
            _add_table_header(tbl, ["Status", "Priority", "Due Date", "WP Ref"],
                              bg="1a4d80", fg="DAA520")
            row = tbl.add_row()
            row.cells[0].text = t.get("status","")
            row.cells[1].text = t.get("priority","")
            row.cells[2].text = str(t.get("due_date","")) if t.get("due_date") else "—"
            row.cells[3].text = t.get("working_paper_ref","") or "—"

            # Assignees
            assignees = t.get("assignee_name","") or "Unassigned"
            _add_kv(doc, "    Assigned To", assignees)

            # Description
            if t.get("description"):
                _add_kv(doc, "    Description", t["description"])

            # Comments
            cmts = comments_by_task.get(tid, [])
            if cmts:
                doc.add_paragraph("    Comments:", style=None).runs[0].bold = True
                for c in cmts:
                    p = doc.add_paragraph(style=None)
                    p.paragraph_format.left_indent = Cm(1)
                    r1 = p.add_run(f"[{c.get('author_name','?')} — {c.get('created_at','')[:16]}]")
                    r1.bold = True
                    r1.font.size = Pt(9)
                    r1.font.color.rgb = RGBColor(80, 80, 80)
                    p.add_run(f": {c.get('content','')}")

            # Reviews
            revs = reviews_by_task.get(tid, [])
            if revs:
                doc.add_paragraph("    Reviews:", style=None).runs[0].bold = True
                for rv in revs:
                    p = doc.add_paragraph(style=None)
                    p.paragraph_format.left_indent = Cm(1)
                    action = rv.get("action","")
                    color = RGBColor(30, 126, 68) if action == "Approved" else RGBColor(197, 48, 48)
                    r1 = p.add_run(f"[{action}] ")
                    r1.bold = True
                    r1.font.color.rgb = color
                    r1.font.size = Pt(9)
                    p.add_run(f"{rv.get('reviewer_name','')} — {rv.get('reviewed_at','')[:16]}")
                    if rv.get("remarks"):
                        p.add_run(f" — {rv['remarks']}")

            doc.add_paragraph()

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    #  SECTION 4: QUERY SHEET
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "4. Query Sheet")
    if queries:
        tbl = doc.add_table(rows=1, cols=6)
        tbl.style = 'Table Grid'
        _add_table_header(tbl,
            ["Sr.", "Query", "Response", "Status", "Raised By", "Date"])
        for q in queries:
            row = tbl.add_row()
            row.cells[0].text = str(q.get("sr_no",""))
            row.cells[1].text = q.get("query_text","")
            row.cells[2].text = q.get("response","") or "Pending"
            row.cells[3].text = q.get("status","")
            row.cells[4].text = q.get("raised_by_name","")
            row.cells[5].text = str(q.get("raised_date",""))[:10] if q.get("raised_date") else ""
    else:
        doc.add_paragraph("No queries raised for this engagement.")

    # ══════════════════════════════════════════════════════════
    #  FOOTER NOTE
    # ══════════════════════════════════════════════════════════
    doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(
        f"Generated by CA FirmHub"
        + (f" | {firm_name}" if firm_name else "")
        + f" | {datetime.now().strftime('%d-%m-%Y %H:%M')}"
    )
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(150, 150, 150)

    doc.save(filepath)
