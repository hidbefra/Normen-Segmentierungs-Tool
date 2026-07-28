# Software-Anforderungsspezifikation (SRS)
## Interaktives Tool zur Segmentierung, Korrektur und Export von Normen-PDFs

---

## 1. Übersicht & Zielsetzung

Ziel des Projekts ist die Entwicklung einer modularen, webbasierten Anwendung mit **Python-Backend**, um PDF-Normen und Gesetzestexte kapitel- und absatzweise zu analysieren, visuell zu verifizieren, interaktiv zu korrigieren und in eine strukturierte Tabellenform (CSV/Excel via Power Query) zu exportieren.

Das System verarbeitet sowohl **native digitale PDFs** als auch **gescannte PDFs**, inklusive Dokumenten mit oder ohne vorhandene OCR-Textschicht. Falls keine unsichtbare OCR-Schicht vorhanden ist, erzeugt das System automatisch eine OCR-Layer. Es arbeitet projektbasiert auf Ordnerebene (**Multi-PDF-Batchverarbeitung**) und nutzt einen **Human-in-the-Loop-Ansatz**: Ein regelbasierter Parser übernimmt als Standard die Erstsegmentierung, ergänzt durch ein **optional nutzbares KI/LLM-Modul**, während der Anwender über eine Split-Screen-Oberfläche visuelle Feinkorrekturen vornimmt.

---

## 2. Systemarchitektur & Ordner-/Projekt-Workflow

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        PROJEKT-ORDNER (Input/Output)                   │
│  - Eingabe: Beliebig viele Norm-PDFs (native & OCR-gescannt)           │
│  - Persistence: SQLite DB-Sicherungsdatei (`project_database.db`)     │
│  - Schnittstelle: Automatische CSV-Datei (`norm_data_powerquery.csv`)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Laden / Speichern
┌───────────────────────────────────▼────────────────────────────────────┐
│                        WEB-OBERFLÄCHE (Frontend)                        │
│  - Ordner-Auswahl / Projekt-Öffnung per GUI                            │
│  - LLM-Modell-Konfiguration (API-Key, Provider/Modell-Auswahl)         │
│  - Button: "KI-Analyse manuell starten"                                │
│  - Dokumenten-Umschalter (PDF-Auswahl)                                 │
│  - Split-Screen: PDF-Viewer (links) & Absatz-Editor (rechts)          │
│  - Deep-Link Anspringen von Absätzen & Nachbar-Kontext               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST / Query Params
┌───────────────────────────────────▼────────────────────────────────────┐
│                        PYTHON-BACKEND (Server)                         │
│  1. Ordner- & DB-Manager      --> DB-Erkennung, Laden & Sicherung       │
│  2. OCR & PDF Engine          --> Liest native & unsichtbare Textlayer  │
│  3. KI / LLM Module (Optional)--> Multimodale & Text-Strukturanalyse  │
│  4. Dynamic Renderer          --> Farbcodierung & Nachbar-Highlights    │
│  5. Cross-Page Merge Engine   --> Fügt seitentrennende Sätze zusammen  │
│  6. Sentence Boundary Engine  --> Satz-Trimming bei Bounding-Box-Puffer │
│  7. Data Store (SQLite / CSV) --> Feste UUIDs über ALLE PDFs hinweg    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ CSV / REST API
┌───────────────────────────────────▼────────────────────────────────────┐
│                  TABELLENVERARBEITUNG (Power Query)                     │
│  - Import der zentralen CSV in Microsoft Excel via Power Query         │
│  - Rückverlinkung per Deep-Link direkt in die Web-UI                   │
└────────────────────────────────────────────────────────────────────────┘
```

* **Backend / UI Framework:** Python, bevorzugt FastAPI + PDF.js
* **PDF- & OCR-Verarbeitung:** PyMuPDF (`fitz`), optional `pdfplumber` / `pytesseract` (für unsichtbare Textlayer)
* **KI / LLM-Anbindung:** LangChain / LlamaIndex / Direct REST API (Unterstützung für OpenAI, Claude, Ollama/Local LLMs)
* **Datenbank / Persistence:** SQLite (lokale `.db`-Datei im Projektordner) + `pandas`
* **Tabellen-Integration:** Microsoft Excel mit Power Query

### UI-Stack: Streamlit vs. FastAPI + PDF.js
* **Streamlit**
  * Pro: Schnelle Prototypen, einfache UI-Erstellung, weniger Frontend-Aufwand.
  * Contra: Eingeschränkte Kontrolle über komplexe PDF-Interaktionen und Deep-Linking, begrenzte Komponentenflexibilität.
* **FastAPI + PDF.js**
  * Pro: Bessere Kontrolle über UI, leistungsfähiger PDF-Viewer, sauberere Trennung zwischen Backend und Frontend.
  * Contra: Höherer Entwicklungsaufwand, zusätzliche Web-Technologien erforderlich.

---

## 3. Funktionale Anforderungen (Phasen 1–7)

### Phase 1: Projekt-Ordner-Management & Input-Spezifikation (Native & OCR)

* **Ordner-Auswahl über GUI:**
  * Der Anwender wählt über die Benutzeroberfläche einen lokalen Projektordner aus.
* **Unterstützung für OCR & Native PDFs:**
  * Das System verarbeitet native Dokumente sowie gescannte PDFs mit oder ohne vorhandene OCR-Textschicht.
  * Fehlt die OCR-Schicht, erzeugt das Backend automatisch eine OCR-Textschicht und liest die räumlichen Koordinaten (`bbox`) für die Visualisierung.
  * Das Backend synchronisiert die Text- und Bild-Ebenen im Viewer, um die Bearbeitung präzise zu ermöglichen.
* **Multi-PDF Batch-Verarbeitung:**
  * Durchsuchen des Ordners nach allen enthaltenen PDF-Dateien (`*.pdf`).
* **Erkennung & Laden existierender Projekt-Datenbanken:**
  * Vorhandene Datenbanksicherungen (`project_database.db`) werden automatisch erkannt und geladen (inkl. aller früheren KI-Segmentierungen und Korrekturen).
* **Automatische DB-Sicherung im Projektordner:**
  * Jede Anpassung speichert direkt in die lokale SQLite-Datei im Projektordner zurück.

---

### Phase 2: KI / LLM Anbindung & Manuelle Triggerung über die GUI

* **LLM-Konfiguration in der UI:**
  * In den Einstellungen der Web-Oberfläche kann der Anwender flexibel ein LLM verknüpfen:
    * **Provider-Auswahl:** OpenAI (GPT-4o), Anthropic (Claude 3.5), Local/Self-Hosted (via Ollama / LM Studio).
    * **API-Key & Endpoint:** Eingabefelder zur sicheren Verbindung.
* **Segmentation ohne KI:**
  * Das System muss zuverlässig ohne KI segmentieren können und verwendet einen regelbasierten Parser als Standardmechanismus.
* **Manuelle KI-Triggerung:**
  * Die KI-Segmentierung läuft **nicht zwingend automatisch**, sondern kann jederzeit über einen Button **" 🤖 KI-Segmentierung starten"** manuell für das aktuelle PDF oder den gesamten Ordner getriggert werden.
* **Funktionsweise der KI-Segmentierung:**
  * **Multimodal / Vision:** Das LLM analysiert die gescannte Seite visuell und erkennt Absätze, Überschriften und Randbereiche unabhängig vom OCR-Layout.
  * **NLP-Strukturanalyse:** Das LLM korrigiert Erkennungsfehler der OCR-Ebene und teilt den Fließtext in zusammenhängende Kapitel und logische Absätze auf.

### Phase 2.1: Server-Steuerung über kleines GUI

* **Server Start / Stop über GUI:**
  * Der Python-Server kann direkt über ein kleines Desktop-GUI gestartet und gestoppt werden.
  * Das GUI soll möglichst einfach gehalten sein, zum Beispiel mit Qt oder einer ähnlichen kleinen nativen Oberfläche.
* **Statusanzeige im GUI:**
  * Das GUI zeigt an, ob der Server läuft, gestoppt wurde oder beim Start ein Fehler aufgetreten ist.
* **Bedienung:**
  * Start und Stop sollen ohne Terminal-Befehle möglich sein.
  * Das GUI kann als separater Launcher oder als kleines Hilfsfenster neben der Web-Oberfläche bereitgestellt werden.

### Phase 2.2: Logging & Diagnose

* **Zentrales Logging:**
  * Das gesamte Projekt schreibt Logs in eine gemeinsame Log-Datei.
  * Alle relevanten Komponenten sollen über denselben Logging-Workflow protokollieren.
* **Log-Datei:**
  * Die Log-Datei wird im Projektordner oder in einem klar definierten Log-Verzeichnis abgelegt.
  * Log-Rotation oder eine vergleichbare Begrenzung sollte vorgesehen werden, damit die Datei nicht unbegrenzt wächst.
* **Log-Level / Granularität:**
  * Die Log-Granularität soll über ein konfigurierbares Log-Level steuerbar sein.
  * Geeignete Standard-Log-Levels sind: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
  * Empfohlene Voreinstellung ist `INFO` für den normalen Betrieb und `DEBUG` für die Fehlersuche.
* **Anforderungen an Inhalte:**
  * Start/Stop-Aktionen des Servers, Fehler beim Laden von PDFs, DB-Zugriffe, Exportvorgänge und relevante GUI-Aktionen sollen protokolliert werden.
  * Sensible Inhalte wie API-Keys oder vertrauliche Nutzdaten dürfen nicht im Klartext geloggt werden.

---

### Phase 3: Seitenübergreifende Abschnitte (Cross-Page Handling)

* **Verbindung über Seitenränder hinweg:**
  * Geht ein Absatz am unteren Rand der Seite $N$ weiter auf die Seite $N+1$, muss das System dies als **einzigen zusammenhängenden Block** erfassen.
* **Multi-Page Bounding-Boxen:**
  * Das Datenmodell unterstützt mehrteilige Bounding-Boxen pro Absatz:
    * `page_start`, `bbox_start` (Seite $N$)
    * `page_end`, `bbox_end` (Seite $N+1$)
* **Semantische Zusammenführung (Satzfluss):**
  * Das Backend (oder das LLM) prüft am Seitenende, ob ein Satzzeichen den Absatz abschließt. Fehlt ein Satzzeichen, wird der erste Satz der Folgeseite automatisch an den vorherigen Block angehängt.
* **Visuelle Darstellung im Viewer:**
  * Beim Anspringen eines seitenübergreifenden Absatzes hebt der PDF-Viewer die jeweiligen Bereiche auf **beiden betroffenen Seiten** hervor.

---

### Phase 4: Datenstruktur & Übergreifende UUID-Architektur

* **Globale Eindeutigkeit:** Jeder Absatz erhält eine universell eindeutige ID (`UUIDv4`).
* **Erweitertes Datenbank-Schema (`blocks` in SQLite):**
  * `id`: `String` (UUIDv4)
  * `doc_name`: `String` (PDF-Dateiname)
  * `section`: `String` (Kapitelnummer, z. B. "4.2.1")
  * `content`: `Text` (Bereinigter Text, inkl. seitenübergreifendem Merge)
  * `pages`: `List[Integer]` (Liste der beteiligten Seiten, z. B. `[2, 3]`)
  * `bboxes`: `JSON` (Zuordnung von Seiten und Bounding-Box-Koordinaten)
  * `ai_generated`: `Boolean` (Flag, ob durch KI oder Regelparser erzeugt)
  * `DeepLink_Editor`: `String` (URL-Aufruf für die UI)

---

### Phase 5: Web-Oberfläche & Visueller Editor (Split-Screen)

* **Dokumenten- & KI-Umschalter:** Schnellzugriff auf Dokumente und KI-Steuerung.
* **Split-Screen Layout:**
  * **Links:** PDF-Viewer mit visueller Hervorhebung der OCR-/Text-Ebenen.
  * **Rechts:** Editor mit Möglichkeit zur manuelle Anpassung der KI-Ergebnisse.
* **Dynamisches Re-Coloring & Nachbar-Highlights:**
  * Fokus-Absatz (Rot), Nachbar-Absätze (Gelb/Orange). Automatische Farbanpassung aller Folgestufen bei Änderungen.

---

### Phase 6: Überlappende Bounding Boxen & Satzgrenzen-Regel

* **Toleranzbereiche:** Erlaubte Pufferzonen bei manueller Grenzanpassung.
* **Satzgrenzen-Filter (Sentence Boundary Trimming):**
  * Nur Sätze, deren Satzzeichen (`.`, `!`, `?`, `:`) innerhalb der Box liegen, fließen in den finale Text ein.

---

### Phase 7: Deep-Linking & Power Query / Excel-Integration

* **Dokument- & Seitenübergreifendes Deep-Linking:**
  * Der Deep-Link öffnet die Web-UI, lädt das richtige PDF und springt direkt auf die Startseite des (ggf. seitenübergreifenden) Absatzes.
* **Zentrale CSV-Ausgabe (`norm_data_powerquery.csv`):**
  * Automatische Synchronisation für den One-Click-Import in Microsoft Excel via Power Query.
  * Die CSV enthält mindestens die Spalten: `ID`, `doc_name`, `section`, `content`, `DeepLink_Editor`.

---

## 4. Speicher- & Ordnerstruktur im Ziel-Ordner

```text
📁 /Mein_Normen_Projekt/
 ├── 📄 DIN_EN_ISO_9001.pdf       <-- Native oder OCR-gescannte PDF 1
 ├── 📄 DIN_EN_ISO_14001.pdf      <-- Native oder OCR-gescannte PDF 2
 ├── 💾 project_database.db       <-- SQLite (enthält KI-Strukturen & Manuelle Korrekturen)
 └── 📊 norm_data_powerquery.csv  <-- Auto-Export für Excel Power Query
```

---

## 5. Nicht-funktionale Anforderungen

1. **Robustheit bei gescannten PDFs:** Korrekte Zuordnung der unsichtbaren Textschicht zur visuellen Darstellungsmatrix des PDF-Scans.
2. **Flexibilität der KI-Anbindung:** Lauffähigkeit sowohl mit Cloud-LLMs als auch mit lokalen, datenschutzkonformen Modellen (Ollama).
3. **Persistenz:** Vollständige Erhaltung aller manuellen und KI-generierten Korrekturen in der lokalen `project_database.db`.
4. **Multiuser-Szenario:** Das System soll lokal arbeiten, aber Optionen für eine spätere Mehrbenutzer-Unterstützung über Netzlaufwerk oder SharePoint ermöglichen.
5. **Aktuelle Datenbasis:** Es reicht eine aktuelle Datenbankdatei. Historisierung und Versionierung erfolgen über CSV-Exporte und eindeutige IDs.
6. **Bedienbarkeit des Servers:** Start und Stopp des Servers sollen über ein kleines GUI ohne Terminal-Eingriff möglich sein.
7. **Nachvollziehbarkeit:** Alle wesentlichen Vorgänge sollen zentral in einer Log-Datei protokolliert werden, mit konfigurierbarer Granularität über standardisierte Log-Levels.

### Mehrbenutzer-/Netzwerk-Optionen
* **SQLite auf Netzlaufwerk / SharePoint:** Nicht empfehlenswert. SQLite ist nicht für gleichzeitige Zugriffe über Netzwerkdateien ausgelegt und kann zu Datenkorruption oder Sperrproblemen führen.
* **Bessere Alternative:** Verwende eine zentrale Datenbank wie PostgreSQL oder MySQL auf einem Server, auf die alle Installationen zugreifen. Das ist stabiler und unterstützt Mehrbenutzerzugriffe.
* **Hybrid-Ansatz:** Lokale SQLite-Datei als Primärspeicher, zusätzliche Synchronisation über CSV/Datei-Export oder einen einfachen REST-API-Service, der Commit- und Read-Requests koordiniert.
* **SharePoint/Netzlaufwerk als Archiv:** Nutze SharePoint eher zur Speicherung von CSV-Exports und Projektarchiven, nicht als aktiven SQLite-Speicherort.
