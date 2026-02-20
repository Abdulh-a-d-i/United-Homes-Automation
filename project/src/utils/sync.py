# GHL SYNC - COMMENTED OUT (No paid GHL API access)
# All sync functions preserved below for reference.
# Calendar sync will be handled by direct Google/Outlook integration.

# from datetime import datetime, timedelta
# from src.utils.ghl import get_calendar_events, get_all_users
# from src.utils.db import (
#     get_all_technicians,
#     insert_appointment_cache,
#     upsert_technician_from_ghl,
#     get_technician_by_ghl_user_id
# )
# import json
#
#
# def sync_calendar_appointments():
#     techs = get_all_technicians()
#     synced_count = 0
#     today = datetime.now()
#     start_date = today - timedelta(days=7)
#     end_date = today + timedelta(days=90)
#     for tech in techs:
#         if not tech.get("ghl_calendar_id"):
#             continue
#         try:
#             events = get_calendar_events(
#                 tech["ghl_calendar_id"],
#                 start_date,
#                 end_date
#             )
#             for event in events:
#                 start_time = datetime.fromisoformat(event["startTime"].replace("Z", "+00:00"))
#                 end_time = datetime.fromisoformat(event["endTime"].replace("Z", "+00:00"))
#                 insert_appointment_cache(
#                     ghl_appointment_id=event["id"],
#                     technician_id=tech["id"],
#                     customer_name=event.get("title", ""),
#                     customer_phone="",
#                     service_type="",
#                     address=event.get("address", ""),
#                     latitude=event.get("latitude"),
#                     longitude=event.get("longitude"),
#                     start_time=start_time,
#                     end_time=end_time,
#                     status=event.get("status", "scheduled")
#                 )
#                 synced_count += 1
#         except Exception as e:
#             print(f"Error syncing calendar for tech {tech['name']}: {str(e)}")
#             continue
#     return {"synced_appointments": synced_count}
#
#
# def sync_technicians_from_ghl():
#     users = get_all_users()
#     synced_count = 0
#     for user in users:
#         tags = user.get("tags", [])
#         if "technician" in [tag.lower() for tag in tags]:
#             try:
#                 custom_fields = user.get("customFields", {})
#                 skills_str = custom_fields.get("skills", "[]")
#                 if isinstance(skills_str, str):
#                     skills = json.loads(skills_str) if skills_str else []
#                 else:
#                     skills = skills_str
#                 skills_json = json.dumps(skills) if skills else None
#                 upsert_technician_from_ghl(
#                     ghl_user_id=user["id"],
#                     ghl_calendar_id=user.get("calendarId", ""),
#                     name=user["name"],
#                     email=user["email"],
#                     phone=user.get("phone", ""),
#                     skills=skills_json,
#                     home_latitude=custom_fields.get("home_latitude"),
#                     home_longitude=custom_fields.get("home_longitude")
#                 )
#                 synced_count += 1
#             except Exception as e:
#                 print(f"Error syncing technician {user.get('name', 'Unknown')}: {str(e)}")
#                 continue
#     return {"synced_technicians": synced_count}
