import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import io

# ====================== إعداد الصفحة والـ CSS ======================
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
    .form-section {
        background: white; padding: 1.5rem; border-radius: 12px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 1.5rem;
    }
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

init_db()

# ====================== دوال مساعدة ======================
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

# ====================== الجلسة ======================
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

# إنشاء التبويبات (يجب أن تكون قبل أي with tabs[])
if st.session_state.user_role == "مدير":
    tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجل والبحث", "📂 الأرشيف", "📈 الإحصائيات", "⚙️ الإعدادات"])
else:
    tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجل والبحث"])

# ====================== تبويب الحجز الجديد (النسخة المحسنة والنهائية) ======================
with tabs[0]:
    st.markdown('<h2 style="text-align:center; color:#1e3c72; margin-bottom:10px;">✨ تسجيل نزيل جديد</h2>', unsafe_allow_html=True)
    
    # خطوات مرئية
    st.markdown("""
        <div style="display:flex; justify-content:center; gap:15px; margin:20px 0; flex-wrap:wrap;">
            <div style="background:#1e3c72; color:white; padding:8px 18px; border-radius:30px; font-weight:bold; min-width:140px; text-align:center;">1. البيانات الشخصية</div>
            <div style="background:#e6f0ff; color:#1e3c72; padding:8px 18px; border-radius:30px; min-width:140px; text-align:center;">2. الوثائق</div>
            <div style="background:#e6f0ff; color:#1e3c72; padding:8px 18px; border-radius:30px; min-width:140px; text-align:center;">3. تفاصيل الإقامة</div>
        </div>
    """, unsafe_allow_html=True)

    with st.form("enhanced_booking_form", clear_on_submit=False):
        
        # حفظ البيانات في الجلسة لعدم المسح عند الخطأ
        defaults = {
            "name": "", "birth_date": date.today() - timedelta(days=365*22),
            "birth_place": "", "address": "", "nationality": "الجزائر",
            "id_type": "بطاقة التعريف الوطنية", "id_number": "", "phone": "",
            "nights": 1, "check_in": date.today(), "wing": list(wings.keys())[0],
            "room": list(wings[list(wings.keys())[0]].keys())[0], "bed": "سرير 1",
            "purpose": "سياحة / زيارة عائلية", "purpose_other": "",
            "companions_count": 0, "companions_names": "", "notes": "",
            "guardian_name": "", "guardian_permission": "موافقة خطية موقعة"
        }

        for key, val in defaults.items():
            if f"form_{key}" not in st.session_state:
                st.session_state[f"form_{key}"] = val

        if 'form_error' not in st.session_state:
            st.session_state.form_error = ""

        # عرض رسالة الخطأ إن وجدت
        if st.session_state.form_error:
            st.error(st.session_state.form_error)

        # قسم البيانات الشخصية
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown("### 👤 البيانات الشخصية")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم واللقب *", value=st.session_state["form_name"], key="name_input")
            birth_date = st.date_input("تاريخ الازدياد", value=st.session_state["form_birth_date"], key="birth_date_input")
            birth_place = st.text_input("مكان الازدياد", value=st.session_state["form_birth_place"], key="birth_place_input")
        with c2:
            address = st.text_input("العنوان الكامل", value=st.session_state["form_address"], key="address_input")
            nationality = st.selectbox("الجنسية", ["الجزائر", "تونس", "المغرب", "فرنسا", "أخرى"], 
                                    index=["الجزائر", "تونس", "المغرب", "فرنسا", "أخرى"].index(st.session_state["form_nationality"]) if st.session_state["form_nationality"] in ["الجزائر", "تونس", "المغرب", "فرنسا", "أخرى"] else 0, key="nationality_input")
            phone = st.text_input("رقم الهاتف (اختياري)", value=st.session_state["form_phone"], placeholder="05XX XXX XXX", key="phone_input")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # قسم الوثائق
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown("### 🪪 الوثائق الرسمية")
        cA, cB = st.columns(2)
        with cA:
            id_type = st.selectbox("نوع الوثيقة", ["بطاقة التعريف الوطنية", "جواز السفر", "رخصة السياقة", "أخرى"], 
                                index=["بطاقة التعريف الوطنية", "جواز السفر", "رخصة السياقة", "أخرى"].index(st.session_state["form_id_type"]) if st.session_state["form_id_type"] in ["بطاقة التعريف الوطنية", "جواز السفر", "رخصة السياقة", "أخرى"] else 0, key="id_type_input")
            id_number = st.text_input("رقم الوثيقة *", value=st.session_state["form_id_number"], key="id_number_input")
        with cB:
            st.markdown("**الجنسية**")
            nat2 = st.selectbox("", ["الجزائرية", "تونسية", "مغربية", "فرنسية", "أخرى"], key="nat2_input")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # قسم تفاصيل الإقامة + التكلفة
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown("### 🏨 تفاصيل الإقامة")
        c3, c4, c5 = st.columns([2, 3, 3])
        with c3:
            nights = st.number_input("عدد الليالي", min_value=1, value=st.session_state["form_nights"], step=1, key="nights_input")
        with c4:
            check_in = st.date_input("تاريخ الدخول", value=st.session_state["form_check_in"], key="check_in_input")
            check_out = check_in + timedelta(days=nights)
            st.caption(f"**الخروج:** {check_out.strftime('%Y-%m-%d')}")
        with c5:
            total_cost = nights * 400
            st.metric("التكلفة المتوقعة", f"{total_cost:,} دج", help="400 دج لليلة الواحدة")

        wing = st.selectbox("الجناح", list(wings.keys()), index=list(wings.keys()).index(st.session_state["form_wing"]) if st.session_state["form_wing"] in wings else 0, key="wing_input")
        room = st.selectbox("الغرفة", list(wings[wing].keys()), index=list(wings[wing].keys()).index(st.session_state["form_room"]) if st.session_state["form_room"] in wings[wing] else 0, key="room_input")
        bed = st.selectbox("السرير", [f"سرير {i+1}" for i in range(wings[wing][room])], key="bed_input")
        st.markdown('</div>', unsafe_allow_html=True)

        # الحقول الإضافية
        with st.expander("ℹ️ معلومات إضافية (اختياري)"):
            purpose = st.selectbox("غرض الإقامة", ["سياحة / زيارة عائلية", "عمل / مهمة رسمية", "دراسة / تدريب", "علاج طبي", "نشاط رياضي أو ثقافي", "عبور / ترانزيت", "أخرى"], key="purpose_input")
            if purpose == "أخرى":
                purpose_other = st.text_input("وضّح السبب الآخر", value=st.session_state["form_purpose_other"], key="purpose_other_input")
            companions_count = st.number_input("عدد المرافقين", min_value=0, max_value=8, value=st.session_state["form_companions_count"], key="companions_count_input")
            if companions_count > 0:
                companions_names = st.text_area("أسماء المرافقين", value=st.session_state["form_companions_names"], key="companions_names_input")
            notes = st.text_area("ملاحظات / طلبات خاصة", value=st.session_state["form_notes"], key="notes_input")

        # منطقة القاصرين
        age = (date.today() - birth_date).days // 365
        if age < 18:
            st.markdown('<div class="minor-box">⚠️ النزيل قاصر (عمر ≈ {age} سنة) - يرجى تسجيل ولي الأمر</div>', unsafe_allow_html=True)
            g1, g2 = st.columns(2)
            with g1:
                guardian_name = st.text_input("اسم ولي الأمر", value=st.session_state["form_guardian_name"], key="guardian_name_input")
            with g2:
                guardian_permission = st.selectbox("نوع التصريح", ["موافقة خطية", "حضور ولي الأمر", "إذن قضائي"], key="guardian_permission_input")

        submitted = st.form_submit_button("💾 تأكيد وتسجيل النزيل", type="primary", use_container_width=True)

        if submitted:
            # حفظ القيم في الجلسة
            st.session_state["form_name"] = name
            st.session_state["form_birth_date"] = birth_date
            st.session_state["form_birth_place"] = birth_place
            st.session_state["form_address"] = address
            st.session_state["form_nationality"] = nationality
            st.session_state["form_id_type"] = id_type
            st.session_state["form_id_number"] = id_number
            st.session_state["form_phone"] = phone
            st.session_state["form_nights"] = nights
            st.session_state["form_check_in"] = check_in
            st.session_state["form_wing"] = wing
            st.session_state["form_room"] = room
            st.session_state["form_bed"] = bed

            errors = []
            if not name.strip(): errors.append("الاسم واللقب مطلوب")
            if not id_number.strip(): errors.append("رقم الوثيقة مطلوب")

            if errors:
                st.session_state.form_error = " | ".join(errors)
                st.rerun()
            else:
                st.session_state.form_error = ""
                add_guest(name, birth_date, birth_place, address, id_number, wing, room, bed, check_in, check_out)
                
                st.markdown(
                    f"""
                    <div class="success-box">
                        <h2>🎉 تم التسجيل بنجاح!</h2>
                        <h3>{name}</h3>
                        <p><strong>المدة:</strong> {nights} ليلة • {check_in} → {check_out}</p>
                        <p style="font-size:1.5rem; color:#006400;"><strong>التكلفة: {nights*400:,} دج</strong></p>
                    </div>
                    """, unsafe_allow_html=True
                )
                st.balloons()

                if st.button("➕ حجز نزيل جديد", type="secondary", use_container_width=True):
                    for key in list(st.session_state.keys()):
                        if key.startswith("form_"):
                            st.session_state[key] = defaults[key.replace("form_", "")]
                    st.session_state.form_error = ""
                    st.rerun()

# ====================== تبويب حالة الغرف ======================
with tabs[1]:
    st.subheader("📊 حالة الأجنحة والأسرة")
    for wing_name, rooms in wings.items():
        st.markdown(f"**{wing_name}**")
        for room_name, bed_count in rooms.items():
            st.write(f"  {room_name}")
            cols = st.columns(5)
            for i in range(bed_count):
                col = cols[i % 5]
                status = "occupied" if is_bed_occupied(wing_name, room_name, f"سرير {i+1}") else "free"
                col.markdown(f'<div class="bed-box {status}">{i+1}</div>', unsafe_allow_html=True)

# تذييل
st.markdown("""
    <div class="developer-footer">
        Developer <span style="color:#00d4ff; font-weight:bold;">®ridha_merzoug®</span> [رضا مرزوق] - 2026
    </div>
""", unsafe_allow_html=True)
