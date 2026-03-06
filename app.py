import streamlit as st
import json
from datetime import datetime, date
import pandas as pd
import io
import hashlib
from math import ceil

# --- إعدادات الصفحة ---
st.set_page_config(page_title="إدارة بيت الشباب محمدي يوسف", page_icon="🏢", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { direction: RTL; text-align: right; font-family: 'Cairo', sans-serif; }
    [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; background-color: #1e40af; color: white; border: none; padding: 0.6rem; }
    .main-header { text-align: center; color: #1e40af; background: #f0f4ff; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 2px solid #1e40af; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8fafc; color: #475569; text-align: center; padding: 8px; border-top: 1px solid #e2e8f0; font-weight: bold; z-index: 100; }
    .room-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)

# --- بيانات المستخدمين (مع hash بسيط) ---
def hash_password(pw, salt="youth_hostel_2026"):
    return hashlib.sha256((pw + salt).encode()).hexdigest()

USERS = {
    "admin": {"password_hash": hash_password("admin123"), "role": "admin"},
    "reception": {"password_hash": hash_password("recep2026"), "role": "user"}
}

ROOMS_CONFIG = {
    "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
    "جناح إناث": {"غرفة 06": 6, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد اناث 01": 3, "مرقد اناث 02": 4}
}
ALL_ROOM_NAMES = [room for group in ROOMS_CONFIG.values() for room in group.keys()]

# سعر افتراضي – يمكن تغييره من sidebar للأدمن
DEFAULT_BED_PRICE = 400

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
if "bed_price" not in st.session_state:
    st.session_state.bed_price = DEFAULT_BED_PRICE

# --- تسجيل الدخول ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<div class='main-header'><h1>🏢 إدارة بيت الشباب محمدي يوسف</h1></div>", unsafe_allow_html=True)
    user = st.text_input("👤 اسم المستخدم")
    pw = st.text_input("🔑 كلمة السر", type="password")
    if st.button("تسجيل الدخول"):
        if user in USERS and USERS[user]["password_hash"] == hash_password(pw):
            st.session_state.auth = True
            st.session_state.user_role = USERS[user]["role"]
            st.session_state.user_name = user
            st.rerun()
        else:
            st.error("بيانات خاطئة")
    st.markdown("<div class='footer'>مطور من طرف ®ridha_merzoug®</div>", unsafe_allow_html=True)
    st.stop()

# --- القائمة الجانبية ---
st.sidebar.markdown(f"### 👤 المستخدم: {st.session_state.user_name} ({st.session_state.user_role})")
if st.session_state.user_role == "admin":
    st.sidebar.markdown("### ⚙️ إعدادات الأدمن")
    st.session_state.bed_price = st.sidebar.number_input("سعر السرير اليومي (دج)", value=st.session_state.bed_price, min_value=100, step=50)

menu = ["📊 الإحصائيات المالية", "🏨 إدارة الغرف والحجز", "👥 قائمة النزلاء", "📂 الأرشيف"]
choice = st.sidebar.radio("القائمة الرئيسية", menu)

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.auth = False
    st.rerun()

# --- الصفحات ---

# 1. الإحصائيات
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

# 2. إدارة الغرف
elif choice == "🏨 إدارة الغرف والحجز":
    st.markdown("<div class='main-header'><h2>🏨 وضعية الغرف محمدي يوسف</h2></div>", unsafe_allow_html=True)
    
    for group, rooms in ROOMS_CONFIG.items():
        st.subheader(group)
        for r, max_b in rooms.items():
            occ = len(st.session_state.db[r]["residents"])
            status = "🔴 ممتلئة" if occ >= max_b else "🟢 متاحة"
            with st.expander(f"{r} - {occ}/{max_b} ({status})", expanded=False):
                st.markdown(f"<div class='room-card'>السعة: {max_b} | المشغول: {occ} | المتاح: {max_b - occ}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("➕ تسجيل مقيم جديد")
    with st.form("add_form"):
        col1, col2 = st.columns(2)
        f_name = col1.text_input("اسم المقيم الكامل")
        f_room = col1.selectbox("اختر الغرفة", ALL_ROOM_NAMES)
        f_gender = col2.selectbox("الجنس", ["ذكر", "أنثى"])
        f_nation = col2.text_input("الجنسية", "جزائرية")
        f_kids = st.number_input("عدد الأطفال", 0, 10)
        f_free = st.checkbox("إقامة مجانية")
        if st.form_submit_button("حفظ البيانات"):
            max_b = next(v for g in ROOMS_CONFIG.values() for k,v in g.items() if k == f_room)
            if len(st.session_state.db[f_room]["residents"]) < max_b:
                st.session_state.db[f_room]["residents"].append({
                    "name": f_name.strip(), "gender": f_gender, "nation": f_nation.strip(), 
                    "kids": f_kids, "is_free": f_free, 
                    "entry": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                save_data()
                st.success("تم التسجيل بنجاح")
                st.rerun()
            else:
                st.error("الغرفة ممتلئة")

# 3. قائمة النزلاء + تعديل + خروج مع تأكيد
elif choice == "👥 قائمة النزلاء":
    st.markdown("<div class='main-header'><h2>👥 قائمة النزلاء الحاليين</h2></div>", unsafe_allow_html=True)
    
    if "confirm_exit" not in st.session_state:
        st.session_state.confirm_exit = None

    for r in ALL_ROOM_NAMES:
        res_list = st.session_state.db[r]["residents"]
        with st.expander(f"🏠 {r} ({len(res_list)} فرد)", expanded=False):
            if not res_list:
                st.info("فارغة")
                continue
            for idx, p in enumerate(res_list):
                entry_dt = datetime.strptime(p["entry"], "%Y-%m-%d %H:%M")
                delta = datetime.now() - entry_dt
                nights = max(1, ceil(delta.total_seconds() / 86400))  # عدد الليالي الدقيق
                total = 0 if p["is_free"] else nights * st.session_state.bed_price
                
                st.markdown(f"<div class='room-card'><strong>{p['name']}</strong> ({p['gender']}) - {p['nation']}<br>دخول: {p['entry']}<br>الليالي: {nights} | المبلغ: {total} دج</div>", unsafe_allow_html=True)
                
                col_edit, col_exit = st.columns(2)
                if col_edit.button("✏️ تعديل", key=f"edit_{r}_{idx}"):
                    with st.form(f"edit_form_{r}_{idx}"):
                        edit_name = st.text_input("الاسم", value=p["name"])
                        edit_nation = st.text_input("الجنسية", value=p["nation"])
                        edit_kids = st.number_input("عدد الأطفال", value=p["kids"])
                        edit_free = st.checkbox("إقامة مجانية", value=p["is_free"])
                        if st.form_submit_button("حفظ التعديل"):
                            p["name"] = edit_name.strip()
                            p["nation"] = edit_nation.strip()
                            p["kids"] = edit_kids
                            p["is_free"] = edit_free
                            save_data()
                            st.success("تم التعديل")
                            st.rerun()

                if col_exit.button("🚪 خروج", key=f"exit_{r}_{idx}"):
                    st.session_state.confirm_exit = (r, idx, total)
                    st.rerun()

    # نافذة التأكيد
    if st.session_state.confirm_exit:
        r, idx, total = st.session_state.confirm_exit
        st.warning(f"هل أنت متأكد من خروج **{st.session_state.db[r]['residents'][idx]['name']}** ؟\nالمبلغ المستحق: {total} دج")
        col_yes, col_no = st.columns(2)
        if col_yes.button("نعم، خروج نهائي"):
            p = st.session_state.db[r]["residents"].pop(idx)
            p.update({"exit": datetime.now().strftime("%Y-%m-%d %H:%M"), "paid_val": total, "room": r})
            st.session_state.db["archive"].append(p)
            save_data()
            st.session_state.confirm_exit = None
            st.success("تم تسجيل الخروج")
            st.rerun()
        if col_no.button("إلغاء"):
            st.session_state.confirm_exit = None
            st.rerun()

# 4. الأرشيف + بحث
elif choice == "📂 الأرشيف":
    st.markdown("<div class='main-header'><h2>📂 الأرشيف التاريخي</h2></div>", unsafe_allow_html=True)
    
    search_name = st.text_input("ابحث بالاسم")
    search_room = st.selectbox("ابحث بالغرفة", ["الكل"] + ALL_ROOM_NAMES)
    
    archive = st.session_state.db["archive"]
    filtered = archive
    if search_name:
        filtered = [e for e in filtered if search_name.lower() in e["name"].lower()]
    if search_room != "الكل":
        filtered = [e for e in filtered if e.get("room") == search_room]
    
    if filtered:
        df_arch = pd.DataFrame(filtered).rename(columns={
            "name": "الاسم", "gender": "الجنس", "nation": "الجنسية", "kids": "الأطفال",
            "entry": "الدخول", "exit": "الخروج", "paid_val": "المبلغ", "room": "الغرفة"
        })
        st.dataframe(df_arch, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_arch.to_excel(writer, index=False)
        st.download_button("📥 تحميل التقرير (Excel)", output.getvalue(), f"أرشيف_{date.today()}.xlsx")
    else:
        st.info("لا توجد نتائج مطابقة للبحث")

# التوقيع
st.markdown("<div class='footer'>إدارة بيت الشباب محمدي يوسف - مطور من طرف ®ridha_merzoug® - نسخة محدثة 2026</div>", unsafe_allow_html=True)
