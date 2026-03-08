import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
from fpdf import FPDF
import io

# ────────────────────────────────────────────────
#                إعداد الصفحة والـ CSS
# ────────────────────────────────────────────────
st.set_page_config(page_title="نظام بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    * { font-family: 'Tahoma', 'Arial', sans-serif; direction: RTL; text-align: right; }
    .main-title { 
        background: linear-gradient(90deg, #1e3c72, #2a5298); 
        color: white; padding: 20px; border-radius: 15px; 
        text-align: center; margin-bottom: 25px; 
        font-size: 1.6rem; font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .developer-footer { 
        background: #1e3c72; color: #ffffff; padding: 8px; 
        border-radius: 10px; text-align: center; margin-top: 50px; 
        font-size: 0.8rem; border: 1px solid #00d4ff;
    }
    .success-box {
        background: #d4edda; color: #155724; padding: 1.5rem; 
        border-radius: 10px; border: 1px solid #c3e6cb; 
        margin: 1.5rem 0; text-align: center;
    }
    .minor-box {
        background: #fff3cd; border-color: #ffc107;
        padding: 1rem; border-radius: 8px; margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               قاعدة البيانات
# ────────────────────────────────────────────────
DB_FILE = 'youth_hostel.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS current_guests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, prenom TEXT, nom_jeune_fille TEXT,
        date_naissance TEXT, lieu_naissance TEXT,
        nom_pere TEXT, profession TEXT, adresse TEXT,
        nationalite TEXT, nature_doc TEXT, num_doc TEXT,
        date_emission TEXT, num_arrivee TEXT, duree_sejour INTEGER,
        phone TEXT, notes TEXT, status TEXT DEFAULT 'مقيم'
    )''')
    conn.commit()
    conn.close()

init_db()

# ────────────────────────────────────────────────
#               دالة توليد PDF (بطاقة المسافر الرسمية)
# ────────────────────────────────────────────────
def generate_voyageur_pdf(data):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # عنوان البطاقة
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "بطاقة المسافر - Fiche de Voyageur", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, "بيت الشباب محمدي يوسف - قالمة", ln=True, align='C')
    pdf.ln(5)

    # الجدول
    pdf.set_font("Arial", '', 11)
    col_width = 95

    fields = [
        ("الاسم", data.get("nom", "")),
        ("اللقب", data.get("prenom", "")),
        ("اللقب قبل الزواج", data.get("nom_jeune_fille", "")),
        ("تاريخ الازدياد", data.get("date_naissance", "")),
        ("مكان الازدياد", data.get("lieu_naissance", "")),
        ("اسم الأب", data.get("nom_pere", "")),
        ("المهنة", data.get("profession", "")),
        ("العنوان", data.get("adresse", "")),
        ("الجنسية", data.get("nationalite", "الجزائرية")),
        ("نوع الوثيقة", data.get("nature_doc", "")),
        ("رقم الوثيقة", data.get("num_doc", "")),
        ("صادرة في", data.get("date_emission", "")),
        ("رقم الوصول", data.get("num_arrivee", "")),
        ("مدة الإقامة", f"{data.get('duree_sejour', '')} يوم"),
    ]

    for label, value in fields:
        pdf.cell(col_width, 10, label + " : ", border=1)
        pdf.cell(col_width, 10, str(value), border=1, ln=True)

    pdf.ln(10)
    pdf.cell(0, 10, "التوقيع : ..............................................", ln=True)

    # حفظ الـ PDF في الذاكرة
    pdf_output = io.BytesIO()
    pdf.output(pdf_output, 'S')
    pdf_output.seek(0)
    return pdf_output

# ────────────────────────────────────────────────
#               باقي الكود (الجلسة، تسجيل الدخول، إلخ)
# ────────────────────────────────────────────────
# ... (الجزء الخاص بالجلسة والأجنحة وتسجيل الدخول كما في النسخ السابقة)

# تبويب الحجز الجديد
with tabs[0]:
    st.markdown('<h3 style="color:#1e3c72; text-align:center;">➕ تسجيل نزيل جديد - بطاقة المسافر الرسمية</h3>', unsafe_allow_html=True)

    with st.form("official_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("الاسم (Nom)")
            prenom = st.text_input("اللقب (Prénom)")
            nom_jeune_fille = st.text_input("اللقب قبل الزواج (Nom de Jeune fille)")
            date_naissance = st.date_input("تاريخ الازدياد")
            lieu_naissance = st.text_input("مكان الازدياد")

        with col2:
            nom_pere = st.text_input("اسم الأب")
            profession = st.text_input("المهنة")
            adresse = st.text_input("العنوان")
            nationalite = st.text_input("الجنسية", value="الجزائرية")

        st.markdown("---")
        colA, colB = st.columns(2)
        with colA:
            nature_doc = st.selectbox("نوع الوثيقة", ["بطاقة التعريف", "جواز سفر", "رخصة سياقة"])
            num_doc = st.text_input("رقم الوثيقة")
        with colB:
            date_emission = st.date_input("صادرة في")
            num_arrivee = st.text_input("رقم الوصول")
            duree_sejour = st.number_input("مدة الإقامة (أيام)", min_value=1, value=1)

        submitted = st.form_submit_button("💾 تأكيد الحجز", type="primary", use_container_width=True)

        if submitted:
            if not nom or not prenom or not num_doc:
                st.error("يرجى ملء الحقول الإجبارية")
            else:
                st.success("تم التسجيل بنجاح!")

                # زر طباعة PDF
                data = {
                    "nom": nom, "prenom": prenom, "nom_jeune_fille": nom_jeune_fille,
                    "date_naissance": date_naissance, "lieu_naissance": lieu_naissance,
                    "nom_pere": nom_pere, "profession": profession, "adresse": adresse,
                    "nationalite": nationalite, "nature_doc": nature_doc, "num_doc": num_doc,
                    "date_emission": date_emission, "num_arrivee": num_arrivee,
                    "duree_sejour": duree_sejour
                }

                pdf_file = generate_voyageur_pdf(data)
                st.download_button(
                    label="🖨️ طباعة بطاقة المسافر PDF",
                    data=pdf_file,
                    file_name=f"بطاقة_{nom}_{prenom}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

# تذييل
st.markdown("""
    <div class="developer-footer">
        Developer <span style="color:#00d4ff; font-weight:bold;">®ridha_merzoug®</span> [رضا مرزوق] - 2026
    </div>
""", unsafe_allow_html=True)
