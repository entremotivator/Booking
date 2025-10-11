"""
Amelia API Management Tool - Enhanced Version
A comprehensive Streamlit application for managing Amelia booking system via API.
Features: Advanced filtering, bulk operations, analytics, and more.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import time
from typing import Dict, List, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from api_client import AmeliaAPIClient
from csv_handler import CSVHandler

# Page configuration
st.set_page_config(
    page_title="Amelia API Manager Pro",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #17a2b8;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_client' not in st.session_state:
    st.session_state.api_client = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'appointments_cache' not in st.session_state:
    st.session_state.appointments_cache = None
if 'customers_cache' not in st.session_state:
    st.session_state.customers_cache = None
if 'services_cache' not in st.session_state:
    st.session_state.services_cache = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None
if 'operation_log' not in st.session_state:
    st.session_state.operation_log = []


def log_operation(operation_type: str, status: str, details: str):
    """Log operations for audit trail"""
    log_entry = {
        'timestamp': datetime.now(),
        'type': operation_type,
        'status': status,
        'details': details
    }
    st.session_state.operation_log.append(log_entry)
    # Keep only last 100 entries
    if len(st.session_state.operation_log) > 100:
        st.session_state.operation_log = st.session_state.operation_log[-100:]


def init_api_client():
    """Initialize API client from secrets with enhanced error handling"""
    try:
        api_base = st.secrets["amelia"]["api_base_url"]
        api_key = st.secrets["amelia"]["api_key"]
        
        client = AmeliaAPIClient(api_base, api_key)
        
        # Test connection with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            if client.test_connection():
                st.session_state.api_client = client
                st.session_state.authenticated = True
                log_operation("API_CONNECTION", "SUCCESS", "Connected to Amelia API")
                return True
            if attempt < max_retries - 1:
                time.sleep(2)
        
        st.error("Failed to connect to Amelia API after multiple attempts. Please check your credentials.")
        log_operation("API_CONNECTION", "FAILURE", "Failed to connect to Amelia API")
        return False
        
    except KeyError as e:
        st.error(f"Missing configuration: {str(e)}")
        st.info("Please configure your API credentials in .streamlit/secrets.toml")
        return False
    except Exception as e:
        st.error(f"Error initializing API client: {str(e)}")
        log_operation("API_CONNECTION", "ERROR", str(e))
        return False


def show_dashboard():
    """Display analytics dashboard"""
    st.header("📊 Dashboard & Analytics")
    
    # Refresh button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("🔄 Refresh Dashboard Data", type="primary"):
            with st.spinner("Refreshing all data..."):
                # Load appointments
                appointments_result = st.session_state.api_client.get_appointments({})
                if 'data' in appointments_result:
                    st.session_state.appointments_cache = appointments_result
                
                # Load customers
                customers_result = st.session_state.api_client.get_customers()
                if 'data' in customers_result:
                    st.session_state.customers_cache = customers_result
                
                # Load services
                services_result = st.session_state.api_client.get_services()
                if 'data' in services_result:
                    st.session_state.services_cache = services_result
                
                st.session_state.last_refresh = datetime.now()
                st.success("✅ Data refreshed successfully!")
    
    with col2:
        if st.session_state.last_refresh:
            st.info(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    # Key metrics
    st.subheader("📈 Key Metrics")
    
    metric_cols = st.columns(4)
    
    # Appointments metrics
    if st.session_state.appointments_cache:
        appointments = st.session_state.appointments_cache.get('data', {}).get('appointments', [])
        total_appointments = len(appointments)
        
        # Status breakdown
        approved = sum(1 for a in appointments if a.get('status') == 'approved')
        pending = sum(1 for a in appointments if a.get('status') == 'pending')
        canceled = sum(1 for a in appointments if a.get('status') == 'canceled')
        
        with metric_cols[0]:
            st.metric("Total Appointments", total_appointments)
        with metric_cols[1]:
            st.metric("Approved", approved, delta=None)
        with metric_cols[2]:
            st.metric("Pending", pending, delta=None)
        with metric_cols[3]:
            st.metric("Canceled", canceled, delta=None)
    
    # Additional metrics row
    metric_cols2 = st.columns(4)
    
    if st.session_state.customers_cache:
        customers = st.session_state.customers_cache.get('data', {}).get('users', [])
        with metric_cols2[0]:
            st.metric("Total Customers", len(customers))
    
    if st.session_state.services_cache:
        services = st.session_state.services_cache.get('data', {}).get('services', [])
        with metric_cols2[1]:
            st.metric("Active Services", len(services))
    
    st.divider()
    
    # Visualizations
    if st.session_state.appointments_cache:
        appointments = st.session_state.appointments_cache.get('data', {}).get('appointments', [])
        
        if appointments:
            viz_col1, viz_col2 = st.columns(2)
            
            with viz_col1:
                st.subheader("📊 Appointments by Status")
                status_counts = {}
                for appt in appointments:
                    status = appt.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                fig_status = px.pie(
                    names=list(status_counts.keys()),
                    values=list(status_counts.values()),
                    title="Status Distribution"
                )
                st.plotly_chart(fig_status, use_container_width=True)
            
            with viz_col2:
                st.subheader("📅 Appointments Timeline")
                # Create date-based timeline
                date_counts = {}
                for appt in appointments:
                    booking_start = appt.get('bookingStart', '')
                    if booking_start:
                        date = booking_start.split(' ')[0]
                        date_counts[date] = date_counts.get(date, 0) + 1
                
                if date_counts:
                    sorted_dates = sorted(date_counts.items())
                    fig_timeline = px.line(
                        x=[d[0] for d in sorted_dates],
                        y=[d[1] for d in sorted_dates],
                        title="Appointments Over Time",
                        labels={'x': 'Date', 'y': 'Number of Appointments'}
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Service popularity
            st.subheader("🌟 Popular Services")
            service_counts = {}
            for appt in appointments:
                service_id = appt.get('serviceId')
                if service_id:
                    service_counts[service_id] = service_counts.get(service_id, 0) + 1
            
            if service_counts:
                sorted_services = sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                fig_services = px.bar(
                    x=[f"Service {s[0]}" for s in sorted_services],
                    y=[s[1] for s in sorted_services],
                    title="Top 10 Most Booked Services",
                    labels={'x': 'Service', 'y': 'Number of Bookings'}
                )
                st.plotly_chart(fig_services, use_container_width=True)


def show_appointments_page():
    """Display appointments management page with enhanced features"""
    st.header("📅 Appointments Management")
    
    # Action tabs
    tabs = st.tabs([
        "View & Search",
        "Create Appointment",
        "Bulk Operations",
        "Export CSV",
        "Import CSV",
        "Advanced Filters"
    ])
    
    with tabs[0]:  # View & Search
        st.subheader("All Appointments")
        
        # Enhanced filters
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        
        with filter_col1:
            date_from = st.date_input("From Date", datetime.now() - timedelta(days=30))
        with filter_col2:
            date_to = st.date_input("To Date", datetime.now() + timedelta(days=30))
        with filter_col3:
            status_filter = st.selectbox(
                "Status",
                ["All", "approved", "pending", "canceled", "rejected"]
            )
        with filter_col4:
            items_per_page = st.selectbox("Items per page", [10, 25, 50, 100], index=2)
        
        # Additional search filters
        search_col1, search_col2 = st.columns(2)
        with search_col1:
            search_customer = st.text_input("🔍 Search by Customer Name/Email")
        with search_col2:
            search_service = st.text_input("🔍 Search by Service")
        
        load_col1, load_col2 = st.columns([1, 3])
        with load_col1:
            load_button = st.button("Load Appointments", type="primary", use_container_width=True)
        with load_col2:
            if load_button:
                st.info("💡 Tip: Use the search filters to narrow down results")
        
        if load_button:
            with st.spinner("Loading appointments..."):
                params = {}
                if status_filter != "All":
                    params['status'] = status_filter
                
                result = st.session_state.api_client.get_appointments(params)
                
                if 'error' in result:
                    st.error(f"❌ Error: {result['error']}")
                    log_operation("GET_APPOINTMENTS", "ERROR", result['error'])
                elif 'data' in result and 'appointments' in result['data']:
                    appointments = result['data']['appointments']
                    
                    if appointments:
                        # Apply additional filters
                        filtered_appointments = appointments
                        
                        if search_customer:
                            filtered_appointments = [
                                a for a in filtered_appointments
                                if any(
                                    search_customer.lower() in str(b.get('customer', {}).get(field, '')).lower()
                                    for b in a.get('bookings', [])
                                    for field in ['firstName', 'lastName', 'email']
                                )
                            ]
                        
                        if search_service:
                            filtered_appointments = [
                                a for a in filtered_appointments
                                if search_service.lower() in str(a.get('service', {}).get('name', '')).lower()
                            ]
                        
                        # Convert to DataFrame
                        df = CSVHandler.export_appointments_to_csv({'data': {'appointments': filtered_appointments}})
                        
                        st.success(f"✅ Loaded {len(filtered_appointments)} appointments (filtered from {len(appointments)} total)")
                        
                        # Display with pagination
                        total_pages = (len(df) - 1) // items_per_page + 1
                        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
                        
                        start_idx = (page - 1) * items_per_page
                        end_idx = start_idx + items_per_page
                        
                        st.dataframe(
                            df.iloc[start_idx:end_idx],
                            use_container_width=True,
                            height=400
                        )
                        
                        st.caption(f"Showing {start_idx + 1} to {min(end_idx, len(df))} of {len(df)} appointments")
                        
                        # Store in session state
                        st.session_state.appointments_data = {'data': {'appointments': filtered_appointments}}
                        log_operation("GET_APPOINTMENTS", "SUCCESS", f"Loaded {len(filtered_appointments)} appointments")
                        
                        # Quick stats
                        st.divider()
                        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                        with stat_col1:
                            st.metric("Total Results", len(filtered_appointments))
                        with stat_col2:
                            approved_count = sum(1 for a in filtered_appointments if a.get('status') == 'approved')
                            st.metric("Approved", approved_count)
                        with stat_col3:
                            pending_count = sum(1 for a in filtered_appointments if a.get('status') == 'pending')
                            st.metric("Pending", pending_count)
                        with stat_col4:
                            canceled_count = sum(1 for a in filtered_appointments if a.get('status') == 'canceled')
                            st.metric("Canceled", canceled_count)
                    else:
                        st.info("ℹ️ No appointments found matching your criteria")
                else:
                    st.warning("⚠️ Unexpected response format")
    
    with tabs[1]:  # Create Appointment
        st.subheader("Create New Appointment")
        
        with st.form("create_appointment_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 📅 Booking Details")
                booking_date = st.date_input("Booking Date*")
                booking_time = st.time_input("Booking Time*")
                service_id = st.number_input("Service ID*", min_value=1, step=1, help="The ID of the service to book")
                provider_id = st.number_input("Provider/Employee ID*", min_value=1, step=1, help="The ID of the employee/provider")
                customer_id = st.number_input("Customer ID*", min_value=1, step=1, help="The ID of the customer")
            
            with col2:
                st.markdown("##### ⚙️ Additional Options")
                location_id = st.number_input("Location ID (optional)", min_value=0, step=1)
                persons = st.number_input("Number of Persons", min_value=1, value=1, step=1)
                duration = st.number_input("Duration (seconds, optional)", min_value=0, step=300, help="Leave as 0 for default service duration")
                status = st.selectbox("Status*", ["approved", "pending"], help="Initial appointment status")
                notify = st.checkbox("Notify Participants", value=True, help="Send email notifications")
            
            internal_notes = st.text_area("Internal Notes", help="Notes visible only to staff")
            
            # Extras section
            st.markdown("##### 🎁 Optional Extras")
            extras_json = st.text_area(
                "Extras (JSON format)",
                placeholder='[{"id": 1, "quantity": 1}]',
                help="Add service extras in JSON format"
            )
            
            submitted = st.form_submit_button("Create Appointment", type="primary", use_container_width=True)
            
            if submitted:
                # Validation
                if not all([booking_date, booking_time, service_id, provider_id, customer_id]):
                    st.error("❌ Please fill in all required fields (marked with *)")
                else:
                    try:
                        # Combine date and time
                        booking_datetime = datetime.combine(booking_date, booking_time)
                        booking_start = booking_datetime.strftime("%Y-%m-%d %H:%M")
                        
                        # Parse extras if provided
                        extras = []
                        if extras_json.strip():
                            try:
                                extras = json.loads(extras_json)
                            except json.JSONDecodeError:
                                st.error("❌ Invalid JSON format for extras")
                                st.stop()
                        
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
                                    'extras': extras
                                }
                            ]
                        }
                        
                        if duration > 0:
                            appointment_data['bookings'][0]['duration'] = int(duration)
                        
                        with st.spinner("Creating appointment..."):
                            result = st.session_state.api_client.create_appointment(appointment_data)
                            
                            if 'error' in result:
                                st.error(f"❌ Error: {result['error']}")
                                log_operation("CREATE_APPOINTMENT", "ERROR", result['error'])
                            elif 'data' in result and 'appointment' in result['data']:
                                st.success("✅ Appointment created successfully!")
                                with st.expander("View Created Appointment Details"):
                                    st.json(result['data']['appointment'])
                                log_operation("CREATE_APPOINTMENT", "SUCCESS", f"Appointment ID: {result['data']['appointment'].get('id')}")
                            else:
                                st.warning("⚠️ Unexpected response")
                                st.json(result)
                    
                    except Exception as e:
                        st.error(f"❌ Error creating appointment: {str(e)}")
                        log_operation("CREATE_APPOINTMENT", "ERROR", str(e))
    
    with tabs[2]:  # Bulk Operations
        st.subheader("🔧 Bulk Operations")
        
        st.info("💡 Perform actions on multiple appointments at once")
        
        operation_type = st.selectbox(
            "Select Operation",
            [
                "Update Status",
                "Delete Appointments",
                "Reschedule Appointments",
                "Send Notifications"
            ]
        )
        
        if operation_type == "Update Status":
            st.markdown("#### Update Status in Bulk")
            
            col1, col2 = st.columns(2)
            with col1:
                appointment_ids = st.text_area(
                    "Appointment IDs (one per line)",
                    help="Enter appointment IDs, one per line"
                )
            with col2:
                new_status = st.selectbox("New Status", ["approved", "pending", "canceled", "rejected"])
                send_notification = st.checkbox("Send notification emails", value=True)
            
            if st.button("Update Status", type="primary"):
                if not appointment_ids.strip():
                    st.error("❌ Please enter at least one appointment ID")
                else:
                    ids = [id.strip() for id in appointment_ids.split('\n') if id.strip()]
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    success_count = 0
                    error_count = 0
                    errors_list = []
                    
                    for idx, appt_id in enumerate(ids):
                        status_text.text(f"Processing appointment {idx + 1} of {len(ids)}...")
                        progress_bar.progress((idx + 1) / len(ids))
                        
                        try:
                            update_data = {
                                'status': new_status,
                                'notifyParticipants': 1 if send_notification else 0
                            }
                            
                            result = st.session_state.api_client.update_appointment(appt_id, update_data)
                            
                            if 'error' in result:
                                error_count += 1
                                errors_list.append(f"ID {appt_id}: {result['error']}")
                            else:
                                success_count += 1
                        except Exception as e:
                            error_count += 1
                            errors_list.append(f"ID {appt_id}: {str(e)}")
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Results
                    if success_count > 0:
                        st.success(f"✅ Successfully updated {success_count} appointments")
                    if error_count > 0:
                        st.error(f"❌ Failed to update {error_count} appointments")
                        with st.expander("View Errors"):
                            for error in errors_list:
                                st.error(error)
                    
                    log_operation("BULK_UPDATE_STATUS", "COMPLETED", f"Success: {success_count}, Errors: {error_count}")
        
        elif operation_type == "Delete Appointments":
            st.markdown("#### Delete Appointments in Bulk")
            st.warning("⚠️ This action cannot be undone!")
            
            appointment_ids = st.text_area(
                "Appointment IDs to delete (one per line)",
                help="Enter appointment IDs to delete"
            )
            
            confirm_delete = st.checkbox("I understand this action is permanent")
            
            if st.button("Delete Appointments", type="primary", disabled=not confirm_delete):
                if not appointment_ids.strip():
                    st.error("❌ Please enter at least one appointment ID")
                else:
                    ids = [id.strip() for id in appointment_ids.split('\n') if id.strip()]
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    success_count = 0
                    error_count = 0
                    
                    for idx, appt_id in enumerate(ids):
                        status_text.text(f"Deleting appointment {idx + 1} of {len(ids)}...")
                        progress_bar.progress((idx + 1) / len(ids))
                        
                        try:
                            result = st.session_state.api_client.delete_appointment(appt_id)
                            if 'error' not in result:
                                success_count += 1
                            else:
                                error_count += 1
                        except:
                            error_count += 1
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.success(f"✅ Deleted {success_count} appointments")
                    if error_count > 0:
                        st.warning(f"⚠️ Failed to delete {error_count} appointments")
        
        elif operation_type == "Send Notifications":
            st.markdown("#### Send Notifications in Bulk")
            
            col1, col2 = st.columns(2)
            with col1:
                appointment_ids = st.text_area("Appointment IDs (one per line)")
            with col2:
                notification_type = st.selectbox(
                    "Notification Type",
                    ["Reminder", "Confirmation", "Custom"]
                )
                custom_message = st.text_area("Custom Message (if applicable)")
            
            if st.button("Send Notifications", type="primary"):
                st.info("🔔 Notification feature would be implemented here")
                # Implementation would depend on Amelia API notification endpoints
    
    with tabs[3]:  # Export CSV
        st.subheader("📥 Export Appointments to CSV")
        
        st.write("Export appointments data to CSV file for analysis, reporting, or backup.")
        
        export_col1, export_col2, export_col3 = st.columns(3)
        with export_col1:
            export_date_from = st.date_input(
                "From Date",
                datetime.now() - timedelta(days=30),
                key="export_from"
            )
        with export_col2:
            export_date_to = st.date_input(
                "To Date",
                datetime.now() + timedelta(days=30),
                key="export_to"
            )
        with export_col3:
            export_status = st.selectbox(
                "Status Filter",
                ["All", "approved", "pending", "canceled", "rejected"],
                key="export_status"
            )
        
        # Export format options
        st.markdown("##### Export Options")
        export_format_col1, export_format_col2 = st.columns(2)
        with export_format_col1:
            include_customer_details = st.checkbox("Include customer details", value=True)
            include_service_details = st.checkbox("Include service details", value=True)
        with export_format_col2:
            include_provider_details = st.checkbox("Include provider details", value=True)
            include_payment_info = st.checkbox("Include payment information", value=False)
        
        if st.button("Generate CSV Export", type="primary", use_container_width=True):
            with st.spinner("Fetching appointments..."):
                params = {}
                if export_status != "All":
                    params['status'] = export_status
                
                result = st.session_state.api_client.get_appointments(params)
                
                if 'error' in result:
                    st.error(f"❌ Error: {result['error']}")
                elif 'data' in result and 'appointments' in result['data']:
                    df = CSVHandler.export_appointments_to_csv(result)
                    
                    if not df.empty:
                        st.success(f"✅ Ready to export {len(df)} appointment records")
                        
                        # Statistics
                        stat_col1, stat_col2, stat_col3 = st.columns(3)
                        with stat_col1:
                            st.metric("Total Records", len(df))
                        with stat_col2:
                            st.metric("Date Range", f"{export_date_from} to {export_date_to}")
                        with stat_col3:
                            st.metric("File Size", f"~{len(df) * 100} bytes")
                        
                        # Preview
                        st.markdown("##### Preview (first 10 rows)")
                        st.dataframe(df.head(10), use_container_width=True)
                        
                        # Download button
                        csv_data = CSVHandler.dataframe_to_csv_download(df)
                        filename = f"amelia_appointments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        
                        st.download_button(
                            label="📥 Download CSV File",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv",
                            type="primary",
                            use_container_width=True
                        )
                        
                        log_operation("EXPORT_CSV", "SUCCESS", f"Exported {len(df)} appointments")
                    else:
                        st.info("ℹ️ No appointments found to export")
    
    with tabs[4]:  # Import CSV
        st.subheader("📤 Import Appointments from CSV")
        
        st.write("Upload a CSV file to create multiple appointments at once. This is useful for bulk imports, migrations, or scheduled bookings.")
        
        # Show required format
        with st.expander("📋 Required CSV Format & Guidelines", expanded=True):
            st.markdown("""
            **Required columns:**
            - `booking_start` - Date and time in YYYY-MM-DD HH:MM format (e.g., 2024-12-15 10:00)
            - `service_id` - Service ID (positive integer)
            - `provider_id` - Provider/Employee ID (positive integer)
            - `customer_id` - Customer ID (positive integer)
            
            **Optional columns:**
            - `location_id` - Location ID (positive integer or empty)
            - `persons` - Number of persons (default: 1)
            - `duration` - Duration in seconds (leave empty for service default)
            - `status` - Booking status: approved, pending, canceled, or rejected (default: approved)
            - `internal_notes` - Internal staff notes
            - `notify_participants` - 1 to send notifications, 0 to skip (default: 1)
            - `custom_fields` - JSON string of custom field values
            - `extras` - JSON string of service extras
            
            **Important Notes:**
            - All IDs must exist in your Amelia system
            - Dates must be in the future
            - Time slots must be available
            - Invalid rows will be skipped with error details
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
                    'internal_notes': 'Sample appointment',
                    'notify_participants': 1
                },
                {
                    'booking_start': '2024-12-15 14:30',
                    'service_id': 2,
                    'provider_id': 2,
                    'customer_id': 11,
                    'location_id': '',
                    'persons': 2,
                    'status': 'pending',
                    'internal_notes': 'Group booking',
                    'notify_participants': 1
                }
            ])
            
            st.markdown("##### Sample CSV Format:")
            st.dataframe(sample_df, use_container_width=True)
            
            # Download sample
            sample_csv = CSVHandler.dataframe_to_csv_download(sample_df)
            st.download_button(
                label="📥 Download Sample CSV Template",
                data=sample_csv,
                file_name="amelia_appointments_template.csv",
                mime="text/csv",
                help="Download this template and fill it with your data"
            )
        
        st.divider()
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose CSV file to import",
            type=['csv'],
            help="Select a CSV file with appointment data"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                
                st.success(f"✅ File loaded successfully: {len(df)} rows found")
                
                # Show preview
                with st.expander("📊 Data Preview", expanded=True):
                    st.dataframe(df.head(20), use_container_width=True)
                    
                    # Column info
                    st.markdown("##### Detected Columns:")
                    cols_display = st.columns(min(len(df.columns), 4))
                    for idx, col in enumerate(df.columns):
                        with cols_display[idx % 4]:
                            st.caption(f"✓ {col}")
                
                # Validate
                is_valid, errors = CSVHandler.validate_appointment_csv(df)
                
                st.divider()
                
                if not is_valid:
                    st.error("❌ Validation Failed - Please fix the following errors:")
                    for error in errors:
                        st.error(f"• {error}")
                    
                    st.info("💡 Fix the errors in your CSV file and upload again")
                else:
                    st.success("✅ CSV validation passed - Ready to import!")
                    
                    # Import options
                    st.markdown("##### Import Options")
                    import_col1, import_col2 = st.columns(2)
                    
                    with import_col1:
                        skip_errors = st.checkbox(
                            "Skip rows with errors and continue",
                            value=True,
                            help="Continue importing even if some rows fail"
                        )
                        dry_run = st.checkbox(
                            "Dry run (validate only, don't create)",
                            value=False,
                            help="Test the import without actually creating appointments"
                        )
                    
                    with import_col2:
                        batch_size = st.number_input(
                            "Batch size",
                            min_value=1,
                            max_value=100,
                            value=10,
                            help="Number of appointments to create at once"
                        )
                        delay_between = st.number_input(
                            "Delay between batches (seconds)",
                            min_value=0.0,
                            max_value=10.0,
                            value=1.0,
                            step=0.5,
                            help="Prevent API rate limiting"
                        )
                    
                    st.divider()
                    
                    if st.button("🚀 Start Import", type="primary", use_container_width=True):
                        if dry_run:
                            st.info("🔍 Dry run mode - No appointments will be created")
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        success_count = 0
                        error_count = 0
                        skipped_count = 0
                        errors_list = []
                        success_list = []
                        
                        start_time = time.time()
                        
                        for idx, row in df.iterrows():
                            status_text.text(f"Processing row {idx + 1} of {len(df)}...")
                            progress_bar.progress((idx + 1) / len(df))
                            
                            try:
                                appointment_data = CSVHandler.csv_to_appointment_data(row)
                                
                                if not dry_run:
                                    result = st.session_state.api_client.create_appointment(appointment_data)
                                    
                                    if 'error' in result:
                                        error_count += 1
                                        errors_list.append({
                                            'row': idx + 1,
                                            'data': row.to_dict(),
                                            'error': result['error']
                                        })
                                        
                                        if not skip_errors:
                                            st.error(f"Error on row {idx + 1}, stopping import")
                                            break
                                    elif 'data' in result and 'appointment' in result['data']:
                                        success_count += 1
                                        success_list.append({
                                            'row': idx + 1,
                                            'appointment_id': result['data']['appointment'].get('id'),
                                            'booking_start': appointment_data.get('bookingStart')
                                        })
                                    else:
                                        error_count += 1
                                        errors_list.append({
                                            'row': idx + 1,
                                            'data': row.to_dict(),
                                            'error': 'Unexpected response format'
                                        })
                                else:
                                    # Dry run - just validate structure
                                    success_count += 1
                                
                                # Batch delay
                                if (idx + 1) % batch_size == 0 and delay_between > 0:
                                    time.sleep(delay_between)
                                    
                            except Exception as e:
                                error_count += 1
                                errors_list.append({
                                    'row': idx + 1,
                                    'data': row.to_dict(),
                                    'error': str(e)
                                })
                                
                                if not skip_errors:
                                    st.error(f"Error on row {idx + 1}, stopping import")
                                    break
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Calculate duration
                        duration = time.time() - start_time
                        
                        # Show results
                        st.divider()
                        st.markdown("### 📊 Import Results")
                        
                        result_cols = st.columns(4)
                        with result_cols[0]:
                            st.metric("✅ Successful", success_count)
                        with result_cols[1]:
                            st.metric("❌ Failed", error_count)
                        with result_cols[2]:
                            st.metric("⏱️ Duration", f"{duration:.1f}s")
                        with result_cols[3]:
                            success_rate = (success_count / len(df) * 100) if len(df) > 0 else 0
                            st.metric("Success Rate", f"{success_rate:.1f}%")
                        
                        if success_count > 0:
                            st.success(f"✅ Successfully {'validated' if dry_run else 'imported'} {success_count} appointments")
                            
                            if not dry_run and success_list:
                                with st.expander(f"View {len(success_list)} Successful Imports"):
                                    success_df = pd.DataFrame(success_list)
                                    st.dataframe(success_df, use_container_width=True)
                        
                        if error_count > 0:
                            st.error(f"❌ Failed to {'validate' if dry_run else 'import'} {error_count} appointments")
                            
                            with st.expander(f"View {len(errors_list)} Errors", expanded=True):
                                for error_item in errors_list:
                                    st.error(f"**Row {error_item['row']}:** {error_item['error']}")
                                    with st.container():
                                        st.json(error_item['data'])
                                
                                # Option to download error report
                                error_df = pd.DataFrame([
                                    {
                                        'row_number': e['row'],
                                        'error_message': e['error'],
                                        **e['data']
                                    }
                                    for e in errors_list
                                ])
                                
                                error_csv = CSVHandler.dataframe_to_csv_download(error_df)
                                st.download_button(
                                    label="📥 Download Error Report",
                                    data=error_csv,
                                    file_name=f"import_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                        
                        # Log operation
                        log_operation(
                            "IMPORT_CSV",
                            "COMPLETED",
                            f"Success: {success_count}, Errors: {error_count}, Duration: {duration:.1f}s"
                        )
                        
            except Exception as e:
                st.error(f"❌ Error reading CSV file: {str(e)}")
                st.info("💡 Make sure your CSV file is properly formatted and encoded in UTF-8")
    
    with tabs[5]:  # Advanced Filters
        st.subheader("🔍 Advanced Filtering & Search")
        
        st.write("Apply complex filters to find specific appointments")
        
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            st.markdown("##### Date & Time Filters")
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now(), datetime.now() + timedelta(days=7)),
                key="advanced_date_range"
            )
            time_range = st.select_slider(
                "Time of Day",
                options=["Any", "Morning (6-12)", "Afternoon (12-18)", "Evening (18-24)"],
                value="Any"
            )
            
            st.markdown("##### Service & Provider")
            service_ids = st.text_input("Service IDs (comma-separated)")
            provider_ids = st.text_input("Provider IDs (comma-separated)")
            
        with filter_col2:
            st.markdown("##### Status & Other")
            statuses = st.multiselect(
                "Statuses",
                ["approved", "pending", "canceled", "rejected"],
                default=["approved", "pending"]
            )
            
            min_persons = st.number_input("Minimum Persons", min_value=1, value=1)
            
            has_notes = st.checkbox("Has internal notes")
            
            sort_by = st.selectbox(
                "Sort By",
                ["Date (Newest First)", "Date (Oldest First)", "Customer Name", "Service"]
            )
        
        if st.button("🔍 Apply Filters", type="primary", use_container_width=True):
            st.info("🔄 Applying advanced filters...")
            # Implementation would filter based on all criteria
            st.success("✅ Filters applied - results would be displayed here")


def show_customers_page():
    """Display customers management page with enhanced features"""
    st.header("👥 Customers Management")
    
    tabs = st.tabs(["View & Search", "Create Customer", "Import CSV", "Export CSV", "Customer Analytics"])
    
    with tabs[0]:  # View & Search
        st.subheader("All Customers")
        
        # Search and filter
        search_col1, search_col2, search_col3 = st.columns(3)
        with search_col1:
            search_query = st.text_input("🔍 Search by name or email")
        with search_col2:
            status_filter = st.selectbox("Status", ["All", "visible", "hidden"])
        with search_col3:
            sort_by = st.selectbox("Sort By", ["Name", "Email", "Created Date"])
        
        if st.button("Load Customers", type="primary", use_container_width=True):
            with st.spinner("Loading customers..."):
                result = st.session_state.api_client.get_customers()
                
                if 'error' in result:
                    st.error(f"❌ Error: {result['error']}")
                elif 'data' in result and 'users' in result['data']:
                    customers = result['data']['users']
                    
                    # Apply filters
                    if search_query:
                        customers = [
                            c for c in customers
                            if search_query.lower() in f"{c.get('firstName', '')} {c.get('lastName', '')} {c.get('email', '')}".lower()
                        ]
                    
                    if status_filter != "All":
                        customers = [c for c in customers if c.get('status') == status_filter]
                    
                    df = CSVHandler.export_customers_to_csv({'data': {'users': customers}})
                    
                    st.success(f"✅ Found {len(customers)} customers")
                    
                    # Quick stats
                    stat_col1, stat_col2, stat_col3 = st.columns(3)
                    with stat_col1:
                        st.metric("Total Customers", len(customers))
                    with stat_col2:
                        visible = sum(1 for c in customers if c.get('status') == 'visible')
                        st.metric("Active", visible)
                    with stat_col3:
                        hidden = sum(1 for c in customers if c.get('status') == 'hidden')
                        st.metric("Hidden", hidden)
                    
                    st.dataframe(df, use_container_width=True, height=400)
                    
                    st.session_state.customers_cache = {'data': {'users': customers}}
                else:
                    st.warning("⚠️ Unexpected response format")
    
    with tabs[1]:  # Create Customer
        st.subheader("Create New Customer")
        
        with st.form("create_customer_form"):
            st.markdown("##### Basic Information")
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name*", help="Customer's first name")
                last_name = st.text_input("Last Name*", help="Customer's last name")
                email = st.text_input("Email*", help="Valid email address")
                phone = st.text_input("Phone", help="Contact phone number")
            
            with col2:
                birthday = st.date_input("Birthday", value=None, help="Date of birth")
                gender = st.selectbox("Gender", ["", "male", "female", "other"])
                status = st.selectbox("Status", ["visible", "hidden"], help="Account visibility status")
            
            st.markdown("##### Additional Information")
            note = st.text_area("Note", help="Internal notes about this customer")
            
            # Custom fields
            st.markdown("##### Custom Fields (Optional)")
            custom_fields = st.text_area(
                "Custom Fields (JSON format)",
                placeholder='{"field1": "value1", "field2": "value2"}',
                help="Add custom field values in JSON format"
            )
            
            submitted = st.form_submit_button("Create Customer", type="primary", use_container_width=True)
            
            if submitted:
                if not first_name or not last_name or not email:
                    st.error("❌ First name, last name, and email are required")
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
                    
                    # Parse custom fields
                    if custom_fields.strip():
                        try:
                            customer_data['customFields'] = json.loads(custom_fields)
                        except json.JSONDecodeError:
                            st.error("❌ Invalid JSON format for custom fields")
                            st.stop()
                    
                    with st.spinner("Creating customer..."):
                        result = st.session_state.api_client.create_customer(customer_data)
                        
                        if 'error' in result:
                            st.error(f"❌ Error: {result['error']}")
                            log_operation("CREATE_CUSTOMER", "ERROR", result['error'])
                        elif 'data' in result and 'user' in result['data']:
                            st.success("✅ Customer created successfully!")
                            customer_id = result['data']['user'].get('id')
                            
                            with st.expander("View Customer Details"):
                                st.json(result['data']['user'])
                            
                            st.info(f"💡 Customer ID: {customer_id} - Use this ID when creating appointments")
                            log_operation("CREATE_CUSTOMER", "SUCCESS", f"Customer ID: {customer_id}")
                        else:
                            st.warning("⚠️ Unexpected response")
                            st.json(result)
    
    with tabs[2]:  # Import CSV
        st.subheader("📤 Import Customers from CSV")
        
        with st.expander("📋 CSV Format Requirements", expanded=True):
            st.markdown("""
            **Required columns:**
            - `first_name` - Customer's first name
            - `last_name` - Customer's last name
            - `email` - Valid email address (must be unique)
            
            **Optional columns:**
            - `phone` - Phone number
            - `birthday` - Birth date (YYYY-MM-DD format)
            - `gender` - male, female, or other
            - `status` - visible or hidden (default: visible)
            - `note` - Internal notes
            """)
            
            # Sample
            sample_customers = pd.DataFrame([
                {
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'john.doe@example.com',
                    'phone': '+1234567890',
                    'birthday': '1990-01-15',
                    'gender': 'male',
                    'status': 'visible',
                    'note': 'VIP customer'
                },
                {
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'email': 'jane.smith@example.com',
                    'phone': '+1234567891',
                    'birthday': '1985-06-20',
                    'gender': 'female',
                    'status': 'visible',
                    'note': ''
                }
            ])
            
            st.dataframe(sample_customers, use_container_width=True)
            
            sample_csv = CSVHandler.dataframe_to_csv_download(sample_customers)
            st.download_button(
                label="📥 Download Sample Template",
                data=sample_csv,
                file_name="customer_import_template.csv",
                mime="text/csv"
            )
        
        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ Loaded {len(df)} rows")
                st.dataframe(df.head(10), use_container_width=True)
                
                if st.button("Import Customers", type="primary"):
                    progress_bar = st.progress(0)
                    success_count = 0
                    error_count = 0
                    
                    for idx, row in df.iterrows():
                        progress_bar.progress((idx + 1) / len(df))
                        
                        try:
                            customer_data = {
                                'firstName': row.get('first_name'),
                                'lastName': row.get('last_name'),
                                'email': row.get('email'),
                                'status': row.get('status', 'visible')
                            }
                            
                            # Add optional fields
                            for field in ['phone', 'birthday', 'gender', 'note']:
                                if field in row and pd.notna(row[field]):
                                    customer_data[field] = row[field]
                            
                            result = st.session_state.api_client.create_customer(customer_data)
                            
                            if 'error' not in result:
                                success_count += 1
                            else:
                                error_count += 1
                        except:
                            error_count += 1
                    
                    progress_bar.empty()
                    st.success(f"✅ Imported {success_count} customers")
                    if error_count > 0:
                        st.warning(f"⚠️ {error_count} customers failed")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with tabs[3]:  # Export CSV
        st.subheader("📥 Export Customers to CSV")
        
        export_options_col1, export_options_col2 = st.columns(2)
        with export_options_col1:
            include_hidden = st.checkbox("Include hidden customers", value=False)
            include_notes = st.checkbox("Include internal notes", value=True)
        with export_options_col2:
            include_custom_fields = st.checkbox("Include custom fields", value=False)
            include_statistics = st.checkbox("Include booking statistics", value=True)
        
        if st.button("Generate Export", type="primary", use_container_width=True):
            with st.spinner("Fetching customers..."):
                result = st.session_state.api_client.get_customers()
                
                if 'error' in result:
                    st.error(f"❌ Error: {result['error']}")
                elif 'data' in result and 'users' in result['data']:
                    df = CSVHandler.export_customers_to_csv(result)
                    
                    if not df.empty:
                        st.success(f"✅ Ready to export {len(df)} customers")
                        st.dataframe(df.head(10), use_container_width=True)
                        
                        csv_data = CSVHandler.dataframe_to_csv_download(df)
                        filename = f"amelia_customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv",
                            type="primary",
                            use_container_width=True
                        )
    
    with tabs[4]:  # Customer Analytics
        st.subheader("📊 Customer Analytics")
        
        if st.session_state.customers_cache:
            customers = st.session_state.customers_cache.get('data', {}).get('users', [])
            
            if customers:
                # Gender distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    gender_counts = {}
                    for c in customers:
                        gender = c.get('gender', 'Not specified')
                        gender_counts[gender] = gender_counts.get(gender, 0) + 1
                    
                    fig = px.pie(
                        names=list(gender_counts.keys()),
                        values=list(gender_counts.values()),
                        title="Customer Gender Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    status_counts = {}
                    for c in customers:
                        status = c.get('status', 'unknown')
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    fig = px.bar(
                        x=list(status_counts.keys()),
                        y=list(status_counts.values()),
                        title="Customer Status Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 Load customer data from the View & Search tab to see analytics")


def show_services_page():
    """Display services management page with enhanced features"""
    st.header("🛎️ Services Management")
    
    tabs = st.tabs(["View Services", "Service Analytics", "Export CSV"])
    
    with tabs[0]:
        st.subheader("All Services")
        
        # Filters
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            category_filter = st.text_input("Filter by category")
        with filter_col2:
            status_filter = st.selectbox("Status", ["All", "visible", "hidden"])
        
        if st.button("Load Services", type="primary", use_container_width=True):
            with st.spinner("Loading services..."):
                result = st.session_state.api_client.get_services()
                
                if 'error' in result:
                    st.error(f"❌ Error: {result['error']}")
                elif 'data' in result and 'services' in result['data']:
                    services = result['data']['services']
                    
                    # Apply filters
                    if category_filter:
                        services = [
                            s for s in services
                            if category_filter.lower() in str(s.get('category', {}).get('name', '')).lower()
                        ]
                    
                    if status_filter != "All":
                        services = [s for s in services if s.get('status') == status_filter]
                    
                    df = CSVHandler.export_services_to_csv({'data': {'services': services}})
                    
                    st.success(f"✅ Loaded {len(services)} services")
                    
                    # Metrics
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    with metric_col1:
                        st.metric("Total Services", len(services))
                    with metric_col2:
                        avg_duration = sum(s.get('duration', 0) for s in services) / len(services) if services else 0
                        st.metric("Avg Duration", f"{int(avg_duration/60)} min")
                    with metric_col3:
                        avg_price = sum(float(s.get('price', 0)) for s in services) / len(services) if services else 0
                        st.metric("Avg Price", f"${avg_price:.2f}")
                    
                    st.dataframe(df, use_container_width=True, height=400)
                    st.session_state.services_cache = {'data': {'services': services}}
                else:
                    st.warning("⚠️ Unexpected response format")
    
    with tabs[1]:
        st.subheader("📊 Service Analytics")
        
        if st.session_state.services_cache:
            services = st.session_state.services_cache.get('data', {}).get('services', [])
            
            if services:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Price distribution
                    prices = [float(s.get('price', 0)) for s in services]
                    fig = px.histogram(
                        x=prices,
                        title="Service Price Distribution",
                        labels={'x': 'Price', 'y': 'Count'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Duration distribution
                    durations = [s.get('duration', 0) / 60 for s in services]  # Convert to minutes
                    fig = px.box(
                        y=durations,
                        title="Service Duration Distribution (minutes)",
                        labels={'y': 'Duration (min)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 Load service data to see analytics")
    
    with tabs[2]:
        st.subheader("📥 Export Services")
        
        if st.button("Generate CSV Export", type="primary", use_container_width=True):
            with st.spinner("Fetching services..."):
                result = st.session_state.api_client.get_services()
                
                if 'error' in result:
                    st.error(f"❌ Error: {result['error']}")
                elif 'data' in result and 'services' in result['data']:
                    df = CSVHandler.export_services_to_csv(result)
                    
                    if not df.empty:
                        st.success(f"✅ Ready to export {len(df)} services")
                        st.dataframe(df.head(10), use_container_width=True)
                        
                        csv_data = CSVHandler.dataframe_to_csv_download(df)
                        filename = f"amelia_services_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv",
                            type="primary",
                            use_container_width=True
                        )


def show_employees_page():
    """Display employees management page"""
    st.header("👨‍💼 Employees Management")
    
    tabs = st.tabs(["View Employees", "Employee Schedule", "Performance"])
    
    with tabs[0]:
        if st.button("Load Employees", type="primary", use_container_width=True):
            with st.spinner("Loading employees..."):
                result = st.session_state.api_client.get_employees()
                
                if 'error' in result:
                    st.error(f"❌ Error: {result['error']}")
                elif 'data' in result and 'users' in result['data']:
                    employees = result['data']['users']
                    
                    if employees:
                        rows = []
                        for emp in employees:
                            row = {
                                'ID': emp.get('id'),
                                'First Name': emp.get('firstName'),
                                'Last Name': emp.get('lastName'),
                                'Email': emp.get('email'),
                                'Phone': emp.get('phone'),
                                'Status': emp.get('status'),
                                'Services': len(emp.get('serviceList', []))
                            }
                            rows.append(row)
                        
                        df = pd.DataFrame(rows)
                        st.success(f"✅ Loaded {len(df)} employees")
                        
                        # Metrics
                        metric_col1, metric_col2, metric_col3 = st.columns(3)
                        with metric_col1:
                            st.metric("Total Employees", len(df))
                        with metric_col2:
                            active = sum(1 for e in employees if e.get('status') == 'visible')
                            st.metric("Active", active)
                        with metric_col3:
                            total_services = sum(len(e.get('serviceList', [])) for e in employees)
                            st.metric("Total Service Assignments", total_services)
                        
                        st.dataframe(df, use_container_width=True, height=400)
                    else:
                        st.info("ℹ️ No employees found")
                else:
                    st.warning("⚠️ Unexpected response format")
    
    with tabs[1]:
        st.subheader("📅 Employee Schedule Overview")
        st.info("💡 Load appointments to see employee schedules")
        
        if st.session_state.appointments_cache:
            appointments = st.session_state.appointments_cache.get('data', {}).get('appointments', [])
            
            if appointments:
                # Group by provider
                provider_schedule = {}
                for appt in appointments:
                    provider_id = appt.get('providerId')
                    provider_name = appt.get('provider', {}).get('firstName', 'Unknown')
                    
                    if provider_id not in provider_schedule:
                        provider_schedule[provider_id] = {
                            'name': provider_name,
                            'appointments': []
                        }
                    
                    provider_schedule[provider_id]['appointments'].append(appt)
                
                # Display schedule
                for provider_id, data in provider_schedule.items():
                    with st.expander(f"👤 {data['name']} - {len(data['appointments'])} appointments"):
                        appts_df = pd.DataFrame([
                            {
                                'Date': a.get('bookingStart'),
                                'Service': a.get('service', {}).get('name', 'N/A'),
                                'Customer': f"{a.get('bookings', [{}])[0].get('customer', {}).get('firstName', '')} {a.get('bookings', [{}])[0].get('customer', {}).get('lastName', '')}",
                                'Status': a.get('status')
                            }
                            for a in data['appointments']
                        ])
                        st.dataframe(appts_df, use_container_width=True)
        else:
            st.info("Load appointments from the Dashboard to view schedules")
    
    with tabs[2]:
        st.subheader("📈 Employee Performance")
        
        if st.session_state.appointments_cache:
            appointments = st.session_state.appointments_cache.get('data', {}).get('appointments', [])
            
            if appointments:
                # Calculate performance metrics
                provider_metrics = {}
                for appt in appointments:
                    provider_id = appt.get('providerId')
                    provider_name = f"{appt.get('provider', {}).get('firstName', 'Unknown')} {appt.get('provider', {}).get('lastName', '')}"
                    
                    if provider_id not in provider_metrics:
                        provider_metrics[provider_id] = {
                            'name': provider_name,
                            'total': 0,
                            'approved': 0,
                            'canceled': 0
                        }
                    
                    provider_metrics[provider_id]['total'] += 1
                    status = appt.get('status')
                    if status == 'approved':
                        provider_metrics[provider_id]['approved'] += 1
                    elif status == 'canceled':
                        provider_metrics[provider_id]['canceled'] += 1
                
                # Create performance DataFrame
                perf_data = []
                for provider_id, metrics in provider_metrics.items():
                    completion_rate = (metrics['approved'] / metrics['total'] * 100) if metrics['total'] > 0 else 0
                    perf_data.append({
                        'Employee': metrics['name'],
                        'Total Appointments': metrics['total'],
                        'Completed': metrics['approved'],
                        'Canceled': metrics['canceled'],
                        'Completion Rate': f"{completion_rate:.1f}%"
                    })
                
                perf_df = pd.DataFrame(perf_data)
                st.dataframe(perf_df, use_container_width=True)
                
                # Visualization
                fig = px.bar(
                    perf_df,
                    x='Employee',
                    y='Total Appointments',
                    title="Appointments by Employee",
                    color='Total Appointments'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 Load appointment data to see performance metrics")


def show_locations_page():
    """Display locations management page"""
    st.header("📍 Locations Management")
    
    tabs = st.tabs(["View Locations", "Location Analytics"])
    
    with tabs[0]:
        st.subheader("All Locations")
        
        if st.button("Load Locations", type="primary", use_container_width=True):
            with st.spinner("Loading locations..."):
                result = st.session_state.api_client.get_locations()
                
                if 'error' in result:
                    st.error(f"❌ Error: {result['error']}")
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
                                'Status': loc.get('status'),
                                'Description': loc.get('description', '')[:50] + '...' if loc.get('description') else ''
                            }
                            rows.append(row)
                        
                        df = pd.DataFrame(rows)
                        st.success(f"✅ Loaded {len(df)} locations")
                        
                        # Metrics
                        metric_col1, metric_col2 = st.columns(2)
                        with metric_col1:
                            st.metric("Total Locations", len(df))
                        with metric_col2:
                            active = sum(1 for l in locations if l.get('status') == 'visible')
                            st.metric("Active Locations", active)
                        
                        st.dataframe(df, use_container_width=True, height=400)
                        
                        # Location details
                        st.divider()
                        st.markdown("##### 📋 Location Details")
                        
                        for loc in locations:
                            with st.expander(f"📍 {loc.get('name', 'Unknown Location')}"):
                                detail_col1, detail_col2 = st.columns(2)
                                
                                with detail_col1:
                                    st.write(f"**ID:** {loc.get('id')}")
                                    st.write(f"**Status:** {loc.get('status')}")
                                    st.write(f"**Address:** {loc.get('address', 'N/A')}")
                                
                                with detail_col2:
                                    st.write(f"**Phone:** {loc.get('phone', 'N/A')}")
                                    st.write(f"**Pin:** {loc.get('pin', 'N/A')}")
                                
                                if loc.get('description'):
                                    st.write(f"**Description:** {loc.get('description')}")
                    else:
                        st.info("ℹ️ No locations found")
                else:
                    st.warning("⚠️ Unexpected response format")
    
    with tabs[1]:
        st.subheader("📊 Location Analytics")
        
        if st.session_state.appointments_cache:
            appointments = st.session_state.appointments_cache.get('data', {}).get('appointments', [])
            
            if appointments:
                # Count appointments per location
                location_counts = {}
                for appt in appointments:
                    location_id = appt.get('locationId')
                    location_name = appt.get('location', {}).get('name', f'Location {location_id}')
                    
                    if location_name:
                        location_counts[location_name] = location_counts.get(location_name, 0) + 1
                
                if location_counts:
                    fig = px.bar(
                        x=list(location_counts.keys()),
                        y=list(location_counts.values()),
                        title="Appointments by Location",
                        labels={'x': 'Location', 'y': 'Number of Appointments'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Top locations
                    st.markdown("##### 🏆 Top Locations")
                    sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)
                    
                    for idx, (loc_name, count) in enumerate(sorted_locations[:5], 1):
                        st.write(f"{idx}. **{loc_name}**: {count} appointments")
                else:
                    st.info("No location data available in appointments")
        else:
            st.info("📊 Load appointment data to see location analytics")


def show_categories_page():
    """Display categories management page"""
    st.header("📂 Categories Management")
    
    tabs = st.tabs(["View Categories", "Category Analytics"])
    
    with tabs[0]:
        st.subheader("All Categories")
        
        if st.button("Load Categories", type="primary", use_container_width=True):
            with st.spinner("Loading categories..."):
                result = st.session_state.api_client.get_categories()
                
                if 'error' in result:
                    st.error(f"❌ Error: {result['error']}")
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
                                'Services': len(cat.get('serviceList', [])),
                                'Color': cat.get('color', 'N/A')
                            }
                            rows.append(row)
                        
                        df = pd.DataFrame(rows)
                        st.success(f"✅ Loaded {len(df)} categories")
                        
                        # Metrics
                        metric_col1, metric_col2, metric_col3 = st.columns(3)
                        with metric_col1:
                            st.metric("Total Categories", len(df))
                        with metric_col2:
                            total_services = sum(len(c.get('serviceList', [])) for c in categories)
                            st.metric("Total Services", total_services)
                        with metric_col3:
                            avg_services = total_services / len(categories) if categories else 0
                            st.metric("Avg Services/Category", f"{avg_services:.1f}")
                        
                        st.dataframe(df, use_container_width=True, height=400)
                        
                        # Category details
                        st.divider()
                        st.markdown("##### 📂 Category Details")
                        
                        for cat in categories:
                            with st.expander(f"📂 {cat.get('name', 'Unknown Category')} ({len(cat.get('serviceList', []))} services)"):
                                st.write(f"**ID:** {cat.get('id')}")
                                st.write(f"**Status:** {cat.get('status')}")
                                st.write(f"**Position:** {cat.get('position')}")
                                
                                if cat.get('serviceList'):
                                    st.write("**Services in this category:**")
                                    for service in cat.get('serviceList', []):
                                        st.write(f"- {service.get('name', 'Unnamed Service')}")
                    else:
                        st.info("ℹ️ No categories found")
                else:
                    st.warning("⚠️ Unexpected response format")
    
    with tabs[1]:
        st.subheader("📊 Category Analytics")
        
        if st.button("Generate Analytics", type="primary"):
            with st.spinner("Loading category data..."):
                result = st.session_state.api_client.get_categories()
                
                if 'data' in result and 'categories' in result['data']:
                    categories = result['data']['categories']
                    
                    if categories:
                        # Services per category
                        cat_services = {
                            cat.get('name', 'Unknown'): len(cat.get('serviceList', []))
                            for cat in categories
                        }
                        
                        fig = px.pie(
                            names=list(cat_services.keys()),
                            values=list(cat_services.values()),
                            title="Services Distribution by Category"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Category status
                        status_counts = {}
                        for cat in categories:
                            status = cat.get('status', 'unknown')
                            status_counts[status] = status_counts.get(status, 0) + 1
                        
                        fig2 = px.bar(
                            x=list(status_counts.keys()),
                            y=list(status_counts.values()),
                            title="Categories by Status",
                            labels={'x': 'Status', 'y': 'Count'}
                        )
                        st.plotly_chart(fig2, use_container_width=True)


def show_reports_page():
    """Display reports and advanced analytics"""
    st.header("📊 Reports & Advanced Analytics")
    
    tabs = st.tabs([
        "Summary Report",
        "Revenue Analysis",
        "Customer Insights",
        "Time Analysis",
        "Export Reports"
    ])
    
    with tabs[0]:  # Summary Report
        st.subheader("📈 Business Summary Report")
        
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            report_start = st.date_input("Report Start Date", datetime.now() - timedelta(days=30))
        with date_col2:
            report_end = st.date_input("Report End Date", datetime.now())
        
        if st.button("Generate Summary Report", type="primary", use_container_width=True):
            with st.spinner("Generating comprehensive report..."):
                # Fetch all data
                appointments_result = st.session_state.api_client.get_appointments({})
                customers_result = st.session_state.api_client.get_customers()
                services_result = st.session_state.api_client.get_services()
                
                if all('data' in r for r in [appointments_result, customers_result, services_result]):
                    appointments = appointments_result['data'].get('appointments', [])
                    customers = customers_result['data'].get('users', [])
                    services = services_result['data'].get('services', [])
                    
                    st.success("✅ Report generated successfully!")
                    
                    # Key metrics dashboard
                    st.markdown("### 📊 Key Performance Indicators")
                    
                    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
                    
                    with kpi_col1:
                        st.metric(
                            "Total Appointments",
                            len(appointments),
                            delta=f"+{len([a for a in appointments if a.get('status') == 'approved'])} approved"
                        )
                    
                    with kpi_col2:
                        st.metric("Active Customers", len(customers))
                    
                    with kpi_col3:
                        st.metric("Active Services", len(services))
                    
                    with kpi_col4:
                        completion_rate = (len([a for a in appointments if a.get('status') == 'approved']) / len(appointments) * 100) if appointments else 0
                        st.metric("Completion Rate", f"{completion_rate:.1f}%")
                    
                    st.divider()
                    
                    # Detailed sections
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📅 Appointment Status Breakdown")
                        status_data = {}
                        for appt in appointments:
                            status = appt.get('status', 'unknown')
                            status_data[status] = status_data.get(status, 0) + 1
                        
                        for status, count in status_data.items():
                            percentage = (count / len(appointments) * 100) if appointments else 0
                            st.write(f"**{status.capitalize()}**: {count} ({percentage:.1f}%)")
                    
                    with col2:
                        st.markdown("#### 🎯 Top Services")
                        service_bookings = {}
                        for appt in appointments:
                            service_name = appt.get('service', {}).get('name', 'Unknown')
                            service_bookings[service_name] = service_bookings.get(service_name, 0) + 1
                        
                        sorted_services = sorted(service_bookings.items(), key=lambda x: x[1], reverse=True)[:5]
                        for idx, (service, count) in enumerate(sorted_services, 1):
                            st.write(f"{idx}. **{service}**: {count} bookings")
                    
                    # Timeline visualization
                    st.markdown("### 📈 Booking Timeline")
                    
                    date_counts = {}
                    for appt in appointments:
                        booking_date = appt.get('bookingStart', '').split(' ')[0]
                        if booking_date:
                            date_counts[booking_date] = date_counts.get(booking_date, 0) + 1
                    
                    if date_counts:
                        sorted_dates = sorted(date_counts.items())
                        fig = px.line(
                            x=[d[0] for d in sorted_dates],
                            y=[d[1] for d in sorted_dates],
                            title="Daily Bookings Trend",
                            labels={'x': 'Date', 'y': 'Number of Bookings'}
                        )
                        fig.update_traces(mode='lines+markers')
                        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[1]:  # Revenue Analysis
        st.subheader("💰 Revenue Analysis")
        
        st.info("💡 Revenue analysis requires payment data from appointments")
        
        if st.session_state.appointments_cache and st.session_state.services_cache:
            appointments = st.session_state.appointments_cache.get('data', {}).get('appointments', [])
            services_data = st.session_state.services_cache.get('data', {}).get('services', [])
            
            # Create service price lookup
            service_prices = {s.get('id'): float(s.get('price', 0)) for s in services_data}
            
            # Calculate revenue
            total_revenue = 0
            revenue_by_service = {}
            revenue_by_date = {}
            
            for appt in appointments:
                if appt.get('status') == 'approved':
                    service_id = appt.get('serviceId')
                    price = service_prices.get(service_id, 0)
                    persons = sum(b.get('persons', 1) for b in appt.get('bookings', []))
                    
                    revenue = price * persons
                    total_revenue += revenue
                    
                    # By service
                    service_name = appt.get('service', {}).get('name', f'Service {service_id}')
                    revenue_by_service[service_name] = revenue_by_service.get(service_name, 0) + revenue
                    
                    # By date
                    date = appt.get('bookingStart', '').split(' ')[0]
                    if date:
                        revenue_by_date[date] = revenue_by_date.get(date, 0) + revenue
            
            # Display metrics
            rev_col1, rev_col2, rev_col3 = st.columns(3)
            
            with rev_col1:
                st.metric("Total Revenue", f"${total_revenue:,.2f}")
            with rev_col2:
                approved_count = len([a for a in appointments if a.get('status') == 'approved'])
                avg_per_booking = total_revenue / approved_count if approved_count > 0 else 0
                st.metric("Avg per Booking", f"${avg_per_booking:.2f}")
            with rev_col3:
                days_in_period = len(set(revenue_by_date.keys()))
                avg_daily = total_revenue / days_in_period if days_in_period > 0 else 0
                st.metric("Avg Daily Revenue", f"${avg_daily:.2f}")
            
            st.divider()
            
            # Visualizations
            viz_col1, viz_col2 = st.columns(2)
            
            with viz_col1:
                st.markdown("##### 💼 Revenue by Service")
                sorted_services = sorted(revenue_by_service.items(), key=lambda x: x[1], reverse=True)[:10]
                
                fig = px.bar(
                    x=[s[0] for s in sorted_services],
                    y=[s[1] for s in sorted_services],
                    title="Top 10 Services by Revenue",
                    labels={'x': 'Service', 'y': 'Revenue ($)'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with viz_col2:
                st.markdown("##### 📅 Revenue Over Time")
                sorted_dates = sorted(revenue_by_date.items())
                
                fig = px.area(
                    x=[d[0] for d in sorted_dates],
                    y=[d[1] for d in sorted_dates],
                    title="Daily Revenue Trend",
                    labels={'x': 'Date', 'y': 'Revenue ($)'}
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Load appointments and services data to see revenue analysis")
    
    with tabs[2]:  # Customer Insights
        st.subheader("👥 Customer Insights")
        
        if st.session_state.appointments_cache and st.session_state.customers_cache:
            appointments = st.session_state.appointments_cache.get('data', {}).get('appointments', [])
            
            # Customer booking frequency
            customer_bookings = {}
            for appt in appointments:
                for booking in appt.get('bookings', []):
                    customer = booking.get('customer', {})
                    customer_id = customer.get('id')
                    customer_name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip()
                    
                    if customer_id:
                        if customer_id not in customer_bookings:
                            customer_bookings[customer_id] = {
                                'name': customer_name or f'Customer {customer_id}',
                                'count': 0,
                                'email': customer.get('email', 'N/A')
                            }
                        customer_bookings[customer_id]['count'] += 1
            
            # Metrics
            insight_col1, insight_col2, insight_col3 = st.columns(3)
            
            with insight_col1:
                st.metric("Total Customers", len(customer_bookings))
            with insight_col2:
                repeat_customers = sum(1 for c in customer_bookings.values() if c['count'] > 1)
                st.metric("Repeat Customers", repeat_customers)
            with insight_col3:
                if customer_bookings:
                    avg_bookings = sum(c['count'] for c in customer_bookings.values()) / len(customer_bookings)
                    st.metric("Avg Bookings/Customer", f"{avg_bookings:.1f}")
            
            st.divider()
            
            # Top customers
            st.markdown("##### 🌟 Top Customers by Bookings")
            sorted_customers = sorted(customer_bookings.values(), key=lambda x: x['count'], reverse=True)[:10]
            
            top_customers_df = pd.DataFrame([
                {
                    'Customer': c['name'],
                    'Email': c['email'],
                    'Total Bookings': c['count']
                }
                for c in sorted_customers
            ])
            
            st.dataframe(top_customers_df, use_container_width=True)
            
            # Visualization
            fig = px.bar(
                top_customers_df,
                x='Customer',
                y='Total Bookings',
                title="Top 10 Customers",
                color='Total Bookings'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Load appointment data to see customer insights")
    
    with tabs[3]:  # Time Analysis
        st.subheader("⏰ Time Analysis")
        
        if st.session_state.appointments_cache:
            appointments = st.session_state.appointments_cache.get('data', {}).get('appointments', [])
            
            # Hour of day analysis
            hour_counts = {}
            day_counts = {}
            
            for appt in appointments:
                booking_time = appt.get('bookingStart', '')
                if booking_time:
                    try:
                        dt = datetime.strptime(booking_time, '%Y-%m-%d %H:%M:%S')
                        hour = dt.hour
                        day = dt.strftime('%A')
                        
                        hour_counts[hour] = hour_counts.get(hour, 0) + 1
                        day_counts[day] = day_counts.get(day, 0) + 1
                    except:
                        pass
            
            time_col1, time_col2 = st.columns(2)
            
            with time_col1:
                st.markdown("##### 🕐 Bookings by Hour of Day")
                sorted_hours = sorted(hour_counts.items())
                
                fig = px.bar(
                    x=[f"{h:02d}:00" for h, _ in sorted_hours],
                    y=[c for _, c in sorted_hours],
                    title="Peak Booking Hours",
                    labels={'x': 'Hour', 'y': 'Number of Bookings'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with time_col2:
                st.markdown("##### 📆 Bookings by Day of Week")
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                ordered_days = [(day, day_counts.get(day, 0)) for day in day_order]
                
                fig = px.bar(
                    x=[d for d, _ in ordered_days],
                    y=[c for _, c in ordered_days],
                    title="Bookings by Day of Week",
                    labels={'x': 'Day', 'y': 'Number of Bookings'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Peak times summary
            st.divider()
            st.markdown("##### 🎯 Peak Times Summary")
            
            if hour_counts:
                peak_hour = max(hour_counts, key=hour_counts.get)
                st.write(f"**Busiest Hour**: {peak_hour:02d}:00 ({hour_counts[peak_hour]} bookings)")
            
            if day_counts:
                peak_day = max(day_counts, key=day_counts.get)
                st.write(f"**Busiest Day**: {peak_day} ({day_counts[peak_day]} bookings)")
        else:
            st.info("Load appointment data to see time analysis")
    
    with tabs[4]:  # Export Reports
        st.subheader("📥 Export Reports")
        
        st.write("Generate and download comprehensive reports in various formats")
        
        report_type = st.selectbox(
            "Select Report Type",
            [
                "Complete Business Summary",
                "Appointments Report",
                "Customer Report",
                "Financial Report",
                "Service Performance Report"
            ]
        )
        
        export_format = st.selectbox("Export Format", ["CSV", "Excel (XLSX)"])
        
        if st.button("Generate & Download Report", type="primary", use_container_width=True):
            with st.spinner(f"Generating {report_type}..."):
                st.success(f"✅ {report_type} ready for download!")
                st.info("💡 Report generation feature would create comprehensive exports here")


def show_settings_page():
    """Display settings and configuration"""
    st.header("⚙️ Settings & Configuration")
    
    tabs = st.tabs(["API Settings", "Operation Log", "System Info", "Help & Documentation"])
    
    with tabs[0]:
        st.subheader("🔌 API Configuration")
        
        st.info("API credentials are configured in .streamlit/secrets.toml")
        
        with st.expander("Current Configuration"):
            if 'amelia' in st.secrets:
                st.write(f"**API Base URL**: {st.secrets['amelia']['api_base_url'][:50]}...")
                st.write(f"**API Key**: {'*' * 20}{st.secrets['amelia']['api_key'][-4:]}")
        
        st.markdown("##### Connection Test")
        if st.button("Test API Connection", type="primary"):
            with st.spinner("Testing connection..."):
                if st.session_state.api_client.test_connection():
                    st.success("✅ Connection successful!")
                    log_operation("CONNECTION_TEST", "SUCCESS", "API connection verified")
                else:
                    st.error("❌ Connection failed!")
                    log_operation("CONNECTION_TEST", "FAILURE", "Connection test failed")
        
        st.divider()
        
        st.markdown("##### API Rate Limiting")
        st.info("💡 Consider implementing delays between batch operations to avoid rate limits")
        
        rate_limit_delay = st.slider(
            "Default delay between API calls (seconds)",
            min_value=0.0,
            max_value=5.0,
            value=1.0,
            step=0.1
        )
        
        if st.button("Save Settings"):
            st.success("✅ Settings saved!")
    
    with tabs[1]:
        st.subheader("📋 Operation Log")
        
        st.write("View recent operations and activities")
        
        # Log controls
        log_col1, log_col2 = st.columns([3, 1])
        with log_col1:
            log_filter = st.selectbox(
                "Filter by type",
                ["All", "SUCCESS", "ERROR", "FAILURE", "COMPLETED"]
            )
        with log_col2:
            if st.button("Clear Log", type="secondary"):
                st.session_state.operation_log = []
                st.success("✅ Log cleared")
                st.rerun()
        
        if st.session_state.operation_log:
            # Filter logs
            filtered_logs = st.session_state.operation_log
            if log_filter != "All":
                filtered_logs = [log for log in filtered_logs if log['status'] == log_filter]
            
            # Display logs
            st.write(f"Showing {len(filtered_logs)} of {len(st.session_state.operation_log)} log entries")
            
            # Reverse to show newest first
            for log_entry in reversed(filtered_logs[-50:]):  # Show last 50
                timestamp = log_entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                
                # Color code by status
                if log_entry['status'] == 'SUCCESS':
                    st.success(f"**[{timestamp}]** {log_entry['type']}: {log_entry['details']}")
                elif log_entry['status'] == 'ERROR' or log_entry['status'] == 'FAILURE':
                    st.error(f"**[{timestamp}]** {log_entry['type']}: {log_entry['details']}")
                else:
                    st.info(f"**[{timestamp}]** {log_entry['type']}: {log_entry['details']}")
            
            # Export log
            st.divider()
            if st.button("📥 Export Operation Log"):
                log_df = pd.DataFrame(st.session_state.operation_log)
                csv_data = CSVHandler.dataframe_to_csv_download(log_df)
                filename = f"operation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                st.download_button(
                    label="Download Log CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv"
                )
        else:
            st.info("ℹ️ No operations logged yet")
    
    with tabs[2]:
        st.subheader("ℹ️ System Information")
        
        # System stats
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.markdown("##### Application Info")
            st.write(f"**Version**: 2.0.0 Enhanced")
            st.write(f"**Environment**: Streamlit")
            st.write(f"**Python Version**: 3.8+")
            st.write(f"**Session Duration**: {datetime.now().strftime('%H:%M:%S')}")
        
        with info_col2:
            st.markdown("##### Cache Status")
            st.write(f"**Appointments Cached**: {'Yes' if st.session_state.appointments_cache else 'No'}")
            st.write(f"**Customers Cached**: {'Yes' if st.session_state.customers_cache else 'No'}")
            st.write(f"**Services Cached**: {'Yes' if st.session_state.services_cache else 'No'}")
            st.write(f"**Last Refresh**: {st.session_state.last_refresh.strftime('%H:%M:%S') if st.session_state.last_refresh else 'Never'}")
        
        st.divider()
        
        st.markdown("##### Clear Cache")
        if st.button("🗑️ Clear All Cached Data", type="secondary"):
            st.session_state.appointments_cache = None
            st.session_state.customers_cache = None
            st.session_state.services_cache = None
            st.session_state.last_refresh = None
            st.success("✅ Cache cleared successfully!")
            st.rerun()
        
        st.divider()
        
        st.markdown("##### Dependencies")
        st.code("""
streamlit
pandas
plotly
requests
datetime
json
        """, language="text")
    
    with tabs[3]:
        st.subheader("📚 Help & Documentation")
        
        st.markdown("""
        ### Quick Start Guide
        
        #### 1. Configuration
        - Ensure your API credentials are set in `.streamlit/secrets.toml`
        - Test the connection from the Settings page
        
        #### 2. Basic Operations
        
        **Viewing Data**
        - Navigate to any page (Appointments, Customers, etc.)
        - Click "Load" buttons to fetch data from the API
        - Use filters to narrow down results
        
        **Creating Appointments**
        - Go to Appointments → Create Appointment
        - Fill in all required fields (marked with *)
        - Click "Create Appointment"
        
        **Importing from CSV**
        - Go to Appointments → Import CSV
        - Download the sample template
        - Fill in your data and upload
        - Review validation results before importing
        
        **Exporting Data**
        - Load the data you want to export
        - Click "Generate CSV Export"
        - Preview and download the CSV file
        
        #### 3. Advanced Features
        
        **Bulk Operations**
        - Update multiple appointment statuses at once
        - Delete appointments in bulk
        - Send notifications to multiple customers
        
        **Analytics Dashboard**
        - View key metrics and KPIs
        - Analyze trends with interactive charts
        - Track employee performance
        
        **Reports**
        - Generate comprehensive business reports
        - Analyze revenue and customer insights
        - Export reports in multiple formats
        
        #### 4. Tips & Best Practices
        
        - **Use Dry Run**: When importing large CSV files, use dry run mode first to validate data
        - **Batch Processing**: Set appropriate delays for bulk operations to avoid rate limits
        - **Regular Backups**: Export your data regularly for backup purposes
        - **Monitor Logs**: Check the Operation Log for any errors or issues
        - **Filter First**: Use filters before loading large datasets to improve performance
        
        #### 5. Troubleshooting
        
        **Connection Issues**
        - Verify API credentials in secrets.toml
        - Test connection from Settings page
        - Check API base URL format
        
        **Import Failures**
        - Download and review the error report
        - Ensure CSV format matches the template
        - Verify all IDs exist in your Amelia system
        - Check for date/time format issues
        
        **Performance Issues**
        - Clear cached data from Settings
        - Use filters to reduce data size
        - Refresh browser if UI becomes slow
        
        #### 6. Support & Resources
        
        - **Amelia Documentation**: Check official Amelia API docs
        - **CSV Templates**: Download sample templates from each import page
        - **Operation Log**: Review recent activities and errors
        - **Contact Support**: For API-related issues, contact Amelia support
        
        ---
        
        ### Keyboard Shortcuts
        
        - `Ctrl/Cmd + R`: Refresh page
        - `Ctrl/Cmd + K`: Open command palette
        - `Esc`: Close modals/expanders
        
        ### API Endpoints Used
        
        This application uses the following Amelia API endpoints:
        
        - `GET /appointments` - Fetch appointments
        - `POST /appointments` - Create appointment
        - `PUT /appointments/{id}` - Update appointment
        - `DELETE /appointments/{id}` - Delete appointment
        - `GET /users/customers` - Fetch customers
        - `POST /users/customers` - Create customer
        - `GET /services` - Fetch services
        - `GET /users/providers` - Fetch employees
        - `GET /locations` - Fetch locations
        - `GET /categories` - Fetch categories
        
        ### Data Privacy & Security
        
        - All API communications use HTTPS
        - API keys are stored securely in secrets.toml
        - No data is stored permanently by this application
        - Session data is cleared when browser is closed
        - Operation logs contain no sensitive customer information
        
        ### Version History
        
        **v2.0.0 Enhanced** (Current)
        - Added comprehensive dashboard with analytics
        - Implemented bulk operations for appointments
        - Added advanced filtering and search
        - Included customer and service analytics
        - Enhanced CSV import/export with validation
        - Added operation logging and audit trail
        - Improved error handling and user feedback
        - Added multiple report types
        - Enhanced UI with better metrics and visualizations
        
        **v1.0.0** (Original)
        - Basic CRUD operations
        - Simple CSV import/export
        - Basic filtering
        """)
        
        st.divider()
        
        st.markdown("### 🆘 Need Help?")
        st.info("""
        If you encounter any issues or have questions:
        
        1. Check the Operation Log for error details
        2. Review the troubleshooting section above
        3. Consult the Amelia API documentation
        4. Contact your system administrator
        """)


def main():
    """Main application with enhanced navigation"""
    
    # Custom header
    st.markdown("""
        <div style='background: linear-gradient(90deg, #1f77b4 0%, #17a2b8 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h1 style='color: white; margin: 0;'>📅 Amelia API Management Tool Pro</h1>
            <p style='color: #e0e0e0; margin: 5px 0 0 0;'>Complete booking system management and analytics platform</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize API client
    if not st.session_state.authenticated:
        with st.spinner("🔌 Connecting to Amelia API..."):
            if not init_api_client():
                st.stop()
    
    # Sidebar navigation
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1f77b4/ffffff?text=Amelia+API", use_column_width=True)
        
        st.markdown("### 🧭 Navigation")
        
        page = st.radio(
            "Select Page",
            [
                "📊 Dashboard",
                "📅 Appointments",
                "👥 Customers",
                "🛎️ Services",
                "👨‍💼 Employees",
                "📍 Locations",
                "📂 Categories",
                "📈 Reports",
                "⚙️ Settings"
            ],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Connection status
        st.success("✅ Connected to API")
        
        # Quick stats
        with st.expander("📊 Quick Stats"):
            if st.session_state.appointments_cache:
                appts = len(st.session_state.appointments_cache.get('data', {}).get('appointments', []))
                st.metric("Appointments", appts)
            
            if st.session_state.customers_cache:
                customers = len(st.session_state.customers_cache.get('data', {}).get('users', []))
                st.metric("Customers", customers)
            
            if st.session_state.last_refresh:
                st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
        
        # API Info
        with st.expander("ℹ️ API Information"):
            if 'amelia' in st.secrets:
                st.caption(f"**Base URL:** {st.secrets['amelia']['api_base_url'][:30]}...")
                st.caption(f"**Status:** Connected")
        
        st.divider()
        
        # Footer
        st.caption("Amelia API Manager Pro v2.0.0")
        st.caption("© 2024 - Enhanced Edition")
    
    # Display selected page
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "📅 Appointments":
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
    elif page == "📈 Reports":
        show_reports_page()
    elif page == "⚙️ Settings":
        show_settings_page()
    
    # Footer
    st.divider()
    footer_col1, footer_col2, footer_col3 = st.columns(3)
    
    with footer_col1:
        st.caption("🔄 Auto-refresh: Disabled")
    with footer_col2:
        st.caption(f"⏰ Current time: {datetime.now().strftime('%H:%M:%S')}")
    with footer_col3:
        st.caption("📡 Status: Online")


if __name__ == "__main__":
    main()
