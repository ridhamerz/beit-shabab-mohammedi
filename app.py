import streamlit as st
import json
from datetime import datetime, date
import pandas as pd
import io
import hashlib
from math import ceil

# --- إعدادات الصفحة ---
st.set_page_config(page_title="إدارة بيت الشباب محمدي يوسف", page_icon="🏢", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');

    /* عام */
    html, body, [class*="css"] {
        direction: rtl;
        text-align: right;
        font-family: 'Cairo', sans-serif;
        background: linear-gradient(135deg, #f0f4ff 0%, #e0eaff 100%);
    }

    /* إخفاء عناصر Streamlit غير مرغوبة */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Headers أنيقة */
    .enhanced-header {
        background: linear-gradient(90deg, #1e40af, #3b82f6);
        color: white;
        padding: 2.5rem 1rem;
        border-radius: 16px;
        margin: 1.5rem 0 2rem;
        box-shadow: 0 6px 12px rgba(30,64,175,0.2);
        text-align: center;
    }
    .enhanced-header h1, .enhanced-header h2 {
        margin: 0;
        font-weight: 700;
    }

    /* Sidebar تحسين */
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-left: 1px solid #e2e8f0;
        box-shadow: -2px 0 10px rgba(0,0,0,0.05);
    }
    .sidebar .sidebar-content {
        padding: 1.5rem 1rem;
    }

    /* أزرار */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        font-weight: 600;
        padding: 0.8rem;
        transition: all 0.3s ease;
        border: none;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .stButton>button[kind="primary"] {
        background: #22c55e !important;
        color: white !important;
    }

    /* كروت الغرف والنزلاء */
    .room-card, .resident-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        transition: all 0.25s ease;
    }
    .room-card:hover, .resident-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }

    /* جدول الإحصائيات */
    .stats-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 1.5rem 0;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .stats-table th, .stats-table td {
        padding: 1rem;
        text-align: right;
        border-bottom: 1px solid #e2e8f0;
    }
    .stats-table th {
        background: #1e40af;
        color: white;
        font-weight: 600;
    }
    .stats-table tr:nth-child(even) {
        background: #f8fafc;
    }
    .stats-table tr:hover {
        background: #eff6ff;
    }

    /* Footer */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background: #1e293b;
        color: #cbd5e1;
        text-align: center;
        padding: 0.9rem;
        font-size: 0.95rem;
        border-top: 3px solid #3b82f6;
        z-index: 999;
    }

    /* تحسين الأعمدة على الموبايل */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# باقي الكود نفسه (USERS, ROOMS_CONFIG, load_data, save_data, hash_password, إلخ...)
# ... (انسخ باقي التعريفات من النسخة السابقة: USERS, ROOMS_CONFIG, load_data, save_data, إلخ)

# --- تسجيل الدخول ---
# (نفس الكود السابق بدون تغيير)

# --- Sidebar ---
st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
st.sidebar.markdown(f"**الصلاحية:** { 'مدير' if st.session_state.user_role == 'admin' else 'استقبال' }")

if st.session_state.user_role == "admin":
    st.sidebar.markdown("### ⚙️ إعدادات")
    st.session_state.bed_price = st.sidebar.number_input("سعر السرير اليومي", value=st.session_state.bed_price, min_value=100, step=50)

menu = ["🏨 إدارة الغرف والحجز", "👥 قائمة النزلاء", "📊 الإحصائيات المالية", "📂 الأرشيف"]
choice = st.sidebar.radio("القائمة", menu, index=0)

if st.sidebar.button("🚪 تسجيل الخروج", type="primary"):
    st.session_state.auth = False
    st.rerun()

# --- الصفحات (مع تعديلات بسيطة في العرض لتناسب التصميم الجديد) ---

# 1. إدارة الغرف
if choice == "🏨 إدارة الغرف والحجز":
    st.markdown("<div class='enhanced-header'><h2>🏨 وضعية الغرف - بيت الشباب محمدي يوسف</h2></div>", unsafe_allow_html=True)
    
    for group, rooms in ROOMS_CONFIG.items():
        st.subheader(group)
        cols = st.columns(2) if len(rooms) > 1 else st.columns(1)
        for i, (r, max_b) in enumerate(rooms.items()):
            with cols[i % len(cols)]:
                occ = len(st.session_state.db[r]["residents"])
                status_color = "#ef4444" if occ >= max_b else "#22c55e"
                st.markdown(f"""
                <div class="room-card">
                    <h4 style="margin:0; color:{status_color};">{r}</h4>
                    <p style="margin:0.5rem 0; font-size:1.1rem;">
                        <strong>{occ}</strong> / {max_b} <span style="color:#64748b;">مشغول</span>
                    </p>
                    <p style="color:#64748b; margin:0;">متاح: {max_b - occ}</p>
                </div>
                """, unsafe_allow_html=True)

    # باقي جزء إضافة مقيم جديد (نفس السابق مع class resident-card إذا أردت)

# 2. قائمة النزلاء → استخدم .resident-card بدل room-card في عرض كل شخص

# 3. الإحصائيات → الجدول الجديد يبدو أجمل بكثير مع الـ CSS أعلاه

# 4. الأرشيف → نفس السابق

# Footer
st.markdown("<div class='footer'>© 2026 إدارة بيت الشباب محمدي يوسف | مطور: ®ridha_merzoug® | نسخة محسّنة</div>", unsafe_allow_html=True)
