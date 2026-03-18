"""
OgaDoctor - Pharmacist Portal
==============================

Pharmacists log in to see their medication counseling sessions, earnings, and ratings.

Features:
- Personal dashboard with stats
- View assigned medication counseling sessions
- Provide medication advice
- See patient reviews and ratings
- Track earnings and payouts
- Manage availability
- Update profile and bank details

Author: Christian Egwuonwu
Version: 1.0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase import create_client

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="OgaDoctor - Pharmacist Portal",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    .consultation-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #7b1fa2;
        margin: 10px 0;
    }
    .review-card {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SUPABASE CONNECTION
# ============================================================================
@st.cache_resource
def init_supabase():
    """Initialize Supabase connection"""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
        st.stop()

supabase = init_supabase()

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.pharmacist_id = None
    st.session_state.pharmacist_data = None

# ============================================================================
# AUTHENTICATION
# ============================================================================
if not st.session_state.logged_in:
    st.title("💊 OgaDoctor - Pharmacist Portal")
    st.markdown("### Login to access your dashboard")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            phone = st.text_input(
                "Phone Number",
                placeholder="+234XXXXXXXXX",
                help="Enter your registered phone number"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )
            
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submit:
                if not phone or not password:
                    st.error("Please enter both phone number and password")
                else:
                    try:
                        # Check credentials
                        # For MVP, using simple password field in pharmacists table
                        pharmacist = supabase.table('pharmacists')\
                            .select('*')\
                            .eq('phone_number', phone)\
                            .execute().data
                        
                        if pharmacist and len(pharmacist) > 0:
                            # For MVP: password = last 4 digits of phone
                            expected_password = phone[-4:]
                            
                            if password == expected_password:
                                st.session_state.logged_in = True
                                st.session_state.pharmacist_id = pharmacist[0]['id']
                                st.session_state.pharmacist_data = pharmacist[0]
                                st.success("Login successful!")
                                st.rerun()
                            else:
                                st.error("Invalid password")
                        else:
                            st.error("Pharmacist not found. Please contact admin.")
                    
                    except Exception as e:
                        st.error(f"Login error: {str(e)}")
        
        st.info("""
        **First time login?**
        
        Your temporary password is the last 4 digits of your phone number.
        Please change it after logging in.
        
        Contact admin if you need help: +234XXXXXXXXX
        """)

else:
    # ========================================================================
    # LOGGED IN - MAIN DASHBOARD
    # ========================================================================
    
    pharmacist_id = st.session_state.pharmacist_id
    
    # Refresh pharmacist data
    pharmacist_data = supabase.table('pharmacists')\
        .select('*')\
        .eq('id', pharmacist_id)\
        .single()\
        .execute().data
    
    st.session_state.pharmacist_data = pharmacist_data
    
    # ========================================================================
    # SIDEBAR
    # ========================================================================
    st.sidebar.title(f"💊 Pharm. {pharmacist_data['full_name']}")
    st.sidebar.markdown("**Medication Counseling Specialist**")
    
    # Availability toggle
    is_online = st.sidebar.toggle(
        "🟢 I'm Available",
        value=pharmacist_data.get('is_online', False),
        help="Toggle your availability status"
    )
    
    if is_online != pharmacist_data.get('is_online', False):
        supabase.table('pharmacists').update({
            'is_online': is_online,
            'last_active_at': datetime.now().isoformat()
        }).eq('id', pharmacist_id).execute()
        st.sidebar.success("Availability updated!")
    
    st.sidebar.markdown("---")
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "💬 My Sessions",
            "⭐ Reviews & Ratings",
            "💰 Earnings",
            "⚙️ Settings"
        ],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    
    # Quick stats in sidebar
    st.sidebar.metric("Total Sessions", pharmacist_data.get('total_consultations', 0))
    st.sidebar.metric("Rating", f"{pharmacist_data.get('rating', 0):.1f} ⭐")
    st.sidebar.metric("Total Earnings", f"₦{pharmacist_data.get('total_earnings', 0):,.0f}")
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.pharmacist_id = None
        st.session_state.pharmacist_data = None
        st.rerun()
    
    # ========================================================================
    # PAGE 1: DASHBOARD
    # ========================================================================
    if page == "📊 Dashboard":
        st.title("📊 My Dashboard")
        st.markdown(f"Welcome back, **Pharm. {pharmacist_data['full_name']}**!")
        
        # Top metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Sessions",
                pharmacist_data.get('total_consultations', 0)
            )
        
        with col2:
            st.metric(
                "Total Earnings",
                f"₦{pharmacist_data.get('total_earnings', 0):,.0f}"
            )
        
        with col3:
            st.metric(
                "Average Rating",
                f"{pharmacist_data.get('rating', 0):.1f} ⭐"
            )
        
        with col4:
            status_color = "🟢" if pharmacist_data.get('is_online') else "🔴"
            status_text = "Online" if pharmacist_data.get('is_online') else "Offline"
            st.metric("Status", f"{status_color} {status_text}")
        
        st.markdown("---")
        
        # Today's stats
        st.subheader("📅 Today's Performance")
        
        today = datetime.now().date()
        
        today_sessions = supabase.table('Consultations')\
            .select('*')\
            .eq('pharmacist_id', pharmacist_id)\
            .gte('created_at', today.isoformat())\
            .execute().data
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Today's Sessions", len(today_sessions))
        
        with col2:
            completed_today = len([c for c in today_sessions if c.get('status') == 'completed'])
            st.metric("Completed Today", completed_today)
        
        with col3:
            today_earnings = completed_today * 400  # ₦400 per session for pharmacists
            st.metric("Today's Earnings", f"₦{today_earnings:,.0f}")
        
        st.markdown("---")
        
        # Pending sessions
        st.subheader("⏳ Pending Medication Counseling Sessions")
        
        pending = supabase.table('Consultations')\
            .select('*')\
            .eq('pharmacist_id', pharmacist_id)\
            .in_('status', ['assigned', 'in_progress'])\
            .order('created_at', desc=False)\
            .limit(5)\
            .execute().data
        
        if not pending:
            st.info("✅ No pending sessions. Great work!")
        else:
            for session in pending:
                priority_colors = {
                    'URGENT': '#ffebee',
                    'MODERATE': '#fff9e6',
                    'LOW': '#e8f5e9'
                }
                bg_color = priority_colors.get(session.get('priority', 'MODERATE'), '#fff9e6')
                
                st.markdown(f"""
                <div style='background-color: {bg_color}; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                    <h4>{session.get('priority', 'MODERATE')} - Patient #{session['id'][:8]}</h4>
                    <p><strong>Question:</strong> {session['symptoms'][:100]}...</p>
                    <p><strong>Status:</strong> {session['status']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"View Details", key=f"view_{session['id']}"):
                    st.session_state.selected_session = session['id']
                    st.info("Go to 'My Sessions' to view full details")
        
        st.markdown("---")
        
        # Recent activity chart
        st.subheader("📈 Last 7 Days Activity")
        
        week_ago = (datetime.now() - timedelta(days=7)).date()
        
        week_sessions = supabase.table('Consultations')\
            .select('*')\
            .eq('pharmacist_id', pharmacist_id)\
            .gte('created_at', week_ago.isoformat())\
            .execute().data
        
        if week_sessions:
            df = pd.DataFrame(week_sessions)
            df['date'] = pd.to_datetime(df['created_at']).dt.date
            daily_counts = df.groupby('date').size().reset_index(name='count')
            
            fig = px.bar(
                daily_counts,
                x='date',
                y='count',
                title='Daily Sessions',
                labels={'date': 'Date', 'count': 'Sessions'}
            )
            fig.update_traces(marker_color='#7b1fa2')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sessions in the last 7 days")
    
    # ========================================================================
    # PAGE 2: MY SESSIONS
    # ========================================================================
    elif page == "💬 My Sessions":
        st.title("💬 My Medication Counseling Sessions")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_status = st.selectbox(
                "Status",
                ["All", "Assigned", "In Progress", "Completed", "Referred"]
            )
        
        with col2:
            filter_priority = st.selectbox(
                "Priority",
                ["All", "URGENT", "MODERATE", "LOW"]
            )
        
        with col3:
            date_filter = st.selectbox(
                "Time Period",
                ["Today", "This Week", "This Month", "All Time"]
            )
        
        # Build query
        query = supabase.table('Consultations')\
            .select('*')\
            .eq('pharmacist_id', pharmacist_id)\
            .order('created_at', desc=True)
        
        # Apply filters
        if filter_status != "All":
            query = query.eq('status', filter_status.lower().replace(' ', '_'))
        
        if filter_priority != "All":
            query = query.eq('priority', filter_priority)
        
        if date_filter == "Today":
            query = query.gte('created_at', datetime.now().date().isoformat())
        elif date_filter == "This Week":
            week_ago = (datetime.now() - timedelta(days=7)).date()
            query = query.gte('created_at', week_ago.isoformat())
        elif date_filter == "This Month":
            month_ago = (datetime.now() - timedelta(days=30)).date()
            query = query.gte('created_at', month_ago.isoformat())
        
        sessions = query.execute().data
        
        st.write(f"**{len(sessions)} session(s) found**")
        
        st.markdown("---")
        
        # Display sessions
        if not sessions:
            st.info("No sessions match your filters")
        else:
            for session in sessions:
                with st.expander(
                    f"💊 Patient #{session['id'][:8]} - {session['symptoms'][:50]}... ({session['status']})"
                ):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📋 Patient Question")
                        st.write(f"**Name:** {session.get('patient_name', 'N/A')}")
                        st.write(f"**Phone:** {session.get('patient_phone', 'N/A')}")
                        st.write(f"**Question:** {session['symptoms']}")
                        st.write(f"**Severity:** {session.get('severity', 'N/A')}")
                        st.write(f"**Duration:** {session.get('duration', 'N/A')}")
                        st.write(f"**Priority:** {session.get('priority', 'MODERATE')}")
                        
                        created = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
                        st.write(f"**Received:** {created.strftime('%Y-%m-%d %I:%M %p')}")
                    
                    with col2:
                        st.markdown("#### 🤖 AI Assessment")
                        if session.get('ai_diagnosis'):
                            st.info(f"**Assessment:** {session['ai_diagnosis']}")
                        else:
                            st.write("No AI assessment available")
                        
                        if session.get('ai_drug_recommendations'):
                            st.success(f"**AI Recommendations:** {session['ai_drug_recommendations']}")
                        
                        st.markdown("#### 💰 Payment")
                        st.write(f"**Session Fee:** ₦{session.get('consultation_fee', 1000):,.0f}")
                        st.write(f"**Your Payout:** ₦{session.get('pharmacist_payout', 400):,.0f}")
                        
                        if session.get('patient_rating'):
                            st.write(f"**Patient Rating:** {'⭐' * session['patient_rating']}")
                    
                    st.markdown("---")
                    
                    # Your response
                    st.markdown("#### 💊 Your Medication Counseling")
                    
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        assessment = st.text_area(
                            "Your Assessment",
                            value=session.get('pharmacist_diagnosis', ''),
                            key=f"assess_{session['id']}",
                            height=100,
                            help="Your professional assessment (not diagnosis - that's for doctors)"
                        )
                    
                    with col_b:
                        recommendations = st.text_area(
                            "Medication Recommendations",
                            value=session.get('pharmacist_prescription', ''),
                            key=f"rec_{session['id']}",
                            height=100,
                            help="OTC medications and dosage advice"
                        )
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if session['status'] in ['assigned', 'in_progress']:
                            if st.button("💾 Save Progress", key=f"save_{session['id']}"):
                                supabase.table('Consultations').update({
                                    'pharmacist_diagnosis': assessment,
                                    'pharmacist_prescription': recommendations,
                                    'status': 'in_progress'
                                }).eq('id', session['id']).execute()
                                st.success("Progress saved!")
                                st.rerun()
                    
                    with col2:
                        if session['status'] in ['assigned', 'in_progress']:
                            if st.button("✅ Complete Session", key=f"complete_{session['id']}"):
                                supabase.table('Consultations').update({
                                    'pharmacist_diagnosis': assessment,
                                    'pharmacist_prescription': recommendations,
                                    'status': 'completed',
                                    'completed_at': datetime.now().isoformat()
                                }).eq('id', session['id']).execute()
                                st.success("Session completed!")
                                st.rerun()
                    
                    with col3:
                        if session['status'] in ['assigned', 'in_progress']:
                            if st.button("👨‍⚕️ Refer to Doctor", key=f"refer_{session['id']}"):
                                supabase.table('Consultations').update({
                                    'pharmacist_diagnosis': assessment,
                                    'status': 'referred_to_doctor',
                                    'pharmacist_response': 'needs_doctor'
                                }).eq('id', session['id']).execute()
                                st.warning("Patient referred to doctor")
                                st.rerun()
    
    # ========================================================================
    # PAGE 3: REVIEWS & RATINGS
    # ========================================================================
    elif page == "⭐ Reviews & Ratings":
        st.title("⭐ Reviews & Ratings")
        
        # Get reviews
        reviews = supabase.table('reviews')\
            .select('*')\
            .eq('pharmacist_id', pharmacist_id)\
            .eq('review_type', 'pharmacist_review')\
            .order('created_at', desc=True)\
            .execute().data
        
        if not reviews:
            st.info("No reviews yet. Complete sessions to receive patient feedback!")
        else:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
            
            with col1:
                st.metric("Average Rating", f"{avg_rating:.2f} ⭐")
            
            with col2:
                st.metric("Total Reviews", len(reviews))
            
            with col3:
                five_star = len([r for r in reviews if r['rating'] == 5])
                st.metric("5-Star Reviews", five_star)
            
            st.markdown("---")
            
            # Rating distribution
            st.subheader("📊 Rating Distribution")
            
            rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for review in reviews:
                rating_counts[review['rating']] = rating_counts.get(review['rating'], 0) + 1
            
            df_ratings = pd.DataFrame({
                'Rating': ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
                'Count': [rating_counts[1], rating_counts[2], rating_counts[3], rating_counts[4], rating_counts[5]]
            })
            
            fig = px.bar(
                df_ratings,
                x='Rating',
                y='Count',
                title='Rating Distribution',
                color='Count',
                color_continuous_scale='Purples'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Individual reviews
            st.subheader("💬 Patient Feedback")
            
            for review in reviews:
                st.markdown(f"""
                <div class='review-card'>
                    <h4>{'⭐' * review['rating']} ({review['rating']}/5)</h4>
                    <p>{review.get('feedback', 'No written feedback provided')}</p>
                    <small>Patient ID: {review.get('user_id', 'Unknown')[:8]}... • {review['created_at'][:10]}</small>
                </div>
                """, unsafe_allow_html=True)
    
    # ========================================================================
    # PAGE 4: EARNINGS
    # ========================================================================
    elif page == "💰 Earnings":
        st.title("💰 My Earnings")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Earnings", f"₦{pharmacist_data.get('total_earnings', 0):,.0f}")
        
        with col2:
            # Calculate pending payout
            completed_unpaid = supabase.table('Consultations')\
                .select('pharmacist_payout')\
                .eq('pharmacist_id', pharmacist_id)\
                .eq('status', 'completed')\
                .eq('payout_status', 'pending')\
                .execute().data
            
            pending_amount = sum(c.get('pharmacist_payout', 400) for c in completed_unpaid)
            st.metric("Pending Payout", f"₦{pending_amount:,.0f}")
        
        with col3:
            # This month's earnings
            month_ago = (datetime.now() - timedelta(days=30)).date()
            month_sessions = supabase.table('Consultations')\
                .select('pharmacist_payout')\
                .eq('pharmacist_id', pharmacist_id)\
                .eq('status', 'completed')\
                .gte('completed_at', month_ago.isoformat())\
                .execute().data
            
            month_earnings = sum(c.get('pharmacist_payout', 400) for c in month_sessions)
            st.metric("This Month", f"₦{month_earnings:,.0f}")
        
        st.markdown("---")
        
        # Earnings trend
        st.subheader("📈 Earnings Trend (Last 30 Days)")
        
        earnings_data = supabase.table('Consultations')\
            .select('*')\
            .eq('pharmacist_id', pharmacist_id)\
            .eq('status', 'completed')\
            .gte('completed_at', month_ago.isoformat())\
            .order('completed_at', desc=False)\
            .execute().data
        
        if earnings_data:
            df = pd.DataFrame(earnings_data)
            df['completed_at'] = pd.to_datetime(df['completed_at'])
            df['date'] = df['completed_at'].dt.date
            df['payout'] = df['pharmacist_payout'].fillna(400)
            
            daily_earnings = df.groupby('date')['payout'].sum().reset_index()
            
            fig = px.line(
                daily_earnings,
                x='date',
                y='payout',
                title='Daily Earnings',
                labels={'date': 'Date', 'payout': 'Earnings (₦)'}
            )
            fig.update_traces(line_color='#7b1fa2', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No earnings data for the last 30 days")
        
        st.markdown("---")
        
        # Detailed transaction history
        st.subheader("📋 Transaction History")
        
        all_completed = supabase.table('Consultations')\
            .select('*')\
            .eq('pharmacist_id', pharmacist_id)\
            .eq('status', 'completed')\
            .order('completed_at', desc=True)\
            .limit(50)\
            .execute().data
        
        if all_completed:
            df_transactions = pd.DataFrame(all_completed)
            df_transactions['completed_at'] = pd.to_datetime(df_transactions['completed_at'])
            df_transactions['payout'] = df_transactions['pharmacist_payout'].fillna(400)
            
            display_df = df_transactions[[
                'completed_at', 'patient_name', 'payout', 'payout_status'
            ]].copy()
            
            display_df.columns = ['Date', 'Patient', 'Amount (₦)', 'Payout Status']
            display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Export option
            csv = display_df.to_csv(index=False)
            st.download_button(
                "📥 Export to CSV",
                data=csv,
                file_name=f"earnings_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No completed sessions yet")
    
    # ========================================================================
    # PAGE 5: SETTINGS
    # ========================================================================
    elif page == "⚙️ Settings":
        st.title("⚙️ Settings")
        
        # Profile information
        st.subheader("👤 Profile Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Full Name:** {pharmacist_data['full_name']}")
            st.write(f"**Phone Number:** {pharmacist_data['phone_number']}")
            st.write(f"**Email:** {pharmacist_data.get('email', 'Not provided')}")
        
        with col2:
            st.write(f"**PCN License:** {pharmacist_data.get('pcn_license_number', 'N/A')}")
            st.write(f"**Status:** {pharmacist_data.get('status', 'active')}")
            st.write(f"**Member Since:** {pharmacist_data.get('created_at', '')[:10]}")
        
        st.markdown("---")
        
        # Bank details
        st.subheader("💳 Bank Details (for Payouts)")
        
        bank_details = pharmacist_data.get('bank_details', {})
        
        with st.form("bank_details_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                account_name = st.text_input(
                    "Account Name",
                    value=bank_details.get('account_name', '') if isinstance(bank_details, dict) else ''
                )
                account_number = st.text_input(
                    "Account Number",
                    value=bank_details.get('account_number', '') if isinstance(bank_details, dict) else ''
                )
            
            with col2:
                bank_name = st.selectbox(
                    "Bank Name",
                    ["Select Bank", "GTBank", "Access Bank", "First Bank", "UBA", 
                     "Zenith Bank", "Stanbic IBTC", "Fidelity Bank", "Union Bank"],
                    index=0
                )
            
            if st.form_submit_button("💾 Update Bank Details", type="primary"):
                supabase.table('pharmacists').update({
                    'bank_details': {
                        'account_name': account_name,
                        'account_number': account_number,
                        'bank_name': bank_name
                    }
                }).eq('id', pharmacist_id).execute()
                st.success("Bank details updated successfully!")
                st.rerun()
        
        st.markdown("---")
        
        # Change password
        st.subheader("🔐 Change Password")
        
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Change Password"):
                st.info("Password change feature coming soon! Contact admin for now.")
        
        st.markdown("---")
        
        # Help and support
        st.subheader("❓ Help & Support")
        
        st.info("""
        **Need help?**
        
        Contact OgaDoctor Support:
        - 📞 Phone: +234XXXXXXXXX
        - 📧 Email: support@ogadoctor.com
        - 💬 WhatsApp: +234XXXXXXXXX
        
        Operating Hours: 8AM - 8PM (Mon-Sat)
        """)

# ============================================================================
# FOOTER
# ============================================================================
if st.session_state.logged_in:
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 20px;'>
            <p>OgaDoctor Pharmacist Portal v1.0 | © 2026 OgaDoctor Health Services</p>
        </div>
    """, unsafe_allow_html=True)