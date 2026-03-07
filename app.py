import streamlit as st
import pandas as pd
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="نظام استقبال بيت الشباب", layout="wide")

# --- منطق الحماية والدخول ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_role = None

def login():
    st.title("🔐 تسجيل الدخول للنظام")
    user = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة السر", type="password")
    if st.button("دخول"):
        if user == "admin" and password == "1234":
            st.session_state.authenticated = True
            st.session_state.user_role = "admin"
            st.rerun()
        elif user == "reception" and password == "5678":
            st.session_state.authenticated = True
            st.session_state.user_role = "receptionist"
            st.rerun()
        else:
            st.error("بيانات الدخول غير صحيحة")

if not st.session_state.authenticated:
    login()
    st.stop()

# --- إدارة البيانات ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=[
        'الاسم', 'اللقب', 'تاريخ الميلاد', 'التصنيف', 'الجنسية', 'الليالي', 'المبلغ', 'التاريخ'
    ])

# --- واجهة البرنامج ---
st.sidebar.title(f"مرحباً: {st.session_state.user_role}")
if st.sidebar.button("تسجيل الخروج"):
    st.session_state.authenticated = False
    st.rerun()

st.title("🏨 نظام إدارة بيت شباب محمدي يوسف")

# تحديد التبويبات بناءً على الصلاحية
tabs_list = ["➕ تسجيل حجز", "📋 قائمة الحجوزات"]
if st.session_state.user_role == "admin":
    tabs_list.append("📊 الإحصائيات والمالية")

tabs = st.tabs(tabs_list)

# 1. تبويب التسجيل
with tabs[0]:
    with st.form("booking_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("الاسم")
            last_name = st.text_input("اللقب")
            dob = st.date_input("تاريخ الميلاد", min_value=datetime(1940, 1, 1))
        with col2:
            nation = st.selectbox("الجنسية", ["جزائرية", "تونسية", "فرنسية", "أخرى"])
            is_free = st.checkbox("إقامة مجانية")
            nights = st.number_input("عدد الليالي", min_value=1, value=1)
        
        submit = st.form_submit_button("حفظ البيانات")
        
        if submit:
            # حساب العمر
            age = (datetime.now().date() - dob).days // 365
            category = "طفل" if age < 18 else ("أجنبي" if nation != "جزائرية" else "بالغ")
            
            # حساب السعر
            price = 0 if is_free else (nights * 400)
            
            new_data = {
                'الاسم': name, 'اللقب': last_name, 'تاريخ الميلاد': dob,
                'التصنيف': category, 'الجنسية': nation, 
                'الليالي': nights, 'المبلغ': price, 'التاريخ': datetime.now().date()
            }
            st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_data])], ignore_index=True)
            st.success(f"تم التسجيل: {category} - المبلغ: {price} دج")

# 2. تبويب قائمة الحجوزات (مع التعديل والحذف للمدير)
with tabs[1]:
    st.subheader("📋 سجل الحجوزات")
    df = st.session_state.db
    if not df.empty:
        for index, row in df.iterrows():
            col_data, col_edit, col_del = st.columns([6, 1, 1])
            col_data.write(f"**{row['الاسم']} {row['اللقب']}** | {row['التصنيف']} | {row['المبلغ']} دج")
            
            if st.session_state.user_role == "admin":
                if col_edit.button("📝", key=f"edit_{index}"):
                    st.info("ميزة التعديل السريع قيد التفعيل")
                if col_del.button("🗑️", key=f"del_{index}"):
                    st.session_state.db = st.session_state.db.drop(index)
                    st.rerun()
    else:
        st.write("لا توجد حجوزات حالياً.")

# 3. تبويب الإحصائيات (للمدير فقط)
if st.session_state.user_role == "admin":
    with tabs[2]:
        st.subheader("📊 التقارير المالية والعددية")
        res = st.session_state.db
        if not res.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي المداخيل", f"{res['المبلغ'].sum()} دج")
            c2.metric("عدد الأجانب", len(res[res['التصنيف'] == "أجنبي"]))
            c3.metric("عدد الأطفال", len(res[res['التصنيف'] == "طفل"]))

# تذييل الصفحة باسمك
st.markdown("---")
st.markdown("<center>المطور: <b>ridha_merzoug</b></center>", unsafe_allow_html=True)
