import html as html_module
import re
from urllib.parse import parse_qs, quote, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

try:
    from ...config import DEFAULT_USER_AGENT
except ImportError:
    from aniworld.config import DEFAULT_USER_AGENT

FILMPALAST_REQUEST_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Referer": "https://filmpalast.to/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.7,en;q=0.6",
}

FILMPALAST_SERIES_EPISODE_TITLE_PATTERN = re.compile(
    r"^(?P<series>.+?)\s+S(?P<season>\d{1,2})E(?P<episode>\d{1,3})(?:\s*[:-]\s*(?P<episode_title>.+))?$",
    re.IGNORECASE,
)

FILMPALAST_SEARCH_URL = "https://filmpalast.to/search/title/{}"
FILMPALAST_FORM_SEARCH_URL = "https://filmpalast.to/search"


def fetch_filmpalast_html(url, data=None):
    payload = None
    if data is not None:
        payload = urlencode(data).encode("utf-8")
    request = Request(url, data=payload, headers=FILMPALAST_REQUEST_HEADERS)
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_filmpalast_search_results(html):
    article_pattern = re.compile(
        r"<article\b[^>]*class=\"[^\"]*\bliste\b[^\"]*\"[^>]*>(.*?)</article>",
        re.IGNORECASE | re.DOTALL,
    )
    title_pattern = re.compile(
        r'<h2[^>]*>\s*<a[^>]+href="(?:(?:https?:)?//filmpalast\.to)?(/stream/[^"]+)"[^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    cover_pattern = re.compile(
        r'<img[^>]+src="([^"]*/files/movies/[^"]+)"',
        re.IGNORECASE,
    )
    generic_image_pattern = re.compile(
        r'<img[^>]+src="([^"]+)"[^>]+(?:class="[^"]*\bcover(?:-opacity)?\b[^"]*"|alt="[^"]*stream)',
        re.IGNORECASE,
    )

    results = []
    seen = set()

    for article_match in article_pattern.finditer(html):
        block = article_match.group(1)
        title_match = title_pattern.search(block)
        if not title_match:
            continue

        link = title_match.group(1).strip()
        if not link or link in seen:
            continue
        seen.add(link)

        title = html_module.unescape(
            re.sub(r"<[^>]+>", "", title_match.group(2) or "").strip()
        )
        image_match = cover_pattern.search(block) or generic_image_pattern.search(block)
        poster_url = ""
        if image_match:
            raw_image = image_match.group(1).strip()
            if raw_image.startswith("//"):
                poster_url = f"https:{raw_image}"
            elif raw_image.startswith("http"):
                poster_url = raw_image
            else:
                poster_url = f"https://filmpalast.to{raw_image}"

        results.append(
            {
                "title": title or link.rsplit("/", 1)[-1].replace("-", " ").title(),
                "link": link,
                "poster_url": poster_url,
            }
        )

    if results:
        return results

    fallback_pattern = re.compile(
        r'<a[^>]+href="(?:(?:https?:)?//filmpalast\.to)?(/stream/[^"]+)"[^>]*title="([^"]+)"',
        re.IGNORECASE,
    )
    for match in fallback_pattern.finditer(html):
        link = match.group(1).strip()
        if not link or link in seen:
            continue
        seen.add(link)
        results.append(
            {
                "title": html_module.unescape(match.group(2).strip()),
                "link": link,
                "poster_url": "",
            }
        )

    return results


def search_filmpalast_entries(keyword):
    query_value = (keyword or "").strip()
    if not query_value:
        return []

    html = fetch_filmpalast_html(FILMPALAST_SEARCH_URL.format(quote(query_value)))
    results = parse_filmpalast_search_results(html)
    if results:
        return results

    fallback_html = fetch_filmpalast_html(
        FILMPALAST_FORM_SEARCH_URL,
        data={"headerSearchText": query_value, "t1": "tags"},
    )
    return parse_filmpalast_search_results(fallback_html)


def parse_filmpalast_title_info(title):
    title = (title or "").strip()
    if not title:
        return None

    match = FILMPALAST_SERIES_EPISODE_TITLE_PATTERN.match(title)
    if not match:
        return None

    series_title = re.sub(r"\s+", " ", (match.group("series") or "").strip())
    episode_title = re.sub(
        r"\s+",
        " ",
        (match.group("episode_title") or "").strip(),
    )
    return {
        "series_title": series_title,
        "season_number": int(match.group("season")),
        "episode_number": int(match.group("episode")),
        "episode_title": episode_title,
        "is_series_episode": True,
    }


def normalize_filmpalast_series_key(title):
    return re.sub(r"[^a-z0-9]+", "", (title or "").strip().lower())


def build_filmpalast_series_url(source_url, series_title):
    parsed = urlparse((source_url or "").strip())
    query = urlencode({"aw_mode": "series", "aw_title": series_title})
    return urlunparse(parsed._replace(query=query, fragment=""))


def build_filmpalast_season_url(source_url, series_title, season_number):
    parsed = urlparse((source_url or "").strip())
    query = urlencode(
        {
            "aw_mode": "season",
            "aw_title": series_title,
            "aw_season": int(season_number),
        }
    )
    return urlunparse(parsed._replace(query=query, fragment=""))


def parse_filmpalast_virtual_url(url):
    parsed = urlparse((url or "").strip())
    params = parse_qs(parsed.query or "")
    mode = params.get("aw_mode") or ""
    if isinstance(mode, list):
        mode = mode[0] if mode else ""
    if mode not in {"series", "season"}:
        return None
    title = params.get("aw_title", "")
    if isinstance(title, list):
        title = title[0] if title else ""
    if not title:
        return None
    title = html_module.unescape(title)
    season_number = None
    if mode == "season":
        try:
            raw_season = params.get("aw_season", "0")
            if isinstance(raw_season, list):
                raw_season = raw_season[0] if raw_season else "0"
            season_number = int(raw_season)
        except ValueError:
            season_number = None
    return {
        "mode": mode,
        "series_title": title,
        "season_number": season_number,
        "source_url": urlunparse(parsed._replace(query="", fragment="")),
    }


def group_filmpalast_search_results(results):
    grouped = {}
    passthrough = []

    for item in results or []:
        info = parse_filmpalast_title_info(item.get("title"))
        if not info:
            passthrough.append(item)
            continue

        key = normalize_filmpalast_series_key(info["series_title"])
        bucket = grouped.setdefault(
            key,
            {
                "series_title": info["series_title"],
                "poster_url": item.get("poster_url") or "",
                "entries": [],
                "source_url": item.get("link") or "",
            },
        )
        if not bucket.get("poster_url") and item.get("poster_url"):
            bucket["poster_url"] = item["poster_url"]
        bucket["entries"].append(
            {
                **item,
                **info,
            }
        )

    series_results = []
    for bucket in grouped.values():
        bucket["entries"].sort(
            key=lambda entry: (
                entry["season_number"],
                entry["episode_number"],
            )
        )
        source_url = bucket["source_url"] or bucket["entries"][0].get("link") or ""
        series_results.append(
            {
                "title": bucket["series_title"],
                "link": build_filmpalast_series_url(
                    f"https://filmpalast.to{source_url}"
                    if source_url.startswith("/")
                    else source_url,
                    bucket["series_title"],
                ),
                "poster_url": bucket["poster_url"],
                "is_series": True,
            }
        )

    return passthrough + series_results
