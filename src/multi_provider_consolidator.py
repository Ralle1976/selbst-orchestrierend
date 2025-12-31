#!/usr/bin/env python3
"""
Multi-Provider Consolidation Daemon

Uses Gemini as primary, Qwen as fallback, Kimi as emergency fallback.
Maximizes free tier usage across all providers.

Usage:
    python3 multi_provider_consolidator.py run       # Run once
    python3 multi_provider_consolidator.py daemon    # Run as daemon
    python3 multi_provider_consolidator.py force     # Force with any available provider
    python3 multi_provider_consolidator.py status    # Show provider status
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Tuple

MEMORY_DIR = Path.home() / ".claude-memory"
EVENTS_FILE = MEMORY_DIR / "events.jsonl"
SUMMARIES_FILE = MEMORY_DIR / "summaries.json"
CONSOLIDATION_FLAG = MEMORY_DIR / ".needs_consolidation"
PROVIDER_STATUS_FILE = MEMORY_DIR / "provider_status.json"

# CLI Paths
CLI_DIR = Path.home() / ".claude/commands"
GEMINI_CLI = CLI_DIR / "gemini-cli"
QWEN_CLI = CLI_DIR / "qwen-cli"
KIMI_CLI = CLI_DIR / "kimi-cli"

# Provider Configuration
# GEMINI_TIER: "free" or "pro" - set via environment variable
GEMINI_TIER = os.getenv("GEMINI_TIER", "pro")  # Default to pro since user has subscription

PROVIDERS = {
    "gemini": {
        "cli": GEMINI_CLI,
        "model": "gemini-2.0-flash" if GEMINI_TIER == "pro" else "gemini-3.0-flash",
        "context": 2_000_000 if GEMINI_TIER == "pro" else 1_000_000,
        "daily_limit": 10000 if GEMINI_TIER == "pro" else 60,  # Pro: 2000 RPM = ~10k safe/day
        "cooldown_hours": 0.1 if GEMINI_TIER == "pro" else 1,  # Pro: 6 min cooldown
        "priority": 1
    },
    "qwen": {
        "cli": QWEN_CLI,
        "model": "qwen3-turbo",  # Fast, generous limits
        "context": 32_000,
        "daily_limit": 500,     # Very generous
        "cooldown_hours": 0.25, # 15 min
        "priority": 2
    },
    "kimi": {
        "cli": KIMI_CLI,
        "model": "kimi-k2-0711",
        "context": 256_000,
        "daily_limit": 100,
        "cooldown_hours": 0.5,
        "priority": 3
    }
}

# Shorter interval for Pro users (more API headroom)
MIN_INTERVAL_SECONDS = 300 if GEMINI_TIER == "pro" else 900  # Pro: 5 min, Free: 15 min


def load_json(path: Path, default=None) -> dict:
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return default if default is not None else {}


def save_json(path: Path, data: dict) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_provider_status() -> Dict:
    """Get or initialize provider status."""
    status = load_json(PROVIDER_STATUS_FILE, {
        "providers": {
            name: {
                "calls_today": 0,
                "last_call": None,
                "last_error": None,
                "consecutive_errors": 0,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            for name in PROVIDERS
        }
    })

    # Reset daily counters if new day
    today = datetime.now().strftime("%Y-%m-%d")
    for name, pstatus in status["providers"].items():
        if pstatus.get("date") != today:
            pstatus["calls_today"] = 0
            pstatus["date"] = today
            pstatus["consecutive_errors"] = 0

    return status


def update_provider_status(name: str, success: bool, error: str = None) -> None:
    """Update provider status after a call."""
    status = get_provider_status()
    pstatus = status["providers"][name]

    pstatus["calls_today"] += 1
    pstatus["last_call"] = datetime.now().isoformat()

    if success:
        pstatus["consecutive_errors"] = 0
        pstatus["last_error"] = None
    else:
        pstatus["consecutive_errors"] += 1
        pstatus["last_error"] = error

    save_json(PROVIDER_STATUS_FILE, status)


def can_use_provider(name: str) -> Tuple[bool, str]:
    """Check if provider can be used."""
    config = PROVIDERS[name]
    status = get_provider_status()
    pstatus = status["providers"][name]

    # Check if CLI exists
    if not config["cli"].exists():
        return False, f"CLI not found: {config['cli']}"

    # Check daily limit
    if pstatus["calls_today"] >= config["daily_limit"]:
        return False, f"Daily limit reached ({config['daily_limit']})"

    # Check cooldown after error
    if pstatus["consecutive_errors"] >= 3:
        if pstatus["last_call"]:
            last_call = datetime.fromisoformat(pstatus["last_call"])
            cooldown = timedelta(hours=config["cooldown_hours"] * pstatus["consecutive_errors"])
            if datetime.now() < last_call + cooldown:
                return False, f"In cooldown (consecutive errors: {pstatus['consecutive_errors']})"

    return True, "OK"


def select_provider() -> Tuple[Optional[str], str]:
    """Select best available provider."""
    # Sort by priority
    sorted_providers = sorted(PROVIDERS.items(), key=lambda x: x[1]["priority"])

    for name, config in sorted_providers:
        can_use, reason = can_use_provider(name)
        if can_use:
            return name, f"Selected {name}: {reason}"

    return None, "No providers available"


def call_provider(name: str, prompt: str) -> Optional[str]:
    """Call a specific provider."""
    config = PROVIDERS[name]

    payload = {
        "prompt": prompt,
        "model": config["model"]
    }

    # Add provider-specific options
    if name == "qwen":
        payload["approval_mode"] = "yolo"
    elif name == "gemini":
        payload["yolo"] = True
    elif name == "kimi":
        payload["approval_mode"] = "yolo"

    try:
        result = subprocess.run(
            ["node", str(config["cli"])],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=180  # 3 min timeout
        )

        if result.returncode == 0:
            response = json.loads(result.stdout)
            if response.get("success"):
                update_provider_status(name, True)
                return response.get("output")

        # Error
        error_msg = result.stderr or result.stdout
        update_provider_status(name, False, error_msg[:200])
        return None

    except subprocess.TimeoutExpired:
        update_provider_status(name, False, "Timeout")
        return None
    except Exception as e:
        update_provider_status(name, False, str(e)[:200])
        return None


def consolidate_with_fallback() -> Tuple[bool, str]:
    """Consolidate using best available provider with fallback."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    # Check if consolidation needed
    if not CONSOLIDATION_FLAG.exists():
        return False, "No consolidation needed"

    # Get events
    summaries = load_json(SUMMARIES_FILE, {"last_event_count": 0})
    if not EVENTS_FILE.exists():
        return False, "No events file"

    with open(EVENTS_FILE, 'r') as f:
        all_events = [json.loads(line) for line in f.readlines()]

    last_count = summaries.get("last_event_count", 0)
    new_events = all_events[last_count:]

    if not new_events:
        CONSOLIDATION_FLAG.unlink(missing_ok=True)
        return False, "No new events"

    # Prepare prompt
    events_text = "\n".join([
        f"[{e.get('timestamp', '')}] {json.dumps(e, ensure_ascii=False)}"
        for e in new_events[-50:]
    ])

    previous_summary = summaries.get("latest_summary", "Keine vorherige Zusammenfassung.")

    prompt = f"""Du bist ein Memory-Konsolidator für ein Multi-Agent-System.

VORHERIGE ZUSAMMENFASSUNG:
{previous_summary}

NEUE EVENTS ({len(new_events)} Stück):
{events_text}

AUFGABE:
1. Fasse die neuen Events kurz zusammen (max 150 Wörter)
2. Identifiziere wichtige Erkenntnisse/Entscheidungen
3. Notiere offene Aufgaben

FORMAT:
## Session Update
[Kurze Zusammenfassung]

## Erkenntnisse
- [Punkt 1]

## Offene Aufgaben
- [ ] [Aufgabe 1]
"""

    # Try providers in order
    provider_name, selection_msg = select_provider()
    if not provider_name:
        return False, f"No provider available: {selection_msg}"

    print(f"Using provider: {provider_name}")
    summary = call_provider(provider_name, prompt)

    if summary:
        # Update summaries
        total_events = len(all_events)
        summaries["latest_summary"] = summary
        summaries["last_consolidated"] = datetime.now().isoformat()
        summaries["last_event_count"] = total_events
        summaries["last_provider"] = provider_name

        if "consolidations" not in summaries:
            summaries["consolidations"] = []

        summaries["consolidations"].append({
            "timestamp": datetime.now().isoformat(),
            "events_processed": len(new_events),
            "total_events": total_events,
            "provider": provider_name
        })
        summaries["consolidations"] = summaries["consolidations"][-100:]

        save_json(SUMMARIES_FILE, summaries)
        CONSOLIDATION_FLAG.unlink(missing_ok=True)

        return True, f"Consolidated with {provider_name}"

    # Try fallback
    for fallback_name in ["qwen", "kimi", "gemini"]:
        if fallback_name == provider_name:
            continue
        can_use, _ = can_use_provider(fallback_name)
        if can_use:
            print(f"Trying fallback: {fallback_name}")
            summary = call_provider(fallback_name, prompt)
            if summary:
                # Save (same as above)
                summaries["latest_summary"] = summary
                summaries["last_consolidated"] = datetime.now().isoformat()
                summaries["last_event_count"] = len(all_events)
                summaries["last_provider"] = fallback_name
                save_json(SUMMARIES_FILE, summaries)
                CONSOLIDATION_FLAG.unlink(missing_ok=True)
                return True, f"Consolidated with fallback {fallback_name}"

    return False, "All providers failed"


def show_status() -> None:
    """Show multi-provider status."""
    status = get_provider_status()

    print("Multi-Provider Consolidator Status")
    print("=" * 50)

    for name, config in PROVIDERS.items():
        pstatus = status["providers"][name]
        can_use, reason = can_use_provider(name)

        print(f"\n{name.upper()} (priority: {config['priority']})")
        print(f"  CLI: {'OK' if config['cli'].exists() else 'MISSING'}")
        print(f"  Model: {config['model']}")
        print(f"  Context: {config['context']:,} tokens")
        print(f"  Calls today: {pstatus['calls_today']}/{config['daily_limit']}")
        print(f"  Last call: {pstatus.get('last_call', 'Never')}")
        print(f"  Errors: {pstatus['consecutive_errors']}")
        print(f"  Available: {'YES' if can_use else f'NO - {reason}'}")

    print("\n" + "=" * 50)
    summaries = load_json(SUMMARIES_FILE, {})
    print(f"Last consolidation: {summaries.get('last_consolidated', 'Never')}")
    print(f"Last provider used: {summaries.get('last_provider', 'None')}")
    print(f"Events processed: {summaries.get('last_event_count', 0)}")


def daemon_mode():
    """Run as daemon."""
    print("Starting Multi-Provider Consolidator Daemon...")
    print(f"Check interval: 30 minutes")

    while True:
        try:
            if CONSOLIDATION_FLAG.exists():
                print(f"\n[{datetime.now().isoformat()}] Consolidation triggered")
                success, msg = consolidate_with_fallback()
                print(f"Result: {msg}")
            else:
                print(".", end="", flush=True)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)

        time.sleep(1800)  # 30 minutes


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "run":
        success, msg = consolidate_with_fallback()
        print(msg)
    elif cmd == "force":
        CONSOLIDATION_FLAG.touch()
        success, msg = consolidate_with_fallback()
        print(msg)
    elif cmd == "daemon":
        daemon_mode()
    elif cmd == "status":
        show_status()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
