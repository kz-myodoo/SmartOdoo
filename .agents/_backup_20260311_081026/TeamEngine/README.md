# 🚀 TeamEngine v3.0.1 (Lean) — Orkiestrator Zespołu AI

Silnik, który zamienia pojedynczego bota w zespół specjalistów: PM, Architekt, Dev (×3 MultiDev), QA, Analityk, Security, Dokumentalista, Bibliotekarz, Policjant (/pol).

## 📂 Skład

### CORE (aktualizowalna warstwa)
| Plik | Rola |
|------|------|
| `.agents/TEAM_RULES.md` | Konstytucja — 10 artykułów |
| `.agents/workflows/pm.md` | Smart Router + inline /doc + /web |
| `.agents/workflows/pol.md` | Wewnętrzna Policja (/pol) — Kill Switch dla zawieszonych procesów. Nienawidzi błędów AI. |
| `.agents/workflows/arch.md` | Planista (Pre/Post Checklists, Test Strategy) |
| `.agents/workflows/dev.md` | SingleDev Worker |
| `.agents/workflows/dev_worker.md` | MultiDev Worker (parametryzowany B{N}) |
| `.agents/workflows/qa.md` | Gatekeeper (Pattern Review + Error Registry) |
| `.agents/workflows/anal.md` | Deep Researcher |
| `TeamEngine/scripts/` | Deploy + Update skrypty |

### PROJECT (chroniona warstwa — nie nadpisywana)
| Plik | Rola |
|------|------|
| `.agents/PROJECT_SKILLS.md` | Skille per projekt |
| `docs/blueprint/tom1-5/` | Wiedza projektowa |
| `docs/sprints/` | Sprinty projektu |

## 🛠️ Użycie

```powershell
# Deploy na nowy projekt:
.\TeamEngine\scripts\deploy_engine.ps1 -TargetPath "C:\ProjektX" -ProjectName "ProjektX"

# Update istniejącego (tylko CORE):
.\TeamEngine\scripts\update_engine.ps1 -SourcePath "C:\od_zera_do_ai\PM_Center" -TargetPath "C:\ProjektX"

# Dry run (podgląd zmian bez nadpisywania):
.\TeamEngine\scripts\update_engine.ps1 -SourcePath "C:\od_zera_do_ai\PM_Center" -TargetPath "C:\ProjektX" -DryRun
```

Lub w rozmowie: `deploy engine` → `/pm` poprowadzi.

## 🛰️ Scout — Naczelny Dyrektor (Zarządzanie Farmą)
Wbudowany system zarządzania wieloma projektami (multi-workspace) z poziomu PM_Center.
Dostępne komendy na czacie:
- `/scout recon` — Rozpoznaje wszystkie instancje TeamEngine we wskazanym obszarze.
- `/scout audit` — Weryfikuje które instancje są przestarzałe.
- `/scout harvest` — Konsoliduje pliki `error_registry.md` z wielu projektów by wyciągnąć globalne lekcje.
- `/scout deploy` — Automatycznie aktualizuje wszystkie przestarzałe projekty do najnowszej wersji.

## 📊 v3.0 vs v2.0
| Metryka | v2.0 | v3.0 |
|---------|------|------|
| Pliki workflow | 10 | 6 |
| Rozmiar kontekstowy | 71.7 KB | 26.9 KB |
| Duplikacja | ~35% | ~8% |
| Test Strategy w planie | ❌ | ✅ |
| Error Registry (feedback loop) | ❌ | ✅ |

---
📅 *TeamEngine v3.0 Lean — 2026-03-05*
