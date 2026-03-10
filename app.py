import datetime # لإضافة التوقيت الفعلي

# --- داخل تبويب الحجز tabs[0] ---
with tabs[0]:
    if st.session_state.get('booking_success'):
        st.markdown('<div class="success-box"><h3>🎉 تم تسجيل الحجز بنجاح!</h3></div>', unsafe_allow_html=True)
        if st.button("➕ تسجيل نزيل جديد", type="primary", use_container_width=True):
            st.session_state.booking_success = False
            st.rerun()
    else:
        st.markdown('<div class="section-box"><h4>🔍 تسجيل حجز احترافي - بيت الشباب</h4></div>', unsafe_allow_html=True)
        
        search_id = st.text_input("🪪 ابحث برقم الوثيقة لنزيل سابق:", placeholder="اكتب الرقم لملء البيانات...")
        old_guest = get_old_guest(search_id) if search_id else None

        with st.form("final_booking_form"):
            # --- القسم الأول: المعلومات الشخصية ---
            st.markdown("##### 👤 معلومات النزيل الأساسية")
            name = st.text_input("الاسم واللقب الكامل", value=old_guest[0] if old_guest else "")
            
            # 💡 تعديل رضا: وضع تاريخ الميلاد ومكان الازدياد بجانب بعضهما
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                bday = st.date_input("📅 تاريخ الميلاد", value=pd.to_datetime(old_guest[1]) if old_guest else date(2000,1,1))
            with col_b2:
                bplace = st.text_input("📍 مكان الازدياد", value=old_guest[2] if old_guest else "")

            # 💡 تعديل رضا: وضع الجنسية ونوع الوثيقة بجانب بعضهما
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                nations = ["جزائرية", "تونسية", "مغربية", "ليبية", "موريتانية", "فرنسية", "أخرى"]
                nationality = st.selectbox("🌍 الجنسية", nations, index=0 if not old_guest else nations.index(old_guest[6]) if old_guest[6] in nations else 6)
            with col_n2:
                id_type = st.selectbox("📄 نوع الوثيقة", ["بطاقة تعريف (عادية)", "بطاقة تعريف (بيومترية)", "رخصة سياقة (عادية)", "رخصة سياقة (بيومترية)", "جواز سفر", "اخرى"])

            # معلومات التواصل والعمل
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                id_num = st.text_input("🔢 رقم الوثيقة", value=search_id if search_id else "")
                job = st.text_input("💼 المهنة", value=old_guest[4] if old_guest else "")
            with col_c2:
                phone = st.text_input("📞 رقم الهاتف", value=old_guest[5] if old_guest else "")
                addr = st.text_input("🏠 العنوان الكامل")

            # --- القسم الثاني: الحالات الخاصة (أجانب / قاصرين) ---
            age = calculate_age(bday)
            is_foreigner = nationality != "جزائرية"
            
            if is_foreigner or age < 18:
                col_spec1, col_spec2 = st.columns(2)
                with col_spec1:
                    if is_foreigner:
                        st.info("🛂 بيانات الأجانب")
                        entry_date = st.date_input("تاريخ الدخول للجزائر", date.today())
                with col_spec2:
                    if age < 18:
                        st.warning(f"⚠️ قاصر ({age} سنة)")
                        minor_auth = st.selectbox("📝 نوع التصريح:", ["تصريح أبوي", "حضور الولي", "أمر بمهمة", "أخرى"])

            # --- القسم الثالث: ميزة المرافقين (Companions) ---
            st.markdown("---")
            st.markdown("##### 👨‍👩‍👧‍👦 ميزة المرافقين الإضافيين")
            companions = st.text_area("أدخل أسماء المرافقين (إن وجدوا)", placeholder="مثال: الزوجة فلانة، الابن فلان...")

            # --- القسم الرابع: السكن والأسرة الشاغرة ---
            st.markdown("---")
            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                wing = st.selectbox("🏢 الجناح", ["جناح ذكور 👨", "جناح إناث 👩"])
            with col_res2:
                room = st.selectbox("🚪 الغرفة", [f"غرفة {i:02d}" for i in range(1, 11)])
            with col_res3:
                nights = st.number_input("🌙 الليالي", min_value=1, value=1)

            vacant_beds = get_vacant_beds(wing, room)
            if vacant_beds:
                bed = st.radio("🛏️ اختر السرير الشاغر:", vacant_beds, horizontal=True)
                
                # تسجيل توقيت الدخول الفعلي تلقائياً
                current_time = datetime.datetime.now().strftime("%H:%M")
                st.caption(f"🕒 توقيت التسجيل الفعلي: {current_time}")

                submit = st.form_submit_button("💾 تأكيد وحفظ الحجز النهائي", type="primary", use_container_width=True)
            else:
                st.error("⚠️ الغرفة ممتلئة!")
                submit = False

            if submit:
                # حفظ البيانات مع التوقيت والمرافقين
                # (ملاحظة: تأكد من تحديث قاعدة البيانات لتشمل أعمدة companions و check_in_time)
                st.session_state.booking_success = True
                st.rerun()

# الفوتر ثابت دائماً
st.markdown('<div class="developer-footer">Developer ®ridha_merzoug® [رضا مرزوق] - 2026</div>', unsafe_allow_html=True)
