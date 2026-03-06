import streamlit as st
import json
from datetime import datetime, date
import pandas as pd
import io

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="إدارة بيت الشباب - محمدي يوسف", page_icon="🏢", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { direction: RTL; text-align: right; font-family: 'Cairo', sans-serif; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; background-color: #1e40af; color: white; }
    .main-header { text-align: center; color: #1e40af; background: #f0f4ff; padding: 15px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #1e40af; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8fafc; color: #475569; text-align: center; padding: 5px; border-top: 1px solid #e2e8f0; font-weight: bold; z-index: 100; }
    .stMetric { background: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# --- 2. البيانات الأساسية ---
USERS = {"admin": {"password": "admin123", "role": "admin"}, "reception": {"password": "recep2026", "role": "user"}}

ROOMS_CONFIG = {
    "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
    "جناح إناث": {"غرفة 06": 6, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد اناث 01": 3, "مرقد اناث 02": 4}
}
ALL_ROOM_NAMES = [room for group in ROOMS_CONFIG.values() for room in group.keys()]
BED_PRICE = 400 

# --- 3. وظائف البيانات ---
def load_data():
    try:
        with open("youth_hostel_pro_db.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if "archive" not in data: data["archive"] = []
            return data
    except:
        return {room: {"residents": []} for room in ALL_ROOM_NAMES} | {"archive": []}

def save_data():
    with open("youth_hostel_pro_db.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.db, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state:
    st.session_state.db = load_data()

# --- 4. تسجيل الدخول ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<div class='main-header'><h1>🏢 نظام الإدارة والمحاسبة الذكي</h1></div>", unsafe_allow_html=True)
    user = st.text_input("👤 اسم المستخدم")
    pw = st.text_input("🔑 كلمة السر", type="password")
    if st.button("دخول"):
        if user in USERS and USERS[user]["password"] == pw:
            st.session_state.auth, st.session_state.user_role, st.session_state.user_name = True, USERS[user]["role"], user
            st.rerun()
    st.markdown("<div class='footer'>مطور من طرف ®ridha_merzoug®</div>", unsafe_allow_html=True)
    st.stop()

# --- 5. القائمة الجانبية ---
st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
menu = ["📊 الإحصائيات العامة", "🏨 إدارة الغرف والحجز", "👥 قائمة النزلاء", "📂 الأرشيف"]
choice = st.sidebar.radio("القائمة", menu)

# --- 6. الصفحات ---

# صفحة 1: الإحصائيات (شاملة الجنس والجنسية والدخل)
if choice == "📊 الإحصائيات العامة":
    st.markdown("<h2 class='main-header'>📊 الملخص الإحصائي والمالي</h2>", unsafe_allow_html=True)
    
    # حساب المقيمين حالياً بالتفصيل
    current_residents = []
    for r in ALL_ROOM_NAMES:
        current_residents.extend(st.session_state.db[r]["residents"])
    
    total_res = len(current_residents)
    males = len([p for p in current_residents if p['gender'] == "ذكر"])
    females = len([p for p in current_residents if p['gender'] == "أنثى"])
    foreigners = len([p for p in current_residents if p['nation'].lower() != "جزائرية" and p['nation'].lower() != "جزائري"])
    
    # حساب الدخل
    today_str = date.today().strftime("%Y-%m-%d")
    month_str = date.today().strftime("%Y-%m")
    daily_rev = sum(e.get("paid_val", 0) for e in st.session_state.db["archive"] if e.get("exit", "").startswith(today_str))
    monthly_rev = sum(e.get("paid_val", 0) for e in st.session_state.db["archive"] if e.get("exit", "").startswith(month_str))

    # عرض المربعات الإحصائية
    c1, c2, c3 = st.columns(3)
    c1.metric("👥 إجمالي المقيمين", f"{total_res} فرد")
    c2.metric("💰 الدخل اليومي", f"{daily_rev} دج")
    c3.metric("📅 الدخل الشهري", f"{monthly_rev} دج")
    
    st.markdown("---")
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("👨 عدد الذكور", f"{males}")
    cc2.metric("👩 عدد الإناث", f"{females}")
    cc3.metric("🌍 عدد الأجانب", f"{foreigners}")

# صفحة 2: إدارة الغرف والحجز
elif choice == "🏨 إدارة الغرف والحجز":
    st.markdown("<h2 class='main-header'>🏨 وضعية الغرف وتسجيل الحجز</h2>", unsafe_allow_html=True)
    
    status_data = []
    for r in ALL_ROOM_NAMES:
        max_b = next(v for g in ROOMS_CONFIG.values() for k,v in g.items() if k == r)
        occ = len(st.session_state.db[r]["residents"])
        status_data.append({"الغرفة": r, "السعة": max_b, "المشغول": occ, "المتاح": max_b - occ, "الحالة": "🔴 ممتلئة" if occ >= max_b else "🟢 متاحة"})
    st.table(pd.DataFrame(status_data))

    st.markdown("---")
    st.subheader("➕ إضافة مقيم جديد")
    with st.form("add_res"):
        c1, c2, c3 = st.columns(3)
        f_name = c1.text_input("اسم المقيم الكامل")
        f_room = c2.selectbox("الغرفة", ALL_ROOM_NAMES)
        f_gender = c3.selectbox("الجنس", ["ذكر", "أنثى"])
        
        c4, c5, c6 = st.columns(3)
        f_nation = c4.text_input("الجنسية (مثلاً: جزائرية، تونسية...)", "جزائرية")
        f_kids = c5.number_input("عدد الأطفال", 0, 10)
        f_free = c6.checkbox("إقامة مجانية")
        
        if st.form_submit_button("حفظ الحجز"):
            max_b = next(v for g in ROOMS_CONFIG.values() for k,v in g.items() if k == f_room)
            if len(st.session_state.db[f_room]["residents"]) < max_b:
                st.session_state.db[f_room]["residents"].append({
                    "name": f_name, "gender": f_gender, "nation": f_nation, 
                    "kids": f_kids, "is_free": f_free, 
                    "entry": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                save_data()
                st.success(f"تم تسجيل {f_name}")
                st.rerun()
            else: st.error("الغرفة ممتلئة")

# صفحة 3: قائمة النزلاء (قائمة منسدلة لكل غرفة)
elif choice == "👥 قائمة النزلاء":
    st.markdown("<h2 class='main-header'>👥 تفاصيل المقيمين حسب الغرف</h2>", unsafe_allow_html=True)
    
    for r in ALL_ROOM_NAMES:
        res_list = st.session_state.db[r]["residents"]
        with st.expander(f"🏠 {r} - ({len(res_list)} مقيمين)", expanded=False):
            if res_list:
                for idx, p in enumerate(res_list):
                    entry_dt = datetime.strptime(p["entry"], "%Y-%m-%d %H:%M")
                    days = max(1, (datetime.now() - entry_dt).days)
                    total = 0 if p["is_free"] else days * BED_PRICE
                    
                    cc1, cc2, cc3, cc4, cc5 = st.columns([2,1,1,1,1])
                    cc1.write(f"**الاسم:** {p['name']} ({p['gender']})")
                    cc2.write(f"**الجنسية:** {p['nation']}")
                    cc3.write(f"**أطفال:** {p['kids']}")
                    cc4.write(f"**المبلغ:** {total} دج")
                    
                    if cc5.button("خروج", key=f"out_{r}_{idx}"):
                        p["exit"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        p["paid_val"] = total
                        p["room"] = r
                        st.session_state.db["archive"].append(p)
                        st.session_state.db[r]["residents"].pop(idx)
                        save_data()
                        st.rerun()
            else:
                st.write("الغرفة فارغة")

# صفحة 4: الأرشيف
elif choice == "📂 الأرشيف":
    st.markdown("<h2 class='main-header'>📂 أرشيف البيانات والتقارير</h2>", unsafe_allow_html=True)
    if st.session_state.db["archive"]:
        df_arch = pd.DataFrame(st.session_state.db["archive"])
        # إعادة تسمية الأعمدة للعربية في التقرير
        df_display = df_arch.rename(columns={
            "name": "الاسم", "gender": "الجنس", "nation": "الجنسية", 
            "kids": "الأطفال", "entry": "الدخول", "exit": "الخروج", 
            "paid_val": "المبلغ المدفوع", "room": "الغرفة"
        })
        st.dataframe(df_display, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_display.to_excel(writer, index=False)
        st.download_button("📥 تحميل التقرير الشامل Excel", output.getvalue(), f"تقرير_{date.today()}.xlsx")

# التوقيع
st.markdown("<div class='footer'>تم التطوير بواسطة: ®ridha_merzoug®</div>", unsafe_allow_html=True)
if st.sidebar.button("تسجيل الخروج"):
    st.session_state.auth = False
    st.rerun()
