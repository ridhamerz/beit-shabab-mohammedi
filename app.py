import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. إعدادات الصفحة والتنسيق الجمالي
st.set_page_config(page_title="نظام استقبال بيت الشباب", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
    * { font-family: 'Noto Sans Arabic', sans-serif; direction: RTL; }
    .alarm-banner {
        background-color: #ff4b4b; color: white; padding: 15px;
        border-radius: 10px; border-left: 10px solid #8B0000;
        animation: blinker 1.5s linear infinite; font-weight: bold;
        text-align: center; margin-bottom: 20px;
    }
    @keyframes blinker { 50% { opacity: 0.6; } }
    .room-box {
        display: inline-block; width: 70px; height: 70px; margin: 5px;
        border-radius: 12px; text-align: center; line-height: 70px;
        color: white; font-weight: bold; font-size: 1.1em;
    }
    .free { background-color: #28a745; box-shadow: 0 4px #1e7e34; }
    .occupied { background-color: #dc3545; box-shadow: 0 4px #a71d2a; }
    .developer-footer {
        background: linear-gradient(45deg, #1e3c72, #2a5298);
        padding: 20px; border-radius: 15px; color: white;
        text-align: center; font-weight: bold; margin-top: 50px;
    }
    .dev-name { color: #00d4ff; font-size: 1.2em; text-shadow: 1px 1px 2px black; }
    </style>
    """, unsafe_allow_html=True)

# 2. إدارة الحالة الأمنية والبيانات
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
    st.session_state.db = pd.DataFrame(columns=[
        'الاسم', 'اللقب', 'رقم الغرفة', 'التصنيف', 'الجنسية', 'الليالي', 'المبلغ', 'تاريخ الخروج'
    ])

# 3. نظام الحماية وقفل البرنامج
if st.session_state.lock_until and datetime.now() < st.session_state.lock_until:
    remaining = int((st.session_state.lock_until - datetime.now()).total_seconds())
    st.error(f"⚠️ البرنامج مغلق بسبب محاولات خاطئة. انتظر {remaining} ثانية.")
    st.stop()

# 4. واجهة تسجيل الدخول
if not st.session_state.authenticated:
    st.title("🔐 تسجيل الدخول - نظام محمدي يوسف")
    col_login, _ = st.columns([1, 1])
    with col_login:
        role = st.selectbox("الصفة", ["مدير", "عون استقبال"])
        pwd = st.text_input("كلمة السر", type="password")
        if st.button("دخول"):
            if pwd == st.session_state.passwords[role]:
                st.session_state.authenticated, st.session_state.user_role = True, role
                st.session_state.login_attempts = 0
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                if st.session_state.login_attempts >= 3:
                    st.session_state.lock_until = datetime.now() + timedelta(minutes=1)
                    st.rerun()
                else: st.warning(f"كلمة سر خاطئة! المتبقي: {3 - st.session_state.login_attempts}")
    st.stop()

# 5. التنبيه الصلب (Alarm)
today = datetime.now().date()
overdue_list = st.session_state.db[st.session_state.db['تاريخ الخروج'] <= today]
if not overdue_list.empty:
    st.markdown(f'<div class="alarm-banner">🚨 تنبيه: يوجد {len(overdue_list)} نزلاء انتهت مدة إقامتهم ويجب الإخلاء فوراً!</div>', unsafe_allow_html=True)

# 6. واجهة البرنامج الرئيسية
st.sidebar.title(f"👤 {st.session_state.user_role}")
if st.sidebar.button("خروج"):
    st.session_state.authenticated = False
    st.rerun()

tabs = st.tabs(["➕ تسجيل جديد", "📋 قائمة النزلاء", "🗺️ خريطة الغرف", "⚙️ الإعدادات"])

# التبويب الأول: التسجيل
with tabs[0]:
    st.subheader("📝 إدخال بيانات النزيل")
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم", key="n")
            last_name = st.text_input("اللقب", key="ln")
            dob = st.date_input("تاريخ الميلاد", value=datetime(2000,1,1))
            room = st.selectbox("رقم الغرفة", [f"غرفة {i}" for i in range(1, 21)])
        with c2:
            nation = st.selectbox("الجنسية", ["جزائرية", "أخرى"])
            nights = st.number_input("عدد الليالي", min_value=1, value=1)
            is_free = st.checkbox("إقامة مجانية")
        
        if st.button("✅ تأكيد الحجز وحفظ البيانات", use_container_width=True):
            if name and last_name:
                age = (datetime.now().date() - dob).days // 365
                category = "طفل" if age < 18 else ("أجنبي" if nation != "جزائرية" else "بالغ")
                price = 0 if is_free else (nights * 400)
                exit_d = datetime.now().date() + timedelta(days=nights)
                
                new_row = {
                    'الاسم': name, 'اللقب': last_name, 'رقم الغرفة': room,
                    'التصنيف': category, 'الجنسية': nation, 'الليالي': nights,
                    'المبلغ': price, 'تاريخ الخروج': exit_d
                }
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"تم تسجيل {name} بنجاح. المبلغ: {price} دج")
            else: st.error("يرجى ملء الاسم واللقب")

# التبويب الثاني: السجل مع الحذف
with tabs[1]:
    st.subheader("📋 سجل الحجوزات الحالي")
    if not st.session_state.db.empty:
        for i, row in st.session_state.db.iterrows():
            col_txt, col_btn = st.columns([5, 1])
            col_txt.write(f"**{row['الاسم']} {row['اللقب']}** - {row['رقم الغرفة']} (المغادرة: {row['تاريخ الخروج']})")
            if st.session_state.user_role == "مدير":
                if col_btn.button("🗑️ حذف", key=f"del_{i}"):
                    st.session_state.db = st.session_state.db.drop(i)
                    st.rerun()
    else: st.info("السجل فارغ حالياً.")

# التبويب الثالث: الخريطة
with tabs[2]:
    st.subheader("🗺️ الحالة البصرية للغرف")
    occ_rooms = st.session_state.db['رقم الغرفة'].values
    cols = st.columns(5)
    for i in range(1, 21):
        r_n = f"غرفة {i}"
        cls = "occupied" if r_n in occ_rooms else "free"
        cols[(i-1)%5].markdown(f'<div class="room-box {cls}">{i}</div>', unsafe_allow_html=True)

# التبويب الرابع: الإعدادات
with tabs[3]:
    if st.session_state.user_role == "مدير":
        st.subheader("⚙️ تغيير كلمات السر")
        target = st.selectbox("تغيير لـ", ["مدير", "عون استقبال"])
        new_p = st.text_input("كلمة السر الجديدة", type="password")
        if st.button("تحديث"):
            st.session_state.passwords[target] = new_p
            st.success("تم التحديث!")
    else: st.info("الإعدادات متاحة للمدير فقط.")

# تذييل المطور
st.markdown(f"""
    <div class="developer-footer">
        Developer <span class="dev-name">®ridha_merzoug®</span> [رضا مرزوق]
    </div>
    """, unsafe_allow_html=True)
