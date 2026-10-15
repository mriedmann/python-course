// Offline support: precache the built site (incl. the self-hosted Pyodide 0.28.1 in pyodide/), then serve cache-first.
// __BUILD__ is replaced by site/tools/sw_manifest.py after render, so every new build changes this file,
// which makes the browser install the new worker and a fresh cache.
const BUILD = "__BUILD__";
const CACHE = "course-" + BUILD;
const ROOT = new URL("./", self.location).href; // site root = directory of sw.js

async function precacheList() {
  const manifest = await (await fetch(ROOT + "sw-manifest.json", { cache: "no-cache" })).json();
  return manifest.files.map((f) => ROOT + f); // includes the self-hosted Pyodide in pyodide/
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE);
      const urls = await precacheList();
      let next = 0;
      // 6 parallel downloads; any failure rejects, so the old worker stays in charge until a full precache works
      await Promise.all(
        Array.from({ length: 6 }, async () => {
          while (next < urls.length) {
            const url = urls[next++];
            const res = await fetch(url);
            if (!res.ok) throw new Error(res.status + " " + url);
            await cache.put(url, res);
          }
        }),
      );
      await self.skipWaiting();
    })(),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      for (const key of await caches.keys()) if (key.startsWith("course-") && key !== CACHE) await caches.delete(key);
      await self.clients.claim();
    })(),
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET" || req.headers.has("range")) return;
  if (!req.url.startsWith(ROOT)) return; // third-party APIs (U13) stay live
  event.respondWith(
    (async () => {
      const cache = await caches.open(CACHE);
      const hit = await cache.match(req, { ignoreSearch: true }) ||
        (req.url.split(/[?#]/)[0].endsWith("/") && (await cache.match(req.url.split(/[?#]/)[0] + "index.html")));
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok) cache.put(req, res.clone());
      return res;
    })(),
  );
});
