import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta

# ────────────────────────────────────────────────
#                إعداد الصفحة + CSS الملكي المعتمد
# ────────────────────────────────────────────────
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', 'Tahoma', sans-serif; direction: RTL; text-align: right; }
    
    .official-header {
        text-align: center; color: #1e3c72; font-size: 0.85rem;
        font-weight: bold; line-height: 1.4; margin-bottom: 5px;
    }
    
    .main-title { 
        background: linear-gradient(90deg, #1e3c72, #2a5298); 
        color: white; padding: 12px; border-radius: 10px; 
        text-align: center; margin-bottom: 20px; font-size: 1.35rem; font-weight: bold;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }

    .stat-container {
        display: flex; gap: 10px; margin-bottom: 20px; justify-content: space-between;
    }
    .stat-card {
        flex: 1; padding: 15px; border-radius: 10px; text-align: center; color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .stat-val { font-size: 1.7rem; font-weight: bold; display: block; }
    .stat-label { font-size: 0.85rem; opacity: 0.9; }

    .section-box {
        background: #ffffff; padding: 1.5rem; border-radius: 10px; 
        margin-bottom: 1.2rem; border-right: 5px solid #1e3c72;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    .bed-box { 
        display: inline-block; width: 35px; height: 35px; margin: 3px; 
        border-radius: 5px; text-align: center; line-height: 35px; 
        color: white; font-size: 0.85rem; font-weight: bold; 
    }

    .developer-footer { 
        background: #1e3c72; color: #ffffff; padding: 10px; 
        border-radius: 8px; text-align: center; margin-top: 50px; 
        font-size: 0.8rem; border: 1px solid #00d4ff;
    }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               إدارة البيانات (v8 المستقرة)
# ────────────────────────────────────────────────
DB_FILE = 'hostel_guelma_v8_stable.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS current_guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, birth_date TEXT, id_type TEXT, id_card TEXT UNIQUE, 
            wing TEXT, room TEXT, bed TEXT, check_in TEXT, check_out TEXT,
            is_minor TEXT, minor_doc TEXT, phone TEXT, purpose TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, birth_date TEXT, id_type TEXT, id_card TEXT, 
            phone TEXT, wing TEXT, room TEXT, bed TEXT, check_in TEXT, check_out TEXT
        )''')
        conn.commit()

init_db()

# ────────────────────────────────────────────────
#               بوابة الدخول
# ────────────────────────────────────────────────
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.markdown('<div class="official-header">🇩🇿 وزارة الشباب والرياضة<br>مديرية الشباب والرياضة لولاية قالمة</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title">🔐 تسجيل الدخول للنظام</div>', unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        pwd = st.text_input("🔑 كلمة المرور", type="password")
        if st.button("🔓 دخول للنظام", use_container_width=True):
            if pwd == "1234": st.session_state.authenticated = True; st.rerun()
            else: st.error("❌ كلمة المرور خاطئة")
    st.stop()

# ────────────────────────────────────────────────
#               الواجهة الرئيسية
# ────────────────────────────────────────────────
st.markdown('<div class="official-header">🇩🇿 وزارة الشباب والرياضة | مديرية الشباب والرياضة | ديوان مؤسسات الشباب</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🏢 نظام إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)

with sqlite3.connect(DB_FILE) as conn:
    g_count = conn.execute("SELECT COUNT(*) FROM current_guests").fetchone()[0]
    b_avail = 76 - g_count

st.markdown(f"""
    <div class="stat-container">
        <div class="stat-card" style="background:#1e3c72"><span class="stat-label">👥 المقيمون حالياً</span><span class="stat-val">{g_count}</span></div>
        <div class="stat-card" style="background:#28a745"><span class="stat-label">🛏️ أسرة شاغرة</span><span class="stat-val">{b_avail}</span></div>
        <div class="stat-card" style="background:#f39c12"><span class="stat-label">⭐ حالة النظام</span><span class="stat-val">متصل ✅</span></div>
    </div>
""", unsafe_allow_html=True)

wings = {
    "جناح ذكور 👨": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
    "جناح إناث 👩": {"غرفة 06": 2, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد إناث 01": 3, "مرقد إناث 02": 4}
}

tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف"])

# ────────────────────────────────────────────────
#               تبويب حجز جديد
# ────────────────────────────────────────────────
with tabs[0]:
    if 'booking_success' not in st.session_state:
        st.session_state.booking_success = False

    if st.session_state.booking_success:
        st.balloons()
        st.success(f"🎉 تم تسجيل النزيل **{st.session_state.last_guest}** بنجاح!")
        st.info(f"📍 الموقع: **{st.session_state.last_room}** | **{st.session_state.last_bed}**")
        if st.button("➕ القيام بحجز جديد", type="primary", use_container_width=True):
            st.session_state.booking_success = False
            st.session_state.selected_bed = None
            st.rerun()
    else:
        st.markdown('<div class="section-box"><h4>📝 استمارة تسجيل نزيل</h4></div>', unsafe_allow_html=True)
        
        id_card_val = st.text_input("🪪 رقم بطاقة الهوية / جواز السفر")
        
        with sqlite3.connect(DB_FILE) as conn:
            old_data = conn.execute("SELECT name, birth_date, phone, id_type FROM archive WHERE id_card=? ORDER BY id DESC LIMIT 1", (id_card_val,)).fetchone()
        
        if old_data: st.info(f"💡 نزيل سابق: {old_data[0]}")

        col1, col2 = st.columns(2)
        with col1:
            g_name = st.text_input("👤 الاسم واللقب", value=old_data[0] if old_data else "")
            g_id_type = st.selectbox("📄 نوع الوثيقة", ["بطاقة تعريف وطنية", "جواز سفر", "رخصة سياقة"], 
                                   index=["بطاقة تعريف وطنية", "جواز سفر", "رخصة سياقة"].index(old_data[3]) if old_data else 0)
            def_bday = date.fromisoformat(old_data[1]) if old_data else date(2000, 1, 1)
            g_bday = st.date_input("📅 تاريخ الميلاد", value=def_bday)
        
        with col2:
            g_phone = st.text_input("📞 رقم الهاتف", value=old_data[2] if old_data else "")
            g_purpose = st.selectbox("🎯 غرض الزيارة", ["سياحة", "عمل", "رياضة", "أخرى"])
            g_wing = st.selectbox("🏢 الجناح", list(wings.keys()))

        is_minor = "لا"; minor_doc = "لا يوجد"
        if (date.today().year - g_bday.year) < 18:
            is_minor = "نعم"
            st.warning("⚠️ تنبيه: النزيل قاصر")
            minor_doc = st.selectbox("📎 وثيقة القاصر", ["تصريح أبوي مصادق عليه", "حضور الولي الشرعي", "أمر بمهمة جماعي"])

        st.markdown("---")
        st.subheader("🛏️ خريطة الأسرة")
        r_sel = st.selectbox("🚪 اختر الغرفة", list(wings[g_wing].keys()))
        
        with sqlite3.connect(DB_FILE) as conn:
            occ = [r[0] for r in conn.execute("SELECT bed FROM current_guests WHERE wing=? AND room=?", (g_wing, r_sel)).fetchall()]
        
        cols = st.columns(8)
        for i in range(wings[g_wing][r_sel]):
            b_lbl = f"سرير {i+1}"
            if b_lbl in occ: 
                cols[i].button(f"🚫 {i+1}", key=f"bk_{i}", disabled=True)
            else:
                if st.session_state.get('selected_bed') == b_lbl:
                    if cols[i].button(f"✅ {i+1}", key=f"bk_{i}", type="primary"): 
                        st.session_state.selected_bed = b_lbl
                else:
                    if cols[i].button(f"🟢 {i+1}", key=f"bk_{i}"): 
                        st.session_state.selected_bed = b_lbl
                        st.rerun()

        days = st.number_input("🌙 عدد الليالي", min_value=1, value=1)

        if st.button("💾 تأكيد وحفظ الحجز", use_container_width=True, type="primary"):
            if not g_name or not id_card_val or not st.session_state.get('selected_bed'):
                st.error("⚠️ يرجى إكمال البيانات واختيار السرير")
            else:
                try:
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO current_guests (name, birth_date, id_type, id_card, wing, room, bed, check_in, check_out, is_minor, minor_doc, phone, purpose) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                     (g_name, str(g_bday), g_id_type, id_card_val, g_wing, r_sel, st.session_state.selected_bed, str(date.today()), str(date.today()+timedelta(days=days)), is_minor, minor_doc, g_phone, g_purpose))
                    
                    st.session_state.booking_success = True
                    st.session_state.last_guest = g_name
                    st.session_state.last_room = r_sel
                    st.session_state.last_bed = st.session_state.selected_bed
                    st.rerun()
                except: st.error("🚫 النزيل مسجل حالياً!")

# ────────────────────────────────────────────────
#               تبويب حالة الغرف
# ────────────────────────────────────────────────
with tabs[1]:
    for w, rs in wings.items():
        st.markdown(f"### 🏢 {w}")
        for r, cnt in rs.items():
            with sqlite3.connect(DB_FILE) as conn:
                occ_beds = [r[0] for r in conn.execute("SELECT bed FROM current_guests WHERE wing=? AND room=?", (w, r)).fetchall()]
            cr, cb = st.columns([1, 6])
            cr.write(f"**🚪 {r}**")
            h = "".join([f'<div class="bed-box" style="background:{"#dc3545" if f"سرير {i+1}" in occ_beds else "#28a745"}">{i+1}</div>' for i in range(cnt)])
            cb.markdown(h, unsafe_allow_html=True)

st.markdown(f'<div class="developer-footer">Developer <span style="color:#00d4ff;">®ridha_merzoug®</span> [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
