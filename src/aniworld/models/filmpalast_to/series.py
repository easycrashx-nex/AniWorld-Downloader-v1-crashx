try:
    from ..common import clean_title
except ImportError:
    from aniworld.models.common import clean_title

from .episode import FilmPalastEpisode
from .season import FilmPalastSeason
from .shared import (
    group_filmpalast_search_results,
    normalize_filmpalast_series_key,
    parse_filmpalast_title_info,
    parse_filmpalast_virtual_url,
    search_filmpalast_entries,
)


class FilmPalastSeries:
    def __init__(self, url: str):
        virtual = parse_filmpalast_virtual_url(url)
        if not virtual or virtual["mode"] != "series":
            raise ValueError(f"Invalid FilmPalast series URL: {url}")

        self.url = url
        self.source_url = virtual["source_url"]
        self._series_title = virtual["series_title"]
        self.__entries = None
        self.__representative = None
        self.__seasons = None

    @property
    def title(self):
        return self._series_title

    @property
    def title_cleaned(self):
        return clean_title(self.title)

    @property
    def _entries(self):
        if self.__entries is None:
            all_entries = search_filmpalast_entries(self._series_title)
            target_key = normalize_filmpalast_series_key(self._series_title)
            matches = []
            for item in all_entries:
                info = parse_filmpalast_title_info(item.get("title"))
                if not info:
                    continue
                if normalize_filmpalast_series_key(info["series_title"]) != target_key:
                    continue
                entry_url = item.get("link") or ""
                if entry_url.startswith("/"):
                    entry_url = f"https://filmpalast.to{entry_url}"
                matches.append(
                    {
                        **item,
                        **info,
                        "url": entry_url,
                    }
                )
            if not matches and self.source_url:
                try:
                    fallback_episode = FilmPalastEpisode(self.source_url)
                    fallback_info = fallback_episode._title_info
                    if (
                        fallback_info
                        and normalize_filmpalast_series_key(
                            fallback_info.get("series_title")
                        )
                        == target_key
                    ):
                        matches.append(
                            {
                                "title": fallback_episode.title_de,
                                "poster_url": fallback_episode.poster_url or "",
                                "url": self.source_url,
                                **fallback_info,
                            }
                        )
                except Exception:
                    pass
            matches.sort(key=lambda item: (item["season_number"], item["episode_number"]))
            self.__entries = matches
        return self.__entries

    @property
    def _representative(self):
        if self.__representative is None:
            first_url = self.source_url or (self._entries[0]["url"] if self._entries else "")
            if not first_url:
                raise ValueError(f"No FilmPalast episodes found for series '{self.title}'")
            self.__representative = FilmPalastEpisode(
                first_url,
                parsed_info=self._entries[0] if self._entries else None,
            )
        return self.__representative

    @property
    def description(self):
        return self._representative.description

    @property
    def genres(self):
        return self._representative.genres

    @property
    def release_year(self):
        return self._representative.release_year

    @property
    def poster_url(self):
        poster = self._entries[0].get("poster_url") if self._entries else ""
        return poster or self._representative.poster_url

    @property
    def seasons(self):
        if self.__seasons is None:
            season_numbers = sorted({entry["season_number"] for entry in self._entries})
            if not season_numbers and self._representative.is_series_episode:
                season_numbers = [self._representative.season_number]
            self.__seasons = [
                FilmPalastSeason(
                    self._build_season_url(season_number),
                    series=self,
                )
                for season_number in season_numbers
            ]
        return self.__seasons

    @property
    def season_count(self):
        return len(self.seasons)

    def _build_season_url(self, season_number):
        from .shared import build_filmpalast_season_url

        return build_filmpalast_season_url(self.source_url, self.title, season_number)

    def download(self):
        for season in self.seasons:
            for episode in season.episodes:
                episode.download()

    def watch(self):
        for season in self.seasons:
            for episode in season.episodes:
                episode.watch()

    def syncplay(self):
        for season in self.seasons:
            for episode in season.episodes:
                episode.syncplay()
