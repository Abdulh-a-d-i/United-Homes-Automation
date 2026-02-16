"""
Test script for the new Retell-compatible endpoints
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_check_availability():
    """Test the check-technician-availability endpoint"""
    print("=" * 60)
    print("Testing /check-technician-availability endpoint")
    print("=" * 60)
    
    payload = {
        "requested_time": "2026-02-14T09:00:00Z",
        "service_type": "Gutter Cleaning & Repair",
        "confirmed_address": "123 Main St, Charlotte, NC 28202"
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/check-technician-availability",
            json=payload
        )
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("available"):
                print(f"\n✅ SUCCESS: Found technician ID {data['technician_id']} ({data['technician_name']})")
                return data['technician_id']
            else:
                print(f"\n⚠️  {data.get('message')}")
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")
    
    return None


def test_book_appointment(technician_id):
    """Test the book-appointment endpoint with the technician ID"""
    print("\n" + "=" * 60)
    print("Testing /book-appointment endpoint")
    print("=" * 60)
    
    payload = {
        "customer_name": "John Doe",
        "customer_phone": "+19876543210",
        "customer_email": "johndoe@example.com",
        "technician_id": technician_id,
        "service_type": "Gutter Cleaning & Repair",
        "address": "123 Main St, Charlotte, NC 28202",
        "latitude": 35.2271,
        "longitude": -80.8431,
        "start_time": "2026-02-14T09:00:00Z",
        "duration_minutes": 60
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/book-appointment",
            json=payload
        )
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print(f"\n✅ SUCCESS: Appointment booked!")
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")


if __name__ == "__main__":
    # First, check availability and get technician ID
    tech_id = test_check_availability()
    
    if tech_id:
        # Then book with that technician ID
        test_book_appointment(tech_id)
    else:
        print("\n⚠️  Skipping booking test - no technician available")
