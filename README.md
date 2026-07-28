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

Der Server kann über ein kleines Desktop-GUI gestartet und gestoppt werden:

```powershell
normen-tool-gui
```

Alternativ kann der Launcher auch als Modul gestartet werden:

```powershell
python -m normen_tool.server_launcher
```

Direkter Dateistart ist ebenfalls möglich:

```powershell
python src/normen_tool/server_launcher.py
```

Alternativ kann der Server weiterhin direkt mit `uvicorn` gestartet werden:

```powershell
uvicorn normen_tool.main:app --reload
```

Die Logs landen standardmäßig in `logs/normen_tool.log`.

### Troubleshooting Launcher

- Wenn `normen-tool-gui` nicht gefunden wird, führe im Projekt aus:
   - `python -m pip install -e .[dev]`
- Wenn der Prozess mit Exit-Code `1` endet, starte den Launcher in der aktiven `.venv` und prüfe die Log-Datei unter `logs/normen_tool.log`.
- Für einen schnellen Import-Check:
   - `python -c "import tkinter, uvicorn; print('ok')"`

## Tests

```powershell
pytest
pytest --cov=src --cov-report=term-missing --cov-report=html
```
