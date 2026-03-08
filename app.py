import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta, datetime
import os

# 1. إعداد الصفحة والتنسيق الاحترافي
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { 
        background: linear-gradient(90deg, #1e3c72, #2a5298); 
        color: white; padding: 20px; border-radius: 15px; 
        text-align: center; margin-bottom: 25px; font-size: 1.6rem; font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .bed-box { 
        display: inline-block; width: 42px; height: 38px; margin: 4px; 
        border-radius: 6px; text-align: center; line-height: 38px; 
        color: white; font-size: 0.85rem; font-weight: bold; 
    }
    .free { background-color: #28a745; border-bottom: 3px solid #1e7e34; }
    .occupied { background-color: #dc3545; border-bottom: 3px solid #a71d2a; }
    .section-box { background: #f8f9fa; padding: 1.2rem; border-radius: 10px; margin-bottom: 1.2rem; border-right: 5px solid #1e3c72; }
    .minor-box { background: #fff3cd !important; border-right: 5px solid #ffc107 !important; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 10px; border-radius: 10px; text-align: center; margin-top: 50px; font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

# 2. قاعدة البيانات (SQLite)
DB_FILE = 'youth_hostel_v2.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # جدول النزلاء الحاليين (تم إزالة UNIQUE من id_card للسماح بالزيارات المتكررة)
    c.execute('''CREATE TABLE IF NOT EXISTS current_guests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, birth_date TEXT, birth_place TEXT, address TEXT,
        id_card TEXT, wing TEXT, room TEXT, bed TEXT,
        check_in TEXT, check_out TEXT, status TEXT DEFAULT 'مقيم',
        is_minor TEXT, guardian_name TEXT, guardian_permission TEXT, price INTEGER
    )''')
    # جدول الأرشيف
    c.execute('''CREATE TABLE IF NOT EXISTS archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, id_card TEXT, wing TEXT, room TEXT, bed TEXT,
        check_in TEXT, check_out TEXT, status TEXT DEFAULT 'غادر'
    )''')
    conn.commit()
    conn.close()

init_db()

# 3. الدوال المساعدة
def get_occupied_beds(wing, room):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT bed FROM current_guests WHERE wing=? AND room=?", conn, params=(wing, room))
    conn.close()
    return df['bed'].tolist()

def check_out_guest(guest_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # جلب بيانات النزيل قبل حذفه
    c.execute("SELECT name, id_card, wing, room, bed, check_in, check_out FROM current_guests WHERE id=?", (guest_id,))
    data = c.fetchone()
    if data:
        # إضافة للأرشيف
        c.execute("INSERT INTO archive (name, id_card, wing, room, bed, check_in, check_out) VALUES (?,?,?,?,?,?,?)", data)
        # حذف من الحاليين
        c.execute("DELETE FROM current_guests WHERE id=?", (guest_id,))
    conn.commit()
    conn.close()

# 4. الحالة والأجنحة
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'passwords' not in st.session_state: st.session_state.passwords = {"مدير": "1234", "عون استقبال": "5678"}

wings = {
    "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
    "جناح إناث": {"غرفة 06": 2, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد إناث 01": 3, "مرقد إناث 02": 4}
}

# 5. تسجيل الدخول
if not st.session_state.authenticated:
    st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
    role = st.selectbox("الصفة", ["مدير", "عون استقبال"])
    pwd = st.text_input("كلمة السر", type="password")
    if st.button("دخول للنظام", use_container_width=True):
        if pwd == st.session_state.passwords[role]:
            st.session_state.authenticated = True
            st.session_state.user_role = role
            st.rerun()
    st.stop()

# 6. الواجهة والتبويبات
st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)

if st.session_state.user_role == "مدير":
    tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجل والبحث", "📂 الأرشيف", "📈 إحصائيات", "⚙️ الإعدادات"])
else:
    tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجل والبحث"])

# --- تبويب الحجز الجديد ---
with tabs[0]:
    with st.form("main_form", clear_on_submit=True):
        st.markdown('<div class="section-box"><h4>👤 بيانات النزيل</h4></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم واللقب")
            b_date = st.date_input("تاريخ الازدياد", value=date(2000, 1, 1))
            b_place = st.text_input("مكان الازدياد")
        with c2:
            id_val = st.text_input("رقم بطاقة التعريف / جواز السفر")
            address = st.text_input("العنوان الكامل")
            phone = st.text_input("رقم الهاتف")

        st.markdown('<div class="section-box"><h4>🏨 تفاصيل الإقامة</h4></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            wing = st.selectbox("الجناح", list(wings.keys()))
        with col2:
            room = st.selectbox("الغرفة", list(wings[wing].keys()))
        with col3:
            # ميزة رضا الجديدة: عرض الأسرة المتاحة فقط
            occ_beds = get_occupied_beds(wing, room)
            available_beds = [f"سرير {i+1}" for i in range(wings[wing][room]) if f"سرير {i+1}" not in occ_beds]
            bed = st.selectbox("السرير المتاح", available_beds if available_beds else ["لا يوجد سرير شاغر"])

        nights = st.number_input("عدد الليالي", min_value=1, value=1)
        
        # منطق القاصرين (كما أبدعت فيه يا رضا)
        age = (date.today() - b_date).days // 365
        g_name = g_perm = ""
        is_minor = "لا"
        if age < 18:
            is_minor = "نعم"
            st.markdown(f'<div class="minor-box">⚠️ النزيل قاصر ({age} سنة). يرجى ملء بيانات الولي:</div>', unsafe_allow_html=True)
            gx1, gx2 = st.columns(2)
            g_name = gx1.text_input("اسم ولي الأمر")
            g_perm = gx2.selectbox("نوع التصريح", ["موافقة خطية", "حضور شخصي", "وصاية"])

        if st.form_submit_button("💾 حفظ وتسجيل الحجز", use_container_width=True):
            if not name or not id_val or bed == "لا يوجد سرير شاغر":
                st.error("يرجى التأكد من ملء البيانات واختيار سرير متاح.")
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("""INSERT INTO current_guests 
                    (name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, is_minor, guardian_name, guardian_permission, price)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (name, str(b_date), b_place, address, id_val, wing, room, bed, str(date.today()), str(date.today() + timedelta(days=nights)), is_minor, g_name, g_perm, nights*400))
                conn.commit()
                conn.close()
                st.success(f"تم تسجيل النزيل {name} في {bed}")
                st.rerun()

# --- تبويب حالة الغرف ---
with tabs[1]:
    st.subheader("📊 خريطة الأسرة الحالية")
    for w_name, rooms in wings.items():
        st.markdown(f"**{w_name}**")
        for r_name, b_count in rooms.items():
            cols = st.columns([1, 6])
            cols[0].write(f"_{r_name}_")
            occ = get_occupied_beds(w_name, r_name)
            html = ""
            for i in range(1, b_count + 1):
                status = "occupied" if f"سرير {i}" in occ else "free"
                html += f'<div class="bed-box {status}">{i}</div>'
            cols[1].markdown(html, unsafe_allow_html=True)

# --- تبويب السجل والبحث (مع ميزة الإخلاء) ---
with tabs[2]:
    st.subheader("🔍 البحث وإدارة المقيمين")
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, name, id_card, wing, room, bed, check_out FROM current_guests", conn)
    conn.close()
    
    search = st.text_input("ابحث بالاسم أو رقم البطاقة...")
    if search:
        df = df[df['name'].str.contains(search) | df['id_card'].str.contains(search)]
    
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    if not df.empty:
        col_sel, col_btn = st.columns([3, 1])
        to_out = col_sel.selectbox("اختر نزيل للمغادرة", df['name'].tolist())
        g_id = df[df['name'] == to_out]['id'].values[0]
        if col_btn.button("🔔 إنهاء الإقامة وإخلاء السرير", type="primary"):
            check_out_guest(g_id)
            st.success(f"تم إخلاء {to_out} ونقله للأرشيف.")
            st.rerun()

# --- تبويبات المدير (الأرشيف والإحصائيات) ---
if st.session_state.user_role == "مدير":
    with tabs[3]:
        st.subheader("📂 أرشيف النزلاء السابقين")
        conn = sqlite3.connect(DB_FILE)
        df_arc = pd.read_sql_query("SELECT * FROM archive ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df_arc, use_container_width=True)
    
    with tabs[4]:
        st.subheader("📈 إحصائيات المؤسسة")
        conn = sqlite3.connect(DB_FILE)
        total_now = pd.read_sql_query("SELECT COUNT(*) as count FROM current_guests", conn)['count'][0]
        total_arch = pd.read_sql_query("SELECT COUNT(*) as count FROM archive", conn)['count'][0]
        revenue = pd.read_sql_query("SELECT SUM(price) as total FROM current_guests", conn)['total'][0] or 0
        conn.close()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("النزلاء حالياً", total_now)
        c2.metric("إجمالي الأرشيف", total_arch)
        c3.metric("المداخيل المتوقعة", f"{revenue} دج")

# تذييل المطور
st.markdown(f'<div class="developer-footer">Developer <span style="color:#00d4ff;">®ridha_merzoug®</span> [رضا_مرزوق]</div>', unsafe_allow_html=True)
