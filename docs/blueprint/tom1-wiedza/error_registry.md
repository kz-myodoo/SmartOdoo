# 🐛 Error Registry — Powtarzające się Problemy

> **Cel:** Identyfikacja wzorców błędów, aby `/arch` mógł im zapobiegać w planach.
> **Zasada:** QA dodaje wpis po review z verdyktem ⚠️ lub ❌.
> **Reguła 3x:** Jeśli błąd pojawia się 3x+ → `/arch` MUSI dodać jawną instrukcję w Pattern Registry.

---

## Aktywne Wzorce Błędów

| ID | Kategoria | Opis | Sprinty | Ile razy | Status |
|----|-----------|------|---------|----------|--------|
| _E001_ | _np. Naming_ | _np. Dev nie trzymał się camelCase_ | _SO-01_ | _1x_ | _🟢 Jednorazowy_ |
| E002 | Monorepo Deps | NPM hoisting conflict — phantom deps, major version split (np. Tailwind v3 i v4), wyciek do roota | SO-12 Zdalna | 1x | 🔴 Systemowy |

**Statusy:**
- 🟢 Jednorazowy — pojawił się raz, monitorujemy
- 🟡 Powtarza się (2x) — uwaga, może być trendem
- 🔴 Systemowy (3x+) — **WYMAGA interwencji /arch** (Pattern Registry update)
- ✅ Rozwiązany — dodano do Pattern Registry, nie powtarza się

---

## Rozwiązane Wzorce (archiwum)

| ID | Kategoria | Opis | Rozwiązanie | Sprint rozwiązania |
|----|-----------|------|-------------|-------------------|
| E002 | Monorepo Deps | NPM hoisting conflict... | Ścisła izolacja (Strict Workspace Isolation). Zero app-deps w roocie. `npm install` czyszczący stare cache. Wprowadzenie "Version Contracts" w PROJECT_SKILLS.md | Deploy Guard |

---

## Jak używać?

### `/qa` — po review:
1. Znajdź kategorię błędu (naming, imports, error handling, security, testy, types, async)
2. Sprawdź czy ID już istnieje → jeśli tak, zwiększ "Ile razy" i dodaj sprint
3. Jeśli nowy → dodaj nowy wiersz z kolejnym ID
4. Zmień status jeśli przekroczono próg (2x → 🟡, 3x → 🔴)

### `/arch` — na starcie sprintu:
1. Przeczytaj tabelę — zwróć uwagę na 🔴 i 🟡
2. Dla 🔴: dodaj jawną instrukcję w Pattern Registry lub DoD zadania
3. Po dodaniu do Pattern Registry → przenieś do "Rozwiązane" ze statusem ✅

---
📅 *Utworzono: 2026-03-05 | TeamEngine v3.0*

