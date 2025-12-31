# Self-Orchestrating Multi-Agent System / Selbst-Orchestrierendes Multi-Agent-System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Bash 4.0+](https://img.shields.io/badge/bash-4.0+-green.svg)](https://www.gnu.org/software/bash/)

**A sophisticated multi-agent orchestration system where Gemini acts as the strategic brain, Claude executes tasks, and Ralph automates the development loop.**

**Ein ausgeklügeltes Multi-Agent-Orchestrierungssystem, bei dem Gemini als strategisches Gehirn fungiert, Claude Aufgaben ausführt und Ralph die Entwicklungsschleife automatisiert.**

---

## Table of Contents / Inhaltsverzeichnis

- [English Documentation](#english-documentation)
  - [Overview](#overview)
  - [Architecture](#architecture)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Components](#components)
  - [Usage Guide](#usage-guide)
  - [Configuration](#configuration)
- [Deutsche Dokumentation](#deutsche-dokumentation)
  - [Übersicht](#übersicht)
  - [Architektur](#architektur)
  - [Installation](#installation-1)
  - [Schnellstart](#schnellstart)
  - [Komponenten](#komponenten)
  - [Nutzungsanleitung](#nutzungsanleitung)
  - [Konfiguration](#konfiguration-1)

---

# English Documentation

## Overview

This system solves a fundamental problem in AI-assisted development: **context loss**.

Traditional AI assistants forget everything between sessions. Claude Code, while powerful, has a limited context window (~200K tokens) that gets exhausted during complex projects.

**Our Solution:** Use Gemini Pro's massive 2M token context as the "strategic brain" that:
- Remembers everything across sessions
- Plans and prioritizes tasks strategically
- Recognizes patterns and adjusts strategy
- Delegates execution to Claude (the best coder)

### Key Innovation

```
┌─────────────────────────────────────────────────────────────────┐
│  GEMINI PRO (2M Context) = Strategic Brain                     │
│  • Sees EVERYTHING (complete project history)                  │
│  • Generates PROMPT.md + @fix_plan.md                          │
│  • Prioritizes tasks, recognizes patterns                      │
│  • Adjusts strategy when problems occur                        │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  RALPH LOOP = Autonomous Execution                             │
│  • Reads PROMPT.md, works through @fix_plan.md                 │
│  • Circuit breaker, exit detection                             │
│  • Prevents infinite loops and API waste                       │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  CLAUDE = Executor                                              │
│  • Writes code, uses tools                                     │
│  • Logs events → back to Gemini                                │
│  • Best-in-class code generation                               │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture

### Why This Works

| Aspect | Without Orchestrator | With Gemini Orchestrator |
|--------|---------------------|--------------------------|
| **Context** | Claude forgets after ~200K | Gemini retains 2M tokens |
| **Planning** | Claude improvises | Gemini plans strategically |
| **Patterns** | Not recognized | Gemini detects repetitions |
| **Adaptation** | Manual intervention needed | Automatic re-prioritization |
| **Errors** | Claude stuck → User must help | Gemini suggests alternatives |

### Component Interaction

```
User gives task
       ↓
orchestrate init "Build REST API"
       ↓
Gemini analyzes & generates PROMPT.md + @fix_plan.md
       ↓
ralph --monitor (autonomous loop)
       ↓
Claude executes tasks, logs events
       ↓
Events → ~/.claude-memory/events.jsonl
       ↓
Gemini consolidates every 5 min (with Pro subscription)
       ↓
On problems: orchestrate stuck "Description"
       ↓
After many tasks: orchestrate analyze
       ↓
Session end: orchestrate summary
```

## Installation

### Prerequisites

- Python 3.8+
- Bash 4.0+
- Node.js (for CLI tools)
- tmux (optional, for monitoring)
- jq (for JSON processing)

### Step 1: Clone Repository

```bash
git clone https://github.com/Ralle1976/selbst-orchestrierend.git
cd selbst-orchestrierend
```

### Step 2: Install Components

```bash
# Install Python dependencies
pip install --user -r requirements.txt

# Install Ralph globally
cd ralph-system
./install.sh
cd ..

# Copy core files to Claude memory directory
mkdir -p ~/.claude-memory
cp src/*.py ~/.claude-memory/
cp scripts/*.sh ~/.claude-memory/
chmod +x ~/.claude-memory/*.sh ~/.claude-memory/*.py

# Create command wrappers
mkdir -p ~/.local/bin
echo '#!/bin/bash
python3 ~/.claude-memory/gemini_orchestrator.py "$@"' > ~/.local/bin/orchestrate
echo '#!/bin/bash
python3 ~/.claude-memory/memory_interface.py "$@"' > ~/.local/bin/memory
echo '#!/bin/bash
~/.claude-memory/claude_start.sh "$@"' > ~/.local/bin/claude-start
chmod +x ~/.local/bin/{orchestrate,memory,claude-start}

# Ensure ~/.local/bin is in PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Step 3: Configure API Access

The system uses multiple AI providers with automatic fallback:

1. **Gemini Pro** (Primary - requires subscription ~$20/month)
   - Set up Gemini CLI: `gemini auth login`

2. **Qwen** (Fallback - generous free tier)
   - Get API key from [DashScope](https://dashscope.console.aliyun.com/)
   - Configure Qwen CLI

3. **Kimi** (Emergency fallback)
   - Get API key from [Moonshot](https://platform.moonshot.cn/)
   - `export MOONSHOT_API_KEY=sk-...`

## Quick Start

```bash
# 1. Start the system (launches daemon, shows status)
claude-start

# 2. Initialize a new task (Gemini plans everything)
orchestrate init "Create a REST API for a booking system with Python Flask"

# 3. Start autonomous execution
ralph --monitor

# 4. If stuck on something
orchestrate stuck "Getting connection timeout errors"

# 5. Check progress analysis
orchestrate analyze

# 6. End session with summary
orchestrate summary
```

## Components

### 1. Gemini Orchestrator (`src/gemini_orchestrator.py`)

The strategic brain that:
- Analyzes user tasks and creates execution plans
- Generates `PROMPT.md` (instructions) and `@fix_plan.md` (task list)
- Provides help when stuck
- Summarizes sessions for context preservation

**Commands:**
```bash
orchestrate init "task description"  # Initialize new task
orchestrate analyze                   # Analyze current situation
orchestrate replan                    # Re-prioritize tasks
orchestrate stuck "error description" # Get help with blockers
orchestrate summary                   # Generate session summary
orchestrate next                      # Suggest next action
```

### 2. Multi-Provider Consolidator (`src/multi_provider_consolidator.py`)

Handles memory consolidation with automatic provider fallback:

| Provider | Priority | Daily Limit | Context |
|----------|----------|-------------|---------|
| Gemini Pro | 1 | ~10,000 | 2M tokens |
| Qwen | 2 | ~500 | 32K tokens |
| Kimi | 3 | ~100 | 256K tokens |

**Commands:**
```bash
python3 ~/.claude-memory/multi_provider_consolidator.py status  # Show status
python3 ~/.claude-memory/multi_provider_consolidator.py force   # Force consolidation
python3 ~/.claude-memory/multi_provider_consolidator.py daemon  # Run as daemon
```

### 3. Memory Interface (`src/memory_interface.py`)

Simple key-value and event storage:

```bash
memory write "key" "value"           # Store knowledge
memory read "key"                    # Retrieve knowledge
memory event '{"action": "done"}'    # Log event
memory context 4000                  # Get context for prompts
memory status                        # Show memory status
```

### 4. Ralph System (`ralph-system/`)

Autonomous development loop based on [ralph-claude-code](https://github.com/frankbria/ralph-claude-code):

- **Circuit Breaker**: Prevents infinite loops
- **Exit Detection**: Stops when tasks are complete
- **Rate Limiting**: Respects API limits
- **tmux Integration**: Live monitoring dashboard

## Usage Guide

### Starting a New Project

```bash
# Create project directory
mkdir my-project && cd my-project

# Start orchestration system
claude-start

# Let Gemini plan the project
orchestrate init "Build a user authentication system with JWT tokens"

# Review generated files
cat PROMPT.md       # Instructions for Claude
cat @fix_plan.md    # Prioritized task list

# Start autonomous development
ralph --monitor
```

### Handling Problems

When Claude gets stuck:

```bash
# Get strategic help from Gemini
orchestrate stuck "TypeError: Cannot read property 'id' of undefined in UserController"

# Gemini will:
# 1. Analyze the error in context of all previous events
# 2. Check what was attempted before
# 3. Suggest alternative approaches
# 4. Optionally update the task plan
```

### Session Management

```bash
# At the end of a work session
orchestrate summary

# This creates a summary that includes:
# - What was accomplished
# - Key decisions made
# - Open items
# - Recommendations for next session

# The summary is saved and will be available next time you run:
claude-start
```

## Configuration

### Environment Variables

```bash
# Provider tier (affects rate limits)
export GEMINI_TIER="pro"  # or "free"

# Memory directory (default: ~/.claude-memory)
export MEMORY_DIR="$HOME/.claude-memory"
```

### Customizing Providers

Edit `src/multi_provider_consolidator.py`:

```python
PROVIDERS = {
    "gemini": {
        "model": "gemini-2.0-flash",  # or other models
        "daily_limit": 10000,          # adjust based on subscription
        "priority": 1
    },
    # ... other providers
}
```

---

# Deutsche Dokumentation

## Übersicht

Dieses System löst ein fundamentales Problem bei KI-unterstützter Entwicklung: **Kontextverlust**.

Traditionelle KI-Assistenten vergessen alles zwischen Sessions. Claude Code, obwohl leistungsstark, hat ein begrenztes Kontextfenster (~200K Token), das bei komplexen Projekten erschöpft wird.

**Unsere Lösung:** Nutze Gemini Pros massiven 2M Token Kontext als "strategisches Gehirn", das:
- Sich an alles über Sessions hinweg erinnert
- Aufgaben strategisch plant und priorisiert
- Muster erkennt und Strategie anpasst
- Ausführung an Claude delegiert (den besten Coder)

### Kern-Innovation

```
┌─────────────────────────────────────────────────────────────────┐
│  GEMINI PRO (2M Kontext) = Strategisches Gehirn                │
│  • Sieht ALLES (komplette Projekthistorie)                     │
│  • Generiert PROMPT.md + @fix_plan.md                          │
│  • Priorisiert Aufgaben, erkennt Muster                        │
│  • Passt Strategie bei Problemen an                            │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  RALPH LOOP = Autonome Ausführung                              │
│  • Liest PROMPT.md, arbeitet @fix_plan.md ab                   │
│  • Circuit-Breaker, Exit-Detection                             │
│  • Verhindert Endlosschleifen und API-Verschwendung            │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  CLAUDE = Executor                                              │
│  • Schreibt Code, nutzt Tools                                  │
│  • Loggt Events → zurück zu Gemini                             │
│  • Beste Code-Generierung seiner Klasse                        │
└─────────────────────────────────────────────────────────────────┘
```

## Architektur

### Warum das funktioniert

| Aspekt | Ohne Orchestrator | Mit Gemini Orchestrator |
|--------|-------------------|-------------------------|
| **Kontext** | Claude vergisst nach ~200K | Gemini behält 2M Token |
| **Planung** | Claude improvisiert | Gemini plant strategisch |
| **Muster** | Werden nicht erkannt | Gemini erkennt Wiederholungen |
| **Anpassung** | Manuelle Intervention nötig | Automatische Neupriorisierung |
| **Fehler** | Claude stuck → User muss helfen | Gemini schlägt Alternativen vor |

### Komponenten-Interaktion

```
User gibt Aufgabe
       ↓
orchestrate init "Baue REST API"
       ↓
Gemini analysiert & generiert PROMPT.md + @fix_plan.md
       ↓
ralph --monitor (autonome Schleife)
       ↓
Claude führt Tasks aus, loggt Events
       ↓
Events → ~/.claude-memory/events.jsonl
       ↓
Gemini konsolidiert alle 5 min (mit Pro Abo)
       ↓
Bei Problemen: orchestrate stuck "Beschreibung"
       ↓
Nach vielen Tasks: orchestrate analyze
       ↓
Session Ende: orchestrate summary
```

## Installation

### Voraussetzungen

- Python 3.8+
- Bash 4.0+
- Node.js (für CLI-Tools)
- tmux (optional, für Monitoring)
- jq (für JSON-Verarbeitung)

### Schritt 1: Repository klonen

```bash
git clone https://github.com/Ralle1976/selbst-orchestrierend.git
cd selbst-orchestrierend
```

### Schritt 2: Komponenten installieren

```bash
# Python-Abhängigkeiten installieren
pip install --user -r requirements.txt

# Ralph global installieren
cd ralph-system
./install.sh
cd ..

# Kerndateien ins Claude-Memory-Verzeichnis kopieren
mkdir -p ~/.claude-memory
cp src/*.py ~/.claude-memory/
cp scripts/*.sh ~/.claude-memory/
chmod +x ~/.claude-memory/*.sh ~/.claude-memory/*.py

# Befehlswrapper erstellen
mkdir -p ~/.local/bin
echo '#!/bin/bash
python3 ~/.claude-memory/gemini_orchestrator.py "$@"' > ~/.local/bin/orchestrate
echo '#!/bin/bash
python3 ~/.claude-memory/memory_interface.py "$@"' > ~/.local/bin/memory
echo '#!/bin/bash
~/.claude-memory/claude_start.sh "$@"' > ~/.local/bin/claude-start
chmod +x ~/.local/bin/{orchestrate,memory,claude-start}

# Sicherstellen dass ~/.local/bin im PATH ist
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Schritt 3: API-Zugang konfigurieren

Das System nutzt mehrere KI-Provider mit automatischem Fallback:

1. **Gemini Pro** (Primär - erfordert Abo ~20€/Monat)
   - Gemini CLI einrichten: `gemini auth login`

2. **Qwen** (Fallback - großzügiges kostenloses Kontingent)
   - API-Key von [DashScope](https://dashscope.console.aliyun.com/) holen
   - Qwen CLI konfigurieren

3. **Kimi** (Notfall-Fallback)
   - API-Key von [Moonshot](https://platform.moonshot.cn/) holen
   - `export MOONSHOT_API_KEY=sk-...`

## Schnellstart

```bash
# 1. System starten (startet Daemon, zeigt Status)
claude-start

# 2. Neue Aufgabe initialisieren (Gemini plant alles)
orchestrate init "Erstelle eine REST API für ein Buchungssystem mit Python Flask"

# 3. Autonome Ausführung starten
ralph --monitor

# 4. Bei Blockern
orchestrate stuck "Bekomme Connection Timeout Fehler"

# 5. Fortschrittsanalyse prüfen
orchestrate analyze

# 6. Session mit Zusammenfassung beenden
orchestrate summary
```

## Komponenten

### 1. Gemini Orchestrator (`src/gemini_orchestrator.py`)

Das strategische Gehirn, das:
- User-Aufgaben analysiert und Ausführungspläne erstellt
- `PROMPT.md` (Anweisungen) und `@fix_plan.md` (Aufgabenliste) generiert
- Hilfe bei Blockern bietet
- Sessions für Kontexterhaltung zusammenfasst

**Befehle:**
```bash
orchestrate init "Aufgabenbeschreibung"  # Neue Aufgabe initialisieren
orchestrate analyze                       # Aktuelle Situation analysieren
orchestrate replan                        # Aufgaben neu priorisieren
orchestrate stuck "Fehlerbeschreibung"    # Hilfe bei Blockern
orchestrate summary                       # Session-Zusammenfassung erstellen
orchestrate next                          # Nächste Aktion vorschlagen
```

### 2. Multi-Provider Consolidator (`src/multi_provider_consolidator.py`)

Handhabt Memory-Konsolidierung mit automatischem Provider-Fallback:

| Provider | Priorität | Tageslimit | Kontext |
|----------|-----------|------------|---------|
| Gemini Pro | 1 | ~10.000 | 2M Token |
| Qwen | 2 | ~500 | 32K Token |
| Kimi | 3 | ~100 | 256K Token |

**Befehle:**
```bash
python3 ~/.claude-memory/multi_provider_consolidator.py status  # Status zeigen
python3 ~/.claude-memory/multi_provider_consolidator.py force   # Konsolidierung erzwingen
python3 ~/.claude-memory/multi_provider_consolidator.py daemon  # Als Daemon starten
```

### 3. Memory Interface (`src/memory_interface.py`)

Einfacher Key-Value und Event-Speicher:

```bash
memory write "key" "value"           # Wissen speichern
memory read "key"                    # Wissen abrufen
memory event '{"action": "done"}'    # Event loggen
memory context 4000                  # Kontext für Prompts holen
memory status                        # Memory-Status zeigen
```

### 4. Ralph System (`ralph-system/`)

Autonome Entwicklungsschleife basierend auf [ralph-claude-code](https://github.com/frankbria/ralph-claude-code):

- **Circuit Breaker**: Verhindert Endlosschleifen
- **Exit Detection**: Stoppt wenn Aufgaben erledigt
- **Rate Limiting**: Respektiert API-Limits
- **tmux Integration**: Live-Monitoring-Dashboard

## Nutzungsanleitung

### Neues Projekt starten

```bash
# Projektverzeichnis erstellen
mkdir mein-projekt && cd mein-projekt

# Orchestrierungssystem starten
claude-start

# Gemini das Projekt planen lassen
orchestrate init "Baue ein Benutzer-Authentifizierungssystem mit JWT Tokens"

# Generierte Dateien prüfen
cat PROMPT.md       # Anweisungen für Claude
cat @fix_plan.md    # Priorisierte Aufgabenliste

# Autonome Entwicklung starten
ralph --monitor
```

### Probleme behandeln

Wenn Claude feststeckt:

```bash
# Strategische Hilfe von Gemini holen
orchestrate stuck "TypeError: Cannot read property 'id' of undefined in UserController"

# Gemini wird:
# 1. Den Fehler im Kontext aller vorherigen Events analysieren
# 2. Prüfen was zuvor versucht wurde
# 3. Alternative Ansätze vorschlagen
# 4. Optional den Aufgabenplan aktualisieren
```

### Session-Verwaltung

```bash
# Am Ende einer Arbeitssession
orchestrate summary

# Dies erstellt eine Zusammenfassung die enthält:
# - Was erreicht wurde
# - Getroffene Entscheidungen
# - Offene Punkte
# - Empfehlungen für nächste Session

# Die Zusammenfassung wird gespeichert und ist beim nächsten Start verfügbar:
claude-start
```

## Konfiguration

### Umgebungsvariablen

```bash
# Provider-Tier (beeinflusst Rate-Limits)
export GEMINI_TIER="pro"  # oder "free"

# Memory-Verzeichnis (Standard: ~/.claude-memory)
export MEMORY_DIR="$HOME/.claude-memory"
```

### Provider anpassen

`src/multi_provider_consolidator.py` bearbeiten:

```python
PROVIDERS = {
    "gemini": {
        "model": "gemini-2.0-flash",  # oder andere Modelle
        "daily_limit": 10000,          # je nach Abo anpassen
        "priority": 1
    },
    # ... andere Provider
}
```

---

## License / Lizenz

MIT License - see [LICENSE](LICENSE) for details.

## Credits / Danksagungen

- [Ralph for Claude Code](https://github.com/frankbria/ralph-claude-code) by Frank Bria
- Anthropic for Claude
- Google for Gemini
- Alibaba for Qwen
- Moonshot for Kimi

## Author / Autor

**Ralle1976** - [GitHub](https://github.com/Ralle1976)

---

*Built with AI, orchestrated by AI, for humans who want to get things done.*

*Gebaut mit KI, orchestriert von KI, für Menschen die Dinge erledigen wollen.*
