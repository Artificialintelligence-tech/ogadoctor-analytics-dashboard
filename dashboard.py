import streamlit as st

st.set_page_config(layout="wide")
st.title("🔔 OgaDoctor - Pharmacy Dashboard")
st.markdown("**Brother's Pharmacy - Live Patients**")

if st.button("💉 TEST FEVER PATIENT", use_container_width=True):
    with st.container(border=True):
        st.error("""
        🔔 Aisha Musa, 28 • 15min away
        🔥 Fever 3 days + chills + headache
        🦠 Malaria-like symptoms
        💊 Likely: Coartem/Lone Star
        📍 [MAP LINK]
        """)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ STOCK OK"): 
                st.success("✅ Aisha notified: 'Pharmacy ready!'")
        with col2:
            if st.button("❌ NO STOCK"):
                st.error("❌ Aisha re-routed")

st.info("💡 Demo ready! Show brother tomorrow")
