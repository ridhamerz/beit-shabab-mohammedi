import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta

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
#               قاعدة البيانات (محدثة)
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
        guardian_permission TEXT,
        nationality TEXT,
        id_type TEXT,
        phone TEXT,
        purpose TEXT,
        purpose_other TEXT,
        companions_count INTEGER DEFAULT 0,
        companions_names TEXT,
        notes TEXT
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
        guardian_permission TEXT,
        nationality TEXT,
        id_type TEXT,
        phone TEXT,
        purpose TEXT,
        purpose_other TEXT,
        companions_count INTEGER DEFAULT 0,
        companions_names TEXT,
        notes TEXT
    )''')
    
    conn.commit()
    conn.close()

init_db()

# ────────────────────────────────────────────────
#               دوال مساعدة (محسنة)
# ────────────────────────────────────────────────
def calculate_age(birth_date):
    """حساب العمر بدقة"""
    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age

def is_bed_occupied(wing, room, bed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM current_guests WHERE wing=? AND room=? AND bed=? AND status='مقيم'", 
              (wing, room, bed))
    result = c.fetchone()
    conn.close()
    return result is not None

def add_guest(name, birth_date, birth_place, address, id_card, wing, room, bed, 
              check_in, check_out, guardian_name=None, guardian_permission=None,
              nationality="الجزائر", id_type="بطاقة التعريف الوطنية", phone="",
              purpose="", purpose_other="", companions_count=0, companions_names="", notes=""):
    age = calculate_age(birth_date)
    is_minor = 'نعم' if age < 18 else 'لا'
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO current_guests 
            (name, birth_date, birth_place, address, id_card, wing, room, bed, 
             check_in, check_out, is_minor, guardian_name, guardian_permission,
             nationality, id_type, phone, purpose, purpose_other, 
             companions_count, companions_names, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, str(birth_date), birth_place, address, id_card, wing, room, bed, 
              str(check_in), str(check_out), is_minor, guardian_name, guardian_permission,
              nationality, id_type, phone, purpose, purpose_other, 
              companions_count, companions_names, notes))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("❌ رقم الوثيقة موجود مسبقاً!")
        return False
    except Exception as e:
        st.error(f"خطأ في التسجيل: {str(e)}")
        return False
    finally:
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

# تهيئة كل الحقول في الجلسة (شاملة الآن)
defaults = {
    "name": "",
    "birth_date": date.today() - timedelta(days=365*22),
    "birth_place": "",
    "address": "",
    "nationality": "الجزائر",
    "id_type": "بطاقة التعريف الوطنية",
    "id_number": "",
    "phone": "",
    "nights": 1,
    "check_in": date.today(),
    "wing": list(wings.keys())[0],
    "room": list(wings[list(wings.keys())[0]].keys())[0],
    "bed": "سرير 1",
    "purpose": "سياحة / زيارة عائلية",
    "purpose_other": "",
    "companions_count": 0,
    "companions_names": "",
    "notes": "",
    "guardian_name": "",
    "guardian_permission": "موافقة خطية موقعة"
}

for key, val in defaults.items():
    if f"form_{key}" not in st.session_state:
        st.session_state[f"form_{key}"] = val

if 'form_error' not in st.session_state:
    st.session_state.form_error = ""

if 'booking_success' not in st.session_state:
    st.session_state.booking_success = False

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
#               تبويب الحجز الجديد (النسخة النهائية المصححة)
# ────────────────────────────────────────────────
with tabs[0]:
    if st.session_state.booking_success:
        st.markdown(
            """
            <div class="success-box">
                <h3 style="margin:0 0 1rem 0; color:#0f5132;">🎉 تم التسجيل بنجاح!</h3>
                <p style="margin:0.5rem 0; font-size:1.1rem;">
                    النزيل تم تسجيله بنجاح
                </p>
                <p style="margin:0.5rem 0;">
                    يمكنك الآن إضافة نزيل آخر
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if st.button("➕ حجز نزيل جديد", type="primary", use_container_width=True):
            st.session_state.booking_success = False
            st.session_state.form_error = ""
            for key in defaults:
                st.session_state[f"form_{key}"] = defaults[key]
            st.rerun()
    else:
        if st.session_state.form_error:
            st.error(st.session_state.form_error)

        with st.form("booking_form_final", clear_on_submit=False):
            # قسم المعلومات الأساسية
            st.markdown(
                '<div class="section-box" style="border-color:#1e3c72;">'
                '<h4 style="margin:0; color:#1e3c72;">👤 معلومات النزيل الأساسية</h4></div>',
                unsafe_allow_html=True
            )
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**الاسم واللقب** 👤")
                name = st.text_input("", value=st.session_state["form_name"], key="name_input", label_visibility="collapsed")
                
                st.markdown("**تاريخ الازدياد** 📅")
                birth_date = st.date_input("", value=st.session_state["form_birth_date"], key="birth_date_input", label_visibility="collapsed")
                
                st.markdown("**مكان الازدياد** 🏙️")
                birth_place = st.text_input("", value=st.session_state["form_birth_place"], key="birth_place_input", label_visibility="collapsed")
                
                st.markdown("**العنوان الكامل** 🏠")
                address = st.text_input("", value=st.session_state["form_address"], key="address_input", label_visibility="collapsed")

            with col2:
                st.markdown("**الجنسية** 🌍")
                nationalities = ["الجزائر", "تونس", "المغرب", "فرنسا", "إسبانيا", "إيطاليا", "تركيا", "أخرى"]
                nat_index = nationalities.index(st.session_state["form_nationality"]) if st.session_state["form_nationality"] in nationalities else 0
                nationality = st.selectbox("", nationalities, index=nat_index, key="nationality_select", label_visibility="collapsed")
                
                st.markdown("**نوع الوثيقة** 🪪")
                id_types = ["بطاقة التعريف الوطنية", "جواز السفر", "رخصة السياقة", "أخرى"]
                id_index = id_types.index(st.session_state["form_id_type"]) if st.session_state["form_id_type"] in id_types else 0
                id_type = st.selectbox("", id_types, index=id_index, key="id_type_select", label_visibility="collapsed")
                
                id_label = {
                    "بطاقة التعريف الوطنية": "رقم بطاقة التعريف",
                    "جواز السفر": "رقم جواز السفر",
                    "رخصة السياقة": "رقم رخصة السياقة",
                    "أخرى": "رقم الوثيقة"
                }[id_type]
                st.markdown(f"**{id_label}** 🔢")
                id_number = st.text_input("", value=st.session_state["form_id_number"], key="id_number_input", label_visibility="collapsed")
                
                st.markdown("**رقم الهاتف** 📱 (اختياري)")
                phone = st.text_input("", value=st.session_state["form_phone"], placeholder="05XX XXX XXX", key="phone_input", label_visibility="collapsed")

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
                nights = st.number_input("", min_value=1, value=st.session_state["form_nights"], step=1, key="nights_input", label_visibility="collapsed")
            with c2:
                st.markdown("**تاريخ الدخول** 📅")
                check_in = st.date_input("", value=st.session_state["form_check_in"], key="check_in_input", label_visibility="collapsed")
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

            # اختيار الجناح والغرفة والسرير
            wing = st.selectbox("الجناح", list(wings.keys()), 
                               index=list(wings.keys()).index(st.session_state["form_wing"]) 
                               if st.session_state["form_wing"] in wings else 0, 
                               key="wing_select")
            room = st.selectbox("الغرفة", list(wings[wing].keys()), 
                               index=list(wings[wing].keys()).index(st.session_state["form_room"]) 
                               if st.session_state["form_room"] in wings[wing] else 0, 
                               key="room_select")
            bed_options = [f"سرير {i+1}" for i in range(wings[wing][room])]
            bed = st.selectbox("رقم السرير", bed_options, 
                              index=bed_options.index(st.session_state["form_bed"]) 
                              if st.session_state["form_bed"] in bed_options else 0, 
                              key="bed_select")

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
                purpose_index = purposes.index(st.session_state["form_purpose"]) if st.session_state["form_purpose"] in purposes else 0
                purpose = st.selectbox("", purposes, index=purpose_index, key="purpose_select")
                purpose_other = ""
                if purpose == "أخرى":
                    purpose_other = st.text_input("وضّح السبب الآخر", value=st.session_state["form_purpose_other"], key="purpose_other_input")

                companions_count = st.number_input("عدد الأشخاص المرافقين", min_value=0, max_value=8, 
                                                 value=st.session_state["form_companions_count"], key="companions_count")
                companions_names = ""
                if companions_count > 0:
                    companions_names = st.text_area(
                        f"أسماء المرافقين ({companions_count})",
                        value=st.session_state["form_companions_names"],
                        height=100,
                        placeholder="اكتب اسم كل شخص في سطر منفصل\nخاصة القاصرين",
                        key="companions_names_area"
                    )

                notes = st.text_area("ملاحظات / طلبات خاصة", value=st.session_state["form_notes"], height=110,
                                    placeholder="مثال: يفضل سرير سفلي – حساسية غذائية – يصطحب طفل رضيع...",
                                    key="notes_area")

            # منطقة القاصرين
            age = calculate_age(birth_date)
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
                    guardian_name = st.text_input("اسم ولي الأمر / الوصي", value=st.session_state["form_guardian_name"], key="guardian_name_input")
                with colG2:
                    gp_options = [
                        "موافقة خطية موقعة",
                        "حضور ولي الأمر شخصياً",
                        "إذن قضائي / وصاية رسمية",
                        "مرافق معتمد من ولي الأمر",
                        "حالة خاصة (يرجى التوضيح في الملاحظات)"
                    ]
                    gp_index = gp_options.index(st.session_state["form_guardian_permission"]) if st.session_state["form_guardian_permission"] in gp_options else 0
                    guardian_permission = st.selectbox("نوع التصريح / الإذن", gp_options, index=gp_index, key="guardian_permission_select")

            # زر التأكيد الرئيسي
            submitted = st.form_submit_button(
                "💾 تأكيد الحجز وتسجيل النزيل",
                type="primary",
                use_container_width=True
            )

            if submitted:
                # جمع القيم الحالية
                current = {
                    "name": name.strip(),
                    "birth_date": birth_date,
                    "birth_place": birth_place.strip(),
                    "address": address.strip(),
                    "nationality": nationality,
                    "id_type": id_type,
                    "id_number": id_number.strip(),
                    "phone": phone.strip(),
                    "nights": nights,
                    "check_in": check_in,
                    "wing": wing,
                    "room": room,
                    "bed": bed,
                    "purpose": purpose,
                    "purpose_other": purpose_other,
                    "companions_count": companions_count,
                    "companions_names": companions_names,
                    "notes": notes,
                    "guardian_name": guardian_name.strip() if guardian_name else "",
                    "guardian_permission": guardian_permission
                }

                # التحقق
                errors = []
                if not current["name"]: errors.append("الاسم واللقب مطلوب")
                if not current["id_number"]: errors.append("رقم الوثيقة مطلوب")

                # التحقق من السرير
                if is_bed_occupied(current["wing"], current["room"], current["bed"]):
                    errors.append("❌ السرير محجوز حالياً! اختر سرير آخر")

                if errors:
                    st.session_state.form_error = " | ".join(errors)
                    # حفظ القيم لإعادة العرض
                    for k, v in current.items():
                        st.session_state[f"form_{k}"] = v
                    st.rerun()
                else:
                    st.session_state.form_error = ""
                    success = add_guest(
                        current["name"], current["birth_date"], current["birth_place"], current["address"],
                        current["id_number"], current["wing"], current["room"], current["bed"],
                        current["check_in"], current["check_in"] + timedelta(days=current["nights"]),
                        current["guardian_name"], current["guardian_permission"],
                        current["nationality"], current["id_type"], current["phone"],
                        current["purpose"], current["purpose_other"],
                        current["companions_count"], current["companions_names"], current["notes"]
                    )
                    
                    if success:
                        st.session_state.booking_success = True
                        st.rerun()

# ────────────────────────────────────────────────
#               تبويب حالة الغرف (محسن)
# ────────────────────────────────────────────────
with tabs[1]:
    st.subheader("📊 حالة الأجنحة والأسرة")
    for wing_name, rooms in wings.items():
        st.markdown(f"**{wing_name}**")
        for room_name, bed_count in rooms.items():
            st.write(f"**{room_name}**")
            cols = st.columns(5)
            for i in range(bed_count):
                col = cols[i % 5]
                bed_num = f"سرير {i+1}"
                status = "occupied" if is_bed_occupied(wing_name, room_name, bed_num) else "free"
                col.markdown(f'<div class="bed-box {status}">{i+1}</div>', unsafe_allow_html=True)

# تذييل
st.markdown("""
    <div class="developer-footer">
        Developer <span style="color:#00d4ff; font-weight:bold;">®ridha_merzoug®</span> [رضا مرزوق] - 2026
    </div>
""", unsafe_allow_html=True)
