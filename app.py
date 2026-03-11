import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3
import os

# ==================== إعداد الصفحة والتنسيق ====================
st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; font-size: 1.3rem; font-weight: bold; }
    .bed-box { display: inline-block; width: 40px; height: 35px; margin: 3px; border-radius: 5px; text-align: center; line-height: 35px; color: white; font-size: 0.8rem; font-weight: bold; }
    .free { background-color: #28a745; }
    .occupied { background-color: #dc3545; }
    .wing-header { background-color: #f1f3f5; padding: 10px; border-radius: 8px; margin-top: 15px; border-right: 5px solid #1e3c72; font-weight: bold; }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 8px; border-radius: 10px; text-align: center; margin-top: 40px; font-size: 0.75rem; }
    </style>
    """, unsafe_allow_html=True)

# ==================== قاعدة البيانات SQLite ====================
DB_FILE = "biet_chabab.db"

def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_conn()
    # 1. جدول الحجوزات
    conn.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, الاسم_واللقب TEXT, تاريخ_الازدياد TEXT, العنوان TEXT, 
        رقم_البطاقة TEXT, المهنة TEXT, الجناح TEXT, الغرفة TEXT, السرير TEXT, تاريخ_الدخول DATE, تاريخ_الخروج DATE)''')
    
    # 2. جدول إعدادات الغرف
    conn.execute('CREATE TABLE IF NOT EXISTS rooms_config (wing TEXT, room TEXT, beds_count INTEGER, PRIMARY KEY (wing, room))')
    
    # 3. جدول المستخدمين (الجديد)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, full_name TEXT, role TEXT)''')
    
    # تعبئة الغرف والمستخدم الأول (المدير) عند أول تشغيل
    if conn.execute("SELECT COUNT(*) FROM rooms_config").fetchone()[0] == 0:
        initial_wings = {
            "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
            "جناح إناث": {"غرفة 06": 2, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد إناث 01": 3, "مرقد إناث 02": 4}
        }
        for w, rs in initial_wings.items():
            for r, b in rs.items():
                conn.execute("INSERT INTO rooms_config VALUES (?, ?, ?)", (w, r, b))
    
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ("admin", "1234", "المدير العام", "مدير"))
    
    conn.commit()
    conn.close()

init_db()

# ==================== دوال التحكم بالبيانات ====================
def add_user(uname, pwd, fname, role):
    try:
        conn = get_conn()
        conn.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (uname, pwd, fname, role))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def load_wings_config():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM rooms_config", conn)
    conn.close()
    config = {}
    for wing in df['wing'].unique():
        config[wing] = dict(df[df['wing'] == wing][['room', 'beds_count']].values)
    return config

def update_room_beds(wing, room, new_count):
    conn = get_conn()
    conn.execute("UPDATE rooms_config SET beds_count = ? WHERE wing = ? AND room = ?", (new_count, wing, room))
    conn.commit()
    conn.close()

# ==================== الحالة الأساسية والجلسة ====================
wings = load_wings_config()
total_beds = sum(sum(rooms.values()) for rooms in wings.values())

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'user_role' not in st.session_state: st.session_state.user_role = None

# ==================== بوابة الدخول ====================
if not st.session_state.authenticated:
    st.markdown('<div class="main-title">®® نظام بيت الشباب محمدي يوسف قالمة ®®</div>', unsafe_allow_html=True)
    st.subheader("🔐 تسجيل الدخول")
    uname = st.text_input("اسم المستخدم")
    pwd = st.text_input("كلمة السر", type="password")
    if st.button("دخول", use_container_width=True):
        conn = get_conn()
        user = conn.execute("SELECT role FROM users WHERE username=? AND password=?", (uname, pwd)).fetchone()
        conn.close()
        if user:
            st.session_state.authenticated = True
            st.session_state.user_role = user[0]
            st.rerun()
        else: st.error("❌ بيانات الدخول غير صحيحة")
    st.stop()

# ==================== الواجهة الرئيسية ====================
st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
if st.sidebar.button("🚪 خروج"):
    st.session_state.authenticated = False
    st.rerun()

# التبويبات حسب الصلاحية
tabs_list = ["➕ حجز جديد", "📊 عدد الغرف"]
if st.session_state.user_role == "مدير":
    tabs_list += ["📋 السجل العام", "📈 الإحصائيات", "⚙️ الإعدادات"]
tabs = st.tabs(tabs_list)

today = date.today()

# --- تبويب حجز جديد وعدد الغرف (بنفس منطق كودك الأصلي) ---
with tabs[0]:
    # (هنا يوضع كود استمارة الحجز الخاص بك)
    st.subheader("📝 استمارة حجز جديدة")
    # ... نفس كود استمارة الحجز ...
    st.info("جاهز لاستقبال بيانات النزلاء")

with tabs[1]:
    st.subheader("📊 حالة الأسرة اليوم")
    # (هنا يوضع كود المربعات الملونة الخاص بك)
    st.write("عرض حالة الأجنحة...")

# ==================== تبويب الإعدادات (المدمج) ====================
if st.session_state.user_role == "مدير":
    with tabs[4]:
        st.subheader("⚙️ إعدادات النظام المتقدمة")
        
        # 1. إدارة المستخدمين (إضافتك الجديدة)
        st.markdown("### 👥 إدارة المستخدمين")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**إضافة مستخدم جديد**")
            new_uname = st.text_input("اسم المستخدم الجديد")
            new_pass = st.text_input("كلمة السر", type="password", key="new_u_pass")
            new_fname = st.text_input("الاسم الكامل للموظف")
            new_role = st.selectbox("الرتبة", ["عون استقبال", "مدير"])
            if st.button("إضافة المستخدم"):
                if add_user(new_uname, new_pass, new_fname, new_role):
                    st.success("✅ تم إضافة المستخدم بنجاح")
                    st.rerun()
                else: st.error("❌ اسم المستخدم موجود مسبقاً")
        with col2:
            st.write("**قائمة المستخدمين الحاليين**")
            users_df = pd.read_sql_query("SELECT username, full_name, role FROM users", get_conn())
            st.dataframe(users_df, use_container_width=True)

        st.divider()

        # 2. إدارة سعة الغرف (الميزة السابقة)
        st.markdown("### 🛏️ تعديل سعة الغرف")
        c_w, c_r, c_n = st.columns(3)
        with c_w: w_e = st.selectbox("الجناح", list(wings.keys()))
        with c_r: r_e = st.selectbox("الغرفة", list(wings[w_e].keys()))
        with c_n: n_val = st.number_input("العدد الجديد", min_value=1, value=wings[w_e][r_e])
        if st.button("تحديث سعة الغرفة"):
            update_room_beds(w_e, r_e, n_val)
            st.success("✅ تم التحديث")
            st.rerun()

# ==================== التذييل ====================
st.markdown(f'<div class="developer-footer">Developer <span style="color:#00d4ff;">®ridha_merzoug®</span> [رضا مرزوق] — النسخة المحسنة 2026</div>', unsafe_allow_html=True)
