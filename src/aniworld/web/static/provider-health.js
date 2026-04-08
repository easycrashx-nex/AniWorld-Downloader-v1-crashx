const providerHealthList = document.getElementById("providerHealthList");
const providerHistoryList = document.getElementById("providerHistoryList");
const providerFailureList = document.getElementById("providerFailureList");
const providerBenchmarkList = document.getElementById("providerBenchmarkList");
const providerBenchmarkEpisodeUrlInput = document.getElementById(
  "providerBenchmarkEpisodeUrl",
);
const providerBenchmarkLanguageSelect = document.getElementById(
  "providerBenchmarkLanguage",
);
const providerBenchmarkRunBtn = document.getElementById(
  "providerBenchmarkRunBtn",
);
let providerHealthRequest = null;
let providerHistoryRequest = null;
let providerFailureRequest = null;
let providerBenchmarkRequest = null;

function providerHealthTone(health) {
  return health || "idle";
}

function formatProviderDate(value) {
  if (!value) return "No activity yet";
  const date = new Date(String(value).replace(" ", "T") + "Z");
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function renderProviderHealth(items) {
  if (!providerHealthList) return;
  if (!items.length) {
    providerHealthList.innerHTML =
      '<div class="stats-empty">No provider health data yet.</div>';
    return;
  }

  providerHealthList.innerHTML = items
    .map((item) => {
      const tone = providerHealthTone(item.health);
      return `
        <article class="provider-health-card provider-health-${tone}">
          <div class="provider-health-head">
            <div>
              <div class="provider-health-rank">#${Number(item.rank || 0)}</div>
              <div class="provider-health-name">${escProviderHealth(item.provider || "Unknown")}</div>
              <div class="provider-health-status">${escProviderHealth((item.health || "idle").toUpperCase())}</div>
            </div>
            <div class="provider-health-score-wrap">
              <div class="provider-health-score">${Number(item.score || 0)}</div>
              <div class="provider-health-rate">${Number(item.success_rate || 0)}%</div>
            </div>
          </div>
          <div class="provider-health-metrics">
            <span>${Number(item.running || 0)} running</span>
            <span>${Number(item.queued || 0)} queued</span>
            <span>${Number(item.failed_24h || 0)} failed today</span>
          </div>
          <div class="provider-health-meta">
            <div>Completed: <strong>${Number(item.completed || 0)}</strong></div>
            <div>Failed: <strong>${Number(item.failed || 0)}</strong></div>
            <div>Delivered: <strong>${Number(item.episodes || 0)} eps</strong></div>
          </div>
          <div class="provider-health-foot">
            <span>Last success: ${escProviderHealth(formatProviderDate(item.last_success_at))}</span>
            <span>Last failure: ${escProviderHealth(formatProviderDate(item.last_failure_at))}</span>
          </div>
        </article>`;
    })
    .join("");
}

function renderProviderHistory(items) {
  if (!providerHistoryList) return;
  const flatItems = Array.isArray(items)
    ? items
    : Object.entries(items || {}).flatMap(([provider, entries]) =>
        (entries || []).map((entry) => Object.assign({ provider }, entry)),
      );
  if (!flatItems.length) {
    providerHistoryList.innerHTML =
      '<div class="stats-empty">No provider score history has been collected yet.</div>';
    return;
  }

  const grouped = new Map();
  flatItems.forEach((item) => {
    const key = item.provider || "Unknown";
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key).push(item);
  });

  providerHistoryList.innerHTML = Array.from(grouped.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([provider, entries]) => {
      const ordered = entries
        .slice()
        .sort(
          (a, b) =>
            new Date(a.snapshotted_at || 0).getTime() -
            new Date(b.snapshotted_at || 0).getTime(),
        );
      const latest = ordered[ordered.length - 1] || {};
      const maxScore = Math.max(
        1,
        ...ordered.map((entry) => Number(entry.score || 0)),
      );
      return `
        <article class="provider-history-card">
          <div class="provider-history-head">
            <div>
              <strong>${escProviderHealth(provider)}</strong>
              <span>${ordered.length} snapshots</span>
            </div>
            <div class="provider-history-meta">
              <span>Latest ${Number(latest.score || 0)}</span>
              <span>${escProviderHealth(
                formatProviderDate(latest.snapshotted_at),
              )}</span>
            </div>
          </div>
          <div class="provider-history-bars">
            ${ordered
              .slice(-12)
              .map((entry) => {
                const score = Number(entry.score || 0);
                const height = Math.max(10, Math.round((score / maxScore) * 100));
                return `
                  <span
                    class="provider-history-bar"
                    style="height:${height}%"
                    title="${escProviderHealth(
                      `${provider}: ${score} at ${formatProviderDate(
                        entry.snapshotted_at,
                      )}`,
                    )}"
                  ></span>`;
              })
              .join("")}
          </div>
          <div class="provider-history-foot">
            <span>${Number(latest.completed || 0)} completed</span>
            <span>${Number(latest.failed || 0)} failed</span>
            <span>${Number(latest.running || 0)} running</span>
          </div>
        </article>`;
    })
    .join("");
}

function renderProviderFailures(items) {
  if (!providerFailureList) return;
  if (!Array.isArray(items) || !items.length) {
    providerFailureList.innerHTML =
      '<div class="stats-empty">No provider failure analytics are available yet.</div>';
    return;
  }

  providerFailureList.innerHTML = items
    .map((item) => {
      const reasons = Array.isArray(item.top_reasons) ? item.top_reasons : [];
      const titles = Array.isArray(item.latest_titles) ? item.latest_titles : [];
      return `
        <article class="provider-failure-card">
          <div class="provider-failure-head">
            <div>
              <strong>${escProviderHealth(item.provider || "Unknown")}</strong>
              <span>${Number(item.failed_total || 0)} recent failures</span>
            </div>
            <span>${escProviderHealth(formatProviderDate(item.latest_failure_at))}</span>
          </div>
          <div class="provider-failure-reasons">
            ${reasons.length
              ? reasons
                  .map(
                    (reason) =>
                      `<span class="provider-failure-chip" title="${escProviderHealth(
                        reason.reason || "Unknown failure",
                      )}">${escProviderHealth(reason.count)}x ${escProviderHealth(
                        reason.reason || "Unknown failure",
                      )}</span>`,
                  )
                  .join("")
              : '<span class="provider-failure-chip">No parsed reasons yet</span>'}
          </div>
          ${
            titles.length
              ? `<div class="provider-failure-titles">${titles
                  .map((title) => `<span>${escProviderHealth(title)}</span>`)
                  .join("")}</div>`
              : ""
          }
        </article>`;
    })
    .join("");
}

function renderProviderBenchmark(data) {
  if (!providerBenchmarkList) return;
  const sample = data?.sample || {};
  const results = Array.isArray(data?.results) ? data.results : [];
  if (!results.length) {
    providerBenchmarkList.innerHTML =
      '<div class="stats-empty">No benchmark results available for this sample.</div>';
    return;
  }

  providerBenchmarkList.innerHTML = `
    <div class="provider-benchmark-summary">
      <strong>${escProviderHealth(sample.title || "Sample episode")}</strong>
      <span>${escProviderHealth(sample.language || "-")}</span>
      <span>${escProviderHealth(sample.episode_url || "-")}</span>
    </div>
    <div class="provider-benchmark-cards">
      ${results
        .map((item) => {
          const tone =
            item.status === "ready"
              ? "is-ready"
              : item.status === "broken"
                ? "is-warn"
                : "is-error";
          return `
            <article class="provider-benchmark-card ${tone}">
              <div class="provider-benchmark-head">
                <div>
                  <div class="provider-health-rank">#${Number(item.rank || 0)}</div>
                  <strong>${escProviderHealth(item.provider || "Unknown")}</strong>
                </div>
                <div class="provider-benchmark-latency">${Number(item.latency_ms || 0)} ms</div>
              </div>
              <div class="provider-benchmark-meta">
                <span>${escProviderHealth((item.status || "unknown").toUpperCase())}</span>
                <span>${escProviderHealth(item.redirect_host || "No redirect host")}</span>
              </div>
              ${
                item.error
                  ? `<div class="provider-benchmark-error">${escProviderHealth(item.error)}</div>`
                  : item.redirect_url
                    ? `<div class="provider-benchmark-url">${escProviderHealth(item.redirect_url)}</div>`
                    : ""
              }
            </article>`;
        })
        .join("")}
    </div>`;
}

async function loadProviderHealth() {
  if (!providerHealthList) return null;
  if (providerHealthRequest) return providerHealthRequest;
  providerHealthRequest = (async () => {
    try {
      const resp = await fetch("/api/provider-health");
      const data = await resp.json();
      renderProviderHealth(data.items || []);
      return data.items || [];
    } catch (e) {
      providerHealthList.innerHTML =
        '<div class="stats-empty">Provider health could not be loaded.</div>';
      return null;
    } finally {
      providerHealthRequest = null;
    }
  })();
  return providerHealthRequest;
}

async function loadProviderHistory() {
  if (!providerHistoryList) return null;
  if (providerHistoryRequest) return providerHistoryRequest;
  providerHistoryRequest = (async () => {
    try {
      const resp = await fetch("/api/provider-health/history?hours=168");
      const data = await resp.json();
      renderProviderHistory(data.items || []);
      return data.items || [];
    } catch (e) {
      providerHistoryList.innerHTML =
        '<div class="stats-empty">Provider score history could not be loaded.</div>';
      return null;
    } finally {
      providerHistoryRequest = null;
    }
  })();
  return providerHistoryRequest;
}

async function loadProviderFailures() {
  if (!providerFailureList) return null;
  if (providerFailureRequest) return providerFailureRequest;
  providerFailureRequest = (async () => {
    try {
      const resp = await fetch("/api/provider-health/failures");
      const data = await resp.json();
      renderProviderFailures(data.items || []);
      return data.items || [];
    } catch (e) {
      providerFailureList.innerHTML =
        '<div class="stats-empty">Provider failure analytics could not be loaded.</div>';
      return null;
    } finally {
      providerFailureRequest = null;
    }
  })();
  return providerFailureRequest;
}

async function runProviderBenchmark() {
  if (!providerBenchmarkList) return null;
  if (providerBenchmarkRequest) return providerBenchmarkRequest;
  if (providerBenchmarkRunBtn) providerBenchmarkRunBtn.disabled = true;
  providerBenchmarkList.innerHTML =
    '<div class="stats-empty">Running provider benchmark...</div>';

  providerBenchmarkRequest = (async () => {
    try {
      const resp = await fetch("/api/provider-health/benchmark", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          episode_url: providerBenchmarkEpisodeUrlInput?.value || "",
          language: providerBenchmarkLanguageSelect?.value || "German Dub",
        }),
      });
      const data = await resp.json();
      if (data.error) {
        throw new Error(data.error);
      }
      renderProviderBenchmark(data);
      return data;
    } catch (e) {
      providerBenchmarkList.innerHTML =
        '<div class="stats-empty">Provider benchmark failed: ' +
        escProviderHealth(e.message || "Unknown error") +
        "</div>";
      return null;
    } finally {
      providerBenchmarkRequest = null;
      if (providerBenchmarkRunBtn) providerBenchmarkRunBtn.disabled = false;
    }
  })();
  return providerBenchmarkRequest;
}

function escProviderHealth(value) {
  const div = document.createElement("div");
  div.textContent = value == null ? "" : String(value);
  return div.innerHTML;
}

loadProviderHealth();
loadProviderHistory();
loadProviderFailures();

if (window.LiveUpdates && typeof window.LiveUpdates.subscribe === "function") {
  window.LiveUpdates.subscribe(["queue", "dashboard", "settings"], () => {
    loadProviderHealth();
    loadProviderHistory();
    loadProviderFailures();
  });
}

if (providerBenchmarkLanguageSelect && window.refreshCustomSelect) {
  window.refreshCustomSelect(providerBenchmarkLanguageSelect);
}

setInterval(() => {
  if (!window.LiveUpdates || !window.LiveUpdates.isConnected()) {
    loadProviderHealth();
    loadProviderHistory();
    loadProviderFailures();
  }
}, 30000);
