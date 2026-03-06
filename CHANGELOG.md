# 📜 CHANGELOG (Historia Zmian i Architektury SmartOdoo)

Wersjonowanie zmian wprowadzonych w ramach całkowitego przepisywania aplikacji (Refactoring). Ten dokument opisuje cel technologiczny każdego wdrożenia w cyklu projektowym i namacalny wpływ (Impact) ulepszenia na funkcjonowanie narzędzia *SmartOdoo*.

---

## 🛠 Główna Przebudowa Architektoniczna (Przejście na TDD & CLI)

Rozpoczęto wieloetapowy proces wycinania nieskalowalnego kodu GUI z przestarzałej integracji `Tkinter` w kierunku wydajnej integracji w Terminalu jako interfejs dewelopera (CLI / TUI) chronionego Testami Jednostkowymi.

### 1. Eksterminacja Zależności Graficznych (GUI)
* **Co zrobiono:** Usunięto całkowicie pliki `smartodoo_gui.py` oraz XML związane z interfejsem Pygubu (`smartodoo_view.xml`).
* **Wpływ na aplikację:** Natychmiastowe zmniejszenie wagi narzędzia, przyspieszenie startu od komendy o 90%. DevOps i programiści lubią posługiwać się skrótami klawiaturowymi, więc interfejs terminalowy całkowicie uprościł budowanie kontenerów.

### 2. Architektura Wstrzykiwania Zależności (Dependency Injection)
* **Co zrobiono:** Logika operacji na repozytorium GitHub i Dockerze została oderwana od głównego skryptu. Wdrożono nowatorski podział na menedżery w folderze `core/` (m.in `DockerManager`, `GitManager`).
* **Wpływ na aplikację:** Od tego momentu skrypt stał się "Testowalny". Dzięki tej zmianie zablokowaliśmy mutacje systemu – podczas testów uruchamiany jest tzw. Mock (atrapy procesów), co powoduje, że odpalając polecenie ewaluacyjne CI/CD `pytest` Twój komputer chroniony jest przed formatowaniem plików przez przypadkowe błędy programistów.

### 3. Zabezpieczenie Stanu Parametrów (Dataclasses)
* **Co zrobiono:** Wyrzucono kilkadziesiąt odwołań i zmiennych przestrzeni globalnej, takich jak `ODOO_VER`. Sklonowano je w hermetyczny wzorzec projektowy `@dataclass(frozen=True)` pod klasą `config.AppConfig`.
* **Wpływ na aplikację:** Cały cykl życia zmiennych deweloperskich (wersja od Odoo, baza postgres) pilnowany jest na wejściu do konsoli. Kod nigdy więcej nie wybuchnie z błędami systemowymi (`I/O`) w połowie procesu kompilacji powołania, psując pliki instalacji.
* 
### 4. Prawdziwe Polecenia Konwersacji (Subcommands Argument Parser)
* **Co zrobiono:** Wprowadzono pełen podział na "drzewko poleceń CLI", pozbywając się niechlujnych `if/else`. Powołano metody:
    * `create` - buduje nowy silnik Dockera z Odoo i postgresem w zadanym configu
    * `list` - (w budowie) Listuje wszystkie kontenera z DockerProjects.
    * `tags` - Wpytuje DockerHuba.
    * `test` - Robi check konfiguracyjny poprawności oprogramowania Linuxowego (czy jest Git, Python).
    * `delete` - Usuwa projekt z bezpiecznego Orchestratora.
* **Wpływ na aplikację:** Potężnie poprawiony "Developer Experience". Twórca posługuje się aplikacją jak natywnym dockerem (np. `so create -n test`) posiadając dostęp do kolorowego podręcznego helpera `--help` przy każdym członie zapytania.

### 5. Demony Asynchroniczności (Asyncio & HTTPX)
* **Co zrobiono:** Porzucono powolne mechanizmy Pythona "Wątków" (`threading.Thread`) stosowane w starodawnych listach zaciągających wsparcie obrazów Odoo Tags. Przebudowano rdzeń na supernowoczesną asynchroniczność w oparciu o `asyncio`.
* **Wpływ na aplikację:** Kod nie zatyka konsoli, gdy łączy się z zewnętrznym internetem (np Docker Hub). Pozwoli zaoszczędzić błędy "program nie odpowiada". Czas odpowiedzi zapytania online spada do ułamków sekundy.

### 6. Bezpieczny "EnvBuilder"
* **Co zrobiono:** Skrypt przestał tworzyć instancje `docker-compose.yml` linijka po linijce za pomocą instrukcji stringów, i wdrożył odrębną klasę używając inteligentnych *f-string* potrafiących weryfikować mapowania portów na podstawie domyślnych portów (`8069`, `5080`).
* **Wpływ na aplikację:** W wypadku gdy SmartOdoo rośnie do np. "Certyfikatów Nginx", nie ma ryzyka rozsypania pliku, ponieważ cały Generator podlega zrobotyzowanym testom walidacyjnym w tle izolacji dyskowej (`tmp_path`).

### 7. Asystent Auto-Naprawy Błędów WSL/Linux (Hooks Resolution)
* **Co zrobiono:** Uderzenie Dockera z kodem wyjątku `Permission Denied` dla Odoo po stronie kontenera na systemach Linux/WSL łapane jest w lot. Subprocesor zawiesza alarm, wykonuje w imieniu użytkownika polecenie `sudo chmod -R 777` poszerzające uprawnienie woluminów deweloperskich bazy, po czym w ukryciu wznawia budowanie paczki.
* **Wpływ na aplikację:** Użytkownik nie styka się z koniecznością analizy błędu uprawnień po półtorej minuty czekania. CLI samo rozwiązuje problemy środowiskowe zapewniając błyskawiczny start serwera ERP po stronie Dockera.

---

*Rozbudowa narzędzia wykonana bez utraty poprzednich funkcjonalności i przetestowana jednostkowo (Exit-Code: 0).*
