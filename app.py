import streamlit as st
import requests

# --- App Title ---
st.set_page_config(page_title="Amelia API Demo", layout="centered")
st.title("🎯 Amelia API Streamlit Demo")

# --- Sidebar ---
st.sidebar.header("API Configuration")
API_BASE_URL = "https://videmiservices.com/wp-admin/admin-ajax.php?action=wpamelia_api&call=/api/v1"
st.sidebar.write("**Base URL:**")
st.sidebar.code(API_BASE_URL)

# Optional: API key input
api_key = st.sidebar.text_input("API Key (if required)", type="password")

# --- Main Content ---
st.subheader("Test API Connection")

if st.button("Test Connection"):
    try:
        # Example: Test endpoint (you can replace with actual endpoint)
        endpoint = f"{API_BASE_URL}/settings"
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        response = requests.get(endpoint, headers=headers)

        if response.status_code == 200:
            st.success("✅ Connection successful!")
            st.json(response.json())
        else:
            st.error(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"⚠️ Connection failed: {e}")

# --- Footer ---
st.markdown("---")
st.caption("Made with ❤️ using Streamlit and Amelia API")
