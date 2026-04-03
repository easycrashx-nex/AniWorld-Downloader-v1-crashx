import os
import re
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urljoin
from urllib.request import Request, urlopen

try:
    from ...config import Audio, GLOBAL_SESSION, NAMING_TEMPLATE, Subtitles, logger
    from ...extractors import provider_functions
    from ..common import (
        ProviderData,
        check_downloaded,
        clean_title,
        download as episode_download,
        syncplay as episode_syncplay,
        watch as episode_watch,
    )
except ImportError:
    from aniworld.config import (
        Audio,
        GLOBAL_SESSION,
        NAMING_TEMPLATE,
        Subtitles,
        logger,
    )
    from aniworld.extractors import provider_functions
    from aniworld.models.common import (
        ProviderData,
        check_downloaded,
        clean_title,
        download as episode_download,
        syncplay as episode_syncplay,
        watch as episode_watch,
    )

FILMPALAST_EPISODE_PATTERN = re.compile(
    r"^https?://(?:www\.)?filmpalast\.to/stream/[A-Za-z0-9\-]+/?(?:[?#].*)?$",
    re.IGNORECASE,
)

_PROVIDER_NAME_MAP = {
    "voe": "VOE",
    "voe hd": "VOE",
    "voe.sx": "VOE",
    "veev": "Veev",
    "veev hd": "Veev",
    "vidhide": "Vidhide",
    "vidhide hd": "Vidhide",
    "vidara": "Vidara",
    "vidara hd": "Vidara",
    "vidoza": "Vidoza",
    "vidmoly": "Vidmoly",
    "vidsonic": "Vidsonic",
    "vidsonic hd": "Vidsonic",
    "doodstream": "Doodstream",
    "dood": "Doodstream",
    "filemoon": "Filemoon",
    "streamtape": "Streamtape",
    "loadx": "LoadX",
    "luluvdo": "Luluvdo",
}

_LANGUAGE_KEY_MAP = {
    "German Dub": (Audio.GERMAN, Subtitles.NONE),
    "English Dub": (Audio.ENGLISH, Subtitles.NONE),
}

_FILMPALAST_PROVIDER_PREFERENCE = (
    "Vidhide",
    "Vidara",
    "Vidoza",
    "Vidmoly",
    "VOE",
)

_FILMPALAST_REQUEST_HEADERS = {
    "User-Agent": os.getenv(
        "ANIWORLD_FILMPALAST_UA",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    ),
    "Referer": "https://filmpalast.to/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.7,en;q=0.6",
}


def _fetch_filmpalast_text(url):
    request = Request(url, headers=_FILMPALAST_REQUEST_HEADERS)
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def _resolve_filmpalast_redirect(url):
    request = Request(url, headers=_FILMPALAST_REQUEST_HEADERS)
    with urlopen(request, timeout=20) as response:
        return response.geturl()


class FilmPalastEpisode:
    """Movie-like episode wrapper for direct filmpalast.to stream URLs."""

    def __init__(
        self,
        url: str,
        selected_path: str = None,
        selected_language: str = None,
        selected_provider: str = None,
    ):
        if not self.is_valid_filmpalast_episode_url(url):
            raise ValueError(f"Invalid FilmPalast URL: {url}")

        self.url = url.rstrip("/")
        self.__selected_path_param = selected_path
        self.__selected_language_param = selected_language
        self.__selected_provider_param = selected_provider

        self.__html = None
        self.__title_de = None
        self.__description = None
        self.__genres = None
        self.__release_year = None
        self.__runtime_min = None
        self.__image_url = None
        self.__provider_data = None
        self.__provider_availability = None
        self.__selected_path = None
        self.__selected_language = None
        self.__selected_provider = None
        self.__redirect_url = None
        self.__provider_url = None
        self.__base_folder = None
        self.__folder_path = None
        self.__file_name = None
        self.__file_extension = None
        self.__episode_path = None
        self.__is_downloaded = None

    @staticmethod
    def is_valid_filmpalast_episode_url(url):
        return bool(FILMPALAST_EPISODE_PATTERN.match((url or "").strip()))

    @property
    def _html(self):
        if self.__html is None:
            logger.debug("fetching (%s)...", self.url)
            self.__html = _fetch_filmpalast_text(self.url)
        return self.__html

    @property
    def title_de(self):
        if self.__title_de is None:
            match = re.search(r'<em itemprop="name">(.*?)</em>', self._html)
            if match:
                self.__title_de = re.sub(r"\s+", " ", match.group(1)).strip()
            else:
                slug = self.url.rstrip("/").rsplit("/", 1)[-1]
                self.__title_de = slug.replace("-", " ").title()
        return self.__title_de

    @property
    def title(self):
        return self.title_de

    @property
    def title_cleaned(self):
        return clean_title(self.title_de)

    @property
    def description(self):
        if self.__description is None:
            match = re.search(
                r'<span itemprop="description">(.*?)</span>', self._html, re.DOTALL
            )
            if match:
                self.__description = re.sub(r"\s+", " ", match.group(1)).strip()
            else:
                self.__description = ""
        return self.__description

    @property
    def genres(self):
        if self.__genres is None:
            self.__genres = [
                re.sub(r"\s+", " ", item).strip()
                for item in re.findall(
                    r'href="https://filmpalast.to/search/genre/.*?">(.*?)</a>',
                    self._html,
                )
                if item.strip()
            ]
        return self.__genres

    @property
    def release_year(self):
        if self.__release_year is None:
            match = re.search(r"Ver&ouml;ffentlicht:\s*(\d{4})", self._html)
            self.__release_year = int(match.group(1)) if match else ""
        return self.__release_year

    @property
    def runtime_min(self):
        if self.__runtime_min is None:
            match = re.search(r"Spielzeit:\s*<em>(.*?)</em>", self._html)
            if match:
                digits = re.sub(r"[^0-9]", "", match.group(1))
                self.__runtime_min = int(digits) if digits else None
            else:
                self.__runtime_min = None
        return self.__runtime_min

    @property
    def image_url(self):
        if self.__image_url is None:
            match = re.search(r'itemprop="image"\s+src="(.*?)"', self._html)
            if match:
                self.__image_url = urljoin(self.url, match.group(1).strip())
            else:
                self.__image_url = None
        return self.__image_url

    @property
    def poster_url(self):
        return self.image_url

    def _normalize_provider_name(self, raw_name):
        if not raw_name:
            return None
        key = raw_name.strip().lower()
        return _PROVIDER_NAME_MAP.get(key)

    @property
    def provider_data(self):
        if self.__provider_data is None:
            providers = {
                entry["name"]: entry["url"]
                for entry in self.provider_availability
                if entry.get("supported")
            }

            if not providers:
                raise ValueError("No supported stream providers found on FilmPalast")

            self.__provider_data = ProviderData(
                {(Audio.GERMAN, Subtitles.NONE): providers}
            )
        return self.__provider_data

    @property
    def provider_availability(self):
        if self.__provider_availability is None:
            entries = []
            blocks = re.findall(
                r'<ul class="currentStreamLinks">(.*?)</ul>', self._html, re.DOTALL
            )

            for block in blocks:
                name_match = re.search(r'<p class="hostName">(.*?)</p>', block)
                url_match = re.search(
                    r'<a [^>]*?(?:data-player-url|href)="([^"]+)"', block
                )
                provider_name = self._normalize_provider_name(
                    name_match.group(1) if name_match else ""
                )
                provider_url = (
                    urljoin(self.url, url_match.group(1).strip()) if url_match else None
                )

                if not provider_name or not provider_url:
                    continue
                if any(
                    existing["name"] == provider_name and existing["url"] == provider_url
                    for existing in entries
                ):
                    continue

                entries.append(
                    {
                        "name": provider_name,
                        "url": provider_url,
                        "supported": f"get_direct_link_from_{provider_name.lower()}"
                        in provider_functions,
                    }
                )

            self.__provider_availability = entries
        return self.__provider_availability

    def _available_language_labels(self):
        labels = []
        for (audio, subtitles), providers in self.provider_data._data.items():
            if not providers:
                continue
            if audio == Audio.GERMAN and subtitles == Subtitles.NONE:
                labels.append("German Dub")
            elif audio == Audio.ENGLISH and subtitles == Subtitles.NONE:
                labels.append("English Dub")
        return labels or ["German Dub"]

    @property
    def selected_path(self):
        if self.__selected_path is None:
            raw_path = self.__selected_path_param or os.getenv(
                "ANIWORLD_DOWNLOAD_PATH", str(Path.home() / "Downloads")
            )
            path = Path(raw_path).expanduser()
            if not path.is_absolute():
                path = Path.home() / path
            self.__selected_path = str(path)
        return self.__selected_path

    @selected_path.setter
    def selected_path(self, value):
        self.__selected_path_param = value
        self.__selected_path = None
        self.__base_folder = None
        self.__folder_path = None
        self.__episode_path = None

    @property
    def selected_language(self):
        if self.__selected_language is None:
            preferred = self.__selected_language_param or os.getenv(
                "ANIWORLD_LANGUAGE", "German Dub"
            )
            available = self._available_language_labels()
            self.__selected_language = (
                preferred if preferred in available else available[0]
            )
        return self.__selected_language

    @selected_language.setter
    def selected_language(self, value):
        self.__selected_language_param = value
        self.__selected_language = None
        self.__selected_provider = None
        self.__redirect_url = None
        self.__provider_url = None

    @property
    def selected_provider(self):
        if self.__selected_provider is None:
            preferred = self.__selected_provider_param or os.getenv("ANIWORLD_PROVIDER")
            providers = self.provider_data.get(
                _LANGUAGE_KEY_MAP.get(
                    self.selected_language, (Audio.GERMAN, Subtitles.NONE)
                )
            )
            if not providers:
                providers = next(iter(self.provider_data._data.values()))
            if preferred and preferred in providers:
                self.__selected_provider = preferred
            else:
                self.__selected_provider = next(
                    (
                        provider_name
                        for provider_name in _FILMPALAST_PROVIDER_PREFERENCE
                        if provider_name in providers
                    ),
                    next(iter(providers)),
                )
        return self.__selected_provider

    @property
    def redirect_url(self):
        if self.__redirect_url is None:
            link = self.provider_link(self.selected_language, self.selected_provider)
            if not link:
                raise ValueError(
                    f"Provider '{self.selected_provider}' is not available for {self.url}"
                )
            self.__redirect_url = link
        return self.__redirect_url

    @property
    def provider_url(self):
        if self.__provider_url is None:
            self.__provider_url = _resolve_filmpalast_redirect(self.redirect_url)
        return self.__provider_url

    @property
    def stream_url(self):
        extractor = provider_functions.get(
            f"get_direct_link_from_{self.selected_provider.lower()}"
        )
        if not extractor:
            raise ValueError(
                f"The provider '{self.selected_provider}' is not yet implemented."
            )
        return extractor(self.provider_url)

    @property
    def _base_folder(self):
        if self.__base_folder is None:
            folder_name = self.title_cleaned
            if self.release_year:
                folder_name = f"{folder_name} ({self.release_year})"
            self.__base_folder = Path(self.selected_path) / folder_name
        return self.__base_folder

    @property
    def _folder_path(self):
        if self.__folder_path is None:
            self.__folder_path = self._base_folder
        return self.__folder_path

    @property
    def _file_name(self):
        if self.__file_name is None:
            naming_template = os.getenv("ANIWORLD_NAMING_TEMPLATE", NAMING_TEMPLATE)
            fallback_name = self.title_cleaned
            try:
                file_template = naming_template.split("/")[-1]
            except IndexError:
                file_template = fallback_name + ".mkv"

            if "." in file_template:
                file_template = ".".join(file_template.split(".")[:-1])

            file_template = (
                file_template.replace("%title%", "{title}")
                .replace("%year%", "{year}")
                .replace("%imdbid%", "{imdbid}")
                .replace("%season%", "{season}")
                .replace("%episode%", "{episode}")
                .replace("%language%", "{language}")
            )

            try:
                rendered = file_template.format(
                    title=self.title_cleaned,
                    year=self.release_year or "",
                    imdbid="",
                    season="01",
                    episode="001",
                    language=self.selected_language,
                )
                rendered = clean_title(rendered) or fallback_name
            except Exception:
                rendered = fallback_name

            self.__file_name = rendered
        return self.__file_name

    @property
    def _file_extension(self):
        if self.__file_extension is None:
            naming_template = os.getenv("ANIWORLD_NAMING_TEMPLATE", NAMING_TEMPLATE)
            file_part = naming_template.split("/")[-1] if naming_template else ""
            self.__file_extension = (
                file_part.rsplit(".", 1)[-1] if "." in file_part else "mkv"
            )
        return self.__file_extension

    @property
    def _episode_path(self):
        if self.__episode_path is None:
            self.__episode_path = (
                self._folder_path / f"{self._file_name}.{self._file_extension}"
            )
        return self.__episode_path

    @property
    def is_downloaded(self):
        if self.__is_downloaded is None:
            self.__is_downloaded = check_downloaded(self._episode_path)
        return self.__is_downloaded

    @property
    def episode_number(self):
        return 1

    @property
    def season(self):
        return SimpleNamespace(season_number=1)

    def provider_link(self, language, provider):
        language_key = _LANGUAGE_KEY_MAP.get(
            language, (Audio.GERMAN, Subtitles.NONE)
        )
        return self.provider_data.get(language_key).get(provider)

    download = episode_download
    watch = episode_watch
    syncplay = episode_syncplay
