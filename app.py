import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# 1. إعدادات الواجهة الفاخرة (CSS)
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    
    .main-title { 
        background: linear-gradient(90deg, #1e3c72, #2a5298); 
        color: white; padding: 20px; border-radius: 15px; 
        text-align: center; margin-bottom: 25px; 
        font-size: 1.5rem; font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    .bed-box { 
        display: inline-block; width: 42px; height: 38px; margin: 4px; 
        border-radius: 6px; text-align: center; line-height: 38px; 
        color: white; font-size: 0.85rem; font-weight: bold; 
    }
    .free { background-color: #28a745; border-bottom: 3px solid #1e7e34; }
    .occupied { background-color: #dc3545; border-bottom: 3px solid #a71d2a; }
    
    .stat-card { 
        background: white; padding: 20px; border-radius: 12px; 
        border-right: 6px solid #1e3c72; text-align: center; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); 
    }
    
    .developer-footer { 
        background: #1e3c72; color: #ffffff; padding: 8px; 
        border-radius: 10px; text-align: center; margin-top: 50px; 
        font-size: 0.75rem; border: 1px solid #00d4ff;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. إدارة قواعد البيانات (Excel/CSV)
def load_db(file):
    if os.path.exists(file): return pd.read_csv(file)
    cols = ['الاسم واللقب', 'تاريخ الازدياد', 'العنوان', 'رقم البطاقة', 'الجناح', 'الغرفة', 'السرير', 'تاريخ الدخول', 'تاريخ الخروج', 'الحالة']
    return pd.DataFrame(columns=cols)

# تحميل البيانات عند بدء التشغيل
if 'db' not in st.session_state: st.session_state.db = load_db('current_guests.csv')
if 'archive' not in st.session_state: st.session_state.archive = load_db('archive.csv')
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'passwords' not in st.session_state: st.session_state.passwords = {"مدير": "1234", "عون استقبال": "5678"}

# هيكلة الأجنحة كما طلبت
wings = {
    "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
    "جناح إناث": {"غرفة 06": 2, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد إناث 01": 3, "مرقد إناث 02": 4}
}

# --- 3. نظام تسجيل الدخول ---
if not st.session_state.authenticated:
    st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
    st.subheader("🔐 الدخول للنظام")
    role = st.selectbox("الصفة", ["مدير", "عون استقبال"])
    pwd = st.text_input("كلمة السر", type="password")
    if st.button("دخول آمن", use_container_width=True):
        if pwd == st.session_state.passwords[role]:
            st.session_state.authenticated = True
            st.session_state.user_role = role
            st.rerun()
        else: st.error("كلمة السر خاطئة!")
    st.stop()

# --- 4. الواجهة الرئيسية بعد الدخول ---
st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
st.sidebar.write(f"👤 المستخدم: **{st.session_state.user_role}**")
if st.sidebar.button("تسجيل الخروج"):
    st.session_state.authenticated = False
    st.rerun()

# تخصيص التبويبات حسب الصلاحية
if st.session_state.user_role == "مدير":
    tabs = st.tabs(["➕ حجز جديد", "📊 عدد الغرف", "📋 السجل والبحث", "📂 الأرشيف", "📈 الإحصائيات", "⚙️ الإعدادات"])
else:
    tabs = st.tabs(["➕ حجز جديد", "📊 عدد الغرف", "📋 السجل والبحث"])

# --- تبويب الحجز الجديد ---
with tabs[0]:
    st.subheader("📝 تسجيل نزيل جديد")
    with st.form("booking_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم واللقب")
            birth = st.text_input("تاريخ ومكان الازدياد")
            addr = st.text_input("العنوان الكامل")
        with c2:
            id_val = st.text_input("رقم بطاقة التعريف")
            w_choice = st.selectbox("الجناح", list(wings.keys()))
            r_choice = st.selectbox("الغرفة", list(wings[w_choice].keys()))
            b_choice = st.selectbox("رقم السرير", [f"سرير {i+1}" for i in range(wings[w_choice][r_choice])])
        
        if st.form_submit_button("✅ تأكيد وحفظ"):
            if name and id_val:
                new_guest = {
                    'الاسم واللقب': name, 'تاريخ الازدياد': birth, 'العنوان': addr, 'رقم البطاقة': id_val,
                    'الجناح': w_choice, 'الغرفة': r_choice, 'السرير': b_choice, 
                    'تاريخ الدخول': datetime.now().date(), 'تاريخ الخروج': datetime.now().date() + timedelta(days=1), 'الحالة': 'مقيم'
                }
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_guest])], ignore_index=True)
                st.session_state.db.to_csv('current_guests.csv', index=False)
                st.success("تم تسجيل النزيل وحفظ السرير.")
            else: st.error("يرجى ملء البيانات.")

# --- تبويب خريطة الغرف والأسرة ---
with tabs[1]:
    st.subheader("📊 حالة الأجنحة والأسرة")
    for wing, rooms in wings.items():
        st.markdown(f'<div style="background:#f8f9fa; padding:10px; border-radius:10px; border-right:5px solid #1e3c72; margin-top:15px;"><b>{wing}</b></div>', unsafe_allow_html=True)
        for room, count in rooms.items():
            cols = st.columns([1, 6])
            cols[0].write(f"**{room}**")
            html = ""
            for b in range(1, count + 1):
                b_name = f"سرير {b}"
                is_occ = not st.session_state.db[(st.session_state.db['الجناح'] == wing) & (st.session_state.db['الغرفة'] == room) & (st.session_state.db['السرير'] == b_name)].empty
                status = "occupied" if is_occ else "free"
                html += f'<div class="bed-box {status}">{b}</div>'
            cols[1].markdown(html, unsafe_allow_html=True)

# --- تبويب السجل والبحث (مع ميزة الإخلاء) ---
with tabs[2]:
    st.subheader("🔍 سجل المقيمين الحاليين")
    search = st.text_input("ابحث بالاسم أو رقم البطاقة...")
    df_display = st.session_state.db
    if search:
        df_display = df_display[df_display['الاسم واللقب'].str.contains(search) | df_display['رقم البطاقة'].str.contains(search)]
    st.dataframe(df_display, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🚪 إنهاء إقامة نزيل")
    if not st.session_state.db.empty:
        out_name = st.selectbox("اختر النزيل المغادر", st.session_state.db['الاسم واللقب'].tolist())
        if st.button("إخلاء السرير ونقل للأرشيف"):
            row = st.session_state.db[st.session_state.db['الاسم واللقب'] == out_name].copy()
            row['الحالة'] = 'غادر'
            st.session_state.archive = pd.concat([st.session_state.archive, row], ignore_index=True)
            st.session_state.db = st.session_state.db[st.session_state.db['الاسم واللقب'] != out_name]
            st.session_state.db.to_csv('current_guests.csv', index=False)
            st.session_state.archive.to_csv('archive.csv', index=False)
            st.success(f"تم إخلاء سبيل {out_name} وتحديث الأرشيف.")
            st.rerun()

# --- تبويبات المدير فقط ---
if st.session_state.user_role == "مدير":
    with tabs[3]:
        st.subheader("📂 الأرشيف التاريخي للنزلاء")
        st.dataframe(st.session_state.archive, use_container_width=True)

    with tabs[4]:
        st.subheader("📈 تقارير الإحصائيات")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="stat-card"><h3>{len(st.session_state.db)}</h3><p>نزلاء مقيمين</p></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card"><h3>{len(st.session_state.archive)}</h3><p>إجمالي الأرشيف</p></div>', unsafe_allow_html=True)
        total_b = sum(sum(r.values()) for r in wings.values())
        c3.markdown(f'<div class="stat-card"><h3>%{ (len(st.session_state.db)/total_b)*100:.1f}</h3><p>نسبة الإشغال</p></div>', unsafe_allow_html=True)

    with tabs[5]:
        st.subheader("⚙️ إعدادات النظام")
        target_u = st.selectbox("تغيير كلمة سر", ["مدير", "عون استقبال"])
        new_p = st.text_input("كلمة السر الجديدة", type="password")
        if st.button("حفظ"):
            st.session_state.passwords[target_u] = new_p
            st.success("تم تحديث كلمة السر بنجاح.")

# 5. تذييل المطور (باسمك وبحجم صغير)
st.markdown(f"""
    <div class="developer-footer">
        Developer <span style="color:#00d4ff; font-weight:bold;">®ridha_merzoug®</span> [رضا مرزوق] - 2026
    </div>
    """, unsafe_allow_html=True)
