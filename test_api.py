"""
Test script for Amelia API connectivity
Run this script to verify your API credentials are working correctly.
"""

from api_client import AmeliaAPIClient
import json
import sys

def test_api_connection():
    """Test API connection and basic operations"""
    
    print("=" * 60)
    print("Amelia API Connection Test")
    print("=" * 60)
    print()
    
    # Get credentials
    api_base = input("Enter API Base URL: ").strip()
    if not api_base:
        api_base = "https://videmiservices.com/wp-admin/admin-ajax.php?action=wpamelia_api&call=/api/v1"
        print(f"Using default: {api_base}")
    
    api_key = input("Enter API Key: ").strip()
    if not api_key:
        api_key = "n3B2dUCRbkE372m6jRXPwGHI9JGVLJ1f2xHVySWgK4VY"
        print(f"Using provided key")
    
    print()
    print("-" * 60)
    print("Testing connection...")
    print("-" * 60)
    
    # Initialize client
    client = AmeliaAPIClient(api_base, api_key)
    
    # Test 1: Categories
    print("\n1. Testing GET /categories...")
    result = client.get_categories()
    
    if 'error' in result:
        print(f"   ❌ FAILED: {result['error']}")
        print("\n   Possible issues:")
        print("   - API key is invalid or expired")
        print("   - API endpoint URL is incorrect")
        print("   - Server is blocking requests")
        print("   - Amelia plugin is not activated")
        return False
    elif 'data' in result and 'categories' in result['data']:
        categories = result['data']['categories']
        print(f"   ✓ SUCCESS: Found {len(categories)} categories")
        if categories:
            print(f"   Sample: {categories[0].get('name', 'N/A')}")
    else:
        print(f"   ⚠ UNEXPECTED RESPONSE:")
        print(f"   {json.dumps(result, indent=2)[:200]}...")
    
    # Test 2: Services
    print("\n2. Testing GET /services...")
    result = client.get_services()
    
    if 'error' in result:
        print(f"   ❌ FAILED: {result['error']}")
    elif 'data' in result and 'services' in result['data']:
        services = result['data']['services']
        print(f"   ✓ SUCCESS: Found {len(services)} services")
        if services:
            print(f"   Sample: {services[0].get('name', 'N/A')}")
    else:
        print(f"   ⚠ UNEXPECTED RESPONSE")
    
    # Test 3: Customers
    print("\n3. Testing GET /users/customers...")
    result = client.get_customers()
    
    if 'error' in result:
        print(f"   ❌ FAILED: {result['error']}")
    elif 'data' in result and 'users' in result['data']:
        customers = result['data']['users']
        print(f"   ✓ SUCCESS: Found {len(customers)} customers")
        if customers:
            customer = customers[0]
            print(f"   Sample: {customer.get('firstName', '')} {customer.get('lastName', '')}")
    else:
        print(f"   ⚠ UNEXPECTED RESPONSE")
    
    # Test 4: Appointments
    print("\n4. Testing GET /appointments...")
    result = client.get_appointments()
    
    if 'error' in result:
        print(f"   ❌ FAILED: {result['error']}")
    elif 'data' in result and 'appointments' in result['data']:
        appointments = result['data']['appointments']
        print(f"   ✓ SUCCESS: Found {len(appointments)} appointments")
        if appointments:
            apt = appointments[0]
            print(f"   Sample: Appointment #{apt.get('id')} - {apt.get('bookingStart', 'N/A')}")
    else:
        print(f"   ⚠ UNEXPECTED RESPONSE")
    
    print()
    print("=" * 60)
    print("✓ API Connection Test Complete!")
    print("=" * 60)
    print()
    print("If all tests passed, you can now run the Streamlit app:")
    print("  streamlit run app.py")
    print()
    
    return True


if __name__ == "__main__":
    try:
        test_api_connection()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

