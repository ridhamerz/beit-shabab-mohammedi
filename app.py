import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta

# ────────────────────────────────────────────────
#                إعداد الصفحة + CSS
# ────────────────────────────────────────────────
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', 'Tahoma', sans-serif; direction: RTL; text-align: right; }
    
    .main-title { 
        background: linear-gradient(90deg, #1e3c72, #2a5298); 
        color: white; padding: 12px; border-radius: 10px; 
        text-align: center; margin-bottom: 20px; font-size: 1.35rem; font-weight: bold;
    }

    .stat-card {
        padding: 15px; border-radius: 10px; text-align: center; color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    .section-box {
        background: #ffffff; padding: 1.5rem; border-radius: 10px; 
        margin-bottom: 1.2rem; border-right: 5px solid #1e3c72;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* تنسيق أزرار الأسرة التفاعلية */
    .stButton > button { border-radius: 8px; font-weight: bold; }
    .bed-btn-free { background-color: #28a745 !important; color: white !important; }
    .bed-btn-occ { background-color: #dc3545 !important; color: white !important; cursor: not-allowed !important; }
    .bed-btn-selected { background-color: #007bff !important; color: white !important; border: 2px solid white !important; }

    .developer-footer { 
        background: #1e3c72; color: #ffffff; padding: 10px; 
        border-radius: 8px; text-align: center; margin-top: 50px; 
        font-size: 0.8rem; border: 1px solid #00d4ff;
    }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               إدارة البيانات
# ────────────────────────────────────────────────
DB_FILE = 'hostel_guelma_pro_v7.db'

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
    st.markdown('<div class="main-title">🔐 تسجيل الدخول للنظام</div>', unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول", use_container_width=True):
            if pwd == "1234": st.session_state.authenticated = True; st.rerun()
            else: st.error("❌ كلمة المرور خاطئة")
    st.stop()

# ────────────────────────────────────────────────
#               الواجهة الرئيسية
# ────────────────────────────────────────────────
st.markdown('<div class="main-title">نظام إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)

# إحصائيات علوية سريعة
with sqlite3.connect(DB_FILE) as conn:
    g_count = conn.execute("SELECT COUNT(*) FROM current_guests").fetchone()[0]
    exp_count = conn.execute("SELECT COUNT(*) FROM current_guests WHERE check_out <= ?", (str(date.today()),)).fetchone()[0]

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="stat-card" style="background:#1e3c72"><small>👥 المقيمون</small><br><b>{g_count}</b></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="stat-card" style="background:#28a745"><small>🛏️ أسرة شاغرة</small><br><b>{76 - g_count}</b></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="stat-card" style="background:#dc3545"><small>🔔 تنبيه مغادرة</small><br><b>{exp_count}</b></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="stat-card" style="background:#f39c12"><small>⭐ حالة النظام</small><br><b>نشط</b></div>', unsafe_allow_html=True)

wings = {
    "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
    "جناح إناث": {"غرفة 06": 2, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد إناث 01": 3, "مرقد إناث 02": 4}
}

tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 المغادرة", "📂 الأرشيف"])

# ────────────────────────────────────────────────
#               تبويب حجز جديد (المطور)
# ────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<div class="section-box"><h4>📝 استمارة الحجز الذكية</h4></div>', unsafe_allow_html=True)
    
    # 1. نظام البحث التلقائي (Auto-Fill)
    id_input = st.text_input("🔍 أدخل رقم الهوية (للبحث والملء التلقائي)", help="إذا كان النزيل مسجلاً سابقاً، ستمتلئ البيانات تلقائياً")
    
    with sqlite3.connect(DB_FILE) as conn:
        old_data = conn.execute("SELECT name, birth_date, phone, id_type FROM archive WHERE id_card=? ORDER BY id DESC LIMIT 1", (id_input,)).fetchone()
    
    if old_data:
        st.success(f"✅ تم التعرف على النزيل: {old_data[0]}")

    # استخدام session_state لحفظ البيانات ومنع ضياعها
    col1, col2 = st.columns(2)
    with col1:
        g_name = st.text_input("الاسم واللقب كامل", value=old_data[0] if old_data else "")
        g_id_type = st.selectbox("نوع الوثيقة", ["بطاقة تعريف وطنية", "جواز سفر", "رخصة سياقة"], index=["بطاقة تعريف وطنية", "جواز سفر", "رخصة سياقة"].index(old_data[3]) if old_data else 0)
        default_bday = date.fromisoformat(old_data[1]) if old_data else date(2000, 1, 1)
        g_bday = st.date_input("تاريخ الميلاد", value=default_bday)
    
    with col2:
        g_phone = st.text_input("رقم الهاتف", value=old_data[2] if old_data else "")
        g_purpose = st.selectbox("غرض الإقامة", ["سياحة", "عمل", "رياضة", "أخرى"])
        g_wing = st.selectbox("الجناح", list(wings.keys()))

    # 2. نظام القاصرين
    is_minor = "لا"
    minor_doc = "لا يوجد"
    if (date.today().year - g_bday.year) < 18:
        is_minor = "نعم"
        st.warning("⚠️ هذا النزيل قاصر")
        minor_doc = st.selectbox("وثيقة القاصر الإضافية", ["تصريح أبوي مصادق عليه", "حضور الولي الشرعي", "أمر بمهمة جماعي"])

    # 3. خريطة الأسرة التفاعلية
    st.markdown("---")
    st.subheader("🛏️ اختيار السرير (خريطة تفاعلية)")
    r_sel = st.selectbox("اختر الغرفة أولاً", list(wings[g_wing].keys()))
    
    with sqlite3.connect(DB_FILE) as conn:
        occupied = [r[0] for r in conn.execute("SELECT bed FROM current_guests WHERE wing=? AND room=?", (g_wing, r_sel)).fetchall()]
    
    total_beds = wings[g_wing][r_sel]
    cols = st.columns(8) # عرض الأسرة بشكل أفقي
    selected_bed = st.session_state.get('selected_bed', None)

    for i in range(total_beds):
        bed_label = f"سرير {i+1}"
        is_occ = bed_label in occupied
        
        btn_type = "secondary"
        if is_occ:
            cols[i].button(f"🚫 {i+1}", key=f"btn_{i}", disabled=True, help="مشغول")
        else:
            if st.session_state.get('selected_bed') == bed_label:
                if cols[i].button(f"✅ {i+1}", key=f"btn_{i}", type="primary"):
                    st.session_state.selected_bed = bed_label
            else:
                if cols[i].button(f"🟢 {i+1}", key=f"btn_{i}"):
                    st.session_state.selected_bed = bed_label
                    st.rerun()

    if st.session_state.get('selected_bed'):
        st.info(f"السرير المختار حالياً: **{st.session_state.selected_bed}** في **{r_sel}**")

    days = st.number_input("عدد الليالي", min_value=1, value=1)

    # 4. زر التأكيد مع منع ضياع البيانات
    if st.button("💾 تأكيد وحفظ الحجز النهائي", use_container_width=True, type="primary"):
        if not g_name or not id_input or not st.session_state.get('selected_bed'):
            st.error("❌ خطأ: يرجى ملء الاسم ورقم الهوية واختيار سرير من الخريطة!")
        else:
            try:
                with sqlite3.connect(DB_FILE) as conn:
                    conn.execute("INSERT INTO current_guests (name, birth_date, id_type, id_card, wing, room, bed, check_in, check_out, is_minor, minor_doc, phone, purpose) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                 (g_name, str(g_bday), g_id_type, id_input, g_wing, r_sel, st.session_state.selected_bed, str(date.today()), str(date.today()+timedelta(days=days)), is_minor, minor_doc, g_phone, g_purpose))
                st.success(f"✨ تم تسجيل النزيل {g_name} بنجاح!")
                st.session_state.selected_bed = None # تصفير السرير فقط عند النجاح
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("🚫 هذا النزيل موجود حالياً في المؤسسة!")

# --- بقية التبويبات مع الحفاظ على التنسيق ---
with tabs[1]:
    for w, rs in wings.items():
        st.markdown(f"### 🏢 {w}")
        for r, cnt in rs.items():
            with sqlite3.connect(DB_FILE) as conn:
                occ = [r[0] for r in conn.execute("SELECT bed FROM current_guests WHERE wing=? AND room=?", (w, r)).fetchall()]
            c_r, c_b = st.columns([1, 6])
            c_r.write(f"**{r}**")
            h = "".join([f'<div style="display:inline-block; width:35px; height:35px; margin:3px; border-radius:5px; background:{"#dc3545" if f"سرير {i+1}" in occ else "#28a745"}; color:white; text-align:center; line-height:35px; font-weight:bold;">{i+1}</div>' for i in range(cnt)])
            c_b.markdown(h, unsafe_allow_html=True)

with tabs[2]:
    st.subheader("📋 مغادرة نزيل")
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT id, name, id_card, wing, room, bed, check_out FROM current_guests", conn)
    st.dataframe(df, use_container_width=True)
    if not df.empty:
        target = st.selectbox("اختر النزيل المغادر", df['name'].tolist())
        if st.button("🔔 تأكيد المغادرة وإخلاء السرير"):
            with sqlite3.connect(DB_FILE) as conn:
                tid = df[df['name'] == target]['id'].values[0]
                guest = conn.execute("SELECT name, birth_date, id_type, id_card, phone, wing, room, bed, check_in, check_out FROM current_guests WHERE id=?", (tid,)).fetchone()
                conn.execute("INSERT INTO archive (name, birth_date, id_type, id_card, phone, wing, room, bed, check_in, check_out) VALUES (?,?,?,?,?,?,?,?,?,?)", guest)
                conn.execute("DELETE FROM current_guests WHERE id=?", (tid,))
            st.success("تمت العملية بنجاح"); st.rerun()

with tabs[3]:
    st.subheader("📂 أرشيف المؤسسة")
    term = st.text_input("🔍 بحث بالاسم أو الهوية")
    with sqlite3.connect(DB_FILE) as conn:
        res = pd.read_sql_query("SELECT * FROM archive WHERE name LIKE ? OR id_card LIKE ?", conn, params=(f'%{term}%', f'%{term}%'))
    st.dataframe(res, use_container_width=True)

st.markdown(f'<div class="developer-footer">Developer <span style="color:#00d4ff;">®ridha_merzoug®</span> [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
