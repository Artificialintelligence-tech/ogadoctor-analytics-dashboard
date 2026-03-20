"""
OgaDoctor - Doctor Portal
=========================
Doctors log in to see their consultations, earnings, ratings
"""

import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(
    page_title="OgaDoctor Doctor Portal",
    page_icon="👨‍⚕️",
    layout="wide"
)

# ============================================================================
# SUPABASE CONNECTION
# ============================================================================
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        st.stop()

supabase = init_supabase()

# ============================================================================
# SESSION STATE
# ============================================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# ============================================================================
# AUTHENTICATION
# ============================================================================
if not st.session_state.logged_in:
    st.title("👨‍⚕️ OgaDoctor - Doctor Portal")
    st.markdown("### Login to access your dashboard")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        phone = st.text_input("Phone Number", placeholder="+234XXXXXXXXX")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", type="primary", use_container_width=True):
            try:
                doctor = supabase.table('doctors')\
                    .select('*')\
                    .eq('phone_number', phone)\
                    .execute().data
                
                if doctor and len(doctor) > 0:
                    # MVP: password = last 4 digits
                    expected_password = phone[-4:]
                    
                    if password == expected_password:
                        st.session_state.logged_in = True
                        st.session_state.doctor_id = doctor[0]['id']
                        st.session_state.doctor_name = doctor[0]['full_name']
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid password")
                else:
                    st.error("Doctor not found")
            except Exception as e:
                st.error(f"Login error: {str(e)}")
        
        st.info("**First time?** Password = last 4 digits of your phone number")

else:
    # ========================================================================
    # LOGGED IN
    # ========================================================================
    
    doctor_id = st.session_state.doctor_id
    doctor_name = st.session_state.doctor_name
    
    # Get fresh doctor data
    doctor = supabase.table('doctors')\
        .select('*')\
        .eq('id', doctor_id)\
        .single()\
        .execute().data
    
    # ========================================================================
    # SIDEBAR
    # ========================================================================
    st.sidebar.title(f"👨‍⚕️ Dr. {doctor_name}")
    
    # Availability toggle
    is_online = st.sidebar.toggle(
        "🟢 I'm Available",
        value=doctor.get('is_online', False)
    )
    
    if is_online != doctor.get('is_online'):
        supabase.table('doctors').update({
            'is_online': is_online
        }).eq('id', doctor_id).execute()
        st.sidebar.success("Status updated!")
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
    
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio("Navigation", [
        "📊 My Dashboard",
        "💬 My Consultations", 
        "⭐ My Reviews",
        "💰 My Earnings",
        "⚙️ Settings"
    ])
    
    # ========================================================================
    # PAGE 1: DASHBOARD
    # ========================================================================
    if page == "📊 My Dashboard":
        st.title("📊 My Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Consultations", doctor.get('total_consultations', 0))
        
        with col2:
            st.metric("Total Earnings", f"₦{doctor.get('total_earnings', 0):,.0f}")
        
        with col3:
            st.metric("Average Rating", f"{doctor.get('rating', 0):.1f} ⭐")
        
        with col4:
            status = "🟢 Online" if doctor.get('is_online') else "🔴 Offline"
            st.metric("Status", status)
        
        st.markdown("---")
        st.subheader("Today's Performance")
        
        from datetime import datetime
        today = datetime.now().date()
        
        today_consultations = supabase.table('Consultations')\
            .select('*')\
            .eq('doctor_id', doctor_id)\
            .gte('created_at', today.isoformat())\
            .execute().data
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Today's Consultations", len(today_consultations))
        
        with col2:
            today_earnings = len(today_consultations) * 705
            st.metric("Today's Earnings", f"₦{today_earnings:,.0f}")
    
    # ========================================================================
    # PAGE 2: MY CONSULTATIONS
    # ========================================================================
    elif page == "💬 My Consultations":
        st.title("💬 My Consultations")
        
        filter_status = st.selectbox("Filter by Status", [
            "All", "Assigned", "In Progress", "Completed"
        ])
        
        query = supabase.table('Consultations')\
            .select('*')\
            .eq('doctor_id', doctor_id)\
            .order('created_at', desc=True)
        
        if filter_status != "All":
            query = query.eq('status', filter_status.lower().replace(' ', '_'))
        
        consultations = query.execute().data
        
        st.write(f"**{len(consultations)} consultation(s)**")
        
        for consult in consultations:
            with st.expander(f"Patient #{consult['id'][:8]} - {consult.get('symptoms', 'N/A')[:50]}..."):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Patient:** {consult.get('patient_name', 'N/A')}")
                    st.write(f"**Symptoms:** {consult.get('symptoms', 'N/A')}")
                    st.write(f"**Severity:** {consult.get('severity', 'N/A')}")
                    st.write(f"**Duration:** {consult.get('duration', 'N/A')}")
                
                with col2:
                    st.write(f"**Status:** {consult.get('status', 'N/A')}")
                    st.write(f"**Fee:** ₦{consult.get('consultation_fee', 1500):,.0f}")
                    st.write(f"**Your Payout:** ₦{consult.get('doctor_payout', 705):,.0f}")
                    
                    if consult.get('patient_rating'):
                        st.write(f"**Rating:** {'⭐' * consult['patient_rating']}")
                
                if consult.get('ai_diagnosis'):
                    st.info(f"**AI Assessment:** {consult['ai_diagnosis']}")
                
                # Diagnosis
                diagnosis = st.text_area(
                    "Your Diagnosis:",
                    value=consult.get('pharmacist_diagnosis', ''),
                    key=f"diag_{consult['id']}"
                )
                
                prescription = st.text_area(
                    "Your Prescription:",
                    value=consult.get('pharmacist_prescription', ''),
                    key=f"presc_{consult['id']}"
                )
                
                # Actions
                if consult['status'] in ['assigned', 'in_progress']:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("💾 Save", key=f"save_{consult['id']}"):
                            supabase.table('Consultations').update({
                                'pharmacist_diagnosis': diagnosis,
                                'pharmacist_prescription': prescription,
                                'status': 'in_progress'
                            }).eq('id', consult['id']).execute()
                            st.success("Saved!")
                            st.rerun()
                    
                    with col2:
                        if st.button("✅ Complete", key=f"done_{consult['id']}"):
                            from datetime import datetime
                            supabase.table('Consultations').update({
                                'pharmacist_diagnosis': diagnosis,
                                'pharmacist_prescription': prescription,
                                'status': 'completed',
                                'completed_at': datetime.now().isoformat()
                            }).eq('id', consult['id']).execute()
                            st.success("Completed!")
                            st.rerun()
    
    # ========================================================================
    # PAGE 3: MY REVIEWS
    # ========================================================================
    elif page == "⭐ My Reviews":
        st.title("⭐ My Reviews")
        
        reviews = supabase.table('reviews')\
            .select('*')\
            .eq('doctor_id', doctor_id)\
            .order('created_at', desc=True)\
            .execute().data
        
        if not reviews:
            st.info("No reviews yet!")
        else:
            avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average Rating", f"{avg_rating:.1f} ⭐")
            with col2:
                st.metric("Total Reviews", len(reviews))
            
            st.markdown("---")
            
            for review in reviews:
                st.markdown(f"""
                <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                    <h4>{'⭐' * review['rating']} ({review['rating']}/5)</h4>
                    <p>{review.get('feedback', 'No comment')}</p>
                    <small>{review.get('created_at', '')[:10]}</small>
                </div>
                """, unsafe_allow_html=True)
    
    # ========================================================================
    # PAGE 4: MY EARNINGS
    # ========================================================================
    elif page == "💰 My Earnings":
        st.title("💰 My Earnings")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Earnings", f"₦{doctor.get('total_earnings', 0):,.0f}")
        
        with col2:
            pending = supabase.table('Consultations')\
                .select('doctor_payout')\
                .eq('doctor_id', doctor_id)\
                .eq('status', 'completed')\
                .eq('payout_status', 'pending')\
                .execute().data
            
            pending_amount = sum(p.get('doctor_payout', 705) for p in pending)
            st.metric("Pending Payout", f"₦{pending_amount:,.0f}")
        
        with col3:
            st.metric("This Month", f"₦{doctor.get('monthly_earnings', 0):,.0f}")
        
        st.markdown("---")
        st.subheader("Earnings History")
        
        consultations = supabase.table('Consultations')\
            .select('*')\
            .eq('doctor_id', doctor_id)\
            .eq('status', 'completed')\
            .order('completed_at', desc=True)\
            .limit(20)\
            .execute().data
        
        if consultations:
            df = pd.DataFrame(consultations)
            
            if 'completed_at' in df.columns and 'doctor_payout' in df.columns:
                df['completed_at'] = pd.to_datetime(df['completed_at'])
                df['date'] = df['completed_at'].dt.date
                
                daily_earnings = df.groupby('date')['doctor_payout'].sum().reset_index()
                st.line_chart(daily_earnings.set_index('date'))
                
                st.dataframe(
                    df[['completed_at', 'patient_name', 'doctor_payout']],
                    use_container_width=True
                )
    
    # ========================================================================
    # PAGE 5: SETTINGS
    # ========================================================================
    elif page == "⚙️ Settings":
        st.title("⚙️ Settings")
        
        st.subheader("Profile Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {doctor.get('full_name', 'N/A')}")
            st.write(f"**Phone:** {doctor.get('phone_number', 'N/A')}")
            st.write(f"**Email:** {doctor.get('email', 'N/A')}")
        
        with col2:
            st.write(f"**Specialization:** {doctor.get('specialization', 'General Practice')}")
            st.write(f"**MDCN License:** {doctor.get('mdcn_license_number', 'N/A')}")
            st.write(f"**Status:** {doctor.get('status', 'active')}")
        
        st.markdown("---")
        st.subheader("Bank Details")
        
        bank_details = doctor.get('bank_details', {})
        
        with st.form("bank_form"):
            account_name = st.text_input(
                "Account Name",
                value=bank_details.get('account_name', '') if isinstance(bank_details, dict) else ''
            )
            account_number = st.text_input(
                "Account Number",
                value=bank_details.get('account_number', '') if isinstance(bank_details, dict) else ''
            )
            bank_name = st.selectbox("Bank", [
                "Select Bank", "GTBank", "Access Bank", "First Bank",
                "UBA", "Zenith Bank", "Stanbic IBTC"
            ])
            
            if st.form_submit_button("💾 Update"):
                supabase.table('doctors').update({
                    'bank_details': {
                        'account_name': account_name,
                        'account_number': account_number,
                        'bank_name': bank_name
                    }
                }).eq('id', doctor_id).execute()
                st.success("Bank details updated!")
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>OgaDoctor Doctor Portal v1.0 | © 2026 OgaDoctor</p>
</div>
""", unsafe_allow_html=True)