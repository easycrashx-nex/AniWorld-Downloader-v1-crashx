import json
from urllib.parse import urlparse

import niquests

try:
    from ...config import DEFAULT_USER_AGENT, GLOBAL_SESSION
except ImportError:
    from aniworld.config import DEFAULT_USER_AGENT, GLOBAL_SESSION


def _extract_filecode(embed_url):
    path = urlparse(embed_url).path.rstrip("/")
    filecode = path.rsplit("/", 1)[-1]
    if not filecode:
        raise ValueError(f"Invalid Vidara URL: {embed_url}")
    return filecode


def _get_vidara_payload(embed_url):
    filecode = _extract_filecode(embed_url)
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Referer": embed_url,
        "Origin": "https://vidara.to",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
    }
    response = GLOBAL_SESSION.post(
        "https://vidara.to/api/stream",
        headers=headers,
        data=json.dumps({"filecode": filecode, "device": "web"}),
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"Unexpected Vidara response for {embed_url}")
    return payload


def get_direct_link_from_vidara(embed_url):
    """Get direct Vidara HLS stream URL."""
    if not embed_url:
        raise ValueError("Embed URL cannot be empty")

    try:
        payload = _get_vidara_payload(embed_url)
    except niquests.RequestException as err:
        raise ValueError(f"Failed to fetch Vidara stream data: {err}") from err

    stream_url = payload.get("streaming_url")
    if not stream_url:
        raise ValueError(f"No Vidara streaming URL found in {embed_url}")
    return stream_url


def get_preview_image_link_from_vidara(embed_url):
    """Get Vidara preview image URL."""
    if not embed_url:
        raise ValueError("Embed URL cannot be empty")

    try:
        payload = _get_vidara_payload(embed_url)
    except niquests.RequestException as err:
        raise ValueError(f"Failed to fetch Vidara preview data: {err}") from err

    preview_url = payload.get("thumbnail")
    if not preview_url:
        raise ValueError(f"No Vidara preview image found in {embed_url}")
    return preview_url
