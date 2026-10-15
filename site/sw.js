// Offline support: precache the built site (incl. the self-hosted Pyodide 0.28.1 in pyodide/), then serve cache-first.
// __BUILD__ is replaced by site/tools/sw_manifest.py after render, so every new build changes this file,
// which makes the browser install the new worker and a fresh cache.
const BUILD = "__BUILD__";
const CACHE = "course-" + BUILD;
// Site root = directory of sw.js, or SW_ROOT set by workspace/service-worker.js (JupyterLite registers that one).
const ROOT = new URL(self.SW_ROOT || "./", self.location).href;
// JupyterLite's drive protocol (its own service-worker.js, replaced by site/tools/lite_build.py): the kernel's
// file access (/api/drive) and input() (/api/stdin/) are relayed to the lab page over this channel.
const LITE = new BroadcastChannel("/sw-api.v1");

async function precacheList() {
  const manifest = await (await fetch(ROOT + "sw-manifest.json", { cache: "no-cache" })).json();
  return manifest.files.map((f) => ROOT + f); // includes the self-hosted Pyodide in pyodide/
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE);
      // Workspace registration: the kernel starts before an install could finish, so activate at once and cache
      // at runtime (fetch below). shortcut: workspace-first visitors get offline only for what they opened;
      // any lesson page then installs the root worker with the full precache.
      const urls = self.SW_ROOT ? [] : await precacheList();
      let next = 0;
      // 6 parallel downloads; any failure rejects, so the old worker stays in charge until a full precache works
      await Promise.all(
        Array.from({ length: 6 }, async () => {
          while (next < urls.length) {
            const url = urls[next++];
            if (await cache.match(url)) continue; // already cached at runtime by the workspace registration
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

async function relayToLab(req, path) {
  const body = await req.json();
  return new Promise((resolve) => {
    const onMessage = ({ data }) => {
      if (data.browsingContextId !== body.browsingContextId || data.requestId !== body.requestId) return;
      LITE.removeEventListener("message", onMessage);
      resolve(new Response(JSON.stringify(data.response)));
    };
    LITE.addEventListener("message", onMessage);
    LITE.postMessage({ ...body, pathname: path });
  });
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (url.pathname === "/api/service-worker-heartbeat") return event.respondWith(new Response("ok"));
  if (url.origin === location.origin && /\/api\/(drive|stdin\/)/.test(url.pathname)) {
    return event.respondWith(relayToLab(req, url.pathname));
  }
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
