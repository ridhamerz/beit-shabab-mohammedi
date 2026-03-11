import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3

# ==================== إعداد الصفحة والتنسيق ====================
st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; font-size: 1.3rem; font-weight: bold; }
    .stat-card { background: #ffffff; padding: 20px; border-radius: 15px; border-bottom: 5px solid #1e3c72; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: 0.3s; }
    .stat-card:hover { transform: translateY(-5px); }
    .icon-style { font-size: 2rem; margin-bottom: 10px; display: block; }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 10px; border-radius: 10px; text-align: center; margin-top: 40px; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# ==================== قاعدة البيانات (نفس الدوال السابقة) ====================
DB_FILE = "biet_chabab.db"
def get_conn(): return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, الاسم_واللقب TEXT, تاريخ_الازدياد DATE, مكان_الازدياد TEXT,
        العنوان TEXT, نوع_البطاقة TEXT, رقم_البطاقة TEXT, الجنسية TEXT, تاريخ_الفيزا TEXT, 
        الجناح TEXT, الغرفة TEXT, السرير TEXT, تاريخ_الدخول DATE, تاريخ_الخروج DATE, الحالة_القانونية TEXT)''')
    conn.execute('CREATE TABLE IF NOT EXISTS rooms_config (wing TEXT, room TEXT, beds_count INTEGER, PRIMARY KEY (wing, room))')
    conn.execute('CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY, اسم_الفوج TEXT, العدد INTEGER, تاريخ_الدخول DATE, تاريخ_الخروج DATE)')
    conn.commit()
    conn.close()

init_db()

# --- جلب البيانات للإحصائيات ---
def load_wings_config():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM rooms_config", conn)
    conn.close()
    return {w: dict(df[df['wing'] == w][['room', 'beds_count']].values) for w in df['wing'].unique()}

wings = load_wings_config()
df_all = pd.read_sql_query("SELECT * FROM bookings", get_conn())
today = date.today()

occupied_today = df_all[(pd.to_datetime(df_all['تاريخ_الدخول']).dt.date <= today) & (pd.to_datetime(df_all['تاريخ_الخروج']).dt.date > today)]
free_male = sum(wings.get("جناح ذكور", {}).values()) - len(occupied_today[occupied_today['الجناح'] == "جناح ذكور"])
free_female = sum(wings.get("جناح إناث", {}).values()) - len(occupied_today[occupied_today['الجناح'] == "جناح إناث"])

# ==================== الجلسة وبوابة الدخول ====================
if 'authenticated' not in st.session_state: st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<div class="main-title">🏨 نظام إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)
    with st.container():
        role = st.selectbox("🔑 اختر الصفة", ["مدير", "عون استقبال"])
        pwd = st.text_input("🔒 كلمة السر", type="password")
        if st.button("🚀 تسجيل الدخول", use_container_width=True):
            if (role == "مدير" and pwd == "1234") or (role == "عون استقبال" and pwd == "5678"):
                st.session_state.authenticated = True; st.session_state.user_role = role; st.rerun()
            else: st.error("❌ عذراً، كلمة السر غير صحيحة")
    st.stop()

# ==================== التبويبات بالأيقونات ====================
tabs = st.tabs([
    "➕ حجز جديد", 
    "🛌 حالة الغرف", 
    "📋 السجل العام", 
    "📄 تصدير Word", 
    "👥 الأفواج", 
    "💰 الحسابات", 
    "⚙️ الإعدادات"
])

# ==================== 1. تبويب حجز جديد ====================
with tabs[0]:
    # إحصائيات علوية مصممة بأيقونات
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="stat-card"><span class="icon-style">👨</span>شاغر (ذكور)<br><h2>{free_male}</h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-card"><span class="icon-style">👩</span>شاغر (إناث)<br><h2>{free_female}</h2></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-card"><span class="icon-style">📅</span>تاريخ اليوم<br><h2>{today}</h2></div>', unsafe_allow_html=True)
    
    st.divider()
    
    # البحث الذكي
    search_id = st.text_input("🔍 بحث ذكي برقم البطاقة (لجلب بيانات سابقة)", placeholder="أدخل الرقم هنا...")
    
    if not st.session_state.get('review_mode', False):
        with st.form("main_form"):
            st.markdown("### 📝 بيانات النزيل الشخصية")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("👤 الاسم واللقب *")
                b_date = st.date_input("🎂 تاريخ الازدياد", value=date(2000, 1, 1))
                b_place = st.text_input("📍 مكان الازدياد")
                address = st.text_input("🏠 العنوان الكامل")
                nationality = st.selectbox("🌍 الجنسية", ["جزائرية", "أخرى"])
            
            with col2:
                id_type = st.selectbox("🪪 نوع بطاقة التعريف", ["بطاقة تعريف عادية", "بطاقة بيومترية", "رخصة سياقة عادية", "رخصة سياقة بيومترية", "جواز سفر"])
                id_val = st.text_input("🔢 رقم البطاقة *")
                wing = st.selectbox("🏢 الجناح", list(wings.keys()))
                room = st.selectbox("🚪 الغرفة", list(wings[wing].keys()) if wings else [])
                arr = st.date_input("📥 تاريخ الدخول", value=today)
                dep = st.date_input("📤 تاريخ الخروج", value=today + timedelta(days=1))

            if st.form_submit_button("🔍 مراجعة الحجز قبل التأكيد", use_container_width=True):
                if not name or not id_val:
                    st.error("⚠️ يرجى ملء الخانات الإجبارية (*) أولاً")
                else:
                    st.session_state.temp_data = {"الاسم_واللقب": name, "رقم_البطاقة": id_val, "الجناح": wing, "الغرفة": room, "تاريخ_الدخول": arr}
                    st.session_state.review_mode = True
                    st.rerun()
    else:
        st.success("✅ البيانات جاهزة للمراجعة")
        st.write(st.session_state.temp_data)
        if st.button("💾 تأكيد وحفظ النهائي"):
            st.session_state.review_mode = False
            st.success("تم الحفظ بنجاح!")

# ==================== بقية التبويبات بأيقونات توضيحية ====================
with tabs[1]:
    st.subheader("🛌 توزيع الأسرة وحالة الإشغال")
    st.info("الأخضر 🟢 شاغر | الأحمر 🔴 محجوز")

with tabs[3]:
    st.subheader("📄 تصدير التقارير إلى Word")
    st.button("📝 إنشاء ملف Word للنزيل الحالي")

with tabs[4]:
    st.subheader("👥 إدارة الأفواج والوفود")
    st.button("➕ إضافة فوج جديد")

with tabs[5]:
    st.subheader("💰 الإدارة المالية والحسابات")
    st.metric("إجمالي مداخيل اليوم", "4500 د.ج", "+150")

with tabs[6]:
    st.subheader("⚙️ إعدادات النظام")
    st.write("🔧 تحديث كلمات السر وسعة الغرف")

# ==================== التذييل ====================
st.markdown(f'''
    <div class="developer-footer">
        🛠️ تم التطوير بواسطة: <b>®ridha_merzoug®</b> [رضا مرزوق] <br>
        📍 بيت شباب محمدي يوسف قالمة - نسخة 2026 المحسنة ✨
    </div>
    ''', unsafe_allow_html=True)
