import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# 1. إعدادات الصفحة والتصميم
st.set_page_config(page_title="منظومة محمدي يوسف V2.3", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&family=Orbitron:wght@500&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(135deg, #001f3f, #0074D9); color: white; padding: 1.5rem; border-radius: 15px; text-align: center; margin-bottom: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .form-section { background: #ffffff; padding: 25px; border-radius: 15px; border-right: 8px solid #0074D9; margin-bottom: 25px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .stat-card { background: #f0f7ff; padding: 15px; border-radius: 12px; border: 1px solid #b3d7ff; text-align: center; height: 100%; }
    .review-box { background: #fff3cd; border: 2px dashed #ffc107; padding: 25px; border-radius: 15px; margin-top: 25px; }
    .danger-text { color: #dc3545; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. إدارة قاعدة البيانات
DB_FILE = "hostel_pro_v2_2026.db"
TOTAL_BEDS_PER_WING = 38 # إجمالي 76 سرير (38 ذكور / 38 إناث)

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

def is_already_resident(id_num):
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT wing, room, bed FROM guests WHERE id_num=? AND status='مقيم'", (id_num,)).fetchone()

def get_wing_occupancy(wing):
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT COUNT(*) FROM guests WHERE wing=? AND status='مقيم'", (wing,)).fetchone()[0]

init_db()

# 3. الواجهة الرئيسية
st.markdown('<div class="main-title">🏢 منظومة إدارة بيت الشباب محمدي يوسف<br><small>الإصدار الأمني الاحترافي V2.3</small></div>', unsafe_allow_html=True)

# 📊 الميزة 1: لوحة الإحصائيات الشاملة
occ_m = get_wing_occupancy("جناح ذكور")
occ_f = get_wing_occupancy("جناح إناث")

col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.markdown(f'<div class="stat-card"><b>🏨 إجمالي الأسرّة</b><br><h2 style="color:#0074D9;">76</h2></div>', unsafe_allow_html=True)
with col_s2:
    st.markdown(f'<div class="stat-card"><b>♂️ شاغر (ذكور)</b><br><h2 style="color:#28a745;">{TOTAL_BEDS_PER_WING - occ_m}</h2></div>', unsafe_allow_html=True)
with col_s3:
    st.markdown(f'<div class="stat-card"><b>♀️ شاغر (إناث)</b><br><h2 style="color:#28a745;">{TOTAL_BEDS_PER_WING - occ_f}</h2></div>', unsafe_allow_html=True)

st.write("---")

# ميزة البحث التلقائي
with st.expander("🔍 البحث عن نزيل سابق (تعبئة تلقائية)"):
    s_id = st.text_input("رقم الهوية للبحث")
    if st.button("استرجاع البيانات"):
        with sqlite3.connect(DB_FILE) as conn:
            old = conn.execute("SELECT * FROM guests WHERE id_num=? LIMIT 1", (s_id,)).fetchone()
            if old:
                st.session_state.k_name, st.session_state.k_nat = old[1], old[7]
                st.session_state.k_addr, st.session_state.k_job = old[4], old[10]
                st.session_state.k_phone = old[11]
                st.success("✅ تم العثور على البيانات!")
            else: st.error("لا يوجد سجل سابق.")

# --- استمارة الحجز المتطورة ---
st.markdown('<div class="form-section"><h3>📝 معلومات النزيل والمرافقين</h3>', unsafe_allow_html=True)

name = st.text_input("👤 الاسم واللقب الكامل *", key="k_name")

c1, c2 = st.columns(2)
b_date = c1.date_input("📅 تاريخ الميلاد", min_value=date(1940, 1, 1), key="k_bdate")
b_place = c2.text_input("📍 مكان الازدياد", key="k_bplace")

address = st.text_input("🏠 العنوان الشخصي الكامل", key="k_addr")

c3, c4 = st.columns(2)
id_type = c3.selectbox("📄 نوع الوثيقة", ["بطاقة تعريف بيومترية", "بطاقة تعريف عادية", "رخصة سياقة بيومترية", "رخصة سياقة عادية", "جواز السفر", "اخرى"], key="k_idtype")
id_num = c4.text_input("🔢 رقم الوثيقة *", key="k_idnum")

if id_num:
    res_info = is_already_resident(id_num)
    if res_info: st.error(f"🚨 تنبيه أمني: هذا النزيل مقيم حالياً في {res_info[0]} - {res_info[1]}")

# ميزة الجنسية المتقدمة
c5, c6 = st.columns(2)
nat_options = ["جزائرية", "تونسية", "مغربية", "ليبية", "فرنسية", "صحراوية", "أخرى"]
nat_choice = c5.selectbox("🇩🇿 الجنسية", nat_options, key="k_nat_choice")

if nat_choice == "أخرى":
    nat = c5.text_input("اكتب الجنسية يدوياً", key="k_nat_manual")
else:
    nat = nat_choice

visa_ex = None
is_visa_valid = True
if nat != "جزائرية":
    st.info("ℹ️ بيانات الفيزا للأجانب (إجباري حسب القانون الجزائري)")
    cv1, cv2 = st.columns(2)
    visa_in = cv1.date_input("🛂 تاريخ الدخول", key="k_visa_in")
    visa_ex = cv2.date_input("📅 تاريخ انتهاء الفيزا", key="k_visa_ex")
    if visa_ex < date.today():
        st.markdown('<p class="danger-text">🚨 خطأ قانوني: لا يمكن حجز غرفة لأجنبي بتأشيرة منتهية الصلاحية!</p>', unsafe_allow_html=True)
        is_visa_valid = False

c7, c8 = st.columns(2)
job = c7.text_input("💼 المهنة", key="k_job")
phone = c8.text_input("📞 الهاتف", key="k_phone")

num_comps = st.number_input("👨‍👩‍👧‍👦 عدد المرافقين", min_value=0, max_value=10, key="k_num_comps")
comps = st.text_area("أدخل أسماء وأعمار المرافقين", key="k_comp")
note = st.text_area("🗒️ ملاحظات", key="k_note")

# حساب العمر ومنطق القاصر
age = date.today().year - b_date.year - ((date.today().month, date.today().day) < (b_date.month, b_date.day))
minor_doc = ""
is_minor_valid = True

if age < 18:
    st.warning(f"⚠️ النزيل قاصر ({age} سنة)")
    minor_doc = st.selectbox("📜 الوثيقة المبررة (إجباري للقاصر) *", ["-- اختر الوثيقة --", "تصريح ابوي", "حضور الولي", "امر بمهة", "تصريح امني", "اخرى"], key="k_minor")
    if minor_doc == "-- اختر الوثيقة --":
        st.markdown('<p class="danger-text">🚨 يجب اختيار وثيقة تبرر حجز القاصر للمتابعة.</p>', unsafe_allow_html=True)
        is_minor_valid = False

st.markdown("---")
c9, c10 = st.columns(2)
wing = c9.selectbox("🏢 الجناح", ["جناح ذكور", "جناح إناث"], key="k_wing")
room = c10.selectbox("🚪 الغرفة", [f"غرفة {i:02d}" for i in range(1, 11)], key="k_room")

avail_beds = get_available_beds(wing, room)
bed = st.selectbox("🛏️ السرير الشاغر", avail_beds, key="k_bed") if avail_beds else None

# منطق زر التأكيد المعقد
can_confirm = is_visa_valid and is_minor_valid and name and id_num and bed

if st.button("تأكيد ومراجعة الحجز 📑", use_container_width=True, disabled=not can_confirm):
    st.session_state.confirm = True
elif not can_confirm:
    st.info("يرجى تصحيح الأخطاء (الفيزا، وثيقة القاصر، أو البيانات الناقصة) لتفعيل زر التأكيد.")

# --- وضع المراجعة ---
if st.session_state.get('confirm', False):
    st.markdown('<div class="review-box"><h4>👁️ مراجعة نهائية قبل الحفظ</h4>', unsafe_allow_html=True)
    st.write(f"النزيل: {name} | الجنسية: {nat} | الهوية: {id_num}")
    st.write(f"الموقع: {wing} - {room} - {bed}")
    if age < 18: st.write(f"الحالة: قاصر (الوثيقة: {minor_doc})")
    
    cr1, cr2 = st.columns(2)
    if cr1.button("إتمام الحفظ النهائي ✅", type="primary"):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""INSERT INTO guests (name, b_date, b_place, address, id_type, id_num, nationality, visa_date, visa_expiry, job, phone, note, companions, num_comps, minor_doc, wing, room, bed, check_in) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                         (name, str(b_date), b_place, address, id_type, id_num, nat, str(date.today()), str(visa_ex), job, phone, note, comps, num_comps, minor_doc, wing, room, bed, str(date.today())))
        st.balloons(); st.success("تم تسجيل النزيل بنجاح!"); st.session_state.confirm = False; st.rerun()
    if cr2.button("تعديل البيانات ✏️"): st.session_state.confirm = False; st.info("يمكنك تعديل الخانات الآن")

st.markdown("</div><center><h2 style='font-family:Orbitron;'>RIDHA MERZOUG LABS</h2></center>", unsafe_allow_html=True)
