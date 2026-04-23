import os
import re
import tomllib
import inspect
from enum import Enum
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import fake_useragent
from niquests import RequestException, Session
from niquests.adapters import HTTPAdapter
from niquests.utils import create_resolver
from packaging.version import parse as parse_version

from .env import merge_env
from .logger import get_logger

VERSION = None


def display_version(value=None):
    raw = str(value if value is not None else VERSION or "").strip()
    if not raw:
        return ""
    return raw if raw.lower().startswith("v") else f"v{raw}"


def _read_source_version():
    try:
        pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
        with pyproject_path.open("rb") as fh:
            data = tomllib.load(fh)
        return data.get("project", {}).get("version")
    except Exception:
        return None

try:
    VERSION = version("aniworld")
except PackageNotFoundError:
    VERSION = _read_source_version()
else:
    VERSION = _read_source_version() or VERSION


def is_newest_version() -> bool:
    """Checks if the installed version is the newest available on PyPI."""
    if not VERSION:
        return False

    try:
        response = GLOBAL_SESSION.get("https://pypi.org/pypi/aniworld/json")
        response.raise_for_status()
        latest_version = response.json()["info"]["version"]
        return parse_version(VERSION) >= parse_version(latest_version)
    except RequestException:
        # Could not fetch PyPI info, assume not newest
        return False


# AniWorld configuration directory
ANIWORLD_CONFIG_DIR = Path.home() / ".aniworld"

# Load .env file whenever config is imported
merge_env(
    Path(__file__).resolve().parent / ".env.example",
    ANIWORLD_CONFIG_DIR / ".env",
)

logger = get_logger(__name__)

NAMING_TEMPLATE = os.getenv(
    "ANIWORLD_NAMING_TEMPLATE",
    "{title} ({year}) [imdbid-{imdbid}]/Season {season}/{title} S{season}E{episode}.mkv",
)

# Video codec configuration
VIDEO_CODEC = os.getenv("ANIWORLD_VIDEO_CODEC", "copy")

# Simple codec mapping using ffmpeg defaults
VIDEO_CODEC_MAP = {
    "copy": "copy",
    "h264": "libx264",
    "h265": "libx265",
    "av1": "libsvtav1",
}

ACTION_METHODS = {
    "Download": "download",
    "Watch": "watch",
    "Syncplay": "syncplay",
}


def get_video_codec():
    """Get and validate video codec from environment variable."""
    codec = VIDEO_CODEC
    if codec not in VIDEO_CODEC_MAP:
        logger.warning(
            f"Invalid video codec '{codec}', falling back to 'copy'. Valid options: {list(VIDEO_CODEC_MAP.keys())}"
        )
        return "copy"
    return VIDEO_CODEC_MAP[codec]


# NIQUESTS

try:
    DEFAULT_USER_AGENT = str(
        fake_useragent.UserAgent(os=["Windows", "Mac OS X"]).random
    )
except fake_useragent.errors.FakeUserAgentError:
    # TODO: fix - currently happens on nuitka builds
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"

LULUVDO_USER_AGENT = (
    "Mozilla/5.0 (Android 15; Mobile; rv:132.0) Gecko/132.0 Firefox/132.0"
)

DNS_MODE_SYSTEM = "system"
DNS_MODE_GOOGLE = "google"
DNS_MODE_CLOUDFLARE = "cloudflare"
DNS_MODE_QUAD9 = "quad9"

DNS_MODE_CONFIG = {
    DNS_MODE_SYSTEM: {
        "label": "System default",
        "resolver": None,
        "servers": [],
        "env_resolver": "",
    },
    DNS_MODE_GOOGLE: {
        "label": "Google (8.8.8.8)",
        "resolver": [
            "dou://8.8.8.8",
            "dou://8.8.4.4",
            "dot+google://",
            "doh+google://",
        ],
        "servers": ["8.8.8.8", "8.8.4.4"],
        "env_resolver": "dou://8.8.8.8",
    },
    DNS_MODE_CLOUDFLARE: {
        "label": "Cloudflare (1.1.1.1)",
        "resolver": [
            "dou://1.1.1.1",
            "dou://1.0.0.1",
            "doh+cloudflare://",
        ],
        "servers": ["1.1.1.1", "1.0.0.1"],
        "env_resolver": "dou://1.1.1.1",
    },
    DNS_MODE_QUAD9: {
        "label": "Quad9 (9.9.9.9)",
        "resolver": [
            "dou://9.9.9.9",
            "dou://149.112.112.112",
            "doh://dns.quad9.net",
        ],
        "servers": ["9.9.9.9", "149.112.112.112"],
        "env_resolver": "dou://9.9.9.9",
    },
}


def normalize_dns_mode(value):
    mode = str(value or "").strip().lower()
    return mode if mode in DNS_MODE_CONFIG else DNS_MODE_GOOGLE


def get_dns_mode_label(mode):
    normalized = normalize_dns_mode(mode)
    return DNS_MODE_CONFIG[normalized]["label"]


def get_dns_resolver_servers(mode):
    normalized = normalize_dns_mode(mode)
    return list(DNS_MODE_CONFIG[normalized]["servers"])


def get_dns_resolver_definition(mode):
    normalized = normalize_dns_mode(mode)
    resolver = DNS_MODE_CONFIG[normalized]["resolver"]
    return list(resolver) if resolver else None


def _get_adapter_kwargs(resolver):
    params = inspect.signature(HTTPAdapter.__init__).parameters
    kwargs = {}
    if "resolver" in params:
        kwargs["resolver"] = resolver
    if "quic_cache_layer" in params and hasattr(GLOBAL_SESSION, "quic_cache_layer"):
        kwargs["quic_cache_layer"] = getattr(GLOBAL_SESSION, "quic_cache_layer")
    if "max_retries" in params and hasattr(GLOBAL_SESSION, "retries"):
        kwargs["max_retries"] = getattr(GLOBAL_SESSION, "retries")
    if "disable_http2" in params and hasattr(GLOBAL_SESSION, "_disable_http2"):
        kwargs["disable_http2"] = getattr(GLOBAL_SESSION, "_disable_http2")
    if "disable_http3" in params and hasattr(GLOBAL_SESSION, "_disable_http3"):
        kwargs["disable_http3"] = getattr(GLOBAL_SESSION, "_disable_http3")
    if "disable_ipv6" in params and hasattr(GLOBAL_SESSION, "disable_ipv6"):
        kwargs["disable_ipv6"] = getattr(GLOBAL_SESSION, "disable_ipv6")
    if "disable_ipv4" in params and hasattr(GLOBAL_SESSION, "disable_ipv4"):
        kwargs["disable_ipv4"] = getattr(GLOBAL_SESSION, "disable_ipv4")
    if "pool_connections" in params and hasattr(GLOBAL_SESSION, "pool_connections"):
        kwargs["pool_connections"] = getattr(GLOBAL_SESSION, "pool_connections")
    if "pool_maxsize" in params and hasattr(GLOBAL_SESSION, "pool_maxsize"):
        kwargs["pool_maxsize"] = getattr(GLOBAL_SESSION, "pool_maxsize")
    return kwargs


def get_global_dns_mode():
    return normalize_dns_mode(getattr(GLOBAL_SESSION, "_aniworld_dns_mode", DNS_MODE_GOOGLE))


def apply_global_dns_mode(mode):
    normalized = normalize_dns_mode(mode)
    resolver_definition = get_dns_resolver_definition(normalized)
    env_resolver = str(DNS_MODE_CONFIG[normalized].get("env_resolver") or "").strip()
    if env_resolver:
        os.environ["NIQUESTS_DNS_URL"] = env_resolver
    else:
        os.environ.pop("NIQUESTS_DNS_URL", None)
    new_resolver = create_resolver(resolver_definition)

    GLOBAL_SESSION.resolver = new_resolver
    GLOBAL_SESSION._own_resolver = True
    GLOBAL_SESSION.mount("https://", HTTPAdapter(**_get_adapter_kwargs(new_resolver)))
    GLOBAL_SESSION.mount("http://", HTTPAdapter(**_get_adapter_kwargs(new_resolver)))
    GLOBAL_SESSION._aniworld_dns_mode = normalized

    os.environ["ANIWORLD_DNS_MODE"] = normalized

    return normalized

GLOBAL_SESSION = Session(
    resolver=get_dns_resolver_definition(
        normalize_dns_mode(os.environ.get("ANIWORLD_DNS_MODE", DNS_MODE_GOOGLE))
    ),
    headers={
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Dest": "document",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Mode": "navigate",
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://aniworld.to/search",
        "Priority": "u=0, i",
    },
)
GLOBAL_SESSION._aniworld_dns_mode = normalize_dns_mode(
    os.environ.get("ANIWORLD_DNS_MODE", DNS_MODE_GOOGLE)
)
_default_env_resolver = str(
    DNS_MODE_CONFIG[get_global_dns_mode()].get("env_resolver") or ""
).strip()
if _default_env_resolver:
    os.environ["NIQUESTS_DNS_URL"] = _default_env_resolver
else:
    os.environ.pop("NIQUESTS_DNS_URL", None)

logger.debug("Config initialized successfully")

# -----------------------------
# Provider Stuff
# -----------------------------
SUPPORTED_PROVIDERS = (
    "VOE",
    "Vidhide",
    "Vidara",
    "Filemoon",
    "Vidmoly",
    "Vidoza",
    "Doodstream",
    # "LoadX",
    # "Luluvdo",
    # "Streamtape",
)

PROVIDER_HEADERS_D = {
    "Vidhide": {
        "User-Agent": DEFAULT_USER_AGENT,
        "Referer": "https://dhtpre.com/",
        "Origin": "https://dhtpre.com",
    },
    "Vidara": {
        "User-Agent": DEFAULT_USER_AGENT,
        "Referer": "https://vidara.to/",
        "Origin": "https://vidara.to",
    },
    "Vidmoly": {"Referer": "https://vidmoly.biz"},
    "Doodstream": {"Referer": "https://dood.li/"},
    "VOE": {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Referer": "https://voe.sx/",
        "Origin": "https://voe.sx",
    },
    "LoadX": {"Accept": "*/*"},
    "Filemoon": {"User-Agent": DEFAULT_USER_AGENT, "Referer": "https://filemoon.to"},
    "Luluvdo": {
        "User-Agent": LULUVDO_USER_AGENT,
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://luluvdo.com",
        "Referer": "https://luluvdo.com/",
    },
}

PROVIDER_HEADERS_W = {
    "Vidhide": {
        "User-Agent": DEFAULT_USER_AGENT,
        "Referer": "https://dhtpre.com/",
        "Origin": "https://dhtpre.com",
    },
    "Vidara": {
        "User-Agent": DEFAULT_USER_AGENT,
        "Referer": "https://vidara.to/",
        "Origin": "https://vidara.to",
    },
    "Vidmoly": {"Referer": "https://vidmoly.biz"},
    "Doodstream": {"Referer": "https://dood.li/"},
    "VOE": {"User-Agent": DEFAULT_USER_AGENT},
    "Luluvdo": {"User-Agent": LULUVDO_USER_AGENT},
    "Filemoon": {"User-Agent": DEFAULT_USER_AGENT, "Referer": "https://filemoon.to"},
}


# -----------------------------
# Language Stuff
# -----------------------------
class Audio(Enum):
    """
    Available audio language options:

        - JAPANESE: Japanese dubbed audio
        - GERMAN:   German dubbed audio
        - ENGLISH:  English dubbed audio

    Required source for each option:

        Japanese Dub -> Source: German Sub, English Sub
        German Dub   -> Source: German Dub
        English Dub  -> Source: English Dub
    """

    JAPANESE = "Japanese"
    GERMAN = "German"
    ENGLISH = "English"


class Subtitles(Enum):
    """
    Available subtitle language options:

        - NONE:    No subtitles
        - GERMAN:  German subtitles
        - ENGLISH: English subtitles

    Required source for each option:

        German Sub   -> Source: German Sub
        English Sub  -> Source: English Sub
    """

    NONE = "None"
    GERMAN = "German"
    ENGLISH = "English"


# Map site-specific language keys to semantic meaning
LANG_KEY_MAP = {
    "1": (Audio.GERMAN, Subtitles.NONE),  # German Dub
    "2": (Audio.JAPANESE, Subtitles.ENGLISH),  # English Sub
    "3": (Audio.JAPANESE, Subtitles.GERMAN),  # German Sub
    "4": (Audio.ENGLISH, Subtitles.NONE),  # English Dub
}

LANG_LABELS = {
    "1": "German Dub",
    "2": "English Sub",
    "3": "German Sub",
    "4": "English Dub",
}

LANG_CODE_MAP = {
    Audio.ENGLISH: "eng",
    Audio.GERMAN: "deu",
    Audio.JAPANESE: "jpn",
    Subtitles.ENGLISH: "eng",
    Subtitles.GERMAN: "deu",
    Subtitles.NONE: None,
}


INVERSE_LANG_KEY_MAP = {v: k for k, v in LANG_KEY_MAP.items()}
INVERSE_LANG_LABELS = {v: k for k, v in LANG_LABELS.items()}

# -----------------------------
# Patterns
# -----------------------------


ANIWORLD_SERIES_PATTERN = re.compile(
    r"^https?://(www\.)?aniworld\.to/anime/stream/[a-zA-Z0-9\-]+/?$", re.IGNORECASE
)

# series slug + (/staffel-N or /filme)
ANIWORLD_SEASON_PATTERN = re.compile(
    r"^https?://(www\.)?aniworld\.to/anime/stream/"
    r"[a-zA-Z0-9\-]+/"
    r"(staffel-\d+|filme)"
    r"/?$",
    re.IGNORECASE,
)

ANIWORLD_EPISODE_PATTERN = re.compile(
    r"^https?://(www\.)?aniworld\.to/anime/stream/"
    r"[a-zA-Z0-9\-]+/"  # series slug
    r"(staffel-\d+/episode-\d+|"  # season/episode
    r"filme/film-\d+)"  # movie/film
    r"/?$",
    re.IGNORECASE,
)

HANIME_TV_SERIES_PATTERN = re.compile(
    r"^https?://(?:www\.)?hanime\.tv/videos/hentai/[A-Za-z0-9\-]+/?$",
    re.IGNORECASE,
)

FILMPALAST_EPISODE_PATTERN = re.compile(
    r"^https?://(?:www\.)?filmpalast\.to/stream/[A-Za-z0-9\-]+/?(?:[?#].*)?$",
    re.IGNORECASE,
)

SERIENSTREAM_SERIES_PATTERN = re.compile(
    r"^https?://(www\.)?(serienstream|s)\.to/serie/[a-zA-Z0-9\-]+/?$", re.IGNORECASE
)

SERIENSTREAM_SEASON_PATTERN = re.compile(
    r"^https?://(www\.)?(serienstream|s)\.to/serie/"
    r"[a-zA-Z0-9\-]+/"
    r"staffel-\d+"
    r"/?$",
    re.IGNORECASE,
)

SERIENSTREAM_EPISODE_PATTERN = re.compile(
    r"^https?://(www\.)?(serienstream|s)\.to/serie/"
    r"[a-zA-Z0-9\-]+/"
    r"staffel-\d+/episode-\d+"
    r"/?$",
    re.IGNORECASE,
)

HIANIME_SERIES_PATTERN = re.compile(r"", re.IGNORECASE)

HIANIME_SEASON_PATTERN = re.compile(r"", re.IGNORECASE)

HIANIME_EPISODE_PATTERN = re.compile(r"", re.IGNORECASE)

# -----------------------------
# Directories
# -----------------------------

# TODO: add many other directories and use them throughout the app

# Determine mpv scripts directory
# On Linux/macOS: ~/.config/mpv/scripts
# On Windows: %APPDATA%\mpv\scripts
if os.name == "nt":
    MPV_CONFIG_DIR = Path(os.getenv("APPDATA")) / "mpv"
else:
    MPV_CONFIG_DIR = Path.home() / ".config" / "mpv"

MPV_SCRIPTS_DIR = MPV_CONFIG_DIR / "scripts"
