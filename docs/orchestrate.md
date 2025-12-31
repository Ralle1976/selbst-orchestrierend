---
name: orchestrate
description: Gemini Orchestrator - Strategische Steuerung des Multi-Agent-Systems. Nutzt Geminis 2M Kontext für Planung, Analyse und Task-Management. Automatisch aufrufen bei neuen Aufgaben, Blockern oder zur Analyse.
tools: Bash, Read, Write
---

# Gemini Orchestrator Skill

Strategisches Gehirn des Multi-Agent-Systems. Gemini hat 2M Context und steuert Claude.

## Wann automatisch nutzen:

1. **Neue komplexe Aufgabe** → `init`
2. **Stuck/Blocker** → `stuck`
3. **Nach 10+ Tasks** → `analyze`
4. **Session Ende** → `summary`
5. **Autonome Überwachung** → `watch`

## Commands

### Neue Aufgabe initialisieren
```bash
orchestrate init "Aufgabenbeschreibung"
```
Generiert: PROMPT.md + @fix_plan.md für Ralph

### Watch-Daemon starten (NEU!)
```bash
orchestrate watch          # Startet Überwachungs-Daemon
orchestrate watch --stop   # Stoppt den Daemon
```
Überwacht Ralph automatisch und greift bei Stillstand ein:
- Erkennt wenn @fix_plan.md sich nicht ändert
- Schreibt Hints in `.orchestrator_hints.md`
- Eskaliert nach mehreren Stalls

### Situation analysieren
```bash
orchestrate analyze
```
Gemini analysiert Progress, Probleme, nächste Schritte

### Tasks neu priorisieren
```bash
orchestrate replan
```
Aktualisiert @fix_plan.md basierend auf aktuellem Stand

### Bei Blockern helfen
```bash
orchestrate stuck "Fehlerbeschreibung"
```
Gemini schlägt alternative Ansätze vor

### Session zusammenfassen
```bash
orchestrate summary
```
Erstellt Zusammenfassung für nächste Session

### Nächste Aktion empfehlen
```bash
orchestrate next
```

### Aktuellen Hint lesen
```bash
orchestrate hint
```

## Neuer Workflow mit Watch-Daemon

```
┌─────────────────────────────────────────────────────────┐
│  Terminal 1: orchestrate watch                          │
│     │                                                   │
│     ├──▶ Überwacht @fix_plan.md (alle 60s)             │
│     ├──▶ Erkennt Stillstand (>180s ohne Änderung)      │
│     ├──▶ Schreibt Hints → .orchestrator_hints.md       │
│     └──▶ Eskaliert nach 3x Stillstand                  │
│              │                                          │
│              ▼                                          │
│  Terminal 2: ralph --monitor                            │
│     │                                                   │
│     ├──▶ Liest PROMPT.md + @fix_plan.md                │
│     ├──▶ Prüft .orchestrator_hints.md                  │
│     ├──▶ Führt Tasks aus                               │
│     └──▶ Markiert [x] → Watch erkennt Fortschritt      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## WICHTIG: Korrekter Workflow

**NIEMALS `orchestrate init` innerhalb von Claude Code ausführen!**

Claude sieht die generierten Dateien sofort und fängt an zu arbeiten -
ohne Ralph-Loop, ohne Watch-Daemon, ohne Kontrolle.

## Quick Start (im TERMINAL, nicht in Claude!)

```bash
# Schritt 1: Im normalen Terminal (NICHT Claude!)
cd /dein/projekt
orchestrate init "Meine Aufgabe"

# Schritt 2: Watch-Daemon starten
orchestrate watch &

# Schritt 3: Ralph starten (startet Claude kontrolliert)
ralph --monitor

# ODER alles auf einmal:
claude-start --ralph
```

**Merke:** `orchestrate init` = Terminal, `ralph --monitor` = startet Claude

## Kommunikationsdateien

| Datei | Zweck |
|-------|-------|
| `PROMPT.md` | Hauptanweisungen für Claude |
| `@fix_plan.md` | Task-Liste mit Checkboxen |
| `.orchestrator_hints.md` | Hints vom Watch-Daemon |
| `.ralph_status.json` | Status von Ralph (optional) |

## Automatische Integration

Bei jeder signifikanten Aktion Event loggen:
```bash
memory event '{"action": "...", "details": "..."}'
```
