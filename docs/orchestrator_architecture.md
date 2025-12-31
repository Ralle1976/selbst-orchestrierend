# Optimale Multi-Agent Architektur: Gemini als Dirigent

## Kernkonzept

```
                    ┌─────────────────────────────────┐
                    │         GEMINI PRO              │
                    │      (Strategic Brain)          │
                    │                                 │
                    │  • 2M Token Kontext             │
                    │  • Sieht ALLES                  │
                    │  • Generiert Strategien         │
                    │  • Erstellt PROMPT.md           │
                    │  • Priorisiert Tasks            │
                    │  • Erkennt Patterns             │
                    └───────────┬─────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │    WATCH DAEMON       │  ◄── NEU!
                    │  (orchestrate watch)  │
                    │  • Überwacht Progress │
                    │  • Greift bei Stall   │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │    TASK QUEUE         │
                    │  (Ralph @fix_plan.md) │
                    └───────────┬───────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
    ┌───────────┐         ┌───────────┐         ┌───────────┐
    │  CLAUDE   │         │  CLAUDE   │         │   QWEN    │
    │  Agent 1  │         │  Agent 2  │         │  (Review) │
    │  (Code)   │         │  (Tests)  │         │           │
    └─────┬─────┘         └─────┬─────┘         └─────┬─────┘
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │    EVENT LOG          │
                    │  (events.jsonl)       │
                    └───────────┬───────────┘
                                │
                                └──────────→ Zurück zu GEMINI
```

## Workflow

### 1. Initialisierung (User gibt Aufgabe)
```
User: "Baue eine Booking-API"
     ↓
Gemini analysiert:
- Was ist das Ziel?
- Welche Komponenten brauchen wir?
- Welche Reihenfolge macht Sinn?
     ↓
Gemini generiert:
- PROMPT.md (für Ralph)
- @fix_plan.md (priorisierte Tasks)
- Architektur-Entscheidungen
```

### 2. Execution Loop (Ralph + Claude + Watch)
```
orchestrate watch startet (Hintergrund)
     ↓
Ralph startet mit Gemini-generiertem PROMPT.md
     ↓
Claude Agent führt Task aus
     ↓
Event wird geloggt: {"action": "created", "file": "BookingController.php"}
     ↓
Claude meldet: "Task 1 erledigt"
     ↓
Ralph markiert Checkbox [x] in @fix_plan.md
     ↓
Watch Daemon erkennt Änderung → Reset Timer
     ↓
Ralph startet nächsten Task
```

### 3. Automatische Stall-Detection (NEU!)
```
Watch Daemon überwacht @fix_plan.md
     ↓
Keine Änderung seit 180 Sekunden?
     ↓
Watch ruft Gemini: "Warum steckt Ralph fest?"
     ↓
Gemini analysiert:
- Letzte Events
- Aktueller @fix_plan.md Stand
- Mögliche Probleme
     ↓
Gemini schreibt Hint → .orchestrator_hints.md
     ↓
Ralph (bei nächster Iteration) liest Hint
     ↓
Claude passt Strategie an
```

### 4. Eskalation bei hartnäckigen Problemen
```
3x Stillstand in Folge erkannt
     ↓
Watch eskaliert → Vollständige Neuanalyse
     ↓
Gemini:
- Identifiziert Kernproblem
- Schlägt Task-Überspringung vor
- Generiert alternativen Ansatz
     ↓
.orchestrator_hints.md enthält ESKALATION
     ↓
Ralph/Claude führt Neuplanung durch
```

### 5. Strategische Anpassung (Gemini - manuell)
```
Alle 10 Tasks ODER bei Blockers:
     ↓
orchestrate analyze
     ↓
Gemini liest alle Events seit letzter Analyse
     ↓
Gemini analysiert:
- Was wurde erreicht?
- Welche Probleme traten auf?
- Brauchen wir neue Tasks?
- Muss die Priorität angepasst werden?
     ↓
Gemini aktualisiert:
- @fix_plan.md mit neuen/angepassten Tasks
- Optional: Feedback an User
```

## Rollen-Definition

### Gemini Pro (Dirigent/Stratege)
- **Input:** Alle Events, Code-Änderungen, Fehler, User-Anforderungen
- **Output:**
  - Strategische Entscheidungen
  - PROMPT.md für Ralph
  - @fix_plan.md Updates
  - Architektur-Guidance
  - Hints bei Stillstand (via Watch)
- **Wann aufrufen:**
  - Initial bei neuer Aufgabe
  - Automatisch bei Stillstand (Watch Daemon)
  - Alle 10-15 Tasks (manuell)
  - Bei Blockern/Fehlern
  - Am Ende einer Session

### Watch Daemon (Automatische Überwachung) - NEU!
- **Input:** @fix_plan.md Änderungen
- **Output:**
  - .orchestrator_hints.md (Hints für Ralph)
  - Logs in orchestrator_watch.log
- **Konfiguration:**
  - Check-Intervall: 60 Sekunden
  - Stall-Schwelle: 180 Sekunden
  - Max Interventionen vor Eskalation: 3

### Claude (Executor)
- **Input:** Einzelne Tasks aus @fix_plan.md, Hints aus .orchestrator_hints.md
- **Output:**
  - Code-Änderungen
  - Test-Ergebnisse
  - Event-Logs
- **Stärken nutzen:**
  - Tool-Nutzung (Bash, Edit, etc.)
  - Code-Qualität
  - Problemlösung

### Qwen (Reviewer/Second Opinion)
- **Input:** Code von Claude, kritische Entscheidungen
- **Output:**
  - Code-Reviews
  - Alternative Vorschläge
  - Validation
- **Wann aufrufen:**
  - Bei komplexen Code-Änderungen
  - Vor wichtigen Architektur-Entscheidungen
  - Als Fallback wenn Claude stuck ist

## Kommunikationsdateien

| Datei | Erstellt von | Gelesen von | Zweck |
|-------|--------------|-------------|-------|
| `PROMPT.md` | Gemini | Ralph/Claude | Hauptanweisungen |
| `@fix_plan.md` | Gemini | Ralph/Claude | Task-Liste |
| `.orchestrator_hints.md` | Watch Daemon | Ralph/Claude | Hints bei Stillstand |
| `.ralph_status.json` | Ralph | Watch Daemon | Status-Updates |
| `events.jsonl` | Alle | Gemini | Event-Log |

## Vorteile dieser Architektur

1. **Gemini vergisst nichts** - 2M Context = komplette Projekthistorie
2. **Claude bleibt effizient** - Bekommt fokussierte Tasks
3. **Watch Daemon greift automatisch ein** - Keine manuelle Intervention nötig
4. **Qwen als Sicherheitsnetz** - Zweite Meinung bei kritischen Stellen
5. **Ralph automatisiert** - Continuous Loop ohne manuelle Intervention
6. **Selbst-korrigierend** - Gemini erkennt Patterns und passt an

## Trigger für Gemini-Intervention

| Trigger | Quelle | Aktion |
|---------|--------|--------|
| Neue User-Aufgabe | Manuell | Generiere PROMPT.md + @fix_plan.md |
| Stillstand >180s | Watch Daemon | Hint schreiben |
| 3x Stillstand | Watch Daemon | Eskalation + Neuplanung |
| 10 Tasks erledigt | Manuell | Analyse + ggf. Neupriorisierung |
| 3+ Fehler in Folge | Manuell | Problemanalyse + Strategieänderung |
| "stuck" Detection | Manuell | Alternativer Ansatz vorschlagen |
| Session Ende | Manuell | Zusammenfassung + nächste Schritte |

## API-Budget (Gemini Pro)

Mit ~10000 Calls/Tag:
- Initial-Analyse: 1 Call
- Watch Interventionen: ~10-20 Calls/Tag
- Alle 10 Tasks: ~20 Calls/Tag (bei 200 Tasks)
- Fehler-Handling: ~10 Calls/Tag
- Session-Summaries: ~5 Calls/Tag

**Ergebnis: ~50-60 Calls/Tag = 0.5% des Budgets**

→ Massiv Headroom für häufigere Interventionen!

## Quick Start

```bash
# Methode 1: Alles automatisch
claude-start --ralph

# Methode 2: Manuell
orchestrate init "Meine Aufgabe"
orchestrate watch &              # Hintergrund
ralph --monitor                  # Vordergrund

# Stoppen
orchestrate watch --stop
```
