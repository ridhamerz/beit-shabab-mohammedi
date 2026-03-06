import streamlit as st
import json
from datetime import datetime, date
import pandas as pd
import io
import hashlib

# ====================== إعدادات الصفحة ======================
st.set_page_config(
    page_title="إدارة بيت الشباب محمدي يوسف",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== التصميم الاحترافي المحسن ======================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif !important; }
    .stApp { direction: rtl !important; text-align: right !important; background-color: #f8fafc; }
    
    .room-card {
        background: white; padding: 20px; border-radius: 15px; border-right: 8px solid;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 15px; transition: 0.3s;
    }
    .room-card:hover { transform: scale(1.02); }
    
    .enhanced-header {
        background: linear-gradient(90deg, #1e40af, #3b82f6);
        color: white; padding: 1.5rem; border-radius: 15px;
        text-align: center; margin-bottom: 2rem;
    }
    .footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: #1e293b; color: white; text-align: center;
        padding: 0.5rem; z-index: 100; font-size: 14px;
    }
    .stats-box {
        background: white; padding: 15px; border-radius: 10px;
        border: 1px solid #e2e8f0; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ====================== الدوال البرمجية ======================
def hash_password(pw):
    return hashlib.sha256((pw + "youth_hostel_2026").encode()).hexdigest()

# كلمات المرور (يمكن للمدير تغييرها لاحقاً في ملف JSON)
DEFAULT_USERS = {
    "admin": {"hash": hash_password("admin123"), "role": "admin"},
    "reception": {"hash": hash_password("recep2026"), "role": "user"}
}

ROOMS_CONFIG = {
    "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد ذكور": 8},
    "جناح إناث": {"غرفة 06": 6, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد أناث": 8}
}
ALL_ROOMS = [r for g in ROOMS_CONFIG.values() for r in g.keys()]

def load_data():
    try:
        with open("youth_hostel_v5_db.json", "r", encoding="utf-8") as f:
            d = json.load(f)
            if "users" not in d: d["users"] = DEFAULT_USERS
            return d
    except:
        return {r: {"residents": []} for r in ALL_ROOMS} | {"archive": [], "users": DEFAULT_USERS}

def save_data():
    with open("youth_hostel_v5_db.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.db, f, ensure_ascii=False, indent=4)

# تهيئة البيانات
if "db" not in st.session_state: st.session_state.db = load_data()
if "auth" not in st.session_state: st.session_state.auth = False
if "bed_price" not in st.session_state: st.session_state.bed_price = 400

# ====================== نظام الدخول ======================
if not st.session_state.auth:
    st.markdown("<div class='enhanced-header'><h1>🏢 إدارة بيت الشباب محمدي يوسف</h1></div>", unsafe_allow_html=True)
    col = st.columns([1,1.5,1])[1]
    with col:
        u = st.text_input("👤 اسم المستخدم")
        p = st.text_input("🔑 كلمة السر", type="password")
        if st.button("دخول النظام", type="primary", use_container_width=True):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u]["hash"] == hash_password(p):
                st.session_state.auth, st.session_state.user_name = True, u
                st.session_state.user_role = st.session_state.db["users"][u]["role"]
                st.rerun()
            else: st.error("بيانات خاطئة")
    st.stop()

# ====================== القائمة الجانبية ======================
st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
menu = st.sidebar.radio("القائمة الرئيسية", ["🏨 إدارة الغرف والحجز", "👥 قائمة النزلاء", "📊 الإحصائيات", "📂 الأرشيف"])

if st.session_state.user_role == "admin":
    with st.sidebar.expander("🛠️ إعدادات المدير"):
        st.session_state.bed_price = st.number_input("💰 سعر السرير", value=st.session_state.bed_price)
        new_p = st.text_input("تغيير كلمة المرور", type="password")
        if st.button("حفظ"):
            st.session_state.db["users"][st.session_state.user_name]["hash"] = hash_password(new_p)
            save_data(); st.success("تم الحفظ")

if st.sidebar.button("🚪 خروج"):
    st.session_state.auth = False; st.rerun()

# ====================== 1. إدارة الغرف ======================
if menu == "🏨 إدارة الغرف والحجز":
    st.markdown("<div class='enhanced-header'><h2>🏨 وضعية الغرف والتسجيل</h2></div>", unsafe_allow_html=True)
    
    for group, rooms in ROOMS_CONFIG.items():
        st.subheader(f"📍 {group}")
        cols = st.columns(3)
        for i, (r_name, max_b) in enumerate(rooms.items()):
            occ = len(st.session_state.db[r_name]["residents"])
            avail = max_b - occ
            color = "#10b981" if avail > 2 else "#f59e0b" if avail > 0 else "#ef4444"
            with cols[i % 3]:
                st.markdown(f"""
                <div class="room-card" style="border-color: {color};">
                    <h3 style="margin:0;">{r_name}</h3>
                    <h2 style="color:#1e40af;">{occ} / {max_b}</h2>
                    <small>المتاح: {avail}</small>
                </div>
                """, unsafe_allow_html=True)

    st.divider()
    with st.expander("➕ تسجيل نزيل جديد", expanded=True):
        with st.form("reg_form"):
            c1, c2 = st.columns(2)
            fn = c1.text_input("الاسم الكامل")
            rm = c1.selectbox("الغرفة", ALL_ROOMS)
            gen = c2.selectbox("الجنس", ["ذكر", "أنثى"])
            nat = c2.text_input("الجنسية", "جزائرية")
            if st.form_submit_button("✅ تأكيد الحجز", type="primary"):
                if fn and len(st.session_state.db[rm]["residents"]) < 10: # فحص بسيط
                    st.session_state.db[rm]["residents"].append({
                        "name": fn, "gender": gen, "nation": nat, 
                        "entry": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_data(); st.success("تم التسجيل"); st.rerun()

# ====================== 2. قائمة النزلاء ======================
elif menu == "👥 قائمة النزلاء":
    st.markdown("<div class='enhanced-header'><h2>👥 قائمة النزلاء الحاليين</h2></div>", unsafe_allow_html=True)
    for r in ALL_ROOMS:
        res = st.session_state.db[r]["residents"]
        if res:
            with st.expander(f"🏠 {r} - ({len(res)} نزلاء)"):
                for idx, p in enumerate(res):
                    col1, col2 = st.columns([3,1])
                    col1.write(f"👤 **{p['name']}** | {p['gender']} | دخول: {p['entry']}")
                    if col2.button("تسجيل خروج", key=f"ex_{r}_{idx}"):
                        days = max(1, (datetime.now() - datetime.strptime(p['entry'], "%Y-%m-%d %H:%M")).days)
                        p.update({"exit": datetime.now().strftime("%Y-%m-%d %H:%M"), "paid": days * st.session_state.bed_price, "room": r})
                        st.session_state.db["archive"].append(p)
                        st.session_state.db[r]["residents"].pop(idx)
                        save_data(); st.rerun()

# ====================== 3. الإحصائيات ======================
elif menu == "📊 الإحصائيات":
    st.markdown("<div class='enhanced-header'><h2>📊 الإحصائيات والتقارير</h2></div>", unsafe_allow_html=True)
    all_res = []
    for r in ALL_ROOMS: all_res.extend(st.session_state.db[r]["residents"])
    
    m = len([x for x in all_res if x['gender']=="ذكر"])
    f = len([x for x in all_res if x['gender']=="أنثى"])
    rev = sum(e.get("paid",0) for e in st.session_state.db["archive"] if e["exit"].startswith(date.today().strftime("%Y-%m-%d")))
    
    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي المقيمين", len(all_res))
    col2.metric("دخل اليوم", f"{rev} دج")
    col3.metric("ذكر / أنثى", f"{m} / {f}")
    
    st.write("### 📝 مسودة طباعة سريعة")
    st.text_area("بيانات الحالة الحالية (للطباعة):", f"تقرير يوم: {date.today()}\nإجمالي النزلاء: {len(all_res)}\nذكور: {m} | إناث: {f}", height=150)

# ====================== 4. الأرشيف ======================
elif menu == "📂 الأرشيف":
    st.markdown("<div class='enhanced-header'><h2>📂 الأرشيف التاريخي</h2></div>", unsafe_allow_html=True)
    if st.session_state.db["archive"]:
        df = pd.DataFrame(st.session_state.db["archive"])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل التقرير الشامل Excel", csv, "archive.csv", "text/csv")

# الفوتر
st.markdown(f"<div class='footer'>© {date.today().year} إدارة بيت الشباب محمدي يوسف • مطور من طرف ®ridha_merzoug®</div>", unsafe_allow_html=True)
