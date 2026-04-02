const CACHE_NAME = "aniworld-shell-v1";
const SHELL_ASSETS = [
  "/static/style.css",
  "/static/background.js",
  "/static/custom-selects.js",
  "/static/live-updates.js",
  "/static/queue.js",
  "/static/app.js",
  "/static/library.js",
  "/static/autosync.js",
  "/static/settings.js",
  "/static/shell.js",
  "/static/icon.svg",
  "/static/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS)),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key)),
      ),
    ),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  const requestUrl = new URL(event.request.url);
  if (requestUrl.origin !== self.location.origin) return;

  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          return response;
        })
        .catch(async () => {
          return new Response(
            '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Offline</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#08111d;color:#ecf5ff;font:16px Manrope,Segoe UI,sans-serif;padding:24px}main{max-width:440px;padding:28px;border:1px solid rgba(255,255,255,.08);border-radius:24px;background:rgba(8,18,31,.92);text-align:center}h1{margin:0 0 12px;font-size:1.8rem}p{margin:0;color:#9bb0c8;line-height:1.6}</style></head><body><main><h1>Offline</h1><p>The web app is installed, but this page needs a network connection right now. Reconnect and try again.</p></main></body></html>',
            {
              headers: { "Content-Type": "text/html; charset=utf-8" },
            },
          );
        }),
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const networkFetch = fetch(event.request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          return response;
        })
        .catch(() => cached);

      return cached || networkFetch;
    }),
  );
});
