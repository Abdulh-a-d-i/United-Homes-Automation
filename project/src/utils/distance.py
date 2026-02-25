"""Distance and location estimation utilities."""
import math
from datetime import datetime

from src.utils.db import get_technician, get_tech_appointments_for_day

# Earth radius in miles
EARTH_RADIUS_MILES = 3959


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two lat/lng points using the Haversine formula.

    Args:
        lat1: Latitude of point 1 (degrees).
        lon1: Longitude of point 1 (degrees).
        lat2: Latitude of point 2 (degrees).
        lon2: Longitude of point 2 (degrees).

    Returns:
        Distance in miles.
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_MILES * c


def estimate_tech_location(tech_id, target_datetime):
    """Estimate a technician's location at a given datetime.

    Uses their appointment schedule for the day to predict where
    they will be. Falls back to home coordinates if no appointments.

    Args:
        tech_id: Technician database ID.
        target_datetime: The datetime to estimate location for.

    Returns:
        Dict with 'latitude' and 'longitude' keys, or None.
    """
    tech = get_technician(tech_id)
    if not tech:
        return None

    target_date = target_datetime.date()
    appointments = get_tech_appointments_for_day(tech_id, target_date)

    if not appointments:
        return {
            "latitude": float(tech["home_latitude"]),
            "longitude": float(tech["home_longitude"]),
        }

    for i, appt in enumerate(appointments):
        if target_datetime < appt["start_time"]:
            if i == 0:
                return {
                    "latitude": float(tech["home_latitude"]),
                    "longitude": float(tech["home_longitude"]),
                }
            prev_appt = appointments[i - 1]
            return {
                "latitude": float(prev_appt["latitude"]),
                "longitude": float(prev_appt["longitude"]),
            }

        if appt["start_time"] <= target_datetime <= appt["end_time"]:
            return {
                "latitude": float(appt["latitude"]),
                "longitude": float(appt["longitude"]),
            }

    last_appt = appointments[-1]
    return {
        "latitude": float(last_appt["latitude"]),
        "longitude": float(last_appt["longitude"]),
    }
