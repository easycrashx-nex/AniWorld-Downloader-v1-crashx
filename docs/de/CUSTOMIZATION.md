# Customization Guide

Diese Anleitung beschreibt `.env`, Web-UI-Settings und Build-spezifische Anpassungen.

## 1. Was ist wo persistent?

### Pro Account

- Favorites
- Search History
- UI Settings
- Browser Notification Settings

### Global / gemeinsam

- Stats
- Provider Score History
- Queue / Timeline Archiv
- Diagnostics Snapshots

### Nur temporaer, wenn nur in der Web-UI geaendert

Wenn du sie restart-sicher willst, auch in `.env` oder Docker-Env setzen:

- Download Path
- Language Separation
- Disable English Sub
- Auto-Sync Defaults
- Experimental FilmPalast
- Bandwidth Limit
- Provider Fallback Order
- Disk Guard Thresholds
- Library Auto-Repair Toggle
- Experimental stuck-download self-heal

## 2. Config-Datei

Standardpfad:

- Windows: `%USERPROFILE%\\.aniworld\\.env`
- Linux/macOS: `~/.aniworld/.env`

## 3. Wichtige `.env`-Werte

### Downloads

```env
ANIWORLD_DOWNLOAD_PATH=Downloads
ANIWORLD_LANG_SEPARATION=0
ANIWORLD_DISABLE_ENGLISH_SUB=0
```

### Default Sprache / Provider

```env
ANIWORLD_LANGUAGE="German Dub"
ANIWORLD_PROVIDER=VOE
```

### Auto-Sync Defaults

```env
ANIWORLD_SYNC_SCHEDULE=0
ANIWORLD_SYNC_LANGUAGE=German Dub
ANIWORLD_SYNC_PROVIDER=VOE
```

### Erweiterte Build-Settings

```env
ANIWORLD_EXPERIMENTAL_FILMPALAST=0
ANIWORLD_EXPERIMENTAL_SELF_HEAL=0
```

## 4. UI Settings

Der Build enthaelt u. a.:

- Density
- UI Scale
- Theme Color
- Theme Preset
- Card Radius
- Animation Speed
- Content Width
- Modal Width
- Nav Size
- Table Density
- Background Effects

## 5. Default Search Filters

Verfuegbar:

- default sort
- default genres
- default year from
- default year to
- favorites only
- downloaded only

## 6. Browser Notifications

Konfigurierbar:

- Hauptschalter
- Browse
- Queue
- Auto-Sync
- Library
- Settings
- System

Wichtig:

- Browser-Permission noetig
- funktioniert bei offenem Tab
- keine Service-Worker-Pushes

## 7. Diagnostics und Server-Sichtbarkeit

Der Build zeigt auch:

- Bind Host / Port / LAN URLs
- Public IP
- best-effort VPN-/Tunnel-Erkennung
- Disk Guard
- Cache Warmup Sichtbarkeit

Typische erkannte Setups:

- WireGuard
- OpenVPN / tun
- Tailscale
- PPP-Tunnel
- Gluetun-aehnliche Setups

Das experimentelle Self-Heal wird ebenfalls in Settings und Diagnostics sichtbar gemacht. Wenn es aktiviert ist, beobachtet es laufende ffmpeg-Downloads auf harte Hänger, beendet den hängenden Prozessbaum und legt denselben Queue-Job wieder in `queued`, statt ihn zu verlieren. Standardmaessig bleibt es aus, weil die Recovery bei kaputten Streams zusaetzliche Last erzeugen kann.

## 8. Experimentelles Self-Heal

Aktivierbar in:

- `Settings > Development`

oder ueber `.env` / Docker-Env:

```env
ANIWORLD_EXPERIMENTAL_SELF_HEAL=1
```

Es ist gedacht fuer:

- echte ffmpeg-Haenger
- Queue-Rettung ohne Server-Neustart

Es ist nicht gedacht als:

- allgemeiner AI-Debugger
- Ersatz fuer normale Retry-/Fallback-Logik

## 9. Library- und Modal-Helfer

Aktuell enthalten:

- `Add Selected To Auto-Sync` direkt aus der Library
- Duplicate-Schutz beim Auto-Sync-Anlegen
- exakte Missing-Episode-Labels
- `Queue Missing`
- `Auto-Repair Missing`
- Modal-Aktion fuer nur undownloadete Folgen passend zur aktuellen Sprache

## 10. Provider

Der Build bietet aktuell:

- VOE
- Vidhide
- Vidara
- Filemoon
- Vidmoly
- Vidoza
- Doodstream

Die echte Verfuegbarkeit haengt weiter von Quelle, Sprache und Episode ab.
