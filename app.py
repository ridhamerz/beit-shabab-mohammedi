import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import os

# ====================== إعدادات الواجهة (أوف لاين) ======================
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    * { 
        font-family: 'Tahoma', 'Arial', sans-serif; 
        direction: RTL; 
        text-align: right; 
    }
    
    .main-title { 
        background: linear-gradient(90deg, #1e3c72, #2a5298); 
        color: white; padding: 20px; border-radius: 15px; 
        text-align: center; margin-bottom: 25px; 
        font-size: 1.5rem; font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    .bed-box { 
        display: inline-block; width: 42px; height: 38px; margin: 4px; 
        border-radius: 6px; text-align: center; line-height: 38px; 
        color: white; font-size: 0.85rem; font-weight: bold; 
    }
    .free { background-color: #28a745; border-bottom: 3px solid #1e7e34; }
    .occupied { background-color: #dc3545; border-bottom: 3px solid #a71d2a; }
    
    .stat-card { 
        background: white; padding: 20px; border-radius: 12px; 
        border-right: 6px solid #1e3c72; text-align: center; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); 
    }
    
    .developer-footer { 
        background: #1e3c72; color: #ffffff; padding: 8px; 
        border-radius: 10px; text-align: center; margin-top: 50px; 
        font-size: 0.75rem; border: 1px solid #00d4ff;
    }
    </style>
    """, unsafe_allow_html=True)

# ====================== قاعدة البيانات SQLite ======================
DB_FILE = 'youth_hostel.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS current_guests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    birth TEXT,
                    address TEXT,
                    id_card TEXT UNIQUE,
                    wing TEXT,
                    room TEXT,
                    bed TEXT,
                    check_in TEXT,
                    check_out TEXT,
                    status TEXT DEFAULT 'مقيم'
                 )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS archive (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    birth TEXT,
                    address TEXT,
                    id_card TEXT,
                    wing TEXT,
                    room TEXT,
                    bed TEXT,
                    check_in TEXT,
                    check_out TEXT,
                    status TEXT
                 )''')
    
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

def is_bed_occupied(wing, room, bed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""SELECT id FROM current_guests 
                 WHERE wing=? AND room=? AND bed=? AND status='مقيم'""", 
              (wing, room, bed))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def add_guest(name, birth, address, id_card, wing, room, bed, check_in, check_out):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""INSERT INTO current_guests 
                 (name, birth, address, id_card, wing, room, bed, check_in, check_out)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (name, birth, address, id_card, wing, room, bed, check_in, check_out))
    conn.commit()
    conn.close()

def evacuate_guest(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # نقل البيانات للأرشيف
    c.execute("""INSERT INTO archive 
                 (name, birth, address, id_card, wing, room, bed, check_in, check_out, status)
                 SELECT name, birth, address, id_card, wing, room, bed, check_in, check_out, 'غادر'
                 FROM current_guests WHERE name=?""", (name,))
    
    # حذف من الحاليين
    c.execute("DELETE FROM current_guests WHERE name=?", (name,))
    
    conn.commit()
    conn.close()

# ====================== بدء البرنامج ======================
init_db()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'passwords' not in st.session_state:
    st.session_state.passwords = {"مدير": "1234", "عون استقبال": "5678"}

wings = {
    "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
    "جناح إناث": {"غرفة 06": 2, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد إناث 01": 3, "مرقد إناث 02": 4}
}

# ====================== تسجيل الدخول ======================
if not st.session_state.authenticated:
    st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
    st.subheader("🔐 الدخول للنظام")
    role = st.selectbox("الصفة", ["مدير", "عون استقبال"])
    pwd = st.text_input("كلمة السر", type="password")
    if st.button("دخول آمن", use_container_width=True):
        if pwd == st.session_state.passwords.get(role):
            st.session_state.authenticated = True
            st.session_state.user_role = role
            st.rerun()
        else:
            st.error("كلمة السر خاطئة!")
    st.stop()

# ====================== الواجهة الرئيسية ======================
st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
st.sidebar.write(f"👤 المستخدم: **{st.session_state.user_role}**")
if st.sidebar.button("تسجيل الخروج"):
    st.session_state.authenticated = False
    st.rerun()

# التبويبات
if st.session_state.user_role == "مدير":
    tabs = st.tabs(["➕ حجز جديد", "📊 عدد الغرف", "📋 السجل والبحث", "📂 الأرشيف", "📈 الإحصائيات", "⚙️ الإعدادات"])
else:
    tabs = st.tabs(["➕ حجز جديد", "📊 عدد الغرف", "📋 السجل والبحث"])

# ====================== تبويب الحجز الجديد ======================
with tabs[0]:
    st.subheader("📝 تسجيل نزيل جديد")
    with st.form("booking_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم واللقب *")
            birth = st.text_input("تاريخ ومكان الازدياد")
            addr = st.text_input("العنوان الكامل")
        with c2:
            id_card = st.text_input("رقم بطاقة التعريف *")
            wing = st.selectbox("الجناح", list(wings.keys()))
            room = st.selectbox("الغرفة", list(wings[wing].keys()))
            bed = st.selectbox("رقم السرير", [f"سرير {i+1}" for i in range(wings[wing][room])])
            
            check_in = st.date_input("تاريخ الدخول", value=date.today())
            check_out = st.date_input("تاريخ الخروج", value=date.today() + timedelta(days=1))
        
        if st.form_submit_button("✅ تأكيد وحفظ"):
            if not name or not id_card:
                st.error("يرجى ملء الاسم ورقم البطاقة")
            elif check_out <= check_in:
                st.error("تاريخ الخروج يجب أن يكون بعد تاريخ الدخول")
            elif is_bed_occupied(wing, room, bed):
                st.error(f"❌ السرير {bed} في {room} محجوز حالياً!")
            else:
                add_guest(name, birth, addr, id_card, wing, room, bed, str(check_in), str(check_out))
                st.success(f"✅ تم تسجيل النزيل {name} بنجاح")
                st.rerun()

# ====================== تبويب خريطة الغرف ======================
with tabs[1]:
    st.subheader("📊 حالة الأجنحة والأسرة")
    current_df = get_current_guests()
    
    for wing_name, rooms in wings.items():
        st.markdown(f'<div style="background:#f8f9fa; padding:10px; border-radius:10px; border-right:5px solid #1e3c72; margin-top:15px;"><b>{wing_name}</b></div>', unsafe_allow_html=True)
        for room_name, bed_count in rooms.items():
            cols = st.columns([1, 6])
            cols[0].write(f"**{room_name}**")
            html = ""
            for b in range(1, bed_count + 1):
                b_name = f"سرير {b}"
                is_occ = not current_df[
                    (current_df['wing'] == wing_name) & 
                    (current_df['room'] == room_name) & 
                    (current_df['bed'] == b_name)
                ].empty
                status = "occupied" if is_occ else "free"
                html += f'<div class="bed-box {status}">{b}</div>'
            cols[1].markdown(html, unsafe_allow_html=True)

# ====================== تبويب السجل والبحث ======================
with tabs[2]:
    st.subheader("🔍 سجل المقيمين الحاليين")
    search = st.text_input("ابحث بالاسم أو رقم البطاقة...")
    df = get_current_guests()
    
    if search:
        df = df[df['name'].str.contains(search) | df['id_card'].str.contains(search)]
    
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🚪 إنهاء إقامة نزيل")
    if not df.empty:
        out_name = st.selectbox("اختر النزيل المغادر", df['name'].tolist())
        if st.button("إخلاء السرير ونقل للأرشيف"):
            evacuate_guest(out_name)
            st.success(f"تم إخلاء سبيل {out_name} وتحديث الأرشيف.")
            st.rerun()

# ====================== تبويبات المدير فقط ======================
if st.session_state.user_role == "مدير":
    with tabs[3]:
        st.subheader("📂 الأرشيف التاريخي")
        st.dataframe(get_archive(), use_container_width=True)

    with tabs[4]:
        st.subheader("📈 تقارير الإحصائيات")
        current = get_current_guests()
        archive = get_archive()
        total_beds = sum(sum(r.values()) for r in wings.values())
        occupancy = (len(current) / total_beds * 100) if total_beds > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="stat-card"><h3>{len(current)}</h3><p>نزلاء مقيمين</p></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card"><h3>{len(archive)}</h3><p>إجمالي الأرشيف</p></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card"><h3>{occupancy:.1f}%</h3><p>نسبة الإشغال</p></div>', unsafe_allow_html=True)

    with tabs[5]:
        st.subheader("⚙️ إعدادات النظام")
        target = st.selectbox("تغيير كلمة سر", ["مدير", "عون استقبال"])
        new_pass = st.text_input("كلمة السر الجديدة", type="password")
        if st.button("حفظ"):
            st.session_state.passwords[target] = new_pass
            st.success("تم تحديث كلمة السر بنجاح.")

# ====================== تذييل ======================
st.markdown("""
    <div class="developer-footer">
        Developer <span style="color:#00d4ff; font-weight:bold;">®ridha_merzoug®</span> [رضا مرزوق] - 2026
    </div>
    """, unsafe_allow_html=True)
