import streamlit as st

# ====================== إعدادات الصفحة ======================
st.set_page_config(
    page_title="إدارة بيت الشباب محمدي يوسف",
    page_icon="🛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== دعم RTL + خط Cairo (بدون باكج إضافي) ======================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Cairo', sans-serif !important;
    }
    
    .stApp, .main, section[data-testid="stSidebar"] {
        direction: rtl !important;
        text-align: right !important;
    }
    
    h1, h2, h3, p, span, label, button, .stMarkdown {
        direction: rtl !important;
        text-align: right !important;
        unicode-bidi: plaintext;
    }
    
    /* تحسين الكروت */
    .room-card {
        background: white;
        padding: 25px 20px;
        border-radius: 16px;
        border: 3px solid #10b981;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# JavaScript لتعزيز الـ RTL
st.components.v1.html("""
<script>
    document.documentElement.setAttribute('dir', 'rtl');
    document.body.style.direction = 'rtl';
</script>
""", height=0)

# ====================== بيانات الغرف (الغرفة 05 مضافة) ======================
rooms = [
    {"id": "01", "name": "مرقد ذكور", "occupied": 3, "total": 8},
    {"id": "05", "name": "غرفة",      "occupied": 4, "total": 8},   # ← الغرفة الجديدة رقم 05
    {"id": "06", "name": "غرفة",      "occupied": 6, "total": 6},
    {"id": "08", "name": "غرفة",      "occupied": 2, "total": 6},
    {"id": "01", "name": "مرقد أناث", "occupied": 3, "total": 8},
]

# ====================== الواجهة ======================
st.title("🛏️ إدارة بيت الشباب محمدي يوسف")
st.markdown("### حالة الإشغال - مارس 2026")

# عرض الكروت في شبكة 2 أعمدة
col1, col2 = st.columns(2)

for i, room in enumerate(rooms):
    available = room["total"] - room["occupied"]
    status = "🟢 متاح" if available >= 3 else "🟡 شبه ممتلئ" if available > 0 else "🔴 ممتلئ"
    color = "#10b981" if available >= 3 else "#eab308" if available > 0 else "#ef4444"
    
    with (col1 if i % 2 == 0 else col2):
        st.markdown(f"""
        <div class="room-card" style="border-color: {color};">
            <h2 style="margin:0; color:#1e3a8a;">{room['id']}</h2>
            <h3 style="margin:8px 0 20px 0; color:#334155;">{room['name']}</h3>
            
            <div style="font-size: 2.8rem; font-weight: 700; color:#1e40af;">
                {room['occupied']} / {room['total']}
            </div>
            <p style="font-size: 1.4rem; color:{color}; margin:15px 0 0 0;">
                المتاح: <strong>{available} سرير</strong><br>
                {status}
            </p>
        </div>
        """, unsafe_allow_html=True)

# ====================== نموذج تسجيل مقيم (كما في الصورة) ======================
st.divider()
st.subheader("تسجيل مقيم جديد")

c1, c2 = st.columns(2)
with c1:
    st.selectbox("الجنس", ["ذكر", "أنثى"], key="gender")
with c2:
    st.text_input("اسم المقيم الكامل", placeholder="أدخل الاسم الكامل...", key="name")

if st.button("✅ تسجيل الدخول", type="primary", use_container_width=True):
    if st.session_state.name:
        st.success(f"تم تسجيل {st.session_state.name} بنجاح!")
    else:
        st.error("يرجى إدخال اسم المقيم")

# ====================== Footer ======================
st.caption("© إدارة بيت الشباب محمدي يوسف 2026 • مطور من طرف merzoug")
