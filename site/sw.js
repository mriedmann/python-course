// Offline support: precache the built site and the Pyodide 0.28.1 files from the CDN, then serve cache-first.
// __BUILD__ is replaced by site/tools/sw_manifest.py after render, so every new build changes this file,
// which makes the browser install the new worker and a fresh cache.
const BUILD = "__BUILD__";
const CACHE = "course-" + BUILD;
const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.28.1/full/";
const ROOT = new URL("./", self.location).href; // site root = directory of sw.js
const norm = (n) => n.toLowerCase().replace(/[-_.]+/g, "-");

async function precacheList() {
  const manifest = await (await fetch(ROOT + "sw-manifest.json", { cache: "no-cache" })).json();
  const urls = manifest.files.map((f) => ROOT + f);
  const lock = await (await fetch(PYODIDE + "pyodide-lock.json")).json();
  const byName = new Map(Object.entries(lock.packages).map(([k, v]) => [norm(k), v]));
  const files = new Set(["pyodide.mjs", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]);
  const todo = [...manifest.pyodide_packages];
  const seen = new Set();
  while (todo.length) {
    const name = norm(todo.pop());
    if (seen.has(name)) continue;
    seen.add(name);
    const pkg = byName.get(name);
    if (!pkg) throw new Error("package not in pyodide-lock.json: " + name);
    files.add(pkg.file_name);
    todo.push(...pkg.depends);
  }
  return urls.concat([...files].map((f) => PYODIDE + f));
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
  if (!req.url.startsWith(ROOT) && !req.url.startsWith(PYODIDE)) return; // third-party APIs (U13) stay live
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
