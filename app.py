import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3

# ==================== إعداد الصفحة والتنسيق ====================
st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; font-size: 1.3rem; font-weight: bold; }
    .stat-card { background: #ffffff; padding: 20px; border-radius: 15px; border-bottom: 5px solid #1e3c72; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: 0.3s; }
    .stat-card:hover { transform: translateY(-5px); }
    .icon-style { font-size: 2rem; margin-bottom: 10px; display: block; }
    .bed-box { display: inline-block; width: 40px; height: 35px; margin: 3px; border-radius: 5px; text-align: center; line-height: 35px; color: white; font-size: 0.8rem; font-weight: bold; }
    .free { background-color: #28a745; }
    .occupied { background-color: #dc3545; }
    .wing-header { background-color: #f1f3f5; padding: 10px; border-radius: 8px; margin-top: 15px; border-right: 5px solid #1e3c72; font-weight: bold; }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 10px; border-radius: 10px; text-align: center; margin-top: 40px; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# ==================== قاعدة البيانات ====================
DB_FILE = "biet_chabab.db"

def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        الاسم_واللقب TEXT,
        تاريخ_الازدياد DATE,
        مكان_الازدياد TEXT,
        العنوان TEXT,
        نوع_البطاقة TEXT,
        رقم_البطاقة TEXT,
        الجنسية TEXT,
        تاريخ_الفيزا TEXT,
        الجناح TEXT,
        الغرفة TEXT,
        السرير TEXT,
        تاريخ_الدخول DATE,
        تاريخ_الخروج DATE,
        الحالة_القانونية TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS rooms_config (
        wing TEXT,
        room TEXT,
        beds_count INTEGER,
        PRIMARY KEY (wing, room)
    )''')
    conn.commit()

    if conn.execute("SELECT COUNT(*) FROM rooms_config").fetchone()[0] == 0:
        default_rooms = [
            ("جناح ذكور", "غرفة 01", 6), ("جناح ذكور", "غرفة 02", 6), ("جناح ذكور", "غرفة 03", 6),
            ("جناح ذكور", "غرفة 04", 6), ("جناح ذكور", "غرفة 05", 6),
            ("جناح ذكور", "مرقد ذكور 01", 3), ("جناح ذكور", "مرقد ذكور 02", 4),
            ("جناح إناث", "غرفة 06", 2), ("جناح إناث", "غرفة 07", 6), ("جناح إناث", "غرفة 08", 6),
            ("جناح إناث", "غرفة 09", 6), ("جناح إناث", "مرقد إناث 01", 3), ("جناح إناث", "مرقد إناث 02", 4)
        ]
        conn.executemany("INSERT INTO rooms_config (wing, room, beds_count) VALUES (?,?,?)", default_rooms)
        conn.commit()
    conn.close()

init_db()

def load_wings_config():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM rooms_config", conn)
    conn.close()
    wings_dict = {}
    for wing in df['wing'].unique():
        sub = df[df['wing'] == wing]
        wings_dict[wing] = dict(zip(sub['room'], sub['beds_count']))
    return wings_dict

wings = load_wings_config()

def load_bookings():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    conn.close()
    return df

# ==================== الجلسة ====================
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'review_mode' not in st.session_state: st.session_state.review_mode = False
if 'temp_data' not in st.session_state: st.session_state.temp_data = {}

if not st.session_state.authenticated:
    st.markdown('<div class="main-title">🏨 نظام إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)
    with st.container():
        role = st.selectbox("🔑 اختر الصفة", ["مدير", "عون استقبال"])
        pwd = st.text_input("🔒 كلمة السر", type="password")
        if st.button("🚀 تسجيل الدخول", use_container_width=True):
            if (role == "مدير" and pwd == "1234") or (role == "عون استقبال" and pwd == "5678"):
                st.session_state.authenticated = True
                st.session_state.user_role = role
                st.rerun()
            else:
                st.error("❌ عذراً، كلمة السر غير صحيحة")
    st.stop()

# ==================== التبويبات ====================
tabs = st.tabs([
    "➕ حجز جديد", 
    "🛌 حالة الغرف", 
    "📋 السجل العام", 
    "📄 تصدير Word", 
    "👥 الأفواج", 
    "💰 الحسابات", 
    "⚙️ الإعدادات"
])

today = date.today()

# ==================== 1. حجز جديد ====================
with tabs[0]:
    # حساب الإشغال بأمان (محمي من KeyError و DataFrame فارغ) ← التعديل الوحيد هنا
    df_all = load_bookings()
    
    male_occupied = 0
    female_occupied = 0
    
    if not df_all.empty and 'الجناح' in df_all.columns and 'تاريخ_الدخول' in df_all.columns and 'تاريخ_الخروج' in df_all.columns:
        occupied_today = df_all[
            (pd.to_datetime(df_all['تاريخ_الدخول'], errors='coerce').dt.date <= today) & 
            (pd.to_datetime(df_all['تاريخ_الخروج'], errors='coerce').dt.date > today)
        ]
        if not occupied_today.empty:
            male_occupied = len(occupied_today[occupied_today['الجناح'] == "جناح ذكور"])
            female_occupied = len(occupied_today[occupied_today['الجناح'] == "جناح إناث"])
    
    free_male = sum(wings.get("جناح ذكور", {}).values()) - male_occupied
    free_female = sum(wings.get("جناح إناث", {}).values()) - female_occupied

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="stat-card"><span class="icon-style">👨</span>شاغر (ذكور)<br><h2>{free_male}</h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-card"><span class="icon-style">👩</span>شاغر (إناث)<br><h2>{free_female}</h2></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-card"><span class="icon-style">📅</span>تاريخ اليوم<br><h2>{today}</h2></div>', unsafe_allow_html=True)
    
    st.divider()
    
    if not st.session_state.review_mode:
        with st.form("main_form"):
            st.markdown("### 📝 بيانات النزيل الشخصية")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("👤 الاسم واللقب *")
                b_date = st.date_input("🎂 تاريخ الازدياد", value=date(2000, 1, 1))
                b_place = st.text_input("📍 مكان الازدياد")
                address = st.text_input("🏠 العنوان الكامل")
                nationality = st.selectbox("🌍 الجنسية", ["جزائرية", "أخرى"])
            
            with col2:
                id_type = st.selectbox("🪪 نوع بطاقة التعريف", ["بطاقة تعريف عادية", "بطاقة بيومترية", "رخصة سياقة عادية", "رخصة سياقة بيومترية", "جواز سفر"])
                id_val = st.text_input("🔢 رقم البطاقة *")
                wing = st.selectbox("🏢 الجناح", list(wings.keys()))
                room_list = list(wings[wing].keys()) if wing in wings else []
                room = st.selectbox("🚪 الغرفة", room_list)
                bed_list = [f"سرير {i+1}" for i in range(wings[wing][room])] if room and wing in wings else []
                bed = st.selectbox("🛏️ السرير", bed_list)
                arr = st.date_input("📥 تاريخ الدخول", value=today)
                dep = st.date_input("📤 تاريخ الخروج", value=today + timedelta(days=1))
                legal_status = st.text_input("⚖️ الحالة القانونية")

            if st.form_submit_button("🔍 مراجعة الحجز قبل التأكيد", use_container_width=True):
                if not name or not id_val or not bed:
                    st.error("⚠️ يرجى ملء الخانات الإجبارية (*) أولاً")
                else:
                    st.session_state.temp_data = {
                        "الاسم_واللقب": name, "تاريخ_الازدياد": b_date, "مكان_الازدياد": b_place,
                        "العنوان": address, "نوع_البطاقة": id_type, "رقم_البطاقة": id_val,
                        "الجنسية": nationality, "تاريخ_الفيزا": "", "الجناح": wing,
                        "الغرفة": room, "السرير": bed, "تاريخ_الدخول": arr,
                        "تاريخ_الخروج": dep, "الحالة_القانونية": legal_status
                    }
                    st.session_state.review_mode = True
                    st.rerun()
    else:
        st.success("✅ البيانات جاهزة للمراجعة")
        st.json(st.session_state.temp_data)
        if st.button("💾 تأكيد وحفظ النهائي", use_container_width=True):
            conn = get_conn()
            overlap = conn.execute("""
                SELECT COUNT(*) FROM bookings 
                WHERE الجناح=? AND الغرفة=? AND السرير=? 
                AND تاريخ_الدخول < ? AND تاريخ_الخروج > ?
            """, (st.session_state.temp_data["الجناح"], st.session_state.temp_data["الغرفة"],
                  st.session_state.temp_data["السرير"], st.session_state.temp_data["تاريخ_الخروج"],
                  st.session_state.temp_data["تاريخ_الدخول"])).fetchone()[0]
            
            if overlap > 0:
                st.error("❌ السرير محجوز في هذه الفترة!")
            else:
                pd.DataFrame([st.session_state.temp_data]).to_sql("bookings", conn, if_exists="append", index=False)
                st.success(f"✅ تم حفظ الحجز بنجاح! سرير {st.session_state.temp_data['السرير']}")
                st.session_state.review_mode = False
                st.rerun()
            conn.close()

# ==================== 2. حالة الغرف ====================
with tabs[1]:
    st.subheader("🛌 توزيع الأسرة وحالة الإشغال")
    st.info("الأخضر 🟢 شاغر | الأحمر 🔴 محجوز")
    df = load_bookings()
    for wing, rooms in wings.items():
        st.markdown(f'<div class="wing-header">{wing}</div>', unsafe_allow_html=True)
        for room, count in rooms.items():
            cols = st.columns([1, 5])
            cols[0].write(f"**{room}**")
            html = ""
            for b in range(1, count + 1):
                b_name = f"سرير {b}"
                is_occ = not df[
                    (df['الجناح'] == wing) & (df['الغرفة'] == room) & 
                    (df['السرير'] == b_name) &
                    (pd.to_datetime(df['تاريخ_الدخول'], errors='coerce').dt.date <= today) &
                    (pd.to_datetime(df['تاريخ_الخروج'], errors='coerce').dt.date > today)
                ].empty if not df.empty else False
                status = "occupied" if is_occ else "free"
                html += f'<div class="bed-box {status}">{b}</div>'
            cols[1].markdown(html, unsafe_allow_html=True)

# ==================== باقي التبويبات (بدون أي تغيير) ====================
with tabs[2]:
    st.subheader("📋 السجل العام")
    df = load_bookings()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("لا توجد حجوزات بعد")

with tabs[3]:
    st.subheader("📄 تصدير التقارير إلى Word")
    st.button("📝 إنشاء ملف Word للنزيل الحالي")
    st.info("سيتم تفعيل التصدير الكامل قريباً")

with tabs[4]:
    st.subheader("👥 إدارة الأفواج والوفود")
    st.button("➕ إضافة فوج جديد")

with tabs[5]:
    st.subheader("💰 الإدارة المالية والحسابات")
    st.metric("إجمالي مداخيل اليوم", "4500 د.ج", "+150")

with tabs[6]:
    st.subheader("⚙️ إعدادات النظام")
    st.write("🔧 تحديث كلمات السر وسعة الغرف")

# ==================== التذييل ====================
st.markdown(f'''
    <div class="developer-footer">
        🛠️ تم التطوير بواسطة: <b>®ridha_merzoug®</b> [رضا مرزوق] <br>
        📍 بيت شباب محمدي يوسف قالمة - نسخة 2026 المحسنة ✨
    </div>
    ''', unsafe_allow_html=True)
