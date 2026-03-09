import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta

# ────────────────────────────────────────────────
#                إعداد الصفحة + CSS الملكي
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
        text-align: center; margin-bottom: 20px; 
        font-size: 1.35rem; font-weight: bold;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }

    /* لوحة الإحصائيات الملونة */
    .stat-container {
        display: flex; gap: 10px; margin-bottom: 20px; justify-content: space-between;
    }
    .stat-card {
        flex: 1; padding: 15px; border-radius: 10px; text-align: center; color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .stat-val { font-size: 1.7rem; font-weight: bold; display: block; }
    .stat-label { font-size: 0.85rem; opacity: 0.9; }

    .bed-box { 
        display: inline-block; width: 42px; height: 38px; margin: 4px; 
        border-radius: 6px; text-align: center; line-height: 38px; 
        color: white; font-size: 0.85rem; font-weight: bold; 
    }
    .free { background-color: #28a745; border-bottom: 3px solid #1e7e34; }
    .occupied { background-color: #dc3545; border-bottom: 3px solid #a71d2a; }
    
    .section-box {
        background: #f8f9fa; padding: 1rem; border-radius: 10px; 
        margin-bottom: 1.2rem; border-right: 5px solid #1e3c72;
    }

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
DB_FILE = 'youth_hostel_guelma_final.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS current_guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, birth_date TEXT, id_card TEXT UNIQUE, 
            wing TEXT, room TEXT, bed TEXT,
            check_in TEXT, check_out TEXT,
            is_minor TEXT, phone TEXT, purpose TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, birth_date TEXT, id_card TEXT, 
            phone TEXT, wing TEXT, room TEXT, bed TEXT,
            check_in TEXT, check_out TEXT
        )''')
        conn.commit()

init_db()

# ────────────────────────────────────────────────
#               بوابة الدخول
# ────────────────────────────────────────────────
if 'authenticated' not in st.session_state: st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<div class="official-header">وزارة الشباب والرياضة<br>مديرية الشباب والرياضة لولاية قالمة<br>ديوان مؤسسات الشباب</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title">نظام إدارة بيت الشباب محمدي يوسف</div>', unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        pwd = st.text_input("🔑 كلمة مرور النظام", type="password")
        if st.button("🔓 دخول للنظام", use_container_width=True):
            if pwd == "1234": st.session_state.authenticated = True; st.rerun()
            else: st.error("❌ كلمة المرور غير صحيحة")
    st.markdown(f'<div class="developer-footer">Developer <span style="color:#00d4ff;">®ridha_merzoug®</span> [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
    st.stop()

# ────────────────────────────────────────────────
#               الواجهة الرئيسية
# ────────────────────────────────────────────────
st.markdown('<div class="official-header">وزارة الشباب والرياضة | مديرية الشباب والرياضة | ديوان مؤسسات الشباب</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">نظام إدارة بيت الشباب محمدي يوسف - قالمة</div>', unsafe_allow_html=True)

# استرجاع الإحصائيات
with sqlite3.connect(DB_FILE) as conn:
    c = conn.cursor()
    today = str(date.today())
    g_count = c.execute("SELECT COUNT(*) FROM current_guests").fetchone()[0]
    exp_today = c.execute("SELECT COUNT(*) FROM current_guests WHERE check_out <= ?", (today,)).fetchone()[0]
    m_count = c.execute("SELECT COUNT(*) FROM current_guests WHERE is_minor='نعم'").fetchone()[0]
    b_avail = 76 - g_count

# لوحة الإحصائيات بالأيقونات 
st.markdown(f"""
    <div class="stat-container">
        <div class="stat-card" style="background:#1e3c72"><span class="stat-label">👥 المقيمون</span><span class="stat-val">{g_count}</span></div>
        <div class="stat-card" style="background:#28a745"><span class="stat-label">🛏️ أسرة شاغرة</span><span class="stat-val">{b_avail}</span></div>
        <div class="stat-card" style="background:#f39c12"><span class="stat-label">👶 قاصرون</span><span class="stat-val">{m_count}</span></div>
        <div class="stat-card" style="background:#dc3545"><span class="stat-label">🔔 تنبيه مغادرة</span><span class="stat-val">{exp_today}</span></div>
    </div>
""", unsafe_allow_html=True)

wings = {
    "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
    "جناح إناث": {"غرفة 06": 2, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد إناث 01": 3, "مرقد إناث 02": 4}
}

tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجل والمغادرة", "📂 الأرشيف والبحث"])

with tabs[0]:
    with st.expander("🔍 بحث سريع عن نزيل سابق (بالهوية)", expanded=False):
        id_search = st.text_input("أدخل رقم بطاقة التعريف لملء البيانات تلقائياً")
        with sqlite3.connect(DB_FILE) as conn:
            g_data = conn.execute("SELECT name, birth_date, phone FROM archive WHERE id_card=? ORDER BY id DESC LIMIT 1", (id_search,)).fetchone()
        if g_data: st.success(f"✅ تم العثور على بيانات النزيل: {g_data[0]}")

    with st.form("booking_form", clear_on_submit=True):
        st.markdown('<div class="section-box"><h4>📝 إدخال بيانات الحجز</h4></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم واللقب", value=g_data[0] if g_data else "")
            bday = st.date_input("تاريخ الميلاد", value=date.fromisoformat(g_data[1]) if g_data else date(1995, 1, 1))
            idn = st.text_input("رقم الهوية", value=id_search if id_search else "")
        with c2:
            phone = st.text_input("رقم الهاتف", value=g_data[2] if g_data else "")
            purp = st.selectbox("غرض الإقامة", ["سياحة", "عمل", "رياضة", "أخرى"])
            w_sel = st.selectbox("الجناح", list(wings.keys()))
        
        r_sel = st.selectbox("الغرفة / المرقد", list(wings[w_sel].keys()))
        with sqlite3.connect(DB_FILE) as conn:
            occ = [r[0] for r in conn.execute("SELECT bed FROM current_guests WHERE wing=? AND room=?", (w_sel, r_sel)).fetchall()]
        
        avail = [f"سرير {i+1}" for i in range(wings[w_sel][r_sel]) if f"سرير {i+1}" not in occ]
        b_sel = st.selectbox("السرير", avail if avail else ["❌ ممتلئة"])
        nights = st.number_input("عدد الليالي", min_value=1, value=1)
        
        if st.form_submit_button("💾 تأكيد وحفظ الحجز", use_container_width=True):
            if not name or "❌" in b_sel: st.error("⚠️ يرجى إكمال البيانات")
            else:
                try:
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("INSERT INTO current_guests (name, birth_date, id_card, wing, room, bed, check_in, check_out, is_minor, phone, purpose) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (name, str(bday), idn, w_sel, r_sel, b_sel, str(date.today()), str(date.today()+timedelta(days=nights)), "نعم" if (date.today().year - bday.year) < 18 else "لا", phone, purp))
                    st.success("✨ تم تسجيل الحجز بنجاح"); st.rerun()
                except: st.error("🚫 هذا النزيل مسجل حالياً!")

with tabs[1]:
    for w, rs in wings.items():
        st.markdown(f"### 🏢 {w}")
        for r, cnt in rs.items():
            with sqlite3.connect(DB_FILE) as conn:
                occ = [r[0] for r in conn.execute("SELECT bed FROM current_guests WHERE wing=? AND room=?", (w, r)).fetchall()]
            cols = st.columns([1, 6])
            cols[0].write(f"**{r}**")
            h = "".join([f'<div class="bed-box {"occupied" if f"سرير {i+1}" in occ else "free"}">{i+1}</div>' for i in range(cnt)])
            cols[1].markdown(h, unsafe_allow_html=True)

with tabs[2]:
    st.subheader("📋 قائمة المقيمين الحالية")
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT id, name, id_card, wing, room, bed, check_out FROM current_guests", conn)
    st.dataframe(df, use_container_width=True)
    if not df.empty:
        target = st.selectbox("اختر نزيل لتسجيل مغادرته", df['name'].tolist())
        if st.button("🔔 تسجيل مغادرة وإخلاء السرير"):
            with sqlite3.connect(DB_FILE) as conn:
                tid = df[df['name'] == target]['id'].values[0]
                guest = conn.execute("SELECT name, birth_date, id_card, phone, wing, room, bed, check_in, check_out FROM current_guests WHERE id=?", (tid,)).fetchone()
                conn.execute("INSERT INTO archive (name, birth_date, id_card, phone, wing, room, bed, check_in, check_out) VALUES (?,?,?,?,?,?,?,?,?)", guest)
                conn.execute("DELETE FROM current_guests WHERE id=?", (tid,))
            st.success("تم الإخلاء بنجاح"); st.rerun()

with tabs[3]:
    st.subheader("📂 البحث المتقدم في الأرشيف")
    c_s, c_d1, c_d2 = st.columns([2, 1, 1])
    term = c_s.text_input("🔍 ابحث بالاسم أو رقم الهوية")
    d_from = c_d1.date_input("🗓️ من تاريخ", date.today()-timedelta(days=30))
    d_to = c_d2.date_input("🗓️ إلى تاريخ", date.today())
    
    with sqlite3.connect(DB_FILE) as conn:
        res = pd.read_sql_query("SELECT * FROM archive WHERE (name LIKE ? OR id_card LIKE ?) AND check_in BETWEEN ? AND ?", 
                               conn, params=(f'%{term}%', f'%{term}%', str(d_from), str(d_to)))
    st.dataframe(res, use_container_width=True)
    st.download_button("📊 تحميل التقرير (Excel)", res.to_csv(index=False).encode('utf-8-sig'), "hostel_report.csv")

st.markdown(f'<div class="developer-footer">Developer <span style="color:#00d4ff;">®ridha_merzoug®</span> [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
