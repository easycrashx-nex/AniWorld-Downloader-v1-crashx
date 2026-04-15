# First Setup

Diese Anleitung beschreibt eine frische Einrichtung des angepassten AniWorld Downloader Builds.

## 1. Installationsart wählen

### Lokale Source-Installation

Nutze sie, wenn du:

- lokal entwickeln willst
- den neuesten Stand aus diesem Repository nutzen willst
- den Downloader direkt auf deinem PC laufen lässt

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

Optional:

- eine venv, falls macOS globale `pip install`-Befehle blockiert

## 3. Wichtige Ordner

AniWorld Downloader verwendet standardmäßig:

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

## 4. TL;DR Schnellstart

Wenn Python und FFmpeg schon eingerichtet sind, sind das die kürzesten empfohlenen Befehle.

### Windows

```powershell
py -m pip uninstall -y aniworld
py -m pip install --upgrade "git+https://github.com/easycrashx-nex/AniworldDownloader-Update.git#egg=aniworld"
aniworld -w -wA
```

### Linux

```bash
python3 -m pip uninstall -y aniworld
python3 -m pip install --upgrade "git+https://github.com/easycrashx-nex/AniworldDownloader-Update.git#egg=aniworld"
aniworld -w -wA
```

### macOS

```bash
python3 -m pip uninstall -y aniworld
python3 -m pip install --upgrade "git+https://github.com/easycrashx-nex/AniworldDownloader-Update.git#egg=aniworld"
aniworld -w -wA
```

Wenn macOS die globale Installation blockiert, nutze stattdessen:

```bash
mkdir -p aniworld && cd aniworld
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade "git+https://github.com/easycrashx-nex/AniworldDownloader-Update.git#egg=aniworld"
aniworld -w -wA
```

Hinweise:

- Damit wird ein altes installiertes `aniworld`-Paket durch diesen Custom-GitHub-Build ersetzt.
- Dein vorhandener `.aniworld`-Ordner wird dabei nicht gelöscht.
- Wenn `aniworld` danach noch auf den alten Stand zeigt, öffne ein neues Terminal.

## 5. Lokales Setup auf Windows

```powershell
git clone https://github.com/easycrashx-nex/AniworldDownloader-Update.git aniworld
cd aniworld
py -m pip install --upgrade pip
py -m pip install -e .
powershell -ExecutionPolicy Bypass -File .\install-launcher.ps1
.\aniworld.cmd -w
```

Mit Web-Auth:

```powershell
.\aniworld.cmd -w -wA
```

Im LAN freigeben:

```powershell
.\aniworld.cmd -w -wA --web-expose
```

Hinweise:

- `git clone ... aniworld` erstellt den Ordner `aniworld` automatisch für dich.
- `pip install -e .` funktioniert nur im echten Repository-Ordner, also dort, wo auch `pyproject.toml` liegt.
- `aniworld.cmd` liegt direkt im Repository und startet bewusst euren lokalen Custom-Build aus `src`, damit nicht versehentlich ein alter global installierter `aniworld`-Befehl startet.
- `install-launcher.ps1` installiert einen userweiten `aniworld`-Befehl nach `%USERPROFILE%\.local\bin` und ergänzt diesen Ordner im User-`PATH`.
- Wenn du statt `git clone` ein ZIP benutzt, musst du zuerst das ZIP entpacken und dann dieselben Befehle im entpackten Projektordner ausführen.
- Eine venv ist optional. Nutze sie nur, wenn du bewusst isolierte Python-Pakete willst.

Nach der einmaligen Launcher-Installation kannst du in neuen Terminals einfach nutzen:

```powershell
aniworld -w -wA
```

## 6. Lokales Setup auf Linux

```bash
git clone https://github.com/easycrashx-nex/AniworldDownloader-Update.git aniworld && cd aniworld && python3 -m pip install --upgrade pip && python3 -m pip install -e . && chmod +x ./aniworld ./install-launcher.sh && ./install-launcher.sh && ./aniworld -w
```

Nach der einmaligen Launcher-Installation kannst du in neuen Terminals einfach nutzen:

```bash
aniworld -w -wA
```

## 7. Lokales Setup auf macOS

```bash
git clone https://github.com/easycrashx-nex/AniworldDownloader-Update.git aniworld && cd aniworld && python3 -m pip install --upgrade pip && python3 -m pip install -e . && chmod +x ./aniworld ./install-launcher.sh && ./install-launcher.sh && ./aniworld -w
```

Wenn macOS Installationen in die System-/Homebrew-Python-Umgebung blockiert, nutze die venv-Variante:

```bash
git clone https://github.com/easycrashx-nex/AniworldDownloader-Update.git aniworld
cd aniworld
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
chmod +x ./aniworld ./install-launcher.sh
./install-launcher.sh
./aniworld -w
```

Nach der einmaligen Launcher-Installation kannst du in neuen Terminals einfach nutzen:

```bash
aniworld -w -wA
```

Hinweise:

- Auf manchen macOS-Setups ist globales `pip install` gesperrt, z. B. durch das System oder eine extern verwaltete Python-Umgebung.
- Dann nimm den venv-Block oben statt die globale Installation zu erzwingen.
- Sobald die venv aktiv ist, funktioniert `aniworld` in dieser Shell normal.

## 8. Erststart

### Ohne `-wA`

- keine Login-Wand
- Web-UI öffnet direkt

### Mit `-wA`

- Setup/Login erscheint
- erster User wird Admin
- weitere User können später in `Settings > User Management` angelegt werden

## 9. Nach dem ersten Start prüfen

1. Web-UI öffnet sich
2. Suche liefert Ergebnisse
3. Serien-Modal öffnet sich
4. Settings laden
5. Diagnostics laden
6. Queue und Timeline sind erreichbar

Wenn das klappt, ist die Installation gesund.

## 10. Typische Probleme

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
