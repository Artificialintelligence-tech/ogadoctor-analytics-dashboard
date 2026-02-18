import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")
st.title("🔔 OgaDoctor - Pharmacy Dashboard")
st.markdown("**Live patient queue for [Brother's Pharmacy]**")

# Patient queue
if 'patients' not in st.session_state:
    st.session_state.patients = []

col1, col2 = st.columns(2)
with col1:
    if st.button("💉 TEST PATIENT (Fever)", use_container_width=True):
        st.session_state.patients.append({
            "name": "Aisha Musa", "age": 28, "time": datetime.now(),
            "symptoms": "Fever 3 days + chills", 
            "possible": "Malaria-like symptoms",
            "drugs": "Coartem/Lone Star", "status": "New"
        })
        st.rerun()

# Show patients
for i, patient in enumerate(st.session_state.patients):
    st.markdown("---")
    st.error(f"🔔 NEW PATIENT: {patient['name']}, {patient['age']}")
    col1, col2, col3 = st.columns([2,1,1])
    
    with col1:
        st.write(f"**Symptoms:** {patient['symptoms']}")
        st.write(f"**Possible:** {patient['possible']}")
        st.write(f"**Likely needs:** {patient['drugs']}")
    
    with col2:
        if st.button("✅ STOCK OK", key=f"ok{i}"):
            patient['status'] = "Confirmed"
            st.success("✅ Patient notified with MAP!")
    
    with col3:
        if st.button("❌ NO STOCK", key=f"no{i}"):
            patient['status'] = "No stock"
            st.error("❌ Patient sent to next pharmacy")
