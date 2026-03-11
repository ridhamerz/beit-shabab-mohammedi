import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3
import os

# ==================== إعداد الصفحة والتنسيق ====================
st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; font-size: 1.3rem; font-weight: bold; }
    .bed-box { display: inline-block; width: 40px; height: 35px; margin: 3px; border-radius: 5px; text-align: center; line-height: 35px; color: white; font-size: 0.8rem; font-weight: bold; }
    .free { background-color: #28a745; }
    .occupied { background-color: #dc3545; }
    .wing-header { background-color: #f1f3f5; padding: 10px; border-radius: 8px; margin-top: 15px; border-right: 5px solid #1e3c72; font-weight: bold; }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 8px; border-radius: 10px; text-align: center; margin-top: 40px; font-size: 0.75rem; }
    </style>
    """, unsafe_allow_html=True)

# ==================== قاعدة البيانات SQLite ====================
DB_FILE = "biet_chabab.db"

def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            الاسم_واللقب TEXT,
            تاريخ_الازدياد TEXT,
            العنوان TEXT,
            رقم_البطاقة TEXT,
            المهنة TEXT,
            الجناح TEXT,
            الغرفة TEXT,
            السرير TEXT,
            تاريخ_الدخول DATE,
            تاريخ_الخروج DATE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def load_db():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    conn.close()
    return df

def save_booking(data_dict):
    conn = get_conn()
    pd.DataFrame([data_dict]).to_sql("bookings", conn, if_exists="append", index=False)
    conn.close()

def delete_booking(bid):
    conn = get_conn()
    conn.execute("DELETE FROM bookings WHERE id = ?", (bid,))
    conn.commit()
    conn.close()

def update_db(edited_df):
    conn = get_conn()
    edited_df.to_sql("bookings", conn, if_exists="replace", index=False)
    conn.close()

# ==================== البيانات الأساسية ====================
wings = {
    "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
    "جناح إناث": {"غرفة 06": 2, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد إناث 01": 3, "مرقد إناث 02": 4}
}

total_beds = sum(sum(rooms.values()) for rooms in wings.values())

# ==================== الجلسة ====================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'passwords' not in st.session_state:
    st.session_state.passwords = {"مدير": "1234", "عون استقبال": "5678"}

# ==================== بوابة الدخول ====================
if not st.session_state.authenticated:
    st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
    with st.container():
        st.subheader("🔐 الدخول للنظام")
        role = st.selectbox("اختر الصفة", ["مدير", "عون استقبال"])
        pwd = st.text_input("كلمة السر", type="password")
        if st.button("تسجيل الدخول", use_container_width=True):
            if pwd == st.session_state.passwords[role]:
                st.session_state.authenticated = True
                st.session_state.user_role = role
                st.rerun()
            else:
                st.error("❌ كلمة السر خاطئة")
    st.stop()

# ==================== الواجهة الرئيسية ====================
st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)
st.sidebar.info(f"👤 المستخدم الحالي: {st.session_state.user_role}")

if st.sidebar.button("🚪 خروج"):
    st.session_state.authenticated = False
    st.rerun()

# التبويبات
if st.session_state.user_role == "مدير":
    tabs = st.tabs(["➕ حجز جديد", "📊 عدد الغرف", "📋 السجل العام", "📈 الإحصائيات", "⚙️ الإعدادات"])
else:
    tabs = st.tabs(["➕ حجز جديد", "📊 عدد الغرف"])

today = date.today()

# ==================== تبويب: حجز جديد ====================
with tabs[0]:
    st.subheader("📝 استمارة الحجز")
    with st.form("booking_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم واللقب *")
            birth = st.text_input("تاريخ ومكان الازدياد")
            addr = st.text_input("العنوان الكامل")
        with c2:
            id_info = st.text_input("رقم بطاقة التعريف")
            job = st.text_input("المهنة")
            wing = st.selectbox("الجناح", list(wings.keys()))
            room = st.selectbox("الغرفة", list(wings[wing].keys()))
            bed_options = [f"سرير {i+1}" for i in range(wings[wing][room])]
            bed = st.selectbox("السرير", bed_options)
            
            arr = st.date_input("تاريخ الدخول", value=today)
            dep = st.date_input("تاريخ الخروج", value=today + timedelta(days=1))
            
            nights = (dep - arr).days
            st.info(f"عدد الأيام: **{nights}** ليلة")

        submitted = st.form_submit_button("💾 حفظ الحجز", use_container_width=True)
        
        if submitted:
            if not name or dep <= arr:
                st.error("❌ يرجى ملء الاسم وتأكد أن تاريخ الخروج بعد الدخول")
            else:
                # التحقق من التوفر
                conn = get_conn()
                overlap = pd.read_sql_query("""
                    SELECT COUNT(*) as cnt FROM bookings 
                    WHERE الجناح=? AND الغرفة=? AND السرير=? 
                    AND تاريخ_الدخول < ? AND تاريخ_الخروج > ?
                """, conn, params=(wing, room, bed, dep, arr))
                conn.close()
                
                if overlap['cnt'].iloc[0] > 0:
                    st.error("❌ السرير محجوز في هذه الفترة!")
                else:
                    new_record = {
                        "الاسم_واللقب": name, "تاريخ_الازدياد": birth, "العنوان": addr,
                        "رقم_البطاقة": id_info, "المهنة": job,
                        "الجناح": wing, "الغرفة": room, "السرير": bed,
                        "تاريخ_الدخول": arr, "تاريخ_الخروج": dep
                    }
                    save_booking(new_record)
                    st.success(f"✅ تم الحجز بنجاح! (سرير {bed} - {wing})")
                    st.rerun()

# ==================== تبويب: عدد الغرف ====================
with tabs[1]:
    st.subheader("📊 حالة الأسرة والأجنحة (اليوم الحالي)")
    for wing_name, rooms in wings.items():
        st.markdown(f'<div class="wing-header">{wing_name}</div>', unsafe_allow_html=True)
        for room_name, bed_count in rooms.items():
            cols = st.columns([1, 5])
            cols[0].write(f"**{room_name}**")
            html = ""
            for b in range(1, bed_count + 1):
                b_name = f"سرير {b}"
                # التحقق من الإشغال اليوم
                df = load_db()
                occupied = not df[
                    (df['الجناح'] == wing_name) &
                    (df['الغرفة'] == room_name) &
                    (df['السرير'] == b_name) &
                    (df['تاريخ_الدخول'] <= today) &
                    (df['تاريخ_الخروج'] > today)
                ].empty
                status = "occupied" if occupied else "free"
                html += f'<div class="bed-box {status}">{b}</div>'
            cols[1].markdown(html, unsafe_allow_html=True)

# ==================== تبويب: السجل العام (للمدير فقط) ====================
if st.session_state.user_role == "مدير":
    with tabs[2]:
        st.subheader("📋 السجل العام")
        df = load_db()
        if df.empty:
            st.info("لا توجد حجوزات بعد")
        else:
            # بحث
            search = st.text_input("🔍 بحث بالاسم أو رقم البطاقة")
            if search:
                df = df[df['الاسم_واللقب'].str.contains(search, na=False) | 
                       df['رقم_البطاقة'].str.contains(search, na=False)]
            
            edited_df = st.data_editor(
                df, 
                use_container_width=True, 
                num_rows="dynamic",
                key="data_editor"
            )
            
            col1, col2, col3 = st.columns(3)
            if col1.button("💾 حفظ التعديلات", use_container_width=True):
                update_db(edited_df)
                st.success("تم حفظ التعديلات")
                st.rerun()
            
            if col2.button("🗑️ مسح السجل بالكامل", use_container_width=True):
                if st.checkbox("أنا متأكد أريد مسح كل شيء"):
                    conn = get_conn()
                    conn.execute("DELETE FROM bookings")
                    conn.commit()
                    conn.close()
                    st.success("تم المسح")
                    st.rerun()
            
            if col3.button("📥 تصدير إلى Excel", use_container_width=True):
                df.to_excel("حجوزات_بيت_الشباب.xlsx", index=False)
                st.success("تم التصدير! الملف في مجلد التطبيق")

# ==================== تبويب: الإحصائيات (جديد) ====================
if st.session_state.user_role == "مدير":
    with tabs[3]:
        st.subheader("📈 لوحة الإحصائيات")
        df = load_db()
        
        col1, col2, col3, col4 = st.columns(4)
        current_guests = len(df[(df['تاريخ_الدخول'] <= today) & (df['تاريخ_الخروج'] > today)]) if not df.empty else 0
        occupancy_rate = round((current_guests / total_beds) * 100, 1) if total_beds > 0 else 0
        
        col1.metric("النزلاء اليوم", current_guests, f"{occupancy_rate}% إشغال")
        col2.metric("إجمالي الحجوزات", len(df))
        col3.metric("إجمالي الأسرة", total_beds)
        col4.metric("الخروجات غداً", len(df[df['تاريخ_الخروج'] == today + timedelta(days=1)]) if not df.empty else 0)
        
        st.markdown("### النزلاء الحاليين")
        if not df.empty:
            current = df[(df['تاريخ_الدخول'] <= today) & (df['تاريخ_الخروج'] > today)]
            st.dataframe(current[['الاسم_واللقب', 'الجناح', 'الغرفة', 'السرير', 'تاريخ_الخروج']], use_container_width=True)

# ==================== تبويب: الإعدادات ====================
if st.session_state.user_role == "مدير":
    with tabs[4]:
        st.subheader("⚙️ إعدادات كلمات السر")
        target = st.selectbox("تغيير كلمة سر لـ", ["مدير", "عون استقبال"])
        new_pwd = st.text_input("كلمة السر الجديدة", type="password")
        if st.button("تحديث كلمة السر"):
            if new_pwd:
                st.session_state.passwords[target] = new_pwd
                st.success(f"تم تغيير كلمة سر {target}")

# ==================== التذييل ====================
st.markdown(f"""
    <div class="developer-footer">
        Developer <span style="color:#00d4ff;">®ridha_merzoug®</span> [رضا مرزوق] — النسخة المحسنة 2026
    </div>
    """, unsafe_allow_html=True)
