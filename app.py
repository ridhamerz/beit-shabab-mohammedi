import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import io

# ────────────────────────────────────────────────
#                إعداد الصفحة + CSS الملكي
# ────────────────────────────────────────────────
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', 'Tahoma', sans-serif; direction: RTL; text-align: right; }
    
    .official-header { text-align: center; color: #1e3c72; font-size: 0.85rem; font-weight: bold; line-height: 1.4; margin-bottom: 5px; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 12px; border-radius: 10px; text-align: center; margin-bottom: 20px; font-size: 1.35rem; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .stat-container { display: flex; gap: 10px; margin-bottom: 20px; justify-content: space-between; }
    .stat-card { flex: 1; padding: 15px; border-radius: 10px; text-align: center; color: white; box-shadow: 0 4px 8px rgba(0,0,0,0.15); }
    .stat-val { font-size: 1.7rem; font-weight: bold; display: block; }
    .section-box { background: #ffffff; padding: 1.5rem; border-radius: 10px; margin-bottom: 1.2rem; border-right: 5px solid #1e3c72; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .bed-box { display: inline-block; width: 35px; height: 35px; margin: 3px; border-radius: 5px; text-align: center; line-height: 35px; color: white; font-size: 0.85rem; font-weight: bold; }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 10px; border-radius: 8px; text-align: center; margin-top: 50px; font-size: 0.8rem; border: 1px solid #00d4ff; }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               إدارة البيانات والتصدير
# ────────────────────────────────────────────────
DB_FILE = 'hostel_guelma_v8_stable.db'

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

def generate_word_report(data, r_date):
    doc = Document()
    section = doc.sections[0]
    section.orientation = 1 
    section.page_width, section.page_height = section.page_height, section.page_width

    # الترويسة المطلوبة بالترتيب
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
    
    headers = ["الملاحظات", "المهنة", "عدد الليالي", "نوع ورقم بطاقة التعريف", "العنوان الشخصي", "تاريخ ومكان الازدياد", "الاسم واللقب", "رقم الغرفة", "رقم"]
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        run = hdr_cells[i].paragraphs[0].runs[0]
        run.bold = True
        hdr_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    for idx, row in enumerate(data, 1):
        row_cells = table.add_row().cells
        row_cells[8].text = str(idx)
        row_cells[7].text = str(row[7]) # الغرفة
        row_cells[6].text = str(row[1]) # الاسم
        row_cells[5].text = f"{row[2]} بـ {row[3]}" # تاريخ ومكان الميلاد
        row_cells[4].text = str(row[16]) if row[16] else "قالمة" # العنوان
        row_cells[3].text = f"{row[4]} {row[5]}" # نوع ورقم البطاقة
        row_cells[2].text = "1" 
        row_cells[1].text = str(row[15]) if row[15] else "/" # المهنة
        row_cells[0].text = "" # ملاحظات
        for cell in row_cells: cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    target = io.BytesIO()
    doc.save(target)
    return target.getvalue()

# ────────────────────────────────────────────────
#               الواجهة الرئيسية
# ────────────────────────────────────────────────
st.markdown('<div class="official-header">🇩🇿 وزارة الشباب والرياضة | مديرية الشباب والرياضة | ديوان مؤسسات الشباب</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🏢 نظام إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)

with sqlite3.connect(DB_FILE) as conn:
    g_count = conn.execute("SELECT COUNT(*) FROM current_guests").fetchone()[0]
    b_avail = 76 - g_count

st.markdown(f"""
    <div class="stat-container">
        <div class="stat-card" style="background:#1e3c72"><span class="stat-val">{g_count}</span><span>👥 مقيم حالياً</span></div>
        <div class="stat-card" style="background:#28a745"><span class="stat-val">{b_avail}</span><span>🛏️ أسرة شاغرة</span></div>
        <div class="stat-card" style="background:#f39c12"><span class="stat-val">متصل ✅</span><span>⭐ حالة النظام</span></div>
    </div>
""", unsafe_allow_html=True)

wings = {
    "جناح ذكور 👨": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد 01": 3, "مرقد 02": 4},
    "جناح إناث 👩": {"غرفة 06": 2, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد 01": 3, "مرقد 02": 4}
}

tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 التقارير والطباعة"])

# --- تبويب الحجز ---
with tabs[0]:
    if st.session_state.get('booking_success'):
        st.balloons()
        st.success(f"🎉 تم تسجيل النزيل **{st.session_state.last_guest}** بنجاح!")
        if st.button("➕ حجز جديد", type="primary", use_container_width=True):
            st.session_state.booking_success = False; st.rerun()
    else:
        st.markdown('<div class="section-box"><h4>📝 استمارة تسجيل نزيل</h4></div>', unsafe_allow_html=True)
        id_card_val = st.text_input("🪪 رقم بطاقة الهوية / جواز السفر")
        col1, col2 = st.columns(2)
        with col1:
            g_name = st.text_input("👤 الاسم واللقب")
            g_bday = st.date_input("📅 تاريخ الميلاد", value=date(2000, 1, 1))
            g_bplace = st.text_input("📍 مكان الميلاد")
            g_address = st.text_input("🏠 العنوان الشخصي")
        with col2:
            g_id_type = st.selectbox("📄 نوع الوثيقة", ["بطاقة تعريف وطنية", "جواز سفر", "رخصة سياقة"])
            g_job = st.text_input("💼 المهنة")
            g_phone = st.text_input("📞 رقم الهاتف")
            g_wing = st.selectbox("🏢 الجناح", list(wings.keys()))
        
        r_sel = st.selectbox("🚪 اختر الغرفة", list(wings[g_wing].keys()))
        # (هنا يوضع كود اختيار الأسرة كما في النسخة السابقة)
        # للتبسيط سأفترض اختيار السرير 1 برمجياً للتجربة:
        sel_bed = "سرير 1" 
        
        if st.button("💾 تأكيد وحفظ الحجز", use_container_width=True, type="primary"):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO current_guests (name, birth_date, birth_place, id_type, id_card, wing, room, bed, check_in, job, address) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                             (g_name, str(g_bday), g_bplace, g_id_type, id_card_val, g_wing, r_sel, sel_bed, str(date.today()), g_job, g_address))
            st.session_state.booking_success = True; st.session_state.last_guest = g_name; st.rerun()

# --- تبويب التقارير ---
with tabs[2]:
    st.markdown('<div class="section-box"><h4>📄 استخراج السجلات الرسمية (Word)</h4></div>', unsafe_allow_html=True)
    report_date = st.date_input("📅 اختر تاريخ اليوم المطلوب", date.today())
    if st.button("📝 توليد سجل الوارد اليومي", use_container_width=True):
        with sqlite3.connect(DB_FILE) as conn:
            data = conn.execute("SELECT * FROM current_guests WHERE check_in = ?", (str(report_date),)).fetchall()
        if data:
            file_bytes = generate_word_report(data, report_date)
            st.download_button("📥 تحميل ملف Word الجاهز", file_bytes, f"سجل_{report_date}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.warning("⚠️ لا توجد حجوزات في هذا التاريخ")

st.markdown(f'<div class="developer-footer">Developer <span style="color:#00d4ff;">®ridha_merzoug®</span> [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
