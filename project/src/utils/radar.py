import os
import requests
from dotenv import load_dotenv

load_dotenv()


def geocode_address(messy_address):
    url = "https://api.radar.io/v1/geocode/forward"
    headers = {
        "Authorization": os.getenv("RADAR_API_KEY")
    }
    params = {
        "query": messy_address
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("addresses") and len(data["addresses"]) > 0:
            address_data = data["addresses"][0]
            return {
                "formatted_address": address_data.get("formattedAddress"),
                "latitude": address_data.get("latitude"),
                "longitude": address_data.get("longitude"),
                "confidence": address_data.get("confidence")
            }
    
    return None
