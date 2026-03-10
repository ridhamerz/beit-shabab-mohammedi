import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import date, timedelta

# 1. إعداد الصفحة والـ CSS الملكي
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; font-weight: bold; }
    .stat-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); text-align: center; border-bottom: 5px solid #28a745; }
    .section-box { background: #ffffff; padding: 25px; border-radius: 12px; border-right: 6px solid #1e3c72; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .review-card { background: #f1f4f9; padding: 25px; border-radius: 15px; border: 2px dashed #1e3c72; line-height: 1.8; }
    .developer-footer { background: #1e3c72; color: white; padding: 10px; border-radius: 10px; text-align: center; margin-top: 50px; font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

# 2. قاعدة البيانات والإحصائيات
DB_FILE = 'youth_hostel_pro_v8.db'
CAPACITY = 60

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS current_guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, bday TEXT, bplace TEXT, 
            id_num TEXT, nationality TEXT, visa_date TEXT, wing TEXT, room TEXT, 
            nights INTEGER, status TEXT DEFAULT 'مقيم'
        )''')

def get_stats():
    with sqlite3.connect(DB_FILE) as conn:
        m_occ = conn.execute("SELECT COUNT(*) FROM current_guests WHERE wing LIKE '%ذكور%' AND status='مقيم'").fetchone()[0]
        f_occ = conn.execute("SELECT COUNT(*) FROM current_guests WHERE wing LIKE '%إناث%' AND status='مقيم'").fetchone()[0]
    return (CAPACITY - m_occ), (CAPACITY - f_occ)

init_db()

# 3. إدارة الحالة
if 'step' not in st.session_state: st.session_state.step = "input"
if 'data' not in st.session_state: st.session_state.data = {}

# 4. الواجهة
st.markdown('<div class="main-title">🏢 إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)
tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجلات"])

with tabs[0]:
    m_free, f_free = get_stats()
    c_s1, c_s2 = st.columns(2)
    c_s1.markdown(f'<div class="stat-card">👨 شاغر (ذكور): {m_free}</div>', unsafe_allow_html=True)
    c_s2.markdown(f'<div class="stat-card" style="border-bottom-color:#e83e8c">👩 شاغر (إناث): {f_free}</div>', unsafe_allow_html=True)

    if st.session_state.step == "input":
        st.markdown('<div class="section-box"><h4>✍️ تسجيل بيانات النزيل</h4></div>', unsafe_allow_html=True)
        with st.form("entry_form"):
            name = st.text_input("👤 الاسم واللقب الكامل *")
            
            col1, col2 = st.columns(2)
            with col1:
                bday = st.date_input("📅 تاريخ الميلاد", date(2000, 1, 1))
                # قائمة الجنسيات
                nat_options = ["جزائرية", "تونسية", "مغربية", "ليبية", "صحراوية", "فرنسية", "أخرى"]
                nationality_sel = st.selectbox("🌍 الجنسية", nat_options)
            
            with col2:
                bplace = st.text_input("📍 مكان الازدياد")
                id_num = st.text_input("🔢 رقم الوثيقة *")

            # --- منطق الأجانب والجنسية "أخرى" ---
            other_nat = ""
            visa_date = None
            
            if nationality_sel == "أخرى":
                c_other1, c_other2 = st.columns(2)
                with c_other1:
                    other_nat = st.text_input("📝 اكتب الجنسية الأخرى:")
                with c_other2:
                    visa_date = st.date_input("🛂 تاريخ دخول الجزائر (الفيزا)", date.today())
            elif nationality_sel != "جزائرية":
                visa_date = st.date_input("🛂 تاريخ دخول الجزائر (الفيزا)", date.today())

            st.markdown("---")
            col3, col4, col5 = st.columns(3)
            wing = col3.selectbox("🏢 الجناح", ["جناح ذكور 👨", "جناح إناث 👩"])
            room = col4.selectbox("🚪 الغرفة", [f"غرفة {i:02d}" for i in range(1, 11)])
            nights = col5.number_input("🌙 عدد الليالي", min_value=1)

            if st.form_submit_button("📑 مراجعة البيانات", type="primary", use_container_width=True):
                if not name or not id_num or (nationality_sel == "أخرى" and not other_nat):
                    st.error("⚠️ يرجى ملء كافة الخانات الإجبارية.")
                else:
                    # تحديد الجنسية النهائية
                    final_nat = other_nat if nationality_sel == "أخرى" else nationality_sel
                    st.session_state.data = {
                        "name": name, "bday": str(bday), "bplace": bplace, "id": id_num, 
                        "nat": final_nat, "visa": str(visa_date) if visa_date else "غير مطلوب",
                        "wing": wing, "room": room, "nights": nights
                    }
                    st.session_state.step = "review"; st.rerun()

    elif st.session_state.step == "review":
        d = st.session_state.data
        st.markdown('<div class="section-box"><h4>👁️ مراجعة المعلومات قبل الحفظ</h4></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="review-card">
            <b>👤 النزيل:</b> {d['name']} <br>
            <b>🌍 الجنسية:</b> {d['nat']} | <b>🛂 الفيزا:</b> {d['visa']} <br>
            <b>🔢 الوثيقة:</b> {d['id']} <br>
            <b>📅 الميلاد:</b> {d['bday']} ({d['bplace']}) <br>
            <b>🏢 التسكين:</b> {d['wing']} - {d['room']} | <b>🌙 المدة:</b> {d['nights']} ليالي
        </div>
        """, unsafe_allow_html=True)
        
        c_f1, c_f2 = st.columns(2)
        if c_f1.button("✅ تأكيد نهائي", type="primary", use_container_width=True):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO current_guests (name, bday, bplace, id_num, nationality, visa_date, wing, room, nights) VALUES (?,?,?,?,?,?,?,?,?)",
                             (d['name'], d['bday'], d['bplace'], d['id'], d['nat'], d['visa'], d['wing'], d['room'], d['nights']))
            st.success("تم الحفظ بنجاح!"); st.session_state.step = "input"; st.rerun()
        if c_f2.button("✏️ تعديل", use_container_width=True):
            st.session_state.step = "input"; st.rerun()

st.markdown('<div class="developer-footer">Developer ®ridha_merzoug® [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
