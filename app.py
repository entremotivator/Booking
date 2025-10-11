"""
Amelia API Management Tool
A comprehensive Streamlit application for managing Amelia booking system via API.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from api_client import AmeliaAPIClient
from csv_handler import CSVHandler

# Page configuration
st.set_page_config(
    page_title="Amelia API Manager",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'api_client' not in st.session_state:
    st.session_state.api_client = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False


def init_api_client():
    """Initialize API client from secrets"""
    try:
        api_base = st.secrets["amelia"]["api_base_url"]
        api_key = st.secrets["amelia"]["api_key"]
        
        client = AmeliaAPIClient(api_base, api_key)
        
        # Test connection
        if client.test_connection():
            st.session_state.api_client = client
            st.session_state.authenticated = True
            return True
        else:
            st.error("Failed to connect to Amelia API. Please check your credentials.")
            return False
    except Exception as e:
        st.error(f"Error initializing API client: {str(e)}")
        st.info("Please configure your API credentials in .streamlit/secrets.toml")
        return False


def show_appointments_page():
    """Display appointments management page"""
    st.header("📅 Appointments Management")
    
    # Action tabs
    tab1, tab2, tab3, tab4 = st.tabs(["View Appointments", "Create Appointment", "Export CSV", "Import CSV"])
    
    with tab1:
        st.subheader("All Appointments")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            date_from = st.date_input("From Date", datetime.now() - timedelta(days=30))
        with col2:
            date_to = st.date_input("To Date", datetime.now() + timedelta(days=30))
        with col3:
            status_filter = st.selectbox("Status", ["All", "approved", "pending", "canceled", "rejected"])
        
        if st.button("Load Appointments", type="primary"):
            with st.spinner("Loading appointments..."):
                params = {}
                if status_filter != "All":
                    params['status'] = status_filter
                
                result = st.session_state.api_client.get_appointments(params)
                
                if 'error' in result:
                    st.error(f"Error: {result['error']}")
                elif 'data' in result and 'appointments' in result['data']:
                    appointments = result['data']['appointments']
                    
                    if appointments:
                        # Convert to DataFrame for display
                        df = CSVHandler.export_appointments_to_csv(result)
                        st.success(f"Loaded {len(appointments)} appointments")
                        st.dataframe(df, use_container_width=True)
                        
                        # Store in session state for export
                        st.session_state.appointments_data = result
                    else:
                        st.info("No appointments found")
                else:
                    st.warning("Unexpected response format")
    
    with tab2:
        st.subheader("Create New Appointment")
        
        with st.form("create_appointment_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                booking_date = st.date_input("Booking Date")
                booking_time = st.time_input("Booking Time")
                service_id = st.number_input("Service ID", min_value=1, step=1)
                provider_id = st.number_input("Provider/Employee ID", min_value=1, step=1)
                customer_id = st.number_input("Customer ID", min_value=1, step=1)
            
            with col2:
                location_id = st.number_input("Location ID (optional)", min_value=0, step=1)
                persons = st.number_input("Number of Persons", min_value=1, value=1, step=1)
                duration = st.number_input("Duration (seconds, optional)", min_value=0, step=300)
                status = st.selectbox("Status", ["approved", "pending"])
                notify = st.checkbox("Notify Participants", value=True)
            
            internal_notes = st.text_area("Internal Notes")
            
            submitted = st.form_submit_button("Create Appointment", type="primary")
            
            if submitted:
                # Combine date and time
                booking_datetime = datetime.combine(booking_date, booking_time)
                booking_start = booking_datetime.strftime("%Y-%m-%d %H:%M")
                
                appointment_data = {
                    'bookingStart': booking_start,
                    'serviceId': int(service_id),
                    'providerId': int(provider_id),
                    'locationId': int(location_id) if location_id > 0 else None,
                    'notifyParticipants': 1 if notify else 0,
                    'internalNotes': internal_notes,
                    'bookings': [
                        {
                            'customerId': int(customer_id),
                            'persons': int(persons),
                            'status': status,
                            'extras': []
                        }
                    ]
                }
                
                if duration > 0:
                    appointment_data['bookings'][0]['duration'] = int(duration)
                
                with st.spinner("Creating appointment..."):
                    result = st.session_state.api_client.create_appointment(appointment_data)
                    
                    if 'error' in result:
                        st.error(f"Error: {result['error']}")
                    elif 'data' in result and 'appointment' in result['data']:
                        st.success("Appointment created successfully!")
                        st.json(result['data']['appointment'])
                    else:
                        st.warning("Unexpected response")
                        st.json(result)
    
    with tab3:
        st.subheader("Export Appointments to CSV")
        
        st.write("Export appointments data to CSV file for analysis or backup.")
        
        col1, col2 = st.columns(2)
        with col1:
            export_date_from = st.date_input("From Date", datetime.now() - timedelta(days=30), key="export_from")
        with col2:
            export_date_to = st.date_input("To Date", datetime.now() + timedelta(days=30), key="export_to")
        
        export_status = st.selectbox("Status Filter", ["All", "approved", "pending", "canceled", "rejected"], key="export_status")
        
        if st.button("Generate CSV Export", type="primary"):
            with st.spinner("Fetching appointments..."):
                params = {}
                if export_status != "All":
                    params['status'] = export_status
                
                result = st.session_state.api_client.get_appointments(params)
                
                if 'error' in result:
                    st.error(f"Error: {result['error']}")
                elif 'data' in result and 'appointments' in result['data']:
                    df = CSVHandler.export_appointments_to_csv(result)
                    
                    if not df.empty:
                        st.success(f"Ready to export {len(df)} appointment records")
                        
                        # Preview
                        st.write("Preview:")
                        st.dataframe(df.head(10), use_container_width=True)
                        
                        # Download button
                        csv_data = CSVHandler.dataframe_to_csv_download(df)
                        filename = f"amelia_appointments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv",
                            type="primary"
                        )
                    else:
                        st.info("No appointments found to export")
    
    with tab4:
        st.subheader("Import Appointments from CSV")
        
        st.write("Upload a CSV file to create multiple appointments at once.")
        
        # Show required format
        with st.expander("📋 Required CSV Format"):
            st.write("""
            **Required columns:**
            - `booking_start` - Date and time (YYYY-MM-DD HH:MM format)
            - `service_id` - Service ID (number)
            - `provider_id` - Provider/Employee ID (number)
            - `customer_id` - Customer ID (number)
            
            **Optional columns:**
            - `location_id` - Location ID (number)
            - `persons` - Number of persons (default: 1)
            - `duration` - Duration in seconds
            - `status` - Booking status (default: approved)
            - `internal_notes` - Internal notes
            - `notify_participants` - 1 or 0 (default: 1)
            - `custom_fields` - JSON string of custom fields
            """)
            
            # Sample CSV
            sample_df = pd.DataFrame([
                {
                    'booking_start': '2024-12-15 10:00',
                    'service_id': 1,
                    'provider_id': 1,
                    'customer_id': 10,
                    'location_id': 1,
                    'persons': 1,
                    'status': 'approved',
                    'internal_notes': 'Sample appointment'
                }
            ])
            st.write("Sample format:")
            st.dataframe(sample_df)
            
            # Download sample
            sample_csv = CSVHandler.dataframe_to_csv_download(sample_df, "sample_appointments.csv")
            st.download_button(
                label="Download Sample CSV",
                data=sample_csv,
                file_name="sample_appointments.csv",
                mime="text/csv"
            )
        
        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                
                st.write(f"Loaded {len(df)} rows from CSV")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Validate
                is_valid, errors = CSVHandler.validate_appointment_csv(df)
                
                if not is_valid:
                    st.error("Validation errors found:")
                    for error in errors:
                        st.error(f"- {error}")
                else:
                    st.success("✅ CSV validation passed")
                    
                    if st.button("Import Appointments", type="primary"):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        success_count = 0
                        error_count = 0
                        errors_list = []
                        
                        for idx, row in df.iterrows():
                            status_text.text(f"Processing row {idx + 1} of {len(df)}...")
                            progress_bar.progress((idx + 1) / len(df))
                            
                            try:
                                appointment_data = CSVHandler.csv_to_appointment_data(row)
                                result = st.session_state.api_client.create_appointment(appointment_data)
                                
                                if 'error' in result:
                                    error_count += 1
                                    errors_list.append(f"Row {idx + 1}: {result['error']}")
                                elif 'data' in result and 'appointment' in result['data']:
                                    success_count += 1
                                else:
                                    error_count += 1
                                    errors_list.append(f"Row {idx + 1}: Unexpected response")
                            except Exception as e:
                                error_count += 1
                                errors_list.append(f"Row {idx + 1}: {str(e)}")
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Show results
                        st.success(f"✅ Successfully imported {success_count} appointments")
                        if error_count > 0:
                            st.error(f"❌ Failed to import {error_count} appointments")
                            with st.expander("View Errors"):
                                for error in errors_list:
                                    st.error(error)
                        
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")


def show_customers_page():
    """Display customers management page"""
    st.header("👥 Customers Management")
    
    tab1, tab2, tab3 = st.tabs(["View Customers", "Create Customer", "Export CSV"])
    
    with tab1:
        st.subheader("All Customers")
        
        if st.button("Load Customers", type="primary"):
            with st.spinner("Loading customers..."):
                result = st.session_state.api_client.get_customers()
                
                if 'error' in result:
                    st.error(f"Error: {result['error']}")
                elif 'data' in result and 'users' in result['data']:
                    df = CSVHandler.export_customers_to_csv(result)
                    st.success(f"Loaded {len(df)} customers")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("Unexpected response format")
    
    with tab2:
        st.subheader("Create New Customer")
        
        with st.form("create_customer_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name*")
                last_name = st.text_input("Last Name*")
                email = st.text_input("Email*")
                phone = st.text_input("Phone")
            
            with col2:
                birthday = st.date_input("Birthday", value=None)
                gender = st.selectbox("Gender", ["", "male", "female"])
                status = st.selectbox("Status", ["visible", "hidden"])
                note = st.text_area("Note")
            
            submitted = st.form_submit_button("Create Customer", type="primary")
            
            if submitted:
                if not first_name or not last_name or not email:
                    st.error("First name, last name, and email are required")
                else:
                    customer_data = {
                        'firstName': first_name,
                        'lastName': last_name,
                        'email': email,
                        'status': status
                    }
                    
                    if phone:
                        customer_data['phone'] = phone
                    if birthday:
                        customer_data['birthday'] = birthday.strftime('%Y-%m-%d')
                    if gender:
                        customer_data['gender'] = gender
                    if note:
                        customer_data['note'] = note
                    
                    with st.spinner("Creating customer..."):
                        result = st.session_state.api_client.create_customer(customer_data)
                        
                        if 'error' in result:
                            st.error(f"Error: {result['error']}")
                        elif 'data' in result and 'user' in result['data']:
                            st.success("Customer created successfully!")
                            st.json(result['data']['user'])
                        else:
                            st.warning("Unexpected response")
                            st.json(result)
    
    with tab3:
        st.subheader("Export Customers to CSV")
        
        if st.button("Generate CSV Export", type="primary", key="export_customers"):
            with st.spinner("Fetching customers..."):
                result = st.session_state.api_client.get_customers()
                
                if 'error' in result:
                    st.error(f"Error: {result['error']}")
                elif 'data' in result and 'users' in result['data']:
                    df = CSVHandler.export_customers_to_csv(result)
                    
                    if not df.empty:
                        st.success(f"Ready to export {len(df)} customers")
                        st.dataframe(df.head(10), use_container_width=True)
                        
                        csv_data = CSVHandler.dataframe_to_csv_download(df)
                        filename = f"amelia_customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv",
                            type="primary"
                        )


def show_services_page():
    """Display services management page"""
    st.header("🛎️ Services Management")
    
    tab1, tab2 = st.tabs(["View Services", "Export CSV"])
    
    with tab1:
        st.subheader("All Services")
        
        if st.button("Load Services", type="primary"):
            with st.spinner("Loading services..."):
                result = st.session_state.api_client.get_services()
                
                if 'error' in result:
                    st.error(f"Error: {result['error']}")
                elif 'data' in result and 'services' in result['data']:
                    df = CSVHandler.export_services_to_csv(result)
                    st.success(f"Loaded {len(df)} services")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("Unexpected response format")
    
    with tab2:
        st.subheader("Export Services to CSV")
        
        if st.button("Generate CSV Export", type="primary", key="export_services"):
            with st.spinner("Fetching services..."):
                result = st.session_state.api_client.get_services()
                
                if 'error' in result:
                    st.error(f"Error: {result['error']}")
                elif 'data' in result and 'services' in result['data']:
                    df = CSVHandler.export_services_to_csv(result)
                    
                    if not df.empty:
                        st.success(f"Ready to export {len(df)} services")
                        st.dataframe(df.head(10), use_container_width=True)
                        
                        csv_data = CSVHandler.dataframe_to_csv_download(df)
                        filename = f"amelia_services_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv",
                            type="primary"
                        )


def show_employees_page():
    """Display employees management page"""
    st.header("👨‍💼 Employees Management")
    
    if st.button("Load Employees", type="primary"):
        with st.spinner("Loading employees..."):
            result = st.session_state.api_client.get_employees()
            
            if 'error' in result:
                st.error(f"Error: {result['error']}")
            elif 'data' in result and 'users' in result['data']:
                employees = result['data']['users']
                
                if employees:
                    # Create DataFrame
                    rows = []
                    for emp in employees:
                        row = {
                            'ID': emp.get('id'),
                            'First Name': emp.get('firstName'),
                            'Last Name': emp.get('lastName'),
                            'Email': emp.get('email'),
                            'Phone': emp.get('phone'),
                            'Status': emp.get('status')
                        }
                        rows.append(row)
                    
                    df = pd.DataFrame(rows)
                    st.success(f"Loaded {len(df)} employees")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No employees found")
            else:
                st.warning("Unexpected response format")


def show_locations_page():
    """Display locations management page"""
    st.header("📍 Locations Management")
    
    if st.button("Load Locations", type="primary"):
        with st.spinner("Loading locations..."):
            result = st.session_state.api_client.get_locations()
            
            if 'error' in result:
                st.error(f"Error: {result['error']}")
            elif 'data' in result and 'locations' in result['data']:
                locations = result['data']['locations']
                
                if locations:
                    rows = []
                    for loc in locations:
                        row = {
                            'ID': loc.get('id'),
                            'Name': loc.get('name'),
                            'Address': loc.get('address'),
                            'Phone': loc.get('phone'),
                            'Status': loc.get('status')
                        }
                        rows.append(row)
                    
                    df = pd.DataFrame(rows)
                    st.success(f"Loaded {len(df)} locations")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No locations found")
            else:
                st.warning("Unexpected response format")


def show_categories_page():
    """Display categories management page"""
    st.header("📂 Categories Management")
    
    if st.button("Load Categories", type="primary"):
        with st.spinner("Loading categories..."):
            result = st.session_state.api_client.get_categories()
            
            if 'error' in result:
                st.error(f"Error: {result['error']}")
            elif 'data' in result and 'categories' in result['data']:
                categories = result['data']['categories']
                
                if categories:
                    rows = []
                    for cat in categories:
                        row = {
                            'ID': cat.get('id'),
                            'Name': cat.get('name'),
                            'Status': cat.get('status'),
                            'Position': cat.get('position'),
                            'Services': len(cat.get('serviceList', []))
                        }
                        rows.append(row)
                    
                    df = pd.DataFrame(rows)
                    st.success(f"Loaded {len(df)} categories")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No categories found")
            else:
                st.warning("Unexpected response format")


def main():
    """Main application"""
    
    # Title
    st.title("📅 Amelia API Management Tool")
    
    # Initialize API client
    if not st.session_state.authenticated:
        with st.spinner("Connecting to Amelia API..."):
            if not init_api_client():
                st.stop()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    page = st.sidebar.radio(
        "Select Page",
        [
            "📅 Appointments",
            "👥 Customers",
            "🛎️ Services",
            "👨‍💼 Employees",
            "📍 Locations",
            "📂 Categories"
        ]
    )
    
    # Connection status
    st.sidebar.success("✅ Connected to Amelia API")
    
    # API Info
    with st.sidebar.expander("ℹ️ API Information"):
        st.write(f"**Base URL:** {st.secrets['amelia']['api_base_url'][:50]}...")
        st.write(f"**Status:** Connected")
    
    # Display selected page
    if page == "📅 Appointments":
        show_appointments_page()
    elif page == "👥 Customers":
        show_customers_page()
    elif page == "🛎️ Services":
        show_services_page()
    elif page == "👨‍💼 Employees":
        show_employees_page()
    elif page == "📍 Locations":
        show_locations_page()
    elif page == "📂 Categories":
        show_categories_page()


if __name__ == "__main__":
    main()

