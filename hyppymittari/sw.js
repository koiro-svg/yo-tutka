// Hyppymittari offline cache (erilliset-8).
// - vendor/, models/, the manifest and the icon are cache-first: bump VERSION whenever they change.
// - The page and the analysis modules are one "app set": fetched together, stored only when every part is a
//   genuine answer (200, not redirected, the expected type), and kept as a generation. A page is always served with
//   the modules of its own generation, so a slow network can never pair a new page with an old module (or the
//   reverse), and a captive portal's HTML or a 5xx during a deploy never replaces the working copy.
const VERSION = '2';
const CORE = 'hyppy-core-' + VERSION, APP = 'hyppy-app-';
const BASE = new URL('./', self.location).href;   // the folder of sw.js
const PAGE_KEY = BASE + '__page';                  // the page is kept under one key, whatever URL opened it
const MODULES = ['jump-analysis.js', 'reach-distance.js'].map(p => BASE + p);
const CORE_FILES = ['manifest.webmanifest', 'icons/icon-192.png',
  'vendor/mediapipe/vision_bundle.mjs', 'vendor/mediapipe/wasm/vision_wasm_internal.js',
  'vendor/mediapipe/wasm/vision_wasm_internal.wasm', 'models/pose_landmarker_lite.task'].map(p => BASE + p);
// The full model (video analysis) is cached the first time it is used.
const isCore = url => url.startsWith(BASE + 'vendor/') || url.startsWith(BASE + 'models/') || CORE_FILES.includes(url);
const NET_WAIT = 3000;   // a weak signal at the track: after this the cached app set answers

// A cached copy must not carry redirect info: a navigation can't be answered with a "redirected" response.
const plain = res => new Response(res.body, { status: res.status, statusText: res.statusText, headers: res.headers });
const genuine = (res, type) => res.ok && !res.redirected && res.type === 'basic' && (res.headers.get('content-type') || '').includes(type);
const sleep = ms => new Promise(r => setTimeout(r, ms));

// Which app generation each page (client) was served from. In memory only: if the worker restarts between a page
// and its module requests (milliseconds apart), the newest generation answers.
const servedFrom = new Map();
function remember(clientId, name) {
  if (!clientId) return;
  servedFrom.set(clientId, name);
  if (servedFrom.size > 20) servedFrom.delete(servedFrom.keys().next().value);
}

async function appCaches() {
  return (await caches.keys()).filter(k => k.startsWith(APP)).sort((a, b) => +b.slice(APP.length) - +a.slice(APP.length));
}

/** Fetches the page and the modules together; stores them as a new generation only if all are genuine. */
async function fetchApp(pageUrl) {
  const opts = { cache: 'no-cache', credentials: 'same-origin' };
  const [page, ...mods] = await Promise.all([fetch(pageUrl, opts), ...MODULES.map(u => fetch(u, opts))]);
  if (!genuine(page, 'text/html') || !mods.every(m => genuine(m, 'javascript'))) return null;
  const name = APP + Date.now(), cache = await caches.open(name);
  await Promise.all([cache.put(PAGE_KEY, plain(page.clone())), ...mods.map((m, i) => cache.put(MODULES[i], m))]);
  // Keep the previous generation too: a page opened from it may still be loading its modules.
  for (const old of (await appCaches()).slice(2)) await caches.delete(old);
  return { name, page };
}

self.addEventListener('install', e => e.waitUntil((async () => {
  await (await caches.open(CORE)).addAll(CORE_FILES);
  await fetchApp(self.registration.scope);   // best effort: the first navigation tries again
  await self.skipWaiting();
})()));

self.addEventListener('activate', e => e.waitUntil((async () => {
  for (const k of await caches.keys()) if ((k.startsWith('hyppy-core-') && k !== CORE) || k === 'hyppy-page') await caches.delete(k);
  await self.clients.claim();
})()));

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  if (req.mode === 'navigate') { e.respondWith(navigate(e)); return; }
  if (!req.url.startsWith(BASE)) return;   // other paths and origins: untouched
  if (MODULES.includes(req.url)) e.respondWith(module(e));
  else if (isCore(req.url)) e.respondWith(cacheFirst(req));
});

async function navigate(e) {
  const [newest] = await appCaches();
  const refresh = fetchApp(e.request.url).catch(() => null);
  e.waitUntil(refresh);   // a refresh that loses the race still lands for the next load
  if (!newest) {
    const app = await refresh;
    if (app) { remember(e.resultingClientId, app.name); return app.page; }
    return fetch(e.request).catch(() => Response.error());
  }
  const app = await Promise.race([refresh, sleep(NET_WAIT).then(() => null)]);
  if (app) { remember(e.resultingClientId, app.name); return app.page; }
  remember(e.resultingClientId, newest);
  return (await (await caches.open(newest)).match(PAGE_KEY)) || fetch(e.request).catch(() => Response.error());
}

async function module(e) {
  const name = servedFrom.get(e.clientId) || (await appCaches())[0];
  const hit = name && await (await caches.open(name)).match(e.request.url);
  return hit || fetch(e.request).catch(() => Response.error());
}

async function cacheFirst(req) {
  const cache = await caches.open(CORE), hit = await cache.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok) cache.put(req, res.clone());
  return res;
}
