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
#                1. إعداد الصفحة والـ CSS الملكي
# ────────────────────────────────────────────────
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { 
        background: linear-gradient(90deg, #1e3c72, #2a5298); 
        color: white; padding: 20px; border-radius: 15px; 
        text-align: center; margin-bottom: 25px; font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .section-box {
        background: #ffffff; padding: 20px; border-radius: 12px; 
        border-right: 6px solid #1e3c72; margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .bed-box { 
        display: inline-block; width: 45px; height: 40px; margin: 5px; 
        border-radius: 8px; text-align: center; line-height: 40px; 
        color: white; font-weight: bold; font-size: 0.9rem;
    }
    .free { background-color: #28a745; border-bottom: 3px solid #1e7e34; }
    .occupied { background-color: #dc3545; border-bottom: 3px solid #a71d2a; }
    .developer-footer { 
        background: #1e3c72; color: white; padding: 10px; 
        border-radius: 10px; text-align: center; margin-top: 50px; 
        font-size: 0.8rem; border: 1px solid #00d4ff;
    }
    .success-box { background: #d4edda; color: #155724; padding: 15px; border-radius: 10px; text-align: center; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               2. إدارة قاعدة البيانات
# ────────────────────────────────────────────────
DB_FILE = 'youth_hostel_v10.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS current_guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, birth_date TEXT, birth_place TEXT, address TEXT,
            id_card TEXT, wing TEXT, room TEXT, bed TEXT,
            check_in TEXT, check_out TEXT, status TEXT DEFAULT 'مقيم',
            job TEXT, phone TEXT, notes TEXT, nights INTEGER
        )''')
        conn.commit()

init_db()

# ────────────────────────────────────────────────
#               3. الدوال المساعدة (الذكاء البرمجي)
# ────────────────────────────────────────────────
def get_old_guest(id_num):
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT name, birth_date, birth_place, address, job, phone FROM current_guests WHERE id_card=? ORDER BY id DESC LIMIT 1", (id_num,)).fetchone()

def get_vacant_beds(wing, room):
    all_beds = [str(i) for i in range(1, 7)] # افتراض 6 أسرة لكل غرفة
    with sqlite3.connect(DB_FILE) as conn:
        occupied = conn.execute("SELECT bed FROM current_guests WHERE wing=? AND room=? AND status='مقيم'", (wing, room)).fetchall()
        occupied_list = [str(row[0]) for row in occupied]
    return [b for b in all_beds if b not in occupied_list]

def generate_word_report(data, r_date):
    doc = Document()
    section = doc.sections[0]
    section.orientation = 1
    section.page_width, section.page_height = section.page_height, section.page_width
    for line in ["وزارة الشباب والرياضة", "مديرية الشباب والرياضة لولاية قالمة", "ديوان مؤسسات الشباب لولاية قالمة", "بيت الشباب محمدي يوسف قالمة"]:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line); run.bold = True; run.font.size = Pt(14)
    doc.add_paragraph(f"\nسجل الحجوزات اليومي بتاريخ: {r_date}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    table = doc.add_table(rows=1, cols=9); table.style = 'Table Grid'
    headers = ["الملاحظات", "المهنة", "عدد الليالي", "رقم الوثيقة", "العنوان", "الميلاد", "الاسم واللقب", "الغرفة", "رقم"]
    for i, h in enumerate(headers): table.rows[0].cells[i].text = h
    for idx, row in enumerate(data, 1):
        cells = table.add_row().cells
        cells[8].text, cells[7].text, cells[6].text = str(idx), str(row[7]), str(row[1])
        cells[5].text, cells[4].text, cells[3].text = f"{row[2]}", str(row[4]), str(row[5])
        cells[2].text, cells[1].text, cells[0].text = str(row[15]), str(row[12]), str(row[14])
    target = io.BytesIO(); doc.save(target); return target.getvalue()

# ────────────────────────────────────────────────
#               4. نظام الدخول الصارم
# ────────────────────────────────────────────────
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div class="main-title">🔐 تسجيل الدخول للنظام</div>', unsafe_allow_html=True)
    with st.container():
        role = st.selectbox("👤 اختر الصفة:", ["مدير", "عون استقبال"])
        pwd = st.text_input("🔑 كلمة السر:", type="password")
        if st.button("دخول", use_container_width=True):
            if (role == "مدير" and pwd == "1234") or (role == "عون استقبال" and pwd == "5678"):
                st.session_state.auth = True; st.session_state.role = role; st.rerun()
            else: st.error("❌ كلمة السر خاطئة")
    st.stop()

# ────────────────────────────────────────────────
#               5. الواجهة الرئيسية
# ────────────────────────────────────────────────
st.markdown('<div class="main-title">🏢 نظام إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)
st.sidebar.success(f"مرحباً: {st.session_state.role}")
if st.sidebar.button("تسجيل الخروج"): st.session_state.auth = False; st.rerun()

tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجلات"])

# --- تبويب الحجز (الذكاء الاصطناعي والتوفر) ---
with tabs[0]:
    st.markdown('<div class="section-box"><h4>🔍 البحث السريع والتسجيل</h4></div>', unsafe_allow_html=True)
    search_id = st.text_input("🪪 أدخل رقم الهوية (للملء التلقائي):", placeholder="اكتب رقم بطاقة التعريف هنا...")
    
    old_guest = get_old_guest(search_id) if search_id else None
    if old_guest: st.info(f"✅ تم العثور على بيانات: {old_guest[0]}")

    with st.form("booking_v10"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("👤 الاسم واللقب الكامل", value=old_guest[0] if old_guest else "")
            bday = st.date_input("📅 تاريخ الميلاد", value=pd.to_datetime(old_guest[1]) if old_guest else date(2000,1,1))
            bplace = st.text_input("📍 مكان الميلاد", value=old_guest[2] if old_guest else "")
            addr = st.text_input("🏠 العنوان الشخصي", value=old_guest[3] if old_guest else "")
            job = st.text_input("💼 المهنة", value=old_guest[4] if old_guest else "")
        with c2:
            id_num = st.text_input("🪪 رقم الوثيقة", value=search_id if search_id else "")
            phone = st.text_input("📞 رقم الهاتف", value=old_guest[5] if old_guest else "")
            nights = st.number_input("🌙 عدد الليالي", min_value=1, value=1)
            wing = st.selectbox("🏢 الجناح", ["جناح ذكور 👨", "جناح إناث 👩"])
            room = st.selectbox("🚪 رقم الغرفة", [f"غرفة {i:02d}" for i in range(1, 11)])

        # ميزة الأسرة الشاغرة فقط
        vacant_beds = get_vacant_beds(wing, room)
        if vacant_beds:
            bed = st.radio("🛏️ الأسرة الشاغرة (اختر واحداً):", vacant_beds, horizontal=True)
            notes = st.text_area("📝 ملاحظات إضافية")
            submit = st.form_submit_button("💾 تأكيد الحجز", type="primary", use_container_width=True)
        else:
            st.error("⚠️ هذه الغرفة ممتلئة حالياً!")
            submit = False

        if submit:
            out_date = date.today() + timedelta(days=nights)
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("""INSERT INTO current_guests 
                (name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, job, phone, notes, nights) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (name, str(bday), bplace, addr, id_num, wing, room, bed, str(date.today()), str(out_date), job, phone, notes, nights))
            st.success("🎉 تم تسجيل الحجز بنجاح!"); st.balloons()

# --- تبويب حالة الغرف (بصري) ---
with tabs[1]:
    st.markdown('<div class="section-box"><h4>📊 خريطة الأسرة الحالية</h4></div>', unsafe_allow_html=True)
    with sqlite3.connect(DB_FILE) as conn:
        booked = pd.read_sql_query("SELECT wing, room, bed, name FROM current_guests WHERE status='مقيم'", conn)
    
    for w in ["جناح ذكور 👨", "جناح إناث 👩"]:
        st.subheader(w)
        cols = st.columns(5)
        for i in range(1, 11):
            r_name = f"غرفة {i:02d}"
            with cols[(i-1)%5]:
                st.write(f"**{r_name}**")
                for b in range(1, 7):
                    is_occ = booked[(booked['wing']==w) & (booked['room']==r_name) & (booked['bed']==str(b))]
                    color = "occupied" if not is_occ.empty else "free"
                    st.markdown(f'<div class="bed-box {color}" title="{is_occ["name"].iloc[0] if not is_occ.empty else "شاغر"}">{b}</div>', unsafe_allow_html=True)

# --- تبويب السجلات والطباعة ---
with tabs[2]:
    st.markdown('<div class="section-box"><h4>📋 استخراج سجل الوارد (Word)</h4></div>', unsafe_allow_html=True)
    rep_date = st.date_input("اختر التاريخ:", date.today())
    if st.button("📥 تحميل ملف الوورد"):
        with sqlite3.connect(DB_FILE) as conn:
            data = conn.execute("SELECT * FROM current_guests WHERE check_in=?", (str(rep_date),)).fetchall()
        if data:
            st.download_button("📁 اضغط هنا للتحميل", generate_word_report(data, rep_date), f"سجل_{rep_date}.docx")
        else: st.warning("لا توجد بيانات لهذا التاريخ")

# الفوتر
st.markdown('<div class="developer-footer">Developer ®ridha_merzoug® [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
