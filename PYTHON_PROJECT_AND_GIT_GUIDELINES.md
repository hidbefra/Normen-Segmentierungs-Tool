# Python-Projekt- und Git-Richtlinien

Dieses Dokument beschreibt die zentralen Regeln für Python-Projekte und Git-Workflows im aktuellen Repository. Ziel ist konsistente Struktur, stabile Builds und einfache Wartbarkeit.

---

## 📋 Inhaltsverzeichnis

1. [Virtuelle Umgebung & Setup](#1-virtuelle-umgebung--setup)
2. [Paketverwaltung](#2-paketverwaltung)
3. [Projektstruktur](#3-projektstruktur)
4. [Codequalität und Tools](#4-codequalität-und-tools)
5. [Tests](#5-tests)
6. [Git & Branching](#6-git--branching)
7. [CI / Review](#7-ci--review)
8. [Dokumentation](#8-dokumentation)
9. [Planungsprozess](#9-planungsprozess)

---

## 1. Virtuelle Umgebung & Setup

Jedes Projekt verwendet eine lokale virtuelle Umgebung (`.venv`). Das verhindert Versionskonflikte und hält das System-Python sauber.

### Setup-Skript

Wähle für Unix/macOS `setup_env.sh` und für Windows `setup_env.ps1`.

```bash
#!/usr/bin/env bash
set -e

ENV_NAME=".venv"
python3 -m venv "$ENV_NAME"
source "$ENV_NAME/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .[dev]
pre-commit install || true
```

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .[dev]
pre-commit install
```

### Wichtige Regeln
- Verwende immer eine Projekt-spezifische `venv`.
- Installiere Abhängigkeiten nur aus `pyproject.toml` oder optional `requirements.txt`.
- Aktiviere die Umgebung, bevor du Befehle ausführst.

---

## 2. Paketverwaltung

Verwende `pyproject.toml` als zentrale Projektkonfiguration.

### Minimaler Aufbau

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "mein_projekt"
version = "0.1.0"
description = "Kurzbeschreibung"
requires-python = ">=3.10"
dependencies = [
  "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=7.4.0",
  "pytest-cov>=4.1.0",
  "black>=23.0.0",
  "ruff>=0.1.0",
  "mypy>=1.5.0",
  "pre-commit>=3.4.0",
]
```

### Regeln
- Produktionsabhängigkeiten in `dependencies`
- Entwicklungsabhängigkeiten in `project.optional-dependencies.dev`
- Keine hardcodierten Secrets im Code

---

## 3. Projektstruktur

Nutze das `src`-Layout für sauberes Packaging und klare Grenzen.

### Standardstruktur

```text
mein_projekt/
├── .github/
│   └── workflows/
├── docs/
├── src/
│   └── mein_projekt/
├── tests/
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml
├── README.md
└── setup_env.sh
```

### Prinzipien
- Ein Modul/Package erfüllt eine klare Aufgabe.
- Keine zirkulären Abhängigkeiten.
- Konfiguration über Umgebungsvariablen oder `config.py`.
- Öffentliches API nur über definierte Exporte.

---

## 4. Codequalität und Tools

Automatisiere Stil und Qualität, statt sie manuell zu diskutieren.

### Werkzeuge
- `black` oder `ruff format`
- `ruff` als Linter
- `mypy` für Typprüfung
- `pre-commit` als Hook-Manager

### Beispiel `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

### Empfohlene Befehle

```bash
ruff check src tests
ruff format src tests
mypy src
pytest
```

---

## 5. Tests

Testing ist Pflicht. Jeder Merge muss mit Tests abgesichert werden.

### Regeln
- Testdateien heißen `test_*.py`
- Testfunktionen heißen `test_*`
- Isolation: keine echten externen Services in Unit-Tests
- Nutze Fixtures für wiederverwendbare Daten
- Ziel: mindestens 80 % Coverage für `src/`

### Beispiel

```python
import pytest
from mein_projekt.core.processor import DataProcessor

@pytest.fixture
def processor():
    return DataProcessor(threshold=10)


def test_process_data_success(processor):
    data = [5, 12, 18, 3]
    assert processor.filter_above_threshold(data) == [12, 18]


def test_process_data_invalid_input(processor):
    with pytest.raises(TypeError):
        processor.filter_above_threshold("invalid_data")
```

### Testbefehle

```bash
pytest
pytest --cov=src --cov-report=term-missing --cov-report=html
```

---

## 6. Git & Branching

Arbeite in Feature-Branches und halte `main` stabil.

### Branch-Konventionen
- `feature/<kurzbeschreibung>`
- `bugfix/<kurzbeschreibung>`
- `hotfix/<kurzbeschreibung>`
- `chore/<kurzbeschreibung>`

### Commit-Format

```text
<type>(<scope>): kurze beschreibung

optional: ausführlichere details
```

### Typen
- `feat`
- `fix`
- `docs`
- `style`
- `refactor`
- `test`
- `chore`

### Regeln
- 50–72 Zeichen für die erste Zeile
- Imperativform
- Kein Punkt am Ende
- Ein Commit = eine logische Änderung

### PR-Regeln
- PR gegen `main`
- Beschreibung, Tests und Referenzen angeben
- CI muss grün sein
- Review muss abgeschlossen sein

---

## 7. CI / Review

CI prüft automatisiert Format, Typen, Tests und Code-Qualität.

### Reviewer-Checks
- `src`-Layout korrekt?
- Keine Secrets im Code?
- Saubere Fehlerbehandlung?
- Passende Tests vorhanden?
- Typen geprüft?

### Beispiel GitHub Action

```yaml
name: AI Code Reviewer
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run AI Code Review Agent
        uses: your-reviewer-agent-action@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          config-file: .github/reviewer_prompt.md
```

---

## 8. Dokumentation

Dokumentation ist Teil des Projekts.

- `README.md`: Setup, Nutzung, wichtigste Befehle
- `docs/`: Erweiterte Informationen zur Architektur, API und Konfiguration
- `CHANGELOG.md`: Wichtige Änderungen und Releases

---

## 9. Planungsprozess

Der Arbeitsablauf folgt dem Plan & Execute Prinzip:

1. Kontext & Klärung
2. Planung & Spezifikation
3. Review & Freigabe
4. Umsetzung & Tests

### Ablauf
- Klare Anforderungen sammeln
- Plan mit betroffenen Dateien und Tests erstellen
- Plan prüfen lassen
- Umsetzung nach Plan, testen und mergen

---

## 10. Zusammenfassung

Kurz:
- Nutze `.venv`
- Konfiguriere in `pyproject.toml`
- Strukturiere im `src`-Layout
- Automatisiere Linter, Formatter und Typprüfungen
- Schreibe Tests
- Nutze saubere Git-Branches und Commit-Nachrichten
- Dokumentiere und reviewe jeden PR
