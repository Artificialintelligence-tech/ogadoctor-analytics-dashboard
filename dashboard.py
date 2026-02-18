import streamlit as st
import time

st.set_page_config(page_title="OgaDoctor Dashboard", layout="wide")

st.title("🔔 OgaDoctor - New Patients")
st.markdown("---")

if 'patients' not in st.session_state:
    st.session_state.patients = []

# Test patient button
if st.button("💉 ADD TEST PATIENT", type="primary"):
    new_patient = {
        "name": "Aisha Ibrahim",
        "age": 28,
        "distance": "15min walk",
        "symptoms": "Fever 3 days, chills, headache",
        "possible": "Malaria-like symptoms",
        "drugs": "Coartem/Lone Star",
        "status": "New"
    }
    st.session_state.patients.append(new_patient)
    st.rerun()

# Patient queue
for i, patient in enumerate(st.session_state.patients):
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.error(f"🔔 {patient['name']}, {patient['age']}")
            st.write(f"**Distance:** {patient['distance']}")
            st.write(f"**Symptoms:** {patient['symptoms']}")
            st.write(f"**Possible:** {patient['possible']}")
        with col2:
            if st.button("✅ STOCK OK", key=f"ok_{i}"):
                patient['status'] = "Confirmed"
                st.success("Patient notified!")
        with col3:
            if st.button("❌ NO STOCK", key=f"no_{i}"):
                patient['status'] = "No stock"
                st.error("Patient re-routed")
