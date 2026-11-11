// Site search (julkinen-6; own pages and the no-data state 10.11.2026), shared by the home page and the YO bar (scripts/yo-nav.html). Both load this module with
// import() on first use, and the data is fetched on the first search: AI models, coding agents, tools and the YO subjects
// and topics (data/yo-topics.json, generated from yo-tutka.html's yo-data block by scripts/yo_index.py), YO practice per
// subject, and the Visa quiz titles (data/visa.json and its packs; koti-F3, 11.11.2026).
// AI card links carry the raw name; /ai turns it into its card id (one id scheme, owned by ai.html's parseHash).
const getJson = u => fetch(u, {cache: 'no-cache'}).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });
const norm = s => String(s || '').toLowerCase();
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const enc = encodeURIComponent;

// The site's own pages: always in the index, also when every data fetch fails (new root page = a row here).
const PAGES = [
  {kind: 'Sivu', title: 'AI-opas', sub: 'Parhaat tekoälymallit, koodausagentit ja työkalut', href: '/ai', text: 'ai-opas tekoäly mallit koodausagentit työkalut'},
  {kind: 'Sivu', title: 'YO-tutka', sub: 'Ylioppilaskokeiden aiheet ja todennäköisyydet', href: '/yo-tutka', text: 'yo-tutka ylioppilaskoe ylioppilaskirjoitukset aiheet todennäköisyys'},
  {kind: 'Sivu', title: 'YO-harjoittelu', sub: 'Tehtävät kaavaeditorilla, vihjeet, malliratkaisut ja koesimulaatio', href: '/yo-harjoittelu', text: 'yo-harjoittelu harjoittelu harjoittele kertaus koesimulaatio kaavaeditori abitti vihjeet malliratkaisut'},
  {kind: 'Sivu', title: 'Hyppymittari', sub: 'Pystyhyppy, kosketuskorkeus ja loikat puhelimen kameralla', href: '/hyppymittari', text: 'hyppymittari hyppy pystyhyppy kosketuskorkeus vauhditon pituus kolmiloikka viisiloikka kamera'},
  {kind: 'Sivu', title: 'Visakaksintaisto', sub: 'Tietovisat kaveria vastaan: listat, liput, kartat ja monivalinnat', href: '/visa', text: 'visakaksintaisto visa tietovisa kaksintaisto liput kartta maat pääkaupungit 1v1'},
  {kind: 'Sivu', title: 'Tietosuoja', sub: 'Mitä sivusto tallentaa ja miten tiedot poistetaan', href: '/tietosuoja', text: 'tietosuoja tietosuojaseloste evästeet yksityisyys tili poisto'},
];

// Visa: visa.html has no deep link to a single quiz (its #hash is a room code), so a quiz hit opens the lobby, whose own
// search finds the quiz by the same title. All packs or nothing: a failed pack makes the whole source fail (retried).
const VISA_FORMAT = {flags: 'liput', map: 'kartta', choice: 'monivalinta'};
const visa = () => getJson('/data/visa.json').then(d =>
  Promise.all((d.packs || []).map(n => getJson(`/data/visa/${enc(n)}.json`))).then(ps => ({cats: d.cats || {}, quizzes: [...(d.quizzes || []), ...ps.flatMap(p => p.quizzes || [])]})));

let index = null;
async function build(models, tools){
  const ai = () => getJson('/data/ai-models.json'), tl = () => getJson('/data/ai-tools.json');
  const parts = await Promise.all([models ? models.catch(ai) : ai(), getJson('/data/coding-agents.json'), tools ? tools.catch(tl) : tl(), getJson('/data/yo-topics.json'), visa()].map(p => p.catch(() => null)));
  if (parts.includes(null)) index = null;   // a source that failed (network) is fetched again on the next search
  const [m, a, t, yo, vz] = parts;
  const out = PAGES.map(x => ({...x}));
  out.partial = parts.includes(null);   // hitsHtml: "no data" is not "no hits"
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
  // YO: /yo-tutka#<subject>[/<topic>] (yo-tutka.html's deep links) and the subject's practice page /yo-harjoittelu#/<subject>.
  // A topic hit opens the topic panel, whose Harjoittele and Pikatesti buttons lead to its practice tasks.
  if (yo) for (const s of yo.subjects || []) {
    out.push({kind: 'YO-aine', title: s.name, sub: 'YO-tutka: aiheet ja todennäköisyydet', href: `/yo-tutka#${enc(s.id)}`, text: s.name});
    out.push({kind: 'YO-harjoittelu', title: s.name, sub: 'Harjoittele tehtäviä: vihjeet, malliratkaisut ja koesimulaatio', href: `/yo-harjoittelu#/${enc(s.id)}`, text: `${s.name} harjoittelu harjoittele harjoitustehtävät tehtävät koesimulaatio`});
    for (const x of s.topics || []) out.push({kind: 'YO-aihe', title: x.name, sub: `${s.name} · ${x.description}`, href: `/yo-tutka#${enc(s.id)}/${enc(x.id)}`, text: `${x.name} ${x.description} ${s.name}`});
  }
  if (vz) for (const x of vz.quizzes) {
    const title = x.title?.fi, cat = vz.cats[x.cat]?.fi || '';
    if (typeof title !== 'string' || !title) continue;
    out.push({kind: 'Visa', title, sub: ['Visakaksintaisto', cat, VISA_FORMAT[x.format]].filter(Boolean).join(' · '), href: '/visa', text: `${title} ${cat}`});
  }
  for (const x of out) { x.text = norm(x.text); x.key = norm(x.title); }
  return out;
}

// Up to eight hits, titles that start with the query first. `models`: the home page passes its own ai-models.json fetch,
// so the AI card and the search share one request (fetched again here if it failed); `tools` likewise for ai-tools.json.
export async function search(q, models, tools){
  const v = norm(q.trim());
  if (!v) return [];
  const all = await (index ||= build(models, tools));
  const found = all.filter(x => x.text.includes(v)).sort((x, y) => y.key.startsWith(v) - x.key.startsWith(v)).slice(0, 8);
  found.partial = all.partial;
  return found;
}

// (found, q) is the whole contract (the YO bar calls it the same way); `found.partial` comes from search().
export const NO_DATA = '<li class="none" role="status">Haku ei saanut kaikkea dataa. Tarkista yhteys ja yritä uudelleen.</li>';
export const hitsHtml = (found, q) => found.length
  ? found.map(x => `<li><a href="${esc(x.href)}"><small>${esc(x.kind)}</small><b>${esc(x.title)}</b><span>${esc(x.sub || '')}</span></a></li>`).join('')
  : found.partial ? NO_DATA
  : `<li class="none">Ei osumia. Kokeile toista sanaa tai avaa <a href="/ai?q=${enc(norm(q.trim()))}">AI-opas</a> tai <a href="/yo-tutka">YO-tutka</a>.</li>`;
