import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta

# ────────────────────────────────────────────────
#                إعداد الصفحة + التصميم الملكي V2026
# ────────────────────────────────────────────────
st.set_page_config(page_title="منظومة محمدي يوسف - قالمة V2026", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&family=Orbitron:wght@500;900&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { 
        background: linear-gradient(135deg, #000428, #004e92); 
        color: white; padding: 22px; border-radius: 18px; text-align: center; margin-bottom: 28px; 
        font-size: 1.9rem; font-weight: bold; box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    .section-box { 
        background: #ffffff; padding: 24px; border-radius: 16px; 
        border-right: 7px solid #004e92; box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-bottom: 25px; 
    }
    .minor-tag { background: #fff9db; padding: 14px; border-radius: 12px; border: 2px dashed #fcc419; margin: 18px 0; font-weight: bold; }
    .success-box { background: #d4edda; color: #155724; padding: 18px; border-radius: 12px; border: 1px solid #c3e6cb; text-align: center; font-weight: bold; font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               قاعدة البيانات الرسمية V2026
# ────────────────────────────────────────────────
DB_FILE = 'hostel_guelma_official_v2026.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, nationality TEXT, address TEXT,
            id_type TEXT, id_num TEXT UNIQUE, phone TEXT,
            wing TEXT, room TEXT, bed_num TEXT,
            check_in TEXT, check_out TEXT, nights INTEGER,
            status TEXT DEFAULT 'مقيم',
            is_minor INTEGER DEFAULT 0,
            guardian_name TEXT, guardian_rel TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, id_num TEXT, wing TEXT, room TEXT, bed_num TEXT,
            check_in TEXT, check_out TEXT, nights INTEGER
        )''')

init_db()

# ────────────────────────────────────────────────
#               دوال مساعدة آمنة
# ────────────────────────────────────────────────
def get_occupied_beds(wing, room):
    with sqlite3.connect(DB_FILE) as conn:
        res = conn.execute("SELECT bed_num FROM guests WHERE wing=? AND room=? AND status='مقيم'", (wing, room)).fetchall()
        return [r[0] for r in res]

def checkout_guest(guest_id):
    with sqlite3.connect(DB_FILE) as conn:
        guest = conn.execute("SELECT name, id_num, wing, room, bed_num, check_in, nights FROM guests WHERE id=?", (guest_id,)).fetchone()
        if guest:
            check_out = date.today()
            nights = (check_out - date.fromisoformat(guest[5])).days
            conn.execute("""INSERT INTO archive (name, id_num, wing, room, bed_num, check_in, check_out, nights) 
                            VALUES (?,?,?,?,?,?,?,?)""",
                        (guest[0], guest[1], guest[2], guest[3], guest[4], guest[5], str(check_out), nights))
            conn.execute("UPDATE guests SET status='مغادر', check_out=? WHERE id=?", (str(check_out), guest_id))

# ────────────────────────────────────────────────
#               الواجهة الرئيسية + الإحصائيات
# ────────────────────────────────────────────────
st.markdown('<div class="main-title">منظومة إدارة بيت الشباب محمدي يوسف - قالمة<br><small>الإصدار الرسمي V2026</small></div>', unsafe_allow_html=True)

with sqlite3.connect(DB_FILE) as conn:
    total = conn.execute("SELECT COUNT(*) FROM guests WHERE status='مقيم'").fetchone()[0]
    minors = conn.execute("SELECT COUNT(*) FROM guests WHERE is_minor=1 AND status='مقيم'").fetchone()[0]
    today_in = conn.execute("SELECT COUNT(*) FROM guests WHERE check_in=?", (str(date.today()),)).fetchone()[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("المقيمون حاليًا", total, delta=f"{total} نزيل")
col2.metric("القاصرون", minors, delta=f"+{minors} تحت 18")
col3.metric("الداخلون اليوم", today_in)
col4.metric("الأسرة الشاغرة", 76 - total, delta=f"{76-total} من 76")

tab1, tab2, tab3 = st.tabs(["حجز جديد", "السجلات والبحث", "التصدير"])

# ───────────────────── تبويب الحجز الجديد ─────────────────────
with tab1:
    if 'step' not in st.session_state: st.session_state.step = "input"
    
    if st.session_state.step == "input":
        st.markdown('<div class="section-box"><h3>إدخال بيانات النزيل</h3></div>', unsafe_allow_html=True)
        
        name = st.text_input("الاسم واللقب الكامل *", key="k_name")
        col1, col2 = st.columns(2)
        nationality = col1.text_input("الجنسية", value="جزائرية", key="k_nat")
        address = col2.text_input("العنوان الكامل", key="k_addr")
        
        is_minor = st.checkbox("هل النزيل قاصر؟", key="k_minor")
        g_name, g_rel = "", ""
        if is_minor:
            st.markdown('<div class="minor-tag">بيانات ولي الأمر مطلوبة</div>', unsafe_allow_html=True)
            gm1, gm2 = st.columns(2)
            g_name = gm1.text_input("اسم ولي الأمر *", key="k_gname")
            g_rel = gm2.selectbox("صلة القرابة", ["أب", "أم", "أخ أكبر", "عم/خال", "وصي قانوني"], key="k_grel")

        c_w, c_r = st.columns(2)
        wing = c_w.selectbox("الجناح", ["جناح ذكور", "جناح إناث"], key="k_wing")
        room = c_r.selectbox("الغرفة", [f"غرفة {i:02d}" for i in range(1, 11)], key="k_room")
        
        occ = get_occupied_beds(wing, room)
        avail = [f"سرير {i:02d}" for i in range(1, 7) if f"سرير {i:02d}" not in occ]
        
        if not avail:
            st.error("الغرفة ممتلئة حاليًا!")
        else:
            bed_num = st.selectbox("السرير المتوفر", avail, key="k_bed")
            st.success(f"تم حجز {bed_num}")

        nights = st.number_input("عدد الليالي", min_value=1, value=1, key="k_nights")

        with st.expander("بيانات الهوية والاتصال"):
            idt = st.selectbox("نوع الوثيقة", ["بطاقة التعريف الوطنية", "جواز السفر", "رخصة السياقة"], key="k_idt")
            idn = st.text_input("رقم الوثيقة *", key="k_idn")
            phone = st.text_input("رقم الهاتف", key="k_phone")

        if st.button("مراجعة الحجز", type="primary", use_container_width=True):
            if name and idn and bed_num:
                st.session_state.temp = {
                    "name":name, "nationality":nationality, "address":address, "wing":wing, "room":room,
                    "bed_num":bed_num, "nights":nights, "id_type":idt, "id_num":idn, "phone":phone,
                    "is_minor":is_minor, "guardian_name":g_name, "guardian_rel":g_rel
                }
                st.session_state.step = "review"
                st.rerun()
            else:
                st.error("يرجى ملء الحقول المطلوبة")

    elif st.session_state.step == "review":
        d = st.session_state.temp
        st.markdown('<div class="section-box"><h3>مراجعة نهائية</h3></div>', unsafe_allow_html=True)
        st.write(f"**النزيل**: {d['name']}")
        st.write(f"**الموقع**: {d['wing']} → {d['room']} → {d['bed_num']}")
        st.write(f"**الوثيقة**: {d['id_type']} - {d['id_num']}")
        st.write(f"**المدة**: {d['nights']} ليالي")
        if d['is_minor']: st.warning(f"قاصر - الولي: {d['guardian_name']} ({d['guardian_rel']})")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("تأكيد الحجز", type="primary", use_container_width=True):
                check_out = date.today() + timedelta(days=d['nights'])
                with sqlite3.connect(DB_FILE) as conn:
                    try:
                        conn.execute("""INSERT INTO guests 
                            (name, nationality, address, id_type, id_num, phone, wing, room, bed_num, 
                             check_in, check_out, nights, is_minor, guardian_name, guardian_rel)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (d['name'], d['nationality'], d['address'], d['id_type'], d['id_num'], d['phone'],
                             d['wing'], d['room'], d['bed_num'], str(date.today()), str(check_out),
                             d['nights'], int(d['is_minor']), d['guardian_name'], d['guardian_rel']))
                        st.balloons()
                        st.success("تم تسجيل النزيل بنجاح!")
                        st.session_state.step = "input"
                        if 'temp' in st.session_state: del st.session_state.temp
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("رقم الوثيقة مكرر أو النزيل موجود مسبقًا")

        with c2:
            if st.button("تعديل", use_container_width=True):
                st.session_state.step = "input"
                st.rerun()

# ───────────────────── تبويب السجلات والبحث (آمن 100%) ─────────────────────
with tab2:
    st.markdown('<div class="section-box"><h3>النزلاء المقيمون</h3></div>', unsafe_allow_html=True)
    
    search = st.text_input("ابحث بالاسم أو رقم الوثيقة أو السرير", key="search")

    with sqlite3.connect(DB_FILE) as conn:
        if search:
            query = """
                SELECT id, name, wing, room, bed_num, check_in, id_num, phone
                FROM guests WHERE status='مقيم'
                  AND (name LIKE ? OR id_num LIKE ? OR bed_num LIKE ? OR phone LIKE ?)
                ORDER BY check_in DESC
            """
            df = pd.read_sql_query(query, conn, params=(f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'))
        else:
            df = pd.read_sql_query("SELECT id, name, wing, room, bed_num, check_in, id_num, phone FROM guests WHERE status='مقيم' ORDER BY check_in DESC", conn)

    if df.empty:
        st.info("لا يوجد نزلاء حاليًا")
    else:
        for _, row in df.iterrows():
            with st.expander(f"{row['name']} • {row['wing']} • {row['room']} • {row['bed_num']} • منذ: {row['check_in']}"):
                col1, col2 = st.columns([3, 1])
                col1.write(f"**رقم الوثيقة**: {row['id_num']}")
                col1.write(f"**الهاتف**: {row['phone'] or 'غير مدخل'}")
                if col2.button("تسجيل خروج", key=f"out_{row['id']}"):
                    checkout_guest(row['id'])
                    st.success(f"تم تسجيل خروج {row['name']}")
                    st.rerun()

# ───────────────────── تبويب التصدير ─────────────────────
with tab3:
    st.markdown('<div class="section-box"><h3>تصدير البيانات</h3></div>', unsafe_allow_html=True)
    with sqlite3.connect(DB_FILE) as conn:
        df_export = pd.read_sql_query("SELECT * FROM guests WHERE status='مقيم'", conn)
    
    if not df_export.empty:
        csv = df_export.to_csv(index=False).encode('utf-8-sig')
        st.download_button("تحميل قائمة النزلاء (CSV)", data=csv, 
                          file_name=f"نزلاء_محمدي_يوسف_{date.today()}.csv", mime="text/csv")
    else:
        st.info("لا توجد بيانات للتصدير")

# ────────────────────────────────────────────────
#               التوقيع الأسطوري الرسمي
# ────────────────────────────────────────────────
st.markdown(f"""
    <div style="text-align: center; margin-top: 80px; padding: 35px; background: linear-gradient(135deg, #000428, #004e92); border-radius: 25px; color: white;">
        <h1 style="font-family: 'Orbitron', sans-serif; letter-spacing: 5px; margin:0; color:#00d4ff;">RIDHA MERZOUG LABS</h1>
        <h3 style="margin:15px 0; color:white;">PREMIUM HOSTEL SYSTEM V2026</h3>
        <p style="margin:5px; opacity:0.9;">© 2026 - وزارة الشباب والرياضة - ولاية قالمة</p>
        <p style="margin:5px; font-weight: bold; color:#00ff9d;">تمت البرمجة بحب من  & رضا</p>
    </div>
""", unsafe_allow_html=True)
