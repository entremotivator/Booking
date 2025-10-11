"""
CSV Handler for Amelia API
Handles CSV import/export operations for appointments and other entities.
"""

import pandas as pd
import io
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class CSVHandler:
    """Handles CSV import and export operations"""
    
    @staticmethod
    def export_appointments_to_csv(appointments_data: Dict) -> pd.DataFrame:
        """
        Convert appointments API response to CSV-ready DataFrame
        
        Args:
            appointments_data: API response containing appointments
            
        Returns:
            DataFrame ready for CSV export
        """
        if 'data' not in appointments_data or 'appointments' not in appointments_data['data']:
            return pd.DataFrame()
        
        appointments = appointments_data['data']['appointments']
        rows = []
        
        for apt in appointments:
            # Extract booking information
            bookings = apt.get('bookings', [])
            
            if not bookings:
                # Appointment without bookings
                row = {
                    'appointment_id': apt.get('id'),
                    'booking_start': apt.get('bookingStart'),
                    'booking_end': apt.get('bookingEnd'),
                    'status': apt.get('status'),
                    'service_id': apt.get('serviceId'),
                    'provider_id': apt.get('providerId'),
                    'location_id': apt.get('locationId'),
                    'internal_notes': apt.get('internalNotes', ''),
                    'customer_id': None,
                    'customer_name': '',
                    'customer_email': '',
                    'customer_phone': '',
                    'persons': 0,
                    'price': 0,
                    'payment_status': '',
                    'payment_gateway': ''
                }
                rows.append(row)
            else:
                # Create a row for each booking
                for booking in bookings:
                    customer = booking.get('customer', {}) or {}
                    payments = booking.get('payments', [])
                    payment = payments[0] if payments else {}
                    
                    row = {
                        'appointment_id': apt.get('id'),
                        'booking_id': booking.get('id'),
                        'booking_start': apt.get('bookingStart'),
                        'booking_end': apt.get('bookingEnd'),
                        'status': apt.get('status'),
                        'booking_status': booking.get('status'),
                        'service_id': apt.get('serviceId'),
                        'provider_id': apt.get('providerId'),
                        'location_id': apt.get('locationId'),
                        'internal_notes': apt.get('internalNotes', ''),
                        'customer_id': booking.get('customerId'),
                        'customer_first_name': customer.get('firstName', ''),
                        'customer_last_name': customer.get('lastName', ''),
                        'customer_email': customer.get('email', ''),
                        'customer_phone': customer.get('phone', ''),
                        'persons': booking.get('persons', 1),
                        'price': booking.get('price', 0),
                        'payment_status': payment.get('status', ''),
                        'payment_gateway': payment.get('gateway', ''),
                        'payment_amount': payment.get('amount', 0),
                        'duration': booking.get('duration', apt.get('duration', 0)),
                        'custom_fields': booking.get('customFields', ''),
                        'token': booking.get('token', '')
                    }
                    rows.append(row)
        
        return pd.DataFrame(rows)
    
    @staticmethod
    def export_customers_to_csv(customers_data: Dict) -> pd.DataFrame:
        """
        Convert customers API response to CSV-ready DataFrame
        
        Args:
            customers_data: API response containing customers
            
        Returns:
            DataFrame ready for CSV export
        """
        if 'data' not in customers_data or 'users' not in customers_data['data']:
            return pd.DataFrame()
        
        customers = customers_data['data']['users']
        rows = []
        
        for customer in customers:
            row = {
                'id': customer.get('id'),
                'first_name': customer.get('firstName'),
                'last_name': customer.get('lastName'),
                'email': customer.get('email'),
                'phone': customer.get('phone'),
                'birthday': customer.get('birthday'),
                'gender': customer.get('gender'),
                'status': customer.get('status'),
                'note': customer.get('note'),
                'country_phone_iso': customer.get('countryPhoneIso'),
                'external_id': customer.get('externalId'),
                'total_appointments': customer.get('totalAppointments', 0)
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    @staticmethod
    def validate_appointment_csv(df: pd.DataFrame) -> tuple[bool, List[str]]:
        """
        Validate appointment CSV data
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        required_columns = ['booking_start', 'service_id', 'provider_id', 'customer_id']
        
        # Check required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        
        if errors:
            return False, errors
        
        # Validate data types and values
        for idx, row in df.iterrows():
            row_num = idx + 2  # +2 for header and 0-indexing
            
            # Check booking_start format
            try:
                pd.to_datetime(row['booking_start'])
            except:
                errors.append(f"Row {row_num}: Invalid date format in booking_start")
            
            # Check IDs are numeric
            for col in ['service_id', 'provider_id', 'customer_id']:
                if pd.notna(row.get(col)) and not str(row[col]).replace('.', '').isdigit():
                    errors.append(f"Row {row_num}: {col} must be numeric")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def csv_to_appointment_data(row: pd.Series) -> Dict:
        """
        Convert CSV row to Amelia API appointment format
        
        Args:
            row: DataFrame row
            
        Returns:
            Dictionary formatted for API
        """
        # Parse booking_start
        booking_start = pd.to_datetime(row['booking_start']).strftime('%Y-%m-%d %H:%M')
        
        # Build appointment data
        appointment_data = {
            'bookingStart': booking_start,
            'serviceId': int(row['service_id']),
            'providerId': int(row['provider_id']),
            'locationId': int(row.get('location_id', 0)) if pd.notna(row.get('location_id')) else None,
            'notifyParticipants': int(row.get('notify_participants', 1)),
            'internalNotes': str(row.get('internal_notes', '')),
            'bookings': [
                {
                    'customerId': int(row['customer_id']),
                    'persons': int(row.get('persons', 1)),
                    'status': str(row.get('status', 'approved')),
                    'extras': [],
                    'duration': int(row.get('duration', 0)) if pd.notna(row.get('duration')) else None,
                }
            ]
        }
        
        # Add optional fields
        if pd.notna(row.get('custom_fields')):
            try:
                custom_fields = json.loads(row['custom_fields']) if isinstance(row['custom_fields'], str) else row['custom_fields']
                appointment_data['bookings'][0]['customFields'] = custom_fields
            except:
                pass
        
        return appointment_data
    
    @staticmethod
    def export_services_to_csv(services_data: Dict) -> pd.DataFrame:
        """
        Convert services API response to CSV-ready DataFrame
        
        Args:
            services_data: API response containing services
            
        Returns:
            DataFrame ready for CSV export
        """
        if 'data' not in services_data or 'services' not in services_data['data']:
            return pd.DataFrame()
        
        services = services_data['data']['services']
        rows = []
        
        for service in services:
            row = {
                'id': service.get('id'),
                'name': service.get('name'),
                'description': service.get('description'),
                'category_id': service.get('categoryId'),
                'price': service.get('price'),
                'duration': service.get('duration'),
                'min_capacity': service.get('minCapacity'),
                'max_capacity': service.get('maxCapacity'),
                'status': service.get('status'),
                'color': service.get('color'),
                'deposit': service.get('deposit'),
                'deposit_payment': service.get('depositPayment'),
                'time_before': service.get('timeBefore'),
                'time_after': service.get('timeAfter')
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    @staticmethod
    def dataframe_to_csv_download(df: pd.DataFrame, filename: str = "export.csv") -> bytes:
        """
        Convert DataFrame to CSV bytes for download
        
        Args:
            df: DataFrame to convert
            filename: Suggested filename
            
        Returns:
            CSV data as bytes
        """
        return df.to_csv(index=False).encode('utf-8')

