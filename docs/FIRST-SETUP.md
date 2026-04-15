# First Setup

This guide covers a fresh setup of the customized AniWorld Downloader build from this repository.

## 1. Choose your installation mode

### Use local source install if:

- you want to edit the project locally
- you want the latest custom UI/backend changes from this repo
- you are running it directly on your own PC

### Use Docker / Docker Compose if:

- you want an always-on host
- you want simpler server deployment
- you want cleaner isolation
- you want persistent app data without managing a Python environment manually

## 2. Prerequisites

## Windows

- Python 3.9 to 3.13 recommended
- FFmpeg installed and available in `PATH`
- a browser such as Chrome, Edge, or Firefox

Notes:

- Web UI mode is recommended on Windows
- the old terminal UI can still be limited by `curses` support on newer Python builds

## Linux

- Python 3.9 to 3.13
- FFmpeg
- a browser

Typical package example on Debian / Ubuntu:

```bash
sudo apt update
sudo apt install -y python3 python3-pip ffmpeg
```

## macOS

- Python 3.9 to 3.13
- FFmpeg
- a browser

Typical Homebrew example:

```bash
brew install python ffmpeg
```

Optional:

- IINA if you want macOS-native playback integration
- a virtual environment if your macOS Python setup blocks global `pip install`

## 3. Important folders

AniWorld Downloader uses the same hidden config/app-data folder pattern across all platforms:

- Windows: `%USERPROFILE%\.aniworld`
- Linux: `~/.aniworld`
- macOS: `~/.aniworld`

That folder is where you will find:

- `.env`
- `aniworld.db`
- account data
- favorites
- search history
- stats archive
- stats snapshots
- provider score history
- UI preferences

Default download path:

- usually your user `Downloads` folder unless overridden

## 4. TL;DR quick install

If you already have Python and FFmpeg set up, these are the shortest recommended commands.

### Windows PowerShell

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

If macOS blocks the global install, use this instead:

```bash
mkdir -p aniworld && cd aniworld
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade "git+https://github.com/easycrashx-nex/AniworldDownloader-Update.git#egg=aniworld"
aniworld -w -wA
```

Notes:

- This replaces an older installed `aniworld` package with this custom GitHub build.
- It does not remove your `.aniworld` app-data folder.
- Open a new terminal if `aniworld` still points to an older install after the upgrade.

## 5. Local source setup on Windows

Open PowerShell in the folder where the new `aniworld` project folder should be created and run:

```powershell
git clone https://github.com/easycrashx-nex/AniworldDownloader-Update.git aniworld
cd aniworld
py -m pip install --upgrade pip
py -m pip install -e .
powershell -ExecutionPolicy Bypass -File .\install-launcher.ps1
.\aniworld.cmd -w
```

Enable local Web UI accounts from the start:

```powershell
.\aniworld.cmd -w -wA
```

Expose to your LAN:

```powershell
.\aniworld.cmd -w -wA --web-expose
```

Notes:

- `git clone ... aniworld` creates the `aniworld` folder for you automatically.
- `pip install -e .` only works inside the real repository folder, meaning the folder must contain `pyproject.toml`.
- `aniworld.cmd` is included in this repository and forces the local custom build from `src`, so it does not accidentally launch an older global `aniworld` install.
- `install-launcher.ps1` installs a user-level `aniworld` command into `%USERPROFILE%\.local\bin` and adds that folder to your user `PATH`.
- If you used a ZIP instead of `git clone`, first extract the ZIP and then run the same commands inside the extracted project folder.
- A virtual environment is optional. Use one only if you explicitly want isolated Python packages.

After the one-time launcher install, future terminals can use:

```powershell
aniworld -w -wA
```

## 6. Local source setup on Linux

```bash
git clone https://github.com/easycrashx-nex/AniworldDownloader-Update.git aniworld && cd aniworld && python3 -m pip install --upgrade pip && python3 -m pip install -e . && chmod +x ./aniworld ./install-launcher.sh && ./install-launcher.sh && ./aniworld -w
```

With local accounts:

```bash
./aniworld -w -wA
```

Expose to your LAN:

```bash
./aniworld -w -wA --web-expose
```

After the one-time launcher install, future terminals can use:

```bash
aniworld -w -wA
```

## 7. Local source setup on macOS

```bash
git clone https://github.com/easycrashx-nex/AniworldDownloader-Update.git aniworld && cd aniworld && python3 -m pip install --upgrade pip && python3 -m pip install -e . && chmod +x ./aniworld ./install-launcher.sh && ./install-launcher.sh && ./aniworld -w
```

If macOS blocks installs into the system/Homebrew Python environment, use the venv variant:

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

With local accounts:

```bash
./aniworld -w -wA
```

Expose to your LAN:

```bash
./aniworld -w -wA --web-expose
```

After the one-time launcher install, future terminals can use:

```bash
aniworld -w -wA
```

Notes:

- On some macOS setups, global `pip install` is blocked by the system or by an externally managed Python environment.
- In that case, use the venv block above instead of forcing a global install.
- Once the venv is activated, `aniworld` works normally inside that shell session.

## 8. First launch behavior

### Without `-wA`

- the Web UI opens without a login wall
- you use it directly

### With `-wA`

- the first run shows setup / login flow
- the first created user becomes admin
- after that, additional users can be created in `Settings > User Management`

## 9. What happens on the first start

On first start, the app may:

- create the `~/.aniworld` folder
- create the web database
- install or validate browser/runtime dependencies
- create your first account if Web Auth is enabled

## 10. Verify the setup

After the Web UI starts:

1. Open the app in your browser.
2. Open a search result.
3. Open the queue modal.
4. Open Settings and confirm server info, UI settings, and paths are visible.
5. Open Diagnostics and confirm runtime/cache/storage cards load.

If all of that works, your installation is healthy.

## 11. Basic troubleshooting

### Port already in use

Use a different port:

```bash
python -m aniworld -w --web-port 8090
```

Windows:

```powershell
py -m aniworld -w --web-port 8090
```

### Browser shows stale UI after updates

Use a hard refresh:

- Windows / Linux: `Ctrl + F5`
- macOS: `Cmd + Shift + R`

### Windows terminal mode fails because of `curses`

Use the Web UI mode:

```powershell
py -m aniworld -w
```

### FFmpeg not found

Install FFmpeg and ensure it is available in your shell `PATH`.

### Want more than the first-run basics

Continue with:

- [Usage Guide](USAGE.md)
- [Customization Guide](CUSTOMIZATION.md)
- [Server Deployment Guide](SERVER-DEPLOYMENT.md)
