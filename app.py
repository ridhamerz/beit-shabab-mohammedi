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
    st.title("🏠 لوحة التحكم")
    occupied = sum(r["occupied"] for r in data.values())
    cols = st.columns(3)
    cols[0].metric("إجمالي الأسرة", TOTAL_BEDS)
    cols[1].metric("المشغولة حالياً", occupied)
    cols[2].metric("الفارغة", TOTAL_BEDS - occupied)

# إدارة الغرف (للأدمن فقط)
elif page == "إدارة الغرف":
    st.title("🛏️ إدارة الغرف")
    for group_name, group in rooms_config.items():
        st.subheader(group_name)
        for room, max_beds in group.items():
            current = data[room]["occupied"]
            new_occ = st.slider(f"عدد الأسرة المشغولة في {room} (أقصى {max_beds})", 0, max_beds, current, key=room)
            if st.button(f"حفظ {room}"):
                data[room]["occupied"] = new_occ
                save_data()
                st.success(f"تم حفظ {room}")

# تسجيل دخول مقيم
elif page == "تسجيل دخول مقيم":
    st.title("👤 تسجيل دخول مقيم")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("اسم المقيم")
        gender = st.radio("الجنس", ["ذكر", "أنثى"])
        age_group = st.radio("الفئة", ["رجل/امرأة", "طفل"])
        nationality = st.selectbox("الجنسية", ["جزائري", "أجنبي"])
        room = st.selectbox("الغرفة", ghoraf)
    with col2:
        is_free = st.checkbox("إقامة مجانية")
        from_who = st.text_input("من طرف من؟")
    notes = st.text_area("ملاحظات")

    if st.button("تسجيل"):
        max_beds = [v for group in rooms_config.values() for k, v in group.items() if k == room][0]
        if data[room]["occupied"] >= max_beds:
            st.error("الغرفة ممتلئة")
        else:
            entry_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            data[room]["residents"].append({
                "name": name,
                "gender": gender,
                "age_group": age_group,
                "nationality": nationality,
                "entry_time": entry_time,
                "exit_time": None,
                "is_free": is_free,
                "from_who": from_who,
                "notes": notes
            })
            data[room]["occupied"] += 1
            save_data()
            st.success("تم التسجيل")

# قائمة المقيمين
elif page == "قائمة المقيمين":
    st.title("📋 قائمة المقيمين")
    # (كما هو في الكود السابق، مع إضافة عرض الجنسية والجنس والعمر في الجدول)

# الحجوزات
elif page == "الحجوزات":
    st.title("📅 الحجوزات للأفواج")
    if st.session_state.role == "admin" or st.session_state.role == "user":
        room = st.selectbox("الغرفة", ghoraf)
        from_date = st.date_input("من تاريخ")
        to_date = st.date_input("إلى تاريخ")
        group_name = st.text_input("اسم الفوج")
        num_people = st.number_input("عدد الأشخاص", min_value=1)
        notes = st.text_area("ملاحظات")

        if st.button("حجز"):
            data[room]["reservations"].append({
                "group_name": group_name,
                "from_date": str(from_date),
                "to_date": str(to_date),
                "num_people": num_people,
                "notes": notes
            })
            save_data()
            st.success("تم الحجز")

    # عرض الحجوزات
    st.subheader("الحجوزات الحالية")
    for room in ghoraf:
        if data[room]["reservations"]:
            st.write(f"**{room}:**")
            for res in data[room]["reservations"]:
                st.write(f"{res['group_name']} من {res['from_date']} إلى {res['to_date']} ({res['num_people']} شخص)")

# إحصائيات متقدمة
elif page == "إحصائيات متقدمة":
    st.title("إحصائيات متقدمة")
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")

    # حسابات يومي وشهري
    daily_income = 0
    monthly_income = 0
    daily_guests = 0
    monthly_guests = 0
    males = females = children = foreigners = free = 0

    for room in data.values():
        for res in room["residents"]:
            entry_day = res["entry_time"][:10]
            entry_month = res["entry_time"][:7]
            if entry_day == today:
                daily_guests += 1
                if not res["is_free"]:
                    daily_income += BED_PRICE
                if res["gender"] == "ذكر":
                    males += 1
                elif res["gender"] == "أنثى":
                    females += 1
                if res["age_group"] == "طفل":
                    children += 1
                if res["nationality"] == "أجنبي":
                    foreigners += 1
                if res["is_free"]:
                    free += 1
            if entry_month == month:
                monthly_guests += 1
                if not res["is_free"]:
                    monthly_income += BED_PRICE

    stats_data = {
        "الإحصائية": ["مدخول اليوم", "مدخول الشهر", "مجموع النزلاء اليوم", "مجموع النزلاء الشهر", "عدد الذكور", "عدد الإناث", "عدد الأطفال", "عدد الأجانب", "عدد المجانيين"],
        "القيمة": [daily_income, monthly_income, daily_guests, monthly_guests, males, females, children, foreigners, free]
    }

    df = pd.DataFrame(stats_data)
    st.table(df)

st.caption("نظام إدارة بيت الشباب محمدي يوسف © 2026 _ridha_merzoug 😊")
