"""
Amelia API Client - Fixed Version
Handles all API communications with the Amelia booking system.
Proper HTTP methods and enhanced error handling.
"""

import requests
from typing import Dict, List, Optional, Any
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AmeliaAPIClient:
    """Client for interacting with Amelia API"""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the Amelia API client
        
        Args:
            base_url: Base URL for the API
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'Amelia': api_key
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """
        Make an HTTP request to the API with proper error handling
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.info(f"{method} {url}")
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, params=params, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, params=params, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=30)
            else:
                return {"error": f"Unsupported HTTP method: {method}", "success": False}
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            try:
                result = response.json()
                return result
            except json.JSONDecodeError:
                # If response is not JSON, return raw text
                return {"data": response.text, "success": True}
                
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get('message', error_msg)
            except:
                pass
            logger.error(error_msg)
            return {"error": error_msg, "success": False, "status_code": e.response.status_code}
            
        except requests.exceptions.ConnectionError as e:
            error_msg = "Connection Error: Unable to connect to API"
            logger.error(error_msg)
            return {"error": error_msg, "success": False}
            
        except requests.exceptions.Timeout as e:
            error_msg = "Timeout Error: Request took too long"
            logger.error(error_msg)
            return {"error": error_msg, "success": False}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request Error: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "success": False}
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            result = self.get_categories()
            return "error" not in result and "data" in result
        except:
            return False
    
    # Categories
    def get_categories(self) -> Dict:
        """Get all categories"""
        return self._make_request('GET', '/categories')
    
    def get_category(self, category_id: int) -> Dict:
        """Get a specific category"""
        return self._make_request('GET', f'/categories/{category_id}')
    
    def create_category(self, data: Dict) -> Dict:
        """Create a new category"""
        return self._make_request('POST', '/categories', data=data)
    
    def update_category(self, category_id: int, data: Dict) -> Dict:
        """Update a category"""
        return self._make_request('PUT', f'/categories/{category_id}', data=data)
    
    def delete_category(self, category_id: int) -> Dict:
        """Delete a category"""
        return self._make_request('DELETE', f'/categories/{category_id}')
    
    # Appointments
    def get_appointments(self, params: Optional[Dict] = None) -> Dict:
        """
        Get appointments with optional filters
        
        Args:
            params: Query parameters like dates, status, etc.
        """
        return self._make_request('GET', '/appointments', params=params)
    
    def get_appointment(self, appointment_id: int) -> Dict:
        """Get a specific appointment"""
        return self._make_request('GET', f'/appointments/{appointment_id}')
    
    def create_appointment(self, data: Dict) -> Dict:
        """
        Create a new appointment
        
        Example data format:
        {
            "bookingStart": "2024-12-15 10:00:00",
            "bookingEnd": "2024-12-15 11:00:00",
            "notifyParticipants": 1,
            "serviceId": 1,
            "providerId": 1,
            "locationId": 1,
            "internalNotes": "Notes here",
            "bookings": [
                {
                    "customerId": 1,
                    "persons": 1,
                    "status": "approved",
                    "customFields": {},
                    "extras": []
                }
            ]
        }
        """
        return self._make_request('POST', '/appointments', data=data)
    
    def update_appointment(self, appointment_id: int, data: Dict) -> Dict:
        """Update an appointment"""
        return self._make_request('PUT', f'/appointments/{appointment_id}', data=data)
    
    def delete_appointment(self, appointment_id: int) -> Dict:
        """Delete an appointment"""
        return self._make_request('DELETE', f'/appointments/{appointment_id}')
    
    def update_appointment_status(self, appointment_id: int, status: str, notify: bool = True) -> Dict:
        """
        Update appointment status
        
        Args:
            appointment_id: ID of the appointment
            status: New status (approved, pending, canceled, rejected)
            notify: Whether to send notification emails
        """
        data = {
            "status": status,
            "notifyParticipants": 1 if notify else 0
        }
        return self._make_request('PUT', f'/appointments/{appointment_id}/status', data=data)
    
    # Customers
    def get_customers(self, params: Optional[Dict] = None) -> Dict:
        """Get all customers"""
        return self._make_request('GET', '/users/customers', params=params)
    
    def get_customer(self, customer_id: int) -> Dict:
        """Get a specific customer"""
        return self._make_request('GET', f'/users/customers/{customer_id}')
    
    def create_customer(self, data: Dict) -> Dict:
        """
        Create a new customer
        
        Example data format:
        {
            "firstName": "John",
            "lastName": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "birthday": "1990-01-15",
            "gender": "male",
            "status": "visible",
            "note": "VIP customer"
        }
        """
        return self._make_request('POST', '/users/customers', data=data)
    
    def update_customer(self, customer_id: int, data: Dict) -> Dict:
        """Update a customer"""
        return self._make_request('PUT', f'/users/customers/{customer_id}', data=data)
    
    def delete_customer(self, customer_id: int) -> Dict:
        """Delete a customer"""
        return self._make_request('DELETE', f'/users/customers/{customer_id}')
    
    # Services
    def get_services(self) -> Dict:
        """Get all services"""
        return self._make_request('GET', '/services')
    
    def get_service(self, service_id: int) -> Dict:
        """Get a specific service"""
        return self._make_request('GET', f'/services/{service_id}')
    
    def create_service(self, data: Dict) -> Dict:
        """
        Create a new service
        
        Example data format:
        {
            "name": "Haircut",
            "description": "Professional haircut service",
            "color": "#1788FB",
            "price": 50,
            "status": "visible",
            "categoryId": 1,
            "duration": 3600,
            "timeBefore": 0,
            "timeAfter": 0,
            "bringingAnyone": 0,
            "maxCapacity": 1,
            "minCapacity": 1
        }
        """
        return self._make_request('POST', '/services', data=data)
    
    def update_service(self, service_id: int, data: Dict) -> Dict:
        """Update a service"""
        return self._make_request('PUT', f'/services/{service_id}', data=data)
    
    def delete_service(self, service_id: int) -> Dict:
        """Delete a service"""
        return self._make_request('DELETE', f'/services/{service_id}')
    
    # Employees (Providers)
    def get_employees(self, params: Optional[Dict] = None) -> Dict:
        """Get all employees/providers"""
        return self._make_request('GET', '/users/providers', params=params)
    
    def get_employee(self, employee_id: int) -> Dict:
        """Get a specific employee"""
        return self._make_request('GET', f'/users/providers/{employee_id}')
    
    def create_employee(self, data: Dict) -> Dict:
        """
        Create a new employee
        
        Example data format:
        {
            "firstName": "Jane",
            "lastName": "Smith",
            "email": "jane@example.com",
            "phone": "+1234567890",
            "note": "Senior stylist",
            "status": "visible",
            "externalId": "EMP001",
            "pictureFullPath": "",
            "picturethumbPath": "",
            "translations": null
        }
        """
        return self._make_request('POST', '/users/providers', data=data)
    
    def update_employee(self, employee_id: int, data: Dict) -> Dict:
        """Update an employee"""
        return self._make_request('PUT', f'/users/providers/{employee_id}', data=data)
    
    def delete_employee(self, employee_id: int) -> Dict:
        """Delete an employee"""
        return self._make_request('DELETE', f'/users/providers/{employee_id}')
    
    def get_employee_schedule(self, employee_id: int, params: Optional[Dict] = None) -> Dict:
        """
        Get employee schedule/working hours
        
        Args:
            employee_id: ID of the employee
            params: Optional filters (date range, etc.)
        """
        return self._make_request('GET', f'/users/providers/{employee_id}/schedule', params=params)
    
    def update_employee_schedule(self, employee_id: int, data: Dict) -> Dict:
        """
        Update employee working hours
        
        Example data format:
        {
            "weekDays": [
                {
                    "dayIndex": 1,
                    "startTime": "09:00:00",
                    "endTime": "17:00:00",
                    "breaks": [
                        {
                            "startTime": "12:00:00",
                            "endTime": "13:00:00"
                        }
                    ]
                }
            ]
        }
        """
        return self._make_request('PUT', f'/users/providers/{employee_id}/schedule', data=data)
    
    def get_employee_services(self, employee_id: int) -> Dict:
        """Get services assigned to an employee"""
        return self._make_request('GET', f'/users/providers/{employee_id}/services')
    
    def assign_employee_to_service(self, employee_id: int, service_id: int, data: Optional[Dict] = None) -> Dict:
        """
        Assign an employee to a service
        
        Args:
            employee_id: ID of the employee
            service_id: ID of the service
            data: Optional data (price override, custom capacity, etc.)
        """
        payload = data or {}
        return self._make_request('POST', f'/users/providers/{employee_id}/services/{service_id}', data=payload)
    
    def remove_employee_from_service(self, employee_id: int, service_id: int) -> Dict:
        """Remove an employee from a service"""
        return self._make_request('DELETE', f'/users/providers/{employee_id}/services/{service_id}')
    
    def get_employee_days_off(self, employee_id: int) -> Dict:
        """Get employee days off"""
        return self._make_request('GET', f'/users/providers/{employee_id}/days-off')
    
    def add_employee_day_off(self, employee_id: int, data: Dict) -> Dict:
        """
        Add a day off for employee
        
        Example data format:
        {
            "startDate": "2024-12-25",
            "endDate": "2024-12-26",
            "repeat": false,
            "name": "Christmas Holiday"
        }
        """
        return self._make_request('POST', f'/users/providers/{employee_id}/days-off', data=data)
    
    def delete_employee_day_off(self, employee_id: int, day_off_id: int) -> Dict:
        """Delete an employee day off"""
        return self._make_request('DELETE', f'/users/providers/{employee_id}/days-off/{day_off_id}')
    
    # Locations
    def get_locations(self) -> Dict:
        """Get all locations"""
        return self._make_request('GET', '/locations')
    
    def get_location(self, location_id: int) -> Dict:
        """Get a specific location"""
        return self._make_request('GET', f'/locations/{location_id}')
    
    def create_location(self, data: Dict) -> Dict:
        """
        Create a new location
        
        Example data format:
        {
            "name": "Main Office",
            "description": "Our main location",
            "address": "123 Main St",
            "phone": "+1234567890",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "pictureFullPath": "",
            "pictureThumbPath": "",
            "pin": "",
            "status": "visible",
            "translations": null
        }
        """
        return self._make_request('POST', '/locations', data=data)
    
    def update_location(self, location_id: int, data: Dict) -> Dict:
        """Update a location"""
        return self._make_request('PUT', f'/locations/{location_id}', data=data)
    
    def delete_location(self, location_id: int) -> Dict:
        """Delete a location"""
        return self._make_request('DELETE', f'/locations/{location_id}')
    
    # Extras
    def get_extras(self) -> Dict:
        """Get all extras"""
        return self._make_request('GET', '/extras')
    
    def get_extra(self, extra_id: int) -> Dict:
        """Get a specific extra"""
        return self._make_request('GET', f'/extras/{extra_id}')
    
    def create_extra(self, data: Dict) -> Dict:
        """Create a new extra"""
        return self._make_request('POST', '/extras', data=data)
    
    def update_extra(self, extra_id: int, data: Dict) -> Dict:
        """Update an extra"""
        return self._make_request('PUT', f'/extras/{extra_id}', data=data)
    
    def delete_extra(self, extra_id: int) -> Dict:
        """Delete an extra"""
        return self._make_request('DELETE', f'/extras/{extra_id}')
    
    # Coupons
    def get_coupons(self) -> Dict:
        """Get all coupons"""
        return self._make_request('GET', '/coupons')
    
    def get_coupon(self, coupon_id: int) -> Dict:
        """Get a specific coupon"""
        return self._make_request('GET', f'/coupons/{coupon_id}')
    
    def create_coupon(self, data: Dict) -> Dict:
        """Create a new coupon"""
        return self._make_request('POST', '/coupons', data=data)
    
    def update_coupon(self, coupon_id: int, data: Dict) -> Dict:
        """Update a coupon"""
        return self._make_request('PUT', f'/coupons/{coupon_id}', data=data)
    
    def delete_coupon(self, coupon_id: int) -> Dict:
        """Delete a coupon"""
        return self._make_request('DELETE', f'/coupons/{coupon_id}')
    
    # Custom Fields
    def get_custom_fields(self) -> Dict:
        """Get all custom fields"""
        return self._make_request('GET', '/fields')
    
    def get_custom_field(self, field_id: int) -> Dict:
        """Get a specific custom field"""
        return self._make_request('GET', f'/fields/{field_id}')
    
    def create_custom_field(self, data: Dict) -> Dict:
        """Create a new custom field"""
        return self._make_request('POST', '/fields', data=data)
    
    def update_custom_field(self, field_id: int, data: Dict) -> Dict:
        """Update a custom field"""
        return self._make_request('PUT', f'/fields/{field_id}', data=data)
    
    def delete_custom_field(self, field_id: int) -> Dict:
        """Delete a custom field"""
        return self._make_request('DELETE', f'/fields/{field_id}')
    
    # Notifications
    def send_notification(self, data: Dict) -> Dict:
        """
        Send custom notification
        
        Example data format:
        {
            "appointmentId": 123,
            "type": "email",
            "template": "appointment_reminder",
            "recipients": ["customer@example.com"]
        }
        """
        return self._make_request('POST', '/notifications/send', data=data)
    
    # Statistics and Reports
    def get_statistics(self, params: Optional[Dict] = None) -> Dict:
        """
        Get statistics
        
        Args:
            params: Optional filters (date range, type, etc.)
        """
        return self._make_request('GET', '/stats', params=params)
    
    def get_revenue_report(self, params: Optional[Dict] = None) -> Dict:
        """Get revenue report"""
        return self._make_request('GET', '/reports/revenue', params=params)
