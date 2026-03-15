import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import sqlite3
import hashlib
from docx import Document
import io
import os
import plotly.express as px

# --- 1. إعدادات الصفحة ---
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

# --- 2. إدارة قاعدة البيانات ---
DB_FILE = "hostel_data_v5.db" # تم تغيير الاسم لضمان بداية نظيفة

def sha256(text): return hashlib.sha256(text.encode("utf-8")).hexdigest()

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # جدول الغرف
    cur.execute("CREATE TABLE IF NOT EXISTS rooms_config (wing TEXT, room TEXT, beds_count INTEGER, PRIMARY KEY (wing, room))")
    # جدول المستخدمين
    cur.execute("CREATE TABLE IF NOT EXISTS users (role TEXT PRIMARY KEY, password_hash TEXT)")
    # جدول الحجوزات
    cur.execute("""CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, birth_date DATE, birth_place TEXT,
        address TEXT, id_type TEXT, id_number TEXT, nationality TEXT, visa_date DATE,
        phone_number TEXT, profession TEXT, wing TEXT, room TEXT, bed TEXT,
        minor_doc TEXT, check_in DATE, check_out DATE, payment REAL, status TEXT DEFAULT 'IN', 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, out_at TIMESTAMP
    )""")
    # جدول الحجوزات المستقبلية
    cur.execute("""CREATE TABLE IF NOT EXISTS future_bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, group_name TEXT, person_count INTEGER, 
        booking_date DATE, phone TEXT
    )""")
    
    # التأكد من وجود الأعمدة الجديدة (لتجنب DatabaseError)
    cols_to_check = [("nationality", "TEXT"), ("visa_date", "DATE"), ("minor_doc", "TEXT"), ("profession", "TEXT"), ("out_at", "TIMESTAMP")]
    for col_name, col_type in cols_to_check:
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

# --- 3. نظام الدخول ---
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
            with get_conn() as conn:
                u = conn.execute("SELECT password_hash FROM users WHERE role=?", (role,)).fetchone()
                if u and sha256(pwd) == u[0]:
                    st.session_state.auth, st.session_state.role = True, role
                    st.rerun()
                else: st.error("❌ كلمة المرور خاطئة")
    st.stop()

# --- القائمة الجانبية ---
st.sidebar.title(f"👤 {st.session_state.role}")
if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.auth = False
    st.rerun()

tabs = st.tabs(["📊 الإحصائيات", "➕ حجز جديد", "📅 حجوزات مستقبلية", "🔍 السجل والإخلاء", "📁 الأرشيف", "⚙️ الإعدادات"])

# --- التبويب 0: الإحصائيات ---
with tabs[0]:
    with get_conn() as conn:
        total_rooms = conn.execute("SELECT COUNT(*) FROM rooms_config").fetchone()[0]
        male_t = conn.execute("SELECT SUM(beds_count) FROM rooms_config WHERE wing='جناح ذكور'").fetchone()[0] or 0
        male_o = conn.execute("SELECT COUNT(*) FROM bookings WHERE status='IN' AND wing='جناح ذكور'").fetchone()[0]
        female_t = conn.execute("SELECT SUM(beds_count) FROM rooms_config WHERE wing='جناح إناث'").fetchone()[0] or 0
        female_o = conn.execute("SELECT COUNT(*) FROM bookings WHERE status='IN' AND wing='جناح إناث'").fetchone()[0]

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="stat-card"><h3>{total_rooms}</h3><p>إجمالي الغرف</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-card"><h3>{male_t - male_o}</h3><p>شاغر (ذكور)</p></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-card"><h3>{female_t - female_o}</h3><p>شاغر (إناث)</p></div>', unsafe_allow_html=True)

# --- التبويب 1: حجز جديد ---
with tabs[1]:
    if st.session_state.step == "input":
        st.subheader("📝 إدخال بيانات النزيل")
        with st.form("main_form"):
            c1, c2 = st.columns(2)
            with c1:
                f_name = st.text_input("الاسم واللقب *")
                b_date = st.date_input("تاريخ الميلاد *", min_value=date(1900,1,1), max_value=date(2060,12,31), value=date(2000,1,1))
                b_place = st.text_input("مكان الميلاد *")
                address = st.text_input("العنوان الشخصي *")
            with c2:
                id_type = st.selectbox("نوع الوثيقة *", ["بطاقة تعريف عادية", "بيومترية", "رخصة سياقة عادية", "بيومترية", "جواز سفر", "أخرى"])
                id_num = st.text_input("رقم الوثيقة *")
                nat_type = st.radio("الجنسية *", ["جزائرية", "أجنبي"], horizontal=True)
                phone = st.text_input("رقم الهاتف (اختياري)")
                nights = st.number_input("عدد الليالي *", min_value=1, value=1)
            
            # حقول إضافية تظهر حسب الحاجة
            nationality = "جزائرية"
            visa_date = None
            if nat_type == "أجنبي":
                nationality = st.text_input("الجنسية بالتفصيل *")
                visa_date = st.date_input("تاريخ دخول التراب الوطني (الفيزا) *")
            
            age = (date.today() - b_date).days // 365
            minor_doc = "N/A"
            if age < 18:
                st.warning(f"⚠️ النزيل قاصر ({age} سنة)")
                minor_doc = st.selectbox("الوثيقة الإجبارية للقاصر *", ["تصريح أبوي", "حضور الولي", "تصريح من الشرطة"])

            with get_conn() as conn:
                df_r = pd.read_sql("SELECT * FROM rooms_config", conn)
            w_choice = st.selectbox("الجناح", df_r['wing'].unique())
            r_choice = st.selectbox("الغرفة", df_r[df_r['wing']==w_choice]['room'].unique())
            b_choice = st.selectbox("السرير", [f"سرير {i}" for i in range(1, 7)])

            if st.form_submit_button("👁️ مراجعة قبل التأكيد"):
                if not f_name or not b_place or not address or not id_num:
                    st.error("⚠️ يرجى ملء كافة الخانات الإجبارية")
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
        st.subheader("📋 مراجعة نهائية")
        d = st.session_state.booking_data
        st.info(f"النزيل: {d['full_name']} | الغرفة: {d['room']} | المبلغ: {d['payment']} دج")
        c_b1, c_b2 = st.columns(2)
        if c_b1.button("🔙 تعديل"): st.session_state.step = "input"; st.rerun()
        if c_b2.button("✅ تأكيد الحجز", type="primary"):
            with get_conn() as conn:
                conn.execute("""INSERT INTO bookings (full_name, birth_date, birth_place, address, id_type, id_number, nationality, visa_date, phone_number, wing, room, bed, minor_doc, check_in, check_out, payment) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
                             (d['full_name'], d['birth_date'], d['birth_place'], d['address'], d['id_type'], d['id_number'], d['nationality'], d['visa_date'], d['phone'], d['wing'], d['room'], d['bed'], d['minor_doc'], date.today(), date.today()+timedelta(days=d['nights']), d['payment']))
                conn.commit()
            st.success("🎉 تم الحجز!"); st.session_state.step = "input"; st.rerun()

# --- التبويب 2: حجوزات مستقبلية ---
with tabs[2]:
    st.subheader("📅 الحجوزات القادمة")
    with st.expander("➕ إضافة حجز مستقبلي"):
        with st.form("f_form"):
            fn = st.text_input("اسم الفوج/الشخص"); fc = st.number_input("العدد", 1); fd = st.date_input("التاريخ"); fp = st.text_input("الهاتف")
            if st.form_submit_button("حفظ"):
                with get_conn() as conn:
                    conn.execute("INSERT INTO future_bookings (group_name, person_count, booking_date, phone) VALUES (?,?,?,?)", (fn, fc, fd, fp))
                    conn.commit(); st.rerun()
    with get_conn() as conn:
        df_f = pd.read_sql("SELECT * FROM future_bookings ORDER BY booking_date", conn)
    for _, r in df_f.iterrows():
        diff = (r['booking_date'] - date.today()).days
        if diff <= 3: st.markdown(f'<div class="red-alert">🚨 تنبيه: حجز {r["group_name"]} بعد {diff} أيام!</div>', unsafe_allow_html=True)
        st.write(f"👤 {r['group_name']} | 👥 {r['person_count']} | 📅 {r['booking_date']}")

# --- التبويب 3: السجل والإخلاء ---
with tabs[3]:
    with get_conn() as conn:
        df_in = pd.read_sql("SELECT id, full_name, room, bed, check_in, payment FROM bookings WHERE status='IN'", conn)
    st.dataframe(df_in, use_container_width=True)
    sel = st.selectbox("اختر نزيل للمغادرة:", df_in['full_name'] + " (ID: " + df_in['id'].astype(str) + ")", index=None)
    if sel and st.button("🚪 إخلاء سبيل"):
        tid = sel.split("(ID: ")[1].replace(")", "")
        with get_conn() as conn:
            conn.execute("UPDATE bookings SET status='OUT', out_at=? WHERE id=?", (datetime.now(), tid))
            conn.commit(); st.rerun()

# --- التبويب 4: الأرشيف ---
with tabs[4]:
    with get_conn() as conn:
        df_arch = pd.read_sql("SELECT * FROM bookings ORDER BY id DESC", conn)
    st.dataframe(df_arch, use_container_width=True)
    if st.button("📝 تصدير الأرشيف لـ Word"):
        doc = Document(); doc.add_heading('سجل النزلاء - بيت الشباب', 0)
        table = doc.add_table(rows=1, cols=4); table.style = 'Table Grid'
        for i, h in enumerate(['الاسم واللقب', 'الميلاد', 'العنوان', 'الهوية']): table.rows[0].cells[i].text = h
        for _, r in df_arch.iterrows():
            row = table.add_row().cells
            row[0].text, row[1].text = str(r['full_name']), f"{r['birth_date']} بـ {r['birth_place']}"
            row[2].text, row[3].text = str(r['address']), f"{r['id_type']} ({r['id_number']})"
        b_word = io.BytesIO(); doc.save(b_word); st.download_button("⬇️ تحميل سجل Word", b_word.getvalue(), "Archive.docx")

# --- التبويب 5: الإعدادات ---
with tabs[5]:
    st.subheader("⚙️ الإعدادات")
    if st.session_state.role == "مدير":
        new_pwd = st.text_input("كلمة مرور المدير الجديدة", type="password")
        if st.button("تحديث كلمة السر"):
            with get_conn() as conn:
                conn.execute("UPDATE users SET password_hash=? WHERE role='مدير'", (sha256(new_pwd),))
                conn.commit(); st.success("✅ تم التحديث")
    else: st.warning("مخصص للمدير فقط")

st.markdown(f'<div class="developer-footer">© RIDHA MERZOUG  | <span style="color:#00d4ff;">®ridha_merzoug®</span> - {date.today().year}</div>', unsafe_allow_html=True)
