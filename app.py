import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import date, timedelta
from io import BytesIO

# 1. إعداد الصفحة والـ CSS
st.set_page_config(page_title="Hostel Management Pro - قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&family=Orbitron:wght@500&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(135deg, #000428, #004e92); color: white; padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 30px; border-bottom: 5px solid #00d4ff; }
    .stat-card-creative { flex: 1; padding: 20px; border-radius: 15px; color: white; box-shadow: 0 6px 15px rgba(0,0,0,0.1); margin: 5px; min-width: 250px; }
    .male-card { background: linear-gradient(135deg, #1e3c72, #2a5298); border-right: 8px solid #00d4ff; }
    .female-card { background: linear-gradient(135deg, #764ba2, #667eea); border-right: 8px solid #ff00cc; }
    .total-card { background: linear-gradient(135deg, #11998e, #38ef7d); border-right: 8px solid #ffffff; }
    .stat-value { font-size: 2.2rem; font-weight: bold; display: block; }
    .section-box { background: white; padding: 20px; border-radius: 12px; border-right: 6px solid #1e3c72; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .alert-card { background: #fff5f5; border: 1px solid #feb2b2; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .dev-signature { text-align: center; margin-top: 50px; padding: 20px; background: #f1f1f1; border-radius: 50px 50px 0 0; }
    .dev-text { font-family: 'Orbitron', sans-serif; letter-spacing: 2px; color: #1e3c72; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. إدارة قاعدة البيانات
DB_FILE = 'hostel_guelma_v14.db'
CAP_MALE, CAP_FEMALE = 60, 60

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, bday TEXT, bplace TEXT, 
            id_type TEXT, id_num TEXT, nationality TEXT, visa_date TEXT, job TEXT, phone TEXT,
            guardian TEXT, companions TEXT, wing TEXT, room TEXT, nights INTEGER, check_in TEXT, status TEXT DEFAULT 'مقيم'
        )''')

def get_db_connection():
    return sqlite3.connect(DB_FILE)

init_db()

# 3. الدوال البرمجية (Logic)
def get_occupied_rooms():
    with get_db_connection() as conn:
        res = conn.execute("SELECT wing, room FROM guests WHERE status='مقيم'").fetchall()
        return [f"{r[0]}-{r[1]}" for r in res]

def get_checkout_today():
    today = date.today()
    checkout_list = []
    with get_db_connection() as conn:
        data = conn.execute("SELECT name, wing, room, check_in, nights FROM guests WHERE status='مقيم'").fetchall()
        for row in data:
            check_in_date = datetime.datetime.strptime(row[3], '%Y-%m-%d').date()
            if check_in_date + timedelta(days=row[4]) <= today:
                checkout_list.append(row)
    return checkout_list

# 4. واجهة المستخدم
st.markdown('<div class="main-title">🏢 HOSTEL MANAGEMENT PRO | محمدي يوسف - قالمة</div>', unsafe_allow_html=True)

# التنبيه بموعد المغادرة (Checkout Alerts)
checkouts = get_checkout_today()
if checkouts:
    with st.expander(f"⏰ تنبيه: يوجد {len(checkouts)} نزلاء انتهت مدة إقامتهم اليوم!", expanded=True):
        for c in checkouts:
            st.markdown(f'<div class="alert-card">⚠️ النزيل: <b>{c[0]}</b> | {c[1]} - {c[2]} (تاريخ الدخول: {c[3]})</div>', unsafe_allow_html=True)

m_occ = 0; f_occ = 0
with get_db_connection() as conn:
    m_occ = conn.execute("SELECT COUNT(*) FROM guests WHERE wing LIKE '%ذكور%' AND status='مقيم'").fetchone()[0]
    f_occ = conn.execute("SELECT COUNT(*) FROM guests WHERE wing LIKE '%إناث%' AND status='مقيم'").fetchone()[0]

st.markdown(f"""<div style="display: flex; flex-wrap: wrap; justify-content: space-around;">
    <div class="stat-card-creative male-card"><span>👨 شاغر (ذكور)</span><span class="stat-value">{CAP_MALE - m_occ}</span></div>
    <div class="stat-card-creative total-card"><span>🏨 إجمالي المقيمين</span><span class="stat-value">{m_occ + f_occ}</span></div>
    <div class="stat-card-creative female-card"><span>👩 شاغر (إناث)</span><span class="stat-value">{CAP_FEMALE - f_occ}</span></div>
</div>""", unsafe_allow_html=True)

tabs = st.tabs(["➕ حجز جديد", "📋 السجلات والإحصائيات", "👮‍♂️ تصدير أمني"])

with tabs[0]:
    if 'step' not in st.session_state: st.session_state.step = "input"
    
    if st.session_state.step == "input":
        st.markdown('<div class="section-box"><h4>🔍 بحث ذكي عن نزيل</h4></div>', unsafe_allow_html=True)
        search_id = st.text_input("أدخل رقم الهوية:")
        found_data = None
        if search_id:
            with get_db_connection() as conn:
                found_data = conn.execute("SELECT name, bday, bplace, id_type, nationality, job, phone, guardian, companions FROM guests WHERE id_num=? ORDER BY id DESC LIMIT 1", (search_id,)).fetchone()
        
        with st.form("booking_form"):
            st.markdown("---")
            name = st.text_input("👤 الاسم واللقب الكامل *", value=found_data[0] if found_data else "")
            c1, c2 = st.columns(2)
            bday = c1.date_input("📅 تاريخ الميلاد", value=datetime.datetime.strptime(found_data[1], '%Y-%m-%d').date() if found_data else date(2000,1,1))
            bplace = c2.text_input("📍 مكان الازدياد", value=found_data[2] if found_data else "")
            
            # منع الحجز المزدوج (فحص الغرف)
            occupied = get_occupied_rooms()
            
            c3, c4 = st.columns(2)
            wing = c3.selectbox("🏢 الجناح", ["جناح ذكور 👨", "جناح إناث 👩"])
            room = c4.selectbox("🚪 الغرفة", [f"غرفة {i:02d}" for i in range(1, 11)])
            
            nights = st.number_input("🌙 عدد الليالي", min_value=1, value=1)
            
            # بيانات إضافية
            with st.expander("🛠️ بيانات إضافية (الجنسية، الهاتف، المرافقين)"):
                id_num = st.text_input("🔢 رقم الوثيقة *", value=search_id if search_id else "")
                phone = st.text_input("📞 الهاتف", value=found_data[6] if found_data else "")
                job = st.text_input("💼 المهنة", value=found_data[5] if found_data else "")
                comps = st.text_area("👨‍👩‍👧‍👦 المرافقون", value=found_data[8] if found_data else "")

            if st.form_submit_button("📑 مراجعة الحجز", type="primary", use_container_width=True):
                current_selection = f"{wing}-{room}"
                if current_selection in occupied:
                    st.error(f"⚠️ الغرفة {room} في {wing} مشغولة حالياً! يرجى اختيار غرفة أخرى.")
                elif name and id_num:
                    st.session_state.temp = {"name":name, "bday":str(bday), "wing":wing, "room":room, "nights":nights, "id":id_num, "phone":phone, "job":job, "comps":comps}
                    st.session_state.step = "review"; st.rerun()
                else: st.error("الاسم ورقم الوثيقة مطلوبان!")

    elif st.session_state.step == "review":
        d = st.session_state.temp
        st.markdown('<div class="section-box"><h4>👁️ تأكيد الحجز</h4></div>', unsafe_allow_html=True)
        st.info(f"النزيل: {d['name']} | التسكين: {d['wing']} {d['room']} | المدة: {d['nights']} ليالٍ")
        
        if st.button("✅ تأكيد وحفظ", type="primary"):
            with get_db_connection() as conn:
                conn.execute("INSERT INTO guests (name, bday, wing, room, nights, id_num, phone, job, companions, check_in) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                             (d['name'], d['bday'], d['wing'], d['room'], d['nights'], d['id'], d['phone'], d['job'], d['comps'], str(date.today())))
            st.success("تم التسجيل بنجاح!"); st.session_state.step = "input"; st.rerun()
        
        # ميزة اختيارية: محاكاة طباعة الوصل
        st.download_button("📄 تحميل وصل الحجز (Text)", f"وصل حجز بيت الشباب\nالنزيل: {d['name']}\nالغرفة: {d['room']}\nالتاريخ: {date.today()}", file_name="receipt.txt")

with tabs[1]:
    with get_db_connection() as conn:
        df = pd.read_sql("SELECT * FROM guests ORDER BY id DESC", conn)
        st.dataframe(df, use_container_width=True)

with tabs[2]:
    st.markdown('<div class="section-box"><h4>👮‍♂️ تصدير سجل النزلاء (Police Export)</h4></div>', unsafe_allow_html=True)
    if st.button("📥 إنشاء تقرير إكسل اليومي"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='النزلاء')
        st.download_button("تحميل ملف Excel", output.getvalue(), "Daily_Security_Report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# توقيع المطور الإبداعي
st.markdown(f"""
    <div class="dev-signature">
        <p style="margin-bottom:5px; font-size:0.8rem; color:#888;">Crafted with Precision by</p>
        <div class="dev-text">⚡ <span style="color:#00d4ff;">RIDHA</span> MERZOUG <span style="color:#00d4ff;">TECH</span> ⚡</div>
        <p style="font-size:0.7rem; color:#aaa; margin-top:5px;">© 2026 AI-MODERNIZED SYSTEMS</p>
    </div>
""", unsafe_allow_html=True)
