# koirosvg.com (repo koiro-svg/yo-tutka)

Mikä tämä on: koirosvg.com-sivuston julkaisurepo. Kotivalikko (`index.html`) ja kaksi
työkalua: AI-malliopas (`ai-opas.html`) ja YO-tutka (`yo-tutka.html`). Repo on **julkinen**.

## Build & run
- Ei buildia. `python3 -m http.server` repon juuressa ja avaa `/ai-opas.html`
  (opas hakee `data/ai-models.json`:n fetchillä, joten file:// ei toimi).
- Vercel julkaisee mainin automaattisesti; `vercel.json`:n `cleanUrls` tekee
  `/ai-opas` ja `/yo-tutka` -polut.

## Arkkitehtuuri
- Jokainen sivu on itsenäinen tiedosto (CSS/JS sisällä). Työkalusivujen värit/fontit ovat samat
  tokenit kuin YO-tutkassa – kopioitu jokaiseen sivuun. Poikkeus: kotivalikko (`index.html`)
  on tarkoituksella aina tumma "tutka"-teema (Unbounded + canvas-tutka-animaatio).
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
- Tekstikategoriat ovat `BENCH`-taulussa (update_models.py). Jos testiä ei löydy, lista jää
  tyhjäksi ("Ei dataa vielä") – älä korvaa sitä toisella mittarilla hiljaa.
- `coverage` = osuus top 20 -malleista, joilla on testin tulos. Alle 0,5 → sivulla varoitus.
- API-avain vain GitHub-secretissä. Repo on julkinen.
- Samasta mallista tulee API:sta monta versiota ("Claude Opus 5.5 (Adaptive Reasoning, Max
  Effort…)"). `item()` pilkkoo sulkeiden edestä ja `top()` pitää vain parhaan version –
  muuten yksi malli täyttää koko listan.
- Monen testin kategorioissa (automaatio, asiakaspalvelu) testit valitaan kärkimallien (top 20 älykkyydellä) kattavuuden mukaan ja kaikilta
  vaaditaan samat testit. Älä keskiarvoista eri testijoukkoja eri malleille (ei vertailukelpoista),
  äläkä valitse testejä koko mallijoukon mukaan (uusimmat mallit putoavat pois).
- AA:n Math Index jäi päivittymättä joulukuussa 2025 → matematiikka poistettu (27.9.2026).
  `stale()` ai-opas.html:ssä varoittaa, jos listan uusin malli on yli 180 päivää vanha.
- Kuva-/videoarenan tyyli- ja aihekategoriat (`include_categories=true`) on jätetty pois
  tarkoituksella: kärkimalleilla (GPT Image 2.5 ym.) ei ole kategoriadataa, joten alalistat
  nostivat vanhoja malleja kärkeen. Tarkista `--inspect`-ajolla ennen kuin otat käyttöön.
- Uusia kenttiä tutkitaan ajamalla workflow `inspect: true` (tulostaa vain kenttien nimet
  ja kattavuuden lokiin, ei päivitä dataa).
- `data/`-kansio syntyy vasta ensimmäisestä ajosta; skripti luo sen itse (`mkdir`).
- Kotivalikon tutka-animaatio pysähtyy `prefers-reduced-motion`-asetuksella (piirretään kerran).
  Uusi työkalu = uusi kortti `.tools`-listaan + uusi nimetty piste `blips`-taulukkoon.
- Ei sisäisiä skrollialueita: aihetaulukko ja lämpökartta mahtuvat sarakkeeseensa kaikilla
  leveyksillä (320 px →). Kapeassa `.sec`-sarakkeessa container queryt vaihtavat taulukon
  korttiriveiksi (≤ 620 px) ja lämpökartan ruudukoksi (≤ 520 px, `--n` = tutkintokertojen
  määrä). Pitkät URL-tekstit rivittyvät (`overflow-wrap:anywhere`). Älä palauta
  `min-width`iä tai `overflow-x:auto`-kääreitä. Testaa 320–414 px kaikilla aineilla.
