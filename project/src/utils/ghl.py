# GHL INTEGRATION - COMMENTED OUT (No paid GHL API access)
# All GHL functions preserved below for reference.
# Replaced by direct Google/Outlook calendar integration.

# import os
# import requests
# from datetime import datetime, timedelta
# from dotenv import load_dotenv
#
# load_dotenv()
#
# GHL_BASE_URL = "https://services.leadconnectorhq.com"
#
#
# def create_or_update_contact(name, phone, email, custom_fields=None):
#     url = f"{GHL_BASE_URL}/contacts/"
#     headers = {
#         "Authorization": f"Bearer {os.getenv('GHL_API_KEY')}",
#         "Content-Type": "application/json"
#     }
#     search_url = f"{GHL_BASE_URL}/contacts/search"
#     search_params = {"phone": phone}
#     search_response = requests.get(search_url, headers=headers, params=search_params)
#     payload = {
#         "name": name,
#         "phone": phone,
#         "email": email
#     }
#     if custom_fields:
#         payload["customFields"] = custom_fields
#     if search_response.status_code == 200:
#         contacts = search_response.json().get("contacts", [])
#         if contacts:
#             contact_id = contacts[0]["id"]
#             update_url = f"{GHL_BASE_URL}/contacts/{contact_id}"
#             response = requests.put(update_url, headers=headers, json=payload)
#             if response.status_code == 200:
#                 return contact_id
#     response = requests.post(url, headers=headers, json=payload)
#     if response.status_code in [200, 201]:
#         return response.json().get("contact", {}).get("id")
#     return None
#
#
# def create_appointment(calendar_id, contact_id, title, start_time, end_time,
#                       address, notes=None, custom_fields=None):
#     url = f"{GHL_BASE_URL}/calendars/{calendar_id}/appointments"
#     headers = {
#         "Authorization": f"Bearer {os.getenv('GHL_API_KEY')}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "calendarId": calendar_id,
#         "contactId": contact_id,
#         "title": title,
#         "startTime": start_time.isoformat(),
#         "endTime": end_time.isoformat(),
#         "address": address
#     }
#     if notes:
#         payload["notes"] = notes
#     if custom_fields:
#         payload["customFields"] = custom_fields
#     response = requests.post(url, headers=headers, json=payload)
#     if response.status_code in [200, 201]:
#         return response.json().get("appointment", {}).get("id")
#     return None
#
#
# def check_calendar_availability(calendar_id, start_time, duration_minutes):
#     url = f"{GHL_BASE_URL}/calendars/{calendar_id}/free-slots"
#     headers = {
#         "Authorization": f"Bearer {os.getenv('GHL_API_KEY')}"
#     }
#     end_time = start_time + timedelta(minutes=duration_minutes)
#     params = {
#         "startDate": start_time.date().isoformat(),
#         "endDate": start_time.date().isoformat()
#     }
#     response = requests.get(url, headers=headers, params=params)
#     if response.status_code == 200:
#         slots = response.json().get("slots", [])
#         for slot in slots:
#             slot_start = datetime.fromisoformat(slot["start"])
#             slot_end = datetime.fromisoformat(slot["end"])
#             if slot_start <= start_time and end_time <= slot_end:
#                 return True
#     return False
#
#
# def get_user_details(user_id):
#     url = f"{GHL_BASE_URL}/users/{user_id}"
#     headers = {
#         "Authorization": f"Bearer {os.getenv('GHL_API_KEY')}"
#     }
#     response = requests.get(url, headers=headers)
#     if response.status_code == 200:
#         return response.json().get("user")
#     return None
#
#
# def get_calendar_events(calendar_id, start_date, end_date):
#     url = f"{GHL_BASE_URL}/calendars/{calendar_id}/events"
#     headers = {
#         "Authorization": f"Bearer {os.getenv('GHL_API_KEY')}"
#     }
#     params = {
#         "startDate": start_date.isoformat(),
#         "endDate": end_date.isoformat()
#     }
#     response = requests.get(url, headers=headers, params=params)
#     if response.status_code == 200:
#         return response.json().get("events", [])
#     return []
#
#
# def get_all_users():
#     url = f"{GHL_BASE_URL}/users/"
#     headers = {
#         "Authorization": f"Bearer {os.getenv('GHL_API_KEY')}"
#     }
#     response = requests.get(url, headers=headers)
#     if response.status_code == 200:
#         return response.json().get("users", [])
#     return []
