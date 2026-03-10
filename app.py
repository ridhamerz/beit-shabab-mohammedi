import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import io

# ────────────────────────────────────────────────
#                إعداد الصفحة والـ CSS (تنسيقاتك الأصلية)
# ────────────────────────────────────────────────
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', 'Tahoma', sans-serif; direction: RTL; text-align: right; }
    .main-title { 
        background: linear-gradient(90deg, #1e3c72, #2a5298); 
        color: white; padding: 20px; border-radius: 15px; 
        text-align: center; margin-bottom: 25px; 
        font-size: 1.6rem; font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .bed-box { 
        display: inline-block; width: 42px; height: 38px; margin: 4px; 
        border-radius: 6px; text-align: center; line-height: 38px; 
        color: white; font-size: 0.85rem; font-weight: bold; 
    }
    .free { background-color: #28a745; border-bottom: 3px solid #1e7e34; }
    .occupied { background-color: #dc3545; border-bottom: 3px solid #a71d2a; }
    .stat-card { 
        background: white; padding: 20px; border-radius: 12px; 
        border-right: 6px solid #1e3c72; text-align: center; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); 
    }
    .developer-footer { 
        background: #1e3c72; color: #ffffff; padding: 8px; 
        border-radius: 10px; text-align: center; margin-top: 50px; 
        font-size: 0.8rem; border: 1px solid #00d4ff;
    }
    .section-box {
        background: #f8f9fa; padding: 1rem; border-radius: 8px; 
        margin-bottom: 1.2rem; border-right: 4px solid;
    }
    .minor-box {
        background: #fff3cd !important; border-color: #ffc107 !important;
        padding: 1rem; border-radius: 8px; margin: 1rem 0;
    }
    .success-box {
        background: #d4edda; color: #155724; padding: 1.5rem; 
        border-radius: 10px; border: 1px solid #c3e6cb; 
        margin: 1.5rem 0; text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               قاعدة البيانات (تعديلك)
# ────────────────────────────────────────────────
DB_FILE = 'youth_hostel.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS current_guests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, birth_date TEXT, birth_place TEXT, address TEXT,
        id_card TEXT UNIQUE, wing TEXT, room TEXT, bed TEXT,
        check_in TEXT, check_out TEXT, status TEXT DEFAULT 'مقيم',
        is_minor TEXT DEFAULT 'لا', guardian_name TEXT, guardian_permission TEXT,
        job TEXT, phone TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# ────────────────────────────────────────────────
#               دالة تصدير الوورد الرسمية (الجديدة)
# ────────────────────────────────────────────────
def generate_word_report(data, r_date):
    doc = Document()
    section = doc.sections[0]
    section.orientation = 1 # وضعية العرض Landscape
    section.page_width, section.page_height = section.page_height, section.page_width

    # الترويسة الرسمية لولاية قالمة
    header_text = [
        "وزارة الشباب والرياضة",
        "مديرية الشباب والرياضة لولاية قالمة",
        "ديوان مؤسسات الشباب لولاية قالمة",
        "بيت الشباب محمدي يوسف قالمة"
    ]
    for line in header_text:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line); run.bold = True; run.font.size = Pt(13)
        p.paragraph_format.space_after = Pt(0)

    doc.add_paragraph(f"\nسجل الحجوزات اليومي بتاريخ: {r_date}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # بناء الجدول (9 أعمدة كما طلبت سابقاً)
    table = doc.add_table(rows=1, cols=9); table.style = 'Table Grid'; table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["الملاحظات", "المهنة", "عدد الليالي", "نوع ورقم الوثيقة", "العنوان الشخصي", "تاريخ ومكان الازدياد", "الاسم واللقب", "رقم الغرفة", "رقم"]
    
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
        table.rows[0].cells[i].paragraphs[0].runs[0].bold = True

    for idx, row in enumerate(data, 1):
        cells = table.add_row().cells
        cells[8].text = str(idx)             # المسلسل
        cells[7].text = str(row[7])          # رقم الغرفة
        cells[6].text = str(row[1])          # الاسم
        cells[5].text = f"{row[2]} بـ {row[3]}" # الميلاد والمكان
        cells[4].text = str(row[4])          # العنوان
        cells[3].text = str(row[5])          # رقم الهوية
        cells[2].text = "1"                  # الليالي
        cells[1].text = str(row[15]) if row[15] else "/" # المهنة
        cells[0].text = str(row[13]) if row[12]=='نعم' else "" # ملاحظات ولي الأمر
        for c in cells: c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    target = io.BytesIO(); doc.save(target)
    return target.getvalue()

# ────────────────────────────────────────────────
#               بقية الدوال والمنطق (كود رضا المعدل)
# ────────────────────────────────────────────────
def is_bed_occupied(wing, room, bed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM current_guests WHERE wing=? AND room=? AND bed=? AND status='مقيم'", (wing, room, bed))
    res = c.fetchone(); conn.close(); return res is not None

def add_guest(name, b_date, b_place, addr, id_c, wing, room, bed, c_in, c_out, g_name, g_perm, job, phone):
    age = (date.today() - b_date).days // 365
    is_m = 'نعم' if age < 18 else 'لا'
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("""INSERT INTO current_guests (name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, is_minor, guardian_name, guardian_permission, job, phone)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
              (name, str(b_date), b_place, addr, id_c, wing, room, bed, str(c_in), str(c_out), is_m, g_name, g_perm, job, phone))
    conn.commit(); conn.close()

# تسجيل الدخول (نفس منطقك)
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
    role = st.selectbox("الصفة", ["مدير", "عون استقبال"])
    pwd = st.text_input("كلمة السر", type="password")
    if st.button("دخول آمن", use_container_width=True):
        if pwd == ("1234" if role=="مدير" else "5678"):
            st.session_state.authenticated = True; st.session_state.user_role = role; st.rerun()
    st.stop()

st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجل والطباعة"])

# --- تبويب الحجز (تنسيق رضا الكامل) ---
with tabs[0]:
    if st.session_state.get('booking_success'):
        st.markdown('<div class="success-box"><h3>🎉 تم التسجيل بنجاح!</h3></div>', unsafe_allow_html=True)
        if st.button("➕ حجز نزيل جديد"): st.session_state.booking_success = False; st.rerun()
    else:
        with st.form("booking_form"):
            st.markdown('<div class="section-box" style="border-color:#1e3c72;"><h4>👤 معلومات النزيل</h4></div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("الاسم واللقب")
                b_date = st.date_input("تاريخ الميلاد", date(2000,1,1))
                b_place = st.text_input("مكان الميلاد")
                addr = st.text_input("العنوان")
            with col2:
                id_c = st.text_input("رقم الوثيقة")
                job = st.text_input("المهنة")
                phone = st.text_input("الهاتف")
                wing = st.selectbox("الجناح", ["جناح ذكور", "جناح إناث"])
            
            room = st.selectbox("الغرفة", ["غرفة 01", "غرفة 02", "غرفة 03", "غرفة 04", "غرفة 05"])
            bed = st.radio("السرير", ["سرير 1", "سرير 2", "سرير 3", "سرير 4"], horizontal=True)
            
            # قسم القاصرين
            age = (date.today() - b_date).days // 365
            g_name = g_perm = ""
            if age < 18:
                st.warning(f"⚠️ النزيل قاصر ({age} سنة)")
                g_name = st.text_input("اسم ولي الأمر")
                g_perm = st.selectbox("نوع التصريح", ["موافقة خطية", "حضور شخصي"])

            if st.form_submit_button("💾 تأكيد الحجز"):
                add_guest(name, b_date, b_place, addr, id_c, wing, room, bed, date.today(), date.today()+timedelta(days=1), g_name, g_perm, job, phone)
                st.session_state.booking_success = True; st.rerun()

# --- تبويب حالة الغرف (تنسيق رضا) ---
with tabs[1]:
    st.subheader("📊 حالة الأجنحة والأسرة")
    wings_map = {"جناح ذكور": 5, "جناح إناث": 5}
    for w_name in wings_map:
        st.write(f"**{w_name}**")
        cols = st.columns(5)
        for i in range(1, 6):
            status = "occupied" if is_bed_occupied(w_name, f"غرفة {i:02d}", "سرير 1") else "free"
            cols[i-1].markdown(f'<div class="bed-box {status}">غ {i}</div>', unsafe_allow_html=True)

# --- تبويب الطباعة (الجديد كلياً بـ Word) ---
with tabs[2]:
    st.markdown('<div class="section-box" style="border-color:#28a745;"><h4>📋 استخراج السجل الرسمي</h4></div>', unsafe_allow_html=True)
    target_date = st.date_input("اختر تاريخ السجل", date.today())
    if st.button("📄 توليد ملف Word للطباعة"):
        with sqlite3.connect(DB_FILE) as conn:
            data = conn.execute("SELECT * FROM current_guests WHERE check_in = ?", (str(target_date),)).fetchall()
        if data:
            doc_bytes = generate_word_report(data, target_date)
            st.download_button("📥 تحميل سجل الوارد الجاهز", doc_bytes, f"سجل_{target_date}.docx")
        else: st.warning("لا توجد بيانات لهذا التاريخ")

st.markdown('<div class="developer-footer">Developer ®ridha_merzoug® [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
