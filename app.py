import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
from fpdf import FPDF
import os

# ────────────────────────────────────────────────
#                إعداد الصفحة والـ CSS الفخم
# ────────────────────────────────────────────────
st.set_page_config(page_title="بيت الشباب محمدي يوسف - قالمة", layout="wide")

st.markdown("""
<style>
    * {font-family: 'Tahoma', 'Arial', sans-serif; direction: RTL; text-align: right;}
    .main-title {
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        color: white; padding: 20px; border-radius: 15px;
        text-align: center; margin-bottom: 25px; font-size: 1.8rem; font-weight: bold;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .bed-box {
        display: inline-block; width: 44px; height: 40px; margin: 5px;
        border-radius: 8px; text-align: center; line-height: 40px;
        color: white; font-weight: bold; cursor: pointer; position: relative;
    }
    .bed-box:hover::after {
        content: attr(title); position: absolute; top: -40px; left: 50%;
        transform: translateX(-50%); background: #222; color: #fff;
        padding: 8px 14px; border-radius: 6px; font-size: 0.9rem; white-space: nowrap;
        z-index: 9999; box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    }
    .free {background-color: #28a745; border-bottom: 4px solid #1e7e34;}
    .occupied {background-color: #dc3545; border-bottom: 4px solid #a71d2a;}
    .success-box {background: #d4edda; color: #155724; padding: 1.5rem; border-radius: 12px; border: 1px solid #c3e6cb; text-align: center; margin: 1rem 0;}
    .minor-box {background: #fff3cd !important; border-color: #ffc107 !important; padding: 1rem; border-radius: 8px; margin: 1rem 0;}
    .developer-footer {background: #1e3c72; color: #fff; padding: 10px; border-radius: 10px; text-align: center; margin-top: 50px; font-size: 0.9rem;}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#                     قاعدة البيانات
# ────────────────────────────────────────────────
DB_FILE = "youth_hostel.db"

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
        name TEXT, birth_date TEXT, birth_place TEXT, address TEXT, id_card TEXT,
        wing TEXT, room TEXT, bed TEXT, check_in TEXT, check_out TEXT, status TEXT,
        is_minor TEXT, guardian_name TEXT, guardian_permission TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# ────────────────────────────────────────────────
#                     دوال مساعدة
# ────────────────────────────────────────────────
def is_bed_occupied(wing, room, bed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM current_guests WHERE wing=? AND room=? AND bed=? AND status='مقيم'", (wing, room, bed))
    result = c.fetchone()
    conn.close()
    return result is not None

def add_guest(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO current_guests 
            (name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, is_minor, guardian_name, guardian_permission)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data["name"], str(data["birth_date"]), data["birth_place"], data["address"],
             data["id_number"], data["wing"], data["room"], data["bed"],
             str(data["check_in"]), str(data["check_out"]),
             'نعم' if (date.today() - data["birth_date"]).days // 365 < 18 else 'لا',
             data.get("guardian_name", ""), data.get("guardian_permission", "")))
        conn.commit()
        conn.close()
        return True, "تم التسجيل بنجاح!"
    except sqlite3.IntegrityError as e:
        conn.close()
        if "UNIQUE" in str(e):
            return False, "هذا الرقم موجود مسبقًا! النزيل مسجل من قبل."
        return False, "خطأ في قاعدة البيانات."
    except Exception as e:
        conn.close()
        return False, f"خطأ غير متوقع: {str(e)}"

def generate_receipt_pdf(guest):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # خط عربي (حمل ملف DejaVuSans.ttf أو Arial وحطه في نفس المجلد)
    try:
        pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        pdf.set_font("DejaVu", size=14)
    except:
        pdf.set_font("Arial", size=14)
    
    pdf.set_fill_color(30, 60, 114)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, "بيت الشباب محمدي يوسف - قالمة", ln=1, align='C')
    pdf.set_text_color(30, 60, 114)
    pdf.set_font("", size=18)
    pdf.cell(0, 15, "وصل دخول رسمي", ln=1, align='C')
    pdf.ln(10)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("", size=12)
    info = [
        f"الاسم الكامل: {guest['name']}",
        f"رقم الوثيقة: {guest['id_number']}",
        f"تاريخ الدخول: {guest['check_in']}",
        f"تاريخ الخروج: {guest['check_out']}",
        f"الجناح: {guest['wing']} | الغرفة: {guest['room']} | السرير: {guest['bed']}",
        f"عدد الليالي: {guest['nights']} | التكلفة: {guest['nights']*400:,} دج",
    ]
    for line in info:
        pdf.cell(0, 12, line, ln=1)
    
    pdf.ln(20)
    pdf.set_font("", size=14)
    pdf.cell(0, 10, "مرحبا بكم دائمًا في بيت الشباب", ln=1, align='C')
    
    filename = f"وصل_دخول_{guest['id_number']}_{date.today()}.pdf"
    pdf.output(filename)
    return filename

# ────────────────────────────────────────────────
#                     الجلسة والأجنحة
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

# القيم الافتراضية
defaults = { "name": "", "birth_date": date.today() - timedelta(days=365*22), "birth_place": "", "address": "", "nationality": "الجزائر",
    "id_type": "بطاقة التعريف الوطنية", "id_number": "", "phone": "", "nights": 1, "check_in": date.today(),
    "wing": "جناح ذكور", "room": "غرفة 01", "bed": "سرير 1", "purpose": "سياحة / زيارة عائلية",
    "purpose_other": "", "companions_count": 0, "companions_names": "", "notes": "", "guardian_name": "", "guardian_permission": "موافقة خطية موقعة"
}
for k, v in defaults.items():
    if f"form_{k}" not in st.session_state:
        st.session_state[f"form_{k}"] = v

# تسجيل الدخول
if not st.session_state.authenticated:
    st.markdown('<div class="main-title">بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)
    st.subheader("الدخول للنظام")
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

st.markdown('<div class="main-title">بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)
st.sidebar.write(f"المستخدم: **{st.session_state.user_role}**")
if st.sidebar.button("تسجيل الخروج"): st.session_state.authenticated = False; st.rerun()

tabs = st.tabs(["حجز جديد", "حالة الغرف", "السجل والبحث", "الأرشيف", "الإحصائيات", "الإعدادات"]) if st.session_state.user_role == "مدير" else st.tabs(["حجز جديد", "حالة الغرف", "السجل والبحث"])

# ────────────────────────────────────────────────
#                    تبويب الحجز الجديد
# ────────────────────────────────────────────────
with tabs[0]:
    if st.session_state.get("booking_success", False):
        st.markdown(f"""
        <div class="success-box">
            <h3>تم تسجيل النزيل بنجاح!</h3>
            <p><strong>{st.session_state.last_guest_name}</strong> تم إلحاقه في:</p>
            <p>{st.session_state.last_wing} → {st.session_state.last_room} → {st.session_state.last_bed}</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("حجز نزيل جديد", type="primary", use_container_width=True):
                st.session_state.booking_success = False
                for k in defaults: st.session_state[f"form_{k}"] = defaults[k]
                st.rerun()
        with c2:
            if st.button("طباعة وصل الدخول PDF", type="secondary", use_container_width=True):
                pdf_file = generate_receipt_pdf(st.session_state.last_guest_data)
                with open(pdf_file, "rb") as f:
                    st.download_button("تحميل الوصل", f, pdf_file, "application/pdf", use_container_width=True)
    else:
        if st.session_state.get("form_error"): st.error(st.session_state.form_error)
        
        with st.form("booking_form", clear_on_submit=False):
            st.markdown("### معلومات النزيل")
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("الاسم واللقب", value=st.session_state.form_name, key="f_name")
                birth_date = st.date_input("تاريخ الميلاد", value=st.session_state.form_birth_date, key="f_birth")
                birth_place = st.text_input("مكان الميلاد", value=st.session_state.form_birth_place, key="f_bplace")
                address = st.text_input("العنوان", value=st.session_state.form_address, key="f_addr")
            with c2:
                nationality = st.selectbox("الجنسية", ["الجزائر","تونس","المغرب","فرنسا","أخرى"], index=0, key="f_nat")
                id_type = st.selectbox("نوع الوثيقة", ["بطاقة التعريف الوطنية","جواز السفر","رخصة السياقة"], key="f_idtype")
                id_number = st.text_input("رقم الوثيقة", value=st.session_state.form_id_number, key="f_idnum")
                phone = st.text_input("رقم الهاتف (اختياري)", value=st.session_state.form_phone, key="f_phone")
            
            st.markdown("### تفاصيل الحجز")
            coln1, coln2, coln3 = st.columns(3)
            with coln1:
                nights = st.number_input("عدد الليالي", min_value=1, value=st.session_state.form_nights, key="f_nights")
            with coln2:
                check_in = st.date_input("تاريخ الدخول", value=st.session_state.form_check_in, key="f_checkin")
                check_out = check_in + timedelta(days=nights)
                st.write(f"الخروج: **{check_out:%Y-%m-%d}**")
            with coln3:
                st.markdown(f"<div style='background:#e8f5e8;padding:15px;border-radius:10px;text-align:center;'><strong style='font-size:1.5rem;color:#006400;'>{nights*400:,} دج</strong><br><small>400 دج / الليلة</small></div>", unsafe_allow_html=True)
            
            wing = st.selectbox("الجناح", list(wings.keys()), key="f_wing")
            room = st.selectbox("الغرفة", list(wings[wing].keys()), key="f_room")
            bed = st.selectbox("السرير", [f"سرير {i+1}" for i in range(wings[wing][room])], key="f_bed")
            
            age = (date.today() - birth_date).days // 365
            guardian_name = guardian_permission = ""
            if age < 18:
                st.markdown('<div class="minor-box"><strong>النزيل قاصر (عمر ≈ {age} سنة)</strong><br>يرجى تسجيل بيانات ولي الأمر</div>', unsafe_allow_html=True)
                g1, g2 = st.columns(2)
                with g1: guardian_name = st.text_input("اسم ولي الأمر", key="f_guardian")
                with g2: guardian_permission = st.selectbox("نوع الإذن", ["موافقة خطية موقعة","حضور شخصي","إذن قضائي"], key="f_gperm")
            
            submitted = st.form_submit_button("تأكيد الحجز وتسجيل النزيل", type="primary", use_container_width=True)
            
            if submitted:
                # حفظ كل القيم فورًا
                for key in ["name","birth_date","birth_place","address","id_number","phone","nights","check_in","wing","room","bed","guardian_name","guardian_permission"]:
                    st.session_state[f"form_{key}"] = locals()[key]
                
                errors = []
                if not name.strip(): errors.append("الاسم مطلوب")
                if not id_number.strip(): errors.append("رقم الوثيقة مطلوب")
                if is_bed_occupied(wing, room, bed): errors.append("السرير محجوز!")
                
                if errors:
                    st.session_state.form_error = " | ".join(errors)
                    st.rerun()
                else:
                    guest_data = {
                        "name": name, "birth_date": birth_date, "birth_place": birth_place, "address": address,
                        "id_number": id_number, "wing": wing, "room": room, "bed": bed,
                        "check_in": check_in, "check_out": check_out, "nights": nights,
                        "guardian_name": guardian_name, "guardian_permission": guardian_permission
                    }
                    success, msg = add_guest(guest_data)
                    if success:
                        st.session_state.booking_success = True
                        st.session_state.last_guest_name = name
                        st.session_state.last_wing = wing
                        st.session_state.last_room = room
                        st.session_state.last_bed = bed
                        st.session_state.last_guest_data = guest_data
                        st.session_state.form_error = ""
                        st.rerun()
                    else:
                        st.error(msg)

# ────────────────────────────────────────────────
#                    تبويب حالة الغرف (مع hover)
# ────────────────────────────────────────────────
with tabs[1]:
    st.subheader("حالة الأجنحة والأسرة")
    for wing_name, rooms in wings.items():
        st.markdown(f"**{wing_name}**")
        for room_name, bed_count in rooms.items():
            st.write(f"• {room_name}")
            cols = st.columns(5)
            for i in range(bed_count):
                bed_name = f"سرير {i+1}"
                occupied = is_bed_occupied(wing_name, room_name, bed_name)
                status = "occupied" if occupied else "free"
                tooltip = ""
                if occupied:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("SELECT name FROM current_guests WHERE wing=? AND room=? AND bed=? AND status='مقيم'", (wing_name, room_name, bed_name))
                    row = c.fetchone()
                    conn.close()
                    if row: tooltip = f"title='{row[0]}'"
                with cols[i % 5]:
                    st.markdown(f'<div class="bed-box {status}" {tooltip}>{i+1}</div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
#                        التذييل
# ────────────────────────────────────────────────
st.markdown("""
<div class="developer-footer">
    Developed with ❤️ by <span style="color:#00d4ff;font-weight:bold;">ridha_merzoug</span> [رضا مرزوق] © 2026
</div>
""", unsafe_allow_html=True)
