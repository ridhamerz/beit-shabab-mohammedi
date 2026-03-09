import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import io

# 1. إعدادات الصفحة والتنسيق الملكي
st.set_page_config(page_title="نظام بيت شباب قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px; font-weight: bold; }
    .section-box { background: #f8f9fa; padding: 20px; border-radius: 10px; border-right: 5px solid #1e3c72; margin-bottom: 20px; }
    .developer-footer { background: #1e3c72; color: white; padding: 10px; border-radius: 8px; text-align: center; margin-top: 30px; font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

# 2. إدارة قاعدة البيانات (النسخة v9 لضمان توافق الأعمدة)
DB_FILE = 'hostel_guelma_v9_final.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS current_guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, birth_date TEXT, birth_place TEXT, id_type TEXT, id_card TEXT, 
            wing TEXT, room TEXT, bed TEXT, check_in TEXT, check_out TEXT,
            is_minor TEXT, minor_doc TEXT, phone TEXT, purpose TEXT, job TEXT, address TEXT
        )''')
        conn.commit()

init_db()

# 3. دالة تصدير الوورد المراجعة (بالترتيب الرسمي)
def generate_word_report(data, r_date):
    doc = Document()
    section = doc.sections[0]
    section.orientation = 1 
    section.page_width, section.page_height = section.page_height, section.page_width

    header_text = [
        "وزارة الشباب والرياضة",
        "مديرية الشباب والرياضة لولاية قالمة",
        "ديوان مؤسسات الشباب لولاية قالمة",
        "بيت الشباب محمدي يوسف قالمة"
    ]
    for line in header_text:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line)
        run.bold = True
        run.font.size = Pt(13)
        p.paragraph_format.space_after = Pt(0)

    doc.add_paragraph(f"\nسجل الحجوزات اليومي بتاريخ: {r_date}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    table = doc.add_table(rows=1, cols=9)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # رأس الجدول كما طلبت
    headers = ["الملاحظات", "المهنة", "عدد الليالي", "نوع ورقم بطاقة التعريف", "العنوان الشخصي", "تاريخ ومكان الازدياد", "الاسم واللقب", "رقم الغرفة", "رقم"]
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        hdr_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    for idx, row in enumerate(data, 1):
        row_cells = table.add_row().cells
        row_cells[8].text = str(idx)             # المسلسل
        row_cells[7].text = str(row[7])          # رقم الغرفة (Index 7)
        row_cells[6].text = str(row[1])          # الاسم (Index 1)
        row_cells[5].text = f"{row[2]} بـ {row[3]}" # الميلاد (Index 2 & 3)
        row_cells[4].text = str(row[16]) if row[16] else "قالمة" # العنوان (Index 16)
        row_cells[3].text = f"{row[4]} {row[5]}" # الهوية (Index 4 & 5)
        row_cells[2].text = "1"                  # الليالي
        row_cells[1].text = str(row[15]) if row[15] else "/" # المهنة (Index 15)
        row_cells[0].text = ""                   # ملاحظات
        for cell in row_cells: cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    target = io.BytesIO()
    doc.save(target)
    return target.getvalue()

# 4. الواجهة الرسومية والتبويبات
st.markdown('<div class="main-title">🏢 نظام إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)

tabs = st.tabs(["➕ حجز جديد", "📊 الإحصائيات", "📋 التقارير"])

with tabs[0]: # تبويب الحجز
    st.markdown('<div class="section-box"><h4>📝 استمارة تسجيل نزيل</h4></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        g_name = st.text_input("👤 الاسم واللقب")
        g_bday = st.date_input("📅 تاريخ الميلاد", value=date(2000, 1, 1))
        g_bplace = st.text_input("📍 مكان الميلاد")
        g_address = st.text_input("🏠 العنوان الشخصي")
        g_job = st.text_input("💼 المهنة")
    with col2:
        g_id_type = st.selectbox("📄 نوع الوثيقة", ["بطاقة تعريف وطنية", "جواز سفر", "رخصة سياقة"])
        id_card_val = st.text_input("🪪 رقم الوثيقة")
        g_phone = st.text_input("📞 رقم الهاتف")
        g_purpose = st.text_input("🎯 غرض الزيارة")
        g_wing = st.selectbox("🏢 الجناح", ["جناح ذكور 👨", "جناح إناث 👩"])
    
    r_sel = st.selectbox("🚪 اختر الغرفة", ["غرفة 01", "غرفة 02", "غرفة 03", "غرفة 04", "غرفة 05"])
    bed_sel = st.radio("🛏️ السرير", ["1", "2", "3", "4", "5", "6"], horizontal=True)

    if st.button("💾 حفظ الحجز", use_container_width=True, type="primary"):
        if g_name and id_card_val:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("""INSERT INTO current_guests 
                (name, birth_date, birth_place, id_type, id_card, wing, room, bed, check_in, phone, purpose, job, address) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
                (g_name, str(g_bday), g_bplace, g_id_type, id_card_val, g_wing, r_sel, bed_sel, str(date.today()), g_phone, g_purpose, g_job, g_address))
            st.success(f"✅ تم تسجيل {g_name} بنجاح!")
        else: st.error("الرجاء ملء الاسم ورقم الهوية")

with tabs[2]: # تبويب التقارير
    st.subheader("📑 استخراج سجل الوارد (Word)")
    r_date = st.date_input("اختر التاريخ", date.today())
    if st.button("📄 توليد وتحميل الملف"):
        with sqlite3.connect(DB_FILE) as conn:
            data = conn.execute("SELECT * FROM current_guests WHERE check_in = ?", (str(r_date),)).fetchall()
        if data:
            doc_bytes = generate_word_report(data, r_date)
            st.download_button("📥 اضغط هنا لتحميل ملف الوورد", doc_bytes, f"سجل_{r_date}.docx")
        else: st.warning("لا توجد بيانات لهذا التاريخ")

st.markdown(f'<div class="developer-footer">Developer ®ridha_merzoug® [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
