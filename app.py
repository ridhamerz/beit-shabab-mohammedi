import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import date, timedelta
from io import BytesIO

# 1. إعداد الصفحة والتصميم (CSS)
st.set_page_config(page_title="Hostel Management Pro - قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&family=Orbitron:wght@500;900&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(135deg, #000428, #004e92); color: white; padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 30px; border-bottom: 5px solid #00d4ff; }
    .stat-card-creative { flex: 1; padding: 20px; border-radius: 15px; color: white; box-shadow: 0 6px 15px rgba(0,0,0,0.1); margin: 5px; min-width: 250px; }
    .male-card { background: linear-gradient(135deg, #1e3c72, #2a5298); border-right: 8px solid #00d4ff; }
    .female-card { background: linear-gradient(135deg, #764ba2, #667eea); border-right: 8px solid #ff00cc; }
    .total-card { background: linear-gradient(135deg, #11998e, #38ef7d); border-right: 8px solid #ffffff; }
    .stat-value { font-size: 2.2rem; font-weight: bold; display: block; }
    .section-box { background: white; padding: 20px; border-radius: 12px; border-right: 6px solid #1e3c72; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .alert-card { background: #fff5f5; border: 1px solid #feb2b2; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 2. إدارة قاعدة البيانات (V18 - تشمل الأسرة والعنوان)
DB_FILE = 'hostel_guelma_v18.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, bday TEXT, bplace TEXT, 
            id_num TEXT, job TEXT, phone TEXT, address TEXT, 
            wing TEXT, room TEXT, bed_num TEXT, nights INTEGER, check_in TEXT, status TEXT DEFAULT 'مقيم'
        )''')

def get_db_connection():
    return sqlite3.connect(DB_FILE)

init_db()

# 3. الدوال المنطقية (Smart Logic)
def get_occupied_beds(wing, room):
    """جلب قائمة الأسرة المحجوزة حالياً في غرفة محددة"""
    with get_db_connection() as conn:
        res = conn.execute("SELECT bed_num FROM guests WHERE wing=? AND room=? AND status='مقيم'", (wing, room)).fetchall()
        return [r[0] for r in res]

def get_checkout_today():
    today = date.today()
    checkout_list = []
    with get_db_connection() as conn:
        data = conn.execute("SELECT name, wing, room, bed_num, check_in, nights FROM guests WHERE status='مقيم'").fetchall()
        for row in data:
            try:
                check_in_date = datetime.datetime.strptime(row[4], '%Y-%m-%d').date()
                if check_in_date + timedelta(days=row[5]) <= today:
                    checkout_list.append(row)
            except: continue
    return checkout_list

# 4. الواجهة البرمجية
st.markdown('<div class="main-title">🏢 HOSTEL MANAGEMENT PRO | محمدي يوسف - قالمة</div>', unsafe_allow_html=True)

# تنبيهات المغادرة التلقائية
checkouts = get_checkout_today()
if checkouts:
    with st.expander(f"⏰ تنبيهات الإخلاء اليوم ({len(checkouts)})", expanded=True):
        for c in checkouts:
            st.markdown(f'<div class="alert-card">⚠️ النزيل: <b>{c[0]}</b> | {c[1]} - {c[2]} ({c[3]})</div>', unsafe_allow_html=True)

tabs = st.tabs(["➕ تسجيل حجز ذكي", "📋 سجل المقيمين", "👮‍♂️ التقارير الأمنية"])

# --- التبويب الأول: الحجز الذكي ---
with tabs[0]:
    if 'step' not in st.session_state: st.session_state.step = "input"
    if 'temp' not in st.session_state: st.session_state.temp = {}

    if st.session_state.step == "input":
        st.markdown('<div class="section-box"><h4>🔍 إدخال بيانات النزيل</h4></div>', unsafe_allow_html=True)
        
        # البحث الذكي لاسترجاع بيانات النزلاء السابقين
        search_id = st.text_input("رقم الهوية للبحث السريع (اختياري):")
        found_data = None
        if search_id:
            with get_db_connection() as conn:
                found_data = conn.execute("SELECT name, bday, bplace, id_num, job, phone, address FROM guests WHERE id_num=? ORDER BY id DESC LIMIT 1", (search_id,)).fetchone()

        with st.form("booking_form"):
            name = st.text_input("👤 الاسم واللقب الكامل *", value=st.session_state.temp.get('name', found_data[0] if found_data else ""))
            address = st.text_input("🏠 العنوان الشخصي الكامل", value=st.session_state.temp.get('address', found_data[6] if found_data else ""))
            
            c1, c2 = st.columns(2)
            wing = c1.selectbox("🏢 الجناح", ["جناح ذكور 👨", "جناح إناث 👩"])
            room = c2.selectbox("🚪 الغرفة", [f"غرفة {i:02d}" for i in range(1, 11)])
            
            # --- نظام الأسرة الذكي (يخفي المحجوز) ---
            occ_beds = get_occupied_beds(wing, room)
            all_beds = [f"سرير {i:02d}" for i in range(1, 7)] # نفترض 6 أسرة لكل غرفة
            available_beds = [b for b in all_beds if b not in occ_beds]
            
            if not available_beds:
                st.error("❌ عذراً، جميع أسرة هذه الغرفة مشغولة!")
                bed_num = None
            else:
                bed_num = st.selectbox("🛏️ اختيار السرير الشاغر", available_beds)
            
            nights = st.number_input("🌙 عدد الليالي", min_value=1, value=1)
            
            with st.expander("🛠️ البيانات القانونية (الوثيقة والهاتف)"):
                id_num = st.text_input("🔢 رقم الوثيقة *", value=st.session_state.temp.get('id', search_id if search_id else ""))
                phone = st.text_input("📞 رقم الهاتف", value=st.session_state.temp.get('phone', found_data[5] if found_data else ""))
            
            if st.form_submit_button("📑 مراجعة البيانات قبل الحفظ", type="primary", use_container_width=True):
                if name and id_num and bed_num:
                    st.session_state.temp = {"name":name, "address":address, "wing":wing, "room":room, "bed":bed_num, "nights":nights, "id":id_num, "phone":phone}
                    st.session_state.step = "review"
                    st.rerun()
                else: st.error("يرجى التأكد من ملء الاسم، رقم الوثيقة، واختيار سرير متاح.")

    elif st.session_state.step == "review":
        d = st.session_state.temp
        st.markdown('<div class="section-box"><h4>👁️ تأكيد الحجز النهائي</h4></div>', unsafe_allow_html=True)
        st.info(f"النزيل: {d['name']} | العنوان: {d['address']}")
        st.warning(f"التسكين: {d['wing']} - {d['room']} - {d['bed']} | المدة: {d['nights']} ليلة")
        
        col_btns = st.columns(2)
        with col_btns[0]:
            if st.button("✅ تأكيد وحفظ", type="primary", use_container_width=True):
                with get_db_connection() as conn:
                    conn.execute("INSERT INTO guests (name, address, wing, room, bed_num, nights, id_num, phone, check_in) VALUES (?,?,?,?,?,?,?,?,?)", 
                                 (d['name'], d['address'], d['wing'], d['room'], d['bed'], d['nights'], d['id'], d['phone'], str(date.today())))
                st.success("🎉 تم تسجيل النزيل بنجاح!")
                st.session_state.temp = {}; st.session_state.step = "input"; st.rerun()
        with col_btns[1]:
            if st.button("✏️ العودة للتعديل", use_container_width=True):
                st.session_state.step = "input"; st.rerun()

# --- التبويبات الأخرى ---
with tabs[1]:
    with get_db_connection() as conn:
        df = pd.read_sql("SELECT name, wing, room, bed_num, address, check_in FROM guests WHERE status='مقيم'", conn)
        st.dataframe(df, use_container_width=True)

with tabs[2]:
    if st.button("📥 تحميل تقرير الشرطة (Excel)"):
        with get_db_connection() as conn:
            full_df = pd.read_sql("SELECT * FROM guests", conn)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                full_df.to_excel(writer, index=False)
            st.download_button("اضغط هنا للتحميل", output.getvalue(), f"Police_Report_{date.today()}.xlsx")

# --- توقيع المطور بلمسة إبداعية فخمة (RIDHA MERZOUG LABS) ---
st.markdown(f"""
    <div style="text-align: center; margin-top: 50px; padding: 30px; border-top: 2px solid #f0f2f6; background: #fafafa;">
        <div style="display: inline-block;">
            <p style="margin: 0; font-size: 0.7rem; color: #888; letter-spacing: 4px; font-weight: bold; text-transform: uppercase;">Engineered with Precision by</p>
            <h1 style="font-family: 'Orbitron', sans-serif; font-weight: 900; margin: 10px 0; font-size: 2rem; background: linear-gradient(135deg, #1e3c72, #00d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                RIDHA MERZOUG <span style="font-size: 1rem; color: #1e3c72; -webkit-text-fill-color: #1e3c72;">LABS</span>
            </h1>
            <div style="width: 80px; height: 4px; background: linear-gradient(90deg, #1e3c72, #00d4ff); margin: 0 auto; border-radius: 10px;"></div>
            <p style="margin-top: 15px; font-size: 0.85rem; color: #1e3c72; font-weight: 700; letter-spacing: 1px;">PREMIUM HOSTEL SOLUTIONS | EDITION 2026</p>
        </div>
    </div>
""", unsafe_allow_html=True)
