if page == "📊 Live Queue":
    st.title("🔔 Live Patient Queue - Clinical Review")
    
    consultations = get_consultations()
    
    for i, patient in enumerate(consultations):
        # Priority header with color coding
        priority_color = {
            'URGENT': '🔴',
            'MODERATE': '🟡',
            'LOW': '🟢'
        }.get(patient.get('priority', 'MODERATE'), '🟡')
        
        st.markdown(f"### {priority_color} {patient['priority']} - {patient['patient_name']}, {patient.get('age', 'N/A')}")
        
        # Two-column layout: Patient Info vs AI Assessment
        col1, col2 = st.columns([1, 1])
        
        # LEFT COLUMN: Patient Information
        with col1:
            st.markdown("#### 📋 Patient Information")
            st.write(f"**📞 Phone:** {patient['patient_phone']}")
            st.write(f"**🩺 Symptoms:** {patient['symptoms']}")
            st.write(f"**📊 Severity:** {patient['severity']}")
            st.write(f"**⏰ Duration:** {patient['duration']}")
            st.write(f"**🕐 Received:** {patient['created_at'][:16]}")
            
            if patient.get('detected_keywords'):
                st.error(f"⚠️ **Alert Keywords:** {patient['detected_keywords']}")
        
        # RIGHT COLUMN: AI Clinical Assessment
        with col2:
            st.markdown("#### 🤖 AI Clinical Assessment")
            
            if patient.get('ai_diagnosis'):
                st.info(f"**Diagnosis:** {patient['ai_diagnosis']}")
            
            if patient.get('ai_drug_recommendations'):
                st.success(f"**Recommended Medications:**\n\n{patient['ai_drug_recommendations']}")
        
        st.markdown("---")
        
        # PHARMACIST REVIEW SECTION
        st.markdown("#### 👨‍⚕️ Pharmacist Clinical Decision")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            # Pharmacist's diagnosis
            pharmacist_diagnosis = st.text_area(
                "Your Diagnosis:",
                value=patient.get('pharmacist_diagnosis', ''),
                key=f"diagnosis_{i}",
                placeholder="Your professional assessment (can agree with or modify AI diagnosis)",
                help="What do you think the patient actually has?"
            )
            
            # Agreement level
            agreement = st.radio(
                "AI Diagnosis Assessment:",
                options=['Agree with AI', 'Partially agree', 'Disagree with AI'],
                key=f"agreement_{i}",
                horizontal=True
            )
        
        with col_b:
            # Pharmacist's prescription
            pharmacist_prescription = st.text_area(
                "Your Prescription:",
                value=patient.get('pharmacist_prescription', ''),
                key=f"prescription_{i}",
                placeholder="Actual medications and dosages you're prescribing",
                height=150
            )
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✅ Confirm & Dispense", key=f"confirm_{i}", use_container_width=True):
                # Map radio choice to database value
                agreement_map = {
                    'Agree with AI': 'agreed',
                    'Partially agree': 'modified',
                    'Disagree with AI': 'disagreed'
                }
                
                # Update database
                supabase.table('consultations')\
                    .update({
                        'pharmacist_diagnosis': pharmacist_diagnosis,
                        'pharmacist_prescription': pharmacist_prescription,
                        'diagnosis_agreement': agreement_map[agreement],
                        'status': 'confirmed',
                        'pharmacist_response': 'stock_available',
                        'response_time': datetime.now().isoformat()
                    })\
                    .eq('id', patient['id'])\
                    .execute()
                
                st.success(f"✅ Prescription confirmed for {patient['patient_name']}")
                st.rerun()
        
        with col2:
            if st.button("❌ Out of Stock", key=f"no_stock_{i}", use_container_width=True):
                supabase.table('consultations')\
                    .update({
                        'pharmacist_diagnosis': pharmacist_diagnosis,
                        'status': 'referred',
                        'pharmacist_response': 'out_of_stock',
                        'response_time': datetime.now().isoformat()
                    })\
                    .eq('id', patient['id'])\
                    .execute()
                st.error("❌ Patient referred to alternative pharmacy")
                st.rerun()
        
        with col3:
            if st.button("🏥 Refer to Doctor", key=f"refer_{i}", use_container_width=True):
                supabase.table('consultations')\
                    .update({
                        'pharmacist_diagnosis': pharmacist_diagnosis,
                        'status': 'referred_to_doctor',
                        'pharmacist_response': 'needs_doctor',
                        'response_time': datetime.now().isoformat()
                    })\
                    .eq('id', patient['id'])\
                    .execute()
                st.warning("🏥 Patient advised to see a doctor")
                st.rerun()
        
        with col4:
            if st.button("📞 Call Patient", key=f"call_{i}", use_container_width=True):
                st.info(f"📞 Calling {patient['patient_name']}...")
        
        st.markdown("---")
        st.markdown("---")
