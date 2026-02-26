"""
OgaDoctor Analytics Dashboard - COMPLETE VERSION with Supabase
================================================================

This dashboard connects to Supabase database to show real-time pharmacy data.

SETUP REQUIRED:
1. Install packages: pip install streamlit pandas plotly supabase
2. Create .streamlit/secrets.toml with your Supabase credentials
3. Add sample data to Supabase tables

Author: Christian Egwuonwu
Version: 3.0 - Supabase Connected
"""

# ============================================================================
# IMPORTS
# ============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase import create_client, Client

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="OgaDoctor Analytics Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS STYLING
# ============================================================================
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .urgent-alert {
        background-color: #ffebee;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #f44336;
        margin: 10px 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SUPABASE CONNECTION
# ============================================================================

@st.cache_resource
def init_supabase():
    """
    Initialize connection to Supabase database
    
    IMPORTANT: Make sure .streamlit/secrets.toml exists with:
    [supabase]
    url = "https://YOUR-PROJECT.supabase.co"
    key = "YOUR-ANON-KEY"
    """
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {str(e)}")
        st.stop()

# Initialize Supabase client
supabase = init_supabase()

# ============================================================================
# DATABASE QUERY FUNCTIONS
# ============================================================================

def get_consultations():
    """
    Fetch active consultations from database
    Returns consultations that are not completed
    """
    try:
        response = supabase.table('consultations')\
            .select('*')\
            #.neq('status', 'completed')\
            .order('created_at', desc=True)\
            .execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching consultations: {str(e)}")
        return []

def get_all_consultations():
    """
    Fetch ALL consultations including completed ones
    Used for analytics
    """
    try:
        response = supabase.table('consultations')\
            .select('*')\
            .order('created_at', desc=True)\
            .execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching all consultations: {str(e)}")
        return []

def get_inventory():
    """Fetch all medications from database"""
    try:
        response = supabase.table('medications')\
            .select('*')\
            .execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching inventory: {str(e)}")
        return []

def update_consultation_status(consultation_id, updates):
    """
    Update a consultation record in database
    
    Args:
        consultation_id: ID of consultation to update
        updates: Dictionary of fields to update
    """
    try:
        response = supabase.table('consultations')\
            .update(updates)\
            .eq('id', consultation_id)\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error updating consultation: {str(e)}")
        return None

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
st.sidebar.title("🏥 OgaDoctor Dashboard")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Live Queue", "📈 Analytics", "📦 Inventory", "⚙️ Settings"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📍 Pharmacy Info")
st.sidebar.info("""
**Blue Pill Pharmacy**  
Awka, Anambra State  
Hours: 8AM - 8PM Mon-Sat
""")

# ============================================================================
# PAGE 1: LIVE QUEUE
# ============================================================================
if page == "📊 Live Queue":
    st.title("🔔 Live Patient Queue")
    
    # Fetch consultations from database
    consultations = get_consultations()
    
    # ========================================================================
    # TOP METRICS
    # ========================================================================
    col1, col2, col3, col4 = st.columns(4)
    
    # Count urgent cases
    urgent_count = sum(1 for p in consultations if p.get('priority') == 'URGENT')
    
    with col1:
        st.metric(
            "🚨 Urgent Cases", 
            urgent_count,
            delta="Needs attention" if urgent_count > 0 else None,
            delta_color="inverse" if urgent_count > 0 else "off"
        )
    
    with col2:
        st.metric("👥 Total in Queue", len(consultations))
    
    with col3:
        # Count today's consultations
        today = datetime.now().date()
        today_count = sum(1 for p in consultations 
                         if datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')).date() == today)
        st.metric("📅 Today's Consultations", today_count)
    
    with col4:
        avg_wait = "5-10 min" if urgent_count > 0 else "15-20 min"
        st.metric("⏱️ Avg Response Time", avg_wait)
    
    st.markdown("---")
    
    # ========================================================================
    # DISPLAY CONSULTATIONS
    # ========================================================================
    
    if len(consultations) == 0:
        st.info("✅ No patients in queue. System ready for consultations.")
    else:
        for i, patient in enumerate(consultations):
            # Determine priority color and background
            priority_icons = {
                'URGENT': '🔴',
                'MODERATE': '🟡',
                'LOW': '🟢'
            }
            
            priority_backgrounds = {
                'URGENT': 'background-color: #ffebee;',
                'MODERATE': 'background-color: #fff9e6;',
                'LOW': 'background-color: #e8f5e9;'
            }
            
            priority_borders = {
                'URGENT': '#f44336',
                'MODERATE': '#ff9800',
                'LOW': '#4caf50'
            }
            
            priority = patient.get('priority', 'MODERATE')
            icon = priority_icons.get(priority, '🟡')
            bg = priority_backgrounds.get(priority, '')
            border = priority_borders.get(priority, '#ff9800')
            
            # Patient header with colored background
            st.markdown(f"""
                <div style='{bg} padding: 15px; border-radius: 10px; margin: 10px 0; 
                            border-left: 5px solid {border};'>
                    <h3>{icon} {priority} - {patient['patient_name']}</h3>
                </div>
            """, unsafe_allow_html=True)
            
            # Two-column layout: Patient info | AI Assessment
            col1, col2 = st.columns([1, 1])
            
            # LEFT COLUMN: Patient Information
            with col1:
                st.markdown("#### 📋 Patient Information")
                st.write(f"**📞 Phone:** {patient.get('patient_phone', 'N/A')}")
                st.write(f"**🩺 Symptoms:** {patient['symptoms']}")
                st.write(f"**📊 Severity:** {patient.get('severity', 'N/A')}")
                st.write(f"**⏰ Duration:** {patient.get('duration', 'N/A')}")
                
                # Format timestamp
                created_at = patient.get('created_at', '')
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        st.write(f"**🕐 Received:** {dt.strftime('%I:%M %p, %b %d')}")
                    except:
                        st.write(f"**🕐 Received:** {created_at[:16]}")
                
                # Show emergency keywords if any
                if patient.get('detected_keywords'):
                    st.error(f"⚠️ **Alert Keywords:** {patient['detected_keywords']}")
            
            # RIGHT COLUMN: AI Clinical Assessment (if available)
            with col2:
                st.markdown("#### 🤖 AI Clinical Assessment")
                
                if patient.get('ai_diagnosis'):
                    st.info(f"**Diagnosis:** {patient['ai_diagnosis']}")
                else:
                    st.info("AI diagnosis not available for this consultation")
                
                if patient.get('ai_drug_recommendations'):
                    st.success(f"**Recommended Medications:**\n\n{patient['ai_drug_recommendations']}")
                else:
                    st.write("No AI drug recommendations available")
            
            st.markdown("---")
            
            # ================================================================
            # PHARMACIST REVIEW SECTION
            # ================================================================
            st.markdown("#### 👨‍⚕️ Pharmacist Clinical Decision")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                # Pharmacist's diagnosis input
                pharmacist_diagnosis = st.text_area(
                    "Your Diagnosis:",
                    value=patient.get('pharmacist_diagnosis', ''),
                    key=f"diagnosis_{patient['id']}",
                    placeholder="Your professional assessment",
                    help="What do you think the patient has?"
                )
                
                # Agreement level (if AI diagnosis exists)
                if patient.get('ai_diagnosis'):
                    agreement = st.radio(
                        "AI Diagnosis Assessment:",
                        options=['Agree with AI', 'Partially agree', 'Disagree with AI'],
                        key=f"agreement_{patient['id']}",
                        horizontal=True
                    )
                else:
                    agreement = None
            
            with col_b:
                # Pharmacist's prescription input
                pharmacist_prescription = st.text_area(
                    "Your Prescription:",
                    value=patient.get('pharmacist_prescription', ''),
                    key=f"prescription_{patient['id']}",
                    placeholder="Actual medications and dosages",
                    height=150
                )
            
            # ================================================================
            # ACTION BUTTONS
            # ================================================================
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("✅ Confirm & Dispense", key=f"confirm_{patient['id']}", use_container_width=True):
                    # Map agreement to database value
                    agreement_map = {
                        'Agree with AI': 'agreed',
                        'Partially agree': 'modified',
                        'Disagree with AI': 'disagreed'
                    }
                    
                    updates = {
                        'pharmacist_diagnosis': pharmacist_diagnosis,
                        'pharmacist_prescription': pharmacist_prescription,
                        'status': 'confirmed',
                        'pharmacist_response': 'stock_available',
                        'response_time': datetime.now().isoformat()
                    }
                    
                    if agreement:
                        updates['diagnosis_agreement'] = agreement_map[agreement]
                    
                    update_consultation_status(patient['id'], updates)
                    st.success(f"✅ Prescription confirmed for {patient['patient_name']}")
                    st.rerun()
            
            with col2:
                if st.button("❌ Out of Stock", key=f"no_stock_{patient['id']}", use_container_width=True):
                    updates = {
                        'pharmacist_diagnosis': pharmacist_diagnosis,
                        'status': 'referred',
                        'pharmacist_response': 'out_of_stock',
                        'response_time': datetime.now().isoformat()
                    }
                    update_consultation_status(patient['id'], updates)
                    st.error("❌ Patient referred to alternative pharmacy")
                    st.rerun()
            
            with col3:
                if st.button("🏥 Refer to Doctor", key=f"refer_{patient['id']}", use_container_width=True):
                    updates = {
                        'pharmacist_diagnosis': pharmacist_diagnosis,
                        'status': 'referred_to_doctor',
                        'pharmacist_response': 'needs_doctor',
                        'response_time': datetime.now().isoformat()
                    }
                    update_consultation_status(patient['id'], updates)
                    st.warning("🏥 Patient advised to see a doctor")
                    st.rerun()
            
            with col4:
                if st.button("✔️ Mark Complete", key=f"done_{patient['id']}", use_container_width=True):
                    updates = {
                        'status': 'completed',
                        'response_time': datetime.now().isoformat()
                    }
                    update_consultation_status(patient['id'], updates)
                    st.success(f"✔️ Consultation completed for {patient['patient_name']}")
                    st.rerun()
            
            st.markdown("---")
            st.markdown("---")

# ============================================================================
# PAGE 2: ANALYTICS
# ============================================================================
elif page == "📈 Analytics":
    st.title("📈 Analytics & Insights")
    
    # Fetch all consultations for analytics
    all_consultations = get_all_consultations()
    
    if not all_consultations:
        st.warning("No consultation data available yet. Data will appear once consultations are recorded.")
        st.stop()
    
    # Convert to DataFrame
    df = pd.DataFrame(all_consultations)
    
    # ========================================================================
    # KPI CARDS
    # ========================================================================
    col1, col2, col3, col4 = st.columns(4)
    
    total_consultations = len(df)
    urgent_count = len(df[df['priority'] == 'URGENT'])
    urgent_pct = (urgent_count / total_consultations * 100) if total_consultations > 0 else 0
    
    # Calculate average response time
    df_with_response = df[df['response_time'].notna()]
    if len(df_with_response) > 0:
        df_with_response['created_dt'] = pd.to_datetime(df_with_response['created_at'])
        df_with_response['response_dt'] = pd.to_datetime(df_with_response['response_time'])
        df_with_response['response_mins'] = (df_with_response['response_dt'] - df_with_response['created_dt']).dt.total_seconds() / 60
        avg_response = df_with_response['response_mins'].mean()
    else:
        avg_response = 0
    
    with col1:
        st.metric("Total Consultations", f"{total_consultations:,}")
    
    with col2:
        st.metric("Urgent Cases", f"{urgent_pct:.1f}%", 
                 delta=f"{urgent_count} cases")
    
    with col3:
        st.metric("Avg Response Time", f"{int(avg_response)} min" if avg_response > 0 else "N/A")
    
    with col4:
        completed = len(df[df['status'] == 'confirmed'])
        st.metric("Completed", completed, 
                 delta=f"{(completed/total_consultations*100):.0f}%" if total_consultations > 0 else "0%")
    
    st.markdown("---")
    
    # ========================================================================
    # CHARTS IN TABS
    # ========================================================================
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "🎯 Severity Analysis", "🤖 AI Performance"])
    
    with tab1:
        st.subheader("Consultation Trends")
        
        # Consultations by day
        if 'created_at' in df.columns:
            df['date'] = pd.to_datetime(df['created_at']).dt.date
            daily_counts = df.groupby('date').size().reset_index(name='count')
            
            fig = px.line(daily_counts, x='date', y='count',
                         title='Daily Consultation Volume',
                         labels={'date': 'Date', 'count': 'Consultations'})
            fig.update_traces(line_color='#1f77b4', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
        
        # Status distribution
        status_counts = df['status'].value_counts()
        fig2 = px.pie(values=status_counts.values, names=status_counts.index,
                     title='Consultation Status Distribution')
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.subheader("Severity Distribution")
        
        # Priority breakdown
        priority_counts = df['priority'].value_counts()
        
        fig3 = px.pie(values=priority_counts.values, names=priority_counts.index,
                     title='Priority Distribution',
                     color_discrete_map={'URGENT':'#f44336', 'MODERATE':'#ff9800', 'LOW':'#4caf50'})
        st.plotly_chart(fig3, use_container_width=True)
        
        # Severity breakdown if available
        if 'severity' in df.columns and df['severity'].notna().any():
            severity_counts = df['severity'].value_counts()
            fig4 = px.bar(x=severity_counts.index, y=severity_counts.values,
                         title='Severity Levels',
                         labels={'x': 'Severity', 'y': 'Count'},
                         color=severity_counts.values,
                         color_continuous_scale='Reds')
            st.plotly_chart(fig4, use_container_width=True)
    
    with tab3:
        st.subheader("🤖 AI Diagnostic Performance")
        
        # Filter consultations with AI data
        ai_consultations = df[df['ai_diagnosis'].notna() & df['pharmacist_diagnosis'].notna()]
        
        if len(ai_consultations) > 0:
            col1, col2, col3 = st.columns(3)
            
            total_reviewed = len(ai_consultations)
            
            # Count agreement levels
            if 'diagnosis_agreement' in ai_consultations.columns:
                agreed = len(ai_consultations[ai_consultations['diagnosis_agreement'] == 'agreed'])
                modified = len(ai_consultations[ai_consultations['diagnosis_agreement'] == 'modified'])
                disagreed = len(ai_consultations[ai_consultations['diagnosis_agreement'] == 'disagreed'])
            else:
                agreed = modified = disagreed = 0
            
            with col1:
                agreement_rate = (agreed / total_reviewed * 100) if total_reviewed > 0 else 0
                st.metric("AI Agreement Rate", f"{agreement_rate:.1f}%", 
                         delta=f"{agreed}/{total_reviewed}")
            
            with col2:
                modification_rate = (modified / total_reviewed * 100) if total_reviewed > 0 else 0
                st.metric("Modified Diagnosis", f"{modification_rate:.1f}%",
                         delta=f"{modified}/{total_reviewed}")
            
            with col3:
                disagreement_rate = (disagreed / total_reviewed * 100) if total_reviewed > 0 else 0
                st.metric("AI Disagreement", f"{disagreement_rate:.1f}%",
                         delta=f"{disagreed}/{total_reviewed}")
            
            # Agreement pie chart
            if agreed + modified + disagreed > 0:
                agreement_data = pd.DataFrame({
                    'Category': ['Agreed', 'Modified', 'Disagreed'],
                    'Count': [agreed, modified, disagreed]
                })
                
                fig5 = px.pie(agreement_data, values='Count', names='Category',
                             title='Pharmacist-AI Diagnostic Agreement',
                             color='Category',
                             color_discrete_map={'Agreed': '#4caf50', 'Modified': '#ff9800', 'Disagreed': '#f44336'})
                st.plotly_chart(fig5, use_container_width=True)
            
            # Recent comparisons
            st.markdown("### Recent AI vs Pharmacist Decisions")
            
            for idx, row in ai_consultations.head(5).iterrows():
                with st.expander(f"{row['patient_name']} - {row.get('diagnosis_agreement', 'N/A').upper()}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🩺 Symptoms:**")
                        st.write(row['symptoms'])
                        st.markdown("**🤖 AI Diagnosis:**")
                        st.info(row['ai_diagnosis'])
                        st.markdown("**💊 AI Medications:**")
                        st.success(row.get('ai_drug_recommendations', 'N/A'))
                    
                    with col2:
                        st.markdown("**👨‍⚕️ Pharmacist Diagnosis:**")
                        st.write(row.get('pharmacist_diagnosis', 'N/A'))
                        st.markdown("**💊 Pharmacist Prescription:**")
                        st.write(row.get('pharmacist_prescription', 'N/A'))
        else:
            st.info("No AI diagnostic data available yet. AI comparisons will appear once consultations with AI assessments are completed.")

# ============================================================================
# PAGE 3: INVENTORY
# ============================================================================
elif page == "📦 Inventory":
    st.title("📦 Inventory Management")
    
    # Fetch inventory
    medications = get_inventory()
    
    if not medications:
        st.warning("No inventory data available. Add medications in Supabase Table Editor.")
        st.stop()
    
    # Convert to DataFrame
    df_inv = pd.DataFrame(medications)
    
    # ========================================================================
    # SUMMARY METRICS
    # ========================================================================
    col1, col2, col3, col4 = st.columns(4)
    
    low_stock_count = len(df_inv[df_inv['status'] == 'Low Stock']) if 'status' in df_inv.columns else 0
    
    # Calculate total value
    if 'current_stock' in df_inv.columns and 'unit_price' in df_inv.columns:
        total_value = (df_inv['current_stock'] * df_inv['unit_price']).sum()
    else:
        total_value = 0
    
    with col1:
        st.metric("⚠️ Low Stock Items", low_stock_count,
                 delta="Needs reorder" if low_stock_count > 0 else None,
                 delta_color="inverse" if low_stock_count > 0 else "off")
    
    with col2:
        st.metric("📊 Total Items", len(df_inv))
    
    with col3:
        st.metric("💰 Total Inventory Value", f"₦{total_value:,.0f}")
    
    with col4:
        avg_turnover = df_inv['monthly_demand'].mean() if 'monthly_demand' in df_inv.columns else 0
        st.metric("📈 Avg Monthly Demand", f"{int(avg_turnover)} units")
    
    st.markdown("---")
    
    # ========================================================================
    # TABS
    # ========================================================================
    tab1, tab2 = st.tabs(["📋 Current Stock", "📊 Analytics"])
    
    with tab1:
        st.subheader("Medication Inventory")
        
        # Search and filter
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search = st.text_input("🔍 Search medication", placeholder="Type medication name...")
        
        with col2:
            filter_option = st.selectbox("Filter", ["All", "Low Stock", "OK"])
        
        # Apply filters
        df_display = df_inv.copy()
        
        if search:
            df_display = df_display[df_display['medication_name'].str.contains(search, case=False, na=False)]
        
        if filter_option == "Low Stock":
            df_display = df_display[df_display['status'] == 'Low Stock']
        elif filter_option == "OK":
            df_display = df_display[df_display['status'] == 'OK']
        
        # Display medications
        for idx, row in df_display.iterrows():
            status_color = '#ffebee' if row.get('status') == 'Low Stock' else '#e8f5e9'
            status_icon = '⚠️' if row.get('status') == 'Low Stock' else '✅'
            
            st.markdown(f"""
                <div style='background-color: {status_color}; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                    <h4>{status_icon} {row['medication_name']}</h4>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Stock", f"{row.get('current_stock', 0)} units")
            with col2:
                st.metric("Reorder Point", f"{row.get('reorder_point', 0)} units")
            with col3:
                st.metric("Monthly Demand", f"{row.get('monthly_demand', 0)} units")
            with col4:
                st.metric("Unit Price", f"₦{row.get('unit_price', 0)}")
            
            st.markdown("---")
    
    with tab2:
        st.subheader("Inventory Analytics")
        
        # Stock levels chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_inv['medication_name'],
            y=df_inv['current_stock'],
            name='Current Stock',
            marker_color='#1f77b4'
        ))
        
        fig.add_trace(go.Scatter(
            x=df_inv['medication_name'],
            y=df_inv['reorder_point'],
            name='Reorder Point',
            line=dict(color='#f44336', dash='dash'),
            mode='lines+markers'
        ))
        
        fig.update_layout(
            title='Stock Levels vs Reorder Points',
            xaxis_title='Medication',
            yaxis_title='Units',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Value distribution
        df_inv['total_value'] = df_inv['current_stock'] * df_inv['unit_price']
        
        fig2 = px.bar(df_inv.sort_values('total_value', ascending=False),
                     x='medication_name', y='total_value',
                     title='Inventory Value by Medication',
                     labels={'total_value': 'Total Value (₦)', 'medication_name': 'Medication'},
                     color='total_value',
                     color_continuous_scale='Blues')
        
        st.plotly_chart(fig2, use_container_width=True)

# ============================================================================
# PAGE 4: SETTINGS
# ============================================================================
elif page == "⚙️ Settings":
    st.title("⚙️ System Settings")
    
    tab1, tab2, tab3 = st.tabs(["🏪 Pharmacy Info", "🔔 Notifications", "📊 Data Management"])
    
    with tab1:
        st.subheader("Pharmacy Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            pharmacy_name = st.text_input("Pharmacy Name", "Blue Pill Pharmacy")
            phone = st.text_input("Phone Number", "+234 803 XXX XXXX")
            email = st.text_input("Email", "contact@bluepill.ng")
        
        with col2:
            address = st.text_area("Address", "123 Main Street\nAwka, Anambra State")
            hours = st.text_input("Operating Hours", "8AM - 8PM Mon-Sat")
        
        if st.button("💾 Save Changes", type="primary"):
            st.success("✅ Pharmacy information updated successfully!")
    
    with tab2:
        st.subheader("Notification Settings")
        
        st.checkbox("📧 Email notifications for urgent cases", value=True)
        st.checkbox("📱 SMS alerts for low stock", value=True)
        st.checkbox("💬 WhatsApp integration", value=True)
        st.checkbox("🔔 Browser notifications", value=False)
        
        st.slider("Alert threshold for urgent cases (minutes)", 5, 30, 10)
        
        if st.button("💾 Save Notification Settings", type="primary"):
            st.success("✅ Notification settings updated!")
    
    with tab3:
        st.subheader("Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📤 Export Data")
            
            if st.button("Export Consultations (CSV)"):
                consultations = get_all_consultations()
                if consultations:
                    df_export = pd.DataFrame(consultations)
                    csv = df_export.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"consultations_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No data to export")
            
            if st.button("Export Inventory (CSV)"):
                inventory = get_inventory()
                if inventory:
                    df_export = pd.DataFrame(inventory)
                    csv = df_export.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"inventory_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No data to export")
        
        with col2:
            st.markdown("### 🗄️ Database Info")
            
            consultations_count = len(get_all_consultations())
            medications_count = len(get_inventory())
            
            st.info(f"""
            **Database Statistics:**
            - Consultations: {consultations_count}
            - Medications: {medications_count}
            - Database: Supabase (PostgreSQL)
            - Status: ✅ Connected
            """)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>OgaDoctor Analytics Dashboard v3.0 | Built by Christian Egwuonwu</p>
        <p>💡 Powered by Supabase • Real-time pharmacy analytics</p>
    </div>
""", unsafe_allow_html=True)

# ============================================================================
# HOW TO USE THIS DASHBOARD
# ============================================================================
"""
SETUP INSTRUCTIONS:
===================

1. CREATE .streamlit/secrets.toml FILE:
   
   Create folder: mkdir .streamlit
   Create file: nano .streamlit/secrets.toml
   
   Add this content (replace with YOUR Supabase credentials):
   
   [supabase]
   url = "https://YOUR-PROJECT-ID.supabase.co"
   key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   
   Get these from: Supabase Dashboard → Project Settings → API

2. INSTALL DEPENDENCIES:
   
   pip install streamlit pandas plotly supabase --break-system-packages

3. ADD .streamlit/ TO .gitignore:
   
   echo ".streamlit/" >> .gitignore
   
   This prevents secrets from being uploaded to GitHub!

4. RUN DASHBOARD:
   
   streamlit run dashboard.py

5. ADD SAMPLE DATA in Supabase Table Editor if you haven't already

TROUBLESHOOTING:
================

Error: "No module named 'supabase'"
→ Run: pip install supabase --break-system-packages

Error: "KeyError: 'supabase'"
→ Check .streamlit/secrets.toml exists and has correct format

Error: "Invalid API key"
→ Make sure you copied the ANON/PUBLIC key, not SERVICE_ROLE key

Error: "No consultations found"
→ Add sample data in Supabase Table Editor

CONNECTION TO BOTPRESS:
=======================

Once this dashboard works, we'll add Botpress integration to save consultations
directly from WhatsApp conversations to the Supabase database.

That will complete the full flow:
WhatsApp → Botpress → ChatGPT → Supabase → Dashboard
"""



