import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# إعدادات الصفحة والواجهة
st.set_page_config(page_title="نظام إدارة الحجوزات", layout="wide")

# تنسيق CSS لدعم اللغة العربية والواجهة الجميلة
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# تهيئة مخزن البيانات (في بيئة حقيقية يفضل ربطه بـ Google Sheets أو SQL)
if 'bookings' not in st.session_state:
    st.session_state.bookings = pd.DataFrame(columns=[
        'الاسم', 'اللقب', 'تاريخ الازدياد', 'مكان الازدياد', 'العنوان', 
        'رقم الهوية', 'المهنة', 'الجنسية', 'الفئة', 'الجنس', 
        'عدد الليالي', 'المبلغ المدفوع', 'تاريخ الحجز', 'ملاحظات'
    ])

# العنوان الرئيسي
st.title("🏨 نظام إدارة الحجوزات المتطور")
st.markdown("---")

# تقسيم الشاشة: نموذج الإدخال والإحصائيات
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📝 إدخال بيانات النزيل")
    with st.form("booking_form", clear_on_submit=True):
        name = st.text_input("الاسم")
        last_name = st.text_input("اللقب")
        dob = st.date_input("تاريخ الازدياد", min_value=datetime(1940, 1, 1))
        pob = st.text_input("مكان الازدياد")
        address = st.text_area("العنوان الشخصي")
        id_card = st.text_input("رقم بطاقة التعريف")
        job = st.text_input("المهنة")
        nationality = st.selectbox("الجنسية", ["جزائرية", "أخرى"])
        
        c1, c2 = st.columns(2)
        with c1:
            category = st.selectbox("الفئة", ["بالغ", "طفل", "مقيم مجاني"])
            gender = st.selectbox("الجنس", ["ذكر", "أنثى"])
        with c2:
            nights = st.number_input("عدد الليالي", min_value=1, step=1)
            price = st.number_input("المبلغ الإجمالي (دج)", min_value=0, step=100)
        
        notes = st.text_area("ملاحظات")
        
        submit = st.form_submit_button("حفظ الحجز")
        
        if submit:
            new_data = {
                'الاسم': name, 'اللقب': last_name, 'تاريخ الازدياد': dob,
                'مكان الازدياد': pob, 'العنوان': address, 'رقم الهوية': id_card,
                'المهنة': job, 'الجنسية': nationality, 'الفئة': category,
                'الجنس': gender, 'عدد الليالي': nights, 'المبلغ المدفوع': price,
                'تاريخ الحجز': datetime.now().date(), 'ملاحظات': notes
            }
            st.session_state.bookings = pd.concat([st.session_state.bookings, pd.DataFrame([new_data])], ignore_index=True)
            st.success("تم تسجيل الحجز بنجاح!")

with col2:
    st.subheader("📊 لوحة الإحصائيات (الشهري واليومي)")
    df = st.session_state.bookings
    
    if not df.empty:
        # حسابات سريعة
        today = datetime.now().date()
        daily_df = df[df['تاريخ الحجز'] == today]
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("نزلاء اليوم", len(daily_df))
        m2.metric("مدخول اليوم", f"{daily_df['المبلغ المدفوع'].sum()} دج")
        m3.metric("نزلاء الشهر", len(df))
        m4.metric("مدخول الشهر", f"{df['المبلغ المدفوع'].sum()} دج")

        # رسومات بيانية
        st.markdown("---")
        g1, g2 = st.columns(2)
        
        with g1:
            # توزيع الجنس
            fig_gender = px.pie(df, names='الجنس', title='توزيع الجنس (ذكر/أنثى)')
            st.plotly_chart(fig_gender, use_container_width=True)
            
        with g2:
            # توزيع الفئات (أطفال، أجانب، مجاني)
            fig_cat = px.bar(df, x='الفئة', color='الجنسية', title='توزيع الفئات والجنسيات')
            st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("لا توجد بيانات لعرض الإحصائيات حالياً.")

# عرض الجدول الرئيسي
st.markdown("---")
st.subheader("📋 سجل الحجوزات الكامل")
st.dataframe(st.session_state.bookings, use_container_width=True)

# إضافة تذييل باسمك كما تفضل دائماً
st.markdown(f"""
    <div style='text-align: center; color: grey; padding: 20px;'>
        المطور: ridha_merzoug | نظام إدارة بيت الشباب
    </div>
    """, unsafe_allow_html=True)
        
