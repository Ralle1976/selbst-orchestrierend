# Example Workflow / Beispiel-Workflow

## English

### Scenario: Building a REST API for a Todo Application

#### Step 1: Start the System

```bash
claude-start
```

Expected output:
```
╔═══════════════════════════════════════════════════════════╗
║     🧠 Claude Multi-Agent System with Gemini Orchestrator  ║
╚═══════════════════════════════════════════════════════════╝

[09:00:00] Prüfe Provider-Status...

GEMINI (priority: 1)
  CLI: OK
  Model: gemini-2.0-flash
  Context: 2,000,000 tokens
  Calls today: 0/10000
  Available: YES

[09:00:01] Lade letzten Kontext...
(Previous session context shown here)

✓ System bereit!
```

#### Step 2: Initialize the Project

```bash
mkdir todo-api && cd todo-api
orchestrate init "Create a REST API for a Todo application using Python Flask. Include CRUD operations, user authentication with JWT, SQLite database, and proper error handling."
```

Gemini will generate:
- `PROMPT.md` - Detailed instructions for Claude
- `@fix_plan.md` - Prioritized task checklist

#### Step 3: Review Generated Files

```bash
cat PROMPT.md
```

Example output:
```markdown
# Todo REST API

## Goal
Build a production-ready REST API for todo management with authentication.

## Requirements
1. User registration and login with JWT tokens
2. CRUD operations for todos (Create, Read, Update, Delete)
3. SQLite database with proper schema
4. Input validation and error handling
5. API documentation

## Technical Specifications
- Python 3.8+ with Flask
- Flask-JWT-Extended for authentication
- SQLAlchemy ORM
- RESTful conventions

## Exit Criteria
- All endpoints working with proper responses
- Authentication protecting todo operations
- Tests passing
```

```bash
cat @fix_plan.md
```

Example output:
```markdown
# Task List

## Phase 1: Setup
- [ ] Initialize Flask project structure
- [ ] Set up SQLite database and models
- [ ] Configure JWT authentication

## Phase 2: Core Features
- [ ] Implement user registration endpoint
- [ ] Implement user login endpoint
- [ ] Implement todo CRUD endpoints

## Phase 3: Polish
- [ ] Add input validation
- [ ] Implement error handlers
- [ ] Write basic tests
```

#### Step 4: Start Autonomous Development with Watch Daemon

**NEW: With automatic monitoring!**

```bash
# Option A: All-in-one (recommended)
claude-start --ralph

# Option B: Manual (two terminals)
# Terminal 1:
orchestrate watch &

# Terminal 2:
ralph --monitor
```

This starts:
- **Watch Daemon** (background): Monitors @fix_plan.md for stalls
- **Ralph Loop** (tmux session): Executes tasks autonomously

Ralph will:
1. Read PROMPT.md
2. Execute tasks from @fix_plan.md
3. Mark completed tasks with [x]
4. Continue until all tasks done or exit conditions met

Watch Daemon will:
1. Check @fix_plan.md every 60 seconds
2. Detect stalls (no change for 180+ seconds)
3. Write hints to `.orchestrator_hints.md`
4. Escalate after 3 consecutive stalls

#### Step 5: Automatic Stall Handling (NEW!)

If Claude gets stuck, the **Watch Daemon automatically intervenes**:

Watch Daemon output:
```
[09:15:00] ⚠ Stillstand erkannt (195s)
  → Intervention 1/3
[09:15:02] Hint geschrieben: Das Problem scheint ein fehlender Import...
```

The daemon creates `.orchestrator_hints.md`:
```markdown
# Orchestrator Hint
**Zeit:** 2024-12-31 09:15:02
**Priorität:** WARNUNG

Das Problem scheint ein fehlender Import zu sein.

Mögliche Lösung:
1. Prüfe ob flask-jwt-extended installiert ist
2. Führe `pip install flask-jwt-extended` aus
3. Versuche den Import erneut

---
*Diese Datei wird automatisch vom Orchestrator generiert.*
```

Ralph/Claude will read this hint and adjust strategy!

#### Step 6: Manual Intervention (if still needed)

If automatic hints don't help:

```bash
# In another terminal
orchestrate stuck "Flask-JWT-Extended import error: ModuleNotFoundError"
```

Gemini response:
```
ANALYSIS:
The error indicates Flask-JWT-Extended is not installed.

SOLUTION:
1. Add to requirements.txt: flask-jwt-extended>=4.0.0
2. Run: pip install flask-jwt-extended
3. Retry the import

ALTERNATIVE:
If issues persist, consider using PyJWT directly with a custom decorator.
```

#### Step 7: Progress Analysis

After several tasks:

```bash
orchestrate analyze
```

Example output:
```
═══════════════════════════════════════════════════════════
GEMINI ANALYSIS:
═══════════════════════════════════════════════════════════

## Progress Summary
- 8 of 12 tasks completed (67%)
- Authentication system fully implemented
- CRUD endpoints working

## Observations
- Good progress on core features
- No repeated errors detected
- Pattern: Using SQLAlchemy correctly

## Recommendations
1. Continue with remaining tasks
2. Consider adding input validation before tests
3. Current prioritization looks correct

## Estimated Completion
3-4 more iterations should complete remaining tasks.
```

#### Step 8: Complete Session

```bash
# Stop watch daemon
orchestrate watch --stop

# Generate summary
orchestrate summary
```

Generates a summary saved for next session:
```markdown
## Session Summary

### Accomplished
- Complete Flask project structure
- User authentication with JWT
- Todo CRUD endpoints
- SQLite database with User and Todo models

### Key Decisions
- Used Flask-JWT-Extended for token management
- SQLite for simplicity (can migrate to PostgreSQL)
- RESTful conventions followed

### Open Items
- [ ] Input validation
- [ ] Error handlers
- [ ] Tests

### Recommendations
Next session: Focus on validation and error handling first,
then write tests to verify everything works.
```

---

## Deutsch

### Szenario: Erstellen einer REST API für eine Todo-Anwendung

#### Schritt 1: System starten

```bash
claude-start
```

#### Schritt 2: Projekt initialisieren

```bash
mkdir todo-api && cd todo-api
orchestrate init "Erstelle eine REST API für eine Todo-Anwendung mit Python Flask. Implementiere CRUD-Operationen, Benutzerauthentifizierung mit JWT, SQLite-Datenbank und ordentliche Fehlerbehandlung."
```

#### Schritt 3: Generierte Dateien prüfen

```bash
cat PROMPT.md
cat @fix_plan.md
```

#### Schritt 4: Autonome Entwicklung mit Watch-Daemon starten (NEU!)

```bash
# Option A: Alles auf einmal (empfohlen)
claude-start --ralph

# Option B: Manuell (zwei Terminals)
# Terminal 1:
orchestrate watch &

# Terminal 2:
ralph --monitor
```

**Was passiert:**
- Watch-Daemon überwacht @fix_plan.md im Hintergrund
- Ralph führt Tasks autonom aus
- Bei Stillstand (>180s): Watch schreibt automatisch Hints
- Nach 3x Stillstand: Eskalation mit Neuplanung

#### Schritt 5: Automatische Stall-Behandlung (NEU!)

Der Watch-Daemon erkennt wenn Ralph festsitzt:

```
[09:15:00] ⚠ Stillstand erkannt (195s)
  → Intervention 1/3
[09:15:02] Hint geschrieben: Das Problem scheint...
```

Ralph liest `.orchestrator_hints.md` und passt Strategie an!

#### Schritt 6: Manuelle Intervention (falls nötig)

```bash
orchestrate stuck "Flask-JWT-Extended Import-Fehler: ModuleNotFoundError"
```

#### Schritt 7: Fortschrittsanalyse

```bash
orchestrate analyze
```

#### Schritt 8: Session beenden

```bash
orchestrate watch --stop
orchestrate summary
```

---

## Tips / Tipps

### English

1. **Use claude-start --ralph** - Starts everything automatically including watch daemon
2. **Let Gemini plan** - Don't skip `orchestrate init`. The planning phase is crucial.
3. **Trust the watch daemon** - It automatically handles most stalls
4. **Log important events** - Use `memory event` for significant decisions.
5. **Check hints** - Run `orchestrate hint` to see current hint
6. **Review fix_plan.md** - You can manually edit tasks if priorities change.
7. **Run summary regularly** - Especially before long breaks.

### Deutsch

1. **Nutze claude-start --ralph** - Startet alles automatisch inkl. Watch-Daemon
2. **Lass Gemini planen** - Überspringe `orchestrate init` nicht.
3. **Vertraue dem Watch-Daemon** - Er behandelt die meisten Stillstände automatisch
4. **Logge wichtige Events** - Nutze `memory event` für bedeutsame Entscheidungen.
5. **Prüfe Hints** - Mit `orchestrate hint` siehst du den aktuellen Hint
6. **Prüfe fix_plan.md** - Du kannst Tasks manuell bearbeiten.
7. **Führe summary regelmäßig aus** - Besonders vor längeren Pausen.

---

## Command Reference / Befehlsübersicht

| Command | Description | Beschreibung |
|---------|-------------|--------------|
| `claude-start` | Start system | System starten |
| `claude-start --ralph` | Start system + watch + ralph | System + Watch + Ralph |
| `claude-start --stop` | Stop all daemons | Alle Daemons stoppen |
| `orchestrate init "..."` | Initialize task | Aufgabe initialisieren |
| `orchestrate watch` | Start watch daemon | Watch-Daemon starten |
| `orchestrate watch --stop` | Stop watch daemon | Watch-Daemon stoppen |
| `orchestrate hint` | Show current hint | Aktuellen Hint zeigen |
| `orchestrate analyze` | Analyze progress | Fortschritt analysieren |
| `orchestrate stuck "..."` | Get help with blocker | Hilfe bei Blocker |
| `orchestrate replan` | Re-prioritize tasks | Tasks neu priorisieren |
| `orchestrate summary` | Generate summary | Zusammenfassung erstellen |
| `ralph --monitor` | Start ralph loop | Ralph-Loop starten |
