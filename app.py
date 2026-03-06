import streamlit as st
import json
from datetime import datetime, date
import pandas as pd
import io

# --- 1. إعدادات الصفحة والتصميم المحسن للهواتف ---
st.set_page_config(page_title="إدارة بيت الشباب محمدي يوسف", page_icon="🏢", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* تنسيق عام */
    html, body, [class*="css"] { 
        direction: RTL; 
        text-align: right; 
        font-family: 'Cairo', sans-serif; 
    }

    /* حل مشكلة الخط العمودي وتحسين العرض على الهاتف */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 calc(100% - 1rem) !important;
        min-width: 100% !important;
    }

    /* تنسيق الأزرار */
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        font-weight: bold; 
        background-color: #1e40af; 
        color: white; 
        border: none;
        padding: 0.5rem;
    }

    /* العنوان الرئيسي */
    .main-header { 
        text-align: center; 
        color: #1e40af; 
        background: #f0f4ff; 
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 20px; 
        border: 2px solid #1e40af; 
    }

    /* التوقيع السفلي */
    .footer { 
        position: fixed; 
        left: 0; 
        bottom: 0; 
        width: 100%; 
        background-color: #f8fafc; 
        color: #475569; 
        text-align: center; 
        padding: 8px; 
        border-top: 1px solid #e2e8f0; 
        font-weight: bold; 
        z-index: 100; 
    }
</style>
""", unsafe_allow_html=True)

# --- 2. البيانات والوظائف الأساسية ---
USERS = {"admin": {"password": "admin123", "role": "admin"}, "reception": {"password": "recep2026", "role": "user"}}

ROOMS_CONFIG = {
    "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
    "جناح إناث": {"غرفة 06": 6, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد اناث 01": 3, "مرقد اناث 02": 4}
}
ALL_ROOM_NAMES = [room for group in ROOMS_CONFIG.values() for room in group.keys()]
BED_PRICE = 400 

def load_data():
    try:
        with open("youth_hostel_final_db.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if "archive" not in data: data["archive"] = []
            return data
    except:
        return {room: {"residents": []} for room in ALL_ROOM_NAMES} | {"archive": []}

def save_data():
    with open("youth_hostel_final_db.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.db, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state:
    st.session_state.db = load_data()

# --- 3. نظام تسجيل الدخول ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<div class='main-header'><h1>🏢 إدارة بيت الشباب محمدي يوسف</h1></div>", unsafe_allow_html=True)
    user = st.text_input("👤 اسم المستخدم")
    pw = st.text_input("🔑 كلمة السر", type="password")
    if st.button("تسجيل الدخول"):
        if user in USERS and USERS[user]["password"] == pw:
            st.session_state.auth, st.session_state.user_role, st.session_state.user_name = True, USERS[user]["role"], user
            st.rerun()
        else:
            st.error("بيانات خاطئة")
    st.markdown("<div class='footer'>مطور من طرف ®ridha_merzoug®</div>", unsafe_allow_html=True)
    st.stop()

# --- 4. القائمة الجانبية ---
st.sidebar.markdown(f"### 👤 المستخدم: {st.session_state.user_name}")
menu = ["📊 الإحصائيات المالية", "🏨 إدارة الغرف والحجز", "👥 قائمة النزلاء", "📂 الأرشيف"]
choice = st.sidebar.radio("القائمة الرئيسية", menu)

# --- 5. الصفحات والوظائف ---

# الصفحة 1: الإحصائيات
if choice == "📊 الإحصائيات المالية":
    st.markdown("<div class='main-header'><h2>📊 الملخص الإحصائي والمالي</h2></div>", unsafe_allow_html=True)
    
    current_res = []
    for r in ALL_ROOM_NAMES: current_res.extend(st.session_state.db[r]["residents"])
    
    males = len([p for p in current_res if p['gender'] == "ذكر"])
    females = len([p for p in current_res if p['gender'] == "أنثى"])
    foreigners = len([p for p in current_res if p['nation'].lower() not in ["جزائرية", "جزائري"]])
    
    today = date.today().strftime("%Y-%m-%d")
    month = date.today().strftime("%Y-%m")
    daily_rev = sum(e.get("paid_val", 0) for e in st.session_state.db["archive"] if e.get("exit", "").startswith(today))
    monthly_rev = sum(e.get("paid_val", 0) for e in st.session_state.db["archive"] if e.get("exit", "").startswith(month))

    c1, c2, c3 = st.columns(3)
    c1.metric("👥 المقيمين حالياً", f"{len(current_res)}")
    c2.metric("💰 دخل اليوم", f"{daily_rev} دج")
    c3.metric("📅 دخل الشهر", f"{monthly_rev} دج")
    
    st.markdown("---")
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("👨 الذكور", males)
    cc2.metric("👩 الإناث", females)
    cc3.metric("🌍 الأجانب", foreigners)

# الصفحة 2: إدارة الغرف والحجز
elif choice == "🏨 إدارة الغرف والحجز":
    st.markdown("<div class='main-header'><h2>🏨 وضعية الغرف محمدي يوسف</h2></div>", unsafe_allow_html=True)
    
    status_data = []
    for r in ALL_ROOM_NAMES:
        max_b = next(v for g in ROOMS_CONFIG.values() for k,v in g.items() if k == r)
        occ = len(st.session_state.db[r]["residents"])
        status_data.append({"الغرفة": r, "السعة": max_b, "المشغول": occ, "المتاح": max_b - occ, "الحالة": "🔴 ممتلئة" if occ >= max_b else "🟢 متاحة"})
    st.table(pd.DataFrame(status_data))

    st.markdown("---")
    st.subheader("➕ تسجيل مقيم جديد")
    with st.form("add_form"):
        f_name = st.text_input("اسم المقيم الكامل")
        f_room = st.selectbox("اختر الغرفة", ALL_ROOM_NAMES)
        f_gender = st.selectbox("الجنس", ["ذكر", "أنثى"])
        f_nation = st.text_input("الجنسية", "جزائرية")
        f_kids = st.number_input("عدد الأطفال", 0, 10)
        f_free = st.checkbox("إقامة مجانية")
        if st.form_submit_button("حفظ البيانات"):
            max_b = next(v for g in ROOMS_CONFIG.values() for k,v in g.items() if k == f_room)
            if len(st.session_state.db[f_room]["residents"]) < max_b:
                st.session_state.db[f_room]["residents"].append({
                    "name": f_name, "gender": f_gender, "nation": f_nation, 
                    "kids": f_kids, "is_free": f_free, 
                    "entry": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                save_data(); st.success("تم التسجيل"); st.rerun()
            else: st.error("الغرفة ممتلئة")

# الصفحة 3: قائمة النزلاء
elif choice == "👥 قائمة النزلاء":
    st.markdown("<div class='main-header'><h2>👥 تفاصيل النزلاء حسب الغرفة</h2></div>", unsafe_allow_html=True)
    for r in ALL_ROOM_NAMES:
        res_list = st.session_state.db[r]["residents"]
        with st.expander(f"🏠 {r} - ({len(res_list)} فرد)", expanded=False):
            if res_list:
                for idx, p in enumerate(res_list):
                    days = max(1, (datetime.now() - datetime.strptime(p["entry"], "%Y-%m-%d %H:%M")).days)
                    total = 0 if p["is_free"] else days * BED_PRICE
                    col_a, col_b, col_c = st.columns([3,2,1])
                    col_a.write(f"**{p['name']}** ({p['gender']}) - {p['nation']}")
                    col_b.write(f"المبلغ: {total} دج")
                    if col_c.button("خروج", key=f"btn_{r}_{idx}"):
                        p.update({"exit": datetime.now().strftime("%Y-%m-%d %H:%M"), "paid_val": total, "room": r})
                        st.session_state.db["archive"].append(p)
                        st.session_state.db[r]["residents"].pop(idx)
                        save_data(); st.rerun()
            else: st.write("فارغة")

# الصفحة 4: الأرشيف
elif choice == "📂 الأرشيف":
    st.markdown("<div class='main-header'><h2>📂 سجل البيانات التاريخي</h2></div>", unsafe_allow_html=True)
    if st.session_state.db["archive"]:
        df_arch = pd.DataFrame(st.session_state.db["archive"]).rename(columns={
            "name": "الاسم", "gender": "الجنس", "nation": "الجنسية", "kids": "الأطفال",
            "entry": "الدخول", "exit": "الخروج", "paid_val": "المبلغ", "room": "الغرفة"
        })
        st.dataframe(df_arch, use_container_width=True)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_arch.to_excel(writer, index=False)
        st.download_button("📥 تحميل التقرير (Excel)", output.getvalue(), f"تقرير_{date.today()}.xlsx")

# التوقيع الثابت
st.markdown("<div class='footer'>إدارة بيت الشباب محمدي يوسف - مطور من طرف ®ridha_merzoug®</div>", unsafe_allow_html=True)
if st.sidebar.button("تسجيل الخروج"):
    st.session_state.auth = False; st.rerun()
