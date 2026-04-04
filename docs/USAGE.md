# Usage Guide

This guide explains how the customized Web UI is structured and how the main workflows work.

## Top-level navigation

## Browse

Browse contains:

- Home
- Library
- Favorites

### Home

Use Home to:

- switch between AniWorld and SerienStream / S.TO
- search titles
- apply quick genres
- use advanced search filters
- revisit search history
- open the series modal

### Library

Use Library to:

- browse downloaded content by location
- filter by language
- search local content
- sort results
- detect missing episodes
- compare local library state with the source
- inspect the exact episode labels that are missing
- queue or auto-repair missing episodes
- select visible series and add them directly to Auto-Sync

### Favorites

Favorites is a dedicated page now. It is no longer mixed into the Home page.

Use it to:

- reopen pinned series quickly
- keep a clean list separate from general browsing

## Stats

Stats contains:

- Stats
- Timeline
- Radar

### Stats page

Use Stats to view:

- total downloads
- total delivered episodes
- provider quality
- storage-related summary
- activity chart
- global stats shared across accounts

### Timeline page

Timeline is the archive/history area.

It shows:

- completed downloads
- failed downloads
- cancelled downloads
- error details
- retry actions

Important:

- Timeline is separate from Queue
- clearing finished queue items does not clear Timeline

### Radar page

Radar is the new-release area.

Use it to:

- see fresh episode updates
- inspect release activity

## Queue

Queue is the live work area.

Use it to:

- see active downloads
- see progress, speed, and ETA
- retry failed items
- clear finished queue items
- solve captcha prompts when required

Queue is for current and pending work. Timeline is for archive/history.

## Settings

Settings contains:

- Settings
- Auto-Sync
- Provider Health
- Audit Log
- Diagnostics

### Settings page

Settings lets you manage:

- users
- custom download paths
- server info
- browser notifications
- UI settings
- default search filters
- Auto-Sync defaults
- download behavior
- development toggles such as experimental FilmPalast
- disk guard thresholds
- bandwidth limit
- provider fallback order
- backup export / import restore
- VPN / tunnel visibility and public IP detection

### Auto-Sync page

Use Auto-Sync to:

- create and manage tracked series jobs
- sync one job
- sync selected jobs
- sync all jobs
- edit language/provider/path per job
- add series directly from Library selections

The edit dialog only exposes languages and providers that are actually available for that series.

### Provider Health page

Use Provider Health to:

- check which providers are currently healthy
- see recent failures
- inspect activity and success rates
- inspect provider score history over time

### Audit Log page

Audit Log shows:

- account activity
- queue actions
- Auto-Sync actions
- settings changes

This is especially useful in multi-user setups.

### Diagnostics page

Diagnostics shows:

- runtime / worker state
- cache warmup state and cache ages
- disk guard visibility
- server bind / LAN / open URL information
- live process information from the running web backend

## Alerts

The `Alerts` menu is the in-app notification center.

It stores recent notices for:

- Browse
- Queue
- Auto-Sync
- Library
- Settings
- system/general messages

Browser notifications can also be enabled in Settings, but they only work while the browser tab is open.

## Series modal

When you open a series from Browse or Favorites, the modal gives you:

- cover and series details
- quick stats
- favorite button
- language selection
- provider selection
- download path selection
- Auto-Sync toggle
- season/episode browser
- language flags per episode when available
- a helper action to select only undownloaded episodes for the chosen language

## Search filters

Home search supports:

- query text
- genre filter
- year from
- year to
- sort mode
- favorites only
- downloaded only
- quick genre chips
- search history

## Multi-user behavior

With Web Auth enabled:

- the first setup user becomes admin
- admins can create more users
- favorites are per account
- search history is per account
- UI settings are per account
- browser notification settings are per account
- stats are global/shared
- provider score history is global/shared

## Source notes

### AniWorld

- main anime source
- stable in this build

### SerienStream / S.TO

- stable in this build
- language information is resolved more precisely per episode than before

### FilmPalast

- still experimental
- hidden by default
- can be enabled in `Settings > Development`

## Good daily workflow

1. Search on Home
2. Open a series
3. Choose language/provider/path
4. Queue downloads
5. Monitor Queue
6. Use Timeline as your permanent history
7. Use Library Compare to detect missing episodes
8. Use Auto-Sync for ongoing shows
