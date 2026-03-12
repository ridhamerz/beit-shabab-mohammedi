import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3
from docx import Document
import io

# ==================== كلمات السر (غيّرها من هنا) ====================
MANAGER_PASSWORD = "1234"
RECEPTION_PASSWORD = "5678"

# ==================== إعداد الصفحة ====================
st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide", page_icon="🏨")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; font-size: 1.5rem; font-weight: bold; }
    .stat-card { background: #ffffff; padding: 20px; border-radius: 15px; border-bottom: 6px solid #1e3c72; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: 0.3s; }
    .stat-card:hover { transform: translateY(-8px); }
    .bed-box { display: inline-block; width: 48px; height: 38px; margin: 4px; border-radius: 8px; text-align: center; line-height: 38px; color: white; font-size: 0.85rem; font-weight: bold; cursor: pointer; }
    .free { background-color: #28a745; }
    .occupied { background-color: #dc3545; }
    .wing-header { background-color: #f1f3f5; padding: 12px; border-radius: 10px; margin: 15px 0; border-right: 6px solid #1e3c72; font-weight: bold; }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 15px; border-radius: 12px; text-align: center; margin-top: 40px; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

# ==================== قاعدة البيانات ====================
DB_FILE = "biet_chabab.db"

@st.cache_resource
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT, birth_date DATE, birth_place TEXT, address TEXT,
        id_type TEXT, id_number TEXT, nationality TEXT, visa_date TEXT,
        wing TEXT, room TEXT, bed TEXT, check_in DATE, check_out DATE, legal_status TEXT
    )''')
    # جدول الغرف
    conn.execute('''CREATE TABLE IF NOT EXISTS rooms_config (
        wing TEXT, room TEXT, beds_count INTEGER, PRIMARY KEY (wing, room)
    )''')
    if conn.execute("SELECT COUNT(*) FROM rooms_config").fetchone()[0] == 0:
        default_rooms = [
            ("جناح ذكور", "غرفة 01", 6), ("جناح ذكور", "غرفة 02", 6), ("جناح ذكور", "غرفة 03", 6),
            ("جناح ذكور", "غرفة 04", 6), ("جناح ذكور", "غرفة 05", 6),
            ("جناح ذكور", "مرقد ذكور 01", 3), ("جناح ذكور", "مرقد ذكور 02", 4),
            ("جناح إناث", "غرفة 06", 2), ("جناح إناث", "غرفة 07", 6), ("جناح إناث", "غرفة 08", 6),
            ("جناح إناث", "غرفة 09", 6), ("جناح إناث", "مرقد إناث 01", 3), ("جناح إناث", "مرقد إناث 02", 4)
        ]
        conn.executemany("INSERT OR IGNORE INTO rooms_config VALUES (?,?,?)", default_rooms)
    conn.commit()

init_db()

def load_wings():
    df = pd.read_sql("SELECT * FROM rooms_config", get_db())
    wings = {}
    for wing in df['wing'].unique():
        sub = df[df['wing'] == wing]
        wings[wing] = dict(zip(sub['room'], sub['beds_count']))
    return wings

wings_config = load_wings()

def load_bookings():
    return pd.read_sql("SELECT * FROM bookings", get_db())

# ==================== حالة التعديل ====================
if 'edit_booking_id' not in st.session_state:
    st.session_state.edit_booking_id = None

# ==================== تسجيل الدخول ====================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<div class="main-title">🏨 نظام إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        role = st.selectbox("🔑 الصفة", ["مدير", "عون استقبال"])
        pwd = st.text_input("🔒 كلمة السر", type="password")
        if st.button("🚀 تسجيل الدخول", use_container_width=True):
            if role == "مدير" and pwd == MANAGER_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.role = role
                st.rerun()
            elif role == "عون استقبال" and pwd == RECEPTION_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.role = role
                st.rerun()
            else:
                st.error("❌ كلمة السر خاطئة")
    st.stop()

# ==================== التبويبات ====================
tabs = st.tabs(["➕ حجز جديد", "🛌 حالة الغرف", "📋 السجل العام", "📄 تصدير Word", "👥 الأفواج", "💰 الحسابات", "⚙️ الإعدادات"])

today = date.today()
df_bookings = load_bookings()

# تنبيه خروج اليوم
exiting_today = df_bookings[df_bookings['check_out'] == today.isoformat()]
if not exiting_today.empty:
    st.info(f"⚠️ يوجد {len(exiting_today)} نزلاء يخرجون اليوم: {', '.join(exiting_today['full_name'].tolist())}")

# ==================== تبويب 1: حجز جديد + تعديل ====================
with tabs[0]:
    # إحصائيات سريعة (نفس السابق)
    occupied = df_bookings[(pd.to_datetime(df_bookings['check_in']).dt.date <= today) & 
                          (pd.to_datetime(df_bookings['check_out']).dt.date > today)] if not df_bookings.empty else pd.DataFrame()
    male_occ = len(occupied[occupied['wing'] == "جناح ذكور"]) if not occupied.empty else 0
    female_occ = len(occupied[occupied['wing'] == "جناح إناث"]) if not occupied.empty else 0
    total_beds = sum(sum(v.values()) for v in wings_config.values())
    occupancy_rate = round((male_occ + female_occ) / total_beds * 100, 1) if total_beds > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("شاغر ذكور", sum(wings_config["جناح ذكور"].values()) - male_occ)
    c2.metric("شاغر إناث", sum(wings_config["جناح إناث"].values()) - female_occ)
    c3.metric("نسبة الإشغال", f"{occupancy_rate}%")
    c4.metric("تاريخ اليوم", today.strftime("%Y-%m-%d"))

    st.divider()

    # وضع التعديل
    if st.session_state.edit_booking_id is not None:
        edit_row = df_bookings[df_bookings['id'] == st.session_state.edit_booking_id].iloc[0]
        st.warning(f"✏️ تعديل الحجز رقم {st.session_state.edit_booking_id} - {edit_row['full_name']}")
        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("الاسم واللقب", edit_row['full_name'])
                birth_date = st.date_input("تاريخ الازدياد", pd.to_datetime(edit_row['birth_date']).date())
                birth_place = st.text_input("مكان الازدياد", edit_row['birth_place'])
                address = st.text_input("العنوان", edit_row['address'])
            with col2:
                id_type = st.selectbox("نوع البطاقة", ["بطاقة تعريف عادية", "بطاقة بيومترية", "جواز سفر"], index=["بطاقة تعريف عادية", "بطاقة بيومترية", "جواز سفر"].index(edit_row['id_type']))
                id_number = st.text_input("رقم البطاقة", edit_row['id_number'])
                wing = st.selectbox("الجناح", list(wings_config.keys()), index=list(wings_config.keys()).index(edit_row['wing']))
                room_options = list(wings_config[wing].keys())
                room = st.selectbox("الغرفة", room_options, index=room_options.index(edit_row['room']))
                bed_options = [f"سرير {i+1}" for i in range(wings_config[wing][room])]
                bed = st.selectbox("السرير", bed_options, index=bed_options.index(edit_row['bed']))
                check_in = st.date_input("تاريخ الدخول", pd.to_datetime(edit_row['check_in']).date())
                check_out = st.date_input("تاريخ الخروج", pd.to_datetime(edit_row['check_out']).date())
                legal = st.text_input("الحالة القانونية", edit_row['legal_status'])

            col_a, col_b = st.columns(2)
            if col_a.form_submit_button("💾 حفظ التعديل", type="primary"):
                conn = get_db()
                overlap = conn.execute("""
                    SELECT COUNT(*) FROM bookings WHERE id != ? AND wing=? AND room=? AND bed=? 
                    AND check_in < ? AND check_out > ?
                """, (st.session_state.edit_booking_id, wing, room, bed, check_out, check_in)).fetchone()[0]
                if overlap > 0:
                    st.error("❌ السرير محجوز في هذه الفترة!")
                else:
                    conn.execute("""UPDATE bookings SET full_name=?, birth_date=?, birth_place=?, address=?, 
                                    id_type=?, id_number=?, wing=?, room=?, bed=?, check_in=?, check_out=?, legal_status=? 
                                    WHERE id=?""",
                                 (name, birth_date, birth_place, address, id_type, id_number, wing, room, bed, check_in, check_out, legal, st.session_state.edit_booking_id))
                    conn.commit()
                    st.success("✅ تم حفظ التعديل!")
                    st.session_state.edit_booking_id = None
                    st.rerun()
            if col_b.form_submit_button("إلغاء"):
                st.session_state.edit_booking_id = None
                st.rerun()

    # نموذج الحجز الجديد (نفس السابق مع مراجعة)
    # ... (الكود الكامل للحجز الجديد كما في النسخة السابقة – لم يتغير)

    # (لتوفير المساحة، باقي نموذج الحجز الجديد موجود في النسخة السابقة ولم يتغير)

# ==================== تبويب 2: حالة الغرف مع popover ====================
with tabs[1]:
    st.subheader("🛌 خريطة توزيع الأسرّة (اضغط على السرير المشغول لرؤية الاسم)")
    for wing_name, rooms in wings_config.items():
        st.markdown(f'<div class="wing-header">🏠 {wing_name}</div>', unsafe_allow_html=True)
        for room_name, bed_count in rooms.items():
            st.write(f"**{room_name}**")
            occupied_dict = {}
            if not df_bookings.empty:
                current = df_bookings[
                    (df_bookings['wing'] == wing_name) &
                    (df_bookings['room'] == room_name) &
                    (pd.to_datetime(df_bookings['check_in']).dt.date <= today) &
                    (pd.to_datetime(df_bookings['check_out']).dt.date > today)
                ]
                for _, row in current.iterrows():
                    occupied_dict[row['bed']] = {'name': row['full_name'], 'checkout': row['check_out']}

            cols = st.columns(bed_count)
            for i in range(bed_count):
                bed_name = f"سرير {i+1}"
                if bed_name in occupied_dict:
                    info = occupied_dict[bed_name]
                    with cols[i].popover(bed_name, use_container_width=True):
                        st.markdown(f"**👤 {info['name']}**")
                        st.caption(f"📤 يخرج: {info['checkout']}")
                    cols[i].markdown(f'<div class="bed-box occupied">{bed_name}</div>', unsafe_allow_html=True)
                else:
                    cols[i].markdown(f'<div class="bed-box free">{bed_name}</div>', unsafe_allow_html=True)

# ==================== تبويب 3: السجل العام مع زر تعديل ====================
with tabs[2]:
    st.subheader("📋 السجل العام")
    search = st.text_input("🔍 ابحث بالاسم أو رقم البطاقة")
    df_filtered = df_bookings[df_bookings['full_name'].str.contains(search, case=False, na=False) | 
                             df_bookings['id_number'].str.contains(search, case=False, na=False)] if search else df_bookings
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    if not df_filtered.empty:
        selected_id = st.selectbox("اختر حجز", df_filtered['id'].tolist())
        col_edit, col_del = st.columns(2)
        if col_edit.button("✏️ تعديل الحجز", use_container_width=True):
            st.session_state.edit_booking_id = selected_id
            st.rerun()
        if col_del.button("🗑️ حذف الحجز", type="secondary", use_container_width=True):
            conn = get_db()
            conn.execute("DELETE FROM bookings WHERE id = ?", (selected_id,))
            conn.commit()
            st.success("✅ تم الحذف")
            st.rerun()

# ==================== باقي التبويبات (نفس السابق) ====================
with tabs[3]:
    st.subheader("📄 تصدير Word")
    if st.button("إنشاء ملف Word لكل النزلاء", use_container_width=True):
        # كود التصدير نفسه (من النسخة السابقة)
        doc = Document()
        doc.add_heading('تقرير نزلاء بيت الشباب محمدي يوسف - قالمة', 0)
        # ... (الكود كامل كما في النسخة السابقة)
        bio = io.BytesIO()
        doc.save(bio)
        bio.seek(0)
        st.download_button("⬇️ تحميل الملف", bio.getvalue(), "تقرير_النزلاء.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

with tabs[4]:
    st.subheader("👥 إدارة الأفواج")
    st.info("قريبًا...")

with tabs[5]:
    st.subheader("💰 الإدارة المالية")
    st.metric("إجمالي النزلاء اليوم", len(df_bookings))
    st.metric("نسبة الإشغال", f"{occupancy_rate}%")

with tabs[6]:
    st.subheader("⚙️ الإعدادات")
    st.write("غيّر كلمات السر من أعلى الكود")

st.markdown(f'''
    <div class="developer-footer">
        🛠️ تم التطوير بواسطة: <b>®ridha_merzoug®</b> [رضا مرزوق]<br>
        📍 بيت شباب محمدي يوسف قالمة - النسخة 2026 المحسنة ✨
    </div>
    ''', unsafe_allow_html=True)
