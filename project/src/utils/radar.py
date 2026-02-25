import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()


def geocode_address(messy_address):
    url = "https://api.radar.io/v1/geocode/forward"
    api_key = os.getenv("RADAR_API_KEY")

    logging.info(f"[RADAR] Geocoding address: '{messy_address}'")

    headers = {"Authorization": api_key}
    params = {"query": messy_address}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        logging.info(f"[RADAR] Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            addresses = data.get("addresses", [])
            logging.info(f"[RADAR] Found {len(addresses)} address results")

            if addresses:
                addr = addresses[0]
                result = {
                    "formatted_address": addr.get("formattedAddress"),
                    "latitude": addr.get("latitude"),
                    "longitude": addr.get("longitude"),
                    "confidence": addr.get("confidence")
                }
                logging.info(f"[RADAR] Result: {result['formatted_address']} ({result['latitude']}, {result['longitude']}) confidence={result['confidence']}")
                return result
            else:
                logging.warning(f"[RADAR] No addresses found for: '{messy_address}'")
        else:
            logging.error(f"[RADAR] API error {response.status_code}: {response.text[:200]}")

    except requests.exceptions.Timeout:
        logging.error(f"[RADAR] Request timed out for: '{messy_address}'")
    except Exception as e:
        logging.error(f"[RADAR] Exception: {e}")

    return None
