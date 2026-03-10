import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import date, timedelta

# 1. إعداد الصفحة والـ CSS الإبداعي (الهوية البصرية لبيت الشباب)
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    
    .main-title { 
        background: linear-gradient(90deg, #0f2027, #203a43, #2c5364); 
        color: white; padding: 25px; border-radius: 20px; 
        text-align: center; margin-bottom: 30px; font-weight: bold;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }

    /* تصميم البطاقات الإحصائية المطور */
    .dashboard-container { display: flex; gap: 15px; margin-bottom: 30px; }
    
    .stat-card-creative {
        flex: 1; padding: 20px; border-radius: 15px; color: white;
        position: relative; overflow: hidden; transition: 0.4s;
        box-shadow: 0 6px 15px rgba(0,0,0,0.1);
    }
    .stat-card-creative:hover { transform: translateY(-8px); box-shadow: 0 12px 25px rgba(0,0,0,0.2); }
    
    .male-card { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); border-right: 8px solid #00d4ff; }
    .female-card { background: linear-gradient(135deg, #764ba2 0%, #667eea 100%); border-right: 8px solid #ff00cc; }
    .total-card { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); border-right: 8px solid #ffffff; }

    .stat-label-small { font-size: 0.9rem; opacity: 0.9; font-weight: 300; }
    .stat-value-big { font-size: 2.2rem; font-weight: bold; display: block; margin: 5px 0; }
    .progress-bg { background: rgba(255,255,255,0.2); height: 8px; border-radius: 10px; margin-top: 10px; }
    .progress-fill { background: white; height: 8px; border-radius: 10px; }
    
    .section-box { background: #ffffff; padding: 25px; border-radius: 15px; border-right: 6px solid #1e3c72; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .review-card { background: #f8faff; padding: 25px; border-radius: 15px; border: 2px dashed #1e3c72; line-height: 2; font-size: 1.1rem; color: #1e3c72; }
    .developer-footer { background: #1e3c72; color: white; padding: 10px; border-radius: 10px; text-align: center; margin-top: 50px; font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

# 2. إدارة قاعدة البيانات
DB_FILE = 'hostel_guelma_final_v1.db'
CAP_MALE = 60
CAP_FEMALE = 60

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, bday TEXT, bplace TEXT, id_num TEXT, id_type TEXT,
            nationality TEXT, visa_date TEXT, wing TEXT, room TEXT, 
            nights INTEGER, check_in TEXT, check_in_time TEXT, status TEXT DEFAULT 'مقيم'
        )''')

def get_stats():
    with sqlite3.connect(DB_FILE) as conn:
        m_occ = conn.execute("SELECT COUNT(*) FROM guests WHERE wing LIKE '%ذكور%' AND status='مقيم'").fetchone()[0]
        f_occ = conn.execute("SELECT COUNT(*) FROM guests WHERE wing LIKE '%إناث%' AND status='مقيم'").fetchone()[0]
    return m_occ, f_occ

init_db()

# 3. إدارة حالة البرنامج
if 'step' not in st.session_state: st.session_state.step = "input"
if 'temp_data' not in st.session_state: st.session_state.temp_data = {}

# 4. الواجهة والبيانات اللحظية
st.markdown('<div class="main-title">🏢 إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)

m_occ, f_occ = get_stats()
m_free = CAP_MALE - m_occ
f_free = CAP_FEMALE - f_occ
total_guests = m_occ + f_occ

# حساب النسب المئوية للتحميل
m_perc = (m_occ / CAP_MALE) * 100
f_perc = (f_occ / CAP_FEMALE) * 100

# --- لوحة التحكم الإبداعية ---
st.markdown(f"""
<div class="dashboard-container">
    <div class="stat-card-creative male-card">
        <span class="stat-label-small">👨 جناح الذكور (شاغر)</span>
        <span class="stat-value-big">{m_free}</span>
        <div class="stat-label-small">تم إشغال {m_occ} من أصل {CAP_MALE}</div>
        <div class="progress-bg"><div class="progress-fill" style="width: {m_perc}%"></div></div>
    </div>
    <div class="stat-card-creative total-card">
        <span class="stat-label-small">📋 إجمالي المقيمين حالياً</span>
        <span class="stat-value-big">{total_guests}</span>
        <div class="stat-label-small">نزيل مسجل حالياً في المؤسسة</div>
        <div style="font-size: 1.5rem; margin-top:5px;">🏨</div>
    </div>
    <div class="stat-card-creative female-card">
        <span class="stat-label-small">👩 جناح الإناث (شاغر)</span>
        <span class="stat-value-big">{f_free}</span>
        <div class="stat-label-small">تم إشغال {f_occ} من أصل {CAP_FEMALE}</div>
        <div class="progress-bg"><div class="progress-fill" style="width: {f_perc}%"></div></div>
    </div>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجلات"])

with tabs[0]:
    # المرحلة 1: إدخال البيانات
    if st.session_state.step == "input":
        st.markdown('<div class="section-box"><h4>✍️ تسجيل نزيل جديد</h4></div>', unsafe_allow_html=True)
        with st.form("booking_form"):
            name = st.text_input("👤 الاسم واللقب الكامل (إجباري) *")
            
            col1, col2 = st.columns(2)
            with col1:
                bday = st.date_input("📅 تاريخ الميلاد", date(2000, 1, 1))
                nat_options = ["جزائرية", "تونسية", "مغربية", "ليبية", "فرنسية", "أخرى"]
                nat_sel = st.selectbox("🌍 الجنسية", nat_options)
            with col2:
                bplace = st.text_input("📍 مكان الازدياد")
                id_type = st.selectbox("📄 نوع الوثيقة", ["بطاقة تعريف بيومترية", "جواز سفر", "رخصة سياقة"])

            id_num = st.text_input("🔢 رقم الوثيقة (إجباري) *")

            # منطق الجنسية والفيزا
            other_nat = ""
            visa_date = None
            if nat_sel == "أخرى":
                c_ot1, c_ot2 = st.columns(2)
                other_nat = c_ot1.text_input("📝 اكتب الجنسية:")
                visa_date = c_ot2.date_input("🛂 تاريخ دخول الجزائر (الفيزا)", date.today())
            elif nat_sel != "جزائرية":
                visa_date = st.date_input("🛂 تاريخ دخول الجزائر (الفيزا)", date.today())

            st.markdown("---")
            col3, col4, col5 = st.columns(3)
            wing = col3.selectbox("🏢 الجناح", ["جناح ذكور 👨", "جناح إناث 👩"])
            room = col4.selectbox("🚪 الغرفة", [f"غرفة {i:02d}" for i in range(1, 11)])
            nights = col5.number_input("🌙 عدد الليالي", min_value=1, value=1)

            if st.form_submit_button("📑 مراجعة البيانات قبل التأكيد", type="primary", use_container_width=True):
                if not name or not id_num or (nat_sel == "أخرى" and not other_nat):
                    st.error("⚠️ يرجى ملء الخانات الإجبارية.")
                else:
                    final_nat = other_nat if nat_sel == "أخرى" else nat_sel
                    st.session_state.temp_data = {
                        "name": name, "bday": str(bday), "bplace": bplace, "id_num": id_num,
                        "id_type": id_type, "nat": final_nat, "visa": str(visa_date) if visa_date else "غير مطلوب",
                        "wing": wing, "room": room, "nights": nights
                    }
                    st.session_state.step = "review"
                    st.rerun()

    # المرحلة 2: المراجعة والتأكيد
    elif st.session_state.step == "review":
        d = st.session_state.temp_data
        st.markdown('<div class="section-box"><h4>👁️ مراجعة نهائية قبل الحفظ</h4></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="review-card">
            <b>👤 النزيل:</b> {d['name']} <br>
            <b>🌍 الجنسية:</b> {d['nat']} | <b>🛂 تاريخ الفيزا:</b> {d['visa']} <br>
            <b>🔢 الوثيقة:</b> {d['id_num']} ({d['id_type']}) <br>
            <b>📅 الميلاد:</b> {d['bday']} في {d['bplace']} <br>
            <hr>
            <b>🏢 التسكين:</b> {d['wing']} - {d['room']} | <b>🌙 المدة:</b> {d['nights']} ليالي
        </div>
        """, unsafe_allow_html=True)
        
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("✅ تأكيد نهائي وحفظ", type="primary", use_container_width=True):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("""INSERT INTO guests 
                (name, bday, bplace, id_num, id_type, nationality, visa_date, wing, room, nights, check_in, check_in_time) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (d['name'], d['bday'], d['bplace'], d['id_num'], d['id_type'], d['nat'], d['visa'], d['wing'], d['room'], d['nights'], 
                 str(date.today()), datetime.datetime.now().strftime("%H:%M")))
            st.success("🎉 تم تسجيل الحجز بنجاح!")
            st.balloons()
            st.session_state.step = "input"
            st.rerun()
            
        if c_btn2.button("✏️ العودة للتعديل", use_container_width=True):
            st.session_state.step = "input"
            st.rerun()

st.markdown('<div class="developer-footer">Developer ®ridha_merzoug® [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
