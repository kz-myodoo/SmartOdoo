# Sprint PM-01: Wdrożenie SmartOdoo v1 (Perfect Architecture)
> 📅 **Start:** 2026-03-11 | **Deadline:** 2026-03-15 | **Status:** 🟡 In Progress
> 🗺️ **Roadmap Ref:** `Stabilny CLI dla Odoo 16/18` -> `docs/blueprint/tom3-specyfikacja/02_roadmap.md`
> 🏷️ **Projekt:** SmartOdoo v1 | 🔀 **Tryb:** MultiDev
> 🔄 **Flow:** `/arch → /dev → /qa → /audyt+/sec ║ → /doc+/web ║ → Release`

---

## SEKCJA A — /arch (Planista)

### 🎯 Business Discovery
- **Dla kogo?** Programiści, administratorzy serwera, liderzy techniczni.
- **Problem:** Środowisko do stawiania Odoo (SmartOdoo) po refaktorze utraciło funkcje kluczowe (brak 9 zmiennych w .env, utrata opcji restore DB+filestore, bugi w LF w bashu). Musimy scalić dobre strony oryginału i refaktora w jedną doskonałą aplikację CLI.
- **Metryka sukcesu:** Czas postawienia odzyskiwanego zrzutu DB z filestorem < 5 minut poprzez wywołanie 1 komendy. Poprawne wygenerowanie 15/15 zmiennych .env. Brak buga `\r` (CRLF).
- **ROI:** Bardzo wysoki (eliminacja powtarzalnych, frustrujących ręcznych prac).

### 📖 User Stories (→ baza E2E testów)
**US-1:** JAKO programista CHCĘ wygenerować kompletny plik .env dla Odoo 16 ŻEBY kontener wstał bez błędu braku poświadczeń. 
- KIEDY uruchamiam `so create --name test` TO generuje się .env z 15 zdefiniowanymi zmiennymi.

**US-2:** JAKO administrator CHCĘ odtworzyć środowisko klienta z pliku dump.sql i katalogu filestore ŻEBY mieć pełną działającą kopię.
- KIEDY uruchamiam `so restore --dump d.sql --filestore f/ --db test` TO baza jest odtworzona, filestore przegrany, a hasło dla admina zresetowane.

**US-3:** JAKO użytkownik Windows CHCĘ by pliki SH były formatowane pod Linuksa ŻEBY kontener Docker bash nie rzucał błędami interpretera `\r\n`.
- KIEDY plik `entrypoint.sh` jest renderowany z templatki TO zapisywany jest zawsze ucięty z LF na końcu.

### 🧩 Pattern Registry
| Wzorzec | Architektura | Opis |
|---------|--------------|------|
| Typer / Click CLI | CLI Interface | Do obsługi interfejsu wiersza poleceń zamiast argparse. Czyste komendy z argumentami. |
| Pydantic BaseSettings | Config | Konfiguracja, automatyczna walidacja typu i .env import. |
| Jinja2 Templates | Szablonowanie | Szablony `odoo.conf.j2`, `docker-compose.yml.j2`, bez kopiowania "na sztywno". |
| Docker SDK / subprocess | Ops | Klasa `DockerOps` odpowiadająca za interakcje (izolacja logiki by ją łatwo mockować w testach). |

### 🛠️ Skills Audit
| Agent | Skille Bazowe | Skille Dodatkowe | Uzasadnienie dodania |
|-------|---------------|------------------|----------------------|
| /dev  | @python-fastapi-development | @bash-linux, @docker-expert | Zadanie w dużej mierze oparte na bashu i powłokach kontenera. |
| /qa   | @playwright-skill | @systematic-debugging, @find-bugs | QA będzie testował E2E operacje na kontenerach (wywołując polecenia CLI w oparciu o mockowany system docelowy). |

### 🧪 Test Strategy
| Warstwa | Potrzebna? | Co testować? | Kto implementuje? |
|---------|-----------|-------------|-------------------|
| Unit | ✅ | `env_builder.py` (generacja 15 kluczy), parsing flag. | /dev (TDD Red Phase) |
| Integration | ✅ | Połączenie pomiędzy `cli` a `core/docker_ops.py` (nawet z mockami subprocesu). | /dev |
| Contract | ❌ | Brak REST API. | - |
| E2E | ✅ | Fizyczne wywołania komend `so create`, `so restore` z testowymi dumpami. | /qa |

### 🎯 US → E2E Mapping (obowiązkowe)
| US | Scenariusz KIEDY→TO | Plik E2E testu | Priorytet |
|----|---------------------|----------------|:---------:|
| US-1 | KIEDY uruchamiany `so create` TO pełny .env | `tests/e2e/test_cli_create.py` | 🔴 |
| US-2 | KIEDY uruchamiany `so restore` TO import DB | `tests/e2e/test_cli_restore.py` | 🔴 |
| US-3 | KIEDY generujemy plik bash TO zapis LF | `tests/e2e/test_platform_lf.py` | 🔴 |

### 📊 Per-Task Test Types
| Zadanie | Unit | Integration | Contract | E2E | Plik testowy |
|---------|:----:|:-----------:|:--------:|:---:|-------------|
| B1.1 Model Konfiguracji | ✅ | - | - | ✅ | `tests/unit/test_config.py` |
| B1.2 Szablony Jinja2 | ✅ | ✅ | - | ✅ | `tests/unit/test_templates.py` |
| B1.3 Normalizacja LF | ✅ | - | - | ✅ | `tests/unit/test_platform.py` |
| B2.1 Zarządzacz Dockerem | ✅ | ✅ | - | ✅ | `tests/unit/test_docker_ops.py` |
| B2.2 Operacje na DB (Przywracanie) | ✅ | ✅ | - | ✅ | `tests/unit/test_db_ops.py` |
| B3.1 Typer / CLI Router | ✅ | - | - | ✅ | `tests/unit/test_cli.py` |

### 🧠 ADR (jeśli complexity > 5)
| Decyzja | Wybór | Uzasadnienie |
|---------|-------|-------------|
| Subprocess vs DockerSDK | DockerSDK / wrapper Subprocess | Jeśli DockerSDK za trudny na instalację globalną, użyj solidnego subprocess wrappera typu `def run_docker(cmd: list)`. Wrapper pozwala mockować output subprocesu w pytest. |

### 📋 Zadania Architekta
- [x] Business Discovery
- [x] User Stories (min. 3)
- [x] Skills Audit
- [x] Complexity Assessment + Research Gate (Zatrwierdzone)
- [x] Test Strategy 
- [x] Error Registry Check (znane pułapki bugu linii znaków nowej LF vs CRLF na Windows i pustego env)
- [x] Security Scope (Bezpieczeństwo kontenerów i bazy, reset haseł skryptem .sql, uważać by logi Odoo nie wyrzucały envs)
- [x] Technical Planning (L1-L5)
- [x] Rozbicie zadań per agent
- [x] Handoff do wykonawców

---

## SEKCJA B — /dev (Implementacja)

> **Tryb MultiDev** (Moduły są częściowo ustrukturyzowane, więc praca równoległa wymaga uważnego interfejso-wania - jednak ze względu na mały zespół, opcjonalnie rozdzielone scope na core, ops, cli)

### B1 — /dev1: [Core Config & Templates]
- **📁 Scope:** `smartodoo/core/config.py`, `smartodoo/templates/`, `smartodoo/core/platform.py`
- [ ] **Zadanie 1:** Stwórz Pydantic BaseSettings wymuszający 15 kluczowych zmiennych dla środowiska Odoo. — *DoD: testy jednostkowe `test_config.py` przechodzą (Unit).*
- [ ] **Zadanie 2:** Przepisz `docker-compose.yml`, `odoo.conf`, `entrypoint.sh` na Jinja2 i zrób funkcję wyciągającą, wstrzykującą config. — *DoD: generowane pliki zawierają poprawne wartości.*
- [ ] **Zadanie 3:** Dodaj mechanizm LF enforcing (wymuszenie unix line endings `\n` nawet na Windows) dla `.sh` toolsów. — *DoD: `test_platform.py` udowadnia zapis po unixowemu.*

### B2 — /dev2: [Operations Ops]
- **📁 Scope:** `smartodoo/core/docker_ops.py`, `smartodoo/core/db_ops.py`
- [ ] **Zadanie 1:** Oprogramuj `DockerOps` odpowiadające za `docker compose up -d`, `docker stop`, `docker exec`. — *DoD: Wrapper działa i zwraca wynik tekstowy lub błąd.*
- [ ] **Zadanie 2:** Wdraż silnik nowej komendy `restore` z dump.sql wewnątrz kontenera, przy użyciu psql i drop DB z podmianą ról/uprawnień. — *DoD: Kod ma funkcję obsługującą plik lokalny z przeniesieniem i przywróceniem w Dockerxe.*
- [ ] **Zadanie 3:** Obsłuż kopiowanie wielkiego folderu filestore z dysku lokalnego do the kontenera `docker cp`. — *DoD: Plik fizycznie przeniesiony i nadpisane uprawnienia chown.*

### B3 — /dev3: [CLI Router & UX]
- **📁 Scope:** `smartodoo/cli.py`
- [ ] **Zadanie 1:** Przygotuj aplikację `click` / `typer` pod komendy `create`, `restore`, `start`. — *DoD: App odpala polecenia z poprawnymi flagami.*
- [ ] **Zadanie 2:** Złóż do kupy komponenty B1, B2. Skonfiguruj bogate komunikaty terminala `rich` (Rich library). — *DoD: UI nie wymaga PyGubu/Tkinter ale jest intuicyjne.*
- [ ] **Zadanie 3:** Przetestuj interakcje od startu do końca dla `--help` do poszczególnych komend. — *DoD: Zintegrowane E2E.*

---

## SEKCJA C — /qa (Jakość)
- [ ] Code Review sekcji B
- [ ] Pattern Consistency Review (porównaj z Registry)
- [ ] Testy przechodzą
- [ ] Lint & format OK
- [ ] Zgodność z DoD

---
## SEKCJA B½ — /audyt (Spójność Kodu)
| Wymiar | Ocena | Uwagi |
|--------|-------|-------|
| Pattern Consistency | | |
| Architecture Compliance | | |
| Tech Debt Trend | | |
| Skill Usage | | |

---
## SEKCJA D — /sec (Security)
> **Status:** ✅ Obowiązkowa (Praca operacyjna na lokalnym środowisku i hasłach systemowych bazy DB/Enterprise Github token)

---
## SEKCJA E — /doc + /web (Dokumentacja)
### /doc (Dokumentalista)
- [ ] Aktualizacja `00_master_knowledge_map.md`
- [ ] README dla v1 przygotowane.
- [ ] Changelog

### /web (Bibliotekarz)
- [ ] Archiwizacja wiedzy w Tomach 1-5 (jeśli nowe wnioski dt. Docker z Windows)
- [ ] Tagowanie: [#smartodoo, #docker, #odoo, #devops]

---
## SEKCJA F — 📚 LESSONS LEARNED (na koniec sprintu)
### ✅ Co poszło dobrze?
- _..._
### ⚠️ Co poprawić?
- _..._
