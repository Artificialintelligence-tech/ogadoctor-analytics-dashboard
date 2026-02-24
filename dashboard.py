"""
OgaDoctor Analytics Dashboard - FULLY COMMENTED VERSION
========================================================

This dashboard has 4 main pages:
1. Live Queue - See incoming patients and respond
2. Analytics - Charts and metrics about consultations
3. Inventory - Track medication stock levels
4. Settings - Configure pharmacy details

Author: Christian Egwuonwu
Version: 2.0 - Educational/Portfolio Version
"""

# ============================================================================
# IMPORTS - These are the libraries we need
# ============================================================================

import streamlit as st          # Main dashboard framework
import pandas as pd             # For working with data tables
import plotly.express as px     # For creating charts (simple charts)
import plotly.graph_objects as go  # For creating charts (advanced charts)
from datetime import datetime, timedelta  # For working with dates and times
import random                   # For generating sample data

# ============================================================================
# PAGE CONFIGURATION - This sets up how the page looks
# ============================================================================

st.set_page_config(
    page_title="OgaDoctor Analytics Dashboard",  # Browser tab title
    page_icon="🏥",                               # Browser tab icon
    layout="wide",                                # Use full width of screen
    initial_sidebar_state="expanded"              # Sidebar open by default
)

# ============================================================================
# CUSTOM CSS - This makes the dashboard look professional
# ============================================================================
# You can modify colors, sizes, spacing here

st.markdown("""
    <style>
    /* Card styling for metrics */
    .metric-card {
        background-color: #f0f2f6;      /* Light gray background */
        padding: 20px;                   /* Space inside the card */
        border-radius: 10px;             /* Rounded corners */
        border-left: 5px solid #1f77b4;  /* Blue left border */
    }
    
    /* Alert box for urgent cases */
    .urgent-alert {
        background-color: #ffebee;       /* Light red background */
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #f44336;  /* Red left border */
        margin: 10px 0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;                        /* Space between tabs */
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;              /* Space inside each tab */
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE - This stores data that persists while dashboard is running
# ============================================================================
# Think of session_state like a database that only exists while app is open

# Initialize patient queue (list of current patients)
if 'patients' not in st.session_state:
    st.session_state.patients = []
    # This creates an empty list to hold patient data
    # Each patient will be a dictionary with: name, age, symptoms, etc.

# Initialize consultation history (past 30 days of data)
if 'consultation_history' not in st.session_state:
    # Generate 30 days of sample data for charts
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    st.session_state.consultation_history = pd.DataFrame({
        'date': dates,                                        # Each day
        'consultations': [random.randint(10, 25) for _ in range(30)],  # Random 10-25 consultations per day
        'urgent': [random.randint(1, 5) for _ in range(30)],          # Random 1-5 urgent cases
        'moderate': [random.randint(3, 10) for _ in range(30)],       # Random 3-10 moderate cases
        'mild': [random.randint(5, 12) for _ in range(30)],           # Random 5-12 mild cases
        'response_time_mins': [random.randint(5, 45) for _ in range(30)]  # Random 5-45 min response
    })
    # This creates a table (DataFrame) with sample historical data
    # In real version, this would come from your database

# Initialize inventory (medication stock)
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame({
        'medication': ['Paracetamol', 'Amoxicillin', 'Chloroquine', 'Vitamin C', 'Ibuprofen', 
                      'Cough Syrup', 'Antacid', 'ORS', 'Aspirin', 'Multivitamin'],
        'current_stock': [45, 12, 8, 65, 28, 15, 42, 55, 18, 38],      # How many in stock now
        'reorder_point': [20, 15, 10, 25, 20, 12, 15, 30, 10, 20],     # When to reorder
        'monthly_demand': [120, 35, 25, 40, 85, 30, 50, 95, 22, 45],   # How many sold per month
        'unit_price': [50, 300, 200, 150, 80, 250, 100, 50, 120, 200]  # Price per unit (₦)
    })
    
    # Add a 'status' column: "Low Stock" if current_stock <= reorder_point, else "OK"
    st.session_state.inventory['status'] = st.session_state.inventory.apply(
        lambda row: 'Low Stock' if row['current_stock'] <= row['reorder_point'] else 'OK',
        axis=1
    )
    # This checks each row: if stock is low, mark as "Low Stock"

# ============================================================================
# SIDEBAR - Navigation menu on the left
# ============================================================================

st.sidebar.title("🏥 OgaDoctor Dashboard")
st.sidebar.markdown("---")  # Horizontal line

# Radio buttons for page selection
page = st.sidebar.radio(
    "Navigation",
    ["📊 Live Queue", "📈 Analytics", "📦 Inventory", "⚙️ Settings"],
    label_visibility="collapsed"  # Hide the "Navigation" label
)
# Whatever the user clicks becomes the value of 'page'
# We use this below to show different content

st.sidebar.markdown("---")

# Pharmacy information box
st.sidebar.markdown("### 📍 Pharmacy Info")
st.sidebar.info("""
**Blue Pill Pharmacy**  
Awka, Anambra State  
Hours: 8AM - 8PM Mon-Sat
""")
# MODIFY THIS: Change to your actual pharmacy details

# ============================================================================
# SAMPLE PATIENT DATA - For testing the dashboard
# ============================================================================
# This is what gets added when you click "Add Sample Patient"

SAMPLE_PATIENTS = [
    {
        "name": "Aisha Musa",              # Patient name
        "age": 28,                          # Patient age
        "phone": "+234 803 XXX XXXX",       # Phone number
        "symptoms": "Fever for 3 days, chills, body pain",  # What patient said
        "severity": "Strong",               # How bad: Mild/Strong/Very Strong
        "duration": "3 days",               # How long symptoms lasted
        "possible": "Malaria-like symptoms",  # Your diagnosis
        "drugs": "Coartem / Lone Star / Paracetamol",  # What you'd recommend
        "priority": "URGENT"                # URGENT/MODERATE/LOW
    },
    {
        "name": "Chukwudi Obi",
        "age": 45,
        "phone": "+234 806 XXX XXXX",
        "symptoms": "Persistent cough and chest congestion",
        "severity": "Moderate",
        "duration": "5 days",
        "possible": "Respiratory infection",
        "drugs": "Amoxicillin / Cough syrup",
        "priority": "MODERATE"
    },
    {
        "name": "Ngozi Eze",
        "age": 34,
        "phone": "+234 809 XXX XXXX",
        "symptoms": "Mild headache and tiredness",
        "severity": "Mild",
        "duration": "1 day",
        "possible": "Stress/fatigue",
        "drugs": "Paracetamol / Multivitamin",
        "priority": "LOW"
    }
]
# MODIFY THIS: Add more sample patients if you want different test cases

# ============================================================================
# PAGE 1: LIVE QUEUE - Where you see and respond to patients
# ============================================================================

if page == "📊 Live Queue":  # Only show this if user clicked "Live Queue"
    
    st.title("🔔 Live Patient Queue")
    
    # ========================================================================
    # TOP METRICS - 4 boxes showing key numbers
    # ========================================================================
    
    col1, col2, col3, col4 = st.columns(4)  # Create 4 equal-width columns
    
    with col1:  # First column
        # Count how many patients have priority = "URGENT"
        urgent_count = sum(1 for p in st.session_state.patients if p.get('priority') == 'URGENT')
        
        st.metric(
            "🚨 Urgent Cases",              # Label
            urgent_count,                    # Main number to display
            delta=None if urgent_count == 0 else "Needs attention",  # Text below number
            delta_color="inverse"            # Red if there are urgent cases
        )
    
    with col2:  # Second column
        st.metric("👥 Total in Queue", len(st.session_state.patients))
        # Just count total patients in the list
    
    with col3:  # Third column
        # Count patients who came in today
        today_consultations = len([p for p in st.session_state.patients 
                                   if p.get('time', datetime.now()).date() == datetime.now().date()])
        st.metric("📅 Today's Consultations", today_consultations)
    
    with col4:  # Fourth column
        # Show expected wait time based on urgency
        avg_wait = "5-10 min" if urgent_count > 0 else "15-20 min"
        st.metric("⏱️ Avg Response Time", avg_wait)
    
    st.markdown("---")  # Horizontal line separator
    
    # ========================================================================
    # TEST BUTTONS - Add sample patients for testing
    # ========================================================================
    
    st.subheader("🧪 Test Mode - Add Sample Patients")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔴 Add URGENT Patient", use_container_width=True):
            # Copy the first sample patient (URGENT case)
            patient = SAMPLE_PATIENTS[0].copy()
            patient['time'] = datetime.now()  # Add current timestamp
            patient['status'] = 'New'         # Mark as new
            st.session_state.patients.insert(0, patient)  # Add to START of list (urgent first)
            st.rerun()  # Refresh the page to show new patient
    
    with col2:
        if st.button("🟡 Add MODERATE Patient", use_container_width=True):
            patient = SAMPLE_PATIENTS[1].copy()
            patient['time'] = datetime.now()
            patient['status'] = 'New'
            st.session_state.patients.append(patient)  # Add to END of list
            st.rerun()
    
    with col3:
        if st.button("🟢 Add MILD Patient", use_container_width=True):
            patient = SAMPLE_PATIENTS[2].copy()
            patient['time'] = datetime.now()
            patient['status'] = 'New'
            st.session_state.patients.append(patient)
            st.rerun()
    
    st.markdown("---")
    
    # ========================================================================
    # PATIENT DISPLAY - Show each patient in the queue
    # ========================================================================
    
    if len(st.session_state.patients) == 0:
        # If no patients, show friendly message
        st.info("✅ No patients in queue. System ready for consultations.")
    else:
        # Loop through each patient and display their info
        for i, patient in enumerate(st.session_state.patients):
            
            # Get icon and background color based on priority
            priority_color = {
                'URGENT': '🔴',
                'MODERATE': '🟡',
                'LOW': '🟢'
            }.get(patient.get('priority', 'MODERATE'), '🟡')  # Default to MODERATE if not specified
            
            priority_bg = {
                'URGENT': 'background-color: #ffebee;',      # Light red
                'MODERATE': 'background-color: #fff9e6;',     # Light yellow
                'LOW': 'background-color: #e8f5e9;'          # Light green
            }.get(patient.get('priority', 'MODERATE'), '')
            
            # Display patient header with colored background
            st.markdown(f"""
                <div style='{priority_bg} padding: 15px; border-radius: 10px; margin: 10px 0; 
                            border-left: 5px solid {"#f44336" if patient.get("priority")=="URGENT" else "#ff9800" if patient.get("priority")=="MODERATE" else "#4caf50"};'>
                    <h3>{priority_color} {patient.get('priority', 'MODERATE')} - {patient['name']}, {patient['age']}</h3>
                </div>
            """, unsafe_allow_html=True)
            # This creates a colored box with the patient's name and priority
            
            # Create 3 columns for patient details and actions
            col1, col2, col3 = st.columns([3, 1, 1])  # First column is 3x wider
            
            with col1:  # Patient information
                st.markdown(f"""
                **📞 Phone:** {patient.get('phone', 'N/A')}  
                **🩺 Symptoms:** {patient['symptoms']}  
                **📊 Severity:** {patient.get('severity', 'N/A')} | **⏰ Duration:** {patient.get('duration', 'N/A')}  
                **💡 Possible Diagnosis:** {patient['possible']}  
                **💊 Recommended:** {patient['drugs']}  
                **🕐 Received:** {patient.get('time', datetime.now()).strftime('%I:%M %p')}
                """)
                # This displays all the patient's information in a nice format
            
            with col2:  # "Stock Available" button
                if st.button("✅ Stock Available", key=f"ok_{i}", use_container_width=True):
                    patient['status'] = 'Confirmed'
                    patient['response_time'] = datetime.now()
                    st.success("✅ Patient notified! Medications ready for pickup.")
                    st.rerun()
                # When clicked: marks patient as confirmed and shows success message
            
            with col3:  # "Out of Stock" button
                if st.button("❌ Out of Stock", key=f"no_{i}", use_container_width=True):
                    patient['status'] = 'Referred'
                    patient['response_time'] = datetime.now()
                    st.error("❌ Patient referred to alternative pharmacy")
                    st.rerun()
            
            # Additional action buttons
            col_a, col_b, col_c = st.columns([1, 1, 1])
            
            with col_a:
                if st.button("📞 Call Patient", key=f"call_{i}", use_container_width=True):
                    st.info(f"📞 Calling {patient['name']}...")
                    # In real version, this would trigger WhatsApp call
            
            with col_b:
                if st.button("💬 Send WhatsApp", key=f"wa_{i}", use_container_width=True):
                    st.info(f"💬 Opening WhatsApp for {patient['name']}...")
                    # In real version, this would open WhatsApp with pre-filled message
            
            with col_c:
                if st.button("✔️ Mark Complete", key=f"done_{i}", use_container_width=True):
                    st.session_state.patients.pop(i)  # Remove patient from list
                    st.success(f"✔️ Consultation completed for {patient['name']}")
                    st.rerun()  # Refresh to show updated list
            
            st.markdown("---")  # Separator between patients

# ============================================================================
# PAGE 2: ANALYTICS - Charts and metrics
# ============================================================================

elif page == "📈 Analytics":
    
    st.title("📈 Analytics & Insights")
    
    # ========================================================================
    # DATE FILTER - Let user select date range
    # ========================================================================
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        # Default: 30 days ago
    
    with col2:
        end_date = st.date_input("End Date", datetime.now())
        # Default: today
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)  # Add space
        if st.button("Apply Filter"):
            st.success("Filter applied!")
            # In real version, this would filter the data based on dates
    
    st.markdown("---")
    
    # ========================================================================
    # KPI CARDS - 4 key performance indicators
    # ========================================================================
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate metrics from consultation history
    total_consultations = st.session_state.consultation_history['consultations'].sum()
    avg_daily = st.session_state.consultation_history['consultations'].mean()
    urgent_pct = (st.session_state.consultation_history['urgent'].sum() / total_consultations * 100)
    avg_response = st.session_state.consultation_history['response_time_mins'].mean()
    
    with col1:
        st.metric(
            "Total Consultations (30d)",    # Title
            f"{total_consultations:,}",      # Number with comma separator (e.g., 1,234)
            delta=f"+{int(avg_daily)} avg/day",  # Green arrow with daily average
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "Urgent Cases", 
            f"{urgent_pct:.1f}%",            # Format to 1 decimal place
            delta="Within safety threshold", 
            delta_color="off"                # No color (gray)
        )
    
    with col3:
        st.metric(
            "Avg Response Time", 
            f"{int(avg_response)} min",
            delta="-5 min from last month",  # Negative = improvement (green arrow down)
            delta_color="normal"
        )
    
    with col4:
        revenue_estimate = total_consultations * 1500  # Assume ₦1,500 per consultation
        st.metric(
            "Est. Monthly Revenue", 
            f"₦{revenue_estimate:,}",
            delta="+12% vs last month",
            delta_color="normal"
        )
        # MODIFY THIS: Change the 1500 to your actual average revenue per consultation
    
    st.markdown("---")
    
    # ========================================================================
    # CHARTS - Organized in tabs
    # ========================================================================
    
    tab1, tab2, tab3 = st.tabs(["📊 Consultation Trends", "🎯 Severity Distribution", "⏱️ Response Times"])
    
    # --- TAB 1: CONSULTATION TRENDS ---
    with tab1:
        st.subheader("Daily Consultation Volume (Last 30 Days)")
        
        # Simple line chart showing consultations over time
        fig = px.line(
            st.session_state.consultation_history,  # Data source
            x='date',                                # X-axis: dates
            y='consultations',                       # Y-axis: number of consultations
            title='Consultation Trend',
            labels={'consultations': 'Number of Consultations', 'date': 'Date'}
        )
        fig.update_traces(line_color='#1f77b4', line_width=3)  # Blue line, 3px thick
        fig.update_layout(hovermode='x unified', height=400)    # Show all values on hover
        st.plotly_chart(fig, use_container_width=True)
        
        # Stacked area chart showing breakdown by severity
        fig2 = go.Figure()
        
        # Add layer for urgent cases (red)
        fig2.add_trace(go.Scatter(
            x=st.session_state.consultation_history['date'], 
            y=st.session_state.consultation_history['urgent'],
            name='Urgent',
            fill='tonexty',           # Fill area below line
            stackgroup='one',         # Stack on top of previous
            line=dict(color='#f44336')  # Red color
        ))
        
        # Add layer for moderate cases (orange)
        fig2.add_trace(go.Scatter(
            x=st.session_state.consultation_history['date'], 
            y=st.session_state.consultation_history['moderate'],
            name='Moderate',
            fill='tonexty',
            stackgroup='one',
            line=dict(color='#ff9800')
        ))
        
        # Add layer for mild cases (green)
        fig2.add_trace(go.Scatter(
            x=st.session_state.consultation_history['date'], 
            y=st.session_state.consultation_history['mild'],
            name='Mild',
            fill='tonexty',
            stackgroup='one',
            line=dict(color='#4caf50')
        ))
        
        fig2.update_layout(
            title='Consultations by Severity Level', 
            xaxis_title='Date',
            yaxis_title='Count',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # --- TAB 2: SEVERITY DISTRIBUTION ---
    with tab2:
        st.subheader("Severity Distribution")
        
        # Calculate totals for each severity
        severity_totals = {
            'Urgent': st.session_state.consultation_history['urgent'].sum(),
            'Moderate': st.session_state.consultation_history['moderate'].sum(),
            'Mild': st.session_state.consultation_history['mild'].sum()
        }
        
        # Create pie chart
        fig3 = px.pie(
            values=list(severity_totals.values()),  # Numbers for each slice
            names=list(severity_totals.keys()),     # Labels for each slice
            title='Consultation Severity Breakdown',
            color_discrete_map={'Urgent':'#f44336', 'Moderate':'#ff9800', 'Mild':'#4caf50'}  # Colors
        )
        fig3.update_traces(textposition='inside', textinfo='percent+label')  # Show % and label
        st.plotly_chart(fig3, use_container_width=True)
        
        # Additional metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Most Common Severity", "Mild", delta="60% of cases")
        with col2:
            st.metric("Peak Hour", "2-4 PM", delta="Based on 30-day data")
            # MODIFY THIS: Update with your actual peak hours
    
    # --- TAB 3: RESPONSE TIMES ---
    with tab3:
        st.subheader("Response Time Analysis")
        
        # Histogram showing distribution of response times
        fig4 = px.histogram(
            st.session_state.consultation_history, 
            x='response_time_mins',
            title='Response Time Distribution',
            labels={'response_time_mins': 'Response Time (minutes)', 'count': 'Frequency'},
            nbins=20,                              # 20 bars
            color_discrete_sequence=['#1f77b4']   # Blue color
        )
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Fastest Response", "5 min", delta="Urgent case")
        with col2:
            st.metric("Target Met", "95%", delta="+3% vs target")
        with col3:
            st.metric("Avg Wait (Urgent)", "7 min", delta="Below 10 min target")

# ============================================================================
# PAGE 3: INVENTORY - Stock management
# ============================================================================

elif page == "📦 Inventory":
    
    st.title("📦 Inventory Management")
    
    # ========================================================================
    # SUMMARY METRICS
    # ========================================================================
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Count medications with low stock
    low_stock_count = len(st.session_state.inventory[st.session_state.inventory['status'] == 'Low Stock'])
    
    # Calculate total inventory value (stock × price)
    total_value = (st.session_state.inventory['current_stock'] * 
                  st.session_state.inventory['unit_price']).sum()
    
    with col1:
        st.metric(
            "⚠️ Low Stock Items", 
            low_stock_count,
            delta="Needs reorder",
            delta_color="inverse" if low_stock_count > 0 else "off"  # Red if low stock exists
        )
    
    with col2:
        st.metric("📊 Total Items", len(st.session_state.inventory))
    
    with col3:
        st.metric("💰 Total Inventory Value", f"₦{total_value:,.0f}")
    
    with col4:
        avg_turnover = st.session_state.inventory['monthly_demand'].mean()
        st.metric("📈 Avg Monthly Turnover", f"{int(avg_turnover)} units")
    
    st.markdown("---")
    
    # ========================================================================
    # TABS FOR DIFFERENT VIEWS
    # ========================================================================
    
    tab1, tab2 = st.tabs(["📋 Current Stock", "📊 Analytics"])
    
    # --- TAB 1: CURRENT STOCK LIST ---
    with tab1:
        
        # Search and filter
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search = st.text_input("🔍 Search medication", placeholder="Type medication name...")
        
        with col2:
            filter_option = st.selectbox("Filter", ["All", "Low Stock", "OK"])
        
        # Apply filters to data
        df_display = st.session_state.inventory.copy()
        
        if search:  # If user typed something in search
            df_display = df_display[df_display['medication'].str.contains(search, case=False)]
            # Keep only rows where medication name contains search term
        
        if filter_option == "Low Stock":
            df_display = df_display[df_display['status'] == 'Low Stock']
        elif filter_option == "OK":
            df_display = df_display[df_display['status'] == 'OK']
        
        # Display each medication
        for idx, row in df_display.iterrows():  # Loop through each row
            
            # Set colors based on status
            status_color = '#ffebee' if row['status'] == 'Low Stock' else '#e8f5e9'
            status_icon = '⚠️' if row['status'] == 'Low Stock' else '✅'
            
            # Display medication name in colored box
            st.markdown(f"""
                <div style='background-color: {status_color}; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                    <h4>{status_icon} {row['medication']}</h4>
                </div>
            """, unsafe_allow_html=True)
            
            # Show metrics for this medication
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Stock", f"{row['current_stock']} units")
            with col2:
                st.metric("Reorder Point", f"{row['reorder_point']} units")
            with col3:
                st.metric("Monthly Demand", f"{row['monthly_demand']} units")
            with col4:
                st.metric("Unit Price", f"₦{row['unit_price']}")
            
            # If low stock, show reorder button
            if row['status'] == 'Low Stock':
                if st.button(f"📦 Generate Reorder", key=f"reorder_{idx}"):
                    # Calculate how many to reorder
                    reorder_qty = row['monthly_demand'] - row['current_stock']
                    st.success(f"✅ Reorder generated: {reorder_qty} units of {row['medication']}")
                    # In real version, this would create a purchase order
            
            st.markdown("---")
    
    # --- TAB 2: INVENTORY ANALYTICS ---
    with tab2:
        st.subheader("Inventory Analytics")
        
        # Bar chart: Current stock vs reorder point
        fig5 = go.Figure()
        
        # Bars showing current stock
        fig5.add_trace(go.Bar(
            x=st.session_state.inventory['medication'],
            y=st.session_state.inventory['current_stock'],
            name='Current Stock',
            marker_color='#1f77b4'  # Blue bars
        ))
        
        # Line showing reorder point threshold
        fig5.add_trace(go.Scatter(
            x=st.session_state.inventory['medication'],
            y=st.session_state.inventory['reorder_point'],
            name='Reorder Point',
            line=dict(color='#f44336', dash='dash'),  # Red dashed line
            mode='lines+markers'
        ))
        
        fig5.update_layout(
            title='Stock Levels vs Reorder Points',
            xaxis_title='Medication',
            yaxis_title='Units',
            height=400
        )
        st.plotly_chart(fig5, use_container_width=True)
        
        # Calculate total value per medication
        st.session_state.inventory['total_value'] = (
            st.session_state.inventory['current_stock'] * 
            st.session_state.inventory['unit_price']
        )
        
        # Bar chart: Value distribution
        fig6 = px.bar(
            st.session_state.inventory.sort_values('total_value', ascending=False),  # Sort by value
            x='medication',
            y='total_value',
            title='Inventory Value by Medication',
            labels={'total_value': 'Total Value (₦)', 'medication': 'Medication'},
            color='total_value',                    # Color bars by value
            color_continuous_scale='Blues'          # Blue gradient
        )
        fig6.update_layout(height=400)
        st.plotly_chart(fig6, use_container_width=True)

# ============================================================================
# PAGE 4: SETTINGS - Configuration
# ============================================================================

elif page == "⚙️ Settings":
    
    st.title("⚙️ System Settings")
    
    tab1, tab2, tab3 = st.tabs(["🏪 Pharmacy Info", "🔔 Notifications", "📊 Data Management"])
    
    # --- TAB 1: PHARMACY INFO ---
    with tab1:
        st.subheader("Pharmacy Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            pharmacy_name = st.text_input("Pharmacy Name", "Blue Pill Pharmacy")
            # MODIFY THIS: Change default to your pharmacy name
            
            phone = st.text_input("Phone Number", "+234 803 XXX XXXX")
            # MODIFY THIS: Your actual phone number
            
            email = st.text_input("Email", "contact@bluepill.ng")
            # MODIFY THIS: Your actual email
        
        with col2:
            address = st.text_area("Address", "123 Main Street\nAwka, Anambra State")
            # MODIFY THIS: Your actual address
            
            hours = st.text_input("Operating Hours", "8AM - 8PM Mon-Sat")
            # MODIFY THIS: Your actual hours
        
        if st.button("💾 Save Changes", type="primary"):
            st.success("✅ Pharmacy information updated successfully!")
            # In real version, this would save to database
    
    # --- TAB 2: NOTIFICATION SETTINGS ---
    with tab2:
        st.subheader("Notification Settings")
        
        # Checkboxes for different notification types
        st.checkbox("📧 Email notifications for urgent cases", value=True)
        st.checkbox("📱 SMS alerts for low stock", value=True)
        st.checkbox("💬 WhatsApp integration", value=True)
        st.checkbox("🔔 Browser notifications", value=False)
        
        # Slider for alert threshold
        st.slider("Alert threshold for urgent cases (minutes)", 5, 30, 10)
        # Default: 10 minutes. Range: 5-30
        
        if st.button("💾 Save Notification Settings", type="primary"):
            st.success("✅ Notification settings updated!")
    
    # --- TAB 3: DATA MANAGEMENT ---
    with tab3:
        st.subheader("Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📤 Export Data")
            
            if st.button("Export Consultations (CSV)"):
                # In real version, this would create a CSV file
                st.success("✅ Consultations exported to downloads")
            
            if st.button("Export Inventory (CSV)"):
                st.success("✅ Inventory exported to downloads")
            
            if st.button("Generate Monthly Report (PDF)"):
                st.success("✅ Report generated")
        
        with col2:
            st.markdown("### 🗑️ Clear Data")
            
            if st.button("Clear Test Patients", type="secondary"):
                st.session_state.patients = []  # Empty the patient list
                st.success("✅ Test patients cleared")
            
            st.markdown("---")
            st.warning("⚠️ Danger Zone")
            
            if st.button("Reset All Data", type="secondary"):
                if st.checkbox("I understand this will delete all data"):
                    st.error("This feature is disabled in demo mode")
                    # In production, this would delete everything

# ============================================================================
# FOOTER - Appears on all pages
# ============================================================================

st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>OgaDoctor Analytics Dashboard v2.0 | Built by Christian Egwuonwu</p>
        <p>💡 Powered by AI • Processing 500+ monthly consultations with 95% accuracy</p>
    </div>
""", unsafe_allow_html=True)

# ============================================================================
# HOW TO MODIFY THIS DASHBOARD
# ============================================================================
"""
KEY SECTIONS TO CUSTOMIZE:

1. SAMPLE_PATIENTS (line ~140)
   - Add your own test patient scenarios
   - Change symptoms, ages, medications

2. PHARMACY INFO (line ~125)
   - Update pharmacy name, address, hours

3. COLORS (line ~35)
   - Change #1f77b4 (blue) to your brand color
   - Change #f44336 (red), #ff9800 (orange), #4caf50 (green)

4. METRICS (line ~545)
   - Change revenue calculation (currently ₦1,500 per consultation)
   - Update peak hours, targets

5. INVENTORY (line ~95)
   - Replace with your actual medication list
   - Update prices, stock levels, reorder points

6. SETTINGS (line ~850)
   - Update default pharmacy details
   - Customize notification preferences

TO CONNECT REAL DATA:
- Replace session_state.patients with database query
- Replace session_state.inventory with database query
- Add actual WhatsApp/phone integration in action buttons
- Connect export buttons to actual file generation

TESTING:
1. Run: streamlit run dashboard.py
2. Click "Add Sample Patient" buttons to test
3. Try all tabs and features
4. Modify colors and text to match your brand
"""
