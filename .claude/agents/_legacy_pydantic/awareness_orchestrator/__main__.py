"""
Main entry point for running Awareness Orchestrator as a module.

Usage:
    python -m awareness_orchestrator orchestrate <file> <task>
    python -m awareness_orchestrator analyze <file>
    python -m awareness_orchestrator dashboard
"""

from .cli import main

if __name__ == "__main__":
    main()
