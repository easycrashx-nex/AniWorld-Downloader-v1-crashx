# First Setup

Diese Anleitung beschreibt eine frische Einrichtung des angepassten AniWorld Downloader Builds.

## 1. Installationsart waehlen

### Lokale Source-Installation

Nutze sie, wenn du:

- lokal entwickeln willst
- den neuesten Stand aus diesem Repository nutzen willst
- den Downloader direkt auf deinem PC laufen laesst

### Docker / Docker Compose

Nutze es, wenn du:

- einen Server oder Dauerbetrieb willst
- eine saubere Trennung vom Host willst
- persistente Daten ohne manuelle Python-Pflege bevorzugst

## 2. Voraussetzungen

### Windows

- Python 3.9 bis 3.13 empfohlen
- FFmpeg im `PATH`
- Browser wie Chrome, Edge oder Firefox

### Linux

- Python 3.9 bis 3.13
- `python3-venv`
- FFmpeg
- Browser

Beispiel Debian / Ubuntu:

```bash
sudo apt update
sudo apt install -y python3 python3-venv ffmpeg
```

### macOS

- Python 3.9 bis 3.13
- FFmpeg
- Browser

Beispiel Homebrew:

```bash
brew install python ffmpeg
```

## 3. Wichtige Ordner

AniWorld Downloader verwendet standardmaessig:

- Windows: `%USERPROFILE%\\.aniworld`
- Linux: `~/.aniworld`
- macOS: `~/.aniworld`

Dort liegen typischerweise:

- `.env`
- `aniworld.db`
- Account-Daten
- Favorites
- Search History
- Stats-Archiv und Stats-Snapshots
- Provider Score History
- UI-Preferences

## 4. Lokales Setup auf Windows

```powershell
cd <project-folder>
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -e .
py -m aniworld -w
```

Mit Web-Auth:

```powershell
py -m aniworld -w -wA
```

Im LAN freigeben:

```powershell
py -m aniworld -w -wA --web-expose
```

## 5. Lokales Setup auf Linux

```bash
cd <project-folder>
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m aniworld -w
```

## 6. Lokales Setup auf macOS

```bash
cd <project-folder>
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m aniworld -w
```

## 7. Erststart

### Ohne `-wA`

- keine Login-Wand
- Web-UI oeffnet direkt

### Mit `-wA`

- Setup/Login erscheint
- erster User wird Admin
- weitere User koennen spaeter in `Settings > User Management` angelegt werden

## 8. Nach dem ersten Start pruefen

1. Web-UI oeffnet sich
2. Suche liefert Ergebnisse
3. Serien-Modal oeffnet sich
4. Settings laden
5. Diagnostics laden
6. Queue und Timeline sind erreichbar

Wenn das klappt, ist die Installation gesund.

## 9. Typische Probleme

### Port belegt

```bash
python -m aniworld -w --web-port 8090
```

Windows:

```powershell
py -m aniworld -w --web-port 8090
```

### Browser zeigt alten Stand

- Windows / Linux: `Ctrl + F5`
- macOS: `Cmd + Shift + R`

### FFmpeg fehlt

FFmpeg installieren und sicherstellen, dass es im Shell-`PATH` liegt.
