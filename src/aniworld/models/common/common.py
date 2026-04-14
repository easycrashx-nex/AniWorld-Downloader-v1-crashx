import getpass
import hashlib
import importlib.util
import os
import platform
import re
import shlex
import signal
import subprocess
import sys
import time
import threading as _threading
from pathlib import Path
from typing import Tuple

import ffmpeg

from ...autodeps import DependencyManager

try:
    from ...autodeps import get_player_path, get_syncplay_path
    from ...config import (
        INVERSE_LANG_LABELS,
        LANG_CODE_MAP,
        LANG_KEY_MAP,
        PROVIDER_HEADERS_D,
        PROVIDER_HEADERS_W,
        Audio,
        Subtitles,
        get_video_codec,
        logger,
    )
except ImportError:
    from aniworld.autodeps import get_player_path, get_syncplay_path
    from aniworld.config import (
        INVERSE_LANG_LABELS,
        LANG_CODE_MAP,
        LANG_KEY_MAP,
        PROVIDER_HEADERS_D,
        PROVIDER_HEADERS_W,
        Audio,
        Subtitles,
        get_video_codec,
        logger,
    )

# Precompile regex for forbidden filename characters
FORBIDDEN_CHARS = re.compile(r'[<>:"/\\|?*]')


def clean_title(title: str) -> str:
    """Clean a string to make it safe for use as a filename."""
    return FORBIDDEN_CHARS.sub("", title).strip()


def check_downloaded(episode_path):
    result = {
        "exists": False,
        "video_langs": set(),
        "audio_langs": set(),
    }

    if not episode_path.exists():
        return result

    result["exists"] = True

    try:
        probe = ffmpeg.probe(episode_path)
    except ffmpeg.Error:
        return result

    streams = probe.get("streams", [])

    for s in streams:
        lang = s.get("tags", {}).get("language", "und")
        if s.get("codec_type") == "video":
            result["video_langs"].add(lang)
        elif s.get("codec_type") == "audio":
            result["audio_langs"].add(lang)

    return result


class ProviderData:
    """
    Container for provider URLs grouped by language settings.

    The internal structure is:

        dict[(Audio, Subtitles)][provider_name]

    Meaning:
    - The key is a tuple of (Audio, Subtitles)
    - The value is a dictionary mapping provider names to their URLs
    """

    def __init__(self, data):
        self._data = data

    def __str__(self):
        # return f"{self.__class__.__name__}({self._data!r})"
        lines = []

        for (audio, subtitles), providers in sorted(
            self._data.items(), key=lambda item: (item[0][0].value, item[0][1].value)
        ):
            header = f"{audio.value} audio"
            if subtitles != Subtitles.NONE:
                header += f" + {subtitles.value} subtitles"

            lines.append(header)

            for provider, url in providers.items():
                lines.append(f"  - {provider:<8} -> {url}")

            lines.append("")

        return "\n".join(lines).rstrip()

    def __repr__(self):
        return f"{self.__class__.__name__}({self._data!r})"

    # Accept a tuple directly
    def get(self, lang_tuple: Tuple[Audio, Subtitles]):
        return self._data.get(lang_tuple, {})

    # Behave like a dictionary
    def __getitem__(self, lang_tuple: Tuple[Audio, Subtitles]):
        return self._data[lang_tuple]


class DownloadCancelledError(RuntimeError):
    """Raised when an active download is intentionally stopped."""


# -----------------------------------------------------------------------------
# Episode actions (moved from models/*/episode.py)
# -----------------------------------------------------------------------------


def _remove_empty_dirs(folder_path, base_folder):
    """Remove folder_path and base_folder if they are empty directories."""
    try:
        if folder_path.is_dir() and not any(folder_path.iterdir()):
            folder_path.rmdir()
        if base_folder.is_dir() and not any(base_folder.iterdir()):
            base_folder.rmdir()
    except OSError:
        pass


# Thread-safe global for current ffmpeg download progress (used by web UI)
_ffmpeg_progress_lock = _threading.Lock()
_ffmpeg_progress = {
    "percent": 0.0,
    "time": "",
    "speed": "",
    "bandwidth": "",
    "active": False,
    "engine": "",
    "phase": "",
    "host": "",
    "mode": "",
    "profile": "",
}
_ffmpeg_runtime = {
    "active": False,
    "pid": None,
    "label": "",
    "started_at": 0.0,
    "last_progress_at": 0.0,
    "stall_timeout": 0,
    "reason": "",
    "engine": "",
    "phase": "",
    "host": "",
    "mode": "",
    "profile": "",
    "_process": None,
}


def _download_backend_mode():
    backend = str(os.getenv("ANIWORLD_DOWNLOAD_BACKEND", "auto") or "auto").strip().lower()
    return backend if backend in {"auto", "ffmpeg", "ytdlp"} else "auto"


def _download_speed_profile():
    profile = str(os.getenv("ANIWORLD_DOWNLOAD_SPEED_PROFILE", "balanced") or "balanced").strip().lower()
    return profile if profile in {"fast", "balanced", "safe"} else "balanced"


def _rate_limit_guard_enabled():
    return str(os.getenv("ANIWORLD_RATE_LIMIT_GUARD", "1") or "1").strip() == "1"


def _preflight_check_enabled():
    return str(os.getenv("ANIWORLD_PREFLIGHT_CHECK", "1") or "1").strip() == "1"


def _auto_provider_switch_enabled():
    return str(os.getenv("ANIWORLD_AUTO_PROVIDER_SWITCH", "1") or "1").strip() == "1"


def _provider_engine_rules():
    rules = {}
    raw = str(os.getenv("ANIWORLD_DOWNLOAD_ENGINE_RULES", "") or "")
    for part in raw.split(","):
        chunk = str(part or "").strip()
        if not chunk or ":" not in chunk:
            continue
        provider, engine = chunk.split(":", 1)
        provider = provider.strip()
        engine = engine.strip().lower()
        if provider and engine in {"ffmpeg", "ytdlp"}:
            rules[provider.lower()] = engine
    return rules


def _adaptive_engine_for_provider(provider_name):
    provider = str(provider_name or "").strip()
    rules = _provider_engine_rules()
    if provider.lower() in rules:
        return rules[provider.lower()], "rule"

    mode = _download_backend_mode()
    if mode in {"ffmpeg", "ytdlp"}:
        return mode, "forced"

    profile = _download_speed_profile()
    conservative = _rate_limit_guard_enabled() or profile == "safe"
    fast_lane = {"voe", "filemoon", "vidhide"}
    safe_lane = {"vidmoly", "vidoza", "doodstream", "vidara"}
    lowered = provider.lower()
    if lowered in safe_lane and conservative:
        return "ffmpeg", "adaptive"
    if lowered in fast_lane:
        return "ytdlp", "adaptive"
    if profile == "fast":
        return "ytdlp", "adaptive"
    return "ffmpeg", "adaptive"


def _engine_attempt_order(provider_name, full_stream_needed):
    primary, mode = _adaptive_engine_for_provider(provider_name)
    order = [primary]
    if full_stream_needed:
        fallback = "ffmpeg" if primary == "ytdlp" else "ytdlp"
        if fallback not in order:
            order.append(fallback)
    return order, mode


def _fragment_concurrency():
    profile = _download_speed_profile()
    if profile == "safe":
        return 1
    if profile == "fast":
        return 2 if _rate_limit_guard_enabled() else 4
    return 1 if _rate_limit_guard_enabled() else 2


def _set_transfer_runtime(engine="", phase="", host="", mode="", profile="", active=True):
    with _ffmpeg_progress_lock:
        if engine:
            _ffmpeg_progress["engine"] = engine
            _ffmpeg_runtime["engine"] = engine
        if phase:
            _ffmpeg_progress["phase"] = phase
            _ffmpeg_runtime["phase"] = phase
        if host:
            _ffmpeg_progress["host"] = host
            _ffmpeg_runtime["host"] = host
        if mode:
            _ffmpeg_progress["mode"] = mode
            _ffmpeg_runtime["mode"] = mode
        if profile:
            _ffmpeg_progress["profile"] = profile
            _ffmpeg_runtime["profile"] = profile
        _ffmpeg_progress["active"] = bool(active)


def _yt_dlp_available():
    return importlib.util.find_spec("yt_dlp") is not None


def _bandwidth_limit_output_kwargs():
    raw = str(os.getenv("ANIWORLD_BANDWIDTH_LIMIT_KBPS", "0") or "0").strip()
    try:
        limit_kbps = int(float(raw))
    except (TypeError, ValueError):
        limit_kbps = 0
    if limit_kbps <= 0:
        return {}
    limit_kbps = max(128, min(limit_kbps, 250000))
    return {
        "maxrate": f"{limit_kbps}k",
        "bufsize": f"{max(limit_kbps * 2, 512)}k",
    }


def get_ffmpeg_progress():
    """Return a snapshot of the current ffmpeg download progress."""
    with _ffmpeg_progress_lock:
        return dict(_ffmpeg_progress)


def get_ffmpeg_runtime_state():
    """Return sanitized runtime state for the active ffmpeg process."""
    with _ffmpeg_progress_lock:
        return {
            "active": bool(_ffmpeg_runtime.get("active")),
            "pid": _ffmpeg_runtime.get("pid"),
            "label": _ffmpeg_runtime.get("label") or "",
            "started_at": float(_ffmpeg_runtime.get("started_at") or 0.0),
            "last_progress_at": float(_ffmpeg_runtime.get("last_progress_at") or 0.0),
            "stall_timeout": int(_ffmpeg_runtime.get("stall_timeout") or 0),
            "reason": _ffmpeg_runtime.get("reason") or "",
            "engine": _ffmpeg_runtime.get("engine") or "",
            "phase": _ffmpeg_runtime.get("phase") or "",
            "host": _ffmpeg_runtime.get("host") or "",
            "mode": _ffmpeg_runtime.get("mode") or "",
            "profile": _ffmpeg_runtime.get("profile") or "",
        }


def _reset_ffmpeg_runtime_state():
    _ffmpeg_runtime.update(
        active=False,
        pid=None,
        label="",
        started_at=0.0,
        last_progress_at=0.0,
        stall_timeout=0,
        reason="",
        engine="",
        phase="",
        host="",
        mode="",
        profile="",
        _process=None,
    )


def _kill_ffmpeg_process_tree(process):
    if process is None:
        return False
    try:
        if process.poll() is not None:
            return False
    except Exception:
        return False

    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=5,
            )
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except Exception:
        try:
            process.kill()
        except Exception:
            return False
    return True


def terminate_ffmpeg_process_tree(reason="manual stop"):
    """Terminate the active ffmpeg process tree, if any."""
    with _ffmpeg_progress_lock:
        process = _ffmpeg_runtime.get("_process")
        if not process:
            return False
        _ffmpeg_runtime["reason"] = str(reason or "manual stop")

    killed = _kill_ffmpeg_process_tree(process)
    if killed:
        with _ffmpeg_progress_lock:
            _ffmpeg_progress.update(
                percent=0.0, time="", speed="", bandwidth="", active=False
            )
    return killed


def _parse_ffmpeg_time(time_str):
    """Parse ffmpeg time string (HH:MM:SS.xx) to seconds."""
    try:
        parts = time_str.split(":")
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    except (ValueError, IndexError):
        pass
    return 0.0


def _print_cli_progress(percent, time_str, speed_str, label=""):
    """Print a simple CLI progress bar without ANSI colors."""
    if not sys.stderr.isatty():
        return
    bar_width = 30
    filled = int(bar_width * percent / 100)
    bar = "#" * filled + "-" * (bar_width - filled)
    prefix = f"{label} - " if label else ""
    line = f"\r{prefix}[{bar}] {percent:5.1f}% | {time_str} | {speed_str}  "
    sys.stderr.write(line)
    sys.stderr.flush()


def _run_ffmpeg_with_progress(node, overwrite_output=True, label=""):
    """Run an ffmpeg node and stream its progress output cleanly.

    Includes stall detection: if FFmpeg stops making progress (same frame/time
    values) for STALL_TIMEOUT seconds the process is killed so the caller's
    retry logic can kick in.
    """
    import queue
    import threading

    STALL_TIMEOUT = (
        600  # 10 minutes without progress → kill (must exceed reconnect_delay_max=300)
    )

    runtime_reason = ""
    debug_mode = os.getenv("ANIWORLD_DEBUG_MODE", "0") == "1"
    is_tty = sys.stderr.isatty()

    # Regex to extract progress indicators from ffmpeg status lines
    _RE_FRAME = re.compile(r"frame=\s*(\d+)")
    _RE_TIME = re.compile(r"time=(\S+)")
    _RE_SPEED = re.compile(r"speed=\s*(\S+)")
    _RE_BITRATE = re.compile(r"bitrate=\s*(\S+)")
    _RE_SIZE = re.compile(r"size=\s*(\d+(?:\.\d+)?)\s*([kKmM])(?:i)?B", re.IGNORECASE)
    _RE_DURATION = re.compile(r"Duration:\s*(\d+:\d+:\d+\.\d+)")

    # Use shorter stats_period for smoother progress (1s in non-debug, 10s in debug)
    stats_period = "10" if debug_mode else "1"

    args = ffmpeg.compile(node, overwrite_output=overwrite_output)
    if "-stats_period" not in args:
        args.insert(-1, "-stats_period")
        args.insert(-1, stats_period)

    popen_kwargs = {
        "args": args,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.PIPE,
        "universal_newlines": False,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0
        )
    else:
        popen_kwargs["start_new_session"] = True

    process = subprocess.Popen(**popen_kwargs)

    # --- reader thread: reads stderr byte-by-byte and pushes complete lines ---
    line_queue = queue.Queue()

    def _reader():
        buf = bytearray()
        while True:
            char = process.stderr.read(1)
            if not char:
                # EOF – push whatever is left
                if buf:
                    line_queue.put(buf.decode("utf-8", errors="replace").strip())
                line_queue.put(None)  # sentinel
                return
            if char in (b"\r", b"\n"):
                if buf:
                    line_queue.put(buf.decode("utf-8", errors="replace").strip())
                    buf.clear()
            else:
                buf.extend(char)

    reader_thread = threading.Thread(target=_reader, daemon=True)
    reader_thread.start()

    # --- main loop: consume lines, log them, and watch for stalls ---
    stderr_lines = []  # collect non-progress stderr lines for error reporting
    last_frame = None
    last_time = None
    last_size_kb = None
    last_size_ts = None
    last_change = time.monotonic()
    total_duration = 0.0

    started_at = time.time()
    with _ffmpeg_progress_lock:
        _ffmpeg_progress.update(
            percent=0.0,
            time="",
            speed="",
            bandwidth="",
            active=True,
            phase="downloading",
        )
        _ffmpeg_runtime.update(
            active=True,
            pid=process.pid,
            label=label or "",
            started_at=started_at,
            last_progress_at=started_at,
            stall_timeout=STALL_TIMEOUT,
            reason="",
            phase="downloading",
            _process=process,
        )

    try:
        while True:
            try:
                line_str = line_queue.get(timeout=1.0)
            except queue.Empty:
                # No new line within 1 s – just check the stall timer
                if time.monotonic() - last_change > STALL_TIMEOUT:
                    logger.warning(
                        "[FFmpeg] Stall detected – no progress for "
                        f"{STALL_TIMEOUT}s. Killing process."
                    )
                    with _ffmpeg_progress_lock:
                        _ffmpeg_runtime["reason"] = "stall timeout"
                    _kill_ffmpeg_process_tree(process)
                    break
                continue

            if line_str is None:
                # Reader thread finished (EOF)
                break

            # Log the line
            if line_str.startswith("frame=") or line_str.startswith("size="):
                # --- extract progress values ---
                cur_frame = None
                cur_time = None
                cur_time_str = ""
                cur_speed_str = ""
                cur_bitrate_str = ""
                cur_bw_str = ""
                m = _RE_FRAME.search(line_str)
                if m:
                    cur_frame = m.group(1)
                m = _RE_TIME.search(line_str)
                if m:
                    cur_time = m.group(1)
                    cur_time_str = m.group(1)
                m = _RE_SPEED.search(line_str)
                if m:
                    cur_speed_str = m.group(1)
                m = _RE_BITRATE.search(line_str)
                if m:
                    cur_bitrate_str = m.group(1)
                    if cur_bitrate_str.lower() == "n/a":
                        cur_bitrate_str = ""
                m = _RE_SIZE.search(line_str)
                if m:
                    size_val = float(m.group(1))
                    size_unit = m.group(2).lower()
                    size_kb = size_val * (1024 if size_unit == "m" else 1)
                    now = time.monotonic()
                    if last_size_kb is not None and last_size_ts is not None:
                        dt = now - last_size_ts
                        if dt > 0:
                            kb_per_sec = (size_kb - last_size_kb) / dt
                            if kb_per_sec > 0:
                                mb_per_sec = kb_per_sec / 1024
                                cur_bw_str = f"{mb_per_sec:.1f} MB/s"
                    last_size_kb = size_kb
                    last_size_ts = now

                # Compute percentage
                percent = 0.0
                if total_duration > 0 and cur_time_str:
                    elapsed = _parse_ffmpeg_time(cur_time_str)
                    percent = min((elapsed / total_duration) * 100, 100.0)

                # Update global progress for web UI
                with _ffmpeg_progress_lock:
                    prev_bw = _ffmpeg_progress.get("bandwidth", "")
                    _ffmpeg_progress.update(
                        percent=round(percent, 1),
                        time=cur_time_str,
                        speed=cur_speed_str,
                        bandwidth=cur_bw_str or prev_bw,
                        active=True,
                        phase="downloading",
                    )
                    _ffmpeg_runtime["last_progress_at"] = time.time()

                if debug_mode:
                    logger.info(f"[FFmpeg Progress] {line_str}")
                elif is_tty:
                    _print_cli_progress(percent, cur_time_str, cur_speed_str, label)

                # --- stall detection ---
                if cur_frame != last_frame or cur_time != last_time:
                    last_frame = cur_frame
                    last_time = cur_time
                    last_change = time.monotonic()
                elif time.monotonic() - last_change > STALL_TIMEOUT:
                    logger.warning(
                        "[FFmpeg] Stall detected – no progress for "
                        f"{STALL_TIMEOUT}s. Killing process."
                    )
                    with _ffmpeg_progress_lock:
                        _ffmpeg_runtime["reason"] = "stall timeout"
                    _kill_ffmpeg_process_tree(process)
                    break
            elif line_str:
                # Try to capture total duration from ffmpeg header
                if total_duration == 0.0:
                    dm = _RE_DURATION.search(line_str)
                    if dm:
                        total_duration = _parse_ffmpeg_time(dm.group(1))

                logger.debug(f"[FFmpeg] {line_str}")
                stderr_lines.append(line_str)

        # Clear the progress line in CLI
        if not debug_mode and is_tty:
            sys.stderr.write("\r" + " " * 120 + "\r")
            sys.stderr.flush()

    finally:
        with _ffmpeg_progress_lock:
            runtime_reason = _ffmpeg_runtime.get("reason") or ""
            _ffmpeg_progress.update(
                percent=0.0,
                time="",
                speed="",
                bandwidth="",
                active=False,
                phase="",
            )
            _reset_ffmpeg_runtime_state()

    reader_thread.join(timeout=5)
    process.wait()
    if process.returncode != 0:
        if runtime_reason and any(
            token in runtime_reason.lower()
            for token in ("cancel", "manual stop", "stall timeout")
        ):
            raise DownloadCancelledError(runtime_reason)
        detail = (
            "\n".join(stderr_lines[-20:])
            if stderr_lines
            else f"exit code {process.returncode}"
        )
        logger.error(f"[FFmpeg] Process failed (rc={process.returncode}):\n{detail}")
        raise RuntimeError(f"ffmpeg error (rc={process.returncode}): {detail}")


def _parse_percent_number(raw):
    cleaned = re.sub(r"[^0-9.]", "", str(raw or ""))
    if not cleaned:
        return 0.0
    try:
        return max(0.0, min(float(cleaned), 100.0))
    except (TypeError, ValueError):
        return 0.0


def _run_ytdlp_with_progress(url, output_template, headers=None, label=""):
    """Download a direct media URL via yt-dlp and surface progress through the existing runtime state."""
    import queue
    import threading

    STALL_TIMEOUT = 420
    runtime_reason = ""
    cmd = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--ignore-config",
        "--force-overwrites",
        "--no-part",
        "--newline",
        "--no-warnings",
        "--progress",
        "--progress-template",
        "download:%(progress.status)s|%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s",
        "--output",
        output_template,
        "--concurrent-fragments",
        str(_fragment_concurrency()),
        "--force-generic-extractor",
    ]

    for key, value in (headers or {}).items():
        cmd.extend(["--add-header", f"{key}:{value}"])

    cmd.append(url)

    popen_kwargs = {
        "args": cmd,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "universal_newlines": True,
        "encoding": "utf-8",
        "errors": "replace",
        "bufsize": 1,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0
        )
    else:
        popen_kwargs["start_new_session"] = True

    process = subprocess.Popen(**popen_kwargs)
    line_queue = queue.Queue()

    def _reader():
        try:
            for raw_line in process.stdout:
                line_queue.put((raw_line or "").strip())
        finally:
            line_queue.put(None)

    reader_thread = threading.Thread(target=_reader, daemon=True)
    reader_thread.start()

    started_at = time.time()
    last_change = time.monotonic()
    stderr_lines = []
    last_percent = 0.0

    with _ffmpeg_progress_lock:
        _ffmpeg_progress.update(
            percent=0.0,
            time="",
            speed="",
            bandwidth="",
            active=True,
            phase="downloading",
        )
        _ffmpeg_runtime.update(
            active=True,
            pid=process.pid,
            label=label or "",
            started_at=started_at,
            last_progress_at=started_at,
            stall_timeout=STALL_TIMEOUT,
            reason="",
            phase="downloading",
            _process=process,
        )

    try:
        while True:
            try:
                line_str = line_queue.get(timeout=1.0)
            except queue.Empty:
                if time.monotonic() - last_change > STALL_TIMEOUT:
                    logger.warning(
                        "[yt-dlp] Stall detected - no progress for "
                        f"{STALL_TIMEOUT}s. Killing process."
                    )
                    with _ffmpeg_progress_lock:
                        _ffmpeg_runtime["reason"] = "stall timeout"
                    _kill_ffmpeg_process_tree(process)
                    break
                continue

            if line_str is None:
                break

            if line_str.startswith("download:"):
                _, payload = line_str.split("download:", 1)
                parts = payload.split("|")
                status = (parts[0] if len(parts) > 0 else "").strip().lower()
                percent = _parse_percent_number(parts[1] if len(parts) > 1 else "")
                speed = (parts[2] if len(parts) > 2 else "").strip()
                eta = (parts[3] if len(parts) > 3 else "").strip()
                eta_text = ""
                if eta and eta.upper() not in {"NA", "N/A", "UNKNOWN"}:
                    eta_text = f"ETA {eta}"

                with _ffmpeg_progress_lock:
                    _ffmpeg_progress.update(
                        percent=round(percent, 1),
                        time=eta_text,
                        speed=speed,
                        bandwidth=speed,
                        active=status != "finished",
                        phase="muxing" if status == "finished" else "downloading",
                    )
                    _ffmpeg_runtime["last_progress_at"] = time.time()

                if status == "finished" or percent > last_percent:
                    last_change = time.monotonic()
                    last_percent = percent
                continue

            if line_str:
                logger.debug(f"[yt-dlp] {line_str}")
                stderr_lines.append(line_str)
    finally:
        with _ffmpeg_progress_lock:
            runtime_reason = _ffmpeg_runtime.get("reason") or ""
            _ffmpeg_progress.update(
                percent=0.0, time="", speed="", bandwidth="", active=False
            )
            _reset_ffmpeg_runtime_state()

    reader_thread.join(timeout=5)
    process.wait()
    if process.returncode != 0:
        if runtime_reason and any(
            token in runtime_reason.lower()
            for token in ("cancel", "manual stop", "stall timeout")
        ):
            raise DownloadCancelledError(runtime_reason)
        detail = (
            "\n".join(stderr_lines[-20:])
            if stderr_lines
            else f"exit code {process.returncode}"
        )
        raise RuntimeError(f"yt-dlp error (rc={process.returncode}): {detail}")


def _find_ytdlp_output(output_template):
    path = Path(output_template)
    pattern = path.name.replace("%(ext)s", "*")
    candidates = [
        candidate
        for candidate in path.parent.glob(pattern)
        if candidate.is_file()
        and not candidate.name.endswith(".part")
        and candidate.name != path.name
    ]
    if not candidates:
        if path.exists():
            return path
        return None
    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return candidates[0]


def _cleanup_ytdlp_outputs(output_template):
    path = Path(output_template)
    pattern = path.name.replace("%(ext)s", "*")
    for candidate in path.parent.glob(pattern):
        if candidate.is_file():
            try:
                candidate.unlink()
            except OSError:
                pass


def _tag_downloaded_stream(input_path, output_path, audio_code, wants_clean_video, sub_video_code):
    _set_transfer_runtime(phase="metadata", active=True)
    stream_metadata = {"metadata:s:a:0": f"language={audio_code}"}
    if (not wants_clean_video) and sub_video_code:
        stream_metadata["metadata:s:v:0"] = f"language={sub_video_code}"
    _run_ffmpeg_with_progress(
        ffmpeg.input(str(input_path)).output(
            str(output_path),
            c="copy",
            **stream_metadata,
        )
    )


def download(self):
    """Download required audio/video streams for an episode (AniWorld + s.to) with retry logic."""
    if platform.system() == "Windows":
        manager = DependencyManager()
        manager.fetch_binary("ffmpeg")

    max_retries = 3
    attempt = 0

    while attempt < max_retries:
        try:
            attempt += 1
            check = check_downloaded(self._episode_path)

            headers = PROVIDER_HEADERS_D.get(self.selected_provider, {})
            input_kwargs = {
                "reconnect": 1,
                "reconnect_streamed": 1,
                "reconnect_delay_max": 300,  # wait up to 5 min for connection recovery
            }
            if headers:
                header_list = [f"{k}: {v}" for k, v in headers.items()]
                input_kwargs["headers"] = "\r\n".join(header_list) + "\r\n"

            url = (getattr(self, "url", "") or "").lower()
            is_serienstream = ("serienstream.to" in url) or ("s.to" in url)

            if is_serienstream and hasattr(self, "_normalize_language"):
                audio_enum, sub_enum = self._normalize_language(self.selected_language)
                audio_code = {"German": "deu", "English": "eng"}.get(
                    getattr(audio_enum, "value", None)
                )
                if not audio_code:
                    raise ValueError(
                        f"Unsupported audio language for serienstream.to: {audio_enum}"
                    )
                wants_clean_video = True
                sub_video_code = None
            else:
                selected_key = INVERSE_LANG_LABELS[self.selected_language]
                audio_enum, sub_enum = LANG_KEY_MAP[selected_key]

                audio_code = LANG_CODE_MAP[audio_enum]
                wants_clean_video = sub_enum == Subtitles.NONE
                sub_video_code = None if wants_clean_video else LANG_CODE_MAP[sub_enum]

            has_video = bool(check["video_langs"])
            has_audio = audio_code in check["audio_langs"]

            need_audio = not has_audio
            if not has_video:
                need_video = True
            elif not wants_clean_video:
                need_video = sub_video_code not in check["video_langs"]
            else:
                need_video = False

            if not need_audio and not need_video:
                logger.debug(f"[SKIPPED] {self._file_name}")
                return

            os.makedirs(self._folder_path, exist_ok=True)

            # Label for CLI progress bar (e.g. "Title S01E001")
            ep_label = os.path.splitext(self._file_name)[0] if self._file_name else ""

            full_stream_needed = need_audio and need_video
            provider_name = str(getattr(self, "selected_provider", "") or "")
            engine_order, engine_mode = _engine_attempt_order(
                provider_name,
                full_stream_needed,
            )
            if not _yt_dlp_available():
                engine_order = [engine for engine in engine_order if engine != "ytdlp"]
            if not engine_order:
                engine_order = ["ffmpeg"]
            engine_choice = engine_order[min(attempt - 1, len(engine_order) - 1)]
            use_ytdlp = full_stream_needed and engine_choice == "ytdlp"
            stream_host = ""
            try:
                from urllib.parse import urlparse

                stream_host = urlparse(str(self.stream_url or "")).netloc
            except Exception:
                stream_host = ""
            _set_transfer_runtime(
                engine=engine_choice,
                host=stream_host,
                mode=engine_mode,
                profile=_download_speed_profile(),
                phase="preflight" if _preflight_check_enabled() else "downloading",
                active=True,
            )

            temp_audio = self._episode_path.with_suffix(".temp_audio.mkv")
            temp_video = self._episode_path.with_suffix(".temp_video.mkv")
            temp_full = self._episode_path.with_suffix(".temp_full.mkv")
            temp_ytdlp_template = str(self._episode_path.with_suffix(".temp_ytdlp.%(ext)s"))

            if full_stream_needed:
                logger.debug(
                    "[DOWNLOADING] full preset (audio + video together) via %s",
                    "yt-dlp" if use_ytdlp else "ffmpeg",
                )

                if use_ytdlp:
                    raw_temp = None
                    try:
                        _run_ytdlp_with_progress(
                            self.stream_url,
                            temp_ytdlp_template,
                            headers=headers,
                            label=ep_label,
                        )
                        raw_temp = _find_ytdlp_output(temp_ytdlp_template)
                        if not raw_temp or not raw_temp.exists():
                            raise RuntimeError("yt-dlp finished without creating an output file")
                        _tag_downloaded_stream(
                            raw_temp,
                            temp_full,
                            audio_code,
                            wants_clean_video,
                            sub_video_code,
                        )
                    finally:
                        _cleanup_ytdlp_outputs(temp_ytdlp_template)
                else:
                    stream_metadata = {"metadata:s:a:0": f"language={audio_code}"}
                    if (not wants_clean_video) and sub_video_code:
                        stream_metadata["metadata:s:v:0"] = f"language={sub_video_code}"
                    bandwidth_kwargs = _bandwidth_limit_output_kwargs()

                    video_codec = get_video_codec()
                    _run_ffmpeg_with_progress(
                        ffmpeg.input(self.stream_url, **input_kwargs).output(
                            str(temp_full),
                            vcodec=video_codec,
                            acodec=video_codec,
                            **stream_metadata,
                            **bandwidth_kwargs,
                        ),
                        label=ep_label,
                    )

                if self._episode_path.exists():
                    _set_transfer_runtime(phase="muxing", active=True)
                    inputs = [
                        ffmpeg.input(str(self._episode_path)),
                        ffmpeg.input(str(temp_full)),
                    ]
                    output_path = self._episode_path.with_suffix(".new.mkv")
                    _run_ffmpeg_with_progress(
                        ffmpeg.output(*inputs, str(output_path), c="copy")
                    )
                    os.replace(output_path, self._episode_path)
                else:
                    os.replace(temp_full, self._episode_path)

                if temp_full.exists():
                    temp_full.unlink()
                return

            if need_audio:
                logger.debug("[DOWNLOADING] audio stream")
                _set_transfer_runtime(engine="ffmpeg", phase="audio", active=True)
                video_codec = get_video_codec()
                bandwidth_kwargs = _bandwidth_limit_output_kwargs()
                _run_ffmpeg_with_progress(
                    ffmpeg.input(self.stream_url, **input_kwargs).output(
                        str(temp_audio),
                        acodec=video_codec,
                        map="0:a:0?",
                        **{"metadata:s:a:0": f"language={audio_code}"},
                        **bandwidth_kwargs,
                    ),
                    label=ep_label,
                )

            if need_video:
                logger.debug("[DOWNLOADING] video stream")
                _set_transfer_runtime(engine="ffmpeg", phase="video", active=True)
                video_codec = get_video_codec()
                bandwidth_kwargs = _bandwidth_limit_output_kwargs()
                _run_ffmpeg_with_progress(
                    ffmpeg.input(self.stream_url, **input_kwargs).output(
                        str(temp_video),
                        vcodec=video_codec,
                        map="0:v:0?",
                        **(
                            {}
                            if wants_clean_video
                            else {"metadata:s:v:0": f"language={sub_video_code}"}
                        ),
                        **bandwidth_kwargs,
                    ),
                    label=ep_label,
                )

            logger.debug("[MUXING] combining streams")
            _set_transfer_runtime(engine="ffmpeg", phase="muxing", active=True)
            inputs = (
                [ffmpeg.input(str(self._episode_path))]
                if self._episode_path.exists()
                else []
            )

            if need_audio:
                inputs.append(ffmpeg.input(str(temp_audio)))
            if need_video:
                inputs.append(ffmpeg.input(str(temp_video)))

            output_path = self._episode_path.with_suffix(".new.mkv")
            _run_ffmpeg_with_progress(
                ffmpeg.output(*inputs, str(output_path), c="copy")
            )
            os.replace(output_path, self._episode_path)

            for f in (temp_audio, temp_video):
                if f.exists():
                    f.unlink()

            # If download succeeds, exit loop
            break

        except DownloadCancelledError:
            # Intentional stops must not fall into the normal retry loop.
            for suffix in (
                ".temp_full.mkv",
                ".temp_audio.mkv",
                ".temp_video.mkv",
                ".new.mkv",
            ):
                temp = self._episode_path.with_suffix(suffix)
                if temp.exists():
                    temp.unlink()
            _cleanup_ytdlp_outputs(temp_ytdlp_template)
            raise

        except Exception as e:
            # Clean up temp files from failed attempt
            for suffix in (
                ".temp_full.mkv",
                ".temp_audio.mkv",
                ".temp_video.mkv",
                ".new.mkv",
            ):
                temp = self._episode_path.with_suffix(suffix)
                if temp.exists():
                    temp.unlink()
            _cleanup_ytdlp_outputs(temp_ytdlp_template)

            logger.error(f"Download attempt {attempt}/{max_retries} failed: {e}")
            if attempt >= max_retries:
                _remove_empty_dirs(self._folder_path, self._base_folder)
                raise
            else:
                # Reset cached URL properties so retry resolves fresh URLs
                for attr in list(vars(self)):
                    if attr.endswith("__redirect_url") or attr.endswith(
                        "__provider_url"
                    ):
                        setattr(self, attr, None)
                logger.debug("Retrying download...")


def watch(self):
    """Watch the current episode with provider headers."""

    print(f"[WATCHING] {self._file_name}")

    headers = PROVIDER_HEADERS_W.get(self.selected_provider, {})
    cmd = [str(get_player_path()), self.stream_url]

    # AniSkip: AniWorld only; ignore for s.to
    aniskip_enabled = os.getenv("ANIWORLD_ANISKIP", "0") == "1"
    if aniskip_enabled and hasattr(self, "skip_times"):
        skip_times = self.skip_times
    else:
        skip_times = None

    if skip_times:
        from ...aniskip import build_mpv_flags, setup_aniskip

        setup_aniskip()
        skip_flags = build_mpv_flags(skip_times).split()
        cmd.extend(skip_flags)
        logger.debug(f"[SKIP TIMES FOUND]: {skip_flags}")

    cmd.extend(
        ["--no-ytdl", "--fs", "--quiet", f"--force-media-title={self._file_name}"]
    )

    if headers:
        header_args = [f"{k}: {v}" for k, v in headers.items()]
        cmd.append("--http-header-fields=" + ",".join(header_args))

    print(" ".join(cmd))
    subprocess.run(cmd)


def syncplay(self):
    """Syncplay an episode (AniWorld + s.to)."""

    print(f"[Syncplaying] {self._file_name}")

    # TODO: implement IINA support for syncplay (Syncplay may not detect IINA binary reliably)
    # Force mpv for now (get_player_path() reads this env var)
    os.environ["ANIWORLD_USE_IINA"] = "0"

    syncplay_host = os.getenv("ANIWORLD_SYNCPLAY_HOST") or "syncplay.pl:8998"
    syncplay_password = os.getenv("ANIWORLD_SYNCPLAY_PASSWORD")

    # getpass.getuser() is usually fine, but can fail in some environments
    syncplay_username = os.getenv("ANIWORLD_SYNCPLAY_USERNAME")

    if not syncplay_username:
        try:
            syncplay_username = getpass.getuser()
        except Exception:
            syncplay_username = "AniWorld-Downloader"

    room = "AniWorld"
    file_name = self._file_name.replace(" ", "_")

    if syncplay_password:
        # Log what we're using to derive the room (helps debugging)
        logger.debug(f"{room}-{file_name}-{syncplay_password}")
        room += (
            "-"
            + hashlib.sha256(
                f"-{file_name}-{syncplay_password}".encode("utf-8")
            ).hexdigest()
        )
    else:
        logger.debug(f"{room}-{file_name}")
        room += f"-{file_name}"

    syncplay_room = os.getenv("ANIWORLD_SYNCPLAY_ROOM") or room

    logger.debug(room)

    cmd = [
        str(get_syncplay_path()),
        "--no-gui",
        "--no-store",
        "--host",
        syncplay_host,
        "--room",
        syncplay_room,
        "--name",
        syncplay_username,
        "--player-path",
        str(get_player_path()),
        self.stream_url,
        # "/Users/phoenixthrush/Downloads/Caramelldansen.webm",
    ]

    # MPV flags come after this
    cmd.append("--")

    aniskip_enabled = os.getenv("ANIWORLD_ANISKIP", "0") == "1"
    skip_times = self.skip_times if aniskip_enabled else None

    if skip_times:
        from ...aniskip import build_mpv_flags, setup_aniskip

        setup_aniskip()
        skip_flags = build_mpv_flags(skip_times).split()
        cmd.extend(skip_flags)
        logger.debug(f"[SKIP TIMES FOUND]: {skip_flags}")

    cmd.extend(
        ["--no-ytdl", "--fs", "--quiet", f"--force-media-title={self._file_name}"]
    )

    headers = PROVIDER_HEADERS_W.get(self.selected_provider, {})

    if headers:
        header_args = [f"{k}: {v}" for k, v in headers.items()]
        cmd.append("--http-header-fields=" + ",".join(header_args))

    logger.debug("\n" + shlex.join(cmd))
    subprocess.run(cmd)


if __name__ == "__main__":
    from aniworld.models import AniworldEpisode

    ep = AniworldEpisode(
        "https://aniworld.to/anime/stream/highschool-dxd/staffel-1/episode-1"
    )

    ep.syncplay()
