import streamlit as st
import json
from datetime import datetime, date
import pandas as pd
import io
import hashlib

# ====================== إعدادات الصفحة المحسنة للجوال ======================
st.set_page_config(
    page_title="إدارة بيت الشباب محمدي يوسف",
    page_icon="🏢",
    layout="wide", # ضروري لملء الشاشة
    initial_sidebar_state="collapsed" # تبدأ مغلقة لتعطي مساحة للغرف
)

# ====================== نظام التصميم المرن (Responsive CSS) ======================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    * { font-family: 'Cairo', sans-serif !important; }
    
    /* إصلاح اتجاه الصفحة ومنع النصوص العمودية */
    .stApp { direction: rtl !important; text-align: right !important; }
    
    /* تصميم بطاقات الغرف لتكون منتظمة */
    .room-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        border-right: 6px solid #1e40af;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        text-align: center;
        min-height: 120px;
    }
    
    .room-card h3 { font-size: 1.1rem; margin-bottom: 5px; color: #1e293b; }
    .room-card h2 { font-size: 1.8rem; color: #1e40af; margin: 5px 0; }
    .room-card small { color: #64748b; font-weight: bold; }

    /* تحسين شكل القائمة الجانبية على الهاتف */
    [data-testid="stSidebar"] {
        direction: rtl !important;
        text-align: right !important;
    }

    /* إصلاح تداخل العناوين الكبيرة */
    .enhanced-header {
        background: linear-gradient(90deg, #1e40af, #3b82f6);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
        font-size: 0.9rem !important;
    }
    .enhanced-header h1, .enhanced-header h2 { font-size: 1.3rem !important; margin: 0; }

    /* تنسيق الفوتر ليناسب الجوال */
    .footer {
        text-align: center;
        color: #475569;
        padding: 10px;
        font-size: 11px;
        background: #f1f5f9;
        margin-top: 20px;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ====================== الدوال البرمجية ======================
def hash_password(pw):
    return hashlib.sha256((pw + "youth_hostel_2026").encode()).hexdigest()

DEFAULT_USERS = {
    "admin": {"hash": hash_password("admin123"), "role": "admin"},
    "reception": {"hash": hash_password("recep2026"), "role": "user"}
}

ROOMS_CONFIG = {
    "جناح ذكور 👨": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد ذكور": 8},
    "جناح إناث 👩": {"غرفة 06": 6, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد أناث": 8}
}
ALL_ROOMS = [r for g in ROOMS_CONFIG.values() for r in g.keys()]

def load_data():
    try:
        with open("youth_hostel_db_v6.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {r: {"residents": []} for r in ALL_ROOMS} | {"archive": [], "users": DEFAULT_USERS}

def save_data():
    with open("youth_hostel_db_v6.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.db, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state: st.session_state.db = load_data()
if "auth" not in st.session_state: st.session_state.auth = False

# ====================== الدخول ======================
if not st.session_state.auth:
    st.markdown("<div class='enhanced-header'><h1>إدارة بيت الشباب محمدي يوسف</h1></div>", unsafe_allow_html=True)
    u = st.text_input("👤 المستخدم")
    p = st.text_input("🔑 كود الدخول", type="password")
    if st.button("دخول", use_container_width=True):
        if u in st.session_state.db["users"] and st.session_state.db["users"][u]["hash"] == hash_password(p):
            st.session_state.auth, st.session_state.user_name = True, u
            st.session_state.user_role = st.session_state.db["users"][u]["role"]
            st.rerun()
    st.stop()

# ====================== القائمة الجانبية ======================
# وضعنا الخيارات في الأعلى لسهولة الوصول إليها في الجوال
menu = st.sidebar.radio("📋 القائمة", ["🏨 الغرف والحجز", "👥 قائمة النزلاء", "📊 الإحصائيات", "📂 الأرشيف"])

if st.session_state.user_role == "admin":
    with st.sidebar.expander("⚙️ إعدادات الإدارة"):
        new_p = st.text_input("كلمة سر جديدة", type="password")
        if st.button("تغيير"):
            st.session_state.db["users"][st.session_state.user_name]["hash"] = hash_password(new_p)
            save_data(); st.success("تم")

if st.sidebar.button("🚪 خروج"):
    st.session_state.auth = False; st.rerun()

# ====================== 1. إدارة الغرف (إصلاح الانتظام) ======================
if menu == "🏨 الغرف والحجز":
    st.markdown("<div class='enhanced-header'><h2>🏨 وضعية الغرف</h2></div>", unsafe_allow_html=True)
    
    for group, rooms in ROOMS_CONFIG.items():
        st.subheader(group)
        # استخدام columns بشكل متزن (2 في الصف الواحد للجوال)
        cols = st.columns(2) 
        for i, (r_name, max_b) in enumerate(rooms.items()):
            occ = len(st.session_state.db[r_name]["residents"])
            avail = max_b - occ
            color = "#10b981" if avail > 1 else "#ef4444"
            with cols[i % 2]:
                st.markdown(f"""
                <div class="room-card" style="border-right-color: {color};">
                    <h3>{r_name}</h3>
                    <h2>{occ}/{max_b}</h2>
                    <small style="color:{color}">المتاح: {avail}</small>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("➕ تسجيل نزيل جديد"):
        with st.form("reg_v6"):
            name = st.text_input("الاسم")
            room = st.selectbox("الغرفة", ALL_ROOMS)
            gen = st.selectbox("الجنس", ["ذكر", "أنثى"])
            nat = st.text_input("الجنسية", "جزائرية")
            if st.form_submit_button("حفظ", use_container_width=True):
                if name:
                    st.session_state.db[room]["residents"].append({
                        "name": name, "gender": gen, "nation": nat, 
                        "entry": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_data(); st.rerun()

# ====================== 2. قائمة النزلاء ======================
elif menu == "👥 قائمة النزلاء":
    st.markdown("<div class='enhanced-header'><h2>👥 النزلاء الحاليين</h2></div>", unsafe_allow_html=True)
    for r in ALL_ROOMS:
        res = st.session_state.db[r]["residents"]
        if res:
            with st.expander(f"🏠 {r} ({len(res)})"):
                for idx, p in enumerate(res):
                    st.write(f"**{p['name']}** ({p['gender']})")
                    if st.button(f"خروج {p['name']}", key=f"ex_{r}_{idx}"):
                        p.update({"exit": datetime.now().strftime("%Y-%m-%d %H:%M"), "room": r})
                        st.session_state.db["archive"].append(p)
                        st.session_state.db[r]["residents"].pop(idx)
                        save_data(); st.rerun()

# ====================== 3. الإحصائيات ======================
elif menu == "📊 الإحصائيات":
    st.markdown("<div class='enhanced-header'><h2>📊 الإحصائيات</h2></div>", unsafe_allow_html=True)
    all_p = []
    for r in ALL_ROOMS: all_p.extend(st.session_state.db[r]["residents"])
    
    st.metric("إجمالي النزلاء حالياً", len(all_p))
    m = len([x for x in all_p if x['gender']=="ذكر"])
    f = len([x for x in all_p if x['gender']=="أنثى"])
    st.write(f"👨 ذكور: {m} | 👩 إناث: {f}")

# ====================== 4. الأرشيف ======================
elif menu == "📂 الأرشيف":
    st.markdown("<div class='enhanced-header'><h2>📂 سجل الأرشيف</h2></div>", unsafe_allow_html=True)
    if st.session_state.db["archive"]:
        st.dataframe(pd.DataFrame(st.session_state.db["archive"]), use_container_width=True)

# التوقيع
st.markdown(f"<div class='footer'>إدارة بيت الشباب محمدي يوسف<br>© 2026 مطور من طرف ®ridha_merzoug®</div>", unsafe_allow_html=True)
