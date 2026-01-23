import requests
from requests.structures import CaseInsensitiveDict
from dotenv import load_dotenv
from .logger import setup_logger
from urllib.parse import quote
import os

logger = setup_logger("GEOCODING")
load_dotenv(".env")
GEOCODE_API = os.getenv("GEOCODE_API")


headers = CaseInsensitiveDict()
headers["Accept"] = "application/json"


def geocoding_function(address):
    if not address:
        return None
    try:
        encoded_address = quote(address)
        url = f"https://api.geoapify.com/v1/geocode/search?text={encoded_address}&apiKey={GEOCODE_API}"
        response = requests.get(url, headers=headers,timeout=10)
        data = response.json()
        lon, lat = data["features"][0]["geometry"]["coordinates"]
        logger.info("Geocoding success | lon=%s lat=%s", lon, lat)
        return lon,lat
    except Exception as e:
        logger.error("Error occured while geocoding: %s", e)
        return None
    


if __name__ == '__main__':
    result = geocoding_function("Warszawa, ul. Marszałkowska 1")
    print(result)
