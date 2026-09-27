# koirosvg.com (repo koiro-svg/yo-tutka)

Mikä tämä on: koirosvg.com-sivuston julkaisurepo. Kotivalikko (`index.html`) ja kaksi
työkalua: AI-malliopas (`ai-opas.html`) ja YO-tutka (`yo-tutka.html`). Repo on **julkinen**.

## Build & run
- Ei buildia. `python3 -m http.server` repon juuressa ja avaa `/ai-opas.html`
  (opas hakee `data/ai-models.json`:n fetchillä, joten file:// ei toimi).
- Vercel julkaisee mainin automaattisesti; `vercel.json`:n `cleanUrls` tekee
  `/ai-opas` ja `/yo-tutka` -polut.

## Arkkitehtuuri
- Jokainen sivu on itsenäinen tiedosto (CSS/JS sisällä). Värit/fontit ovat samat
  tokenit kuin YO-tutkassa – kopioitu jokaiseen sivuun.
- AI-opas: `scripts/update_models.py` (stdlib) → `data/ai-models.json` →
  `ai-opas.html` renderöi. GitHub Action `update-models.yml` joka toinen päivä,
  secret `AA_API_KEY`. Ks. README.
- YO-tutkan lähde on `~/sovellukset/yo-tutka/` (data + koosta.py); tänne tuodaan
  vain data README:n komennolla.

## Known sharp edges (don't regress these)
- YO-tutka on `yo-tutka.html`, ei `index.html` – README:n datansiirtokomento
  kirjoittaa siihen. Älä kopioi sovellukset-kansion `index.html`:ää tänne sokeasti.
- Artificial Analysisin ilmainen API vaatii näkyvän attribuution
  (linkki artificialanalysis.ai) – älä poista sitä ai-opas.html:n footerista.
- `update_models.py` säilyttää epäonnistuneen kategorian vanhan datan; älä muuta
  sitä kirjoittamaan tyhjää listaa virheen sattuessa.
- Automaatio-kategoria käyttää agenttimittaria vain jos API sen antaa; muuten
  fallback on Intelligence Index ja se kerrotaan mittarin nimessä. Pidä rehellinen.
- API-avain vain GitHub-secretissä. Repo on julkinen.
- Samasta mallista tulee API:sta monta versiota ("Claude Opus 5.5 (Adaptive Reasoning, Max
  Effort…)"). `item()` pilkkoo sulkeiden edestä ja `top()` pitää vain parhaan version –
  muuten yksi malli täyttää koko listan.
- Agenttitestit valitaan kärkimallien (top 20 älykkyydellä) kattavuuden mukaan ja kaikilta
  vaaditaan samat testit. Älä keskiarvoista eri testijoukkoja eri malleille (ei vertailukelpoista),
  äläkä valitse testejä koko mallijoukon mukaan (uusimmat mallit putoavat pois).
- AA:n Math Index jäi päivittymättä joulukuussa 2025. `stale()` ai-opas.html:ssä näyttää
  varoituksen, jos listan uusin malli on yli 180 päivää vanha.
- `data/`-kansio syntyy vasta ensimmäisestä ajosta; skripti luo sen itse (`mkdir`).
