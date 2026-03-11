# 🚀 TeamEngine — Silnik Orkiestracji v3.2 (Lean)

> **Cel:** Jeden silnik zarządza zespołem agentów AI. Klonowalny na dowolny projekt.
> **Wersja:** 3.2 | **Data:** 2026-03-11

---

## Co to jest?

**TeamEngine** = `create-react-app` dla zarządzania projektem z AI. Zamienia pojedynczego bota w zespół (PM, Architekt, Dev, QA, Security, Dokumentalista, Analityk).

**Kluczowe elementy:**
1. `TEAM_RULES.md` — Konstytucja zespołu
2. `.agents/workflows/` — Mózg każdego agenta
3. Sprint Artifact v3 — Checkboxy per agent (bez ceremonii)
4. Roadmapa — Cele strategiczne powiązane ze sprintami
5. `TeamEngine/scripts/` — Deploy i Update

---

## Użycie

W rozmowie: **`deploy engine`** lub **`/pm`** → poprowadzi (komendy PowerShell w `.agents/workflows/pm.md`).

---

## Co się kopiuje?

### ✅ CORE (aktualizowalna)
| Element | Opis |
|---------|------|
| `.agents/TEAM_RULES.md` | Kompaktowa konstytucja |
| `.agents/workflows/*.md` | pm, arch, dev, qa, audyt, sec, anal |
| `TeamEngine/` | Skrypty + dokumentacja |

### ✅ SZABLONY (reset treści)
| Element | Opis |
|---------|------|
| `docs/blueprint/00_master_knowledge_map.md` | Spis treści |
| `docs/blueprint/tom1-5/` | Puste katalogi |
| `docs/blueprint/tom4-skills/06_sprint_artifact_template.md` | Sprint v3 |

### ❌ NIE KOPIOWANE
Treść Tomów 1-5, raporty sprintów, PROJECT_SKILLS.md

---

## Architektura dwóch warstw

```
┌──────────────────────── CORE (aktualizowalna) ─┐
│  TEAM_RULES.md  ·  workflows/*.md  ·  TeamEngine/  │
├──────────────────────── PROJECT (chroniona) ────┤
│  PROJECT_SKILLS.md  ·  docs/blueprint/*  ·  docs/sprints/*  │
└─────────────────────────────────────────────────┘
```

Update nadpisuje CORE, chroni PROJECT. Backup automatyczny.

### Flow agentów (Variant B + Research Gate v3.2)
```
              ┌─ /anal (research) ─┐
/arch ────────┤ (jeśli complexity≥7)├──→ /dev (TDD) → /qa (systematic 7-step)
              └────────────────────┘        │              │
                                            │    ┌─ /audyt (spójność) ─┐   ┌─ /doc ─┐
                                            └───→┤                     ├→  ┤        ├→ Release
                                                 └─ /sec (security)   ─┘   └─ /web ─┘
```

---

## ADR

| Decyzja | Uzasadnienie |
|---------|-------------|
| PowerShell | Windows jako główne środowisko |
| Kopiowanie plików (nie git submodule) | Niezależna ewolucja per projekt |
| Sprint v3 (Lean) | Checkboxy = progress. Bez progress barów i Execution Logów |
| Jeden dev.md (SingleDev + MultiDev) | 95% identyczne → parametryzowany warunkiem na starcie |
| STRIDE source of truth w sec.md | Sprint template referencjuje, nie duplikuje |
| Deploy guard (deploy.md) | Zapewnienie postawialności środowiska poza głównym workflowem |
| Deploy engine w pm.md | 07_team_engine opisuje architekturę, pm.md ma komendy |
| doc + web inline w pm.md | Za krótkie na osobne pliki (15 + 22 linii) |
| Rozdzielenie CORE/PROJECT | Skille projektowo-specyficzne, nie do nadpisywania |
| Variant B Flow (v3.1) | /qa przed /audyt+/sec = testowany kod trafia do audytu. Industry pattern: Code→Test→Review |
| /audyt agent (v3.1) | Luka między /arch a /dev. Audytor sprawdza spójność kodu z planem architektury |
| /audyt+/sec parallel (v3.1) | Różne wymiary (spójność vs bezpieczeństwo), brak zależności → równoległe |
| /doc+/web parallel (v3.1) | Różne typy dokumentacji (changelog vs biblioteka), brak zależności |
| /arch Research Gate (v3.2) | Shift-left research: complexity≥7 → /anal prompt → walidacja vs ADR. Google/Stripe pattern |
| /qa Systematic 7-Step (v3.2) | Risk-based planning, smoke test, @find-bugs, E2E from US, regression, evidence-based verdict |
| TDD Enforcement (v3.2) | US→E2E mapping, per-task test types, Contract tests na API, Integration na multi-component |
| Sprint Template v3.2 | US→E2E Mapping table + Per-Task Test Types table w sekcji A sprint artifact |

---
📅 *v3.2 Lean — 2026-03-11*
