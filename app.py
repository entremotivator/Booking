import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

# -----------------------------
# Load Secrets
# -----------------------------
API_BASE_URL = st.secrets["amelia"]["api_base_url"]
WP_USER = st.secrets["amelia"]["wp_username"]
WP_PASS = st.secrets["amelia"]["wp_password"]

# Use only WordPress authentication (not API key)
HEADERS = {
    "Content-Type": "application/json"
}

AUTH = HTTPBasicAuth(WP_USER, WP_PASS)

# -----------------------------
# Helper Functions
# -----------------------------
def get_services():
    url = f"{API_BASE_URL}/services"
    st.write(f"🔍 Connecting to: {url}")
    response = requests.get(url, headers=HEADERS, auth=AUTH)
    st.write(f"📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        st.error(f"Error loading services: {response.status_code}")
        st.error(f"Response: {response.text}")
        return []

def get_employees():
    url = f"{API_BASE_URL}/employees"
    response = requests.get(url, headers=HEADERS, auth=AUTH)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        st.error(f"Error loading employees: {response.status_code} — {response.text}")
        return []

def get_available_slots(service_id, employee_id, date):
    url = f"{API_BASE_URL}/bookings/slots"
    payload = {
        "serviceId": service_id,
        "providerId": employee_id,
        "date": date.strftime("%Y-%m-%d")
    }
    response = requests.post(url, json=payload, headers=HEADERS, auth=AUTH)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        st.warning(f"No available slots found. Status: {response.status_code}")
        return []

def create_booking(service_id, employee_id, customer_name, customer_email, date, time):
    url = f"{API_BASE_URL}/bookings"
    payload = {
        "serviceId": service_id,
        "providerId": employee_id,
        "bookingStart": f"{date} {time}",
        "customer": {
            "firstName": customer_name,
            "email": customer_email
        }
    }
    response = requests.post(url, json=payload, headers=HEADERS, auth=AUTH)
    if response.status_code == 200:
        return True, response.json()
    else:
        return False, response.text

def get_customer_bookings(customer_email):
    url = f"{API_BASE_URL}/customers/bookings?email={customer_email}"
    response = requests.get(url, headers=HEADERS, auth=AUTH)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        st.warning(f"No bookings found. Status: {response.status_code}")
        return []

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Amelia Booking Admin", layout="centered")

st.title("💼 Amelia Booking App")
st.write("Book services using Amelia API with WordPress Admin authentication.")

# Configuration info
with st.expander("ℹ️ Setup Requirements"):
    st.info("""
    **Your API Base URL should be:**
    `https://yoursite.com/wp-json/amelia/v1`
    
    **WordPress Password:**
    Must be an Application Password (generated in WordPress Admin → Users → Profile)
    
    **Format:** `xxxx xxxx xxxx xxxx xxxx xxxx` (with spaces)
    """)

menu = st.sidebar.selectbox("Menu", ["Book Appointment", "My Bookings", "About"])

if menu == "Book Appointment":
    st.subheader("📅 Schedule a Booking")

    services = get_services()
    if services:
        service_options = {s['name']: s['id'] for s in services}
        selected_service_name = st.selectbox("Select a Service", list(service_options.keys()))
        selected_service_id = service_options[selected_service_name]

        employees = get_employees()
        employee_options = {e['firstName'] + " " + e['lastName']: e['id'] for e in employees}
        selected_employee_name = st.selectbox("Select an Employee", list(employee_options.keys()))
        selected_employee_id = employee_options[selected_employee_name]

        booking_date = st.date_input("Select a Date", datetime.now())

        if st.button("Check Available Slots"):
            slots = get_available_slots(selected_service_id, selected_employee_id, booking_date)
            if slots:
                slot_times = [slot["time"] for slot in slots]
                selected_time = st.selectbox("Select a Time Slot", slot_times)
                with st.form("booking_form"):
                    customer_name = st.text_input("Your Name")
                    customer_email = st.text_input("Your Email")
                    confirm = st.form_submit_button("Confirm Booking")
                    if confirm:
                        success, result = create_booking(
                            selected_service_id, selected_employee_id, customer_name, customer_email,
                            booking_date.strftime("%Y-%m-%d"), selected_time
                        )
                        if success:
                            st.success("✅ Booking confirmed successfully!")
                        else:
                            st.error(f"Error creating booking: {result}")
            else:
                st.warning("No slots available for that date.")

elif menu == "My Bookings":
    st.subheader("📋 View Your Bookings")
    customer_email = st.text_input("Enter your booking email")
    if st.button("View My Bookings"):
        bookings = get_customer_bookings(customer_email)
        if bookings:
            for booking in bookings:
                st.write(f"**Service:** {booking['service']['name']}")
                st.write(f"**Date:** {booking['bookingStart']}")
                st.write(f"**Employee:** {booking['provider']['firstName']} {booking['provider']['lastName']}")
                st.divider()
        else:
            st.info("No bookings found for that email.")

elif menu == "About":
    st.info("""
    This app connects to Amelia Booking API with **WordPress Admin authentication** 
    to securely retrieve and manage bookings.
    
    **Troubleshooting 403 Errors:**
    1. Ensure API Base URL is: `https://yoursite.com/wp-json/amelia/v1`
    2. Use WordPress Application Password (not regular password)
    3. Verify WordPress REST API is enabled
    4. Check that Amelia plugin API access is enabled
    5. Confirm user has admin privileges
    """)
