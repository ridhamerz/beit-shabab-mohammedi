import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import io

# ====================== إعدادات الصفحة والـ CSS ======================
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    * { font-family: 'Tahoma', 'Arial', sans-serif; direction: RTL; text-align: right; }
    .main-title { 
        background: linear-gradient(90deg, #1e3c72, #2a5298); 
        color: white; padding: 20px; border-radius: 15px; 
        text-align: center; margin-bottom: 25px; 
        font-size: 1.5rem; font-weight: bold;
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
        font-size: 0.75rem; border: 1px solid #00d4ff;
    }
    </style>
""", unsafe_allow_html=True)

# ====================== إعداد قاعدة البيانات ======================
DB_FILE = 'youth_hostel.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # جدول المقيمين الحاليين
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
    
    # جدول الأرشيف
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
        guardian_permission TEXT
    )''')
    
    conn.commit()
    conn.close()

    # إضافة الأعمدة الجديدة إذا لم تكن موجودة
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for table in ['current_guests', 'archive']:
        for col_def in [
            'is_minor TEXT DEFAULT "لا"',
            'guardian_name TEXT',
            'guardian_permission TEXT'
        ]:
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
            except sqlite3.OperationalError:
                pass  # العمود موجود بالفعل
    conn.commit()
    conn.close()

def get_current_guests():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM current_guests WHERE status = 'مقيم'", conn)
    conn.close()
    return df

def get_archive():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM archive", conn)
    conn.close()
    return df

def get_monthly_data(month, year):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        "SELECT * FROM archive WHERE strftime('%Y-%m', check_out) = ?",
        conn, params=(f"{year}-{month:02d}",)
    )
    conn.close()
    return df

def is_bed_occupied(wing, room, bed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM current_guests WHERE wing=? AND room=? AND bed=? AND status='مقيم'", 
              (wing, room, bed))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def add_guest(name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, guardian_name, guardian_permission):
    age = (date.today() - birth_date).days // 365
    is_minor = 'نعم' if age < 18 else 'لا'
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO current_guests 
        (name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, is_minor, guardian_name, guardian_permission)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, str(birth_date), birth_place, address, id_card, wing, room, bed, str(check_in), str(check_out), is_minor, guardian_name or None, guardian_permission or None))
    conn.commit()
    conn.close()

def update_guest(gid, name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, guardian_name, guardian_permission):
    age = (date.today() - birth_date).days // 365
    is_minor = 'نعم' if age < 18 else 'لا'
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        UPDATE current_guests SET
            name=?, birth_date=?, birth_place=?, address=?, id_card=?, wing=?, room=?, bed=?, check_in=?, check_out=?, 
            is_minor=?, guardian_name=?, guardian_permission=?
        WHERE id=?
    """, (name, str(birth_date), birth_place, address, id_card, wing, room, bed, str(check_in), str(check_out), 
          is_minor, guardian_name or None, guardian_permission or None, gid))
    conn.commit()
    conn.close()

def evacuate_guest(gid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO archive 
        (name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, status, is_minor, guardian_name, guardian_permission)
        SELECT name, birth_date, birth_place, address, id_card, wing, room, bed, check_in, check_out, 'غادر', is_minor, guardian_name, guardian_permission
        FROM current_guests WHERE id=?
    """, (gid,))
    c.execute("DELETE FROM current_guests WHERE id=?", (gid,))
    conn.commit()
    conn.close()

# ====================== تهيئة البيانات ======================
init_db()

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

# ====================== تسجيل الدخول ======================
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

# ====================== الواجهة الرئيسية ======================
st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
st.sidebar.write(f"👤 المستخدم: **{st.session_state.user_role}**")
if st.sidebar.button("تسجيل الخروج"):
    st.session_state.authenticated = False
    st.rerun()

tabs = st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجل والبحث", "📂 الأرشيف", "📈 الإحصائيات", "⚙️ الإعدادات"]) \
    if st.session_state.user_role == "مدير" else \
    st.tabs(["➕ حجز جديد", "📊 حالة الغرف", "📋 السجل والبحث"])

# ====================== حجز جديد ======================
with tabs[0]:
    st.subheader("📝 تسجيل نزيل جديد")
    with st.form("booking_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم واللقب *")
            birth_date = st.date_input("تاريخ الازدياد", value=date.today() - timedelta(days=365*20))
            birth_place = st.text_input("مكان الازدياد")
            addr = st.text_input("العنوان الكامل")
        with c2:
            id_card = st.text_input("رقم بطاقة التعريف *")
            wing = st.selectbox("الجناح", list(wings.keys()))
            room = st.selectbox("الغرفة", list(wings[wing].keys()))
            bed = st.selectbox("رقم السرير", [f"سرير {i+1}" for i in range(wings[wing][room])])
            check_in = st.date_input("تاريخ الدخول", value=date.today())
            check_out = st.date_input("تاريخ الخروج", value=date.today() + timedelta(days=1))

        age = (date.today() - birth_date).days // 365

        guardian_name = None
        guardian_permission = None
        if age < 18:
            st.markdown("**معلومات ولي الأمر / الوصي (للقاصرين)**")
            guardian_name = st.text_input("اسم ولي الأمر / الوصي")
            guardian_permission = st.selectbox("نوع التصريح / الإذن", [
                "موافقة خطية من ولي الأمر",
                "حضور ولي الأمر شخصيًا",
                "إذن قضائي أو رسمي",
                "مرافق معتمد من ولي الأمر",
                "غير مطلوب / حالة خاصة"
            ])

        submitted = st.form_submit_button("✅ تأكيد وحفظ")

        if submitted:
            if not name or not id_card:
                st.error("يرجى ملء الاسم ورقم البطاقة")
            elif check_out <= check_in:
                st.error("تاريخ الخروج يجب أن يكون بعد تاريخ الدخول")
            elif is_bed_occupied(wing, room, bed):
                st.error(f"❌ السرير {bed} في {room} محجوز حالياً!")
            else:
                if age < 18:
                    st.warning(f"⚠️ تنبيه: النزيل قاصر (عمر {age} سنة). يُرجى التأكد من وجود ولي أمر أو إذن قانوني.")
                
                add_guest(name, birth_date, birth_place, addr, id_card, wing, room, bed, check_in, check_out,
                          guardian_name, guardian_permission)
                st.success(f"تم تسجيل النزيل {name} بنجاح (عمر: {age} سنة)")
                st.rerun()

# ====================== حالة الغرف ======================
with tabs[1]:
    st.subheader("📊 حالة الأجنحة والأسرة")
    current_df = get_current_guests()
    
    for wing_name, rooms in wings.items():
        st.markdown(f'<div style="background:#f8f9fa; padding:10px; border-radius:10px; border-right:5px solid #1e3c72; margin-top:15px;"><b>{wing_name}</b></div>', unsafe_allow_html=True)
        for room_name, bed_count in rooms.items():
            cols = st.columns([1, 6])
            cols[0].write(f"**{room_name}**")
            html = ""
            for b in range(1, bed_count + 1):
                b_name = f"سرير {b}"
                is_occ = not current_df[(current_df['wing'] == wing_name) & 
                                       (current_df['room'] == room_name) & 
                                       (current_df['bed'] == b_name)].empty
                status = "occupied" if is_occ else "free"
                html += f'<div class="bed-box {status}">{b}</div>'
            cols[1].markdown(html, unsafe_allow_html=True)

# ====================== السجل والبحث + تعديل + إخلاء ======================
with tabs[2]:
    st.subheader("🔍 سجل المقيمين الحاليين")
    search = st.text_input("ابحث بالاسم أو رقم البطاقة...")
    df = get_current_guests()
    
    if search:
        df = df[df['name'].str.contains(search, case=False, na=False) | 
                df['id_card'].str.contains(search, na=False)]
    
    st.dataframe(df, use_container_width=True)
    
    # تعديل نزيل
    st.markdown("---")
    st.subheader("✏️ تعديل بيانات نزيل")
    if not df.empty:
        edit_id = st.selectbox("اختر النزيل", df['id'].tolist(), 
                              format_func=lambda x: df.loc[df['id']==x, 'name'].values[0])
        if edit_id:
            row = df[df['id'] == edit_id].iloc[0]
            with st.form("edit_form"):
                c1, c2 = st.columns(2)
                with c1:
                    e_name = st.text_input("الاسم واللقب *", row['name'])
                    e_birth_date = st.date_input("تاريخ الازدياد", date.fromisoformat(row['birth_date']))
                    e_birth_place = st.text_input("مكان الازدياد", row['birth_place'])
                    e_address = st.text_input("العنوان", row['address'])
                with c2:
                    e_id_card = st.text_input("رقم البطاقة *", row['id_card'])
                    e_wing = st.selectbox("الجناح", list(wings.keys()), 
                                         index=list(wings.keys()).index(row['wing']))
                    e_room = st.selectbox("الغرفة", list(wings[e_wing].keys()), 
                                         index=list(wings[e_wing].keys()).index(row['room']))
                    e_bed_idx = int(row['bed'].split()[-1]) - 1 if 'سرير' in row['bed'] else 0
                    e_bed = st.selectbox("السرير", [f"سرير {i+1}" for i in range(wings[e_wing][e_room])], 
                                        index=e_bed_idx)
                    e_check_in = st.date_input("تاريخ الدخول", date.fromisoformat(row['check_in']))
                    e_check_out = st.date_input("تاريخ الخروج", date.fromisoformat(row['check_out']))

                e_age = (date.today() - e_birth_date).days // 365
                e_guardian_name = row.get('guardian_name', '')
                e_guardian_perm = row.get('guardian_permission', '')
                if e_age < 18:
                    st.markdown("**معلومات ولي الأمر / الوصي**")
                    e_guardian_name = st.text_input("اسم ولي الأمر", value=e_guardian_name)
                    e_guardian_perm = st.selectbox("نوع التصريح", [
                        "موافقة خطية من ولي الأمر",
                        "حضور ولي الأمر شخصيًا",
                        "إذن قضائي أو رسمي",
                        "مرافق معتمد من ولي الأمر",
                        "غير مطلوب / حالة خاصة"
                    ], index=["موافقة خطية من ولي الأمر", ...].index(e_guardian_perm) if e_guardian_perm in [...] else 0)

                if st.form_submit_button("💾 حفظ التعديلات"):
                    if not e_name or not e_id_card:
                        st.error("الاسم ورقم البطاقة مطلوبان")
                    elif e_check_out <= e_check_in:
                        st.error("تاريخ الخروج يجب أن يكون بعد الدخول")
                    elif is_bed_occupied(e_wing, e_room, e_bed) and \
                         (e_wing != row['wing'] or e_room != row['room'] or e_bed != row['bed']):
                        st.error("السرير محجوز")
                    else:
                        if e_age < 18:
                            st.warning(f"⚠️ تنبيه: النزيل قاصر (عمر {e_age} سنة)")
                        update_guest(edit_id, e_name, e_birth_date, e_birth_place, e_address, e_id_card,
                                     e_wing, e_room, e_bed, e_check_in, e_check_out,
                                     e_guardian_name, e_guardian_perm)
                        st.success("تم التعديل بنجاح")
                        st.rerun()

    # إخلاء نزيل
    st.markdown("---")
    st.subheader("🚪 إنهاء إقامة نزيل")
    if not df.empty:
        out_id = st.selectbox("اختر النزيل المغادر", df['id'].tolist(), 
                             format_func=lambda x: df.loc[df['id']==x, 'name'].values[0])
        if st.button("إخلاء السرير ونقل للأرشيف"):
            evacuate_guest(out_id)
            st.success("تم الإخلاء ونقل البيانات للأرشيف")
            st.rerun()

# ====================== تبويبات المدير فقط ======================
if st.session_state.user_role == "مدير":
    with tabs[3]:
        st.subheader("📂 الأرشيف")
        st.dataframe(get_archive(), use_container_width=True)

        st.subheader("تصدير شهري")
        today = date.today()
        m = st.selectbox("الشهر", range(1,13), index=today.month-1)
        y = st.number_input("السنة", 2000, 2100, today.year)
        monthly = get_monthly_data(m, y)
        if not monthly.empty:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                monthly.to_excel(writer, index=False)
            buf.seek(0)
            st.download_button("تحميل XLSX", buf, f"archive_{y}_{m:02d}.xlsx",
                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("لا بيانات لهذا الشهر")

    with tabs[4]:
        st.subheader("الإحصائيات")
        curr = get_current_guests()
        arch = get_archive()
        total_beds = sum(sum(r.values()) for r in wings.values())
        occ = len(curr) / total_beds * 100 if total_beds > 0 else 0
        cols = st.columns(3)
        cols[0].metric("نزلاء حاليين", len(curr))
        cols[1].metric("إجمالي الأرشيف", len(arch))
        cols[2].metric("نسبة الإشغال", f"{occ:.1f}%")

    with tabs[5]:
        st.subheader("إعدادات")
        target = st.selectbox("تغيير كلمة مرور", ["مدير", "عون استقبال"])
        np = st.text_input("كلمة المرور الجديدة", type="password")
        if st.button("حفظ"):
            st.session_state.passwords[target] = np
            st.success("تم التغيير")

# ====================== تذييل ======================
st.markdown("""
    <div class="developer-footer">
        Developer <span style="color:#00d4ff; font-weight:bold;">®ridha_merzoug®</span> [رضا مرزوق] - 2026
    </div>
""", unsafe_allow_html=True)
