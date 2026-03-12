import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
import io
from streamlit_gsheets import GSheetsConnection

# ==================== 1. الإعدادات والأسعار ====================
MANAGER_PASSWORD = "1234"
RECEPTION_PASSWORD = "5678"
PRICE_PER_NIGHT = 400
# رابط ملفك الذ
SHEET_URL = "https://docs.google.com/spreadsheets/d/1J9_c_ONGxvpdDbLVi360GGcl9pkXCLNSL84PQlLCs38/edit?usp=sharing"

st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide", page_icon="🏨")

# تنسيق CSS احترافي وشامل
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; }
    .bed-box { display: inline-block; width: 50px; height: 40px; margin: 5px; border-radius: 8px; text-align: center; line-height: 40px; color: white; font-weight: bold; font-size: 0.8rem; }
    .free { background-color: #28a745; border-bottom: 4px solid #1e7e34; }
    .occupied { background-color: #dc3545; border-bottom: 4px solid #bd2130; }
    .wing-header { background: #f8f9fa; padding: 10px; border-right: 5px solid #1e3c72; margin: 15px 0; font-weight: bold; border-radius: 5px; }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 15px; border-radius: 12px; text-align: center; margin-top: 40px; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

# ==================== 2. قاعدة البيانات والربط السحابي ====================
DB_FILE = "biet_chabab.db"

@st.cache_resource
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, birth_date DATE, 
        birth_place TEXT, address TEXT, id_number TEXT, wing TEXT, 
        room TEXT, bed TEXT, check_in DATE, check_out DATE, legal_status TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS rooms_config (wing TEXT, room TEXT, beds_count INTEGER, PRIMARY KEY (wing, room))''')
    if conn.execute("SELECT COUNT(*) FROM rooms_config").fetchone()[0] == 0:
        rooms = [("جناح ذكور", f"غرفة {i:02d}", 6) for i in range(1, 6)] + \
                [("جناح إناث", f"غرفة {i:02d}", 6) for i in range(6, 11)]
        conn.executemany("INSERT INTO rooms_config VALUES (?,?,?)", rooms)
    conn.commit()

init_db()
# اتصال Google Sheets
conn_gsheets = st.connection("gsheets", type=GSheetsConnection)

def calculate_nights(d1, d2):
    return max((pd.to_datetime(d2).date() - pd.to_datetime(d1).date()).days, 1)

def save_to_google_sheets(new_row):
    try:
        existing_data = conn_gsheets.read(spreadsheet=SHEET_URL)
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row])], ignore_index=True)
        conn_gsheets.update(spreadsheet=SHEET_URL, data=updated_df)
        return True
    except Exception as e:
        st.error(f"⚠️ خطأ في مزامنة الهاتف: {e}")
        return False

# ==================== 3. دوال تصدير ملفات Word ====================

def add_official_header_footer(doc):
    section = doc.sections[0]
    header = section.header
    htable = header.add_table(1, 2, width=Inches(6.5))
    cell_l = htable.rows[0].cells[0]
    cell_l.text = "مديرية الشباب والرياضة لولاية قالمة\nديوان مؤسسات الشباب قالمة\nبيت الشباب الشهيد محمدي يوسف قالمة"
    cell_l.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in cell_l.paragraphs[0].runs: run.font.size = Pt(9); run.bold = True
    cell_r = htable.rows[0].cells[1]
    try:
        cell_r.paragraphs[0].add_run().add_picture("logo.png", width=Inches(0.7))
    except:
        cell_r.text = "[الشعار الرسمي]"
    cell_r.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer = section.footer
    footer.paragraphs[0].text = "عون الاستقبال: ............................          الحارس الليلي: ............................"
    footer.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

def generate_report_table(df):
    doc = Document()
    add_official_header_footer(doc)
    section = doc.sections[0]
    def save_booking():
    if st.session_state.temp_data:
        try:
            # 1. الحفظ في قاعدة البيانات المحلية (داخل التطبيق)
            conn_db = get_db()
            cursor = conn_db.cursor()
            cursor.execute('''
                INSERT INTO bookings (full_name, id_number, room, check_in, check_out, nights, total_price, legal_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                st.session_state.temp_data['full_name'],
                st.session_state.temp_data['id_number'],
                st.session_state.temp_data['room'],
                str(st.session_state.temp_data['check_in']),
                str(st.session_state.temp_data['check_out']),
                calculate_nights(st.session_state.temp_data['check_in'], st.session_state.temp_data['check_out']),
                calculate_nights(st.session_state.temp_data['check_in'], st.session_state.temp_data['check_out']) * PRICE_PER_NIGHT,
                st.session_state.temp_data['legal_status']
            ))
            conn_db.commit()

            # 2. الحفظ والمزامنة مع Google Sheets (الهاتف)
            conn_gs = st.connection("gsheets", type=GSheetsConnection)
            
            # تجهيز البيانات بنفس ترتيب الأعمدة في ملفك
            new_row = pd.DataFrame([{
                "الاسم واللقب": st.session_state.temp_data['full_name'],
                "رقم الهوية": st.session_state.temp_data['id_number'],
                "رقم الغرفة": st.session_state.temp_data['room'],
                "تاريخ الدخول": str(st.session_state.temp_state.check_in),
                "تاريخ الخروج": str(st.session_state.temp_state.check_out),
                "عدد الليالي": calculate_nights(st.session_state.temp_data['check_in'], st.session_state.temp_data['check_out']),
                "المبلغ الإجمالي (دج)": calculate_nights(st.session_state.temp_data['check_in'], st.session_state.temp_data['check_out']) * PRICE_PER_NIGHT,
                "الحالة القانونية": st.session_state.temp_data['legal_status']
            }])
            
            # إرسال البيانات للرابط
            existing_data = conn_gs.read(spreadsheet=SHEET_URL)
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn_gs.update(spreadsheet=SHEET_URL, data=updated_df)

            st.success("✅ تم الحفظ بنجاح وتمت المزامنة مع الهاتف!")
            st.session_state.temp_data = None
            st.balloons() # احتفال بسيط بنجاح العملية
        except Exception as e:
            st.error(f"حدث خطأ في المزامنة: {e}")

        row_cells[3].text = str(row['address'])
        row_cells[4].text = str(calculate_nights(row['check_in'], row['check_out']))
        row_cells[5].text = str(row['legal_status'])
        for cell in row_cells:
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio

def generate_receipt(row):
    doc = Document()
    add_official_header_footer(doc)
    doc.add_heading('وصل استلام مبلغ مالي', 1).alignment = WD_ALIGN_PARAGRAPH.CENTER
    nights = calculate_nights(row['check_in'], row['check_out'])
    total = nights * PRICE_PER_NIGHT
    p = doc.add_paragraph()
    p.add_run(f"\nاستلمنا من السيد(ة): {row['full_name']}\n").bold = True
    p.add_run(f"مبلغ قدره: {total} دج (مقابل إقامة لمدة {nights} ليلة)\n")
    p.add_run(f"الجناح: {row['wing']} | الغرفة: {row['room']}\n")
    p.add_run(f"تاريخ الدخول: {row['check_in']} | تاريخ الخروج: {row['check_out']}\n")
    p.add_run(f"\nحرر بقالمة في: {date.today()}\n")
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio

# ==================== 4. منطق التطبيق والواجهة ====================

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'review_mode' not in st.session_state: st.session_state.review_mode = False

if not st.session_state.authenticated:
    st.markdown('<div class="main-title">🏨 إدارة بيت الشباب محمدي يوسف قالمة</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        role = st.selectbox("🔑 الصفة", ["مدير", "عون استقبال"])
        pwd = st.text_input("🔒 كلمة السر", type="password")
        if st.button("🚀 دخول", use_container_width=True):
            if (role == "مدير" and pwd == MANAGER_PASSWORD) or (role == "عون استقبال" and pwd == RECEPTION_PASSWORD):
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("❌ خطأ في كلمة السر")
    st.stop()

tabs = st.tabs(["➕ حجز جديد", "🛌 حالة الغرف", "📋 السجل العام", "📄 تصدير Word", "💰 الحسابات"])
df_bookings = pd.read_sql("SELECT  * FROM bookings", get_db())
df_rooms = pd.read_sql("SELECT * FROM rooms_config", get_db())
today = date.today()

# --- 1. حجز جديد ---
with tabs[0]:
    if not st.session_state.review_mode:
        with st.form("new_booking_form"):
            st.markdown("### 👤 بيانات النزيل")
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("الاسم واللقب *")
                b_date = st.date_input("تاريخ الازدياد", date(2000, 1, 1))
                b_place = st.text_input("مكان الازدياد")
                address = st.text_input("العنوان الكامل")
            with c2:
                id_val = st.text_input("رقم بطاقة التعريف *")
                wing_sel = st.selectbox("الجناح", df_rooms['wing'].unique())
                room_sel = st.selectbox("الغرفة", df_rooms[df_rooms['wing'] == wing_sel]['room'])
                d_in = st.date_input("تاريخ الدخول", today)
                d_out = st.date_input("تاريخ الخروج", today + timedelta(days=1))
            
            age = (today - b_date).days // 365
            legal = "عادي"
            if age < 18:
                st.warning(f"⚠️ النزيل قاصر ({age} سنة)")
                legal = st.selectbox("الوثيقة القانونية للقاصر", ["تصريح أبوي", "حضور الولي", "أمر بمهمة"])

            if st.form_submit_button("🔍 مراجعة الحجز"):
                st.session_state.temp_data = {
                    "full_name": name, "birth_date": b_date, "birth_place": b_place, "address": address,
                    "id_number": id_val, "wing": wing_sel, "room": room_sel, "check_in": d_in, "check_out": d_out, "legal_status": legal
                }
                st.session_state.review_mode = True
                st.rerun()
    else:
        st.subheader("🧐 تأكيد البيانات")
        st.write(st.session_state.temp_data)
        col_a, col_b = st.columns(2)
        if col_a.button("✅ حفظ وتزامن مع الهاتف", use_container_width=True):
            # 1. حفظ محلي
            pd.DataFrame([st.session_state.temp_data]).to_sql("bookings", get_db(), if_exists="append", index=False)
            # 2. رفع لجوجل شيتس
            gs_row = {
                "الاسم واللقب": st.session_state.temp_data['full_name'],
                "رقم الهوية": st.session_state.temp_data['id_number'],
                "رقم الغرفة": st.session_state.temp_data['room'],
                "تاريخ الدخول": str(st.session_state.temp_data['check_in']),
                "تاريخ الخروج": str(st.session_state.temp_data['check_out']),
                "عدد الليالي": calculate_nights(st.session_state.temp_data['check_in'], st.session_state.temp_data['check_out']),
                "المبلغ الإجمالي (دج)": calculate_nights(st.session_state.temp_data['check_in'], st.session_state.temp_data['check_out']) * PRICE_PER_NIGHT,
                "الحالة القانونية": st.session_state.temp_data['legal_status']
            }
            save_to_google_sheets(gs_row)
            st.session_state.review_mode = False
            st.rerun()
        if col_b.button("🔙 تعديل", use_container_width=True):
            st.session_state.review_mode = False
            st.rerun()

# --- 2. حالة الغرف ---
with tabs[1]:
    st.subheader("🛌 خريطة الغرف والأسرّة")
    for wing_n in df_rooms['wing'].unique():
        st.markdown(f'<div class="wing-header">📍 {wing_n}</div>', unsafe_allow_html=True)
        w_rooms = df_rooms[df_rooms['wing'] == wing_n]
        for _, r_data in w_rooms.iterrows():
            with st.expander(f"🚪 {r_data['room']} ({r_data['beds_count']} أسرّة)"):
                cols = st.columns(r_data['beds_count'])
                # جلب النزلاء الموجودين حالياً في هذه الغرفة
                occ_now = df_bookings[
                    (df_bookings['room'] == r_data['room']) & 
                    (pd.to_datetime(df_bookings['check_in']).dt.date <= today) & 
                    (pd.to_datetime(df_bookings['check_out']).dt.date > today)
                ]
                for i in range(r_data['beds_count']):
                    if i < len(occ_now):
                        cols[i].markdown(f'<div class="bed-box occupied" title="النزيل: {occ_now.iloc[i]["full_name"]}">س{i+1}</div>', unsafe_allow_html=True)
                    else:
                        cols[i].markdown(f'<div class="bed-box free">س{i+1}</div>', unsafe_allow_html=True)

# --- 3. السجل ---
with tabs[2]:
    st.dataframe(df_bookings, use_container_width=True)

# --- 4. التصدير ---
with tabs[3]:
    st.subheader("📄 مركز الوثائق")
    if not df_bookings.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.info("📊 التقرير العام (جدول)")
            st.download_button("⬇️ تحميل جدول النزلاء", generate_report_table(df_bookings), "تقرير_شامل.docx")
        with c2:
            st.info("🧾 الوثائق الفردية")
            sel_user = st.selectbox("اختر نزيل", df_bookings['full_name'].unique())
            u_row = df_bookings[df_bookings['full_name'] == sel_user].iloc[-1]
            st.download_button(f"⬇️ تحميل وصل {sel_user}", generate_receipt(u_row), f"وصل_{sel_user}.docx")

# --- 5. الحسابات ---
with tabs[4]:
    total_nights = df_bookings.apply(lambda r: calculate_nights(r['check_in'], r['check_out']), axis=1).sum()
    st.metric("إجمالي المداخيل المحققة", f"{total_nights * PRICE_PER_NIGHT} دج")

st.markdown(f'<div class="developer-footer">🛠️ تم التطوير بواسطة: <b>RIDHA MERZOUG</b> | 📍 بيت شباب محمدي يوسف قالمة - 2026</div>', unsafe_allow_html=True)
