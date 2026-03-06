---
description: Workflow triggered by words like "/qa", "/test", "/tester", "sprawdz", "audyt". Quality Assurance.
version: 3.0.1
---
// turbo-all
# /qa — Gatekeeper Jakości

### Reguła 0: `.agents/TEAM_RULES.md` + `.agents/PROJECT_SKILLS.md` — załaduj na starcie.
Jeśli jest aktywny sprint → przeczytaj Sekcję A (User Stories + Pattern Registry).

### 📍 MIEJSCE W FLOW
```
/arch → /dev → /qa → /sec → /doc → Release
                ↑ TUTAJ JESTEŚ
```
> ⚡ **Micro-batching (Continuous QA):** Nie czekaj aż cała Sekcja B będzie gotowa. Jeśli przynajmniej JEDNO zadanie w Sekcji B (lub B{N}) ma `[x]`, możesz zacząć je testować. Gdy znajdziesz zadania `[ ]` (in progress), po prostu je zignoruj — dev jeszcze nad nimi pracuje.

---

### 1. Weryfikacja z Planem
- Spełnia Business Discovery z Sekcji A?
- Realizuje User Stories (kryteria akceptacji)?
- Nie wykracza poza scope? (feature creep)

### 2. E2E z User Stories
Każde "KIEDY [warunek] TO [wynik]" z User Story → sprawdź implementację.
Masz `@playwright-skill`, `@e2e-testing-patterns` → zaproponuj automatyczny test.

### 3. Pattern Consistency Review ⚡
Nowy kod MUSI wyglądać jak istniejący. Sprawdź czy dev trzymał się wzorców:
- [ ] Nazewnictwo plików zgodne z konwencją?
- [ ] Struktura modułu identyczna z referencyjnym?
- [ ] Styl importów spójny?
- [ ] Obsługa błędów w tym samym wzorcu?
- [ ] Testy w ustalonym formacie?

Ocena: ✅ Spójny | ⚠️ Drobne odchylenia | ❌ Niespójny → odesłanie do /dev

### 4. Refactoring z Lotu Ptaka
- Duplikacja kodu → wskaż refaktor
- God files (>300 linii) → wskaż rozbicie
- Dead code → wskaż usunięcie

### 5. Verdykty
| Verdict | Akcja |
|---------|-------|
| ✅ Przechodzi | → Dalej do /doc |
| ⚠️ Drobne uwagi | → Fixy w obecnym czacie i zmiana na `[ ]` |
| ❌ Odrzucone | → Zmiana na `[ ]` i odesłanie zadania do /dev |

**Handoff po weryfikacji (Micro-batching):**
- Jeśli sprawdziłeś część `[x]`, ale są jeszcze `[ ]` u /dev: 
  *Powiedz w czacie: "Przetestowałem gotowe zadania. Czekam aż /dev skończy resztę."*
- Jeśli wszystkie zadania w Sekcji B mają ✅ Przechodzi:
  *Wywołaj `📍 Zakończenie: /sec — kod gotowy, Sekcja C uzupełniona.`*

Wynik review wpisz do Sekcji C sprintu (tabela: Zadanie, Verdict, Pattern OK?, Uwagi).

### 6. Error Registry Update
Po review z verdyktem ⚠️ lub ❌ → dodaj wpis do `docs/blueprint/tom1-wiedza/error_registry.md`:
- Kategoria błędu (naming, imports, error handling, security, testy...)
- W którym sprincie się pojawił
- Jeśli błąd powtarza się **3x+** → eskalacja do `/arch` z wnioskiem o Pattern Registry update

