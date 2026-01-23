
from .logger import setup_logger
from google import genai
import re
import json
import time

logger = setup_logger("AI_CLIENT")

client = genai.Client()

def ai_response(text: str, categories: str, max_retries = 3, retry_delay = 30) -> dict:
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

**WAŻNE**: 
Podsyłam ci słownik z mojej bazy danych, na jego bazie przypisuj odpowiednio auctionCategory(w słowniku 'category') i auctionValue(w słowniku 'value')
auctionCategory może być TYLKO jedną z tych wartości, dla których posiadamy klucz 'category'.
auctionValue może być TYLKO jedną z tych wartości, dla których posiadamy klucz 'value'.
{categories}

Jeśli nie pasuje do żadnej z tych kategorii, ustaw null.

Zwróć JEDEN OBIEKT JSON zgodny ze schematem:

{{
  "title": "string" | null,  # Tytuł ogłoszenia / nazwa licytowanej nieruchomości/ruchomości
  "auctionId": "bigint" | null,  # Unikalny identyfikator licytacji
  "auctionCategory": "string" | null,  # Kategoria: "APARTMENTS", "HOUSES", "LAND", "INDUSTRIAL_MACHINES" lub null
  "auctionValue": "string" | null, # Wartość dla kategorii: "grunty", "lokale użytkowe", "mieszkania", "meble"
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
