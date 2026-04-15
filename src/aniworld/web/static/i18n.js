(function initAniworldI18n() {
  const body = document.body;
  if (!body) return;

  const originalTextNodes = new WeakMap();
  const originalTitle = document.title;
  const originalLang = document.documentElement.getAttribute("lang") || "en";
  let currentLocale =
    (window.ANIWORLD_BOOT_SETTINGS &&
      window.ANIWORLD_BOOT_SETTINGS.ui &&
      window.ANIWORLD_BOOT_SETTINGS.ui.locale) ||
    body.dataset.uiLocale ||
    "en";

  const EXACT = {
    de: {
      Browse: "Entdecken",
      Home: "Start",
      Library: "Bibliothek",
      Favorites: "Favoriten",
      Stats: "Statistiken",
      Timeline: "Zeitverlauf",
      Radar: "Radar",
      Queue: "Warteschlange",
      Settings: "Einstellungen",
      "Auto-Sync": "Auto-Sync",
      "Provider Health": "Provider-Status",
      "Audit Log": "Prüfprotokoll",
      Diagnostics: "Diagnose",
      Maintenance: "Wartung",
      Downloads: "Downloads",
      Configuration: "Konfiguration",
      History: "Verlauf",
      Updates: "Updates",
      Activity: "Aktivität",
      Runtime: "Laufzeit",
      Storage: "Speicher",
      Cache: "Cache",
      Testing: "Testen",
      Sessions: "Sitzungen",
      Live: "Live",
      Benchmark: "Benchmark",
      Failures: "Fehler",
      Pinned: "Angepinnt",
      Overview: "Übersicht",
      "Download Queue": "Download-Warteschlange",
      "Errors Only": "Nur Fehler",
      "Retry Failed": "Fehlgeschlagene erneut starten",
      "Clear Finished": "Abgeschlossene leeren",
      "Check Now": "Jetzt prüfen",
      Restart: "Neustart",
      "Update Now": "Jetzt aktualisieren",
      Status: "Status",
      Branch: "Branch",
      "Update Notes": "Update-Hinweise",
      "Server Info": "Server-Info",
      "Browser Notifications": "Browser-Benachrichtigungen",
      "External Notifications": "Externe Benachrichtigungen",
      "UI Settings": "UI-Einstellungen",
      "UI Language": "Oberflächensprache",
      "Theme Preset": "Theme-Vorgabe",
      Density: "Dichte",
      "UI Scale": "UI-Skalierung",
      "Theme Color": "Themenfarbe",
      "Card Radius": "Kartenradius",
      "Animation Speed": "Animationsgeschwindigkeit",
      "Content Width": "Inhaltsbreite",
      "Modal Width": "Modalbreite",
      "Nav Size": "Navigationsgröße",
      "Table Density": "Tabellendichte",
      "Background Effects": "Hintergrundeffekte",
      Custom: "Benutzerdefiniert",
      Airy: "Luftig",
      Cozy: "Gemütlich",
      Compact: "Kompakt",
      Tight: "Dicht",
      Smaller: "Kleiner",
      Default: "Standard",
      Larger: "Größer",
      Structured: "Strukturiert",
      Soft: "Weich",
      Round: "Rund",
      Slow: "Langsam",
      Normal: "Normal",
      Fast: "Schnell",
      Wide: "Breit",
      Dynamic: "Dynamisch",
      Minimal: "Minimal",
      Off: "Aus",
      "Default Search Filters": "Standard-Suchfilter",
      "Auto-Sync Defaults": "Auto-Sync-Standards",
      "Download Path": "Download-Pfad",
      Save: "Speichern",
      "Download Engine": "Download-Engine",
      "Speed Mode": "Geschwindigkeitsmodus",
      "Smart Retry Profile": "Intelligentes Retry-Profil",
      "Save Download Rules": "Download-Regeln speichern",
      "Disk Space Guard": "Speicherplatz-Schutz",
      "Backup & Restore": "Backup & Wiederherstellung",
      "Export Backup": "Backup exportieren",
      "Import Backup": "Backup importieren",
      Search: "Suchen",
      Random: "Zufall",
      Genre: "Genre",
      "Sort By": "Sortieren nach",
      "Favorites Only": "Nur Favoriten",
      "Downloaded Only": "Nur heruntergeladen",
      "Reset Filters": "Filter zurücksetzen",
      "Quick Genres": "Schnellgenres",
      "Fresh picks": "Neu dabei",
      "Trending now": "Gerade angesagt",
      "New Animes": "Neue Animes",
      "Popular Animes": "Beliebte Animes",
      "New Series": "Neue Serien",
      "Popular Series": "Beliebte Serien",
      "All Locations": "Alle Speicherorte",
      "All Languages": "Alle Sprachen",
      "Largest First": "Größte zuerst",
      "Most Episodes": "Meiste Folgen",
      "All Titles": "Alle Titel",
      "Only Missing Episodes": "Nur fehlende Folgen",
      "Only Duplicates": "Nur Duplikate",
      "Only Clean Titles": "Nur saubere Titel",
      "Library Compare": "Bibliotheksabgleich",
      "Select Visible": "Sichtbare auswählen",
      "Clear Selection": "Auswahl leeren",
      "Auto-Repair Missing": "Fehlende automatisch reparieren",
      "Refresh Compare": "Abgleich aktualisieren",
      "Favorite Series": "Favorisierte Serien",
      "Download Health": "Download-Gesundheit",
      Quality: "Qualität",
      "Recent Activity": "Letzte Aktivitäten",
      "New Episodes": "Neue Folgen",
      "Mark Seen": "Als gesehen markieren",
      "User Audit": "Benutzer-Audit",
      "All Users": "Alle Benutzer",
      "All Actions": "Alle Aktionen",
      Logins: "Anmeldungen",
      Retries: "Wiederholungen",
      "Edit Sync Job": "Sync-Job bearbeiten",
      Language: "Sprache",
      Provider: "Provider",
      Path: "Pfad",
      Enabled: "Aktiviert",
      Disabled: "Deaktiviert",
      Cancel: "Abbrechen",
      "Select All": "Alle auswählen",
      Clear: "Leeren",
      "Sync Selected": "Auswahl synchronisieren",
      "Sync All": "Alles synchronisieren",
      "Provider Scoreboard": "Provider-Rangliste",
      "Provider Score History": "Provider-Score-Verlauf",
      "Provider Benchmark": "Provider-Benchmark",
      "Sample Episode URL": "Beispiel-Folgen-URL",
      "Run Benchmark": "Benchmark starten",
      "Provider Failure Analytics": "Provider-Fehleranalyse",
      "Maintenance Actions": "Wartungsaktionen",
      "Warm Runtime Caches": "Laufzeit-Caches aufwärmen",
      "Snapshot Provider Scores": "Provider-Scores speichern",
      "Recover Worker": "Worker wiederherstellen",
      "Clear Temp Files": "Temporäre Dateien löschen",
      "Provider Test Tool": "Provider-Testwerkzeug",
      "Episode URL": "Folgen-URL",
      "Run Test": "Test starten",
      "Download Session History": "Download-Sitzungsverlauf",
      "System Diagnostics": "Systemdiagnose",
      "Runtime Cache": "Laufzeit-Cache",
      Unsupported: "Nicht unterstützt",
      "Not Available": "Nicht verfügbar",
      Granted: "Erlaubt",
      Blocked: "Blockiert",
      "Ask in Browser": "Im Browser fragen",
      Unavailable: "Nicht verfügbar",
      "Loading...": "Wird geladen...",
      "Checking...": "Prüfe...",
      "Check whether this installation is behind GitHub and launch a guided update from the web UI.":
        "Prüfe, ob diese Installation hinter GitHub liegt, und starte ein geführtes Update direkt aus der Weboberfläche.",
      "In Progress": "Läuft",
      Queued: "Eingereiht",
      Failed: "Fehlgeschlagen",
      Cancelled: "Abgebrochen",
      "Retry Now": "Jetzt erneut starten",
      "Hard Cancel": "Hart abbrechen",
      Manual: "Manuell",
      Retry: "Erneut",
      "German Dub": "Deutsch Dub",
      "English Sub": "Englisch Sub",
      "German Sub": "Deutsch Sub",
      "English Dub": "Englisch Dub",
      "Direct / local": "Direkt / lokal",
      Direct: "Direkt",
    },
  };

  const PHRASES = {
    de: {
      "Manage users, storage targets, and sync defaults without leaving the web console.":
        "Verwalte Nutzer, Speicherziele und Sync-Standards direkt in der Weboberfläche.",
      "Search AniWorld titles, inspect seasons, and queue downloads from a cleaner control surface.":
        "Durchsuche AniWorld-Titel, prüfe Staffeln und stelle Downloads über eine aufgeräumte Oberfläche in die Warteschlange.",
      "Search AniWorld titles, inspect seasons, and queue downloads. FilmPalast movie links can be pasted directly into search.":
        "Durchsuche AniWorld-Titel, prüfe Staffeln und stelle Downloads in die Warteschlange. FilmPalast-Filmlinks können direkt in die Suche eingefügt werden.",
      "Browse downloaded titles by location, season, and episode from a single overview.":
        "Durchsuche heruntergeladene Titel nach Speicherort, Staffel und Folge in einer einzigen Übersicht.",
      "Track downloads, storage usage, queue pressure, and provider stability from one cleaner dashboard.":
        "Verfolge Downloads, Speicherverbrauch, Warteschlangenlast und Provider-Stabilität in einem übersichtlichen Dashboard.",
      "Keep your pinned series in one place and jump back into them without digging through search again.":
        "Halte deine angepinnten Serien an einem Ort und springe ohne erneutes Suchen direkt zurück.",
      "Keep tracked series current and manage scheduled download jobs from one place.":
        "Halte verfolgte Serien aktuell und verwalte geplante Download-Jobs an einem Ort.",
      "Watch host stability, recent failures, and current queue pressure without digging through individual jobs.":
        "Beobachte Host-Stabilität, letzte Fehler und die aktuelle Warteschlangenlast, ohne einzelne Jobs zu prüfen.",
      "Run upkeep tasks, inspect recent download sessions, and test providers without touching the queue directly.":
        "Führe Wartungsaufgaben aus, prüfe letzte Download-Sitzungen und teste Provider, ohne direkt in die Warteschlange einzugreifen.",
      "Inspect worker state, cache warmup, storage headroom, and database pressure from one place.":
        "Prüfe Worker-Zustand, Cache-Warmup, verfügbaren Speicher und Datenbanklast an einem Ort.",
      "See what finished, what failed, and what needs attention without digging through the queue modal.":
        "Sieh, was abgeschlossen wurde, was fehlgeschlagen ist und was Aufmerksamkeit braucht, ohne die Warteschlange öffnen zu müssen.",
      "Keep an eye on newly released episodes and mark your latest findings as seen.":
        "Behalte neu veröffentlichte Folgen im Blick und markiere deine neuesten Funde als gesehen.",
      "Review account actions, queue changes, favorites, and sync activity per user.":
        "Prüfe Kontoaktionen, Warteschlangenänderungen, Favoriten und Sync-Aktivitäten pro Nutzer.",
      "Desktop notifications work while the web UI is open in your browser. Because the service worker was intentionally removed, this is not a background push system for fully closed tabs.":
        "Desktop-Benachrichtigungen funktionieren, solange die Weboberfläche in deinem Browser geöffnet ist. Da der Service Worker absichtlich entfernt wurde, ist das kein Hintergrund-Push-System für vollständig geschlossene Tabs.",
      "Turn desktop notifications on or off for this account. Category toggles below decide which areas are allowed to raise a browser notification.":
        "Aktiviere oder deaktiviere Desktop-Benachrichtigungen für dieses Konto. Die Schalter unten bestimmen, welche Bereiche Browser-Benachrichtigungen auslösen dürfen.",
      "Checking GitHub for updates...":
        "GitHub wird auf Updates geprüft...",
      "Starting the update task...": "Update-Aufgabe wird gestartet...",
      "Restarting downloader. Reload this page in a few seconds.":
        "Downloader wird neu gestartet. Lade diese Seite in ein paar Sekunden neu.",
      "No update data available.": "Keine Update-Daten verfügbar.",
      "No update task is running.": "Keine Update-Aufgabe läuft.",
      "Restart required to load the new code.":
        "Neustart erforderlich, um den neuen Code zu laden.",
    },
  };

  const REGEX = {
    de: [
      [/^(\d+) selected$/, (m, count) => `${count} ausgewählt`],
      [/^(\d+) error\(s\)$/, (m, count) => `${count} Fehler`],
      [/^(\d+)h (\d+)m remaining$/, (m, h, min) => `noch ${h}h ${min}m`],
      [/^(\d+)m remaining$/, (m, min) => `noch ${min}m`],
      [/^(\d+)s remaining$/, (m, sec) => `noch ${sec}s`],
      [/^(\d+)m ago$/, (m, min) => `vor ${min} Min.`],
      [/^(\d+)h ago$/, (m, h) => `vor ${h} Std.`],
      [/^(\d+)\/(\d+) episodes selected$/, (m, a, b) => `${a}/${b} Folgen ausgewählt`],
      [/^(\d+)\/(\d+) episodes completed$/, (m, a, b) => `${a}/${b} Folgen abgeschlossen`],
      [/^(\d+)\/(\d+) episodes$/, (m, a, b) => `${a}/${b} Folgen`],
      [/^(\d+) total$/, (m, count) => `${count} insgesamt`],
      [/^Source: (.+)$/, (m, value) => `Quelle: ${value}`],
      [/^Last checked: (.+)$/, (m, value) => `Zuletzt geprüft: ${value}`],
    ],
  };

  const ATTRIBUTE_NAMES = ["placeholder", "title", "aria-label"];

  function normalizeWhitespace(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function splitWhitespace(value) {
    const raw = String(value || "");
    const match = raw.match(/^(\s*)([\s\S]*?)(\s*)$/);
    return {
      leading: match ? match[1] : "",
      core: match ? match[2] : raw,
      trailing: match ? match[3] : "",
    };
  }

  function translateCoreText(value, locale) {
    if (!value || locale === "en") return value;
    const normalized = normalizeWhitespace(value);
    if (!normalized) return value;
    if (EXACT[locale] && EXACT[locale][normalized]) return EXACT[locale][normalized];
    if (PHRASES[locale] && PHRASES[locale][normalized]) return PHRASES[locale][normalized];
    for (const [pattern, replacer] of REGEX[locale] || []) {
      if (pattern.test(normalized)) return normalized.replace(pattern, replacer);
    }
    let nextValue = normalized;
    for (const [source, translated] of Object.entries(PHRASES[locale] || {})) {
      if (source !== nextValue && nextValue.includes(source)) {
        nextValue = nextValue.split(source).join(translated);
      }
    }
    return nextValue;
  }

  function translateText(value, locale = currentLocale) {
    if (locale === "en") return value;
    const parts = splitWhitespace(value);
    return parts.leading + translateCoreText(parts.core, locale) + parts.trailing;
  }

  function shouldSkipTextNode(node) {
    const parent = node.parentElement;
    if (!parent) return true;
    return !!parent.closest(
      "script, style, code, pre, textarea, input[type='text'], input[type='password'], input[type='number'], input[type='email'], input[type='url']",
    );
  }

  function translateTextNode(node) {
    if (!node || shouldSkipTextNode(node)) return;
    const original = originalTextNodes.has(node)
      ? originalTextNodes.get(node)
      : node.nodeValue;
    if (!originalTextNodes.has(node)) originalTextNodes.set(node, original);
    const nextValue = currentLocale === "en" ? original : translateText(original, currentLocale);
    if (nextValue !== node.nodeValue) node.nodeValue = nextValue;
  }

  function originalAttrKey(attr) {
    return "i18nOriginal" + attr.replace(/-([a-z])/g, (match, char) => char.toUpperCase());
  }

  function translateAttribute(el, attr) {
    if (!el.hasAttribute(attr)) return;
    const datasetKey = originalAttrKey(attr);
    const original = Object.prototype.hasOwnProperty.call(el.dataset, datasetKey)
      ? el.dataset[datasetKey]
      : el.getAttribute(attr);
    if (!Object.prototype.hasOwnProperty.call(el.dataset, datasetKey)) {
      el.dataset[datasetKey] = original;
    }
    const nextValue = currentLocale === "en" ? original : translateText(original, currentLocale);
    if (nextValue !== el.getAttribute(attr)) el.setAttribute(attr, nextValue);
  }

  function translateButtonLikeValue(el) {
    if (!el || !("value" in el) || !/^(button|submit|reset)$/i.test(el.type || "")) return;
    const original = el.dataset.i18nOriginalValue || el.value;
    el.dataset.i18nOriginalValue = original;
    const nextValue = currentLocale === "en" ? original : translateText(original, currentLocale);
    if (nextValue !== el.value) el.value = nextValue;
  }

  function applyTranslations(root = document.body) {
    if (!root) return;
    document.title = currentLocale === "en" ? originalTitle : translateText(originalTitle, currentLocale);
    const textWalker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    let textNode = textWalker.nextNode();
    while (textNode) {
      translateTextNode(textNode);
      textNode = textWalker.nextNode();
    }
    const elementRoot = root.nodeType === Node.ELEMENT_NODE ? root : root.parentElement;
    if (!elementRoot) return;
    [elementRoot, ...elementRoot.querySelectorAll("*")].forEach((el) => {
      ATTRIBUTE_NAMES.forEach((attr) => translateAttribute(el, attr));
      translateButtonLikeValue(el);
    });
    document.documentElement.setAttribute("lang", currentLocale === "de" ? "de" : originalLang);
    body.dataset.uiLocale = currentLocale;
    if (typeof window.refreshCustomSelects === "function") {
      window.refreshCustomSelects(document);
    }
  }

  function setLocale(locale) {
    currentLocale = locale === "de" ? "de" : "en";
    if (window.ANIWORLD_BOOT_SETTINGS && window.ANIWORLD_BOOT_SETTINGS.ui) {
      window.ANIWORLD_BOOT_SETTINGS.ui.locale = currentLocale;
    }
    applyTranslations(document.body);
    document.dispatchEvent(
      new CustomEvent("aniworld:locale-change", {
        detail: { locale: currentLocale },
      }),
    );
  }

  const observer = new MutationObserver((mutations) => {
    if (currentLocale === "en") return;
    for (const mutation of mutations) {
      if (mutation.type === "characterData") {
        translateTextNode(mutation.target);
        continue;
      }
      if (mutation.type === "attributes") {
        applyTranslations(mutation.target);
        continue;
      }
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.TEXT_NODE) {
          translateTextNode(node);
        } else if (node.nodeType === Node.ELEMENT_NODE) {
          applyTranslations(node);
        }
      });
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
    attributes: true,
    attributeFilter: ATTRIBUTE_NAMES,
  });

  window.AniworldI18n = {
    getLocale() {
      return currentLocale;
    },
    setLocale,
    translateText,
    apply: applyTranslations,
  };

  applyTranslations(document.body);
})();
