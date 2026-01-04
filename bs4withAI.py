import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
import os

# Załaduj zmienne z .env (upewnij się, że masz tam GEMINI_API_KEY lub ustaw klucz w Client)
load_dotenv(".env")
url = "https://licytacje.komornik.pl/Notice/Details/662790"

# Inicjalizacja klienta
client = genai.Client()

def fetch_auction_data(url):
    html = requests.get(url, timeout=10).text
    soup = BeautifulSoup(html, "html.parser")
    spans = soup.find_all('span', {'class' : 'value'})
    elicytacje_spans = [span.find('a')['href'] for span in spans if span.find('a', href=True) and 'elicytacje' in span.find('a')['href']]
    
    return {
        'text': soup.get_text(separator="\n", strip=True),
        'elicytacje_links': elicytacje_spans
    }

def ai_response(text):
    # Tworzymy pełny prompt łączący instrukcję i dane
    full_prompt = f"""
    Jesteś ekspertem od danych. Wyciągnij dane z ogłoszenia o licytacji komorniczej.
    Zwróć dane WYŁĄCZNIE jako czysty obiekt JSON (bez markdownu, bez ```json).
    
    Wymagane pola:
    - suma_oszacowania (int)
    - cena_wywolawcza (int)
    - data_licytacji (format YYYY-MM-DD)
    - godzina_licytacji (format HH:MM)
    - adres (string)
    - sygnatura (string)
    - nr_ksiegi_wieczystej (string)

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
    result = ai_response(data['text'])
    print(json.dumps(result, indent=4, ensure_ascii=False))