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

Schnelle Backup-Befehle:

### Windows

```powershell
Copy-Item "$HOME\.aniworld" "$HOME\.aniworld.backup" -Recurse -Force
```

### Linux / macOS

```bash
cp -a ~/.aniworld ~/.aniworld.backup
```

## 3. Altes pip-Setup

### Windows

```powershell
py -m pip uninstall -y aniworld
```

### Linux / macOS

```bash
python3 -m pip uninstall -y aniworld
```

Danach diesen Build normal neu installieren.

Das ist stark empfohlen, wenn auf dem Rechner vorher schon ein altes globales `aniworld` installiert war.

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

Danach erstellt der neue Build einen frischen `.aniworld`-Ordner.

### Hard Reset: alten App-Datenordner loeschen

Nur machen, wenn du den alten lokalen Stand wirklich komplett loswerden willst.

Windows:

```powershell
Remove-Item "$HOME\.aniworld" -Recurse -Force
```

Linux / macOS:

```bash
rm -rf ~/.aniworld
```

Wenn du `.aniworld` loeschst, verlierst du die alten lokalen:

- Accounts
- gespeicherten Settings
- Favorites
- Search History
- Stats-Archiv / Snapshots
- Provider Score History
- Audit Log
- Auto-Sync Jobs
- lokale Auth-/Session-Daten

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

## 9. Empfohlener Weg fuer die meisten Nutzer

Wenn du moeglichst sauber umsteigen willst:

1. `.aniworld` sichern
2. Download-Ordner sichern
3. altes `aniworld` per `pip uninstall -y aniworld` entfernen
4. wenn du wirklich frisch starten willst, `.aniworld` umbenennen oder loeschen
5. diesen Custom-Build neu installieren
6. nur dann ein Backup zurueckspielen, wenn du die alten Daten bewusst behalten willst
