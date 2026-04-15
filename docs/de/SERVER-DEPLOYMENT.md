# Server Deployment Guide

Diese Anleitung beschreibt den empfohlenen Betrieb auf Servern und Dauerlauf-Systemen.

## Empfohlene Reihenfolge

1. Docker Compose
2. plain Docker
3. bare-metal Linux mit systemd

## 1. Docker Compose

Start:

```bash
docker-compose up -d --build
```

Der aktuelle Compose-Stand ist bereits auf diese Web-UI angepasst.

### Wichtige Mounts

- `./Downloads:/app/Downloads`
- `aniworld-data:/home/aniworld/.aniworld`

### Wichtige Defaults

- `ANIWORLD_WEB_PORT=8080`
- `ANIWORLD_WEB_EXPOSE=1`
- `ANIWORLD_WEB_NO_BROWSER=1`
- `ANIWORLD_WEB_THREADS=16`
- `ANIWORLD_WEB_AUTH=1`
- `ANIWORLD_EXPERIMENTAL_FILMPALAST=0`

## 2. Plain Docker

Linux / macOS:

```bash
docker build -t aniworld .
docker run -d --name aniworld-downloader \
  -p 8080:8080 \
  -v "${PWD}/Downloads:/app/Downloads" \
  -v aniworld-data:/home/aniworld/.aniworld \
  -e ANIWORLD_WEB_AUTH=1 \
  aniworld
```

## 3. Bare-metal Linux mit systemd

Beispiel:

- App-Ordner: `/opt/aniworld`
- User: `aniworld`

Beispiel-Start:

```bash
python -m aniworld -w --web-expose --no-browser --web-port 8080
```

Eine venv ist auch hier optional und kein Muss.

## 4. Reverse Proxy

Wenn du einen Reverse Proxy nutzt, setze:

```env
ANIWORLD_WEB_BASE_URL=https://deine-domain.example
```

## 5. Backups

Ohne `.aniworld` verlierst du:

- Accounts
- Favorites
- Stats-Archiv
- Stats-Snapshots
- Provider Score History
- Search History
- UI Preferences
- Audit Log
- Auto-Sync Jobs

Immer sichern:

- Download-Speicher
- `.aniworld`

## 6. Monitoring

Du solltest beobachten:

- Container- oder Service-Restarts
- freien Speicherplatz
- Schreibrechte im Download-Ziel
- Diagnostics-Seite
- Cache Warmup bei großen Libraries
- VPN-/Tunnel-Zustand, falls der Server davon abhängt

## 7. Empfohlene Server-Defaults

```env
ANIWORLD_WEB_AUTH=1
ANIWORLD_WEB_EXPOSE=1
ANIWORLD_WEB_NO_BROWSER=1
ANIWORLD_WEB_THREADS=16
ANIWORLD_EXPERIMENTAL_FILMPALAST=0
```
