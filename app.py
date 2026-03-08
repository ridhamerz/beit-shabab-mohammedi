import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import io

# ────────────────────────────────────────────────
#                إعداد الصفحة والـ CSS
# ────────────────────────────────────────────────
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    * { font-family: 'Tahoma', 'Arial', sans-serif; direction: RTL; text-align: right; }
    .main-title { 
        background: linear-gradient(90deg, #1e3c72, #2a5298); 
        color: white; padding: 20px; border-radius: 15px; 
        text-align: center; margin-bottom: 25px; 
        font-size: 1.6rem; font-weight: bold;
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
        font-size: 0.8rem; border: 1px solid #00d4ff;
    }
    .section-box {
        background: #f8f9fa; padding: 1rem; border-radius: 8px; 
        margin-bottom: 1.2rem; border-right: 4px solid;
    }
    .minor-box {
        background: #fff3cd !important; border-color: #ffc107 !important;
        padding: 1rem; border-radius: 8px; margin: 1rem 0;
    }
    .success-box {
        background: #d4edda; color: #155724; padding: 1.5rem; 
        border-radius: 10px; border: 1px solid #c3e6cb; 
        margin: 1.5rem 0; text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               إعداد قاعدة البيانات
# ────────────────────────────────────────────────
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

init_db()

# ────────────────────────────────────────────────
#               دوال مساعدة
# ────────────────────────────────────────────────
def is_bed_occupied(wing, room, bed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM current_guests WHERE wing=? AND room=? AND bed=? AND status='مقيم'", 
              (wing, room, bed))
    result = c.fetchone()
    conn.close()
    return result is not None

def add_guest(name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, guardian_name=None, guardian_permission=None):
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

# ────────────────────────────────────────────────
#               الجلسة والأجنحة
# ────────────────────────────────────────────────
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

# العنوان الرئيسي
st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
st.sidebar.write(f"👤 المستخدم: **{st.session_state.user_role}**")
if st.sidebar.button("تسجيل الخروج"):
    st.session_state.authenticated = False
    st.rerun()

tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجل والبحث", "📂 الأرشيف", "📈 الإحصائيات", "⚙️ الإعدادات"]) \
    if st.session_state.user_role == "مدير" else \
    st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجل والبحث"])

# ────────────────────────────────────────────────
#               تبويب الحجز الجديد (محسن)
# ────────────────────────────────────────────────
with tabs[0]:
    st.markdown(
        '<h3 style="color:#1e3c72; text-align:center; margin-bottom:1.5rem;">'
        '➕ تسجيل نزيل جديد</h3>',
        unsafe_allow_html=True
    )

    with st.form("booking_form_enhanced", clear_on_submit=True):
        # قسم المعلومات الأساسية
        st.markdown(
            '<div class="section-box" style="border-color:#1e3c72;">'
            '<h4 style="margin:0; color:#1e3c72;">👤 معلومات النزيل الأساسية</h4></div>',
            unsafe_allow_html=True
        )
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**الاسم واللقب** 👤")
            name = st.text_input("", placeholder="الاسم الكامل", label_visibility="collapsed")
            
            st.markdown("**تاريخ الازدياد** 📅")
            birth_date = st.date_input("", value=date.today() - timedelta(days=365*22), label_visibility="collapsed")
            
            st.markdown("**مكان الازدياد** 🏙️")
            birth_place = st.text_input("", label_visibility="collapsed")
            
            st.markdown("**العنوان الكامل** 🏠")
            address = st.text_input("", label_visibility="collapsed")

        with col2:
            st.markdown("**الجنسية** 🌍")
            nationalities = ["الجزائر", "تونس", "المغرب", "فرنسا", "إسبانيا", "إيطاليا", "تركيا", "أخرى"]
            nationality = st.selectbox("", nationalities, index=0, label_visibility="collapsed")
            
            st.markdown("**نوع الوثيقة** 🪪")
            id_type = st.selectbox("", [
                "بطاقة التعريف الوطنية",
                "جواز السفر",
                "رخصة السياقة",
                "أخرى"
            ], label_visibility="collapsed")
            
            id_label = {
                "بطاقة التعريف الوطنية": "رقم بطاقة التعريف",
                "جواز السفر": "رقم جواز السفر",
                "رخصة السياقة": "رقم رخصة السياقة",
                "أخرى": "رقم الوثيقة"
            }[id_type]
            st.markdown(f"**{id_label}** 🔢")
            id_number = st.text_input("", label_visibility="collapsed")
            
            st.markdown("**رقم الهاتف** 📱")
            phone = st.text_input("", placeholder="05XX XXX XXX", label_visibility="collapsed")

        st.markdown("<hr style='border-top:1px dashed #ccc; margin:1.5rem 0;'>", unsafe_allow_html=True)

        # قسم تفاصيل الحجز
        st.markdown(
            '<div class="section-box" style="border-color:#28a745;">'
            '<h4 style="margin:0; color:#1e7e34;">🏨 تفاصيل الحجز</h4></div>',
            unsafe_allow_html=True
        )
        c1, c2, c3 = st.columns([2, 3, 3])
        with c1:
            st.markdown("**عدد الليالي** 🌙")
            nights = st.number_input("", min_value=1, value=1, step=1, label_visibility="collapsed")
        with c2:
            st.markdown("**تاريخ الدخول** 📅")
            check_in = st.date_input("", value=date.today(), label_visibility="collapsed")
            check_out = check_in + timedelta(days=nights)
            st.caption(f"الخروج المتوقع: **{check_out:%Y-%m-%d}**")
        with c3:
            total_cost = nights * 400
            st.markdown(
                f'<div style="background:#e6ffe6; padding:1rem; border-radius:8px; text-align:center; border:1px solid #b3e6b3;">'
                f'<strong style="font-size:1.4rem; color:#006400;">{total_cost:,} دج</strong><br>'
                '<small>التكلفة المتوقعة (400 دج / ليلة)</small></div>',
                unsafe_allow_html=True
            )

        wing = st.selectbox("الجناح", list(wings.keys()))
        room = st.selectbox("الغرفة", list(wings[wing].keys()))
        bed = st.selectbox("رقم السرير", [f"سرير {i+1}" for i in range(wings[wing][room])])

        # قسم الحقول الثانوية (مطوي)
        with st.expander("ℹ️ معلومات إضافية وطلبات خاصة", expanded=False):
            st.markdown("**غرض / سبب الإقامة** 🎯")
            purposes = [
                "سياحة / زيارة عائلية",
                "عمل / مهمة رسمية",
                "دراسة / تكوين / تدريب",
                "علاج طبي",
                "نشاط رياضي أو ثقافي",
                "عبور / ترانزيت",
                "أخرى"
            ]
            purpose = st.selectbox("", purposes)
            if purpose == "أخرى":
                purpose_other = st.text_input("وضّح السبب الآخر")

            companions_count = st.number_input("عدد الأشخاص المرافقين", min_value=0, max_value=8, value=0)
            if companions_count > 0:
                companions_names = st.text_area(
                    f"أسماء المرافقين ({companions_count})",
                    height=100,
                    placeholder="اكتب اسم كل شخص في سطر منفصل\nخاصة القاصرين"
                )

            notes = st.text_area("ملاحظات / طلبات خاصة", height=110,
                                placeholder="مثال: يفضل سرير سفلي – حساسية غذائية – يصطحب طفل رضيع...")

        # منطقة القاصرين (صندوق برتقالي/أصفر خفيف)
        age = (date.today() - birth_date).days // 365
        guardian_name = guardian_permission = ""
        if age < 18:
            st.markdown(
                '<div class="minor-box">'
                f'<strong style="color:#664d03;">⚠️ تنبيه: النزيل قاصر (العمر الحالي ≈ {age} سنة)</strong><br>'
                '<small>يرجى تسجيل بيانات ولي الأمر أو الوصي القانوني</small></div>',
                unsafe_allow_html=True
            )
            colG1, colG2 = st.columns(2)
            with colG1:
                guardian_name = st.text_input("اسم ولي الأمر / الوصي")
            with colG2:
                guardian_permission = st.selectbox("نوع التصريح / الإذن", [
                    "موافقة خطية موقعة",
                    "حضور ولي الأمر شخصياً",
                    "إذن قضائي / وصاية رسمية",
                    "مرافق معتمد من ولي الأمر",
                    "حالة خاصة (يرجى التوضيح في الملاحظات)"
                ])

        # زر التأكيد البارز
        if st.form_submit_button("💾 تأكيد الحجز وتسجيل النزيل", type="primary", use_container_width=True):
            if not name or not id_number or not phone:
                st.error("الاسم، رقم الوثيقة، ورقم الهاتف مطلوبة")
            elif is_bed_occupied(wing, room, bed):
                st.error("❌ هذا السرير محجوز حالياً")
            else:
                add_guest(name, birth_date, birth_place, address, id_number, wing, room, bed, check_in, check_out,
                          guardian_name, guardian_permission)

                # رسالة نجاح مفصلة وجميلة
                st.markdown(
                    f"""
                    <div class="success-box">
                        <h3 style="margin:0 0 1rem 0; color:#0f5132;">🎉 تم التسجيل بنجاح!</h3>
                        <p style="margin:0.5rem 0; font-size:1.1rem;">
                            <strong>النزيل:</strong> {name}
                        </p>
                        <p style="margin:0.5rem 0;">
                            <strong>المكان:</strong> {wing} → {room} → {bed}
                        </p>
                        <p style="margin:0.5rem 0;">
                            <strong>المدة:</strong> {nights} ليلة من {check_in:%Y-%m-%d} إلى {check_out:%Y-%m-%d}
                        </p>
                        <p style="margin:0.8rem 0; font-size:1.25rem; font-weight:bold; color:#006400;">
                            💰 التكلفة المتوقعة: {total_cost:,} دج
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button("➕ حجز نزيل جديد", type="secondary", use_container_width=True):
                    st.rerun()

# ────────────────────────────────────────────────
#               تبويب حالة الغرف
# ────────────────────────────────────────────────
with tabs[1]:
    st.subheader("📊 حالة الأجنحة والأسرة")
    # هنا يمكنك إضافة عرض الخريطة كما كان سابقاً (الكود المختصر)
    st.info("خريطة الأسرّة – يمكن توسيعها لاحقاً")

# باقي التبويبات يمكن توسيعها بنفس الطريقة حسب الحاجة

# تذييل
st.markdown("""
    <div class="developer-footer">
        Developer <span style="color:#00d4ff; font-weight:bold;">®ridha_merzoug®</span> [رضا مرزوق] - 2026
    </div>
""", unsafe_allow_html=True)
