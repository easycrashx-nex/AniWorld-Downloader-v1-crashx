# Usage Guide

Diese Anleitung beschreibt den aktuellen Web-UI-Flow dieses Builds.

## Browse

Browse enthaelt:

- Home
- Library
- Favorites

### Home

Home ist fuer:

- Quellwechsel zwischen AniWorld und SerienStream / S.TO
- Suche
- Quick Genres
- Advanced Search Filter
- Search History
- Oeffnen des Serien-Modals

### Library

Library kann:

- lokale Titel nach Speicherort und Sprache anzeigen
- fehlende Episoden gegen Quelle vergleichen
- exakte fehlende Episodenlabels anzeigen
- `Queue Missing` und `Auto-Repair Missing`
- sichtbare Serien markieren und direkt zu Auto-Sync hinzufuegen

### Favorites

Favorites ist eine eigene Seite und nicht mehr mit Home vermischt.

## Stats

Stats enthaelt:

- Stats
- Timeline
- Radar

### Stats

Zeigt:

- globale Downloadzahlen
- Episodenzahlen
- Provider-Qualitaet
- Storage-Summary
- Activity Chart

### Timeline

Timeline ist das Archiv:

- completed
- failed
- cancelled
- Fehlerdetails
- Retry
- Delete einzelner Timeline-Eintraege

Wichtig:

- Timeline ist getrennt von Queue
- `Clear Finished` leert nicht die Timeline

### Radar

Zeigt neue Aktivitaet / frische Releases.

## Queue

Queue ist der Live-Arbeitsbereich.

Du siehst dort:

- laufende Downloads
- Fortschritt, Speed, ETA
- Retry / Cancel / Clear Finished
- Captcha-Hinweise

## Settings

Settings enthaelt:

- Settings
- Auto-Sync
- Provider Health
- Audit Log
- Diagnostics

### Settings-Seite

Hier kannst du verwalten:

- User
- Custom Paths
- Server Info
- Browser Notifications
- UI Settings
- Default Search Filters
- Auto-Sync Defaults
- Bandwidth Limit
- Provider Fallback Order
- Disk Guard
- Backup Export / Import Restore
- VPN-/Tunnel-Sichtbarkeit
- Development-Optionen wie FilmPalast

### Auto-Sync

Auto-Sync kann:

- Jobs anlegen und bearbeiten
- einzelne Jobs syncen
- selektierte Jobs syncen
- alle Jobs syncen
- nur gueltige Sprachen/Provider pro Serie anbieten
- Library-Selektionen direkt uebernehmen

### Provider Health

Provider Health zeigt:

- aktuelle Provider-Werte
- Fehler / Erfolgsquote
- Scoreboard
- Provider Score History

### Audit Log

Zeigt User-, Queue-, Auto-Sync- und Settings-Aktionen.

### Diagnostics

Diagnostics zeigt:

- Runtime / Worker State
- Cache Warmup und Cache-Alter
- Disk Guard Infos
- Server / Bind / LAN / Open URL Infos

## Alerts

`Alerts` ist das In-App Notification Center.

Es sammelt Meldungen fuer:

- Browse
- Queue
- Auto-Sync
- Library
- Settings
- System

## Serien-Modal

Das Modal bietet:

- Poster und Serieninfos
- Favorite Button
- Sprache / Provider / Download Path
- Auto-Sync Toggle
- Season Browser
- Sprach-Flaggen pro Folge
- Aktion zum Auswaehlen nur der noch nicht geladenen Folgen fuer die aktuelle Sprache

## Multi-User

Mit `-wA`:

- erster User wird Admin
- Favorites sind pro Account
- Search History ist pro Account
- UI Settings sind pro Account
- Browser Notification Settings sind pro Account
- Stats und Provider Score History sind global
