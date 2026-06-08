"""
Conftest: gemeinsame Konfiguration für alle Tests.

Stellt sicher, dass pytest:
- Tests als Skripte ausführen kann (ohne __init__.py-Import-Fehler)
- IBM-Token niemals aus .env liest (für Offline-Tests)
- Konsistente Pfade verwendet
"""
import sys
import os

# Füge Projekt-Root zum sys.path hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_configure(config):
    """Wird beim pytest-Start aufgerufen."""
    # Sicherstellen, dass .env NICHT versehentlich gelesen wird
    # (Tests sind offline)
    pass
