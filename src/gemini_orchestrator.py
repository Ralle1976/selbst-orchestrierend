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
    python3 gemini_orchestrator.py watch                         # Daemon: Überwacht Ralph, greift bei Stillstand ein
    python3 gemini_orchestrator.py watch --stop                  # Watch-Daemon stoppen
"""

import json
import os
import subprocess
import sys
import time
import hashlib
import signal
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

# Communication files (in project directory)
ORCHESTRATOR_HINTS = Path(".orchestrator_hints.md")
RALPH_STATUS_FILE = Path(".ralph_status.json")
WATCH_PID_FILE = MEMORY_DIR / ".orchestrator_watch.pid"

# Watch configuration
WATCH_INTERVAL = 60  # Check every 60 seconds
STALL_THRESHOLD = 180  # Consider stalled after 3 minutes without change
MAX_STALL_INTERVENTIONS = 3  # Max interventions before escalating


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


def get_file_hash(path: Path) -> str:
    """Get MD5 hash of file content."""
    if not path.exists():
        return ""
    return hashlib.md5(path.read_bytes()).hexdigest()


def write_hint(hint: str, priority: str = "INFO"):
    """Write a hint for Ralph to read."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    hint_content = f"""# Orchestrator Hint
**Zeit:** {timestamp}
**Priorität:** {priority}

{hint}

---
*Diese Datei wird automatisch vom Orchestrator generiert.*
*Ralph sollte diese Hinweise berücksichtigen.*
"""
    ORCHESTRATOR_HINTS.write_text(hint_content)
    print(f"[{timestamp}] Hint geschrieben: {hint[:50]}...")


def clear_hint():
    """Remove hint file after it's been processed."""
    if ORCHESTRATOR_HINTS.exists():
        ORCHESTRATOR_HINTS.unlink()


def read_ralph_status() -> dict:
    """Read Ralph's status file."""
    if RALPH_STATUS_FILE.exists():
        try:
            return json.loads(RALPH_STATUS_FILE.read_text())
        except:
            pass
    return {}


def watch_daemon():
    """Watch daemon - monitors Ralph and intervenes on stalls."""
    print("="*60)
    print("ORCHESTRATOR WATCH DAEMON")
    print("="*60)
    print(f"Überwache: {FIX_PLAN_FILE.absolute()}")
    print(f"Check-Intervall: {WATCH_INTERVAL}s")
    print(f"Stillstand-Schwelle: {STALL_THRESHOLD}s")
    print("="*60)

    # Save PID for stop command
    WATCH_PID_FILE.write_text(str(os.getpid()))

    # State tracking
    last_hash = get_file_hash(FIX_PLAN_FILE)
    last_change_time = time.time()
    stall_interventions = 0

    def signal_handler(sig, frame):
        print("\nWatch Daemon beendet.")
        WATCH_PID_FILE.unlink(missing_ok=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while True:
        try:
            time.sleep(WATCH_INTERVAL)

            current_hash = get_file_hash(FIX_PLAN_FILE)
            current_time = time.time()

            # Check for changes
            if current_hash != last_hash:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Änderung erkannt in @fix_plan.md")
                last_hash = current_hash
                last_change_time = current_time
                stall_interventions = 0
                clear_hint()  # Clear any previous hints
                continue

            # Check for stall
            time_since_change = current_time - last_change_time

            if time_since_change > STALL_THRESHOLD:
                stall_interventions += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠ Stillstand erkannt ({int(time_since_change)}s)")

                if stall_interventions >= MAX_STALL_INTERVENTIONS:
                    # Escalate - full replan
                    print("  → Eskalation: Führe vollständige Neuplanung durch...")
                    intervene_escalate()
                    last_change_time = current_time  # Reset timer
                else:
                    # Normal intervention - give hint
                    print(f"  → Intervention {stall_interventions}/{MAX_STALL_INTERVENTIONS}")
                    intervene_stall(time_since_change)
                    last_change_time = current_time  # Reset timer
            else:
                # Status update
                ralph_status = read_ralph_status()
                if ralph_status:
                    status_str = ralph_status.get("status", "unknown")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ralph: {status_str}, letzte Änderung vor {int(time_since_change)}s")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Überwache... (keine Änderung seit {int(time_since_change)}s)")

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Fehler: {e}")


def intervene_stall(stall_duration: float):
    """Intervene when Ralph appears stalled."""
    events = load_events(20)
    current_plan = load_file_if_exists(FIX_PLAN_FILE)

    # Get recent events for context
    events_text = "\n".join([
        f"- {e.get('action', str(e)[:50])}"
        for e in events[-5:]
    ]) if events else "Keine Events"

    prompt = f"""Du bist der Orchestrator. Ralph (Claude) scheint seit {int(stall_duration)} Sekunden festzustecken.

AKTUELLER @fix_plan.md:
{current_plan[:1500]}

LETZTE EVENTS:
{events_text}

AUFGABE:
Gib einen KURZEN, KONKRETEN Hinweis (max 100 Wörter):
1. Was könnte das Problem sein?
2. Welcher konkrete nächste Schritt hilft?

Sei direkt und praktisch!
"""

    response = call_gemini(prompt, "gemini-2.0-flash")
    if response:
        write_hint(response, "WARNUNG")
        log_decision("watch_intervene", f"stall:{int(stall_duration)}s", response[:200])
    else:
        write_hint("Orchestrator konnte keine Analyse durchführen. Bitte manuell mit 'orchestrate stuck' prüfen.", "FEHLER")


def intervene_escalate():
    """Escalated intervention - full replan."""
    print("  → Rufe Gemini für Neuplanung...")

    events = load_events(50)
    current_plan = load_file_if_exists(FIX_PLAN_FILE)

    events_text = "\n".join([
        f"[{e.get('timestamp', '')[:16]}] {e.get('action', str(e)[:50])}"
        for e in events[-20:]
    ])

    prompt = f"""Du bist der Orchestrator. Ralph (Claude) ist MEHRFACH festgesteckt. Zeit für eine Neuplanung.

AKTUELLER @fix_plan.md:
{current_plan}

LETZTE EVENTS:
{events_text}

ANALYSE & NEUPLANUNG:
1. Identifiziere das Kernproblem (warum steckt er fest?)
2. Welche Tasks sollten übersprungen/vereinfacht werden?
3. Gibt es einen alternativen Ansatz?

Gib aus:
1. KURZE ANALYSE (3-5 Zeilen)
2. KONKRETER NEXT STEP (1 Zeile)
3. Optional: Neue Task-Priorisierung

Sei pragmatisch - manchmal ist 'überspringen' die richtige Lösung!
"""

    response = call_gemini(prompt, "gemini-2.0-flash")
    if response:
        write_hint(response, "ESKALATION")
        log_decision("watch_escalate", "multiple_stalls", response[:300])

        # Also update @fix_plan.md if there's a clear new priority
        if "ÜBERSPRINGE" in response.upper() or "SKIP" in response.upper():
            print("  → Schlage Task-Änderung vor...")


def stop_watch_daemon():
    """Stop the watch daemon."""
    if WATCH_PID_FILE.exists():
        try:
            pid = int(WATCH_PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"Watch Daemon gestoppt (PID: {pid})")
            WATCH_PID_FILE.unlink(missing_ok=True)
        except ProcessLookupError:
            print("Watch Daemon war nicht aktiv")
            WATCH_PID_FILE.unlink(missing_ok=True)
        except Exception as e:
            print(f"Fehler beim Stoppen: {e}")
    else:
        print("Kein Watch Daemon aktiv")


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
    elif cmd == "watch":
        if len(sys.argv) >= 3 and sys.argv[2] == "--stop":
            stop_watch_daemon()
        else:
            watch_daemon()
    elif cmd == "hint":
        # Read current hint (for debugging)
        if ORCHESTRATOR_HINTS.exists():
            print(ORCHESTRATOR_HINTS.read_text())
        else:
            print("Keine Hints vorhanden")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
