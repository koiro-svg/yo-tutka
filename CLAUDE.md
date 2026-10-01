# koirosvg.com (repo koiro-svg/yo-tutka)

Mikä tämä on: koirosvg.com-sivuston julkaisurepo. Kotivalikko (`index.html`) ja työkalut:
AI-malliopas (`ai-opas.html`), AI-työkalupakki (`ai-tyokalut.html`), YO-tutka
(`yo-tutka.html`) ja sen harjoitusosio YO-harjoittelu (`yo-harjoittelu.html`). Repo on **julkinen**.

## Build & run
- Ei buildia. `python3 -m http.server` repon juuressa ja avaa `/ai-opas.html`
  (opas ja työkalupakki hakevat `data/*.json`:n fetchillä, joten file:// ei toimi).
- Vercel julkaisee mainin automaattisesti; `vercel.json`:n `cleanUrls` tekee
  `/ai-opas` ja `/yo-tutka` -polut.

## Arkkitehtuuri
- Jokainen sivu on itsenäinen tiedosto (CSS/JS sisällä). Kaikki kolme sivua käyttävät samaa
  tarkoituksella aina tummaa "tutka"-teemaa (tokenit kopioitu jokaiseen sivuun, Unbounded-otsikot,
  turkoosi `--accent`). Kotivalikossa lisäksi canvas-tutka-animaatio. Työkalusivuilla on
  `← koirosvg.com`-paluulinkki (`.crumb`) mastheadissa – pidä se jokaisessa uudessa sivussa.
- AI-opas: `scripts/update_models.py` (stdlib) → `data/ai-models.json` →
  `ai-opas.html` renderöi. GitHub Action `update-models.yml` joka toinen päivä,
  secret `AA_API_KEY`. Ks. README.
- AI-työkalupakki: `data/ai-tools.json` → `ai-tyokalut.html` renderöi (fetch). Dataa
  päivittää ajastettu Claude-pilviagentti (routine) joka toinen päivä ohjeen
  `scripts/UPDATE_TOOLS.md` mukaan, ja `scripts/validate_tools.py` tarkistaa sen ennen
  committia. Ei API-avainta eikä GitHub Actionia.
- YO-tutkan lähde on `~/sovellukset/yo-tutka/` (data + koosta.py); tänne tuodaan
  vain data README:n komennolla.
- YO-harjoittelu (`/yo-harjoittelu`): Abitti-tyylinen vastauseditori (digabi/MathQuill +
  MathJax CDN:stä), vihjeet ja malliratkaisut, itsearvio, kertauslista, koesimulaatio ja
  apuvälinepaneeli (Mafy-taulukot, GeoGebra, Desmos upotettuina). Tehtävälistan se hakee
  `yo-tutka.html`:n `yo-data`-lohkosta fetchillä; harjoitussisältö on
  `data/practice/<aine>/<kerta>.json` (kirjoitusohje `scripts/PRACTICE_CONTENT.md`,
  tarkistus `scripts/validate_practice.py`, kopiointitarkistus `scripts/check_overlap.py`).
  Vastaukset (IndexedDB) ja arviot (localStorage `yo-practice`) ovat vain käyttäjän selaimessa.
  YO-tutka lukee samat arviot "Harjoittele seuraavaksi" -listaan.

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
- Kotivalikon oikeassa alakulmassa on tarkoituksella huomaamaton lukko-ikoni (`.lock`,
  väri #5A7194 = 3,7:1 kontrasti, absoluuttisesti sijoitettu ettei siirrä asettelua) → `https://oma.koirosvg.com`, yksityinen alue (repo koiro-svg/koirosvg-oma,
  yksityinen). Älä tee siitä näkyvää korttia äläkä lisää sitä tutkan `blips`-pisteisiin.
- Ei sisäisiä skrollialueita: aihetaulukko ja lämpökartta mahtuvat sarakkeeseensa kaikilla
  leveyksillä (320 px →). Kapeassa `.sec`-sarakkeessa container queryt vaihtavat taulukon
  korttiriveiksi (≤ 620 px) ja lämpökartan ruudukoksi (≤ 520 px, `--n` = tutkintokertojen
  määrä). Pitkät URL-tekstit rivittyvät (`overflow-wrap:anywhere`). Älä palauta
  `min-width`iä tai `overflow-x:auto`-kääreitä. Testaa 320–414 px kaikilla aineilla.
- AI-työkalupakin päivitysagentti saa muuttaa vain `data/ai-tools.json`:ia. Osa-alueet
  (`id` ja järjestys) muutetaan vain käsin, ja validaattori estää yli `MAX_SWAPS` työkalun
  vaihdon kerralla. Vertailukohta on julkaistu versio (koirosvg.com/data/ai-tools.json,
  varalla origin/main), joten raja toimii myös Vercelin buildissa. Käsin tehtävä
  rakennemuutos: nosta `revision` samassa commitissa. Agentti ei saa koskea siihen.
  Älä löysää näitä rajoja, koska repo julkaisee suoraan.
- `vercel.json`:n `buildCommand` ajaa validaattorin jokaisessa deployssa. Epävalidi data
  kaataa deployn ja edellinen versio jää näkyviin. Älä poista sitä.
- `updated` = viimeisin onnistunut tarkistus. Sivu näyttää varoituksen, jos se on yli 5 pv
  vanha (eli ajastus on pysähtynyt). Älä kirjaa hintoihin määräaikaisia kampanjahintoja.
- Kotivalikon kortissa ei ole lukumääriä tarkoituksella, koska ne vanhenisivat automaattisissa
  päivityksissä.
- Työkalupakin linkit renderöidään vain `https://`-alkuisina (`safeUrl`, validaattori
  vaatii saman), ja kaikki teksti menee `esc()`:n läpi. Älä ohita näitä uusissa kentissä.
- `ai-tyokalut.html` hakee datan fetchillä, joten file:// ei toimi (sama kuin AI-oppaassa).
- **YO-harjoittelu, tekijänoikeus:** YTL:n tehtävätekstejä ja aineistoja ei saa julkaista, ja repo on
  julkinen. Harjoitussisällössä on vain omin sanoin kirjoitettu kuvaus, omat vihjeet ja ratkaisut sekä
  linkki alkuperäiseen. Jokainen uusi tiedosto ajetaan `check_overlap.py`:n läpi (6 sanan yhteiset
  jaksot = 0, paitsi lähdeviitteet). Validaattori hylkää yli 900 merkin `prompt`in.
- `yo-harjoittelu.html` jäsentää tehtävälistan `yo-tutka.html`:n `<script id="yo-data">`-lohkosta
  (sama kuin validaattori). Älä nimeä tai poista lohkoa. Sivu ei toimi file://-osoitteesta.
- localStorage-avain `yo-practice` ja arvion avainmuoto `aine|kerta|n|yksikkö` ovat yhteisiä
  `yo-harjoittelu.html`:lle ja `yo-tutka.html`:n `practiceScores()`:lle (myös sovellukset-kopiossa).
  Muuta molempia kerralla.
- Vastauskenttä (`.answer`) on tarkoituksella vaalea "paperi" tumman teeman keskellä, koska kaavat
  tallennetaan mustina SVG-kuvina (`<img>` ei peri `currentColor`ia). Samasta syystä MathJaxin
  `svg.fontCache` on `'none'` (kaavakuva on itsenäinen). Älä vaihda kumpaakaan.
- MathJaxin `ignoreHtmlClass` jättää `.answer`- ja `.eq-edit`-alueet pois, muuten käyttäjän
  kirjoittama `$` ladottaisiin kaavaksi.
- Vastaus-HTML kulkee aina `sanitize()`:n läpi (teksti, `br`, `div`, `img.eq` + `data-latex`,
  `img.shot` vain `data:image/…`). "Avaa tallennettu" lukee ulkopuolisen tiedoston, joten älä
  löysää sääntöä.
- digabi/MathQuill ei tunne kaikkia LaTeX-komentoja (esim. `\rightleftharpoons` kirjoittaa tyhjää).
  Tällaiset merkit syötetään `typedText`illä (`CHARS`-taulun tila 2). Testaa uusi painike
  katsomalla `mf.latex()`-tulos.
- Työkalupalkin napit estävät `mousedown`in oletustoiminnon, jotta kursori pysyy vastauksessa.
  Älä poista sitä, tai merkit ja kaavat lisätään väärään kohtaan.
- Äidinkielen kaksi koetta ovat samassa tiedostossa. Osioiden `group` erottaa ne omiksi
  simulaatioikseen, ja osion `examUrl`/`gradingUrl`/`minutes` ohittavat tiedoston yleiset.
- Kirjastot on lukittu versioihin: jQuery 3.7.1 (cdnjs), @digabi/mathquill 0.10.12 ja mathjax 3.2.2
  (jsdelivr). digabi-haara on sama kuin Abitissa ja Mafynetissä. Älä vaihda sitä perus-MathQuilliin.
  jQueryllä, MathQuillilla ja sen CSS:llä on SRI-tarkiste (`integrity`). Jos vaihdat version, laske
  tarkiste uudelleen, muuten selain estää kirjaston. MathJax ladataan vasta ensimmäisen kaavan kohdalla
  (`mjReady`), ja kaikki MathJax-kutsut kulkevat jonossa (`mjRun`), koska mhchem latautuu kesken ladonnan.
- Leveät kaavat 320 px:n näytöllä: MathJax 3 ei rivitä kaavoja. Siksi `.md`, `.unit` ja `.help` ovat
  `grid-template-columns:minmax(0,1fr)` ja `.md>*{min-width:0}`, rivinsisäisen kaavan SVG:llä on `max-width:100%`
  ja näkymättömällä `mjx-assistive-mml`:llä `max-width:100%`. Jos yksikin puuttuu, sivu levenee (testattu
  fysiikan ja kemian ratkaisuilla). Älä korjaa tätä `overflow-x:auto`-kääreellä.
- Apuvälinepaneelin laskimet (GeoGebra, Desmos) vievät näppäimistön fokuksen latautuessaan. Sivun
  latautuessa palautettu laskin odottaa siksi "Avaa"-napin painallusta (`showAid(id, restore)`).
- Koesimulaation vastaukset tallentuvat avaimella `koe|aine|kerta|n|yksikkö`, erillään harjoitusvastauksista.
  "Uusi yritys" poistaa ne. Arviot (`scores`) ovat yhteisiä, ja kertauslista etenee vain, kun kohta on
  erääntynyt (`r.due <= today()`), jotta arvion korjaaminen ei hyppää kertausvälejä yli.
