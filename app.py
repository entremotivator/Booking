import streamlit as st
import requests
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="Amelia API - Appointments Manager",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Amelia API - Appointments Manager")

# Sidebar for API Configuration
st.sidebar.header("⚙️ API Configuration")
st.sidebar.markdown("Configure your Amelia API connection below:")

amelia_url = st.sidebar.text_input(
    "Amelia Site URL",
    value="https://your-site.com",
    help="Enter your WordPress site URL (e.g., https://example.com) - without trailing slash"
)

# Remove trailing slash if present
amelia_url = amelia_url.rstrip('/')

amelia_api_key = st.sidebar.text_input(
    "Amelia API Key",
    type="password",
    help="Enter your Amelia API key from the Elite license"
)

# Advanced options
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 Advanced Options")

use_custom_headers = st.sidebar.checkbox("Use Custom Headers", value=True)
if use_custom_headers:
    user_agent = st.sidebar.text_input(
        "User-Agent",
        value="AmeliaAPIClient/1.0",
        help="Custom User-Agent header"
    )
    add_content_type = st.sidebar.checkbox("Add Content-Type header", value=True)
else:
    user_agent = None
    add_content_type = False

# Boolean parameter format
bool_format = st.sidebar.selectbox(
    "Boolean Parameter Format",
    ["lowercase (true/false)", "Python (True/False)", "integer (1/0)"],
    help="Format for boolean parameters in GET requests"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 API Information")
st.sidebar.info(
    "**Base Path:**\n"
    f"`{amelia_url}/wp-admin/admin-ajax.php?action=wpamelia_api&call=/api/v1`\n\n"
    "**Authentication:**\n"
    "Header: `Amelia: <your-api-key>`"
)

# Helper function to build API URL
def build_api_url(endpoint):
    """Build the full API URL for a given endpoint"""
    base_path = f"{amelia_url}/wp-admin/admin-ajax.php?action=wpamelia_api&call=/api/v1"
    return f"{base_path}{endpoint}"

# Helper function to convert boolean parameters
def convert_bool_param(value):
    """Convert boolean to appropriate format based on settings"""
    if not isinstance(value, bool):
        return value
    
    if bool_format == "lowercase (true/false)":
        return "true" if value else "false"
    elif bool_format == "integer (1/0)":
        return 1 if value else 0
    else:  # Python (True/False)
        return value

# Helper function to prepare headers
def prepare_headers():
    """Prepare request headers with proper configuration"""
    if not amelia_api_key:
        return None
    
    headers = {
        "Amelia": amelia_api_key
    }
    
    if use_custom_headers:
        if user_agent:
            headers["User-Agent"] = user_agent
        if add_content_type:
            headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
    
    return headers

# Helper function to make API requests
def make_api_request(method, endpoint, data=None, params=None):
    """Make an API request to Amelia"""
    if not amelia_api_key:
        st.warning("⚠️ Please enter your Amelia API Key in the sidebar.")
        return None
    
    url = build_api_url(endpoint)
    headers = prepare_headers()
    
    if headers is None:
        return None
    
    # Convert boolean parameters if present
    if params:
        params = {k: convert_bool_param(v) for k, v in params.items()}
    
    # Debug information
    with st.expander("🔍 Debug Information"):
        st.write("**Request URL:**", url)
        st.write("**Headers:**", {k: v if k != "Amelia" else "***HIDDEN***" for k, v in headers.items()})
        st.write("**Params:**", params)
        st.write("**Data:**", data)
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None
        
        # Show response details
        with st.expander("📡 Response Details"):
            st.write("**Status Code:**", response.status_code)
            st.write("**Response Headers:**", dict(response.headers))
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ HTTP Error: {e}")
        if hasattr(e.response, 'text'):
            with st.expander("⚠️ Error Response Details"):
                st.code(e.response.text, language="html")
                st.write("**Possible Solutions:**")
                st.markdown("""
                1. **Verify API Key**: Ensure your API key is correct and not expired
                2. **Check License**: API endpoints require Elite license
                3. **WordPress Permissions**: Check if your WordPress user has proper permissions
                4. **Server Configuration**: Contact your hosting provider about mod_security or firewall rules
                5. **URL Format**: Ensure the site URL is correct (no trailing slash)
                6. **Try Different Headers**: Toggle the "Use Custom Headers" option
                """)
        return None
    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. The server took too long to respond.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Request Error: {e}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON Decode Error: {e}")
        st.info("The server returned a non-JSON response. This might indicate a server-side error.")
        return None

# Main content tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 View Appointments",
    "➕ Add Appointment",
    "✏️ Update Status",
    "🔍 Get Single Appointment",
    "🗑️ Delete Appointment"
])

# Tab 1: View Appointments
with tab1:
    st.header("📋 View All Appointments")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now())
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    col3, col4, col5 = st.columns(3)
    with col3:
        skip_services = st.checkbox("Skip Services", value=False)
    with col4:
        skip_providers = st.checkbox("Skip Providers", value=False)
    with col5:
        as_array = st.checkbox("Return as Array", value=True)
    
    if st.button("🔄 Fetch Appointments", key="fetch_appointments"):
        params = {
            "dates": f"{start_date.strftime('%Y-%m-%d')}:{end_date.strftime('%Y-%m-%d')}",
            "skipServices": skip_services,
            "skipProviders": skip_providers,
            "asArray": as_array
        }
        
        with st.spinner("Fetching appointments..."):
            appointments = make_api_request("GET", "/appointments", params=params)
        
        if appointments:
            st.success("✅ Appointments fetched successfully!")
            st.session_state.appointments = appointments
            st.json(appointments)
        else:
            st.warning("No appointments found or error occurred.")

# Tab 2: Add Appointment
with tab2:
    st.header("➕ Add New Appointment")
    
    with st.form("add_appointment_form"):
        st.subheader("Appointment Details")
        
        col1, col2 = st.columns(2)
        with col1:
            booking_date = st.date_input("Booking Date", datetime.now())
            booking_time = st.time_input("Booking Time", datetime.now().time())
        with col2:
            customer_id = st.number_input("Customer ID", min_value=1, value=1)
            persons = st.number_input("Number of Persons", min_value=1, value=1)
        
        col3, col4, col5 = st.columns(3)
        with col3:
            service_id = st.number_input("Service ID", min_value=1, value=1)
        with col4:
            provider_id = st.number_input("Provider ID", min_value=1, value=1)
        with col5:
            location_id = st.number_input("Location ID", min_value=1, value=1)
        
        notify_participants = st.checkbox("Notify Participants", value=True)
        internal_notes = st.text_area("Internal Notes (Optional)")
        
        submitted = st.form_submit_button("✅ Create Appointment")
        
        if submitted:
            booking_start = f"{booking_date.strftime('%Y-%m-%d')} {booking_time.strftime('%H:%M')}"
            
            data = {
                "bookingStart": booking_start,
                "bookings": [{
                    "customerId": int(customer_id),
                    "persons": int(persons)
                }],
                "serviceId": int(service_id),
                "providerId": int(provider_id),
                "locationId": int(location_id),
                "notifyParticipants": notify_participants
            }
            
            if internal_notes:
                data["internalNotes"] = internal_notes
            
            with st.spinner("Creating appointment..."):
                result = make_api_request("POST", "/appointments", data=data)
            
            if result:
                st.success("✅ Appointment created successfully!")
                st.json(result)

# Tab 3: Update Appointment Status
with tab3:
    st.header("✏️ Update Appointment Status")
    
    with st.form("update_status_form"):
        appointment_id = st.number_input("Appointment ID", min_value=1, value=1)
        new_status = st.selectbox(
            "New Status",
            ["approved", "pending", "canceled", "rejected", "no-show"]
        )
        package_customer_id = st.number_input(
            "Package Customer ID (Optional, 0 if not applicable)",
            min_value=0,
            value=0
        )
        
        update_submitted = st.form_submit_button("🔄 Update Status")
        
        if update_submitted:
            data = {"status": new_status}
            if package_customer_id > 0:
                data["packageCustomerId"] = int(package_customer_id)
            
            with st.spinner("Updating appointment status..."):
                result = make_api_request(
                    "POST",
                    f"/appointments/status/{int(appointment_id)}",
                    data=data
                )
            
            if result:
                st.success("✅ Appointment status updated successfully!")
                st.json(result)

# Tab 4: Get Single Appointment
with tab4:
    st.header("🔍 Get Single Appointment")
    
    with st.form("get_appointment_form"):
        appointment_id_get = st.number_input("Appointment ID", min_value=1, value=1, key="get_appt_id")
        get_submitted = st.form_submit_button("🔍 Fetch Appointment")
        
        if get_submitted:
            with st.spinner("Fetching appointment..."):
                result = make_api_request("GET", f"/appointments/{int(appointment_id_get)}")
            
            if result:
                st.success("✅ Appointment fetched successfully!")
                st.json(result)

# Tab 5: Delete Appointment
with tab5:
    st.header("🗑️ Delete Appointment")
    
    st.warning("⚠️ This action cannot be undone!")
    
    with st.form("delete_appointment_form"):
        appointment_id_delete = st.number_input("Appointment ID", min_value=1, value=1, key="delete_appt_id")
        confirm_delete = st.checkbox("I confirm I want to delete this appointment")
        delete_submitted = st.form_submit_button("🗑️ Delete Appointment")
        
        if delete_submitted:
            if not confirm_delete:
                st.error("❌ Please confirm deletion by checking the checkbox.")
            else:
                with st.spinner("Deleting appointment..."):
                    result = make_api_request(
                        "POST",
                        f"/appointments/delete/{int(appointment_id_delete)}"
                    )
                
                if result:
                    st.success("✅ Appointment deleted successfully!")
                    st.json(result)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Resources")
st.sidebar.markdown(
    "[Amelia API Documentation](https://wpamelia.com/amelia-api-appointments/)"
)
st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit | Amelia API Integration")

