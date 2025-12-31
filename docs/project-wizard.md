---
name: project-wizard
description: Interaktiver Projekt-Wizard, der durch gezielte Fragen hilft, Projektanforderungen zu definieren und optimierte PROMPT.md + @fix_plan.md für das selbst-orchestrierende System generiert. Nutze diesen Skill wenn du ein neues Projekt starten willst.
tools: Bash, Read, Write, AskUserQuestion
---

# Project Wizard Skill

Interaktiver Assistent für Projekt-Setup im selbst-orchestrierenden System.

## Workflow

### 1. Begrüßung
Zeige dem User:
```
╔═══════════════════════════════════════════════════════════╗
║         🧙 Project Wizard - Projekt-Initialisierung       ║
╚═══════════════════════════════════════════════════════════╝

Ich helfe dir, dein Projekt optimal zu definieren:
• Gezielte Fragen zu Anforderungen
• Technologie-Vorschläge
• Skills/Expertise-Zuweisung
• Generierung von PROMPT.md + @fix_plan.md
```

### 2. Fragen stellen

Nutze AskUserQuestion für strukturierte Erfassung:

**Runde 1: Basis**
```json
{
  "questions": [
    {
      "question": "Was für ein Projekt möchtest du erstellen?",
      "header": "Projekttyp",
      "options": [
        {"label": "Web App (Fullstack)", "description": "Frontend + Backend + Datenbank"},
        {"label": "REST API", "description": "Backend-Service mit API-Endpunkten"},
        {"label": "CLI Tool", "description": "Kommandozeilen-Anwendung"},
        {"label": "Automation/Script", "description": "Automatisierung, Workflow"}
      ],
      "multiSelect": false
    },
    {
      "question": "Welche Hauptsprache bevorzugst du?",
      "header": "Sprache",
      "options": [
        {"label": "Python (Recommended)", "description": "Schnelle Entwicklung, viele Libraries"},
        {"label": "TypeScript/Node.js", "description": "JavaScript-Ökosystem, async"},
        {"label": "Go", "description": "Performance, Concurrency"},
        {"label": "Rust", "description": "Safety, Performance"}
      ],
      "multiSelect": false
    }
  ]
}
```

**Runde 2: Features**
```json
{
  "questions": [
    {
      "question": "Welche Features brauchst du?",
      "header": "Features",
      "options": [
        {"label": "User Authentication", "description": "Login, Register, JWT"},
        {"label": "Database", "description": "PostgreSQL/SQLite/MongoDB"},
        {"label": "API Endpoints", "description": "REST/GraphQL Schnittstellen"},
        {"label": "Tests", "description": "Unit + Integration Tests"}
      ],
      "multiSelect": true
    },
    {
      "question": "Wie umfangreich soll das Projekt sein?",
      "header": "Scope",
      "options": [
        {"label": "MVP (Recommended)", "description": "Minimal, schnell fertig"},
        {"label": "Standard", "description": "Solide Basis mit Tests"},
        {"label": "Production-Ready", "description": "Vollständig mit Security"}
      ],
      "multiSelect": false
    }
  ]
}
```

**Runde 3: Details (Text-Eingabe)**
Frage nach:
- "Beschreibe kurz was das Projekt tun soll (1-2 Sätze)"
- "Gibt es besondere Anforderungen? (optional)"

### 3. Empfehlungen generieren

Basierend auf Antworten, empfehle:

| Bereich | Agent/Skill | Wann |
|---------|-------------|------|
| Strategische Planung | `orchestrate init` | Immer |
| Code-Review | `qwen-agent` | Bei komplexem Code |
| Security | `security-reviewer` | Bei Auth/User-Daten |
| API-Design | `api-architect` | Bei API-Projekten |
| Performance | `performance-engineer` | Bei Datenbank/Load |
| Docs | `docs-architect` | Bei Libraries |

### 4. PROMPT.md generieren

Schreibe in aktuelles Verzeichnis:

```bash
cat > PROMPT.md << 'EOF'
# [Projektname]

## Ziel
[Aus User-Beschreibung]

## Technologie-Stack
- Sprache: [Gewählt]
- Framework: [Empfohlen basierend auf Typ]
- Datenbank: [Falls gewählt]

## Anforderungen
[Aus Features-Auswahl]

## Empfohlene Agents
- **Orchestrierung:** `orchestrate analyze` bei Blockern
- **Review:** [Basierend auf Projekt]

## Exit-Kriterien
Ralph stoppt wenn:
- [ ] Alle Tasks erledigt
- [ ] Tests bestanden (falls gewählt)
- [ ] Keine Fehler im Build

## Hinweise
[Basierend auf Scope-Auswahl]
EOF
```

### 5. @fix_plan.md generieren

```bash
cat > @fix_plan.md << 'EOF'
# Task-Liste

## Phase 1: Setup
- [ ] Projektstruktur erstellen
- [ ] Dependencies definieren
- [ ] Basis-Konfiguration

## Phase 2: Kern-Features
[Basierend auf Features-Auswahl]

## Phase 3: Tests & Docs
[Falls gewählt]

## Phase 4: Finalisierung
- [ ] Code-Review durchführen
- [ ] Final cleanup
EOF
```

### 6. Abschluss

Zeige:
```
✅ Projekt-Setup erstellt!

Dateien:
  • PROMPT.md - Anweisungen für Claude
  • @fix_plan.md - Priorisierte Tasks

Nächste Schritte:
  1. Dateien prüfen und ggf. anpassen
  2. ralph --monitor starten
  3. Bei Problemen: orchestrate stuck "..."

Empfohlene Skills während der Entwicklung:
  • [Liste basierend auf Projekt]
```

## Beispiel-Session

```
User: /project-wizard

Wizard:
╔═══════════════════════════════════════════════════════════╗
║         🧙 Project Wizard - Projekt-Initialisierung       ║
╚═══════════════════════════════════════════════════════════╝

[AskUserQuestion: Projekttyp, Sprache]

User: Web App, Python

Wizard:
Gute Wahl! Python + Web App → Ich empfehle FastAPI oder Flask.

[AskUserQuestion: Features, Scope]

User: Auth + Database + API, MVP

Wizard:
Für ein MVP mit Auth empfehle ich:
- FastAPI (modern, schnell)
- SQLite (einfach für MVP)
- JWT für Auth

[AskUserQuestion: Beschreibung]

User: "Eine Booking-App für Termine"

Wizard:
Perfekt! Erstelle jetzt die Projektdateien...

✅ PROMPT.md erstellt
✅ @fix_plan.md erstellt

Empfohlene Agents für dieses Projekt:
- orchestrate (Planung & Blocker)
- api-architect (API-Design)
- security-reviewer (vor Deploy)

Starte mit: ralph --monitor
```
