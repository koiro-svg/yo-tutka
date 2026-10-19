// Site search (julkinen-6), shared by the home page and the YO bar (scripts/yo-nav.html). Both load this module with
// import() on first use, and the data is fetched on the first search: AI models, coding agents, tools and the YO subjects
// and topics (data/yo-topics.json, generated from yo-tutka.html's yo-data block by scripts/yo_index.py).
// AI card links carry the raw name; /ai turns it into its card id (one id scheme, owned by ai.html's parseHash).
const getJson = u => fetch(u, {cache: 'no-cache'}).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });
const norm = s => String(s || '').toLowerCase();
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const enc = encodeURIComponent;

let index = null;
async function build(models){
  const ai = () => getJson('/data/ai-models.json');
  const parts = await Promise.all([models ? models.catch(ai) : ai(), getJson('/data/coding-agents.json'), getJson('/data/ai-tools.json'), getJson('/data/yo-topics.json')].map(p => p.catch(() => null)));
  if (parts.includes(null)) index = null;   // a source that failed (network) is fetched again on the next search
  const [m, a, t, yo] = parts;
  const out = [];
  if (m) {
    const seen = new Set();
    for (const [cid, c] of Object.entries(m.categories || {})) for (const it of c.items || []) {
      if (seen.has(it.name)) continue;
      seen.add(it.name);
      out.push({kind: 'Malli', title: it.name, sub: it.creator, href: `/ai#m-${cid}`, text: `${it.name} ${it.creator}`});
    }
  }
  if (a) for (const g of a.agents || []) out.push({kind: 'Koodausagentti', title: g.name, sub: g.bestFor, href: `/ai#a-${enc(g.name)}`, text: `${g.name} ${g.vendor} ${g.bestFor}`});
  if (t) for (const ar of t.areas || []) {
    out.push({kind: 'Osa-alue', title: ar.title, sub: ar.intro, href: `/ai#tyokalut/${ar.id}`, text: `${ar.title} ${ar.intro}`});
    for (const x of ar.tools || []) out.push({kind: 'Työkalu', title: x.name, sub: `${ar.title} · ${x.bestFor}`, href: `/ai#t-${ar.id}-${enc(x.name)}`, text: `${x.name} ${x.vendor} ${x.bestFor} ${x.why}`});
  }
  // YO: /yo-tutka#<subject>[/<topic>] (yo-tutka.html's deep links).
  if (yo) for (const s of yo.subjects || []) {
    out.push({kind: 'YO-aine', title: s.name, sub: 'YO-tutka: aiheet ja todennäköisyydet', href: `/yo-tutka#${enc(s.id)}`, text: s.name});
    for (const x of s.topics || []) out.push({kind: 'YO-aihe', title: x.name, sub: `${s.name} · ${x.description}`, href: `/yo-tutka#${enc(s.id)}/${enc(x.id)}`, text: `${x.name} ${x.description} ${s.name}`});
  }
  for (const x of out) { x.text = norm(x.text); x.key = norm(x.title); }
  return out;
}

// Up to eight hits, titles that start with the query first. `models`: the home page passes its own ai-models.json fetch,
// so the AI card and the search share one request (fetched again here if it failed).
export async function search(q, models){
  const v = norm(q.trim());
  if (!v) return [];
  const all = await (index ||= build(models));
  return all.filter(x => x.text.includes(v)).sort((x, y) => y.key.startsWith(v) - x.key.startsWith(v)).slice(0, 8);
}

export const hitsHtml = (found, q) => found.length
  ? found.map(x => `<li><a href="${esc(x.href)}"><small>${esc(x.kind)}</small><b>${esc(x.title)}</b><span>${esc(x.sub || '')}</span></a></li>`).join('')
  : `<li class="none">Ei osumia. Kokeile toista sanaa tai avaa <a href="/ai?q=${enc(norm(q.trim()))}">AI-opas</a> tai <a href="/yo-tutka">YO-tutka</a>.</li>`;
