#!/usr/bin/env python3
"""
Gemini Orchestrator - Das strategische Gehirn des Multi-Agent-Systems

Gemini hat den Überblick (2M Context) und steuert Claude-Agents.

Usage:
    python3 gemini_orchestrator.py init "User-Aufgabe hier"     # Neue Aufgabe initialisieren
    python3 gemini_orchestrator.py analyze                       # Aktuelle Situation analysieren
    python3 gemini_orchestrator.py replan                        # @fix_plan.md neu priorisieren
    python3 gemini_orchestrator.py stuck "Fehlerbeschreibung"    # Bei Blockern helfen
    python3 gemini_orchestrator.py summary                       # Session zusammenfassen
    python3 gemini_orchestrator.py next                          # Nächste strategische Aktion
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

MEMORY_DIR = Path.home() / ".claude-memory"
EVENTS_FILE = MEMORY_DIR / "events.jsonl"
KNOWLEDGE_FILE = MEMORY_DIR / "knowledge.json"
ORCHESTRATOR_LOG = MEMORY_DIR / "orchestrator_decisions.jsonl"
GEMINI_CLI = Path.home() / ".claude/commands/gemini-cli"

# Ralph project files (relative to CWD)
PROMPT_FILE = Path("PROMPT.md")
FIX_PLAN_FILE = Path("@fix_plan.md")
AGENT_FILE = Path("@AGENT.md")


def load_json(path: Path, default=None):
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return default or {}


def load_events(limit: int = 100) -> list:
    """Load recent events."""
    if not EVENTS_FILE.exists():
        return []
    with open(EVENTS_FILE, 'r') as f:
        lines = f.readlines()
    return [json.loads(line) for line in lines[-limit:]]


def load_file_if_exists(path: Path) -> str:
    """Load file content if it exists."""
    if path.exists():
        return path.read_text()
    return "[Datei existiert nicht]"


def call_gemini(prompt: str, model: str = "gemini-2.0-flash") -> Optional[str]:
    """Call Gemini with a prompt."""
    if not GEMINI_CLI.exists():
        print("ERROR: Gemini CLI not found", file=sys.stderr)
        return None

    payload = {
        "prompt": prompt,
        "model": model,
        "yolo": True
    }

    try:
        result = subprocess.run(
            ["node", str(GEMINI_CLI)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=180
        )

        if result.returncode == 0:
            response = json.loads(result.stdout)
            if response.get("success"):
                return response.get("output")

        print(f"Gemini error: {result.stderr}", file=sys.stderr)
        return None

    except Exception as e:
        print(f"Gemini call failed: {e}", file=sys.stderr)
        return None


def log_decision(action: str, input_summary: str, output_summary: str):
    """Log orchestrator decisions."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    decision = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "input": input_summary[:500],
        "output": output_summary[:500]
    }
    with open(ORCHESTRATOR_LOG, 'a') as f:
        f.write(json.dumps(decision, ensure_ascii=False) + '\n')


def init_task(user_task: str):
    """Initialize a new task - Gemini creates PROMPT.md and @fix_plan.md."""
    print(f"Initialisiere Aufgabe: {user_task[:100]}...")

    # Gather context
    knowledge = load_json(KNOWLEDGE_FILE, {})
    events = load_events(50)

    context_summary = ""
    if knowledge:
        context_summary += "## Bekanntes Wissen\n"
        for k, v in list(knowledge.items())[:10]:
            context_summary += f"- {k}: {v.get('value', v)}\n"

    if events:
        context_summary += "\n## Letzte Events\n"
        for e in events[-10:]:
            context_summary += f"- {e.get('timestamp', '')[:16]}: {e.get('action', str(e)[:50])}\n"

    prompt = f"""Du bist der strategische Orchestrator eines autonomen Entwicklungssystems.

AUFGABE VOM USER:
{user_task}

KONTEXT (bisheriges Wissen):
{context_summary if context_summary else "Keine vorherigen Informationen."}

DEINE AUFGABE:
Erstelle eine vollständige Projektplanung für das Ralph-System.

AUSGABE-FORMAT (EXAKT so, mit den Markern):

---PROMPT_MD_START---
# [Projektname]

## Ziel
[Klare Beschreibung des Ziels]

## Kontext
[Relevante Hintergrundinformationen]

## Anforderungen
1. [Anforderung 1]
2. [Anforderung 2]
...

## Technische Vorgaben
- [Vorgabe 1]
- [Vorgabe 2]

## Exit-Kriterien
Ralph soll stoppen wenn:
- Alle Tasks in @fix_plan.md erledigt sind
- Tests erfolgreich laufen
- [Weitere Kriterien]

## Wichtige Hinweise
- [Hinweis 1]
---PROMPT_MD_END---

---FIX_PLAN_START---
# Task-Liste

## Phase 1: [Name]
- [ ] Task 1 (Priorität: HOCH)
- [ ] Task 2 (Priorität: HOCH)

## Phase 2: [Name]
- [ ] Task 3 (Priorität: MITTEL)
- [ ] Task 4 (Priorität: MITTEL)

## Phase 3: [Name]
- [ ] Task 5 (Priorität: NIEDRIG)
---FIX_PLAN_END---

Sei präzise, priorisiere sinnvoll, und denke an alle notwendigen Schritte!
"""

    print("Frage Gemini um strategische Planung...")
    response = call_gemini(prompt, "gemini-2.0-flash")

    if not response:
        print("ERROR: Gemini konnte nicht antworten", file=sys.stderr)
        return

    # Parse response
    prompt_md = ""
    fix_plan = ""

    if "---PROMPT_MD_START---" in response and "---PROMPT_MD_END---" in response:
        start = response.find("---PROMPT_MD_START---") + len("---PROMPT_MD_START---")
        end = response.find("---PROMPT_MD_END---")
        prompt_md = response[start:end].strip()

    if "---FIX_PLAN_START---" in response and "---FIX_PLAN_END---" in response:
        start = response.find("---FIX_PLAN_START---") + len("---FIX_PLAN_START---")
        end = response.find("---FIX_PLAN_END---")
        fix_plan = response[start:end].strip()

    # Write files
    if prompt_md:
        PROMPT_FILE.write_text(prompt_md)
        print(f"✓ PROMPT.md erstellt ({len(prompt_md)} Zeichen)")
    else:
        print("⚠ PROMPT.md konnte nicht extrahiert werden")
        print("Raw response (first 500 chars):", response[:500])

    if fix_plan:
        FIX_PLAN_FILE.write_text(fix_plan)
        print(f"✓ @fix_plan.md erstellt ({len(fix_plan)} Zeichen)")
    else:
        print("⚠ @fix_plan.md konnte nicht extrahiert werden")

    log_decision("init", user_task[:200], f"prompt_md:{len(prompt_md)}, fix_plan:{len(fix_plan)}")

    print("\n🚀 Bereit! Starte mit: ralph --monitor")


def analyze_situation():
    """Analyze current situation and provide insights."""
    print("Analysiere aktuelle Situation...")

    events = load_events(100)
    knowledge = load_json(KNOWLEDGE_FILE, {})
    fix_plan = load_file_if_exists(FIX_PLAN_FILE)

    # Count completed vs pending tasks
    completed = fix_plan.count("[x]") + fix_plan.count("[X]")
    pending = fix_plan.count("[ ]")

    events_text = "\n".join([
        f"[{e.get('timestamp', '')[:16]}] {json.dumps(e, ensure_ascii=False)[:100]}"
        for e in events[-30:]
    ])

    prompt = f"""Du bist der strategische Orchestrator. Analysiere die aktuelle Situation.

AKTUELLER @fix_plan.md:
{fix_plan[:2000]}

TASK-STATUS:
- Erledigt: {completed}
- Offen: {pending}

LETZTE EVENTS:
{events_text}

ANALYSE-AUFGABEN:
1. Was wurde bisher erreicht?
2. Gibt es Probleme oder Blocker?
3. Ist die aktuelle Priorisierung noch sinnvoll?
4. Welche nächsten Schritte empfiehlst du?

Antworte strukturiert und präzise (max 300 Wörter).
"""

    response = call_gemini(prompt)
    if response:
        print("\n" + "="*60)
        print("GEMINI ANALYSE:")
        print("="*60)
        print(response)
        log_decision("analyze", f"completed:{completed}, pending:{pending}", response[:200])
    else:
        print("ERROR: Analyse fehlgeschlagen")


def replan():
    """Re-prioritize the fix plan based on current state."""
    print("Re-priorisiere @fix_plan.md...")

    events = load_events(100)
    current_plan = load_file_if_exists(FIX_PLAN_FILE)

    events_text = "\n".join([
        f"[{e.get('timestamp', '')[:16]}] {e.get('action', str(e)[:50])}"
        for e in events[-30:]
    ])

    prompt = f"""Du bist der strategische Orchestrator. Die aktuelle Task-Liste muss überarbeitet werden.

AKTUELLER @fix_plan.md:
{current_plan}

LETZTE EVENTS:
{events_text}

AUFGABE:
1. Analysiere welche Tasks erledigt wurden (markiere mit [x])
2. Identifiziere neue Tasks die hinzugefügt werden sollten
3. Re-priorisiere basierend auf Abhängigkeiten und Wichtigkeit
4. Entferne überflüssige oder doppelte Tasks

AUSGABE:
Gib den KOMPLETTEN neuen @fix_plan.md aus, ready to use.
Beginne mit "# Task-Liste" und nutze das Checkbox-Format "- [ ]" bzw "- [x]".
"""

    response = call_gemini(prompt)
    if response:
        # Extract just the task list part
        if "# Task-Liste" in response or "# Task" in response:
            FIX_PLAN_FILE.write_text(response)
            print(f"✓ @fix_plan.md aktualisiert")
            log_decision("replan", current_plan[:200], response[:200])
        else:
            print("Response:")
            print(response)
    else:
        print("ERROR: Replan fehlgeschlagen")


def handle_stuck(error_description: str):
    """Help when stuck on a problem."""
    print(f"Analysiere Blocker: {error_description[:100]}...")

    events = load_events(50)
    current_plan = load_file_if_exists(FIX_PLAN_FILE)

    events_text = "\n".join([
        f"[{e.get('timestamp', '')[:16]}] {json.dumps(e, ensure_ascii=False)[:100]}"
        for e in events[-20:]
    ])

    prompt = f"""Du bist der strategische Orchestrator. Ein Claude-Agent ist blockiert.

PROBLEM:
{error_description}

AKTUELLER @fix_plan.md:
{current_plan[:1500]}

LETZTE EVENTS:
{events_text}

HILFE BENÖTIGT:
1. Was ist die wahrscheinliche Ursache?
2. Welche alternativen Ansätze gibt es?
3. Sollte die Task-Reihenfolge geändert werden?
4. Gibt es fehlende Voraussetzungen?

Gib konkrete, umsetzbare Empfehlungen!
"""

    response = call_gemini(prompt)
    if response:
        print("\n" + "="*60)
        print("GEMINI HILFE:")
        print("="*60)
        print(response)
        log_decision("stuck", error_description[:200], response[:200])
    else:
        print("ERROR: Stuck-Analyse fehlgeschlagen")


def generate_summary():
    """Generate a session summary."""
    print("Erstelle Session-Zusammenfassung...")

    events = load_events(200)
    knowledge = load_json(KNOWLEDGE_FILE, {})
    current_plan = load_file_if_exists(FIX_PLAN_FILE)

    # Calculate stats
    completed = current_plan.count("[x]") + current_plan.count("[X]")
    pending = current_plan.count("[ ]")

    events_text = "\n".join([
        f"[{e.get('timestamp', '')[:16]}] {e.get('action', str(e)[:50])}"
        for e in events
    ])

    prompt = f"""Du bist der strategische Orchestrator. Erstelle eine Session-Zusammenfassung.

STATISTIKEN:
- Tasks erledigt: {completed}
- Tasks offen: {pending}
- Events gesamt: {len(events)}

ALLE EVENTS DIESER SESSION:
{events_text[:3000]}

AKTUELLER PLAN:
{current_plan[:1500]}

ERSTELLE:
1. **Was wurde erreicht** (Bullet Points)
2. **Wichtige Entscheidungen** (die getroffen wurden)
3. **Offene Punkte** (was noch zu tun ist)
4. **Empfehlungen** (für die nächste Session)

Format: Markdown, präzise, max 400 Wörter.
"""

    response = call_gemini(prompt)
    if response:
        print("\n" + "="*60)
        print("SESSION ZUSAMMENFASSUNG:")
        print("="*60)
        print(response)

        # Save to summaries
        summaries_file = MEMORY_DIR / "summaries.json"
        summaries = load_json(summaries_file, {"session_summaries": []})
        summaries["session_summaries"].append({
            "timestamp": datetime.now().isoformat(),
            "summary": response,
            "stats": {"completed": completed, "pending": pending, "events": len(events)}
        })
        summaries["session_summaries"] = summaries["session_summaries"][-20:]

        with open(summaries_file, 'w') as f:
            json.dump(summaries, f, indent=2, ensure_ascii=False)

        log_decision("summary", f"completed:{completed}, pending:{pending}", response[:200])
    else:
        print("ERROR: Summary fehlgeschlagen")


def suggest_next():
    """Suggest next strategic action."""
    events = load_events(30)
    current_plan = load_file_if_exists(FIX_PLAN_FILE)

    completed = current_plan.count("[x]") + current_plan.count("[X]")
    pending = current_plan.count("[ ]")

    # Determine situation
    if pending == 0 and completed > 0:
        print("🎉 Alle Tasks erledigt! Empfehlung: summary")
        return

    if completed == 0 and pending == 0:
        print("📋 Keine Tasks gefunden. Empfehlung: init 'Deine Aufgabe'")
        return

    recent_errors = sum(1 for e in events[-10:] if "error" in str(e).lower())
    if recent_errors >= 3:
        print(f"⚠ {recent_errors} Fehler in letzten 10 Events. Empfehlung: stuck 'Beschreibung'")
        return

    if completed > 10 and completed % 10 < 3:
        print(f"📊 {completed} Tasks erledigt. Empfehlung: analyze oder replan")
        return

    print(f"✓ Status: {completed} erledigt, {pending} offen. Weiter mit: ralph --monitor")


def main():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init" and len(sys.argv) >= 3:
        init_task(" ".join(sys.argv[2:]))
    elif cmd == "analyze":
        analyze_situation()
    elif cmd == "replan":
        replan()
    elif cmd == "stuck" and len(sys.argv) >= 3:
        handle_stuck(" ".join(sys.argv[2:]))
    elif cmd == "summary":
        generate_summary()
    elif cmd == "next":
        suggest_next()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
