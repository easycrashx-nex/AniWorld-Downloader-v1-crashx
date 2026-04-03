import logging
import re
from urllib.parse import urljoin

import niquests

try:
    from ...config import DEFAULT_USER_AGENT, GLOBAL_SESSION, PROVIDER_HEADERS_D
except ImportError:
    from aniworld.config import DEFAULT_USER_AGENT, GLOBAL_SESSION, PROVIDER_HEADERS_D

logger = logging.getLogger(__name__)

PACKED_JS_PATTERN = re.compile(
    r"eval\(function\(p,a,c,k,e,d\)\{.*?\}\('(?P<p>[\s\S]*?)',\s*(?P<a>\d+),\s*(?P<c>\d+),\s*'(?P<k>[\s\S]*?)'\.split\('\|'\)",
    re.DOTALL,
)
LINKS_OBJECT_PATTERN = re.compile(r"var\s+links\s*=\s*\{(?P<body>.*?)\};", re.DOTALL)
LINK_ENTRY_PATTERN = re.compile(
    r'["\']?(?P<key>\w+)["\']?\s*:\s*["\'](?P<url>[^"\']+)["\']'
)
SOURCE_EXPR_PATTERN = re.compile(
    r"sources\s*:\s*\[\s*\{[^}]*file\s*:\s*(?P<expr>[^,}]+)",
    re.DOTALL,
)
DIRECT_URL_PATTERN = re.compile(r'["\'](?P<url>https?://[^"\']+\.m3u8[^"\']*)["\']')
RELATIVE_HLS_PATTERN = re.compile(r'["\'](?P<url>/[^"\']+\.m3u8[^"\']*)["\']')
IMAGE_PATTERN = re.compile(r'property="og:image"\s+content="(?P<url>[^"]+)"')
PLAYER_IMAGE_PATTERN = re.compile(r'image\s*:\s*["\'](?P<url>[^"\']+)["\']')


def _decode_base_n(token, radix):
    if radix <= 10:
        try:
            return int(token)
        except ValueError:
            return -1

    result = 0
    for char in token:
        if "0" <= char <= "9":
            digit = ord(char) - ord("0")
        elif "a" <= char <= "z":
            digit = ord(char) - ord("a") + 10
        elif "A" <= char <= "Z":
            digit = ord(char) - ord("A") + 36
        else:
            return -1

        if digit >= radix:
            return -1
        result = result * radix + digit

    return result


def _unpack_js(packed, radix, keywords):
    def _replace(match):
        token = match.group(1)
        index = _decode_base_n(token, radix)
        if 0 <= index < len(keywords) and keywords[index]:
            return keywords[index]
        return token

    return re.sub(r"\b(\w+)\b", _replace, packed)


def _unpack_vidhide_html(html):
    match = PACKED_JS_PATTERN.search(html)
    if not match:
        return html

    unpacked = _unpack_js(
        match.group("p"),
        int(match.group("a")),
        match.group("k").split("|"),
    )
    return unpacked or html


def _extract_links(unpacked, base_url):
    match = LINKS_OBJECT_PATTERN.search(unpacked)
    if not match:
        return {}

    links = {}
    for key, raw_url in LINK_ENTRY_PATTERN.findall(match.group("body")):
        links[key] = urljoin(base_url, raw_url)
    return links


def _extract_source_from_expression(unpacked, base_url):
    links = _extract_links(unpacked, base_url)
    match = SOURCE_EXPR_PATTERN.search(unpacked)
    if not match:
        return None

    expression = match.group("expr").strip()
    for raw_part in expression.split("||"):
        part = raw_part.strip().strip("()")
        if not part:
            continue
        if part.startswith("links."):
            candidate = links.get(part.split(".", 1)[1])
            if candidate:
                return candidate
        quoted = re.match(r'["\'](?P<url>[^"\']+)["\']', part)
        if quoted:
            return urljoin(base_url, quoted.group("url"))

    return None


def _extract_url_from_html(html, base_url):
    unpacked = _unpack_vidhide_html(html)

    source_url = _extract_source_from_expression(unpacked, base_url)
    if source_url:
        return source_url

    direct_match = DIRECT_URL_PATTERN.search(unpacked)
    if direct_match:
        return direct_match.group("url")

    relative_match = RELATIVE_HLS_PATTERN.search(unpacked)
    if relative_match:
        return urljoin(base_url, relative_match.group("url"))

    return None


def get_direct_link_from_vidhide(embeded_vidhide_link, headers=None):
    if not (embeded_vidhide_link or "").strip():
        raise ValueError("No Vidhide link provided.")

    try:
        if headers is None:
            headers = PROVIDER_HEADERS_D.get(
                "Vidhide", {"User-Agent": DEFAULT_USER_AGENT}
            )

        response = GLOBAL_SESSION.get(embeded_vidhide_link, headers=headers, timeout=30)
        response.raise_for_status()
        source_url = _extract_url_from_html(response.text, embeded_vidhide_link)
        if not source_url:
            raise ValueError("No Vidhide video source found in page.")
        return source_url
    except niquests.RequestException as err:
        raise ValueError(f"Failed to fetch Vidhide page: {err}") from err


def get_preview_image_link_from_vidhide(embeded_vidhide_link, headers=None):
    if not (embeded_vidhide_link or "").strip():
        raise ValueError("No Vidhide link provided.")

    try:
        if headers is None:
            headers = PROVIDER_HEADERS_D.get(
                "Vidhide", {"User-Agent": DEFAULT_USER_AGENT}
            )

        response = GLOBAL_SESSION.get(embeded_vidhide_link, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text

        match = IMAGE_PATTERN.search(html)
        if match:
            return urljoin(embeded_vidhide_link, match.group("url"))

        unpacked = _unpack_vidhide_html(html)
        player_match = PLAYER_IMAGE_PATTERN.search(unpacked)
        if player_match:
            return urljoin(embeded_vidhide_link, player_match.group("url"))

        raise ValueError("No Vidhide preview image found in page.")
    except niquests.RequestException as err:
        raise ValueError(f"Failed to fetch Vidhide preview image: {err}") from err
