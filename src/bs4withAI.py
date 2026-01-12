from socket import SOL_UDP
from urllib.request import url2pathname
import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
import time
import pandas as pd
from .db_fulfill import save_auction
from .logger import setup_logger
from .db_connect import db_login
import re
import os
import hashlib
from datetime import datetime, timezone

conn, error = db_login()
load_dotenv(".env")

logger = setup_logger("BS4WITHAI")

url = "https://licytacje.komornik.pl/Notice/Details/662809"

elicytacje_api = "https://elicytacje.komornik.pl/services/item-back/rest/item"
elicytacje_address_api = "https://elicytacje.komornik.pl/services/item-back/rest/item/{id}/address"
regex = r'/items/(\d+)'


# =======================
# HELPERS
# =======================

def elicytacje_regex(body):
    return list(dict.fromkeys(re.findall(regex, body or "")))


# def clear_attachments(obj):
#     if isinstance(obj, dict):
#         new_obj = {}
#         for k, v in obj.items():
#             if k == "attachments" and isinstance(v, list):
#                 new_obj[k] = [{ik: None for ik in item.keys()} for item in v if isinstance(item, dict)]
#             else:
#                 new_obj[k] = clear_attachments(v)
#         return new_obj
#     elif isinstance(obj, list):
#         return [clear_attachments(v) for v in obj]
#     return obj


def stable_id_from_url(url: str) -> int:
    h = int(hashlib.sha256(url.encode()).hexdigest()[:16], 16)
    return h % 9223372036854775807


def get_category_object(category_name):
    """
    Mapuje nazwę kategorii na obiekt z id zgodny z bazą danych.
    """
    categories = {
        "INDUSTRIAL_MACHINES": {"id": 105, "name": "maszyny przemysłowe"},
        "LAND": {"id": 122, "name": "grunty"},
        "HOUSES": {"id": 123, "name": "domy"},
        "APARTMENTS": {"id": 124, "name": "mieszkania"},
    }
    
    if not category_name:
        return None
    
    return categories.get(category_name)


# =======================
# AI
# =======================

client = genai.Client()

def ai_response(text: str, max_retries = 3, retry_delay = 30) -> dict:
    prompt = f"""
Jesteś ekspertem od polskich licytacji komorniczych.

DOSTAJESZ WYŁĄCZNIE TEKST OGŁOSZENIA.
NIE MASZ dostępu do żadnych innych źródeł.

TWARDY ZAKAZ DOMYŚLANIA SIĘ DANYCH.
Jeżeli informacja:
- NIE WYSTĘPUJE WPROST w tekście
- JEST NIEJEDNOZNACZNA
- MOŻE BYĆ TYLKO PRZYPUSZCZENIEM

TO:
→ USTAW JEJ WARTOŚĆ NA null

ZASADY:
- NIE zgaduj roku budowy, powierzchni, liczby pokoi itp.
- NIE zakładaj standardowych wartości.
- NIE uzupełniaj danych „bo zwykle tak bywa".
- Uzupełniaj TYLKO dane, które są WYRAŹNIE zapisane w tekście.
- Jeśli masz jakąkolwiek wątpliwość → null.

**WAŻNE - TABELE Z WIELOMA POZYCJAMI**:
Jeśli ogłoszenie zawiera tabelę (<table>) z wieloma ruchomościami/nieruchomościami:
- "estimate" = SUMA wszystkich wartości z kolumny "Suma oszacowania"
- "openingvalue" = SUMA wszystkich wartości z kolumny "Cena wywołania"
- "margin" = 1/10 sumy oszacowania (rękojmia)
- "bidstep" = null (różne dla każdej pozycji)
- "name" = ogólny opis np. "Licytacja ruchomości - 4 pojazdy ciężarowe"
Przykład: jeśli tabela ma pozycje 36000 zł, 49000 zł, 53900 zł, 27400 zł to estimate = 166300

**WAŻNE - FORMAT LICZB**:
- Wszystkie liczby MUSZĄ używać kropki (.) jako separatora dziesiętnego, NIE przecinka!
- Przykład: 2369.80 (poprawnie), NIE 2369,80 (błąd)
- Nie używaj spacji ani przecinków jako separatorów tysięcy

**WAŻNE**: auctionCategory może być TYLKO jedną z tych wartości:
- "APARTMENTS" (mieszkania)
- "HOUSES" (domy)
- "LAND" (grunty)
- "INDUSTRIAL_MACHINES" (maszyny przemysłowe)
Jeśli nie pasuje do żadnej z tych kategorii, ustaw null.

Zwróć JEDEN OBIEKT JSON zgodny ze schematem:

{{
  "title": "string" | null,  # Tytuł ogłoszenia / nazwa licytowanej nieruchomości/ruchomości
  "auctionId": "bigint" | null,  # Unikalny identyfikator licytacji
  "auctionCategory": "string" | null,  # Kategoria: "APARTMENTS", "HOUSES", "LAND", "INDUSTRIAL_MACHINES" lub null
  "projectLink": "string" | null,  # Link do ogłoszenia / strony aukcji
  "estimate": number | null,  # Szacunkowa wartość nieruchomości/ruchomości w PLN, jeśli podano
  "openingvalue": number | null,  # Wartość wywoławcza w PLN, jeśli podano
  "margin": number | null,  # Wartość wadium w PLN, jeśli podano
  "bidstep": number | null,  # Minimalny krok licytacji w PLN, jeśli podano
  "startauction": "string" | null,  # Data i godzina rozpoczęcia licytacji w formacie ISO 8601, jeśli podano
  "endauction": "string" | null,  # Data i godzina zakończenia licytacji w formacie ISO 8601, jeśli podano
  "marginduedate": "string" | null,  # Ostateczna data wpłaty wadium w formacie ISO 8601, jeśli podano
  "institutionname": "string" | null,  # Nazwa komornika / kancelarii
  "city": "string" | null,             # Miasto licytowanej nieruchomości/ruchomości
  "name": "string" | null,             # Tytuł licytowanej nieruchomości/ruchomości

  "bailiffData": {{
    "institutionName": "string" | null,  # Nazwa komornika / kancelarii
    "street": "string" | null,           # Ulica komornika / kancelarii
    "buildingNo": "string" | null,       # Numer budynku komornika / kancelarii
    "flatNo": "string" | null,           # Numer lokalu / mieszkania komornika / kancelarii
    "city": "string" | null,             # Miasto komornika / kancelarii
    "zipCode": "string" | null,          # Kod pocztowy komornika / kancelarii
    "country": "string" | null,          # Kraj komornika / kancelarii
    "province": "string" | null,         # Województwo komornika / kancelarii
    "bankName": "string" | null,         # Nazwa banku powiązanego z komornikiem
    "bankIban": "string" | null          # Numer IBAN konta bankowego komornika
  }},

  "additionalParams": {{
    "AREA": {{ "value": number | null, "format": "SINGLE" }},  # Powierzchnia w m² lub ha, jeśli podano
    "NUMBEROFROOMS": {{ "value": integer | null, "format": "SINGLE" }},  # Liczba pokoi, jeśli dotyczy
    "YEAROFCONSTRUCTION": {{ "value": integer | null, "format": "SINGLE" }},  # Rok budowy / wzniesienia budynku
    "HOUSETYPE": {{ "value": "string" | null, "format": "SINGLE" }},  # Typ domu (np. wolnostojący, szeregowy)
    "MEDIA": {{ "value": ["string"] | null, "format": "MULTI" }},  # Media dostępne na posesji (np. ["woda", "kanalizacja", "prąd"])
    "SHARESIZE": {{ "value": "string" | null, "format": "SINGLE" }},  # Udział w nieruchomości (np. "1/1", "1/2")
    "ECONOMICPURPOSE": {{ "value": "string" | null, "format": "SINGLE" }}  # Przeznaczenie nieruchomości (np. "dom mieszkalny", "nieruchomość rolna")
  }},

  "addressData": {{
    "auctionId": null,                     # Zawsze ustaw jako null - zostanie nadane automatycznie
    "institutionName": "string" | null,    # Nazwa instytucji związanej z adresem nieruchomości (jeśli dotyczy)
    "foreignAddress": false,               # Czy adres jest zagraniczny - dla polskich adresów zawsze false
    "streetPrefix": "string" | null,       # Prefiks ulicy (np. "ul.", "al.", "os.") - ODDZIELNY od nazwy ulicy
    "street": "string" | null,             # Nazwa ulicy licytowanej nieruchomości (BEZ prefiksu "ul.")
    "buildingNo": "string" | null,         # Numer budynku (lub "0"/"-" jeśli brak)
    "flatNo": "string" | null,             # Numer lokalu/mieszkania (jeśli dotyczy)
    "city": "string" | null,               # Miasto/miejscowość licytowanej nieruchomości
    "zipCode": "string" | null,            # Kod pocztowy (format XX-XXX)
    "postOffice": "string" | null,         # Urząd pocztowy (jeśli inny niż miasto)
    "country": "Polska",                   # Kraj - domyślnie "Polska"
    "province": "string" | null,           # Województwo (np. "mazowieckie", "małopolskie")
    "district": "string" | null,           # Powiat (jeśli podano)
    "community": "string" | null           # Gmina (jeśli podano)
  }},

  "aiGenerated": true  # Pole do oznaczenia, że JSON został wygenerowany przez AI
}}

TEKST OGŁOSZENIA:
{text}
"""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemma-3-27b-it",
                contents=prompt
            )

            raw = response.text.strip()
            #print("raw text" + raw)
            #print("end of raw text")
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
            if match:
                raw = match.group(1).strip()
            elif raw == "":
                raise ValueError("AI zwróciło pusty tekst – brak danych do parsowania JSON")

            data = json.loads(raw)
            data["aiGenerated"] = True
            return data

        except Exception as e:
            logger.error("AI error (attempt %s/%s): %s", attempt + 1, max_retries, e)
            if attempt < max_retries-1:
                logger.info("Retrying in %s seconds", retry_delay)
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached, returning fallback")
    return {
        "title": None,
        "auctionId": None,
        "auctionCategory": None,
        "projectLink": None,
        "bailiffData": {
            "institutionName": None,
            "street": None,
            "buildingNo": None,
            "flatNo": None,
            "city": None,
            "zipCode": None,
            "country": None,
            "province": None,
            "bankName": None,
            "bankIban": None
        },
        "additionalParams": {},
        "addressData": {
            "auctionId": None,
            "institutionName": None,
            "foreignAddress": False,
            "streetPrefix": None,
            "street": None,
            "buildingNo": None,
            "flatNo": None,
            "city": None,
            "zipCode": None,
            "postOffice": None,
            "country": "Polska",
            "province": None,
            "district": None,
            "community": None
        },
        "aiGenerated": True
    }


# =======================
# AI → API ADAPTER
# =======================

def ai_to_api_object(ai_data: dict, source_url: str) -> tuple:
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
    if isinstance(auction_category, list) and len(auction_category) > 0:
        auction_category = auction_category[0]
    
    # Convert category string to category object with id
    category_obj = get_category_object(auction_category)
    
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
            "auctionCategory": auction_category,
            "projectLink": ai_data.get("projectLink") or source_url,
            "estimate": ai_data.get("estimate"),
            "openingValue": ai_data.get("openingvalue"),
            "margin": ai_data.get("margin"),
            "bidStep": ai_data.get("bidstep"),
            "startAuction": ai_data.get("startauction"),
            "endAuction": ai_data.get("endauction"),
            "marginDueDate": ai_data.get("marginduedate"),
            "itemCategory": category_obj,
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


# =======================
# MAIN
# =======================

def fetch_auction_data(url,conn):
    max_retries = 3
    retry_delay = 5

    try:
        html = requests.get(url, timeout=10).text
    except requests.RequestException as e:
        logger.error("Error while downloading the webstie %s: %s", url, e)

    soup = BeautifulSoup(html, "html.parser")
    spans = soup.find_all("span", {"class": "value"})
    elicytacje_spans = [
        span.find("a")["href"]
        for span in spans
        if span.find("a", href=True) and "elicytacje" in span.find("a")["href"]
    ]

    # ========= AI FALLBACK =========
    if not elicytacje_spans:
      for attempt in range(max_retries):
          try:
              ai_data = ai_response(str(soup))
              df = pd.DataFrame(soup)
              df.to_csv('dane_testowe.csv')
              api_like, address_data = ai_to_api_object(ai_data, url)
              api_like['object']['projectlink'] = url
              save_auction(api_like, conn, address_data)
              logger.info("Auction saved (AI)")
              return  # end after the succes
          except Exception as e:
              logger.error("Error AI, attempt: %s, error %s", attempt+1, e)
              if attempt < max_retries - 1:
                  time.sleep(retry_delay)
              else:
                  logger.error("Maximum retries reached")
      return

    # ========= API =========
    for item in elicytacje_spans:
        item_id: list = elicytacje_regex(item)[0]
        logger.info("Found elicytacje link: %s", item)

        try:
            api_main = requests.get(f"{elicytacje_api}/{item_id}", timeout=10).json()
            api_address = requests.get(
                elicytacje_address_api.replace("{id}", item_id), timeout=10
            ).json()
            api_main['object']['projectlink'] = url
            api_main['object']['aiGenerated'] = False
        except Exception as e:
            logger.error("API elicytacje error occures for ID %s: %s", item_id,e)
            continue

        save_auction(api_main,conn, api_address)
        logger.info("Auction saved (API)")
        time.sleep(1)


if __name__ == "__main__":
    fetch_auction_data(url,conn)