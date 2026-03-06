import streamlit as st
import json
from datetime import datetime
import pandas as pd
import io

st.set_page_config(page_title="بيت الشباب محمدي يوسف", page_icon="🛏️", layout="wide")

st.markdown("""
<style>
    .main {direction: RTL; text-align: right; font-family: 'Cairo', sans-serif;}
    .stButton>button {width: 100%; font-size: 18px;}
    h1, h2, h3 {text-align: center; color: #1e40af;}
</style>
""", unsafe_allow_html=True)

# نظام مستخدمين بسيط (يمكن توسيعه لاحقًا)
USERS = {
    "admin": "admin123",       # غيّر كلمة السر فوراً
    "karim": "karim2026",      # أضف مستخدمين إضافيين هنا
    "reception": "recep2026"
}

# قائمة الغرف
ghoraf = ["1","2","3","4","5","م ذ","م ذ2","جناح ذكور","7","8","9","مرقد إناث","مرقد إناث 2","جناح عائلي"]
TOTAL_BEDS = len(ghoraf) * 6

def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {room: {"occupied": 0, "residents": []} for room in ghoraf}

def save_data():
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)

# تسجيل الدخول
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

if not st.session_state.logged_in:
    st.title("🔐 نظام إدارة بيت الشباب محمدي يوسف")
    col1, col2 = st.columns([3,2])
    with col1:
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة السر", type="password")
    if st.button("دخول"):
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("اسم المستخدم أو كلمة السر خاطئة")
    st.stop()

st.sidebar.title(f"🛏️ مرحباً {st.session_state.username}")
page = st.sidebar.radio("القائمة", 
    ["لوحة التحكم", "إدارة الغرف", "تسجيل دخول مقيم", "قائمة المقيمين", "إحصائيات النزلاء خلال الشهر", "تقارير وتصدير"])

data = st.session_state.setdefault("data", load_data())

# لوحة التحكم
if page == "لوحة التحكم":
    st.title("🏠 لوحة التحكم")
    occupied = sum(r["occupied"] for r in data.values())
    empty = TOTAL_BEDS - occupied
    daily = occupied * 400
    monthly = daily * 30

    cols = st.columns(4)
    cols[0].metric("إجمالي الأسرّة", f"{TOTAL_BEDS}")
    cols[1].metric("المشغولة حالياً", occupied)
    cols[2].metric("الفارغة", empty, delta_color="inverse")
    cols[3].metric("الدخل اليومي", f"{daily:,} دج")

    st.success(f"الدخل الشهري المتوقع ≈ {monthly:,} دج")

# إدارة الغرف (عدد مشغول يدوياً)
elif page == "إدارة الغرف":
    st.title("🛏️ إدارة الغرف")
    room = st.selectbox("اختر الغرفة", ghoraf)
    current = data[room]["occupied"]
    new_val = st.slider("عدد الأسرة المشغولة", 0, 6, current)
    if st.button("حفظ"):
        data[room]["occupied"] = new_val
        save_data()
        st.success(f"تم تحديث غرفة {room}")

# تسجيل دخول مقيم جديد (مع إضافة الجنس والعمر)
elif page == "تسجيل دخول مقيم":
    st.title("👤 تسجيل دخول مقيم")
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("اسم المقيم")
        room = st.selectbox("الغرفة", ghoraf)
    with col2:
        gender = st.radio("الجنس", ["ذكر", "أنثى"], horizontal=True)
        age_group = st.radio("الفئة العمرية", ["بالغ", "طفل (أقل من 12 سنة)"], horizontal=True)
        is_free = st.checkbox("إقامة مجانية")
    with col3:
        from_who = st.text_input("من طرف من؟")
    notes = st.text_area("ملاحظات إضافية")

    if st.button("تسجيل الدخول", type="primary"):
        if data[room]["occupied"] >= 6:
            st.error("الغرفة ممتلئة")
        else:
            entry_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            data[room]["residents"].append({
                "name": name or "بدون اسم",
                "entry_time": entry_time,
                "exit_time": None,
                "gender": gender,
                "age_group": age_group,
                "is_free": is_free,
                "from_who": from_who,
                "notes": notes,
                "registered_by": st.session_state.username
            })
            data[room]["occupied"] += 1
            save_data()
            st.success(f"تم تسجيل {name} ({gender} - {age_group})")

# قائمة المقيمين + تعديل + خروج + حذف (بقي كما هو)
elif page == "قائمة المقيمين":
    st.title("📋 قائمة المقيمين الحاليين")

    tab_view, tab_edit = st.tabs(["عرض الكل", "تعديل / خروج"])

    with tab_view:
        all_res = []
        for rname, info in data.items():
            for idx, res in enumerate(info["residents"]):
                if res["exit_time"] is None:  # فقط الموجودين حالياً
                    status = "🆓 مجاني" if res["is_free"] else "💰 مدفوع"
                    all_res.append({
                        "الاسم": res["name"],
                        "الغرفة": rname,
                        "دخول": res["entry_time"],
                        "الحالة": status,
                        "من طرف": res["from_who"],
                        "ملاحظات": res["notes"],
                        "مسجل بواسطة": res.get("registered_by", "?")
                    })
        if all_res:
            df = pd.DataFrame(all_res)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("لا يوجد مقيمون حالياً")

    with tab_edit:
        selected_room = st.selectbox("اختر الغرفة", ghoraf, key="edit_room")
        residents = [r for r in data[selected_room]["residents"] if r["exit_time"] is None]

        if residents:
            for i, res in enumerate(residents):
                with st.expander(f"{res['name']} — دخول: {res['entry_time']}"):
                    new_name = st.text_input("الاسم", value=res["name"], key=f"name_{i}")
                    new_free = st.checkbox("مجاني", value=res["is_free"], key=f"free_{i}")
                    new_from = st.text_input("من طرف", value=res["from_who"], key=f"from_{i}")
                    new_notes = st.text_area("ملاحظات", value=res["notes"], key=f"notes_{i}")

                    colA, colB, colC = st.columns(3)
                    with colA:
                        if st.button("💾 حفظ التعديلات", key=f"save_{i}"):
                            res["name"] = new_name
                            res["is_free"] = new_free
                            res["from_who"] = new_from
                            res["notes"] = new_notes
                            save_data()
                            st.success("تم الحفظ")
                            st.rerun()
                    with colB:
                        if st.button("🚪 تسجيل خروج", key=f"checkout_{i}"):
                            res["exit_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            data[selected_room]["occupied"] = max(0, data[selected_room]["occupied"] - 1)
                            save_data()
                            st.success("تم تسجيل الخروج")
                            st.rerun()
                    with colC:
                        if st.button("🗑️ حذف نهائي", key=f"del_{i}"):
                            if st.checkbox("تأكيد الحذف النهائي؟"):
                                data[selected_room]["residents"].remove(res)
                                data[selected_room]["occupied"] = max(0, data[selected_room]["occupied"] - 1)
                                save_data()
                                st.success("تم الحذف")
                                st.rerun()
        else:
            st.info("لا يوجد مقيمون حاليون في هذه الغرفة")

# إحصائيات النزلاء خلال الشهر (كل من سكن في الشهر، حتى لو خرج)
elif page == "إحصائيات النزلاء خلال الشهر":
    st.title("إحصائيات النزلاء خلال الشهر")

    # جمع كل التواريخ المتاحة للدخول (لعمل قائمة شهور)
    all_entry_months = set()
    for room_data in data.values():
        for res in room_data["residents"]:
            if "entry_time" in res:
                month = res["entry_time"][:7]  # YYYY-MM
                all_entry_months.add(month)
    
    months_list = sorted(list(all_entry_months), reverse=True)
    if not months_list:
        months_list = [datetime.now().strftime("%Y-%m")]

    selected_month = st.selectbox("اختر الشهر", months_list, index=0)

    # جمع البيانات للشهر المختار
    monthly_residents = []
    males = females = children = male_children = female_children = 0

    for room_name, room_data in data.items():
        for res in room_data["residents"]:
            if "entry_time" in res:
                entry_month = res["entry_time"][:7]
                if entry_month == selected_month:
                    g = res.get("gender", "غير محدد")
                    ag = res.get("age_group", "بالغ")
                    status = "خرج" if res.get("exit_time") else "موجود حالياً"

                    monthly_residents.append({
                        "الاسم": res["name"],
                        "الغرفة": room_name,
                        "دخول": res["entry_time"],
                        "خروج": res.get("exit_time", "لا يزال موجود"),
                        "الجنس": g,
                        "الفئة العمرية": ag,
                        "مجاني": "نعم" if res.get("is_free", False) else "لا",
                        "من طرف": res.get("from_who", ""),
                        "مسجل بواسطة": res.get("registered_by", "?"),
                        "الحالة": status
                    })

                    # الحسابات
                    if g == "ذكر":
                        males += 1
                        if ag == "طفل (أقل من 12 سنة)":
                            male_children += 1
                            children += 1
                    elif g == "أنثى":
                        females += 1
                        if ag == "طفل (أقل من 12 سنة)":
                            female_children += 1
                            children += 1

    # عرض الإجماليات
    cols = st.columns(5)
    cols[0].metric("عدد الذكور", males)
    cols[1].metric("عدد الإناث", females)
    cols[2].metric("إجمالي الأولاد", children)
    cols[3].metric("أولاد ذكور", male_children)
    cols[4].metric("أولاد إناث", female_children)

    st.markdown(f"**إجمالي النزلاء في {selected_month} : {len(monthly_residents)} شخص**")

    if monthly_residents:
        df = pd.DataFrame(monthly_residents)
        st.dataframe(
            df.sort_values(by="دخول", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        # زر تصدير CSV لهذا الشهر
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        st.download_button(
            label=f"تصدير نزلاء شهر {selected_month} (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"نزلاء_{selected_month}.csv",
            mime="text/csv"
        )
    else:
        st.info(f"لا يوجد نزلاء مسجلين في شهر {selected_month}")

# تقارير + تصدير CSV (الباقي كما هو)
elif page == "تقارير وتصدير":
    st.title("📊 التقارير والتصدير")
    occupied = sum(r["occupied"] for r in data.values())
    st.metric("الأسرة المشغولة حالياً", occupied, f"{TOTAL_BEDS - occupied} فارغة")

    # تصدير CSV
    if st.button("📥 تصدير قائمة المقيمين الحاليين (CSV)"):
        current_residents = []
        for rname, info in data.items():
            for res in info["residents"]:
                if res["exit_time"] is None:
                    current_residents.append({
                        "الاسم": res["name"],
                        "الغرفة": rname,
                        "دخول": res["entry_time"],
                        "مجاني": "نعم" if res["is_free"] else "لا",
                        "من طرف": res["from_who"],
                        "ملاحظات": res["notes"],
                        "مسجل بواسطة": res.get("registered_by", "?")
                    })
        if current_residents:
            df = pd.DataFrame(current_residents)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="تحميل الملف CSV",
                data=csv,
                file_name=f"مقيمون_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.info("لا يوجد بيانات للتصدير حالياً")

st.caption("نظام إدارة بيت الشباب محمدي يوسف • © 2026 • تم التطوير بواسطة رضا مرزوق مع مساعدة Grok")
