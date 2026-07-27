# Normen-Segmentierungs-Tool

Dieses Repository enthält ein Python-Projekt für die segmentierte Verarbeitung von Normen-PDFs.

## Setup

1. Erstelle die virtuelle Umgebung:
   ```powershell
   py -3.11 -m venv .venv
   ```
2. Aktiviere die Umgebung:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
3. Installiere die Abhängigkeiten:
   ```powershell
   python -m pip install --upgrade pip setuptools wheel
   python -m pip install -e .[dev]
   ```
4. Installiere Git-Hooks:
   ```bash
   pre-commit install
   ```

## Start

Später kann der Server mit `uvicorn` gestartet werden:

```powershell
uvicorn normen_tool.main:app --reload
```

## Tests

```powershell
pytest
pytest --cov=src --cov-report=term-missing --cov-report=html
```
