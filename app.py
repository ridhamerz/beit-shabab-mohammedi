import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import sqlite3
import hashlib
from docx import Document
from docx.shared import Pt
import io
import os
import plotly.express as px

# --- 1. إعدادات الصفحة والواجهة ---
st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide", page_icon="🏨")

# الثوابت
NIGHT_PRICE = 400

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
* { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
.main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; font-size: 1.5rem; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
.stat-card { background: #ffffff; padding: 20px; border-radius: 15px; border-right: 6px solid #1e3c72; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.room-card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
.bed-box { display: inline-block; width: 42px; height: 38px; margin: 3px; border-radius: 8px; text-align: center; line-height: 38px; color: white; font-size: 0.85rem; font-weight: bold; }
.free { background-color: #2ecc71; border-bottom: 3px solid #27ae60; }
.occupied { background-color: #e74c3c; border-bottom: 3px solid #c0392b; }
.wing-header { background: #1e3c72; color: white; padding: 10px 20px; border-radius: 8px; margin: 20px 0 10px 0; font-weight: bold; }
.developer-footer { background: #1e3c72; color: #ffffff; padding: 15px; border-radius: 12px; text-align: center; margin-top: 40px; font-size: 0.85rem; border: 1px solid #00d4ff; }
</style>
""", unsafe_allow_html=True)

# --- 2. إدارة قاعدة البيانات ---
DB_FILE = "biet_chabab.db"

def sha256(text): return hashlib.sha256(text.encode("utf-8")).hexdigest()

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS rooms_config (wing TEXT, room TEXT, beds_count INTEGER, PRIMARY KEY (wing, room))")
    cur.execute("CREATE TABLE IF NOT EXISTS users (role TEXT PRIMARY KEY, password_hash TEXT)")
    cur.execute("""CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, birth_date DATE, birth_place TEXT,
        address TEXT, phone_number TEXT, id_type TEXT, id_number TEXT, wing TEXT, room TEXT, bed TEXT,
        check_in DATE, check_out DATE, payment REAL, status TEXT DEFAULT 'IN', out_at TIMESTAMP
    )""")
    
    # تحديث الأعمدة إذا كانت قديمة
    try: cur.execute("ALTER TABLE bookings ADD COLUMN phone_number TEXT;")
    except: pass
    
    if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        cur.execute("INSERT INTO users VALUES (?,?)", ("مدير", sha256("1234")))
        cur.execute("INSERT INTO users VALUES (?,?)", ("عون استقبال", sha256("5678")))
    
    if cur.execute("SELECT COUNT(*) FROM rooms_config").fetchone()[0] == 0:
        rooms = [("جناح ذكور", f"غرفة {i:02d}", 6) for i in range(1, 6)] + \
                [("جناح إناث", f"غرفة {i:02d}", 6) for i in range(6, 10)]
        cur.executemany("INSERT INTO rooms_config VALUES (?,?,?)", rooms)
    conn.commit()
    conn.close()

init_db()

# --- 3. نظام الدخول ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<div class="main-title">🏨 نظام إدارة بيت الشباب محمدي يوسف قالمة</div>', unsafe_allow_html=True)
    role = st.selectbox("اختر الصلاحية", ["مدير", "عون استقبال"])
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول آمن للمنظومة", use_container_width=True):
        with get_conn() as conn:
            user = conn.execute("SELECT password_hash FROM users WHERE role=?", (role,)).fetchone()
            if user and sha256(pwd) == user[0]:
                st.session_state.authenticated, st.session_state.role = True, role
                st.rerun()
            else: st.error("❌ كلمة المرور خاطئة")
    st.stop()

# القائمة الجانبية
st.sidebar.title(f"👤 مرحباً: {st.session_state.role}")
if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.authenticated = False
    st.rerun()

tabs = st.tabs(["📊 الإحصائيات والمداخيل", "🛏️ حالة الغرف", "➕ حجز جديد", "🔍 السجل والإخلاء", "📁 الأرشيف والإدارة"])

# التبويب 0: الإحصائيات والمداخيل
with tabs[0]:
    with get_conn() as conn:
        df_stats = pd.read_sql("SELECT payment, check_in, wing, status FROM bookings", conn)
    
    if not df_stats.empty:
        df_stats['check_in'] = pd.to_datetime(df_stats['check_in'])
        df_stats['الشهر'] = df_stats['check_in'].dt.strftime('%Y-%m')
        monthly = df_stats.groupby('الشهر')['payment'].sum().reset_index()
        
        c1, c2, c3 = st.columns(3)
        current_in = len(df_stats[df_stats['status'] == 'IN'])
        c1.markdown(f'<div class="stat-card"><h3>{current_in}</h3><p>نزلاء حاليين</p></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card"><h3>{NIGHT_PRICE} دج</h3><p>سعر الليلة</p></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card"><h3>{df_stats["payment"].sum():,.0f} دج</h3><p>إجمالي المداخيل</p></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("💰 تقرير المداخيل الشهرية")
        st.table(monthly)
        fig = px.bar(monthly, x='الشهر', y='payment', title="تطور المداخيل شهرياً")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد بيانات مسجلة حالياً.")

# التبويب 1: حالة الغرف والأسرة (كروت احترافية)
with tabs[1]:
    with get_conn() as conn:
        occ = pd.read_sql("SELECT wing, room, bed FROM bookings WHERE status='IN'", conn)
        wings_df = pd.read_sql("SELECT * FROM rooms_config ORDER BY wing, room", conn)
    
    for wing in wings_df['wing'].unique():
        st.markdown(f'<div class="wing-header">{wing}</div>', unsafe_allow_html=True)
        w_rooms = wings_df[wings_df['wing'] == wing]
        cols = st.columns(3)
        for idx, row in enumerate(w_rooms.itertuples()):
            with cols[idx % 3]:
                st.markdown(f'<div class="room-card"><strong>🏨 {row.room}</strong><br>', unsafe_allow_html=True)
                html = ""
                for b in range(1, row.beds_count + 1):
                    is_occ = not occ[(occ["wing"]==wing) & (occ["room"]==row.room) & (occ["bed"]==f"سرير {b}")].empty
                    html += f'<div class="bed-box {"occupied" if is_occ else "free"}">{b}</div>'
                st.markdown(html + "</div>", unsafe_allow_html=True)

# التبويب 2: حجز جديد
with tabs[2]:
    st.subheader("📝 تسجيل نزيل جديد (السعر ثابت 400 دج)")
    with st.form("new_booking_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم واللقب كاملاً")
            b_place = st.text_input("مكان الازدياد")
            phone = st.text_input("رقم الهاتف")
            addr = st.text_input("العنوان الحالي")
        with c2:
            id_info = st.text_input("رقم وثيقة الهوية")
            w_choice = st.selectbox("الجناح", wings_df['wing'].unique())
            room_opts = wings_df[wings_df['wing'] == w_choice]['room'].tolist()
            r_choice = st.selectbox("الغرفة", room_opts)
            max_b = wings_df[(wings_df['wing']==w_choice) & (wings_df['room']==r_choice)]['beds_count'].values[0]
            b_choice = st.selectbox("رقم السرير", [f"سرير {i}" for i in range(1, max_b + 1)])
            n_days = st.number_input("عدد الليالي", min_value=1, value=1)
        
        if st.form_submit_button("✅ تأكيد الحجز وحفظ البيانات"):
            if not name or not id_info:
                st.warning("⚠️ يرجى ملء الاسم ورقم الهوية على الأقل.")
            else:
                total_pay = n_days * NIGHT_PRICE
                with get_conn() as conn:
                    if conn.execute("SELECT id FROM bookings WHERE wing=? AND room=? AND bed=? AND status='IN'", (w_choice, r_choice, b_choice)).fetchone():
                        st.error("⚠️ هذا السرير مشغول حالياً!")
                    else:
                        conn.execute("""INSERT INTO bookings (full_name, birth_place, phone_number, address, id_number, wing, room, bed, check_in, check_out, payment) 
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?)""", 
                                     (name, b_place, phone, addr, id_info, w_choice, r_choice, b_choice, date.today(), date.today()+timedelta(days=n_days), total_pay))
                        conn.commit(); st.success(f"✅ تم الحجز بنجاح. المبلغ المطلوب: {total_pay} دج"); st.rerun()

# التبويب 3: السجل والإخلاء والتمديد
with tabs[3]:
    with get_conn() as conn:
        df_in = pd.read_sql("SELECT id, full_name, phone_number, room, bed, check_in, check_out, payment FROM bookings WHERE status='IN'", conn)
    
    st.subheader("🔍 النزلاء المقيمون حالياً")
    st.dataframe(df_in, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.write("🏃 **عمليات سريعة**")
        target = st.selectbox("اختر النزيل:", df_in['full_name'] + " (ID: " + df_in['id'].astype(str) + ")", index=None)
        if st.button("🚪 إخلاء سبيل (Check-out)", type="primary") and target:
            tid = target.split("(ID: ")[1].replace(")", "")
            with get_conn() as conn:
                conn.execute("UPDATE bookings SET status='OUT', out_at=? WHERE id=?", (datetime.now(), tid))
                conn.commit(); st.success("تم الإخلاء"); st.rerun()

    with col_b:
        st.write("⏳ **تمديد الإقامة**")
        if st.button("➕ تمديد ليلة إضافية (+400 دج)") and target:
            tid = target.split("(ID: ")[1].replace(")", "")
            with get_conn() as conn:
                conn.execute("UPDATE bookings SET check_out = date(check_out, '+1 day'), payment = payment + ? WHERE id=?", (NIGHT_PRICE, tid))
                conn.commit(); st.success("تم التمديد بنجاح"); st.rerun()

    with col_c:
        st.write("🧾 **الوثائق**")
        if st.button("🖨️ استخراج وصل النزيل (Word)") and target:
            tid = target.split("(ID: ")[1].replace(")", "")
            row = df_in[df_in['id'] == int(tid)].iloc[0]
            doc = Document()
            doc.add_heading('وصل استلام - بيت الشباب محمدي يوسف', 0)
            p = doc.add_paragraph()
            p.add_run(f"اسم النزيل: {row['full_name']}\n").bold = True
            p.add_run(f"الغرفة: {row['room']} | السرير: {row['bed']}\n")
            p.add_run(f"تاريخ الدخول: {row['check_in']}\n")
            p.add_run(f"المبلغ المدفوع: {row['payment']} دج\n")
            p.add_run(f"رقم الهاتف: {row['phone_number']}\n")
            doc.add_paragraph("\nختم الإدارة: ............................").alignment = 2
            bio = io.BytesIO(); doc.save(bio)
            st.download_button("⬇️ تحميل الوصل الآن", bio.getvalue(), f"وصل_{row['full_name']}.docx")

# التبويب 4: الأرشيف والإدارة المتقدمة
with tabs[4]:
    if st.session_state.role == "مدير":
        st.subheader("⚙️ إعدادات المدير")
        with st.expander("🛠️ تعديل سعة الغرف (إضافة/إنقاص أسرة)"):
            c1, c2, c3 = st.columns(3)
            with c1: e_wing = st.selectbox("الجناح", wings_df['wing'].unique(), key="ew")
            with c2: e_room = st.selectbox("الغرفة", wings_df[wings_df['wing']==e_wing]['room'].unique(), key="er")
            with c3: 
                old_val = wings_df[(wings_df['wing']==e_wing) & (wings_df['room']==e_room)]['beds_count'].values[0]
                new_val = st.number_input("العدد الجديد للأسرة", min_value=1, value=int(old_val))
            if st.button("تحديث السعة فوراً"):
                with get_conn() as conn:
                    conn.execute("UPDATE rooms_config SET beds_count=? WHERE wing=? AND room=?", (new_val, e_wing, e_room))
                    conn.commit(); st.success("تم تحديث سعة الغرفة بنجاح"); st.rerun()

    st.markdown("---")
    st.subheader("📁 أرشيف النزلاء الكامل")
    search = st.text_input("🔍 ابحث بالاسم أو رقم الهاتف أو رقم الهوية...")
    with get_conn() as conn:
        df_arch = pd.read_sql("SELECT * FROM bookings WHERE full_name LIKE ? OR phone_number LIKE ? OR id_number LIKE ? ORDER BY id DESC", 
                              conn, params=(f'%{search}%', f'%{search}%', f'%{search}%'))
    st.dataframe(df_arch, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        out_ex = io.BytesIO()
        df_arch.to_excel(out_ex, index=False)
        st.download_button("📊 تصدير الأرشيف لـ Excel", out_ex.getvalue(), "Archive_Full.xlsx")
    with c2:
        if st.button("📝 تصدير تقرير Word للنزلاء الحاليين"):
            doc = Document(); doc.add_heading('قائمة النزلاء الحاليين', 0)
            table = doc.add_table(rows=1, cols=5); table.style = 'Table Grid'
            for i, h in enumerate(['الاسم', 'الهاتف', 'الغرفة', 'الدخول', 'المبلغ']): table.rows[0].cells[i].text = h
            for _, r in df_in.iterrows():
                row = table.add_row().cells
                row[0].text, row[1].text, row[2].text, row[3].text, row[4].text = str(r['full_name']), str(r['phone_number']), str(r['room']), str(r['check_in']), str(r['payment'])
            b_word = io.BytesIO(); doc.save(b_word)
            st.download_button("⬇️ تحميل تقرير Word", b_word.getvalue(), "Current_Guests.docx")

st.markdown(f'<div class="developer-footer">© RIDHA MERZOUG LABS | Developer <span style="color:#00d4ff; font-weight:bold;">®ridha_merzoug®</span> - {date.today().year}</div>', unsafe_allow_html=True)
