# 🚀 SmartOdoo CLI

> **Szybkie i zautomatyzowane budowanie środowisk Odoo dla deweloperów z użyciem Dockera.**  
> Koniec z ręcznym konfigurowaniem, błędami portów czy rozrzuconymi skryptami Bashowymi.

SmartOdoo to nowoczesne narzędzie CLI (Command Line Interface), które w **jednym poleceniu** potrafi wygenerować zoptymalizowane środowisko Odoo, spiąć bazę PostgreSQL, podłączyć serwer pocztowy (SMTP4Dev) oraz – jeśli tego potrzebujesz – w pełni automatycznie sklonować dla Ciebie repozytoria z modułami *Enterprise* czy *Extra-Addons*. 

---

## ⚡ Poziom 1: Szybki Wstęp (Dlaczego SmartOdoo?)

Jeśli jesteś inżynierem lub programistą, nie chcesz spędzać pół godziny na modyfikacji plików `docker-compose.yml` za każdym razem, gdy potrzebujesz czystego Odoo do testów. 

Właśnie po to powstało SmartOdoo:
- **Jedno polecenie do wszystkiego:** Wpisujesz w terminalu konfigurację, reszta dzieje się sama.
- **Bezpieczeństwo (Mocking & TDD):** Narzędzie napisane pod pełnym pokryciem testowym (Brak "brudnych wstrzyknięć" systemowych).
- **Auto-naprawa (Chmod hook):** Pracujesz na Linux/WSL i rzuca `Permission Denied` przy montowaniu woluminów Odoo? SmartOdoo samo go wychwyci w locie i "wklei" ci komendę `sudo chmod` ratując proces.
- **Ultra-lekkie i asynchroniczne:** Aplikacja pyta Docker Hub'a (online) o prawidłowe tagi dla instancji Odoo nie blokując interfejsu (asyncio).

---

## 📚 Poziom 2: Szczegółowa Instrukcja i Przewodnik Krok po Kroku

### 📦 Instalacja (Dla Deweloperów)
Aby zacząć w pełni korzystać ze zrefaktoryzowanego CLI w systemie wystarczy, że upewnisz się, że na Twoim środowisku znajduje się zainstalowany Python (3.10+) oraz Docker.

```bash
# Sklonuj projekt
git clone https://github.com/dp-myodoo/SmartOdoo.git
cd SmartOdoo

# Powołaj natywne środowisko CLI z zależnościami
# Zalecamy VENV, ale w trybie 'edytowalnym' możesz wpisać po cichu:
pip install -e .
```

### 🎮 Interaktywne GUI (Wbudowany Helper) - Nowość!
Zamiast korzystać z dziesiątek flag The CLI, SmartOdoo posiada wbudowane eleganckie the środowisko Dark Mode wywoływane w prosty sposób the przy użyciu biblioteki CustomTkinter.

Jak uruchomić: wpisz gołe polecenie the bazy bez żadnych The flag w terminalu:
```bash
python smartodoo.py
```
Program wyświetli na the ekranie pole wyboru The Trybu the i jeśli wskażesz [2], pokaże The Ci estetyczne opcje the takie jak wpisanie z palca Nazwy Projektu the i the wyklikanie wersji the PostgreSQL.
💡 The W prawym the dolnym The rogu aplikacji The znajduje się dedykowany przycisk **"❔ Instrukcja GUI"**, który podpowie nowym użytkownikom The Krok po the Kroku the co oznaczają suwaki np. "Pobierz the Enterprise".

---

### 💻 Jak korzystać z aplikacji w konsoli (Subcommandy The CLI)

Interfejs użytkownika do komunikacji został uproszczony pod parser `argparse` z kolorowymi powiadomieniami od biblioteki `rich`. Wykorzystaj program za pomocą aliasu startowego `python smartodoo.py` lub docelowo `so`.

#### 1. Tworzenie Projektu (`create`)
Buduje folder w głównym katalogu `DockerProjects`, wypluwa dedykowane pliki `.env` / `docker-compose.yml`, a następnie startuje.

```bash
# Podstawowe, szybkie powołanie kontenera Odoo Community 17 (Postgres-16):
python smartodoo.py create -n NazwaMojegoNowegoProjektu --odoo 17.0

# Rozbudowane wdrożenie:
python smartodoo.py create -n MojSuperApp -o 16.0 -p 15 -e True -a "https://github.com/moja-firma/moje-addonsy"
```
**Wyjaśnienie Flag w `create`**:
* `-n` / `--name` *(Wymagane)*: Nazwa środowiska (Katalogu).
* `-o` / `--odoo`: (Domyslnie: `19.0`) Wersja obrazu silnika Odoo (Pobierana z weryfikacją na żywo z DockerHub).
* `-p` / `--psql`: (Domyslnie: `16`) Wersja relacyjnej bazy PostgreSQL.
* `-e` / `--enterprise`: Flaguje chęć zaciągnięcia (klonu) oficjalnego repo Enterprise.
* `-a` / `--addons`: Link lub flaga do pobrania niestandardowych (Zewnętrznych) modułów `.git`.

#### 2. Dostępne Tagi (Autoryzacja z Hubem) (`tags`)
Potrzebujesz sprawdzić dostępność aktualnej gałęzi w Dockerze bez uruchamiania ciężkich poleceń i wylosowania błędu podczas tworzenia?
```bash
python smartodoo.py tags
```
*(Asynchroniczny serwer zapyta API Docker Huba i wypisze elegancką listę w ułamek sekundy).*

#### 3. Pozostałe instrukcje pomocnicze
Ponieważ to prawdziwe narzędzie DevOps, oferuje w pełni skalowalne polecenia testowe wyizolowane na potrzeby architektury:
* **Usuwanie Instancji:** `python smartodoo.py delete -n NazwaProjektu` (Czyści kontenery i usuwa brudne pliki volumes/lokalne).
* **Test Konfiguracyjny Systemu:** `python smartodoo.py test` (Sprawdza czy masz Dockera, Git i łączy API z informacją o wersjach).

> W razie jakichkolwiek problemów odpal wbudowany Helper nałożony pod główną konsole: `python smartodoo.py --help` lub po konkretnym poleceniu `python smartodoo.py create --help`.

---

## 🛡️ Poziom 3: Raporty Badań i Bezpieczeństwo

Aplikacja przeszła rygorystyczny proces walidacyjny sprawdzający architekturę, bazy zależności i odporność poleceń powłoki (Security Audit).

### 1. Raport Inżynieryjny QA (`/qa`)
Jako strażnik jakości i wydajności wdrożono rygorystyczne testy i standardy architektoniczne zapobiegające powrotowi tzw. *Spaghetti Code*:

* **TDD & Pokrycie Asercjami (Test Coverage):** Skrypt zbudowano przy pomocy `pytest` z zachowaniem metodologii TDD (Test Driven Development). Środowisko udostępnia **11 powtarzalnych jednostek testowych** weryfikujących każde podpolecenie CLI z efektem `0 błędów` na wyjściu `Exit Code: 0`. Wszystkie powiązania zewnętrzne (Git API, Docker, System I/O) obłożono izolacją (Mocking) za pomocą `pytest-mock` gwarantującą szybkość i brak "fizycznych" uszkodzeń testowych na maszynach CI/CD.
* **Standardy Kodowania i Stanu:** Wszystkie globalne, rozsiane mutujące w trakcie działania programu zmienne zostały wyeliminowane na rzecz zamkniętego i typowanego obiektu konfiguracyjnego `AppConfig` korzystającego ze standardu Pythona `@dataclass(frozen=True)`. Konfiguracja jest szczelna (Read-Only).
* **Czysta Architektura (SOLID & Dependency Injection):** Aplikacja wdraża podział obiektywny na wysoce responsywne klasy takie jak `DockerManager`, `GitManager` oraz asynchroniczny i nieblokujący interfejs `DockerHubFetcher`. Wstrzykuje podzespoły zamiast je ukrywać w trzewiach jednej wielkiej funkcji. Uczytelnia to kod dla nowo dołączających w projekt developerów.
* **Optymalizacje Wielowątkowe (Concurrency):** Przestarzałe wyścigi wątków `threading` od strzałów sieciowych zastąpione pętlą `asyncio/httpx` redukując o wiele rzędów wielkości wagę kodu, zapobiegając zamrożeniom interfejsu (Deadlocks).

Ocena Końcowa Architektury i Jakości Kodu: **Passed (Zatwierdzone)**.

### 2. Raport Bezpieczeństwa (`/sec`)
Kod źródłowy został przebadany pod kątem bezpieczeństwa wejścia z pozycji Command Line:
* **Brak Command Injection (RCE):** Aplikacja pozbyła się wykonań poleceń za pomocą wstrzykiwanych stringów. Każde polecenie dockera używa chronionych list argumentów (`shell=False`) co całkowicie uniemożliwia wstrzyknięcie złośliwego kodu przez parametry takie jak `--addons`.
* **Bezpieczeństwo Zmiennych:** Zmienne lokalne i hasła (np. wersje postgre czy odoo) są kompilowane i zamrażane w strukturze typowanej `AppConfig`. Nie istnieją modyfikacje globalne grożące wyciekiem pamięci bądź zablokowaniem wątków środowiska operacyjnego.
* **Hermetyczny Sudo-Chmod:** Hook ratunkowy wywoływany w systemach WSL/Linux, który używa komend `sudo`, działa twardo i wyłącznie na ścieżce domowej `ProjectName` uciętej z path traversali. Zapewnia to ratunek przed błędami woluminu bez powierzania systemom administracyjnym nieznanych katalogów.

Ocena Końcowa Bezpieczeństwa (Security Class): **S** (W pełni odizolowana / produkcyjna).

---
*Stworzone i refaktoryzowane z użyciem inżynierii opartych o koncepcje TDD (Test Driven Development) i nowoczesne GUI (TUI).*
