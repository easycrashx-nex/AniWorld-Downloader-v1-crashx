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
- FFmpeg
- Browser

Beispiel Debian / Ubuntu:

```bash
sudo apt update
sudo apt install -y python3 python3-pip ffmpeg
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
git clone https://github.com/easycrashx-nex/AniworldDownloader-Update.git aniworld
cd aniworld
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

Hinweise:

- `git clone ... aniworld` erstellt den Ordner `aniworld` automatisch fuer dich.
- `pip install -e .` funktioniert nur im echten Repository-Ordner, also dort, wo auch `pyproject.toml` liegt.
- Wenn du statt `git clone` ein ZIP benutzt, musst du zuerst das ZIP entpacken und dann dieselben Befehle im entpackten Projektordner ausfuehren.
- Eine venv ist optional. Nutze sie nur, wenn du bewusst isolierte Python-Pakete willst.

## 5. Lokales Setup auf Linux

```bash
git clone https://github.com/easycrashx-nex/AniworldDownloader-Update.git aniworld && cd aniworld && python3 -m pip install --upgrade pip && python3 -m pip install -e . && python3 -m aniworld -w
```

## 6. Lokales Setup auf macOS

```bash
git clone https://github.com/easycrashx-nex/AniworldDownloader-Update.git aniworld && cd aniworld && python3 -m pip install --upgrade pip && python3 -m pip install -e . && python3 -m aniworld -w
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
