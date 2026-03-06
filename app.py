import streamlit as st
import json
from datetime import datetime, date
import pandas as pd
import io

st.set_page_config(page_title="إدارة بيت الشباب محمدي يوسف", page_icon="🛏️", layout="wide")

st.markdown("""
<style>
    .main {direction: RTL; text-align: right; font-family: 'Cairo', sans-serif;}
    .stButton>button {width: 100%; font-size: 18px;}
    h1, h2, h3 {text-align: center; color: #1e40af;}
</style>
""", unsafe_allow_html=True)

# نظام المستخدمين + الصلاحيات
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "reception": {"password": "recep2026", "role": "user"}
    # أضف مستخدمين جدد هنا
}

# الغرف الجديدة مع عدد الأسرة
rooms_config = {
    "جناح ذكور": {
        "غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "مرقد ذكور": 3, "مرقد ذكور 02": 4
    },
    "جناح إناث": {
        "غرفة 06": 6, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد اناث 01": 3, "مرقد اناث 02": 4
    }
}
all_rooms = []
for group in rooms_config.values():
    all_rooms.extend(group.keys())
ghoraf = all_rooms
TOTAL_BEDS = sum(sum(group.values()) for group in rooms_config.values())

BED_PRICE = 400  # دج لليلة الواحدة

def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {room: {"occupied": 0, "residents": [], "reservations": []} for room in ghoraf}

def save_data():
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)

# تسجيل الدخول
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("🔐 إدارة بيت الشباب محمدي يوسف")
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة السر", type="password")
    if st.button("دخول"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = USERS[username]["role"]
            st.rerun()
        else:
            st.error("اسم المستخدم أو كلمة السر خاطئة")
    st.stop()

st.sidebar.title(f"🛏️ مرحباً {st.session_state.username} ({st.session_state.role})")

# قائمة الصفحات حسب الصلاحية
pages = ["لوحة التحكم", "تسجيل دخول مقيم", "قائمة المقيمين", "الحجوزات", "إحصائيات متقدمة"]
if st.session_state.role == "admin":
    pages.insert(1, "إدارة الغرف")

page = st.sidebar.radio("القائمة", pages)

data = st.session_state.setdefault("data", load_data())

# لوحة التحكم (بدون الدخل المتوقع)
    st.title("🏠 لوحة التحكم")
import streamlit as st
import json
from datetime import datetime, date
import pandas as pd
import io

st.set_page_config(page_title="إدارة بيت الشباب محمدي يوسف", page_icon="🛏️", layout="wide")

st.markdown("""
<style>
    .main {direction: RTL; text-align: right; font-family: 'Cairo', sans-serif;}
    .stButton>button {width: 100%; font-size: 18px;}
    h1, h2, h3 {text-align: center; color: #1e40af;}
</style>
""", unsafe_allow_html=True)

# نظام المستخدمين + الصلاحيات
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "reception": {"password": "recep2026", "role": "user"}
    # أضف مستخدمين جدد هنا
}

# الغرف الجديدة مع عدد الأسرة
rooms_config = {
    "جناح ذكور": {
        "غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "مرقد ذكور": 3, "مرقد ذكور 02": 4
    },
    "جناح إناث": {
        "غرفة 06": 6, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد اناث 01": 3, "مرقد اناث 02": 4
    }
}
all_rooms = []
for group in rooms_config.values():
    all_rooms.extend(group.keys())
ghoraf = all_rooms
TOTAL_BEDS = sum(sum(group.values()) for group in rooms_config.values())

BED_PRICE = 400  # دج لليلة الواحدة

def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {room: {"occupied": 0, "residents": [], "reservations": []} for room in ghoraf}

def save_data():
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)

# تسجيل الدخول
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("🔐 إدارة بيت الشباب محمدي يوسف")
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة السر", type="password")
    if st.button("دخول"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = USERS[username]["role"]
            st.rerun()
        else:
            st.error("اسم المستخدم أو كلمة السر خاطئة")
    st.stop()

st.sidebar.title(f"🛏️ مرحباً {st.session_state.username} ({st.session_state.role})")

# قائمة الصفحات حسب الصلاحية
pages = ["لوحة التحكم", "تسجيل دخول مقيم", "قائمة المقيمين", "الحجوزات", "إحصائيات متقدمة"]
if st.session_state.role == "admin":
    pages.insert(1, "إدارة الغرف")

page = st.sidebar.radio("القائمة", pages)

data = st.session_state.setdefault("data", load_data())

# لوحة التحكم (بدون الدخل المتوقع)
if page == "لوحة التحكم":
    st.title("🏠 لوحة التحكم - نظرة عامة على الغرف")

    # عرض الجدول لكل مجموعة
    for group_name, group in rooms_config.items():
        st.subheader(group_name)

        table_data = []
        for room, max_beds in group.items():
            occupied = data.get(room, {"occupied": 0})["occupied"]
            free = max_beds - occupied

            # تحديد اللون والحالة
            if occupied == 0:
                status = "🟢 فارغة تمامًا"
                color = "background-color: #d4edda; color: black;"
            elif occupied == max_beds:
                status = "🔴 ممتلئة"
                color = "background-color: #f8d7da; color: black;"
            else:
                status = f"🟡 مشغولة جزئيًا ({occupied}/{max_beds})"
                color = "background-color: #fff3cd; color: black;"

            table_data.append([room, max_beds, occupied, free, status])

        # إنشاء DataFrame
        df = pd.DataFrame(table_data, columns=["اسم الغرفة", "إجمالي الأسرة", "مشغولة", "فارغة", "الحالة"])

        # تنسيق الجدول بالألوان
        styled_df = df.style.applymap(
            lambda val: color if "الحالة" in df.columns and val == df.loc[df.index[df["الحالة"] == val].tolist()[0], "الحالة"] else None,
            subset=["الحالة"]
        )

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "الحالة": st.column_config.TextColumn("الحالة", width="medium")
            }
        )

    # إجمالي عام تحت الجداول
    total_occupied = sum(r["occupied"] for r in data.values())
    st.markdown("---")
    cols = st.columns(3)
    cols[0].metric("إجمالي الأسرة الكلي", TOTAL_BEDS)
    cols[1].metric("المشغولة حاليًا", total_occupied)
    cols[2].metric("الفارغة", TOTAL_BEDS - total_occupied)

st.caption("نظام إدارة بيت الشباب محمدي يوسف © 2026 _ridha_merzoug 😊")
