import copy
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from collections import deque
from importlib.metadata import distribution
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import (
    Flask,
    Response,
    send_file,
    jsonify,
    redirect,
    render_template,
    request,
    stream_with_context,
    url_for,
)
from flask_wtf.csrf import CSRFProtect

from ..config import (
    ANIWORLD_EPISODE_PATTERN,
    ANIWORLD_SEASON_PATTERN,
    ANIWORLD_SERIES_PATTERN,
    DEFAULT_USER_AGENT,
    FILMPALAST_EPISODE_PATTERN,
    GLOBAL_SESSION,
    LANG_KEY_MAP,
    LANG_LABELS,
    SERIENSTREAM_EPISODE_PATTERN,
    SERIENSTREAM_SEASON_PATTERN,
    SERIENSTREAM_SERIES_PATTERN,
    SUPPORTED_PROVIDERS,
    VERSION,
    display_version,
)
from ..extractors import provider_functions
from ..logger import get_logger
from ..models.common.common import (
    get_ffmpeg_runtime_state,
    terminate_ffmpeg_process_tree,
)
from ..providers import normalize_url, resolve_provider
from ..search import (
    fetch_new_animes,
    fetch_new_episodes,
    fetch_new_series,
    fetch_popular_animes,
    fetch_popular_series,
    query_filmpalast,
    query_s_to,
    random_anime,
)
from ..search import query as aniworld_query
from .db import (
    DB_PATH,
    add_autosync_job,
    add_custom_path,
    add_favorite,
    add_to_queue,
    cancel_queue_item,
    clear_completed,
    delete_completed_queue_item,
    delete_download_history_item,
    export_app_state,
    find_autosync_by_url,
    get_activity_chart,
    get_autosync_job,
    get_autosync_jobs,
    get_custom_path_by_id,
    get_custom_paths,
    get_download_history,
    get_download_session_history,
    get_favorite,
    get_general_stats,
    get_provider_quality,
    get_provider_failure_analytics,
    get_provider_health,
    get_provider_score_history,
    get_search_suggestions,
    get_user_preference,
    get_recent_activity,
    list_audit_events,
    list_audit_users,
    list_recent_searches,
    get_recent_series_references,
    get_next_queued,
    get_queue,
    get_queue_stats,
    get_running,
    get_series_meta,
    get_sync_stats,
    init_autosync_db,
    init_custom_paths_db,
    init_favorites_db,
    init_audit_log_db,
    init_provider_score_history_db,
    init_queue_db,
    init_search_history_db,
    init_series_meta_db,
    init_user_preferences_db,
    is_queue_cancelled,
    list_favorites,
    list_series_meta,
    move_queue_item,
    remove_autosync_job,
    remove_custom_path,
    remove_favorite,
    remove_from_queue,
    retry_failed_queue_items,
    retry_queue_item,
    record_audit_event,
    record_search_query,
    requeue_running_item,
    set_captcha_url,
    clear_captcha_url,
    set_user_preference,
    snapshot_provider_score_history,
    set_queue_status,
    touch_series_last_downloaded,
    touch_series_last_synced,
    touch_favorite,
    upsert_series_meta,
    update_autosync_job,
    update_queue_errors,
    update_queue_progress,
    import_app_state,
)

logger = get_logger(__name__)

_ENV_DOWNLOAD_PATH = "ANIWORLD_DOWNLOAD_PATH"
_ENV_LANG_SEPARATION = "ANIWORLD_LANG_SEPARATION"
_ENV_DISABLE_ENGLISH_SUB = "ANIWORLD_DISABLE_ENGLISH_SUB"
_ENV_SYNC_SCHEDULE = "ANIWORLD_SYNC_SCHEDULE"
_ENV_SYNC_LANGUAGE = "ANIWORLD_SYNC_LANGUAGE"
_ENV_SYNC_PROVIDER = "ANIWORLD_SYNC_PROVIDER"
_ENV_EXPERIMENTAL_FILMPALAST = "ANIWORLD_EXPERIMENTAL_FILMPALAST"
_ENV_BANDWIDTH_LIMIT = "ANIWORLD_BANDWIDTH_LIMIT_KBPS"
_ENV_PROVIDER_FALLBACK_ORDER = "ANIWORLD_PROVIDER_FALLBACK_ORDER"
_ENV_DISK_WARN_GB = "ANIWORLD_DISK_WARN_GB"
_ENV_DISK_WARN_PERCENT = "ANIWORLD_DISK_WARN_PERCENT"
_ENV_LIBRARY_AUTO_REPAIR = "ANIWORLD_LIBRARY_AUTO_REPAIR"
_ENV_EXPERIMENTAL_SELF_HEAL = "ANIWORLD_EXPERIMENTAL_SELF_HEAL"
_ENV_SAFE_MODE = "ANIWORLD_SAFE_MODE"
_ENV_DOWNLOAD_BACKEND = "ANIWORLD_DOWNLOAD_BACKEND"
_ENV_DOWNLOAD_ENGINE_RULES = "ANIWORLD_DOWNLOAD_ENGINE_RULES"
_ENV_DOWNLOAD_SPEED_PROFILE = "ANIWORLD_DOWNLOAD_SPEED_PROFILE"
_ENV_AUTO_PROVIDER_SWITCH = "ANIWORLD_AUTO_PROVIDER_SWITCH"
_ENV_RATE_LIMIT_GUARD = "ANIWORLD_RATE_LIMIT_GUARD"
_ENV_PREFLIGHT_CHECK = "ANIWORLD_PREFLIGHT_CHECK"
_ENV_MP4_FALLBACK_REMUX = "ANIWORLD_MP4_FALLBACK_REMUX"
_ENV_UPDATE_REMOTE_URL = "ANIWORLD_UPDATE_REMOTE_URL"
_ENV_UPDATE_REMOTE_BRANCH = "ANIWORLD_UPDATE_REMOTE_BRANCH"
_ENV_UPDATE_LOCAL_COMMIT = "ANIWORLD_UPDATE_LOCAL_COMMIT"
_ENV_DOCKER_REDEPLOY_CMD = "ANIWORLD_DOCKER_REDEPLOY_CMD"
_DEFAULT_FORK_REMOTE_URL = (
    "https://github.com/easycrashx-nex/AniWorld-Downloader-v1-crashx.git"
)

_AUTO_UPDATE_IDLE_SECONDS = 20 * 60
_AUTO_UPDATE_LOOP_SECONDS = 60
_AUTO_UPDATE_REMOTE_CHECK_SECONDS = 15 * 60


def _experimental_flags():
    return {
        "filmpalast": os.environ.get(_ENV_EXPERIMENTAL_FILMPALAST, "0") == "1"
    }


def _cache_scope_token(username):
    value = (username or "").strip()
    return value or "__anon__"


def _set_bool_env(name, enabled):
    os.environ[name] = "1" if enabled else "0"


def _global_pref(key, default=None):
    return get_user_preference("", key, default)


def _set_global_pref(key, value):
    set_user_preference("", key, value)


def _safe_mode_enabled():
    return os.environ.get(_ENV_SAFE_MODE, "0") == "1"


def _resolved_download_path_value():
    raw = os.environ.get(_ENV_DOWNLOAD_PATH, "")
    if raw:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = Path.home() / path
        return str(path)
    return str(Path.home() / "Downloads")


def _discover_local_ipv4_addresses():
    addresses = {"127.0.0.1"}

    try:
        hostname = socket.gethostname()
        for result in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = result[4][0]
            if ip and not ip.startswith("169.254."):
                addresses.add(ip)
    except OSError:
        pass

    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        ip = probe.getsockname()[0]
        if ip and not ip.startswith("169.254."):
            addresses.add(ip)
    except OSError:
        pass
    finally:
        try:
            probe.close()
        except Exception:
            pass

    return sorted(addresses)


def _run_network_command(*commands):
    for command in commands:
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
        except Exception:
            continue
        output = (completed.stdout or "").strip()
        if output:
            return output
    return ""


def _discover_interface_addresses():
    interfaces = []
    seen = set()
    system = platform.system().lower()

    def _store(name, address):
        interface = str(name or "").strip()
        ip = str(address or "").strip()
        if not interface or not ip or ip.startswith("127.") or ip.startswith("169.254."):
            return
        key = (interface.lower(), ip)
        if key in seen:
            return
        seen.add(key)
        interfaces.append({"name": interface, "ip": ip})

    if system in {"linux", "darwin"}:
        output = _run_network_command(
            ["ip", "-o", "-4", "addr", "show", "up"],
            ["ifconfig"],
        )
        for line in output.splitlines():
            if " inet " in line and system == "linux":
                parts = line.split()
                if len(parts) >= 4:
                    _store(parts[1], parts[3].split("/")[0])
            elif system == "darwin":
                match = re.search(r"^([A-Za-z0-9_.:-]+):", line)
                inet = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+)", line)
                if match and inet:
                    _store(match.group(1), inet.group(1))
    elif system == "windows":
        output = _run_network_command(["ipconfig"])
        current_name = None
        for line in output.splitlines():
            adapter = re.match(r"^[A-Za-z].*adapter (.+):$", line.strip())
            if adapter:
                current_name = adapter.group(1)
                continue
            inet = re.search(r"IPv4[^:]*:\s*(\d+\.\d+\.\d+\.\d+)", line)
            if current_name and inet:
                _store(current_name, inet.group(1))
    return interfaces


def _discover_public_ip():
    cached = _cache_get("network:public_ip", 300)
    if cached is not None:
        return cached

    providers = [
        ("https://api.ipify.org?format=json", "ipify"),
        ("https://ifconfig.me/all.json", "ifconfig.me"),
    ]
    for url, source in providers:
        try:
            request = Request(url, headers={"User-Agent": "AniWorldDownloader/5.0"})
            with urlopen(request, timeout=3) as response:
                body = response.read().decode("utf-8", errors="ignore")
            payload = json.loads(body)
            ip = str(payload.get("ip") or payload.get("ip_addr") or "").strip()
            if ip:
                value = {"ip": ip, "source": source}
                _cache_set("network:public_ip", value)
                return value
        except Exception:
            continue

    fallback = {"ip": None, "source": None}
    _cache_set("network:public_ip", fallback)
    return fallback


def _detect_vpn_status():
    cached = _cache_get("network:vpn_status", 120)
    if cached is not None:
        return cached

    interfaces = _discover_interface_addresses()
    vpn_markers = {
        "gluetun": "Gluetun",
        "wg": "WireGuard",
        "wireguard": "WireGuard",
        "tun": "OpenVPN / Tunnel",
        "tap": "OpenVPN / Tunnel",
        "tailscale": "Tailscale",
        "ts": "Tailscale",
        "nordlynx": "NordLynx",
        "mullvad": "Mullvad",
        "proton": "Proton VPN",
        "ivpn": "IVPN",
        "ppp": "PPP VPN",
    }
    vpn_interfaces = []
    vpn_clients = set()
    for item in interfaces:
        name_lower = item["name"].lower()
        for marker, client_name in vpn_markers.items():
            if name_lower.startswith(marker) or marker in name_lower:
                vpn_interfaces.append(item)
                vpn_clients.add(client_name)
                break

    env = os.environ
    gluetun_keys = [
        "VPN_SERVICE_PROVIDER",
        "VPN_TYPE",
        "SERVER_COUNTRIES",
        "GLUETUN_HTTP_CONTROL_SERVER_ADDRESS",
        "DOT",
    ]
    gluetun_present = any(key in env for key in gluetun_keys) or "gluetun" in str(
        env.get("HOSTNAME", "")
    ).lower()
    provider_label = None
    if gluetun_present:
        vpn_clients.add("Gluetun")
        service_provider = str(env.get("VPN_SERVICE_PROVIDER") or "").strip()
        vpn_type = str(env.get("VPN_TYPE") or "").strip()
        provider_label = "Gluetun"
        if service_provider and vpn_type:
            provider_label = f"Gluetun · {service_provider} ({vpn_type})"
        elif service_provider:
            provider_label = f"Gluetun · {service_provider}"
        elif vpn_type:
            provider_label = f"Gluetun · {vpn_type}"

    public_ip = _discover_public_ip()
    detected = bool(vpn_interfaces) or gluetun_present
    result = {
        "detected": detected,
        "mode": "VPN / tunnel" if detected else "Direct / local",
        "provider": provider_label or (sorted(vpn_clients)[0] if vpn_clients else "Direct"),
        "clients": sorted(vpn_clients),
        "interfaces": vpn_interfaces,
        "ips": [item["ip"] for item in vpn_interfaces],
        "public_ip": public_ip.get("ip"),
        "public_ip_source": public_ip.get("source"),
    }
    _cache_set("network:vpn_status", result)
    return result


def _server_network_info(app):
    host = str(app.config.get("WEB_HOST", "127.0.0.1")).strip() or "127.0.0.1"
    port = int(app.config.get("WEB_PORT", 8080))
    is_local_only = host in {"127.0.0.1", "localhost"}
    is_wildcard = host in {"0.0.0.0", "::"}

    if is_local_only:
        ip_addresses = []
        access_urls = []
    elif is_wildcard:
        ip_addresses = [
            ip
            for ip in _discover_local_ipv4_addresses()
            if ip and not ip.startswith("127.")
        ]
        access_urls = [f"http://{ip}:{port}" for ip in ip_addresses]
    else:
        ip_addresses = (
            []
            if host.startswith("127.") or host in {"localhost", "::1"}
            else [host]
        )
        access_urls = [f"http://{host}:{port}"] if ip_addresses else []

    return {
        "server_bind_host": host,
        "server_port": port,
        "server_ips": ip_addresses,
        "server_access_urls": access_urls,
        "server_scope": "Local only" if is_local_only else "LAN / exposed",
        "vpn": _detect_vpn_status(),
    }


_update_runtime_lock = threading.Lock()
_update_runtime_state = {
    "active": False,
    "phase": "idle",
    "message": "",
    "started_at": None,
    "finished_at": None,
    "restart_required": False,
    "last_error": "",
    "last_checked_at": None,
    "requested_by": None,
}
_auto_update_worker_started = False
_download_activity_lock = threading.Lock()
_download_activity_state = {
    "last_activity_at": time.time(),
    "reason": "startup",
}


def _set_update_runtime(**kwargs):
    with _update_runtime_lock:
        _update_runtime_state.update(kwargs)


def _get_update_runtime():
    with _update_runtime_lock:
        return dict(_update_runtime_state)


def _mark_download_activity(reason="activity"):
    with _download_activity_lock:
        _download_activity_state.update(
            {
                "last_activity_at": time.time(),
                "reason": str(reason or "activity"),
            }
        )


def _get_download_activity():
    with _download_activity_lock:
        return dict(_download_activity_state)


def _downloads_busy():
    running = get_running()
    if running:
        return True
    runtime = get_ffmpeg_runtime_state()
    return bool(runtime.get("active"))


def _download_idle_seconds():
    if _downloads_busy():
        return 0
    activity = _get_download_activity()
    last_activity_at = float(activity.get("last_activity_at") or 0.0)
    if last_activity_at <= 0:
        return 0
    return max(0, int(time.time() - last_activity_at))


def _resolve_repo_root():
    candidates = []
    try:
        candidates.append(Path(__file__).resolve().parents[3])
    except Exception:
        pass
    try:
        candidates.append(Path.cwd())
    except Exception:
        pass

    seen = set()
    for candidate in candidates:
        if not candidate:
            continue
        try:
            resolved = candidate.resolve()
        except Exception:
            resolved = candidate
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        if (resolved / ".git").exists():
            return resolved
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=str(resolved),
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return Path(result.stdout.strip())
        except Exception:
            continue
    return None


def _inside_docker():
    if str(os.environ.get("container") or "").strip().lower() in {
        "docker",
        "podman",
        "containerd",
    }:
        return True
    for marker in (Path("/.dockerenv"), Path("/run/.containerenv")):
        try:
            if marker.exists():
                return True
        except Exception:
            continue
    try:
        cgroup = Path("/proc/1/cgroup")
        if cgroup.exists():
            text = cgroup.read_text(encoding="utf-8", errors="ignore").lower()
            if any(token in text for token in ("docker", "kubepods", "containerd", "podman")):
                return True
    except Exception:
        pass
    return False


def _read_installed_direct_url():
    try:
        dist = distribution("aniworld")
        text = dist.read_text("direct_url.json")
        if text:
            return json.loads(text)
    except Exception:
        return None
    return None


def _run_command(args, cwd=None, timeout=30):
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "code": int(result.returncode),
        "stdout": (result.stdout or "").strip(),
        "stderr": (result.stderr or "").strip(),
    }


def _run_git_command(args, cwd, timeout=30):
    return _run_command(args, cwd=cwd, timeout=timeout)


def _normalize_git_remote_url(value):
    url = str(value or "").strip()
    if url.startswith("git+"):
        url = url[4:]
    return url


def _resolve_remote_git_commit(remote_url, ref=None):
    clean_url = _normalize_git_remote_url(remote_url)
    if not clean_url:
        return "", "No remote repository URL was configured."

    refs = []
    requested_ref = str(ref or "").strip()
    if requested_ref:
        refs.append(requested_ref)
    refs.append("HEAD")

    last_error = ""
    seen = set()
    for candidate in refs:
        if candidate in seen:
            continue
        seen.add(candidate)
        result = _run_command(
            ["git", "ls-remote", clean_url, candidate],
            timeout=25,
        )
        if result["code"] == 0 and result["stdout"]:
            return result["stdout"].split()[0].strip(), ""
        last_error = result["stderr"] or result["stdout"] or "Could not check the remote repository."
    return "", last_error


def _build_pip_git_spec(remote_url, revision=None):
    clean_url = str(remote_url or "").strip()
    if not clean_url:
        return ""
    spec = clean_url if clean_url.startswith("git+") else f"git+{clean_url}"
    requested_revision = str(revision or "").strip()
    if requested_revision:
        spec = f"{spec}@{requested_revision}"
    if "#egg=" not in spec:
        spec = f"{spec}#egg=aniworld"
    return spec


def _docker_redeploy_command(repo_root=None):
    configured = str(os.environ.get(_ENV_DOCKER_REDEPLOY_CMD) or "").strip()
    if configured:
        return configured
    candidate_root = None
    try:
        candidate_root = Path(repo_root).resolve() if repo_root else None
    except Exception:
        candidate_root = None
    compose_names = ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml")
    if candidate_root and any((candidate_root / name).exists() for name in compose_names):
        return "docker compose up -d --build"
    return "Redeploy the container image from your Docker host or container platform."


def _remote_update_snapshot(
    *,
    install_mode,
    install_label,
    remote_url,
    branch,
    local_commit,
    repo_root="",
    dirty=False,
    supports_apply=False,
    supports_auto_update=False,
    apply_strategy="manual",
    action_label="Update Now",
    action_hint="",
    manual_command="",
    pip_upgrade_spec="",
):
    clean_remote = _normalize_git_remote_url(remote_url)
    clean_local = str(local_commit or "").strip()
    clean_branch = str(branch or "").strip() or "main"

    if not clean_remote:
        return {
            "supported": False,
            "install_mode": install_mode,
            "install_label": install_label,
            "repo_root": str(repo_root or ""),
            "reason": "No remote update source could be detected for this installation.",
            "supports_apply": False,
            "supports_auto_update": False,
            "apply_strategy": "manual",
            "action_label": action_label,
            "action_hint": action_hint,
            "manual_action_available": bool(manual_command),
            "manual_command": manual_command,
            "checked_at": int(time.time()),
        }

    if not clean_local:
        return {
            "supported": False,
            "install_mode": install_mode,
            "install_label": install_label,
            "repo_root": str(repo_root or ""),
            "remote_url": clean_remote,
            "branch": clean_branch,
            "reason": "The current local commit is unknown, so update checks are unavailable.",
            "supports_apply": False,
            "supports_auto_update": False,
            "apply_strategy": "manual",
            "action_label": action_label,
            "action_hint": action_hint,
            "manual_action_available": bool(manual_command),
            "manual_command": manual_command,
            "checked_at": int(time.time()),
        }

    remote_hash, remote_error = _resolve_remote_git_commit(clean_remote, clean_branch)
    snapshot = {
        "supported": True,
        "install_mode": install_mode,
        "install_label": install_label,
        "repo_root": str(repo_root or ""),
        "branch": clean_branch,
        "remote_url": clean_remote,
        "local_commit": clean_local,
        "remote_commit": remote_hash,
        "local_short": clean_local[:7],
        "remote_short": remote_hash[:7],
        "dirty": bool(dirty),
        "update_available": bool(remote_hash and remote_hash != clean_local),
        "reason": remote_error if not remote_hash else "",
        "supports_apply": bool(supports_apply),
        "supports_auto_update": bool(supports_auto_update),
        "apply_strategy": apply_strategy,
        "action_label": action_label,
        "action_hint": action_hint,
        "manual_action_available": bool(manual_command),
        "manual_command": manual_command,
        "pip_upgrade_spec": pip_upgrade_spec,
        "checked_at": int(time.time()),
    }
    return snapshot


def _git_repo_update_snapshot(repo_root):
    branch_info = _run_git_command(["git", "branch", "--show-current"], repo_root, 12)
    if branch_info["code"] != 0 or not branch_info["stdout"]:
        return {
            "supported": False,
            "install_mode": "git",
            "install_label": "Git checkout",
            "repo_root": str(repo_root),
            "reason": branch_info["stderr"] or "Could not detect the current git branch.",
            "supports_apply": False,
            "supports_auto_update": False,
            "apply_strategy": "manual",
            "action_label": "Update Now",
            "action_hint": "",
            "manual_action_available": False,
            "manual_command": "",
            "checked_at": int(time.time()),
        }

    branch = branch_info["stdout"].strip()
    local_rev = _run_git_command(["git", "rev-parse", "HEAD"], repo_root, 12)
    remote_url = _run_git_command(["git", "remote", "get-url", "origin"], repo_root, 12)
    dirty = _run_git_command(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        repo_root,
        18,
    )
    return _remote_update_snapshot(
        install_mode="git",
        install_label="Git checkout",
        remote_url=remote_url["stdout"] or "",
        branch=branch,
        local_commit=local_rev["stdout"] or "",
        repo_root=str(repo_root),
        dirty=bool(dirty["stdout"]),
        supports_apply=True,
        supports_auto_update=True,
        apply_strategy="git",
        action_label="Update Now",
        action_hint="",
    )


def _pip_vcs_update_snapshot(
    direct_url,
    *,
    install_mode="pip",
    install_label="Pip install",
    supports_apply=True,
    supports_auto_update=True,
    apply_strategy="pip_vcs",
    action_label="Update Now",
    action_hint="",
    manual_command="",
):
    vcs_info = (direct_url or {}).get("vcs_info") or {}
    remote_url = (
        (direct_url or {}).get("url")
        or os.environ.get(_ENV_UPDATE_REMOTE_URL, "")
        or _DEFAULT_FORK_REMOTE_URL
    )
    branch = (
        vcs_info.get("requested_revision")
        or os.environ.get(_ENV_UPDATE_REMOTE_BRANCH, "")
        or "main"
    )
    local_commit = (
        vcs_info.get("commit_id")
        or os.environ.get(_ENV_UPDATE_LOCAL_COMMIT, "")
    )
    return _remote_update_snapshot(
        install_mode=install_mode,
        install_label=install_label,
        remote_url=remote_url,
        branch=branch,
        local_commit=local_commit,
        supports_apply=supports_apply,
        supports_auto_update=supports_auto_update,
        apply_strategy=apply_strategy,
        action_label=action_label,
        action_hint=action_hint,
        manual_command=manual_command,
        pip_upgrade_spec=_build_pip_git_spec(remote_url, branch) if supports_apply else "",
    )


def _docker_update_snapshot(repo_root=None, direct_url=None):
    redeploy_command = _docker_redeploy_command(repo_root)
    action_hint = (
        "This downloader is running in Docker. Update it by redeploying the container image "
        "from your host after the current workload is idle."
    )

    if repo_root:
        base = _git_repo_update_snapshot(repo_root)
        base.update(
            {
                "install_mode": "docker",
                "install_label": "Docker container",
                "supports_apply": False,
                "supports_auto_update": False,
                "apply_strategy": "docker_redeploy",
                "action_label": "Redeploy",
                "action_hint": action_hint,
                "manual_action_available": True,
                "manual_command": redeploy_command,
                "dirty": False,
            }
        )
        return base

    direct = direct_url or _read_installed_direct_url()
    vcs_info = (direct or {}).get("vcs_info") or {}
    if vcs_info.get("vcs") == "git":
        return _pip_vcs_update_snapshot(
            direct,
            install_mode="docker",
            install_label="Docker container",
            supports_apply=False,
            supports_auto_update=False,
            apply_strategy="docker_redeploy",
            action_label="Redeploy",
            action_hint=action_hint,
            manual_command=redeploy_command,
        )

    remote_url = str(
        os.environ.get(_ENV_UPDATE_REMOTE_URL) or _DEFAULT_FORK_REMOTE_URL
    ).strip()
    local_commit = str(os.environ.get(_ENV_UPDATE_LOCAL_COMMIT) or "").strip()
    if remote_url and local_commit:
        return _remote_update_snapshot(
            install_mode="docker",
            install_label="Docker container",
            remote_url=remote_url,
            branch=os.environ.get(_ENV_UPDATE_REMOTE_BRANCH, "main"),
            local_commit=local_commit,
            supports_apply=False,
            supports_auto_update=False,
            apply_strategy="docker_redeploy",
            action_label="Redeploy",
            action_hint=action_hint,
            manual_command=redeploy_command,
        )

    return {
        "supported": False,
        "install_mode": "docker",
        "install_label": "Docker container",
        "repo_root": str(repo_root or ""),
        "reason": (
            "Docker was detected, but no remote update source metadata is available. "
            "Set ANIWORLD_UPDATE_REMOTE_URL and ANIWORLD_UPDATE_LOCAL_COMMIT to enable checks."
        ),
        "supports_apply": False,
        "supports_auto_update": False,
        "apply_strategy": "docker_redeploy",
        "action_label": "Redeploy",
        "action_hint": action_hint,
        "manual_action_available": True,
        "manual_command": redeploy_command,
        "checked_at": int(time.time()),
    }


def _update_source_snapshot(force=False):
    if not force:
        cached = _cache_get("system:update_status", 300)
        if cached is not None:
            return cached

    repo_root = _resolve_repo_root()
    direct_url = _read_installed_direct_url()

    if _inside_docker():
        snapshot = _docker_update_snapshot(repo_root=repo_root, direct_url=direct_url)
    elif repo_root:
        snapshot = _git_repo_update_snapshot(repo_root)
    else:
        vcs_info = (direct_url or {}).get("vcs_info") or {}
        if vcs_info.get("vcs") == "git":
            snapshot = _pip_vcs_update_snapshot(direct_url)
        else:
            snapshot = {
                "supported": False,
                "install_mode": "unknown",
                "install_label": "Unknown install",
                "reason": "No supported update source was detected for this installation.",
                "supports_apply": False,
                "supports_auto_update": False,
                "apply_strategy": "manual",
                "action_label": "Update Now",
                "action_hint": "",
                "manual_action_available": False,
                "manual_command": "",
                "checked_at": int(time.time()),
            }
    _cache_set("system:update_status", snapshot)
    return snapshot


def _update_status_payload(force=False, can_manage=False):
    snapshot = _update_source_snapshot(force=force)
    runtime = _get_update_runtime()
    payload = dict(snapshot)
    payload.update(
        {
            "active": bool(runtime.get("active")),
            "phase": runtime.get("phase") or "idle",
            "message": runtime.get("message") or "",
            "started_at": runtime.get("started_at"),
            "finished_at": runtime.get("finished_at"),
            "restart_required": bool(runtime.get("restart_required")),
            "last_error": runtime.get("last_error") or "",
            "last_checked_at": runtime.get("last_checked_at"),
            "requested_by": runtime.get("requested_by"),
            "can_manage": bool(can_manage),
            "can_apply": bool(can_manage and snapshot.get("supports_apply")),
            "action_available": bool(
                can_manage
                and (
                    snapshot.get("supports_apply")
                    or snapshot.get("manual_action_available")
                )
            ),
            "auto_update_enabled": _normalize_pref_bool(
                _global_pref("auto_update_enabled", "0")
            )
            == "1",
            "downloads_busy": _downloads_busy(),
            "download_idle_seconds": _download_idle_seconds(),
            "auto_update_idle_seconds": _AUTO_UPDATE_IDLE_SECONDS,
        }
    )
    return payload


def _run_update_worker(requested_by=None):
    try:
        _set_update_runtime(
            active=True,
            phase="checking",
            message="Checking repository state...",
            started_at=int(time.time()),
            finished_at=None,
            restart_required=False,
            last_error="",
            last_checked_at=int(time.time()),
            requested_by=requested_by,
        )

        snapshot = _update_source_snapshot(force=True)
        repo_root = snapshot.get("repo_root")
        if not snapshot.get("supported"):
            raise RuntimeError(snapshot.get("reason") or "Updates are not available here.")
        if not snapshot.get("supports_apply"):
            raise RuntimeError(
                snapshot.get("action_hint")
                or "This installation must be updated outside the web UI."
            )
        if snapshot.get("dirty"):
            raise RuntimeError(
                "The git worktree has local changes. Commit or stash them before using the updater."
            )

        python_exe = sys.executable or ""
        if snapshot.get("apply_strategy") == "git":
            if not repo_root:
                raise RuntimeError("The git repository root is unavailable for this installation.")
            branch = snapshot.get("branch") or "main"
            _set_update_runtime(
                phase="fetching",
                message=f"Fetching latest changes from origin/{branch}...",
                last_checked_at=int(time.time()),
            )
            fetch_result = _run_git_command(
                ["git", "fetch", "--quiet", "origin", branch],
                repo_root,
                120,
            )
            if fetch_result["code"] != 0:
                raise RuntimeError(fetch_result["stderr"] or "git fetch failed")

            snapshot = _update_source_snapshot(force=True)
            if not snapshot.get("update_available"):
                _set_update_runtime(
                    active=False,
                    phase="done",
                    message="Already on the latest GitHub version.",
                    finished_at=int(time.time()),
                    last_checked_at=int(time.time()),
                )
                return

            _set_update_runtime(
                phase="pulling",
                message="Downloading and applying the update...",
            )
            pull_result = _run_git_command(
                ["git", "pull", "--ff-only", "origin", branch],
                repo_root,
                180,
            )
            if pull_result["code"] != 0:
                raise RuntimeError(pull_result["stderr"] or "git pull failed")

            if python_exe:
                _set_update_runtime(
                    phase="installing",
                    message="Refreshing the Python installation...",
                )
                pip_result = subprocess.run(
                    [python_exe, "-m", "pip", "install", "-e", str(repo_root)],
                    cwd=str(repo_root),
                    capture_output=True,
                    text=True,
                    timeout=240,
                    check=False,
                )
                if pip_result.returncode != 0:
                    raise RuntimeError(
                        (pip_result.stderr or pip_result.stdout or "pip install failed").strip()
                    )
        elif snapshot.get("apply_strategy") == "pip_vcs":
            if not python_exe:
                raise RuntimeError("Python executable not available for pip upgrade.")
            pip_upgrade_spec = str(snapshot.get("pip_upgrade_spec") or "").strip()
            if not pip_upgrade_spec:
                raise RuntimeError("No pip upgrade source was detected for this installation.")
            _set_update_runtime(
                phase="installing",
                message="Downloading and installing the updated package...",
                last_checked_at=int(time.time()),
            )
            pip_result = subprocess.run(
                [python_exe, "-m", "pip", "install", "--upgrade", pip_upgrade_spec],
                cwd=str(repo_root) if repo_root else None,
                capture_output=True,
                text=True,
                timeout=240,
                check=False,
            )
            if pip_result.returncode != 0:
                raise RuntimeError(
                    (pip_result.stderr or pip_result.stdout or "pip upgrade failed").strip()
                )
        else:
            raise RuntimeError(
                snapshot.get("action_hint")
                or "This installation cannot be updated directly from the web UI."
            )

        _update_source_snapshot(force=True)
        _set_update_runtime(
            active=False,
            phase="done",
            message="Update installed. Restart the downloader to load the new code.",
            finished_at=int(time.time()),
            restart_required=True,
            last_checked_at=int(time.time()),
        )
    except Exception as exc:
        _set_update_runtime(
            active=False,
            phase="error",
            message=str(exc),
            finished_at=int(time.time()),
            last_error=str(exc),
            last_checked_at=int(time.time()),
        )


def _start_update_worker(requested_by=None):
    runtime = _get_update_runtime()
    if runtime.get("active"):
        return False
    thread = threading.Thread(
        target=_run_update_worker,
        kwargs={"requested_by": requested_by},
        daemon=True,
        name="aniworld-git-updater",
    )
    thread.start()
    return True


def _restart_process_worker():
    time.sleep(0.8)
    python_exe = sys.executable or ""
    restart_args = [python_exe, "-m", "aniworld", *sys.argv[1:]]
    try:
        os.execv(python_exe, restart_args)
    except Exception:
        logger.exception("Could not restart downloader process via execv")
        os._exit(1)


def _start_restart_worker():
    thread = threading.Thread(
        target=_restart_process_worker,
        daemon=True,
        name="aniworld-process-restart",
    )
    thread.start()
    return True


def _auto_update_enabled():
    return _normalize_pref_bool(_global_pref("auto_update_enabled", "0")) == "1"


def _auto_update_worker():
    last_remote_probe_at = 0
    while True:
        try:
            time.sleep(_AUTO_UPDATE_LOOP_SECONDS)
            if not _auto_update_enabled():
                continue

            runtime = _get_update_runtime()
            if runtime.get("active") or runtime.get("restart_required"):
                continue

            snapshot = _update_source_snapshot(force=False)
            if not snapshot.get("supports_auto_update"):
                continue

            if _downloads_busy():
                continue

            if _download_idle_seconds() < _AUTO_UPDATE_IDLE_SECONDS:
                continue

            now = time.time()
            if now - last_remote_probe_at < _AUTO_UPDATE_REMOTE_CHECK_SECONDS:
                if not snapshot.get("update_available"):
                    continue
            else:
                snapshot = _update_source_snapshot(force=True)
                last_remote_probe_at = now

            if not snapshot.get("update_available"):
                continue

            if _start_update_worker(requested_by="auto-updater"):
                logger.info("Started automatic updater after %.0f seconds of download idle time", _download_idle_seconds())
                record_audit_event(
                    "system.update_auto_requested",
                    username="",
                    subject_type="system",
                    subject=snapshot.get("install_mode") or "auto-update",
                    details={
                        "install_mode": snapshot.get("install_mode"),
                        "branch": snapshot.get("branch"),
                        "remote_url": snapshot.get("remote_url"),
                    },
                )
        except Exception:
            logger.exception("Automatic update worker failed")


def _ensure_auto_update_worker():
    global _auto_update_worker_started
    if _auto_update_worker_started:
        return
    _auto_update_worker_started = True
    thread = threading.Thread(
        target=_auto_update_worker,
        daemon=True,
        name="aniworld-auto-update",
    )
    thread.start()


def _disk_guard_snapshot():
    from pathlib import Path

    try:
        warn_gb = float(os.environ.get(_ENV_DISK_WARN_GB, "10"))
    except ValueError:
        warn_gb = 10.0
    try:
        warn_pct = float(os.environ.get(_ENV_DISK_WARN_PERCENT, "12"))
    except ValueError:
        warn_pct = 12.0

    targets = []
    seen = set()

    def _add_target(label, path_value):
        raw_path = str(path_value or "").strip()
        if not raw_path:
            return
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = Path.home() / path
        key = str(path).lower()
        if key in seen:
            return
        seen.add(key)
        targets.append((label, path))

    _add_target("Default", _resolved_download_path_value())
    for custom_path in get_custom_paths():
        _add_target(custom_path.get("name") or "Custom", custom_path.get("path"))

    items = []
    overall = "healthy"
    for label, path in targets:
        try:
            usage = shutil.disk_usage(path)
            free_gb = round(usage.free / (1024**3), 2)
            total_gb = round(usage.total / (1024**3), 2)
            used_percent = round((usage.used / usage.total) * 100, 1) if usage.total else 0
            free_percent = round((usage.free / usage.total) * 100, 1) if usage.total else 0
            status = "healthy"
            if free_gb <= warn_gb or free_percent <= warn_pct:
                status = "warning"
                overall = "warning"
            items.append(
                {
                    "label": label,
                    "path": str(path),
                    "total_gb": total_gb,
                    "free_gb": free_gb,
                    "used_percent": used_percent,
                    "free_percent": free_percent,
                    "status": status,
                }
            )
        except Exception as exc:
            overall = "warning"
            items.append(
                {
                    "label": label,
                    "path": str(path),
                    "status": "unknown",
                    "error": str(exc),
                }
            )

    return {
        "status": overall,
        "warn_free_gb": warn_gb,
        "warn_free_percent": warn_pct,
        "paths": items,
    }


_UI_THEME_PRESETS = {
    "custom": None,
    "control": {
        "ui_mode": "compact",
        "ui_theme": "ocean",
        "ui_radius": "structured",
        "ui_motion": "fast",
        "ui_width": "wide",
        "ui_modal_width": "compact",
        "ui_nav_size": "compact",
        "ui_table_density": "compact",
        "ui_background": "grid",
    },
    "cinematic": {
        "ui_mode": "airy",
        "ui_theme": "sunset",
        "ui_radius": "round",
        "ui_motion": "slow",
        "ui_width": "wide",
        "ui_modal_width": "wide",
        "ui_nav_size": "large",
        "ui_table_density": "relaxed",
        "ui_background": "cinematic",
    },
    "frosted": {
        "ui_mode": "cozy",
        "ui_theme": "arctic",
        "ui_radius": "soft",
        "ui_motion": "normal",
        "ui_width": "standard",
        "ui_modal_width": "standard",
        "ui_nav_size": "standard",
        "ui_table_density": "standard",
        "ui_background": "frost",
    },
    "neon": {
        "ui_mode": "tight",
        "ui_theme": "electric",
        "ui_radius": "soft",
        "ui_motion": "fast",
        "ui_width": "wide",
        "ui_modal_width": "standard",
        "ui_nav_size": "compact",
        "ui_table_density": "compact",
        "ui_background": "pulse",
    },
}


def _normalize_bandwidth_limit(value):
    raw = str(value or "").strip()
    if not raw:
        return "0"
    try:
        parsed = int(float(raw))
    except (TypeError, ValueError):
        return "0"
    return str(max(0, min(parsed, 250000)))


def _normalize_provider_fallback_order(value):
    entries = []
    seen = set()
    for raw in str(value or "").split(","):
        provider = str(raw or "").strip()
        if not provider:
            continue
        lowered = provider.lower()
        match = next(
            (name for name in WORKING_PROVIDERS if name.lower() == lowered),
            None,
        )
        if not match or match in seen:
            continue
        seen.add(match)
        entries.append(match)
    return ", ".join(entries)


def _normalize_disk_guard_threshold(value, fallback, upper_bound):
    raw = str(value or "").strip()
    if not raw:
        return fallback
    try:
        parsed = float(raw)
    except (TypeError, ValueError):
        return fallback
    parsed = max(0.0, min(parsed, upper_bound))
    if parsed.is_integer():
        return str(int(parsed))
    return f"{parsed:.1f}".rstrip("0").rstrip(".")


def _normalize_smart_retry_profile(value):
    profile = str(value or "balanced").strip().lower()
    return (
        profile
        if profile in {"conservative", "balanced", "aggressive"}
        else "balanced"
    )


def _normalize_download_backend(value):
    backend = str(value or "auto").strip().lower()
    return backend if backend in {"auto", "ffmpeg", "ytdlp"} else "auto"


def _normalize_download_speed_profile(value):
    profile = str(value or "balanced").strip().lower()
    return profile if profile in {"fast", "balanced", "safe"} else "balanced"


def _normalize_engine_rules(value):
    entries = []
    seen = set()
    for raw in str(value or "").split(","):
        chunk = str(raw or "").strip()
        if not chunk or ":" not in chunk:
            continue
        provider, engine = chunk.split(":", 1)
        provider = provider.strip()
        engine = engine.strip().lower()
        match = next(
            (name for name in WORKING_PROVIDERS if name.lower() == provider.lower()),
            None,
        )
        if not match or engine not in {"ffmpeg", "ytdlp"}:
            continue
        key = f"{match}:{engine}"
        if key in seen:
            continue
        seen.add(key)
        entries.append(key)
    return ", ".join(entries)


def _download_engine_rule_map():
    rules = {}
    for chunk in _normalize_engine_rules(
        os.environ.get(_ENV_DOWNLOAD_ENGINE_RULES, "")
    ).split(","):
        entry = str(chunk or "").strip()
        if not entry or ":" not in entry:
            continue
        provider, engine = entry.split(":", 1)
        rules[provider.strip().lower()] = engine.strip().lower()
    return rules


def _download_speed_profile():
    return _normalize_download_speed_profile(
        os.environ.get(_ENV_DOWNLOAD_SPEED_PROFILE, "balanced")
    )


def _auto_provider_switch_enabled():
    return _normalize_pref_bool(os.environ.get(_ENV_AUTO_PROVIDER_SWITCH, "1")) == "1"


def _rate_limit_guard_enabled():
    return _normalize_pref_bool(os.environ.get(_ENV_RATE_LIMIT_GUARD, "1")) == "1"


def _preflight_check_enabled():
    return _normalize_pref_bool(os.environ.get(_ENV_PREFLIGHT_CHECK, "1")) == "1"


def _recommended_engine_for_provider(provider_name):
    provider = str(provider_name or "").strip()
    lowered = provider.lower()
    rules = _download_engine_rule_map()
    if lowered in rules:
        return {"engine": rules[lowered], "mode": "rule"}

    backend = _normalize_download_backend(os.environ.get(_ENV_DOWNLOAD_BACKEND, "auto"))
    if backend in {"ffmpeg", "ytdlp"}:
        return {"engine": backend, "mode": "forced"}

    profile = _download_speed_profile()
    conservative = _rate_limit_guard_enabled() or profile == "safe"
    fast_lane = {"voe", "filemoon", "vidhide"}
    safe_lane = {"vidmoly", "vidoza", "doodstream", "vidara"}
    if lowered in safe_lane and conservative:
        return {"engine": "ffmpeg", "mode": "adaptive"}
    if lowered in fast_lane or profile == "fast":
        return {"engine": "ytdlp", "mode": "adaptive"}
    return {"engine": "ffmpeg", "mode": "adaptive"}


def _normalize_ui_preset(value):
    preset = str(value or "custom").strip().lower()
    return preset if preset in _UI_THEME_PRESETS else "custom"


def _normalize_ui_locale(value):
    locale = str(value or "en").strip().lower()
    return locale if locale in {"en", "de"} else "en"


def _normalize_ui_scale(value):
    scale = str(value or "100").strip()
    return scale if scale in {"90", "95", "100", "105", "110"} else "100"


def _normalize_ui_mode(value):
    mode = str(value or "cozy").strip().lower()
    return mode if mode in {"airy", "cozy", "compact", "tight"} else "cozy"


def _normalize_ui_theme(value):
    theme = str(value or "ocean").strip().lower()
    return (
        theme
        if theme
        in {
            "ocean",
            "mint",
            "sunset",
            "rose",
            "arctic",
            "forest",
            "ember",
            "amber",
            "lavender",
            "cobalt",
            "coral",
            "mono",
            "electric",
            "berry",
            "midnight",
            "jade",
            "crimson",
            "orchid",
            "citrus",
            "steel",
            "sapphire",
            "ruby",
            "plum",
            "sand",
            "glacier",
            "emerald",
            "neon",
            "peach",
            "sky",
            "bronze",
            "pearl",
            "slate",
            "lemon",
            "aqua",
            "indigo",
            "cherry",
            "lilac",
            "copper",
            "lime",
            "azure",
            "magma",
            "blush",
            "pine",
            "violet",
        }
        else "ocean"
    )


def _normalize_ui_radius(value):
    radius = str(value or "soft").strip().lower()
    return radius if radius in {"structured", "soft", "round"} else "soft"


def _normalize_ui_motion(value):
    motion = str(value or "normal").strip().lower()
    return motion if motion in {"slow", "normal", "fast"} else "normal"


def _normalize_ui_width(value):
    width = str(value or "standard").strip().lower()
    return width if width in {"standard", "wide"} else "standard"


def _normalize_ui_modal_width(value):
    width = str(value or "standard").strip().lower()
    return width if width in {"compact", "standard", "wide"} else "standard"


def _normalize_ui_nav_size(value):
    size = str(value or "standard").strip().lower()
    return size if size in {"compact", "standard", "large"} else "standard"


def _normalize_ui_table_density(value):
    density = str(value or "standard").strip().lower()
    return density if density in {"compact", "standard", "relaxed"} else "standard"


def _normalize_ui_background(value):
    background = str(value or "dynamic").strip().lower()
    return (
        background
        if background
        in {
            "dynamic",
            "cinematic",
            "subtle",
            "minimal",
            "aurora",
            "nebula",
            "frost",
            "ember",
            "grid",
            "pulse",
            "drift",
            "storm",
            "dusk",
            "bloom",
            "off",
        }
        else "dynamic"
    )


def _normalize_pref_bool(value):
    if isinstance(value, bool):
        return "1" if value else "0"
    return (
        "1"
        if str(value or "").strip().lower() in {"1", "true", "yes", "on"}
        else "0"
    )


def _normalize_search_default_sort(value):
    sort = str(value or "source").strip().lower()
    return (
        sort
        if sort in {"source", "year-desc", "year-asc", "title-asc", "title-desc"}
        else "source"
    )


def _normalize_search_default_genres(value):
    entries = []
    seen = set()
    for raw in str(value or "").split(","):
        clean = re.sub(r"\s+", " ", raw).strip()
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        entries.append(clean[:32])
        if len(entries) >= 8:
            break
    return ", ".join(entries)


def _normalize_search_default_year(value):
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        year = int(raw)
    except (TypeError, ValueError):
        return ""
    return str(year) if 1950 <= year <= 2099 else ""


def _settings_payload(
    ui_preset="custom",
    ui_locale="en",
    ui_mode="cozy",
    ui_scale="100",
    ui_theme="ocean",
    ui_radius="soft",
    ui_motion="normal",
    ui_width="standard",
    ui_modal_width="standard",
    ui_nav_size="standard",
    ui_table_density="standard",
    ui_background="dynamic",
    search_default_sort="source",
    search_default_genres="",
    search_default_year_from="",
    search_default_year_to="",
    search_default_favorites_only="0",
    search_default_downloaded_only="0",
    browser_notifications_enabled="0",
    browser_notify_browse="1",
    browser_notify_queue="1",
    browser_notify_autosync="1",
    browser_notify_library="1",
    browser_notify_settings="1",
    browser_notify_system="1",
    auto_open_captcha_tab="0",
):
    return {
        "download_path": _resolved_download_path_value(),
        "lang_separation": os.environ.get(_ENV_LANG_SEPARATION, "0"),
        "disable_english_sub": os.environ.get(_ENV_DISABLE_ENGLISH_SUB, "0"),
        "experimental_filmpalast": os.environ.get(
            _ENV_EXPERIMENTAL_FILMPALAST, "0"
        ),
        "sync_schedule": os.environ.get(_ENV_SYNC_SCHEDULE, "0"),
        "sync_language": os.environ.get(_ENV_SYNC_LANGUAGE, "German Dub"),
        "sync_provider": os.environ.get(_ENV_SYNC_PROVIDER, "VOE"),
        "bandwidth_limit_kbps": _normalize_bandwidth_limit(
            os.environ.get(_ENV_BANDWIDTH_LIMIT, "0")
        ),
        "download_backend": _normalize_download_backend(
            os.environ.get(_ENV_DOWNLOAD_BACKEND, "auto")
        ),
        "download_engine_rules": _normalize_engine_rules(
            os.environ.get(_ENV_DOWNLOAD_ENGINE_RULES, "")
        ),
        "download_speed_profile": _normalize_download_speed_profile(
            os.environ.get(_ENV_DOWNLOAD_SPEED_PROFILE, "balanced")
        ),
        "auto_provider_switch": _normalize_pref_bool(
            os.environ.get(_ENV_AUTO_PROVIDER_SWITCH, "1")
        ),
        "rate_limit_guard": _normalize_pref_bool(
            os.environ.get(_ENV_RATE_LIMIT_GUARD, "1")
        ),
        "preflight_check": _normalize_pref_bool(
            os.environ.get(_ENV_PREFLIGHT_CHECK, "1")
        ),
        "mp4_fallback_remux": _normalize_pref_bool(
            os.environ.get(_ENV_MP4_FALLBACK_REMUX, "0")
        ),
        "provider_fallback_order": _normalize_provider_fallback_order(
            os.environ.get(_ENV_PROVIDER_FALLBACK_ORDER, "")
        ),
        "disk_warn_gb": _normalize_disk_guard_threshold(
            os.environ.get(_ENV_DISK_WARN_GB, "10"), "10", 5000
        ),
        "disk_warn_percent": _normalize_disk_guard_threshold(
            os.environ.get(_ENV_DISK_WARN_PERCENT, "12"), "12", 100
        ),
        "library_auto_repair": _normalize_pref_bool(
            os.environ.get(_ENV_LIBRARY_AUTO_REPAIR, "0")
        ),
        "experimental_self_heal": _normalize_pref_bool(
            os.environ.get(_ENV_EXPERIMENTAL_SELF_HEAL, "0")
        ),
        "safe_mode": _normalize_pref_bool(os.environ.get(_ENV_SAFE_MODE, "0")),
        "ui_preset": _normalize_ui_preset(ui_preset),
        "ui_locale": _normalize_ui_locale(ui_locale),
        "ui_mode": _normalize_ui_mode(ui_mode),
        "ui_scale": _normalize_ui_scale(ui_scale),
        "ui_theme": _normalize_ui_theme(ui_theme),
        "ui_radius": _normalize_ui_radius(ui_radius),
        "ui_motion": _normalize_ui_motion(ui_motion),
        "ui_width": _normalize_ui_width(ui_width),
        "ui_modal_width": _normalize_ui_modal_width(ui_modal_width),
        "ui_nav_size": _normalize_ui_nav_size(ui_nav_size),
        "ui_table_density": _normalize_ui_table_density(ui_table_density),
        "ui_background": _normalize_ui_background(ui_background),
        "search_default_sort": _normalize_search_default_sort(
            search_default_sort
        ),
        "search_default_genres": _normalize_search_default_genres(
            search_default_genres
        ),
        "search_default_year_from": _normalize_search_default_year(
            search_default_year_from
        ),
        "search_default_year_to": _normalize_search_default_year(
            search_default_year_to
        ),
        "search_default_favorites_only": _normalize_pref_bool(
            search_default_favorites_only
        ),
        "search_default_downloaded_only": _normalize_pref_bool(
            search_default_downloaded_only
        ),
        "browser_notifications_enabled": _normalize_pref_bool(
            browser_notifications_enabled
        ),
        "browser_notify_browse": _normalize_pref_bool(browser_notify_browse),
        "browser_notify_queue": _normalize_pref_bool(browser_notify_queue),
        "browser_notify_autosync": _normalize_pref_bool(browser_notify_autosync),
        "browser_notify_library": _normalize_pref_bool(browser_notify_library),
        "browser_notify_settings": _normalize_pref_bool(browser_notify_settings),
        "browser_notify_system": _normalize_pref_bool(browser_notify_system),
        "auto_open_captcha_tab": _normalize_pref_bool(auto_open_captcha_tab),
        "smart_retry_profile": _normalize_smart_retry_profile(
            _global_pref("smart_retry_profile", "balanced")
        ),
        "external_notifications_enabled": _normalize_pref_bool(
            _global_pref("external_notifications_enabled", "0")
        ),
        "external_notification_type": (
            _global_pref("external_notification_type", "generic") or "generic"
        ),
        "external_notification_url": _global_pref("external_notification_url", ""),
        "external_notify_queue": _normalize_pref_bool(
            _global_pref("external_notify_queue", "1")
        ),
        "external_notify_autosync": _normalize_pref_bool(
            _global_pref("external_notify_autosync", "1")
        ),
        "external_notify_library": _normalize_pref_bool(
            _global_pref("external_notify_library", "1")
        ),
        "external_notify_system": _normalize_pref_bool(
            _global_pref("external_notify_system", "1")
        ),
        "auto_update_enabled": _normalize_pref_bool(
            _global_pref("auto_update_enabled", "0")
        ),
        "disk_guard": _disk_guard_snapshot(),
    }


def _external_notification_type():
    value = str(_global_pref("external_notification_type", "generic") or "generic")
    return value if value in {"generic", "discord", "gotify", "ntfy"} else "generic"


def _external_notifications_enabled():
    return (
        not _safe_mode_enabled()
        and _normalize_pref_bool(_global_pref("external_notifications_enabled", "0"))
        == "1"
    )


def _external_notifications_url():
    return str(_global_pref("external_notification_url", "") or "").strip()


def _external_notification_allowed(category):
    normalized = str(category or "system").strip().lower()
    if normalized not in {"queue", "autosync", "library", "system"}:
        normalized = "system"
    return (
        _external_notifications_enabled()
        and _normalize_pref_bool(_global_pref(f"external_notify_{normalized}", "1"))
        == "1"
        and bool(_external_notifications_url())
    )


def _post_external_notification(title, message, category="system", details=None):
    if not _external_notification_allowed(category):
        return False

    url = _external_notifications_url()
    notification_type = _external_notification_type()
    clean_title = str(title or "AniWorld Downloader").strip()[:160]
    clean_message = str(message or "").strip()[:1500]
    payload = {
        "app": "AniWorld Downloader",
        "title": clean_title,
        "message": clean_message,
        "category": category,
        "details": details or {},
        "timestamp": int(time.time()),
    }

    try:
        if notification_type == "discord":
            body = json.dumps(
                {"content": f"**{clean_title}**\n{clean_message}"}
            ).encode("utf-8")
            headers = {"Content-Type": "application/json"}
        elif notification_type == "gotify":
            body = json.dumps(
                {"title": clean_title, "message": clean_message, "priority": 5}
            ).encode("utf-8")
            headers = {"Content-Type": "application/json"}
        elif notification_type == "ntfy":
            body = clean_message.encode("utf-8")
            headers = {
                "Title": clean_title,
                "Tags": "tv,satellite",
                "Priority": "default",
            }
        else:
            body = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json"}

        request_obj = Request(url, data=body, headers=headers, method="POST")
        with urlopen(request_obj, timeout=6) as response:
            return 200 <= int(getattr(response, "status", 200)) < 300
    except Exception as exc:
        logger.warning("External notification failed: %s", exc)
        return False


def _dispatch_external_notification(title, message, category="system", details=None):
    threading.Thread(
        target=_post_external_notification,
        args=(title, message, category, details or {}),
        daemon=True,
        name="aniworld-external-notify",
    ).start()


def _get_working_providers():
    """Return only providers whose extractors are actually implemented."""
    working = []
    for p in SUPPORTED_PROVIDERS:
        func_name = f"get_direct_link_from_{p.lower()}"
        if func_name not in provider_functions:
            continue
        try:
            provider_functions[func_name]("")
        except NotImplementedError:
            continue
        except Exception:
            working.append(p)
    return tuple(working)


WORKING_PROVIDERS = _get_working_providers()
_WORKING_PROVIDER_PREFERENCE = (
    "VOE",
    "Vidhide",
    "Vidara",
    "Filemoon",
    "Vidmoly",
    "Vidoza",
    "Doodstream",
)

# Only match series-level links: /anime/stream/<slug> (no season/episode)
_SERIES_LINK_PATTERN = re.compile(r"^/anime/stream/[a-zA-Z0-9\-]+/?$", re.IGNORECASE)

# Only match s.to series-level links: /serie/<slug> (no season/episode)
_STO_SERIES_LINK_PATTERN = re.compile(
    r"^/serie/(stream/)?[a-zA-Z0-9\-]+/?$", re.IGNORECASE
)


def _ordered_working_providers():
    ordered = []
    seen = set()
    for provider_name in _WORKING_PROVIDER_PREFERENCE:
        if provider_name in WORKING_PROVIDERS and provider_name not in seen:
            ordered.append(provider_name)
            seen.add(provider_name)
    for provider_name in WORKING_PROVIDERS:
        if provider_name not in seen:
            ordered.append(provider_name)
            seen.add(provider_name)
    return tuple(ordered)


def _normalize_title_key(value):
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _detect_site(series_url):
    url = (series_url or "").lower()
    if "filmpalast.to" in url:
        return "filmpalast"
    if "s.to" in url or "serienstream.to" in url:
        return "sto"
    return "aniworld"


def _absolute_asset_url(source_url, asset_url):
    if not asset_url:
        return None
    from urllib.parse import urljoin

    absolute_url = urljoin(source_url, asset_url)
    parsed = urlparse(absolute_url)
    host = (parsed.netloc or "").lower()
    if host in {"s.to", "serienstream.to"} and parsed.path.startswith("/media/images/"):
        return url_for("api_image_proxy", src=absolute_url)
    return absolute_url


def _image_proxy_allowed(source_url):
    if not source_url:
        return False
    try:
        parsed = urlparse(source_url)
    except Exception:
        return False
    host = (parsed.netloc or "").lower()
    return host in {"s.to", "serienstream.to"} and parsed.path.startswith("/media/images/")


def _resolve_base_path(raw_value):
    from pathlib import Path

    if raw_value:
        path = Path(raw_value).expanduser()
        if not path.is_absolute():
            path = Path.home() / path
        return path
    return Path.home() / "Downloads"


def _get_scan_targets():
    raw = os.environ.get("ANIWORLD_DOWNLOAD_PATH", "")
    default_base = _resolve_base_path(raw)
    targets = [("Default", None, default_base)]
    for cp in get_custom_paths():
        targets.append((cp["name"], cp["id"], _resolve_base_path(cp["path"])))
    return targets


def _fetch_and_cache_series_meta(series_url):
    cached = get_series_meta(series_url)
    if cached and cached.get("poster_url"):
        return cached

    try:
        prov = resolve_provider(series_url)
        target = prov.series_cls(url=series_url) if prov.series_cls else prov.episode_cls(url=series_url)
        poster = _absolute_asset_url(
            series_url,
            getattr(target, "poster_url", None) or getattr(target, "image_url", None),
        )
        data = {
            "series_url": series_url,
            "title": getattr(target, "title", None)
            or getattr(target, "title_de", None),
            "poster_url": poster,
            "description": getattr(target, "description", None),
            "release_year": str(getattr(target, "release_year", "") or ""),
            "genres": getattr(target, "genres", []) or [],
        }
        upsert_series_meta(
            series_url=series_url,
            title=data["title"],
            poster_url=data["poster_url"],
            description=data["description"],
            release_year=data["release_year"],
            genres=data["genres"],
        )
        return data
    except Exception:
        return cached


def _build_series_reference_index():
    references = {}

    def _store(
        title,
        series_url,
        poster_url=None,
        site=None,
        last_downloaded_at=None,
        last_synced_at=None,
    ):
        if not title or not series_url:
            return
        key = _normalize_title_key(title)
        if not key:
            return
        current = references.get(key)
        candidate = {
            "title": title,
            "series_url": series_url,
            "poster_url": poster_url,
            "site": site,
            "last_downloaded_at": last_downloaded_at,
            "last_synced_at": last_synced_at,
        }
        if not current or (poster_url and not current.get("poster_url")):
            references[key] = candidate

    meta_by_url = {m["series_url"]: m for m in list_series_meta()}
    for favorite in list_favorites():
        meta = meta_by_url.get(favorite["series_url"], {})
        _store(
            favorite["title"],
            favorite["series_url"],
            favorite.get("poster_url") or meta.get("poster_url"),
            favorite.get("site"),
            meta.get("last_downloaded_at"),
            meta.get("last_synced_at"),
        )
    for ref in get_recent_series_references():
        meta = meta_by_url.get(ref["series_url"], {})
        site = _detect_site(ref["series_url"])
        _store(
            ref["title"],
            ref["series_url"],
            meta.get("poster_url"),
            site,
            meta.get("last_downloaded_at"),
            meta.get("last_synced_at"),
        )
    return references


def _find_series_reference(folder_name, references):
    folder_key = _normalize_title_key(folder_name)
    if not folder_key:
        return None

    best = None
    best_len = -1
    for ref_key, ref in references.items():
        if folder_key.startswith(ref_key) or ref_key.startswith(folder_key):
            if len(ref_key) > best_len:
                best = ref
                best_len = len(ref_key)
    return best


def _scan_library_snapshot(include_meta=True):
    from pathlib import Path

    lang_sep = os.environ.get("ANIWORLD_LANG_SEPARATION", "0") == "1"
    lang_folders = ["german-dub", "english-sub", "german-sub", "english-dub"]
    ep_re = re.compile(r"S(\d{2})E(\d{2,3})", re.IGNORECASE)
    video_exts = {
        ".mkv",
        ".mp4",
        ".avi",
        ".webm",
        ".flv",
        ".mov",
        ".wmv",
        ".m4v",
        ".ts",
    }

    references = _build_series_reference_index() if include_meta else {}
    fetched_meta = 0
    fetch_limit = 8

    summary = {
        "titles": 0,
        "episodes": 0,
        "total_size": 0,
        "by_location": [],
        "by_language": [],
    }

    location_totals = {}
    language_totals = {}

    def _enrich_title(entry):
        nonlocal fetched_meta
        if not include_meta:
            entry["series_url"] = None
            entry["poster_url"] = None
            entry["site"] = None
            entry["last_downloaded_at"] = None
            entry["last_synced_at"] = None
            return entry

        ref = _find_series_reference(entry["folder"], references)
        entry["series_url"] = ref["series_url"] if ref else None
        entry["poster_url"] = ref.get("poster_url") if ref else None
        entry["site"] = ref.get("site") if ref else None
        entry["last_downloaded_at"] = ref.get("last_downloaded_at") if ref else None
        entry["last_synced_at"] = ref.get("last_synced_at") if ref else None

        if entry["series_url"] and not entry["poster_url"] and fetched_meta < fetch_limit:
            meta = _fetch_and_cache_series_meta(entry["series_url"])
            if meta and meta.get("poster_url"):
                entry["poster_url"] = meta["poster_url"]
                fetched_meta += 1

        return entry

    def _scan_base(base, lang_name=None):
        titles = {}
        if not base.is_dir():
            return []

        lang_folder_set = set(lang_folders)
        for folder in base.iterdir():
            if not folder.is_dir():
                continue
            if folder.name in lang_folder_set:
                continue

            entry = titles.setdefault(
                folder.name,
                {
                    "folder": folder.name,
                    "seasons": {},
                    "total_size": 0,
                    "files": [],
                },
            )
            for file_path in folder.rglob("*"):
                if not file_path.is_file() or file_path.name.startswith(".temp_"):
                    continue
                match = ep_re.search(file_path.name)
                if not match:
                    continue
                season_num = int(match.group(1))
                episode_num = int(match.group(2))
                is_video = file_path.suffix.lower() in video_exts
                if not is_video:
                    continue
                try:
                    stat_info = file_path.stat()
                    file_size = stat_info.st_size
                    modified_at = time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.gmtime(stat_info.st_mtime)
                    )
                except OSError:
                    file_size = 0
                    modified_at = None

                season_key = str(season_num)
                entry["seasons"].setdefault(season_key, [])
                if not any(
                    item["episode"] == episode_num and item["file"] == file_path.name
                    for item in entry["seasons"][season_key]
                ):
                    entry["seasons"][season_key].append(
                        {
                            "episode": episode_num,
                            "file": file_path.name,
                            "size": file_size,
                            "is_video": True,
                            "path": str(file_path),
                            "modified_at": modified_at,
                        }
                    )
                    entry["total_size"] += file_size
                entry["files"].append(
                    {
                        "season": season_num,
                        "episode": episode_num,
                        "file": file_path.name,
                        "path": str(file_path),
                        "relative_path": str(file_path.relative_to(folder)),
                        "size": file_size,
                        "ext": file_path.suffix.lower(),
                        "modified_at": modified_at,
                    }
                )

            if lang_name:
                language_totals.setdefault(lang_name, {"episodes": 0, "total_size": 0})
                language_totals[lang_name]["total_size"] += entry["total_size"]

        result = []
        for entry in sorted(titles.values(), key=lambda item: item["folder"].lower()):
            if not any(entry["seasons"].values()):
                continue
            total_eps = sum(
                sum(1 for item in episodes if item.get("is_video", True))
                for episodes in entry["seasons"].values()
            )
            for season_key in entry["seasons"]:
                entry["seasons"][season_key].sort(key=lambda item: item["episode"])
            entry["files"].sort(
                key=lambda item: (
                    item.get("season", 0),
                    item.get("episode", 0),
                    item.get("file", "").lower(),
                )
            )
            entry["file_count"] = len(entry["files"])
            entry["largest_files"] = sorted(
                entry["files"],
                key=lambda item: (-int(item.get("size") or 0), item.get("file", "").lower()),
            )[:8]
            entry["total_episodes"] = total_eps
            if lang_name:
                language_totals[lang_name]["episodes"] += total_eps
            result.append(_enrich_title(entry))
        return result

    locations = []
    for label, cp_id, base_path in _get_scan_targets():
        loc_total_eps = 0
        loc_total_size = 0
        if lang_sep:
            loc_lang_folders = []
            for lang_folder in lang_folders:
                titles = _scan_base(base_path / lang_folder, lang_folder)
                if titles:
                    eps = sum(item["total_episodes"] for item in titles)
                    size = sum(item["total_size"] for item in titles)
                    loc_total_eps += eps
                    loc_total_size += size
                    loc_lang_folders.append(
                        {
                            "name": lang_folder,
                            "titles": titles,
                            "total_episodes": eps,
                            "total_size": size,
                        }
                    )
            if not loc_lang_folders:
                continue
            locations.append(
                {
                    "label": label,
                    "custom_path_id": cp_id,
                    "lang_folders": loc_lang_folders,
                    "titles": None,
                }
            )
        else:
            titles = _scan_base(base_path)
            if not titles:
                continue
            loc_total_eps = sum(item["total_episodes"] for item in titles)
            loc_total_size = sum(item["total_size"] for item in titles)
            locations.append(
                {
                    "label": label,
                    "custom_path_id": cp_id,
                    "lang_folders": None,
                    "titles": titles,
                }
            )

        location_totals[label] = {
            "episodes": loc_total_eps,
            "total_size": loc_total_size,
        }
        summary["episodes"] += loc_total_eps
        summary["total_size"] += loc_total_size

    seen_titles = set()
    for location in locations:
        if location.get("lang_folders"):
            for lang_folder in location["lang_folders"]:
                for title in lang_folder["titles"]:
                    seen_titles.add(
                        (
                            location["label"],
                            lang_folder["name"],
                            title["folder"],
                        )
                    )
        else:
            for title in location["titles"]:
                seen_titles.add((location["label"], title["folder"]))

    summary["titles"] = len(seen_titles)
    summary["by_location"] = [
        {"label": key, **value}
        for key, value in sorted(location_totals.items(), key=lambda item: item[0].lower())
    ]
    summary["by_language"] = [
        {"language": key, **value}
        for key, value in sorted(language_totals.items(), key=lambda item: item[0])
    ]

    return {"lang_sep": lang_sep, "locations": locations, "summary": summary}


# Queue worker state
_queue_worker_started = False
_queue_lock = threading.Lock()

# Auto-sync worker state
_autosync_worker_started = False
_self_heal_worker_started = False
_self_heal_worker_lock = threading.Lock()
_queue_recovery_lock = threading.Lock()
_queue_recovery_state = {}
_self_heal_runtime = {
    "enabled": False,
    "last_action_at": 0.0,
    "last_reason": "",
    "last_queue_id": None,
}

# Track jobs currently being synced to prevent duplicate runs
_syncing_jobs = set()
_syncing_jobs_lock = threading.Lock()

# Schedule intervals in seconds
SYNC_SCHEDULE_MAP = {
    "1min": 60,
    "30min": 1800,
    "1h": 3600,
    "2h": 7200,
    "4h": 14400,
    "8h": 28800,
    "12h": 43200,
    "16h": 57600,
    "24h": 86400,
}

_ui_events = deque(maxlen=120)
_ui_event_seq = 0
_ui_event_lock = threading.Lock()
_ui_event_condition = threading.Condition(_ui_event_lock)
_ui_event_last_emit = {}
_runtime_cache = {}
_runtime_cache_lock = threading.Lock()
_runtime_cache_warmer_started = False
_runtime_cache_warmer_lock = threading.Lock()
_runtime_cache_refresh_timer = None
_runtime_cache_refresh_lock = threading.Lock()


def _self_heal_enabled():
    return (not _safe_mode_enabled()) and (
        os.environ.get(_ENV_EXPERIMENTAL_SELF_HEAL, "0") == "1"
    )


def _record_self_heal_action(queue_id, reason):
    _self_heal_runtime.update(
        enabled=_self_heal_enabled(),
        last_action_at=time.time(),
        last_reason=str(reason or ""),
        last_queue_id=queue_id,
    )


def _peek_queue_recovery(queue_id):
    with _queue_recovery_lock:
        entry = _queue_recovery_state.get(int(queue_id))
        return copy.deepcopy(entry) if entry else None


def _consume_queue_recovery(queue_id):
    with _queue_recovery_lock:
        entry = _queue_recovery_state.pop(int(queue_id), None)
        return copy.deepcopy(entry) if entry else None


def _build_self_heal_error_payload(existing_errors, reason, ffmpeg_state):
    try:
        errors = json.loads(existing_errors or "[]")
    except Exception:
        errors = []

    errors.append(
        {
            "type": "self_heal",
            "error": str(reason or "self-heal recovery"),
            "message": "Experimental watchdog detected a stuck ffmpeg process and requeued the download.",
            "ffmpeg": {
                "pid": ffmpeg_state.get("pid"),
                "label": ffmpeg_state.get("label"),
                "started_at": ffmpeg_state.get("started_at"),
                "last_progress_at": ffmpeg_state.get("last_progress_at"),
                "stall_timeout": ffmpeg_state.get("stall_timeout"),
            },
            "recovered_at": int(time.time()),
        }
    )
    return json.dumps(errors[-20:])


def _attempt_self_heal_requeue(queue_item, reason, ffmpeg_state):
    queue_id = int(queue_item["id"])
    now = time.time()
    with _queue_recovery_lock:
        state = _queue_recovery_state.get(queue_id) or {
            "attempts": 0,
            "last_attempt_at": 0.0,
        }
        if now - float(state.get("last_attempt_at") or 0.0) < 45:
            return False
        state["attempts"] = int(state.get("attempts") or 0) + 1
        state["last_attempt_at"] = now
        state["reason"] = str(reason or "stuck ffmpeg")
        _queue_recovery_state[queue_id] = state

    errors_json = _build_self_heal_error_payload(
        queue_item.get("errors"),
        reason,
        ffmpeg_state,
    )
    requeue_running_item(queue_id, errors_json=errors_json, clear_current_url=True)
    _record_self_heal_action(queue_id, reason)
    record_audit_event(
        "download.self_healed",
        username=queue_item.get("username"),
        subject_type="download",
        subject=queue_item.get("title"),
        details={
            "queue_id": queue_id,
            "reason": reason,
            "attempts": _peek_queue_recovery(queue_id).get("attempts", 0),
            "ffmpeg_pid": ffmpeg_state.get("pid"),
        },
    )
    _dispatch_external_notification(
        "Download self-healed",
        f"{queue_item.get('title') or 'Download'} was requeued after a stuck ffmpeg process was detected.",
        category="system",
        details={
            "queue_id": queue_id,
            "title": queue_item.get("title"),
            "reason": reason,
        },
    )
    _emit_ui_event("queue", "dashboard", "nav", min_interval=0.2)
    return True


def _self_heal_snapshot():
    entry = copy.deepcopy(_self_heal_runtime)
    last_action_at = float(entry.get("last_action_at") or 0.0)
    return {
        "enabled": bool(entry.get("enabled")),
        "last_action_at": last_action_at or None,
        "last_reason": entry.get("last_reason") or "",
        "last_queue_id": entry.get("last_queue_id"),
        "ffmpeg": get_ffmpeg_runtime_state(),
    }


def _cache_get(key, ttl_seconds):
    now = time.monotonic()
    with _runtime_cache_lock:
        entry = _runtime_cache.get(key)
        if not entry:
            return None
        if now - entry["stored_at"] >= ttl_seconds:
            _runtime_cache.pop(key, None)
            return None
        return copy.deepcopy(entry["value"])


def _cache_set(key, value):
    cached_value = copy.deepcopy(value)
    with _runtime_cache_lock:
        _runtime_cache[key] = {
            "stored_at": time.monotonic(),
            "value": cached_value,
        }
    return copy.deepcopy(cached_value)


def _cache_invalidate(*prefixes):
    if not prefixes:
        return
    with _runtime_cache_lock:
        for key in list(_runtime_cache.keys()):
            if any(key.startswith(prefix) for prefix in prefixes):
                _runtime_cache.pop(key, None)


def _warm_runtime_caches_once():
    """Populate the heaviest runtime caches in the background."""
    try:
        _get_cached_stats_payload()
    except Exception as exc:
        logger.warning("Warmup for stats payload failed: %s", exc)

    try:
        _get_cached_library_snapshot(include_meta=False)
    except Exception as exc:
        logger.warning("Warmup for lightweight library snapshot failed: %s", exc)

    try:
        _get_cached_library_snapshot(include_meta=True)
    except Exception as exc:
        logger.warning("Warmup for library snapshot failed: %s", exc)

    try:
        _get_cached_library_compare(refresh=True)
    except Exception as exc:
        logger.warning("Warmup for library compare failed: %s", exc)


def _warm_runtime_caches_startup():
    """Do a startup warmup so the first library/stats view is fast."""
    started_at = time.monotonic()
    logger.info("Starting cache warmup for library/stats surfaces")
    _warm_runtime_caches_once()
    logger.info(
        "Finished cache warmup for library/stats surfaces in %.1fs",
        time.monotonic() - started_at,
    )


def _schedule_runtime_cache_refresh(delay=1.5):
    global _runtime_cache_refresh_timer

    def _refresh():
        global _runtime_cache_refresh_timer
        try:
            _warm_runtime_caches_once()
        finally:
            with _runtime_cache_refresh_lock:
                _runtime_cache_refresh_timer = None

    with _runtime_cache_refresh_lock:
        if _runtime_cache_refresh_timer is not None:
            return
        timer = threading.Timer(delay, _refresh)
        timer.daemon = True
        _runtime_cache_refresh_timer = timer
        timer.start()


def _ensure_runtime_cache_warmer():
    global _runtime_cache_warmer_started
    with _runtime_cache_warmer_lock:
        if _runtime_cache_warmer_started:
            return
        _runtime_cache_warmer_started = True

    def _worker():
        try:
            interval = int(os.environ.get("ANIWORLD_CACHE_WARM_INTERVAL", "45"))
        except ValueError:
            interval = 45
        interval = max(20, min(interval, 900))

        # Warm once right after startup, then refresh periodically.
        while True:
            _warm_runtime_caches_once()
            time.sleep(interval)

    threading.Thread(target=_worker, daemon=True, name="aniworld-cache-warmer").start()


def _diagnostics_cache_snapshot():
    now = time.time()
    with _runtime_cache_lock:
        entries = [
            {
                "key": key,
                "age_seconds": round(now - float(value.get("at") or now), 1),
            }
            for key, value in _runtime_cache.items()
        ]
    entries.sort(key=lambda item: (item["age_seconds"], item["key"]))
    return {
        "entries": entries[:24],
        "count": len(entries),
        "warmer_started": _runtime_cache_warmer_started,
    }


def _build_diagnostics_payload():
    def _safe(factory, fallback, label):
        try:
            return factory()
        except Exception as exc:
            logger.warning("Diagnostics payload section '%s' failed: %s", label, exc)
            return fallback

    try:
        db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
    except OSError:
        db_size = 0
    return {
        "server": _safe(
            lambda: _server_network_info(app),
            {
                "server_bind_host": "127.0.0.1",
                "server_port": 8080,
                "server_ips": [],
                "server_access_urls": [],
                "server_scope": "Unavailable",
            },
            "server",
        ),
        "cache": _safe(
            _diagnostics_cache_snapshot,
            {"entries": [], "count": 0, "warmer_started": False},
            "cache",
        ),
        "queue": _safe(
            get_queue_stats,
            {"total": 0, "by_status": {}, "currently_running": None},
            "queue",
        ),
        "sync": _safe(
            get_sync_stats,
            {
                "total_jobs": 0,
                "enabled": 0,
                "disabled": 0,
                "last_check": None,
                "last_new_found": None,
                "total_episodes_found": 0,
                "jobs": [],
            },
            "sync",
        ),
        "disk_guard": _safe(
            _disk_guard_snapshot,
            {"status": "unknown", "warn_free_gb": 0, "warn_free_percent": 0, "paths": []},
            "disk_guard",
        ),
        "provider_health": _safe(get_provider_health, [], "provider_health")[:6],
        "provider_history_hours": 168,
        "database": {
            "path": str(DB_PATH),
            "size_bytes": db_size,
            "size_mb": round(db_size / (1024 * 1024), 2) if db_size else 0,
        },
        "downloads": {
            "bandwidth_limit_kbps": _normalize_bandwidth_limit(
                os.environ.get(_ENV_BANDWIDTH_LIMIT, "0")
            ),
            "download_backend": _normalize_download_backend(
                os.environ.get(_ENV_DOWNLOAD_BACKEND, "auto")
            ),
            "download_engine_rules": _normalize_engine_rules(
                os.environ.get(_ENV_DOWNLOAD_ENGINE_RULES, "")
            ),
            "download_speed_profile": _download_speed_profile(),
            "auto_provider_switch": _auto_provider_switch_enabled(),
            "rate_limit_guard": _rate_limit_guard_enabled(),
            "preflight_check": _preflight_check_enabled(),
            "fallback_order": _provider_fallback_order(),
            "library_auto_repair": os.environ.get(_ENV_LIBRARY_AUTO_REPAIR, "0")
            == "1",
            "experimental_self_heal": _self_heal_enabled(),
            "safe_mode": _safe_mode_enabled(),
        },
        "self_heal": _safe(
            _self_heal_snapshot,
            {"enabled": False, "last_action_at": None, "last_reason": "", "last_queue_id": None, "ffmpeg": {}},
            "self_heal",
        ),
        "provider_failures": _safe(
            get_provider_failure_analytics,
            [],
            "provider_failures",
        )[:6],
    }


def _build_maintenance_payload():
    diagnostics = _build_diagnostics_payload()
    return {
        "diagnostics": diagnostics,
        "sessions": get_download_session_history(80),
        "provider_failures": get_provider_failure_analytics(),
        "safe_mode": _safe_mode_enabled(),
        "runtime": diagnostics.get("ffmpeg") or {},
        "downloads": {
            "engine": _normalize_download_backend(
                os.environ.get(_ENV_DOWNLOAD_BACKEND, "auto")
            ),
            "engine_rules": _normalize_engine_rules(
                os.environ.get(_ENV_DOWNLOAD_ENGINE_RULES, "")
            ),
            "speed_profile": _download_speed_profile(),
            "auto_provider_switch": _auto_provider_switch_enabled(),
            "rate_limit_guard": _rate_limit_guard_enabled(),
            "preflight_check": _preflight_check_enabled(),
        },
        "webhooks": {
            "enabled": _external_notifications_enabled(),
            "type": _external_notification_type(),
            "url_configured": bool(_external_notifications_url()),
        },
    }


def _maintenance_download_roots():
    roots = {_resolved_download_path_value()}
    for entry in get_custom_paths():
        raw = str(entry.get("path") or "").strip()
        if raw:
            roots.add(str(Path(raw).expanduser()))
    normalized = []
    for raw in roots:
        try:
            resolved = str(Path(raw).expanduser())
        except Exception:
            resolved = str(raw)
        if resolved:
            normalized.append(resolved)
    return sorted(set(normalized))


def _maintenance_clear_temp_files():
    removed = []
    patterns = (
        "*.temp_audio.mkv",
        "*.temp_video.mkv",
        "*.temp_full.mkv",
        "*.temp_ytdlp.*",
        "*.new.mkv",
        "*.part",
    )
    for root in _maintenance_download_roots():
        base = Path(root)
        if not base.exists():
            continue
        for pattern in patterns:
            try:
                matches = list(base.rglob(pattern))
            except Exception:
                matches = []
            for candidate in matches:
                if not candidate.is_file():
                    continue
                try:
                    candidate.unlink()
                    removed.append(str(candidate))
                except OSError:
                    continue
    return {"removed": len(removed), "samples": removed[:12]}


def _maintenance_recover_queue():
    running = get_running()
    if not running:
        return {"recovered": False, "reason": "No running queue item"}

    reason = "maintenance recover action"
    terminate_ffmpeg_process_tree(reason)
    update_queue_progress(
        running["id"],
        int(running.get("current_episode") or 0),
        "",
    )
    requeue_running_item(running["id"], clear_current_url=True)
    _emit_ui_event("queue", "dashboard", "nav", "settings")
    return {
        "recovered": True,
        "queue_id": running["id"],
        "title": running.get("title") or f"Queue #{running['id']}",
    }


def _emit_ui_event(*channels, min_interval=0.75):
    normalized = tuple(sorted({ch for ch in channels if ch}))
    if not normalized:
        return

    if any(
        channel in normalized
        for channel in ("queue", "autosync", "dashboard", "library", "settings", "favorites")
    ):
        _cache_invalidate("stats:", "dashboard:")
    if any(channel in normalized for channel in ("library", "settings", "favorites")):
        _cache_invalidate("library:")
    if any(
        channel in normalized
        for channel in ("queue", "autosync", "dashboard", "library", "settings", "favorites")
    ):
        _schedule_runtime_cache_refresh()

    now = time.monotonic()
    with _ui_event_condition:
        last_emit = _ui_event_last_emit.get(normalized, 0.0)
        if now - last_emit < min_interval:
            return
        _ui_event_last_emit[normalized] = now

        global _ui_event_seq
        _ui_event_seq += 1
        _ui_events.append(
            {
                "seq": _ui_event_seq,
                "channels": list(normalized),
                "emitted_at": time.time(),
            }
        )
        _ui_event_condition.notify_all()


def _pending_ui_events(after_seq):
    return [event for event in _ui_events if event["seq"] > after_seq]


def _extract_provider_info(provider_data):
    disable_eng_sub = os.environ.get("ANIWORLD_DISABLE_ENGLISH_SUB", "0") == "1"
    provider_info = {}

    if hasattr(provider_data, "_data"):
        lang_tuple_to_label = {}
        for key, (audio, subtitles) in LANG_KEY_MAP.items():
            label = LANG_LABELS.get(key)
            if label:
                lang_tuple_to_label[(audio.value, subtitles.value)] = label

        for (audio, subtitles), providers in provider_data._data.items():
            label = lang_tuple_to_label.get((audio.value, subtitles.value))
            if not label:
                continue
            if disable_eng_sub and label == "English Sub":
                continue
            working = [p for p in providers.keys() if p in WORKING_PROVIDERS]
            if working:
                provider_info[label] = working
        return provider_info

    sto_label_map = {
        ("German", "None"): "German Dub",
        ("English", "None"): "English Dub",
    }
    for (audio, subtitles), providers in provider_data.items():
        label = sto_label_map.get((audio.value, subtitles.value))
        if not label:
            continue
        working = [p for p in providers.keys() if p in WORKING_PROVIDERS]
        if working:
            provider_info[label] = working
    return provider_info


def _episode_language_labels_for_ui(episode, allow_provider_lookup=False):
    labels = list(getattr(episode, "available_languages", []) or [])
    if not allow_provider_lookup:
        return labels

    try:
        provider_info = _extract_provider_info(episode.provider_data)
        if provider_info:
            return list(provider_info.keys())
    except Exception:
        pass

    return labels


def _flatten_provider_map(provider_map):
    flattened = []
    seen = set()
    for providers in (provider_map or {}).values():
        for provider_name in providers or []:
            clean = str(provider_name or "").strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            flattened.append(clean)
    return _rank_provider_candidates(flattened)


def _resolve_link_import_target(raw_url):
    url = normalize_url(str(raw_url or "").strip())
    if not url:
        raise ValueError("url is required")

    provider = resolve_provider(url)
    site = _detect_site(url)
    kind = "direct"
    series_url = url
    focus_season_url = ""
    focus_episode_url = ""

    if provider.name == "AniWorld":
        if ANIWORLD_SERIES_PATTERN.fullmatch(url):
            kind = "series"
        elif ANIWORLD_SEASON_PATTERN.fullmatch(url):
            kind = "season"
            focus_season_url = url
            series_url = re.sub(r"/(staffel-\d+|filme)$", "", url, flags=re.IGNORECASE)
        elif ANIWORLD_EPISODE_PATTERN.fullmatch(url):
            kind = "episode"
            focus_episode_url = url
            if "/filme/" in url:
                focus_season_url = re.sub(r"/film-\d+$", "", url, flags=re.IGNORECASE)
                series_url = re.sub(
                    r"/filme/film-\d+$", "", url, flags=re.IGNORECASE
                )
            else:
                focus_season_url = re.sub(
                    r"/episode-\d+$", "", url, flags=re.IGNORECASE
                )
                series_url = re.sub(
                    r"/staffel-\d+/episode-\d+$", "", url, flags=re.IGNORECASE
                )
    elif provider.name == "SerienStream":
        if SERIENSTREAM_SERIES_PATTERN.fullmatch(url):
            kind = "series"
        elif SERIENSTREAM_SEASON_PATTERN.fullmatch(url):
            kind = "season"
            focus_season_url = url
            series_url = re.sub(r"/staffel-\d+$", "", url, flags=re.IGNORECASE)
        elif SERIENSTREAM_EPISODE_PATTERN.fullmatch(url):
            kind = "episode"
            focus_episode_url = url
            focus_season_url = re.sub(r"/episode-\d+$", "", url, flags=re.IGNORECASE)
            series_url = re.sub(
                r"/staffel-\d+/episode-\d+$", "", url, flags=re.IGNORECASE
            )
    elif provider.name == "Filmpalast" and FILMPALAST_EPISODE_PATTERN.fullmatch(url):
        kind = "movie"
        focus_episode_url = url
        focus_season_url = url
        series_url = url

    return {
        "input_url": raw_url,
        "normalized_url": url,
        "site": site,
        "source_name": provider.name,
        "kind": kind,
        "series_url": series_url,
        "focus_season_url": focus_season_url,
        "focus_episode_url": focus_episode_url,
        "auto_sync_supported": bool(provider.series_cls),
    }


def _provider_fallback_order():
    custom = _normalize_provider_fallback_order(
        os.environ.get(_ENV_PROVIDER_FALLBACK_ORDER, "")
    )
    return [value.strip() for value in custom.split(",") if value.strip()]


def _rank_provider_candidates(candidates, preferred=None, exclude=None):
    quality_rows = {row["provider"]: row for row in get_provider_quality()}
    ordered = list(dict.fromkeys([name for name in candidates if name and name != exclude]))
    position_map = {name: index for index, name in enumerate(ordered)}
    fallback_order = _provider_fallback_order()
    fallback_position = {
        name: fallback_order.index(name) for name in fallback_order if name in ordered
    }

    def _score(name):
        row = quality_rows.get(name, {})
        completed = int(row.get("completed") or 0)
        failed = int(row.get("failed") or 0)
        total = completed + failed
        success_rate = completed / total if total else 0.5
        return (
            0 if name == preferred else 1,
            fallback_position.get(name, 999),
            -success_rate,
            -completed,
            failed,
            position_map[name],
            name.lower(),
        )

    return sorted(ordered, key=_score)


def _get_provider_candidates_for_episode(ep_url, language, preferred=None, exclude=None):
    try:
        prov = resolve_provider(ep_url)
        episode = prov.episode_cls(url=ep_url)
        provider_map = _extract_provider_info(episode.provider_data)
        return _rank_provider_candidates(
            provider_map.get(language, []),
            preferred=preferred,
            exclude=exclude,
        )
    except Exception:
        return []


def _ordered_language_labels(labels):
    seen = set()
    ordered = []
    preferred = list(dict.fromkeys(LANG_LABELS.values()))
    extras = []

    for label in labels or []:
        clean = str(label or "").strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        if clean in preferred:
            continue
        extras.append(clean)

    for label in preferred:
        if label in seen:
            ordered.append(label)

    ordered.extend(sorted(extras))
    return ordered


def _collect_autosync_provider_options(series_url, sample_limit=12):
    provider_map = {}

    def _merge(info):
        for language, providers in (info or {}).items():
            working = [name for name in providers if name in WORKING_PROVIDERS]
            if not working:
                continue
            bucket = provider_map.setdefault(language, set())
            bucket.update(working)

    try:
        prov = resolve_provider(series_url)
    except Exception:
        return {}

    sampled = 0

    try:
        if prov.series_cls and prov.season_cls:
            series = prov.series_cls(url=series_url)
            for season_ref in list(getattr(series, "seasons", []) or []):
                try:
                    season_obj = prov.season_cls(url=season_ref.url, series=series)
                except Exception:
                    season_obj = season_ref
                for episode in list(getattr(season_obj, "episodes", []) or []):
                    try:
                        _merge(_extract_provider_info(episode.provider_data))
                    except Exception:
                        continue
                    sampled += 1
                    if sampled >= sample_limit:
                        break
                if sampled >= sample_limit and provider_map:
                    break
        else:
            episode = prov.episode_cls(url=series_url)
            _merge(_extract_provider_info(episode.provider_data))
    except Exception:
        return {}

    normalized = {}
    for language, providers in provider_map.items():
        ranked = _rank_provider_candidates(list(providers))
        if ranked:
            normalized[language] = ranked
    return normalized


def _providers_for_all_languages(provider_map):
    provider_sets = [set(items or []) for items in provider_map.values() if items]
    if not provider_sets:
        return []

    shared = set(provider_sets[0])
    for provider_set in provider_sets[1:]:
        shared &= provider_set

    if shared:
        return _rank_provider_candidates(list(shared))

    merged = set()
    for provider_set in provider_sets:
        merged |= provider_set
    return _rank_provider_candidates(list(merged))


def _build_autosync_job_options(job):
    current_language = str(job.get("language") or "German Dub").strip() or "German Dub"
    current_provider = str(job.get("provider") or "VOE").strip() or "VOE"
    detected_map = _collect_autosync_provider_options(job.get("series_url", ""))
    providers_by_language = {key: list(value) for key, value in detected_map.items()}
    detected = bool(providers_by_language)

    if not providers_by_language:
        fallback_language = (
            current_language if current_language != "All Languages" else "German Dub"
        )
        fallback_provider = (
            current_provider
            if current_provider in WORKING_PROVIDERS
            else (WORKING_PROVIDERS[0] if WORKING_PROVIDERS else "")
        )
        providers_by_language = {fallback_language: [fallback_provider] if fallback_provider else []}

    languages = _ordered_language_labels(providers_by_language.keys())
    allow_all_languages = (
        (os.environ.get("ANIWORLD_LANG_SEPARATION", "0") == "1")
        or current_language == "All Languages"
    ) and len(languages) > 1
    all_language_providers = (
        _providers_for_all_languages(providers_by_language)
        if allow_all_languages
        else []
    )

    if current_language == "All Languages" and allow_all_languages:
        selected_language = "All Languages"
        selected_providers = all_language_providers
    else:
        selected_language = (
            current_language if current_language in providers_by_language else languages[0]
        )
        selected_providers = providers_by_language.get(selected_language, [])

    selected_provider = (
        current_provider
        if current_provider in selected_providers
        else (selected_providers[0] if selected_providers else "")
    )

    return {
        "detected": detected,
        "languages": languages,
        "providers_by_language": providers_by_language,
        "allow_all_languages": allow_all_languages,
        "all_language_providers": all_language_providers,
        "selected_language": selected_language,
        "selected_provider": selected_provider,
    }


def _resolve_autosync_job_provider(job, language):
    configured = str(job.get("provider") or "VOE").strip() or "VOE"
    if configured != "Auto":
        return configured

    options = _build_autosync_job_options(job)
    active_language = str(language or job.get("language") or "").strip()
    if active_language == "All Languages":
        candidates = list(options.get("all_language_providers") or [])
    else:
        candidates = list((options.get("providers_by_language") or {}).get(active_language, []))
        if not candidates and active_language == str(job.get("language") or "").strip():
            candidates = list(options.get("all_language_providers") or [])

    return candidates[0] if candidates else "VOE"


def _pick_retry_provider(queue_item):
    try:
        episodes = json.loads(queue_item["episodes"] or "[]")
    except Exception:
        episodes = []
    if not episodes:
        return queue_item["provider"]

    next_candidates = _get_provider_candidates_for_episode(
        episodes[0],
        queue_item["language"],
        exclude=queue_item["provider"],
    )
    return next_candidates[0] if next_candidates else queue_item["provider"]


def _resolve_provider_benchmark_sample(episode_url="", language=""):
    sample_url = str(episode_url or "").strip()
    sample_language = str(language or "").strip() or "German Dub"

    if sample_url:
        return {
            "episode_url": sample_url,
            "language": sample_language,
            "title": "Manual sample",
        }

    queue_items = get_queue()
    for item in queue_items:
        try:
            episodes = json.loads(item.get("episodes") or "[]")
        except Exception:
            episodes = []
        if not episodes:
            continue
        first_episode = str(episodes[0] or "").strip()
        if not first_episode:
            continue
        return {
            "episode_url": first_episode,
            "language": str(item.get("language") or "German Dub").strip()
            or "German Dub",
            "title": str(item.get("title") or "Queue sample").strip()
            or "Queue sample",
        }

    raise ValueError("No queue episode is available for a benchmark sample")


def _run_provider_benchmark(episode_url="", language=""):
    sample = _resolve_provider_benchmark_sample(episode_url, language)
    prov = resolve_provider(sample["episode_url"])
    if not prov.episode_cls:
        raise ValueError("This source does not support provider benchmarking")

    episode = prov.episode_cls(url=sample["episode_url"])
    provider_map = _extract_provider_info(getattr(episode, "provider_data", None))
    available = _rank_provider_candidates(provider_map.get(sample["language"], []))
    if not available:
        raise ValueError(
            f"No providers are available for {sample['language']} on this episode"
        )

    results = []
    for provider_name in available:
        started_at = time.perf_counter()
        status = "ready"
        redirect_url = ""
        redirect_host = ""
        error_message = ""
        recommendation = _recommended_engine_for_provider(provider_name)

        try:
            redirect_url = str(
                episode.provider_link(sample["language"], provider_name) or ""
            ).strip()
            if not redirect_url:
                status = "broken"
                error_message = "No redirect URL returned"
            else:
                redirect_host = urlparse(redirect_url).netloc
        except Exception as exc:
            status = "error"
            error_message = str(exc)

        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 1)
        results.append(
            {
                "provider": provider_name,
                "status": status,
                "latency_ms": elapsed_ms,
                "redirect_url": redirect_url,
                "redirect_host": redirect_host,
                "error": error_message,
                "recommended_engine": recommendation.get("engine") or "ffmpeg",
                "engine_mode": recommendation.get("mode") or "adaptive",
                "profile": _download_speed_profile(),
            }
        )

    ordered = sorted(
        results,
        key=lambda item: (
            0 if item["status"] == "ready" else 1 if item["status"] == "broken" else 2,
            item["latency_ms"],
            item["provider"].lower(),
        ),
    )
    for rank, item in enumerate(ordered, start=1):
        item["rank"] = rank

    return {
        "sample": sample,
        "results": ordered,
        "provider_count": len(ordered),
        "profile": _download_speed_profile(),
    }


def _download_episode_with_fallback(item, ep_url, selected_path):
    from ..playwright import captcha as _captcha_mod

    providers_to_try = [item["provider"]]
    tried = []
    errors = []
    attempt_details = []

    while providers_to_try:
        provider_name = providers_to_try.pop(0)
        if provider_name in tried:
            continue
        tried.append(provider_name)

        try:
            prov = resolve_provider(ep_url)
            ep_kwargs = {
                "url": ep_url,
                "selected_language": item["language"],
                "selected_provider": provider_name,
            }
            if selected_path:
                ep_kwargs["selected_path"] = selected_path
            episode = prov.episode_cls(**ep_kwargs)
            _captcha_mod._local.queue_id = item["id"]
            if _preflight_check_enabled():
                provider_url = str(getattr(episode, "provider_url", "") or "").strip()
                stream_url = str(getattr(episode, "stream_url", "") or "").strip()
                attempt_details.append(
                    {
                        "provider": provider_name,
                        "message": "Preflight ok",
                        "provider_url": provider_url,
                        "stream_host": urlparse(stream_url).netloc if stream_url else "",
                        "engine": _recommended_engine_for_provider(provider_name).get("engine"),
                    }
                )
                if not stream_url:
                    raise RuntimeError("Preflight could not resolve a stream URL")
            try:
                episode.download()
            finally:
                _captcha_mod._local.queue_id = None
            return provider_name
        except Exception as exc:
            _captcha_mod._local.queue_id = None
            logger.warning(
                "Provider %s failed for %s: %s",
                provider_name,
                ep_url,
                exc,
            )
            attempt_details.append(
                {
                    "provider": provider_name,
                    "message": str(exc),
                }
            )
            errors.append(f"{provider_name}: {exc}")
            if _peek_queue_recovery(item["id"]):
                err = RuntimeError(
                    _peek_queue_recovery(item["id"]).get("reason")
                    or "Experimental self-heal requeued this job"
                )
                err.attempt_details = attempt_details
                raise err
            if _auto_provider_switch_enabled() and len(tried) == 1:
                fallback_candidates = _get_provider_candidates_for_episode(
                    ep_url,
                    item["language"],
                    exclude=provider_name,
                )
                fallback_limit = _smart_retry_fallback_limit()
                if fallback_limit is not None:
                    fallback_candidates = fallback_candidates[:fallback_limit]
                for candidate in fallback_candidates:
                    if candidate not in tried and candidate not in providers_to_try:
                        providers_to_try.append(candidate)

    err = RuntimeError(" | ".join(errors) if errors else "All providers failed")
    err.attempt_details = attempt_details
    raise err


def _build_nav_state(username=None):
    queue = get_queue_stats(username=username)
    sync = get_sync_stats(username=username)
    return {
        "active_queue": int(queue.get("by_status", {}).get("queued", 0))
        + int(queue.get("by_status", {}).get("running", 0)),
        "failed_queue": int(queue.get("by_status", {}).get("failed", 0)),
        "favorites": len(list_favorites(username=username)),
        "autosync_enabled": int(sync.get("enabled", 0)),
    }


def _get_cached_library_snapshot(include_meta=True):
    cache_key = f"library:{1 if include_meta else 0}"
    cached = _cache_get(cache_key, 900.0)
    if cached is not None:
        return cached
    snapshot = _scan_library_snapshot(include_meta=include_meta)
    return _cache_set(cache_key, snapshot)


def _queue_episode_urls(queue_item):
    try:
        entries = json.loads(queue_item.get("episodes") or "[]")
    except Exception:
        entries = []
    return [str(entry or "").strip() for entry in entries if str(entry or "").strip()]


def _episode_label_from_url(url):
    match = re.search(r"staffel-(\d+)/episode-(\d+)", str(url or ""), re.IGNORECASE)
    if match:
        return f"S{int(match.group(1)):02d}E{int(match.group(2)):03d}"
    movie_match = re.search(r"filme/film-(\d+)", str(url or ""), re.IGNORECASE)
    if movie_match:
        return f"Movie {int(movie_match.group(1))}"
    return str(url or "").strip()


def _filter_conflicting_queue_episodes(series_url, language, episode_urls, exclude_queue_id=None):
    requested = [
        str(url or "").strip()
        for url in (episode_urls or [])
        if str(url or "").strip()
    ]
    requested_set = set(requested)
    if not requested_set:
        return {"episodes": [], "skipped": 0, "conflicts": []}

    overlapping = set()
    conflicts = []

    for item in get_queue():
        if exclude_queue_id and item.get("id") == exclude_queue_id:
            continue
        if item.get("status") not in {"queued", "running"}:
            continue
        if item.get("series_url") != series_url:
            continue
        if language and item.get("language") != language:
            continue

        item_episode_urls = set(_queue_episode_urls(item))
        overlap = sorted(requested_set & item_episode_urls)
        if not overlap:
            continue

        overlapping.update(overlap)
        conflicts.append(
            {
                "queue_id": item.get("id"),
                "status": item.get("status"),
                "language": item.get("language"),
                "provider": item.get("provider"),
                "overlap_count": len(overlap),
                "overlap": overlap[:8],
                "overlap_labels": [_episode_label_from_url(url) for url in overlap[:8]],
            }
        )

    filtered = [url for url in requested if url not in overlapping]
    return {
        "episodes": filtered,
        "skipped": len(requested) - len(filtered),
        "conflicts": conflicts,
    }


def _library_title_episode_index(title):
    index = {}
    total = 0
    for season_key, episodes in (title.get("seasons") or {}).items():
        season_number = str(season_key)
        values = sorted(
            {
                int(item.get("episode"))
                for item in (episodes or [])
                if item.get("is_video", True) and item.get("episode")
            }
        )
        if values:
            index[season_number] = values
            total += len(values)
    return {"seasons": index, "total_episodes": total}


def _get_cached_source_episode_index(series_url):
    cache_key = f"library:source:{series_url}"
    cached = _cache_get(cache_key, 900.0)
    if cached is not None:
        return cached

    try:
        prov = resolve_provider(series_url)
        if not prov.series_cls or not prov.season_cls:
            return _cache_set(
                cache_key,
                {"available": False, "reason": "unsupported", "source": getattr(prov, "name", "")},
            )

        series = prov.series_cls(url=series_url)
        seasons = {}
        total = 0
        for season_ref in list(getattr(series, "seasons", []) or []):
            season_obj = prov.season_cls(url=season_ref.url, series=series)
            values = sorted(
                {
                    int(getattr(episode, "episode_number", 0))
                    for episode in list(getattr(season_obj, "episodes", []) or [])
                    if getattr(episode, "episode_number", 0)
                }
            )
            if not values:
                continue
            season_number = str(getattr(season_obj, "season_number", 0) or 0)
            seasons[season_number] = values
            total += len(values)

        return _cache_set(
            cache_key,
            {
                "available": True,
                "source": getattr(prov, "name", "") or "Source",
                "season_count": len(seasons),
                "total_episodes": total,
                "seasons": seasons,
            },
        )
    except Exception as exc:
        logger.warning("Library compare failed for %s: %s", series_url, exc)
        return _cache_set(
            cache_key,
            {"available": False, "reason": "error", "error": str(exc), "source": "Source"},
        )


def _compare_title_with_source(title):
    series_url = str(title.get("series_url") or "").strip()
    if not series_url:
        return {"available": False, "reason": "unlinked"}

    source_index = _get_cached_source_episode_index(series_url)
    if not source_index.get("available"):
        return source_index

    local_index = _library_title_episode_index(title)
    local_seasons = local_index["seasons"]
    remote_seasons = source_index.get("seasons", {})
    missing = []
    extra = []

    for season_key, remote_values in remote_seasons.items():
        local_values = set(local_seasons.get(season_key, []))
        remote_set = set(remote_values)
        for episode_number in sorted(remote_set - local_values):
            missing.append(f"S{int(season_key):02d}E{int(episode_number):03d}")

    for season_key, local_values in local_seasons.items():
        remote_values = set(remote_seasons.get(season_key, []))
        local_set = set(local_values)
        for episode_number in sorted(local_set - remote_values):
            extra.append(f"S{int(season_key):02d}E{int(episode_number):03d}")

    return {
        "available": True,
        "source": source_index.get("source") or "Source",
        "season_count": source_index.get("season_count", 0),
        "remote_total_episodes": source_index.get("total_episodes", 0),
        "local_total_episodes": local_index.get("total_episodes", 0),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "missing": missing,
        "missing_sample": missing[:8],
        "extra": extra,
        "extra_sample": extra[:6],
        "in_sync": not missing,
    }


def _get_cached_library_compare(refresh=False):
    cache_key = "library:compare"
    if refresh:
        _cache_invalidate(cache_key)
    cached = _cache_get(cache_key, 900.0)
    if cached is not None:
        return cached

    snapshot = _get_cached_library_snapshot(include_meta=True)
    items = {}
    summary = {
        "compared": 0,
        "in_sync": 0,
        "out_of_sync": 0,
        "titles_missing": 0,
        "missing_episodes": 0,
        "unavailable": 0,
    }

    seen_urls = set()
    for location in snapshot.get("locations", []):
        title_groups = []
        if location.get("lang_folders"):
            for lang_folder in location["lang_folders"]:
                title_groups.extend(lang_folder.get("titles", []))
        else:
            title_groups.extend(location.get("titles", []))

        for title in title_groups:
            series_url = str(title.get("series_url") or "").strip()
            if not series_url or series_url in seen_urls:
                continue
            seen_urls.add(series_url)
            compare = _compare_title_with_source(title)
            items[series_url] = compare

            if compare.get("available"):
                summary["compared"] += 1
                if compare.get("missing_count", 0) > 0:
                    summary["out_of_sync"] += 1
                    summary["titles_missing"] += 1
                    summary["missing_episodes"] += int(compare.get("missing_count", 0))
                else:
                    summary["in_sync"] += 1
            else:
                summary["unavailable"] += 1

    payload = {"items": items, "summary": summary, "checked_at": int(time.time())}
    return _cache_set(cache_key, payload)


def _language_label_from_library_folder(name):
    mapping = {
        "german-dub": "German Dub",
        "english-sub": "English Sub",
        "german-sub": "German Sub",
        "english-dub": "English Dub",
    }
    return mapping.get(str(name or "").strip().lower(), "German Dub")


def _resolve_missing_episode_urls(series_url, missing_labels):
    if not series_url or not missing_labels:
        return []
    wanted = {str(label).strip().upper() for label in missing_labels if str(label).strip()}
    if not wanted:
        return []

    prov = resolve_provider(series_url)
    if not prov.series_cls or not prov.season_cls:
        return []

    series = prov.series_cls(url=series_url)
    matches = []
    for season_ref in list(getattr(series, "seasons", []) or []):
        season_obj = prov.season_cls(url=season_ref.url, series=series)
        for episode in list(getattr(season_obj, "episodes", []) or []):
            label = f"S{int(getattr(season_obj, 'season_number', 0)):02d}E{int(getattr(episode, 'episode_number', 0)):03d}"
            if label in wanted:
                matches.append((label, episode.url, episode))
    matches.sort(key=lambda item: item[0])
    return matches


def _queue_missing_episode_labels(
    *,
    series_url,
    title,
    missing_labels,
    language="German Dub",
    preferred_provider=None,
    custom_path_id=None,
    username=None,
    source="library:missing",
):
    if not series_url:
        raise ValueError("series_url is required")
    if not isinstance(missing_labels, list) or not missing_labels:
        raise ValueError("missing_labels are required")
    if (
        language == "English Sub"
        and os.environ.get("ANIWORLD_DISABLE_ENGLISH_SUB", "0") == "1"
    ):
        raise PermissionError("English Sub downloads are disabled")

    resolved = _resolve_missing_episode_urls(series_url, missing_labels)
    if not resolved:
        raise LookupError("No matching missing episodes found")

    provider_options = {}
    common_providers = None
    for label, ep_url, episode_obj in resolved:
        options = list(
            _extract_provider_info(getattr(episode_obj, "provider_data", None)).get(
                language, []
            )
            or []
        )
        provider_options[label] = {"url": ep_url, "options": options}
        option_set = set(options)
        common_providers = option_set if common_providers is None else (common_providers & option_set)

    selected_provider = None
    if common_providers:
        if preferred_provider and preferred_provider in common_providers:
            selected_provider = preferred_provider
        else:
            for provider_name in _WORKING_PROVIDER_PREFERENCE:
                if provider_name in common_providers:
                    selected_provider = provider_name
                    break
            if not selected_provider:
                selected_provider = sorted(common_providers)[0]
        episode_urls = [item[1] for item in resolved]
        skipped_unavailable = 0
    else:
        provider_counts = {}
        for item in provider_options.values():
            for provider_name in item["options"]:
                provider_counts[provider_name] = provider_counts.get(provider_name, 0) + 1
        if preferred_provider and preferred_provider in provider_counts:
            selected_provider = preferred_provider
        elif provider_counts:
            selected_provider = sorted(
                provider_counts.items(),
                key=lambda pair: (
                    -pair[1],
                    _WORKING_PROVIDER_PREFERENCE.index(pair[0])
                    if pair[0] in _WORKING_PROVIDER_PREFERENCE
                    else 999,
                    pair[0],
                ),
            )[0][0]
        if not selected_provider:
            raise RuntimeError(
                f"No provider is available for {language} on the missing episodes."
            )
        episode_urls = [
            item["url"]
            for item in provider_options.values()
            if selected_provider in item["options"]
        ]
        skipped_unavailable = len(resolved) - len(episode_urls)

    conflict_guard = _filter_conflicting_queue_episodes(series_url, language, episode_urls)
    queueable_episodes = conflict_guard["episodes"]
    if not queueable_episodes:
        err = RuntimeError("Missing episodes are already queued or currently downloading.")
        err.kind = "queue_conflict"
        err.payload = {
            "skipped_conflicts": conflict_guard["skipped"],
            "skipped_unavailable": skipped_unavailable,
            "conflicts": conflict_guard["conflicts"],
        }
        raise err

    queue_id = add_to_queue(
        title,
        series_url,
        queueable_episodes,
        language,
        selected_provider,
        username,
        custom_path_id=custom_path_id,
        source=source,
    )
    return {
        "queue_id": queue_id,
        "provider": selected_provider,
        "queued_episodes": len(queueable_episodes),
        "skipped_unavailable": skipped_unavailable,
        "skipped_conflicts": conflict_guard["skipped"],
    }


def _run_library_auto_repair(language, preferred_provider, username=None):
    if _safe_mode_enabled():
        return {
            "created": [],
            "skipped": [{"series_url": "", "reason": "Safe mode is enabled"}],
        }
    compare_payload = _get_cached_library_compare(refresh=True)
    snapshot = _get_cached_library_snapshot(include_meta=True)
    titles_by_url = {}
    for location in snapshot.get("locations", []):
        title_groups = []
        if location.get("lang_folders"):
            for lang_folder in location.get("lang_folders", []):
                title_groups.extend(lang_folder.get("titles", []))
        else:
            title_groups.extend(location.get("titles", []))
        for title in title_groups:
            series_url = str(title.get("series_url") or "").strip()
            if series_url:
                titles_by_url[series_url] = title

    created = []
    skipped = []
    for series_url, compare in (compare_payload.get("items") or {}).items():
        missing = list(compare.get("missing") or [])
        if not missing:
            continue
        title_info = titles_by_url.get(series_url, {})
        try:
            result = _queue_missing_episode_labels(
                series_url=series_url,
                title=title_info.get("folder") or title_info.get("title") or series_url,
                missing_labels=missing,
                language=language,
                preferred_provider=preferred_provider,
                username=username,
                source="library:repair",
            )
            created.append(
                {
                    "series_url": series_url,
                    "title": title_info.get("folder") or series_url,
                    "queued_episodes": result["queued_episodes"],
                }
            )
        except Exception as exc:
            skipped.append({"series_url": series_url, "reason": str(exc)})
    return {"created": created, "skipped": skipped}


def _allowed_library_roots():
    roots = []
    for _, _, root in _get_scan_targets():
        try:
            roots.append(root.resolve())
        except Exception:
            continue
    return roots


def _is_path_within_roots(path_string):
    try:
        path = Path(path_string).resolve()
    except Exception:
        return False
    for root in _allowed_library_roots():
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _smart_retry_profile():
    return _normalize_smart_retry_profile(_global_pref("smart_retry_profile", "balanced"))


def _smart_retry_fallback_limit():
    profile = _smart_retry_profile()
    if profile == "conservative":
        return 1
    if profile == "balanced":
        return 2
    return None


def _resolve_duplicate_file_paths(file_paths):
    groups = {}
    for item in file_paths or []:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        if not path or not _is_path_within_roots(path):
            continue
        key = (int(item.get("season") or 0), int(item.get("episode") or 0))
        groups.setdefault(key, []).append(item)

    keep_paths = []
    delete_paths = []
    for entries in groups.values():
        if len(entries) < 2:
            continue
        ordered = sorted(
            entries,
            key=lambda entry: (
                -int(entry.get("size") or 0),
                str(entry.get("path") or "").lower(),
            ),
        )
        keep_paths.append(str(ordered[0].get("path") or ""))
        delete_paths.extend(
            str(entry.get("path") or "") for entry in ordered[1:] if entry.get("path")
        )
    return {
        "keep_paths": [path for path in keep_paths if path],
        "delete_paths": [path for path in delete_paths if path],
    }


def _run_provider_test(episode_url, language, provider):
    prov = resolve_provider(episode_url)
    if not prov.episode_cls:
        raise ValueError("This source does not expose episode testing")

    episode = prov.episode_cls(url=episode_url)
    episode.selected_language = language
    episode.selected_provider = provider

    provider_url = episode.provider_url
    stream_url = episode.stream_url

    return {
        "site": _detect_site(episode_url),
        "episode_url": episode_url,
        "provider_url": provider_url,
        "provider_host": urlparse(provider_url).netloc if provider_url else "",
        "stream_url": stream_url,
        "stream_host": urlparse(stream_url).netloc if stream_url else "",
        "language": language,
        "provider": provider,
        "ok": True,
    }


def _get_cached_stats_payload(username=None):
    cache_key = "stats:summary:global"
    cached = _cache_get(cache_key, 180.0)
    if cached is not None:
        return cached

    general = get_general_stats()
    queue = get_queue_stats()
    sync = get_sync_stats()
    try:
        storage_snapshot = _get_cached_library_snapshot(include_meta=True)
        storage_summary = storage_snapshot.get("summary", {})
    except Exception as exc:
        logger.warning("Stats storage snapshot failed: %s", exc)
        storage_summary = {
            "titles": 0,
            "episodes": 0,
            "total_size": 0,
            "by_location": [],
            "by_language": [],
            "available": False,
            "error": str(exc),
        }
    provider_health = get_provider_health()
    provider_failures = get_provider_failure_analytics()
    payload = {
        "general": general,
        "queue": queue,
        "sync": sync,
        "storage": storage_summary,
        "provider_quality": get_provider_quality(),
        "provider_health": provider_health,
        "provider_failures": provider_failures,
        "activity_chart": get_activity_chart(7),
    }
    return _cache_set(cache_key, payload)


def _queue_worker():
    """Single global worker that processes one download at a time."""
    while True:
        try:
            item = None
            with _queue_lock:
                if not get_running():
                    item = get_next_queued()
                    if item:
                        set_queue_status(item["id"], "running")
                        _mark_download_activity("queue-started")
                        _emit_ui_event("queue", "dashboard", "nav")

            if not item:
                time.sleep(3)
                continue

            episodes = json.loads(item["episodes"])
            errors = []
            requeued_by_self_heal = False

            # Language separation: compute subfolder path if enabled
            import os

            lang_sep = os.environ.get("ANIWORLD_LANG_SEPARATION", "0") == "1"
            if item.get("source") == "sync:all_langs":
                lang_sep = True
            selected_path = None

            from pathlib import Path

            # Determine base path: custom path or default
            custom_path_id = item.get("custom_path_id")
            if custom_path_id:
                cp = get_custom_path_by_id(custom_path_id)
                if cp:
                    base = Path(cp["path"]).expanduser()
                    if not base.is_absolute():
                        base = Path.home() / base
                else:
                    base = None
            else:
                base = None

            if base is None:
                raw = os.environ.get("ANIWORLD_DOWNLOAD_PATH", "")
                if raw:
                    base = Path(raw).expanduser()
                    if not base.is_absolute():
                        base = Path.home() / base
                else:
                    base = Path.home() / "Downloads"

            if lang_sep:
                lang_folder_map = {
                    "German Dub": "german-dub",
                    "English Sub": "english-sub",
                    "German Sub": "german-sub",
                    "English Dub": "english-dub",
                }
                lang_folder = lang_folder_map.get(
                    item["language"], item["language"].lower().replace(" ", "-")
                )
                selected_path = str(base / lang_folder)
            elif custom_path_id:
                selected_path = str(base)

            for i, ep_url in enumerate(episodes):
                update_queue_progress(item["id"], i, ep_url)
                _emit_ui_event("queue", min_interval=0.35)
                try:
                    _download_episode_with_fallback(item, ep_url, selected_path)
                except Exception as e:
                    recovery = _consume_queue_recovery(item["id"])
                    if recovery:
                        logger.warning(
                            "Recovered stuck queue item %s (%s) and requeued it",
                            item["id"],
                            recovery.get("reason") or "self-heal",
                        )
                        requeued_by_self_heal = True
                        update_queue_progress(item["id"], i, "")
                        _emit_ui_event(
                            "queue", "dashboard", "nav", min_interval=0.2
                        )
                        break
                    logger.error(f"Download failed for {ep_url}: {e}")
                    attempt_details = getattr(e, "attempt_details", None) or []
                    errors.append(
                        {
                            "url": ep_url,
                            "error": str(e),
                            "providers_tried": [
                                detail.get("provider")
                                for detail in attempt_details
                                if detail.get("provider")
                            ],
                            "attempts": attempt_details,
                        }
                    )
                    update_queue_errors(item["id"], json.dumps(errors))
                    _emit_ui_event("queue", "dashboard", "nav", min_interval=0.35)

                # Check for cancellation after each episode
                if requeued_by_self_heal:
                    break
                if is_queue_cancelled(item["id"]):
                    logger.info(f"Download cancelled for queue item {item['id']}")
                    update_queue_progress(item["id"], i + 1, "")
                    _mark_download_activity("queue-cancelled")
                    _emit_ui_event("queue", "dashboard", "nav", min_interval=0.35)
                    break

            # Only set final status if not already cancelled
            if requeued_by_self_heal:
                continue
            if not is_queue_cancelled(item["id"]):
                update_queue_progress(item["id"], len(episodes), "")
                status = (
                    "failed" if errors and len(errors) == len(episodes) else "completed"
                )
                set_queue_status(item["id"], status)
                _mark_download_activity(f"queue-{status}")
                if status == "completed" and item.get("series_url"):
                    touch_series_last_downloaded(item.get("series_url"))
                record_audit_event(
                    "download.completed" if status == "completed" else "download.failed",
                    username=item.get("username"),
                    subject_type="download",
                    subject=item.get("title"),
                    details={
                        "queue_id": item["id"],
                        "series_url": item.get("series_url"),
                        "language": item.get("language"),
                        "provider": item.get("provider"),
                        "status": status,
                        "errors": errors[:4],
                    },
                )
                _dispatch_external_notification(
                    "Download completed" if status == "completed" else "Download failed",
                    (
                        f"{item.get('title') or 'Download'} finished successfully."
                        if status == "completed"
                        else f"{item.get('title') or 'Download'} failed after {len(errors)} error(s)."
                    ),
                    category="queue",
                    details={
                        "queue_id": item["id"],
                        "title": item.get("title"),
                        "status": status,
                        "provider": item.get("provider"),
                        "language": item.get("language"),
                    },
                )
                _emit_ui_event("queue", "dashboard", "library", "nav")

        except Exception as e:
            logger.error(f"Queue worker error: {e}", exc_info=True)
            time.sleep(3)


def _ensure_queue_worker():
    """Start the queue worker thread once."""
    global _queue_worker_started
    if _queue_worker_started:
        return
    _queue_worker_started = True

    from .db import get_db

    conn = get_db()
    try:
        conn.execute(
            "UPDATE download_queue SET status = 'queued' WHERE status = 'running'"
        )
        conn.execute("UPDATE download_queue SET captcha_url = NULL")
        conn.commit()
    finally:
        conn.close()

    thread = threading.Thread(target=_queue_worker, daemon=True)
    thread.start()


def _self_heal_watchdog():
    while True:
        try:
            _self_heal_runtime["enabled"] = _self_heal_enabled()
            if not _self_heal_enabled():
                time.sleep(5)
                continue

            running_item = get_running()
            ffmpeg_state = get_ffmpeg_runtime_state()
            if not running_item or not ffmpeg_state.get("active"):
                time.sleep(4)
                continue

            last_progress_at = float(ffmpeg_state.get("last_progress_at") or 0.0)
            stall_timeout = int(ffmpeg_state.get("stall_timeout") or 0)
            if not last_progress_at or not stall_timeout:
                time.sleep(4)
                continue

            grace_period = max(150, min(stall_timeout // 2, 240))
            stale_for = time.time() - last_progress_at
            if stale_for < grace_period:
                time.sleep(4)
                continue

            attempts = (_peek_queue_recovery(running_item["id"]) or {}).get(
                "attempts", 0
            )
            reason = (
                f"Stalled ffmpeg detected after {int(stale_for)}s without progress"
            )
            logger.warning(
                "Experimental self-heal triggered for queue item %s: %s",
                running_item["id"],
                reason,
            )
            terminate_ffmpeg_process_tree(reason)
            if _attempt_self_heal_requeue(running_item, reason, ffmpeg_state):
                if attempts >= 3:
                    logger.warning(
                        "Queue item %s has been recovered multiple times and will remain queued for manual review if it stalls again.",
                        running_item["id"],
                    )
            time.sleep(8)
        except Exception as exc:
            logger.error("Self-heal watchdog error: %s", exc, exc_info=True)
            time.sleep(10)


def _ensure_self_heal_worker():
    global _self_heal_worker_started
    with _self_heal_worker_lock:
        if _self_heal_worker_started:
            return
        _self_heal_worker_started = True

    thread = threading.Thread(
        target=_self_heal_watchdog,
        daemon=True,
        name="aniworld-self-heal",
    )
    thread.start()


def _run_autosync_for_job(job):
    """Check a single autosync job for new/missing episodes and queue them."""
    import os
    from datetime import datetime
    from pathlib import Path

    job_id = job["id"]
    with _syncing_jobs_lock:
        if job_id in _syncing_jobs:
            logger.info("Auto-sync skipped job %d - already running", job_id)
            return
        _syncing_jobs.add(job_id)

    try:
        prov = resolve_provider(job["series_url"])
        if not prov.series_cls or not prov.season_cls:
            logger.warning(
                "Auto-sync skipped job %d for episode-only source: %s",
                job_id,
                job["series_url"],
            )
            update_autosync_job(
                job_id,
                last_check=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            )
            return
        series = prov.series_cls(url=job["series_url"])

        lang_sep = os.environ.get("ANIWORLD_LANG_SEPARATION", "0") == "1"
        # Only use lang_sep for "All Languages" when the global setting is enabled;
        # otherwise scan root directory to avoid phantom missing-episode detection.
        if job.get("language") == "All Languages" and not lang_sep:
            logger.warning(
                "Auto-sync job '%s' uses 'All Languages' but lang_separation is off - scanning root.",
                job.get("title", "?"),
            )

        lang_folder_map = {
            "German Dub": "german-dub",
            "English Sub": "english-sub",
            "German Sub": "german-sub",
            "English Dub": "english-dub",
        }

        target_languages = []
        if job.get("language") == "All Languages":
            disable_eng_sub = os.environ.get("ANIWORLD_DISABLE_ENGLISH_SUB", "0") == "1"
            for lang in lang_folder_map.keys():
                if disable_eng_sub and lang == "English Sub":
                    continue
                target_languages.append(lang)
        else:
            target_languages.append(job["language"])

        total_new_queued = 0
        total_episodes_found = 0
        diff_preview = []
        queued_preview = []
        skipped_preview = []

        def _episode_label(season_number, episode_number):
            return f"S{int(season_number):02d}E{int(episode_number):03d}"

        for target_lang in target_languages:
            job_lang_folder = lang_folder_map.get(
                target_lang, target_lang.lower().replace(" ", "-")
            )

            raw = os.environ.get("ANIWORLD_DOWNLOAD_PATH", "")
            if raw:
                dl_base = Path(raw).expanduser()
                if not dl_base.is_absolute():
                    dl_base = Path.home() / dl_base
            else:
                dl_base = Path.home() / "Downloads"

            scan_roots = [dl_base]
            for cp in get_custom_paths():
                cp_path = Path(cp["path"]).expanduser()
                if not cp_path.is_absolute():
                    cp_path = Path.home() / cp_path
                scan_roots.append(cp_path)

            # Build set of downloaded (season, episode) on disk
            downloaded_eps = set()
            title_clean = (
                getattr(series, "title_cleaned", None) or getattr(series, "title", "")
            ).lower()
            if title_clean:
                ep_re = re.compile(r"S(\d{2})E(\d{2,3})", re.IGNORECASE)
                all_bases = []
                for root in scan_roots:
                    if lang_sep:
                        all_bases.append(root / job_lang_folder)
                    else:
                        all_bases.append(root)
                for base in all_bases:
                    if not base.is_dir():
                        continue
                    for folder in base.iterdir():
                        if not folder.is_dir() or not folder.name.lower().startswith(
                            title_clean
                        ):
                            continue
                        for f in folder.rglob("*"):
                            if f.is_file():
                                m = ep_re.search(f.name)
                                if m:
                                    downloaded_eps.add(
                                        (int(m.group(1)), int(m.group(2)))
                                    )

            # Collect all episode URLs that are NOT yet downloaded
            missing_episodes = []
            missing_labels = []
            lang_total_found = 0
            for season in series.seasons:
                season_obj = prov.season_cls(url=season.url, series=series)
                for ep in season_obj.episodes:
                    # Depending on provider, might need to pre-filter by language here
                    # But the downloader expects full episode URLs and it will pick the right language within them.
                    lang_total_found += 1
                    key = (ep.season.season_number, ep.episode_number)
                    if key not in downloaded_eps:
                        missing_episodes.append(ep.url)
                        missing_labels.append(
                            _episode_label(
                                ep.season.season_number,
                                ep.episode_number,
                            )
                        )

            # In "All Languages" mode we want to make sure the specific language is actually
            # available on this episode before downloading? For VOE/Vidoza, it downloads what is chosen.
            # If a language isn't available, the extractor fails, which is fine (handled in queue).
            # But the queue item will contain episodes.

            # We use max of lang_total_found for updating stats (usually they are same across languages)
            if lang_total_found > total_episodes_found:
                total_episodes_found = lang_total_found

            if missing_episodes:
                conflict_guard = _filter_conflicting_queue_episodes(
                    job["series_url"],
                    target_lang,
                    missing_episodes,
                )
                queueable_episodes = conflict_guard["episodes"]
                queued_labels = missing_labels[: len(queueable_episodes)]
                skipped_labels = missing_labels[len(queueable_episodes) :]
                diff_preview.append(
                    {
                        "language": target_lang,
                        "episodes_found": lang_total_found,
                        "missing_count": len(missing_labels),
                        "missing_sample": missing_labels[:12],
                    }
                )
                if not queueable_episodes:
                    logger.info(
                        "Auto-sync skipped '%s' (%s) - all %d episode(s) already queued/running",
                        job["title"],
                        target_lang,
                        len(missing_episodes),
                    )
                    skipped_preview.append(
                        {
                            "language": target_lang,
                            "reason": "already queued or running",
                            "labels": missing_labels[:12],
                        }
                    )
                    continue

                if conflict_guard["skipped"]:
                    logger.info(
                        "Auto-sync trimmed %d conflicting episode(s) for '%s' (%s)",
                        conflict_guard["skipped"],
                        job["title"],
                        target_lang,
                    )
                    skipped_preview.append(
                        {
                            "language": target_lang,
                            "reason": "queue conflict",
                            "labels": skipped_labels[:12],
                        }
                    )

                total_new_queued += len(queueable_episodes)
                queued_provider = _resolve_autosync_job_provider(job, target_lang)
                add_to_queue(
                    title=job["title"],
                    series_url=job["series_url"],
                    episodes=queueable_episodes,
                    language=target_lang,
                    provider=queued_provider,
                    username=job.get("added_by"),
                    custom_path_id=job.get("custom_path_id"),
                    source="sync:all_langs"
                    if job.get("language") == "All Languages"
                    else "sync",
                )
                logger.info(
                    "Auto-sync queued %d episodes for '%s' (%s)",
                    len(queueable_episodes),
                    job["title"],
                    target_lang,
                )
                queued_preview.append(
                    {
                        "language": target_lang,
                        "labels": queued_labels[:12],
                        "queued_count": len(queueable_episodes),
                        "provider": queued_provider,
                    }
                )
                _emit_ui_event("autosync", "queue", "dashboard", "nav")

        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        update_fields = {
            "last_check": now_str,
            "episodes_found": total_episodes_found,
            "last_diff_json": json.dumps(diff_preview[-8:]),
            "last_queued_json": json.dumps(queued_preview[-8:]),
            "last_skipped_json": json.dumps(skipped_preview[-8:]),
            "last_error": "",
        }

        if total_new_queued > 0:
            update_fields["last_new_found"] = now_str

        update_autosync_job(job["id"], **update_fields)
        if job.get("series_url"):
            touch_series_last_synced(job.get("series_url"))
        if total_new_queued > 0:
            _dispatch_external_notification(
                "Auto-Sync found new episodes",
                f"{job.get('title') or 'Series'} queued {total_new_queued} new episode(s).",
                category="autosync",
                details={
                    "job_id": job["id"],
                    "title": job.get("title"),
                    "queued_count": total_new_queued,
                },
            )
        _emit_ui_event("autosync", "dashboard", "nav", "settings")
    except Exception as e:
        logger.error("Auto-sync failed for '%s': %s", job.get("title", "?"), e)
        from datetime import datetime

        update_autosync_job(
            job["id"],
            last_check=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            last_error=str(e),
        )
        _dispatch_external_notification(
            "Auto-Sync failed",
            f"{job.get('title') or 'Series'} could not be checked: {e}",
            category="autosync",
            details={"job_id": job["id"], "title": job.get("title")},
        )
        _emit_ui_event("autosync", "settings")
    finally:
        with _syncing_jobs_lock:
            _syncing_jobs.discard(job_id)


def _autosync_worker():
    """Background thread that periodically syncs all enabled autosync jobs.

    Uses short-polling (every 10 s) and checks each job's last_check
    against the configured interval so that schedule changes take effect
    immediately instead of blocking in a long sleep.
    """
    import os
    from datetime import datetime, timedelta

    while True:
        try:
            schedule_key = os.environ.get("ANIWORLD_SYNC_SCHEDULE", "0")
            interval = SYNC_SCHEDULE_MAP.get(schedule_key, 0)
            if not interval:
                time.sleep(10)
                continue

            now = datetime.utcnow()
            jobs = get_autosync_jobs()
            for job in jobs:
                if not job.get("enabled"):
                    continue
                # Per-job check: only run if enough time has elapsed
                last_check = job.get("last_check")
                if last_check:
                    try:
                        last_dt = datetime.strptime(last_check, "%Y-%m-%d %H:%M:%S")
                    except (ValueError, TypeError):
                        last_dt = datetime.min
                    if now < last_dt + timedelta(seconds=interval):
                        continue
                _run_autosync_for_job(job)

            time.sleep(10)
        except Exception as e:
            logger.error("Auto-sync worker error: %s", e, exc_info=True)
            time.sleep(30)


def _ensure_autosync_worker():
    """Start the auto-sync worker thread once."""
    global _autosync_worker_started
    if _autosync_worker_started:
        return
    _autosync_worker_started = True
    thread = threading.Thread(target=_autosync_worker, daemon=True)
    thread.start()


def _get_version():
    return display_version(VERSION)


def create_app(auth_enabled=False, sso_enabled=False, force_sso=False):
    import os

    app = Flask(__name__)
    app_version = _get_version()

    base_url = os.environ.get("ANIWORLD_WEB_BASE_URL", "").strip().rstrip("/")
    if base_url:
        from urllib.parse import urlparse

        parsed = urlparse(base_url)
        scheme = parsed.scheme or "https"
        host = parsed.netloc

        # WSGI middleware that overrides scheme/host before Flask sees the request
        _inner_wsgi = app.wsgi_app

        def _proxy_wsgi(environ, start_response):
            environ["wsgi.url_scheme"] = scheme
            if host:
                environ["HTTP_HOST"] = host
            return _inner_wsgi(environ, start_response)

        app.wsgi_app = _proxy_wsgi

    if auth_enabled:
        from .auth import (
            auth_bp,
            get_current_user,
            get_or_create_secret_key,
            init_oidc,
            login_required,
            refresh_session_role,
        )
        from .db import has_any_admin, init_db

        app.secret_key = get_or_create_secret_key()
        app.config["SESSION_COOKIE_HTTPONLY"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
        if base_url.startswith("https"):
            app.config["SESSION_COOKIE_SECURE"] = True
        app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 hours

        csrf = CSRFProtect()

        init_db()
        app.register_blueprint(auth_bp)
        csrf.init_app(app)

        if sso_enabled:
            init_oidc(app, force_sso=force_sso)
        else:
            app.config["OIDC_ENABLED"] = False
            app.config["OIDC_DISPLAY_NAME"] = "SSO"
            app.config["OIDC_ADMIN_USER"] = None
            app.config["OIDC_ADMIN_SUBJECT"] = None
            app.config["FORCE_SSO"] = False

        @app.before_request
        def _check_setup():
            if request.endpoint and request.endpoint.startswith("auth."):
                return None
            if request.endpoint == "static":
                return None
            if not app.config.get("FORCE_SSO", False) and not has_any_admin():
                return redirect(url_for("auth.setup"))
            return None

        @app.before_request
        def _refresh_role():
            return refresh_session_role()

        @app.context_processor
        def _inject_auth():
            user = get_current_user()
            username = (
                user.get("username")
                if isinstance(user, dict)
                else getattr(user, "username", None)
            )
            return {
                "current_user": user,
                "auth_enabled": True,
                "oidc_enabled": app.config.get("OIDC_ENABLED", False),
                "oidc_display_name": app.config.get("OIDC_DISPLAY_NAME", "SSO"),
                "force_sso": app.config.get("FORCE_SSO", False),
                "app_version": app_version,
                "experimental_flags": _experimental_flags(),
                "ui_mode": _normalize_ui_mode(
                    get_user_preference(username, "ui_mode", "cozy")
                ),
                "ui_locale": _normalize_ui_locale(
                    get_user_preference(username, "ui_locale", "en")
                ),
                "ui_scale": get_user_preference(username, "ui_scale", "100"),
                "ui_theme": _normalize_ui_theme(
                    get_user_preference(username, "ui_theme", "ocean")
                ),
                "ui_radius": _normalize_ui_radius(
                    get_user_preference(username, "ui_radius", "soft")
                ),
                "ui_motion": _normalize_ui_motion(
                    get_user_preference(username, "ui_motion", "normal")
                ),
                "ui_width": get_user_preference(username, "ui_width", "standard"),
                "ui_modal_width": _normalize_ui_modal_width(
                    get_user_preference(username, "ui_modal_width", "standard")
                ),
                "ui_nav_size": _normalize_ui_nav_size(
                    get_user_preference(username, "ui_nav_size", "standard")
                ),
                "ui_table_density": _normalize_ui_table_density(
                    get_user_preference(
                        username, "ui_table_density", "standard"
                    )
                ),
                "ui_background": _normalize_ui_background(
                    get_user_preference(username, "ui_background", "dynamic")
                ),
                "search_default_sort": _normalize_search_default_sort(
                    get_user_preference(username, "search_default_sort", "source")
                ),
                "search_default_genres": _normalize_search_default_genres(
                    get_user_preference(username, "search_default_genres", "")
                ),
                "search_default_year_from": _normalize_search_default_year(
                    get_user_preference(username, "search_default_year_from", "")
                ),
                "search_default_year_to": _normalize_search_default_year(
                    get_user_preference(username, "search_default_year_to", "")
                ),
                "search_default_favorites_only": _normalize_pref_bool(
                    get_user_preference(
                        username, "search_default_favorites_only", "0"
                    )
                ),
                "search_default_downloaded_only": _normalize_pref_bool(
                    get_user_preference(
                        username, "search_default_downloaded_only", "0"
                    )
                ),
            }
    else:

        @app.context_processor
        def _inject_no_auth():
            return {
                "current_user": None,
                "auth_enabled": False,
                "oidc_enabled": False,
                "oidc_display_name": "SSO",
                "force_sso": False,
                "app_version": app_version,
                "experimental_flags": _experimental_flags(),
                "ui_mode": _normalize_ui_mode(
                    get_user_preference(None, "ui_mode", "cozy")
                ),
                "ui_locale": _normalize_ui_locale(
                    get_user_preference(None, "ui_locale", "en")
                ),
                "ui_scale": get_user_preference(None, "ui_scale", "100"),
                "ui_theme": _normalize_ui_theme(
                    get_user_preference(None, "ui_theme", "ocean")
                ),
                "ui_radius": _normalize_ui_radius(
                    get_user_preference(None, "ui_radius", "soft")
                ),
                "ui_motion": _normalize_ui_motion(
                    get_user_preference(None, "ui_motion", "normal")
                ),
                "ui_width": get_user_preference(None, "ui_width", "standard"),
                "ui_modal_width": _normalize_ui_modal_width(
                    get_user_preference(None, "ui_modal_width", "standard")
                ),
                "ui_nav_size": _normalize_ui_nav_size(
                    get_user_preference(None, "ui_nav_size", "standard")
                ),
                "ui_table_density": _normalize_ui_table_density(
                    get_user_preference(None, "ui_table_density", "standard")
                ),
                "ui_background": _normalize_ui_background(
                    get_user_preference(None, "ui_background", "dynamic")
                ),
                "search_default_sort": _normalize_search_default_sort(
                    get_user_preference(None, "search_default_sort", "source")
                ),
                "search_default_genres": _normalize_search_default_genres(
                    get_user_preference(None, "search_default_genres", "")
                ),
                "search_default_year_from": _normalize_search_default_year(
                    get_user_preference(None, "search_default_year_from", "")
                ),
                "search_default_year_to": _normalize_search_default_year(
                    get_user_preference(None, "search_default_year_to", "")
                ),
                "search_default_favorites_only": _normalize_pref_bool(
                    get_user_preference(None, "search_default_favorites_only", "0")
                ),
                "search_default_downloaded_only": _normalize_pref_bool(
                    get_user_preference(
                        None, "search_default_downloaded_only", "0"
                    )
                ),
            }

    # Initialize download queue, custom paths and autosync (works with or without auth)
    init_queue_db()
    init_custom_paths_db()
    init_autosync_db()
    init_favorites_db()
    init_series_meta_db()
    init_search_history_db()
    init_user_preferences_db()
    init_audit_log_db()
    init_provider_score_history_db()

    # Wire up captcha hooks so the Playwright module can signal the Web UI
    from ..playwright import captcha as _captcha_mod
    _captcha_mod._on_captcha_start = set_captcha_url
    _captcha_mod._on_captcha_end = clear_captcha_url

    # In debug mode, Flask's reloader runs this in both the parent and child
    # process. Only start workers in the child (actual server) process
    # to avoid duplicate ffmpeg downloads.
    _debug = os.getenv("ANIWORLD_DEBUG_MODE", "0") == "1"
    if not _debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        _ensure_queue_worker()
        _ensure_autosync_worker()
        _ensure_self_heal_worker()
        _ensure_auto_update_worker()

    @app.after_request
    def _set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        return response

    @app.before_request
    def _enforce_json_content_type():
        """Reject non-JSON POST/PUT/DELETE on API routes to prevent form-based CSRF bypass."""
        if request.method in ("POST", "PUT", "DELETE") and request.path.startswith(
            "/api/"
        ):
            if request.content_length and request.content_length > 0:
                ct = request.content_type or ""
                if not ct.startswith("application/json"):
                    return jsonify(
                        {"error": "Content-Type must be application/json"}
                    ), 415

    def _series_modal_template_context():
        return {
            "lang_labels": LANG_LABELS,
            "sto_lang_labels": {"1": "German Dub", "2": "English Dub"},
            "supported_providers": _ordered_working_providers(),
        }

    @app.route("/")
    def index():
        return render_template("index.html", **_series_modal_template_context())

    @app.route("/stats")
    def stats_page():
        return render_template("stats.html")

    @app.route("/favorites")
    def favorites_page():
        return render_template("favorites.html", **_series_modal_template_context())

    @app.route("/timeline")
    def timeline_page():
        return render_template("timeline.html")

    @app.route("/radar")
    def radar_page():
        return render_template("radar.html")

    @app.route("/link-import")
    def link_import_page():
        return render_template(
            "link_import.html", **_series_modal_template_context()
        )

    @app.route("/api/link-import/resolve", methods=["POST"])
    def api_link_import_resolve():
        data = request.get_json(silent=True) or {}
        raw_url = str(data.get("url") or "").strip()
        if not raw_url:
            return jsonify({"error": "url is required"}), 400
        try:
            return jsonify(_resolve_link_import_target(raw_url))
        except Exception as exc:
            logger.warning("Link import resolve failed: %s", exc)
            return jsonify({"error": str(exc)}), 400

    @app.route("/api/search", methods=["POST"])
    def api_search():
        data = request.get_json(silent=True) or {}
        keyword = (data.get("keyword") or "").strip()
        site = (data.get("site") or "aniworld").strip()
        if not keyword:
            return jsonify({"error": "keyword is required"}), 400

        results = []

        if site == "filmpalast":
            filmpalast_results = query_filmpalast(keyword) or []
            if isinstance(filmpalast_results, dict):
                filmpalast_results = [filmpalast_results]
            for item in filmpalast_results:
                link = (item.get("link") or "").strip()
                if not link:
                    continue
                if link.startswith("/"):
                    url = f"https://filmpalast.to{link}"
                elif link.startswith("http"):
                    url = link
                else:
                    url = f"https://filmpalast.to/{link.lstrip('/')}"
                results.append(
                    {
                        "title": item.get("title", "Unknown"),
                        "url": url,
                        "poster_url": item.get("poster_url") or "",
                    }
                )
        elif site == "sto":
            # s.to search
            sto_results = query_s_to(keyword) or []
            if isinstance(sto_results, dict):
                sto_results = [sto_results]
            for item in sto_results:
                link = item.get("link", "")
                if _STO_SERIES_LINK_PATTERN.match(link):
                    title = (
                        item.get("title", "Unknown")
                        .replace("<em>", "")
                        .replace("</em>", "")
                    )
                    results.append(
                        {
                            "title": title,
                            "url": f"https://s.to{link}",
                            "poster_url": _absolute_asset_url(
                                "https://s.to",
                                item.get("poster_url") or "",
                            )
                            or "",
                        }
                    )
        else:
            # AniWorld search
            aw_results = aniworld_query(keyword) or []
            if isinstance(aw_results, dict):
                aw_results = [aw_results]
            for item in aw_results:
                link = item.get("link", "")
                if _SERIES_LINK_PATTERN.match(link):
                    title = (
                        item.get("title", "Unknown")
                        .replace("<em>", "")
                        .replace("</em>", "")
                    )
                    results.append(
                        {
                            "title": title,
                            "url": f"https://aniworld.to{link}",
                        }
                    )

        if results:
            username, _ = _get_current_user_info()
            record_search_query(site, keyword, username=username)
        return jsonify({"results": results})

    @app.route("/api/search/suggestions")
    def api_search_suggestions():
        site = (request.args.get("site") or "aniworld").strip()
        query = (request.args.get("q") or "").strip()
        username, _ = _get_current_user_info()
        suggestions = get_search_suggestions(
            site, query=query, limit=8, username=username
        )
        recent = list_recent_searches(site, limit=6, username=username)
        return jsonify({"suggestions": suggestions, "recent": recent})

    @app.route("/api/series")
    def api_series():
        url = request.args.get("url", "").strip()
        if not url:
            return jsonify({"error": "url is required"}), 400

        try:
            prov = resolve_provider(url)
            target = prov.series_cls(url=url) if prov.series_cls else prov.episode_cls(url=url)
            poster = _absolute_asset_url(
                url,
                getattr(target, "poster_url", None) or getattr(target, "image_url", None),
            )
            title = getattr(target, "title", None) or getattr(target, "title_de", None)
            upsert_series_meta(
                series_url=url,
                title=title,
                poster_url=poster,
                description=getattr(target, "description", ""),
                release_year=str(getattr(target, "release_year", "") or ""),
                genres=getattr(target, "genres", []) or [],
            )
            username, _ = _get_current_user_info()
            touch_favorite(url, username=username)
            series_meta = get_series_meta(url) or {}
            return jsonify(
                {
                    "title": title,
                    "poster_url": poster,
                    "description": getattr(target, "description", ""),
                    "genres": getattr(target, "genres", []),
                    "release_year": getattr(target, "release_year", ""),
                    "is_favorite": bool(get_favorite(url, username=username)),
                    "auto_sync_supported": bool(prov.series_cls),
                    "last_downloaded_at": series_meta.get("last_downloaded_at"),
                    "last_synced_at": series_meta.get("last_synced_at"),
                }
            )
        except Exception as e:
            logger.error(f"Series fetch failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/seasons")
    def api_seasons():
        url = request.args.get("url", "").strip()
        if not url:
            return jsonify({"error": "url is required"}), 400

        try:
            prov = resolve_provider(url)
            if not prov.series_cls or not prov.season_cls:
                return jsonify(
                    {
                        "seasons": [
                            {
                                "url": url,
                                "season_number": 1,
                                "episode_count": 1,
                                "are_movies": True,
                            }
                        ]
                    }
                )
            series = prov.series_cls(url=url)
            seasons_data = []
            for season in series.seasons:
                seasons_data.append(
                    {
                        "url": season.url,
                        "season_number": season.season_number,
                        "episode_count": season.episode_count,
                        "are_movies": getattr(season, "are_movies", False),
                    }
                )
            return jsonify({"seasons": seasons_data})
        except Exception as e:
            logger.error(f"Seasons fetch failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/episodes")
    def api_episodes():
        url = request.args.get("url", "").strip()
        include_provider_details = request.args.get("include_providers", "0") == "1"
        if not url:
            return jsonify({"error": "url is required"}), 400

        try:
            prov = resolve_provider(url)
            if not prov.series_cls or not prov.season_cls:
                episode = prov.episode_cls(url=url)
                downloaded = bool(getattr(episode, "is_downloaded", {}).get("exists"))
                if not downloaded:
                    for custom_path in get_custom_paths():
                        episode.selected_path = str(
                            _resolve_base_path(custom_path.get("path"))
                        )
                        downloaded = bool(
                            getattr(episode, "is_downloaded", {}).get("exists")
                        )
                        if downloaded:
                            break
                provider_info = {}
                providers_flat = []
                if include_provider_details:
                    try:
                        provider_info = _extract_provider_info(episode.provider_data)
                    except Exception:
                        provider_info = {}
                    providers_flat = _flatten_provider_map(provider_info)
                return jsonify(
                    {
                        "episodes": [
                            {
                                "url": episode.url,
                                "episode_number": 1,
                                "title_de": getattr(episode, "title", None)
                                or getattr(episode, "title_de", "")
                                or "",
                                "title_en": "",
                                "downloaded": downloaded,
                                "languages": _episode_language_labels_for_ui(
                                    episode, allow_provider_lookup=True
                                ),
                                "providers_by_language": provider_info,
                                "providers_flat": providers_flat,
                            }
                        ]
                    }
                )
            # Pass series to avoid broken series URL reconstruction in s.to
            # season model (its fallback splits on "-" which fails)
            series_url = re.sub(r"/staffel-\d+/?$", "", url)
            series_url = re.sub(r"/filme/?$", "", series_url)
            try:
                series = prov.series_cls(url=series_url)
            except Exception:
                series = None
            season = prov.season_cls(url=url, series=series)

            # Scan download directory for downloaded episodes.
            # Uses S##E### filename matching so it works regardless of
            # which NAMING_TEMPLATE was active when files were downloaded.
            from pathlib import Path

            lang_sep = os.environ.get("ANIWORLD_LANG_SEPARATION", "0") == "1"
            lang_folders = ["german-dub", "english-sub", "german-sub", "english-dub"]

            raw = os.environ.get("ANIWORLD_DOWNLOAD_PATH", "")
            if raw:
                dl_base = Path(raw).expanduser()
                if not dl_base.is_absolute():
                    dl_base = Path.home() / dl_base
            else:
                dl_base = Path.home() / "Downloads"

            # Collect all scan roots: default + custom paths
            scan_roots = [dl_base]
            for cp in get_custom_paths():
                cp_path = Path(cp["path"]).expanduser()
                if not cp_path.is_absolute():
                    cp_path = Path.home() / cp_path
                scan_roots.append(cp_path)

            # Build set of (season_num, episode_num) found on disk
            downloaded_eps = set()
            try:
                title_clean = ""
                if series:
                    title_clean = (
                        getattr(series, "title_cleaned", None)
                        or getattr(series, "title", "")
                    ).lower()
                if title_clean:
                    ep_re = re.compile(r"S(\d{2})E(\d{2,3})", re.IGNORECASE)
                    all_bases = []
                    for root in scan_roots:
                        if lang_sep:
                            all_bases.extend([root / lf for lf in lang_folders])
                        else:
                            all_bases.append(root)
                    for base in all_bases:
                        if not base.is_dir():
                            continue
                        for folder in base.iterdir():
                            if (
                                not folder.is_dir()
                                or not folder.name.lower().startswith(title_clean)
                            ):
                                continue
                            for f in folder.rglob("*"):
                                if f.is_file():
                                    m = ep_re.search(f.name)
                                    if m:
                                        downloaded_eps.add(
                                            (int(m.group(1)), int(m.group(2)))
                                        )
            except Exception:
                pass

            allow_episode_language_lookup = prov.name in ("SerienStream", "AniWorld")

            episodes_data = []
            for ep in season.episodes:
                downloaded = (
                    ep.season.season_number,
                    ep.episode_number,
                ) in downloaded_eps

                provider_info = {}
                providers_flat = []
                if include_provider_details:
                    try:
                        provider_info = _extract_provider_info(ep.provider_data)
                    except Exception:
                        provider_info = {}
                    providers_flat = _flatten_provider_map(provider_info)

                episodes_data.append(
                    {
                        "url": ep.url,
                        "episode_number": ep.episode_number,
                        "title_de": getattr(ep, "title_de", ""),
                        "title_en": getattr(ep, "title_en", ""),
                        "downloaded": downloaded,
                        "languages": _episode_language_labels_for_ui(
                            ep,
                            allow_provider_lookup=allow_episode_language_lookup,
                        ),
                        "providers_by_language": provider_info,
                        "providers_flat": providers_flat,
                    }
                )
            return jsonify({"episodes": episodes_data})
        except Exception as e:
            logger.error(f"Episodes fetch failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/providers")
    def api_providers():
        url = request.args.get("url", "").strip()
        if not url:
            return jsonify({"error": "url is required"}), 400

        try:
            prov = resolve_provider(url)
            episode = prov.episode_cls(url=url)
            provider_info = _extract_provider_info(episode.provider_data)
            default_language = next(iter(provider_info.keys()), None)
            availability = []

            if hasattr(episode, "provider_availability"):
                availability = list(getattr(episode, "provider_availability") or [])
            else:
                seen_names = set()
                for language, providers in provider_info.items():
                    for provider_name in providers:
                        if provider_name in seen_names:
                            continue
                        seen_names.add(provider_name)
                        availability.append(
                            {
                                "name": provider_name,
                                "supported": True,
                                "languages": [
                                    lang_name
                                    for lang_name, items in provider_info.items()
                                    if provider_name in items
                                ],
                            }
                        )

            return jsonify(
                {
                    "providers": provider_info,
                    "languages": list(provider_info.keys()),
                    "default_language": default_language,
                    "episode_only": not bool(prov.series_cls),
                    "availability": availability,
                }
            )
        except Exception as e:
            logger.error(f"Providers fetch failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/download", methods=["POST"])
    def api_download():
        data = request.get_json(silent=True) or {}
        episodes = data.get("episodes", [])
        language = data.get("language", "German Dub")
        provider = data.get("provider", "VOE")
        title = data.get("title", "Unknown")
        series_url = data.get("series_url", "")

        if not episodes:
            return jsonify({"error": "episodes list is required"}), 400

        if (
            language == "English Sub"
            and os.environ.get("ANIWORLD_DISABLE_ENGLISH_SUB", "0") == "1"
        ):
            return jsonify({"error": "English Sub downloads are disabled"}), 403

        username = None
        if auth_enabled:
            user = get_current_user()
            if user:
                username = (
                    user.get("username")
                    if isinstance(user, dict)
                    else getattr(user, "username", None)
                )

        custom_path_id = data.get("custom_path_id")

        conflict_guard = _filter_conflicting_queue_episodes(
            series_url,
            language,
            episodes,
        )
        queueable_episodes = conflict_guard["episodes"]
        if not queueable_episodes:
            return (
                jsonify(
                    {
                        "error": "Selected episodes are already queued or currently downloading.",
                        "type": "queue_conflict",
                        "skipped_conflicts": conflict_guard["skipped"],
                        "conflicts": conflict_guard["conflicts"],
                    }
                ),
                409,
            )

        queue_id = add_to_queue(
            title,
            series_url,
            queueable_episodes,
            language,
            provider,
            username,
            custom_path_id=custom_path_id,
        )
        _record_user_event(
            "queue.added",
            subject_type="download",
            subject=title,
            details={
                "queue_id": queue_id,
                "series_url": series_url,
                "episodes": len(queueable_episodes),
                "language": language,
                "provider": provider,
                "custom_path_id": custom_path_id,
                "skipped_conflicts": conflict_guard["skipped"],
            },
        )
        _emit_ui_event("queue", "dashboard", "nav")
        return jsonify(
            {
                "queue_id": queue_id,
                "queued_episodes": len(queueable_episodes),
                "skipped_conflicts": conflict_guard["skipped"],
                "conflicts": conflict_guard["conflicts"],
            }
        )

    @app.route("/api/queue")
    def api_queue():
        from ..models.common.common import get_ffmpeg_progress

        items = get_queue()
        ffmpeg_pct = get_ffmpeg_progress()
        return jsonify(
            {
                "items": items,
                "ffmpeg_progress": ffmpeg_pct,
                "runtime": get_ffmpeg_runtime_state(),
            }
        )

    @app.route("/api/queue/<int:queue_id>", methods=["DELETE"])
    def api_queue_remove(queue_id):
        queue_item = next((item for item in get_queue() if item["id"] == queue_id), None)
        ok, err = remove_from_queue(queue_id)
        if not ok:
            return jsonify({"error": err}), 400
        _record_user_event(
            "queue.removed",
            subject_type="download",
            subject=(queue_item or {}).get("title") or f"Queue #{queue_id}",
            details={"queue_id": queue_id},
        )
        _emit_ui_event("queue", "dashboard", "nav")
        return jsonify({"ok": True})

    @app.route("/api/queue/<int:queue_id>/cancel", methods=["POST"])
    def api_queue_cancel(queue_id):
        queue_item = next((item for item in get_queue() if item["id"] == queue_id), None)
        ok, err = cancel_queue_item(queue_id)
        if not ok:
            return jsonify({"error": err}), 400
        _record_user_event(
            "queue.cancelled",
            subject_type="download",
            subject=(queue_item or {}).get("title") or f"Queue #{queue_id}",
            details={"queue_id": queue_id},
        )
        _emit_ui_event("queue", "dashboard", "nav")
        return jsonify({"ok": True})

    @app.route("/api/queue/<int:queue_id>/hard-cancel", methods=["POST"])
    def api_queue_hard_cancel(queue_id):
        queue_item = next((item for item in get_queue() if item["id"] == queue_id), None)
        if not queue_item:
            return jsonify({"error": "Item not found"}), 404
        if queue_item.get("status") != "cancelled" or not queue_item.get("current_url"):
            return (
                jsonify(
                    {
                        "error": "Hard cancel is only available after a running item has been cancelled.",
                    }
                ),
                400,
            )

        reason = f"hard cancel requested for queue item {queue_id}"
        killed = terminate_ffmpeg_process_tree(reason)
        update_queue_progress(
            queue_id,
            int(queue_item.get("current_episode") or 0),
            "",
        )
        _record_user_event(
            "queue.hard_cancelled",
            subject_type="download",
            subject=(queue_item or {}).get("title") or f"Queue #{queue_id}",
            details={
                "queue_id": queue_id,
                "killed_process": bool(killed),
            },
        )
        _emit_ui_event("queue", "dashboard", "nav")
        return jsonify({"ok": True, "killed_process": bool(killed)})

    @app.route("/api/queue/<int:queue_id>/move", methods=["POST"])
    def api_queue_move(queue_id):
        data = request.get_json(silent=True) or {}
        direction = data.get("direction", "").strip()
        if direction not in ("up", "down"):
            return jsonify({"error": "direction must be 'up' or 'down'"}), 400
        ok, err = move_queue_item(queue_id, direction)
        if not ok:
            return jsonify({"error": err}), 400
        _emit_ui_event("queue")
        return jsonify({"ok": True})

    @app.route("/api/queue/<int:queue_id>/retry", methods=["POST"])
    def api_queue_retry(queue_id):
        queue_items = {item["id"]: item for item in get_queue()}
        original = queue_items.get(queue_id)
        provider_override = _pick_retry_provider(original) if original else None
        new_id, err = retry_queue_item(queue_id, provider_override=provider_override)
        if err:
            return jsonify({"error": err}), 400
        _record_user_event(
            "queue.retried",
            subject_type="download",
            subject=(original or {}).get("title") or f"Queue #{queue_id}",
            details={
                "from_queue_id": queue_id,
                "new_queue_id": new_id,
                "provider": provider_override or (original or {}).get("provider"),
            },
        )
        _emit_ui_event("queue", "dashboard", "nav")
        return jsonify(
            {
                "ok": True,
                "queue_id": new_id,
                "provider": provider_override or (original or {}).get("provider"),
            }
        )

    @app.route("/api/queue/retry-failed", methods=["POST"])
    def api_queue_retry_failed():
        overrides = {}
        for item in get_queue():
            if item.get("status") != "failed":
                continue
            overrides[item["id"]] = _pick_retry_provider(item)
        created = retry_failed_queue_items(provider_overrides=overrides)
        if created:
            _record_user_event(
                "queue.retry_failed",
                subject_type="download",
                subject="Failed Queue Items",
                details={"created": created},
            )
            _emit_ui_event("queue", "dashboard", "nav")
        return jsonify({"ok": True, "created": created})

    @app.route("/api/queue/completed", methods=["DELETE"])
    def api_queue_clear():
        clear_completed()
        _record_user_event(
            "queue.cleared_finished",
            subject_type="download",
            subject="Finished Queue Items",
        )
        _emit_ui_event("queue", "dashboard", "nav")
        return jsonify({"ok": True})

    # ── Captcha endpoints ─────────────────────────────────────────────────────

    @app.route("/api/captcha/<int:queue_id>/screenshot")
    def api_captcha_screenshot(queue_id):
        """Return the latest JPEG screenshot of the Playwright captcha page."""
        from ..playwright.captcha import _active_sessions, _active_sessions_lock
        from flask import Response

        with _active_sessions_lock:
            session = _active_sessions.get(queue_id)
        if not session:
            return "", 404
        data = session.get_screenshot()
        if not data:
            return "", 404
        return Response(
            data,
            mimetype="image/jpeg",
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate",
                "Pragma": "no-cache",
            },
        )

    @app.route("/api/captcha/<int:queue_id>/click", methods=["POST"])
    def api_captcha_click(queue_id):
        """Forward a click event (x, y) to the Playwright captcha browser."""
        from ..playwright.captcha import _active_sessions, _active_sessions_lock

        data = request.get_json(silent=True) or {}
        x = data.get("x")
        y = data.get("y")
        if x is None or y is None:
            return jsonify({"error": "x and y are required"}), 400
        with _active_sessions_lock:
            session = _active_sessions.get(queue_id)
        if not session:
            return jsonify({"error": "no active captcha session"}), 404
        session.enqueue_click(int(x), int(y))
        return jsonify({"ok": True})

    @app.route("/api/captcha/<int:queue_id>/status")
    def api_captcha_status(queue_id):
        """Return whether a captcha session is active and whether it has been solved."""
        from ..playwright.captcha import _active_sessions, _active_sessions_lock

        with _active_sessions_lock:
            session = _active_sessions.get(queue_id)
        if not session:
            return jsonify({"active": False})
        return jsonify({"active": True, "done": session.done})

    # ─────────────────────────────────────────────────────────────────────────

    @app.route("/captcha/<int:queue_id>")
    def captcha_page(queue_id):
        queue_item = next(
            (item for item in get_queue() if int(item.get("id") or 0) == queue_id),
            None,
        )
        return render_template(
            "captcha.html",
            queue_id=queue_id,
            queue_item=queue_item,
        )

    @app.route("/api/image-proxy")
    def api_image_proxy():
        source_url = (request.args.get("src") or "").strip()
        if not _image_proxy_allowed(source_url):
            return jsonify({"error": "image source is not allowed"}), 400

        try:
            response = GLOBAL_SESSION.get(
                source_url,
                headers={
                    "User-Agent": DEFAULT_USER_AGENT,
                    "Referer": "https://s.to/",
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                },
                timeout=20,
            )
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "image/jpeg")
            return Response(
                response.content,
                mimetype=content_type,
                headers={"Cache-Control": "public, max-age=1800"},
            )
        except Exception as exc:
            logger.warning("Image proxy failed for %s: %s", source_url, exc)
            return jsonify({"error": "image could not be loaded"}), 502

    @app.route("/library")
    def library_page():
        return render_template("library.html")

    @app.route("/settings")
    def settings_page():
        from pathlib import Path
        import platform

        env_path = Path.home() / ".aniworld" / ".env"
        if platform.system() != "Windows":
            display = "~/.aniworld/.env"
        else:
            display = str(env_path)
        return render_template(
            "settings.html",
            env_path=display,
            supported_providers=_ordered_working_providers(),
        )

    @app.route("/provider-health")
    def provider_health_page():
        return render_template("provider_health.html")

    @app.route("/diagnostics")
    def diagnostics_page():
        return render_template("diagnostics.html")

    @app.route("/maintenance")
    def maintenance_page():
        return render_template("maintenance.html")

    @app.route("/audit")
    def audit_page():
        return render_template("audit.html")

    @app.route("/api/random")
    def api_random():
        site = request.args.get("site", "aniworld").strip()
        if site == "sto":
            return jsonify({"error": "Random is not available for S.TO"}), 400
        url = random_anime()
        if url:
            return jsonify({"url": url})
        return jsonify({"error": "Failed to fetch random anime"}), 500

    # TTL cache for browse endpoints so long-running instances stay fresh
    import time as _time

    _browse_cache = {}
    _BROWSE_TTL = 3600  # 1 hour

    def _cached_browse(key, fetch_fn):
        now = _time.time()
        entry = _browse_cache.get(key)
        if entry and now - entry[0] < _BROWSE_TTL:
            return entry[1]
        results = fetch_fn()
        if results is not None:
            _browse_cache[key] = (now, results)
        return results

    @app.route("/api/new-animes")
    def api_new_animes():
        results = _cached_browse("new_animes", fetch_new_animes)
        if results is None:
            return jsonify({"error": "Failed to fetch new animes"}), 500
        return jsonify({"results": results})

    @app.route("/api/popular-animes")
    def api_popular_animes():
        results = _cached_browse("popular_animes", fetch_popular_animes)
        if results is None:
            return jsonify({"error": "Failed to fetch popular animes"}), 500
        return jsonify({"results": results})

    @app.route("/api/new-series")
    def api_new_series():
        results = _cached_browse("new_series", fetch_new_series)
        if results is None:
            return jsonify({"error": "Failed to fetch new series"}), 500
        return jsonify({"results": results})

    @app.route("/api/popular-series")
    def api_popular_series():
        results = _cached_browse("popular_series", fetch_popular_series)
        if results is None:
            return jsonify({"error": "Failed to fetch popular series"}), 500
        return jsonify({"results": results})

    @app.route("/api/new-episodes")
    def api_new_episodes():
        results = _cached_browse("new_episodes", fetch_new_episodes)
        if results is None:
            return jsonify({"error": "Failed to fetch new episodes"}), 500
        return jsonify({"results": results[:180]})

    @app.route("/api/downloaded-folders")
    def api_downloaded_folders():
        from pathlib import Path

        raw = os.environ.get("ANIWORLD_DOWNLOAD_PATH", "")
        if raw:
            p = Path(raw).expanduser()
            if not p.is_absolute():
                p = Path.home() / p
            dl_path = p
        else:
            dl_path = Path.home() / "Downloads"

        lang_sep = os.environ.get("ANIWORLD_LANG_SEPARATION", "0") == "1"
        lang_folders = ["german-dub", "english-sub", "german-sub", "english-dub"]

        # Collect all paths to scan (default + custom)
        scan_roots = [dl_path]
        for cp in get_custom_paths():
            cp_path = Path(cp["path"]).expanduser()
            if not cp_path.is_absolute():
                cp_path = Path.home() / cp_path
            scan_roots.append(cp_path)

        folders = set()
        for root in scan_roots:
            if lang_sep:
                bases = [root / lf for lf in lang_folders]
            else:
                bases = [root]
            for base in bases:
                if not base.is_dir():
                    continue
                for entry in base.iterdir():
                    if entry.is_dir():
                        folders.add(entry.name)
        return jsonify({"folders": sorted(folders)})

    @app.route("/api/settings", methods=["GET"])
    def api_settings():
        username, _ = _get_current_user_info()
        ui_preset = get_user_preference(username, "ui_preset", "custom")
        ui_locale = get_user_preference(username, "ui_locale", "en")
        ui_mode = get_user_preference(username, "ui_mode", "cozy")
        ui_scale = get_user_preference(username, "ui_scale", "100")
        ui_theme = get_user_preference(username, "ui_theme", "ocean")
        ui_radius = get_user_preference(username, "ui_radius", "soft")
        ui_motion = get_user_preference(username, "ui_motion", "normal")
        ui_width = get_user_preference(username, "ui_width", "standard")
        ui_modal_width = get_user_preference(
            username, "ui_modal_width", "standard"
        )
        ui_nav_size = get_user_preference(username, "ui_nav_size", "standard")
        ui_table_density = get_user_preference(
            username, "ui_table_density", "standard"
        )
        ui_background = get_user_preference(
            username, "ui_background", "dynamic"
        )
        search_default_sort = get_user_preference(
            username, "search_default_sort", "source"
        )
        search_default_genres = get_user_preference(
            username, "search_default_genres", ""
        )
        search_default_year_from = get_user_preference(
            username, "search_default_year_from", ""
        )
        search_default_year_to = get_user_preference(
            username, "search_default_year_to", ""
        )
        search_default_favorites_only = get_user_preference(
            username, "search_default_favorites_only", "0"
        )
        search_default_downloaded_only = get_user_preference(
            username, "search_default_downloaded_only", "0"
        )
        browser_notifications_enabled = get_user_preference(
            username, "browser_notifications_enabled", "0"
        )
        browser_notify_browse = get_user_preference(
            username, "browser_notify_browse", "1"
        )
        browser_notify_queue = get_user_preference(
            username, "browser_notify_queue", "1"
        )
        browser_notify_autosync = get_user_preference(
            username, "browser_notify_autosync", "1"
        )
        browser_notify_library = get_user_preference(
            username, "browser_notify_library", "1"
        )
        browser_notify_settings = get_user_preference(
            username, "browser_notify_settings", "1"
        )
        browser_notify_system = get_user_preference(
            username, "browser_notify_system", "1"
        )
        auto_open_captcha_tab = get_user_preference(
            username, "auto_open_captcha_tab", "0"
        )
        payload = _settings_payload(
            ui_preset=ui_preset,
            ui_locale=ui_locale,
            ui_mode=ui_mode,
            ui_scale=ui_scale,
            ui_theme=ui_theme,
            ui_radius=ui_radius,
            ui_motion=ui_motion,
            ui_width=ui_width,
            ui_modal_width=ui_modal_width,
            ui_nav_size=ui_nav_size,
            ui_table_density=ui_table_density,
            ui_background=ui_background,
            search_default_sort=search_default_sort,
            search_default_genres=search_default_genres,
            search_default_year_from=search_default_year_from,
            search_default_year_to=search_default_year_to,
            search_default_favorites_only=search_default_favorites_only,
            search_default_downloaded_only=search_default_downloaded_only,
            browser_notifications_enabled=browser_notifications_enabled,
            browser_notify_browse=browser_notify_browse,
            browser_notify_queue=browser_notify_queue,
            browser_notify_autosync=browser_notify_autosync,
            browser_notify_library=browser_notify_library,
            browser_notify_settings=browser_notify_settings,
            browser_notify_system=browser_notify_system,
            auto_open_captcha_tab=auto_open_captcha_tab,
        )
        payload.update(_server_network_info(app))
        return jsonify(payload)

    @app.route("/api/settings", methods=["PUT"])
    def api_settings_update():
        data = request.get_json(silent=True) or {}
        if "download_path" in data:
            os.environ[_ENV_DOWNLOAD_PATH] = str(data["download_path"]).strip()
        if "bandwidth_limit_kbps" in data:
            os.environ[_ENV_BANDWIDTH_LIMIT] = _normalize_bandwidth_limit(
                data["bandwidth_limit_kbps"]
            )
        if "download_backend" in data:
            os.environ[_ENV_DOWNLOAD_BACKEND] = _normalize_download_backend(
                data["download_backend"]
            )
        if "download_engine_rules" in data:
            os.environ[_ENV_DOWNLOAD_ENGINE_RULES] = _normalize_engine_rules(
                data["download_engine_rules"]
            )
        if "download_speed_profile" in data:
            os.environ[_ENV_DOWNLOAD_SPEED_PROFILE] = (
                _normalize_download_speed_profile(data["download_speed_profile"])
            )
        if "auto_provider_switch" in data:
            _set_bool_env(_ENV_AUTO_PROVIDER_SWITCH, data["auto_provider_switch"])
        if "rate_limit_guard" in data:
            _set_bool_env(_ENV_RATE_LIMIT_GUARD, data["rate_limit_guard"])
        if "preflight_check" in data:
            _set_bool_env(_ENV_PREFLIGHT_CHECK, data["preflight_check"])
        if "mp4_fallback_remux" in data:
            _set_bool_env(_ENV_MP4_FALLBACK_REMUX, data["mp4_fallback_remux"])
        if "provider_fallback_order" in data:
            os.environ[_ENV_PROVIDER_FALLBACK_ORDER] = (
                _normalize_provider_fallback_order(data["provider_fallback_order"])
            )
        if "disk_warn_gb" in data:
            os.environ[_ENV_DISK_WARN_GB] = _normalize_disk_guard_threshold(
                data["disk_warn_gb"], "10", 5000
            )
        if "disk_warn_percent" in data:
            os.environ[_ENV_DISK_WARN_PERCENT] = _normalize_disk_guard_threshold(
                data["disk_warn_percent"], "12", 100
            )
        if "library_auto_repair" in data:
            _set_bool_env(_ENV_LIBRARY_AUTO_REPAIR, data["library_auto_repair"])
        if "experimental_self_heal" in data:
            _set_bool_env(_ENV_EXPERIMENTAL_SELF_HEAL, data["experimental_self_heal"])
        if "safe_mode" in data:
            _set_bool_env(_ENV_SAFE_MODE, data["safe_mode"])
        if "lang_separation" in data:
            _set_bool_env(_ENV_LANG_SEPARATION, data["lang_separation"])
        if "disable_english_sub" in data:
            _set_bool_env(_ENV_DISABLE_ENGLISH_SUB, data["disable_english_sub"])
        if "experimental_filmpalast" in data:
            _set_bool_env(
                _ENV_EXPERIMENTAL_FILMPALAST, data["experimental_filmpalast"]
            )
        if "sync_schedule" in data:
            sched = str(data["sync_schedule"])
            if sched != "0" and sched not in SYNC_SCHEDULE_MAP:
                return jsonify({"error": f"Invalid sync_schedule: {sched}"}), 400
            os.environ[_ENV_SYNC_SCHEDULE] = sched
        if "sync_language" in data:
            lang = str(data["sync_language"])
            valid_langs = set(LANG_LABELS.values()) | {"All Languages"}
            if lang not in valid_langs:
                return jsonify({"error": f"Invalid sync_language: {lang}"}), 400
            os.environ[_ENV_SYNC_LANGUAGE] = lang
        if "sync_provider" in data:
            prov = str(data["sync_provider"])
            if prov not in WORKING_PROVIDERS:
                return jsonify({"error": f"Invalid sync_provider: {prov}"}), 400
            os.environ[_ENV_SYNC_PROVIDER] = prov
        username, _ = _get_current_user_info()
        if "ui_preset" in data:
            set_user_preference(
                username, "ui_preset", _normalize_ui_preset(data["ui_preset"])
            )
        if "ui_locale" in data:
            set_user_preference(
                username, "ui_locale", _normalize_ui_locale(data["ui_locale"])
            )
        if "ui_mode" in data:
            ui_mode = _normalize_ui_mode(data["ui_mode"])
            set_user_preference(username, "ui_mode", ui_mode)
        if "ui_scale" in data:
            set_user_preference(
                username, "ui_scale", _normalize_ui_scale(data["ui_scale"])
            )
        if "ui_theme" in data:
            set_user_preference(
                username, "ui_theme", _normalize_ui_theme(data["ui_theme"])
            )
        if "ui_radius" in data:
            set_user_preference(
                username, "ui_radius", _normalize_ui_radius(data["ui_radius"])
            )
        if "ui_motion" in data:
            set_user_preference(
                username, "ui_motion", _normalize_ui_motion(data["ui_motion"])
            )
        if "ui_width" in data:
            set_user_preference(
                username, "ui_width", _normalize_ui_width(data["ui_width"])
            )
        if "ui_modal_width" in data:
            set_user_preference(
                username,
                "ui_modal_width",
                _normalize_ui_modal_width(data["ui_modal_width"]),
            )
        if "ui_nav_size" in data:
            set_user_preference(
                username,
                "ui_nav_size",
                _normalize_ui_nav_size(data["ui_nav_size"]),
            )
        if "ui_table_density" in data:
            set_user_preference(
                username,
                "ui_table_density",
                _normalize_ui_table_density(data["ui_table_density"]),
            )
        if "ui_background" in data:
            set_user_preference(
                username,
                "ui_background",
                _normalize_ui_background(data["ui_background"]),
            )
        if "search_default_sort" in data:
            set_user_preference(
                username,
                "search_default_sort",
                _normalize_search_default_sort(data["search_default_sort"]),
            )
        if "search_default_genres" in data:
            set_user_preference(
                username,
                "search_default_genres",
                _normalize_search_default_genres(data["search_default_genres"]),
            )
        if "search_default_year_from" in data:
            set_user_preference(
                username,
                "search_default_year_from",
                _normalize_search_default_year(data["search_default_year_from"]),
            )
        if "search_default_year_to" in data:
            set_user_preference(
                username,
                "search_default_year_to",
                _normalize_search_default_year(data["search_default_year_to"]),
            )
        if "search_default_favorites_only" in data:
            set_user_preference(
                username,
                "search_default_favorites_only",
                _normalize_pref_bool(data["search_default_favorites_only"]),
            )
        if "search_default_downloaded_only" in data:
            set_user_preference(
                username,
                "search_default_downloaded_only",
                _normalize_pref_bool(data["search_default_downloaded_only"]),
            )
        if "browser_notifications_enabled" in data:
            set_user_preference(
                username,
                "browser_notifications_enabled",
                _normalize_pref_bool(data["browser_notifications_enabled"]),
            )
        if "browser_notify_browse" in data:
            set_user_preference(
                username,
                "browser_notify_browse",
                _normalize_pref_bool(data["browser_notify_browse"]),
            )
        if "browser_notify_queue" in data:
            set_user_preference(
                username,
                "browser_notify_queue",
                _normalize_pref_bool(data["browser_notify_queue"]),
            )
        if "browser_notify_autosync" in data:
            set_user_preference(
                username,
                "browser_notify_autosync",
                _normalize_pref_bool(data["browser_notify_autosync"]),
            )
        if "browser_notify_library" in data:
            set_user_preference(
                username,
                "browser_notify_library",
                _normalize_pref_bool(data["browser_notify_library"]),
            )
        if "browser_notify_settings" in data:
            set_user_preference(
                username,
                "browser_notify_settings",
                _normalize_pref_bool(data["browser_notify_settings"]),
            )
        if "browser_notify_system" in data:
            set_user_preference(
                username,
                "browser_notify_system",
                _normalize_pref_bool(data["browser_notify_system"]),
            )
        if "auto_open_captcha_tab" in data:
            set_user_preference(
                username,
                "auto_open_captcha_tab",
                _normalize_pref_bool(data["auto_open_captcha_tab"]),
            )
        current_user, is_admin = _get_current_user_info()
        if is_admin:
            if "smart_retry_profile" in data:
                _set_global_pref(
                    "smart_retry_profile",
                    _normalize_smart_retry_profile(data["smart_retry_profile"]),
                )
            if "auto_update_enabled" in data:
                _set_global_pref(
                    "auto_update_enabled",
                    _normalize_pref_bool(data["auto_update_enabled"]),
                )
            if "external_notifications_enabled" in data:
                _set_global_pref(
                    "external_notifications_enabled",
                    _normalize_pref_bool(data["external_notifications_enabled"]),
                )
            if "external_notification_type" in data:
                notification_type = str(data["external_notification_type"] or "").strip().lower()
                if notification_type not in {"generic", "discord", "gotify", "ntfy"}:
                    return jsonify({"error": "Invalid external_notification_type"}), 400
                _set_global_pref("external_notification_type", notification_type)
            if "external_notification_url" in data:
                _set_global_pref(
                    "external_notification_url",
                    str(data["external_notification_url"] or "").strip(),
                )
            for key in (
                "external_notify_queue",
                "external_notify_autosync",
                "external_notify_library",
                "external_notify_system",
            ):
                if key in data:
                    _set_global_pref(key, _normalize_pref_bool(data[key]))
        _record_user_event(
            "settings.updated",
            subject_type="settings",
            subject="web-settings",
            details={
                key: value
                for key, value in data.items()
                if key
                in {
                    "download_path",
                    "bandwidth_limit_kbps",
                    "download_backend",
                    "provider_fallback_order",
                    "disk_warn_gb",
                    "disk_warn_percent",
                    "library_auto_repair",
                    "safe_mode",
                    "lang_separation",
                    "disable_english_sub",
                    "experimental_filmpalast",
                    "sync_schedule",
                    "sync_language",
                    "sync_provider",
                    "ui_preset",
                    "ui_locale",
                    "ui_mode",
                    "ui_scale",
                    "ui_theme",
                    "ui_radius",
                    "ui_motion",
                    "ui_width",
                    "ui_modal_width",
                    "ui_nav_size",
                    "ui_table_density",
                    "ui_background",
                    "search_default_sort",
                    "search_default_genres",
                    "search_default_year_from",
                    "search_default_year_to",
                    "search_default_favorites_only",
                    "search_default_downloaded_only",
                    "browser_notifications_enabled",
                    "browser_notify_browse",
                    "browser_notify_queue",
                    "browser_notify_autosync",
                    "browser_notify_library",
                    "browser_notify_settings",
                    "browser_notify_system",
                    "auto_open_captcha_tab",
                    "smart_retry_profile",
                    "auto_update_enabled",
                    "external_notifications_enabled",
                    "external_notification_type",
                    "external_notification_url",
                    "external_notify_queue",
                    "external_notify_autosync",
                    "external_notify_library",
                    "external_notify_system",
                }
            },
        )
        _emit_ui_event("settings", "autosync", "dashboard", "library", "nav")
        return jsonify({"ok": True})

    @app.route("/api/custom-paths")
    def api_custom_paths():
        paths = get_custom_paths()
        return jsonify({"paths": paths})

    @app.route("/api/update/status")
    def api_update_status():
        _, is_admin = _get_current_user_info()
        return jsonify(_update_status_payload(force=False, can_manage=is_admin))

    @app.route("/api/update/check", methods=["POST"])
    def api_update_check():
        _, is_admin = _get_current_user_info()
        _set_update_runtime(last_checked_at=int(time.time()))
        payload = _update_status_payload(force=True, can_manage=is_admin)
        return jsonify(payload)

    @app.route("/api/update/apply", methods=["POST"])
    def api_update_apply():
        username, is_admin = _get_current_user_info()
        if not is_admin:
            return jsonify({"error": "Only admins can apply updates."}), 403
        snapshot = _update_source_snapshot(force=True)
        if snapshot.get("manual_action_available") and not snapshot.get("supports_apply"):
            payload = _update_status_payload(force=False, can_manage=True)
            payload.update(
                {
                    "active": False,
                    "phase": "manual",
                    "message": snapshot.get("action_hint")
                    or "This installation must be updated outside the web UI.",
                }
            )
            return jsonify(payload)
        if not _start_update_worker(requested_by=username):
            return jsonify({"error": "An update is already running."}), 409
        _record_user_event(
            "system.update_requested",
            subject_type="system",
            subject=snapshot.get("install_mode") or "web-update",
            details={
                "requested_by": username,
                "install_mode": snapshot.get("install_mode"),
                "apply_strategy": snapshot.get("apply_strategy"),
            },
        )
        return jsonify(_update_status_payload(force=True, can_manage=True))

    @app.route("/api/system/restart", methods=["POST"])
    def api_system_restart():
        username, is_admin = _get_current_user_info()
        if not is_admin:
            return jsonify({"error": "Only admins can restart the downloader."}), 403
        runtime = _get_update_runtime()
        if runtime.get("active"):
            return jsonify({"error": "Wait for the running update to finish first."}), 409
        _record_user_event(
            "system.restart_requested",
            subject_type="system",
            subject="process-restart",
            details={"requested_by": username},
        )
        _start_restart_worker()
        return jsonify(
            {
                "ok": True,
                "message": "Restarting downloader. Reload this page in a few seconds.",
                "reload_after_seconds": 5,
            }
        )

    @app.route("/api/custom-paths", methods=["POST"])
    def api_custom_paths_add():
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        path = (data.get("path") or "").strip()
        if not name or not path:
            return jsonify({"error": "name and path are required"}), 400
        path_id = add_custom_path(name, path)
        _record_user_event(
            "custom_path.added",
            subject_type="custom_path",
            subject=name,
            details={"path": path, "path_id": path_id},
        )
        _emit_ui_event("library", "settings", "autosync")
        return jsonify({"ok": True, "id": path_id})

    @app.route("/api/custom-paths/<int:path_id>", methods=["DELETE"])
    def api_custom_paths_delete(path_id):
        path_row = get_custom_path_by_id(path_id)
        remove_custom_path(path_id)
        _record_user_event(
            "custom_path.deleted",
            subject_type="custom_path",
            subject=(path_row or {}).get("name") or f"Path #{path_id}",
            details={"path_id": path_id},
        )
        _emit_ui_event("library", "settings", "autosync")
        return jsonify({"ok": True})

    # ===== Auto-Sync Page =====

    @app.route("/autosync")
    def autosync_page():
        return render_template(
            "autosync.html", supported_providers=_ordered_working_providers()
        )

    # ===== Auto-Sync API =====

    def _get_current_user_info():
        """Return (username, is_admin) for the current request."""
        if not auth_enabled:
            return None, True  # no auth -> treat as admin
        user = get_current_user()
        if not user:
            return None, False
        username = (
            user.get("username")
            if isinstance(user, dict)
            else getattr(user, "username", None)
        )
        role = (
            user.get("role")
            if isinstance(user, dict)
            else getattr(user, "role", "user")
        )
        return username, role == "admin"

    def _record_user_event(action, subject_type=None, subject=None, details=None):
        username, _ = _get_current_user_info()
        record_audit_event(
            action,
            username=username,
            subject_type=subject_type,
            subject=subject,
            details=details,
        )

    @app.route("/api/autosync")
    def api_autosync_list():
        username, is_admin = _get_current_user_info()
        # Admins see all jobs; regular users see only their own
        jobs = get_autosync_jobs(username=None if is_admin else username)
        return jsonify({"jobs": jobs})

    @app.route("/api/autosync", methods=["POST"])
    def api_autosync_create():
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        series_url = (data.get("series_url") or "").strip()
        language = data.get("language", "German Dub")
        provider = data.get("provider", "VOE")
        custom_path_id = data.get("custom_path_id")

        if not title or not series_url:
            return jsonify({"error": "title and series_url are required"}), 400

        try:
            prov = resolve_provider(series_url)
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400

        if not prov.series_cls or not prov.season_cls:
            return (
                jsonify(
                    {
                        "error": "Auto-Sync is only supported for series sources, not direct movie links."
                    }
                ),
                400,
            )

        existing = find_autosync_by_url(series_url)
        if existing:
            return jsonify(
                {"error": "A sync job for this series already exists", "job": existing}
            ), 409

        username, _ = _get_current_user_info()
        job_id = add_autosync_job(
            title=title,
            series_url=series_url,
            language=language,
            provider=provider,
            custom_path_id=custom_path_id,
            added_by=username,
        )
        _record_user_event(
            "autosync.added",
            subject_type="autosync",
            subject=title,
            details={
                "job_id": job_id,
                "series_url": series_url,
                "language": language,
                "provider": provider,
            },
        )
        _emit_ui_event("autosync", "dashboard", "nav", "settings")
        return jsonify({"ok": True, "id": job_id})

    @app.route("/api/autosync/<int:job_id>", methods=["PUT"])
    def api_autosync_update(job_id):
        job = get_autosync_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        username, is_admin = _get_current_user_info()
        if not is_admin and job.get("added_by") != username:
            return jsonify({"error": "Not authorized to edit this job"}), 403
        data = request.get_json(silent=True) or {}
        allowed = {"title", "language", "provider", "enabled", "custom_path_id"}
        filtered = {k: v for k, v in data.items() if k in allowed}
        options = _build_autosync_job_options(job)
        valid_languages = set(options["languages"])
        if options["allow_all_languages"]:
            valid_languages.add("All Languages")

        language = str(filtered.get("language", job.get("language") or "")).strip()
        provider = str(filtered.get("provider", job.get("provider") or "")).strip()

        if language not in valid_languages:
            return jsonify({"error": "Selected language is not available for this series"}), 400

        if language == "All Languages":
            valid_providers = set(options["all_language_providers"])
        else:
            valid_providers = set(options["providers_by_language"].get(language, []))
        valid_providers.add("Auto")

        if provider not in valid_providers:
            return jsonify({"error": "Selected provider is not available for the chosen language"}), 400

        if "title" in filtered:
            filtered["title"] = str(filtered["title"] or "").strip()
            if not filtered["title"]:
                return jsonify({"error": "Job name is required"}), 400

        update_autosync_job(job_id, **filtered)
        _record_user_event(
            "autosync.updated",
            subject_type="autosync",
            subject=job.get("title") or f"Job #{job_id}",
            details={"job_id": job_id, **filtered},
        )
        _emit_ui_event("autosync", "dashboard", "nav", "settings")
        return jsonify({"ok": True})

    @app.route("/api/autosync/<int:job_id>", methods=["DELETE"])
    def api_autosync_delete(job_id):
        job = get_autosync_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        username, is_admin = _get_current_user_info()
        if not is_admin and job.get("added_by") != username:
            return jsonify({"error": "Not authorized to delete this job"}), 403
        ok, err = remove_autosync_job(job_id)
        if not ok:
            return jsonify({"error": err}), 404
        _record_user_event(
            "autosync.deleted",
            subject_type="autosync",
            subject=job.get("title") or f"Job #{job_id}",
            details={"job_id": job_id},
        )
        _emit_ui_event("autosync", "dashboard", "nav", "settings")
        return jsonify({"ok": True})

    @app.route("/api/autosync/<int:job_id>/options")
    def api_autosync_options(job_id):
        job = get_autosync_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        username, is_admin = _get_current_user_info()
        if not is_admin and job.get("added_by") != username:
            return jsonify({"error": "Not authorized to inspect this job"}), 403

        options = _build_autosync_job_options(job)
        return jsonify({"ok": True, **options})

    @app.route("/api/autosync/<int:job_id>/sync", methods=["POST"])
    def api_autosync_trigger(job_id):
        job = get_autosync_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        username, is_admin = _get_current_user_info()
        if not is_admin and job.get("added_by") != username:
            return jsonify({"error": "Not authorized"}), 403
        with _syncing_jobs_lock:
            if job_id in _syncing_jobs:
                return jsonify({"error": "Sync already running for this job"}), 409
        threading.Thread(target=_run_autosync_for_job, args=(job,), daemon=True).start()
        _record_user_event(
            "autosync.triggered",
            subject_type="autosync",
            subject=job.get("title") or f"Job #{job_id}",
            details={"job_id": job_id},
        )
        _emit_ui_event("autosync")
        return jsonify({"ok": True, "message": "Sync started"})

    @app.route("/api/autosync/sync-all", methods=["POST"])
    def api_autosync_trigger_all():
        username, is_admin = _get_current_user_info()
        jobs = get_autosync_jobs(username=None if is_admin else username)
        started = 0
        for job in jobs:
            if not job.get("enabled"):
                continue
            with _syncing_jobs_lock:
                if job["id"] in _syncing_jobs:
                    continue
            threading.Thread(
                target=_run_autosync_for_job,
                args=(job,),
                daemon=True,
            ).start()
            started += 1
        if started:
            _record_user_event(
                "autosync.triggered_all",
                subject_type="autosync",
                subject="Sync All",
                details={"started": started},
            )
            _emit_ui_event("autosync")
        return jsonify({"ok": True, "started": started})

    @app.route("/api/autosync/sync-selected", methods=["POST"])
    def api_autosync_trigger_selected():
        data = request.get_json(silent=True) or {}
        raw_ids = data.get("ids") or []
        if not isinstance(raw_ids, list):
            return jsonify({"error": "ids must be a list"}), 400

        selected_ids = []
        seen = set()
        for raw_id in raw_ids:
            try:
                job_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if job_id in seen:
                continue
            seen.add(job_id)
            selected_ids.append(job_id)

        if not selected_ids:
            return jsonify({"error": "No sync jobs selected"}), 400

        username, is_admin = _get_current_user_info()
        started = 0
        skipped = []

        for job_id in selected_ids:
            job = get_autosync_job(job_id)
            if not job:
                skipped.append({"id": job_id, "reason": "not_found"})
                continue
            if not is_admin and job.get("added_by") != username:
                skipped.append({"id": job_id, "reason": "forbidden"})
                continue
            with _syncing_jobs_lock:
                if job_id in _syncing_jobs:
                    skipped.append({"id": job_id, "reason": "already_running"})
                    continue
            threading.Thread(
                target=_run_autosync_for_job,
                args=(job,),
                daemon=True,
            ).start()
            started += 1

        if started:
            _record_user_event(
                "autosync.triggered_selected",
                subject_type="autosync",
                subject="Sync Selected",
                details={
                    "started": started,
                    "selected_ids": selected_ids,
                    "skipped": skipped,
                },
            )
            _emit_ui_event("autosync")

        return jsonify({"ok": True, "started": started, "skipped": skipped})

    @app.route("/api/autosync/check", methods=["GET"])
    def api_autosync_check():
        """Check if a sync job exists for a given series URL."""
        url = request.args.get("url", "").strip()
        if not url:
            return jsonify({"exists": False})
        job = find_autosync_by_url(url)
        if not job:
            return jsonify({"exists": False})
        # Only expose job details to the owner or admins
        username, is_admin = _get_current_user_info()
        if not is_admin and job.get("added_by") != username:
            return jsonify({"exists": False})
        return jsonify({"exists": True, "job": job})

    @app.route("/api/favorites")
    def api_favorites():
        username, _ = _get_current_user_info()
        return jsonify({"items": list_favorites(username=username)})

    @app.route("/api/favorites", methods=["POST"])
    def api_favorites_add():
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        series_url = (data.get("series_url") or "").strip()
        poster_url = (data.get("poster_url") or "").strip() or None
        site = (data.get("site") or "").strip() or None
        username, _ = _get_current_user_info()
        if not title or not series_url:
            return jsonify({"error": "title and series_url are required"}), 400
        favorite_id = add_favorite(
            title,
            series_url,
            poster_url=poster_url,
            site=site,
            username=username,
        )
        upsert_series_meta(
            series_url=series_url,
            title=title,
            poster_url=poster_url,
        )
        _record_user_event(
            "favorite.added",
            subject_type="favorite",
            subject=title,
            details={"series_url": series_url, "site": site},
        )
        _emit_ui_event("favorites", "dashboard", "nav", "library")
        return jsonify({"ok": True, "id": favorite_id})

    @app.route("/api/favorites", methods=["DELETE"])
    def api_favorites_delete():
        data = request.get_json(silent=True) or {}
        series_url = (data.get("series_url") or "").strip()
        if not series_url:
            return jsonify({"error": "series_url is required"}), 400
        username, _ = _get_current_user_info()
        favorite = get_favorite(series_url, username=username)
        remove_favorite(series_url, username=username)
        _record_user_event(
            "favorite.removed",
            subject_type="favorite",
            subject=(favorite or {}).get("title") or series_url,
            details={"series_url": series_url},
        )
        _emit_ui_event("favorites", "dashboard", "nav", "library")
        return jsonify({"ok": True})

    @app.route("/api/favorites/touch", methods=["POST"])
    def api_favorites_touch():
        data = request.get_json(silent=True) or {}
        series_url = (data.get("series_url") or "").strip()
        if not series_url:
            return jsonify({"error": "series_url is required"}), 400
        username, _ = _get_current_user_info()
        touch_favorite(series_url, username=username)
        _emit_ui_event("favorites", min_interval=5.0)
        return jsonify({"ok": True})

    # ===== Stats API =====

    @app.route("/api/stats/sync")
    def api_stats_sync():
        stats = get_sync_stats()
        # Compute next_run_at from last check + schedule interval
        schedule_key = os.environ.get("ANIWORLD_SYNC_SCHEDULE", "0")
        interval = SYNC_SCHEDULE_MAP.get(schedule_key, 0)
        stats["schedule"] = schedule_key
        stats["next_run_at"] = None
        if interval and stats.get("last_check"):
            from datetime import datetime, timedelta

            try:
                last = datetime.strptime(stats["last_check"], "%Y-%m-%d %H:%M:%S")
                nxt = last + timedelta(seconds=interval)
                stats["next_run_at"] = nxt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        return jsonify(stats)

    @app.route("/api/stats/queue")
    def api_stats_queue():
        return jsonify(get_queue_stats())

    @app.route("/api/stats/general")
    def api_stats_general():
        return jsonify(get_general_stats())

    @app.route("/api/provider-health")
    def api_provider_health():
        items = get_provider_health()
        snapshot_provider_score_history(items)
        return jsonify({"items": items})

    @app.route("/api/provider-health/history")
    def api_provider_health_history():
        try:
            hours = max(24, min(int(request.args.get("hours", "168")), 24 * 30))
        except ValueError:
            hours = 168
        return jsonify({"items": get_provider_score_history(hours=hours), "hours": hours})

    @app.route("/api/provider-health/failures")
    def api_provider_health_failures():
        return jsonify({"items": get_provider_failure_analytics()})

    @app.route("/api/provider-health/benchmark", methods=["POST"])
    def api_provider_health_benchmark():
        data = request.get_json(silent=True) or {}
        try:
            payload = _run_provider_benchmark(
                episode_url=(data.get("episode_url") or "").strip(),
                language=(data.get("language") or "").strip(),
            )
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400

        _record_user_event(
            "provider.benchmark",
            subject_type="provider",
            subject=(payload.get("sample") or {}).get("title") or "provider-benchmark",
            details={
                "episode_url": (payload.get("sample") or {}).get("episode_url"),
                "language": (payload.get("sample") or {}).get("language"),
                "providers": [item.get("provider") for item in payload.get("results") or []],
            },
        )
        return jsonify(payload)

    @app.route("/api/diagnostics")
    def api_diagnostics():
        return jsonify(_build_diagnostics_payload())

    @app.route("/api/maintenance")
    def api_maintenance():
        return jsonify(_build_maintenance_payload())

    @app.route("/api/maintenance/warm-cache", methods=["POST"])
    def api_maintenance_warm_cache():
        _warm_runtime_caches_once()
        _record_user_event(
            "maintenance.warm_cache",
            subject_type="maintenance",
            subject="runtime-cache",
        )
        _emit_ui_event("library", "dashboard", "settings")
        return jsonify({"ok": True})

    @app.route("/api/maintenance/provider-snapshot", methods=["POST"])
    def api_maintenance_provider_snapshot():
        items = get_provider_health()
        created = snapshot_provider_score_history(items, minimum_interval_minutes=0)
        _record_user_event(
            "maintenance.provider_snapshot",
            subject_type="maintenance",
            subject="provider-score-history",
            details={"snapshots": created},
        )
        _emit_ui_event("dashboard", "settings")
        return jsonify({"ok": True, "snapshots": created})

    @app.route("/api/maintenance/recover-queue", methods=["POST"])
    def api_maintenance_recover_queue():
        payload = _maintenance_recover_queue()
        _record_user_event(
            "maintenance.recover_queue",
            subject_type="maintenance",
            subject=(payload.get("title") or "queue-recover"),
            details=payload,
        )
        return jsonify({"ok": True, **payload})

    @app.route("/api/maintenance/clear-temp-files", methods=["POST"])
    def api_maintenance_clear_temp_files():
        payload = _maintenance_clear_temp_files()
        _record_user_event(
            "maintenance.clear_temp_files",
            subject_type="maintenance",
            subject="temp-cleanup",
            details={"removed": payload.get("removed", 0)},
        )
        return jsonify({"ok": True, **payload})

    @app.route("/api/sessions")
    def api_sessions():
        try:
            limit = max(1, min(int(request.args.get("limit", "80")), 200))
        except ValueError:
            limit = 80
        return jsonify({"items": get_download_session_history(limit)})

    @app.route("/api/provider-test", methods=["POST"])
    def api_provider_test():
        data = request.get_json(silent=True) or {}
        episode_url = str(data.get("episode_url") or "").strip()
        language = str(data.get("language") or "").strip() or "German Dub"
        provider = str(data.get("provider") or "").strip() or "VOE"
        if not episode_url:
            return jsonify({"error": "episode_url is required"}), 400
        try:
            payload = _run_provider_test(episode_url, language, provider)
            return jsonify(payload)
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400

    @app.route("/api/backup/export")
    def api_backup_export():
        username, _ = _get_current_user_info()
        payload = {
            "exported_at": int(time.time()),
            "version": VERSION,
            "settings": _settings_payload(
                ui_preset=get_user_preference(username, "ui_preset", "custom"),
                ui_locale=get_user_preference(username, "ui_locale", "en"),
                ui_mode=get_user_preference(username, "ui_mode", "cozy"),
                ui_scale=get_user_preference(username, "ui_scale", "100"),
                ui_theme=get_user_preference(username, "ui_theme", "ocean"),
                ui_radius=get_user_preference(username, "ui_radius", "soft"),
                ui_motion=get_user_preference(username, "ui_motion", "normal"),
                ui_width=get_user_preference(username, "ui_width", "standard"),
                ui_modal_width=get_user_preference(username, "ui_modal_width", "standard"),
                ui_nav_size=get_user_preference(username, "ui_nav_size", "standard"),
                ui_table_density=get_user_preference(username, "ui_table_density", "standard"),
                ui_background=get_user_preference(username, "ui_background", "dynamic"),
                search_default_sort=get_user_preference(username, "search_default_sort", "source"),
                search_default_genres=get_user_preference(username, "search_default_genres", ""),
                search_default_year_from=get_user_preference(username, "search_default_year_from", ""),
                search_default_year_to=get_user_preference(username, "search_default_year_to", ""),
                search_default_favorites_only=get_user_preference(username, "search_default_favorites_only", "0"),
                search_default_downloaded_only=get_user_preference(username, "search_default_downloaded_only", "0"),
                browser_notifications_enabled=get_user_preference(username, "browser_notifications_enabled", "0"),
                browser_notify_browse=get_user_preference(username, "browser_notify_browse", "1"),
                browser_notify_queue=get_user_preference(username, "browser_notify_queue", "1"),
                browser_notify_autosync=get_user_preference(username, "browser_notify_autosync", "1"),
                browser_notify_library=get_user_preference(username, "browser_notify_library", "1"),
                browser_notify_settings=get_user_preference(username, "browser_notify_settings", "1"),
                browser_notify_system=get_user_preference(username, "browser_notify_system", "1"),
            ),
            "tables": export_app_state(),
        }
        buffer = BytesIO(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
        return send_file(
            buffer,
            mimetype="application/json",
            as_attachment=True,
            download_name=f"aniworld-backup-{int(time.time())}.json",
        )

    @app.route("/api/backup/import", methods=["POST"])
    def api_backup_import():
        upload = request.files.get("backup")
        if not upload:
            return jsonify({"error": "backup file is required"}), 400
        try:
            payload = json.loads(upload.read().decode("utf-8"))
        except Exception:
            return jsonify({"error": "Invalid backup file"}), 400
        settings_payload = payload.get("settings") or {}
        if settings_payload:
            os.environ[_ENV_DOWNLOAD_PATH] = str(
                settings_payload.get("download_path") or os.environ.get(_ENV_DOWNLOAD_PATH, "")
            ).strip()
            os.environ[_ENV_BANDWIDTH_LIMIT] = _normalize_bandwidth_limit(
                settings_payload.get("bandwidth_limit_kbps", os.environ.get(_ENV_BANDWIDTH_LIMIT, "0"))
            )
            os.environ[_ENV_DOWNLOAD_BACKEND] = _normalize_download_backend(
                settings_payload.get("download_backend", os.environ.get(_ENV_DOWNLOAD_BACKEND, "auto"))
            )
            os.environ[_ENV_DOWNLOAD_ENGINE_RULES] = _normalize_engine_rules(
                settings_payload.get(
                    "download_engine_rules",
                    os.environ.get(_ENV_DOWNLOAD_ENGINE_RULES, ""),
                )
            )
            os.environ[_ENV_DOWNLOAD_SPEED_PROFILE] = _normalize_download_speed_profile(
                settings_payload.get(
                    "download_speed_profile",
                    os.environ.get(_ENV_DOWNLOAD_SPEED_PROFILE, "balanced"),
                )
            )
            _set_bool_env(
                _ENV_AUTO_PROVIDER_SWITCH,
                settings_payload.get(
                    "auto_provider_switch",
                    os.environ.get(_ENV_AUTO_PROVIDER_SWITCH, "1"),
                ),
            )
            _set_bool_env(
                _ENV_RATE_LIMIT_GUARD,
                settings_payload.get(
                    "rate_limit_guard",
                    os.environ.get(_ENV_RATE_LIMIT_GUARD, "1"),
                ),
            )
            _set_bool_env(
                _ENV_PREFLIGHT_CHECK,
                settings_payload.get(
                    "preflight_check",
                    os.environ.get(_ENV_PREFLIGHT_CHECK, "1"),
                ),
            )
            _set_bool_env(
                _ENV_MP4_FALLBACK_REMUX,
                settings_payload.get(
                    "mp4_fallback_remux",
                    os.environ.get(_ENV_MP4_FALLBACK_REMUX, "0"),
                ),
            )
            os.environ[_ENV_PROVIDER_FALLBACK_ORDER] = _normalize_provider_fallback_order(
                settings_payload.get("provider_fallback_order", os.environ.get(_ENV_PROVIDER_FALLBACK_ORDER, ""))
            )
            os.environ[_ENV_DISK_WARN_GB] = _normalize_disk_guard_threshold(
                settings_payload.get("disk_warn_gb", os.environ.get(_ENV_DISK_WARN_GB, "10")),
                "10",
                5000,
            )
            os.environ[_ENV_DISK_WARN_PERCENT] = _normalize_disk_guard_threshold(
                settings_payload.get("disk_warn_percent", os.environ.get(_ENV_DISK_WARN_PERCENT, "12")),
                "12",
                100,
            )
            _set_bool_env(_ENV_LIBRARY_AUTO_REPAIR, settings_payload.get("library_auto_repair", "0"))
            _set_bool_env(
                _ENV_EXPERIMENTAL_SELF_HEAL,
                settings_payload.get("experimental_self_heal", "0"),
            )
            _set_bool_env(_ENV_SAFE_MODE, settings_payload.get("safe_mode", "0"))
        counts = import_app_state(payload.get("tables") or payload)
        _record_user_event(
            "backup.imported",
            subject_type="backup",
            subject="restore",
            details={"tables": counts},
        )
        _cache_invalidate("stats:", "dashboard:", "library:")
        _emit_ui_event("settings", "dashboard", "library", "nav", "autosync")
        return jsonify({"ok": True, "tables": counts})

    @app.route("/api/dashboard/stats")
    def api_dashboard_stats():
        return jsonify(_get_cached_stats_payload())

    @app.route("/api/dashboard")
    def api_dashboard():
        username, _ = _get_current_user_info()
        cache_key = f"dashboard:full:{_cache_scope_token(username)}"
        cached = _cache_get(cache_key, 30.0)
        if cached is not None:
            return jsonify(cached)

        stats_payload = _get_cached_stats_payload()
        favorites = list_favorites(username=username)
        meta_by_url = {item["series_url"]: item for item in list_series_meta()}
        for favorite in favorites:
            meta = meta_by_url.get(favorite["series_url"], {})
            if not favorite.get("poster_url"):
                favorite["poster_url"] = meta.get("poster_url")
        releases = _cached_browse("new_episodes", fetch_new_episodes) or []
        payload = {
            **stats_payload,
            "favorites": favorites[:8],
            "recent_activity": get_recent_activity(8, username=username),
            "history": get_download_history(14, username=username),
            "releases": releases[:10],
        }
        return jsonify(_cache_set(cache_key, payload))

    @app.route("/api/nav")
    def api_nav():
        username, _ = _get_current_user_info()
        return jsonify(_build_nav_state(username=username))

    @app.route("/api/events")
    def api_events():
        @stream_with_context
        def _stream():
            last_seq = 0
            yield "retry: 4000\n\n"
            while True:
                with _ui_event_condition:
                    if not _pending_ui_events(last_seq):
                        _ui_event_condition.wait(timeout=25)
                    pending = _pending_ui_events(last_seq)

                if pending:
                    last_seq = pending[-1]["seq"]
                    payload = {
                        "sequence": last_seq,
                        "channels": sorted(
                            {channel for event in pending for channel in event["channels"]}
                        ),
                        "emitted_at": pending[-1]["emitted_at"],
                    }
                    yield f"event: update\ndata: {json.dumps(payload)}\n\n"
                else:
                    yield "event: ping\ndata: {}\n\n"

        response = Response(_stream(), mimetype="text/event-stream")
        response.headers["Cache-Control"] = "no-cache, no-transform"
        response.headers["X-Accel-Buffering"] = "no"
        return response

    @app.route("/api/history")
    def api_history():
        try:
            limit = max(1, min(int(request.args.get("limit", "40")), 100))
        except ValueError:
            limit = 40
        username, _ = _get_current_user_info()
        return jsonify({"items": get_download_history(limit, username=username)})

    @app.route("/api/history/<int:queue_id>", methods=["DELETE"])
    def api_history_delete(queue_id):
        username, _ = _get_current_user_info()
        deleted = delete_download_history_item(queue_id, username=username)
        if not deleted:
            return jsonify({"error": "History item not found"}), 404
        record_audit_event(
            "history.deleted",
            username=username,
            subject_type="history",
            subject=deleted.get("title") or str(queue_id),
            details={"queue_id": queue_id, "status": deleted.get("status")},
        )
        _emit_ui_event("dashboard", "nav", min_interval=0.2)
        return jsonify({"ok": True})

    @app.route("/api/audit")
    def api_audit():
        try:
            limit = max(1, min(int(request.args.get("limit", "80")), 200))
        except ValueError:
            limit = 80
        requested_user = (request.args.get("username") or "").strip()
        action = (request.args.get("action") or "").strip() or None
        current_username, is_admin = _get_current_user_info()
        if is_admin:
            scope_username = requested_user or None
        else:
            scope_username = current_username
        return jsonify(
            {
                "items": list_audit_events(
                    limit=limit,
                    username=scope_username,
                    action=action,
                )
            }
        )

    @app.route("/api/audit/users")
    def api_audit_users():
        _, is_admin = _get_current_user_info()
        if not is_admin:
            return jsonify({"items": []})
        return jsonify({"items": list_audit_users()})

    @app.route("/api/library")
    def api_library():
        return jsonify(_get_cached_library_snapshot(include_meta=True))

    @app.route("/api/library/posters", methods=["POST"])
    def api_library_posters():
        data = request.get_json(silent=True) or {}
        raw_urls = data.get("series_urls") or []
        if not isinstance(raw_urls, list):
            return jsonify({"error": "series_urls must be a list"}), 400

        items = {}
        for series_url in raw_urls[:80]:
            normalized = str(series_url or "").strip()
            if not normalized:
                continue
            meta = _fetch_and_cache_series_meta(normalized) or {}
            poster_url = str(meta.get("poster_url") or "").strip()
            if poster_url:
                items[normalized] = poster_url

        if items:
            _cache_invalidate("library:")

        return jsonify({"items": items})

    @app.route("/api/library/compare")
    def api_library_compare():
        refresh = str(request.args.get("refresh", "0")).strip() == "1"
        payload = _get_cached_library_compare(refresh=refresh)
        if refresh and os.environ.get(_ENV_LIBRARY_AUTO_REPAIR, "0") == "1":
            username, _ = _get_current_user_info()
            payload["auto_repair"] = _run_library_auto_repair(
                os.environ.get(_ENV_SYNC_LANGUAGE, "German Dub"),
                os.environ.get(_ENV_SYNC_PROVIDER, "VOE"),
                username=username,
            )
            if payload["auto_repair"]["created"]:
                _emit_ui_event("queue", "dashboard", "library", "nav")
        return jsonify(payload)

    @app.route("/api/library/queue-missing", methods=["POST"])
    def api_library_queue_missing():
        data = request.get_json(silent=True) or {}
        series_url = str(data.get("series_url") or "").strip()
        title = str(data.get("title") or "").strip() or "Unknown"
        missing_labels = data.get("missing_labels") or []
        language = str(data.get("language") or "").strip() or "German Dub"
        preferred_provider = str(data.get("provider") or "").strip() or None
        custom_path_id = data.get("custom_path_id")

        if not series_url:
            return jsonify({"error": "series_url is required"}), 400
        if not isinstance(missing_labels, list) or not missing_labels:
            return jsonify({"error": "missing_labels are required"}), 400

        username = None
        if auth_enabled:
            user = get_current_user()
            if user:
                username = (
                    user.get("username")
                    if isinstance(user, dict)
                    else getattr(user, "username", None)
                )
        try:
            result = _queue_missing_episode_labels(
                series_url=series_url,
                title=title,
                missing_labels=missing_labels,
                language=language,
                preferred_provider=preferred_provider,
                custom_path_id=custom_path_id,
                username=username,
                source="library:missing",
            )
        except PermissionError as exc:
            return jsonify({"error": str(exc)}), 403
        except LookupError as exc:
            return jsonify({"error": str(exc)}), 404
        except RuntimeError as exc:
            response = {"error": str(exc), **getattr(exc, "payload", {})}
            if getattr(exc, "kind", "") == "queue_conflict":
                response["type"] = "queue_conflict"
            return jsonify(response), 409

        _record_user_event(
            "library.missing_queued",
            subject_type="library",
            subject=title,
            details={
                "queue_id": result["queue_id"],
                "series_url": series_url,
                "language": language,
                "provider": result["provider"],
                "queued_episodes": result["queued_episodes"],
                "requested_missing": len(missing_labels),
                "skipped_unavailable": result["skipped_unavailable"],
                "skipped_conflicts": result["skipped_conflicts"],
            },
        )
        _dispatch_external_notification(
            "Missing episodes queued",
            f"{title} queued {result['queued_episodes']} missing episode(s) from the library compare view.",
            category="library",
            details={
                "title": title,
                "series_url": series_url,
                "queued_episodes": result["queued_episodes"],
            },
        )
        _emit_ui_event("queue", "dashboard", "library", "nav")
        return jsonify(result)

    @app.route("/api/library/repair-missing", methods=["POST"])
    def api_library_repair_missing():
        data = request.get_json(silent=True) or {}
        language = str(data.get("language") or "").strip() or os.environ.get(
            _ENV_SYNC_LANGUAGE, "German Dub"
        )
        preferred_provider = str(data.get("provider") or "").strip() or os.environ.get(
            _ENV_SYNC_PROVIDER, "VOE"
        )
        username, _ = _get_current_user_info()

        repair_result = _run_library_auto_repair(
            language, preferred_provider, username=username
        )

        _record_user_event(
            "library.repair_triggered",
            subject_type="library",
            subject="repair-missing",
            details={
                "queued_titles": len(repair_result["created"]),
                "skipped_titles": len(repair_result["skipped"]),
                "language": language,
                "provider": preferred_provider,
            },
        )
        if repair_result["created"]:
            _dispatch_external_notification(
                "Library auto-repair queued episodes",
                f"Library repair queued missing episodes for {len(repair_result['created'])} title(s).",
                category="library",
                details={"queued_titles": len(repair_result["created"])},
            )
        _emit_ui_event("queue", "dashboard", "library", "nav")
        return jsonify({"ok": True, **repair_result})

    @app.route("/api/library/resolve-duplicates", methods=["POST"])
    def api_library_resolve_duplicates():
        data = request.get_json(silent=True) or {}
        title = str(data.get("title") or "").strip() or "Library Title"
        duplicate_files = data.get("duplicate_files") or []
        if not isinstance(duplicate_files, list) or not duplicate_files:
            return jsonify({"error": "duplicate_files are required"}), 400

        resolved = _resolve_duplicate_file_paths(duplicate_files)
        deleted = []
        failed = []
        for path_string in resolved["delete_paths"]:
            try:
                path = Path(path_string)
                if not path.exists():
                    continue
                path.unlink()
                deleted.append(path_string)
            except Exception as exc:
                failed.append({"path": path_string, "error": str(exc)})

        _record_user_event(
            "library.duplicates_resolved",
            subject_type="library",
            subject=title,
            details={
                "deleted": len(deleted),
                "failed": len(failed),
                "kept": len(resolved["keep_paths"]),
            },
        )
        _emit_ui_event("library", "dashboard", "nav")
        return jsonify(
            {
                "ok": True,
                "deleted": deleted,
                "failed": failed,
                "kept": resolved["keep_paths"],
            }
        )

    @app.route("/api/library/delete", methods=["POST"])
    def api_library_delete():
        import shutil
        from pathlib import Path

        data = request.get_json(silent=True) or {}
        folder = data.get("folder", "")
        season = data.get("season")  # int or null
        episode = data.get("episode")  # int or null
        custom_path_id = data.get("custom_path_id")  # int or null

        # Security: reject dangerous folder names
        if (
            not folder
            or ".." in folder
            or "/" in folder
            or "\\" in folder
            or "\x00" in folder
        ):
            return jsonify({"error": "Invalid folder name"}), 400

        # Resolve base path from custom_path_id or default
        if custom_path_id:
            cp = get_custom_path_by_id(custom_path_id)
            if not cp:
                return jsonify({"error": "Custom path not found"}), 404
            dl_base = Path(cp["path"]).expanduser()
            if not dl_base.is_absolute():
                dl_base = Path.home() / dl_base
        else:
            raw = os.environ.get("ANIWORLD_DOWNLOAD_PATH", "")
            if raw:
                dl_base = Path(raw).expanduser()
                if not dl_base.is_absolute():
                    dl_base = Path.home() / dl_base
            else:
                dl_base = Path.home() / "Downloads"

        lang_sep = os.environ.get("ANIWORLD_LANG_SEPARATION", "0") == "1"
        lang_folders = ["german-dub", "english-sub", "german-sub", "english-dub"]
        lang_folder = data.get("lang_folder")  # str or null

        if lang_sep and lang_folder:
            if lang_folder not in lang_folders:
                return jsonify({"error": "Invalid language folder"}), 400
            bases = [dl_base / lang_folder]
        elif lang_sep:
            bases = [dl_base / lf for lf in lang_folders]
        else:
            bases = [dl_base]

        deleted = 0
        for base in bases:
            title_path = base / folder
            # Verify resolved path is a child of the base
            try:
                title_path.resolve().relative_to(base.resolve())
            except ValueError:
                continue
            if not title_path.is_dir():
                continue

            if season is None and episode is None:
                # Delete entire title
                shutil.rmtree(title_path, ignore_errors=True)
                deleted += 1
            else:
                # Build regex pattern
                if episode is not None:
                    pat = re.compile(
                        rf"S{int(season):02d}E{int(episode):03d}(?!\d)", re.IGNORECASE
                    )
                else:
                    pat = re.compile(rf"S{int(season):02d}E\d{{2,3}}", re.IGNORECASE)

                for f in list(title_path.rglob("*")):
                    if f.is_file() and pat.search(f.name):
                        try:
                            f.unlink()
                            deleted += 1
                        except OSError:
                            pass

                # Cleanup empty directories bottom-up
                for dirpath in sorted(
                    title_path.rglob("*"), key=lambda p: len(p.parts), reverse=True
                ):
                    if dirpath.is_dir():
                        try:
                            dirpath.rmdir()  # only succeeds if empty
                        except OSError:
                            pass
                # Remove title folder itself if empty
                try:
                    title_path.rmdir()
                except OSError:
                    pass

        if deleted == 0:
            return jsonify({"error": "Nothing found to delete"}), 404
        _emit_ui_event("library", "dashboard", "nav")
        return jsonify({"ok": True, "deleted": deleted})

    if auth_enabled:
        from .auth import admin_required

        # Endpoints that require admin instead of just login
        _admin_only = {
            "settings_page",
            "api_settings",
            "api_settings_update",
            "api_library_delete",
            "api_custom_paths_add",
            "api_custom_paths_delete",
            "api_autosync_create",
            "api_autosync_update",
            "api_autosync_delete",
            "api_autosync_trigger",
        }

        # Wrap all non-auth, non-static view functions with login_required
        # (admin_required for settings endpoints)
        _exempt = {
            "static",
            "auth.login",
            "auth.logout",
            "auth.setup",
            "auth.oidc_login",
            "auth.oidc_callback",
        }
        for endpoint, view_func in list(app.view_functions.items()):
            if endpoint not in _exempt:
                if endpoint in _admin_only:
                    app.view_functions[endpoint] = admin_required(view_func)
                else:
                    app.view_functions[endpoint] = login_required(view_func)

        # Exempt JSON API routes from CSRF (they use Content-Type: application/json
        # which provides implicit cross-origin protection via CORS preflight)
        for endpoint in list(app.view_functions):
            if endpoint.startswith("api_") or endpoint.startswith("auth.admin_"):
                csrf.exempt(app.view_functions[endpoint])

    return app


def start_web_ui(
    host="127.0.0.1",
    port=8080,
    open_browser=True,
    auth_enabled=False,
    sso_enabled=False,
    force_sso=False,
):
    """Start the Flask web UI server."""
    import os
    import threading
    import webbrowser

    # Allow env var overrides (Docker-friendly)
    force_sso = force_sso or os.getenv("ANIWORLD_WEB_FORCE_SSO", "0") == "1"
    sso_enabled = sso_enabled or force_sso or os.getenv("ANIWORLD_WEB_SSO", "0") == "1"
    auth_enabled = (
        auth_enabled or force_sso or os.getenv("ANIWORLD_WEB_AUTH", "0") == "1"
    )

    app = create_app(
        auth_enabled=auth_enabled, sso_enabled=sso_enabled, force_sso=force_sso
    )
    app.config["WEB_HOST"] = host
    app.config["WEB_PORT"] = port
    if os.getenv("ANIWORLD_CACHE_WARM_ON_START", "0") == "1":
        _warm_runtime_caches_startup()
    _ensure_runtime_cache_warmer()
    display_host = "localhost" if host == "127.0.0.1" else host
    url = f"http://{display_host}:{port}"
    print(f"Starting AniWorld Web UI on {url}")

    debug = os.getenv("ANIWORLD_DEBUG_MODE", "0") == "1"

    # In debug mode, Flask's reloader spawns a child process that re-executes
    # this function. Only open the browser in the parent (reloader) process
    # to avoid opening it twice.
    is_reloader_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    if open_browser and not is_reloader_child:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()

    if debug:
        app.run(host=host, port=port, debug=True)
    else:
        from waitress import serve

        try:
            waitress_threads = int(os.environ.get("ANIWORLD_WEB_THREADS", "12"))
        except ValueError:
            waitress_threads = 12
        waitress_threads = max(4, min(waitress_threads, 64))

        serve(app, host=host, port=port, threads=waitress_threads)
