import streamlit as st
import json
from datetime import datetime, date
import pandas as pd
import io
import hashlib
from math import ceil

# ====================== إعدادات الصفحة ======================
st.set_page_config(
    page_title="إدارة بيت الشباب محمدي يوسف",
    page_icon="🛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== التصميم الجديد اللي عجبك ======================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Cairo', sans-serif !important; }
    .stApp, section[data-testid="stSidebar"] { direction: rtl !important; text-align: right !important; }
    
    .room-card {
        background: white;
        padding: 25px 20px;
        border-radius: 16px;
        border: 3px solid;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        text-align: center;
        transition: all 0.3s;
    }
    .room-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
    
    .enhanced-header {
        background: linear-gradient(90deg, #1e40af, #3b82f6);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin: 1rem 0 2rem;
        text-align: center;
    }
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: #1e293b;
        color: #cbd5e1;
        text-align: center;
        padding: 1rem;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# JS لتعزيز RTL
st.components.v1.html("""
<script>document.documentElement.setAttribute('dir', 'rtl');</script>
""", height=0)

# ====================== الدوال والثوابت ======================
def hash_password(pw):
    return hashlib.sha256((pw + "youth_hostel_2026").encode()).hexdigest()

USERS = {
    "admin": {"hash": hash_password("admin123"), "role": "admin"},
    "reception": {"hash": hash_password("recep2026"), "role": "user"}
}

ROOMS_CONFIG = {
    "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 8, "مرقد ذكور": 8},
    "جناح إناث": {"غرفة 06": 6, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد أناث": 8}
}
ALL_ROOMS = [r for g in ROOMS_CONFIG.values() for r in g.keys()]

def load_data():
    try:
        with open("youth_hostel_final_db.json", "r", encoding="utf-8") as f:
            d = json.load(f)
            if "archive" not in d: d["archive"] = []
            return d
    except:
        return {r: {"residents": []} for r in ALL_ROOMS} | {"archive": []}

def save_data():
    with open("youth_hostel_final_db.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.db, f, ensure_ascii=False, indent=4)

# ====================== تهيئة session_state ======================
if "auth" not in st.session_state: st.session_state.auth = False
if "user_name" not in st.session_state: st.session_state.user_name = ""
if "user_role" not in st.session_state: st.session_state.user_role = ""
if "bed_price" not in st.session_state: st.session_state.bed_price = 400
if "confirm_exit" not in st.session_state: st.session_state.confirm_exit = None
if "db" not in st.session_state: st.session_state.db = load_data()

# ====================== تسجيل الدخول ======================
if not st.session_state.auth:
    st.markdown("<div class='enhanced-header'><h1>🛏️ إدارة بيت الشباب محمدي يوسف</h1></div>", unsafe_allow_html=True)
    col = st.columns([1,2,1])[1]
    with col:
        u = st.text_input("👤 اسم المستخدم", placeholder="admin أو reception")
        p = st.text_input("🔑 كلمة السر", type="password")
        if st.button("تسجيل الدخول", type="primary", use_container_width=True):
            if u in USERS and USERS[u]["hash"] == hash_password(p):
                st.session_state.auth = True
                st.session_state.user_name = u
                st.session_state.user_role = USERS[u]["role"]
                st.rerun()
            else:
                st.error("❌ بيانات خاطئة")
    st.stop()

# ====================== الشريط الجانبي ======================
st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
st.sidebar.markdown(f"**الصلاحية:** {'🛡️ مدير' if st.session_state.user_role == 'admin' else '👋 استقبال'}")

if st.session_state.user_role == "admin":
    st.session_state.bed_price = st.sidebar.number_input("💰 سعر السرير اليومي (دج)", value=st.session_state.bed_price, min_value=100, step=50)

menu = st.sidebar.radio("القائمة الرئيسية", ["🏨 إدارة الغرف", "👥 قائمة النزلاء", "📊 الإحصائيات", "📂 الأرشيف"])
if st.sidebar.button("🚪 تسجيل الخروج", type="primary"):
    st.session_state.auth = False
    st.rerun()

# ====================== 1. إدارة الغرف (التصميم الجديد) ======================
if menu == "🏨 إدارة الغرف":
    st.markdown("<div class='enhanced-header'><h2>حالة الإشغال - مارس 2026</h2></div>", unsafe_allow_html=True)
    
    for group, rooms in ROOMS_CONFIG.items():
        st.subheader(group)
        cols = st.columns(2)
        for i, (r_name, max_b) in enumerate(rooms.items()):
            occ = len(st.session_state.db[r_name]["residents"])
            avail = max_b - occ
            color = "#10b981" if avail >= 3 else "#eab308" if avail > 0 else "#ef4444"
            status = "🟢 متاح" if avail >= 3 else "🟡 شبه ممتلئ" if avail > 0 else "🔴 ممتلئ"
            
            with cols[i % 2]:
                st.markdown(f"""
                <div class="room-card" style="border-color: {color};">
                    <h2 style="margin:0; color:#1e3a8a;">{r_name}</h2>
                    <div style="font-size: 2.8rem; font-weight: 700; color:#1e40af; margin:15px 0;">
                        {occ} / {max_b}
                    </div>
                    <p style="font-size: 1.4rem; color:{color};">
                        المتاح: <strong>{avail} سرير</strong><br>{status}
                    </p>
                </div>
                """, unsafe_allow_html=True)

    st.divider()
    st.subheader("➕ تسجيل مقيم جديد")
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("اسم المقيم الكامل")
        room = c1.selectbox("اختر الغرفة", ALL_ROOMS)
        gender = c2.selectbox("الجنس", ["ذكر", "أنثى"])
        nation = c2.text_input("الجنسية", "جزائرية")
        if st.form_submit_button("✅ تسجيل", type="primary"):
            max_b = next(v for g in ROOMS_CONFIG.values() for k, v in g.items() if k == room)
            if name and len(st.session_state.db[room]["residents"]) < max_b:
                st.session_state.db[room]["residents"].append({
                    "name": name.strip(), "gender": gender, "nation": nation.strip(),
                    "kids": 0, "is_free": False, "entry": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                save_data()
                st.success(f"✅ تم تسجيل {name}")
                st.rerun()
            else:
                st.error("❌ الاسم فارغ أو الغرفة ممتلئة")

# ====================== 2. قائمة النزلاء ======================
elif menu == "👥 قائمة النزلاء":
    st.markdown("<div class='enhanced-header'><h2>👥 قائمة النزلاء الحاليين</h2></div>", unsafe_allow_html=True)
    # (نفس الكود السابق للقائمة + التعديل + الخروج مع التأكيد - إذا تبغي نضيفه كامل أرسله لك)

# ====================== 3. الإحصائيات ======================
elif menu == "📊 الإحصائيات":
    # نفس الكود السابق مع الجدول والطباعة

# ====================== 4. الأرشيف ======================
elif menu == "📂 الأرشيف":
    # نفس الكود السابق مع البحث والتحميل

# ====================== Footer ======================
st.markdown("<div class='footer'>© 2026 إدارة بيت الشباب محمدي يوسف • مطور من طرف ridha_merzoug</div>", unsafe_allow_html=True)
