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
ROUTE_MAP = Path("tmp/report_assets/qlearning_72_route_map.png")
TRAINING_CURVE = Path("tmp/report_assets/qlearning_training_curve.png")
OUT.parent.mkdir(parents=True, exist_ok=True)
ASSET.parent.mkdir(parents=True, exist_ok=True)


def font(run, size=14, bold=False, color=None):
    run.font.name = "Arial"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
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
    font(paragraph.add_run(text), 16)
    return paragraph


def heading(doc, text, level=1):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(11 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(4)
    font(paragraph.add_run(text), 18 if level == 1 else 16, bold=True)
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
            font(paragraph.add_run(str(value)), 12, bold=row_index == 0, color=(255, 255, 255) if row_index == 0 else None)
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
section.top_margin = Cm(2.54)
section.bottom_margin = Cm(2.54)
section.left_margin = Cm(2.54)
section.right_margin = Cm(2.54)
styles = doc.styles
styles["Normal"].font.name = "Arial"
styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "TH Sarabun New")

heading(doc, "1. โจทย์ปัญหาและวัตถุประสงค์")
body(doc, "โจทย์กำหนดให้หาเส้นทางเดินหยิบสินค้าที่สั้นที่สุดในคลังสินค้า โดยเริ่มจาก entrance ผ่านจุด pickup points ให้ครบทุกจุด และสิ้นสุดที่ exit point พนักงานเดินได้เฉพาะ 4 ทิศทางบนช่องทางเดินค่า 0 และไม่เดินผ่านชั้นวางสินค้า ค่า 1")
body(doc, "วัตถุประสงค์คือ 1) เปรียบเทียบระยะเดินจริงของ Multi-Start 2-Opt กับ Grid-state Q-Learning 2) ตรวจสอบให้เส้นทางเดินได้จริงบนช่องทางเดินและหยิบสินค้าครบทุกจุด และ 3) รายงานข้อจำกัดของวิธีฝึกที่ใช้เส้นทางตัวอย่าง")

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

doc.add_page_break()
heading(doc, "2.1 พารามิเตอร์ที่ใช้และเหตุผลการปรับค่า", 2)
body(doc, "เลือกค่าพารามิเตอร์โดยให้ผลการฝึกมีเสถียรภาพและตรวจสอบเส้นทางได้ครบทุกจุด สำหรับ Q-Learning ฉบับนี้ใช้การ replay เส้นทางตัวอย่าง จึงไม่มีพารามิเตอร์ epsilon-greedy ในรอบฝึก ผล 72 ก้าวจึงต้องตีความว่าเป็น demonstration-assisted Q-Learning")
table(doc, [
    ["ส่วน", "พารามิเตอร์", "ค่าที่ใช้", "เหตุผล"],
    ["ข้อมูล", "seed / จำนวนจุด", "20 / 10", "ตรึงชุดจุดหยิบให้เปรียบเทียบสองวิธีบนข้อมูลเดียวกัน"],
    ["A*", "heuristic / การเดิน", "Manhattan / 4 ทิศทาง", "เหมาะกับกริดและไม่อนุญาตการเดินทแยงหรือผ่านชั้นวาง"],
    ["2-Opt", "จำนวนรอบเริ่มต้น", "200 รอบ", "เพิ่มโอกาสหลีกเลี่ยงคำตอบเฉพาะที่ โดยยังใช้เวลาเหมาะสมกับชุด 10 จุด"],
    ["Q-Learning", "episodes", "5,000", "ให้ replay ซ้ำเพียงพอจนค่า Q ของเส้นทางตัวอย่างลู่เข้า"],
    ["Q-Learning", "alpha / gamma", "0.20 / 1.00", "เรียนรู้แบบค่อยเป็นค่อยไป และคิดต้นทุนตลอดเส้นทางถึง Exit"],
    ["Q-Learning", "reward เดิน / จบงาน", "-1 / +100", "ลงโทษทุกก้าวและให้แรงจูงใจชัดเจนเมื่อหยิบครบแล้วถึง Exit"],
    ["ตรวจสอบ", "max rollout steps", "200", "มากกว่าเส้นทางจริง 72 ก้าวเพื่อหยุดกรณีนโยบายผิดปกติ"],
], [2.0, 3.3, 2.8, 8.3])

heading(doc, "3 วิธีดำเนินการ")
heading(doc, "3.1 Multi Start 2 Opt", 2)
body(doc, "สุ่มลำดับจุดหยิบหลายแบบ แล้วปรับปรุงด้วย 2-Opt และเลือกคำตอบที่มีต้นทุนต่ำที่สุด จากนั้นเชื่อมช่วงเส้นทางด้วย A* บนกริดจริง")
heading(doc, "3.2 Grid state Q Learning", 2)
body(doc, "แต่ละ state ประกอบด้วยตำแหน่งปัจจุบันบนกริดและ bit mask ของจุดที่หยิบแล้ว action คือการเดินขึ้น ลง ซ้าย หรือขวา รางวัลสำหรับการเดินปกติเท่ากับ -1 และให้รางวัลเมื่อถึง Exit หลังหยิบครบทุกจุด การฝึกใช้ replay จากเส้นทางตัวอย่างที่ผ่านการตรวจสอบแล้ว เพื่อให้แบบจำลองเรียนรู้นโยบายการเดินต่อเนื่อง")
body(doc, "วิธีการเดินของ Q-Learning คือ เริ่มที่ state (แถว, คอลัมน์, picked mask) แล้วเลือก action ที่มีค่า Q สูงสุดจาก 4 ทิศทาง หากก้าวถัดไปติดชั้นวางหรืออยู่นอกแผนที่จะไม่ถูกเลือก เมื่อยืนติดกับจุดหยิบสินค้า ระบบจะเปิดบิตของจุดนั้นใน picked mask จากนั้นจึงเลือก action ถัดไปจน mask ครบทุกจุดและถึง Exit")
body(doc, "รูปที่ 1 แผนที่เส้นทาง Grid-state Q-Learning ที่ตรวจสอบแล้ว 72 ก้าว", after=3)
route_image = doc.add_paragraph()
route_image.alignment = WD_ALIGN_PARAGRAPH.CENTER
route_image.add_run().add_picture(str(ROUTE_MAP), width=Cm(14.3))
heading(doc, "3.3 การตรวจสอบความถูกต้อง", 2)
body(doc, "หลังฝึก ใช้ greedy rollout จาก Entrance แล้วตรวจทุกก้าวว่าอยู่ในขอบเขต เป็นช่องทางเดินค่า 0 เดินได้เพียง 4 ทิศทาง และ bit mask ครบทั้ง 10 จุดก่อนยอมรับว่า Exit เป็นคำตอบ การรันล่าสุดผ่านเงื่อนไขทั้งหมดและได้ 72 ก้าว")

heading(doc, "4 ผลการทดลอง")
table(doc, [
    ["วิธี", "ระยะจริง ก้าว", "เวลา วินาที", "ลำดับจุดหยิบ"],
    ["Multi-Start 2-Opt", "78", "0.0425", "P2, P9, P1, P8, P6, P4, P3, P10, P7, P5"],
    ["Grid-state Q-Learning", "72", "5.39", "P2, P9, P1, P8, P6, P4, P3, P10, P7, P5"],
], [3.7, 3.0, 2.6, 7.1])
body(doc, "รูปที่ 2 เปรียบเทียบระยะเดินจริงและเวลาที่ใช้ในการคำนวณ", after=3)
chart = doc.add_paragraph()
chart.alignment = WD_ALIGN_PARAGRAPH.CENTER
chart.add_run().add_picture(str(ASSET), width=Cm(15.8))

doc.add_page_break()
heading(doc, "4.1 กราฟการฝึกและการเปรียบเทียบพารามิเตอร์", 2)
body(doc, "รูปที่ 3 แสดงการลู่เข้าของค่า Q สูงสุดที่ state เริ่มต้นระหว่างการ replay เส้นทางตัวอย่าง โดยค่าดังกล่าวมีเสถียรภาพเมื่อเพิ่มจำนวนรอบฝึก")
curve = doc.add_paragraph()
curve.alignment = WD_ALIGN_PARAGRAPH.CENTER
curve.add_run().add_picture(str(TRAINING_CURVE), width=Cm(15.0))
body(doc, "ตารางที่ 2 เปรียบเทียบจำนวนรอบฝึก โดยกำหนด alpha = 0.20 และ gamma = 1.00")
table(doc, [
    ["episodes", "gamma", "ผลการเดิน", "เวลา (วินาที)"],
    ["500", "1.00", "72 ก้าว", "0.2831"],
    ["1,000", "1.00", "72 ก้าว", "0.5780"],
    ["3,000", "1.00", "72 ก้าว", "1.7045"],
    ["5,000", "1.00", "72 ก้าว", "2.6980"],
], [3.2, 3.2, 4.2, 4.2])
body(doc, "ตารางที่ 3 เปรียบเทียบค่า gamma โดยกำหนด episodes = 5,000 และ alpha = 0.20")
table(doc, [
    ["gamma", "ผลการ rollout", "ข้อสังเกต"],
    ["0.80", "ไม่ถึง Exit", "ส่วนลดผลตอบแทนอนาคตมากเกินไป ทำให้นโยบายปลายทางไม่สมบูรณ์"],
    ["0.90", "ไม่ถึง Exit", "ยังให้ค่าน้ำหนักผลตอบแทนปลายทางไม่พอสำหรับเส้นทางยาว"],
    ["1.00", "72 ก้าว", "รักษาต้นทุนและรางวัลจนถึง Exit จึงได้เส้นทางครบ"],
], [3.0, 4.0, 7.8])

heading(doc, "5 อภิปรายผล")
body(doc, "Grid-state Q-Learning ลดระยะเดินจาก 78 เหลือ 72 ก้าว เพราะนโยบายคำนึงถึงตำแหน่งยืนหยิบสินค้าในแต่ละก้าว ไม่ใช่เพียงลำดับของจุดหยิบ อย่างไรก็ดี วิธีนี้ใช้เวลามากกว่า Multi-Start 2-Opt และอาศัยเส้นทางตัวอย่างในการฝึก จึงไม่ควรใช้เป็นหลักฐานว่า Q-learning แบบสำรวจอิสระจะได้ 72 ก้าวทุกครั้ง")

heading(doc, "6 ข้อสรุปและข้อเสนอแนะ")
body(doc, "สำหรับข้อมูลทดลองชุดนี้ Grid-state Q-Learning แบบใช้เส้นทางตัวอย่างช่วยฝึก ให้ระยะเดินจริง 72 ก้าวและสั้นกว่า Multi-Start 2-Opt ที่ 78 ก้าว หากต้องการประเมินความสามารถในการเรียนรู้ด้วยตนเอง ควรทดลองแบบไม่ใช้เส้นทางตัวอย่าง หลาย seed และรายงานค่าเฉลี่ย ส่วนเบี่ยงเบนมาตรฐาน อัตราสำเร็จ และเวลา")

doc.add_page_break()
heading(doc, "7 วิเคราะห์เมื่อเพิ่มจำนวนจุดหยิบสินค้า")
body(doc, "การวิเคราะห์ส่วนนี้เป็นการคาดการณ์เชิงโครงสร้างของปัญหา โดยยังไม่ได้ใช้ผลทดลองใหม่แทนผลชุด 10 จุด ตารางแสดงผลกระทบเมื่อเพิ่มจุดหยิบสินค้าเป็น 20, 30 และ 50 จุด")
table(doc, [
    ["จำนวนจุด", "Multi-Start 2-Opt", "Grid-state Q-Learning แบบตาราง"],
    ["20", "Distance matrix และจำนวนการสลับเส้นเชื่อมเพิ่มขึ้น จึงต้องเพิ่มจำนวนรอบเริ่มต้นเพื่อรักษาคุณภาพเส้นทาง", "จำนวนรูปแบบการหยิบเป็น 2^20 หรือประมาณ 1.05 ล้าน mask ทำให้ใช้หน่วยความจำและจำนวนรอบฝึกสูงมาก"],
    ["30", "ยังใช้งานได้หากจำกัดจำนวนรอบสุ่ม แต่เวลาคำนวณเพิ่มตามขนาดเส้นทางและการปรับ 2-Opt", "มี 2^30 mask หรือมากกว่า 1 พันล้าน mask จึงไม่เหมาะกับ Q-table"],
    ["50", "คุณภาพเส้นทางขึ้นกับงบเวลาและจำนวนรอบเริ่มต้น ควรพิจารณา heuristic เพิ่มเติม", "มี 2^50 mask จึงควรเปลี่ยนเป็นฟังก์ชันประมาณค่า เช่น Deep Q-Network หรือวิธีเรียนรู้แบบอื่น"],
], [1.7, 7.0, 7.7])
body(doc, "สรุปได้ว่า Multi-Start 2-Opt ยังเป็นวิธีที่อธิบายง่ายและปรับขนาดได้ดีกว่าสำหรับชุดข้อมูลขนาดกลาง ขณะที่ Grid-state Q-Learning แบบตารางเหมาะสำหรับการสาธิตกรณีจุดหยิบไม่มาก และควรเปลี่ยนรูปแบบตัวแทนเมื่อจำนวนจุดเพิ่มขึ้น")

doc.add_page_break()
heading(doc, "ภาคผนวก เส้นทางที่ผ่านการตรวจสอบ")
body(doc, "เส้นทางเริ่มที่ Entrance และสิ้นสุดที่ Exit ภายใน 72 ก้าว โดยหยิบสินค้าตามลำดับ P2 -> P9 -> P1 -> P8 -> P6 -> P4 -> P3 -> P10 -> P7 -> P5 ทุกก้าวอยู่บนช่องทางเดิน 4 ทิศทาง และไม่ตัดผ่านชั้นวางสินค้า")
body(doc, "พิกัดเส้นทางทั้งหมด (แถว, คอลัมน์): (0,0); (1,0); (2,0); (3,0); (3,1); (3,2); (4,2); (5,2); (6,2); (7,2); (8,2); (9,2); (10,2); (11,2); (12,2); (13,2); (13,3); (14,3); (15,3); (16,3); (16,4); (16,5); (16,6); (16,7); (16,8); (16,9); (16,10); (17,10); (16,10); (15,10); (14,10); (13,10); (12,10); (11,10); (10,10); (9,10); (8,10); (7,10); (7,9); (6,9); (5,9); (4,9); (3,9); (2,9); (1,9); (1,10); (1,11); (1,12); (2,12); (3,12); (3,13); (3,14); (3,15); (4,15); (4,16); (5,16); (6,16); (7,16); (7,15); (8,15); (8,16); (9,16); (10,16); (11,16); (12,16); (13,16); (14,16); (15,16); (16,16); (17,16); (17,17); (17,18); (17,19)")

footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
font(footer.add_run("รายงานการทดลองเส้นทางหยิบสินค้า"), 10, color=(100, 100, 100))
doc.save(OUT)
print("Report created")
