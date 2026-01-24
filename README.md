# Inteligentny Scraper Licytacji Komorniczych

![Status](https://img.shields.io/badge/status-in%20progress-orange)
![Progress](https://img.shields.io/badge/progress-85%25-green)

**Projekt w trakcie rozwoju (85%)**

Automatyczne narzędzie do pobierania i przechowywania ogłoszeń o licytacjach komorniczych.
Projekt wykorzystuje **AI (Google Gemini)**, **BeautifulSoup** i bazę danych **PostgreSQL**.

---

## Funkcje

### Pobieranie danych
- logowanie do konta Gmail przez IMAP
- analiza newsletterów z portalu licytacje.komornik.pl

### Inteligentna ekstrakcja treści
- dane z e-licytacji pobierane przez API elicytacje.komornik.pl
- gdy API niedostępne - fallback na **Google Gemini AI**
- ekstrakcja: adres, cena wywoławcza, wadium, daty licytacji, dane komornika

### Baza danych PostgreSQL
- automatyczne tworzenie tabel
- upsert (INSERT ON CONFLICT) - bez duplikatów
- przechowywanie: aukcje, adresy, załączniki, parametry dodatkowe, dane komorników

### Geokodowanie adresów
- automatyczne pobieranie współrzędnych geograficznych (lat/lon)
- integracja z Geoapify Geocoding API

### Interaktywna mapa
- wizualizacja aukcji na mapie (Folium)
- popupy ze zdjęciami, cenami, datami i szczegółami
- automatyczne odświeżanie

### Logowanie
- logi do konsoli i plików (folder `logs/`)
- poziomy: DEBUG (plik), INFO (konsola)

---

## Jak działa (ETL)

1. **Extract** - pobieranie maili z Gmail, wyciąganie linków do licytacji
2. **Transform** - scraping danych przez API lub AI
3. **Load** - zapis do PostgreSQL

---

## Wymagania

### `.env`
```
# Gmail
USER=twoj-email@gmail.com
PASSWORD=twoje-haslo-aplikacji-google

# Gemini AI
GEMINI_API_KEY=twoj_klucz_api_gemini

# Geokodowanie (Geoapify)
GEOCODE_API=twoj_klucz_api_geoapify

# PostgreSQL
DB_NAME=nazwa_bazy
DB_USER=postgres
DB_PASSWORD=haslo
DB_HOST=localhost
DB_PORT=5432
```

---

## Instalacja

```bash
git clone https://github.com/cnied/Licytacje-komornicze---scraper.git
cd Licytacje-komornicze---scraper
pip install -r requirements.txt
```

---

## Uruchomienie

```bash
python main.py
```

### Inne komendy
```bash
# Test połączenia z bazą
python -c "from src.db_connect import db_login; print(db_login())"

# Ręczne tworzenie tabel
python -c "from src.table_creation import create_tables_if_not_exists; from src.db_connect import db_login; conn, err = db_login(); create_tables_if_not_exists(conn, err)"

# Generowanie mapy
python -c "from src.mapka import update_the_map; update_the_map()"

# Uruchomienie testów
pytest tests/
```

---

## Struktura projektu

```
main.py                     # entrypoint
src/
  scraper.py                # główna logika scrapowania (API + AI fallback)
  email_parser.py           # parsowanie maili, regex dla linków
  login.py                  # IMAP Gmail
  ai_client.py              # komunikacja z Google Gemini AI
  data_transformer.py       # transformacja danych AI → format API
  category_service.py       # obsługa kategorii aukcji
  db_connect.py             # połączenie z PostgreSQL
  db_fulfill.py             # zapis danych do bazy
  table_creation.py         # tworzenie tabel
  geocoding.py              # geokodowanie adresów (Geoapify API)
  mapka.py                  # generowanie interaktywnej mapy (Folium)
  logger.py                 # konfiguracja logowania
tests/                      # testy jednostkowe (pytest)
logs/                       # pliki logów (YYYY-MM-DD.log)
.env                        # zmienne środowiskowe
```

---

## Schemat bazy danych

- `auction_item` - główna tabela aukcji
- `auction_item_address` - adresy nieruchomości
- `auction_attachment` - załączniki (zdjęcia)
- `auction_additional_param` - parametry (powierzchnia, pokoje, rok budowy)
- `item_category` - kategorie (mieszkania, domy, grunty, maszyny)
- `bailiff_data` - dane komorników

---

## Bezpieczeństwo

Plik `.env` **nie może trafić do repozytorium**.
Dodaj go do `.gitignore`.

---

## Roadmapa

- [x] Podstawowy scraping HTML
- [x] Integracja z Gemini AI
- [x] API elicytacje.komornik.pl
- [x] Baza danych PostgreSQL
- [x] System logowania
- [x] Geokodowanie adresów
- [x] Testy jednostkowe
- [x] Interaktywna mapa (Folium)
- [ ] Dashboard / UI
- [ ] Filtrowanie i wyszukiwanie
- [ ] Powiadomienia o nowych aukcjach

**Aktualny postęp: ~85%**

---

## Licencja

Open Source
