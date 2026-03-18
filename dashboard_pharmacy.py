"""
OgaDoctor - Pharmacy Owner Portal
==================================
Pharmacy owners log in to see medication orders, manage inventory, and track earnings.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="OgaDoctor - Pharmacy Portal",
    page_icon="🏪",
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
    st.title("🏪 OgaDoctor - Pharmacy Portal")
    st.markdown("### Login to access your pharmacy dashboard")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        phone = st.text_input("Phone Number", placeholder="+234XXXXXXXXX")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", type="primary", use_container_width=True):
            try:
                pharmacy = supabase.table('pharmacies')\
                    .select('*')\
                    .eq('phone_number', phone)\
                    .execute().data
                
                if pharmacy and len(pharmacy) > 0:
                    # MVP: password = last 4 digits
                    expected_password = phone[-4:]
                    
                    if password == expected_password:
                        st.session_state.logged_in = True
                        st.session_state.pharmacy_id = pharmacy[0]['id']
                        st.session_state.pharmacy_data = pharmacy[0]
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid password")
                else:
                    st.error("Pharmacy not found")
            except Exception as e:
                st.error(f"Login error: {str(e)}")
        
        st.info("**First time?** Password = last 4 digits of your phone number")

else:
    # ========================================================================
    # LOGGED IN
    # ========================================================================
    
    pharmacy_id = st.session_state.pharmacy_id
    
    # Get fresh pharmacy data
    pharmacy_data = supabase.table('pharmacies')\
        .select('*')\
        .eq('id', pharmacy_id)\
        .single()\
        .execute().data
    
    # ========================================================================
    # SIDEBAR
    # ========================================================================
    st.sidebar.title(f"🏪 {pharmacy_data['pharmacy_name']}")
    st.sidebar.markdown(f"**{pharmacy_data.get('city', '')}, {pharmacy_data.get('state', '')}**")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
    
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio("Navigation", [
        "📊 Dashboard",
        "📦 Pending Orders",
        "✅ Completed Orders",
        "📋 Inventory",
        "💰 Earnings",
        "⚙️ Settings"
    ])
    
    # Quick stats
    st.sidebar.metric("Total Orders", pharmacy_data.get('total_orders_fulfilled', 0))
    st.sidebar.metric("Revenue", f"₦{pharmacy_data.get('total_revenue', 0):,.0f}")
    
    # ========================================================================
    # PAGE 1: DASHBOARD
    # ========================================================================
    if page == "📊 Dashboard":
        st.title("📊 Pharmacy Dashboard")
        st.markdown(f"Welcome, **{pharmacy_data['pharmacy_name']}**!")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Orders", pharmacy_data.get('total_orders_fulfilled', 0))
        
        with col2:
            st.metric("Total Revenue", f"₦{pharmacy_data.get('total_revenue', 0):,.0f}")
        
        with col3:
            st.metric("Rating", f"{pharmacy_data.get('rating', 0):.1f} ⭐")
        
        with col4:
            commission = pharmacy_data.get('commission_rate', 0.15)
            st.metric("Platform Fee", f"{commission*100:.0f}%")
        
        st.markdown("---")
        
        # Today's activity
        st.subheader("📅 Today's Activity")
        
        today = datetime.now().date()
        
        today_orders = supabase.table('orders')\
            .select('*')\
            .eq('pharmacy_id', pharmacy_id)\
            .gte('created_at', today.isoformat())\
            .execute().data
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Today's Orders", len(today_orders))
        
        with col2:
            completed = len([o for o in today_orders if o.get('status') == 'delivered'])
            st.metric("Completed", completed)
        
        with col3:
            revenue = sum(o.get('pharmacy_payout_amount', 0) for o in today_orders if o.get('status') == 'delivered')
            st.metric("Today's Revenue", f"₦{revenue:,.0f}")
        
        st.markdown("---")
        
        # Pending orders alert
        pending_orders = supabase.table('orders')\
            .select('*')\
            .eq('pharmacy_id', pharmacy_id)\
            .eq('status', 'pending')\
            .execute().data
        
        if pending_orders:
            st.warning(f"⚠️ You have **{len(pending_orders)}** pending order(s)!")
    
    # ========================================================================
    # PAGE 2: PENDING ORDERS
    # ========================================================================
    elif page == "📦 Pending Orders":
        st.title("📦 Pending Medication Orders")
        
        pending_orders = supabase.table('orders')\
            .select('*')\
            .eq('pharmacy_id', pharmacy_id)\
            .in_('status', ['pending', 'accepted', 'preparing'])\
            .order('created_at', desc=False)\
            .execute().data
        
        if not pending_orders:
            st.success("✅ No pending orders!")
        else:
            st.write(f"**{len(pending_orders)} pending order(s)**")
            
            for order in pending_orders:
                st.markdown(f"""
                <div style='background-color: #fff9e6; padding: 20px; border-radius: 10px; margin: 15px 0;'>
                    <h3>📦 Order #{order['id'][:8]}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Patient:** {order.get('patient_name', 'N/A')}")
                    st.write(f"**Phone:** {order.get('patient_phone', 'N/A')}")
                    st.write(f"**Order Total:** ₦{order.get('total_amount', 0):,.0f}")
                    st.write(f"**Your Share (85%):** ₦{order.get('pharmacy_payout_amount', 0):,.0f}")
                
                with col2:
                    st.write(f"**Medications:** {order.get('medications', 'N/A')}")
                    st.write(f"**Delivery Address:** {order.get('delivery_address', 'N/A')}")
                    st.write(f"**Status:** {order.get('status', 'pending').upper()}")
                
                st.markdown("---")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if order.get('status') == 'pending':
                        if st.button("✅ Accept", key=f"accept_{order['id']}"):
                            supabase.table('orders').update({
                                'status': 'accepted',
                                'accepted_at': datetime.now().isoformat()
                            }).eq('id', order['id']).execute()
                            st.success("Order accepted!")
                            st.rerun()
                
                with col2:
                    if order.get('status') == 'accepted':
                        if st.button("📦 Preparing", key=f"prep_{order['id']}"):
                            supabase.table('orders').update({
                                'status': 'preparing'
                            }).eq('id', order['id']).execute()
                            st.info("Marked as preparing")
                            st.rerun()
                
                with col3:
                    if order.get('status') in ['accepted', 'preparing']:
                        if st.button("🚚 Dispatched", key=f"dispatch_{order['id']}"):
                            supabase.table('orders').update({
                                'status': 'out_for_delivery',
                                'dispatched_at': datetime.now().isoformat()
                            }).eq('id', order['id']).execute()
                            st.info("Order dispatched!")
                            st.rerun()
                
                # Delivery confirmation
                if order.get('status') == 'out_for_delivery':
                    if st.button("✅ Delivered", key=f"delivered_{order['id']}", type="primary"):
                        supabase.table('orders').update({
                            'status': 'delivered',
                            'delivered_at': datetime.now().isoformat(),
                            'pharmacy_payout_status': 'pending'
                        }).eq('id', order['id']).execute()
                        st.success("Order completed!")
                        st.rerun()
                
                # Reject option
                if order.get('status') == 'pending':
                    if st.button("❌ Reject (Out of Stock)", key=f"reject_{order['id']}"):
                        supabase.table('orders').update({
                            'status': 'cancelled',
                            'cancellation_reason': 'out_of_stock'
                        }).eq('id', order['id']).execute()
                        st.error("Order rejected")
                        st.rerun()
                
                st.markdown("---")
    
    # ========================================================================
    # PAGE 3: COMPLETED ORDERS
    # ========================================================================
    elif page == "✅ Completed Orders":
        st.title("✅ Completed Orders")
        
        date_filter = st.selectbox("Time Period", [
            "Today", "This Week", "This Month", "All Time"
        ])
        
        query = supabase.table('orders')\
            .select('*')\
            .eq('pharmacy_id', pharmacy_id)\
            .eq('status', 'delivered')\
            .order('delivered_at', desc=True)
        
        if date_filter == "Today":
            query = query.gte('delivered_at', datetime.now().date().isoformat())
        elif date_filter == "This Week":
            week_ago = (datetime.now() - timedelta(days=7)).date()
            query = query.gte('delivered_at', week_ago.isoformat())
        elif date_filter == "This Month":
            month_ago = (datetime.now() - timedelta(days=30)).date()
            query = query.gte('delivered_at', month_ago.isoformat())
        
        completed_orders = query.execute().data
        
        st.write(f"**{len(completed_orders)} completed order(s)**")
        
        if completed_orders:
            total_revenue = sum(o.get('pharmacy_payout_amount', 0) for o in completed_orders)
            st.metric("Total Revenue", f"₦{total_revenue:,.0f}")
            
            st.markdown("---")
            
            # Display as table
            df = pd.DataFrame(completed_orders)
            
            if 'delivered_at' in df.columns:
                df['delivered_at'] = pd.to_datetime(df['delivered_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            display_cols = ['delivered_at', 'patient_name', 'total_amount', 'pharmacy_payout_amount']
            display_df = df[[col for col in display_cols if col in df.columns]]
            
            if not display_df.empty:
                display_df.columns = ['Delivered', 'Patient', 'Order Total', 'Your Share']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # ========================================================================
    # PAGE 4: INVENTORY
    # ========================================================================
    elif page == "📋 Inventory":
        st.title("📋 Medication Inventory")
        st.info("Inventory management coming soon!")
    
    # ========================================================================
    # PAGE 5: EARNINGS
    # ========================================================================
    elif page == "💰 Earnings":
        st.title("💰 My Earnings")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Revenue", f"₦{pharmacy_data.get('total_revenue', 0):,.0f}")
        
        with col2:
            pending_orders = supabase.table('orders')\
                .select('pharmacy_payout_amount')\
                .eq('pharmacy_id', pharmacy_id)\
                .eq('status', 'delivered')\
                .eq('pharmacy_payout_status', 'pending')\
                .execute().data
            
            pending = sum(o.get('pharmacy_payout_amount', 0) for o in pending_orders)
            st.metric("Pending Payout", f"₦{pending:,.0f}")
        
        with col3:
            month_ago = (datetime.now() - timedelta(days=30)).date()
            month_orders = supabase.table('orders')\
                .select('pharmacy_payout_amount')\
                .eq('pharmacy_id', pharmacy_id)\
                .eq('status', 'delivered')\
                .gte('delivered_at', month_ago.isoformat())\
                .execute().data
            
            month_revenue = sum(o.get('pharmacy_payout_amount', 0) for o in month_orders)
            st.metric("This Month", f"₦{month_revenue:,.0f}")
    
    # ========================================================================
    # PAGE 6: SETTINGS
    # ========================================================================
    elif page == "⚙️ Settings":
        st.title("⚙️ Settings")
        
        st.subheader("🏪 Pharmacy Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {pharmacy_data['pharmacy_name']}")
            st.write(f"**Phone:** {pharmacy_data['phone_number']}")
            st.write(f"**City:** {pharmacy_data.get('city', 'N/A')}")
        
        with col2:
            st.write(f"**State:** {pharmacy_data.get('state', 'N/A')}")
            st.write(f"**PCN Reg:** {pharmacy_data.get('pcn_registration_number', 'N/A')}")
            st.write(f"**Status:** {pharmacy_data.get('status', 'active')}")
        
        st.write(f"**Address:** {pharmacy_data.get('address', 'N/A')}")
        
        st.markdown("---")
        st.subheader("🚚 Delivery Settings")
        
        with st.form("delivery_form"):
            delivery_available = st.checkbox(
                "Delivery Available",
                value=pharmacy_data.get('delivery_available', True)
            )
            
            delivery_fee = st.number_input(
                "Delivery Fee (₦)",
                min_value=0,
                max_value=2000,
                value=pharmacy_data.get('delivery_fee', 500),
                step=100
            )
            
            if st.form_submit_button("💾 Update"):
                supabase.table('pharmacies').update({
                    'delivery_available': delivery_available,
                    'delivery_fee': delivery_fee
                }).eq('id', pharmacy_id).execute()
                st.success("Settings updated!")
                st.rerun()
        
        st.markdown("---")
        st.subheader("💳 Bank Details")
        
        bank_details = pharmacy_data.get('bank_details', {})
        
        with st.form("bank_form"):
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
                bank_name = st.selectbox("Bank", [
                    "Select Bank", "GTBank", "Access Bank", "First Bank", 
                    "UBA", "Zenith Bank", "Stanbic IBTC"
                ])
            
            if st.form_submit_button("💾 Update"):
                supabase.table('pharmacies').update({
                    'bank_details': {
                        'account_name': account_name,
                        'account_number': account_number,
                        'bank_name': bank_name
                    }
                }).eq('id', pharmacy_id).execute()
                st.success("Bank details updated!")
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>OgaDoctor Pharmacy Portal v1.0 | © 2026 OgaDoctor</p>
</div>
""", unsafe_allow_html=True)