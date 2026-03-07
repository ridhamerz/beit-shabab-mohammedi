import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# إعدادات الصفحة
st.set_page_config(page_title="نظام استقبال بيت الشباب", layout="wide")

# --- إدارة الحالة الأمنية والبيانات ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_role = None
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0
if 'lock_until' not in st.session_state:
    st.session_state.lock_until = None
if 'passwords' not in st.session_state:
    st.session_state.passwords = {"مدير": "1234", "عون استقبال": "5678"}
if 'db' not in st.session_state:
    # بيانات تجريبية لاختبار المنبه (يمكنك مسحها لاحقاً)
    st.session_state.db = pd.DataFrame([
        {'الاسم': 'نزيل', 'اللقب': 'تجريبي', 'رقم الغرفة': 'غرفة 1', 'تاريخ الخروج': datetime.now().date()}
    ])

# --- نظام الحماية (قفل البرنامج) ---
def check_lock():
    if st.session_state.lock_until and datetime.now() < st.session_state.lock_until:
        remaining = int((st.session_state.lock_until - datetime.now()).total_seconds())
        st.error(f"⚠️ البرنامج مغلق بسبب محاولات خاطئة. يرجى الانتظار {remaining} ثانية.")
        st.stop()
    elif st.session_state.lock_until and datetime.now() >= st.session_state.lock_until:
        st.session_state.lock_until = None
        st.session_state.login_attempts = 0

# --- واجهة تسجيل الدخول ---
def login_page():
    check_lock()
    st.title("🔐 بوابة الدخول - بيت شباب محمدي يوسف")
    
    col1, _ = st.columns([1, 1])
    with col1:
        role = st.selectbox("اختر الصفة", ["مدير", "عون استقبال"])
        password = st.text_input("كلمة السر", type="password")
        
        if st.button("تسجيل الدخول"):
            if password == st.session_state.passwords[role]:
                st.session_state.authenticated = True
                st.session_state.user_role = role
                st.session_state.login_attempts = 0
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                if st.session_state.login_attempts >= 3:
                    st.session_state.lock_until = datetime.now() + timedelta(minutes=1)
                    st.error("❌ تجاوزت المحاولات. قفل البرنامج لمدة دقيقة.")
                    st.rerun()
                else:
                    st.warning(f"كلمة سر خاطئة! المتبقي: {3 - st.session_state.login_attempts}")

if not st.session_state.authenticated:
    login_page()
    st.stop()

# --- تنسيقات التنبيه والمطور ---
st.markdown("""
    <style>
    .alarm-banner {
        background-color: #ff4b4b; color: white; padding: 15px;
        border-radius: 10px; border-left: 10px solid #8B0000;
        animation: blinker 1.5s linear infinite; font-weight: bold;
        text-align: center; margin-bottom: 20px;
    }
    @keyframes blinker { 50% { opacity: 0.6; } }
    .developer-footer {
        background: linear-gradient(45deg, #1e3c72, #2a5298);
        padding: 15px; border-radius: 10px; color: white;
        text-align: center; font-weight: bold; margin-top: 50px;
    }
    .dev-name { color: #00d4ff; font-size: 1.1em; }
    </style>
    """, unsafe_allow_html=True)

# --- نظام المنبه الصلب (يظهر للكل) ---
today = datetime.now().date()
overdue = st.session_state.db[st.session_state.db['تاريخ الخروج'] <= today]

if not overdue.empty:
    st.markdown(f"""
        <div class="alarm-banner">
            🚨 تنبيه صلب لـ {st.session_state.user_role}: يوجد {len(overdue)} نزلاء يجب إخلاء غرفهم الآن!
        </div>
    """, unsafe_allow_html=True)

# --- واجهة البرنامج ---
st.sidebar.title(f"👤 {st.session_state.user_role}")
if st.sidebar.button("خروج"):
    st.session_state.authenticated = False
    st.rerun()

tabs = st.tabs(["🏠 الرئيسية", "🗺️ الخريطة", "➕ تسجيل", "📋 السجل", "⚙️ الإعدادات"])

# تبويب الإعدادات (تغيير كلمة السر للمدير فقط)
with tabs[4]:
    if st.session_state.user_role == "مدير":
        st.subheader("⚙️ إعدادات الأمان")
        target = st.selectbox("تغيير كلمة سر لـ:", ["مدير", "عون استقبال"])
        new_p = st.text_input("كلمة السر الجديدة", type="password")
        if st.button("تحديث"):
            st.session_state.passwords[target] = new_p
            st.success(f"تم تغيير كلمة سر {target}")
    else:
        st.info("ℹ️ الإعدادات متاحة للمدير فقط.")

# --- تذييل المطور المميز ---
st.markdown(f"""
    <div class="developer-footer">
        Developer <span class="dev-name">®ridha_merzoug®</span> [رضا مرزوق]
    </div>
    """, unsafe_allow_html=True)
