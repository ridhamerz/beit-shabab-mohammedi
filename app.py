import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# إعداد الصفحة لتكون مريحة للعين
st.set_page_config(page_title="نظام استقبال بيت الشباب", layout="centered")

# تنسيق CSS احترافي لترتيب الواجهة
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
    * { font-family: 'Noto Sans Arabic', sans-serif; direction: RTL; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #f0f2f6; border-radius: 10px; padding: 10px 20px; color: #31333F;
    }
    .stTabs [aria-selected="true"] { background-color: #007BFF !important; color: white !important; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e6e9ef; padding: 15px; border-radius: 15px; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# تهيئة البيانات
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=[
        'الاسم', 'اللقب', 'الجنس', 'الفئة', 'الجنسية', 'الليالي', 'المبلغ', 'التاريخ'
    ])

st.title("🏨 إدارة حجوزات بيت الشباب")
st.write("---")

# تقسيم البرنامج إلى أقسام واضحة (Tabs)
tab1, tab2, tab3 = st.tabs(["➕ تسجيل جديد", "📋 سجل النزلاء", "📊 الإحصائيات والمالية"])

with tab1:
    st.subheader("📝 استمارة التسجيل")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("الاسم الشخصي")
            gender = st.radio("الجنس", ["ذكر", "أنثى"], horizontal=True)
            category = st.selectbox("تصنيف النزيل", ["بالغ", "طفل", "مقيم مجاني"])
        with col2:
            last_name = st.text_input("اللقب العائلي")
            nationality = st.selectbox("الجنسية", ["جزائرية", "أخرى"])
            price = st.number_input("المبلغ المؤدى (دج)", min_value=0)
        
        nights = st.slider("عدد الليالي", 1, 30, 1)
        
        if st.button("حفظ الحجز الآن", use_container_width=True):
            new_entry = {
                'الاسم': name, 'اللقب': last_name, 'الجنس': gender, 
                'الفئة': category, 'الجنسية': nationality, 
                'الليالي': nights, 'المبلغ': price, 'التاريخ': datetime.now().date()
            }
            st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("تم الحفظ بنجاح")

with tab2:
    st.subheader("📂 قائمة النزلاء المسجلين")
    if not st.session_state.db.empty:
        # إضافة شريط بحث بسيط فوق الجدول
        search = st.text_input("🔍 ابحث عن اسم أو لقب...")
        filtered_df = st.session_state.db[st.session_state.db['الاسم'].str.contains(search) | st.session_state.db['اللقب'].str.contains(search)]
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info("السجل فارغ حالياً.")

with tab3:
    st.subheader("📈 الملخص العام")
    df = st.session_state.db
    if not df.empty:
        # عرض المربعات الإحصائية بشكل أنيق
        m1, m2, m3 = st.columns(3)
        m1.metric("إجمالي النزلاء", len(df))
        m2.metric("إجمالي المداخيل", f"{df['المبلغ'].sum()} دج")
        m3.metric("المقيمين مجاناً", len(df[df['الفئة'] == "مقيم مجاني"]))
        
        st.write("---")
        # رسومات بيانية بسيطة وغير مزدحمة
        c1, c2 = st.columns(2)
        with c1:
            fig_g = px.pie(df, names='الجنس', title="نسبة الذكور والإناث", hole=0.4)
            st.plotly_chart(fig_g, use_container_width=True)
        with c2:
            fig_n = px.bar(df, x='الفئة', title="توزيع الفئات")
            st.plotly_chart(fig_n, use_container_width=True)
    else:
        st.warning("لا توجد بيانات كافية لعرض الإحصائيات.")

st.markdown("<br><hr><center><small>نظام إدارة بيت الشباب | ridha_merzoug</small></center>", unsafe_allow_html=True)
