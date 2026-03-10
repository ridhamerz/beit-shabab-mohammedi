import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# 1. إعدادات الصفحة والتنسيق
st.set_page_config(page_title="منظومة محمدي يوسف V2.1", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(135deg, #001f3f, #0074D9); color: white; padding: 1.5rem; border-radius: 15px; text-align: center; margin-bottom: 2rem; }
    .form-section { background: #f8f9fa; padding: 20px; border-radius: 12px; border-right: 6px solid #0074D9; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .review-box { background: #fff3cd; border: 2px dashed #ffc107; padding: 20px; border-radius: 10px; margin-top: 20px; }
    </style>
""", unsafe_allow_html=True)

# 2. إدارة قاعدة البيانات
DB_FILE = "hostel_pro_2026.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, b_date TEXT, b_place TEXT,
            address TEXT, id_type TEXT, id_num TEXT UNIQUE, nationality TEXT, 
            visa_date TEXT, job TEXT, phone TEXT, note TEXT, companions TEXT,
            minor_doc TEXT, wing TEXT, room TEXT, bed TEXT, status TEXT DEFAULT 'مقيم', check_in TEXT
        )''')

def get_available_beds(wing, room):
    all_beds = [f"سرير {i:02d}" for i in range(1, 7)]
    with sqlite3.connect(DB_FILE) as conn:
        occupied = [r[0] for r in conn.execute("SELECT bed FROM guests WHERE wing=? AND room=? AND status='مقيم'", (wing, room)).fetchall()]
    return [b for b in all_beds if b not in occupied]

init_db()

# 3. الواجهة الرئيسية
st.markdown('<div class="main-title">🏢 منظومة إدارة بيت الشباب - قالمة<br><small>نظام الحجز الذكي V2.1</small></div>', unsafe_allow_html=True)

# ميزة البحث الذكي (خارج الاستمارة)
with st.expander("🔍 البحث التلقائي عن نزيل سابق (لتعبئة البيانات)"):
    s_id = st.text_input("أدخل رقم الهوية للبحث")
    if st.button("استرجاع البيانات"):
        with sqlite3.connect(DB_FILE) as conn:
            old = conn.execute("SELECT * FROM guests WHERE id_num=? LIMIT 1", (s_id,)).fetchone()
            if old:
                st.session_state.k_name = old[1]
                st.session_state.k_nat = old[7]
                st.session_state.k_addr = old[4]
                st.session_state.k_job = old[9]
                st.session_state.k_phone = old[10]
                st.success("✅ تم العثور على البيانات وتجهيزها!")
            else: st.error("لم يتم العثور على سجل سابق.")

# --- استمارة الحجز ---
st.markdown('<div class="form-section"><h3>📝 استمارة معلومات النزيل</h3>', unsafe_allow_html=True)

# توزيع الحقول حسب طلبك
name = st.text_input("👤 الاسم واللقب الكامل *", key="k_name")

c1, c2 = st.columns(2)
b_date = c1.date_input("📅 تاريخ الميلاد", min_value=date(1940, 1, 1), key="k_bdate")
b_place = c2.text_input("📍 مكان الازدياد", key="k_bplace")

address = st.text_input("🏠 العنوان الشخصي الكامل", key="k_addr")

c3, c4 = st.columns(2)
id_types = ["بطاقة تعريف عادية", "بطاقة تعريف بيومترية", "رخصة سياقة عادية", "رخصة سياقة بيومترية", "جواز السفر", "اخرى"]
id_type = c3.selectbox("📄 نوع وثيقة الهوية", id_types, key="k_idtype")
id_num = c4.text_input("🔢 رقم الوثيقة *", key="k_idnum")

c5, c6 = st.columns(2)
nat = c5.text_input("🇩🇿 الجنسية", value="جزائرية", key="k_nat")
visa = ""
if nat != "جزائرية":
    visa = c6.date_input("🛂 تاريخ الدخول إلى الجزائر (الفيزا)", key="k_visa")

c7, c8 = st.columns(2)
job = c7.text_input("💼 المهنة (اختياري)", key="k_job")
phone = c8.text_input("📞 رقم الهاتف (اختياري)", key="k_phone")

note = st.text_area("🗒️ ملاحظات عامة", key="k_note")
comps = st.text_area("👨‍👩‍👧‍👦 المرافقين للنزيل (الأسماء والأعمار)", key="k_comp")

# حساب العمر آلياً
age = date.today().year - b_date.year - ((date.today().month, date.today().day) < (b_date.month, b_date.day))
minor_doc = ""
if age < 18:
    st.warning(f"⚠️ النزيل قاصر (العمر: {age} سنة)")
    minor_doc = st.selectbox("📜 نوع الترخيص المطلوب", ["تصريح ابوي", "حضور الولي", "امر بمهة", "تصريح امني", "اخرى"], key="k_minor")

# قسم الغرفة
st.markdown("---")
c9, c10 = st.columns(2)
wing = c9.selectbox("🏢 الجناح", ["ذكور", "إناث"], key="k_wing")
room = c10.selectbox("🚪 الغرفة", [f"غرفة {i:02d}" for i in range(1, 11)], key="k_room")

# الأسرة الشاغرة فقط
avail_beds = get_available_beds(wing, room)
if avail_beds:
    bed = st.selectbox("🛏️ السرير المتوفر", avail_beds, key="k_bed")
else:
    st.error("الغرفة ممتلئة!")
    bed = None

# زر الحجز
if st.button("تأكيد الحجز 📑", use_container_width=True):
    if not name or not id_num or not bed:
        st.error("⚠️ خطأ: يرجى إدخال الاسم ورقم الهوية واختيار سرير. (لم تفقد البيانات المكتوبة)")
    else:
        st.session_state.confirm = True

# --- وضع المراجعة والتعديل ---
if st.session_state.get('confirm', False):
    st.markdown('<div class="review-box"><h4>👁️ مراجعة البيانات قبل الحفظ النهائي</h4>', unsafe_allow_html=True)
    st.write(f"**النزيل:** {name} | **الجنسية:** {nat} | **العمر:** {age} سنة")
    st.write(f"**الموقع:** {wing} - {room} - {bed}")
    
    cr1, cr2 = st.columns(2)
    if cr1.button("إتمام الحفظ النهائي ✅", type="primary"):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""INSERT INTO guests (name, b_date, b_place, address, id_type, id_num, nationality, visa_date, job, phone, note, companions, minor_doc, wing, room, bed, check_in) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                         (name, str(b_date), b_place, address, id_type, id_num, nat, str(visa), job, phone, note, comps, minor_doc, wing, room, bed, str(date.today())))
        st.balloons()
        st.success("تم الحفظ بنجاح!")
        st.session_state.confirm = False
        st.rerun()
        
    if cr2.button("تعديل البيانات ✏️"):
        st.session_state.confirm = False
        st.info("يمكنك الآن تعديل البيانات في الأعلى.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<center><b>RIDHA MERZOUG LABS</b></center>", unsafe_allow_html=True)
