#!/usr/bin/env python3
"""
Project Wizard - Interactive Project Setup Generator

Creates optimized PROMPT.md and @fix_plan.md based on user requirements.
Can be used standalone or called by Claude Code.

Usage:
    python3 project_wizard.py interactive    # Full interactive mode
    python3 project_wizard.py quick "desc"   # Quick setup from description
    python3 project_wizard.py templates      # Show available templates
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Project Templates
TEMPLATES = {
    "web_fullstack": {
        "name": "Web Application (Fullstack)",
        "description": "Frontend + Backend + Database",
        "default_stack": {
            "backend": "Python + FastAPI",
            "frontend": "React + TypeScript",
            "database": "PostgreSQL",
            "auth": "JWT"
        },
        "phases": [
            ("Setup", ["Projektstruktur anlegen", "Dependencies installieren", "Datenbank-Schema erstellen"]),
            ("Backend", ["API-Endpunkte definieren", "Datenbank-Models erstellen", "Business Logic implementieren"]),
            ("Auth", ["User-Registration", "Login/Logout", "JWT Token Handling"]),
            ("Frontend", ["Komponenten erstellen", "API-Integration", "Routing einrichten"]),
            ("Testing", ["Unit Tests Backend", "Integration Tests", "E2E Tests"]),
            ("Deployment", ["Docker Setup", "Environment Config", "CI/CD Pipeline"])
        ],
        "recommended_agents": ["api-architect", "security-reviewer", "web-app-architect"],
        "skills": ["orchestrate", "memory"]
    },
    "rest_api": {
        "name": "REST API Service",
        "description": "Backend-only API service",
        "default_stack": {
            "backend": "Python + FastAPI",
            "database": "PostgreSQL",
            "docs": "OpenAPI/Swagger"
        },
        "phases": [
            ("Setup", ["Projektstruktur", "Dependencies", "Config Management"]),
            ("Database", ["Schema Design", "Models", "Migrations"]),
            ("API", ["Endpunkte implementieren", "Validation", "Error Handling"]),
            ("Auth", ["Authentication", "Authorization", "Rate Limiting"]),
            ("Testing", ["Unit Tests", "Integration Tests", "API Tests"]),
            ("Docs", ["OpenAPI Schema", "README", "Examples"])
        ],
        "recommended_agents": ["api-architect", "security-reviewer"],
        "skills": ["orchestrate"]
    },
    "cli_tool": {
        "name": "CLI Tool",
        "description": "Command-line application",
        "default_stack": {
            "language": "Python",
            "cli_framework": "Click/Typer",
            "config": "TOML/YAML"
        },
        "phases": [
            ("Setup", ["Projektstruktur", "CLI Framework Setup", "Config Handling"]),
            ("Commands", ["Hauptkommandos implementieren", "Subcommands", "Options/Arguments"]),
            ("Features", ["Core Logic", "Error Handling", "Output Formatting"]),
            ("UX", ["Help Texts", "Progress Bars", "Colors/Styling"]),
            ("Testing", ["Unit Tests", "Integration Tests", "CLI Tests"]),
            ("Distribution", ["PyPI Setup", "Executable Build", "README"])
        ],
        "recommended_agents": ["docs-architect"],
        "skills": ["orchestrate"]
    },
    "automation": {
        "name": "Automation Script",
        "description": "Workflow automation, scripting",
        "default_stack": {
            "language": "Python",
            "scheduling": "Optional (cron/schedule)",
            "logging": "loguru"
        },
        "phases": [
            ("Setup", ["Script-Struktur", "Dependencies", "Config"]),
            ("Core", ["Hauptlogik implementieren", "Error Handling", "Logging"]),
            ("Integration", ["API-Calls", "File Operations", "Data Processing"]),
            ("Testing", ["Unit Tests", "Mocks für externe Services"]),
            ("Deployment", ["Scheduling Setup", "Monitoring", "Alerting"])
        ],
        "recommended_agents": [],
        "skills": ["orchestrate"]
    }
}

# Technology Recommendations
TECH_RECOMMENDATIONS = {
    "backend": {
        "Python + FastAPI": "Modern, async, automatische Docs. Empfohlen für APIs.",
        "Python + Flask": "Einfach, flexibel. Gut für kleinere Projekte.",
        "Node.js + Express": "JavaScript überall. Großes Ecosystem.",
        "Go + Gin": "Performance, einfache Deployment. Gut für Microservices.",
    },
    "frontend": {
        "React + TypeScript": "Industriestandard, große Community.",
        "Vue.js": "Sanfte Lernkurve, gut dokumentiert.",
        "Svelte": "Kompiliert zu vanilla JS, sehr performant.",
        "HTMX": "Einfach, serverseitig. Gut für MVPs.",
    },
    "database": {
        "PostgreSQL": "Robust, feature-reich. Empfohlen für Production.",
        "SQLite": "Eingebettet, kein Server. Perfekt für MVPs.",
        "MongoDB": "Dokumentenbasiert, flexibles Schema.",
        "Redis": "In-Memory, Cache, Queues.",
    }
}

# Scope Definitions
SCOPES = {
    "mvp": {
        "name": "MVP (Minimal Viable Product)",
        "description": "Schnell, nur essenzielle Features",
        "test_coverage": "Basic",
        "docs": "Minimal",
        "security": "Basic",
        "estimated_tasks": "10-15"
    },
    "standard": {
        "name": "Standard",
        "description": "Solide Basis mit Tests und Docs",
        "test_coverage": "70%+",
        "docs": "README + API Docs",
        "security": "Standard Practices",
        "estimated_tasks": "20-30"
    },
    "production": {
        "name": "Production-Ready",
        "description": "Vollständig mit Security, Monitoring, CI/CD",
        "test_coverage": "90%+",
        "docs": "Vollständig",
        "security": "Security Review",
        "estimated_tasks": "40+"
    }
}


def print_banner():
    """Print wizard banner."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║         🧙 Project Wizard - Projekt-Initialisierung       ║
╚═══════════════════════════════════════════════════════════╝
""")


def ask_choice(question: str, options: List[str], allow_multiple: bool = False) -> List[int]:
    """Interactive choice selection."""
    print(f"\n{question}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")

    if allow_multiple:
        print("\n  (Mehrere mit Komma trennen, z.B. 1,3,4)")

    while True:
        try:
            answer = input("\nAuswahl: ").strip()
            if allow_multiple:
                indices = [int(x.strip()) - 1 for x in answer.split(",")]
            else:
                indices = [int(answer) - 1]

            if all(0 <= i < len(options) for i in indices):
                return indices
            print("Ungültige Auswahl, bitte erneut versuchen.")
        except ValueError:
            print("Bitte Zahlen eingeben.")


def ask_text(question: str, default: str = "") -> str:
    """Ask for text input."""
    prompt = f"\n{question}"
    if default:
        prompt += f" [{default}]"
    prompt += ": "

    answer = input(prompt).strip()
    return answer if answer else default


def generate_prompt_md(config: Dict) -> str:
    """Generate PROMPT.md content."""
    template = TEMPLATES.get(config["template"], TEMPLATES["rest_api"])

    content = f"""# {config['name']}

## Ziel
{config['description']}

## Technologie-Stack
"""

    for key, value in config.get("stack", template["default_stack"]).items():
        content += f"- **{key.title()}:** {value}\n"

    content += f"""
## Anforderungen
"""
    for feature in config.get("features", []):
        content += f"- {feature}\n"

    content += f"""
## Scope: {SCOPES[config.get('scope', 'mvp')]['name']}
- Test Coverage: {SCOPES[config.get('scope', 'mvp')]['test_coverage']}
- Dokumentation: {SCOPES[config.get('scope', 'mvp')]['docs']}
- Geschätzte Tasks: {SCOPES[config.get('scope', 'mvp')]['estimated_tasks']}

## Empfohlene Agents/Skills
"""

    content += "- **Orchestrierung:** `orchestrate analyze` bei Blockern, `orchestrate replan` bei Änderungen\n"
    for agent in template.get("recommended_agents", []):
        content += f"- **{agent}:** Für spezialisierte Aufgaben\n"

    content += f"""
## Exit-Kriterien
Ralph soll stoppen wenn:
- Alle Tasks in @fix_plan.md erledigt [x]
- Keine Build-Fehler
- Tests bestanden (falls im Scope)

## Wichtige Hinweise
- Bei Blockern: `orchestrate stuck "Beschreibung"`
- Nach 10+ Tasks: `orchestrate analyze` für Fortschrittscheck
- Session speichern: `orchestrate summary`
"""

    return content


def generate_fix_plan_md(config: Dict) -> str:
    """Generate @fix_plan.md content."""
    template = TEMPLATES.get(config["template"], TEMPLATES["rest_api"])
    scope = config.get("scope", "mvp")

    content = f"""# {config['name']} - Task-Liste

Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Scope: {SCOPES[scope]['name']}

"""

    for phase_name, tasks in template["phases"]:
        content += f"## Phase: {phase_name}\n"
        for task in tasks:
            content += f"- [ ] {task}\n"
        content += "\n"

    # Add scope-specific tasks
    if scope in ["standard", "production"]:
        content += "## Phase: Quality Assurance\n"
        content += "- [ ] Code Review durchführen\n"
        content += "- [ ] Security Check\n"
        if scope == "production":
            content += "- [ ] Performance Optimierung\n"
            content += "- [ ] Load Testing\n"
            content += "- [ ] Monitoring Setup\n"
        content += "\n"

    content += "## Phase: Finalisierung\n"
    content += "- [ ] Dokumentation vervollständigen\n"
    content += "- [ ] README aktualisieren\n"
    content += "- [ ] Final Cleanup\n"

    return content


def interactive_wizard():
    """Full interactive wizard mode."""
    print_banner()
    print("Ich helfe dir, dein Projekt optimal zu definieren.\n")

    config = {}

    # Step 1: Project Type
    template_options = [f"{t['name']} - {t['description']}" for t in TEMPLATES.values()]
    choice = ask_choice("Was für ein Projekt möchtest du erstellen?", template_options)
    config["template"] = list(TEMPLATES.keys())[choice[0]]
    template = TEMPLATES[config["template"]]

    print(f"\n✓ Gewählt: {template['name']}")

    # Step 2: Project Name & Description
    config["name"] = ask_text("Wie soll das Projekt heißen?", "my-project")
    config["description"] = ask_text("Beschreibe kurz was es tun soll")

    # Step 3: Technology Stack
    print("\n📚 Technologie-Stack")
    print(f"   Standard für {template['name']}:")
    for key, value in template["default_stack"].items():
        print(f"   - {key}: {value}")

    customize = ask_text("Stack anpassen? (j/n)", "n").lower() == "j"

    if customize:
        config["stack"] = {}
        for key, default_value in template["default_stack"].items():
            if key in TECH_RECOMMENDATIONS:
                print(f"\nOptionen für {key}:")
                for tech, desc in TECH_RECOMMENDATIONS[key].items():
                    print(f"  • {tech}: {desc}")
                config["stack"][key] = ask_text(f"{key.title()}", default_value)
            else:
                config["stack"][key] = default_value

    # Step 4: Features
    common_features = [
        "Benutzer-Authentifizierung (JWT)",
        "Datenbank-Anbindung",
        "Input Validation",
        "Error Handling",
        "Logging",
        "Unit Tests",
        "API Documentation",
        "Docker Setup"
    ]

    feature_choices = ask_choice(
        "Welche Features brauchst du?",
        common_features,
        allow_multiple=True
    )
    config["features"] = [common_features[i] for i in feature_choices]

    # Step 5: Scope
    scope_options = [f"{s['name']} - {s['description']}" for s in SCOPES.values()]
    scope_choice = ask_choice("Wie umfangreich soll das Projekt sein?", scope_options)
    config["scope"] = list(SCOPES.keys())[scope_choice[0]]

    # Generate files
    print("\n" + "="*60)
    print("Generiere Projektdateien...")

    prompt_content = generate_prompt_md(config)
    fix_plan_content = generate_fix_plan_md(config)

    # Write files
    Path("PROMPT.md").write_text(prompt_content)
    Path("@fix_plan.md").write_text(fix_plan_content)

    print("\n✅ Dateien erstellt:")
    print("   • PROMPT.md")
    print("   • @fix_plan.md")

    # Show recommendations
    print("\n📋 Empfohlene nächste Schritte:")
    print("   1. Dateien prüfen und ggf. anpassen")
    print("   2. ralph --monitor starten")
    print("   3. Bei Problemen: orchestrate stuck '...'")

    print(f"\n🤖 Empfohlene Agents für {template['name']}:")
    for agent in template.get("recommended_agents", []):
        print(f"   • {agent}")

    print("\n" + "="*60)

    return config


def quick_setup(description: str):
    """Quick setup from description (uses Gemini if available)."""
    print_banner()
    print(f"Quick Setup für: {description}\n")

    # Default to MVP REST API
    config = {
        "name": "quick-project",
        "description": description,
        "template": "rest_api",
        "scope": "mvp",
        "features": ["Input Validation", "Error Handling", "Logging"]
    }

    prompt_content = generate_prompt_md(config)
    fix_plan_content = generate_fix_plan_md(config)

    Path("PROMPT.md").write_text(prompt_content)
    Path("@fix_plan.md").write_text(fix_plan_content)

    print("✅ Quick Setup erstellt!")
    print("\nFür bessere Ergebnisse nutze:")
    print("  python3 project_wizard.py interactive")
    print("\nOder lass Gemini planen:")
    print(f"  orchestrate init \"{description}\"")


def show_templates():
    """Show available templates."""
    print_banner()
    print("Verfügbare Projekt-Templates:\n")

    for key, template in TEMPLATES.items():
        print(f"📁 {template['name']}")
        print(f"   {template['description']}")
        print(f"   Stack: {', '.join(template['default_stack'].values())}")
        print(f"   Phasen: {len(template['phases'])}")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "interactive":
        interactive_wizard()
    elif cmd == "quick" and len(sys.argv) >= 3:
        quick_setup(" ".join(sys.argv[2:]))
    elif cmd == "templates":
        show_templates()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
