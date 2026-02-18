import streamlit as st

st.set_page_config(layout="wide")
st.title("🔔 OgaDoctor - Pharmacy Dashboard")
st.markdown("**Brother's Pharmacy - Live Patients**")

if st.button("💉 TEST FEVER PATIENT", use_container_width=True):
    with st.container(border=True):
        st.error("""
        🔔
