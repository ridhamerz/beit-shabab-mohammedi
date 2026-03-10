import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta

# ────────────────────────────────────────────────
#                الثوابت الرسمية V2026.1
# ────────────────────────────────────────────────
TOTAL_BEDS = 76
BEDS_PER_ROOM = 6
WINGS = ["جناح ذكور", "جناح إناث"]
ROOMS = [f"غرفة {i:02d}" for i in range(1, 11)]
DB_FILE = 'hostel_guelma_official_v2026.db'
ADMIN_PASSWORD = "guelma2026"          # غيّرها فوراً لكلمة سر قوية!

# ────────────────────────────────────────────────
#                إعداد الصفحة + التصميم
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
#                حماية الدخول
# ────────────────────────────────────────────────
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<div class="main-title">🔐 الدخول إلى منظومة محمدي يوسف - قالمة</div>', unsafe_allow_html=True)
    pw = st.text_input("كلمة السر الإدارية", type="password", key="admin_pw")
    if st.button("تسجيل الدخول", type="primary", use_container_width=True):
        if pw == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.success("✅ مرحبا بك في المنظومة الرسمية V2026!")
            st.rerun()
        else:
            st.error("❌ كلمة السر خاطئة")
    st.stop()

# ────────────────────────────────────────────────
#               قاعدة البيانات + اتصال محسن
# ────────────────────────────────────────────────
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
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
    conn.commit()

init_db()

# ────────────────────────────────────────────────
#               دوال مساعدة
# ────────────────────────────────────────────────
def get_occupied_beds(wing, room):
    conn = get_db_connection()
    res = conn.execute("SELECT bed_num FROM guests WHERE wing=? AND room=? AND status='مقيم'", (wing, room)).fetchall()
    return [r[0] for r in res]

def checkout_guest(guest_id):
    conn = get_db_connection()
    guest = conn.execute("SELECT name, id_num, wing, room, bed_num, check_in, nights FROM guests WHERE id=?", (guest_id,)).fetchone()
    if guest:
        check_out = date.today()
        nights = (check_out - date.fromisoformat(guest[5])).days
        conn.execute("""INSERT INTO archive (name, id_num, wing, room, bed_num, check_in, check_out, nights) 
                        VALUES (?,?,?,?,?,?,?,?)""",
                    (guest[0], guest[1], guest[2], guest[3], guest[4], guest[5], str(check_out), nights))
        conn.execute("UPDATE guests SET status='مغادر', check_out=? WHERE id=?", (str(check_out), guest_id))
        conn.commit()

# ────────────────────────────────────────────────
#               الواجهة الرئيسية + الإحصائيات
# ────────────────────────────────────────────────
st.markdown('<div class="main-title">منظومة إدارة بيت الشباب محمدي يوسف - قالمة<br><small>الإصدار الرسمي V2026.1</small></div>', unsafe_allow_html=True)

conn = get_db_connection()
total = conn.execute("SELECT COUNT(*) FROM guests WHERE status='مقيم'").fetchone()[0]
minors = conn.execute("SELECT COUNT(*) FROM guests WHERE is_minor=1 AND status='مقيم'").fetchone()[0]
today_in = conn.execute("SELECT COUNT(*) FROM guests WHERE check_in=?", (str(date.today()),)).fetchone()[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("المقيمون حاليًا", total, delta=f"{total} نزيل")
col2.metric("القاصرون", minors, delta=f"+{minors} تحت 18")
col3.metric("الداخلون اليوم", today_in)
col4.metric("الأسرة الشاغرة", TOTAL_BEDS - total, delta=f"{TOTAL_BEDS-total} من {TOTAL_BEDS}")

tab1, tab2, tab3 = st.tabs(["حجز جديد", "السجلات والبحث", "التصدير"])

# ───────────────────── تبويب الحجز الجديد (يدعم التعديل) ─────────────────────
with tab1:
    if 'step' not in st.session_state:
        st.session_state.step = "input"
    if 'is_edit' not in st.session_state:
        st.session_state.is_edit = False
    if 'edit_id_temp' not in st.session_state:
        st.session_state.edit_id_temp = None

    # تحميل بيانات النزيل للتعديل
    if 'edit_id' in st.session_state and st.session_state.edit_id is not None:
        edit_id = st.session_state.edit_id
        row = conn.execute("SELECT * FROM guests WHERE id=?", (edit_id,)).fetchone()
        if row:
            st.session_state.k_name = row[1]
            st.session_state.k_nat = row[2]
            st.session_state.k_addr = row[3]
            st.session_state.k_idt = row[4]
            st.session_state.k_idn = row[5]
            st.session_state.k_phone = row[6]
            st.session_state.k_wing = row[7]
            st.session_state.k_room = row[8]
            st.session_state.k_bed = row[9]
            st.session_state.k_nights = row[12]
            st.session_state.k_minor = bool(row[14])
            if st.session_state.k_minor:
                st.session_state.k_gname = row[15]
                st.session_state.k_grel = row[16]
            st.session_state.is_edit = True
            st.session_state.edit_id_temp = edit_id
            del st.session_state.edit_id

    if st.session_state.step == "input":
        st.markdown(f'<div class="section-box"><h3>{"تعديل بيانات النزيل" if st.session_state.is_edit else "إدخال بيانات النزيل"}</h3></div>', unsafe_allow_html=True)
        
        name = st.text_input("الاسم واللقب الكامل *", key="k_name")
        col1, col2 = st.columns(2)
        nationality = col1.text_input("الجنسية", value="جزائرية", key="k_nat")
        address = col2.text_input("العنوان الكامل", key="k_addr")
        
        is_minor = st.checkbox("هل النزيل قاصر؟", key="k_minor")
        g_name = g_rel = ""
        if is_minor:
            st.markdown('<div class="minor-tag">بيانات ولي الأمر مطلوبة</div>', unsafe_allow_html=True)
            gm1, gm2 = st.columns(2)
            g_name = gm1.text_input("اسم ولي الأمر *", key="k_gname")
            g_rel = gm2.selectbox("صلة القرابة", ["أب", "أم", "أخ أكبر", "عم/خال", "وصي قانوني"], key="k_grel")

        c_w, c_r = st.columns(2)
        wing = c_w.selectbox("الجناح", WINGS, key="k_wing")
        room = c_r.selectbox("الغرفة", ROOMS, key="k_room")
        
        occ = get_occupied_beds(wing, room)
        avail = [f"سرير {i:02d}" for i in range(1, BEDS_PER_ROOM + 1) if f"سرير {i:02d}" not in occ]
        
        if not avail:
            st.error("الغرفة ممتلئة حاليًا!")
        else:
            bed_num = st.selectbox("السرير المتوفر", avail, key="k_bed")
            st.success(f"تم اختيار {bed_num}")

        nights = st.number_input("عدد الليالي", min_value=1, value=1, key="k_nights")

        with st.expander("بيانات الهوية والاتصال"):
            idt = st.selectbox("نوع الوثيقة", ["بطاقة التعريف الوطنية", "جواز السفر", "رخصة السياقة"], key="k_idt")
            idn = st.text_input("رقم الوثيقة *", key="k_idn")
            phone = st.text_input("رقم الهاتف", key="k_phone")

        btn_text = "مراجعة التعديل" if st.session_state.is_edit else "مراجعة الحجز"
        if st.button(btn_text, type="primary", use_container_width=True):
            if name and idn and 'k_bed' in st.session_state:
                st.session_state.temp = {
                    "name": name, "nationality": nationality, "address": address, "wing": wing, "room": room,
                    "bed_num": st.session_state.k_bed, "nights": nights, "id_type": idt, "id_num": idn, "phone": phone,
                    "is_minor": is_minor, "guardian_name": g_name, "guardian_rel": g_rel
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
        if d['is_minor']:
            st.warning(f"قاصر - الولي: {d['guardian_name']} ({d['guardian_rel']})")

        if d['is_minor'] and not d['guardian_name']:
            st.error("يجب إدخال بيانات ولي الأمر للقاصر!")
            st.stop()

        c1, c2 = st.columns(2)
        with c1:
            btn_text = "تحديث بيانات النزيل" if st.session_state.is_edit else "تأكيد الحجز"
            if st.button(btn_text, type="primary", use_container_width=True):
                # منع الحجز المزدوج
                occupied = get_occupied_beds(d['wing'], d['room'])
                if d['bed_num'] in occupied and not st.session_state.is_edit:
                    st.error("❌ السرير تم حجزه من طرف شخص آخر في نفس اللحظة!")
                    st.stop()

                conn = get_db_connection()
                check_out_date = date.today() + timedelta(days=d['nights'])
                try:
                    if st.session_state.is_edit:
                        conn.execute("""UPDATE guests SET name=?, nationality=?, address=?, id_type=?, id_num=?, 
                                      phone=?, wing=?, room=?, bed_num=?, check_in=?, check_out=?, nights=?, 
                                      is_minor=?, guardian_name=?, guardian_rel=? WHERE id=?""",
                            (d['name'], d['nationality'], d['address'], d['id_type'], d['id_num'], d['phone'],
                             d['wing'], d['room'], d['bed_num'], str(date.today()), str(check_out_date),
                             d['nights'], int(d['is_minor']), d['guardian_name'], d['guardian_rel'], st.session_state.edit_id_temp))
                        st.success("✅ تم تحديث بيانات النزيل بنجاح!")
                    else:
                        conn.execute("""INSERT INTO guests 
                            (name, nationality, address, id_type, id_num, phone, wing, room, bed_num, 
                             check_in, check_out, nights, is_minor, guardian_name, guardian_rel)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (d['name'], d['nationality'], d['address'], d['id_type'], d['id_num'], d['phone'],
                             d['wing'], d['room'], d['bed_num'], str(date.today()), str(check_out_date),
                             d['nights'], int(d['is_minor']), d['guardian_name'], d['guardian_rel']))
                        st.balloons()
                        st.success("✅ تم تسجيل النزيل بنجاح!")

                    conn.commit()
                    # إعادة تعيين
                    st.session_state.step = "input"
                    for key in ['temp', 'is_edit', 'edit_id_temp']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("رقم الوثيقة مكرر أو النزيل موجود مسبقًا")

        with c2:
            if st.button("تعديل", use_container_width=True):
                st.session_state.step = "input"
                st.rerun()

# ───────────────────── تبويب السجلات والبحث (محسن) ─────────────────────
with tab2:
    st.markdown('<div class="section-box"><h3>النزلاء المقيمون</h3></div>', unsafe_allow_html=True)
    
    search = st.text_input("ابحث بالاسم أو رقم الوثيقة أو السرير أو الهاتف", key="search")

    conn = get_db_connection()
    if search:
        query = """
            SELECT id, name, wing, room, bed_num, check_in, nights, id_num, phone 
            FROM guests WHERE status='مقيم'
              AND (name LIKE ? OR id_num LIKE ? OR bed_num LIKE ? OR phone LIKE ?)
            ORDER BY check_in DESC
        """
        df = pd.read_sql_query(query, conn, params=(f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        df = pd.read_sql_query("""
            SELECT id, name, wing, room, bed_num, check_in, nights, id_num, phone 
            FROM guests WHERE status='مقيم' ORDER BY check_in DESC
        """, conn)

    if df.empty:
        st.info("لا يوجد نزلاء حاليًا")
    else:
        # حساب الأيام المتبقية
        df['check_in_dt'] = pd.to_datetime(df['check_in'])
        df['expected_out'] = df['check_in_dt'] + pd.to_timedelta(df['nights'], unit='d')
        df['الأيام المتبقية'] = (df['expected_out'] - pd.Timestamp.today()).dt.days
        df['الأيام المتبقية'] = df['الأيام المتبقية'].apply(lambda x: f"{x} يوم ✅" if x > 0 else "منتهية ⚠️")

        display_df = df[['name', 'wing', 'room', 'bed_num', 'check_in', 'الأيام المتبقية', 'id_num', 'phone']]
        st.data_editor(display_df, hide_index=True, use_container_width=True)

        st.markdown("### إجراءات سريعة")
        for _, row in df.iterrows():
            with st.expander(f"{row['name']} • {row['wing']} • {row['room']} • {row['bed_num']} • منذ: {row['check_in']}"):
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(f"**رقم الوثيقة**: {row['id_num']}")
                col1.write(f"**الهاتف**: {row['phone'] or 'غير مدخل'}")
                if col2.button("تسجيل خروج", key=f"out_{row['id']}"):
                    checkout_guest(row['id'])
                    st.success(f"تم تسجيل خروج {row['name']}")
                    st.rerun()
                if col3.button("تعديل", key=f"edit_{row['id']}"):
                    st.session_state.edit_id = row['id']
                    st.info("✅ تم تحميل البيانات. انتقل إلى تبويب «حجز جديد» لإتمام التعديل")
                    st.rerun()

# ───────────────────── تبويب التصدير (متقدم) ─────────────────────
with tab3:
    st.markdown('<div class="section-box"><h3>تصدير البيانات</h3></div>', unsafe_allow_html=True)
    export_type = st.radio("اختر نوع التصدير", 
                          ["النزلاء المقيمون الحاليون", "الأرشيف الكامل", "كل البيانات (مقيم + مغادر)"])
    
    conn = get_db_connection()
    if export_type == "النزلاء المقيمون الحاليون":
        df_export = pd.read_sql_query("SELECT * FROM guests WHERE status='مقيم'", conn)
    elif export_type == "الأرشيف الكامل":
        df_export = pd.read_sql_query("SELECT * FROM archive", conn)
    else:
        df_export = pd.read_sql_query("SELECT * FROM guests", conn)

    if not df_export.empty:
        csv = df_export.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            f"⬇️ تحميل {export_type} (CSV)",
            data=csv,
            file_name=f"منظومة_محمدي_يوسف_{export_type.replace(' ', '_')}_{date.today()}.csv",
            mime="text/csv"
        )
    else:
        st.info("لا توجد بيانات للتصدير")

# ────────────────────────────────────────────────
#               التوقيع الأسطوري
# ────────────────────────────────────────────────
st.markdown(f"""
    <div style="text-align: center; margin-top: 80px; padding: 35px; background: linear-gradient(135deg, #000428, #004e92); border-radius: 25px; color: white;">
        <h1 style="font-family: 'Orbitron', sans-serif; letter-spacing: 5px; margin:0; color:#00d4ff;">RIDHA MERZOUG LABS</h1>
        <h3 style="margin:15px 0; color:white;">PREMIUM HOSTEL SYSTEM V2026.1</h3>
        <p style="margin:5px; opacity:0.9;">© 2026 - وزارة الشباب والرياضة - ولاية قالمة</p>
        <p style="margin:5px; font-weight: bold; color:#00ff9d;">تمت البرمجة بحب من كريم & رضا</p>
    </div>
""", unsafe_allow_html=True)
