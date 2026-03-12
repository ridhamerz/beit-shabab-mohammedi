import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# ==================== 1. الإعدادات والأسعار ====================
MANAGER_PASSWORD = "1234"
RECEPTION_PASSWORD = "5678"
PRICE_PER_NIGHT = 400

st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide", page_icon="🏨")

# تنسيق CSS احترافي
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; }
    .stat-card { background: #ffffff; padding: 20px; border-radius: 15px; border-bottom: 6px solid #1e3c72; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .bed-box { display: inline-block; width: 45px; height: 35px; margin: 3px; border-radius: 6px; text-align: center; line-height: 35px; color: white; font-weight: bold; }
    .free { background-color: #28a745; }
    .occupied { background-color: #dc3545; }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 15px; border-radius: 12px; text-align: center; margin-top: 40px; }
    </style>
    """, unsafe_allow_html=True)

# ==================== 2. قاعدة البيانات ودوال الحفظ ====================
DB_FILE = "biet_chabab.db"

@st.cache_resource
def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT, birth_date DATE, birth_place TEXT, address TEXT,
        id_type TEXT, id_number TEXT, nationality TEXT, wing TEXT, 
        room TEXT, bed TEXT, check_in DATE, check_out DATE, legal_status TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS rooms_config (wing TEXT, room TEXT, beds_count INTEGER, PRIMARY KEY (wing, room))''')
    if conn.execute("SELECT COUNT(*) FROM rooms_config").fetchone()[0] == 0:
        default_rooms = [
            ("جناح ذكور", "غرفة 01", 6), ("جناح ذكور", "غرفة 02", 6), ("جناح ذكور", "غرفة 03", 6),
            ("جناح إناث", "غرفة 06", 2), ("جناح إناث", "غرفة 07", 6), ("جناح إناث", "مرقد إناث 01", 3)
        ]
        conn.executemany("INSERT OR IGNORE INTO rooms_config VALUES (?,?,?)", default_rooms)
    conn.commit()

init_db()

def load_wings_config():
    df = pd.read_sql("SELECT * FROM rooms_config", get_db())
    return {w: dict(zip(df[df['wing'] == w]['room'], df[df['wing'] == w]['beds_count'])) for w in df['wing'].unique()}

def calculate_nights(d1, d2):
    return max((pd.to_datetime(d2).date() - pd.to_datetime(d1).date()).days, 1)

# ==================== 3. دوال تصدير الوثائق (طلبك الأخير) ====================

def add_header_footer(doc):
    section = doc.sections[0]
    header = section.header
    htable = header.add_table(1, 2, width=Inches(6.5))
    # اليسار: نصوص رسمية
    cell_l = htable.rows[0].cells[0]
    cell_l.text = "مديرية الشباب والرياضة لولاية قالمة\nديوان مؤسسات الشباب قالمة\nبيت الشباب محمدي يوسف"
    cell_l.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
    # اليمين: شعار
    cell_r = htable.rows[0].cells[1]
    cell_r.text = "[الشعار الرسمي]"
    cell_r.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    # التذييل
    footer = section.footer
    footer.paragraphs[0].text = "عون الاستقبال: ............................          الحارس الليلي: ............................"
    footer.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

# (هنا تضاف بقية دوال التوليد generate_report_table و generate_police_form كما في الرد السابق)

# ==================== 4. منطق التطبيق والواجهة ====================

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'review_mode' not in st.session_state: st.session_state.review_mode = False

if not st.session_state.authenticated:
    st.markdown('<div class="main-title">🏨 إدارة بيت الشباب محمدي يوسف</div>', unsafe_allow_html=True)
    role = st.selectbox("🔑 الصفة", ["مدير", "عون استقبال"])
    pwd = st.text_input("🔒 كلمة السر", type="password")
    if st.button("🚀 دخول"):
        if (role == "مدير" and pwd == MANAGER_PASSWORD) or (role == "عون استقبال" and pwd == RECEPTION_PASSWORD):
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

tabs = st.tabs(["➕ حجز جديد", "🛌 حالة الغرف", "📋 السجل", "📄 تصدير Word", "💰 الحسابات"])
wings = load_wings_config()
today = date.today()

# --- 1. حجز جديد (مع مراجعة ومنطق قاصر) ---
with tabs[0]:
    if not st.session_state.review_mode:
        with st.form("booking_form"):
            st.markdown("### 👤 بيانات النزيل")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("الاسم واللقب *")
                c_b1, c_b2 = st.columns(2)
                b_date = c_b1.date_input("تاريخ الازدياد", date(2000,1,1))
                b_place = c_b2.text_input("مكان الازدياد")
                nationality = st.selectbox("الجنسية", ["جزائرية", "أخرى"])
            with col2:
                id_val = st.text_input("رقم البطاقة *")
                wing_sel = st.selectbox("الجناح", list(wings.keys()))
                room_sel = st.selectbox("الغرفة", list(wings[wing_sel].keys()))
                bed_sel = st.selectbox("السرير", [f"سرير {i+1}" for i in range(wings[wing_sel][room_sel])])
                d_in = st.date_input("الدخول", today)
                d_out = st.date_input("الخروج", today + timedelta(days=1))
            
            # منطق القاصر
            age = (today - b_date).days // 365
            legal = "بالغ"
            if age < 18:
                st.warning(f"⚠️ النزيل قاصر ({age} سنة)")
                legal = st.selectbox("الوثيقة القانونية", ["تصريح أبوي", "حضور الولي", "أمر بمهمة"])

            if st.form_submit_button("🔍 مراجعة الحجز"):
                st.session_state.temp_data = {
                    "full_name": name, "birth_date": b_date, "birth_place": b_place,
                    "id_number": id_val, "wing": wing_sel, "room": room_sel, "bed": bed_sel,
                    "check_in": d_in, "check_out": d_out, "legal_status": legal, "nationality": nationality
                }
                st.session_state.review_mode = True
                st.rerun()
    else:
        st.subheader("🧐 مراجعة البيانات قبل الحفظ")
        st.json(st.session_state.temp_data)
        if st.button("💾 تأكيد وحفظ"):
            conn = get_db()
            pd.DataFrame([st.session_state.temp_data]).to_sql("bookings", conn, if_exists="append", index=False)
            st.success("تم الحجز!")
            st.session_state.review_mode = False
            st.rerun()
        if st.button("🔙 تعديل"):
            st.session_state.review_mode = False
            st.rerun()

# (بقية التبويبات تعمل كما في السابق)
