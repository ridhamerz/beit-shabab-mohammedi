import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import io

# 1. إعداد الصفحة والتنسيق الملكي
st.set_page_config(page_title="نظام بيت شباب قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; font-weight: bold; }
    .section-box { background: #ffffff; padding: 20px; border-radius: 10px; border-right: 6px solid #1e3c72; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .stat-card { background: #1e3c72; color: white; padding: 15px; border-radius: 10px; text-align: center; }
    .bed-box { display: inline-block; width: 40px; height: 40px; margin: 4px; border-radius: 6px; text-align: center; line-height: 40px; color: white; font-weight: bold; font-size: 0.9rem; }
    .developer-footer { background: #1e3c72; color: white; padding: 12px; border-radius: 8px; text-align: center; margin-top: 40px; font-size: 0.85rem; border: 1px solid #00d4ff; }
    </style>
""", unsafe_allow_html=True)

DB_FILE = 'hostel_guelma_v9_final.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS current_guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, birth_date TEXT, birth_place TEXT, id_type TEXT, id_card TEXT UNIQUE, 
            wing TEXT, room TEXT, bed TEXT, check_in TEXT, check_out TEXT,
            is_minor TEXT, minor_doc TEXT, phone TEXT, purpose TEXT, job TEXT, address TEXT
        )''')
        conn.commit()

init_db()

# دالة تصدير الوورد (الترويسة الرباعية + 9 أعمدة)
def generate_word_report(data, r_date):
    doc = Document()
    section = doc.sections[0]
    section.orientation = 1 
    section.page_width, section.page_height = section.page_height, section.page_width
    
    header_text = ["وزارة الشباب والرياضة", "مديرية الشباب والرياضة لولاية قالمة", "ديوان مؤسسات الشباب لولاية قالمة", "بيت الشباب محمدي يوسف قالمة"]
    for line in header_text:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line); run.bold = True; run.font.size = Pt(14)
        p.paragraph_format.space_after = Pt(0)

    doc.add_paragraph(f"\nسجل الحجوزات اليومي بتاريخ: {r_date}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    table = doc.add_table(rows=1, cols=9); table.style = 'Table Grid'; table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers = ["الملاحظات", "المهنة", "عدد الليالي", "نوع ورقم بطاقة التعريف", "العنوان الشخصي", "تاريخ ومكان الازدياد", "الاسم واللقب", "رقم الغرفة", "رقم"]
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
        table.rows[0].cells[i].paragraphs[0].runs[0].bold = True

    for idx, row in enumerate(data, 1):
        cells = table.add_row().cells
        cells[8].text, cells[7].text, cells[6].text = str(idx), str(row[7]), str(row[1])
        cells[5].text = f"{row[2]} بـ {row[3]}"
        cells[4].text = str(row[16]) if row[16] else "قالمة"
        cells[3].text = f"{row[4]} {row[5]}"
        cells[2].text, cells[1].text, cells[0].text = "1", str(row[15]) if row[15] else "/", ""
        for c in cells: c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    target = io.BytesIO(); doc.save(target)
    return target.getvalue()

# واجهة البرنامج
st.markdown('<div class="main-title">🏢 نظام إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)

# بيانات الأجنحة والغرف
wings_data = {
    "جناح ذكور 👨": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد 01": 4, "مرقد 02": 4},
    "جناح إناث 👩": {"غرفة 06": 6, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "غرفة 10": 6, "مرقد 01": 4, "مرقد 02": 4}
}

tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 التقارير والوارد"])

# التبويب 1: الحجز
with tabs[0]:
    st.markdown('<div class="section-box"><h4>📝 تسجيل نزيل جديد</h4></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("👤 الاسم واللقب"); bday = st.date_input("📅 تاريخ الميلاد", date(2000, 1, 1))
        bplace = st.text_input("📍 مكان الميلاد"); addr = st.text_input("🏠 العنوان الشخصي")
    with c2:
        id_t = st.selectbox("📄 الوثيقة", ["بطاقة تعريف", "جواز سفر"]); id_n = st.text_input("🪪 رقم الوثيقة")
        job = st.text_input("💼 المهنة"); ph = st.text_input("📞 الهاتف"); w_sel = st.selectbox("🏢 الجناح", list(wings_data.keys()))
    
    r_sel = st.selectbox("🚪 الغرفة", list(wings_data[w_sel].keys()))
    b_sel = st.radio("🛏️ السرير", [str(i) for i in range(1, wings_data[w_sel][r_sel]+1)], horizontal=True)

    if st.button("💾 حفظ الحجز", type="primary"):
        if name and id_n:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO current_guests (name, birth_date, birth_place, id_type, id_card, wing, room, bed, check_in, job, address, phone) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                             (name, str(bday), bplace, id_t, id_n, w_sel, r_sel, b_sel, str(date.today()), job, addr, ph))
            st.success("✅ تم الحفظ!"); st.rerun()

# التبويب 2: حالة الغرف (الذي سألت عنه)
with tabs[1]:
    st.markdown('<div class="section-box"><h4>📊 توزيع الأسرة والنزلاء</h4></div>', unsafe_allow_html=True)
    with sqlite3.connect(DB_FILE) as conn:
        booked = pd.read_sql_query("SELECT room, bed, name FROM current_guests", conn)
    
    for wing, rooms in wings_data.items():
        st.subheader(wing)
        cols = st.columns(4)
        for i, (room, count) in enumerate(rooms.items()):
            with cols[i % 4]:
                st.write(f"**{room}**")
                for b in range(1, count + 1):
                    is_full = booked[(booked['room'] == room) & (booked['bed'] == str(b))]
                    bg = "#e74c3c" if not is_full.empty else "#2ecc71"
                    title = is_full['name'].values[0] if not is_full.empty else "شاغر"
                    st.markdown(f'<div class="bed-box" style="background:{bg};" title="{title}">{b}</div>', unsafe_allow_html=True)

# التبويب 3: التقارير
with tabs[2]:
    st.markdown('<div class="section-box"><h4>📄 استخراج سجل الوارد (Word)</h4></div>', unsafe_allow_html=True)
    d_rep = st.date_input("التاريخ", date.today())
    if st.button("📥 تحميل ملف الوورد"):
        with sqlite3.connect(DB_FILE) as conn:
            data = conn.execute("SELECT * FROM current_guests WHERE check_in = ?", (str(d_rep),)).fetchall()
        if data:
            st.download_button("📁 اضغط للتحميل", generate_word_report(data, d_rep), f"سجل_{d_rep}.docx")
        else: st.warning("لا توجد بيانات")

st.markdown(f'<div class="developer-footer">Developer ®ridha_merzoug® [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
