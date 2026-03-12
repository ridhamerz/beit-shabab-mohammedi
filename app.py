import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
import io
from streamlit_gsheets import GSheetsConnection

# ==================== 1. الإعدادات والأسعار ====================
MANAGER_PASSWORD = "1234"
RECEPTION_PASSWORD = "5678"
PRICE_PER_NIGHT = 400
SHEET_URL = "https://docs.google.com/spreadsheets/d/1IfMFMNT2UYF7OzQXU5acDJ06GtxmOFJ1d8oQYOWKwUs/edit?usp=sharing"

st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide", page_icon="🏨")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; }
    .bed-box { display: inline-block; width: 50px; height: 40px; margin: 5px; border-radius: 8px; text-align: center; line-height: 40px; color: white; font-weight: bold; font-size: 0.8rem; }
    .free { background-color: #28a745; border-bottom: 4px solid #1e7e34; }
    .occupied { background-color: #dc3545; border-bottom: 4px solid #bd2130; }
    .wing-header { background: #f8f9fa; padding: 10px; border-right: 5px solid #1e3c72; margin: 15px 0; font-weight: bold; }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 15px; border-radius: 12px; text-align: center; margin-top: 40px; }
    </style>
    """, unsafe_allow_html=True)

# ==================== 2. قاعدة البيانات والربط ====================
DB_FILE = "biet_chabab.db"

@st.cache_resource
def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, birth_date DATE, 
        birth_place TEXT, address TEXT, id_number TEXT, wing TEXT, 
        room TEXT, bed TEXT, check_in DATE, check_out DATE, legal_status TEXT
    )''')
    # إعداد الغرف الافتراضي
    conn.execute('''CREATE TABLE IF NOT EXISTS rooms_config (wing TEXT, room TEXT, beds_count INTEGER, PRIMARY KEY (wing, room))''')
    if conn.execute("SELECT COUNT(*) FROM rooms_config").fetchone()[0] == 0:
        rooms = [("جناح ذكور", f"غرفة {i:02d}", 6) for i in range(1, 6)] + \
                [("جناح إناث", f"غرفة {i:02d}", 6) for i in range(6, 10)]
        conn.executemany("INSERT INTO rooms_config VALUES (?,?,?)", rooms)
    conn.commit()

init_db()
conn_gsheets = st.connection("gsheets", type=GSheetsConnection)

def calculate_nights(d1, d2):
    return max((pd.to_datetime(d2).date() - pd.to_datetime(d1).date()).days, 1)

# ==================== 3. واجهة المستخدم والتبويبات ====================

if 'authenticated' not in st.session_state: st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<div class="main-title">🏨 إدارة بيت الشباب محمدي يوسف</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        role = st.selectbox("🔑 الدخول كـ", ["مدير", "عون استقبال"])
        pwd = st.text_input("🔒 كلمة السر", type="password")
        if st.button("🚀 دخول", use_container_width=True):
            if (role == "مدير" and pwd == MANAGER_PASSWORD) or (role == "عون استقبال" and pwd == RECEPTION_PASSWORD):
                st.session_state.authenticated = True
                st.rerun()
    st.stop()

tabs = st.tabs(["➕ حجز جديد", "🛌 حالة الغرف", "📋 السجل", "📄 Word", "💰 الحسابات"])
df_bookings = pd.read_sql("SELECT * FROM bookings", get_db())
df_rooms = pd.read_sql("SELECT * FROM rooms_config", get_db())

# --- 1. حجز جديد ---
with tabs[0]:
    with st.form("booking"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم واللقب *")
            b_date = st.date_input("تاريخ الازدياد", date(2000,1,1))
            wing = st.selectbox("الجناح", df_rooms['wing'].unique())
        with c2:
            id_num = st.text_input("رقم الهوية *")
            room = st.selectbox("الغرفة", df_rooms[df_rooms['wing'] == wing]['room'])
            d_in = st.date_input("الدخول", date.today())
            d_out = st.date_input("الخروج", date.today() + timedelta(days=1))
        
        if st.form_submit_button("✅ حفظ الحجز"):
            conn = get_db()
            conn.execute("INSERT INTO bookings (full_name, id_number, wing, room, check_in, check_out, birth_date) VALUES (?,?,?,?,?,?,?)",
                         (name, id_num, wing, room, d_in, d_out, b_date))
            conn.commit()
            st.success("تم الحفظ!")
            st.rerun()

# --- 2. حالة الغرف (التبويب الذي سألت عنه) ---
with tabs[1]:
    st.subheader("🛌 توزيع الأسرّة الحالي")
    today = date.today()
    
    for wing_name in df_rooms['wing'].unique():
        st.markdown(f'<div class="wing-header">📍 {wing_name}</div>', unsafe_allow_html=True)
        wing_rooms = df_rooms[df_rooms['wing'] == wing_name]
        
        for _, r_row in wing_rooms.iterrows():
            with st.expander(f"🚪 {r_row['room']} ({r_row['beds_count']} أسرّة)"):
                cols = st.columns(r_row['beds_count'])
                for i in range(r_row['beds_count']):
                    bed_label = f"س{i+1}"
                    # التحقق إذا كان السرير محجوز اليوم
                    is_occ = df_bookings[
                        (df_bookings['room'] == r_row['room']) & 
                        (pd.to_datetime(df_bookings['check_in']).dt.date <= today) & 
                        (pd.to_datetime(df_bookings['check_out']).dt.date > today)
                    ]
                    # تبسيط العرض: إذا وجدنا أي حجز للغرفة نعتبر السرير الأول محجوز وهكذا
                    if i < len(is_occ):
                        cols[i].markdown(f'<div class="bed-box occupied" title="{is_occ.iloc[i]["full_name"]}">{bed_label}</div>', unsafe_allow_html=True)
                    else:
                        cols[i].markdown(f'<div class="bed-box free">{bed_label}</div>', unsafe_allow_html=True)

# --- التبويبات الأخرى (السجل، Word، الحسابات) تبقى كما هي في الكود السابق ---
with tabs[2]: st.dataframe(df_bookings)

st.markdown('<div class="developer-footer">🛠️ تطوير: <b>RIDHA MERZOUG</b> | 2026</div>', unsafe_allow_html=True)
