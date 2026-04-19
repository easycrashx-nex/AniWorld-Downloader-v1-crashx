const linkImportUrl = document.getElementById("linkImportUrl")
const linkImportAnalyzeBtn = document.getElementById("linkImportAnalyzeBtn")
const linkImportWorkspace = document.getElementById("linkImportWorkspace")
const linkImportSummary = document.getElementById("linkImportSummary")
const linkImportLanguage = document.getElementById("linkImportLanguage")
const linkImportProvider = document.getElementById("linkImportProvider")
const linkImportPath = document.getElementById("linkImportPath")
const linkImportStatus = document.getElementById("linkImportStatus")
const linkImportSeasons = document.getElementById("linkImportSeasons")
const linkImportSelectAllBtn = document.getElementById("linkImportSelectAllBtn")
const linkImportSelectCompatibleBtn = document.getElementById(
  "linkImportSelectCompatibleBtn",
)
const linkImportClearBtn = document.getElementById("linkImportClearBtn")
const linkImportQueueBtn = document.getElementById("linkImportQueueBtn")

const linkImportState = {
  resolved: null,
  series: null,
  seasons: [],
  episodeMap: new Map(),
}

if (linkImportAnalyzeBtn && linkImportUrl) {
  linkImportAnalyzeBtn.addEventListener("click", () => analyzeImportedLink())
  linkImportUrl.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault()
      analyzeImportedLink()
    }
  })
  linkImportLanguage?.addEventListener("change", () => {
    refreshLinkImportProviderOptions()
    updateLinkImportSelectionState()
  })
  linkImportProvider?.addEventListener("change", updateLinkImportSelectionState)
  linkImportSelectAllBtn?.addEventListener("click", () => toggleAllImportedEpisodes(true))
  linkImportSelectCompatibleBtn?.addEventListener("click", selectCompatibleImportedEpisodes)
  linkImportClearBtn?.addEventListener("click", () => toggleAllImportedEpisodes(false))
  linkImportQueueBtn?.addEventListener("click", queueImportedEpisodes)
  loadLinkImportPaths()
}

function linkImportToast(message) {
  if (
    window.AniworldNotifications &&
    typeof window.AniworldNotifications.add === "function"
  ) {
    window.AniworldNotifications.add(message, { source: "Link Import" })
  }
  const toast = document.getElementById("toast")
  if (!toast) return
  toast.textContent = message
  toast.style.display = "block"
  setTimeout(() => {
    toast.style.display = "none"
  }, 4000)
}

function linkImportEsc(value) {
  const div = document.createElement("div")
  div.textContent = String(value || "")
  return div.innerHTML
}

function formatLinkImportRelativeDate(value) {
  if (!value) return "Never"
  const raw = String(value).trim()
  const iso = raw.includes("T") ? raw : raw.replace(" ", "T")
  const normalized = /(?:Z|[+-]\d{2}:\d{2})$/i.test(iso) ? iso : `${iso}Z`
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) return raw
  const diffMinutes = Math.floor((Date.now() - date.getTime()) / 60000)
  if (diffMinutes < 1) return "Just now"
  if (diffMinutes < 60) return `${diffMinutes} min ago`
  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours} h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays} d ago`
}

function getLinkImportSiteLabel(site) {
  if (site === "sto") return "SerienStream"
  if (site === "filmpalast") return "FilmPalast"
  return "AniWorld"
}

function getLinkImportKindLabel(kind) {
  if (kind === "series") return "Series Link"
  if (kind === "season") return "Season Link"
  if (kind === "episode") return "Episode Link"
  if (kind === "movie") return "Movie Link"
  return "Direct Link"
}

function getLinkImportEpisodeKey(url) {
  return String(url || "").trim()
}

function setLinkImportBusy(isBusy) {
  if (!linkImportAnalyzeBtn) return
  linkImportAnalyzeBtn.disabled = isBusy
  linkImportAnalyzeBtn.textContent = isBusy ? "Analyzing..." : "Analyze Link"
}

async function loadLinkImportPaths() {
  if (!linkImportPath) return
  try {
    const response = await fetch("/api/custom-paths")
    const data = await response.json()
    while (linkImportPath.options.length > 1) linkImportPath.remove(1)
    for (const path of data.paths || []) {
      const option = document.createElement("option")
      option.value = String(path.id)
      option.textContent = path.name
      linkImportPath.appendChild(option)
    }
    if (window.refreshCustomSelect) window.refreshCustomSelect(linkImportPath)
  } catch (_error) {
    // Best effort only.
  }
}

async function analyzeImportedLink() {
  const rawUrl = String(linkImportUrl?.value || "").trim()
  if (!rawUrl) {
    linkImportToast("Paste a link first.")
    return
  }

  setLinkImportBusy(true)
  try {
    const resolveResponse = await fetch("/api/link-import/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: rawUrl }),
    })
    const resolved = await resolveResponse.json()
    if (!resolveResponse.ok || resolved.error) {
      throw new Error(resolved.error || "Link could not be resolved")
    }
    await loadImportedLinkManifest(resolved)
  } catch (error) {
    linkImportWorkspace.hidden = true
    linkImportToast(`Link analysis failed: ${error.message}`)
  } finally {
    setLinkImportBusy(false)
  }
}

async function loadImportedLinkManifest(resolved) {
  const baseSeriesUrl = resolved.series_url || resolved.normalized_url
  const [seriesResponse, seasonsResponse] = await Promise.all([
    fetch("/api/series?url=" + encodeURIComponent(baseSeriesUrl)),
    resolved.kind === "movie"
      ? Promise.resolve({
          ok: true,
          json: async () => ({
            seasons: [
              {
                url: resolved.focus_season_url || resolved.normalized_url,
                season_number: 1,
                episode_count: 1,
                are_movies: true,
              },
            ],
          }),
        })
      : fetch("/api/seasons?url=" + encodeURIComponent(baseSeriesUrl)),
  ])

  const seriesData = await seriesResponse.json()
  const seasonsData = await seasonsResponse.json()
  if (!seriesResponse.ok || seriesData.error) {
    throw new Error(seriesData.error || "Series details could not be loaded")
  }
  if (!seasonsResponse.ok || seasonsData.error) {
    throw new Error(seasonsData.error || "Season list could not be loaded")
  }

  const allSeasons = Array.isArray(seasonsData.seasons) ? seasonsData.seasons : []
  const targetSeasons = resolved.focus_season_url
    ? allSeasons.filter(
        (season) =>
          String(season.url || "").replace(/\/$/, "") ===
          String(resolved.focus_season_url || "").replace(/\/$/, ""),
      )
    : allSeasons

  const seasonsToFetch = targetSeasons.length
    ? targetSeasons
    : [
        {
          url: resolved.focus_season_url || resolved.normalized_url,
          season_number: 1,
          episode_count: 1,
          are_movies: resolved.kind === "movie",
        },
      ]

  const episodeResponses = await Promise.all(
    seasonsToFetch.map(async (season) => {
      const response = await fetch(
        "/api/episodes?include_providers=1&url=" + encodeURIComponent(season.url),
      )
      const data = await response.json()
      if (!response.ok || data.error) {
        throw new Error(data.error || "Episodes could not be loaded")
      }
      return {
        season,
        episodes: Array.isArray(data.episodes) ? data.episodes : [],
      }
    }),
  )

  linkImportState.resolved = resolved
  linkImportState.series = seriesData
  linkImportState.seasons = episodeResponses.map(({ season, episodes }) => ({
    season,
    episodes: episodes.map((episode) => ({
      ...episode,
      checked:
        resolved.kind === "season" || resolved.kind === "movie"
          ? true
          : resolved.focus_episode_url
            ? String(episode.url || "").replace(/\/$/, "") ===
              String(resolved.focus_episode_url || "").replace(/\/$/, "")
            : false,
    })),
  }))
  linkImportState.episodeMap = new Map()

  for (const seasonEntry of linkImportState.seasons) {
    for (const episode of seasonEntry.episodes) {
      linkImportState.episodeMap.set(getLinkImportEpisodeKey(episode.url), episode)
    }
  }

  renderLinkImportSummary()
  populateLinkImportLanguageOptions()
  refreshLinkImportProviderOptions()
  renderImportedLinkSeasons()
  updateLinkImportSelectionState()
  linkImportWorkspace.hidden = false
}

function getAllImportedEpisodes() {
  return linkImportState.seasons.flatMap((entry) => entry.episodes || [])
}

function getAllImportedLanguages() {
  const languages = new Set()
  for (const episode of getAllImportedEpisodes()) {
    for (const language of episode.languages || []) {
      if (language) languages.add(language)
    }
  }
  return Array.from(languages)
}

function populateLinkImportLanguageOptions() {
  if (!linkImportLanguage) return
  const languages = getAllImportedLanguages()
  linkImportLanguage.innerHTML = languages
    .map((language) => `<option value="${linkImportEsc(language)}">${linkImportEsc(language)}</option>`)
    .join("")

  const preferred = languages.includes("German Dub")
    ? "German Dub"
    : languages.includes("German Sub")
      ? "German Sub"
      : languages[0] || ""
  if (preferred) {
    linkImportLanguage.value = preferred
  }
  if (window.refreshCustomSelect) window.refreshCustomSelect(linkImportLanguage)
}

function getImportedProvidersForLanguage(language) {
  const providers = new Set()
  for (const episode of getAllImportedEpisodes()) {
    const entries = (episode.providers_by_language || {})[language] || []
    for (const provider of entries) {
      if (provider) providers.add(provider)
    }
  }
  return Array.from(providers)
}

function refreshLinkImportProviderOptions() {
  if (!linkImportProvider) return
  const language = linkImportLanguage?.value || ""
  const providers = getImportedProvidersForLanguage(language)
  const previous = linkImportProvider.value || "Auto"

  linkImportProvider.innerHTML =
    '<option value="Auto">Auto (best available)</option>' +
    providers
      .map(
        (provider) =>
          `<option value="${linkImportEsc(provider)}">${linkImportEsc(provider)}</option>`,
      )
      .join("")

  linkImportProvider.value = providers.includes(previous) || previous === "Auto"
    ? previous
    : "Auto"

  if (window.refreshCustomSelect) window.refreshCustomSelect(linkImportProvider)
}

function renderLinkImportSummary() {
  if (!linkImportSummary) return
  const series = linkImportState.series || {}
  const resolved = linkImportState.resolved || {}
  const episodes = getAllImportedEpisodes()
  const seasonCount = linkImportState.seasons.length
  const posterUrl = String(series.poster_url || "").trim()
  const languageCount = getAllImportedLanguages().length

  linkImportSummary.innerHTML = `
    <div class="link-import-summary-card">
      <div class="link-import-summary-poster">
        ${
          posterUrl
            ? `<img src="${linkImportEsc(posterUrl)}" alt="${linkImportEsc(series.title || "Poster")}" />`
            : `<div class="link-import-summary-placeholder">${linkImportEsc(
                String(series.title || "?").slice(0, 2).toUpperCase(),
              )}</div>`
        }
      </div>
      <div class="link-import-summary-copy">
        <div class="link-import-summary-head">
          <span class="modal-source-badge">${linkImportEsc(
            getLinkImportSiteLabel(resolved.site),
          )}</span>
          <span class="link-import-type-badge">${linkImportEsc(
            getLinkImportKindLabel(resolved.kind),
          )}</span>
        </div>
        <h2>${linkImportEsc(series.title || "Resolved Link")}</h2>
        <p class="link-import-summary-description">${
          linkImportEsc(series.description || "Episodes and providers resolved from the pasted link.")
        }</p>
        <div class="link-import-summary-stats">
          <span>${episodes.length} ${episodes.length === 1 ? "episode" : "episodes"}</span>
          <span>${seasonCount} ${seasonCount === 1 ? "season" : "seasons"}</span>
          <span>${languageCount} ${languageCount === 1 ? "language" : "languages"}</span>
          <span>${linkImportEsc(series.release_year || "Unknown year")}</span>
        </div>
        <div class="link-import-summary-meta">
          <span>Last downloaded: ${linkImportEsc(
            formatLinkImportRelativeDate(series.last_downloaded_at),
          )}</span>
          <span>Last synced: ${linkImportEsc(
            formatLinkImportRelativeDate(series.last_synced_at),
          )}</span>
        </div>
      </div>
    </div>
  `
}

function renderImportedLinkSeasons() {
  if (!linkImportSeasons) return
  linkImportSeasons.innerHTML = ""

  linkImportState.seasons.forEach((entry, index) => {
    const section = document.createElement("div")
    section.className = "season-section"
    section.dataset.seasonIndex = String(index)

    const season = entry.season || {}
    const title = season.are_movies
      ? entry.episodes.length === 1
        ? "Movie"
        : "Movies"
      : `Season ${season.season_number}`
    const providerCount = new Set(
      entry.episodes.flatMap((episode) => episode.providers_flat || []),
    ).size

    const header = document.createElement("div")
    header.className = "season-header expanded"
    header.innerHTML = `
      <div class="season-label">
        <span class="season-arrow">&#9654;</span>
        <div class="season-label-stack">
          <span class="season-title">${linkImportEsc(title)}</span>
          <span class="season-subline">${entry.episodes.length} episode(s) - ${providerCount} provider(s)</span>
        </div>
      </div>
    `
    header.addEventListener("click", () => toggleImportedSeason(index))

    const body = document.createElement("div")
    body.className = "season-body expanded"
    body.id = `linkImportSeasonBody-${index}`

    body.innerHTML = `
      <div class="season-toolbar">
        <div class="season-toolbar-meta">
          <span class="season-selected-count" data-link-import-selected="${index}">0 selected</span>
        </div>
        <label class="season-all-label" onclick="event.stopPropagation()">
          <input type="checkbox" data-link-import-season-toggle="${index}">
          Select season
        </label>
      </div>
    `

    entry.episodes.forEach((episode, episodeIndex) => {
      const item = document.createElement("div")
      item.className = "episode-item"
      const primaryTitle =
        episode.title_de ||
        episode.title_en ||
        `${season.are_movies ? "Movie" : "Episode"} ${episode.episode_number || episodeIndex + 1}`
      const secondaryTitle =
        episode.title_en && episode.title_en !== episode.title_de
          ? episode.title_en
          : ""
      const providerChips = (episode.providers_flat || [])
        .slice(0, 6)
        .map(
          (provider) =>
            `<span class="link-import-pill link-import-pill-provider">${linkImportEsc(
              provider,
            )}</span>`,
        )
        .join("")
      const languageChips = (episode.languages || [])
        .map(
          (language) =>
            `<span class="link-import-pill">${linkImportEsc(language)}</span>`,
        )
        .join("")

      item.innerHTML = `
        <label class="episode-checkbox" aria-label="Select ${linkImportEsc(primaryTitle)}">
          <input
            class="episode-selector link-import-episode-checkbox"
            type="checkbox"
            value="${linkImportEsc(episode.url)}"
            ${episode.checked ? "checked" : ""}
          >
        </label>
        <div class="episode-main">
          <div class="episode-topline">
            <span class="ep-num">${season.are_movies ? "MOV" : `E${linkImportEsc(episode.episode_number)}`}</span>
            <div class="episode-title-stack">
              <span class="ep-title">${linkImportEsc(primaryTitle)}</span>
              ${
                secondaryTitle
                  ? `<span class="ep-subtitle">${linkImportEsc(secondaryTitle)}</span>`
                  : ""
              }
            </div>
          </div>
          <div class="episode-meta-row">
            <div class="link-import-pill-list">${languageChips}${providerChips}</div>
            ${
              episode.downloaded
                ? '<span class="episode-state-chip is-downloaded">Downloaded</span>'
                : '<span class="episode-state-chip">Available</span>'
            }
          </div>
        </div>
      `
      const checkbox = item.querySelector(".link-import-episode-checkbox")
      checkbox?.addEventListener("change", () => {
        episode.checked = checkbox.checked
        updateLinkImportSelectionState()
      })
      body.appendChild(item)
    })

    const seasonToggle = body.querySelector(
      `[data-link-import-season-toggle="${index}"]`,
    )
    seasonToggle?.addEventListener("change", () => {
      entry.episodes.forEach((episode) => {
        episode.checked = seasonToggle.checked
      })
      renderImportedLinkSeasons()
      updateLinkImportSelectionState()
    })

    section.appendChild(header)
    section.appendChild(body)
    linkImportSeasons.appendChild(section)
  })
}

function toggleImportedSeason(index) {
  const section = linkImportSeasons?.querySelector(
    `[data-season-index="${index}"]`,
  )
  if (!section) return
  const header = section.querySelector(".season-header")
  const body = section.querySelector(".season-body")
  const isExpanded = header.classList.contains("expanded")
  header.classList.toggle("expanded", !isExpanded)
  body.classList.toggle("expanded", !isExpanded)
}

function getSelectedImportedEpisodes() {
  return getAllImportedEpisodes().filter((episode) => episode.checked)
}

function isImportedEpisodeCompatible(episode) {
  const language = linkImportLanguage?.value || ""
  const provider = linkImportProvider?.value || "Auto"
  const providers = (episode.providers_by_language || {})[language] || []
  if (!language) return false
  if (!providers.length) return false
  if (provider === "Auto") return true
  return providers.includes(provider)
}

function updateLinkImportSelectionState() {
  const allEpisodes = getAllImportedEpisodes()
  const selectedEpisodes = getSelectedImportedEpisodes()
  const compatibleEpisodes = allEpisodes.filter(isImportedEpisodeCompatible)
  const selectedCompatible = selectedEpisodes.filter(isImportedEpisodeCompatible)

  linkImportState.seasons.forEach((entry, index) => {
    const selectedCount = entry.episodes.filter((episode) => episode.checked).length
    const selectedBadge = linkImportSeasons?.querySelector(
      `[data-link-import-selected="${index}"]`,
    )
    if (selectedBadge) {
      selectedBadge.textContent = selectedCount
        ? `${selectedCount} selected`
        : "0 selected"
    }
    const seasonToggle = linkImportSeasons?.querySelector(
      `[data-link-import-season-toggle="${index}"]`,
    )
    if (seasonToggle) {
      seasonToggle.checked =
        entry.episodes.length > 0 && selectedCount === entry.episodes.length
    }
  })

  if (linkImportStatus) {
    const language = linkImportLanguage?.value || "Language"
    const provider = linkImportProvider?.value || "Auto"
    const incompatibleCount = selectedEpisodes.length - selectedCompatible.length
    linkImportStatus.innerHTML = `
      <strong>${selectedEpisodes.length} selected</strong>
      <span>${compatibleEpisodes.length} compatible with ${linkImportEsc(language)} - ${linkImportEsc(provider)}</span>
      ${
        incompatibleCount > 0
          ? `<span class="link-import-status-warning">${incompatibleCount} selected item(s) do not match the current setup</span>`
          : ""
      }
    `
  }

  if (linkImportQueueBtn) {
    linkImportQueueBtn.disabled = selectedCompatible.length === 0
  }
}

function toggleAllImportedEpisodes(checked) {
  linkImportState.seasons.forEach((entry) => {
    entry.episodes.forEach((episode) => {
      episode.checked = checked
    })
  })
  renderImportedLinkSeasons()
  updateLinkImportSelectionState()
}

function selectCompatibleImportedEpisodes() {
  const language = linkImportLanguage?.value || ""
  if (!language) {
    linkImportToast("No language is available for this import.")
    return
  }
  let matched = 0
  linkImportState.seasons.forEach((entry) => {
    entry.episodes.forEach((episode) => {
      episode.checked = isImportedEpisodeCompatible(episode)
      if (episode.checked) matched += 1
    })
  })
  renderImportedLinkSeasons()
  updateLinkImportSelectionState()
  if (!matched) {
    linkImportToast("No episodes match the current language/provider setup.")
  }
}

function chooseImportedEpisodeProvider(episode) {
  const language = linkImportLanguage?.value || ""
  const preferredProvider = linkImportProvider?.value || "Auto"
  const available = (episode.providers_by_language || {})[language] || []
  if (!available.length) return ""
  if (preferredProvider === "Auto") return available[0]
  return available.includes(preferredProvider) ? preferredProvider : ""
}

async function queueImportedEpisodes() {
  const selectedEpisodes = getSelectedImportedEpisodes()
  if (!selectedEpisodes.length) {
    linkImportToast("Select at least one episode first.")
    return
  }

  const language = linkImportLanguage?.value || ""
  if (!language) {
    linkImportToast("No language is available for this import.")
    return
  }

  const providerGroups = new Map()
  let skipped = 0

  for (const episode of selectedEpisodes) {
    const chosenProvider = chooseImportedEpisodeProvider(episode)
    if (!chosenProvider) {
      skipped += 1
      continue
    }
    if (!providerGroups.has(chosenProvider)) {
      providerGroups.set(chosenProvider, [])
    }
    providerGroups.get(chosenProvider).push(episode.url)
  }

  if (!providerGroups.size) {
    linkImportToast("Nothing matches the selected language/provider setup.")
    return
  }

  linkImportQueueBtn.disabled = true
  linkImportQueueBtn.textContent = "Queueing..."

  let queued = 0
  let conflictSkipped = 0

  try {
    for (const [provider, episodes] of providerGroups.entries()) {
      const payload = {
        episodes,
        language,
        provider,
        title: linkImportState.series?.title || "Link Import",
        series_url:
          linkImportState.resolved?.series_url ||
          linkImportState.resolved?.normalized_url ||
          "",
      }
      if (linkImportPath?.value) {
        payload.custom_path_id = Number.parseInt(linkImportPath.value, 10)
      }
      const response = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      const data = await response.json()
      if (!response.ok || data.error) {
        throw new Error(data.error || "Queue request failed")
      }
      conflictSkipped += Number(data.skipped_conflicts || 0)
      queued += episodes.length - Number(data.skipped_conflicts || 0)
    }

    const parts = [`Queued ${queued} episode(s)`]
    if (skipped > 0) {
      parts.push(`${skipped} incompatible`)
    }
    if (conflictSkipped > 0) {
      parts.push(`${conflictSkipped} already queued/running`)
    }
    linkImportToast(parts.join(" - "))
    if (typeof window.loadQueue === "function") window.loadQueue()
  } catch (error) {
    linkImportToast("Queueing failed: " + error.message)
  } finally {
    linkImportQueueBtn.textContent = "Queue Selected"
    updateLinkImportSelectionState()
  }
}
