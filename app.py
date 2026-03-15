import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import sqlite3
import hashlib
from docx import Document
import io
import os
import plotly.express as px

# ==================== إعدادات الصفحة ====================
st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide", page_icon="🏨")

NIGHT_PRICE = 400

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
* { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
.main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
.stat-card { background: white; padding: 20px; border-radius: 15px; border-bottom: 5px solid #1e3c72; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 10px; }
.red-alert { background-color: #ff4b4b; color: white; padding: 10px; border-radius: 8px; font-weight: bold; text-align: center; margin-bottom: 5px; }
.developer-footer { background: #1e3c72; color: white; padding: 15px; border-radius: 12px; text-align: center; margin-top: 50px; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# ==================== قاعدة البيانات ====================
DB_FILE = "hostel_data_v5.db"

def sha256(text): return hashlib.sha256(text.encode("utf-8")).hexdigest()

@st.cache_resource
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS rooms_config (wing TEXT, room TEXT, beds_count INTEGER, PRIMARY KEY (wing, room))")
    cur.execute("CREATE TABLE IF NOT EXISTS users (role TEXT PRIMARY KEY, password_hash TEXT)")
    cur.execute("""CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, birth_date DATE, birth_place TEXT,
        address TEXT, id_type TEXT, id_number TEXT, nationality TEXT, visa_date DATE,
        phone_number TEXT, profession TEXT, wing TEXT, room TEXT, bed TEXT,
        minor_doc TEXT, check_in DATE, check_out DATE, payment REAL, status TEXT DEFAULT 'IN', 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, out_at TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS future_bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, group_name TEXT, person_count INTEGER, 
        booking_date DATE, phone TEXT
    )""")

    # إضافة الأعمدة الجديدة بأمان
    cols = [("nationality", "TEXT"), ("visa_date", "DATE"), ("minor_doc", "TEXT"), ("profession", "TEXT"), ("out_at", "TIMESTAMP")]
    for col_name, col_type in cols:
        try: cur.execute(f"ALTER TABLE bookings ADD COLUMN {col_name} {col_type};")
        except: pass

    if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        cur.execute("INSERT INTO users VALUES (?,?)", ("مدير", sha256("1234")))
        cur.execute("INSERT INTO users VALUES (?,?)", ("عون استقبال", sha256("5678")))

    if cur.execute("SELECT COUNT(*) FROM rooms_config").fetchone()[0] == 0:
        rooms = [("جناح ذكور", f"غرفة {i:02d}", 6) for i in range(1, 6)] + \
                [("جناح إناث", f"غرفة {i:02d}", 6) for i in range(6, 11)]
        cur.executemany("INSERT INTO rooms_config VALUES (?,?,?)", rooms)
    conn.commit()
    conn.close()

init_db()

def load_wings():
    df = pd.read_sql("SELECT * FROM rooms_config", get_db())
    wings = {}
    for wing in df['wing'].unique():
        sub = df[df['wing'] == wing]
        wings[wing] = dict(zip(sub['room'], sub['beds_count']))
    return wings

wings_data = load_wings()

# ==================== تسجيل الدخول ====================
if 'auth' not in st.session_state: st.session_state.auth = False
if 'booking_data' not in st.session_state: st.session_state.booking_data = {}
if 'step' not in st.session_state: st.session_state.step = "input"

if not st.session_state.auth:
    st.markdown('<div class="main-title">🏨 نظام إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        role = st.selectbox("اختر الصلاحية", ["مدير", "عون استقبال"])
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول آمن", use_container_width=True):
            with get_db() as conn:
                u = conn.execute("SELECT password_hash FROM users WHERE role=?", (role,)).fetchone()
                if u and sha256(pwd) == u[0]:
                    st.session_state.auth, st.session_state.role = True, role
                    st.rerun()
                else: st.error("❌ كلمة المرور خاطئة")
    st.stop()

# Sidebar
st.sidebar.title(f"👤 {st.session_state.role}")
if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.auth = False
    st.rerun()

tabs = st.tabs(["➕ حجز جديد", "📅 حجوزات مستقبلية", "🔍 السجل والإخلاء", "📁 الأرشيف", "⚙️ الإعدادات"])

# ==================== تبويب 0: حجز جديد (مع الكروت المدموجة) ====================
with tabs[0]:
    # === الكروت المربعة (الإحصائيات المدموجة) ===
    with get_db() as conn:
        male_total = conn.execute("SELECT SUM(beds_count) FROM rooms_config WHERE wing='جناح ذكور'").fetchone()[0] or 0
        male_occupied = conn.execute("SELECT COUNT(*) FROM bookings WHERE status='IN' AND wing='جناح ذكور'").fetchone()[0]
        female_total = conn.execute("SELECT SUM(beds_count) FROM rooms_config WHERE wing='جناح إناث'").fetchone()[0] or 0
        female_occupied = conn.execute("SELECT COUNT(*) FROM bookings WHERE status='IN' AND wing='جناح إناث'").fetchone()[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="stat-card"><h3>{male_total - male_occupied}</h3><p>شاغر ذكور</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-card"><h3>{female_total - female_occupied}</h3><p>شاغر إناث</p></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-card"><h3>{male_occupied + female_occupied}</h3><p>نزلاء حاليين</p></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="stat-card"><h3>{male_total + female_total}</h3><p>إجمالي الأسرّة</p></div>', unsafe_allow_html=True)

    st.divider()

    # === نموذج الحجز (نفس الهيكل الأصلي مع التصليحات) ===
    if st.session_state.step == "input":
        st.subheader("📝 إدخال بيانات النزيل")
        with st.form("main_form"):
            c1, c2 = st.columns(2)
            with c1:
                f_name = st.text_input("الاسم واللقب *")
                b_date = st.date_input("تاريخ الميلاد *", value=date(2000,1,1))
                b_place = st.text_input("مكان الميلاد *")
                address = st.text_input("العنوان الشخصي *")
            with c2:
                id_type = st.selectbox("نوع الوثيقة *", ["بطاقة تعريف عادية", "بيومترية", "جواز سفر"])
                id_num = st.text_input("رقم الوثيقة *")
                nat_type = st.radio("الجنسية *", ["جزائرية", "أجنبي"], horizontal=True)
                phone = st.text_input("رقم الهاتف")
                nights = st.number_input("عدد الليالي *", min_value=1, value=1)

            nationality = "جزائرية"
            visa_date = None
            if nat_type == "أجنبي":
                nationality = st.text_input("الجنسية بالتفصيل *")
                visa_date = st.date_input("تاريخ الفيزا *")

            age = (date.today() - b_date).days // 365
            minor_doc = "N/A"
            if age < 18:
                st.warning(f"⚠️ النزيل قاصر ({age} سنة)")
                minor_doc = st.selectbox("وثيقة القاصر *", ["تصريح أبوي", "حضور الولي"])

            w_choice = st.selectbox("الجناح", list(wings_data.keys()))
            r_choice = st.selectbox("الغرفة", list(wings_data[w_choice].keys()))
            b_choice = st.selectbox("السرير", [f"سرير {i}" for i in range(1, wings_data[w_choice][r_choice]+1)])

            if st.form_submit_button("👁️ مراجعة قبل التأكيد"):
                if not f_name or not id_num:
                    st.error("⚠️ يرجى ملء الخانات الإجبارية")
                else:
                    st.session_state.booking_data = {
                        "full_name": f_name, "birth_date": b_date, "birth_place": b_place,
                        "address": address, "id_type": id_type, "id_number": id_num,
                        "nationality": nationality, "visa_date": visa_date, "phone": phone,
                        "wing": w_choice, "room": r_choice, "bed": b_choice,
                        "minor_doc": minor_doc, "nights": nights, "payment": nights * NIGHT_PRICE
                    }
                    st.session_state.step = "review"
                    st.rerun()

    elif st.session_state.step == "review":
        d = st.session_state.booking_data
        st.subheader("📋 مراجعة نهائية")
        st.info(f"الاسم: {d['full_name']} | الغرفة: {d['room']} | المبلغ: {d['payment']} دج")
        col1, col2 = st.columns(2)
        if col1.button("🔙 تعديل"):
            st.session_state.step = "input"
            st.rerun()
        if col2.button("✅ تأكيد الحجز", type="primary"):
            with get_db() as conn:
                conn.execute("""INSERT INTO bookings 
                    (full_name, birth_date, birth_place, address, id_type, id_number, nationality, 
                     visa_date, phone_number, wing, room, bed, minor_doc, check_in, check_out, payment)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (d['full_name'], d['birth_date'], d['birth_place'], d['address'], d['id_type'],
                     d['id_number'], d['nationality'], d['visa_date'], d['phone'], d['wing'],
                     d['room'], d['bed'], d['minor_doc'], date.today(), 
                     date.today() + timedelta(days=d['nights']), d['payment']))
                conn.commit()
            st.success("🎉 تم الحجز بنجاح!")
            st.session_state.step = "input"
            st.rerun()

# ==================== تبويب 1: حجوزات مستقبلية (مع الإحصائيات الجديدة) ====================
with tabs[1]:
    st.subheader("📅 الحجوزات القادمة")
    
    # إحصائيات الحجوزات المستقبلية
    with get_db() as conn:
        total_future = conn.execute("SELECT COUNT(*) FROM future_bookings").fetchone()[0]
        st.metric("إجمالي الحجوزات المستقبلية", total_future)

    with st.expander("➕ إضافة حجز مستقبلي"):
        with st.form("f_form"):
            fn = st.text_input("اسم الفوج/الشخص")
            fc = st.number_input("عدد الأشخاص", min_value=1)
            fd = st.date_input("تاريخ الحجز")
            fp = st.text_input("رقم الهاتف")
            if st.form_submit_button("حفظ"):
                with get_db() as conn:
                    conn.execute("INSERT INTO future_bookings (group_name, person_count, booking_date, phone) VALUES (?,?,?,?)", 
                                 (fn, fc, fd, fp))
                    conn.commit()
                st.rerun()

    with get_db() as conn:
        df_f = pd.read_sql("SELECT * FROM future_bookings ORDER BY booking_date", conn)
    for _, r in df_f.iterrows():
        diff = (r['booking_date'] - date.today()).days
        if diff <= 3:
            st.markdown(f'<div class="red-alert">🚨 تنبيه: حجز {r["group_name"]} بعد {diff} أيام!</div>', unsafe_allow_html=True)
        st.write(f"👤 {r['group_name']} | 👥 {r['person_count']} | 📅 {r['booking_date']}")

# باقي التبويبات (السجل، الأرشيف، الإعدادات) بدون تغيير جوهري
with tabs[2]:
    st.subheader("🔍 السجل والإخلاء")
    with get_db() as conn:
        df_in = pd.read_sql("SELECT id, full_name, room, bed, check_in, payment FROM bookings WHERE status='IN'", conn)
    st.dataframe(df_in, use_container_width=True)
    if not df_in.empty:
        sel = st.selectbox("اختر نزيل للإخلاء", df_in['id'])
        if st.button("🚪 إخلاء"):
            with get_db() as conn:
                conn.execute("UPDATE bookings SET status='OUT', out_at=? WHERE id=?", (datetime.now(), sel))
                conn.commit()
            st.success("تم الإخلاء")
            st.rerun()

with tabs[3]:
    st.subheader("📁 الأرشيف")
    with get_db() as conn:
        df_arch = pd.read_sql("SELECT * FROM bookings ORDER BY id DESC", conn)
    st.dataframe(df_arch, use_container_width=True)
    if st.button("📝 تصدير Word"):
        doc = Document()
        doc.add_heading('سجل النزلاء', 0)
        table = doc.add_table(rows=1, cols=4)
        for i, h in enumerate(['الاسم', 'الغرفة', 'التاريخ', 'المبلغ']): table.rows[0].cells[i].text = h
        for _, r in df_arch.iterrows():
            row = table.add_row().cells
            row[0].text = str(r['full_name'])
            row[1].text = f"{r['room']} - {r['bed']}"
            row[2].text = str(r['check_in'])
            row[3].text = str(r['payment'])
        b = io.BytesIO()
        doc.save(b)
        st.download_button("⬇️ تحميل Word", b.getvalue(), "Archive.docx")

with tabs[4]:
    st.subheader("⚙️ الإعدادات")
    if st.session_state.role == "مدير":
        new_pwd = st.text_input("كلمة مرور جديدة", type="password")
        if st.button("تحديث"):
            with get_db() as conn:
                conn.execute("UPDATE users SET password_hash=? WHERE role='مدير'", (sha256(new_pwd),))
                conn.commit()
            st.success("تم التحديث")

st.markdown(f'<div class="developer-footer">© RIDHA MERZOUG LABS | {date.today().year}</div>', unsafe_allow_html=True)
