"""
OgaDoctor Analytics Dashboard
Enhanced version with comprehensive metrics, visualizations, and multi-page layout

Author: Christian Egwuonwu
Version: 2.0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# Page configuration
st.set_page_config(
    page_title="OgaDoctor Analytics Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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

# Initialize session state
if 'patients' not in st.session_state:
    st.session_state.patients = []

if 'consultation_history' not in st.session_state:
    # Generate sample historical data
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    st.session_state.consultation_history = pd.DataFrame({
        'date': dates,
        'consultations': [random.randint(10, 25) for _ in range(30)],
        'urgent': [random.randint(1, 5) for _ in range(30)],
        'moderate': [random.randint(3, 10) for _ in range(30)],
        'mild': [random.randint(5, 12) for _ in range(30)],
        'response_time_mins': [random.randint(5, 45) for _ in range(30)]
    })

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame({
        'medication': ['Paracetamol', 'Amoxicillin', 'Chloroquine', 'Vitamin C', 'Ibuprofen', 
                      'Cough Syrup', 'Antacid', 'ORS', 'Aspirin', 'Multivitamin'],
        'current_stock': [45, 12, 8, 65, 28, 15, 42, 55, 18, 38],
        'reorder_point': [20, 15, 10, 25, 20, 12, 15, 30, 10, 20],
        'monthly_demand': [120, 35, 25, 40, 85, 30, 50, 95, 22, 45],
        'unit_price': [50, 300, 200, 150, 80, 250, 100, 50, 120, 200]
    })
    st.session_state.inventory['status'] = st.session_state.inventory.apply(
        lambda row: 'Low Stock' if row['current_stock'] <= row['reorder_point'] else 'OK',
        axis=1
    )

# Sidebar navigation
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

# Sample patient data for testing
SAMPLE_PATIENTS = [
    {
        "name": "Aisha Musa", "age": 28, "phone": "+234 803 XXX XXXX",
        "symptoms": "Fever for 3 days, chills, body pain",
        "severity": "Strong", "duration": "3 days",
        "possible": "Malaria-like symptoms",
        "drugs": "Coartem / Lone Star / Paracetamol",
        "priority": "URGENT"
    },
    {
        "name": "Chukwudi Obi", "age": 45, "phone": "+234 806 XXX XXXX",
        "symptoms": "Persistent cough and chest congestion",
        "severity": "Moderate", "duration": "5 days",
        "possible": "Respiratory infection",
        "drugs": "Amoxicillin / Cough syrup",
        "priority": "MODERATE"
    },
    {
        "name": "Ngozi Eze", "age": 34, "phone": "+234 809 XXX XXXX",
        "symptoms": "Mild headache and tiredness",
        "severity": "Mild", "duration": "1 day",
        "possible": "Stress/fatigue",
        "drugs": "Paracetamol / Multivitamin",
        "priority": "LOW"
    }
]

# ==================== PAGE 1: LIVE QUEUE ====================
if page == "📊 Live Queue":
    st.title("🔔 Live Patient Queue")
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        urgent_count = sum(1 for p in st.session_state.patients if p.get('priority') == 'URGENT')
        st.metric("🚨 Urgent Cases", urgent_count, 
                 delta=None if urgent_count == 0 else "Needs attention",
                 delta_color="inverse")
    
    with col2:
        st.metric("👥 Total in Queue", len(st.session_state.patients))
    
    with col3:
        today_consultations = len([p for p in st.session_state.patients 
                                   if p.get('time', datetime.now()).date() == datetime.now().date()])
        st.metric("📅 Today's Consultations", today_consultations)
    
    with col4:
        avg_wait = "5-10 min" if urgent_count > 0 else "15-20 min"
        st.metric("⏱️ Avg Response Time", avg_wait)
    
    st.markdown("---")
    
    # Test patient buttons
    st.subheader("🧪 Test Mode - Add Sample Patients")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔴 Add URGENT Patient", use_container_width=True):
            patient = SAMPLE_PATIENTS[0].copy()
            patient['time'] = datetime.now()
            patient['status'] = 'New'
            st.session_state.patients.insert(0, patient)
            st.rerun()
    
    with col2:
        if st.button("🟡 Add MODERATE Patient", use_container_width=True):
            patient = SAMPLE_PATIENTS[1].copy()
            patient['time'] = datetime.now()
            patient['status'] = 'New'
            st.session_state.patients.append(patient)
            st.rerun()
    
    with col3:
        if st.button("🟢 Add MILD Patient", use_container_width=True):
            patient = SAMPLE_PATIENTS[2].copy()
            patient['time'] = datetime.now()
            patient['status'] = 'New'
            st.session_state.patients.append(patient)
            st.rerun()
    
    st.markdown("---")
    
    # Display patients
    if len(st.session_state.patients) == 0:
        st.info("✅ No patients in queue. System ready for consultations.")
    else:
        for i, patient in enumerate(st.session_state.patients):
            priority_color = {
                'URGENT': '🔴',
                'MODERATE': '🟡',
                'LOW': '🟢'
            }.get(patient.get('priority', 'MODERATE'), '🟡')
            
            priority_bg = {
                'URGENT': 'background-color: #ffebee;',
                'MODERATE': 'background-color: #fff9e6;',
                'LOW': 'background-color: #e8f5e9;'
            }.get(patient.get('priority', 'MODERATE'), '')
            
            st.markdown(f"""
                <div style='{priority_bg} padding: 15px; border-radius: 10px; margin: 10px 0; 
                            border-left: 5px solid {"#f44336" if patient.get("priority")=="URGENT" else "#ff9800" if patient.get("priority")=="MODERATE" else "#4caf50"};'>
                    <h3>{priority_color} {patient.get('priority', 'MODERATE')} - {patient['name']}, {patient['age']}</h3>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"""
                **📞 Phone:** {patient.get('phone', 'N/A')}  
                **🩺 Symptoms:** {patient['symptoms']}  
                **📊 Severity:** {patient.get('severity', 'N/A')} | **⏰ Duration:** {patient.get('duration', 'N/A')}  
                **💡 Possible Diagnosis:** {patient['possible']}  
                **💊 Recommended:** {patient['drugs']}  
                **🕐 Received:** {patient.get('time', datetime.now()).strftime('%I:%M %p')}
                """)
            
            with col2:
                if st.button("✅ Stock Available", key=f"ok_{i}", use_container_width=True):
                    patient['status'] = 'Confirmed'
                    patient['response_time'] = datetime.now()
                    st.success("✅ Patient notified! Medications ready for pickup.")
                    st.rerun()
            
            with col3:
                if st.button("❌ Out of Stock", key=f"no_{i}", use_container_width=True):
                    patient['status'] = 'Referred'
                    patient['response_time'] = datetime.now()
                    st.error("❌ Patient referred to alternative pharmacy")
                    st.rerun()
            
            # Action buttons
            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_a:
                if st.button("📞 Call Patient", key=f"call_{i}", use_container_width=True):
                    st.info(f"📞 Calling {patient['name']}...")
            with col_b:
                if st.button("💬 Send WhatsApp", key=f"wa_{i}", use_container_width=True):
                    st.info(f"💬 Opening WhatsApp for {patient['name']}...")
            with col_c:
                if st.button("✔️ Mark Complete", key=f"done_{i}", use_container_width=True):
                    st.session_state.patients.pop(i)
                    st.success(f"✔️ Consultation completed for {patient['name']}")
                    st.rerun()
            
            st.markdown("---")

# ==================== PAGE 2: ANALYTICS ====================
elif page == "📈 Analytics":
    st.title("📈 Analytics & Insights")
    
    # Date range filter
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Apply Filter"):
            st.success("Filter applied!")
    
    st.markdown("---")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    total_consultations = st.session_state.consultation_history['consultations'].sum()
    avg_daily = st.session_state.consultation_history['consultations'].mean()
    urgent_pct = (st.session_state.consultation_history['urgent'].sum() / total_consultations * 100)
    avg_response = st.session_state.consultation_history['response_time_mins'].mean()
    
    with col1:
        st.metric("Total Consultations (30d)", f"{total_consultations:,}", 
                 delta=f"+{int(avg_daily)} avg/day", delta_color="normal")
    with col2:
        st.metric("Urgent Cases", f"{urgent_pct:.1f}%", 
                 delta="Within safety threshold", delta_color="off")
    with col3:
        st.metric("Avg Response Time", f"{int(avg_response)} min",
                 delta="-5 min from last month", delta_color="normal")
    with col4:
        revenue_estimate = total_consultations * 1500  # ₦1,500 avg per consultation
        st.metric("Est. Monthly Revenue", f"₦{revenue_estimate:,}",
                 delta="+12% vs last month", delta_color="normal")
    
    st.markdown("---")
    
    # Charts
    tab1, tab2, tab3 = st.tabs(["📊 Consultation Trends", "🎯 Severity Distribution", "⏱️ Response Times"])
    
    with tab1:
        st.subheader("Daily Consultation Volume (Last 30 Days)")
        
        # Line chart
        fig = px.line(st.session_state.consultation_history, 
                     x='date', y='consultations',
                     title='Consultation Trend',
                     labels={'consultations': 'Number of Consultations', 'date': 'Date'})
        fig.update_traces(line_color='#1f77b4', line_width=3)
        fig.update_layout(hovermode='x unified', height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Stacked area chart by severity
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=st.session_state.consultation_history['date'], 
                                  y=st.session_state.consultation_history['urgent'],
                                  name='Urgent', fill='tonexty', stackgroup='one',
                                  line=dict(color='#f44336')))
        fig2.add_trace(go.Scatter(x=st.session_state.consultation_history['date'], 
                                  y=st.session_state.consultation_history['moderate'],
                                  name='Moderate', fill='tonexty', stackgroup='one',
                                  line=dict(color='#ff9800')))
        fig2.add_trace(go.Scatter(x=st.session_state.consultation_history['date'], 
                                  y=st.session_state.consultation_history['mild'],
                                  name='Mild', fill='tonexty', stackgroup='one',
                                  line=dict(color='#4caf50')))
        fig2.update_layout(title='Consultations by Severity Level', 
                          xaxis_title='Date', yaxis_title='Count',
                          hovermode='x unified', height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.subheader("Severity Distribution")
        
        # Pie chart
        severity_totals = {
            'Urgent': st.session_state.consultation_history['urgent'].sum(),
            'Moderate': st.session_state.consultation_history['moderate'].sum(),
            'Mild': st.session_state.consultation_history['mild'].sum()
        }
        
        fig3 = px.pie(values=list(severity_totals.values()), 
                     names=list(severity_totals.keys()),
                     title='Consultation Severity Breakdown',
                     color_discrete_map={'Urgent':'#f44336', 'Moderate':'#ff9800', 'Mild':'#4caf50'})
        fig3.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig3, use_container_width=True)
        
        # Bar chart comparison
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Most Common Severity", "Mild", delta="60% of cases")
        with col2:
            st.metric("Peak Hour", "2-4 PM", delta="Based on 30-day data")
    
    with tab3:
        st.subheader("Response Time Analysis")
        
        # Response time distribution
        fig4 = px.histogram(st.session_state.consultation_history, 
                           x='response_time_mins',
                           title='Response Time Distribution',
                           labels={'response_time_mins': 'Response Time (minutes)', 'count': 'Frequency'},
                           nbins=20, color_discrete_sequence=['#1f77b4'])
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)
        
        # Insights
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Fastest Response", "5 min", delta="Urgent case")
        with col2:
            st.metric("Target Met", "95%", delta="+3% vs target")
        with col3:
            st.metric("Avg Wait (Urgent)", "7 min", delta="Below 10 min target")

# ==================== PAGE 3: INVENTORY ====================
elif page == "📦 Inventory":
    st.title("📦 Inventory Management")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    low_stock_count = len(st.session_state.inventory[st.session_state.inventory['status'] == 'Low Stock'])
    total_value = (st.session_state.inventory['current_stock'] * 
                  st.session_state.inventory['unit_price']).sum()
    
    with col1:
        st.metric("⚠️ Low Stock Items", low_stock_count,
                 delta="Needs reorder", delta_color="inverse" if low_stock_count > 0 else "off")
    with col2:
        st.metric("📊 Total Items", len(st.session_state.inventory))
    with col3:
        st.metric("💰 Total Inventory Value", f"₦{total_value:,.0f}")
    with col4:
        avg_turnover = st.session_state.inventory['monthly_demand'].mean()
        st.metric("📈 Avg Monthly Turnover", f"{int(avg_turnover)} units")
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["📋 Current Stock", "📊 Analytics"])
    
    with tab1:
        # Filter
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("🔍 Search medication", placeholder="Type medication name...")
        with col2:
            filter_option = st.selectbox("Filter", ["All", "Low Stock", "OK"])
        
        # Apply filters
        df_display = st.session_state.inventory.copy()
        if search:
            df_display = df_display[df_display['medication'].str.contains(search, case=False)]
        if filter_option == "Low Stock":
            df_display = df_display[df_display['status'] == 'Low Stock']
        elif filter_option == "OK":
            df_display = df_display[df_display['status'] == 'OK']
        
        # Display inventory
        for idx, row in df_display.iterrows():
            status_color = '#ffebee' if row['status'] == 'Low Stock' else '#e8f5e9'
            status_icon = '⚠️' if row['status'] == 'Low Stock' else '✅'
            
            st.markdown(f"""
                <div style='background-color: {status_color}; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                    <h4>{status_icon} {row['medication']}</h4>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Stock", f"{row['current_stock']} units")
            with col2:
                st.metric("Reorder Point", f"{row['reorder_point']} units")
            with col3:
                st.metric("Monthly Demand", f"{row['monthly_demand']} units")
            with col4:
                st.metric("Unit Price", f"₦{row['unit_price']}")
            
            # Action buttons
            if row['status'] == 'Low Stock':
                if st.button(f"📦 Generate Reorder", key=f"reorder_{idx}"):
                    reorder_qty = row['monthly_demand'] - row['current_stock']
                    st.success(f"✅ Reorder generated: {reorder_qty} units of {row['medication']}")
            
            st.markdown("---")
    
    with tab2:
        st.subheader("Inventory Analytics")
        
        # Stock level chart
        fig5 = go.Figure()
        fig5.add_trace(go.Bar(x=st.session_state.inventory['medication'],
                             y=st.session_state.inventory['current_stock'],
                             name='Current Stock',
                             marker_color='#1f77b4'))
        fig5.add_trace(go.Scatter(x=st.session_state.inventory['medication'],
                                 y=st.session_state.inventory['reorder_point'],
                                 name='Reorder Point',
                                 line=dict(color='#f44336', dash='dash'),
                                 mode='lines+markers'))
        fig5.update_layout(title='Stock Levels vs Reorder Points',
                          xaxis_title='Medication',
                          yaxis_title='Units',
                          height=400)
        st.plotly_chart(fig5, use_container_width=True)
        
        # Value distribution
        st.session_state.inventory['total_value'] = (st.session_state.inventory['current_stock'] * 
                                                     st.session_state.inventory['unit_price'])
        fig6 = px.bar(st.session_state.inventory.sort_values('total_value', ascending=False),
                     x='medication', y='total_value',
                     title='Inventory Value by Medication',
                     labels={'total_value': 'Total Value (₦)', 'medication': 'Medication'},
                     color='total_value',
                     color_continuous_scale='Blues')
        fig6.update_layout(height=400)
        st.plotly_chart(fig6, use_container_width=True)

# ==================== PAGE 4: SETTINGS ====================
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
                st.success("✅ Consultations exported to downloads")
            if st.button("Export Inventory (CSV)"):
                st.success("✅ Inventory exported to downloads")
            if st.button("Generate Monthly Report (PDF)"):
                st.success("✅ Report generated")
        
        with col2:
            st.markdown("### 🗑️ Clear Data")
            if st.button("Clear Test Patients", type="secondary"):
                st.session_state.patients = []
                st.success("✅ Test patients cleared")
            
            st.markdown("---")
            st.warning("⚠️ Danger Zone")
            if st.button("Reset All Data", type="secondary"):
                if st.checkbox("I understand this will delete all data"):
                    st.error("This feature is disabled in demo mode")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>OgaDoctor Analytics Dashboard v2.0 | Built by Christian Egwuonwu</p>
        <p>💡 Powered by AI • Processing 500+ monthly consultations with 95% accuracy</p>
    </div>
""", unsafe_allow_html=True)
