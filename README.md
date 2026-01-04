# 🏠 Inteligentny Scraper Licytacji Komorniczych

![Status](https://img.shields.io/badge/status-in%20progress-orange)
![Progress](https://img.shields.io/badge/progress-20%25-yellow)

🚧 **Projekt w trakcie rozwoju (20%)** 🚧

Automatyczne narzędzie do pobierania, analizowania i wizualizacji ogłoszeń o licytacjach komorniczych.  
Projekt wykorzystuje **AI (Google Gemini)**, **BeautifulSoup** i **geokodowanie**, a dane prezentuje na interaktywnej mapie.

---

## 🚀 Funkcje

### 📥 Pobieranie danych
- logowanie do konta Gmail przez IMAP  
- analiza newsletterów z portalu licytacje.komornik.pl

### 🧠 Inteligentna ekstrakcja treści
- dane z e-licytacji pobierane z HTML przez BeautifulSoup
- tekstowe obwieszczenia analizowane przez **Google Gemini AI**
- ekstrakcja: adres, cena wywoławcza, opis

### 📍 Geokodowanie
- zamiana adresów na współrzędne geograficzne

### 🗺 Wizualizacja
- analiza lokalizacji licytacji na mapie

---

## 🛠 Jak działa (ETL)

1. **Extract** – pobieranie maili  
2. **Transform** – analiza i normalizacja danych  
3. **Load** – zapis i wizualizacja

---

## 📋 Wymagania

### `credentials.yml`
```yaml
user: "twoj-email@gmail.com"
password: "twoje-haslo-aplikacji-google"
```

### `.env`
```
GEMINI_API_KEY=twoj_klucz_api_gemini
```

---

## 🧪 Instalacja

```bash
git clone https://github.com/cnied/Licytacje-komornicze---scraper.git
cd Licytacje-komornicze---scraper
pip install -r requirements.txt
```

---

## ▶️ Uruchomienie

```bash
python main.py
```

---

## 🧱 Struktura projektu

```
main.py          # entrypoint
bs4withAI.py     # scraper + AI
login.py         # IMAP
credentials.yml  # Gmail
.env             # API keys
database/        # dane historyczne
```

---

## 🛡 Bezpieczeństwo

Pliki `credentials.yml` i `.env` **nie mogą trafić do repozytorium**.  
Dodaj je do `.gitignore`.

---

## 🗺 Roadmapa

- [x] Podstawowy scraping HTML  
- [x] Integracja z Gemini AI  
- [ ] Stabilizacja parserów (WIP)  
- [ ] Geokodowanie zbiorcze  
- [ ] Interaktywna mapa  
- [ ] Dashboard / UI  

**Aktualny postęp: ~20%**

---

## 📝 Licencja

Open Source
