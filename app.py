import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import sqlite3
import hashlib
from docx import Document
import io
import os
import plotly.express as px

# --- 1. إعدادات الصفحة والواجهة ---
st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide", page_icon="🏨")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
* { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
.main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; font-size: 1.5rem; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
.stat-card { background: #ffffff; padding: 20px; border-radius: 15px; border-right: 6px solid #1e3c72; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.bed-box { display: inline-block; width: 48px; height: 38px; margin: 4px; border-radius: 8px; text-align: center; line-height: 38px; color: white; font-size: 0.85rem; font-weight: bold; }
.free { background-color: #28a745; border-bottom: 3px solid #1e7e34; }
.occupied { background-color: #dc3545; border-bottom: 3px solid #a71d2a; }
.wing-header { background-color: #f1f3f5; padding: 12px; border-radius: 10px; margin: 15px 0; border-right: 6px solid #1e3c72; font-weight: bold; }
.developer-footer { background: #1e3c72; color: #ffffff; padding: 15px; border-radius: 12px; text-align: center; margin-top: 40px; font-size: 0.85rem; border: 1px solid #00d4ff; }
</style>
""", unsafe_allow_html=True)

# --- 2. إعدادات قاعدة البيانات SQLite ---
DB_FILE = "biet_chabab.db"

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rooms_config (
        wing TEXT NOT NULL, room TEXT NOT NULL, beds_count INTEGER NOT NULL, PRIMARY KEY (wing, room)
    );""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        role TEXT PRIMARY KEY, password_hash TEXT NOT NULL
    );""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL, birth_date DATE, birth_place TEXT, address TEXT,
        id_type TEXT, id_number TEXT NOT NULL, wing TEXT NOT NULL, room TEXT NOT NULL,
        bed TEXT NOT NULL, check_in DATE NOT NULL, check_out DATE NOT NULL,
        payment REAL DEFAULT 0, status TEXT NOT NULL DEFAULT 'IN', out_at TIMESTAMP
    );""")
    
    # تحديث تلقائي لقاعدة البيانات (إضافة حقل المال إذا لم يوجد)
    try: cur.execute("ALTER TABLE bookings ADD COLUMN payment REAL DEFAULT 0;")
    except: pass

    if cur.execute("SELECT COUNT(*) FROM users;").fetchone()[0] == 0:
        cur.execute("INSERT INTO users(role, password_hash) VALUES (?,?)", ("مدير", sha256("1234")))
        cur.execute("INSERT INTO users(role, password_hash) VALUES (?,?)", ("عون استقبال", sha256("5678")))
    
    if cur.execute("SELECT COUNT(*) FROM rooms_config;").fetchone()[0] == 0:
        default_rooms = [
            ("جناح ذكور", "غرفة 01", 6), ("جناح ذكور", "غرفة 02", 6), ("جناح ذكور", "غرفة 03", 6),
            ("جناح ذكور", "غرفة 04", 6), ("جناح ذكور", "غرفة 05", 6), ("جناح ذكور", "مرقد 01", 3), ("جناح ذكور", "مرقد 02", 4),
            ("جناح إناث", "غرفة 06", 2), ("جناح إناث", "غرفة 07", 6), ("جناح إناث", "غرفة 08", 6),
            ("جناح إناث", "غرفة 09", 6), ("جناح إناث", "مرقد 01", 3), ("جناح إناث", "مرقد 02", 4)
        ]
        cur.executemany("INSERT INTO rooms_config(wing, room, beds_count) VALUES (?,?,?)", default_rooms)
    conn.commit()
    conn.close()

def load_wings():
    with get_conn() as conn:
        df = pd.read_sql("SELECT * FROM rooms_config ORDER BY wing, room", conn)
    wings = {}
    for wing in df['wing'].unique():
        sub = df[df['wing'] == wing]
        wings[wing] = dict(zip(sub['room'], sub['beds_count']))
    return wings

# --- 3. تشغيل النظام ---
init_db()
wings_data = load_wings()

if 'authenticated' not in st.session_state: st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<div class="main-title">🏨 نظام بيت الشباب محمدي يوسف قالمة</div>', unsafe_allow_html=True)
    role = st.selectbox("الصلاحية", ["مدير", "عون استقبال"])
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول آمن", use_container_width=True):
        with get_conn() as conn:
            user = conn.execute("SELECT password_hash FROM users WHERE role=?", (role,)).fetchone()
            if user and sha256(pwd) == user[0]:
                st.session_state.authenticated, st.session_state.role = True, role
                st.rerun()
            else: st.error("❌ كلمة المرور خاطئة")
    st.stop()

# القائمة الجانبية
st.sidebar.title(f"👤 {st.session_state.role}")
if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.authenticated = False
    st.rerun()

# --- 4. التبويبات والعمليات ---
tabs = st.tabs(["📊 الإحصائيات", "🛏️ حالة الغرف", "➕ حجز جديد", "🔍 السجل والإخلاء", "📁 الأرشيف والإدارة"])

# التبويب 0: الإحصائيات (Dashboard)
with tabs[0]:
    st.subheader("📈 لوحة التحكم والإحصائيات")
    with get_conn() as conn:
        df_all = pd.read_sql("SELECT * FROM bookings", conn)
    
    total_beds = sum(sum(r.values()) for r in wings_data.values())
    current_in = len(df_all[df_all['status'] == 'IN'])
    total_rev = df_all['payment'].sum()

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="stat-card"><h3>{current_in}</h3><p>نزلاء حاليين</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-card"><h3>%{ (current_in/total_beds)*100:.1f}</h3><p>نسبة الإشغال</p></div>', unsafe_allow_html=True)
    if st.session_state.role == "مدير":
        c3.markdown(f'<div class="stat-card"><h3>{total_rev:,.2f} دج</h3><p>إجمالي المداخيل</p></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    if not df_all.empty:
        fig = px.pie(df_all[df_all['status'] == 'IN'], names='wing', title="توزيع النزلاء حسب الأجنحة", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

# التبويب 1: خريطة الغرف
with tabs[1]:
    with get_conn() as conn:
        occ_beds = pd.read_sql("SELECT wing, room, bed FROM bookings WHERE status='IN'", conn)
    for wing, rooms in wings_data.items():
        st.markdown(f'<div class="wing-header">{wing}</div>', unsafe_allow_html=True)
        for room, count in rooms.items():
            cols = st.columns([1, 6])
            cols[0].write(f"**{room}**")
            html = "".join([f'<div class="bed-box {"occupied" if not occ_beds[(occ_beds["wing"]==wing) & (occ_beds["room"]==room) & (occ_beds["bed"]==f"سرير {b}")].empty else "free"}">{b}</div>' for b in range(1, count + 1)])
            cols[1].markdown(html, unsafe_allow_html=True)

# التبويب 2: حجز جديد
with tabs[2]:
    st.subheader("📝 تسجيل نزيل جديد")
    with st.form("booking_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم واللقب")
            birth_d = st.date_input("تاريخ الازدياد", value=date(2000, 1, 1))
            addr = st.text_input("العنوان الكامل")
            pay = st.number_input("المبلغ المدفوع (دج)", min_value=0.0, step=100.0)
        with c2:
            id_num = st.text_input("رقم الهوية")
            w_choice = st.selectbox("الجناح", list(wings_data.keys()))
            r_choice = st.selectbox("الغرفة", list(wings_data[w_choice].keys()))
            b_choice = st.selectbox("رقم السرير", [f"سرير {i+1}" for i in range(wings_data[w_choice][r_choice])])
        
        if st.form_submit_button("✅ تأكيد الحجز"):
            if name and id_num:
                with get_conn() as conn:
                    check = conn.execute("SELECT id FROM bookings WHERE wing=? AND room=? AND bed=? AND status='IN'", (w_choice, r_choice, b_choice)).fetchone()
                    if check: st.error("⚠️ السرير مشغول!")
                    else:
                        conn.execute("INSERT INTO bookings (full_name, birth_date, address, id_number, wing, room, bed, check_in, check_out, payment, status) VALUES (?,?,?,?,?,?,?,?,?,?,'IN')", 
                                     (name, str(birth_d), addr, id_num, w_choice, r_choice, b_choice, str(date.today()), str(date.today()+timedelta(days=1)), pay))
                        conn.commit()
                        st.success(f"تم تسجيل {name} بنجاح."); st.rerun()

# التبويب 3: السجل والإخلاء
with tabs[3]:
    with get_conn() as conn:
        df_in = pd.read_sql("SELECT id, full_name as 'الاسم', wing as 'الجناح', room as 'الغرفة', bed as 'السرير', payment as 'المبلغ' FROM bookings WHERE status='IN'", conn)
    st.dataframe(df_in, use_container_width=True, hide_index=True)
    if not df_in.empty:
        out_id = st.selectbox("اختر النزيل للمغادرة:", df_in['الاسم'] + " (" + df_in['الغرفة'] + ")", index=None)
        if st.button("🚪 تأكيد الإخلاء", type="primary") and out_id:
            s_name = out_id.split(" (")[0]
            with get_conn() as conn:
                conn.execute("UPDATE bookings SET status='OUT', out_at=? WHERE full_name=? AND status='IN'", (str(datetime.now()), s_name))
                conn.commit()
            st.success("✅ تم الإخلاء."); st.rerun()

# التبويب 4: الأرشيف والإدارة المتقدمة
with tabs[4]:
    st.subheader("📂 الأرشيف والنسخ الاحتياطي")
    c1, c2 = st.columns(2)
    with c1: start_d = st.date_input("من تاريخ", date.today() - timedelta(days=30))
    with c2: end_d = st.date_input("إلى تاريخ", date.today())
    
    with get_conn() as conn:
        df_arch = pd.read_sql("SELECT * FROM bookings WHERE check_in BETWEEN ? AND ?", conn, params=(str(start_d), str(end_d)))
    st.dataframe(df_arch, use_container_width=True)

    # أزرار الإدارة
    col1, col2, col3 = st.columns(3)
    with col1:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_arch.to_excel(writer, index=False, sheet_name='Sheet1')
        st.download_button("📊 تحميل الأرشيف Excel", output.getvalue(), "archive.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    with col2:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "rb") as f:
                st.download_button("🛡️ نسخة احتياطية (DB)", f.read(), "backup_system.db", "application/octet-stream")
    
    with col3:
        if st.button("📝 تقرير Word للنزلاء الحاليين"):
            doc = Document(); doc.add_heading('تقرير النزلاء الحاليين', 0)
            table = doc.add_table(rows=1, cols=4); table.style = 'Table Grid'
            for i, h in enumerate(['الاسم', 'الجناح', 'الغرفة', 'السرير']): table.rows[0].cells[i].text = h
            for _, r in df_in.iterrows():
                row = table.add_row().cells
                row[0].text, row[1].text, row[2].text, row[3].text = str(r['الاسم']), str(r['الجناح']), str(r['الغرفة']), str(r['السرير'])
            b_word = io.BytesIO(); doc.save(b_word)
            st.download_button("⬇️ تحميل Word", b_word.getvalue(), "Report.docx")

st.markdown(f'<div class="developer-footer">RIDHA MERZOUG LABS | <span style="color:#00d4ff;">®ridha_merzoug®</span> - {date.today().year}</div>', unsafe_allow_html=True)
