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

### 2. Execution Loop (Ralph + Claude)
```
Ralph startet mit Gemini-generiertem PROMPT.md
     ↓
Claude Agent führt Task aus
     ↓
Event wird geloggt: {"action": "created", "file": "BookingController.php"}
     ↓
Claude meldet: "Task 1 erledigt"
     ↓
Ralph markiert Checkbox, startet nächsten Task
```

### 3. Strategische Anpassung (Gemini)
```
Alle 10 Tasks ODER bei Blockers:
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
- **Wann aufrufen:**
  - Initial bei neuer Aufgabe
  - Alle 10-15 Tasks
  - Bei Blockern/Fehlern
  - Am Ende einer Session

### Claude (Executor)
- **Input:** Einzelne Tasks aus @fix_plan.md
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

## Vorteile dieser Architektur

1. **Gemini vergisst nichts** - 2M Context = komplette Projekthistorie
2. **Claude bleibt effizient** - Bekommt fokussierte Tasks
3. **Qwen als Sicherheitsnetz** - Zweite Meinung bei kritischen Stellen
4. **Ralph automatisiert** - Continuous Loop ohne manuelle Intervention
5. **Selbst-korrigierend** - Gemini erkennt Patterns und passt an

## Trigger für Gemini-Intervention

| Trigger | Aktion |
|---------|--------|
| Neue User-Aufgabe | Generiere PROMPT.md + @fix_plan.md |
| 10 Tasks erledigt | Analyse + ggf. Neupriorisierung |
| 3+ Fehler in Folge | Problemanalyse + Strategieänderung |
| "stuck" Detection | Alternativer Ansatz vorschlagen |
| Session Ende | Zusammenfassung + nächste Schritte |

## API-Budget (Gemini Pro)

Mit ~10000 Calls/Tag:
- Initial-Analyse: 1 Call
- Alle 10 Tasks: ~20 Calls/Tag (bei 200 Tasks)
- Fehler-Handling: ~10 Calls/Tag
- Session-Summaries: ~5 Calls/Tag

**Ergebnis: ~35 Calls/Tag = 3.5% des Budgets**

→ Massiv Headroom für häufigere Interventionen!
