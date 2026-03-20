"""
OgaDoctor - Pharmacy Owner Portal
==================================
Pharmacy owners log in to see medication orders, manage inventory, and track earnings.
"""

import streamlit as st
import pandas as pd
import json
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
    try:
        pharmacy_data = supabase.table('pharmacies')\
            .select('*')\
            .eq('id', pharmacy_id)\
            .single()\
            .execute().data
    except Exception as e:
        st.error(f"Error loading pharmacy data: {str(e)}")
        st.stop()
    
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
        
        try:
            today_orders = supabase.table('orders')\
                .select('*')\
                .eq('pharmacy_id', pharmacy_id)\
                .gte('created_at', today.isoformat())\
                .execute().data or []
        except:
            today_orders = []
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Today's Orders", len(today_orders))
        
        with col2:
            completed = len([o for o in today_orders if o.get('order_status') == 'Delivered'])
            st.metric("Completed", completed)
        
        with col3:
            revenue = sum(o.get('pharmacy_payout_amount', 0) for o in today_orders if o.get('order_status') == 'Delivered')
            st.metric("Today's Revenue", f"₦{revenue:,.0f}")
        
        st.markdown("---")
        
        # Pending orders alert
        try:
            pending_orders = supabase.table('orders')\
                .select('*')\
                .eq('pharmacy_id', pharmacy_id)\
                .in_('order_status', ['Pending', 'Confirmed'])\
                .execute().data or []
        except:
            pending_orders = []
        
        if pending_orders:
            st.warning(f"⚠️ You have **{len(pending_orders)}** pending order(s)!")
        else:
            st.info("✅ No pending orders at the moment")
    
    # ========================================================================
    # PAGE 2: PENDING ORDERS
    # ========================================================================
    elif page == "📦 Pending Orders":
        st.title("📦 Pending Medication Orders")
        
        try:
            pending_orders = supabase.table('orders')\
                .select('*')\
                .eq('pharmacy_id', pharmacy_id)\
                .in_('order_status', ['Pending', 'Confirmed', 'Preparing'])\
                .order('created_at', desc=False)\
                .execute().data or []
        except Exception as e:
            st.error(f"Error loading orders: {str(e)}")
            pending_orders = []
        
        if not pending_orders:
            st.success("✅ No pending orders!")
        else:
            st.write(f"**{len(pending_orders)} pending order(s)**")
            
            for order in pending_orders:
                st.markdown(f"""
                <div style='background-color: #fff9e6; padding: 20px; border-radius: 10px; margin: 15px 0;'>
                    <h3>📦 Order #{order['id']}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Customer Phone:** {order.get('customer_phone', 'N/A')}")
                    st.write(f"**Order Total:** ₦{order.get('total_amount', 0):,.2f}")
                    st.write(f"**Your Share (85%):** ₦{order.get('pharmacy_payout_amount', 0):,.2f}")
                    st.write(f"**Delivery Fee:** ₦{order.get('delivery_fee', 0):,.2f}")
                
                with col2:
                    # Parse order items (JSON string)
                    try:
                        items = json.loads(order.get('order_items', '[]'))
                        st.write("**Medications:**")
                        for item in items:
                            st.write(f"- {item.get('name', 'Unknown')}: {item.get('quantity', 0)} x ₦{item.get('unit_price', 0)} = ₦{item.get('total', 0)}")
                    except:
                        st.write(f"**Medications:** {order.get('order_items', 'N/A')}")
                    
                    st.write(f"**Delivery Address:** {order.get('address', 'N/A')}")
                    st.write(f"**Delivery Time:** {order.get('delivery_time', 'N/A')}")
                    st.write(f"**Status:** {order.get('order_status', 'Pending')}")
                
                st.markdown("---")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if order.get('order_status') == 'Pending':
                        if st.button("✅ Accept", key=f"accept_{order['id']}"):
                            try:
                                supabase.table('orders').update({
                                    'order_status': 'Confirmed'
                                }).eq('id', order['id']).execute()
                                st.success("Order accepted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                
                with col2:
                    if order.get('order_status') == 'Confirmed':
                        if st.button("📦 Preparing", key=f"prep_{order['id']}"):
                            try:
                                supabase.table('orders').update({
                                    'order_status': 'Preparing'
                                }).eq('id', order['id']).execute()
                                st.info("Marked as preparing")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                
                with col3:
                    if order.get('order_status') in ['Confirmed', 'Preparing']:
                        if st.button("🚚 Out for Delivery", key=f"dispatch_{order['id']}"):
                            try:
                                supabase.table('orders').update({
                                    'order_status': 'Out for Delivery'
                                }).eq('id', order['id']).execute()
                                st.info("Order dispatched!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                
                # Delivery confirmation
                if order.get('order_status') == 'Out for Delivery':
                    if st.button("✅ Mark as Delivered", key=f"delivered_{order['id']}", type="primary"):
                        try:
                            supabase.table('orders').update({
                                'order_status': 'Delivered',
                                'pharmacy_payout_status': 'pending'
                            }).eq('id', order['id']).execute()
                            st.success("Order completed!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                # Reject option
                if order.get('order_status') == 'Pending':
                    if st.button("❌ Reject (Out of Stock)", key=f"reject_{order['id']}"):
                        try:
                            supabase.table('orders').update({
                                'order_status': 'Cancelled'
                            }).eq('id', order['id']).execute()
                            st.error("Order rejected and will be reassigned")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
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
            .eq('order_status', 'Delivered')\
            .order('created_at', desc=True)
        
        if date_filter == "Today":
            query = query.gte('created_at', datetime.now().date().isoformat())
        elif date_filter == "This Week":
            week_ago = (datetime.now() - timedelta(days=7)).date()
            query = query.gte('created_at', week_ago.isoformat())
        elif date_filter == "This Month":
            month_ago = (datetime.now() - timedelta(days=30)).date()
            query = query.gte('created_at', month_ago.isoformat())
        
        try:
            completed_orders = query.execute().data or []
        except Exception as e:
            st.error(f"Error loading orders: {str(e)}")
            completed_orders = []
        
        st.write(f"**{len(completed_orders)} completed order(s)**")
        
        if completed_orders:
            total_revenue = sum(o.get('pharmacy_payout_amount', 0) for o in completed_orders)
            st.metric("Total Revenue", f"₦{total_revenue:,.2f}")
            
            st.markdown("---")
            
            # Display as table
            df = pd.DataFrame(completed_orders)
            
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            display_cols = ['created_at', 'customer_phone', 'total_amount', 'pharmacy_payout_amount', 'patient_rating']
            display_df = df[[col for col in display_cols if col in df.columns]]
            
            if not display_df.empty:
                display_df.columns = ['Date', 'Customer', 'Order Total', 'Your Share', 'Rating']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No completed orders for this time period")
    
    # ========================================================================
    # PAGE 4: INVENTORY
    # ========================================================================
    elif page == "📋 Inventory":
        st.title("📋 Medication Inventory")
        st.info("Inventory management coming soon!")
        
        st.markdown("---")
        st.subheader("Coming Soon Features:")
        st.write("✅ Add medications to inventory")
        st.write("✅ Update stock levels")
        st.write("✅ Set medication prices")
        st.write("✅ Mark items as out of stock")
        st.write("✅ Receive low stock alerts")
    
    # ========================================================================
    # PAGE 5: EARNINGS
    # ========================================================================
    elif page == "💰 Earnings":
        st.title("💰 My Earnings")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Revenue", f"₦{pharmacy_data.get('total_revenue', 0):,.2f}")
        
        with col2:
            try:
                pending_payouts = supabase.table('orders')\
                    .select('pharmacy_payout_amount')\
                    .eq('pharmacy_id', pharmacy_id)\
                    .eq('order_status', 'Delivered')\
                    .eq('pharmacy_payout_status', 'pending')\
                    .execute().data or []
            except:
                pending_payouts = []
            
            pending = sum(o.get('pharmacy_payout_amount', 0) for o in pending_payouts)
            st.metric("Pending Payout", f"₦{pending:,.2f}")
        
        with col3:
            month_ago = (datetime.now() - timedelta(days=30)).date()
            try:
                month_orders = supabase.table('orders')\
                    .select('pharmacy_payout_amount')\
                    .eq('pharmacy_id', pharmacy_id)\
                    .eq('order_status', 'Delivered')\
                    .gte('created_at', month_ago.isoformat())\
                    .execute().data or []
            except:
                month_orders = []
            
            month_revenue = sum(o.get('pharmacy_payout_amount', 0) for o in month_orders)
            st.metric("This Month", f"₦{month_revenue:,.2f}")
        
        st.markdown("---")
        
        # Recent earnings
        st.subheader("📋 Recent Earnings")
        
        try:
            recent_orders = supabase.table('orders')\
                .select('*')\
                .eq('pharmacy_id', pharmacy_id)\
                .eq('order_status', 'Delivered')\
                .order('created_at', desc=True)\
                .limit(10)\
                .execute().data or []
        except:
            recent_orders = []
        
        if recent_orders:
            for order in recent_orders:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    created = pd.to_datetime(order['created_at']).strftime('%Y-%m-%d %H:%M')
                    st.write(f"**{created}** - {order.get('customer_phone', 'N/A')}")
                with col2:
                    st.write(f"₦{order.get('pharmacy_payout_amount', 0):,.2f}")
                with col3:
                    payout_status = order.get('pharmacy_payout_status', 'pending')
                    if payout_status == 'paid':
                        st.success("✅ Paid")
                    else:
                        st.warning("⏳ Pending")
                st.markdown("---")
        else:
            st.info("No earnings yet. Complete orders to start earning!")
    
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
                value=int(pharmacy_data.get('delivery_fee', 500)),
                step=100
            )
            
            if st.form_submit_button("💾 Update Delivery Settings"):
                try:
                    supabase.table('pharmacies').update({
                        'delivery_available': delivery_available,
                        'delivery_fee': delivery_fee
                    }).eq('id', pharmacy_id).execute()
                    st.success("Settings updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating settings: {str(e)}")
        
        st.markdown("---")
        st.subheader("💳 Bank Details (for Payouts)")
        
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
                    "UBA", "Zenith Bank", "Stanbic IBTC", "Fidelity Bank",
                    "Union Bank", "Sterling Bank", "Wema Bank"
                ])
            
            if st.form_submit_button("💾 Update Bank Details"):
                try:
                    supabase.table('pharmacies').update({
                        'bank_details': {
                            'account_name': account_name,
                            'account_number': account_number,
                            'bank_name': bank_name
                        }
                    }).eq('id', pharmacy_id).execute()
                    st.success("Bank details updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating bank details: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>OgaDoctor Pharmacy Portal v1.0 | © 2026 OgaDoctor Health Services</p>
</div>
""", unsafe_allow_html=True)