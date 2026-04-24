// Download path settings
const downloadPathInput = document.getElementById("downloadPath");
const langSeparationCb = document.getElementById("langSeparation");
const disableEnglishSubCb = document.getElementById("disableEnglishSub");
const experimentalFilmpalastCb = document.getElementById(
  "experimentalFilmpalast",
);
const experimentalSelfHealCb = document.getElementById("experimentalSelfHeal");
const safeModeCb = document.getElementById("safeMode");
const autoOpenCaptchaTabCb = document.getElementById("autoOpenCaptchaTab");
const uiPresetSelect = document.getElementById("uiPreset");
const uiLocaleSelect = document.getElementById("uiLocale");
const uiModeSelect = document.getElementById("uiMode");
const uiScaleSelect = document.getElementById("uiScale");
const uiThemeSelect = document.getElementById("uiTheme");
const uiRadiusSelect = document.getElementById("uiRadius");
const uiMotionSelect = document.getElementById("uiMotion");
const uiWidthSelect = document.getElementById("uiWidth");
const uiModalWidthSelect = document.getElementById("uiModalWidth");
const uiNavSizeSelect = document.getElementById("uiNavSize");
const uiTableDensitySelect = document.getElementById("uiTableDensity");
const uiBackgroundSelect = document.getElementById("uiBackground");
const uiSettingsImportFileInput = document.getElementById("uiSettingsImportFile");
const bandwidthLimitInput = document.getElementById("bandwidthLimit");
const downloadBackendSelect = document.getElementById("downloadBackend");
const downloadSpeedProfileSelect = document.getElementById(
  "downloadSpeedProfile",
);
const downloadEngineRulesInput = document.getElementById("downloadEngineRules");
const autoProviderSwitchCb = document.getElementById("autoProviderSwitch");
const rateLimitGuardCb = document.getElementById("rateLimitGuard");
const preflightCheckCb = document.getElementById("preflightCheck");
const mp4FallbackRemuxCb = document.getElementById("mp4FallbackRemux");
const providerFallbackOrderInput = document.getElementById(
  "providerFallbackOrder",
);
const smartRetryProfileSelect = document.getElementById("smartRetryProfile");
const diskWarnGbInput = document.getElementById("diskWarnGb");
const diskWarnPercentInput = document.getElementById("diskWarnPercent");
const libraryAutoRepairCb = document.getElementById("libraryAutoRepair");
const backupImportFileInput = document.getElementById("backupImportFile");
const serverBindHostValue = document.getElementById("serverBindHost");
const serverPortValue = document.getElementById("serverPort");
const serverScopeValue = document.getElementById("serverScope");
const serverVpnModeValue = document.getElementById("serverVpnMode");
const serverVpnProviderValue = document.getElementById("serverVpnProvider");
const serverPublicIpValue = document.getElementById("serverPublicIp");
const serverIpsWrap = document.getElementById("serverIps");
const serverAccessUrlsWrap = document.getElementById("serverAccessUrls");
const serverVpnIpsWrap = document.getElementById("serverVpnIps");
const serverVpnClientsWrap = document.getElementById("serverVpnClients");
const serverVpnInterfaces = document.getElementById("serverVpnInterfaces");
const diskGuardList = document.getElementById("diskGuardList");
const dnsModeSelect = document.getElementById("dnsMode");
const dnsRetestBtn = document.getElementById("dnsRetestBtn");
const dnsStatusValue = document.getElementById("dnsStatusValue");
const dnsServersWrap = document.getElementById("dnsServers");
const dnsReachabilityList = document.getElementById("dnsReachabilityList");
const externalNotificationsEnabledCb = document.getElementById(
  "externalNotificationsEnabled",
);
const externalNotificationTypeSelect = document.getElementById(
  "externalNotificationType",
);
const externalNotificationUrlInput = document.getElementById(
  "externalNotificationUrl",
);
const externalNotifyQueueCb = document.getElementById("externalNotifyQueue");
const externalNotifyAutosyncCb = document.getElementById(
  "externalNotifyAutosync",
);
const externalNotifyLibraryCb = document.getElementById("externalNotifyLibrary");
const externalNotifySystemCb = document.getElementById("externalNotifySystem");
const browserNotificationsEnabledCb = document.getElementById(
  "browserNotificationsEnabled",
);
const browserNotifyBrowseCb = document.getElementById("browserNotifyBrowse");
const browserNotifyQueueCb = document.getElementById("browserNotifyQueue");
const browserNotifyAutosyncCb = document.getElementById(
  "browserNotifyAutosync",
);
const browserNotifyLibraryCb = document.getElementById("browserNotifyLibrary");
const browserNotifySettingsCb = document.getElementById(
  "browserNotifySettings",
);
const browserNotifySystemCb = document.getElementById("browserNotifySystem");
const browserNotificationStatus = document.getElementById(
  "browserNotificationStatus",
);
const browserNotificationPermissionBtn = document.getElementById(
  "browserNotificationPermissionBtn",
);
const updateStatusValue = document.getElementById("updateStatusValue");
const updateBranchValue = document.getElementById("updateBranchValue");
const updateLocalCommitValue = document.getElementById("updateLocalCommitValue");
const updateRemoteCommitValue = document.getElementById(
  "updateRemoteCommitValue",
);
const updateInstallModeValue = document.getElementById("updateInstallModeValue");
const updateStatusNote = document.getElementById("updateStatusNote");
const updateCheckBtn = document.getElementById("updateCheckBtn");
const restartAppBtn = document.getElementById("restartAppBtn");
const updateApplyBtn = document.getElementById("updateApplyBtn");
const autoUpdateEnabledCb = document.getElementById("autoUpdateEnabled");
const autoUpdateHint = document.getElementById("autoUpdateHint");
const updateCommitPreview = document.getElementById("updateCommitPreview");
const updateCommitHistoryDetails = document.getElementById(
  "updateCommitHistoryDetails",
);
const updateCommitHistoryBody = document.getElementById(
  "updateCommitHistoryBody",
);
const updateCommitPagination = document.getElementById("updateCommitPagination");
const updateCommitPrevBtn = document.getElementById("updateCommitPrevBtn");
const updateCommitNextBtn = document.getElementById("updateCommitNextBtn");
const updateCommitPageLabel = document.getElementById("updateCommitPageLabel");
const settingsUpdateOverlay = document.getElementById("settingsUpdateOverlay");
const settingsUpdateOverlayMessage = document.getElementById(
  "settingsUpdateOverlayMessage",
);
const settingsUpdateOverlayPhase = document.getElementById(
  "settingsUpdateOverlayPhase",
);
const settingsUpdateOverlayCommand = document.getElementById(
  "settingsUpdateOverlayCommand",
);
const settingsUpdateOverlaySpinner = document.getElementById(
  "settingsUpdateOverlaySpinner",
);
const settingsUpdateOverlayClose = document.getElementById(
  "settingsUpdateOverlayClose",
);
const settingsUpdateOverlayRestart = document.getElementById(
  "settingsUpdateOverlayRestart",
);
const settingsRestartBanner = document.getElementById("settingsRestartBanner");
const settingsRestartBannerBtn = document.getElementById(
  "settingsRestartBannerBtn",
);
const externalNotificationTestBtn = document.getElementById(
  "externalNotificationTestBtn",
);
const settingsSaveBar = document.getElementById("settingsSaveBar");
const settingsSaveAllBtn = document.getElementById("settingsSaveAllBtn");
const settingsDiscardBtn = document.getElementById("settingsDiscardBtn");
const searchDefaultSortSelect = document.getElementById("searchDefaultSort");
const searchDefaultGenresInput = document.getElementById(
  "searchDefaultGenres",
);
const searchDefaultYearFromInput = document.getElementById(
  "searchDefaultYearFrom",
);
const searchDefaultYearToInput = document.getElementById("searchDefaultYearTo");
const searchDefaultFavoritesOnlyCb = document.getElementById(
  "searchDefaultFavoritesOnly",
);
const searchDefaultDownloadedOnlyCb = document.getElementById(
  "searchDefaultDownloadedOnly",
);
const syncScheduleSelect = document.getElementById("syncSchedule");
const syncLanguageSelect = document.getElementById("syncLanguage");
const syncProviderSelect = document.getElementById("syncProvider");
let settingsRequest = null;
let customPathsRequest = null;
let updateStatusRequest = null;
let updatePollTimer = null;
let updateOverlayDismissed = false;
let restartInFlight = false;
let updateCheckInFlight = false;
let restartReloadTimer = null;
let updateCommitPage = 1;
let updateCommitPages = 0;
let updateCommitRequest = null;
let settingsBaselineState = null;
let settingsDirty = false;
let settingsApplyingState = false;
const settingsDraftMode = true;
const UPDATE_POLL_IDLE_MS = 300000;
const UPDATE_POLL_ACTIVE_MS = 2500;
const RESTART_RELOAD_INTERVAL_MS = 5000;
const SYNC_LANGUAGE_OPTIONS = ["German Dub", "English Sub", "German Sub"];
const UI_PRESETS = {
  control: {
    ui_mode: "compact",
    ui_theme: "ocean",
    ui_radius: "structured",
    ui_motion: "fast",
    ui_width: "wide",
    ui_modal_width: "compact",
    ui_nav_size: "compact",
    ui_table_density: "compact",
    ui_background: "grid",
  },
  cinematic: {
    ui_mode: "airy",
    ui_theme: "sunset",
    ui_radius: "round",
    ui_motion: "slow",
    ui_width: "wide",
    ui_modal_width: "wide",
    ui_nav_size: "large",
    ui_table_density: "relaxed",
    ui_background: "cinematic",
  },
  frosted: {
    ui_mode: "cozy",
    ui_theme: "arctic",
    ui_radius: "soft",
    ui_motion: "normal",
    ui_width: "standard",
    ui_modal_width: "standard",
    ui_nav_size: "standard",
    ui_table_density: "standard",
    ui_background: "frost",
  },
  neon: {
    ui_mode: "tight",
    ui_theme: "electric",
    ui_radius: "soft",
    ui_motion: "fast",
    ui_width: "wide",
    ui_modal_width: "standard",
    ui_nav_size: "compact",
    ui_table_density: "compact",
    ui_background: "pulse",
  },
};
const UI_SETTINGS_EXPORT_KEYS = [
  "ui_preset",
  "ui_locale",
  "ui_mode",
  "ui_scale",
  "ui_theme",
  "ui_radius",
  "ui_motion",
  "ui_width",
  "ui_modal_width",
  "ui_nav_size",
  "ui_table_density",
  "ui_background",
];

async function updateSettings(body) {
  const resp = await fetch("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await resp.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return data;
}

function refreshSettingsSelects() {
  if (!window.refreshCustomSelect) return;
  if (syncScheduleSelect) window.refreshCustomSelect(syncScheduleSelect);
  if (syncLanguageSelect) window.refreshCustomSelect(syncLanguageSelect);
  if (syncProviderSelect) window.refreshCustomSelect(syncProviderSelect);
  if (uiPresetSelect) window.refreshCustomSelect(uiPresetSelect);
  if (uiLocaleSelect) window.refreshCustomSelect(uiLocaleSelect);
  if (uiModeSelect) window.refreshCustomSelect(uiModeSelect);
  if (uiScaleSelect) window.refreshCustomSelect(uiScaleSelect);
  if (uiThemeSelect) window.refreshCustomSelect(uiThemeSelect);
  if (uiRadiusSelect) window.refreshCustomSelect(uiRadiusSelect);
  if (uiMotionSelect) window.refreshCustomSelect(uiMotionSelect);
  if (uiWidthSelect) window.refreshCustomSelect(uiWidthSelect);
  if (uiModalWidthSelect) window.refreshCustomSelect(uiModalWidthSelect);
  if (uiNavSizeSelect) window.refreshCustomSelect(uiNavSizeSelect);
  if (uiTableDensitySelect) window.refreshCustomSelect(uiTableDensitySelect);
  if (uiBackgroundSelect) window.refreshCustomSelect(uiBackgroundSelect);
  if (smartRetryProfileSelect) window.refreshCustomSelect(smartRetryProfileSelect);
  if (downloadBackendSelect) window.refreshCustomSelect(downloadBackendSelect);
  if (dnsModeSelect) window.refreshCustomSelect(dnsModeSelect);
  if (downloadSpeedProfileSelect) {
    window.refreshCustomSelect(downloadSpeedProfileSelect);
  }
  if (searchDefaultSortSelect)
    window.refreshCustomSelect(searchDefaultSortSelect);
}

function renderSettingsChipList(container, values) {
  if (!container) return;
  container.innerHTML = "";
  const entries = Array.isArray(values) ? values.filter(Boolean) : [];
  if (!entries.length) {
    const chip = document.createElement("span");
    chip.className = "settings-chip";
    chip.textContent = "Unavailable";
    container.appendChild(chip);
    return;
  }
  entries.forEach((value) => {
    const chip = document.createElement("span");
    chip.className = "settings-chip";
    chip.textContent = value;
    container.appendChild(chip);
  });
}

function escapeSettingsHtml(value) {
  const div = document.createElement("div");
  div.textContent = value == null ? "" : String(value);
  return div.innerHTML;
}

function buildManualUiPayload(payload) {
  const nextPayload = Object.assign({}, payload);
  if (uiPresetSelect && uiPresetSelect.value !== "custom") {
    uiPresetSelect.value = "custom";
    nextPayload.ui_preset = "custom";
  }
  refreshSettingsSelects();
  return nextPayload;
}

function applyUiPresetValues(values = {}) {
  if (uiModeSelect && values.ui_mode) uiModeSelect.value = values.ui_mode;
  if (uiThemeSelect && values.ui_theme) uiThemeSelect.value = values.ui_theme;
  if (uiRadiusSelect && values.ui_radius) uiRadiusSelect.value = values.ui_radius;
  if (uiMotionSelect && values.ui_motion) uiMotionSelect.value = values.ui_motion;
  if (uiWidthSelect && values.ui_width) uiWidthSelect.value = values.ui_width;
  if (uiModalWidthSelect && values.ui_modal_width) {
    uiModalWidthSelect.value = values.ui_modal_width;
  }
  if (uiNavSizeSelect && values.ui_nav_size) {
    uiNavSizeSelect.value = values.ui_nav_size;
  }
  if (uiTableDensitySelect && values.ui_table_density) {
    uiTableDensitySelect.value = values.ui_table_density;
  }
  if (uiBackgroundSelect && values.ui_background) {
    uiBackgroundSelect.value = values.ui_background;
  }
  refreshSettingsSelects();
  if (typeof window.applyUiDensity === "function" && values.ui_mode) {
    window.applyUiDensity(values.ui_mode);
  }
  if (typeof window.applyUiTheme === "function" && values.ui_theme) {
    window.applyUiTheme(values.ui_theme);
  }
  if (typeof window.applyUiRadius === "function" && values.ui_radius) {
    window.applyUiRadius(values.ui_radius);
  }
  if (typeof window.applyUiMotion === "function" && values.ui_motion) {
    window.applyUiMotion(values.ui_motion);
  }
  if (typeof window.applyUiWidth === "function" && values.ui_width) {
    window.applyUiWidth(values.ui_width);
  }
  if (
    typeof window.applyUiModalWidth === "function" &&
    values.ui_modal_width
  ) {
    window.applyUiModalWidth(values.ui_modal_width);
  }
  if (typeof window.applyUiNavSize === "function" && values.ui_nav_size) {
    window.applyUiNavSize(values.ui_nav_size);
  }
  if (
    typeof window.applyUiTableDensity === "function" &&
    values.ui_table_density
  ) {
    window.applyUiTableDensity(values.ui_table_density);
  }
  if (typeof window.applyUiBackground === "function" && values.ui_background) {
    window.applyUiBackground(values.ui_background);
  }
}

function renderDiskGuard(data) {
  if (!diskGuardList) return;
  const items = Array.isArray(data?.paths) ? data.paths : [];
  if (!items.length) {
    diskGuardList.innerHTML =
      '<div class="settings-disk-card"><strong>Unavailable</strong><span>No storage information could be collected.</span></div>';
    return;
  }
  diskGuardList.innerHTML = items
    .map((item) => {
      const tone =
        item.status === "warning"
          ? "warning"
          : item.status === "unknown"
            ? "unknown"
            : "healthy";
      const detail = item.error
        ? item.error
        : `${Number(item.free_gb || 0).toFixed(2)} GB free · ${Number(
            item.free_percent || 0,
          ).toFixed(1)}% free`;
      return (
        '<div class="settings-disk-card settings-disk-card-' +
        tone +
        '">' +
        "<strong>" +
        escapeSettingsHtml(item.label) +
        "</strong>" +
        '<span class="settings-disk-path">' +
        escapeSettingsHtml(item.path) +
        "</span>" +
        '<span class="settings-disk-meta">' +
        escapeSettingsHtml(detail) +
        "</span>" +
        "</div>"
      );
    })
    .join("");
}

function renderVpnInterfaces(data) {
  if (!serverVpnInterfaces) return;
  const items = Array.isArray(data) ? data : [];
  if (!items.length) {
    serverVpnInterfaces.innerHTML =
      '<div class="settings-disk-card"><strong>No tunnel interface detected</strong><span>The downloader currently looks like it is using a direct network path.</span></div>';
    return;
  }
  serverVpnInterfaces.innerHTML = items
    .map(
      (item) => `
        <div class="settings-disk-card">
          <strong>${escapeSettingsHtml(item.name || "Unknown interface")}</strong>
          <span class="settings-disk-meta">${escapeSettingsHtml(
            item.ip || "No IP detected",
          )}</span>
        </div>`,
    )
    .join("");
}

function collectUiSettingsPayload() {
  return {
    ui_preset: uiPresetSelect?.value || "custom",
    ui_locale: uiLocaleSelect?.value || "en",
    ui_mode: uiModeSelect?.value || "cozy",
    ui_scale: uiScaleSelect?.value || "100",
    ui_theme: uiThemeSelect?.value || "ocean",
    ui_radius: uiRadiusSelect?.value || "soft",
    ui_motion: uiMotionSelect?.value || "normal",
    ui_width: uiWidthSelect?.value || "standard",
    ui_modal_width: uiModalWidthSelect?.value || "standard",
    ui_nav_size: uiNavSizeSelect?.value || "standard",
    ui_table_density: uiTableDensitySelect?.value || "standard",
    ui_background: uiBackgroundSelect?.value || "dynamic",
  };
}

function captureSettingsState() {
  return {
    download_path: downloadPathInput?.value?.trim() || "",
    lang_separation: !!langSeparationCb?.checked,
    disable_english_sub: !!disableEnglishSubCb?.checked,
    experimental_filmpalast: !!experimentalFilmpalastCb?.checked,
    experimental_self_heal: !!experimentalSelfHealCb?.checked,
    safe_mode: !!safeModeCb?.checked,
    auto_open_captcha_tab: !!autoOpenCaptchaTabCb?.checked,
    auto_update_enabled: !!autoUpdateEnabledCb?.checked,
    external_notifications_enabled: !!externalNotificationsEnabledCb?.checked,
    external_notification_type: externalNotificationTypeSelect?.value || "generic",
    external_notification_url:
      String(externalNotificationUrlInput?.value || "").trim(),
    external_notify_queue: !!externalNotifyQueueCb?.checked,
    external_notify_autosync: !!externalNotifyAutosyncCb?.checked,
    external_notify_library: !!externalNotifyLibraryCb?.checked,
    external_notify_system: !!externalNotifySystemCb?.checked,
    browser_notifications_enabled: !!browserNotificationsEnabledCb?.checked,
    browser_notify_browse: !!browserNotifyBrowseCb?.checked,
    browser_notify_queue: !!browserNotifyQueueCb?.checked,
    browser_notify_autosync: !!browserNotifyAutosyncCb?.checked,
    browser_notify_library: !!browserNotifyLibraryCb?.checked,
    browser_notify_settings: !!browserNotifySettingsCb?.checked,
    browser_notify_system: !!browserNotifySystemCb?.checked,
    ui_preset: uiPresetSelect?.value || "custom",
    ui_locale: uiLocaleSelect?.value || "en",
    ui_mode: uiModeSelect?.value || "cozy",
    ui_scale: uiScaleSelect?.value || "100",
    ui_theme: uiThemeSelect?.value || "ocean",
    ui_radius: uiRadiusSelect?.value || "soft",
    ui_motion: uiMotionSelect?.value || "normal",
    ui_width: uiWidthSelect?.value || "standard",
    ui_modal_width: uiModalWidthSelect?.value || "standard",
    ui_nav_size: uiNavSizeSelect?.value || "standard",
    ui_table_density: uiTableDensitySelect?.value || "standard",
    ui_background: uiBackgroundSelect?.value || "dynamic",
    search_default_sort: searchDefaultSortSelect?.value || "source",
    search_default_genres: searchDefaultGenresInput?.value || "",
    search_default_year_from: searchDefaultYearFromInput?.value || "",
    search_default_year_to: searchDefaultYearToInput?.value || "",
    search_default_favorites_only: !!searchDefaultFavoritesOnlyCb?.checked,
    search_default_downloaded_only: !!searchDefaultDownloadedOnlyCb?.checked,
    sync_schedule: syncScheduleSelect?.value || "0",
    sync_language: syncLanguageSelect?.value || "German Dub",
    sync_provider: syncProviderSelect?.value || "VOE",
    bandwidth_limit_kbps: bandwidthLimitInput?.value || "0",
    download_backend: downloadBackendSelect?.value || "auto",
    dns_mode: dnsModeSelect?.value || "google",
    download_speed_profile: downloadSpeedProfileSelect?.value || "balanced",
    download_engine_rules: downloadEngineRulesInput?.value || "",
    auto_provider_switch: !!autoProviderSwitchCb?.checked,
    rate_limit_guard: !!rateLimitGuardCb?.checked,
    preflight_check: !!preflightCheckCb?.checked,
    mp4_fallback_remux: !!mp4FallbackRemuxCb?.checked,
    provider_fallback_order: providerFallbackOrderInput?.value || "",
    smart_retry_profile: smartRetryProfileSelect?.value || "balanced",
    library_auto_repair: !!libraryAutoRepairCb?.checked,
    disk_warn_gb: diskWarnGbInput?.value || "8",
    disk_warn_percent: diskWarnPercentInput?.value || "12",
  };
}

function cloneSettingsState(state) {
  return JSON.parse(JSON.stringify(state || {}));
}

function statesEqual(left, right) {
  return JSON.stringify(left || {}) === JSON.stringify(right || {});
}

function setSettingsDirty(nextDirty) {
  settingsDirty = !!nextDirty;
  if (settingsSaveBar) settingsSaveBar.hidden = !settingsDirty;
  if (settingsSaveAllBtn) settingsSaveAllBtn.disabled = !settingsDirty;
  if (settingsDiscardBtn) settingsDiscardBtn.disabled = !settingsDirty;
}

function refreshSettingsDirtyState() {
  if (settingsApplyingState || !settingsDraftMode || !settingsBaselineState) {
    setSettingsDirty(false);
    return;
  }
  setSettingsDirty(!statesEqual(captureSettingsState(), settingsBaselineState));
}

function syncSettingsBaselineFromDom() {
  settingsBaselineState = cloneSettingsState(captureSettingsState());
  refreshSettingsDirtyState();
}

function mergeSettingsBaseline(patch) {
  settingsBaselineState = Object.assign(
    {},
    settingsBaselineState || {},
    patch || {},
  );
  refreshSettingsDirtyState();
}

function handleSettingsDraft(localApply) {
  if (!settingsDraftMode || settingsApplyingState) return false;
  if (typeof localApply === "function") localApply();
  refreshSettingsDirtyState();
  return true;
}

function attachSettingsDirtyListeners() {
  if (!settingsDraftMode) return;
  document
    .querySelectorAll(
      ".settings-container input, .settings-container select, .settings-container textarea",
    )
    .forEach((element) => {
      element.addEventListener("input", refreshSettingsDirtyState);
      element.addEventListener("change", refreshSettingsDirtyState);
    });

  window.addEventListener("beforeunload", (event) => {
    if (!settingsDirty) return;
    event.preventDefault();
    event.returnValue = "";
  });

  document.addEventListener("click", (event) => {
    if (!settingsDirty) return;
    const link = event.target.closest("a[href]");
    if (!link) return;
    if (link.closest(".settings-save-bar")) return;
    if (link.getAttribute("href")?.startsWith("#")) return;
    const keepEditing = !window.confirm(
      "You have unsaved settings. Press OK to discard them and continue, or Cancel to stay here and save them first.",
    );
    if (keepEditing) {
      event.preventDefault();
    } else {
      setSettingsDirty(false);
    }
  });
}

function renderDnsDiagnostics(data) {
  if (dnsStatusValue) {
    dnsStatusValue.textContent = data?.status || "DNS diagnostics unavailable";
  }
  renderSettingsChipList(
    dnsServersWrap,
    Array.isArray(data?.servers) && data.servers.length
      ? data.servers
      : [data?.mode === "system" ? "System resolver" : "Unavailable"],
  );
  if (!dnsReachabilityList) return;
  dnsReachabilityList.innerHTML = "";
  const entries = Array.isArray(data?.reachability) ? data.reachability : [];
  if (!entries.length) {
    dnsReachabilityList.innerHTML =
      '<div class="settings-disk-card settings-disk-card-unknown"><strong>No DNS diagnostics yet</strong></div>';
    return;
  }
  entries.forEach((entry) => {
    const ok = !!entry?.ok;
    const card = document.createElement("div");
    card.className = "settings-disk-card";
    if (!ok) card.classList.add("settings-dns-card-error");
    const finalHost = String(entry?.final_host || "").trim();
    const meta = [];
    if (entry?.message) meta.push(String(entry.message));
    if (finalHost) meta.push(`Resolved via ${finalHost}`);
    if (entry?.status_code) meta.push(`HTTP ${entry.status_code}`);
    card.innerHTML =
      `<strong>${escapeSettingsHtml(entry?.domain || "Unknown host")}</strong>` +
      `<span class="settings-disk-meta ${ok ? "settings-dns-ok" : "settings-dns-error"}">${escapeSettingsHtml(meta.join(" • "))}</span>`;
    dnsReachabilityList.appendChild(card);
  });
}

function triggerUiSettingsImport() {
  if (!uiSettingsImportFileInput) return;
  uiSettingsImportFileInput.click();
}

function exportUiSettings() {
  const payload = {
    exported_at: new Date().toISOString(),
    type: "aniworld-ui-settings",
    settings: collectUiSettingsPayload(),
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = "aniworld-ui-settings.json";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(href);
  showToast("UI settings exported");
}

async function importUiSettings() {
  const file = uiSettingsImportFileInput?.files?.[0];
  if (!file) return;
  try {
    const raw = await file.text();
    const parsed = JSON.parse(raw);
    const source = parsed?.settings && typeof parsed.settings === "object"
      ? parsed.settings
      : parsed;
    const payload = {};
    UI_SETTINGS_EXPORT_KEYS.forEach((key) => {
      if (Object.prototype.hasOwnProperty.call(source, key)) {
        payload[key] = source[key];
      }
    });
    if (!Object.keys(payload).length) {
      throw new Error("No UI settings found in this file");
    }
    await updateSettings(payload);
    await loadSettings();
    showToast("UI settings imported");
  } catch (e) {
    showToast("Failed to import UI settings: " + e.message);
  } finally {
    if (uiSettingsImportFileInput) uiSettingsImportFileInput.value = "";
  }
}

function formatUpdateTimestamp(value) {
  if (!value) return "";
  const date = new Date(Number(value) * 1000);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString();
}

function formatIdleSeconds(value) {
  const total = Math.max(0, Number(value || 0));
  if (!Number.isFinite(total) || total <= 0) return "0m";
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${Math.max(1, minutes)}m`;
}

function setUpdateOverlayVisible(visible) {
  if (!settingsUpdateOverlay) return;
  settingsUpdateOverlay.hidden = !visible;
}

function setUpdateSpinnerVisible(visible) {
  if (!settingsUpdateOverlaySpinner) return;
  settingsUpdateOverlaySpinner.hidden = !visible;
}

function clearRestartReloadProbe() {
  if (restartReloadTimer) {
    clearTimeout(restartReloadTimer);
    restartReloadTimer = null;
  }
}

function scheduleRestartReloadProbe(delayMs = RESTART_RELOAD_INTERVAL_MS) {
  clearRestartReloadProbe();
  const probe = async () => {
    try {
      const resp = await fetch("/api/update/status", {
        method: "GET",
        cache: "no-store",
      });
      if (resp.ok) {
        window.location.reload();
        return;
      }
    } catch (e) {
      // Server still restarting. Keep probing.
    }
    restartReloadTimer = setTimeout(probe, RESTART_RELOAD_INTERVAL_MS);
  };
  restartReloadTimer = setTimeout(probe, delayMs);
}

function scheduleUpdatePolling(intervalMs = UPDATE_POLL_IDLE_MS) {
  if (updatePollTimer) clearInterval(updatePollTimer);
  updatePollTimer = setInterval(() => {
    loadUpdateStatus(false);
  }, intervalMs);
}

function renderUpdateStatus(data) {
  if (!updateStatusValue) return;

  const supported = !!data?.supported;
  const active = !!data?.active;
  const updateAvailable = !!data?.update_available;
  const canManage = !!data?.can_manage;
  const canApply = !!data?.can_apply;
  const actionAvailable = !!data?.action_available;
  const dirty = !!data?.dirty;
  const restartRequired = !!data?.restart_required;
  const supportsApply = !!data?.supports_apply;
  const supportsAutoUpdate = !!data?.supports_auto_update;
  const autoUpdateEnabled = !!data?.auto_update_enabled;
  const downloadsBusy = !!data?.downloads_busy;
  const installLabel = data?.install_label || "Unknown install";
  const actionLabel = data?.action_label || "Update Now";
  const actionHint = String(data?.action_hint || "");
  const manualCommand = String(data?.manual_command || "");
  const phase = String(data?.phase || "idle");
  const rawMessage = String(data?.message || data?.reason || "");
  const message =
    rawMessage === "No update data available." ? "" : rawMessage;

  let statusText = "Up to date";
  if (!supported) statusText = "Unavailable";
  else if (active) statusText = "Updating";
  else if (restartRequired) statusText = "Restart Required";
  else if (dirty) statusText = "Worktree Dirty";
  else if (updateAvailable) statusText = "Update Available";

  updateStatusValue.textContent = statusText;
  if (updateBranchValue) updateBranchValue.textContent = data?.branch || "-";
  if (updateLocalCommitValue) {
    updateLocalCommitValue.textContent = data?.local_short || "-";
    updateLocalCommitValue.title = data?.local_commit || "";
  }
  if (updateRemoteCommitValue) {
    updateRemoteCommitValue.textContent = data?.remote_short || "-";
    updateRemoteCommitValue.title = data?.remote_commit || "";
  }
  if (updateInstallModeValue) {
    updateInstallModeValue.textContent = installLabel;
  }

  if (updateStatusNote) {
    const details = [];
    if (message) details.push(message);
    if (actionHint && !active && !restartRequired) details.push(actionHint);
    if (data?.remote_url) details.push("Remote: " + data.remote_url);
    if (data?.last_checked_at) {
      details.push("Last checked: " + formatUpdateTimestamp(data.last_checked_at));
    } else if (data?.checked_at) {
      details.push("Last checked: " + formatUpdateTimestamp(data.checked_at));
    }
    if (data?.restart_required) {
      details.push("Restart required to load the new code.");
    }
    if (autoUpdateEnabled) {
      if (!supportsAutoUpdate) {
        details.push("Automatic updates are not available for this install mode.");
      } else if (downloadsBusy) {
        details.push("Automatic updates are waiting for the current download to finish.");
      } else {
        details.push(
          "Automatic updates wait for " +
            formatIdleSeconds(data?.auto_update_idle_seconds) +
            " of download idle time. Current idle: " +
            formatIdleSeconds(data?.download_idle_seconds),
        );
      }
    }
    updateStatusNote.textContent = details.filter(Boolean).join(" ");
  }

  if (autoUpdateEnabledCb) {
    autoUpdateEnabledCb.checked = autoUpdateEnabled;
    autoUpdateEnabledCb.disabled =
      !canManage || active || restartInFlight || !supportsAutoUpdate;
    autoUpdateEnabledCb.title = !canManage
      ? "Only admins can change automatic updates"
      : !supportsAutoUpdate
        ? "Automatic updates are not available for this installation mode"
        : "";
  }
  if (autoUpdateHint) {
    autoUpdateHint.textContent = supportsAutoUpdate
      ? "Automatic updates wait for " +
        formatIdleSeconds(data?.auto_update_idle_seconds) +
        " of download idle time and never start while a transfer is active."
      : "Automatic updates are disabled for installation modes that need a manual redeploy or reinstall.";
  }

  if (updateCheckBtn) {
    updateCheckBtn.disabled = active || restartInFlight || updateCheckInFlight;
    updateCheckBtn.textContent =
      active || updateCheckInFlight ? "Checking..." : "Check Now";
  }
  if (restartAppBtn) {
    restartAppBtn.disabled = active || restartInFlight || !canManage;
    restartAppBtn.textContent = restartInFlight ? "Restarting..." : "Restart";
    restartAppBtn.title = !canManage
      ? "Only admins can restart the downloader"
      : active
        ? "Wait for the running update to finish first"
        : "";
  }
  if (updateApplyBtn) {
    updateApplyBtn.disabled =
      active ||
      restartInFlight ||
      !supported ||
      !actionAvailable ||
      !updateAvailable ||
      dirty;
    updateApplyBtn.textContent = active ? "Updating..." : actionLabel;
    updateApplyBtn.title = !canManage
      ? "Only admins can manage updates"
      : dirty
        ? "Commit or stash local changes before updating"
        : !updateAvailable
          ? "This installation is already on the latest version"
          : !actionAvailable
            ? actionHint || "Updates for this install mode must be handled outside the web UI"
        : "";
  }

  if (settingsUpdateOverlayMessage) {
    settingsUpdateOverlayMessage.textContent = message;
  }
  if (settingsUpdateOverlayPhase) {
    settingsUpdateOverlayPhase.textContent =
      phase === "done"
      ? "Finished"
      : phase === "error"
          ? "Update failed"
          : phase === "manual"
            ? "Manual action required"
          : phase.charAt(0).toUpperCase() + phase.slice(1);
  }
  if (settingsUpdateOverlayCommand) {
    settingsUpdateOverlayCommand.hidden = !manualCommand || active;
    settingsUpdateOverlayCommand.textContent = manualCommand;
  }
  setUpdateSpinnerVisible(active || updateCheckInFlight);
  if (active) updateOverlayDismissed = false;
  if (settingsRestartBanner) {
    settingsRestartBanner.hidden = !restartRequired || restartInFlight;
  }
  const shouldShowOverlay =
    active ||
    (!updateOverlayDismissed &&
      supported &&
      (phase === "done" || phase === "error" || phase === "manual" || restartRequired));
  if (settingsUpdateOverlayClose) {
    settingsUpdateOverlayClose.hidden =
      active || !(phase === "done" || phase === "error" || phase === "manual" || restartRequired);
  }
  if (settingsUpdateOverlayRestart) {
    settingsUpdateOverlayRestart.hidden =
      active || restartInFlight || !restartRequired || !canManage;
  }
  setUpdateOverlayVisible(shouldShowOverlay);
}

async function loadUpdateStatus(force = false) {
  if (!updateStatusValue) return null;
  if (updateStatusRequest && !force) return updateStatusRequest;
  const request = (async () => {
    try {
      const resp = await fetch(force ? "/api/update/check" : "/api/update/status", {
        method: force ? "POST" : "GET",
        cache: "no-store",
      });
      const data = await resp.json();
      renderUpdateStatus(data || {});
      return data;
    } catch (e) {
      renderUpdateStatus({
        supported: false,
        reason: "Update status could not be loaded.",
      });
      return null;
    } finally {
      if (!force) updateStatusRequest = null;
    }
  })();
  if (!force) updateStatusRequest = request;
  return request;
}

function renderUpdateCommitPreview(data) {
  if (!updateCommitPreview) return;
  const items = Array.isArray(data?.items) ? data.items : [];
  if (!items.length) {
    updateCommitPreview.innerHTML =
      '<div class="settings-hint">No commit preview is available for this installation.</div>';
    return;
  }
  updateCommitPreview.innerHTML = items
    .map(
      (item) => `
        <article class="settings-commit-item settings-commit-item-preview">
          <div class="settings-commit-head">
            <strong>${escapeSettingsHtml(item.subject || "Untitled commit")}</strong>
            <span>${escapeSettingsHtml(item.short_hash || "-")}</span>
          </div>
          <div class="settings-commit-meta">
            <span>${escapeSettingsHtml(item.author || "Unknown")}</span>
            <span>${escapeSettingsHtml(item.date || "-")}</span>
          </div>
        </article>`,
    )
    .join("");
}

function renderUpdateCommitHistory(data) {
  if (!updateCommitHistoryBody) return;
  if (!data?.supported) {
    updateCommitHistoryBody.innerHTML =
      '<div class="settings-hint">' +
      escapeSettingsHtml(data?.reason || "Commit history is unavailable.") +
      "</div>";
    if (updateCommitPagination) updateCommitPagination.hidden = true;
    return;
  }

  const items = Array.isArray(data?.items) ? data.items : [];
  if (!items.length) {
    updateCommitHistoryBody.innerHTML =
      '<div class="settings-hint">No commits were returned for this page.</div>';
    if (updateCommitPagination) updateCommitPagination.hidden = true;
    return;
  }

  updateCommitHistoryBody.innerHTML = items
    .map(
      (item) => `
        <article class="settings-commit-item">
          <div class="settings-commit-head">
            <strong>${escapeSettingsHtml(item.subject || "Untitled commit")}</strong>
            <span>${escapeSettingsHtml(item.short_hash || "-")}</span>
          </div>
          <div class="settings-commit-meta">
            <span>${escapeSettingsHtml(item.author || "Unknown")}</span>
            <span>${escapeSettingsHtml(item.date || "-")}</span>
          </div>
        </article>`,
    )
    .join("");

  updateCommitPages = Number(data?.pages || 0);
  if (updateCommitPageLabel) {
    updateCommitPageLabel.textContent = updateCommitPages
      ? `Page ${Number(data?.page || 1)} of ${updateCommitPages}`
      : "Page 1";
  }
  if (updateCommitPrevBtn) {
    updateCommitPrevBtn.disabled = Number(data?.page || 1) <= 1;
  }
  if (updateCommitNextBtn) {
    updateCommitNextBtn.disabled =
      !updateCommitPages || Number(data?.page || 1) >= updateCommitPages;
  }
  if (updateCommitPagination) {
    updateCommitPagination.hidden = updateCommitPages <= 1;
  }
}

async function loadUpdateCommits(page = 1, perPage = 30, previewOnly = false) {
  if (updateCommitRequest) return updateCommitRequest;
  updateCommitRequest = (async () => {
    try {
      const resp = await fetch(
        `/api/update/commits?page=${Number(page || 1)}&per_page=${Number(perPage || 30)}`,
        { cache: "no-store" },
      );
      const data = await resp.json();
      if (previewOnly) renderUpdateCommitPreview(data);
      else renderUpdateCommitHistory(data);
      return data;
    } catch (e) {
      const fallback = {
        supported: false,
        reason: "Commit history could not be loaded.",
      };
      if (previewOnly) renderUpdateCommitPreview(fallback);
      else renderUpdateCommitHistory(fallback);
      return fallback;
    } finally {
      updateCommitRequest = null;
    }
  })();
  return updateCommitRequest;
}

async function testExternalNotification() {
  if (!externalNotificationTestBtn) return;
  externalNotificationTestBtn.disabled = true;
  const originalLabel = externalNotificationTestBtn.textContent;
  externalNotificationTestBtn.textContent = "Sending...";
  try {
    const resp = await fetch("/api/settings/test-webhook", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await resp.json();
    if (!resp.ok || data.error) {
      throw new Error(data.error || "Webhook test failed");
    }
    showToast("Test notification sent");
  } catch (e) {
    showToast("Webhook test failed: " + e.message);
  } finally {
    externalNotificationTestBtn.disabled = false;
    externalNotificationTestBtn.textContent = originalLabel;
  }
}

async function saveAllSettings() {
  const payload = captureSettingsState();
  try {
    await updateSettings(payload);
    syncSettingsBaselineFromDom();
    invalidateQueuePrefs();
    await refreshDnsDiagnostics(true);
    await loadUpdateStatus(false);
    showToast("All settings saved");
  } catch (e) {
    showToast("Failed to save settings: " + e.message);
  }
}

async function discardAllSettingsChanges() {
  if (!settingsDirty) return;
  settingsApplyingState = true;
  try {
    await loadSettings();
    syncSettingsBaselineFromDom();
    showToast("Settings changes discarded");
  } finally {
    settingsApplyingState = false;
  }
}

async function startWebUpdate() {
  if (!updateApplyBtn || updateApplyBtn.disabled) return;
  clearRestartReloadProbe();
  updateOverlayDismissed = false;
  setUpdateOverlayVisible(true);
  renderUpdateStatus({
    supported: true,
    active: true,
    phase: "checking",
    message: "Starting the update task...",
    can_apply: true,
  });
  try {
    const resp = await fetch("/api/update/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await resp.json();
    if (!resp.ok || data.error) {
      renderUpdateStatus(
        Object.assign({}, data, {
          supported: true,
          active: false,
          phase: "error",
          message: data.error || "Update could not be started.",
          can_apply: true,
        }),
      );
      showToast(data.error || "Update could not be started");
      return;
    }
    if (data?.phase === "manual" && !data?.active) {
      renderUpdateStatus(data);
      showToast(data.message || "Manual redeploy required");
      scheduleUpdatePolling();
      return;
    }
    renderUpdateStatus(data);
    showToast("Update started");
    if (updatePollTimer) clearInterval(updatePollTimer);
    updatePollTimer = setInterval(async () => {
      const status = await loadUpdateStatus(false);
      if (!status?.active) {
        clearInterval(updatePollTimer);
        updatePollTimer = null;
        scheduleUpdatePolling();
      }
    }, UPDATE_POLL_ACTIVE_MS);
  } catch (e) {
    renderUpdateStatus({
      supported: true,
      active: false,
      phase: "error",
      message: "Update could not be started.",
      can_apply: true,
    });
    showToast("Update could not be started: " + e.message);
  }
}

async function restartDownloaderFromSettings() {
  if (!restartAppBtn || restartAppBtn.disabled) return;
  clearRestartReloadProbe();
  restartInFlight = true;
  updateOverlayDismissed = false;
  if (updateCheckBtn) updateCheckBtn.disabled = true;
  if (restartAppBtn) {
    restartAppBtn.disabled = true;
    restartAppBtn.textContent = "Restarting...";
  }
  if (updateApplyBtn) updateApplyBtn.disabled = true;
  if (settingsUpdateOverlayMessage) {
    settingsUpdateOverlayMessage.textContent =
      "Restarting downloader. Reload this page in a few seconds.";
  }
  if (settingsUpdateOverlayPhase) {
    settingsUpdateOverlayPhase.textContent = "Restarting";
  }
  if (settingsUpdateOverlayClose) {
    settingsUpdateOverlayClose.hidden = true;
  }
  if (settingsUpdateOverlayRestart) {
    settingsUpdateOverlayRestart.hidden = true;
  }
  setUpdateOverlayVisible(true);
  try {
    const resp = await fetch("/api/system/restart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await resp.json();
    if (!resp.ok || data.error) {
      restartInFlight = false;
      renderUpdateStatus({
        supported: true,
        active: false,
        phase: "error",
        message: data.error || "Restart could not be started.",
        can_apply: true,
      });
      showToast(data.error || "Restart could not be started");
      return;
    }
    if (settingsUpdateOverlayMessage) {
      settingsUpdateOverlayMessage.textContent =
        data.message || "Restarting downloader. Reload this page in a few seconds.";
    }
    if (settingsUpdateOverlayCommand) {
      settingsUpdateOverlayCommand.hidden = true;
      settingsUpdateOverlayCommand.textContent = "";
    }
    showToast("Restart started");
    scheduleRestartReloadProbe(
      Number(data?.reload_after_seconds || 5) * 1000,
    );
  } catch (e) {
    restartInFlight = false;
    renderUpdateStatus({
      supported: true,
      active: false,
      phase: "error",
      message: "Restart could not be started.",
      can_apply: true,
    });
    showToast("Restart could not be started: " + e.message);
  }
}

async function checkForUpdatesNow() {
  if (!updateCheckBtn || updateCheckBtn.disabled) return;
  updateCheckInFlight = true;
  renderUpdateStatus({
    supported: true,
    active: false,
    phase: "checking",
    message: "Checking GitHub for updates...",
    can_apply: true,
  });
  try {
    await loadUpdateStatus(true);
  } finally {
    updateCheckInFlight = false;
    await loadUpdateStatus(false);
  }
}

function updateExternalNotificationState() {
  const enabled = !!externalNotificationsEnabledCb?.checked;
  [
    externalNotificationTypeSelect,
    externalNotificationUrlInput,
    externalNotifyQueueCb,
    externalNotifyAutosyncCb,
    externalNotifyLibraryCb,
    externalNotifySystemCb,
  ].forEach((field) => {
    if (!field) return;
    field.disabled = !enabled;
  });
}

function browserNotificationsSupported() {
  return typeof window !== "undefined" && "Notification" in window;
}

function updateBrowserNotificationCategoryState() {
  const enabled = !!browserNotificationsEnabledCb?.checked;
  [
    browserNotifyBrowseCb,
    browserNotifyQueueCb,
    browserNotifyAutosyncCb,
    browserNotifyLibraryCb,
    browserNotifySettingsCb,
    browserNotifySystemCb,
  ].forEach((checkbox) => {
    if (!checkbox) return;
    checkbox.disabled = !enabled;
  });
}

function renderBrowserNotificationPermissionState() {
  if (!browserNotificationStatus || !browserNotificationPermissionBtn) return;

  if (!browserNotificationsSupported()) {
    browserNotificationStatus.textContent = "Unsupported";
    browserNotificationPermissionBtn.disabled = true;
    browserNotificationPermissionBtn.textContent = "Not Available";
    return;
  }

  const permission = Notification.permission;
  if (permission === "granted") {
    browserNotificationStatus.textContent = "Granted";
    browserNotificationPermissionBtn.disabled = true;
    browserNotificationPermissionBtn.textContent = "Enabled";
    return;
  }
  if (permission === "denied") {
    browserNotificationStatus.textContent = "Blocked";
    browserNotificationPermissionBtn.disabled = false;
    browserNotificationPermissionBtn.textContent = "Open Browser Settings";
    return;
  }

  browserNotificationStatus.textContent = "Ask in Browser";
  browserNotificationPermissionBtn.disabled = false;
  browserNotificationPermissionBtn.textContent = "Enable in Browser";
}

function applyBrowserNotificationPrefsClient(data) {
  if (browserNotificationsEnabledCb) {
    browserNotificationsEnabledCb.checked =
      data.browser_notifications_enabled === "1";
  }
  if (browserNotifyBrowseCb) {
    browserNotifyBrowseCb.checked = data.browser_notify_browse !== "0";
  }
  if (browserNotifyQueueCb) {
    browserNotifyQueueCb.checked = data.browser_notify_queue !== "0";
  }
  if (browserNotifyAutosyncCb) {
    browserNotifyAutosyncCb.checked = data.browser_notify_autosync !== "0";
  }
  if (browserNotifyLibraryCb) {
    browserNotifyLibraryCb.checked = data.browser_notify_library !== "0";
  }
  if (browserNotifySettingsCb) {
    browserNotifySettingsCb.checked = data.browser_notify_settings !== "0";
  }
  if (browserNotifySystemCb) {
    browserNotifySystemCb.checked = data.browser_notify_system !== "0";
  }
  updateBrowserNotificationCategoryState();
  renderBrowserNotificationPermissionState();
}

async function loadSettings() {
  if (settingsRequest) return settingsRequest;
  settingsRequest = (async () => {
    try {
      settingsApplyingState = true;
      const resp = await fetch("/api/settings");
      const data = await resp.json();
      downloadPathInput.value = data.download_path || "";
      if (langSeparationCb)
        langSeparationCb.checked = data.lang_separation === "1";
      if (disableEnglishSubCb)
        disableEnglishSubCb.checked = data.disable_english_sub === "1";
      if (experimentalFilmpalastCb)
        experimentalFilmpalastCb.checked = data.experimental_filmpalast === "1";
      if (experimentalSelfHealCb) {
        experimentalSelfHealCb.checked = data.experimental_self_heal === "1";
      }
      if (safeModeCb) {
        safeModeCb.checked = data.safe_mode === "1";
      }
      if (autoOpenCaptchaTabCb) {
        autoOpenCaptchaTabCb.checked = data.auto_open_captcha_tab === "1";
      }
      if (externalNotificationsEnabledCb) {
        externalNotificationsEnabledCb.checked =
          data.external_notifications_enabled === "1";
      }
      if (externalNotificationTypeSelect) {
        externalNotificationTypeSelect.value =
          data.external_notification_type || "generic";
      }
      if (externalNotificationUrlInput) {
        externalNotificationUrlInput.value = data.external_notification_url || "";
      }
      if (externalNotifyQueueCb) {
        externalNotifyQueueCb.checked = data.external_notify_queue !== "0";
      }
      if (externalNotifyAutosyncCb) {
        externalNotifyAutosyncCb.checked = data.external_notify_autosync !== "0";
      }
      if (externalNotifyLibraryCb) {
        externalNotifyLibraryCb.checked = data.external_notify_library !== "0";
      }
      if (externalNotifySystemCb) {
        externalNotifySystemCb.checked = data.external_notify_system !== "0";
      }
      if (autoUpdateEnabledCb) {
        autoUpdateEnabledCb.checked = data.auto_update_enabled === "1";
      }
      updateExternalNotificationState();
      if (uiPresetSelect) uiPresetSelect.value = data.ui_preset || "custom";
      if (uiLocaleSelect) uiLocaleSelect.value = data.ui_locale || "en";
      if (uiModeSelect) uiModeSelect.value = data.ui_mode || "cozy";
      if (uiScaleSelect) uiScaleSelect.value = data.ui_scale || "100";
      if (uiThemeSelect) uiThemeSelect.value = data.ui_theme || "ocean";
      if (uiRadiusSelect) uiRadiusSelect.value = data.ui_radius || "soft";
      if (uiMotionSelect) uiMotionSelect.value = data.ui_motion || "normal";
      if (uiWidthSelect) uiWidthSelect.value = data.ui_width || "standard";
      if (uiModalWidthSelect) {
        uiModalWidthSelect.value = data.ui_modal_width || "standard";
      }
      if (uiNavSizeSelect) uiNavSizeSelect.value = data.ui_nav_size || "standard";
      if (uiTableDensitySelect) {
        uiTableDensitySelect.value = data.ui_table_density || "standard";
      }
      if (uiBackgroundSelect) {
        uiBackgroundSelect.value = data.ui_background || "dynamic";
      }
      if (bandwidthLimitInput) {
        bandwidthLimitInput.value = data.bandwidth_limit_kbps || "0";
      }
      if (downloadBackendSelect) {
        downloadBackendSelect.value = data.download_backend || "auto";
      }
      if (dnsModeSelect) {
        dnsModeSelect.value = data.dns_mode || "google";
      }
      if (downloadSpeedProfileSelect) {
        downloadSpeedProfileSelect.value =
          data.download_speed_profile || "balanced";
      }
      if (downloadEngineRulesInput) {
        downloadEngineRulesInput.value = data.download_engine_rules || "";
      }
      if (autoProviderSwitchCb) {
        autoProviderSwitchCb.checked = data.auto_provider_switch !== "0";
      }
      if (rateLimitGuardCb) {
        rateLimitGuardCb.checked = data.rate_limit_guard !== "0";
      }
      if (preflightCheckCb) {
        preflightCheckCb.checked = data.preflight_check !== "0";
      }
      if (mp4FallbackRemuxCb) {
        mp4FallbackRemuxCb.checked = data.mp4_fallback_remux === "1";
      }
      if (providerFallbackOrderInput) {
        providerFallbackOrderInput.value = data.provider_fallback_order || "";
      }
      if (smartRetryProfileSelect) {
        smartRetryProfileSelect.value = data.smart_retry_profile || "balanced";
      }
      if (diskWarnGbInput) {
        diskWarnGbInput.value = data.disk_warn_gb || "8";
      }
      if (diskWarnPercentInput) {
        diskWarnPercentInput.value = data.disk_warn_percent || "12";
      }
      if (libraryAutoRepairCb) {
        libraryAutoRepairCb.checked = data.library_auto_repair === "1";
      }
      if (serverBindHostValue) {
        serverBindHostValue.textContent = data.server_bind_host || "-";
      }
      if (serverPortValue) {
        serverPortValue.textContent = String(data.server_port || "-");
      }
      if (serverScopeValue) {
        serverScopeValue.textContent = data.server_scope || "-";
      }
      if (serverVpnModeValue) {
        serverVpnModeValue.textContent = data.vpn?.mode || "Direct / local";
      }
      if (serverVpnProviderValue) {
        serverVpnProviderValue.textContent = data.vpn?.provider || "Direct";
      }
      if (serverPublicIpValue) {
        serverPublicIpValue.textContent = data.vpn?.public_ip || "Unavailable";
        serverPublicIpValue.title = data.vpn?.public_ip_source
          ? "Source: " + data.vpn.public_ip_source
          : "";
      }
      renderSettingsChipList(serverIpsWrap, data.server_ips || []);
      renderSettingsChipList(serverAccessUrlsWrap, data.server_access_urls || []);
      renderSettingsChipList(serverVpnIpsWrap, data.vpn?.ips || []);
      renderSettingsChipList(serverVpnClientsWrap, data.vpn?.clients || []);
      renderVpnInterfaces(data.vpn?.interfaces || []);
      renderDiskGuard(data.disk_guard || null);
      renderDnsDiagnostics(data.dns_diagnostics || null);
      applyBrowserNotificationPrefsClient(data);
      if (searchDefaultSortSelect) {
        searchDefaultSortSelect.value = data.search_default_sort || "source";
      }
      if (searchDefaultGenresInput) {
        searchDefaultGenresInput.value = data.search_default_genres || "";
      }
      if (searchDefaultYearFromInput) {
        searchDefaultYearFromInput.value = data.search_default_year_from || "";
      }
      if (searchDefaultYearToInput) {
        searchDefaultYearToInput.value = data.search_default_year_to || "";
      }
      if (searchDefaultFavoritesOnlyCb) {
        searchDefaultFavoritesOnlyCb.checked =
          data.search_default_favorites_only === "1";
      }
      if (searchDefaultDownloadedOnlyCb) {
        searchDefaultDownloadedOnlyCb.checked =
          data.search_default_downloaded_only === "1";
      }
      if (syncScheduleSelect && data.sync_schedule)
        syncScheduleSelect.value = data.sync_schedule;

      const isLangSep = data.lang_separation === "1";
      let currentSyncLang = data.sync_language;
      if (currentSyncLang === "All Languages" && !isLangSep) {
        currentSyncLang = "German Dub";
      }
      updateSyncLanguageDropdown(isLangSep, currentSyncLang);

      if (syncProviderSelect && data.sync_provider)
        syncProviderSelect.value = data.sync_provider;
      refreshSettingsSelects();
      syncSettingsBaselineFromDom();
    } catch (e) {
      showToast("Failed to load settings: " + e.message);
    } finally {
      settingsApplyingState = false;
      settingsRequest = null;
    }
  })();
  return settingsRequest;
}

async function saveBrowserNotificationToggles() {
  if (
    handleSettingsDraft(() => {
      updateBrowserNotificationCategoryState();
      if (typeof window.applyBrowserNotificationPrefs === "function") {
        window.applyBrowserNotificationPrefs(captureSettingsState());
      }
    })
  ) {
    return;
  }
  try {
    const payload = {
      browser_notifications_enabled:
        browserNotificationsEnabledCb?.checked || false,
      browser_notify_browse: browserNotifyBrowseCb?.checked || false,
      browser_notify_queue: browserNotifyQueueCb?.checked || false,
      browser_notify_autosync: browserNotifyAutosyncCb?.checked || false,
      browser_notify_library: browserNotifyLibraryCb?.checked || false,
      browser_notify_settings: browserNotifySettingsCb?.checked || false,
      browser_notify_system: browserNotifySystemCb?.checked || false,
    };
    await updateSettings(payload);
    updateBrowserNotificationCategoryState();
    if (typeof window.applyBrowserNotificationPrefs === "function") {
      window.applyBrowserNotificationPrefs(payload);
    }
    mergeSettingsBaseline(payload);
    showToast("Browser notification settings saved");
  } catch (e) {
    showToast("Failed to save browser notifications: " + e.message);
  }
}

async function requestBrowserNotificationPermission() {
  if (!browserNotificationsSupported()) {
    showToast("Browser notifications are not supported here");
    renderBrowserNotificationPermissionState();
    return;
  }
  if (Notification.permission === "denied") {
    showToast("Browser notifications are blocked in your browser settings");
    renderBrowserNotificationPermissionState();
    return;
  }
  try {
    const result = await Notification.requestPermission();
    renderBrowserNotificationPermissionState();
    if (result === "granted") {
      showToast("Browser notification permission granted");
    } else if (result === "denied") {
      showToast("Browser notification permission was blocked");
    } else {
      showToast("Browser notification permission was dismissed");
    }
  } catch (e) {
    showToast("Failed to request browser notification permission");
  }
}

async function saveLangSeparation() {
  if (
    handleSettingsDraft(() => {
      let currentSyncLang = syncLanguageSelect ? syncLanguageSelect.value : null;
      if (!langSeparationCb.checked && currentSyncLang === "All Languages") {
        currentSyncLang = "German Dub";
      }
      updateSyncLanguageDropdown(langSeparationCb.checked, currentSyncLang);
    })
  ) {
    return;
  }
  try {
    await updateSettings({
      download_path: downloadPathInput.value.trim(),
      lang_separation: langSeparationCb.checked,
    });
    showToast(
      "Language separation " +
        (langSeparationCb.checked ? "enabled" : "disabled"),
    );

    let currentSyncLang = syncLanguageSelect ? syncLanguageSelect.value : null;
    if (!langSeparationCb.checked && currentSyncLang === "All Languages") {
      currentSyncLang = "German Dub";
      updateSyncLanguageDropdown(false, currentSyncLang);
      saveSyncDefaults();
    } else {
      updateSyncLanguageDropdown(langSeparationCb.checked, currentSyncLang);
    }
    mergeSettingsBaseline({
      download_path: downloadPathInput.value.trim(),
      lang_separation: langSeparationCb.checked,
      sync_language: syncLanguageSelect?.value || "German Dub",
    });
  } catch (e) {
    showToast("Failed to save setting: " + e.message);
  }
}

function updateSyncLanguageDropdown(isLangSep, currentValue) {
  if (!syncLanguageSelect) return;
  syncLanguageSelect.innerHTML = "";
  if (isLangSep) {
    const opt = document.createElement("option");
    opt.value = "All Languages";
    opt.textContent = "All Languages";
    syncLanguageSelect.appendChild(opt);
  }
  SYNC_LANGUAGE_OPTIONS.forEach((l) => {
    const opt = document.createElement("option");
    opt.value = l;
    opt.textContent = l;
    syncLanguageSelect.appendChild(opt);
  });
  if (currentValue) syncLanguageSelect.value = currentValue;
  refreshSettingsSelects();
}

async function saveDisableEnglishSub() {
  if (handleSettingsDraft()) return;
  try {
    await updateSettings({
      disable_english_sub: disableEnglishSubCb.checked,
    });
    mergeSettingsBaseline({
      disable_english_sub: disableEnglishSubCb.checked,
    });
    showToast(
      "English Sub downloads " +
        (disableEnglishSubCb.checked ? "disabled" : "enabled"),
    );
  } catch (e) {
    showToast("Failed to save setting: " + e.message);
  }
}

async function saveExperimentalFilmpalast() {
  if (!experimentalFilmpalastCb) return;
  if (handleSettingsDraft()) return;
  try {
    await updateSettings({
      experimental_filmpalast: experimentalFilmpalastCb.checked,
    });
    mergeSettingsBaseline({
      experimental_filmpalast: experimentalFilmpalastCb.checked,
    });
    showToast(
      "FilmPalast " +
        (experimentalFilmpalastCb.checked ? "enabled" : "hidden"),
    );
  } catch (e) {
    showToast("Failed to save development setting: " + e.message);
  }
}

async function saveUiMode() {
  if (!uiModeSelect) return;
  if (
    handleSettingsDraft(() => {
      if (typeof window.applyUiDensity === "function") {
        window.applyUiDensity(uiModeSelect.value);
      }
    })
  ) {
    return;
  }
  try {
    await updateSettings(buildManualUiPayload({ ui_mode: uiModeSelect.value }));
    if (typeof window.applyUiDensity === "function") {
      window.applyUiDensity(uiModeSelect.value);
    }
    mergeSettingsBaseline(buildManualUiPayload({ ui_mode: uiModeSelect.value }));
    showToast("UI mode saved");
  } catch (e) {
    showToast("Failed to save UI mode: " + e.message);
  }
}

async function saveUiScale() {
  if (!uiScaleSelect) return;
  if (
    handleSettingsDraft(() => {
      if (typeof window.applyUiScale === "function") {
        window.applyUiScale(uiScaleSelect.value);
      }
    })
  ) {
    return;
  }
  try {
    await updateSettings(buildManualUiPayload({ ui_scale: uiScaleSelect.value }));
    if (typeof window.applyUiScale === "function") {
      window.applyUiScale(uiScaleSelect.value);
    }
    mergeSettingsBaseline(buildManualUiPayload({ ui_scale: uiScaleSelect.value }));
    showToast("UI scale saved");
  } catch (e) {
    showToast("Failed to save UI scale: " + e.message);
  }
}

async function saveExperimentalSelfHeal() {
  if (!experimentalSelfHealCb) return;
  if (handleSettingsDraft()) return;
  try {
    await updateSettings({
      experimental_self_heal: experimentalSelfHealCb.checked,
    });
    mergeSettingsBaseline({
      experimental_self_heal: experimentalSelfHealCb.checked,
    });
    showToast(
      "Experimental self-heal " +
        (experimentalSelfHealCb.checked ? "enabled" : "disabled"),
    );
  } catch (e) {
    showToast("Failed to save self-heal setting: " + e.message);
  }
}

async function saveUiLocale() {
  if (!uiLocaleSelect) return;
  if (
    handleSettingsDraft(() => {
      if (
        window.AniworldI18n &&
        typeof window.AniworldI18n.setLocale === "function"
      ) {
        window.AniworldI18n.setLocale(uiLocaleSelect.value);
      }
    })
  ) {
    return;
  }
  try {
    await updateSettings({ ui_locale: uiLocaleSelect.value });
    if (window.AniworldI18n && typeof window.AniworldI18n.setLocale === "function") {
      window.AniworldI18n.setLocale(uiLocaleSelect.value);
    }
    mergeSettingsBaseline({ ui_locale: uiLocaleSelect.value });
    showToast(
      uiLocaleSelect.value === "de"
        ? "Oberflächensprache gespeichert"
        : "UI language saved",
    );
  } catch (e) {
    showToast("Failed to save UI language: " + e.message);
  }
}

async function saveAutoUpdateEnabled() {
  if (!autoUpdateEnabledCb) return;
  if (handleSettingsDraft()) return;
  try {
    await updateSettings({
      auto_update_enabled: autoUpdateEnabledCb.checked,
    });
    await loadUpdateStatus(false);
    mergeSettingsBaseline({
      auto_update_enabled: autoUpdateEnabledCb.checked,
    });
    showToast(
      "Automatic updates " + (autoUpdateEnabledCb.checked ? "enabled" : "disabled"),
    );
  } catch (e) {
    showToast("Failed to save automatic updates: " + e.message);
  }
}

async function refreshDnsDiagnostics(force = false) {
  try {
    if (dnsRetestBtn) dnsRetestBtn.disabled = true;
    const suffix = force ? "?force=1" : "";
    const resp = await fetch("/api/settings/dns-diagnostics" + suffix, {
      cache: "no-store",
    });
    const data = await resp.json();
    renderDnsDiagnostics(data);
    return data;
  } catch (e) {
    renderDnsDiagnostics(null);
    showToast("Failed to refresh DNS diagnostics: " + e.message);
    return null;
  } finally {
    if (dnsRetestBtn) dnsRetestBtn.disabled = false;
  }
}

async function saveDnsSettings() {
  if (!dnsModeSelect) return;
  if (handleSettingsDraft()) return;
  try {
    await updateSettings({ dns_mode: dnsModeSelect.value });
    mergeSettingsBaseline({ dns_mode: dnsModeSelect.value });
    await refreshDnsDiagnostics(true);
    showToast("DNS mode saved");
  } catch (e) {
    showToast("Failed to save DNS mode: " + e.message);
  }
}

async function saveSafeMode() {
  if (!safeModeCb) return;
  if (handleSettingsDraft()) return;
  try {
    await updateSettings({
      safe_mode: safeModeCb.checked,
    });
    mergeSettingsBaseline({
      safe_mode: safeModeCb.checked,
    });
    showToast("Safe mode " + (safeModeCb.checked ? "enabled" : "disabled"));
  } catch (e) {
    showToast("Failed to save safe mode: " + e.message);
  }
}

async function saveAutoOpenCaptchaTab() {
  if (!autoOpenCaptchaTabCb) return;
  if (handleSettingsDraft()) return;
  try {
    await updateSettings({
      auto_open_captcha_tab: autoOpenCaptchaTabCb.checked,
    });
    mergeSettingsBaseline({
      auto_open_captcha_tab: autoOpenCaptchaTabCb.checked,
    });
    showToast(
      autoOpenCaptchaTabCb.checked
        ? "Automatic visible captcha tab opening enabled"
        : "Automatic captcha tab opening disabled; captcha stays hidden until opened manually",
    );
  } catch (e) {
    showToast("Failed to save captcha tab setting: " + e.message);
  }
}

async function saveExternalNotificationSettings() {
  updateExternalNotificationState();
  if (handleSettingsDraft()) return;
  try {
    await updateSettings({
      external_notifications_enabled:
        externalNotificationsEnabledCb?.checked || false,
      external_notification_type:
        externalNotificationTypeSelect?.value || "generic",
      external_notification_url:
        String(externalNotificationUrlInput?.value || "").trim(),
      external_notify_queue: externalNotifyQueueCb?.checked || false,
      external_notify_autosync: externalNotifyAutosyncCb?.checked || false,
      external_notify_library: externalNotifyLibraryCb?.checked || false,
      external_notify_system: externalNotifySystemCb?.checked || false,
    });
    mergeSettingsBaseline({
      external_notifications_enabled:
        externalNotificationsEnabledCb?.checked || false,
      external_notification_type:
        externalNotificationTypeSelect?.value || "generic",
      external_notification_url:
        String(externalNotificationUrlInput?.value || "").trim(),
      external_notify_queue: externalNotifyQueueCb?.checked || false,
      external_notify_autosync: externalNotifyAutosyncCb?.checked || false,
      external_notify_library: externalNotifyLibraryCb?.checked || false,
      external_notify_system: externalNotifySystemCb?.checked || false,
    });
    showToast("External notification settings saved");
  } catch (e) {
    showToast("Failed to save external notifications: " + e.message);
  }
}

async function saveUiTheme() {
  if (!uiThemeSelect) return;
  if (
    handleSettingsDraft(() => {
      if (typeof window.applyUiTheme === "function") {
        window.applyUiTheme(uiThemeSelect.value);
      }
    })
  ) {
    return;
  }
  try {
    await updateSettings(buildManualUiPayload({ ui_theme: uiThemeSelect.value }));
    if (typeof window.applyUiTheme === "function") {
      window.applyUiTheme(uiThemeSelect.value);
    }
    mergeSettingsBaseline(buildManualUiPayload({ ui_theme: uiThemeSelect.value }));
    showToast("Theme color saved");
  } catch (e) {
    showToast("Failed to save theme color: " + e.message);
  }
}

async function saveUiRadius() {
  if (!uiRadiusSelect) return;
  if (
    handleSettingsDraft(() => {
      if (typeof window.applyUiRadius === "function") {
        window.applyUiRadius(uiRadiusSelect.value);
      }
    })
  ) {
    return;
  }
  try {
    await updateSettings(buildManualUiPayload({ ui_radius: uiRadiusSelect.value }));
    if (typeof window.applyUiRadius === "function") {
      window.applyUiRadius(uiRadiusSelect.value);
    }
    mergeSettingsBaseline(buildManualUiPayload({ ui_radius: uiRadiusSelect.value }));
    showToast("Card radius saved");
  } catch (e) {
    showToast("Failed to save card radius: " + e.message);
  }
}

async function saveUiMotion() {
  if (!uiMotionSelect) return;
  if (
    handleSettingsDraft(() => {
      if (typeof window.applyUiMotion === "function") {
        window.applyUiMotion(uiMotionSelect.value);
      }
    })
  ) {
    return;
  }
  try {
    await updateSettings(buildManualUiPayload({ ui_motion: uiMotionSelect.value }));
    if (typeof window.applyUiMotion === "function") {
      window.applyUiMotion(uiMotionSelect.value);
    }
    mergeSettingsBaseline(buildManualUiPayload({ ui_motion: uiMotionSelect.value }));
    showToast("Animation speed saved");
  } catch (e) {
    showToast("Failed to save animation speed: " + e.message);
  }
}

async function saveUiWidth() {
  if (!uiWidthSelect) return;
  if (
    handleSettingsDraft(() => {
      if (typeof window.applyUiWidth === "function") {
        window.applyUiWidth(uiWidthSelect.value);
      }
    })
  ) {
    return;
  }
  try {
    await updateSettings(buildManualUiPayload({ ui_width: uiWidthSelect.value }));
    if (typeof window.applyUiWidth === "function") {
      window.applyUiWidth(uiWidthSelect.value);
    }
    mergeSettingsBaseline(buildManualUiPayload({ ui_width: uiWidthSelect.value }));
    showToast("Content width saved");
  } catch (e) {
    showToast("Failed to save content width: " + e.message);
  }
}

async function saveUiModalWidth() {
  if (!uiModalWidthSelect) return;
  if (
    handleSettingsDraft(() => {
      if (typeof window.applyUiModalWidth === "function") {
        window.applyUiModalWidth(uiModalWidthSelect.value);
      }
    })
  ) {
    return;
  }
  try {
    await updateSettings(
      buildManualUiPayload({ ui_modal_width: uiModalWidthSelect.value }),
    );
    if (typeof window.applyUiModalWidth === "function") {
      window.applyUiModalWidth(uiModalWidthSelect.value);
    }
    mergeSettingsBaseline(
      buildManualUiPayload({ ui_modal_width: uiModalWidthSelect.value }),
    );
    showToast("Modal width saved");
  } catch (e) {
    showToast("Failed to save modal width: " + e.message);
  }
}

async function saveUiNavSize() {
  if (!uiNavSizeSelect) return;
  if (
    handleSettingsDraft(() => {
      if (typeof window.applyUiNavSize === "function") {
        window.applyUiNavSize(uiNavSizeSelect.value);
      }
    })
  ) {
    return;
  }
  try {
    await updateSettings(
      buildManualUiPayload({ ui_nav_size: uiNavSizeSelect.value }),
    );
    if (typeof window.applyUiNavSize === "function") {
      window.applyUiNavSize(uiNavSizeSelect.value);
    }
    mergeSettingsBaseline(
      buildManualUiPayload({ ui_nav_size: uiNavSizeSelect.value }),
    );
    showToast("Navigation size saved");
  } catch (e) {
    showToast("Failed to save navigation size: " + e.message);
  }
}

async function saveUiTableDensity() {
  if (!uiTableDensitySelect) return;
  if (
    handleSettingsDraft(() => {
      if (typeof window.applyUiTableDensity === "function") {
        window.applyUiTableDensity(uiTableDensitySelect.value);
      }
    })
  ) {
    return;
  }
  try {
    await updateSettings(
      buildManualUiPayload({ ui_table_density: uiTableDensitySelect.value }),
    );
    if (typeof window.applyUiTableDensity === "function") {
      window.applyUiTableDensity(uiTableDensitySelect.value);
    }
    mergeSettingsBaseline(
      buildManualUiPayload({ ui_table_density: uiTableDensitySelect.value }),
    );
    showToast("Table density saved");
  } catch (e) {
    showToast("Failed to save table density: " + e.message);
  }
}

async function saveUiBackground() {
  if (!uiBackgroundSelect) return;
  if (
    handleSettingsDraft(() => {
      if (typeof window.applyUiBackground === "function") {
        window.applyUiBackground(uiBackgroundSelect.value);
      }
    })
  ) {
    return;
  }
  try {
    await updateSettings(
      buildManualUiPayload({ ui_background: uiBackgroundSelect.value }),
    );
    if (typeof window.applyUiBackground === "function") {
      window.applyUiBackground(uiBackgroundSelect.value);
    }
    mergeSettingsBaseline(
      buildManualUiPayload({ ui_background: uiBackgroundSelect.value }),
    );
    showToast("Background effects saved");
  } catch (e) {
    showToast("Failed to save background effects: " + e.message);
  }
}

async function applyUiPreset() {
  if (!uiPresetSelect) return;
  const preset = uiPresetSelect.value || "custom";
  if (
    handleSettingsDraft(() => {
      if (preset !== "custom") {
        const values = UI_PRESETS[preset];
        if (values) applyUiPresetValues(values);
      }
    })
  ) {
    return;
  }
  try {
    if (preset === "custom") {
      await updateSettings({ ui_preset: "custom" });
      mergeSettingsBaseline({ ui_preset: "custom" });
      showToast("Theme preset set to custom");
      return;
    }
    const values = UI_PRESETS[preset];
    if (!values) return;
    applyUiPresetValues(values);
    await updateSettings(Object.assign({ ui_preset: preset }, values));
    mergeSettingsBaseline(Object.assign({ ui_preset: preset }, values));
    showToast("Theme preset applied");
  } catch (e) {
    showToast("Failed to apply theme preset: " + e.message);
  }
}

async function saveDownloadAdvancedSettings() {
  if (handleSettingsDraft()) return;
  try {
    const payload = {
      bandwidth_limit_kbps: bandwidthLimitInput?.value || "0",
      download_backend: downloadBackendSelect?.value || "auto",
      download_speed_profile: downloadSpeedProfileSelect?.value || "balanced",
      download_engine_rules: downloadEngineRulesInput?.value || "",
      auto_provider_switch: autoProviderSwitchCb?.checked || false,
      rate_limit_guard: rateLimitGuardCb?.checked || false,
      preflight_check: preflightCheckCb?.checked || false,
      mp4_fallback_remux: mp4FallbackRemuxCb?.checked || false,
      provider_fallback_order: providerFallbackOrderInput?.value || "",
      smart_retry_profile: smartRetryProfileSelect?.value || "balanced",
    };
    await updateSettings(payload);
    mergeSettingsBaseline(payload);
    showToast("Download rules saved");
  } catch (e) {
    showToast("Failed to save download rules: " + e.message);
  }
}

async function saveDiskGuardSettings() {
  if (handleSettingsDraft()) return;
  try {
    const payload = {
      disk_warn_gb: diskWarnGbInput?.value || "8",
      disk_warn_percent: diskWarnPercentInput?.value || "12",
    };
    await updateSettings(payload);
    mergeSettingsBaseline(payload);
    await loadSettings();
    showToast("Disk guard thresholds saved");
  } catch (e) {
    showToast("Failed to save disk guard thresholds: " + e.message);
  }
}

async function saveLibraryAutoRepair() {
  if (handleSettingsDraft()) return;
  try {
    await updateSettings({
      library_auto_repair: libraryAutoRepairCb?.checked || false,
    });
    mergeSettingsBaseline({
      library_auto_repair: libraryAutoRepairCb?.checked || false,
    });
    showToast(
      "Library auto-repair " +
        (libraryAutoRepairCb?.checked ? "enabled" : "disabled"),
    );
  } catch (e) {
    showToast("Failed to save library auto-repair: " + e.message);
  }
}

function exportBackup() {
  window.location.href = "/api/backup/export";
}

async function importBackup() {
  const file = backupImportFileInput?.files?.[0];
  if (!file) {
    showToast("Choose a backup file first");
    return;
  }
  if (!confirm("Import this backup into the current downloader data?")) return;
  const formData = new FormData();
  formData.append("backup", file);
  try {
    const resp = await fetch("/api/backup/import", {
      method: "POST",
      body: formData,
    });
    const data = await resp.json();
    if (!resp.ok || data.error) {
      showToast(data.error || "Backup import failed");
      return;
    }
    if (backupImportFileInput) backupImportFileInput.value = "";
    await Promise.all([loadSettings(), loadCustomPaths()]);
    if (typeof loadUsers === "function" && userTableBody) {
      loadUsers();
    }
    if (window.LiveUpdates && typeof window.LiveUpdates.refresh === "function") {
      window.LiveUpdates.refresh(["settings", "library", "dashboard", "nav"]);
    }
    showToast("Backup imported");
  } catch (e) {
    showToast("Failed to import backup: " + e.message);
  }
}

async function saveSearchDefaults() {
  if (handleSettingsDraft()) return;
  try {
    const payload = {
      search_default_sort: searchDefaultSortSelect?.value || "source",
      search_default_genres: searchDefaultGenresInput?.value || "",
      search_default_year_from: searchDefaultYearFromInput?.value || "",
      search_default_year_to: searchDefaultYearToInput?.value || "",
      search_default_favorites_only:
        searchDefaultFavoritesOnlyCb?.checked || false,
      search_default_downloaded_only:
        searchDefaultDownloadedOnlyCb?.checked || false,
    };
    await updateSettings(payload);
    mergeSettingsBaseline(payload);
    showToast("Search defaults saved");
  } catch (e) {
    showToast("Failed to save search defaults: " + e.message);
  }
}

async function resetSearchDefaultsConfig() {
  if (searchDefaultSortSelect) searchDefaultSortSelect.value = "source";
  if (searchDefaultGenresInput) searchDefaultGenresInput.value = "";
  if (searchDefaultYearFromInput) searchDefaultYearFromInput.value = "";
  if (searchDefaultYearToInput) searchDefaultYearToInput.value = "";
  if (searchDefaultFavoritesOnlyCb) searchDefaultFavoritesOnlyCb.checked = false;
  if (searchDefaultDownloadedOnlyCb) {
    searchDefaultDownloadedOnlyCb.checked = false;
  }
  refreshSettingsSelects();
  updateSettingsDirtyState();
  showToast("Search defaults reset in draft");
}

async function saveDownloadPath() {
  if (handleSettingsDraft()) return;
  const download_path = downloadPathInput.value.trim();
  try {
    await updateSettings({ download_path });
    mergeSettingsBaseline({ download_path });
    showToast("Download path saved");
  } catch (e) {
    showToast("Failed to save settings: " + e.message);
  }
}

loadSettings();
loadUpdateStatus(false);
loadUpdateCommits(1, 3, true);
renderBrowserNotificationPermissionState();
attachSettingsDirtyListeners();
window.addEventListener("focus", () => {
  renderBrowserNotificationPermissionState();
  loadUpdateStatus(false);
});
scheduleUpdatePolling();

if (settingsSaveAllBtn) {
  settingsSaveAllBtn.addEventListener("click", saveAllSettings);
}
if (settingsDiscardBtn) {
  settingsDiscardBtn.addEventListener("click", discardAllSettingsChanges);
}
if (dnsRetestBtn) {
  dnsRetestBtn.addEventListener("click", () => refreshDnsDiagnostics(true));
}
if (updateCommitHistoryDetails) {
  updateCommitHistoryDetails.addEventListener("toggle", () => {
    if (updateCommitHistoryDetails.open) {
      updateCommitPage = 1;
      loadUpdateCommits(updateCommitPage, 30, false);
    }
  });
}
if (updateCommitPrevBtn) {
  updateCommitPrevBtn.addEventListener("click", () => {
    if (updateCommitPage <= 1) return;
    updateCommitPage -= 1;
    loadUpdateCommits(updateCommitPage, 30, false);
  });
}
if (updateCommitNextBtn) {
  updateCommitNextBtn.addEventListener("click", () => {
    if (!updateCommitPages || updateCommitPage >= updateCommitPages) return;
    updateCommitPage += 1;
    loadUpdateCommits(updateCommitPage, 30, false);
  });
}

async function saveSyncSchedule() {
  if (!syncScheduleSelect) return;
  if (handleSettingsDraft()) return;
  try {
    await updateSettings({ sync_schedule: syncScheduleSelect.value });
    mergeSettingsBaseline({ sync_schedule: syncScheduleSelect.value });
    showToast("Auto-Sync schedule saved");
  } catch (e) {
    showToast("Failed to save schedule: " + e.message);
  }
}

async function saveSyncDefaults() {
  const body = {};
  if (syncLanguageSelect) body.sync_language = syncLanguageSelect.value;
  if (syncProviderSelect) body.sync_provider = syncProviderSelect.value;
  if (handleSettingsDraft()) return;
  try {
    await updateSettings(body);
    mergeSettingsBaseline(body);
    showToast("Auto-Sync defaults saved");
  } catch (e) {
    showToast("Failed to save defaults: " + e.message);
  }
}

// Custom paths management
const customPathsBody = document.getElementById("customPathsBody");
const customPathsTable = document.getElementById("customPathsTable");

if (customPathsBody) {
  loadCustomPaths();
}

async function loadCustomPaths() {
  if (!customPathsBody) return;
  if (customPathsRequest) return customPathsRequest;
  customPathsRequest = (async () => {
    try {
      const resp = await fetch("/api/custom-paths");
      const data = await resp.json();
      renderCustomPaths(data.paths || []);
    } catch (e) {
      showToast("Failed to load custom paths: " + e.message);
    } finally {
      customPathsRequest = null;
    }
  })();
  return customPathsRequest;
}

function renderCustomPaths(paths) {
  customPathsBody.innerHTML = "";
  if (!paths.length) {
    const tr = document.createElement("tr");
    tr.innerHTML =
      '<td colspan="3" style="color:#6b7280;text-align:center">No custom paths</td>';
    customPathsBody.appendChild(tr);
    return;
  }
  paths.forEach(function (p) {
    const tr = document.createElement("tr");
    tr.innerHTML =
      "<td>" +
      esc(p.name) +
      "</td>" +
      "<td style=\"font-family:'SF Mono','Fira Code',monospace;font-size:.82rem\">" +
      esc(p.path) +
      "</td>" +
      '<td><button class="btn-del" onclick="deleteCustomPath(' +
      p.id +
      ')">Delete</button></td>';
    customPathsBody.appendChild(tr);
  });
}

async function addCustomPath() {
  const name = document.getElementById("newPathName").value.trim();
  const path = document.getElementById("newPathValue").value.trim();
  if (!name || !path) {
    showToast("Name and path are required");
    return;
  }
  try {
    const resp = await fetch("/api/custom-paths", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name, path: path }),
    });
    const data = await resp.json();
    if (data.error) {
      showToast(data.error);
      return;
    }
    document.getElementById("newPathName").value = "";
    document.getElementById("newPathValue").value = "";
    showToast("Custom path added");
    loadCustomPaths();
  } catch (e) {
    showToast("Failed to add custom path: " + e.message);
  }
}

async function deleteCustomPath(id) {
  if (!confirm("Delete this custom path?")) return;
  try {
    const resp = await fetch("/api/custom-paths/" + id, { method: "DELETE" });
    const data = await resp.json();
    if (data.error) {
      showToast(data.error);
      return;
    }
    showToast("Custom path deleted");
    loadCustomPaths();
  } catch (e) {
    showToast("Failed to delete custom path: " + e.message);
  }
}

// User management (only runs if the user table exists)
const userTableBody = document.getElementById("userTableBody");

if (userTableBody) {
  loadUsers();
}

async function loadUsers() {
  if (!userTableBody) return;
  try {
    const resp = await fetch("/admin/api/users");
    const data = await resp.json();
    renderUsers(data.users || []);
  } catch (e) {
    showToast("Failed to load users: " + e.message);
  }
}

function renderUsers(users) {
  const adminCount = users.filter((u) => u.role === "admin").length;
  userTableBody.innerHTML = "";
  users.forEach((u) => {
    const isLastAdmin = u.role === "admin" && adminCount <= 1;
    const tr = document.createElement("tr");
    const authMethod = u.auth_method || "local";
    const authBadge =
      authMethod === "oidc"
        ? '<span class="auth-badge auth-sso">SSO</span>'
        : '<span class="auth-badge auth-local">Local</span>';
    tr.innerHTML =
      `<td>${u.id}</td>` +
      `<td>${esc(u.username)}</td>` +
      `<td>
        <select onchange="changeRole(${u.id}, this.value)" ${isLastAdmin ? "disabled" : ""}>
          <option value="user" ${u.role === "user" ? "selected" : ""}>User</option>
          <option value="admin" ${u.role === "admin" ? "selected" : ""}>Admin</option>
        </select>
      </td>` +
      `<td>${authBadge}</td>` +
      `<td>${esc(u.created_at)}</td>` +
      `<td>${
        isLastAdmin
          ? '<span style="color:#555">protected</span>'
          : `<button class="btn-del" onclick="deleteUser(${u.id})">Delete</button>`
      }</td>`;
    userTableBody.appendChild(tr);
  });
  if (window.refreshCustomSelect) {
    userTableBody.querySelectorAll("select").forEach((select) => {
      window.refreshCustomSelect(select);
    });
  }
}

if (window.LiveUpdates && typeof window.LiveUpdates.subscribe === "function") {
  window.LiveUpdates.subscribe(["settings"], () => {
    loadSettings();
    loadCustomPaths();
    loadUpdateStatus(false);
  });
}

if (updateCheckBtn) {
  updateCheckBtn.addEventListener("click", checkForUpdatesNow);
}

if (restartAppBtn) {
  restartAppBtn.addEventListener("click", restartDownloaderFromSettings);
}

if (updateApplyBtn) {
  updateApplyBtn.addEventListener("click", startWebUpdate);
}
if (settingsUpdateOverlayClose) {
  settingsUpdateOverlayClose.addEventListener("click", () => {
    updateOverlayDismissed = true;
    setUpdateOverlayVisible(false);
  });
}
if (settingsUpdateOverlayRestart) {
  settingsUpdateOverlayRestart.addEventListener(
    "click",
    restartDownloaderFromSettings,
  );
}
if (settingsRestartBannerBtn) {
  settingsRestartBannerBtn.addEventListener(
    "click",
    restartDownloaderFromSettings,
  );
}

async function addUser() {
  const username = document.getElementById("newUsername").value.trim();
  const password = document.getElementById("newPassword").value;
  const role = document.getElementById("newRole").value;

  if (!username || !password) {
    showToast("Username and password required");
    return;
  }

  try {
    const resp = await fetch("/admin/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, role }),
    });
    const data = await resp.json();
    if (data.error) {
      showToast(data.error);
      return;
    }
    document.getElementById("newUsername").value = "";
    document.getElementById("newPassword").value = "";
    showToast("User created");
    loadUsers();
  } catch (e) {
    showToast("Failed to create user: " + e.message);
  }
}

async function deleteUser(id) {
  if (!confirm("Delete this user?")) return;
  try {
    const resp = await fetch(`/admin/api/users/${id}`, { method: "DELETE" });
    const data = await resp.json();
    if (data.error) {
      showToast(data.error);
      return;
    }
    showToast("User deleted");
    loadUsers();
  } catch (e) {
    showToast("Failed to delete user: " + e.message);
  }
}

async function changeRole(id, newRole) {
  try {
    const resp = await fetch(`/admin/api/users/${id}/role`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: newRole }),
    });
    const data = await resp.json();
    if (data.error) {
      showToast(data.error);
      loadUsers();
      return;
    }
    showToast("Role updated");
    loadUsers();
  } catch (e) {
    showToast("Failed to update role: " + e.message);
  }
}

function showToast(msg) {
  if (
    window.AniworldNotifications &&
    typeof window.AniworldNotifications.add === "function"
  ) {
    window.AniworldNotifications.add(msg, { source: "Settings" });
  }
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.style.display = "block";
  setTimeout(() => (t.style.display = "none"), 4000);
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s || "";
  return d.innerHTML;
}
