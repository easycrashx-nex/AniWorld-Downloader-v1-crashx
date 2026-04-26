try:
    from .episode import FilmPalastEpisode
    from .shared import parse_filmpalast_virtual_url
except ImportError:
    from aniworld.models.filmpalast_to.episode import FilmPalastEpisode
    from aniworld.models.filmpalast_to.shared import parse_filmpalast_virtual_url


class FilmPalastSeason:
    def __init__(self, url, series=None):
        virtual = parse_filmpalast_virtual_url(url)
        if not virtual or virtual["mode"] != "season" or not virtual["season_number"]:
            raise ValueError(f"Invalid FilmPalast season URL: {url}")

        self.url = url
        self._series = series
        self._season_number = virtual["season_number"]
        self.__episodes = None

    @property
    def series(self):
        if self._series is None:
            from .series import FilmPalastSeries
            from .shared import build_filmpalast_series_url, parse_filmpalast_virtual_url

            virtual = parse_filmpalast_virtual_url(self.url)
            self._series = FilmPalastSeries(
                build_filmpalast_series_url(
                    virtual["source_url"],
                    virtual["series_title"],
                )
            )
        return self._series

    @property
    def season_number(self):
        return self._season_number

    @property
    def are_movies(self):
        return False

    @property
    def episodes(self):
        if self.__episodes is None:
            entries = [
                entry
                for entry in self.series._entries
                if entry["season_number"] == self.season_number
            ]
            self.__episodes = [
                FilmPalastEpisode(
                    entry["url"],
                    season=self,
                    series=self.series,
                    parsed_info=entry,
                )
                for entry in entries
            ]
        return self.__episodes

    @property
    def episode_count(self):
        return len(self.episodes)

    def download(self):
        for episode in self.episodes:
            episode.download()

    def watch(self):
        for episode in self.episodes:
            episode.watch()

    def syncplay(self):
        for episode in self.episodes:
            episode.syncplay()
