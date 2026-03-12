import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# ==================== 1. الإعدادات الأساسية وكلمات السر ====================
MANAGER_PASSWORD = "1234"
RECEPTION_PASSWORD = "5678"
PRICE_PER_NIGHT = 400

st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide", page_icon="🏨")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; font-size: 1.5rem; }
    .stat-card { background: #ffffff; padding: 20px; border-radius: 15px; border-bottom: 6px solid #1e3c72; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .bed-box { display: inline-block; width: 48px; height: 38px; margin: 4px; border-radius: 8px; text-align: center; line-height: 38px; color: white; font-weight: bold; }
    .free { background-color: #28a745; }
    .occupied { background-color: #dc3545; }
    .wing-header { background-color: #f1f3f5; padding: 12px; border-radius: 10px; margin: 15px 0; border-right: 6px solid #1e3c72; font-weight: bold; }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 15px; border-radius: 12px; text-align: center; margin-top: 40px; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

# ==================== 2. قاعدة البيانات ====================
DB_FILE = "biet_chabab.db"

@st.cache_resource
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT, birth_date DATE, birth_place TEXT, address TEXT,
        id_type TEXT, id_number TEXT, nationality TEXT, visa_date TEXT,
        wing TEXT, room TEXT, bed TEXT, check_in DATE, check_out DATE, legal_status TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS rooms_config (wing TEXT, room TEXT, beds_count INTEGER, PRIMARY KEY (wing, room))''')
    if conn.execute("SELECT COUNT(*) FROM rooms_config").fetchone()[0] == 0:
        default_rooms = [
            ("جناح ذكور", "غرفة 01", 6), ("جناح ذكور", "غرفة 02", 6), ("جناح ذكور", "غرفة 03", 6),
            ("جناح ذكور", "غرفة 04", 6), ("جناح ذكور", "غرفة 05", 6), ("جناح ذكور", "مرقد ذكور 01", 3), ("جناح ذكور", "مرقد ذكور 02", 4),
            ("جناح إناث", "غرفة 06", 2), ("جناح إناث", "غرفة 07", 6), ("جناح إناث", "غرفة 08", 6),
            ("جناح إناث", "غرفة 09", 6), ("جناح إناث", "مرقد إناث 01", 3), ("جناح إناث", "مرقد إناث 02", 4)
        ]
        conn.executemany("INSERT OR IGNORE INTO rooms_config VALUES (?,?,?)", default_rooms)
    conn.commit()

init_db()

# ==================== 3. الدوال المساعدة (Word & Logic) ====================

def calculate_nights(check_in, check_out):
    d1 = pd.to_datetime(check_in).date()
    d2 = pd.to_datetime(check_out).date()
    return max((d2 - d1).days, 1)

def add_official_header_footer(doc):
    section = doc.sections[0]
    header = section.header
    footer = section.footer
    
    # الترويسة (Header) - جدول مخفي
    htable = header.add_table(1, 2, width=Inches(6.5))
    
    # اليمين (الشعار)
    cell_right = htable.rows[0].cells[1]
    try:
        run = cell_right.paragraphs[0].add_run()
        run.add_picture("logo.png", width=Inches(0.7))
    except:
        cell_right.paragraphs[0].text = "[الشعار]"
    cell_right.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # اليسار (النصوص الرسمية)
    cell_left = htable.rows[0].cells[0]
    p_left = cell_left.paragraphs[0]
    p_left.text = "مديرية الشباب والرياضة لولاية قالمة\nديوان مؤسسات الشباب قالمة\nبيت الشباب الشهيد محمدي يوسف قالمة"
    p_left.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in p_left.runs: run.font.size = Pt(9); run.bold = True

    # التذييل (Footer)
    f_p = footer.paragraphs[0]
    f_p.text = "عون الاستقبال: ............................                              الحارس الليلي: ............................"
    f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    f_p.runs[0].font.size = Pt(9)

def generate_report_table(df):
    doc = Document()
    add_official_header_footer(doc)
    doc.add_heading('تقرير النزلاء اليومي', 1).alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    table = doc.add_table(rows=1, cols=6)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    for i, txt in enumerate(['رقم الغرفة', 'الاسم واللقب', 'تاريخ ومكان الازدياد', 'العنوان', 'عدد الليالي', 'ملاحظات']):
        hdr_cells[i].text = txt
        hdr_cells[i].paragraphs[0].runs[0].bold = True

    for _, row in df.iterrows():
        row_cells = table.add_row().cells
        row_cells[0].text = str(row['room'])
        row_cells[1].text = str(row['full_name'])
        row_cells[2].text = f"{row['birth_date']} بـ {row['birth_place']}"
        row_cells[3].text = str(row['address'])
        row_cells[4].text = str(calculate_nights(row['check_in'], row['check_out']))
        row_cells[5].text = str(row['legal_status'])
        
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def generate_police_form(row):
    doc = Document()
    add_official_header_footer(doc)
    doc.add_heading('إستمارة تصريح بالإيواء', 1).alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph()
    p.add_run(f"\nالاسم واللقب: {row['full_name']}\n").bold = True
    p.add_run(f"تاريخ ومكان الازدياد: {row['birth_date']} بـ {row['birth_place']}\n")
    p.add_run(f"رقم الهوية: {row['id_type']} {row['id_number']}\n")
    p.add_run(f"العنوان: {row['address']}\n")
    p.add_run(f"الجناح/الغرفة: {row['wing']} {row['room']}\n")
    p.add_run(f"تاريخ الدخول: {row['check_in']} | الخروج: {row['check_out']}\n")
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio

def generate_receipt(row):
    doc = Document()
    add_official_header_footer(doc)
    doc.add_heading('وصل استلام مبلغ مالي', 1).alignment = WD_ALIGN_PARAGRAPH.CENTER
    nights = calculate_nights(row['check_in'], row['check_out'])
    total = nights * PRICE_PER_NIGHT
    p = doc.add_paragraph(f"\nاستلمنا من السيد(ة): {row['full_name']}\n")
    p.add_run(f"مبلغ قدره: {total} دج (مقابل {nights} ليلة)\n")
    p.add_run(f"بتاريخ: {date.today()}\n")
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio

# ==================== 4. منطق التطبيق والواجهة ====================

if 'authenticated' not in st.session_state: st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<div class="main-title">🏨 إدارة بيت الشباب محمدي يوسف</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        role = st.selectbox("🔑 الصفة", ["مدير", "عون استقبال"])
        pwd = st.text_input("🔒 كلمة السر", type="password")
        if st.button("🚀 دخول", use_container_width=True):
            if (role == "مدير" and pwd == MANAGER_PASSWORD) or (role == "عون استقبال" and pwd == RECEPTION_PASSWORD):
                st.session_state.authenticated = True
                st.session_state.role = role
                st.rerun()
            else: st.error("❌ خطأ")
    st.stop()

tabs = st.tabs(["➕ حجز جديد", "🛌 حالة الغرف", "📋 السجل العام", "📄 تصدير Word", "👥 الأفواج", "💰 الحسابات", "⚙️ الإعدادات"])
df_bookings = pd.read_sql("SELECT * FROM bookings", get_db())
today = date.today()

# --- 1. حجز جديد ---
with tabs[0]:
    with st.form("new_booking"):
        st.markdown("### 👤 بيانات النزيل")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("الاسم واللقب *")
            cb1, cb2 = st.columns(2)
            b_date = cb1.date_input("تاريخ الازدياد", date(2000,1,1))
            b_place = cb2.text_input("مكان الازدياد")
            address = st.text_input("العنوان")
        with col2:
            id_val = st.text_input("رقم البطاقة *")
            wing = st.selectbox("الجناح", ["جناح ذكور", "جناح إناث"])
            room = st.text_input("الغرفة (مثال: غرفة 01)")
            bed = st.selectbox("السرير", [f"سرير {i+1}" for i in range(6)])
            d_in = st.date_input("الدخول", today)
            d_out = st.date_input("الخروج", today + timedelta(days=1))
        
        if st.form_submit_button("✅ حفظ الحجز"):
            conn = get_db()
            conn.execute("INSERT INTO bookings (full_name, birth_date, birth_place, address, id_number, wing, room, bed, check_in, check_out, legal_status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                         (name, b_date, b_place, address, id_val, wing, room, bed, d_in, d_out, "عادي"))
            conn.commit()
            st.success("تم الحفظ!")
            st.rerun()

# --- 2. حالة الغرف ---
with tabs[1]:
    st.subheader("🛌 توزيع الأسرّة")
    # عرض الأسرّة (نظام المربعات الملونة)

# --- 3. السجل ---
with tabs[2]:
    st.dataframe(df_bookings, use_container_width=True)

# --- 4. التصدير (طلبك الأساسي) ---
with tabs[3]:
    st.subheader("📄 مركز الوثائق الرسمية")
    if df_bookings.empty: st.warning("لا توجد بيانات")
    else:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📊 تحميل جدول النزلاء (التقرير الكلي)"):
                st.download_button("⬇️ اضغط للتحميل", generate_report_table(df_bookings), "تقرير_النزلاء.docx")
        with c2:
            sel_name = st.selectbox("اختر نزيل", df_bookings['full_name'].unique())
            row = df_bookings[df_bookings['full_name'] == sel_name].iloc[0]
            if st.button("👮 استمارة الشرطة"):
                st.download_button("⬇️ تحميل الاستمارة", generate_police_form(row), f"شرطة_{sel_name}.docx")
            if st.button("🧾 وصل استلام (400 دج)"):
                st.download_button("⬇️ تحميل الوصل", generate_receipt(row), f"وصل_{sel_name}.docx")

# --- 5. الحسابات ---
with tabs[5]:
    df_bookings['nights'] = df_bookings.apply(lambda r: calculate_nights(r['check_in'], r['check_out']), axis=1)
    total_rev = df_bookings['nights'].sum() * PRICE_PER_NIGHT
    st.metric("إجمالي المداخيل", f"{total_rev} دج")

# --- تذييل الصفحة ---
st.markdown(f'<div class="developer-footer">🛠️ تطوير: <b>®ridha_merzoug®</b> | 📍 بيت شباب محمدي يوسف قالمة - 2026 ✨</div>', unsafe_allow_html=True)
