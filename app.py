import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import date, timedelta
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import io

# ────────────────────────────────────────────────
#                1. إعداد الصفحة والـ CSS الملكي
# ────────────────────────────────────────────────
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { 
        background: linear-gradient(90deg, #1e3c72, #2a5298); 
        color: white; padding: 20px; border-radius: 15px; 
        text-align: center; margin-bottom: 25px; font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .section-box {
        background: #ffffff; padding: 20px; border-radius: 12px; 
        border-right: 6px solid #1e3c72; margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .bed-box { 
        display: inline-block; width: 45px; height: 40px; margin: 5px; 
        border-radius: 8px; text-align: center; line-height: 40px; 
        color: white; font-weight: bold; font-size: 0.9rem;
    }
    .free { background-color: #28a745; border-bottom: 3px solid #1e7e34; }
    .occupied { background-color: #dc3545; border-bottom: 3px solid #a71d2a; }
    .success-box { background: #d4edda; color: #155724; padding: 15px; border-radius: 10px; text-align: center; margin: 10px 0; }
    .developer-footer { 
        background: #1e3c72; color: white; padding: 10px; 
        border-radius: 10px; text-align: center; margin-top: 50px; 
        font-size: 0.8rem; border: 1px solid #00d4ff;
    }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               2. إدارة قاعدة البيانات
# ────────────────────────────────────────────────
DB_FILE = 'youth_hostel_final_v1.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS current_guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, birth_date TEXT, birth_place TEXT, address TEXT,
            id_type TEXT, id_card TEXT, nationality TEXT, entry_date TEXT,
            wing TEXT, room TEXT, bed TEXT, check_in TEXT, check_in_time TEXT,
            check_out TEXT, status TEXT DEFAULT 'مقيم', 
            job TEXT, phone TEXT, notes TEXT, nights INTEGER, companions TEXT, minor_auth TEXT
        )''')
        conn.commit()

init_db()

# ────────────────────────────────────────────────
#               3. الدوال المساعدة (الذكاء البرمجي)
# ────────────────────────────────────────────────
def calculate_age(birth_date):
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_old_guest(id_num):
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT name, birth_date, birth_place, address, job, phone, nationality FROM current_guests WHERE id_card=? ORDER BY id DESC LIMIT 1", (id_num,)).fetchone()

def get_vacant_beds(wing, room):
    all_beds = [str(i) for i in range(1, 7)] 
    with sqlite3.connect(DB_FILE) as conn:
        occupied = conn.execute("SELECT bed FROM current_guests WHERE wing=? AND room=? AND status='مقيم'", (wing, room)).fetchall()
        occupied_list = [str(row[0]) for row in occupied]
    return [b for b in all_beds if b not in occupied_list]

# ────────────────────────────────────────────────
#               4. نظام الدخول الصارم
# ────────────────────────────────────────────────
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div class="main-title">🔐 تسجيل الدخول للنظام</div>', unsafe_allow_html=True)
    role = st.selectbox("👤 اختر الصفة:", ["مدير", "عون استقبال"])
    pwd = st.text_input("🔑 كلمة السر:", type="password")
    if st.button("دخول آمن", use_container_width=True):
        if (role == "مدير" and pwd == "1234") or (role == "عون استقبال" and pwd == "5678"):
            st.session_state.auth = True; st.session_state.role = role; st.rerun()
        else: st.error("❌ كلمة السر خاطئة")
    st.stop()

# ────────────────────────────────────────────────
#               5. الواجهة الرئيسية والتبويبات
# ────────────────────────────────────────────────
st.markdown('<div class="main-title">🏢 إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)

# تعريف التبويبات (هنا نحل مشكلة NameError)
tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجلات"])

# --- التبويب الأول: حجز جديد (تنسيق رضا المطور) ---
with tabs[0]:
    if st.session_state.get('booking_success'):
        st.markdown('<div class="success-box"><h3>🎉 تم تسجيل الحجز بنجاح!</h3></div>', unsafe_allow_html=True)
        if st.button("➕ تسجيل نزيل جديد", type="primary", use_container_width=True):
            st.session_state.booking_success = False; st.rerun()
    else:
        st.markdown('<div class="section-box"><h4>🔍 تسجيل حجز جديد</h4></div>', unsafe_allow_html=True)
        search_id = st.text_input("🪪 ابحث برقم الوثيقة لنزيل سابق:", placeholder="اكتب الرقم لملء البيانات...")
        old_guest = get_old_guest(search_id) if search_id else None

        with st.form("professional_booking_form"):
            st.markdown("##### 👤 معلومات النزيل")
            name = st.text_input("الاسم واللقب الكامل", value=old_guest[0] if old_guest else "")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                bday = st.date_input("📅 تاريخ الميلاد", value=pd.to_datetime(old_guest[1]) if old_guest else date(2000,1,1))
            with col_b2:
                bplace = st.text_input("📍 مكان الازدياد", value=old_guest[2] if old_guest else "")

            col_n1, col_n2 = st.columns(2)
            with col_n1:
                nations = ["جزائرية", "تونسية", "مغربية", "ليبية", "موريتانية", "فرنسية", "أخرى"]
                nationality = st.selectbox("🌍 الجنسية", nations, index=0 if not old_guest else nations.index(old_guest[6]) if old_guest[6] in nations else 0)
            with col_n2:
                id_type = st.selectbox("📄 نوع الوثيقة", ["بطاقة تعريف (عادية)", "بطاقة تعريف (بيومترية)", "رخصة سياقة (عادية)", "رخصة سياقة (بيومترية)", "جواز سفر", "اخرى"])

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                id_num = st.text_input("🔢 رقم الوثيقة", value=search_id if search_id else "")
                job = st.text_input("💼 المهنة", value=old_guest[4] if old_guest else "")
            with col_c2:
                phone = st.text_input("📞 رقم الهاتف", value=old_guest[5] if old_guest else "")
                addr = st.text_input("🏠 العنوان الكامل", value=old_guest[3] if old_guest else "")

            # منطق الأجانب والقاصرين
            age = calculate_age(bday)
            is_foreigner = nationality != "جزائرية"
            entry_date = None
            minor_auth = ""
            
            if is_foreigner or age < 18:
                col_spec1, col_spec2 = st.columns(2)
                with col_spec1:
                    if is_foreigner:
                        entry_date = st.date_input("🛂 تاريخ الدخول للجزائر (الفيزا)", date.today())
                with col_spec2:
                    if age < 18:
                        minor_auth = st.selectbox("📝 نوع تصريح القاصر:", ["تصريح أبوي", "حضور الولي", "أمر بمهمة", "أخرى"])

            st.markdown("---")
            st.markdown("##### 👨‍👩‍👧‍👦 المرافقين وتفاصيل السكن")
            companions = st.text_area("الأسماء المرافقة (إن وجدت)")

            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                wing = st.selectbox("🏢 الجناح", ["جناح ذكور 👨", "جناح إناث 👩"])
            with col_res2:
                room = st.selectbox("🚪 الغرفة", [f"غرفة {i:02d}" for i in range(1, 11)])
            with col_res3:
                nights = st.number_input("🌙 عدد الليالي", min_value=1, value=1)

            vacant_beds = get_vacant_beds(wing, room)
            if vacant_beds:
                bed = st.radio("🛏️ السرير الشاغر المتاح:", vacant_beds, horizontal=True)
                current_time = datetime.datetime.now().strftime("%H:%M")
                st.caption(f"🕒 توقيت التسجيل: {current_time}")
                
                if st.form_submit_button("💾 تأكيد وحفظ الحجز", type="primary", use_container_width=True):
                    out_date = date.today() + timedelta(days=nights)
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("""INSERT INTO current_guests 
                        (name, birth_date, birth_place, address, id_type, id_card, nationality, entry_date, wing, room, bed, check_in, check_in_time, check_out, job, phone, companions, minor_auth, nights) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (name, str(bday), bplace, addr, id_type, id_num, nationality, str(entry_date) if entry_date else None, wing, room, bed, str(date.today()), current_time, str(out_date), job, phone, companions, minor_auth, nights))
                    st.session_state.booking_success = True; st.rerun()
            else:
                st.error("⚠️ الغرفة ممتلئة تماماً!"); st.form_submit_button("💾 تأكيد وحفظ الحجز", disabled=True)

# --- التبويب الثاني: حالة الغرف (تنسيق بصري) ---
with tabs[1]:
    st.markdown('<div class="section-box"><h4>📊 خريطة توزيع الأسرة</h4></div>', unsafe_allow_html=True)
    with sqlite3.connect(DB_FILE) as conn:
        booked = pd.read_sql_query("SELECT wing, room, bed, name FROM current_guests WHERE status='مقيم'", conn)
    
    for w in ["جناح ذكور 👨", "جناح إناث 👩"]:
        st.subheader(w)
        cols = st.columns(5)
        for i in range(1, 11):
            r_name = f"غرفة {i:02d}"
            with cols[(i-1)%5]:
                st.write(f"**{r_name}**")
                for b in range(1, 7):
                    is_occ = booked[(booked['wing']==w) & (booked['room']==r_name) & (booked['bed']==str(b))]
                    color = "occupied" if not is_occ.empty else "free"
                    st.markdown(f'<div class="bed-box {color}" title="{is_occ["name"].iloc[0] if not is_occ.empty else "شاغر"}">{b}</div>', unsafe_allow_html=True)

# --- التبويب الثالث: السجلات ---
with tabs[2]:
    st.info("سيتم ربط هذا التبويب لاحقاً بجداول الإحصائيات الشاملة.")

st.markdown('<div class="developer-footer">Developer ®ridha_merzoug® [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
