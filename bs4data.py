import requests
import json
from bs4 import BeautifulSoup

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL = "llama3.1:8b"
prompt = f"""
Masz poniższy tekst ogłoszenia o licytacji komorniczej w Polsce.

Wyciągnij dane i zwróć WYŁĄCZNIE poprawny JSON
z polami:
- suma_oszacowania (int, PLN)
- cena_wywolawcza (int, PLN)
- data_licytacji (YYYY-MM-DD)
- godzina_licytacji (HH:MM)
- adres (string)
- sygnatura (string)
- nr ksiegi_wieczystej (string)

Jeśli czegoś nie ma, użyj null.

TEKST:
\"\"\"
{text}
\"\"\"
"""

url = "https://licytacje.komornik.pl/Notice/Details/664034"

payload = {
    "model": MODEL,
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0
    }
}

def fetch_auction_data(url):
    html = requests.get(url,timeout=10).text
    soup = BeautifulSoup(html, "html.parser")
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    result = response.json()["response"]
    data = json.loads(result)
    return soup.get_text(separator="\n", strip=True)


if __name__ == "__main__":
    print(json.dumps(data, indent=2, ensure_ascii=False))

