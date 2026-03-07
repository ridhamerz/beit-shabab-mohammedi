import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# 1. إعدادات الصفحة والتنسيق
st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; font-size: 1.3rem; font-weight: bold; }
    .bed-box { display: inline-block; width: 40px; height: 35px; margin: 3px; border-radius: 5px; text-align: center; line-height: 35px; color: white; font-size: 0.8rem; font-weight: bold; }
    .free { background-color: #28a745; }
    .occupied { background-color: #dc3545; }
    .stat-card { background: #f8f9fa; padding: 15px; border-radius: 10px; border-right: 5px solid #1e3c72; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 8px; border-radius: 10px; text-align: center; margin-top: 40px; font-size: 0.75rem; }
    </style>
    """, unsafe_allow_html=True)

# 2. إدارة البيانات (الحفظ الدائم في ملف CSV)
DB_FILE = 'hostel_data.csv'

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=['الاسم واللقب', 'تاريخ الازدياد', 'العنوان', 'رقم البطاقة', 'المهنة', 'الجناح', 'الغرفة', 'السرير', 'تاريخ الخروج', 'المبلغ'])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

if 'db' not in st.session_state:
    st.session_state.db = load_data()
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'passwords' not in st.session_state:
    st.session_state.passwords = {"مدير": "1234", "عون استقبال": "5678"}

wings = {
    "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
    "جناح إناث": {"غرفة 06": 2, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد إناث 01": 3, "مرقد إناث 02": 4}
}

# --- 3. بوابة الدخول ---
if not st.session_state.authenticated:
    st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
    role = st.selectbox("اختر الصفة", ["مدير", "عون استقبال"])
    pwd = st.text_input("كلمة السر", type="password")
    if st.button("دخول", use_container_width=True):
        if pwd == st.session_state.passwords[role]:
            st.session_state.authenticated = True
            st.session_state.user_role = role
            st.rerun()
    st.stop()

# --- 4. واجهة البرنامج ---
st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)

if st.session_state.user_role == "مدير":
    tabs = st.tabs(["➕ حجز جديد", "📊 عدد الغرف", "📋 السجل المالي", "📈 إحصائيات", "⚙️ الإعدادات"])
else:
    tabs = st.tabs(["➕ حجز جديد", "📊 عدد الغرف"])

# تبويب الحجز
with tabs[0]:
    st.subheader("📝 تسجيل نزيل جديد")
    with st.form("booking", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم واللقب")
            birth = st.text_input("تاريخ ومكان الازدياد")
            addr = st.text_input("العنوان")
        with c2:
            id_info = st.text_input("رقم البطاقة")
            w_c = st.selectbox("الجناح", list(wings.keys()))
            r_c = st.selectbox("الغرفة", list(wings[w_c].keys()))
            b_c = st.selectbox("السرير", [f"سرير {i+1}" for i in range(wings[w_c][r_c])])
        
        if st.form_submit_button("💾 حفظ الحجز"):
            new_row = {'الاسم واللقب': name, 'تاريخ الازدياد': birth, 'العنوان': addr, 'رقم البطاقة': id_info, 
                        'الجناح': w_c, 'الغرفة': r_c, 'السرير': b_c, 'تاريخ الخروج': datetime.now().date() + timedelta(days=1), 'المبلغ': 400}
            st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_row])], ignore_index=True)
            save_data(st.session_state.db)
            st.success("✅ تم الحفظ بنجاح في قاعدة البيانات")

# تبويب عدد الغرف
with tabs[1]:
    st.subheader("📊 خريطة الأسرة")
    for wing, rooms in wings.items():
        st.markdown(f'<div style="background:#eee; padding:5px; border-radius:5px; margin-top:10px;"><b>{wing}</b></div>', unsafe_allow_html=True)
        for room, count in rooms.items():
            cols = st.columns([1, 5])
            cols[0].write(f"{room}")
            html = ""
            for b in range(1, count + 1):
                is_occ = not st.session_state.db[(st.session_state.db['الجناح'] == wing) & (st.session_state.db['الغرفة'] == room) & (st.session_state.db['السرير'] == f"سرير {b}")].empty
                status = "occupied" if is_occ else "free"
                html += f'<div class="bed-box {status}">{b}</div>'
            cols[1].markdown(html, unsafe_allow_html=True)

# تبويبات المدير فقط
if st.session_state.user_role == "مدير":
    with tabs[2]:
        st.subheader("📋 السجل العام")
        st.dataframe(st.session_state.db, use_container_width=True)
        if st.button("🗑️ مسح السجل"):
            st.session_state.db = st.session_state.db.iloc[0:0]
            save_data(st.session_state.db)
            st.rerun()

    with tabs[3]:
        st.subheader("📈 نظرة عامة على العمل")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="stat-card"><h3>{len(st.session_state.db)}</h3><p>إجمالي النزلاء</p></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card"><h3>{st.session_state.db["المبلغ"].sum()} دج</h3><p>إجمالي المداخيل</p></div>', unsafe_allow_html=True)
        total_beds = sum(sum(r.values()) for r in wings.values())
        occ_perc = (len(st.session_state.db) / total_beds) * 100
        c3.markdown(f'<div class="stat-card"><h3>%{occ_perc:.1f}</h3><p>نسبة الإشغال</p></div>', unsafe_allow_html=True)

    with tabs[4]:
        st.subheader("⚙️ الإعدادات")
        new_p = st.text_input("تغيير كلمة سر المدير", type="password")
        if st.button("تحديث"):
            st.session_state.passwords["مدير"] = new_p
            st.success("تم التحديث")

# تذييل المطور
st.markdown(f'<div class="developer-footer">Developer <span style="color:#00d4ff;">®ridha_merzoug®</span> [رضا مرزوق]</div>', unsafe_allow_html=True)
