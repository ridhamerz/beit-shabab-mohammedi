import streamlit as st
import sqlite3
from datetime import date, timedelta

# ────────────────────────────────────────────────
#                إعداد الصفحة + CSS محسن للموبايل
# ────────────────────────────────────────────────
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    * { font-family: 'Tahoma', 'Arial', sans-serif; direction: RTL; text-align: right; }
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

    /* تحسين خاص للموبايل */
    @media (max-width: 768px) {
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stNumberInput > div > div > input,
        .stDateInput > div > div > input {
            font-size: 1.05rem !important;
            padding: 12px !important;
            height: auto !important;
        }
        .stMarkdown h4, .stMarkdown p, .stMarkdown strong {
            font-size: 1.1rem !important;
            margin-bottom: 8px !important;
        }
        .section-box {
            padding: 1.2rem !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               قاعدة البيانات + الدوال (نفس السابق)
# ────────────────────────────────────────────────
DB_FILE = 'youth_hostel.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS current_guests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        birth_date TEXT,
        birth_place TEXT,
        address TEXT,
        id_card TEXT UNIQUE,
        wing TEXT,
        room TEXT,
        bed TEXT,
        check_in TEXT,
        check_out TEXT,
        status TEXT DEFAULT 'مقيم',
        is_minor TEXT DEFAULT 'لا',
        guardian_name TEXT,
        guardian_permission TEXT,
        nationality TEXT,
        id_type TEXT,
        phone TEXT,
        purpose TEXT,
        purpose_other TEXT,
        companions_count INTEGER DEFAULT 0,
        companions_names TEXT,
        notes TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS archive (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, ... )''')  # نفس السابق
    conn.commit()
    conn.close()

init_db()

def calculate_age(birth_date):
    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age

def is_bed_occupied(wing, room, bed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM current_guests WHERE wing=? AND room=? AND bed=? AND status='مقيم'", (wing, room, bed))
    return c.fetchone() is not None

def add_guest(...):  # نفس الدالة السابقة (انسخها كاملة)

# ────────────────────────────────────────────────
#               الجلسة + التبويبات (نفس السابق)
# ────────────────────────────────────────────────
# ... (انسخ كود الـ session_state والـ login والـ tabs من الكود السابق)

# ────────────────────────────────────────────────
#               تبويب الحجز الجديد (محسن للموبايل)
# ────────────────────────────────────────────────
with tabs[0]:
    if st.session_state.booking_success:
        # نفس كود النجاح
        pass
    else:
        if st.session_state.form_error:
            st.error(st.session_state.form_error)

        with st.form("booking_form_final", clear_on_submit=False):
            st.markdown('<div class="section-box" style="border-color:#1e3c72;"><h4 style="margin:0; color:#1e3c72;">👤 معلومات النزيل الأساسية</h4></div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**الاسم واللقب** 👤")
                name = st.text_input("", value=st.session_state["form_name"], key="name_input", label_visibility="collapsed")
                
                st.markdown("**تاريخ الازدياد** 📅")
                birth_date = st.date_input("", value=st.session_state["form_birth_date"], min_value=date(1900,1,1), max_value=date.today(), key="birth_date_input", label_visibility="collapsed")
                
                st.markdown("**مكان الازدياد** 🏙️")
                birth_place = st.text_input("", value=st.session_state["form_birth_place"], key="birth_place_input", label_visibility="collapsed")
                
                st.markdown("**العنوان الكامل** 🏠")
                address = st.text_input("", value=st.session_state["form_address"], key="address_input", label_visibility="collapsed")

            with col2:
                st.markdown("**الجنسية** 🌍")
                # ... نفس الـ selectbox مع label_visibility="collapsed"
                # (طبّق نفس النمط على كل الحقول المتبقية)

            submitted = st.form_submit_button("💾 تأكيد الحجز وتسجيل النزيل", type="primary", use_container_width=True)

# تذييل
st.markdown('<div class="developer-footer">Developer ®ridha_merzoug® - 2026</div>', unsafe_allow_html=True)
