#!/bin/bash
#
# Claude Multi-Agent System - Unified Startup Script
#
# Startet alle Komponenten mit einem Befehl:
# - Gemini Memory Daemon (Hintergrund)
# - Prüft Provider-Status
# - Lädt letzten Kontext
# - Optional: Ralph im Projekt
#
# Usage:
#   ./claude_start.sh              # Nur System starten
#   ./claude_start.sh --ralph      # System + Ralph Loop
#   ./claude_start.sh --status     # Nur Status anzeigen
#   ./claude_start.sh --stop       # Daemons stoppen

set -e

# Pfade
MEMORY_DIR="$HOME/.claude-memory"
DAEMON_PID_FILE="$MEMORY_DIR/.consolidator.pid"
ORCHESTRATOR="$MEMORY_DIR/gemini_orchestrator.py"
CONSOLIDATOR="$MEMORY_DIR/multi_provider_consolidator.py"
MEMORY_INTERFACE="$MEMORY_DIR/memory_interface.py"

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Banner
show_banner() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}     🧠 Claude Multi-Agent System with Gemini Orchestrator  ${BLUE}║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Daemon starten
start_daemon() {
    if [ -f "$DAEMON_PID_FILE" ]; then
        OLD_PID=$(cat "$DAEMON_PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            log "Consolidator Daemon läuft bereits (PID: $OLD_PID)"
            return 0
        fi
    fi

    log "Starte Consolidator Daemon..."
    nohup python3 "$CONSOLIDATOR" daemon > "$MEMORY_DIR/consolidator.log" 2>&1 &
    echo $! > "$DAEMON_PID_FILE"
    success "Daemon gestartet (PID: $!)"
}

# Daemon stoppen
stop_daemon() {
    if [ -f "$DAEMON_PID_FILE" ]; then
        PID=$(cat "$DAEMON_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            rm -f "$DAEMON_PID_FILE"
            success "Daemon gestoppt (PID: $PID)"
        else
            rm -f "$DAEMON_PID_FILE"
            warn "Daemon war nicht aktiv"
        fi
    else
        warn "Kein Daemon PID gefunden"
    fi
}

# Provider-Status prüfen
check_providers() {
    log "Prüfe Provider-Status..."
    python3 "$CONSOLIDATOR" status 2>/dev/null | grep -E "(GEMINI|QWEN|KIMI|Available)" || true
}

# Letzten Kontext laden
load_context() {
    log "Lade letzten Kontext..."

    CONTEXT=$(python3 "$MEMORY_INTERFACE" context 2000 2>/dev/null || echo "")

    if [ -n "$CONTEXT" ] && [ "$CONTEXT" != "" ]; then
        echo ""
        echo -e "${YELLOW}═══ Letzter Kontext ═══${NC}"
        echo "$CONTEXT" | head -20
        if [ $(echo "$CONTEXT" | wc -l) -gt 20 ]; then
            echo "... (gekürzt)"
        fi
        echo -e "${YELLOW}════════════════════════${NC}"
    else
        log "Kein vorheriger Kontext gefunden"
    fi
}

# Memory-Status
show_status() {
    log "Memory-Status:"
    python3 "$MEMORY_INTERFACE" status 2>/dev/null || echo "  (nicht verfügbar)"
    echo ""
    check_providers
}

# Event loggen (für Hooks)
log_event() {
    local event_json="$1"
    python3 "$MEMORY_INTERFACE" event "$event_json" 2>/dev/null || true
}

# Nächste Aktion empfehlen
suggest_next() {
    echo ""
    log "Empfohlene nächste Aktion:"
    python3 "$ORCHESTRATOR" next 2>/dev/null || echo "  orchestrator nicht verfügbar"
}

# Ralph starten
start_ralph() {
    if [ ! -f "PROMPT.md" ] && [ ! -f "@fix_plan.md" ]; then
        warn "Kein Ralph-Projekt im aktuellen Verzeichnis"
        echo ""
        echo "Optionen:"
        echo "  1. Neues Projekt erstellen:"
        echo "     python3 $ORCHESTRATOR init 'Deine Aufgabe'"
        echo ""
        echo "  2. Mit ralph-setup:"
        echo "     ralph-setup mein-projekt && cd mein-projekt"
        return 1
    fi

    log "Starte Ralph Loop..."
    ralph --monitor
}

# Hauptlogik
main() {
    mkdir -p "$MEMORY_DIR"

    case "${1:-}" in
        --stop)
            stop_daemon
            exit 0
            ;;
        --status)
            show_banner
            show_status
            exit 0
            ;;
        --ralph)
            show_banner
            start_daemon
            load_context
            start_ralph
            ;;
        --event)
            # Für Hook-Integration
            log_event "$2"
            exit 0
            ;;
        --help|-h)
            echo "Claude Multi-Agent System Startup"
            echo ""
            echo "Usage: $0 [OPTION]"
            echo ""
            echo "Optionen:"
            echo "  (keine)      System starten, Kontext laden"
            echo "  --ralph      System + Ralph Loop starten"
            echo "  --status     Nur Status anzeigen"
            echo "  --stop       Daemons stoppen"
            echo "  --event JSON Event loggen (für Hooks)"
            echo "  --help       Diese Hilfe"
            exit 0
            ;;
        *)
            show_banner
            start_daemon
            echo ""
            check_providers
            echo ""
            load_context
            suggest_next
            echo ""
            success "System bereit!"
            echo ""
            echo "Nächste Schritte:"
            echo "  • Neue Aufgabe:  python3 $ORCHESTRATOR init 'Beschreibung'"
            echo "  • Ralph starten: ./claude_start.sh --ralph"
            echo "  • Analyse:       python3 $ORCHESTRATOR analyze"
            echo ""
            ;;
    esac
}

main "$@"
