import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# 1. إعدادات الصفحة والتصميم
st.set_page_config(page_title="منظومة محمدي يوسف V2.6", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(135deg, #001f3f, #0074D9); color: white; padding: 1rem; border-radius: 15px; text-align: center; margin-bottom:10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 10px 10px 0 0; padding: 10px 25px; font-weight: bold; }
    .stTabs [aria-selected="true"] { background-color: #0074D9 !important; color: white !important; }
    .stat-card { background: #f0f7ff; padding: 10px; border-radius: 12px; border: 1px solid #b3d7ff; text-align: center; }
    .form-section { background: #ffffff; padding: 20px; border-radius: 15px; border-right: 8px solid #0074D9; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# 2. إدارة قاعدة البيانات
DB_FILE = "hostel_pro_v2_2026.db"
TOTAL_BEDS_PER_WING = 38

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, b_date TEXT, b_place TEXT,
            address TEXT, id_type TEXT, id_num TEXT UNIQUE, nationality TEXT, 
            visa_date TEXT, visa_expiry TEXT, job TEXT, phone TEXT, note TEXT, 
            companions TEXT, num_comps INTEGER, minor_doc TEXT, wing TEXT, 
            room TEXT, bed TEXT, status TEXT DEFAULT 'مقيم', check_in TEXT
        )''')

def get_available_beds(wing, room):
    all_beds = [f"سرير {i:02d}" for i in range(1, 7)]
    with sqlite3.connect(DB_FILE) as conn:
        occupied = [r[0] for r in conn.execute("SELECT bed FROM guests WHERE wing=? AND room=? AND status='مقيم'", (wing, room)).fetchall()]
    return [b for b in all_beds if b not in occupied]

def get_resident_info(id_num):
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT name, wing, room, bed FROM guests WHERE id_num=? AND status='مقيم'", (id_num,)).fetchone()

def get_wing_occupancy(wing):
    with sqlite3.connect(DB_FILE) as conn:
        res = conn.execute("SELECT COUNT(*) FROM guests WHERE wing=? AND status='مقيم'", (wing,)).fetchone()
        return res[0] if res else 0

init_db()

# --- الواجهة الرئيسية ---
st.markdown('<div class="main-title">🏢 منظومة بيت الشباب محمدي يوسف - الإدارة الذكية</div>', unsafe_allow_html=True)

# أشرطة الإحصائيات العلوية
occ_m = get_wing_occupancy("جناح ذكور")
occ_f = get_wing_occupancy("جناح إناث")

c_s1, c_s2, c_s3 = st.columns(3)
c_s1.markdown(f'<div class="stat-card">🏨 إجمالي الأسرّة<br><h3>76</h3></div>', unsafe_allow_html=True)
c_s2.markdown(f'<div class="stat-card">♂️ شاغر ذكور<br><h3 style="color:green;">{TOTAL_BEDS_PER_WING - occ_m}</h3></div>', unsafe_allow_html=True)
c_s3.markdown(f'<div class="stat-card">♀️ شاغر إناث<br><h3 style="color:green;">{TOTAL_BEDS_PER_WING - occ_f}</h3></div>', unsafe_allow_html=True)

# إنشاء التبويبات
tab1, tab2 = st.tabs(["📝 حجز جديد (Tab 1)", "📋 السجلات والإدارة (Tab 2)"])

# --- التبويب الأول: الحجز الجديد ---
with tab1:
    with st.expander("🔍 استرجاع بيانات نزيل سابق"):
        s_id = st.text_input("رقم الهوية للبحث")
        if st.button("تعبئة تلقائية"):
            with sqlite3.connect(DB_FILE) as conn:
                old = conn.execute("SELECT * FROM guests WHERE id_num=? ORDER BY id DESC LIMIT 1", (s_id,)).fetchone()
                if old:
                    st.session_state.k_name, st.session_state.k_nat = old[1], old[7]
                    st.session_state.k_addr, st.session_state.k_job = old[4], old[10]
                    st.session_state.k_phone = old[11]
                    st.success("✅ تم العثور على البيانات")

    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    name = st.text_input("👤 الاسم واللقب الكامل *", key="k_name")
    
    col1, col2 = st.columns(2)
    b_date = col1.date_input("📅 تاريخ الميلاد", min_value=date(1940, 1, 1), key="k_bdate")
    b_place = col2.text_input("📍 مكان الازدياد", key="k_bplace")
    
    address = st.text_input("🏠 العنوان الكامل", key="k_addr")
    
    col3, col4 = st.columns(2)
    id_type = col3.selectbox("📄 الوثيقة", ["بطاقة بيومترية", "بطاقة عادية", "رخصة سياقة", "جواز سفر", "أخرى"], key="k_idtype")
    id_num = col4.text_input("🔢 رقم الوثيقة *", key="k_idnum")

    # فحص التكرار اللحظي
    if id_num:
        res = get_resident_info(id_num)
        if res: st.error(f"🚨 تنبيه: النزيل ({res[0]}) مقيم حالياً في {res[1]} - {res[2]}")

    col5, col6 = st.columns(2)
    nat_choice = col5.selectbox("🇩🇿 الجنسية", ["جزائرية", "تونسية", "مغربية", "ليبية", "فرنسية", "أخرى"], key="k_nat_choice")
    nat = col5.text_input("الجنسية يدوياً", key="k_nat_manual") if nat_choice == "أخرى" else nat_choice

    # منطق الفيزا والقاصرين
    visa_ex = None
    is_visa_ok = True
    if nat != "جزائرية":
        st.info("🛂 بيانات الفيزا")
        v_col1, v_col2 = st.columns(2)
        v_in = v_col1.date_input("تاريخ الدخول", key="k_v_in")
        visa_ex = v_col2.date_input("انتهاء الفيزا", key="k_v_ex")
        if visa_ex < date.today():
            st.error("🚨 الفيزا منتهية! لا يمكن الحجز.")
            is_visa_ok = False

    age = date.today().year - b_date.year - ((date.today().month, date.today().day) < (b_date.month, b_date.day))
    is_minor_ok = True
    minor_doc = ""
    if age < 18:
        st.warning(f"⚠️ قاصر ({age} سنة)")
        minor_doc = st.selectbox("📜 الوثيقة المبررة *", ["-- اختر --", "تصريح ابوي", "حضور الولي", "امر بمهة", "تصريح امني"], key="k_minor")
        if minor_doc == "-- اختر --": is_minor_ok = False

    st.divider()
    col9, col10 = st.columns(2)
    wing = col9.selectbox("🏢 الجناح", ["جناح ذكور", "جناح إناث"], key="k_wing")
    room = col10.selectbox("🚪 الغرفة", [f"غرفة {i:02d}" for i in range(1, 11)], key="k_room")
    
    beds = get_available_beds(wing, room)
    bed = st.selectbox("🛏️ السرير", beds, key="k_bed") if beds else None

    can_save = is_visa_ok and is_minor_ok and name and id_num and bed and not get_resident_info(id_num)
    
    if st.button("تأكيد الحجز ✅", use_container_width=True, disabled=not can_save):
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("""INSERT INTO guests (name, b_date, b_place, address, id_type, id_num, nationality, visa_date, visa_expiry, job, phone, companions, num_comps, minor_doc, wing, room, bed, check_in) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                             (name, str(b_date), b_place, address, id_type, id_num, nat, str(date.today()), str(visa_ex), "", "", "", 0, minor_doc, wing, room, bed, str(date.today())))
            st.balloons(); st.success("تم الحجز بنجاح!"); st.rerun()
        except sqlite3.IntegrityError:
            st.error("خطأ: رقم الهوية مسجل مسبقاً.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- التبويب الثاني: السجلات وإدارة الخروج ---
with tab2:
    st.subheader("📋 قائمة المقيمين حالياً")
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT id, name, wing, room, bed, check_in FROM guests WHERE status='مقيم'", conn)
    
    if df.empty:
        st.info("لا يوجد مقيمون حالياً.")
    else:
        search = st.text_input("🔍 ابحث عن اسم نزيل...")
        if search: df = df[df['name'].str.contains(search)]
        
        for idx, row in df.iterrows():
            with st.expander(f"📍 {row['name']} - {row['room']} ({row['bed']})"):
                c_inf, c_act = st.columns([3, 1])
                c_inf.write(f"تاريخ الدخول: {row['check_in']} | الموقع: {row['wing']}")
                if c_act.button("تسجيل خروج 📤", key=f"out_{row['id']}"):
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("UPDATE guests SET status='غادر' WHERE id=?", (row['id'],))
                    st.rerun()

st.markdown("<center><h4>RIDHA MERZOUG LABS</h4></center>", unsafe_allow_html=True)
