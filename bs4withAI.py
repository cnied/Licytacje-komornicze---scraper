import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from google.genai import types



url = "https://licytacje.komornik.pl/Notice/Details/664929"
load_dotenv(".env")
client = genai.Client()

def fetch_auction_data(url):
    
    html = requests.get(url,timeout=10).text
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def ai_response(soup):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction="""
            Wyciągnij dane z ogłoszenia o licytacji komorniczej.
            Zwróć JSON z polami:
            - suma_oszacowania (int)
            - cena_wywolawcza (int)
            - data_licytacji (format YYYY-MM-DD)
            - godzina_licytacji (format HH:MM)
            - adres (string)
            - sygnatura (string)
            - nr_ksiegi_wieczystej (string)
            """
        ),
        contents=soup
    )
    return json.loads(response.text)


if __name__ == "__main__":
    print(ai_response(fetch_auction_data(url)))

