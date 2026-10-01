"""Build the corrected warehouse-routing report."""

from pathlib import Path

import matplotlib.pyplot as plt
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


OUT = Path("output/docx/รายงาน_Q_Learning_72_ก้าว.docx")
ASSET = Path("tmp/report_assets/qlearning_72_comparison.png")
OUT.parent.mkdir(parents=True, exist_ok=True)
ASSET.parent.mkdir(parents=True, exist_ok=True)


def font(run, size=14, bold=False, color=None):
    run.font.name = "TH Sarabun New"
    run._element.rPr.rFonts.set(qn("w:ascii"), "TH Sarabun New")
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "TH Sarabun New")
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def shade(cell, fill):
    props = cell._tc.get_or_add_tcPr()
    node = OxmlElement("w:shd")
    node.set(qn("w:fill"), fill)
    props.append(node)


def border(cell, color="D9D9D9"):
    props = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "6")
        element.set(qn("w:color"), color)
        borders.append(element)
    props.append(borders)


def body(doc, text, before=0, after=6):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.line_spacing = 1.1
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    font(paragraph.add_run(text), 14)
    return paragraph


def heading(doc, text, level=1):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(11 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(4)
    font(paragraph.add_run(text), 18 if level == 1 else 15, bold=True)
    return paragraph


def table(doc, rows, widths):
    result = doc.add_table(rows=len(rows), cols=len(rows[0]))
    result.alignment = WD_TABLE_ALIGNMENT.CENTER
    result.autofit = False
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            cell = result.cell(row_index, column_index)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell.width = Cm(widths[column_index])
            border(cell)
            shade(cell, "34495E" if row_index == 0 else ("F4F7F8" if row_index % 2 == 0 else "FFFFFF"))
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(2)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if row_index == 0 else WD_ALIGN_PARAGRAPH.LEFT
            font(paragraph.add_run(str(value)), 10, bold=row_index == 0, color=(255, 255, 255) if row_index == 0 else None)
    return result


def make_chart():
    plt.rcParams.update({"font.size": 10, "font.family": "DejaVu Sans"})
    figure, axes = plt.subplots(1, 2, figsize=(8.1, 3.15), dpi=180)
    labels = ["Multi-Start\n2-Opt", "Grid-state\nQ-Learning"]
    colors = ["#295B86", "#70AD47"]
    axes[0].bar(labels, [78, 72], color=colors)
    axes[0].set_title("Actual warehouse travel distance")
    axes[0].set_ylabel("Steps")
    axes[0].set_ylim(0, 90)
    for index, value in enumerate([78, 72]):
        axes[0].text(index, value + 2, str(value), ha="center")
    axes[1].bar(labels, [0.0425, 5.39], color=colors)
    axes[1].set_title("Runtime")
    axes[1].set_ylabel("Seconds")
    axes[1].set_ylim(0, 6)
    for index, value in enumerate([0.0425, 5.39]):
        axes[1].text(index, value + 0.15, f"{value:g}", ha="center")
    figure.tight_layout()
    figure.savefig(ASSET, bbox_inches="tight")
    plt.close(figure)


make_chart()
doc = Document()
section = doc.sections[0]
section.top_margin = Cm(1.7)
section.bottom_margin = Cm(1.7)
section.left_margin = Cm(1.8)
section.right_margin = Cm(1.8)
styles = doc.styles
styles["Normal"].font.name = "TH Sarabun New"
styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "TH Sarabun New")

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_after = Pt(3)
font(title.add_run("รายงานการเปรียบเทียบ Q Learning และ Multi Start 2 Opt"), 24, bold=True)
subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
subtitle.paragraph_format.space_after = Pt(12)
font(subtitle.add_run("การหาเส้นทางหยิบสินค้าในคลังสินค้าด้วย A Star Search"), 16)

heading(doc, "บทสรุปผู้บริหาร")
body(doc, "การทดลองบนแผนที่คลังสินค้าขนาด 18 x 20 และจุดหยิบสินค้า 10 จุด พบว่า Grid-state Q-Learning ที่ใช้เส้นทางตัวอย่างช่วยฝึก เดินได้ 72 ก้าว ซึ่งสั้นกว่า Multi-Start 2-Opt ที่เดินได้ 78 ก้าว 6 ก้าว ผลนี้เกิดจากการให้สถานะของตัวแทนประกอบด้วยตำแหน่งบนกริดและรายการจุดที่หยิบแล้ว จึงรักษาตำแหน่งยืนหยิบสินค้าในเส้นทางต่อเนื่องได้")
body(doc, "ผล 72 ก้าวเป็นผลของ demonstration-assisted Q-learning ไม่ใช่การสำรวจแบบ Q-learning ล้วน ๆ จึงควรใช้เพื่อแสดงศักยภาพของการกำหนดสถานะบนกริดและเป็นเส้นอ้างอิงสำหรับการพัฒนาโมเดลต่อไป")

heading(doc, "1 วัตถุประสงค์")
body(doc, "1) เปรียบเทียบระยะเดินจริงของ Multi-Start 2-Opt กับ Grid-state Q-Learning 2) ตรวจสอบให้เส้นทางเดินได้จริงบนช่องทางเดินและหยิบสินค้าครบทุกจุด 3) รายงานข้อจำกัดของวิธีฝึกที่ใช้เส้นทางตัวอย่าง")

heading(doc, "2 ข้อมูลและการตั้งค่าการทดลอง")
body(doc, "คลังสินค้าถูกแทนด้วยกริดขนาด 18 x 20 ค่า 0 คือทางเดิน และค่า 1 คือชั้นวางสินค้า จุดเริ่มต้นอยู่ที่ (0, 0) จุดสิ้นสุดอยู่ที่ (17, 19) และสุ่มจุดหยิบสินค้า 10 จุดด้วย seed = 20")
table(doc, [
    ["รายการ", "ค่าที่ใช้"],
    ["จำนวนจุดหยิบสินค้า", "10 จุด"],
    ["วิธีหาเส้นทางระหว่างช่อง", "A* Search"],
    ["สถานะ Q-Learning", "ตำแหน่ง (แถว, คอลัมน์) และ picked mask"],
    ["การฝึก", "Q-learning replay จากเส้นทางตัวอย่าง 72 ก้าว"],
    ["epochs / alpha / gamma", "5,000 / 0.20 / 1.00"],
    ["การตรวจผล", "เดินจาก Entrance ผ่านทุกจุดหยิบถึง Exit"],
], [6.0, 10.4])

heading(doc, "3 วิธีดำเนินการ")
heading(doc, "3.1 Multi Start 2 Opt", 2)
body(doc, "สุ่มลำดับจุดหยิบหลายแบบ แล้วปรับปรุงด้วย 2-Opt และเลือกคำตอบที่มีต้นทุนต่ำที่สุด จากนั้นเชื่อมช่วงเส้นทางด้วย A* บนกริดจริง")
heading(doc, "3.2 Grid state Q Learning", 2)
body(doc, "แต่ละ state ประกอบด้วยตำแหน่งปัจจุบันบนกริดและ bit mask ของจุดที่หยิบแล้ว action คือการเดินขึ้น ลง ซ้าย หรือขวา รางวัลสำหรับการเดินปกติเท่ากับ -1 และให้รางวัลเมื่อถึง Exit หลังหยิบครบทุกจุด การฝึกใช้ replay จากเส้นทางตัวอย่างที่ผ่านการตรวจสอบแล้ว เพื่อให้แบบจำลองเรียนรู้นโยบายการเดินต่อเนื่อง")

heading(doc, "4 ผลการทดลอง")
table(doc, [
    ["วิธี", "ระยะจริง ก้าว", "เวลา วินาที", "ลำดับจุดหยิบ"],
    ["Multi-Start 2-Opt", "78", "0.0425", "P2, P9, P1, P8, P6, P4, P3, P10, P7, P5"],
    ["Grid-state Q-Learning", "72", "5.39", "P2, P9, P1, P8, P6, P4, P3, P10, P7, P5"],
], [3.7, 3.0, 2.6, 7.1])
body(doc, "รูปที่ 1 เปรียบเทียบระยะเดินจริงและเวลาที่ใช้ในการคำนวณ", after=3)
chart = doc.add_paragraph()
chart.alignment = WD_ALIGN_PARAGRAPH.CENTER
chart.add_run().add_picture(str(ASSET), width=Cm(15.8))

heading(doc, "5 อภิปรายผล")
body(doc, "Grid-state Q-Learning ลดระยะเดินจาก 78 เหลือ 72 ก้าว เพราะนโยบายคำนึงถึงตำแหน่งยืนหยิบสินค้าในแต่ละก้าว ไม่ใช่เพียงลำดับของจุดหยิบ อย่างไรก็ดี วิธีนี้ใช้เวลามากกว่า Multi-Start 2-Opt และอาศัยเส้นทางตัวอย่างในการฝึก จึงไม่ควรใช้เป็นหลักฐานว่า Q-learning แบบสำรวจอิสระจะได้ 72 ก้าวทุกครั้ง")

heading(doc, "6 ข้อสรุปและข้อเสนอแนะ")
body(doc, "สำหรับข้อมูลทดลองชุดนี้ Grid-state Q-Learning แบบใช้เส้นทางตัวอย่างช่วยฝึก ให้ระยะเดินจริง 72 ก้าวและสั้นกว่า Multi-Start 2-Opt ที่ 78 ก้าว หากต้องการประเมินความสามารถในการเรียนรู้ด้วยตนเอง ควรทดลองแบบไม่ใช้เส้นทางตัวอย่าง หลาย seed และรายงานค่าเฉลี่ย ส่วนเบี่ยงเบนมาตรฐาน อัตราสำเร็จ และเวลา")

heading(doc, "ภาคผนวก เส้นทางที่ผ่านการตรวจสอบ")
body(doc, "เส้นทางเริ่มที่ Entrance และสิ้นสุดที่ Exit ภายใน 72 ก้าว โดยหยิบสินค้าตามลำดับ P2 -> P9 -> P1 -> P8 -> P6 -> P4 -> P3 -> P10 -> P7 -> P5 ทุกก้าวอยู่บนช่องทางเดิน 4 ทิศทาง และไม่ตัดผ่านชั้นวางสินค้า")

footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
font(footer.add_run("รายงานการทดลองเส้นทางหยิบสินค้า"), 10, color=(100, 100, 100))
doc.save(OUT)
print("Report created")
