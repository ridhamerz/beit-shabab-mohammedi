import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import date, timedelta
from io import BytesIO

# 1. الإعدادات العامة والتصميم
st.set_page_config(page_title="Hostel Management Pro - قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&family=Orbitron:wght@500;900&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(135deg, #000428, #004e92); color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; }
    .section-box { background: #ffffff; padding: 20px; border-radius: 12px; border-right: 5px solid #004e92; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .minor-tag { background: #fff9db; padding: 10px; border-radius: 8px; border: 1px dashed #fcc419; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# 2. قاعدة البيانات (إصدار V23 الشامل)
DB_FILE = 'hostel_final_v23.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, nationality TEXT, address TEXT,
            id_type TEXT, id_num TEXT, phone TEXT, wing TEXT, room TEXT, bed_num TEXT,
            is_minor INTEGER, guardian_name TEXT, guardian_rel TEXT, check_in TEXT, status TEXT DEFAULT 'مقيم'
        )''')

def get_occupied_beds(wing, room):
    with sqlite3.connect(DB_FILE) as conn:
        res = conn.execute("SELECT bed_num FROM guests WHERE wing=? AND room=? AND status='مقيم'", (wing, room)).fetchall()
        return [r[0] for r in res]

init_db()

# 3. الواجهة الرئيسية
st.markdown('<div class="main-title">🏢 منظومة محمدي يوسف | الإدارة الشاملة للنزلاء</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["➕ حجز جديد", "📋 السجلات", "👮‍♂️ التصدير"])

with tab1:
    if 'step' not in st.session_state: st.session_state.step = "input"
    
    if st.session_state.step == "input":
        st.markdown('<div class="section-box"><h4>📝 إدخال بيانات النزيل</h4></div>', unsafe_allow_html=True)
        
        # الخانات الأساسية مع (key) لمنع "الهلوسة" واختفاء البيانات
        name = st.text_input("👤 الاسم واللقب الكامل *", key="k_name")
        
        col1, col2 = st.columns(2)
        nationality = col1.text_input("🇩🇿 الجنسية", value="جزائرية", key="k_nat")
        address = col2.text_input("🏠 العنوان الشخصي الكامل", key="k_addr")
        
        is_minor = st.checkbox("👶 هل النزيل قاصر؟", key="k_minor")
        g_name, g_rel = "", ""
        if is_minor:
            st.markdown('<div class="minor-tag">🛡️ بيانات ولي الأمر</div>', unsafe_allow_html=True)
            gm1, gm2 = st.columns(2)
            g_name = gm1.text_input("اسم ولي الأمر *", key="k_gname")
            g_rel = gm2.selectbox("صلة القرابة", ["أب", "أم", "أخ أكبر", "عم/خال", "مؤطر"], key="k_grel")

        st.markdown("---")
        # اختيار الغرفة والسرير
        c_w, c_r, c_b = st.columns(3)
        wing = c_w.selectbox("🏢 الجناح", ["جناح ذكور 👨", "جناح إناث 👩"], key="k_wing")
        room = c_r.selectbox("🚪 الغرفة", [f"غرفة {i:02d}" for i in range(1, 11)], key="k_room")
        
        # نظام الأسرة الشاغرة
        occ = get_occupied_beds(wing, room)
        all_beds = [f"سرير {i:02d}" for i in range(1, 7)]
        avail = [b for b in all_beds if b not in occ]
        
        if not avail:
            st.error("❌ الغرفة ممتلئة!")
            bed_num = None
        else:
            bed_num = c_b.selectbox("🛏️ السرير الشاغر", avail, key="k_bed")

        with st.expander("🛠️ بيانات الهوية والاتصال"):
            idt = st.selectbox("📄 نوع الوثيقة", ["بطاقة تعريف", "جواز سفر", "رخصة سياقة"], key="k_idt")
            idn = st.text_input("🔢 رقم الوثيقة *", key="k_idn")
            phone = st.text_input("📞 رقم الهاتف", key="k_phone")

        if st.button("📑 مراجعة الحجز", type="primary", use_container_width=True):
            if name and idn and bed_num:
                st.session_state.temp = {
                    "n":name, "nat":nationality, "adr":address, "w":wing, "r":room, "b":bed_num,
                    "it":idt, "in":idn, "ph":phone, "is_m":is_minor, "gn":g_name, "gr":g_rel
                }
                st.session_state.step = "review"
                st.rerun()
            else: st.error("يرجى ملء الاسم، رقم الوثيقة، واختيار سرير.")

    elif st.session_state.step == "review":
        d = st.session_state.temp
        st.markdown('<div class="section-box"><h4>👁️ مراجعة نهائية</h4></div>', unsafe_allow_html=True)
        st.info(f"النزيل: {d['n']} | الوثيقة: {d['it']} ({d['in']})")
        if d['is_m']: st.warning(f"الولي: {d['gn']} ({d['gr']})")
        
        col_b = st.columns(2)
        with col_b[0]:
            if st.button("✅ تأكيد وحفظ", type="primary", use_container_width=True):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO guests (name, nationality, address, id_type, id_num, phone, wing, room, bed_num, is_minor, guardian_name, guardian_rel, check_in) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                 (d['n'], d['nat'], d['adr'], d['it'], d['in'], d['ph'], d['w'], d['r'], d['b'], int(d['is_m']), d['gn'], d['gr'], str(date.today())))
                st.success("🎉 تم الحفظ بنجاح!")
                st.session_state.step = "input"; st.rerun()
        with col_b[1]:
            if st.button("✏️ تعديل", use_container_width=True):
                st.session_state.step = "input"; st.rerun()

# --- التوقيع الإبداعي المستقر ---
st.markdown(f"""
    <div style="text-align: center; margin-top: 50px; padding: 20px; border-top: 2px solid #eee;">
        <h2 style="font-family: 'Orbitron', sans-serif; color: #1e3c72; letter-spacing: 2px;">RIDHA MERZOUG LABS</h2>
        <p style="color: #00d4ff; font-weight: bold;">PREMIUM SYSTEM V2026</p>
    </div>
""", unsafe_allow_html=True)
