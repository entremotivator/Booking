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

# Input API Key (required with default value)
api_key = st.sidebar.text_input("API Key", value="n3B2dUCRbkE372m6jRXPwGHI9JGVLJ1f2xHVySWgK4VY", type="password")
st.sidebar.markdown(
    "You must generate an API Key in Amelia → Settings → API to access endpoints."
)

# --- Helper Function for API requests ---
def amelia_api_call(endpoint: str, payload: dict = None):
    """
    Makes API calls to Amelia through WordPress admin-ajax.php
    """
    # Remove leading slash if present
    endpoint = endpoint.lstrip('/')
    
    # Construct the full URL with proper parameters
    url = f"{API_BASE_URL}?action=wpamelia_api&call=/api/v1/{endpoint}"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "StreamlitApp"
    }
    
    # Add Authorization header if API key is provided
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        # Use GET for listing endpoints, POST for creating/updating
        if payload is None:
            response = requests.get(url, headers=headers, timeout=30)
        else:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Check response status
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("❌ Unauthorized: Invalid API key")
            return None
        elif response.status_code == 403:
            st.error("❌ Forbidden: Check API permissions in Amelia settings")
            return None
        elif response.status_code == 404:
            st.error(f"❌ Endpoint not found: {endpoint}")
            return None
        else:
            st.error(f"❌ Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("⚠️ Request timed out. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Connection failed. Check your internet connection and API URL.")
        return None
    except Exception as e:
        st.error(f"⚠️ Request failed: {str(e)}")
        return None

# --- Main Content ---
st.subheader("Test API Connection / List Data")

# Create columns for better layout
col1, col2 = st.columns(2)

with col1:
    if st.button("📋 List Services", use_container_width=True):
        if not api_key:
            st.warning("Please enter an API key in the sidebar!")
        else:
            with st.spinner("Fetching services..."):
                result = amelia_api_call("services")
                if result:
                    st.success("✅ Services fetched successfully!")
                    st.json(result)
    
    if st.button("👥 List Employees", use_container_width=True):
        if not api_key:
            st.warning("Please enter an API key in the sidebar!")
        else:
            with st.spinner("Fetching employees..."):
                result = amelia_api_call("users/providers")
                if result:
                    st.success("✅ Employees fetched successfully!")
                    st.json(result)

with col2:
    if st.button("📅 List Appointments", use_container_width=True):
        if not api_key:
            st.warning("Please enter an API key in the sidebar!")
        else:
            with st.spinner("Fetching appointments..."):
                result = amelia_api_call("appointments")
                if result:
                    st.success("✅ Appointments fetched successfully!")
                    st.json(result)
    
    if st.button("⚙️ Test Connection (Settings)", use_container_width=True):
        if not api_key:
            st.warning("Please enter an API key in the sidebar!")
        else:
            with st.spinner("Testing connection..."):
                result = amelia_api_call("settings")
                if result:
                    st.success("✅ Connection successful!")
                    st.json(result)

# --- Additional Endpoints ---
st.markdown("---")
st.subheader("Additional Endpoints")

col3, col4 = st.columns(2)

with col3:
    if st.button("📍 List Locations", use_container_width=True):
        if not api_key:
            st.warning("Please enter an API key in the sidebar!")
        else:
            with st.spinner("Fetching locations..."):
                result = amelia_api_call("locations")
                if result:
                    st.success("✅ Locations fetched successfully!")
                    st.json(result)

with col4:
    if st.button("🏷️ List Categories", use_container_width=True):
        if not api_key:
            st.warning("Please enter an API key in the sidebar!")
        else:
            with st.spinner("Fetching categories..."):
                result = amelia_api_call("categories")
                if result:
                    st.success("✅ Categories fetched successfully!")
                    st.json(result)

# --- Debug Info ---
with st.expander("🔧 Debug Information"):
    st.write("**API Configuration:**")
    st.write(f"- Base URL: `{API_BASE_URL}`")
    st.write(f"- API Key provided: `{'Yes' if api_key else 'No'}`")
    st.write(f"- Example full URL: `{API_BASE_URL}?action=wpamelia_api&call=/api/v1/services`")

# --- Footer ---
st.markdown("---")
st.caption("Made with ❤️ using Streamlit and Amelia API")
