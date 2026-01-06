import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
import time
import re
import os


load_dotenv(".env")
#url = "https://licytacje.komornik.pl/Notice/Details/662790" #ten url do zabezpieczenia - po przejsciu na elicytacje blokada dostępu
url = "https://licytacje.komornik.pl/Notice/Details/663384"


elicytacje_api = "https://elicytacje.komornik.pl/services/item-back/rest/item"
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
    json_data = ai_response(soup.get_text())
    print("Data downloaded from webpage")

    if elicytacje_spans is not None:
        #print(repr(elicytacje_spans[0]))
        #print(elicytacje_regex(elicytacje_spans[0]))
        for item in elicytacje_spans:
            api_link = elicytacje_api + "/" + elicytacje_regex(item)[0]
            api_response = requests.get(api_link, timeout=10).json()
            json_data = clear_attachments(api_response)
            print("Data downloaded from API")
            print(api_link)
            time.sleep(1)
            #print(api_response)
            #print(json.dumps(api_response, indent=2, ensure_ascii=False))


    return {
        'json_data': json_data,
        'elicytacje_links': elicytacje_spans
    }

def ai_response(text):
    full_prompt = f"""
Jesteś ekspertem od danych i polskich ogłoszeń o licytacjach komorniczych.
Na wejściu dostajesz WYŁĄCZNIE TEKST ogłoszenia (bez żadnego JSON-a z API).

Twoim zadaniem jest przeczytać ten tekst i wyciągnąć z niego jak najwięcej informacji,
zwracając jeden obiekt JSON w ściśle określonym formacie.

Wymagane pola i ich znaczenie:

- "title": string
  Opis / nazwa licytowanego przedmiotu (np. dom, mieszkanie, działka),
  zwykle w pierwszych liniach ogłoszenia lub wyraźnie jako tytuł.

- "city": string
  Miejscowość, w której położona jest nieruchomość.
  Szukaj fragmentów typu: "położonej pod adresem: ..., <miasto>", "w miejscowości ...".

- "courtBailiffName": string
  Nazwa komornika i sądu prowadzącego egzekucję,
  np. "Komornik Sądowy przy Sądzie Rejonowym w Olkuszu Bartosz Kryj".

- "estimate": float | null
  Suma oszacowania nieruchomości w złotych.
  Szukaj zdań typu: "Suma oszacowania wynosi 328 700,00 zł".
  Usuń spacje i kropki jako separatory tysięcy, przecinek zamień na kropkę.

- "openingValue": float | null
  Cena wywołania (cena, od której zaczyna się licytacja).
  Szukaj zdań typu: "cena wywołania jest równa ... zł".

- "margin": float | null
  Wysokość rękojmi (wadium) w złotych.
  Szukaj zdań typu: "rękojmia w wysokości ... zł".

- "auctionDate": "YYYY-MM-DD" | null
  Data rozpoczęcia licytacji.
  Szukaj fragmentów typu: "w dniu 31/12/2025 r.".
  Zamień format DD/MM/RRRR lub DD.MM.RRRR na YYYY-MM-DD.

- "auctionTime": "HH:MM" | null
  Godzina rozpoczęcia licytacji.
  Szukaj fragmentów typu: "o godz. 09:00", wynik zwróć jako "09:00".

- "marginDueDate": "YYYY-MM-DD HH:MM" | null
  Termin złożenia rękojmi (data i godzina).
  Szukaj zdań typu: "najpóźniej na 2 dni robocze przed rozpoczęciem przetargu"
  lub bezpośrednio podanej daty z godziną.
  Jeśli znajdziesz tylko datę lub tylko godzinę, użyj null.

- "address": string | null
  Pełny adres nieruchomości w jednej linii,
  np. "Tarnawa 124, 32-353 Trzyciąż".
  Zbuduj z elementów typu: ulica, numer, kod pocztowy, miejscowość.

- "KWNumber": string | null
  Numer księgi wieczystej.
  Szukaj fragmentów typu: "księgę wieczystą o numerze KR1O/00056050/6".

- "area": float | null
  Powierzchnia działki lub budynku w metrach kwadratowych.
  Preferuj ogólną powierzchnię nieruchomości,
  np. "Powierzchnia użytkowa budynku mieszkalnego wynosi 64,01 m2".
  Zamień przecinek na kropkę.

- "shareSize": string | null
  Wielkość udziału, np. "1/1".
  Szukaj fraz typu: "Wielkość udziału 1/1".

- "numberOfRooms": int | null
  Liczba pokoi.
  Szukaj fraz typu: "Liczba pokoi 3" lub opisu "trzypokojowe".

- "yearOfConstruction": int | null
  Rok budowy.
  Szukaj fraz typu: "Rok budowy 1940".

- "houseType": string | null
  Typ zabudowy, np. "wolnostojący", "szeregowy", "bliźniak".
  Szukaj fraz typu: "Rodzaj domu wolnostojący".

- "media": [ "woda" | "prad" | "gaz" | "kanalizacja" ]
  Lista dostępnych mediów.
  Mapowanie:
    - jeśli w tekście jest "woda" → dodaj "woda",
    - "energia elektryczna", "prąd", "siła" → dodaj "prad",
    - "gaz" → dodaj "gaz",
    - "kanalizacja", "zbiornik na ścieki", "oczyszczalnia" → dodaj "kanalizacja".
  Nie duplikuj wartości, zwróć listę unikalnych.

- "roomsList": [string] | null
  Lista pomieszczeń, jeśli są wyliczone,
  np. "kuchnia, łazienka, pokój, salon".

- "viewingDates": [
    {{
      "date": "YYYY-MM-DD",
      "timeFrom": "HH:MM",
      "timeTo": "HH:MM"
    }}
  ] | []
  Terminy oględzin nieruchomości.
  Szukaj fragmentów typu:
  "W ciągu dwóch ostatnich tygodni przed licytacją wolno oglądać lokal
   w dni powszednie od godz. 8.00 do godz. 18.00".
  Jeśli jest tylko ogólny zakres (jak powyżej), możesz zbudować jeden wpis
  z datą null i tylko godzinami lub zwrócić pustą listę, jeśli nie da się
  jednoznacznie zidentyfikować dat.

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