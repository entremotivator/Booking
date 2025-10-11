"""
Streamlit App: WordPress Amelia Booking API Explorer
-----------------------------------------------------
Usage:
    pip install -r requirements.txt
    streamlit run amelia_booking_app.py

requirements.txt:
    streamlit
    requests
    pandas
"""

import streamlit as st
import requests
import json
import pandas as pd
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Page setup
st.set_page_config(
    page_title="Amelia Booking API Explorer",
    layout="wide",
    page_icon="📅"
)

# -------------------------------------
# Sidebar: WordPress Connection
# -------------------------------------
st.sidebar.title("🔐 Amelia API Connection")

wp_base = st.sidebar.text_input("WordPress Site URL", "https://videmiservices.com").rstrip("/")
amelia_api_key = st.sidebar.text_input("Amelia API Key", type="password", help="Enter your Amelia API key from WordPress admin")

headers = {
    "Accept": "application/json", 
    "Content-Type": "application/json"
}
if amelia_api_key:
    headers["Amelia"] = amelia_api_key

st.sidebar.markdown("---")
st.sidebar.markdown("**Options**")
api_base = st.sidebar.text_input("Amelia API Base Path", "wp-admin/admin-ajax.php?action=wpamelia_api&call=/api/v1")
show_raw_json = st.sidebar.checkbox("Show Raw JSON Responses", value=False)

# API URLs
amelia_url = f"{wp_base}/{api_base}"

st.title("📅 WordPress Amelia Booking API Explorer")
st.caption("Manage appointments, bookings, services, customers, and employees using the Amelia REST API with API Key authentication.")

# -------------------------------------
# Helper functions
# -------------------------------------
def amelia_get(endpoint: str, params: Dict[str, Any] = None, silent_on_error: bool = False) -> Optional[Any]:
    """Fetch JSON from Amelia REST API."""
    # Construct URL: base includes the call parameter, so we append the endpoint
    url = f"{amelia_url}/{endpoint}"
    try:
        res = requests.get(url, headers=headers, params=params, timeout=30)
        res.raise_for_status()
        return res.json()
    except requests.HTTPError as e:
        if not silent_on_error:
            error_msg = f"HTTP {res.status_code}: {e}"
            try:
                error_data = res.json()
                if isinstance(error_data, dict):
                    error_msg += f"\n{error_data.get('message', res.text)}"
            except:
                error_msg += f"\n{res.text}"
            st.error(error_msg)
        return None
    except Exception as e:
        if not silent_on_error:
            st.error(f"Error connecting to {url}: {e}")
        return None

def amelia_post(endpoint: str, data: Dict[str, Any]) -> Optional[Any]:
    """Create a new resource via POST request."""
    # Construct URL: base includes the call parameter, so we append the endpoint
    url = f"{amelia_url}/{endpoint}"
    try:
        res = requests.post(url, headers=headers, json=data, timeout=30)
        res.raise_for_status()
        return res.json()
    except requests.HTTPError as e:
        try:
            error_data = res.json()
            st.error(f"POST failed: {error_data.get('message', str(e))}")
        except:
            st.error(f"POST failed: {e}\n{res.text}")
        return None
    except Exception as e:
        st.error(f"POST failed: {e}")
        return None

def download_json(obj, filename: str, label="Download JSON"):
    """Create a download button for JSON data."""
    b = json.dumps(obj, indent=2).encode("utf-8")
    st.download_button(label=label, data=b, file_name=filename, mime="application/json")

def safe_get(data: dict, key: str, default=""):
    """Safely get a value from a dictionary."""
    val = data.get(key, default)
    return val if val is not None else default

# -------------------------------------
# Tabs
# -------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 Appointments", "📋 Bookings", "🛠️ Services", "👥 Customers", "👔 Employees"])

# -------------------------------------
# TAB 1: APPOINTMENTS
# -------------------------------------
with tab1:
    st.header("📅 Appointments Management")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        # Date range selector
        date_from = st.date_input("From Date", datetime.now())
        date_to = st.date_input("To Date", datetime.now() + timedelta(days=7))
    
    with col2:
        fetch_appointments_btn = st.button("🔄 Fetch Appointments", key="fetch_appointments")
    
    if fetch_appointments_btn:
        with st.spinner("Fetching appointments..."):
            params = {
                "dates": f"{date_from},{date_to}",
                "page": 1,
                "skipServices": 0,
                "skipProviders": 0
            }
            result = amelia_get("appointments", params=params)
            
            if result and result.get("data"):
                st.session_state["appointments"] = result["data"]
                st.success(f"✅ Fetched appointments successfully")
                
                if show_raw_json:
                    with st.expander("Raw JSON Response"):
                        st.json(result)
    
    appointments_data = st.session_state.get("appointments", {})
    
    if appointments_data and "appointments" in appointments_data:
        st.subheader("📊 Appointments Overview")
        
        # Flatten appointments by date
        all_appointments = []
        for date_key, date_data in appointments_data.get("appointments", {}).items():
            if isinstance(date_data, dict) and "appointments" in date_data:
                for apt in date_data["appointments"]:
                    all_appointments.append(apt)
        
        if all_appointments:
            rows = []
            for apt in all_appointments:
                if isinstance(apt, dict):
                    # Get first booking for customer info
                    bookings = apt.get("bookings", [])
                    customer_name = ""
                    customer_email = ""
                    status = ""
                    
                    if bookings and len(bookings) > 0:
                        first_booking = bookings[0]
                        customer = first_booking.get("customer", {})
                        if customer:
                            customer_name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}"
                            customer_email = customer.get("email", "")
                        status = first_booking.get("status", "")
                    
                    rows.append({
                        "ID": apt.get("id"),
                        "Date": apt.get("bookingStart", ""),
                        "Service": apt.get("service", {}).get("name", ""),
                        "Provider": apt.get("provider", {}).get("firstName", "") + " " + apt.get("provider", {}).get("lastName", ""),
                        "Customer": customer_name,
                        "Email": customer_email,
                        "Status": status,
                        "Price": apt.get("price", 0)
                    })
            
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, height=400)
            
            col1, col2 = st.columns(2)
            with col1:
                download_json(all_appointments, "appointments.json", label="⬇️ Download Appointments JSON")
            with col2:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Download Appointments CSV",
                    data=csv,
                    file_name="appointments.csv",
                    mime="text/csv"
                )
    
    # Appointment Management Section
    st.markdown("---")
    st.subheader("🛠️ Appointment Management")
    
    action_tabs = st.tabs(["📋 View", "➕ Create", "✏️ Update", "🗑️ Delete"])
    
    # VIEW TAB
    with action_tabs[0]:
        appointment_id = st.number_input("Enter Appointment ID", min_value=1, key="view_apt_id")
        if st.button("📥 Load Appointment"):
            with st.spinner("Loading appointment..."):
                result = amelia_get(f"appointments/{appointment_id}")
                if result and result.get("data"):
                    st.session_state["current_appointment"] = result["data"]["appointment"]
                    st.success("✅ Appointment loaded successfully")
                    if show_raw_json:
                        st.json(result)
        
        current_apt = st.session_state.get("current_appointment")
        if current_apt:
            st.write("### Appointment Details")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ID", current_apt.get("id"))
                st.metric("Date", current_apt.get("bookingStart", ""))
            with col2:
                st.metric("Service ID", current_apt.get("serviceId", ""))
                st.metric("Provider ID", current_apt.get("providerId", ""))
            with col3:
                st.metric("Location ID", current_apt.get("locationId", ""))
                st.metric("Price", f"${current_apt.get('price', 0)}")
            
            st.write("### Bookings")
            bookings = current_apt.get("bookings", [])
            if bookings:
                for booking in bookings:
                    with st.expander(f"Booking ID: {booking.get('id')} - Status: {booking.get('status')}"):
                        customer = booking.get("customer", {})
                        st.write(f"**Customer:** {customer.get('firstName', '')} {customer.get('lastName', '')}")
                        st.write(f"**Email:** {customer.get('email', '')}")
                        st.write(f"**Phone:** {customer.get('phone', '')}")
                        st.write(f"**Persons:** {booking.get('persons', 1)}")
                        st.write(f"**Price:** ${booking.get('price', 0)}")
    
    # CREATE TAB
    with action_tabs[1]:
        st.write("Create a new appointment")
        with st.form("create_appointment_form"):
            col1, col2 = st.columns(2)
            with col1:
                create_booking_start = st.text_input("Booking Start (YYYY-MM-DD HH:MM)", "2024-12-20 09:00")
                create_service_id = st.number_input("Service ID", min_value=1, value=1)
                create_provider_id = st.number_input("Provider ID", min_value=1, value=1)
            with col2:
                create_location_id = st.number_input("Location ID", min_value=1, value=1)
                create_customer_id = st.number_input("Customer ID", min_value=1, value=1)
                create_notify = st.checkbox("Notify Participants", value=True)
            
            if st.form_submit_button("➕ Create Appointment"):
                payload = {
                    "bookingStart": create_booking_start,
                    "bookings": [
                        {
                            "customerId": create_customer_id,
                            "duration": 1800,
                            "extras": [],
                            "persons": 1,
                            "status": "approved"
                        }
                    ],
                    "internalNotes": "",
                    "locationId": create_location_id,
                    "notifyParticipants": 1 if create_notify else 0,
                    "providerId": create_provider_id,
                    "recurring": [],
                    "serviceId": create_service_id
                }
                
                result = amelia_post("appointments", payload)
                if result:
                    st.success(f"✅ Appointment created successfully! ID: {result.get('data', {}).get('appointment', {}).get('id', 'N/A')}")
                    if show_raw_json:
                        st.json(result)
    
    # UPDATE TAB
    with action_tabs[2]:
        update_apt_id = st.number_input("Appointment ID to Update", min_value=1, key="update_apt_id")
        
        with st.form("update_appointment_form"):
            st.write("Update appointment details (only changed fields)")
            col1, col2 = st.columns(2)
            with col1:
                update_booking_start = st.text_input("New Booking Start (YYYY-MM-DD HH:MM)", "")
                update_provider_id = st.number_input("New Provider ID", min_value=0, value=0)
            with col2:
                update_location_id = st.number_input("New Location ID", min_value=0, value=0)
                update_notes = st.text_area("Internal Notes", "")
            
            if st.form_submit_button("💾 Update Appointment"):
                payload = {}
                if update_booking_start:
                    payload["bookingStart"] = update_booking_start
                if update_provider_id > 0:
                    payload["providerId"] = update_provider_id
                if update_location_id > 0:
                    payload["locationId"] = update_location_id
                if update_notes:
                    payload["internalNotes"] = update_notes
                
                if payload:
                    result = amelia_post(f"appointments/{update_apt_id}", payload)
                    if result:
                        st.success("✅ Appointment updated successfully")
                        if show_raw_json:
                            st.json(result)
                else:
                    st.warning("Please provide at least one field to update")
    
    # DELETE TAB
    with action_tabs[3]:
        delete_apt_id = st.number_input("Appointment ID to Delete", min_value=1, key="delete_apt_id")
        
        if st.button("🗑️ Delete Appointment", type="primary"):
            if st.session_state.get("confirm_delete_apt"):
                result = amelia_post(f"appointments/delete/{delete_apt_id}", {})
                if result:
                    st.success("✅ Appointment deleted successfully")
                    st.session_state.pop("confirm_delete_apt", None)
                    if show_raw_json:
                        st.json(result)
            else:
                st.session_state["confirm_delete_apt"] = True
                st.warning("⚠️ Click Delete again to confirm deletion")

# -------------------------------------
# TAB 2: BOOKINGS
# -------------------------------------
with tab2:
    st.header("📋 Bookings Management")
    
    st.info("💡 Bookings are created through the customer-facing booking flow. Use this section to create bookings on behalf of customers.")
    
    booking_type = st.radio("Booking Type", ["Appointment", "Event", "Package"], horizontal=True)
    
    if booking_type == "Appointment":
        st.subheader("➕ Create Appointment Booking")
        
        with st.form("create_booking_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Appointment Details**")
                booking_start = st.text_input("Booking Start (YYYY-MM-DD HH:MM)", "2024-12-20 09:00")
                service_id = st.number_input("Service ID", min_value=1, value=1)
                provider_id = st.number_input("Provider ID", min_value=1, value=1)
                location_id = st.number_input("Location ID", min_value=1, value=1)
            
            with col2:
                st.write("**Customer Details**")
                customer_first_name = st.text_input("First Name", "John")
                customer_last_name = st.text_input("Last Name", "Doe")
                customer_email = st.text_input("Email", "john.doe@example.com")
                customer_phone = st.text_input("Phone", "")
            
            col1, col2 = st.columns(2)
            with col1:
                persons = st.number_input("Number of Persons", min_value=1, value=1)
                duration = st.number_input("Duration (seconds)", min_value=300, value=1800, step=300)
            with col2:
                payment_gateway = st.selectbox("Payment Gateway", ["onSite", "stripe", "payPal", "mollie", "razorpay"])
                notify_participants = st.checkbox("Notify Participants", value=True)
            
            if st.form_submit_button("➕ Create Booking"):
                payload = {
                    "type": "appointment",
                    "bookings": [
                        {
                            "extras": [],
                            "customFields": {},
                            "deposit": False,
                            "locale": "en_US",
                            "utcOffset": None,
                            "persons": persons,
                            "customerId": None,
                            "customer": {
                                "id": None,
                                "firstName": customer_first_name,
                                "lastName": customer_last_name,
                                "email": customer_email,
                                "phone": customer_phone,
                                "countryPhoneIso": "",
                                "externalId": None
                            },
                            "duration": duration
                        }
                    ],
                    "payment": {
                        "gateway": payment_gateway,
                        "currency": "USD",
                        "data": {}
                    },
                    "recaptcha": None,
                    "locale": "en_US",
                    "timeZone": "UTC",
                    "bookingStart": booking_start,
                    "notifyParticipants": 1 if notify_participants else 0,
                    "locationId": location_id,
                    "providerId": provider_id,
                    "serviceId": service_id,
                    "utcOffset": None,
                    "recurring": [],
                    "package": [],
                    "couponCode": None
                }
                
                result = amelia_post("bookings", payload)
                if result:
                    st.success("✅ Booking created successfully!")
                    if show_raw_json:
                        st.json(result)
    
    elif booking_type == "Event":
        st.subheader("➕ Create Event Booking")
        
        with st.form("create_event_booking_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Event Details**")
                event_id = st.number_input("Event ID", min_value=1, value=1)
                event_persons = st.number_input("Number of Persons", min_value=1, value=1)
            
            with col2:
                st.write("**Customer Details**")
                event_customer_first = st.text_input("First Name", "Jane")
                event_customer_last = st.text_input("Last Name", "Smith")
                event_customer_email = st.text_input("Email", "jane.smith@example.com")
            
            event_payment_gateway = st.selectbox("Payment Gateway", ["onSite", "stripe", "payPal"], key="event_payment")
            event_amount = st.number_input("Payment Amount", min_value=0.0, value=20.0, step=1.0)
            
            if st.form_submit_button("➕ Create Event Booking"):
                payload = {
                    "type": "event",
                    "bookings": [
                        {
                            "customer": {
                                "email": event_customer_email,
                                "externalId": None,
                                "firstName": event_customer_first,
                                "id": None,
                                "lastName": event_customer_last,
                                "phone": "",
                                "countryPhoneIso": ""
                            },
                            "customFields": {},
                            "customerId": 0,
                            "persons": event_persons,
                            "ticketsData": None,
                            "utcOffset": None,
                            "deposit": False
                        }
                    ],
                    "payment": {
                        "amount": str(event_amount),
                        "gateway": event_payment_gateway,
                        "currency": "USD"
                    },
                    "recaptcha": False,
                    "locale": "en_US",
                    "timeZone": "UTC",
                    "couponCode": "",
                    "eventId": event_id
                }
                
                result = amelia_post("bookings", payload)
                if result:
                    st.success("✅ Event booking created successfully!")
                    if show_raw_json:
                        st.json(result)
    
    else:  # Package
        st.subheader("➕ Create Package Booking")
        st.info("Package bookings allow customers to book multiple services together. Configure the package appointments below.")
        
        with st.form("create_package_booking_form"):
            st.write("**Customer Details**")
            col1, col2 = st.columns(2)
            with col1:
                pkg_customer_first = st.text_input("First Name", "Alice")
                pkg_customer_last = st.text_input("Last Name", "Johnson")
            with col2:
                pkg_customer_email = st.text_input("Email", "alice.johnson@example.com")
                pkg_customer_phone = st.text_input("Phone", "")
            
            st.write("**Package Details**")
            package_id = st.number_input("Package ID", min_value=1, value=1)
            pkg_persons = st.number_input("Number of Persons", min_value=1, value=1)
            
            st.write("**Package Appointments** (Add at least one)")
            num_appointments = st.number_input("Number of Appointments in Package", min_value=1, max_value=5, value=2)
            
            package_appointments = []
            for i in range(num_appointments):
                st.write(f"**Appointment {i+1}**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    apt_start = st.text_input(f"Start Time", f"2024-12-{20+i} 10:00", key=f"pkg_start_{i}")
                with col2:
                    apt_service = st.number_input(f"Service ID", min_value=1, value=1, key=f"pkg_service_{i}")
                with col3:
                    apt_provider = st.number_input(f"Provider ID", min_value=1, value=1, key=f"pkg_provider_{i}")
                
                package_appointments.append({
                    "bookingStart": apt_start,
                    "serviceId": apt_service,
                    "providerId": apt_provider,
                    "locationId": 1,
                    "utcOffset": 0,
                    "notifyParticipants": 1
                })
            
            pkg_payment_gateway = st.selectbox("Payment Gateway", ["onSite", "stripe", "payPal"], key="pkg_payment")
            
            if st.form_submit_button("➕ Create Package Booking"):
                payload = {
                    "type": "package",
                    "bookings": [
                        {
                            "customFields": {},
                            "deposit": False,
                            "locale": "en_US",
                            "utcOffset": None,
                            "customerId": None,
                            "customer": {
                                "firstName": pkg_customer_first,
                                "lastName": pkg_customer_last,
                                "email": pkg_customer_email,
                                "phone": pkg_customer_phone,
                                "countryPhoneIso": "",
                                "externalId": None,
                                "translations": None
                            },
                            "persons": pkg_persons
                        }
                    ],
                    "payment": {
                        "gateway": pkg_payment_gateway,
                        "currency": "USD",
                        "data": {}
                    },
                    "locale": "en_US",
                    "timeZone": "UTC",
                    "package": package_appointments,
                    "packageId": package_id,
                    "utcOffset": 0,
                    "couponCode": None
                }
                
                result = amelia_post("bookings", payload)
                if result:
                    st.success("✅ Package booking created successfully!")
                    if show_raw_json:
                        st.json(result)

# -------------------------------------
# TAB 3: SERVICES
# -------------------------------------
with tab3:
    st.header("🛠️ Services Management")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        fetch_services_btn = st.button("🔄 Fetch All Services", key="fetch_services")
    
    if fetch_services_btn:
        with st.spinner("Fetching services..."):
            result = amelia_get("services", params={"page": 1})
            if result and result.get("data"):
                st.session_state["services"] = result["data"]["services"]
                st.success(f"✅ Fetched {len(result['data']['services'])} services")
                if show_raw_json:
                    with st.expander("Raw JSON Response"):
                        st.json(result)
    
    services = st.session_state.get("services", [])
    
    if services:
        st.subheader(f"📊 Services Overview ({len(services)} total)")
        
        rows = []
        for svc in services:
            if isinstance(svc, dict):
                rows.append({
                    "ID": svc.get("id"),
                    "Name": svc.get("name", ""),
                    "Price": f"${svc.get('price', 0)}",
                    "Duration": f"{svc.get('duration', 0) // 60} min",
                    "Capacity": f"{svc.get('minCapacity', 1)}-{svc.get('maxCapacity', 1)}",
                    "Status": svc.get("status", ""),
                    "Category ID": svc.get("categoryId", "")
                })
        
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, height=400)
        
        col1, col2 = st.columns(2)
        with col1:
            download_json(services, "services.json", label="⬇️ Download Services JSON")
        with col2:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Services CSV",
                data=csv,
                file_name="services.csv",
                mime="text/csv"
            )
    
    # Service Management
    st.markdown("---")
    st.subheader("🛠️ Service Management")
    
    service_tabs = st.tabs(["📋 View", "➕ Create", "✏️ Update"])
    
    # VIEW TAB
    with service_tabs[0]:
        service_id = st.number_input("Enter Service ID", min_value=1, key="view_service_id")
        if st.button("📥 Load Service"):
            with st.spinner("Loading service..."):
                result = amelia_get(f"services/{service_id}")
                if result and result.get("data"):
                    st.session_state["current_service"] = result["data"]["service"]
                    st.success("✅ Service loaded successfully")
                    if show_raw_json:
                        st.json(result)
        
        current_svc = st.session_state.get("current_service")
        if current_svc:
            st.write("### Service Details")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ID", current_svc.get("id"))
                st.metric("Name", current_svc.get("name", ""))
            with col2:
                st.metric("Price", f"${current_svc.get('price', 0)}")
                st.metric("Duration", f"{current_svc.get('duration', 0) // 60} min")
            with col3:
                st.metric("Min Capacity", current_svc.get("minCapacity", 1))
                st.metric("Max Capacity", current_svc.get("maxCapacity", 1))
            
            st.write("**Description:**", current_svc.get("description", "No description"))
            st.write("**Status:**", current_svc.get("status", ""))
            st.write("**Category ID:**", current_svc.get("categoryId", ""))
    
    # CREATE TAB
    with service_tabs[1]:
        st.write("Create a new service")
        with st.form("create_service_form"):
            col1, col2 = st.columns(2)
            with col1:
                svc_name = st.text_input("Service Name", "New Service")
                svc_price = st.number_input("Price", min_value=0.0, value=20.0, step=1.0)
                svc_duration = st.number_input("Duration (minutes)", min_value=5, value=30, step=5)
            with col2:
                svc_category = st.number_input("Category ID", min_value=1, value=1)
                svc_min_cap = st.number_input("Min Capacity", min_value=1, value=1)
                svc_max_cap = st.number_input("Max Capacity", min_value=1, value=1)
            
            svc_description = st.text_area("Description", "")
            svc_providers = st.text_input("Provider IDs (comma-separated)", "1")
            
            if st.form_submit_button("➕ Create Service"):
                provider_ids = [int(p.strip()) for p in svc_providers.split(",") if p.strip().isdigit()]
                
                payload = {
                    "categoryId": svc_category,
                    "color": "#1788FB",
                    "description": svc_description,
                    "duration": svc_duration * 60,
                    "providers": provider_ids,
                    "extras": [],
                    "maxCapacity": svc_max_cap,
                    "minCapacity": svc_min_cap,
                    "name": svc_name,
                    "price": svc_price,
                    "status": "visible",
                    "bringingAnyone": True,
                    "show": True,
                    "aggregatedPrice": True
                }
                
                result = amelia_post("services", payload)
                if result:
                    st.success(f"✅ Service created successfully! ID: {result.get('data', {}).get('service', {}).get('id', 'N/A')}")
                    if show_raw_json:
                        st.json(result)
    
    # UPDATE TAB
    with service_tabs[2]:
        update_svc_id = st.number_input("Service ID to Update", min_value=1, key="update_svc_id")
        
        with st.form("update_service_form"):
            st.write("Update service details (only changed fields)")
            col1, col2 = st.columns(2)
            with col1:
                update_svc_name = st.text_input("New Name", "")
                update_svc_price = st.number_input("New Price", min_value=0.0, value=0.0, step=1.0)
            with col2:
                update_svc_duration = st.number_input("New Duration (minutes)", min_value=0, value=0, step=5)
                update_svc_status = st.selectbox("Status", ["", "visible", "hidden", "disabled"])
            
            if st.form_submit_button("💾 Update Service"):
                payload = {}
                if update_svc_name:
                    payload["name"] = update_svc_name
                if update_svc_price > 0:
                    payload["price"] = update_svc_price
                if update_svc_duration > 0:
                    payload["duration"] = update_svc_duration * 60
                if update_svc_status:
                    payload["status"] = update_svc_status
                
                if payload:
                    result = amelia_post(f"services/{update_svc_id}", payload)
                    if result:
                        st.success("✅ Service updated successfully")
                        if show_raw_json:
                            st.json(result)
                else:
                    st.warning("Please provide at least one field to update")

# -------------------------------------
# TAB 4: CUSTOMERS
# -------------------------------------
with tab4:
    st.header("👥 Customers Management")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        search_customer = st.text_input("Search Customers", "")
        fetch_customers_btn = st.button("🔄 Fetch Customers", key="fetch_customers")
    
    if fetch_customers_btn:
        with st.spinner("Fetching customers..."):
            params = {"page": 1}
            if search_customer:
                params["search"] = search_customer
            
            result = amelia_get("users/customers", params=params)
            if result and result.get("data"):
                st.session_state["customers"] = result["data"]["users"]
                st.success(f"✅ Fetched {len(result['data']['users'])} customers")
                if show_raw_json:
                    with st.expander("Raw JSON Response"):
                        st.json(result)
    
    customers = st.session_state.get("customers", [])
    
    if customers:
        st.subheader(f"📊 Customers Overview ({len(customers)} total)")
        
        rows = []
        for cust in customers:
            if isinstance(cust, dict):
                rows.append({
                    "ID": cust.get("id"),
                    "First Name": cust.get("firstName", ""),
                    "Last Name": cust.get("lastName", ""),
                    "Email": cust.get("email", ""),
                    "Phone": cust.get("phone", ""),
                    "Status": cust.get("status", ""),
                    "Total Appointments": cust.get("totalAppointments", 0)
                })
        
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, height=400)
        
        col1, col2 = st.columns(2)
        with col1:
            download_json(customers, "customers.json", label="⬇️ Download Customers JSON")
        with col2:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Customers CSV",
                data=csv,
                file_name="customers.csv",
                mime="text/csv"
            )
    
    # Customer Management
    st.markdown("---")
    st.subheader("🛠️ Customer Management")
    
    customer_tabs = st.tabs(["📋 View", "➕ Create", "✏️ Update", "🗑️ Delete"])
    
    # VIEW TAB
    with customer_tabs[0]:
        customer_id = st.number_input("Enter Customer ID", min_value=1, key="view_customer_id")
        if st.button("📥 Load Customer"):
            with st.spinner("Loading customer..."):
                result = amelia_get(f"users/customers/{customer_id}")
                if result and result.get("data"):
                    st.session_state["current_customer"] = result["data"]["user"]
                    st.success("✅ Customer loaded successfully")
                    if show_raw_json:
                        st.json(result)
        
        current_cust = st.session_state.get("current_customer")
        if current_cust:
            st.write("### Customer Details")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ID", current_cust.get("id"))
                st.write(f"**Name:** {current_cust.get('firstName', '')} {current_cust.get('lastName', '')}")
            with col2:
                st.write(f"**Email:** {current_cust.get('email', '')}")
                st.write(f"**Phone:** {current_cust.get('phone', '')}")
            with col3:
                st.write(f"**Status:** {current_cust.get('status', '')}")
                st.write(f"**Gender:** {current_cust.get('gender', 'N/A')}")
            
            st.write(f"**Birthday:** {current_cust.get('birthday', 'N/A')}")
            st.write(f"**Note:** {current_cust.get('note', 'No notes')}")
    
    # CREATE TAB
    with customer_tabs[1]:
        st.write("Create a new customer")
        with st.form("create_customer_form"):
            col1, col2 = st.columns(2)
            with col1:
                cust_first = st.text_input("First Name", "John")
                cust_last = st.text_input("Last Name", "Doe")
                cust_email = st.text_input("Email", "john.doe@example.com")
            with col2:
                cust_phone = st.text_input("Phone", "+1234567890")
                cust_gender = st.selectbox("Gender", ["", "male", "female"])
                cust_birthday = st.text_input("Birthday (YYYY-MM-DD)", "")
            
            cust_note = st.text_area("Note", "")
            
            if st.form_submit_button("➕ Create Customer"):
                payload = {
                    "firstName": cust_first,
                    "lastName": cust_last,
                    "email": cust_email,
                    "phone": cust_phone,
                    "gender": cust_gender,
                    "note": cust_note
                }
                
                if cust_birthday:
                    payload["birthday"] = cust_birthday
                
                result = amelia_post("users/customers", payload)
                if result:
                    st.success(f"✅ Customer created successfully! ID: {result.get('data', {}).get('user', {}).get('id', 'N/A')}")
                    if show_raw_json:
                        st.json(result)
    
    # UPDATE TAB
    with customer_tabs[2]:
        update_cust_id = st.number_input("Customer ID to Update", min_value=1, key="update_cust_id")
        
        with st.form("update_customer_form"):
            st.write("Update customer details")
            col1, col2 = st.columns(2)
            with col1:
                update_cust_first = st.text_input("First Name", "")
                update_cust_last = st.text_input("Last Name", "")
            with col2:
                update_cust_phone = st.text_input("Phone", "")
                update_cust_note = st.text_area("Note", "")
            
            if st.form_submit_button("💾 Update Customer"):
                payload = {}
                if update_cust_first:
                    payload["firstName"] = update_cust_first
                if update_cust_last:
                    payload["lastName"] = update_cust_last
                if update_cust_phone:
                    payload["phone"] = update_cust_phone
                if update_cust_note:
                    payload["note"] = update_cust_note
                
                if payload:
                    result = amelia_post(f"users/customers/{update_cust_id}", payload)
                    if result:
                        st.success("✅ Customer updated successfully")
                        if show_raw_json:
                            st.json(result)
                else:
                    st.warning("Please provide at least one field to update")
    
    # DELETE TAB
    with customer_tabs[3]:
        delete_cust_id = st.number_input("Customer ID to Delete", min_value=1, key="delete_cust_id")
        
        if st.button("🗑️ Delete Customer", type="primary"):
            if st.session_state.get("confirm_delete_cust"):
                result = amelia_post(f"users/customers/delete/{delete_cust_id}", {})
                if result:
                    st.success("✅ Customer deleted successfully")
                    st.session_state.pop("confirm_delete_cust", None)
                    if show_raw_json:
                        st.json(result)
            else:
                st.session_state["confirm_delete_cust"] = True
                st.warning("⚠️ Click Delete again to confirm deletion")

# -------------------------------------
# TAB 5: EMPLOYEES
# -------------------------------------
with tab5:
    st.header("👔 Employees (Providers) Management")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        search_employee = st.text_input("Search Employees", "")
        fetch_employees_btn = st.button("🔄 Fetch Employees", key="fetch_employees")
    
    if fetch_employees_btn:
        with st.spinner("Fetching employees..."):
            params = {"page": 1}
            if search_employee:
                params["search"] = search_employee
            
            result = amelia_get("users/providers", params=params)
            if result and result.get("data"):
                st.session_state["employees"] = result["data"]["users"]
                st.success(f"✅ Fetched {len(result['data']['users'])} employees")
                if show_raw_json:
                    with st.expander("Raw JSON Response"):
                        st.json(result)
    
    employees = st.session_state.get("employees", [])
    
    if employees:
        st.subheader(f"📊 Employees Overview ({len(employees)} total)")
        
        rows = []
        for emp in employees:
            if isinstance(emp, dict):
                rows.append({
                    "ID": emp.get("id"),
                    "First Name": emp.get("firstName", ""),
                    "Last Name": emp.get("lastName", ""),
                    "Email": emp.get("email", ""),
                    "Phone": emp.get("phone", ""),
                    "Status": emp.get("status", ""),
                    "Location ID": emp.get("locationId", "")
                })
        
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, height=400)
        
        col1, col2 = st.columns(2)
        with col1:
            download_json(employees, "employees.json", label="⬇️ Download Employees JSON")
        with col2:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Employees CSV",
                data=csv,
                file_name="employees.csv",
                mime="text/csv"
            )
    
    # Employee Management
    st.markdown("---")
    st.subheader("🛠️ Employee Management")
    
    employee_tabs = st.tabs(["📋 View", "➕ Create", "✏️ Update"])
    
    # VIEW TAB
    with employee_tabs[0]:
        employee_id = st.number_input("Enter Employee ID", min_value=1, key="view_employee_id")
        if st.button("📥 Load Employee"):
            with st.spinner("Loading employee..."):
                result = amelia_get(f"users/providers/{employee_id}")
                if result and result.get("data"):
                    st.session_state["current_employee"] = result["data"]["user"]
                    st.success("✅ Employee loaded successfully")
                    if show_raw_json:
                        st.json(result)
        
        current_emp = st.session_state.get("current_employee")
        if current_emp:
            st.write("### Employee Details")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ID", current_emp.get("id"))
                st.write(f"**Name:** {current_emp.get('firstName', '')} {current_emp.get('lastName', '')}")
            with col2:
                st.write(f"**Email:** {current_emp.get('email', '')}")
                st.write(f"**Phone:** {current_emp.get('phone', '')}")
            with col3:
                st.write(f"**Status:** {current_emp.get('status', '')}")
                st.write(f"**Location ID:** {current_emp.get('locationId', 'N/A')}")
            
            st.write(f"**Note:** {current_emp.get('note', 'No notes')}")
            
            # Show services
            service_list = current_emp.get("serviceList", [])
            if service_list:
                st.write("### Assigned Services")
                for svc in service_list:
                    st.write(f"- Service ID: {svc.get('id')} | Price: ${svc.get('price', 0)} | Capacity: {svc.get('minCapacity', 1)}-{svc.get('maxCapacity', 1)}")
    
    # CREATE TAB
    with employee_tabs[1]:
        st.write("Create a new employee")
        st.info("💡 Creating employees requires work hours configuration. This is a simplified form.")
        
        with st.form("create_employee_form"):
            col1, col2 = st.columns(2)
            with col1:
                emp_first = st.text_input("First Name", "Jane")
                emp_last = st.text_input("Last Name", "Smith")
                emp_email = st.text_input("Email", "jane.smith@example.com")
            with col2:
                emp_phone = st.text_input("Phone", "+1234567890")
                emp_location = st.number_input("Location ID", min_value=1, value=1)
                emp_status = st.selectbox("Status", ["visible", "hidden"])
            
            emp_services = st.text_input("Service IDs (comma-separated)", "1")
            
            if st.form_submit_button("➕ Create Employee"):
                service_ids = [int(s.strip()) for s in emp_services.split(",") if s.strip().isdigit()]
                
                # Build service list
                service_list = []
                for svc_id in service_ids:
                    service_list.append({
                        "id": svc_id,
                        "price": 0,
                        "minCapacity": 1,
                        "maxCapacity": 1
                    })
                
                # Build basic work hours (Mon-Fri 9-5)
                week_day_list = []
                for day_idx in range(1, 6):  # Monday to Friday
                    week_day_list.append({
                        "dayIndex": day_idx,
                        "startTime": "09:00:00",
                        "endTime": "17:00:00",
                        "timeOutList": [],
                        "periodList": [
                            {
                                "startTime": "09:00:00",
                                "endTime": "17:00:00",
                                "locationId": None,
                                "periodLocationList": [],
                                "periodServiceList": []
                            }
                        ]
                    })
                
                payload = {
                    "status": emp_status,
                    "firstName": emp_first,
                    "lastName": emp_last,
                    "email": emp_email,
                    "phone": emp_phone,
                    "locationId": emp_location,
                    "serviceList": service_list,
                    "weekDayList": week_day_list
                }
                
                result = amelia_post("users/providers", payload)
                if result:
                    st.success(f"✅ Employee created successfully! ID: {result.get('data', {}).get('user', {}).get('id', 'N/A')}")
                    if show_raw_json:
                        st.json(result)
    
    # UPDATE TAB
    with employee_tabs[2]:
        update_emp_id = st.number_input("Employee ID to Update", min_value=1, key="update_emp_id")
        
        with st.form("update_employee_form"):
            st.write("Update employee details")
            col1, col2 = st.columns(2)
            with col1:
                update_emp_first = st.text_input("First Name", "")
                update_emp_last = st.text_input("Last Name", "")
            with col2:
                update_emp_phone = st.text_input("Phone", "")
                update_emp_note = st.text_area("Note", "")
            
            if st.form_submit_button("💾 Update Employee"):
                payload = {}
                if update_emp_first:
                    payload["firstName"] = update_emp_first
                if update_emp_last:
                    payload["lastName"] = update_emp_last
                if update_emp_phone:
                    payload["phone"] = update_emp_phone
                if update_emp_note:
                    payload["note"] = update_emp_note
                
                if payload:
                    result = amelia_post(f"users/providers/{update_emp_id}", payload)
                    if result:
                        st.success("✅ Employee updated successfully")
                        if show_raw_json:
                            st.json(result)
                else:
                    st.warning("Please provide at least one field to update")

# -------------------------------------
# Footer
# -------------------------------------
st.markdown("---")
st.caption("🚀 Developed for WordPress Amelia Booking API exploration — supports appointments, bookings, services, customers, and employees. Handles API Key authentication safely.")
