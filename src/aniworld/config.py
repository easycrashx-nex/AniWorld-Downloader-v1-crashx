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

# Legacy video codec configuration
VIDEO_CODEC = os.getenv("ANIWORLD_VIDEO_CODEC", "copy")

VIDEO_CODEC_MAP = {
    "copy": "copy",
    "h264": "libx264",
    "h265": "libx265",
    "av1": "libsvtav1",
}

ENCODING_MODE_COPY = "copy"
ENCODING_MODE_H264 = "h264"
ENCODING_MODE_H265 = "h265"
ENCODING_MODE_EXPERT = "expert"

ENCODING_AUDIO_COPY = "copy"
ENCODING_AUDIO_AAC = "aac"
ENCODING_AUDIO_AC3 = "ac3"

ENCODING_MODES = {
    ENCODING_MODE_COPY,
    ENCODING_MODE_H264,
    ENCODING_MODE_H265,
    ENCODING_MODE_EXPERT,
}

ENCODING_AUDIO_CODECS = {
    ENCODING_AUDIO_COPY,
    ENCODING_AUDIO_AAC,
    ENCODING_AUDIO_AC3,
}

ENCODING_VIDEO_ENCODERS = {
    "libx264": {"label": "CPU (libx264)", "family": "cpu", "codec": "h264"},
    "libx265": {"label": "CPU (libx265)", "family": "cpu", "codec": "h265"},
    "h264_nvenc": {"label": "NVENC H.264", "family": "nvenc", "codec": "h264"},
    "hevc_nvenc": {"label": "NVENC H.265", "family": "nvenc", "codec": "h265"},
    "h264_vaapi": {"label": "VAAPI H.264", "family": "vaapi", "codec": "h264"},
    "hevc_vaapi": {"label": "VAAPI H.265", "family": "vaapi", "codec": "h265"},
    "h264_videotoolbox": {
        "label": "VideoToolbox H.264",
        "family": "videotoolbox",
        "codec": "h264",
    },
    "hevc_videotoolbox": {
        "label": "VideoToolbox H.265",
        "family": "videotoolbox",
        "codec": "h265",
    },
    "libsvtav1": {"label": "CPU (SVT-AV1)", "family": "cpu", "codec": "av1"},
}

ENCODING_MODE_DEFAULT_ENCODERS = {
    ENCODING_MODE_H264: {
        "cpu": "libx264",
        "nvenc": "h264_nvenc",
        "vaapi": "h264_vaapi",
        "videotoolbox": "h264_videotoolbox",
    },
    ENCODING_MODE_H265: {
        "cpu": "libx265",
        "nvenc": "hevc_nvenc",
        "vaapi": "hevc_vaapi",
        "videotoolbox": "hevc_videotoolbox",
    },
}

ENCODING_PRESET_VALUES = {
    "ultrafast",
    "superfast",
    "veryfast",
    "faster",
    "fast",
    "medium",
    "slow",
    "slower",
    "veryslow",
}

ENCODING_MODE = os.getenv("ANIWORLD_ENCODING_MODE", "").strip().lower()
ENCODING_VIDEO_ENCODER = os.getenv("ANIWORLD_ENCODING_VIDEO_ENCODER", "auto").strip()
ENCODING_VIDEO_PRESET = (
    os.getenv("ANIWORLD_ENCODING_VIDEO_PRESET", "medium").strip().lower()
)
ENCODING_VIDEO_CRF = os.getenv("ANIWORLD_ENCODING_VIDEO_CRF", "23").strip()
ENCODING_AUDIO_CODEC = (
    os.getenv("ANIWORLD_ENCODING_AUDIO_CODEC", ENCODING_AUDIO_COPY).strip().lower()
)
ENCODING_VAAPI_DEVICE = os.getenv(
    "ANIWORLD_ENCODING_VAAPI_DEVICE",
    "/dev/dri/renderD128",
).strip()

ACTION_METHODS = {
    "Download": "download",
    "Watch": "watch",
    "Syncplay": "syncplay",
}


def get_video_codec():
    """Backward-compatible helper used by older code paths."""
    return get_ffmpeg_video_kwargs().get("vcodec", "copy")


def _legacy_encoding_mode_default():
    codec = str(VIDEO_CODEC or "").strip().lower()
    if codec == "h264":
        return ENCODING_MODE_H264
    if codec == "h265":
        return ENCODING_MODE_H265
    if codec == "av1":
        return ENCODING_MODE_EXPERT
    return ENCODING_MODE_COPY


def normalize_encoding_mode(value):
    mode = str(value or "").strip().lower()
    if not mode:
        return _legacy_encoding_mode_default()
    return mode if mode in ENCODING_MODES else ENCODING_MODE_COPY


def normalize_encoding_video_encoder(value):
    encoder = str(value or "auto").strip().lower()
    if not encoder:
        return "auto"
    return encoder if encoder == "auto" or encoder in ENCODING_VIDEO_ENCODERS else "auto"


def normalize_encoding_video_preset(value):
    preset = str(value or "medium").strip().lower()
    return preset if preset in ENCODING_PRESET_VALUES else "medium"


def normalize_encoding_video_crf(value):
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        parsed = 23
    return str(max(0, min(parsed, 51)))


def normalize_encoding_audio_codec(value):
    codec = str(value or ENCODING_AUDIO_COPY).strip().lower()
    return codec if codec in ENCODING_AUDIO_CODECS else ENCODING_AUDIO_COPY


def get_encoding_mode():
    return normalize_encoding_mode(os.getenv("ANIWORLD_ENCODING_MODE", ENCODING_MODE))


def get_encoding_video_encoder_preference():
    return normalize_encoding_video_encoder(
        os.getenv("ANIWORLD_ENCODING_VIDEO_ENCODER", ENCODING_VIDEO_ENCODER)
    )


def get_encoding_video_preset():
    return normalize_encoding_video_preset(
        os.getenv("ANIWORLD_ENCODING_VIDEO_PRESET", ENCODING_VIDEO_PRESET)
    )


def get_encoding_video_crf():
    return normalize_encoding_video_crf(
        os.getenv("ANIWORLD_ENCODING_VIDEO_CRF", ENCODING_VIDEO_CRF)
    )


def get_encoding_audio_codec():
    return normalize_encoding_audio_codec(
        os.getenv("ANIWORLD_ENCODING_AUDIO_CODEC", ENCODING_AUDIO_CODEC)
    )


def get_encoding_vaapi_device():
    device = str(
        os.getenv("ANIWORLD_ENCODING_VAAPI_DEVICE", ENCODING_VAAPI_DEVICE) or ""
    ).strip()
    return device or "/dev/dri/renderD128"


def resolve_encoding_video_encoder():
    mode = get_encoding_mode()
    preferred = get_encoding_video_encoder_preference()
    if mode == ENCODING_MODE_COPY:
        return "copy"
    if mode == ENCODING_MODE_EXPERT:
        if preferred != "auto":
            return preferred
        return "libx264"

    target_codec = "h264" if mode == ENCODING_MODE_H264 else "h265"
    if preferred != "auto":
        encoder_meta = ENCODING_VIDEO_ENCODERS.get(preferred)
        if encoder_meta and encoder_meta.get("codec") == target_codec:
            return preferred
        family = (encoder_meta or {}).get("family", "cpu")
    else:
        family = "cpu"
    return ENCODING_MODE_DEFAULT_ENCODERS[target_codec].get(
        family, ENCODING_MODE_DEFAULT_ENCODERS[target_codec]["cpu"]
    )


def get_active_encoding_settings():
    mode = get_encoding_mode()
    encoder = resolve_encoding_video_encoder()
    return {
        "mode": mode,
        "video_encoder_preference": get_encoding_video_encoder_preference(),
        "video_encoder": encoder,
        "video_preset": get_encoding_video_preset(),
        "video_crf": get_encoding_video_crf(),
        "audio_codec": get_encoding_audio_codec(),
        "vaapi_device": get_encoding_vaapi_device(),
        "enabled": mode != ENCODING_MODE_COPY or get_encoding_audio_codec() != ENCODING_AUDIO_COPY,
        "video_family": ENCODING_VIDEO_ENCODERS.get(encoder, {}).get("family", "copy"),
        "video_label": ENCODING_VIDEO_ENCODERS.get(encoder, {}).get("label", "Copy"),
    }


def get_ffmpeg_video_kwargs(settings=None):
    settings = settings or get_active_encoding_settings()
    encoder = str(settings.get("video_encoder") or "copy")
    if encoder == "copy" or settings.get("mode") == ENCODING_MODE_COPY:
        return {"vcodec": "copy"}

    preset = str(settings.get("video_preset") or "medium")
    crf = str(settings.get("video_crf") or "23")
    family = ENCODING_VIDEO_ENCODERS.get(encoder, {}).get("family", "cpu")

    if family == "nvenc":
        return {
            "vcodec": encoder,
            "preset": preset,
            "rc": "vbr",
            "cq": crf,
            "b:v": "0",
        }
    if family == "vaapi":
        return {
            "vcodec": encoder,
            "qp": crf,
            "vf": "format=nv12,hwupload",
        }
    if family == "videotoolbox":
        quality = max(1, min(100, 100 - int((int(crf) / 51) * 80)))
        return {
            "vcodec": encoder,
            "q:v": str(quality),
        }
    return {
        "vcodec": encoder,
        "preset": preset,
        "crf": crf,
    }


def get_ffmpeg_audio_kwargs(settings=None):
    settings = settings or get_active_encoding_settings()
    codec = str(settings.get("audio_codec") or ENCODING_AUDIO_COPY)
    if codec == ENCODING_AUDIO_COPY:
        return {"acodec": "copy"}
    return {"acodec": codec}


def apply_ffmpeg_encoding_args(node, settings=None):
    settings = settings or get_active_encoding_settings()
    encoder = str(settings.get("video_encoder") or "copy")
    if ENCODING_VIDEO_ENCODERS.get(encoder, {}).get("family") == "vaapi":
        return node.global_args("-vaapi_device", settings.get("vaapi_device") or get_encoding_vaapi_device())
    return node


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
            "dot://8.8.8.8?server_hostname=dns.google",
            "dot://8.8.4.4?server_hostname=dns.google",
            "doh+google://",
            "dou://8.8.8.8",
            "dou://8.8.4.4",
        ],
        "servers": ["8.8.8.8", "8.8.4.4"],
        "env_resolver": "dot://8.8.8.8?server_hostname=dns.google",
    },
    DNS_MODE_CLOUDFLARE: {
        "label": "Cloudflare (1.1.1.1)",
        "resolver": [
            "dot://1.1.1.1?server_hostname=cloudflare-dns.com",
            "dot://1.0.0.1?server_hostname=cloudflare-dns.com",
            "doh+cloudflare://",
            "dou://1.1.1.1",
            "dou://1.0.0.1",
        ],
        "servers": ["1.1.1.1", "1.0.0.1"],
        "env_resolver": "dot://1.1.1.1?server_hostname=cloudflare-dns.com",
    },
    DNS_MODE_QUAD9: {
        "label": "Quad9 (9.9.9.9)",
        "resolver": [
            "dot://9.9.9.9?server_hostname=dns.quad9.net",
            "dot://149.112.112.112?server_hostname=dns.quad9.net",
            "doh://dns.quad9.net",
            "dou://9.9.9.9",
            "dou://149.112.112.112",
        ],
        "servers": ["9.9.9.9", "149.112.112.112"],
        "env_resolver": "dot://9.9.9.9?server_hostname=dns.quad9.net",
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

FILMPALAST_SERIES_PATTERN = re.compile(
    r"^https?://(?:www\.)?filmpalast\.to/stream/[A-Za-z0-9\-]+/?\?(?:[^#]*&)?aw_mode=series(?:&[^#]*)?$",
    re.IGNORECASE,
)

FILMPALAST_SEASON_PATTERN = re.compile(
    r"^https?://(?:www\.)?filmpalast\.to/stream/[A-Za-z0-9\-]+/?\?(?:[^#]*&)?aw_mode=season(?:&[^#]*aw_season=\d+[^#]*)?$",
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
