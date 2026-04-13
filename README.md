<a id="readme-top"></a>

# AniWorld Downloader 5.0.0

This repository contains a customized AniWorld Downloader source build with a heavily expanded Web UI, multi-user support, per-account preferences, a persistent history/archive flow, Auto-Sync management, browser notifications, library comparison, provider health, audit logging, experimental stuck-download self-heal recovery, and a large amount of UI customization.

This README documents the build that exists in this repository right now, not the older upstream defaults.

## Documentation Language

English is the default documentation language for this repository.

- English docs: [docs/WIKI.md](docs/WIKI.md)
- German docs: [docs/de/WIKI.md](docs/de/WIKI.md)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security policy: [SECURITY.md](SECURITY.md)

## What This Build Includes

- modern Web UI for AniWorld and SerienStream / S.TO
- optional local account login for the Web UI
- favorites, stats, search history, UI settings, and browser notification preferences stored per account
- dedicated pages for Library, Favorites, Stats, Timeline, Radar, Auto-Sync, Provider Health, and Audit Log
- dedicated Diagnostics page for runtime, cache, storage, and worker visibility
- queue modal with live progress, bandwidth, retries, captcha handling, and cleanup actions
- timeline backed by a separate archive so clearing finished queue items does not wipe history
- experimental self-heal watchdog for stuck ffmpeg downloads that requeues the job instead of dropping it
- library compare / missing episode detection against the source
- library-side bulk selection with direct `Add Selected To Auto-Sync`
- missing-episode lists with direct queue / repair actions
- Auto-Sync with single, selected, and all-job sync triggers
- per-series modal helper for selecting undownloaded episodes that match the chosen language
- per-user browser notification preferences
- large UI customization surface: density, scale, theme colors, radius, nav size, modal width, animation speed, table density, and background effects
- theme presets, diagnostics, provider score history, backup / import, disk guard, VPN / tunnel detection, and bandwidth limiting
- Docker and Docker Compose setup for local servers, VPS setups, NAS boxes, mini PCs, and other always-on hosts

## Stable vs Experimental

### Stable source targets

- AniWorld
- SerienStream / S.TO

### Experimental source target

- FilmPalast

FilmPalast is hidden by default and can be enabled in `Settings > Development`.

## Documentation Map

If you want the full setup and usage docs, start here:

### English

- [Wiki Index](docs/WIKI.md)
- [First Setup](docs/FIRST-SETUP.md)
- [Usage Guide](docs/USAGE.md)
- [Customization Guide](docs/CUSTOMIZATION.md)
- [Migration Guide](docs/MIGRATION.md)
- [Server Deployment Guide](docs/SERVER-DEPLOYMENT.md)

### German

- [Wiki Index](docs/de/WIKI.md)
- [First Setup](docs/de/FIRST-SETUP.md)
- [Usage Guide](docs/de/USAGE.md)
- [Customization Guide](docs/de/CUSTOMIZATION.md)
- [Migration Guide](docs/de/MIGRATION.md)
- [Server Deployment Guide](docs/de/SERVER-DEPLOYMENT.md)

## Quick Start

### TL;DR Quick Start

#### Windows PowerShell

```powershell
py -m pip uninstall -y aniworld
py -m pip install --upgrade "git+https://github.com/easycrashx-nex/AniworldDownloader-Update.git#egg=aniworld"
aniworld -w -wA
```

#### Linux

```bash
python3 -m pip uninstall -y aniworld
python3 -m pip install --upgrade "git+https://github.com/easycrashx-nex/AniworldDownloader-Update.git#egg=aniworld"
aniworld -w -wA
```

#### macOS

```bash
python3 -m pip uninstall -y aniworld
python3 -m pip install --upgrade "git+https://github.com/easycrashx-nex/AniworldDownloader-Update.git#egg=aniworld"
aniworld -w -wA
```

This replaces an older installed `aniworld` package with this custom GitHub build.
It does not delete your existing app data in `%USERPROFILE%\.aniworld` or `~/.aniworld`.

### Recommended local mode

The Web UI is the recommended mode for this build, especially on Windows.

#### Windows PowerShell

```powershell
git clone https://github.com/easycrashx-nex/AniworldDownloader-Update.git aniworld
cd aniworld
py -m pip install --upgrade pip
py -m pip install -e .
powershell -ExecutionPolicy Bypass -File .\install-launcher.ps1
.\aniworld.cmd -w
```

Run the block from the folder where you want the new `aniworld` project folder to be created.
`aniworld.cmd` is a repo-local launcher that always starts this custom build from `src`, even if another global `aniworld` install already exists on the system.
After the one-time launcher install, future terminals can use:

```powershell
aniworld -w -wA
```

#### Linux

```bash
git clone https://github.com/easycrashx-nex/AniworldDownloader-Update.git aniworld && cd aniworld && python3 -m pip install --upgrade pip && python3 -m pip install -e . && chmod +x ./aniworld ./install-launcher.sh && ./install-launcher.sh && ./aniworld -w
```

After the one-time launcher install, future terminals can use:

```bash
aniworld -w -wA
```

#### macOS

```bash
git clone https://github.com/easycrashx-nex/AniworldDownloader-Update.git aniworld && cd aniworld && python3 -m pip install --upgrade pip && python3 -m pip install -e . && chmod +x ./aniworld ./install-launcher.sh && ./install-launcher.sh && ./aniworld -w
```

After the one-time launcher install, future terminals can use:

```bash
aniworld -w -wA
```

If you prefer a virtual environment, you can still use one, but it is optional and not required for this repository.

Expose the Web UI to your LAN if needed:

```bash
python -m aniworld -w --web-expose
```

On Windows, use:

```powershell
.\aniworld.cmd -w --web-expose
```

### Recommended server mode

For server deployments, use Docker Compose:

```bash
docker-compose up -d --build
```

The current Compose file is already tuned for this custom Web UI build.

## Important Behavior Notes

### Config and data path

AniWorld Downloader stores its app data in:

- Windows: `%USERPROFILE%\.aniworld`
- Linux: `~/.aniworld`
- macOS: `~/.aniworld`

That folder contains things like:

- `.env`
- `aniworld.db`
- authentication data
- favorites / stats / search history / per-user preferences

### What is per-account

These are stored separately per logged-in user:

- favorites
- search history
- UI settings
- browser notification settings

These are global / shared in the current build:

- stats
- provider scoreboard / provider score history
- queue / timeline archive
- diagnostics snapshots

### What is not automatically persistent when changed only in the Web UI

Some server-wide settings are intentionally temporary if you only change them inside the Web UI and then restart the app. Persist them in `.env` or Docker environment variables instead.

Typical examples:

- download path
- provider defaults
- language separation
- Auto-Sync defaults
- experimental source toggles
- experimental stuck-download self-heal toggle

### Browser notifications

This build supports browser notifications, but they are not a service-worker push system. Notifications work while the Web UI is open in a browser tab or window. The PWA / service worker setup was intentionally removed to avoid stale-state and loading issues.

### Diagnostics and server visibility

The current build also includes:

- Diagnostics page for runtime, cache, queue, sync, and storage state
- disk guard thresholds and free-space visibility
- server bind host, LAN URLs, and open URLs in Settings
- best-effort VPN / tunnel detection for common setups such as WireGuard, OpenVPN, Tailscale, and Gluetun-like environments
- self-heal/runtime visibility for stuck-download recovery when the experimental watchdog is enabled

### Queue vs Timeline

- Queue is the live working area for active and pending jobs.
- Timeline is the archive/history view.
- Experimental self-heal can requeue a stuck running job instead of letting it die in place.

Clearing finished queue items does not clear Timeline anymore.

## Supported Provider Choices

The build currently exposes these provider options in the app:

- VOE
- Vidhide
- Vidara
- Filemoon
- Vidmoly
- Vidoza
- Doodstream

Availability still depends on the selected source, language, and the actual episode or movie page.

## Windows Note

The Web UI is strongly recommended on modern Windows Python setups. The old terminal UI depends on `curses`, which is more fragile on newer Windows Python versions, especially Python 3.14+.

## Migration From Older Installs

If you already have an older AniWorld Downloader setup and want to move to this custom build, use the migration guide:

- [Migration Guide](docs/MIGRATION.md)

That guide covers:

- old pip installs
- old ZIP / source-folder installs
- old Docker installs
- how to back up or reset your existing `.aniworld` data

## Docker Summary

This repository already includes:

- [Dockerfile](Dockerfile)
- [docker-compose.yaml](docker-compose.yaml)
- [docker-entrypoint.sh](docker-entrypoint.sh)
- [.dockerignore](.dockerignore)

The current Docker setup is designed for the Web UI and includes:

- persistent downloads
- persistent app data
- healthcheck
- Docker-friendly env defaults
- web auth enabled by default in Compose

Full server docs:

- [Server Deployment Guide](docs/SERVER-DEPLOYMENT.md)

## Legal Notice

AniWorld Downloader is a client-side tool. It does not host, upload, or distribute media itself. You are responsible for how you use it and for complying with applicable laws and the terms of the websites you access.

## License

This project is licensed under the [MIT License](LICENSE).

<p align="right">(<a href="#readme-top">back to top</a>)</p>
