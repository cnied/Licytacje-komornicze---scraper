from .logger import setup_logger
import hashlib
from datetime import datetime, timezone
from .category_service import list_category_objects,get_category_object

logger = setup_logger("DATA_TRANSFORMER")

def stable_id_from_url(url: str) -> int:
    h = int(hashlib.sha256(url.encode()).hexdigest()[:16], 16)
    return h % 9223372036854775807

def ai_to_api_object(ai_data: dict, source_url: str, conn) -> tuple:
    """
    Konwertuje dane zwrócone przez AI do struktury zgodnej z API.
    Zwraca krotkę (api_object, address_data).
    """
    auction_id = stable_id_from_url(source_url)
    bailiff = ai_data.get("bailiffData") or {}
    additional = ai_data.get("additionalParams") or {}
    address = ai_data.get("addressData") or {}
    
    # Extract auctionCategory from list if it's a list 
    auction_category = ai_data.get("auctionCategory")
    category_value = ai_data.get("auctionValue")
    if isinstance(auction_category, list) and len(auction_category) > 0:
        auction_category = auction_category[0]
    
    # Convert category string to category object with id
    category_obj = get_category_object(auction_category,category_value,list_category_objects(conn))

    
    # Extract title from list if it's a list
    title = ai_data.get("title")
    if isinstance(title, list) and len(title) > 0:
        title = title[0]

    api_object = {
        "object": {
            "id": auction_id,
            "auctionId": auction_id,
            "name": title,
            "city": ai_data.get("city"),
            "institutionName": bailiff.get("institutionName"),
            "dateCreated": datetime.now(timezone.utc).isoformat(),
            "projectLink": ai_data.get("projectLink") or source_url,
            "estimate": ai_data.get("estimate"),
            "openingValue": ai_data.get("openingvalue"),
            "margin": ai_data.get("margin"),
            "bidStep": ai_data.get("bidstep"),
            "startAuction": ai_data.get("startauction"),
            "endAuction": ai_data.get("endauction"),
            "marginDueDate": ai_data.get("marginduedate"),
            "auctionCategory": auction_category, 
            "itemcategoryid": category_obj,       
            "attachments": [],

            "bailiffData": {
                "bankName": bailiff.get("bankName"),
                "bankIban": bailiff.get("bankIban"),
                "addressData": {
                    "institutionName": bailiff.get("institutionName"),
                    "address": {
                        "street": bailiff.get("street"),
                        "buildingNo": bailiff.get("buildingNo"),
                        "flatNo": bailiff.get("flatNo"),
                        "city": bailiff.get("city"),
                        "zipCode": bailiff.get("zipCode"),
                        "country": bailiff.get("country"),
                        "province": bailiff.get("province"),
                    }
                }
            },


            "additionalParams": additional,

            "aiGenerated": True
        }
    }

    # Przygotuj dane adresowe nieruchomości
    address_data = {
        "auctionId": auction_id,  # zostanie nadane automatycznie
        "institutionName": address.get("institutionName"),
        "foreignAddress": address.get("foreignAddress", False),
        "streetPrefix": address.get("streetPrefix"),
        "street": address.get("street"),
        "buildingNo": address.get("buildingNo"),
        "flatNo": address.get("flatNo"),
        "city": address.get("city"),
        "zipCode": address.get("zipCode"),
        "postOffice": address.get("postOffice"),
        "country": address.get("country", "Polska"),
        "province": address.get("province"),
        "district": address.get("district"),
        "community": address.get("community")
    }

    return api_object, address_data





