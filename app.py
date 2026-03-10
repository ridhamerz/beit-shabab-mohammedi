import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import date

# 1. إعداد الصفحة والـ CSS الإبداعي
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { 
        background: linear-gradient(90deg, #0f2027, #2c5364); 
        color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px;
    }
    .stat-card-creative {
        flex: 1; padding: 20px; border-radius: 15px; color: white;
        box-shadow: 0 6px 15px rgba(0,0,0,0.1); margin: 5px;
    }
    .male-card { background: linear-gradient(135deg, #1e3c72, #2a5298); border-right: 8px solid #00d4ff; }
    .female-card { background: linear-gradient(135deg, #764ba2, #667eea); border-right: 8px solid #ff00cc; }
    .total-card { background: linear-gradient(135deg, #11998e, #38ef7d); border-right: 8px solid #ffffff; }
    .stat-value { font-size: 2rem; font-weight: bold; display: block; }
    .progress-bg { background: rgba(255,255,255,0.2); height: 8px; border-radius: 10px; margin-top: 10px; }
    .progress-fill { background: white; height: 8px; border-radius: 10px; }
    .section-box { background: #ffffff; padding: 20px; border-radius: 12px; border-right: 6px solid #1e3c72; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .review-card { background: #f8faff; padding: 20px; border-radius: 15px; border: 2px dashed #1e3c72; line-height: 2; }
    </style>
""", unsafe_allow_html=True)

# 2. إدارة قاعدة البيانات
DB_FILE = 'hostel_guelma_v10.db'
CAP_MALE, CAP_FEMALE = 60, 60

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, bday TEXT, bplace TEXT, 
            id_num TEXT, nationality TEXT, visa_date TEXT, wing TEXT, room TEXT, 
            nights INTEGER, check_in TEXT, status TEXT DEFAULT 'مقيم'
        )''')

def get_stats():
    with sqlite3.connect(DB_FILE) as conn:
        m_occ = conn.execute("SELECT COUNT(*) FROM guests WHERE wing LIKE '%ذكور%' AND status='مقيم'").fetchone()[0]
        f_occ = conn.execute("SELECT COUNT(*) FROM guests WHERE wing LIKE '%إناث%' AND status='مقيم'").fetchone()[0]
    return m_occ, f_occ

init_db()

# 3. إدارة الحالة (State)
if 'step' not in st.session_state: st.session_state.step = "input"
if 'found_data' not in st.session_state: st.session_state.found_data = None

# 4. واجهة البرنامج
st.markdown('<div class="main-title">🏢 نظام إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)

m_occ, f_occ = get_stats()
m_free, f_free = CAP_MALE - m_occ, CAP_FEMALE - f_occ

# عرض الإحصائيات الإبداعية
st.markdown(f"""
<div style="display: flex; flex-wrap: wrap; justify-content: space-around;">
    <div class="stat-card-creative male-card">
        <span style="font-size:0.9rem;">👨 شاغر (ذكور)</span>
        <span class="stat-value">{m_free}</span>
        <div class="progress-bg"><div class="progress-fill" style="width: {(m_occ/CAP_MALE)*100}%"></div></div>
    </div>
    <div class="stat-card-creative total-card">
        <span style="font-size:0.9rem;">🏨 إجمالي المقيمين</span>
        <span class="stat-value">{m_occ + f_occ}</span>
    </div>
    <div class="stat-card-creative female-card">
        <span style="font-size:0.9rem;">👩 شاغر (إناث)</span>
        <span class="stat-value">{f_free}</span>
        <div class="progress-bg"><div class="progress-fill" style="width: {(f_occ/CAP_FEMALE)*100}%"></div></div>
    </div>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجلات"])

with tabs[0]:
    if st.session_state.step == "input":
        # --- قسم البحث الذكي ---
        st.markdown('<div class="section-box"><h4>🔍 بحث سريع عن نزيل سابق</h4></div>', unsafe_allow_html=True)
        search_id = st.text_input("🪪 أدخل رقم الهوية للبحث الفوري:")
        
        if search_id:
            with sqlite3.connect(DB_FILE) as conn:
                res = conn.execute("SELECT name, bday, bplace, nationality FROM guests WHERE id_num=? ORDER BY id DESC LIMIT 1", (search_id,)).fetchone()
                if res:
                    st.session_state.found_data = res
                    st.success(f"✅ تم العثور على النزيل: {res[0]}")
                else:
                    st.session_state.found_data = None
                    st.info("ℹ️ نزيل جديد (لم يسجل من قبل)")

        # --- نموذج الحجز ---
        st.markdown('<div class="section-box"><h4>✍️ بيانات الحجز</h4></div>', unsafe_allow_html=True)
        fd = st.session_state.found_data
        with st.form("booking_form"):
            name = st.text_input("👤 الاسم واللقب الكامل *", value=fd[0] if fd else "")
            
            c1, c2 = st.columns(2)
            bday = c1.date_input("📅 تاريخ الميلاد", value=datetime.datetime.strptime(fd[1], '%Y-%m-%d').date() if fd else date(2000,1,1))
            bplace = c2.text_input("📍 مكان الازدياد", value=fd[2] if fd else "")

            c3, c4 = st.columns(2)
            nat_sel = c3.selectbox("🌍 الجنسية", ["جزائرية", "تونسية", "مغربية", "فرنسية", "أخرى"], index=(["جزائرية", "تونسية", "مغربية", "فرنسية", "أخرى"].index(fd[3]) if fd and fd[3] in ["جزائرية", "تونسية", "مغربية", "فرنسية", "أخرى"] else 0))
            id_num = c4.text_input("🔢 رقم الوثيقة *", value=search_id if search_id else "")

            # منطق الأجانب
            other_nat, visa_date = "", None
            if nat_sel == "أخرى":
                other_nat = st.text_input("📝 اكتب الجنسية الأخرى:")
                visa_date = st.date_input("🛂 تاريخ دخول الجزائر")
            elif nat_sel != "جزائرية":
                visa_date = st.date_input("🛂 تاريخ دخول الجزائر")

            st.markdown("---")
            c5, c6, c7 = st.columns(3)
            wing = c5.selectbox("🏢 الجناح", ["جناح ذكور 👨", "جناح إناث 👩"])
            room = c6.selectbox("🚪 الغرفة", [f"غرفة {i:02d}" for i in range(1, 11)])
            nights = c7.number_input("🌙 الليالي", min_value=1, value=1)

            if st.form_submit_button("📑 مراجعة البيانات", type="primary", use_container_width=True):
                if name and id_num:
                    final_nat = other_nat if nat_sel == "أخرى" else nat_sel
                    st.session_state.temp = {"name":name, "bday":str(bday), "bplace":bplace, "id":id_num, "nat":final_nat, "visa":str(visa_date) if visa_date else "غير مطلوب", "wing":wing, "room":room, "nights":nights}
                    st.session_state.step = "review"; st.rerun()
                else: st.error("⚠️ يرجى ملء الخانات الإجبارية")

    elif st.session_state.step == "review":
        d = st.session_state.temp
        st.markdown('<div class="section-box"><h4>👁️ مراجعة نهائية</h4></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="review-card"><b>النزيل:</b> {d["name"]}<br><b>الجنسية:</b> {d["nat"]} | <b>الفيزا:</b> {d["visa"]}<br><b>التسكين:</b> {d["wing"]} - {d["room"]}<br><b>المدة:</b> {d["nights"]} ليلة</div>', unsafe_allow_html=True)
        
        col_f1, col_f2 = st.columns(2)
        if col_f1.button("✅ تأكيد وحفظ", type="primary", use_container_width=True):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO guests (name, bday, bplace, id_num, nationality, visa_date, wing, room, nights, check_in) VALUES (?,?,?,?,?,?,?,?,?,?)", (d['name'], d['bday'], d['bplace'], d['id'], d['nat'], d['visa'], d['wing'], d['room'], d['nights'], str(date.today())))
            st.success("تم الحفظ!"); st.session_state.step = "input"; st.rerun()
        if col_f2.button("✏️ تعديل", use_container_width=True): st.session_state.step = "input"; st.rerun()

st.markdown('<div style="text-align:center; color:#666; margin-top:50px;">Developer ®ridha_merzoug® [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
