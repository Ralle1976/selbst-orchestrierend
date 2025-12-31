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

### 4. Agent-Integration

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

## Beispiel: Ralph + Gemini Memory

1. User startet Ralph mit Aufgabe
2. Ralph schreibt Progress → events.jsonl
3. Gemini Daemon (alle 30 min): Fasst Progress zusammen
4. Nächste Ralph-Session: Liest Zusammenfassung als Kontext
