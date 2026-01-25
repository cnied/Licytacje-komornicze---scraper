from .logger import setup_logger
from bs4 import BeautifulSoup
import requests
import pandas as pd
from .category_service import list_category_objects,get_category_object
from .ai_client import ai_response
from .geocoding import geocoding_function
from .data_transformer import ai_to_api_object
from .db_fulfill import save_auction,save_links_to_process
from .email_parser import elicytacje_regex
import time

logger = setup_logger("SCRAPER")

elicytacje_api = "https://elicytacje.komornik.pl/services/item-back/rest/item"
elicytacje_address_api = "https://elicytacje.komornik.pl/services/item-back/rest/item/{id}/address"

def fetch_auction_data(url,conn):
    max_retries = 3
    retry_delay = 5

    try:
        html = requests.get(url, timeout=10).text
    except requests.RequestException as e:
        logger.error("Error while downloading the webstie %s: %s", url, e)
        return

    soup = BeautifulSoup(html, "html.parser")
    categories = list_category_objects(conn)
    spans = soup.find_all("span", {"class": "value"})
    elicytacje_spans = [
        span.find("a")["href"]
        for span in spans
        if span.find("a", href=True) and "elicytacje" in span.find("a")["href"]
    ]

    # ========= AI FALLBACK =========
    if not elicytacje_spans:
        pass
    #   for attempt in range(max_retries):
    #       try:
    #           ai_data = ai_response(str(soup),categories)
    #           df = pd.DataFrame(soup)
    #           df.to_csv('dane_testowe.csv')
    #           api_like, address_data = ai_to_api_object(ai_data, url, conn)
    #           api_like['object']['projectlink'] = url
    #           address = " ".join(filter(None, [
    #             address_data.get("streetPrefix"),
    #             address_data.get("street"),
    #             address_data.get("buildingNo"),
    #             address_data.get("flatNo"),
    #             address_data.get("zipCode"),
    #             address_data.get("postOffice"),
    #             address_data.get("city"),
    #             address_data.get("district"),
    #             address_data.get("province"),
    #             address_data.get("country"),
    #         ]))
    #           lon, lat = geocoding_function(address)
    #           address_data["lon"] = lon
    #           address_data["lat"] = lat

    #           save_auction(api_like, conn, address_data)
    #           logger.info("Auction saved (AI)")
    #           return  # end after the succes
    #       except Exception as e:
    #           logger.error("Error, attempt: %s, error %s", attempt+1, e)
    #           if attempt < max_retries - 1:
    #               time.sleep(retry_delay)
    #           else:
    #               logger.error("Maximum retries reached")
    #   return

    # ========= API =========
    for item in elicytacje_spans:
        item_id: list = elicytacje_regex(item)[0]
        logger.info("Found elicytacje link: %s", item)

        try:
            api_main = requests.get(f"{elicytacje_api}/{item_id}", timeout=10).json()
            api_address = requests.get(
                elicytacje_address_api.replace("{id}", item_id), timeout=10
            ).json()
            address = " ".join(filter(None, [
                api_address.get("streetPrefix"),
                api_address.get("street"),
                api_address.get("buildingNo"),
                api_address.get("flatNo"),
                api_address.get("zipCode"),
                api_address.get("postOffice"),
                api_address.get("city"),
                api_address.get("district"),
                api_address.get("province"),
                api_address.get("country"),
            ]))

            lon, lat = geocoding_function(address)
            api_address["lon"] = lon
            api_address["lat"] = lat
            api_main['object']['projectlink'] = url
            api_main['object']['aiGenerated'] = False
        except Exception as e:
            logger.error("API elicytacje error occures for ID %s: %s", item_id,e)
            continue

        save_auction(api_main,conn, api_address)
        logger.info("Auction saved (API)")
        time.sleep(1)