import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- إعدادات الصفحة ---
st.set_page_config(page_title="إدارة بيت الشباب 🏨", layout="wide")

# --- الثوابت ---
PRICE_PER_NIGHT = 400  # سعر الليلة بالدينار
# تأكد من تحديث هذا الرابط دائماً بالرابط الذي ينتهي بـ sharing
SHEET_URL = "https://docs.google.com/spreadsheets/d/1J9_c_ONGxvpdDbLVi360GGcl9pkXCLNSL84PQlLCs38/edit?usp=sharing"

# --- دالة الاتصال بقاعدة البيانات المحلية ---
def get_db():
    conn = sqlite3.connect('hostel_data.db', check_same_thread=False)
    return conn

# إنشاء الجداول إذا لم تكن موجودة
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            id_number TEXT,
            room TEXT,
            check_in TEXT,
            check_out TEXT,
            nights INTEGER,
            total_price REAL,
            legal_status TEXT
        )
    ''')
    conn.commit()

init_db()

# --- دوال مساعدة ---
def calculate_nights(start_date, end_date):
    if end_date > start_date:
        return (end_date - start_date).days
    return 1

def save_booking():
    if st.session_state.temp_data:
        try:
            # 1. الحفظ في SQLite المحلي
            conn_db = get_db()
            cursor = conn_db.cursor()
            nights = calculate_nights(st.session_state.temp_data['check_in'], st.session_state.temp_data['check_out'])
            total_price = nights * PRICE_PER_NIGHT
            
            cursor.execute('''
                INSERT INTO bookings (full_name, id_number, room, check_in, check_out, nights, total_price, legal_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                st.session_state.temp_data['full_name'],
                st.session_state.temp_data['id_number'],
                st.session_state.temp_data['room'],
                str(st.session_state.temp_data['check_in']),
                str(st.session_state.temp_data['check_out']),
                nights,
                total_price,
                st.session_state.temp_data['legal_status']
            ))
            conn_db.commit()

            # 2. المزامنة مع Google Sheets (الهاتف)
            conn_gs = st.connection("gsheets", type=GSheetsConnection)
            
            new_row = pd.DataFrame([{
                "الاسم واللقب": st.session_state.temp_data['full_name'],
                "رقم الهوية": st.session_state.temp_data['id_number'],
                "رقم الغرفة": st.session_state.temp_data['room'],
                "تاريخ الدخول": str(st.session_state.temp_data['check_in']),
                "تاريخ الخروج": str(st.session_state.temp_data['check_out']),
                "عدد الليالي": nights,
                "المبلغ الإجمالي (دج)": total_price,
                "الحالة القانونية": st.session_state.temp_data['legal_status']
            }])
            
            # قراءة البيانات القديمة ودمج الجديدة
            existing_data = conn_gs.read(spreadsheet=SHEET_URL)
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn_gs.update(spreadsheet=SHEET_URL, data=updated_df)

            st.success("✅ تم الحفظ بنجاح وتمت المزامنة مع الهاتف!")
            st.session_state.temp_data = None
            st.balloons()
        except Exception as e:
            st.error(f"⚠️ خطأ في المزامنة: {e}")

# --- واجهة المستخدم (Streamlit UI) ---
st.title("🏨 نظام إدارة بيت الشباب")

if 'temp_data' not in st.session_state:
    st.session_state.temp_data = None

menu = ["➕ حجز جديد", "📊 سجل النزلاء", "⚙️ الإعدادات"]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

if choice == "➕ حجز جديد":
    st.subheader("تسجيل نزيل جديد")
    
    with st.form("booking_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("الاسم واللقب")
            id_number = st.text_input("رقم الهوية")
            room = st.selectbox("رقم الغرفة", [f"غرفة {i}" for i in range(1, 21)])
        with col2:
            check_in = st.date_input("تاريخ الدخول", datetime.now())
            check_out = st.date_input("تاريخ الخروج", datetime.now())
            legal_status = st.selectbox("الحالة القانونية", ["عادي", "عسكري", "طالب", "أجنبي"])
            
        submitted = st.form_submit_button("🔍 مراجعة الحجز")
        
        if submitted:
            if full_name and id_number:
                st.session_state.temp_data = {
                    'full_name': full_name,
                    'id_number': id_number,
                    'room': room,
                    'check_in': check_in,
                    'check_out': check_out,
                    'legal_status': legal_status
                }
            else:
                st.error("الرجاء ملء جميع الحقول الأساسية")

    if st.session_state.temp_data:
        st.write("---")
        st.info(f"📋 ملخص الحجز للنزيل: **{st.session_state.temp_data['full_name']}**")
        n = calculate_nights(st.session_state.temp_data['check_in'], st.session_state.temp_data['check_out'])
        st.write(f"عدد الليالي: {n} | المبلغ الإجمالي: {n * PRICE_PER_NIGHT} دج")
        
        if st.button("✅ تأكيد الحفظ والمزامنة"):
            save_booking()

elif choice == "📊 سجل النزلاء":
    st.subheader("جميع الحجوزات المسجلة")
    conn = get_db()
    # تم تصحيح النجمة هنا (نجمة واحدة فقط)
    df = pd.read_sql("SELECT * FROM bookings", conn)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # خيار لحذف السجل المحلي
        if st.button("🗑️ مسح السجل المحلي"):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bookings")
            conn.commit()
            st.rerun()
    else:
        st.write("لا توجد حجوزات مسجلة حالياً.")

elif choice == "⚙️ الإعدادات":
    st.subheader("إعدادات النظام")
    st.write(f"سعر الليلة الحالي: **{PRICE_PER_NIGHT} دج**")
    st.write(f"رابط المزامنة النشط: {SHEET_URL}")
