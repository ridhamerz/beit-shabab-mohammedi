import streamlit as st
import json
from datetime import datetime, date
import pandas as pd
import io

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="إدارة بيت الشباب محمدي يوسف", page_icon="🛏️", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] {
        direction: RTL; text-align: right; font-family: 'Cairo', sans-serif;
    }
    .stButton>button {width: 100%; border-radius: 8px; font-weight: bold;}
    .main-header {text-align: center; color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 10px;}
    .footer {text-align: center; color: #6b7280; margin-top: 50px; font-size: 14px; border-top: 1px solid #e5e7eb; padding-top: 10px;}
</style>
""", unsafe_allow_html=True)

# --- 2. الإعدادات والبيانات الثابتة ---
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "reception": {"password": "recep2026", "role": "user"}
}

ROOMS_CONFIG = {
    "جناح ذكور": {
        "غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6,
        "مرقد ذكور 01": 3, "مرقد ذكور 02": 4
    },
    "جناح إناث": {
        "غرفة 06": 6, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6,
        "مرقد اناث 01": 3, "مرقد اناث 02": 4
    }
}

ALL_ROOM_NAMES = [room for group in ROOMS_CONFIG.values() for room in group.keys()]
BED_PRICE = 400 

# --- 3. إدارة الملفات ---
def load_data():
    try:
        with open("youth_hostel_db.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if "archive" not in data: data["archive"] = []
            return data
    except FileNotFoundError:
        initial = {room: {"occupied": 0, "residents": []} for room in ALL_ROOM_NAMES}
        initial["archive"] = []
        return initial

def save_data():
    with open("youth_hostel_db.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.db, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state:
    st.session_state.db = load_data()

# --- 4. نظام تسجيل الدخول ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 class='main-header'>🔐 تسجيل الدخول للنظام</h1>", unsafe_allow_html=True)
    user = st.text_input("اسم المستخدم")
    pw = st.text_input("كلمة السر", type="password")
    if st.button("دخول"):
        if user in USERS and USERS[user]["password"] == pw:
            st.session_state.auth = True
            st.session_state.user_role = USERS[user]["role"]
            st.session_state.user_name = user
            st.rerun()
        else:
            st.error("خطأ في البيانات")
    st.markdown("<div class='footer'>مطور من طرف ®ridha_merzoug®</div>", unsafe_allow_html=True)
    st.stop()

# --- 5. القائمة الجانبية ---
st.sidebar.title(f"مرحباً: {st.session_state.user_name}")
menu = ["🏠 لوحة التحكم", "👤 تسجيل مقيم", "📋 قائمة المقيمين", "📊 الأرشيف والتقارير"]
if st.session_state.user_role == "admin":
    menu.insert(1, "⚙️ إدارة الغرف")

choice = st.sidebar.radio("انتقل إلى:", menu)
st.sidebar.markdown("---")
st.sidebar.write("🏷️ **المطور:**")
st.sidebar.code("®ridha_merzoug®")

# --- 6. الصفحات والوظائف ---

if choice == "🏠 لوحة التحكم":
    st.markdown("<h1 class='main-header'>🏠 حالة الإشغال الفوري</h1>", unsafe_allow_html=True)
    for group, rooms in ROOMS_CONFIG.items():
        st.subheader(group)
        cols = st.columns(len(rooms))
        for i, (r_name, max_b) in enumerate(rooms.items()):
            occ = st.session_state.db.get(r_name, {"occupied": 0})["occupied"]
            with cols[i]:
                color = "#dcfce7" if occ == 0 else ("#fee2e2" if occ >= max_b else "#fef9c3")
                st.markdown(f"<div style='background-color:{color}; padding:10px; border-radius:8px; text-align:center; border:1px solid #ccc;'><b>{r_name}</b><br>{occ}/{max_b}</div>", unsafe_allow_html=True)

elif choice == "⚙️ إدارة الغرف":
    st.markdown("<h1 class='main-header'>⚙️ إدارة الغرف (أدمن)</h1>", unsafe_allow_html=True)
    for r_name in ALL_ROOM_NAMES:
        max_v = next(v for g in ROOMS_CONFIG.values() for k,v in g.items() if k == r_name)
        curr = st.session_state.db[r_name]["occupied"]
        st.session_state.db[r_name]["occupied"] = st.number_input(f"إشغال {r_name}", 0, max_v, curr)
    if st.button("حفظ التعديلات"):
        save_data()
        st.success("تم التحديث")

elif choice == "👤 تسجيل مقيم":
    st.markdown("<h1 class='main-header'>👤 تسجيل وافد جديد</h1>", unsafe_allow_html=True)
    with st.form("entry"):
        name = st.text_input("اسم المقيم بالكامل")
        room = st.selectbox("الغرفة", ALL_ROOM_NAMES)
        is_free = st.checkbox("إقامة مجانية")
        if st.form_submit_button("تأكيد"):
            max_b = next(v for g in ROOMS_CONFIG.values() for k,v in g.items() if k == room)
            if st.session_state.db[room]["occupied"] < max_b:
                res = {"name": name, "room": room, "is_free": is_free, "entry": datetime.now().strftime("%Y-%m-%d %H:%M")}
                st.session_state.db[room]["residents"].append(res)
                st.session_state.db[room]["occupied"] += 1
                save_data()
                st.success("تم!")
            else: st.error("ممتلئة")

elif choice == "📋 قائمة المقيمين":
    st.markdown("<h1 class='main-header'>📋 المقيمين الحاليين</h1>", unsafe_allow_html=True)
    active = []
    for r in ALL_ROOM_NAMES:
        for idx, res in enumerate(st.session_state.db[r]["residents"]):
            days = max(1, (datetime.now() - datetime.strptime(res["entry"], "%Y-%m-%d %H:%M")).days)
            amt = 0 if res["is_free"] else days * BED_PRICE
            active.append({"الاسم": res["name"], "الغرفة": r, "الدخول": res["entry"], "المبلغ": amt, "idx": idx})
    
    if active:
        df = pd.DataFrame(active)
        st.table(df.drop(columns="idx"))
        target = st.selectbox("خروج مقيم:", range(len(active)), format_func=lambda x: active[x]["الاسم"])
        if st.button("تسجيل خروج ودفع"):
            sel = active[target]
            arch = st.session_state.db[sel["الغرفة"]]["residents"].pop(sel["idx"])
            arch["exit"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            arch["paid"] = sel["المبلغ"]
            st.session_state.db["archive"].append(arch)
            st.session_state.db[sel["الغرفة"]]["occupied"] -= 1
            save_data()
            st.rerun()

elif choice == "📊 الأرشيف والتقارير":
    st.markdown("<h1 class='main-header'>📊 الأرشيف والتقارير</h1>", unsafe_allow_html=True)
    if st.session_state.db["archive"]:
        df_arch = pd.DataFrame(st.session_state.db["archive"])
        st.dataframe(df_arch, use_container_width=True)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_arch.to_excel(writer, index=False)
        st.download_button("📥 تحميل Excel", output.getvalue(), f"تقرير_{date.today()}.xlsx")

# --- التوقيع النهائي ---
st.markdown("<div class='footer'>نظام إدارة بيت الشباب محمدي يوسف<br><b>مطور من طرف ®ridha_merzoug®</b></div>", unsafe_allow_html=True)

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.auth = False
    st.rerun()
