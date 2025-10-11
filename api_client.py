"""
Amelia API Client
Handles all API communications with the Amelia booking system.
"""

import requests
from typing import Dict, List, Optional, Any
import json


class AmeliaAPIClient:
    """Client for interacting with Amelia API"""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the Amelia API client
        
        Args:
            base_url: Base URL for the API (e.g., https://example.com/wp-admin/admin-ajax.php?action=wpamelia_api&call=/api/v1)
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """
        Make an HTTP request to the API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Add API key to headers
        headers = self.headers.copy()
        headers['Amelia'] = self.api_key
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, params=params, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "success": False}
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            result = self.get_categories()
            return "error" not in result
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
        return self._make_request('POST', f'/categories/{category_id}', data=data)
    
    def delete_category(self, category_id: int) -> Dict:
        """Delete a category"""
        return self._make_request('POST', f'/categories/delete/{category_id}')
    
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
        """Create a new appointment"""
        return self._make_request('POST', '/appointments', data=data)
    
    def update_appointment(self, appointment_id: int, data: Dict) -> Dict:
        """Update an appointment"""
        return self._make_request('POST', f'/appointments/{appointment_id}', data=data)
    
    def delete_appointment(self, appointment_id: int) -> Dict:
        """Delete an appointment"""
        return self._make_request('POST', f'/appointments/delete/{appointment_id}')
    
    def update_appointment_status(self, appointment_id: int, status: str) -> Dict:
        """Update appointment status"""
        return self._make_request('POST', f'/appointments/status/{appointment_id}', data={"status": status})
    
    # Customers
    def get_customers(self, params: Optional[Dict] = None) -> Dict:
        """Get all customers"""
        return self._make_request('GET', '/users/customers', params=params)
    
    def get_customer(self, customer_id: int) -> Dict:
        """Get a specific customer"""
        return self._make_request('GET', f'/users/customers/{customer_id}')
    
    def create_customer(self, data: Dict) -> Dict:
        """Create a new customer"""
        return self._make_request('POST', '/users/customers', data=data)
    
    def update_customer(self, customer_id: int, data: Dict) -> Dict:
        """Update a customer"""
        return self._make_request('POST', f'/users/customers/{customer_id}', data=data)
    
    def delete_customer(self, customer_id: int) -> Dict:
        """Delete a customer"""
        return self._make_request('POST', f'/users/customers/delete/{customer_id}')
    
    # Services
    def get_services(self) -> Dict:
        """Get all services"""
        return self._make_request('GET', '/services')
    
    def get_service(self, service_id: int) -> Dict:
        """Get a specific service"""
        return self._make_request('GET', f'/services/{service_id}')
    
    def create_service(self, data: Dict) -> Dict:
        """Create a new service"""
        return self._make_request('POST', '/services', data=data)
    
    def update_service(self, service_id: int, data: Dict) -> Dict:
        """Update a service"""
        return self._make_request('POST', f'/services/{service_id}', data=data)
    
    def delete_service(self, service_id: int) -> Dict:
        """Delete a service"""
        return self._make_request('POST', f'/services/delete/{service_id}')
    
    # Employees
    def get_employees(self) -> Dict:
        """Get all employees"""
        return self._make_request('GET', '/users/providers')
    
    def get_employee(self, employee_id: int) -> Dict:
        """Get a specific employee"""
        return self._make_request('GET', f'/users/providers/{employee_id}')
    
    def create_employee(self, data: Dict) -> Dict:
        """Create a new employee"""
        return self._make_request('POST', '/users/providers', data=data)
    
    def update_employee(self, employee_id: int, data: Dict) -> Dict:
        """Update an employee"""
        return self._make_request('POST', f'/users/providers/{employee_id}', data=data)
    
    def delete_employee(self, employee_id: int) -> Dict:
        """Delete an employee"""
        return self._make_request('POST', f'/users/providers/delete/{employee_id}')
    
    # Locations
    def get_locations(self) -> Dict:
        """Get all locations"""
        return self._make_request('GET', '/locations')
    
    def get_location(self, location_id: int) -> Dict:
        """Get a specific location"""
        return self._make_request('GET', f'/locations/{location_id}')
    
    def create_location(self, data: Dict) -> Dict:
        """Create a new location"""
        return self._make_request('POST', '/locations', data=data)
    
    def update_location(self, location_id: int, data: Dict) -> Dict:
        """Update a location"""
        return self._make_request('POST', f'/locations/{location_id}', data=data)
    
    def delete_location(self, location_id: int) -> Dict:
        """Delete a location"""
        return self._make_request('POST', f'/locations/delete/{location_id}')
    
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
        return self._make_request('POST', f'/extras/{extra_id}', data=data)
    
    def delete_extra(self, extra_id: int) -> Dict:
        """Delete an extra"""
        return self._make_request('POST', f'/extras/delete/{extra_id}')
    
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
        return self._make_request('POST', f'/coupons/{coupon_id}', data=data)
    
    def delete_coupon(self, coupon_id: int) -> Dict:
        """Delete a coupon"""
        return self._make_request('POST', f'/coupons/delete/{coupon_id}')
    
    # Events
    def get_events(self, params: Optional[Dict] = None) -> Dict:
        """Get all events"""
        return self._make_request('GET', '/events', params=params)
    
    def get_event(self, event_id: int) -> Dict:
        """Get a specific event"""
        return self._make_request('GET', f'/events/{event_id}')
    
    def create_event(self, data: Dict) -> Dict:
        """Create a new event"""
        return self._make_request('POST', '/events', data=data)
    
    def update_event(self, event_id: int, data: Dict) -> Dict:
        """Update an event"""
        return self._make_request('POST', f'/events/{event_id}', data=data)
    
    def delete_event(self, event_id: int) -> Dict:
        """Delete an event"""
        return self._make_request('POST', f'/events/delete/{event_id}')
    
    # Packages
    def get_packages(self) -> Dict:
        """Get all packages"""
        return self._make_request('GET', '/packages')
    
    def get_package(self, package_id: int) -> Dict:
        """Get a specific package"""
        return self._make_request('GET', f'/packages/{package_id}')
    
    def create_package(self, data: Dict) -> Dict:
        """Create a new package"""
        return self._make_request('POST', '/packages', data=data)
    
    def update_package(self, package_id: int, data: Dict) -> Dict:
        """Update a package"""
        return self._make_request('POST', f'/packages/{package_id}', data=data)
    
    def delete_package(self, package_id: int) -> Dict:
        """Delete a package"""
        return self._make_request('POST', f'/packages/delete/{package_id}')
    
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
        return self._make_request('POST', f'/fields/{field_id}', data=data)
    
    def delete_custom_field(self, field_id: int) -> Dict:
        """Delete a custom field"""
        return self._make_request('POST', f'/fields/delete/{field_id}')

