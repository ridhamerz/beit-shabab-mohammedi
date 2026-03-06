import streamlit as st
import json
from datetime import datetime, date
import pandas as pd
import io
import hashlib
from math import ceil

# ====================== إعدادات الصفحة والتصميم الجذاب ======================
st.set_page_config(page_title="إدارة بيت الشباب محمدي يوسف", page_icon="🏢", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        direction: rtl;
        text-align: right;
        font-family: 'Cairo', sans-serif;
        background: linear-gradient(135deg, #f0f4ff 0%, #e0eaff 100%);
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .enhanced-header {
        background: linear-gradient(90deg, #1e40af, #3b82f6);
        color: white;
        padding: 2.5rem 1rem;
        border-radius: 16px;
        margin: 1.5rem 0 2rem;
        box-shadow: 0 6px 12px rgba(30,64,175,0.25);
        text-align: center;
    }
    .enhanced-header h1, .enhanced-header h2 { margin: 0; font-weight: 700; }

    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-left: 1px solid #e2e8f0;
        box-shadow: -3px 0 15px rgba(0,0,0,0.08);
    }

    .stButton>button {
        width: 100%;
        border-radius: 12px;
        font-weight: 600;
        padding: 0.8rem;
        transition: all 0.3s ease;
        border: none;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 15px rgba(0,0,0,0.15);
    }
    .stButton>button[kind="primary"] { background: #22c55e !important; color: white !important; }

    .room-card, .resident-card {
        background: white;
        border-radius: 14px;
        padding: 1.3rem;
        margin: 0.8rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    .room-card:hover, .resident-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }

    .stats-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 1.5rem 0;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }
    .stats-table th, .stats-table td {
        padding: 1rem;
        text-align: right;
        border-bottom: 1px solid #e2e8f0;
    }
    .stats-table th {
        background: #1e40af;
        color: white;
        font-weight: 700;
    }
    .stats-table tr:nth-child(even) { background: #f8fafc; }
    .stats-table tr:hover { background: #eff6ff; }

    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background: #1e293b;
        color: #cbd5e1;
        text-align: center;
        padding: 1rem;
        font-size: 0.95rem;
        border-top: 4px solid #3b82f6;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# ====================== الثوابت والدوال ======================
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

DEFAULT_BED_PRICE = 400

def load_data():
    try:
        with open("youth_hostel_final_db.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if "archive" not in data:
                data["archive"] = []
            return data
    except:
        return {room: {"residents": []} for room in ALL_ROOM_NAMES} | {"archive": []}

def save_data():
    with open("youth_hostel_final_db.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.db, f, ensure_ascii=False, indent=4)

# ====================== تهيئة session_state ======================
if "auth" not in st.session_state:
    st.session_state.auth = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = ""
if "bed_price" not in st.session_state:
    st.session_state.bed_price = DEFAULT_BED_PRICE
if "confirm_exit" not in st.session_state:
    st.session_state.confirm_exit = None
if "db" not in st.session_state:
    st.session_state.db = load_data()

# ====================== صفحة تسجيل الدخول ======================
if not st.session_state.auth:
    st.markdown("<div class='enhanced-header'><h1>🏢 إدارة بيت الشباب محمدي يوسف</h1></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        user = st.text_input("👤 اسم المستخدم", placeholder="admin أو reception")
        pw = st.text_input("🔑 كلمة السر", type="password")
        
        if st.button("تسجيل الدخول", type="primary"):
            if user in USERS and USERS[user]["password_hash"] == hash_password(pw):
                st.session_state.auth = True
                st.session_state.user_name = user
                st.session_state.user_role = USERS[user]["role"]
                st.rerun()
            else:
                st.error("❌ اسم المستخدم أو كلمة السر خاطئة")
    
    st.markdown("<div class='footer'>مطور من طرف ®ridha_merzoug® - 2026</div>", unsafe_allow_html=True)
    st.stop()   # ← هذا السطر مهم جداً لمنع تنفيذ باقي الكود

# ====================== الشريط الجانبي (بعد التأكد من تسجيل الدخول) ======================
st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
st.sidebar.markdown(f"**الصلاحية:** {'🛡️ مدير النظام' if st.session_state.user_role == 'admin' else '👋 استقبال'}")

if st.session_state.user_role == "admin":
    st.sidebar.markdown("### ⚙️ إعدادات الأدمن")
    st.session_state.bed_price = st.sidebar.number_input(
        "💰 سعر السرير اليومي (دج)", 
        value=st.session_state.bed_price, 
        min_value=100, 
        step=50
    )

menu = ["🏨 إدارة الغرف والحجز", "👥 قائمة النزلاء", "📊 الإحصائيات المالية", "📂 الأرشيف"]
choice = st.sidebar.radio("القائمة الرئيسية", menu, index=0)

if st.sidebar.button("🚪 تسجيل الخروج", type="primary"):
    st.session_state.auth = False
    st.rerun()

# ====================== الصفحات ======================

# 1. إدارة الغرف والحجز
if choice == "🏨 إدارة الغرف والحجز":
    st.markdown("<div class='enhanced-header'><h2>🏨 وضعية الغرف - بيت الشباب محمدي يوسف</h2></div>", unsafe_allow_html=True)
    
    for group, rooms in ROOMS_CONFIG.items():
        st.subheader(group)
        cols = st.columns(2)
        for i, (r, max_b) in enumerate(rooms.items()):
            with cols[i % 2]:
                occ = len(st.session_state.db[r]["residents"])
                status_color = "#ef4444" if occ >= max_b else "#22c55e"
                st.markdown(f"""
                <div class="room-card">
                    <h4 style="margin:0; color:{status_color};">{r}</h4>
                    <p style="margin:0.6rem 0; font-size:1.15rem; font-weight:600;">
                        <strong>{occ}</strong> / {max_b} <span style="color:#64748b;">مشغول</span>
                    </p>
                    <p style="color:#64748b; margin:0;">المتاح: {max_b - occ} سرير</p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("➕ تسجيل مقيم جديد")
    with st.form("add_form"):
        col1, col2 = st.columns(2)
        f_name = col1.text_input("اسم المقيم الكامل")
        f_room = col1.selectbox("اختر الغرفة", ALL_ROOM_NAMES)
        f_gender = col2.selectbox("الجنس", ["ذكر", "أنثى"])
        f_nation = col2.text_input("الجنسية", "جزائرية")
        f_kids = st.number_input("عدد الأطفال", 0, 10, 0)
        f_free = st.checkbox("إقامة مجانية")
        
        if st.form_submit_button("💾 حفظ البيانات"):
            max_b = next(v for g in ROOMS_CONFIG.values() for k,v in g.items() if k == f_room)
            if len(st.session_state.db[f_room]["residents"]) < max_b:
                st.session_state.db[f_room]["residents"].append({
                    "name": f_name.strip(), "gender": f_gender, "nation": f_nation.strip(),
                    "kids": f_kids, "is_free": f_free,
                    "entry": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                save_data()
                st.success("✅ تم تسجيل المقيم بنجاح")
                st.rerun()
            else:
                st.error("❌ الغرفة ممتلئة")

# 2. قائمة النزلاء
elif choice == "👥 قائمة النزلاء":
    st.markdown("<div class='enhanced-header'><h2>👥 قائمة النزلاء الحاليين</h2></div>", unsafe_allow_html=True)
    
    for r in ALL_ROOM_NAMES:
        res_list = st.session_state.db[r]["residents"]
        with st.expander(f"🏠 {r} ({len(res_list)} فرد)", expanded=False):
            if not res_list:
                st.info("الغرفة فارغة")
                continue
            for idx, p in enumerate(res_list):
                entry_dt = datetime.strptime(p["entry"], "%Y-%m-%d %H:%M")
                delta = datetime.now() - entry_dt
                nights = max(1, ceil(delta.total_seconds() / 86400))
                total = 0 if p["is_free"] else nights * st.session_state.bed_price
                
                st.markdown(f"""
                <div class="resident-card">
                    <strong>{p['name']}</strong> ({p['gender']}) - {p['nation']}<br>
                    دخول: {p['entry']}<br>
                    الليالي: {nights} | المبلغ: {total} دج
                </div>
                """, unsafe_allow_html=True)
                
                col_edit, col_exit = st.columns(2)
                if col_edit.button("✏️ تعديل", key=f"edit_{r}_{idx}"):
                    with st.form(f"edit_form_{r}_{idx}"):
                        edit_name = st.text_input("الاسم", p["name"])
                        edit_nation = st.text_input("الجنسية", p["nation"])
                        edit_kids = st.number_input("عدد الأطفال", value=p["kids"])
                        edit_free = st.checkbox("إقامة مجانية", p["is_free"])
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

    # نافذة التأكيد للخروج
    if st.session_state.confirm_exit:
        r, idx, total = st.session_state.confirm_exit
        name = st.session_state.db[r]["residents"][idx]["name"]
        st.warning(f"هل أنت متأكد من خروج **{name}**؟\nالمبلغ المستحق: **{total}** دج")
        col1, col2 = st.columns(2)
        if col1.button("✅ نعم، خروج نهائي"):
            p = st.session_state.db[r]["residents"].pop(idx)
            p.update({"exit": datetime.now().strftime("%Y-%m-%d %H:%M"), "paid_val": total, "room": r})
            st.session_state.db["archive"].append(p)
            save_data()
            st.session_state.confirm_exit = None
            st.success("تم تسجيل الخروج بنجاح")
            st.rerun()
        if col2.button("❌ إلغاء"):
            st.session_state.confirm_exit = None
            st.rerun()

# 3. الإحصائيات المالية (جدول + طباعة)
elif choice == "📊 الإحصائيات المالية":
    st.markdown("<div class='enhanced-header'><h2>📊 الملخص الإحصائي والمالي</h2></div>", unsafe_allow_html=True)
    
    current_res = []
    for r in ALL_ROOM_NAMES:
        current_res.extend(st.session_state.db[r]["residents"])
    
    males = len([p for p in current_res if p['gender'] == "ذكر"])
    females = len([p for p in current_res if p['gender'] == "أنثى"])
    foreigners = len([p for p in current_res if p['nation'].lower() not in ["جزائرية", "جزائري"]])
    
    today = date.today().strftime("%Y-%m-%d")
    month = date.today().strftime("%Y-%m")
    daily_rev = sum(e.get("paid_val", 0) for e in st.session_state.db["archive"] if e.get("exit", "").startswith(today))
    monthly_rev = sum(e.get("paid_val", 0) for e in st.session_state.db["archive"] if e.get("exit", "").startswith(month))
    
    monthly_arch = [e for e in st.session_state.db["archive"] if e.get("exit", "").startswith(month)]
    monthly_total = len(monthly_arch)
    monthly_males = len([p for p in monthly_arch if p.get('gender') == "ذكر"])
    monthly_females = len([p for p in monthly_arch if p.get('gender') == "أنثى"])
    monthly_foreigners = len([p for p in monthly_arch if p.get('nation','').lower() not in ["جزائرية", "جزائري"]])
    monthly_free = len([p for p in monthly_arch if p.get('is_free', False)])
    
    stats_data = {
        "البيان": [
            "المقيمين حالياً", "الذكور حالياً", "الإناث حالياً", "الأجانب حالياً",
            "إجمالي المقيمين بالشهر", "الذكور بالشهر", "الإناث بالشهر", 
            "الأجانب بالشهر", "المقيمين مجاناً بالشهر",
            "دخل اليوم", "دخل الشهر"
        ],
        "القيمة": [
            len(current_res), males, females, foreigners,
            monthly_total, monthly_males, monthly_females, 
            monthly_foreigners, monthly_free,
            f"{daily_rev:,} دج", f"{monthly_rev:,} دج"
        ]
    }
    
    df_stats = pd.DataFrame(stats_data)
    st.markdown(df_stats.to_html(classes="stats-table", index=False, escape=False), unsafe_allow_html=True)
    
    # زر الطباعة
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_stats.to_excel(writer, index=False, sheet_name='إحصائيات')
    st.download_button(
        "🖨️ طباعة الإحصائيات (Excel)",
        output.getvalue(),
        f"إحصائيات_{month}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# 4. الأرشيف
elif choice == "📂 الأرشيف":
    st.markdown("<div class='enhanced-header'><h2>📂 الأرشيف التاريخي</h2></div>", unsafe_allow_html=True)
    
    search_name = st.text_input("🔍 ابحث بالاسم")
    search_room = st.selectbox("ابحث بالغرفة", ["الكل"] + ALL_ROOM_NAMES)
    
    filtered = st.session_state.db["archive"]
    if search_name:
        filtered = [e for e in filtered if search_name.lower() in e.get("name", "").lower()]
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
        st.info("لا توجد سجلات مطابقة")

# ====================== التوقيع ======================
st.markdown("<div class='footer'>© 2026 إدارة بيت الشباب محمدي يوسف • مطور من طرف ®ridha_merzoug® • </div>", unsafe_allow_html=True)
