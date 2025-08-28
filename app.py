import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import random

# Initialize Firebase app only once
# Use a secret manager for your key file in a real-world app
# Streamlit provides a secure way to handle this on the cloud.
if not firebase_admin._apps:
    cred = credentials.Certificate('firestore-key.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.set_page_config(page_title="Blood Donation Dashboard", layout="wide")

st.sidebar.title("🩸 Blood Donation Dashboard")
selected_page = st.sidebar.radio("Navigation", ["Dashboard", "Donor Registration"])

# --- Helper Functions for Data Retrieval ---

def get_realtime_data(collection_name):
    """Fetches all documents from a Firestore collection."""
    docs = db.collection(collection_name).stream()
    data = [doc.to_dict() for doc in docs]
    return data

# --- Page 1: Dashboard ---
if selected_page == "Dashboard":
    st.header("Real-Time Blood Stock & Analytics")

    # Fetching data for the dashboard
    donors_data = get_realtime_data('donors')
    hospitals_data = get_realtime_data('hospitals')

    col1, col2, col3 = st.columns(3)

    # Metric 1: Total Donors
    with col1:
        total_donors = len(donors_data)
        st.metric(label="Total Registered Donors", value=total_donors)

    # Metric 2: Total Hospitals
    with col2:
        total_hospitals = len(hospitals_data)
        st.metric(label="Hospitals on Platform", value=total_hospitals)

    # Metric 3: Total Blood Units (Example)
    with col3:
        # This would be a sum from your hospital inventory data
        total_units = sum(h['inventory']['A+'] for h in hospitals_data if 'inventory' in h)
        st.metric(label="Total A+ Blood Units", value=total_units)

    st.subheader("Hospital Inventory Status")
    
    # Converting hospital data to a DataFrame for display
    hospitals_df = pd.DataFrame(hospitals_data)
    if not hospitals_df.empty:
        st.dataframe(hospitals_df[['name', 'location', 'inventory']])

    # --- Geo-Location Map Visualization ---
    st.subheader("Map of Hospitals and Donors")

    # For the map, we need latitude and longitude.
    # We'll use dummy data for this example.
    map_data = []
    if not hospitals_df.empty:
        for index, row in hospitals_df.iterrows():
            map_data.append({
                'lat': row['lat'],  # Assuming you have lat/lon in your data
                'lon': row['lon'],
                'type': 'Hospital'
            })

    donors_df = pd.DataFrame(donors_data)
    if not donors_df.empty:
        for index, row in donors_df.iterrows():
            map_data.append({
                'lat': row['lat'],
                'lon': row['lon'],
                'type': 'Donor'
            })
    
    map_df = pd.DataFrame(map_data)

    if not map_df.empty:
        # Create a new column to control colors based on type
        map_df['color'] = map_df['type'].apply(lambda x: [255, 0, 0, 160] if x == 'Hospital' else [0, 255, 0, 160])
        
        st.map(map_df, latitude='lat', longitude='lon', color='color', size=50)
    else:
        st.warning("No location data available to display on the map.")

# --- Page 2: Donor Registration ---
elif selected_page == "Donor Registration":
    st.header("Register as a Blood Donor")
    st.write("Join our community to help save lives!")

    with st.form("donor_registration_form"):
        name = st.text_input("Name")
        blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        contact = st.text_input("Contact Number")
        location = st.text_input("City/Location")
        
        # We need a way to get lat/lon. For a real app, you would use a geocoding API.
        # Here, we'll use a placeholder.
        lat = random.uniform(8.0, 13.0)  # Example range for Tamil Nadu
        lon = random.uniform(77.0, 80.0)

        submitted = st.form_submit_button("Register")

        if submitted:
            if name and blood_group and contact and location:
                try:
                    donor_ref = db.collection('donors').document()
                    donor_ref.set({
                        'name': name,
                        'blood_group': blood_group,
                        'contact': contact,
                        'location': location,
                        'lat': lat,
                        'lon': lon,
                        'timestamp': firestore.SERVER_TIMESTAMP
                    })
                    st.success("🎉 You are now a registered donor!")
                    st.balloons()
                except Exception as e:
                    st.error(f"An error occurred: {e}")
            else:
                st.error("Please fill out all the fields.")
