import streamlit as st
import json
from datetime import datetime
import pandas as pd
import hashlib

# ====================== 1. إعدادات المتصفح (منع التداخل) ======================
st.set_page_config(
    page_title="إدارة بيت الشباب محمدي يوسف",
    page_icon="🏢",
    layout="centered", # لضمان عدم تمدد العناصر بشكل مشوه على الشاشات الكبيرة
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    /* فرض الاتجاه من اليمين لليوم ومنع تكسر النصوص */
    html, body, [class*="css"] { 
        direction: RTL !important; 
        text-align: right !important; 
        font-family: 'Cairo', sans-serif !important;
    }
    
    /* إجبار الحاويات على أخذ العرض الكامل لمنع الانقسام العمودي */
    [data-testid="column"], [data-testid="stVerticalBlock"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }

    .main-header {
        background: linear-gradient(90deg, #1e40af, #3b82f6);
        color: white; padding: 20px; border-radius: 15px;
        text-align: center; margin-bottom: 25px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }

    .room-card {
        background: white; padding: 15px; border-radius: 12px;
        border-right: 8px solid #1e40af; margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        display: flex; justify-content: space-between; align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# ====================== 2. الدوال وقاعدة البيانات ======================
def hash_password(pw):
    return hashlib.sha256((pw + "youth_hostel_2026").encode()).hexdigest()

ROOMS_CONFIG = {
    "جناح ذكور 👨": ["غرفة 01", "غرفة 02", "غرفة 03", "غرفة 04", "غرفة 05", "مرقد ذكور"],
    "جناح إناث 👩": ["غرفة 06", "غرفة 07", "غرفة 08", "غرفة 09", "مرقد أناث"]
}
ALL_ROOMS = [r for g in ROOMS_CONFIG.values() for r in g]

def load_data():
    try:
        with open("hostel_v9_db.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "rooms": {r: {"residents": []} for r in ALL_ROOMS},
            "archive": [],
            "users": {
                "admin": {"hash": hash_password("admin123"), "role": "admin"},
                "user": {"hash": hash_password("user123"), "role": "user"}
            }
        }

def save_data():
    with open("hostel_v9_db.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.db, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state: st.session_state.db = load_data()
if "auth" not in st.session_state: st.session_state.auth = False

# ====================== 3. صفحة الدخول (القائمة المنسدلة) ======================
if not st.session_state.auth:
    st.markdown("<div class='main-header'><h1>🔐 دخول النظام</h1></div>", unsafe_allow_html=True)
    
    # القائمة المنسدلة المطلوبة لبروفايل المستخدم
    user_profile = st.selectbox("تسجيل الدخول بصفتي:", ["مدير النظام (Admin)", "موظف استقبال (User)"])
    u_key = "admin" if "Admin" in user_profile else "user"
    
    pwd = st.text_input(f"أدخل كلمة مرور {u_key}", type="password")
    
    if st.button("تسجيل الدخول", use_container_width=True, type="primary"):
        if st.session_state.db["users"][u_key]["hash"] == hash_password(pwd):
            st.session_state.auth = True
            st.session_state.user_role = st.session_state.db["users"][u_key]["role"]
            st.session_state.user_name = u_key
            st.rerun()
        else:
            st.error("❌ عذراً، كلمة السر غير صحيحة")
    st.stop()

# ====================== 4. التحكم في القائمة بناءً على الصلاحيات ======================
st.markdown(f"### 👤 الحساب: {st.session_state.user_name.upper()}")

if st.session_state.user_role == "admin":
    # المدير يرى القائمة المنسدلة كاملة
    menu = st.selectbox("القائمة الرئيسية:", ["🏨 إدارة الغرف والحجز", "👥 قائمة النزلاء", "📊 الإحصائيات", "📂 الأرشيف"])
else:
    # الموظف لا يظهر له خيار التغيير، يرى فقط صفحة الحجز
    menu = "🏨 إدارة الغرف والحجز"
    st.info("ℹ️ أنت الآن في وضع الموظف (عرض صفحة الحجز فقط)")

# ====================== 5. محتوى الصفحات ======================

if menu == "🏨 إدارة الغرف والحجز":
    st.markdown("<div class='main-header'><h2>🏨 حالة الغرف والتسجيل</h2></div>", unsafe_allow_html=True)
    
    for group, rooms in ROOMS_CONFIG.items():
        st.write(f"#### {group}")
        for r_name in rooms:
            count = len(st.session_state.db["rooms"][r_name]["residents"])
            color = "#10b981" if count < 6 else "#ef4444"
            st.markdown(f"""
            <div class="room-card" style="border-right-color: {color}">
                <span>{r_name}</span>
                <span style="font-weight:bold; color:{color}">{count} / 6</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("➕ إضافة مقيم جديد", expanded=True):
        with st.form("quick_reg"):
            n = st.text_input("الاسم الكامل")
            r = st.selectbox("تحديد الغرفة", ALL_ROOMS)
            if st.form_submit_button("تأكيد التسجيل", use_container_width=True):
                if n:
                    st.session_state.db["rooms"][r]["residents"].append({
                        "name": n, "time": datetime.now().strftime("%H:%M")
                    })
                    save_data(); st.success("تم الحفظ"); st.rerun()

elif menu == "👥 قائمة النزلاء":
    # (هذه الصفحة تظهر للمدير فقط)
    st.markdown("<div class='main-header'><h2>👥 قائمة المقيمين حالياً</h2></div>", unsafe_allow_html=True)
    for rm in ALL_ROOMS:
        residents = st.session_state.db["rooms"][rm]["residents"]
        if residents:
            with st.expander(f"🏠 {rm}"):
                for i, p in enumerate(residents):
                    col1, col2 = st.columns([3,1])
                    col1.write(f"👤 {p['name']}")
                    if col2.button("خروج", key=f"ex_{rm}_{i}"):
                        st.session_state.db["archive"].append({"name": p['name'], "room": rm, "date": date.today().isoformat()})
                        st.session_state.db["rooms"][rm]["residents"].pop(i)
                        save_data(); st.rerun()

elif menu == "📊 الإحصائيات":
    st.markdown("<div class='main-header'><h2>📊 إحصائيات سريعة</h2></div>", unsafe_allow_html=True)
    total = sum(len(st.session_state.db["rooms"][rm]["residents"]) for rm in ALL_ROOMS)
    st.metric("إجمالي النزلاء في البيت", total)

elif menu == "📂 الأرشيف":
    st.markdown("<div class='main-header'><h2>📂 سجل البيانات التاريخي</h2></div>", unsafe_allow_html=True)
    if st.session_state.db["archive"]:
        st.table(pd.DataFrame(st.session_state.db["archive"]))

# زر تسجيل الخروج في الأسفل
if st.button("🚪 تسجيل الخروج من النظام", use_container_width=True):
    st.session_state.auth = False; st.rerun()

st.markdown("<div style='text-align:center; color:gray; font-size:10px; margin-top:50px;'>إدارة بيت الشباب محمدي يوسف • ®ridha_merzoug®</div>", unsafe_allow_html=True)
