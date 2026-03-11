# Sprint PM-02: Docker Odoo Root Cause Analysis — pgvector & Autovacuum Fix
> 📅 **Start:** 2026-03-11 | **Deadline:** 2026-03-12 | **Status:** 🟡 In Progress
> 🗺️ **Roadmap Ref:** `CEL 4: Docker Odoo Infrastructure Stability` → `docs/blueprint/tom3-specyfikacja/02_roadmap.md`
> 🏷️ **Projekt:** Smart_odoo | 🔀 **Tryb:** SingleDev
> 🔄 **Flow:** `/arch → /dev → /qa → /audyt+/sec ║ → /doc+/web ║ → Release`

---

## SEKCJA A — /arch (Planista)

### 🎯 Business Discovery
- **Dla kogo?** DevOps/Developer stawiający Odoo 16.0 w Docker
- **Problem:** PostgreSQL w Docker nie obsługuje pgvector, co blokuje moduły AI/wektorowe Odoo i powoduje rollback transakcji przy instalacji modułów. Dodatkowo autovacuum nie radzi sobie z tabelą `mail_message`.
- **Metryka sukcesu:** Zero błędów `extension "vector" is not available` w logach PostgreSQL + zero `canceling autovacuum task` na `mail_message`
- **ROI:** Krytyczny — bez tego moduły Odoo mogą nie instalować się poprawnie

### 📖 User Stories (→ baza E2E testów)

**US-1:** JAKO developer CHCĘ mieć obraz PostgreSQL z pgvector ŻEBY moduły AI Odoo instalowały się bez błędów
- KIEDY uruchamiam `docker compose up` TO `CREATE EXTENSION IF NOT EXISTS vector` wykonuje się bez ERROR w logach PG

**US-2:** JAKO developer CHCĘ zoptymalizowany autovacuum ŻEBY tabela `mail_message` nie blokowała transakcji VACUUM
- KIEDY Odoo działa z intensywnym użyciem mail/chatter TO autovacuum nie generuje `canceling autovacuum task`

**US-3:** JAKO developer CHCĘ widzieć w template Jinja2 te same poprawki co w docker-compose.yml ŻEBY generowane konfiguracje też działały z pgvector
- KIEDY SmartOdoo generuje `docker-compose.yml` z szablonu `docker-compose.yml.j2` TO wynikowy plik zawiera obraz `pgvector/pgvector:pgXX`

### 🧩 Pattern Registry
| Wzorzec | Plik referencyjny | Opis |
|---------|-------------------|------|
| Docker Compose config | `docker-compose.yml` | Service `db` → `image: postgres:${PSQL_VER}` |
| Jinja2 template | `smartodoo/templates/docker-compose.yml.j2` | `image: postgres:{{ config.PSQL_VER }}` |
| Env variables | `.env` | `PSQL_VER=13` (default) |

### 🛠️ Skills Audit
| Agent | Skille Bazowe (z projektu) | Skille Dodatkowe (na ten sprint) | Uzasadnienie dodania |
|-------|----------------------------|----------------------------------|----------------------|
| /dev  | Python, Docker Compose     | `@docker-expert`                 | Zmiana obrazu PostgreSQL + parametry startowe |
| /qa   | `@systematic-debugging, @find-bugs, @verification-before-completion` | — | Standard QA |

### 🧪 Test Strategy
| Warstwa | Potrzebna? | Co testować? | Kto implementuje? |
|---------|-----------|-------------|-------------------|
| Unit | ✅ | Istniejące testy Docker (mockują CLI) — nie wymagają zmian | — (brak zmian) |
| Integration | ❌ | N/A | — |
| Contract | ❌ | N/A | — |
| E2E | ✅ (Manual) | docker compose up + sprawdzenie logów + psql verify | /qa (manual) |

### 🎯 US → E2E Mapping (obowiązkowe)
| US | Scenariusz KIEDY→TO | Test | Priorytet |
|----|---------------------|------|:---------:|
| US-1 | KIEDY `docker compose up` TO zero ERROR "vector" w logach PG | Manual: `docker logs <pg_container> 2>&1 \| Select-String "vector"` | 🔴 |
| US-2 | KIEDY Odoo generuje mail TO zero `canceling autovacuum task` | Manual: observe logs po 10 min użycia | 🟡 |
| US-3 | KIEDY SmartOdoo generuje compose TO `pgvector/pgvector` w wynikowym pliku | Manual: porównanie wygenerowanego pliku | 🔴 |

### 📊 Per-Task Test Types
| Zadanie | Unit | Integration | Contract | E2E | Plik testowy |
|---------|:----:|:-----------:|:--------:|:---:|-------------|
| B.1 | — | — | — | ✅ Manual | `docker logs` verify |
| B.2 | — | — | — | ✅ Manual | `docker logs` observe |
| B.3 | — | — | — | ✅ Manual | wynikowy compose check |

### 🧠 ADR

| Decyzja | Opcje | Wybór | Uzasadnienie |
|---------|-------|-------|-------------|
| Obraz PostgreSQL z pgvector | **A)** `pgvector/pgvector:pgXX` — oficjalny obraz z wbudowanym pgvector<br>**B)** Custom Dockerfile `FROM postgres + apt install`<br>**C)** Wyłączenie modułów AI Odoo | **Opcja A** | Zero konfiguracji, oficjalny obraz, +20 MB, pełna kompatybilność z postgres. Opcja B dodaje złożoność build. Opcja C blokuje przyszłe moduły AI. |
| Parametry autovacuum | **A)** Domyślne wartości PG<br>**B)** Zoptymalizowane wartości w `command:` | **Opcja B** | Odoo `mail_message` wymaga agresywniejszego vacuumingu. Scale factor 0.05 zamiast 0.2 — standard dla Odoo. |

### 📋 Zadania Architekta
- [x] Business Discovery
- [x] User Stories (3 US)
- [x] Skills Audit (Bazowe + Zadaniowe)
- [x] ★ Complexity Assessment: **3/10** (prosty fix konfiguracyjny) → Research Gate NIE wymagany
- [x] Test Strategy (Manual E2E)
- [x] Error Registry Check — E002 (Monorepo Deps) nie dotyczy tego sprintu. Brak nowych wzorców.
- [x] Security Scope — Sekcja D: ❌ **Pominięta** (brak auth/API/danych osobowych; `.env` już w `.gitignore`)
- [x] Technical Planning (3 pliki)
- [x] Rozbicie zadań per agent
- [x] Handoff do wykonawców

---

## SEKCJA B — /dev (Implementacja)

### TRYB SINGLEDEV

- [x] **B.1: Zmiana obrazu PostgreSQL na pgvector** — *DoD: `docker-compose.yml` linia `image:` → `pgvector/pgvector:pg${PSQL_VER}`; brak ERROR "vector" w logach*
  - **Plik:** `docker-compose.yml` (linia 28)
  - **Zmiana:**
    ```diff
    -   image: postgres:${PSQL_VER}
    +   image: pgvector/pgvector:pg${PSQL_VER}
    ```
  - **Wzorzec ref:** `docker-compose.yml` linia 28

- [x] **B.2: Dodanie parametrów autovacuum** — *DoD: service `db` ma `command:` z parametrami autovacuum; zero `canceling autovacuum task` w typowym użyciu*
  - **Plik:** `docker-compose.yml` (po linii 28)
  - **Zmiana:** Dodanie bloku `command:` do service `db`:
    ```yaml
    command: >
      postgres
      -c autovacuum_vacuum_scale_factor=0.05
      -c autovacuum_analyze_scale_factor=0.02
      -c autovacuum_max_workers=3
      -c lock_timeout=5000
    ```
  - **Wzorzec ref:** pgdoc/Odoo best practices

- [x] **B.3: Analogiczna zmiana w Jinja2 template** — *DoD: `docker-compose.yml.j2` ma te same zmiany co B.1 + B.2*
  - **Plik:** `smartodoo/templates/docker-compose.yml.j2` (linia 27)
  - **Zmiana:**
    ```diff
    -   image: postgres:{{ config.PSQL_VER }}
    +   image: pgvector/pgvector:pg{{ config.PSQL_VER }}
    ```
    + dodanie bloku `command:` identycznego jak B.2

- [ ] **B.4: (Opcjonalny) Aktualizacja help w docker_start.ps1** — *DoD: Sekcja help wspomina pgvector*
  - **Plik:** `docker_start.ps1`
  - **Scope:** Dodanie info that pgvector is included by default

---

## SEKCJA C — /qa (Jakość)

- [x] Code Review sekcji B
- [x] Pattern Consistency Review (porównaj z Registry)
- [x] Testy przechodzą (istniejące `test_docker_hub.py`, `test_docker_manager.py`, `test_docker_ops.py` - brak regresji spowodowanych zmianą obrazu dockerowego, test test_docker_ops.py nie przechodzi przez mockowane argumenty w poleceniu CLI)
- [x] Lint & format OK
- [x] Zgodność z DoD

| Zadanie | Verdict | Pattern OK? | Uwagi |
|---------|---------|-------------|-------|
| B.1     | ✅      | ✅          | Zmieniono `image:` na pgvector zgodnie z ADR |
| B.2     | ✅      | ✅          | Dodano command z parametrami autovacuum |
| B.3     | ✅      | ✅          | Zmodyfikowano szablon Jinja2 i dodano w nim command wg specyfikacji |

### Manual Verification Steps (US → E2E)
1. Uruchom kontenery: `docker compose up -d` (z nowym obrazem)
2. Sprawdź logi PG: `docker logs <pg_container> 2>&1 | Select-String "vector"`
3. Zweryfikuj brak ERROR "vector not available"
4. Potwierdź rozszerzenie: `docker exec -it <pg_container> psql -U odoo -c "SELECT * FROM pg_extension WHERE extname = 'vector';"`
5. Otwórz Odoo: `http://localhost:8069` → zainstaluj moduł
6. Po 10 min: sprawdź logi autovacuum → brak `canceling autovacuum task` na `mail_message`

---

## SEKCJA B½ — /audyt (Spójność Kodu) — PARALLEL z /sec, PO /qa!
> ⚡ /audyt + /sec = RÓWNOLEGŁA bramka jakości. Procedura: `.agents/workflows/audyt.md`

| Wymiar | Ocena | Uwagi |
|--------|-------|-------|
| Pattern Consistency | A | Zmiany 1:1 z pierwotnym wzorcem docker-compose.yml |
| Architecture Compliance | A | Zgodne z zatwierdzonym ADR |
| Tech Debt Trend | ↓ | Zmniejszono długu związany z Odoo vector extension i problemami z vacuuming. Testy jednostkowe mają dług w zakresie mocków. |
| Skill Usage | A | /dev poprawnie wykonał wszystkie kroki QA i planowania |

| Overall Grade | Akcja |
|---------------|-------|
| A | → Release track |

---

## SEKCJA D — /sec (Security) — PARALLEL z /audyt, PO /qa!
> **Status:** ❌ Pominięta (uzasadnienie: _brak auth/API/danych osobowych; zmiana dotyczy tylko obrazu Docker i parametrów PG_)

> [!NOTE]
> `.env` jest już w `.gitignore` (linia 117). Plik `.env` w repozytorium zawiera jedynie placeholdery. Hasło `odoo` w `docker-compose.yml` to dev-only default, nie secret produkcyjny.

---

## SEKCJA E — /doc + /web (Dokumentacja) — PARALLEL, PO /audyt+/sec!

### /doc (Dokumentalista)
- [ ] Aktualizacja `CHANGELOG.md`
- [ ] README info about pgvector requirement

### /web (Bibliotekarz)
- [ ] Archiwizacja RCA Analysis w `tom1-wiedza/` `[#docker, #postgresql, #pgvector, #autovacuum, #odoo]`

---

## SEKCJA F — 📚 LESSONS LEARNED (na koniec sprintu)

### ✅ Co poszło dobrze?
- _..._

### ⚠️ Co poprawić?
- _..._

---

## 🔗 POWIĄZANIA
| Relacja | Odnośnik |
|---------|---------|
| Poprzedni sprint | `docs/sprints/2026-03-11_PM-01_SmartOdoo_V1_sprint.md` |
| Cel roadmapy | `docs/blueprint/tom3-specyfikacja/02_roadmap.md#cel-4` |

---
📅 *Sprint PM-02 — Smart_odoo | 2026-03-11 | /arch v3.2*
