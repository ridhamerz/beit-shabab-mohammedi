import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# إعداد الصفحة والتنسيق الجمالي
st.set_page_config(page_title="بيت شباب محمدي يوسف قالمة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: RTL; }
    .main-title { background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; font-size: 1.3rem; font-weight: bold; }
    .bed-box { display: inline-block; width: 45px; height: 35px; margin: 3px; border-radius: 5px; text-align: center; line-height: 35px; color: white; font-size: 0.8rem; font-weight: bold; }
    .free { background-color: #28a745; border-bottom: 3px solid #1e7e34; }
    .occupied { background-color: #dc3545; border-bottom: 3px solid #a71d2a; }
    .wing-header { background-color: #e9ecef; padding: 8px; border-radius: 8px; margin-top: 15px; border-right: 5px solid #1e3c72; font-weight: bold; }
    .developer-footer { background: #1e3c72; color: #ffffff; padding: 6px; border-radius: 10px; text-align: center; margin-top: 30px; font-size: 0.75rem; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">®® برنامج بيت الشباب محمدي يوسف قالمة®®</div>', unsafe_allow_html=True)

# هيكلة الغرف والأسرة
wings = {
    "جناح ذكور": {
        "غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6,
        "مرقد ذكور 01": 3, "مرقد ذكور 02": 4
    },
    "جناح إناث": {
        "غرفة 06": 2, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6,
        "مرقد إناث 01": 3, "مرقد إناث 02": 4
    }
}

# إدارة البيانات
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=[
        'الاسم واللقب', 'تاريخ ومكان الازدياد', 'العنوان الشخصي', 
        'رقم ونوع بطاقة التعريف', 'المهنة', 'عدد الليالي', 'الجناح', 'الغرفة', 'السرير', 'تاريخ الخروج'
    ])

tabs = st.tabs(["📋 السجل والطباعة", "➕ حجز جديد", "📊 عدد الغرف", "⚙️ الإعدادات"])

# --- 1. تبويب السجل والطباعة ---
with tabs[0]:
    st.subheader("📋 قائمة النزلاء الحالية")
    if not st.session_state.db.empty:
        for i, row in st.session_state.db.iterrows():
            with st.expander(f"👤 {row['الاسم واللقب']} - {row['الغرفة']} ({row['السرير']})"):
                col_info, col_print = st.columns([3, 1])
                with col_info:
                    st.write(f"**العنوان:** {row['العنوان الشخصي']}")
                    st.write(f"**البطاقة:** {row['رقم ونوع بطاقة التعريف']}")
                with col_print:
                    # ميزة الطباعة (محاكاة توليد نص الورقة للطباعة السريعة)
                    report_text = f"""
                    مؤسسة بيت الشباب محمدي يوسف - قالمة
                    ----------------------------------
                    ورقة مبيت نزيل
                    الاسم واللقب: {row['الاسم واللقب']}
                    تاريخ الازدياد: {row['تاريخ ومكان الازدياد']}
                    العنوان: {row['العنوان الشخصي']}
                    رقم البطاقة: {row['رقم ونوع بطاقة التعريف']}
                    المهنة: {row['المهنة']}
                    الجناح: {row['الجناح']} | الغرفة: {row['الغرفة']} | السرير: {row['السرير']}
                    تاريخ الخروج: {row['تاريخ الخروج']}
                    ----------------------------------
                    توقيع المستلم: ...........
                    """
                    st.download_button(f"📥 تحميل ورقة المبيت #{i+1}", report_text, file_name=f"guest_{i}.txt")
                    if st.button("🗑️ حذف الحجز", key=f"del_{i}"):
                        st.session_state.db = st.session_state.db.drop(i)
                        st.rerun()
    else:
        st.info("لا يوجد نزلاء حالياً.")

# --- 2. تبويب حجز جديد ---
with tabs[1]:
    st.markdown("#### 📝 إدخال بيانات ورقة المبيت")
    with st.form("pro_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            f_name = st.text_input("الاسم واللقب")
            b_info = st.text_input("تاريخ ومكان الازدياد")
            addr = st.text_input("العنوان الشخصي الكامل")
            id_val = st.text_input("رقم ونوع بطاقة التعريف (ب.ت.و / جواز سفر)")
        with c2:
            job_val = st.text_input("المهنة")
            n_nights = st.number_input("عدد الليالي", min_value=1, value=1)
            w_choice = st.selectbox("الجناح", list(wings.keys()))
            r_choice = st.selectbox("الغرفة", list(wings[w_choice].keys()))
            b_choice = st.selectbox("السرير", [f"سرير {i+1}" for i in range(wings[w_choice][r_choice])])

        if st.form_submit_button("💾 حفظ الحجز وتجهيز الورقة"):
            if f_name and id_val:
                new_entry = {
                    'الاسم واللقب': f_name, 'تاريخ ومكان الازدياد': b_info,
                    'العنوان الشخصي': addr, 'رقم ونوع بطاقة التعريف': id_val,
                    'المهنة': job_val, 'عدد الليالي': n_nights, 'الجناح': w_choice,
                    'الغرفة': r_choice, 'السرير': b_choice,
                    'تاريخ الخروج': datetime.now().date() + timedelta(days=n_nights)
                }
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_entry])], ignore_index=True)
                st.success("تم الحفظ! يمكنك الآن التوجه لتبويب السجل لطباعة الورقة.")
            else:
                st.error("الرجاء ملء الاسم ورقم الهوية على الأقل.")

# --- 3. تبويب عدد الغرف (تعبئة تلقائية) ---
with tabs[2]:
    st.markdown("#### 📊 حالة الأجنحة والأسرة (محدثة تلقائياً)")
    for wing, rooms in wings.items():
        st.markdown(f'<div class="wing-header">{wing}</div>', unsafe_allow_html=True)
        for room, bed_count in rooms.items():
            cols = st.columns([1, 5])
            cols[0].write(f"**{room}**")
            beds_html = ""
            for b in range(1, bed_count + 1):
                b_name = f"سرير {b}"
                is_occupied = not st.session_state.db[
                    (st.session_state.db['الجناح'] == wing) & 
                    (st.session_state.db['الغرفة'] == room) & 
                    (st.session_state.db['السرير'] == b_name)
                ].empty
                st_class = "occupied" if is_occupied else "free"
                beds_html += f'<div class="bed-box {st_class}">{b}</div>'
            cols[1].markdown(beds_html, unsafe_allow_html=True)

# --- تذييل المطور (أنيق وصغير) ---
st.markdown(f"""
    <div class="developer-footer">
        Developer <span style="color:#00d4ff;">®ridha_merzoug®</span> [رضا مرزوق]
    </div>
    """, unsafe_allow_html=True)
