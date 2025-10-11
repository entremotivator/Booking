# Quick Start Guide

Get up and running with the Amelia API Tool in 5 minutes!

## Prerequisites

- Python 3.8+ installed
- Amelia WordPress plugin with API enabled
- Your Amelia API key

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Credentials

Edit `.streamlit/secrets.toml`:

```toml
[amelia]
api_base_url = "https://YOUR-DOMAIN.com/wp-admin/admin-ajax.php?action=wpamelia_api&call=/api/v1"
api_key = "YOUR-API-KEY"
```

**To get your API key:**
1. WordPress Admin → Amelia → Settings → Integrations
2. Enable API and copy the key

### 3. Test Connection

```bash
python test_api.py
```

Press Enter twice to use the configured credentials, or enter new ones.

### 4. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at http://localhost:8501

## Features Overview

### 📅 Appointments
- **View:** Filter by date and status
- **Create:** Add new appointments with all details
- **Export:** Download appointments as CSV
- **Import:** Bulk create from CSV file

### 👥 Customers
- View all customers
- Create new customer records
- Export customer data

### 🛎️ Services
- Browse service catalog
- View pricing and details
- Export services list

### Other Features
- Employees management
- Locations management
- Categories organization

## CSV Import Example

Create a CSV file with these columns:

```csv
booking_start,service_id,provider_id,customer_id,persons,status
2024-12-15 10:00,1,1,10,1,approved
2024-12-15 14:00,1,1,11,2,approved
```

**Required columns:**
- `booking_start` (YYYY-MM-DD HH:MM)
- `service_id` (number)
- `provider_id` (number)
- `customer_id` (number)

**Optional columns:**
- `location_id`, `persons`, `status`, `duration`, `internal_notes`

See `sample_appointments.csv` for a complete example.

## Common Issues

### "Invalid API key"
- Verify the key in WordPress Admin → Amelia → Settings → Integrations
- Ensure API is enabled
- Generate a new key if needed

### "403 Forbidden"
- Check your WordPress site is accessible
- Verify the URL format is correct
- Check server firewall settings

### "Module not found"
- Run: `pip install -r requirements.txt`
- Activate your virtual environment if using one

## Next Steps

1. **Explore the interface** - Navigate through all sections
2. **Export data** - Try exporting appointments to CSV
3. **Import test data** - Use the sample CSV to test imports
4. **Customize** - Modify the code to fit your needs

## Need Help?

See `SETUP_GUIDE.md` for detailed troubleshooting and configuration options.

## File Structure

```
amelia_api_tool/
├── app.py                    # Main Streamlit application
├── api_client.py             # API wrapper
├── csv_handler.py            # CSV import/export logic
├── test_api.py               # Connection test script
├── requirements.txt          # Python dependencies
├── sample_appointments.csv   # Example CSV file
├── README.md                 # Full documentation
├── SETUP_GUIDE.md           # Detailed setup instructions
├── QUICKSTART.md            # This file
└── .streamlit/
    ├── secrets.toml         # Your API credentials (DO NOT COMMIT)
    └── secrets.toml.example # Template for credentials
```

## Security Note

**Never commit `.streamlit/secrets.toml` to version control!**

The `.gitignore` file is already configured to exclude it.

