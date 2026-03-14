import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import sqlite3
import hashlib
from docx import Document
import io

st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide", page_icon="🏨")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
* { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
.main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; font-size: 1.5rem; font-weight: bold; }
.stat-card { background: #ffffff; padding: 20px; border-radius: 15px; border-bottom: 6px solid #1e3c72; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: 0.3s; }
.stat-card:hover { transform: translateY(-8px); }
.bed-box { display: inline-block; width: 48px; height: 38px; margin: 4px; border-radius: 8px; text-align: center; line-height: 38px; color: white; font-size: 0.85rem; font-weight: bold; }
.free { background-color: #28a745; }
.occupied { background-color: #dc3545; }
.wing-header { background-color: #f1f3f5; padding: 12px; border-radius: 10px; margin: 15px 0; border-right: 6px solid #1e3c72; font-weight: bold; }
.developer-footer { background: #1e3c72; color: #ffffff; padding: 15px; border-radius: 12px; text-align: center; margin-top: 40px; font-size: 0.85rem; }
.small-note { font-size: 0.85rem; color: #444; }
</style>
""", unsafe_allow_html=True)

DB_FILE = "biet_chabab.db"

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def table_exists(conn, name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?;", (name,)).fetchone() is not None

def columns_of(conn, table: str):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table});").fetchall()]

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rooms_config (
        wing TEXT NOT NULL,
        room TEXT NOT NULL,
        beds_count INTEGER NOT NULL CHECK (beds_count > 0),
        PRIMARY KEY (wing, room)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        role TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        birth_date DATE,
        birth_place TEXT,
        address TEXT,
        id_type TEXT,
        id_number TEXT NOT NULL,
        nationality TEXT,
        visa_date TEXT,
        wing TEXT NOT NULL,
        room TEXT NOT NULL,
        bed TEXT NOT NULL,
        check_in DATE NOT NULL,
        check_out DATE NOT NULL,
        legal_status TEXT,
        status TEXT NOT NULL DEFAULT 'IN' CHECK (status IN ('IN','OUT')),
        out_at TIMESTAMP
    );
    """)

    conn.commit()

    # Seed users (مرة وحدة)
    if cur.execute("SELECT COUNT(*) FROM users;").fetchone()[0] == 0:
        cur.execute("INSERT INTO users(role, password_hash) VALUES (?,?)", ("مدير", sha256("1234")))
        cur.execute("INSERT INTO users(role, password_hash) VALUES (?,?)", ("عون استقبال", sha256("5678")))
        conn.commit()

    # Seed rooms (مرة وحدة)
    if cur.execute("SELECT COUNT(*) FROM rooms_config;").fetchone()[0] == 0:
        default_rooms = [
            ("جناح ذكور", "غرفة 01", 6), ("جناح ذكور", "غرفة 02", 6), ("جناح ذكور", "غرفة 03", 6),
            ("جناح ذكور", "غرفة 04", 6), ("جناح ذكور", "غرفة 05", 6),
            ("جناح ذكور", "مرقد ذكور 01", 3), ("جناح ذكور", "مرقد ذكور 02", 4),
            ("جناح إناث", "غرفة 06", 2), ("جناح إناث", "غرفة 07", 6), ("جناح إناث", "غرفة 08", 6),
            ("جناح إناث", "غرفة 09", 6), ("جناح إناث", "مرقد إناث 01", 3), ("جناح إناث", "مرقد إناث 02", 4)
        ]
        cur.executemany("INSERT INTO rooms_config(wing, room, beds_count) VALUES (?,?,?)", default_rooms)
        conn.commit()

    # Migration آمن للجدول القديم (إذا كان موجود بأعمدة عربية)
    # الفكرة: إذا كان عندك جدول bookings لكن أعمدته عربية، كنحوّلو للهيكلة الجديدة.
    try:
        cols = columns_of(conn, "bookings")
        arabic_candidates = {"الاسم_واللقب", "تاريخ_الازدياد", "مكان_الازدياد", "العنوان", "نوع_البطاقة", "رقم_البطاقة", "الجناح", "الغرفة", "السرير", "تاريخ_الدخول", "تاريخ_الخروج"}
        if any(c in arabic_candidates for c in cols):
            # rename old
            if not table_exists(conn, "bookings_old"):
                cur.execute("ALTER TABLE bookings RENAME TO bookings_old;")
                # recreate new
                cur.execute("""
                CREATE TABLE bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    birth_date DATE,
                    birth_place TEXT,
                    address TEXT,
                    id_type TEXT,
                    id_number TEXT NOT NULL,
                    nationality TEXT,
                    visa_date TEXT,
                    wing TEXT NOT NULL,
                    room TEXT NOT NULL,
                    bed TEXT NOT NULL,
                    check_in DATE NOT NULL,
                    check_out DATE NOT NULL,
                    legal_status TEXT,
                    status TEXT NOT NULL DEFAULT 'IN' CHECK (status IN ('IN','OUT')),
                    out_at TIMESTAMP
                );
                """)
                # move data (إذا كانت الأعمدة موجودة)
                old_cols = columns_of(conn, "bookings_old")
                mapping = {
                    "full_name": "الاسم_واللقب",
                    "birth_date": "تاريخ_الازدياد",
                    "birth_place": "مكان_الازدياد",
                    "address": "العنوان",
                    "id_type": "نوع_البطاقة",
                    "id_number": "رقم_البطاقة",
                    "nationality": "الجنسية",
                    "visa_date": "تاريخ_الفيزا",
                    "wing": "الجناح",
                    "room": "الغرفة",
                    "bed": "السرير",
                    "check_in": "تاريخ_الدخول",
                    "check_out": "تاريخ_الخروج",
                    "legal_status": "الحالة_القانونية",
                }
                select_parts = []
                insert_cols = []
                for new_c, old_c in mapping.items():
                    if old_c in old_cols:
                        insert_cols.append(new_c)
                        select_parts.append(old_c)
                sql = f"INSERT INTO bookings ({','.join(insert_cols)}) SELECT {','.join(select_parts)} FROM bookings_old;"
                cur.execute(sql)
                cur.execute("DROP TABLE bookings_old;")
                conn.commit()
                st.toast("✅ تم تحويل قاعدة البيانات القديمة بنجاح", icon="🎉")
    except Exception:
        pass

    conn.close()

def load_wings():
    with get_conn() as conn:
        df = pd.read_sql("SELECT * FROM rooms_config ORDER BY wing, room", conn)
    wings = {}
    if df.empty:
        return wings
    for wing in df['wing'].unique():
        sub = df[df['wing'] == wing]
        wings[wing] = dict(zip(sub['room'], sub['beds_count']))
    return wings

def load_bookings():
    with get_conn() as conn:
        return pd.read_sql("SELECT * FROM bookings ORDER BY id DESC", conn)

def current_occupied_df(df_bookings: pd.DataFrame, today: date):
    if df_bookings.empty:
        return df_bookings.iloc[0:0]
    d = df_bookings.copy()
    d["check_in_d"] = pd.to_datetime(d["check_in"], errors="coerce").dt.date
    d["check_out_d"] = pd.to_datetime(d["check_out"], errors="coerce").dt.date
    # يعتبر “حالي” إذا status IN و اليوم داخل المدة
            # تكملة الجزء المقطوع وإغلاق الدالة
        d = d[d["status"].fillna("IN") == "IN"]
        return d
    return pd.DataFrame()

# --- 4. تشغيل النظام والواجهة الرسومية ---
init_db()
wings_data = load_wings()
df_all = load_bookings()

# التحقق من الدخول
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<div class="main-title">🔐 تسجيل الدخول للنظام</div>', unsafe_allow_html=True)
    role = st.selectbox("الصلاحية", ["مدير", "عون استقبال"])
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول آمن", use_container_width=True):
        with get_conn() as conn:
            user = conn.execute("SELECT password_hash FROM users WHERE role=?", (role,)).fetchone()
            if user and sha256(pwd) == user[0]:
                st.session_state.authenticated = True
                st.session_state.role = role
                st.rerun()
            else:
                st.error("❌ كلمة المرور خاطئة")
    st.stop()

# القائمة الجانبية
st.sidebar.title(f"👤 {st.session_state.role}")
if st.sidebar.button("تسجيل الخروج"):
    st.session_state.authenticated = False
    st.rerun()

# التبويبات
tabs = st.tabs(["🏠 الرئيسية", "➕ حجز جديد", "📂 الأرشيف"])

with tabs[0]:
    st.subheader("📊 حالة الغرف والأسرة")
    with get_conn() as conn:
        occ_beds = pd.read_sql("SELECT wing, room, bed FROM bookings WHERE status='IN'", conn)
    
    for wing, rooms in wings_data.items():
        st.markdown(f'<div class="wing-header">{wing}</div>', unsafe_allow_html=True)
        for room, count in rooms.items():
            cols = st.columns([1, 5])
            cols[0].write(f"**{room}**")
            html = ""
            for b in range(1, count + 1):
                b_name = f"سرير {b}"
                is_occ = not occ_beds[(occ_beds['wing'] == wing) & (occ_beds['room'] == room) & (occ_beds['bed'] == b_name)].empty
                status = "occupied" if is_occ else "free"
                html += f'<div class="bed-box {status}">{b}</div>'
            cols[1].markdown(html, unsafe_allow_html=True)

# تذييل المطور
st.markdown(f'<div class="developer-footer">برمجة وتطوير: ®ridha_merzoug® - {date.today().year}</div>', unsafe_allow_html=True)

