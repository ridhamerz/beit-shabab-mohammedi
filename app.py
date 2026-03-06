import streamlit as st
import json
from datetime import datetime
import pandas as pd
import hashlib

# ====================== 1. الإعدادات البصرية وتنسيق CSS ======================
st.set_page_config(page_title="نظام إدارة بيت الشباب محمدي يوسف", page_icon="🏢", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&family=Orbitron:wght@700&display=swap');

    html, body, [class*="css"] { 
        direction: RTL; text-align: right; font-family: 'Cairo', sans-serif; 
    }
    
    .main-header { 
        background: linear-gradient(135deg, #1e3a8a, #2563eb); 
        color: white; padding: 25px; border-radius: 15px; 
        text-align: center; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    .revenue-card {
        background: #ffffff; border: 1px solid #e2e8f0; padding: 20px;
        border-radius: 12px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .warning-stay {
        background-color: #fff1f2; border-right: 6px solid #e11d48;
        padding: 15px; border-radius: 8px; margin: 10px 0; color: #9f1239;
    }

    /* تصميم توقيع المطور المميز */
    .developer-footer {
        background: #0f172a; color: #f8fafc; padding: 30px;
        border-radius: 30px 30px 0 0; text-align: center;
        margin-top: 60px; border-top: 5px solid #3b82f6;
    }

    .developer-name {
        font-family: 'Orbitron', sans-serif; font-size: 26px;
        color: #60a5fa; text-shadow: 0 0 12px #3b82f6;
        letter-spacing: 3px; font-weight: bold; margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ====================== 2. النظام الخلفي وقاعدة البيانات ======================
def hash_password(pw):
    return hashlib.sha256((pw + "guelma_youth_2026").encode()).hexdigest()

ROOMS_CONFIG = {
    "جناح ذكور 👨": ["غرفة 01", "غرفة 02", "غرفة 03", "غرفة 04", "غرفة 05", "مرقد ذكور", "مرقد ذكور 02"],
    "جناح إناث 👩": ["غرفة 06", "غرفة 07", "غرفة 08", "غرفة 09", "مرقد أناث", "مرقد إناث 02"]
}
ALL_ROOMS = [r for g in ROOMS_CONFIG.values() for r in g]

def load_db():
    try:
        with open("hostel_master_db.json", "r", encoding="utf-8") as f: return json.load(f)
    except:
        return {
            "rooms": {r: {"residents": []} for r in ALL_ROOMS},
            "archive": [],
            "users": {"admin": {"hash": hash_password("admin2026")}}
        }

def save_db():
    with open("hostel_master_db.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.db, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state: st.session_state.db = load_db()
if "auth" not in st.session_state: st.session_state.auth = False

# ====================== 3. شاشة حماية النظام ======================
if not st.session_state.auth:
    st.markdown("<div class='main-header'><h1>🏢 نظام إدارة بيت الشباب محمدي يوسف</h1><h3>تسجيل الدخول</h3></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pwd = st.text_input("أدخل كلمة مرور الإدارة", type="password")
        if st.button("دخول النظام", use_container_width=True):
            if st.session_state.db["users"]["admin"]["hash"] == hash_password(pwd):
                st.session_state.auth = True; st.rerun()
            else: st.error("❌ كلمة المرور غير صحيحة")
    st.stop()

# ====================== 4. لوحة الإحصائيات والإيرادات ======================
st.markdown("<div class='main-header'><h1>🏨 لوحة تحكم المؤسسة</h1></div>", unsafe_allow_html=True)

today = datetime.now().strftime("%Y-%m-%d")
this_month = datetime.now().strftime("%Y-%m")

rev_today = 0
rev_month = 0
total_active = sum(len(st.session_state.db["rooms"][r]["residents"]) for r in ALL_ROOMS)

# حساب الإيرادات من النزلاء الحاليين والأرشيف
combined_data = st.session_state.db["archive"] + [res for rm in ALL_ROOMS for res in st.session_state.db["rooms"][rm]["residents"]]
for entry in combined_data:
    amt = entry.get('price', 0)
    d_in = entry['date_in'][:10]
    m_in = entry['date_in'][:7]
    if d_in == today: rev_today += amt
    if m_in == this_month: rev_month += amt

c1, c2, c3 = st.columns(3)
c1.markdown(f"<div class='revenue-card'><h3>💰 إيراد اليوم</h3><h2 style='color:#16a34a'>{rev_today} د.ج</h2></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='revenue-card'><h3>📅 إيراد الشهر</h3><h2 style='color:#2563eb'>{rev_month} د.ج</h2></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='revenue-card'><h3>👥 النزلاء حالياً</h3><h2 style='color:#1e293b'>{total_active}</h2></div>", unsafe_allow_html=True)

# ====================== 5. نموذج تسجيل الحجز (أولاً) ======================
st.write("---")
with st.expander("➕ تسجيل نزيل جديد (حجز جديد)", expanded=True):
    with st.form("main_reg"):
        f1, f2, f3 = st.columns(3)
        with f1:
            name = st.text_input("الاسم واللقب الكامل")
            gender = st.selectbox("الجنس", ["ذكر", "أنثى"])
        with f2:
            nation = st.text_input("الجنسية", "جزائرية")
            room_choice = st.selectbox("تخصيص الغرفة", ALL_ROOMS)
        with f3:
            pay_type = st.selectbox("نوع الحجز", ["بمقابل مادي", "مجاني / إعفاء"])
            price_val = st.number_input("المبلغ (د.ج)", min_value=0, value=500 if pay_type == "بمقابل مادي" else 0)
        
        if st.form_submit_button("إتمام عملية الحجز والحفظ", use_container_width=True):
            if name:
                new_guest = {
                    "name": name, "gender": gender, "nationality": nation,
                    "type": pay_type, "price": price_val,
                    "date_in": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.session_state.db["rooms"][room_choice]["residents"].append(new_guest)
                save_db(); st.success(f"✅ تم تسجيل {name} بنجاح"); st.rerun()

# ====================== 6. محرك البحث وحالة الغرف ======================
st.write("---")
st.subheader("🔍 البحث السريع وإدارة الغرف")
query = st.text_input("ابحث عن نزيل، جنسية، أو رقم غرفة...").lower()

for wing, rooms in ROOMS_CONFIG.items():
    st.markdown(f"### {wing}")
    cols = st.columns(2)
    for idx, r_name in enumerate(rooms):
        residents = st.session_state.db["rooms"][r_name]["residents"]
        # فلترة البحث
        match = [p for p in residents if query in p['name'].lower() or query in r_name.lower() or query in p['nationality'].lower()]
        
        if (query and match) or (not query):
            with cols[idx % 2].expander(f"🏠 {r_name} ({len(residents)}/6)"):
                if not residents: st.info("الغرفة فارغة")
                for i, p in enumerate(residents):
                    # حساب مدة الإقامة للتنبيه
                    d_in = datetime.strptime(p['date_in'], "%Y-%m-%d %H:%M")
                    days = (datetime.now() - d_in).days
                    
                    is_late = days >= 3
                    div_style = "class='warning-stay'" if is_late else "style='padding:10px; border-bottom:1px solid #eee'"
                    
                    st.markdown(f"""
                    <div {div_style}>
                        <b>👤 {p['name']}</b> ({p['nationality']})<br>
                        <small>📅 دخول: {p['date_in']} | 💰 {p['price']} د.ج</small>
                        {"<br><b>⚠️ تنبيه: إقامة مطولة ({} أيام)</b>".format(days) if is_late else ""}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"تسجيل خروج: {p['name']}", key=f"ex_{r_name}_{i}"):
                        p['date_out'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        st.session_state.db["archive"].append(p)
                        st.session_state.db["rooms"][r_name]["residents"].pop(i)
                        save_db(); st.rerun()

# ====================== 7. تصدير البيانات والتقارير ======================
st.write("---")
st.subheader("📂 استخراج التقارير (Excel)")
c_exp1, c_exp2 = st.columns(2)
with c_exp1:
    if st.button("📊 تصدير قائمة النزلاء الحالية"):
        all_now = []
        for rm_n, rm_i in st.session_state.db["rooms"].items():
            for p in rm_i["residents"]: all_now.append({"الغرفة": rm_n, **p})
        if all_now:
            st.download_button("⬇️ تحميل الملف", pd.DataFrame(all_now).to_csv(index=False).encode('utf-8-sig'), "current_guests.csv", "text/csv")
with c_exp2:
    if st.button("📂 تصدير سجل الأرشيف التاريخي"):
        if st.session_state.db["archive"]:
            st.download_button("⬇️ تحميل الأرشيف", pd.DataFrame(st.session_state.db["archive"]).to_csv(index=False).encode('utf-8-sig'), "hostel_archive.csv", "text/csv")

# ====================== 8. تذييل المطور (اسم بارز ومميز) ======================
st.markdown("""
    <div class="developer-footer">
        <p style="margin-bottom: 10px; font-weight: bold; color: #94a3b8; font-size: 16px;">بيت الشباب محمدي يوسف - ولاية قالمة</p>
        <div style="background: rgba(255,255,255,0.05); display: inline-block; padding: 10px 30px; border-radius: 15px;">
            <span style="color: #cbd5e1; font-size: 14px;">DEVELOPED BY</span><br>
            <div class="developer-name">🚀 RIDHA_MERZOUG 🚀</div>
        </div>
        <p style="font-size: 12px; color: #475569; margin-top: 15px; letter-spacing: 1px;">PREMIUM MANAGEMENT SYSTEM © 2026</p>
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 تسجيل الخروج من النظام"):
    st.session_state.auth = False; st.rerun()
