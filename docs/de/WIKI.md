# Wiki Index

Dies ist die deutsche Dokumentationsspur fuer den angepassten AniWorld Downloader Build in diesem Repository.

Die englische Dokumentation bleibt der Hauptstand:

- [English Wiki Index](../WIKI.md)

## Empfohlene Reihenfolge

### Frische Einrichtung

1. [First Setup](FIRST-SETUP.md)
2. [Usage Guide](USAGE.md)
3. [Customization Guide](CUSTOMIZATION.md)

### Umstieg von einer alten Installation

1. [Migration Guide](MIGRATION.md)
2. [First Setup](FIRST-SETUP.md)
3. [Customization Guide](CUSTOMIZATION.md)

### Server / Docker / Dauerbetrieb

1. [Server Deployment Guide](SERVER-DEPLOYMENT.md)
2. [Customization Guide](CUSTOMIZATION.md)
3. [Usage Guide](USAGE.md)

## Dateien

- [First Setup](FIRST-SETUP.md)
  Frische Einrichtung auf Windows, Linux und macOS.

- [Usage Guide](USAGE.md)
  Erklaert die Web-UI, die Seiten und die typischen Workflows.

- [Customization Guide](CUSTOMIZATION.md)
  `.env`, Web-UI-Settings, Themes, Background Effects, Notifications, Diagnostics, Disk Guard, VPN-/Tunnel-Sichtbarkeit und experimentelle Features.

- [Migration Guide](MIGRATION.md)
  Umstieg von alten AniWorld Downloader Setups auf diesen Build, inklusive Paket-Bereinigung, `.aniworld`-Backup und Full-Reset.

- [Server Deployment Guide](SERVER-DEPLOYMENT.md)
  Docker, Docker Compose, Linux systemd, Reverse Proxy und Server-Empfehlungen.

## Wichtige Kurzinfos

- Version: `5.0.0`
- Empfohlener Modus: Web UI
- Konfigurationsordner:
  - Windows: `%USERPROFILE%\\.aniworld`
  - Linux/macOS: `~/.aniworld`
- Stabile Quellen:
  - AniWorld
  - SerienStream / S.TO
- Experimentelle Quelle:
  - FilmPalast

## Build-spezifische Hinweise

- Queue und Timeline sind getrennt. `Clear Finished` leert nicht die Timeline.
- Das experimentelle Self-Heal kann einen haengenden ffmpeg-Download wieder in die Queue legen, statt den Job zu verlieren.
- Favorites, Search History, UI-Settings und Browser-Notification-Settings sind pro Account.
- Stats und Provider Score History sind global.
- Browser-Notifications funktionieren bei offenem Tab. Service Worker / PWA Push wird absichtlich nicht genutzt.
- Manche serverweiten Einstellungen aus der Web-UI bleiben nur bis zum Neustart erhalten, wenn sie nicht auch in `.env` oder Docker-Env gespeichert werden.
