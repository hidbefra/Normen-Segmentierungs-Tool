# 📋 Normen-Segmentierungs-Tool — Projektplan

**Status:** In-Progress | **Letzte Aktualisierung:** 2026-07-28

---

## 🎯 Überblick

Modulare webbasierte Anwendung zur Segmentierung, Korrektur und Export von Normen-PDFs.  
**Tech-Stack:** FastAPI + PDF.js (Frontend), PyMuPDF + Pandas, SQLite

---

## 📅 Phase 1: Backend-Foundation (Woche 1–2)

### 1.1 OCR & PDF-Engine
**Beschreibung:** PyMuPDF-basiertes Laden von PDFs, Text-Layer-Erkennung, automatische OCR bei fehlender TextSchicht.

- [x] Modul `src/normen_tool/pdf_handler.py` erstellen
  - [x] Funktion `load_pdf(path)` — PDF mit Pymupdf laden
  - [x] Funktion `has_text_layer(doc)` — Prüfung auf unsichtbare OCR
  - [x] Funktion `extract_ocr_layer(pdf_path)` — OCR erzeugen via pytesseract/pdfplumber
  - [x] Funktion `get_bbox_and_text(page)` — Bounding Boxes + Text pro Block
- [x] Unit-Tests `tests/test_pdf_handler.py`
  - [x] Test native PDFs (mit Textlayer)
  - [x] Test gescannte PDFs (ohne Textlayer)
  - [x] Test OCR-Generierung
- [x] Abhängigkeiten updaten (optional: pytesseract, pdfplumber)

**Status:** ✅ Abgeschlossen  
**Notizen:** PDFHandler-Klasse mit vollständiger Context-Manager-Unterstützung, 20/20 Unit-Tests bestanden, Code bestanden ruff/mypy.

---

### 1.2 Regelbasierter Parser (Segmentation)
**Beschreibung:** Kapitel- und Absatz-Segmentierung basierend auf Heuristiken (Überschriften, Satzzeichen, Einzüge).

- [x] Modul `src/normen_tool/segmentation.py` erstellen
  - [x] Funktion `parse_blocks(text, bbox_list)` — Text in Absätze teilen
  - [x] Heuristik für Kapitelüberschriften (z.B. "4.2.1" oder "Kapitel 4")
  - [x] Cross-Page-Merge: Satzfluss über Seiten hinweg erkennen
  - [x] Sentence-Boundary-Trimming (nur komplette Sätze)
- [x] Tests `tests/test_segmentation.py`
  - [x] Test mit Sample-Norm-PDF
  - [x] Test Cross-Page-Merge
  - [x] Test Satzgrenzen-Filter

**Status:** ✅ Abgeschlossen  
**Notizen:** RuleBasedSegmenter mit Block/Segment-Klassen, 26/26 Unit-Tests bestanden, Code bestanden ruff/mypy, Cross-Page-Merge mit Satzfluss-Erkennung.

---

### 1.3 DB-Schema & Modelle
**Beschreibung:** SQLite-Datenbank-Schema für Blöcke, UUIDs, Bounding-Boxes, Versionierung.

- [x] Modul `src/normen_tool/db/models.py` — SQLAlchemy/Pydantic Models
  - [x] Block-Model: `id` (UUIDv4), `doc_name`, `section`, `content`, `pages`, `bboxes`, `ai_generated`, `modified_at`
  - [x] Document-Model: `name`, `path`, `created_at`, `page_count`
- [x] Migrations `src/normen_tool/db/migrations.py`
  - [x] Initiale `blocks` + `documents`-Tables
- [x] DB-Utilities `src/normen_tool/db/client.py`
  - [x] Funktion `init_db(project_dir)` — DB-Datei erstellen/laden
  - [x] Funktion `insert_block(...)` — Block speichern
  - [x] Funktion `list_blocks(doc_name)` — Blöcke pro PDF
  - [x] Funktion `update_block(id, content)` — Änderungen speichern
  - [x] Bulk insert, cascading deletes, statistics
- [x] Tests `tests/test_db.py`
  - [x] 21/21 Unit-Tests bestanden

**Status:** ✅ Abgeschlossen  
**Notizen:** DBClient mit vollständigem CRUD + Batch-Operationen, detached instance Fehler behoben, alle Tests grün. Windows teardown-Fehler gelöst. Code bestanden ruff/mypy.

---

## 📅 Phase 2: REST-API (Woche 2–3)

### 2.1 Core Endpoints
**Beschreibung:** FastAPI-Endpoints für Projekt-, PDF- und Block-Verwaltung.

- [ ] **Projekt-Management**
  - [ ] `POST /project/open` — Ordner öffnen, DB laden/erstellen
  - [ ] `GET /project/status` — DB-Datei + PDF-Liste
  
- [ ] **PDF-Verwaltung**
  - [ ] `GET /project/pdfs` — Liste aller PDFs im Ordner
  - [ ] `GET /pdf/{doc_id}/pages` — Seiten + Metadaten
  - [ ] `GET /pdf/{doc_id}/rendered/{page_num}` — Seiten-Rendering (PNG/SVG)
  
- [ ] **Block-Verwaltung (CRUD)**
  - [ ] `GET /blocks/{doc_id}` — Alle Blöcke eines PDFs
  - [ ] `GET /block/{id}` — Ein Block + Details
  - [ ] `POST /block` — Neuen Block erstellen (manuell)
  - [ ] `PATCH /block/{id}` — Block bearbeiten (Content, Section, etc.)
  - [ ] `DELETE /block/{id}` — Block löschen
  
- [ ] **Re-Segmentation**
  - [ ] `POST /pdf/{doc_id}/parse` — Regelparser auf PDF anwenden

- [ ] Tests `tests/test_api.py`
  - [ ] Test alle Endpoints mit Stubs/Mocks

**Status:** ⬜ Nicht gestartet  
**Notizen:** —

---

### 2.2 CSV-Export
**Beschreibung:** Export in `norm_data_powerquery.csv` für Excel Power Query.

- [ ] Modul `src/normen_tool/export.py`
  - [ ] Funktion `export_to_csv(project_dir, blocks)` — CSV schreiben
  - [ ] Spalten: `ID`, `doc_name`, `section`, `content`, `DeepLink_Editor`
  - [ ] DeepLink generieren: `http://localhost:8000/ui?doc={doc_id}&block={block_id}`
  
- [ ] Endpoint `GET /export/csv` — CSV downaden oder im Ordner speichern
- [ ] Tests `tests/test_export.py`

**Status:** ⬜ Nicht gestartet  
**Notizen:** —

---

## 📅 Phase 3: Web-UI (Woche 3–4)

### 3.1 Frontend-Gerüst
**Beschreibung:** HTML5 + PDF.js Viewer, Split-Screen Layout, Block-Editor.

- [ ] Ordner `src/normen_tool/static/` erstellen
  - [ ] `index.html` — Haupt-UI
  - [ ] `styles.css` — Split-Screen Layout (50/50)
  - [ ] `app.js` — Projekt-Auswahl, PDF-Auswahl

- [ ] **Komponenten**
  - [ ] Ordner-Picker (Button → `<input type="file" webkitdirectory>`)
  - [ ] PDF-Dropdown
  - [ ] PDF-Viewer (Links) — PDF.js Canvas
  - [ ] Block-Editor (Rechts) — Textarea + Metadaten
  
- [ ] Endpoint `GET /` — `index.html` servieren

**Status:** ⬜ Nicht gestartet  
**Notizen:** —

---

### 3.2 Deep-Linking & Highlighting
**Beschreibung:** Deep-Links + visuelle Hervorhebung von Blöcken im PDF.

- [ ] Deep-Link-Parser in JS: `?doc={doc_id}&block={block_id}`
  - [ ] PDF laden + auf Seite springen
  - [ ] Block-Hervorhebung (Bounding Box)
  
- [ ] Bounding-Box-Highlighting
  - [ ] Funktion `highlight_bbox(page, bbox, color)` — PDF.js Canvas overlay
  - [ ] Farben: Fokus (Rot), Nachbar (Gelb)

- [ ] Tests: Manuelle Überprüfung

**Status:** ⬜ Nicht gestartet  
**Notizen:** —

---

## 📅 Phase 4: KI/LLM-Integration (Optional, Später)

### 4.1 LLM-Config & API-Bridging
**Beschreibung:** Support für OpenAI, Claude, Ollama mit UI-Konfiguration.

- [ ] Modul `src/normen_tool/llm/config.py`
  - [ ] Settings: Provider (OpenAI/Claude/Ollama), API-Key, Model-Name
  
- [ ] Modul `src/normen_tool/llm/client.py`
  - [ ] Funktionen für REST-Anfragen zu LLM-APIs
  - [ ] Prompt-Template für Segmentierung
  
- [ ] Endpoints
  - [ ] `POST /config/llm` — LLM-Config speichern
  - [ ] `POST /pdf/{doc_id}/segmentate-ai` — KI-Segmentierung starten (async)
  
- [ ] Frontend: Settings-Dialog für API-Key etc.

**Status:** ⬜ Nicht gestartet (Priorität: niedrig)  
**Notizen:** Erst implementieren, wenn regelbasierter Parser stabil läuft.

---

## 🐛 Known Issues & Offene Punkte

| Thema | Beschreibung | Priorität | Status |
|-------|-----------|-----------|--------|
| Datenbank-Locking | SQLite auf Netzwerk: Keine Mehrbenutzer-Unterstützung → später PostgreSQL | Mittel | ⬜ Warten |
| LLM-Datenschutz | Optionale lokale LLMs (Ollama) bevorzugen | Niedrig | ⬜ Warten |
| GUI-Folder-Picker | Windows/Linux: `webkitdirectory` Unterstützung prüfen | Mittel | ⬜ Zu testen |
| Performance | Große PDFs (>500 Seiten): Lazy-Loading, Pagination | Niedrig | ⬜ Nach Phase 3 |
| Backup-Strategie | CSV-Exporte als Versionshistorie | Mittel | ⬜ Dokumentieren |

---

## ✅ Abgeschlossene Aufgaben (Phase 0 + 1.1 + 1.2)

- [x] GitHub-Repo erstellt & initialisiert
- [x] Python-Projekt-Struktur mit `pyproject.toml`, venv
- [x] CI/CD-Workflow (GitHub Actions: lint, type, test)
- [x] `SECURITY.md` Richtlinie
- [x] SRS finalisiert mit OCR-, CSV-, UI-Details
- [x] Initial `src/normen_tool/main.py` + `/health`-Endpoint
- [x] Tests-Gerüst mit pytest
- [x] **Phase 1.1: PDFHandler vollständig implementiert** (PDFLoader, Text-Layer-Erkennung, BBox-Extraktion, 20 Unit-Tests)
- [x] **Phase 1.2: Rule-Based Segmenter implementiert** (Chapter/Section-Erkennung, Cross-Page-Merge, Sentence-Boundary-Trimming, 26 Unit-Tests)

---

## 📊 Fortschritts-Metriken

| Metrik | Wert |
|--------|------|
| **Phasen gesamt** | 4 |
| **Phasen abgeschlossen** | 1 |
| **Tasks gesamt** | ~45 |
| **Tasks abgeschlossen** | ~15 |
| **Completion %** | ~33% |

---

## 🚀 Quick-Start für nächste Schritte

1. **PDF-Handler testen:**
   ```bash
   cd e:\Projekte\Python\Normen-Segmentierungs-Tool
   .\.venv\Scripts\activate
   pytest tests/test_pdf_handler.py -v
   ```

2. **Segmenter entwickeln + testen:**
   ```bash
   pytest tests/test_segmentation.py -v
   ```

3. **DB lokal initialisieren + auf Korrektheit prüfen:**
   ```bash
   python -c "from src.normen_tool.db.client import init_db; init_db('.')"
   ```

---

## 📝 Notizen für Contributors

- Alle neuen Funktionen müssen Tests haben (pytest).
- Code muss via `ruff check` und `mypy` gereinigt sein.
- Vor Push: `git add .`, dann `git commit`, dann `git push origin main`.
- PRs werden optional, once Branch Protection aktiviert ist.

---

**Stand:** 28. Juli 2026 | **Nächste Überprüfung:** Nach Phase 1.3 (DB-Schema)
