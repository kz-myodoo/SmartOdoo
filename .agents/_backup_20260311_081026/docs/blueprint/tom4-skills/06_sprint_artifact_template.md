# 📋 Sprint Artifact v3 — Szablon (Lean)
> **Wersja:** 3.2 | **Data:** 2026-03-11
> **Lokalizacja:** `docs/sprints/PM-[NR]_[temat]_sprint.md`

---

## INSTRUKCJA

1. Skopiuj ten plik do `docs/sprints/PM-[NR]_[temat]_sprint.md`
2. `/arch` wypełnia Sekcję A (cel, user stories, plan)
3. Każdy agent aktualizuje SWOJE checkboxy `[ ]` → `[x]` po wykonaniu

**Tryb MultiDev (opcjonalny):** Gdy zadanie jest duże → `/arch` rozbija Sekcję B na B1/B2/B3. Każdy dev ma własny Scope (folder) i checkboxy. Pliki się NIE mogą pokrywać.

---

# Sprint PM-[NR]: [NAZWA]
> 📅 **Start:** YYYY-MM-DD | **Deadline:** YYYY-MM-DD | **Status:** 🟡 In Progress
> 🗺️ **Roadmap Ref:** `[Cel z roadmapy]` → `docs/blueprint/tom3-specyfikacja/02_roadmap.md`
> 🏷️ **Projekt:** [Nazwa] | 🔀 **Tryb:** SingleDev | MultiDev
> 🔄 **Flow:** `/arch → /dev → /qa → /audyt+/sec ║ → /doc+/web ║ → Release`

---

## SEKCJA A — /arch (Planista)

### 🎯 Business Discovery
- **Dla kogo?** [Odbiorca]
- **Problem:** [1 zdanie]
- **Metryka sukcesu:** [Jak mierzymy?]
- **ROI:** [Wartość > koszt?]

### 📖 User Stories (→ baza E2E testów)

**US-1:** JAKO [kto] CHCĘ [co] ŻEBY [dlaczego]
- KIEDY [warunek] TO [wynik]

**US-2:** JAKO [kto] CHCĘ [co] ŻEBY [dlaczego]
- KIEDY [warunek] TO [wynik]

### 🧩 Pattern Registry
| Wzorzec | Plik referencyjny | Opis |
|---------|-------------------|------|
| _np. Router_ | _src/auth/router.ts_ | _Router → Service → Repo_ |

### 🛠️ Skills Audit
| Agent | Skille Bazowe (z projektu) | Skille Dodatkowe (na ten sprint) | Uzasadnienie dodania |
|-------|----------------------------|----------------------------------|----------------------|
| /dev  | _@react-patterns_          | _@stripe-integration_            | _Sprint oznaczający płatności_ |
| /qa   | _@playwright-skill, @systematic-debugging, @find-bugs, @verification-before-completion, @test-fixing, @e2e-testing-patterns_ | — | _Pełny zestaw QA_ |

### 🧪 Test Strategy
| Warstwa | Potrzebna? | Co testować? | Kto implementuje? |
|---------|-----------|-------------|-------------------|
| Unit | ✅ | _[logika, walidacja]_ | /dev (TDD Red Phase) |
| Integration | ✅/❌ | _[połączenia między modułami]_ | /dev |
| Contract | ✅/❌ | _[interfejsy API, schematy]_ | /dev |
| E2E | ✅ | _[scenariusze z User Stories → patrz mapping]_ | /qa |

### 🎯 US → E2E Mapping (obowiązkowe)
| US | Scenariusz KIEDY→TO | Plik E2E testu | Priorytet |
|----|---------------------|----------------|:---------:|
| US-1 | _KIEDY [warunek] TO [wynik]_ | _test_xxx.test.ts_ | 🔴 |
| US-2 | _KIEDY [warunek] TO [wynik]_ | _test_yyy.test.ts_ | 🔴 |

### 📊 Per-Task Test Types
| Zadanie | Unit | Integration | Contract | E2E | Plik testowy |
|---------|:----:|:-----------:|:--------:|:---:|-------------|
| _B1.1_ | ✅ | ✅ | — | — | _test_xxx.py_ |
| _B1.2_ | ✅ | — | — | ✅ | _test_yyy.test.ts_ |

### 🧠 ADR (jeśli complexity > 5)
| Decyzja | Wybór | Uzasadnienie |
|---------|-------|-------------|

### 📋 Zadania Architekta
- [ ] Business Discovery
- [ ] User Stories (min. 3)
- [ ] Skills Audit (Bazowe + Zadaniowe)
- [ ] ★ Complexity Assessment + Research Gate (jeśli ≥7 → /anal)
- [ ] Test Strategy (TDD + US→E2E Mapping + per-task types)
- [ ] Error Registry Check (`tom1-wiedza/error_registry.md`)
- [ ] Security Scope (Sekcja D obowiązkowa? /sec + /anal research?)
- [ ] Technical Planning (L1-L5)
- [ ] Rozbicie zadań per agent (z przypisanymi typami testów)
- [ ] Handoff do wykonawców

---

## SEKCJA B — /dev (Implementacja)

> **Wybierz tryb:** SingleDev (domyślna lista) lub MultiDev (B1/B2/B3).

### TRYB SINGLEDEV
- [ ] **Zadanie 1:** [Opis] — *DoD: [kryterium]*
- [ ] **Zadanie 2:** [Opis] — *DoD: [kryterium]*
- [ ] **Zadanie 3:** [Opis] — *DoD: [kryterium]*

---

### 🔀 TRYB MULTIDEV

#### B1 — /dev1: [Moduł]
- **📁 Scope:** `src/[folder1]/*`
- [ ] **Zadanie 1:** [Opis] — *DoD: [kryterium]*
- [ ] **Zadanie 2:** [Opis] — *DoD: [kryterium]*

#### B2 — /dev2: [Moduł]
- **📁 Scope:** `src/[folder2]/*`
- [ ] **Zadanie 1:** [Opis] — *DoD: [kryterium]*
- [ ] **Zadanie 2:** [Opis] — *DoD: [kryterium]*

#### B3 — /dev3: [Moduł] ⚡ OPCJONALNA
- **📁 Scope:** `src/[folder3]/*`
- [ ] **Zadanie 1:** [Opis] — *DoD: [kryterium]*

---

## SEKCJA C — /qa (Jakość)

- [ ] Code Review sekcji B
- [ ] Pattern Consistency Review (porównaj z Registry)
- [ ] Testy przechodzą
- [ ] Lint & format OK
- [ ] Zgodność z DoD

| Zadanie | Verdict | Pattern OK? | Uwagi |
|---------|---------|-------------|-------|

---

## SEKCJA B½ — /audyt (Spójność Kodu) — PARALLEL z /sec, PO /qa!
> ⚡ /audyt + /sec = RÓWNOLEGŁA bramka jakości. Procedura: `.agents/workflows/audyt.md`

| Wymiar | Ocena | Uwagi |
|--------|-------|-------|
| Pattern Consistency | [A-F] | |
| Architecture Compliance | [A-F] | |
| Tech Debt Trend | [↑/↓/→] | |
| Skill Usage | [A-F] | |

| Overall Grade | Akcja |
|---------------|-------|
| A-B | → Release track |
| C | → Quick fixy, potem release |
| D-F | → Odrzucenie do /dev |

---

## SEKCJA D — /sec (Security) — PARALLEL z /audyt, PO /qa!
> **Status:** ✅ Obowiązkowa / ❌ Pominięta (uzasadnienie: _[brak auth/API/danych osobowych]_)
> ⚡ /audyt + /sec = RÓWNOLEGŁA bramka jakości. Procedura: `.agents/workflows/sec.md`

### Wyniki audytu (wypełnia /sec wg STRIDE + Checklist z sec.md)
| Obszar | Verdict | Uwagi |
|--------|---------|-------|
| STRIDE | | |
| Zależności (CVE) | | |
| Kod (walidacja, sekrety) | | |
| Research (/anal) | | |

| Verdict końcowy | Akcja |
|-----------------|-------|
| ✅ Bezpieczne | → Release dozwolony |
| ⚠️ Niskie ryzyko | → Fix w następnym sprincie |
| ❌ VETO | → **BLOKADA**. Odesłanie do /dev |

---

## SEKCJA E — /doc + /web (Dokumentacja) — PARALLEL, PO /audyt+/sec!

### /doc (Dokumentalista)
- [ ] Aktualizacja `00_master_knowledge_map.md`
- [ ] README / docstring dla nowych modułów
- [ ] Changelog

### /web (Bibliotekarz)
- [ ] Archiwizacja wiedzy w Tomach 1-5
- [ ] Tagowanie nowych wpisów `[#tag1, #tag2]`
- [ ] Aktualizacja `00_master_knowledge_map.md` (sekcja biblioteki)

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
| Poprzedni sprint | `docs/sprints/PM-[NR-1]_...` |
| Cel roadmapy | `docs/blueprint/tom3-specyfikacja/02_roadmap.md#[cel]` |

---
📅 *Szablon v3.0 (Lean) — TeamEngine | 2026-03-05*
