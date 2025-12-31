#!/usr/bin/env python3
"""
Shared Memory Interface for Multi-Agent Architecture

Usage:
    python3 memory_interface.py write <key> <value>
    python3 memory_interface.py read <key>
    python3 memory_interface.py event <json_event>
    python3 memory_interface.py context [max_tokens]
    python3 memory_interface.py consolidate
    python3 memory_interface.py status
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

MEMORY_DIR = Path.home() / ".claude-memory"
KNOWLEDGE_FILE = MEMORY_DIR / "knowledge.json"
EVENTS_FILE = MEMORY_DIR / "events.jsonl"
SUMMARIES_FILE = MEMORY_DIR / "summaries.json"
AGENT_STATES_FILE = MEMORY_DIR / "agent_states.json"
CONSOLIDATION_FLAG = MEMORY_DIR / ".needs_consolidation"


def ensure_dir():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any = None) -> Any:
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return default if default is not None else {}


def save_json(path: Path, data: Any) -> None:
    ensure_dir()
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_knowledge(key: str, value: Any) -> None:
    """Write key-value to knowledge store."""
    knowledge = load_json(KNOWLEDGE_FILE, {})
    knowledge[key] = {
        "value": value,
        "updated": datetime.now().isoformat(),
        "version": knowledge.get(key, {}).get("version", 0) + 1
    }
    save_json(KNOWLEDGE_FILE, knowledge)
    print(json.dumps({"success": True, "key": key}))


def read_knowledge(key: str) -> Optional[Any]:
    """Read value from knowledge store."""
    knowledge = load_json(KNOWLEDGE_FILE, {})
    if key in knowledge:
        print(json.dumps({"success": True, "value": knowledge[key]["value"]}))
        return knowledge[key]["value"]
    print(json.dumps({"success": False, "error": f"Key '{key}' not found"}))
    return None


def append_event(event_json: str) -> None:
    """Append event to chronological log."""
    ensure_dir()
    try:
        event = json.loads(event_json)
    except json.JSONDecodeError:
        event = {"message": event_json}

    event["timestamp"] = datetime.now().isoformat()

    with open(EVENTS_FILE, 'a') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')

    # Check if consolidation needed (>10 events since last)
    event_count = sum(1 for _ in open(EVENTS_FILE)) if EVENTS_FILE.exists() else 0
    summaries = load_json(SUMMARIES_FILE, {"last_event_count": 0})

    if event_count - summaries.get("last_event_count", 0) >= 10:
        CONSOLIDATION_FLAG.touch()

    print(json.dumps({"success": True, "event_count": event_count}))


def get_context(max_tokens: int = 4000) -> str:
    """Get consolidated context for agents."""
    context_parts = []

    # 1. Latest summary (if exists)
    summaries = load_json(SUMMARIES_FILE, {})
    if "latest_summary" in summaries:
        context_parts.append(f"## Session Summary\n{summaries['latest_summary']}")

    # 2. Key knowledge points
    knowledge = load_json(KNOWLEDGE_FILE, {})
    if knowledge:
        context_parts.append("## Current Knowledge")
        for key, data in list(knowledge.items())[:20]:  # Limit to 20 keys
            context_parts.append(f"- {key}: {data['value']}")

    # 3. Recent events (last 20)
    if EVENTS_FILE.exists():
        with open(EVENTS_FILE, 'r') as f:
            events = [json.loads(line) for line in f.readlines()[-20:]]
        if events:
            context_parts.append("## Recent Events")
            for e in events[-10:]:
                ts = e.get("timestamp", "")[:16]
                msg = e.get("message", e.get("action", str(e)))
                context_parts.append(f"- [{ts}] {msg}")

    context = "\n\n".join(context_parts)

    # Rough token estimate (4 chars = 1 token)
    if len(context) > max_tokens * 4:
        context = context[:max_tokens * 4] + "\n...[truncated]"

    print(context)
    return context


def request_consolidation() -> None:
    """Request Gemini consolidation."""
    ensure_dir()
    CONSOLIDATION_FLAG.touch()
    print(json.dumps({
        "success": True,
        "message": "Consolidation requested",
        "flag_path": str(CONSOLIDATION_FLAG)
    }))


def show_status() -> None:
    """Show memory status."""
    ensure_dir()

    event_count = sum(1 for _ in open(EVENTS_FILE)) if EVENTS_FILE.exists() else 0
    knowledge = load_json(KNOWLEDGE_FILE, {})
    summaries = load_json(SUMMARIES_FILE, {})
    needs_consolidation = CONSOLIDATION_FLAG.exists()

    status = {
        "memory_dir": str(MEMORY_DIR),
        "event_count": event_count,
        "knowledge_keys": len(knowledge),
        "last_consolidation": summaries.get("last_consolidated"),
        "events_since_consolidation": event_count - summaries.get("last_event_count", 0),
        "needs_consolidation": needs_consolidation,
        "knowledge_preview": list(knowledge.keys())[:10]
    }

    print(json.dumps(status, indent=2, ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "write" and len(sys.argv) >= 4:
        write_knowledge(sys.argv[2], sys.argv[3])
    elif cmd == "read" and len(sys.argv) >= 3:
        read_knowledge(sys.argv[2])
    elif cmd == "event" and len(sys.argv) >= 3:
        append_event(sys.argv[2])
    elif cmd == "context":
        max_tokens = int(sys.argv[2]) if len(sys.argv) >= 3 else 4000
        get_context(max_tokens)
    elif cmd == "consolidate":
        request_consolidation()
    elif cmd == "status":
        show_status()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
