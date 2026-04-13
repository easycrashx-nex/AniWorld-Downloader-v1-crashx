# Migration Guide

Diese Anleitung beschreibt den Umstieg von alten AniWorld Downloader Installationen auf diesen Build.

## 1. Zwei Wege

### A. Bestehende Daten behalten

Sinnvoll, wenn du behalten willst:

- Downloads
- Accounts
- Favorites
- Stats
- Provider Score History
- Search History
- Auto-Sync Jobs

### B. Frisch starten

Sinnvoll, wenn du willst:

- saubere Datenbank
- keine alten Accounts
- keine alten Queue-/Timeline-Reste
- keine alten Settings

## 2. Was vorher sichern?

Immer mindestens sichern:

- Download-Ordner
- `.aniworld`-Ordner

Pfade:

- Windows: `%USERPROFILE%\\.aniworld`
- Linux/macOS: `~/.aniworld`

## 3. Altes pip-Setup

### Windows

```powershell
py -m pip uninstall aniworld
```

### Linux / macOS

```bash
python -m pip uninstall aniworld
```

Danach diesen Build normal neu installieren.

## 4. Altes ZIP / Source-Setup

Empfohlener sicherer Weg:

1. alten Projektordner als Backup behalten
2. neuen Build in neuen Ordner legen
3. neuen Build installieren
4. optional nur dann eine venv anlegen, wenn du das bewusst willst

## 5. Sauberer Reset

Windows:

```powershell
Rename-Item "$HOME\\.aniworld" ".aniworld.backup"
```

Linux / macOS:

```bash
mv ~/.aniworld ~/.aniworld.backup
```

## 6. Bestehende Daten behalten

Dann `.aniworld` nicht loeschen oder umbenennen. Der neue Build nutzt:

- Accounts
- Favorites
- bestehende DB
- `.env`

## 7. Docker-Migration

```bash
docker-compose down
docker-compose up -d --build
```

Wichtig:

- bestehende Daten-Volumes behalten
- Download-Mounts nicht aendern, wenn du Daten behalten willst

## 8. Checkliste nach dem Umstieg

- Web-UI oeffnet
- Login funktioniert
- Settings laden
- Queue laedt
- Timeline zeigt Archiv
- Library laedt
- Auto-Sync laedt
- Diagnostics laedt
- Provider Health History laedt
