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

#### Step 4: Start Autonomous Development

```bash
ralph --monitor
```

This opens a tmux session with:
- Left pane: Ralph loop output
- Right pane: Live monitoring

Ralph will:
1. Read PROMPT.md
2. Execute tasks from @fix_plan.md
3. Mark completed tasks with [x]
4. Continue until all tasks done or exit conditions met

#### Step 5: Handle Blockers (if needed)

If Claude gets stuck:

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

#### Step 6: Progress Analysis

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

#### Step 7: Complete Session

```bash
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

#### Schritt 4: Autonome Entwicklung starten

```bash
ralph --monitor
```

#### Schritt 5: Blocker behandeln (falls nötig)

```bash
orchestrate stuck "Flask-JWT-Extended Import-Fehler: ModuleNotFoundError"
```

#### Schritt 6: Fortschrittsanalyse

```bash
orchestrate analyze
```

#### Schritt 7: Session abschließen

```bash
orchestrate summary
```

---

## Tips / Tipps

### English

1. **Let Gemini plan** - Don't skip `orchestrate init`. The planning phase is crucial.
2. **Log important events** - Use `memory event` for significant decisions.
3. **Use stuck early** - Don't waste time if Claude is looping on an error.
4. **Review fix_plan.md** - You can manually edit tasks if priorities change.
5. **Run summary regularly** - Especially before long breaks.

### Deutsch

1. **Lass Gemini planen** - Überspringe `orchestrate init` nicht. Die Planungsphase ist entscheidend.
2. **Logge wichtige Events** - Nutze `memory event` für bedeutsame Entscheidungen.
3. **Nutze stuck frühzeitig** - Verschwende keine Zeit wenn Claude bei einem Fehler hängt.
4. **Prüfe fix_plan.md** - Du kannst Tasks manuell bearbeiten wenn Prioritäten sich ändern.
5. **Führe summary regelmäßig aus** - Besonders vor längeren Pausen.
