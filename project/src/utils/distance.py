import math
from datetime import datetime
from src.utils.db import get_technician, get_tech_appointments_for_day


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 3959
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def estimate_tech_location(tech_id, target_datetime):
    tech = get_technician(tech_id)
    if not tech:
        return None
    
    # Convert timezone-aware datetime to naive for comparison with database datetimes
    if target_datetime.tzinfo is not None:
        target_datetime = target_datetime.replace(tzinfo=None)
    
    target_date = target_datetime.date()
    appointments = get_tech_appointments_for_day(tech_id, target_date)
    
    if not appointments:
        return {
            "latitude": float(tech["home_latitude"]),
            "longitude": float(tech["home_longitude"])
        }
    
    for i, appt in enumerate(appointments):
        if target_datetime < appt["start_time"]:
            if i == 0:
                return {
                    "latitude": float(tech["home_latitude"]),
                    "longitude": float(tech["home_longitude"])
                }
            else:
                prev_appt = appointments[i - 1]
                return {
                    "latitude": float(prev_appt["latitude"]),
                    "longitude": float(prev_appt["longitude"])
                }
        
        elif appt["start_time"] <= target_datetime <= appt["end_time"]:
            return {
                "latitude": float(appt["latitude"]),
                "longitude": float(appt["longitude"])
            }
    
    last_appt = appointments[-1]
    return {
        "latitude": float(last_appt["latitude"]),
        "longitude": float(last_appt["longitude"])
    }
