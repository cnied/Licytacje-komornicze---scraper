import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
import time
from db_fulfill import save_auction
from db_connect import db_login
import re
import os


conn,error = db_login()

load_dotenv(".env")
#url = "https://licytacje.komornik.pl/Notice/Details/662790" #ten url do zabezpieczenia - po przejsciu na elicytacje blokada dostępu
url = "https://licytacje.komornik.pl/Notice/Details/664151"


elicytacje_api = "https://elicytacje.komornik.pl/services/item-back/rest/item"
elicytacje_address_api = "https://elicytacje.komornik.pl/services/item-back/rest/item/{id}/address"
regex = r'/items/(\d+)'


def elicytacje_regex(body):
    if not body:
        return []
    all_links = re.findall(regex, body)
    unique_links = list(dict.fromkeys(all_links))
    return unique_links

def clear_attachments(obj):
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            if k == "attachments" and isinstance(v, list):
                new_list = []
                for item in v:
                    if isinstance(item, dict):
                        new_item = {ik: None for ik in item.keys()}
                        new_list.append(new_item)
                    else:
                        new_list.append(None)
                new_obj[k] = new_list
            else:
                new_obj[k] = clear_attachments(v)
        return new_obj

    elif isinstance(obj, list):
        return [clear_attachments(v) for v in obj]

    else:
        return obj
            

# Inicjalizacja klienta
client = genai.Client()

def fetch_auction_data(url):
    html = requests.get(url, timeout=10).text
    soup = BeautifulSoup(html, "html.parser")


    spans = soup.find_all('span', {'class' : 'value'})
    elicytacje_spans = [span.find('a')['href'] for span in spans if span.find('a', href=True) and 'elicytacje' in span.find('a')['href']]

    if len(elicytacje_spans) == 0:
        json_data_main = ai_response(soup.get_text())
        json_data_address = None
        print("Data downloaded from webpage")
        #print(json_data)

    elif elicytacje_spans is not None:
        #print(repr(elicytacje_spans[0]))
        #print(elicytacje_regex(elicytacje_spans[0]))
        for item in elicytacje_spans:
            api_link = elicytacje_api + "/" + elicytacje_regex(item)[0]
            api_main_response = requests.get(api_link, timeout=10).json()
            print("Span item:", item)
            api_address_response = requests.get(elicytacje_address_api.replace("{id}", elicytacje_regex(item)[0]), timeout=10).json()
            print("API Address Response:", api_address_response)

            json_data_main = clear_attachments(api_main_response)
            json_data_address = clear_attachments(api_address_response)
            print("Data downloaded from API")
            print(api_link)
            #print(json.dumps(json_data, indent=2, ensure_ascii=False))

            try:
                save_auction(json_data_main, json_data_address, conn)
                print("Auction saved:", json_data_main.get("object", {}).get("id"))
            except Exception as e:
                print("Error saving auction:", e)

            time.sleep(1)
            #print(api_response)
            #print(json.dumps(api_response, indent=2, ensure_ascii=False))


    return {
        'json_data_main': json_data_main, 
        'json_data_address': json_data_address,
        'elicytacje_links': elicytacje_spans
    }

def ai_response(text):
    full_prompt = f"""
Jesteś ekspertem od danych i polskich ogłoszeń o licytacjach komorniczych.
Na wejściu dostajesz WYŁĄCZNIE TEKST ogłoszenia (bez żadnego JSON-a z API).

Twoim zadaniem jest przeczytać ten tekst i wyciągnąć z niego jak najwięcej informacji,
zwracając jeden obiekt JSON w ściśle określonym formacie.

DODATKOWE WAŻNE INFORMACJE:
- Wszystkie dane mają pochodzić z TEKSTU ogłoszenia.
- Dodaj pole "aiGenerated": true, aby oznaczyć, że dane powstały z analizy AI.

Wymagane pola i ich znaczenie:

- "title": string
  ...

- "auctionId": int | null
  Identyfikator licytacji, jeśli jest w tekście (np. numer ogłoszenia, numer sprawy,
  numer licytacji, itp.). Jeśli nie ma jednoznacznego numeru – ustaw null.

- "auctionCategory": string | null
  Ogólna kategoria nieruchomości, np. "REAL_ESTATE", "MOVABLES", "CARS".
  Jeśli nie możesz jednoznacznie przypisać kategorii – ustaw null.

- "projectLink": string | null
  Link (URL) do ogłoszenia lub projektu, jeśli występuje w tekście.

- "bailiffData": {{
    "institutionName": string | null,
    "street": string | null,
    "buildingNo": string | null,
    "flatNo": string | null,
    "city": string | null,
    "zipCode": string | null,
    "country": string | null,
    "province": string | null,
    "bankName": string | null,
    "bankIban": string | null
  }}

- "additionalParams": {{
    "AREA": {{
      "value": float | null,
      "format": "SINGLE"
    }},
    "NUMBEROFROOMS": {{
      "value": int | null,
      "format": "SINGLE"
    }},
    "YEAROFCONSTRUCTION": {{
      "value": int | null,
      "format": "SINGLE"
    }},
    "HOUSETYPE": {{
      "value": string | null,
      "format": "SINGLE"
    }},
    "MEDIA": {{
      "value": [ "woda" | "prad" | "gaz" | "kanalizacja" ],
      "format": "MULTI"
    }},
    "SHARESIZE": {{
      "value": string | null,
      "format": "SINGLE"
    }},
    "ECONOMICPURPOSE": {{
      "value": string | null,
      "format": "SINGLE"
    }}
  }}

- "aiGenerated": boolean
  ZAWSZE ustaw na true, ponieważ wszystkie te dane pochodzą z analizy tekstu przez AI.

(Zostaw wszystkie poprzednie pola: title, city, courtBailiffName, estimate, openingValue, margin,
auctionDate, auctionTime, marginDueDate, address, placeOfAuction, KWNumber, area, shareSize,
numberOfRooms, yearOfConstruction, houseType, media, roomsList, viewingDates.)

ZASADY OGÓLNE:
- Jeśli jakiejś informacji NIE DA SIĘ pewnie wyciągnąć z tekstu,
  ustaw odpowiednie pole na null.
- Wszystkie liczby zwracaj jako liczby, nie jako stringi.
- Daty konwertuj do formatu YYYY-MM-DD, godziny do HH:MM.
- Zwróć WYŁĄCZNIE jeden obiekt JSON w opisanym formacie, bez dodatkowego tekstu.

Tekst ogłoszenia:
{text}
"""
    try:
        response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=full_prompt
        )
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        return {"error": f"Wystąpił problem: {str(e)}", "raw_response": getattr(response, 'text', 'Brak odpowiedzi')}

if __name__ == "__main__":
    data = fetch_auction_data(url)
    #print(data['text'])
    #result = ai_response(data['text'])
    #print(json.dumps(result, indent=4, ensure_ascii=False))