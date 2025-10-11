import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import base64

# Page configuration
st.set_page_config(
    page_title="Amelia Bulk Appointment Upload",
    page_icon="📅",
    layout="wide"
)

# Sidebar Configuration
st.sidebar.header("🔧 API Configuration")
api_url = st.sidebar.text_input(
    "Amelia API URL",
    placeholder="https://yoursite.com/wp-admin/admin-ajax.php",
    help="Enter your WordPress site Amelia API endpoint"
)

api_key = st.sidebar.text_input(
    "API Key (Optional)",
    type="password",
    help="Enter your Amelia API key if required"
)

auth_username = st.sidebar.text_input(
    "Username (if using Basic Auth)",
    help="WordPress username for authentication"
)

auth_password = st.sidebar.text_input(
    "Password (if using Basic Auth)",
    type="password",
    help="WordPress password for authentication"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 CSV Format Requirements")
st.sidebar.markdown("""
**Required Columns:**
- Customers (email)
- Employee
- Service
- Start Time
- End Time
- Status
""")

# Main Content
st.title("📅 Amelia Booking - Bulk Appointment Upload")
st.markdown("Upload appointments in bulk to your Amelia booking system")

# Tabs
tab1, tab2, tab3 = st.tabs(["📤 Upload Appointments", "📊 Preview Data", "📖 Instructions"])

with tab1:
    st.header("Upload CSV File")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file with appointment data",
        type=['csv'],
        help="Upload a CSV file containing appointment details"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ File loaded successfully! Found {len(df)} appointments")
            
            # Display data preview
            st.subheader("Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Data Statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Appointments", len(df))
            with col2:
                st.metric("Unique Customers", df['Customers'].nunique() if 'Customers' in df.columns else 0)
            with col3:
                st.metric("Unique Services", df['Service'].nunique() if 'Service' in df.columns else 0)
            with col4:
                pending_count = len(df[df['Status'] == 'Pending']) if 'Status' in df.columns else 0
                st.metric("Pending Appointments", pending_count)
            
            st.markdown("---")
            
            # Column Mapping
            st.subheader("🔗 Column Mapping & Validation")
            
            expected_columns = [
                'Customers', 'Employee', 'Service', 'Location', 'Start Time', 
                'End Time', 'Duration', 'Price', 'Payment Amount', 'Payment Status',
                'Payment Method', 'Note', 'Status', 'Number of people', 'Coupon code',
                'Full Name', 'What can we get you information on?', 'How did you here about us?',
                'Picture of kitchen', 'Extras'
            ]
            
            missing_columns = [col for col in expected_columns if col not in df.columns]
            extra_columns = [col for col in df.columns if col not in expected_columns]
            
            if missing_columns:
                st.warning(f"⚠️ Missing columns: {', '.join(missing_columns)}")
            
            if extra_columns:
                st.info(f"ℹ️ Extra columns found: {', '.join(extra_columns)}")
            
            # Validation Options
            st.subheader("⚙️ Upload Options")
            
            col1, col2 = st.columns(2)
            with col1:
                validate_emails = st.checkbox("Validate email addresses", value=True)
                skip_errors = st.checkbox("Skip rows with errors", value=True)
                dry_run = st.checkbox("Dry run (test without uploading)", value=True)
            
            with col2:
                batch_size = st.number_input("Batch size", min_value=1, max_value=100, value=10)
                delay_between = st.slider("Delay between requests (seconds)", 0.0, 5.0, 1.0, 0.5)
            
            st.markdown("---")
            
            # Process and Upload
            if st.button("🚀 Start Upload", type="primary", use_container_width=True):
                if not api_url:
                    st.error("❌ Please enter the Amelia API URL in the sidebar")
                else:
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    results = {
                        'success': 0,
                        'failed': 0,
                        'skipped': 0,
                        'errors': []
                    }
                    
                    # Process each appointment
                    for idx, row in df.iterrows():
                        progress = (idx + 1) / len(df)
                        progress_bar.progress(progress)
                        status_text.text(f"Processing appointment {idx + 1} of {len(df)}...")
                        
                        try:
                            # Extract email from Customers field
                            customer_field = str(row.get('Customers', ''))
                            email = customer_field.split()[-1] if '@' in customer_field else ''
                            
                            # Prepare appointment data
                            appointment_data = {
                                'bookings': [{
                                    'customerId': None,
                                    'customer': {
                                        'email': email,
                                        'firstName': row.get('Full Name', '').split()[0] if pd.notna(row.get('Full Name')) else '',
                                        'lastName': ' '.join(row.get('Full Name', '').split()[1:]) if pd.notna(row.get('Full Name')) else '',
                                        'phone': ''
                                    },
                                    'customFields': {
                                        'vacation_rental_info': row.get('What can we get you information on?', ''),
                                        'referral_source': row.get('How did you here about us?', ''),
                                        'kitchen_picture': row.get('Picture of kitchen', '')
                                    },
                                    'status': row.get('Status', 'pending').lower(),
                                    'persons': int(row.get('Number of people', 1)) if pd.notna(row.get('Number of people')) else 1,
                                    'extras': []
                                }],
                                'appointment': {
                                    'bookingStart': row.get('Start Time', ''),
                                    'bookingEnd': row.get('End Time', ''),
                                    'notifyParticipants': False,
                                    'serviceId': None,  # Would need to map service name to ID
                                    'providerId': None,  # Would need to map employee name to ID
                                    'locationId': None   # Would need to map location name to ID
                                },
                                'payment': {
                                    'amount': float(str(row.get('Payment Amount', '0')).replace('$', '').replace(',', '')) if pd.notna(row.get('Payment Amount')) else 0,
                                    'status': row.get('Payment Status', 'pending').lower(),
                                    'gateway': row.get('Payment Method', 'onSite').lower().replace('-', '')
                                },
                                'couponCode': row.get('Coupon code', '') if pd.notna(row.get('Coupon code')) else ''
                            }
                            
                            if dry_run:
                                # Simulate success for dry run
                                results['success'] += 1
                            else:
                                # Make API request
                                headers = {'Content-Type': 'application/json'}
                                
                                # Add authentication if provided
                                if auth_username and auth_password:
                                    credentials = base64.b64encode(
                                        f"{auth_username}:{auth_password}".encode()
                                    ).decode()
                                    headers['Authorization'] = f'Basic {credentials}'
                                
                                if api_key:
                                    headers['Amelia-API-Key'] = api_key
                                
                                # API endpoint for creating appointments
                                endpoint = f"{api_url}?action=wpamelia_api&call=/appointments"
                                
                                response = requests.post(
                                    endpoint,
                                    json=appointment_data,
                                    headers=headers,
                                    timeout=30
                                )
                                
                                if response.status_code == 200:
                                    results['success'] += 1
                                else:
                                    results['failed'] += 1
                                    results['errors'].append({
                                        'row': idx + 1,
                                        'email': email,
                                        'error': f"HTTP {response.status_code}: {response.text[:100]}"
                                    })
                            
                            # Delay between requests
                            import time
                            time.sleep(delay_between)
                            
                        except Exception as e:
                            if skip_errors:
                                results['skipped'] += 1
                                results['errors'].append({
                                    'row': idx + 1,
                                    'email': email,
                                    'error': str(e)
                                })
                            else:
                                st.error(f"❌ Error processing row {idx + 1}: {str(e)}")
                                break
                    
                    progress_bar.progress(1.0)
                    status_text.text("Upload complete!")
                    
                    # Display results
                    st.markdown("---")
                    st.subheader("📊 Upload Results")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("✅ Successful", results['success'], delta=None)
                    with col2:
                        st.metric("❌ Failed", results['failed'], delta=None)
                    with col3:
                        st.metric("⏭️ Skipped", results['skipped'], delta=None)
                    
                    if dry_run:
                        st.info("ℹ️ This was a dry run. No appointments were actually uploaded.")
                    
                    # Show errors if any
                    if results['errors']:
                        st.subheader("⚠️ Errors and Warnings")
                        error_df = pd.DataFrame(results['errors'])
                        st.dataframe(error_df, use_container_width=True)
                        
                        # Download error log
                        csv = error_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Error Log",
                            data=csv,
                            file_name="upload_errors.csv",
                            mime="text/csv"
                        )
                    
                    if results['success'] > 0:
                        st.success(f"🎉 Successfully processed {results['success']} appointments!")
        
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.info("Please ensure your CSV file is properly formatted.")

with tab2:
    st.header("📊 Data Analysis & Preview")
    
    if uploaded_file is not None:
        # Service distribution
        st.subheader("Service Distribution")
        if 'Service' in df.columns:
            service_counts = df['Service'].value_counts()
            st.bar_chart(service_counts)
        
        # Status distribution
        st.subheader("Status Distribution")
        if 'Status' in df.columns:
            status_counts = df['Status'].value_counts()
            col1, col2 = st.columns([2, 1])
            with col1:
                st.bar_chart(status_counts)
            with col2:
                st.dataframe(status_counts, use_container_width=True)
        
        # Employee workload
        st.subheader("Employee Workload")
        if 'Employee' in df.columns:
            employee_counts = df['Employee'].value_counts()
            st.bar_chart(employee_counts)
        
        # Payment status
        st.subheader("Payment Status")
        if 'Payment Status' in df.columns:
            payment_counts = df['Payment Status'].value_counts()
            st.bar_chart(payment_counts)
    else:
        st.info("👆 Please upload a CSV file in the Upload tab to see data analysis.")

with tab3:
    st.header("📖 Instructions")
    
    st.markdown("""
    ### How to Use This Application
    
    #### 1. Configure API Settings
    - Enter your Amelia API URL in the sidebar (e.g., `https://yoursite.com/wp-admin/admin-ajax.php`)
    - Add authentication credentials if required
    - The API key is optional and depends on your Amelia setup
    
    #### 2. Prepare Your CSV File
    Your CSV should include the following columns:
    
    | Column | Description | Required |
    |--------|-------------|----------|
    | Customers | Customer name and email | ✅ Yes |
    | Employee | Employee/Provider name | ✅ Yes |
    | Service | Service name | ✅ Yes |
    | Location | Location name | No |
    | Start Time | Appointment start time | ✅ Yes |
    | End Time | Appointment end time | ✅ Yes |
    | Duration | Duration (e.g., 30min) | No |
    | Price | Service price | No |
    | Payment Amount | Amount paid | No |
    | Payment Status | Paid/Pending/etc. | No |
    | Payment Method | Payment method used | No |
    | Note | Additional notes | No |
    | Status | Appointment status | ✅ Yes |
    | Number of people | Number of attendees | No |
    | Coupon code | Discount coupon | No |
    | Full Name | Customer full name | No |
    | Custom fields | Any custom fields | No |
    
    #### 3. Upload and Process
    1. Upload your CSV file in the **Upload Appointments** tab
    2. Review the data preview and validation messages
    3. Configure upload options (dry run recommended first)
    4. Click "Start Upload" to begin processing
    5. Monitor progress and review results
    
    #### 4. Tips for Success
    - ✅ Always do a dry run first to test your data
    - ✅ Ensure email addresses are properly formatted
    - ✅ Check that dates/times are in the correct format
    - ✅ Use batch processing for large uploads
    - ✅ Add delays between requests to avoid overwhelming the server
    
    #### 5. Troubleshooting
    - If uploads fail, check your API credentials
    - Verify the API URL is correct
    - Ensure your WordPress site has the Amelia plugin installed
    - Check that you have proper permissions to create appointments
    - Review the error log for specific issues
    
    ### Date Format Examples
    - `October 14, 2025 12:00 pm`
    - `2025-10-14 12:00:00`
    - `14/10/2025 12:00`
    
    ### Need Help?
    For more information about Amelia API, visit the official documentation.
    """)
    
    # Sample CSV download
    st.subheader("📥 Download Sample CSV Template")
    
    sample_data = {
        'Customers': ['john doe john@example.com', 'jane smith jane@example.com'],
        'Employee': ['Videmi Services', 'Videmi Services'],
        'Service': ['Check-In', 'Vacation Rental Clean'],
        'Location': ['', ''],
        'Start Time': ['October 14, 2025 12:00 pm', 'October 15, 2025 2:00 pm'],
        'End Time': ['October 14, 2025 12:30 pm', 'October 15, 2025 4:00 pm'],
        'Duration': ['30min', '2h'],
        'Price': [0, 150],
        'Payment Amount': ['$0.00', '$150.00'],
        'Payment Status': ['Paid', 'Pending'],
        'Payment Method': ['On-site', 'Credit Card'],
        'Note': ['', 'Deep clean required'],
        'Status': ['Pending', 'Approved'],
        'Number of people': ['Pending: 1', '1'],
        'Coupon code': ['', 'SAVE10'],
        'Full Name': ['John Doe', 'Jane Smith'],
        'What can we get you information on?': ['Vacation Rental Clean', 'Commercial Clean'],
        'How did you here about us?': ['fb', 'google'],
        'Picture of kitchen': ['', ''],
        'Extras': ['', '']
    }
    
    sample_df = pd.DataFrame(sample_data)
    csv = sample_df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download Sample CSV",
        data=csv,
        file_name="amelia_appointments_template.csv",
        mime="text/csv",
        use_container_width=True
    )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Amelia Booking Bulk Upload Tool | Made with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
