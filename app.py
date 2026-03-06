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
        "غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6,
        "مرقد ذكور": 3, "مرقد ذكور 02": 4
    },
    "جناح إناث": {
        "غرفة 06": 6, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6,
        "مرقد اناث 01": 3, "مرقد اناث 02": 4
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

# ────────────────────────────────────────────────
#               لوحة التحكم مع الجدول أولاً
# ────────────────────────────────────────────────
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
        def highlight_status(val):
            if "فارغة" in val:
                return "background-color: #d4edda; color: black;"
            elif "ممتلئة" in val:
                return "background-color: #f8d7da; color: black;"
            elif "مشغولة" in val:
                return "background-color: #fff3cd; color: black;"
            return ""

        styled_df = df.style.map(highlight_status, subset=["الحالة"])

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )

    # إجمالي عام تحت الجداول
    total_occupied = sum(r["occupied"] for r in data.values())
    st.markdown("---")
    cols = st.columns(3)
    cols[0].metric("إجمالي الأسرة الكلي", TOTAL_BEDS)
    cols[1].metric("المشغولة حاليًا", total_occupied)
    cols[2].metric("الفارغة", TOTAL_BEDS - total_occupied)

# ────────────────────────────────────────────────
#               باقي الصفحات (كما هي)
# ────────────────────────────────────────────────

# إدارة الغرف (للأدمن فقط)
elif page == "إدارة الغرف":
    st.title("🛏️ إدارة الغرف")
    for group_name, group in rooms_config.items():
        st.subheader(group_name)
        for room, max_beds in group.items():
            current = data.get(room, {"occupied": 0})["occupied"]
            new_occ = st.slider(f"عدد الأسرة المشغولة في {room} (أقصى {max_beds})", 0, max_beds, current, key=f"slider_{room}")
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
        max_beds = next(v for g in rooms_config.values() for k, v in g.items() if k == room)
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

# (باقي الصفحات: قائمة المقيمين، الحجوزات، إحصائيات متقدمة)
# إذا أردت إكمالها أو تعديلها أكثر، أخبرني

st.caption("نظام إدارة بيت الشباب محمدي يوسف © 2026")
