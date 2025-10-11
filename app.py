import streamlit as st
import requests

# --- App Config ---
st.set_page_config(page_title="Amelia API Streamlit", layout="wide")
st.title("🎯 Amelia API Streamlit Demo")

# --- Sidebar ---
st.sidebar.header("API Configuration")
API_BASE_URL = "https://videmiservices.com/wp-admin/admin-ajax.php?action=wpamelia_api&call=/api/v1"
st.sidebar.write("**Base URL:**")
st.sidebar.code(API_BASE_URL)

# Input API Key (required)
api_key = st.sidebar.text_input("API Key", type="password")
st.sidebar.markdown(
    "You must generate an API Key in Amelia → Settings → API to access endpoints."
)

# --- Helper Function for POST requests ---
def amelia_api_call(endpoint: str, payload: dict = {}):
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else "",
        "Content-Type": "application/json",
        "User-Agent": "StreamlitApp"
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"⚠️ Request failed: {e}")
        return None

# --- Main Content ---
st.subheader("Test API Connection / List Data")

# Buttons for different API calls
if st.button("Test Connection (Settings)"):
    if not api_key:
        st.warning("Please enter an API key in the sidebar!")
    else:
        result = amelia_api_call("settings")
        if result:
            st.success("✅ Connection successful!")
            st.json(result)

if st.button("List Services"):
    if not api_key:
        st.warning("Please enter an API key in the sidebar!")
    else:
        result = amelia_api_call("services")
        if result:
            st.success("✅ Services fetched successfully!")
            st.json(result)

if st.button("List Employees"):
    if not api_key:
        st.warning("Please enter an API key in the sidebar!")
    else:
        result = amelia_api_call("employees")
        if result:
            st.success("✅ Employees fetched successfully!")
            st.json(result)

if st.button("List Appointments"):
    if not api_key:
        st.warning("Please enter an API key in the sidebar!")
    else:
        result = amelia_api_call("appointments")
        if result:
            st.success("✅ Appointments fetched successfully!")
            st.json(result)

# --- Footer ---
st.markdown("---")
st.caption("Made with ❤️ using Streamlit and Amelia API")
