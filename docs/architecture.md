# Multi-Agent Shared Memory Architecture

## Komponenten

### 1. Memory Store (JSON-basiert)
Pfad: `~/.claude-memory/`

```
knowledge.json      - Strukturiertes Wissen (Key-Value)
events.jsonl        - Chronologische Events (append-only)
summaries.json      - Gemini-generierte Zusammenfassungen
agent_states.json   - Zustand der laufenden Agents
```

### 2. Memory Interface (Python)

```python
# Einfaches Interface für alle Agents
class SharedMemory:
    def write(self, key: str, value: any) -> None
    def read(self, key: str) -> any
    def append_event(self, event: dict) -> None
    def get_context(self, max_tokens: int = 4000) -> str
    def request_consolidation(self) -> None  # Triggert Gemini
```

### 3. Gemini Consolidation Daemon

Läuft als Background-Task, konsolidiert wenn:
- 30 Minuten vergangen
- >10 neue Events
- Explizit angefordert

### 4. Watch Daemon (NEU!)

Überwacht Ralph automatisch und greift bei Stillstand ein:

```
┌─────────────────────────────────────────────────────────┐
│  orchestrate watch                                      │
│     │                                                   │
│     ├──▶ Überwacht @fix_plan.md alle 60 Sekunden       │
│     ├──▶ Erkennt Stillstand (>180s ohne Änderung)      │
│     ├──▶ Schreibt Hints → .orchestrator_hints.md       │
│     └──▶ Eskaliert nach 3x Stillstand                  │
└─────────────────────────────────────────────────────────┘
```

**Kommunikationsdateien:**
| Datei | Zweck |
|-------|-------|
| `.orchestrator_hints.md` | Hints vom Watch-Daemon für Ralph |
| `.ralph_status.json` | Status von Ralph (optional) |

### 5. Agent-Integration

Jeder Agent erhält beim Start:
```bash
MEMORY_PATH=~/.claude-memory
MEMORY_CONTEXT=$(python3 memory_interface.py get_context)
```

## Workflow

```
Agent A                    Memory Store              Gemini Daemon
   │                           │                          │
   │─── write("task_x", done)──→│                          │
   │                           │                          │
   │                           │←── every 30min ──────────│
   │                           │    "consolidate"          │
   │                           │                          │
   │                           │─── events.jsonl ────────→│
   │                           │                          │
   │                           │←── summaries.json ───────│
   │                           │                          │
   │←── get_context() ─────────│                          │
```

## Neuer Workflow mit Watch Daemon

```
┌─────────────────────────────────────────────────────────────────┐
│  Terminal 1: orchestrate watch                                  │
│     │                                                           │
│     │ überwacht @fix_plan.md                                    │
│     │                                                           │
│     └───▶ Bei Stillstand: schreibt .orchestrator_hints.md      │
│                    │                                            │
│                    ▼                                            │
│  Terminal 2: ralph --monitor                                    │
│     │                                                           │
│     ├──▶ Liest PROMPT.md + @fix_plan.md                        │
│     ├──▶ Prüft .orchestrator_hints.md                          │
│     ├──▶ Führt Tasks aus (Claude)                              │
│     └──▶ Markiert [x] → Watch erkennt Fortschritt              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Beispiel: Ralph + Gemini Memory + Watch

1. User startet `orchestrate watch` (Hintergrund)
2. User startet `ralph --monitor`
3. Ralph schreibt Progress → @fix_plan.md
4. Watch Daemon überwacht → erkennt Stillstand
5. Watch schreibt Hint → .orchestrator_hints.md
6. Ralph liest Hint, passt Strategie an
7. Gemini Daemon (alle 30 min): Fasst Progress zusammen
8. Nächste Ralph-Session: Liest Zusammenfassung als Kontext

## Quick Start

```bash
# Alles auf einmal starten:
claude-start --ralph

# Oder manuell:
orchestrate watch &      # Watch im Hintergrund
ralph --monitor          # Ralph im Vordergrund
```
