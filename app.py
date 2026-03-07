import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="نظام استقبال بيت الشباب", layout="wide")

# 2. التأكد من وجود قاعدة البيانات في الذاكرة
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['الاسم', 'اللقب', 'رقم الغرفة', 'تاريخ الخروج', 'المبلغ'])

# 3. واجهة البرنامج الرئيسية
st.title("🏨 نظام إدارة بيت شباب محمدي يوسف")

# إنشاء التبويبات بشكل صريح
tab_reg, tab_view, tab_map = st.tabs(["➕ تسجيل نزيل جديد", "📋 قائمة الحجوزات", "🗺️ خريطة الغرف"])

# --- التبويب الأول: التسجيل (تأكد من وجود الخانات هنا) ---
with tab_reg:
    st.subheader("📝 إدخال بيانات النزيل")
    
    # استخدام حاوية (Container) لضمان ظهور العناصر
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("الاسم الشخصي", key="name_input")
            last_name = st.text_input("اللقب العائلي", key="last_name_input")
            room = st.selectbox("رقم الغرفة", [f"غرفة {i}" for i in range(1, 21)], key="room_select")
        
        with col2:
            nights = st.number_input("عدد الليالي", min_value=1, value=1, key="nights_input")
            nation = st.selectbox("الجنسية", ["جزائرية", "أجنبية"], key="nation_select")
            is_free = st.checkbox("إقامة مجانية", key="free_check")

        # زر الحفظ
        if st.button("✅ حفظ الحجز في القائمة", use_container_width=True):
            if name and last_name: # التأكد من ملء البيانات الأساسية
                price = 0 if is_free else (nights * 400)
                exit_date = datetime.now().date() + timedelta(days=nights)
                
                new_data = {
                    'الاسم': name, 'اللقب': last_name, 'رقم الغرفة': room,
                    'تاريخ الخروج': exit_date, 'المبلغ': price
                }
                
                # إضافة البيانات للجلسة
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_data])], ignore_index=True)
                st.success(f"تم تسجيل {name} بنجاح في {room}")
            else:
                st.error("الرجاء إدخال الاسم واللقب!")

# --- التبويب الثاني: عرض البيانات ---
with tab_view:
    st.subheader("📋 السجل الحالي للنزلاء")
    if not st.session_state.db.empty:
        st.table(st.session_state.db) # عرض الجدول بشكل بسيط وواضح
    else:
        st.info("لا يوجد نزلاء مسجلين حالياً. قم بالتسجيل من التبويب الأول.")

# --- التبويب الثالث: الخريطة ---
with tab_map:
    st.subheader("🗺️ حالة الغرف")
    occupied = st.session_state.db['رقم الغرفة'].values
    cols = st.columns(5)
    for i in range(1, 21):
        r_name = f"غرفة {i}"
        color = "🔴" if r_name in occupied else "🟢"
        cols[(i-1)%5].info(f"{color} {r_name}")

# تذييل المطور
st.markdown("---")
st.markdown("<center>Developer <b>®ridha_merzoug®</b> [رضا مرزوق]</center>", unsafe_allow_html=True)
