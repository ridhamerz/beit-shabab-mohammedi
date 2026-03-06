import streamlit as st
import json
from datetime import datetime, date
import pandas as pd
import io

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="إدارة بيت الشباب محمدي يوسف", page_icon="🏢", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { direction: RTL; text-align: right; font-family: 'Cairo', sans-serif; }
    [data-testid="stSidebarNav"] { display: none; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; background-color: #1e40af; color: white; padding: 10px; }
    .main-header { text-align: center; color: #1e40af; background: #f0f4ff; padding: 15px; border-radius: 12px; border: 2px solid #1e40af; margin-bottom: 20px; }
    .footer { text-align: center; color: #475569; padding: 15px; font-weight: bold; font-size: 13px; border-top: 1px solid #e2e8f0; margin-top: 30px; }
    .stats-table { width: 100%; border-collapse: collapse; margin: 10px 0; border: 1px solid #ddd; }
    .stats-table td { padding: 12px; border: 1px solid #ddd; text-align: center; }
    .receipt-box { border: 2px dashed #333; padding: 20px; background: #fff; font-family: 'Courier New', monospace; direction: ltr; text-align: left; }
</style>
""", unsafe_allow_html=True)

# --- 2. إدارة البيانات والإعدادات ---
ROOMS_CONFIG = {
    "جناح ذكور": {"غرفة 01": 6, "غرفة 02": 6, "غرفة 03": 6, "غرفة 04": 6, "غرفة 05": 6, "مرقد ذكور 01": 3, "مرقد ذكور 02": 4},
    "جناح إناث": {"غرفة 06": 6, "غرفة 07": 6, "غرفة 08": 6, "غرفة 09": 6, "مرقد اناث 01": 3, "مرقد اناث 02": 4}
}
ALL_ROOM_NAMES = [room for group in ROOMS_CONFIG.values() for room in group.keys()]
BED_PRICE = 400

def load_all_data():
    try:
        with open("hostel_pro_v4.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "rooms": {room: {"residents": []} for room in ALL_ROOM_NAMES},
            "archive": [],
            "users": {"admin": "admin123", "reception": "recep2026"}
        }

def save_all_data():
    with open("hostel_pro_v4.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.db, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state:
    st.session_state.db = load_all_data()

# --- 3. نظام تسجيل الدخول ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<div class='main-header'><h1>إدارة بيت الشباب محمدي يوسف</h1></div>", unsafe_allow_html=True)
    u_input = st.text_input("👤 اسم المستخدم")
    p_input = st.text_input("🔑 كلمة السر", type="password")
    if st.button("دخول"):
        if u_input in st.session_state.db["users"] and st.session_state.db["users"][u_input] == p_input:
            st.session_state.auth = True
            st.session_state.user_name = u_input
            st.rerun()
        else: st.error("عذراً، كلمة المرور غير صحيحة")
    st.stop()

# --- 4. القائمة الجانبية والتحكم بكلمات المرور ---
st.sidebar.title(f"مرحباً {st.session_state.user_name}")
menu = ["🏨 إدارة الغرف والحجز", "👥 قائمة النزلاء", "📊 الإحصائيات", "📂 الأرشيف"]
choice = st.sidebar.selectbox("القائمة:", menu)

if st.session_state.user_name == "admin":
    with st.sidebar.expander("🔐 تغيير كلمات المرور"):
        target_user = st.selectbox("اختر الحساب", ["admin", "reception"])
        new_pass = st.text_input("كلمة المرور الجديدة", type="password")
        if st.button("حفظ التغيير"):
            st.session_state.db["users"][target_user] = new_pass
            save_all_data()
            st.success(f"تم تغيير كلمة مرور {target_user}")

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.auth = False
    st.rerun()

# --- 5. منطق الصفحات ---

# الصفحة 1: الغرف
if choice == "🏨 إدارة الغرف والحجز":
    st.markdown("<div class='main-header'><h2>🏨 وضعية الغرف والتسجيل</h2></div>", unsafe_allow_html=True)
    status_list = []
    for r in ALL_ROOM_NAMES:
        occ = len(st.session_state.db["rooms"][r]["residents"])
        max_b = next(v for g in ROOMS_CONFIG.values() for k,v in g.items() if k == r)
        status_list.append({"الغرفة": r, "المشغول": occ, "المتاح": max_b - occ, "الحالة": "🟢" if occ < max_b else "🔴"})
    st.table(pd.DataFrame(status_list))

    st.markdown("---")
    st.subheader("➕ تسجيل نزيل جديد")
    with st.form("add_res"):
        name = st.text_input("الاسم الكامل")
        room_sel = st.selectbox("الغرفة", ALL_ROOM_NAMES)
        gender = st.selectbox("الجنس", ["ذكر", "أنثى"])
        nation = st.text_input("الجنسية", "جزائرية")
        if st.form_submit_button("تأكيد الحجز"):
            st.session_state.db["rooms"][room_sel]["residents"].append({
                "name": name, "gender": gender, "nation": nation, 
                "entry": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "by_user": st.session_state.user_name
            })
            save_all_data(); st.success("تم الحجز بنجاح"); st.rerun()

# الصفحة 2: النزلاء والوصل
elif choice == "👥 قائمة النزلاء":
    st.markdown("<div class='main-header'><h2>👥 النزلاء والعمليات</h2></div>", unsafe_allow_html=True)
    for r in ALL_ROOM_NAMES:
        residents = st.session_state.db["rooms"][r]["residents"]
        if residents:
            with st.expander(f"🏠 {r} - ({len(residents)} مقيم)"):
                for i, p in enumerate(residents):
                    st.write(f"👤 **{p['name']}** | {p['gender']} | سجل بواسطة: {p.get('by_user','غير معروف')}")
                    if st.button(f"تسجيل خروج {p['name']}", key=f"ex_{r}_{i}"):
                        p.update({"exit": datetime.now().strftime("%Y-%m-%d %H:%M"), "paid": BED_PRICE, "room": r})
                        st.session_state.db["archive"].append(p)
                        st.session_state.db["rooms"][r]["residents"].pop(i)
                        save_all_data()
                        st.session_state.last_receipt = p # حفظ بيانات آخر وصل لعرضه
                        st.rerun()

    if "last_receipt" in st.session_state:
        st.info("تم تسجيل الخروج بنجاح. يمكنك معاينة الوصل أدناه:")
        res = st.session_state.last_receipt
        receipt_text = f"""
        ===================================
        بيت الشباب محمدي يوسف
        وصل استلام رقم: {datetime.now().strftime('%S%M%H')}
        -----------------------------------
        النزيل: {res['name']}
        الغرفة: {res['room']}
        الدخول: {res['entry']}
        الخروج: {res['exit']}
        المبلغ: {res['paid']} دج
        -----------------------------------
        شكراً لزيارتكم
        ===================================
        """
        st.code(receipt_text)
        if st.button("إخفاء الوصل"): del st.session_state.last_receipt; st.rerun()

# الصفحة 3: الإحصائيات
elif choice == "📊 الإحصائيات":
    st.markdown("<div class='main-header'><h2>📊 تقرير الإحصائيات</h2></div>", unsafe_allow_html=True)
    all_current = []
    for r in ALL_ROOM_NAMES: all_current.extend(st.session_state.db["rooms"][r]["residents"])
    
    m = len([x for x in all_current if x['gender'] == "ذكر"])
    f = len([x for x in all_current if x['gender'] == "أنثى"])
    today_rev = sum(e.get("paid", 0) for e in st.session_state.db["archive"] if e["exit"].startswith(date.today().strftime("%Y-%m-%d")))

    st.markdown(f"""
    <table class="stats-table">
        <tr style="background:#f2f2f2"><td>المؤشر</td><td>القيمة</td></tr>
        <tr><td>المقيمين حالياً</td><td><b>{len(all_current)}</b></td></tr>
        <tr><td>ذكور / إناث</td><td>{m} ذكور | {f} إناث</td></tr>
        <tr><td>مداخيل اليوم</td><td><span style="color:green">{today_rev} دج</span></td></tr>
    </table>
    """, unsafe_allow_html=True)

# الصفحة 4: الأرشيف
elif choice == "📂 الأرشيف":
    st.markdown("<div class='main-header'><h2>📂 سجل الأرشيف والطباعة</h2></div>", unsafe_allow_html=True)
    if st.session_state.db["archive"]:
        df = pd.DataFrame(st.session_state.db["archive"])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل الأرشيف الشامل (CSV)", csv, "archive.csv", "text/csv")

st.markdown("<div class='footer'>إدارة بيت الشباب محمدي يوسف - ®ridha_merzoug®</div>", unsafe_allow_html=True)
