# Contributing

## Scope

This repository is a customized AniWorld Downloader build focused on:

- the expanded Web UI
- server-friendly deployment
- multi-user support
- Auto-Sync and library tooling
- diagnostics, provider health, and UI customization

Contributions should preserve those goals and avoid regressing the current Web-first workflow.

## Before You Start

Please:

- read [README.md](README.md)
- read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- read the documentation index in [docs/WIKI.md](docs/WIKI.md)
- check whether the requested change already exists in the current customized build

If you plan to change behavior in a major way, open an issue or discussion first when possible.

## Development Setup

### Local source install

#### Windows PowerShell

```powershell
cd <project-folder>
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -e .
py -m aniworld -w
```

#### Linux / macOS

```bash
cd <project-folder>
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m aniworld -w
```

## Preferred Contribution Areas

Good contribution targets:

- Web UI improvements
- diagnostics and server tooling
- library / queue / Auto-Sync workflow improvements
- provider resilience and fallback handling
- documentation
- Docker / server deployment improvements
- bug fixes that keep existing user data intact

## Contribution Guidelines

### 1. Do not break persisted user data

Be careful with:

- `.aniworld`
- `aniworld.db`
- timeline / archive data
- user settings and accounts
- custom download paths

Avoid destructive migrations unless absolutely required.

### 2. Keep server behavior explicit

When changing settings behavior, be clear about whether a setting is:

- per user
- global/shared
- temporary unless also persisted in `.env` or Docker env

### 3. Preserve Windows, Linux, and macOS support

Avoid platform-specific assumptions unless they are guarded properly.

### 4. Prefer Web UI consistency

This build is Web-first. New features should integrate cleanly with:

- Browse
- Library
- Queue
- Stats / Timeline / Radar
- Auto-Sync
- Settings

### 5. Keep docs in sync

If you change user-facing behavior, update:

- [README.md](README.md)
- the relevant docs under [docs](docs)
- German docs under [docs/de](docs/de) when the change affects documented user workflows

## Coding Notes

- keep changes focused
- prefer small, reviewable patches
- avoid hardcoded machine-specific paths
- avoid committing local-only directories or files
- keep UI text and naming consistent with the current build

## Testing Expectations

Before submitting, test what applies:

- Web UI still loads
- changed page or workflow still works
- queue-related changes do not break timeline/history
- library changes do not break compare or delete flows
- Auto-Sync changes still prevent duplicate jobs
- settings changes still persist or behave as documented

If you changed JavaScript, run a syntax check where possible.

## Pull Request Guidance

A good PR should include:

- what changed
- why it changed
- whether the change is UI-only, backend-only, or both
- any migration impact
- screenshots for visual changes when relevant

## Security Issues

Do not open public issues for sensitive security problems. See [SECURITY.md](SECURITY.md).
