# Mein Spickzettel

Eine kleine, **komplett lokale** Web-App für zwei Dinge:

1. **Dokumente ablegen und wiederfinden** – Fotos, PDFs, Textdateien (Impfpass, Führerschein, Rechnungen, WhatsApp-Exporte …). Der Text wird automatisch ausgelesen (OCR bei Fotos, Textextraktion bei PDFs) und ist per Volltextsuche durchsuchbar.
2. **Rezepte sammeln und passend auswählen** – Rezept-PDFs importieren oder manuell anlegen; mit „Was koche ich?“ bekommst du deine Rezepte gerankt nach den Zutaten, die du gerade da hast.

Alles läuft auf **deinem eigenen Rechner** – keine Cloud, keine Anmeldung. Die Daten liegen im Ordner `data/`.

## Voraussetzungen

- Python 3.10 oder neuer (python.org bzw. Paketmanager des Systems)
- Optional für Fotos: Tesseract (siehe unten)

## Start (Schritt für Schritt)

```bash
# 1. Projekt-Ordner betreten
cd spickzettel

# 2. Virtuelle Umgebung anlegen (isolierter „Arbeitsbereich“ für die Bibliotheken)
python3 -m venv venv

# 3. Benötigte Bibliotheken installieren
#    Windows: venv\Scripts\pip install -r requirements.txt
#    macOS/Linux: ./venv/bin/pip install -r requirements.txt

# 4. Server starten
#    Windows: venv\Scripts\python run.py
#    macOS/Linux: ./venv/bin/python run.py

# 5. Browser öffnen: http://127.0.0.1:8000
```

## Optional: Fotos durchsuchbar machen (OCR)

Damit Text auf Fotos (z. B. abfotografierter Impfpass) erkannt wird, brauchst du zusätzlich das Programm **Tesseract**:

- **Linux:** `sudo apt install tesseract-ocr tesseract-ocr-deu`
- **macOS:** `brew install tesseract tesseract-lang`
- **Windows:** Installer von „UB Mannheim – tesseract" herunterladen und installieren, Sprache „German" mit wählen

Danach in der aktivierten venv zusätzlich installieren:

```bash
pip install pillow pytesseract
```

Dann findet die App Tesseract automatisch. Die App zeigt oben auf der Seite an, ob OCR aktiv ist. Ohne diesen Schritt läuft die App trotzdem – nur Fotos werden dann nicht per Text durchsucht.

## Aufbau des Projekts

```
spickzettel/
├── run.py               # Startdatei: python run.py
├── requirements.txt     # Liste der Bibliotheken
├── app/
│   ├── main.py          # Die Web-App: alle Seiten und Aktionen
│   ├── db.py            # Datenbank (SQLite) + Volltextsuche (FTS5)
│   ├── ingest.py        # Text aus PDF / Textdatei / Foto (OCR) auslesen
│   └── recipes.py       # Rezept-PDFs zerlegen + Zutaten-Abgleich („Was koche ich?“)
├── templates/           # Die HTML-Seiten (index.html, document.html)
└── data/                # ALLE deine Daten liegen hier (app.db + uploads/)
```

## Datenschutz

- Alles bleibt lokal in `data/`. Nichts wird ins Internet geschickt.
- Tipp: Den Ordner `spickzettel/data` kannst du z. B. mit **Cryptomator** verschlüsseln.
- Tipp: Fotos vom Handy automatisch auf den PC bringen mit **Syncthing** (lokal, verschlüsselt) in den Ordner `data/uploads`.

## Nächste Ausbaustufen (Ideen)

- Semantische Suche („Wann war die Tetanus-Impfung?“ findet auch „Auffrischung 03/2023“) via lokalen Embeddings
- Lokales LLM (Ollama) für Fragen wie „Was kann ich aus meinen Dokumenten zum Thema X wissen?“
- Export/Backup der Datenbank
- Mobile App bzw. Zugriff aus dem Heimnetz
