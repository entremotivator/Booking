import streamlit as st
import requests

st.title("Amelia API Test")

API_URL = "https://videmiservices.com/wp-admin/admin-ajax.php?action=wpamelia_api&call=/api/v1/settings"
api_key = st.text_input("API Key", type="password")

if st.button("Test API"):
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else "",
        "Content-Type": "application/json",
        "User-Agent": "StreamlitApp"
    }
    try:
        response = requests.post(API_URL, headers=headers, json={})
        if response.status_code == 200:
            st.success("✅ API connection successful!")
            st.json(response.json())
        else:
            st.error(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"⚠️ Request failed: {e}")
