import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import io

# ====================== إعدادات الواجهة ======================
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    * { font-family: 'Tahoma', 'Arial', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; font-size: 1.5rem; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .bed-box { display: inline-block; width: 42px; height: 38px; margin: 4px; border-radius: 6px; text-align: center; line-height: 38px; color: white; font-size: 0.85rem; font-weight: bold; }
    .free { background-color: #28a745; border-bottom: 3px solid #1e7e34; }
    .occupied { background-color: #dc3545; border-bottom: 3px solid #a71d2a; }
    .stat-card { background: white; padding: 20px; border-radius: 12px; border-right: 6px solid #1e3c72; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 8px; border-radius: 10px; text-align: center; margin-top: 50px; font-size: 0.75rem; border: 1px solid #00d4ff; }
    </style>
""", unsafe_allow_html=True)

# ====================== قاعدة البيانات ======================
DB_FILE = 'youth_hostel.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS current_guests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        birth_date TEXT,
        birth_place TEXT,
        address TEXT,
        id_card TEXT UNIQUE,
        wing TEXT,
        room TEXT,
        bed TEXT,
        check_in TEXT,
        check_out TEXT,
        status TEXT DEFAULT 'مقيم',
        is_minor TEXT DEFAULT 'لا',
        guardian_name TEXT,
        guardian_permission TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        birth_date TEXT,
        birth_place TEXT,
        address TEXT,
        id_card TEXT,
        wing TEXT,
        room TEXT,
        bed TEXT,
        check_in TEXT,
        check_out TEXT,
        status TEXT,
        is_minor TEXT DEFAULT 'لا',
        guardian_name TEXT,
        guardian_permission TEXT
    )''')
    
    conn.commit()
    conn.close()

    # إضافة الأعمدة إذا لم تكن موجودة
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for table in ['current_guests', 'archive']:
        for col in ['is_minor TEXT DEFAULT "لا"', 'guardian_name TEXT', 'guardian_permission TEXT']:
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass
    conn.commit()
    conn.close()

def get_current_guests():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM current_guests WHERE status = 'مقيم'", conn)
    conn.close()
    return df

def get_archive():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM archive", conn)
    conn.close()
    return df

def get_monthly_data(month, year):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        "SELECT * FROM archive WHERE strftime('%Y-%m', check_out) = ?",
        conn, params=(f"{year}-{month:02d}",)
    )
    conn.close()
    return df

def is_bed_occupied(wing, room, bed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM current_guests WHERE wing=? AND room=? AND bed=? AND status='مقيم'", (wing, room, bed))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def add_guest(name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, guardian_name, guardian_permission):
    age = (date.today() - birth_date).days // 365
    is_minor = 'نعم' if age < 18 else 'لا'
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO current_guests 
        (name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, is_minor, guardian_name, guardian_permission)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, str(birth_date), birth_place, address, id_card, wing, room, bed, str(check_in), str(check_out), is_minor, guardian_name, guardian_permission))
    conn.commit()
    conn.close()

def update_guest(gid, name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, guardian_name, guardian_permission):
    age = (date.today() - birth_date).days // 365
    is_minor = 'نعم' if age < 18 else 'لا'
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        UPDATE current_guests SET
            name=?, birth_date=?, birth_place=?, address=?, id_card=?, wing=?, room=?, bed=?, check_in=?, check_out=?, is_minor=?, guardian_name=?, guardian_permission=?
        WHERE id=?
    """, (name, str(birth_date), birth_place, address, id_card, wing, room, bed, str(check_in), str(check_out), is_minor, guardian_name, guardian_permission, gid))
    conn.commit()
    conn.close()

def evacuate_guest(gid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO archive 
        (name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, status, is_minor, guardian_name, guardian_permission)
        SELECT name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, 'غادر', is_minor, guardian_name, guardian_permission
        FROM current_guests WHERE id=?
    """, (gid,))
    c.execute("DELETE FROM current_guests WHERE id=?", (gid,))
    conn.commit()
    conn.close()

# ====================== تهيئة ======================
init_db()

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'passwords' not in st.session_state:
    st.session_state.passwords = {"مدير": "1234", "عون استقبال": "5678"}

if 'wings' not in st.session_state:
    st.session_state.wings = {
        "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
        "جناح إناث": {"غرفة 06": 2, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد إناث 01": 3, "مرقد إناث 02": 4}
    }
wings = st.session_state.wings

# تسجيل الدخول
if not st.session_state.authenticated:
    st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
    st.subheader("🔐 الدخول للنظام")
    role = st.selectbox("الصفة", ["مدير", "عون استقبال"])
    pwd = st.text_input("كلمة السر", type="password")
    if st.button("دخول آمن", use_container_width=True):
        if pwd == st.session_state.passwords.get(role, ""):
            st.session_state.authenticated = True
            st.session_state.user_role = role
            st.rerun()
        else:
            st.error("كلمة السر خاطئة!")
    st.stop()

# الواجهة الرئيسية
st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
st.sidebar.write(f"👤 المستخدم: **{st.session_state.user_role}**")
if st.sidebar.button("تسجيل الخروج"):
    st.session_state.authenticated = False
    st.rerun()

tabs = (
    st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجل والبحث", "📂 الأرشيف", "📈 الإحصائيات", "⚙️ الإعدادات"])
    if st.session_state.user_role == "مدير" else
    st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجل والبحث"])
)

# حجز جديد
with tabs[0]:
    st.subheader("📝 تسجيل نزيل جديد")
    with st.form("booking_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم واللقب *")
            birth_date = st.date_input("تاريخ الازدياد", value=date.today() - timedelta(days=365*20))
            birth_place = st.text_input("مكان الازدياد")
            addr = st.text_input("العنوان الكامل")
        with c2:
            id_card = st.text_input("رقم بطاقة التعريف *")
            wing = st.selectbox("الجناح", list(wings.keys()))
            room = st.selectbox("الغرفة", list(wings[wing].keys()))
            bed_options = [f"سرير {i+1}" for i in range(wings[wing][room])]
            bed = st.selectbox("رقم السرير", bed_options)
            check_in = st.date_input("تاريخ الدخول", value=date.today())
            check_out = st.date_input("تاريخ الخروج", value=date.today() + timedelta(days=1))

        # حقلي ولي الأمر (يظهران فقط إذا كان قاصر)
        age = (date.today() - birth_date).days // 365
        guardian_name = ""
        guardian_permission = ""
        if age < 18:
            st.markdown("**معلومات ولي الأمر (مطلوبة للقاصرين)**")
            guardian_name = st.text_input("اسم ولي الأمر / الوصي")
            guardian_permission = st.selectbox("نوع التصريح / الإذن", [
                "موافقة خطية",
                "حضور ولي الأمر",
                "إذن قضائي",
                "بدون تصريح (مع مرافق)",
                "غير مطلوب"
            ])

        if st.form_submit_button("✅ تأكيد وحفظ"):
            if not name or not id_card:
                st.error("يرجى ملء الاسم ورقم البطاقة")
            elif check_out <= check_in:
                st.error("تاريخ الخروج يجب أن يكون بعد تاريخ الدخول")
            elif is_bed_occupied(wing, room, bed):
                st.error(f"❌ السرير {bed} في {room} محجوز حالياً!")
            else:
                if age < 18:
                    st.warning(f"⚠️ تنبيه: النزيل قاصر (عمر {age} سنة). يُرجى التأكد من وجود ولي أمر أو إذن قانوني.")
                
                add_guest(name, birth_date, birth_place, addr, id_card, wing, room, bed, check_in, check_out, guardian_name, guardian_permission)
                st.success(f"تم تسجيل النزيل {name} بنجاح (عمر: {age} سنة)")
                st.rerun()

# باقي الكود (حالة الغرف، السجل، التعديل، الإخلاء، الأرشيف، الإحصائيات، الإعدادات) يبقى كما هو مع تعديل بسيط في عرض الجداول لإظهار الحقول الجديدة إذا أردت

# مثال على تعديل عرض الجدول في تبويب السجل:
# st.dataframe(df[['name', 'birth_date', 'age' if 'age' in df else 'birth_date', 'is_minor', 'guardian_name', 'guardian_permission', 'wing', 'room', 'bed']], use_container_width=True)

# تذييل
st.markdown("""
    <div class="developer-footer">
        Developer <span style="color:#00d4ff; font-weight:bold;">®ridha_merzoug®</span> [رضا مرزوق] - 2026
    </div>
""", unsafe_allow_html=True)
