# koirosvg.com (repo koiro-svg/yo-tutka)

Mikä tämä on: koirosvg.com-sivuston julkaisurepo. Kotivalikko (`index.html`) ja työkalut:
AI-opas (`ai.html`: mallit, koodausagentit ja työkalut), YO-tutka (`yo-tutka.html`) ja sen harjoitusosio
YO-harjoittelu (`yo-harjoittelu.html`) sekä Hyppymittari. Repo on **julkinen**.

## Build & run
- Ei buildia. `python3 -m http.server` repon juuressa ja avaa `/ai.html`
  (AI-opas hakee `data/*.json`:n fetchillä, joten file:// ei toimi; `/ai`-polut ja redirectit vaativat Vercelin tai
  pienen palvelimen, joka tekee `cleanUrls`in ja `vercel.json`:n redirectit).
- Vercel julkaisee mainin automaattisesti; `vercel.json`:n `cleanUrls` tekee `/ai` ja `/yo-tutka` -polut, ja 308-redirectit
  ohjaavat vanhat `/ai-opas` → `/ai` ja `/ai-tyokalut` → `/ai?tab=tyokalut` (selain säilyttää #hashin, koska kohteessa ei ole omaa).
- Build ajaa vain tarkistukset: `validate_tools.py`, `validate_practice.py` ja `check_tokens.py`.

## Arkkitehtuuri
- Jokainen sivu on itsenäinen tiedosto (CSS/JS sisällä). Kaikki sivut käyttävät samaa tarkoituksella aina tummaa
  "tutka"-teemaa. **Yhteinen tokenilohko `/* koiro-tokens v2 */`** (fontit, värit, säteet, `kt-`-komponentit: välilehti,
  nappi, kenttä, tilarivi, huomautus, välähdys) on jokaisen sivun ensimmäisen `<style>`-lohkon alussa. Kanoninen kopio on
  `scripts/koiro-tokens.css`; `scripts/check_tokens.py` (buildissa, kaikki juuren `*.html`-sivut) kaataa deployn, jos kopio
  puuttuu tai eroaa (`--write` päivittää). Lohkossa ovat myös yhteiset perussäännöt (`box-sizing`, `:focus-visible`, `[hidden]`).
  Tokenit ovat `:where(:root)`issa, joten sivun oma `:root` voittaa (YO-sivut käyttävät vielä omiaan, tietosuoja ei). Fontit ovat
  omalla palvelimella (`fonts/`, latin-osajoukot, OFL, `fonts/OFL.md`), ei Google Fontsia. Kotivalikossa lisäksi
  canvas-tutka-animaatio. Työkalusivuilla on `← koirosvg.com`-paluulinkki (AI-oppaassa ja tietosuojassa `.crumb` mastheadissa,
  YO-sivuilla yläpalkin `.home`) – pidä se jokaisessa uudessa sivussa.
- **Kotivalikko (19.10.2026, julkinen-1…7):** kolme korttia (AI-opas `/ai`, YO-tutka, Hyppymittari) ja tutkan pisteet samoilla
  nimillä. Pisteet ovat oikeita `<a>`-linkkejä canvasin päällä (%-sijainti samasta kulma/säde-laskusta), kortin hover/fokus
  kääntää viivan sen pisteeseen ja pisteen hover korostaa korttia. AI-kortti hakee `data/ai-models.json`:sta yleiskategorian
  kärjen ja päivitysajan (haun epäonnistuessa ei mitään), ja tuore AI-piste "pingaa". YO-kortti lukee vain tämän selaimen
  `yo-practice`-avaimen (kerrattavat tänään + osaaminen) eikä koskaan kirjoita siihen. Haku (`/` tai ⌘K) lataa AI-datan vasta
  ensimmäisellä näppäilyllä (sama `ai-models.json`-haku kuin kortilla) ja linkittää `/ai`-sivulle raakanimellä (`#a-Cursor`,
  `#t-<osa-alue>-<nimi>`); id-muodon omistaa `ai.html` (`parseHash` slugittaa nimen), joten etusivulla ei ole kopiota. Puhelimella tutka on pieni otsikon vieressä.
  Canvas huomioi devicePixelRatio, piirtää renkaat kerran taustakanvaasille, kääntää valmiin säteen gradientin, ~30 fps,
  pysähtyy näkymättömänä (IntersectionObserver) ja reduced motionilla.
- **AI-opas `ai.html` (19.10.2026, julkinen-8…16; korvasi `ai-opas.html` ja `ai-tyokalut.html`):** välilehdet Mallit ·
  Koodausagentit · Työkalut, yksi haku kaikkiin (osumamäärät välilehdissä, `?q=` osoitteessa), "Mitä haluat tehdä?" -valinta
  (`TASKS`-kytkentätaulu sivun koodissa, ei datassa: kategoria ↔ osa-alue ↔ agentti), Uutta-kortti (45 pv uudet mallit + 3
  uusinta työkalumuutosta), hinta vs. älykkyys -hajontakaavio tehokkuusrajalla ja agenttien kuplakaavio (käsin kirjoitettu SVG,
  viewBox = piirretty leveys), "+"-vertailu (2–3 mallia tai agenttia, alapalkki + vertailutaulukko), puhelimella kortissa
  voittaja + sijat 2–3 ja "Näytä kaikki", osa-aluevalikko, mittarisanasto (`GLOSSARY`, ⓘ) ja Datan tila -lista (kolme lähdettä,
  `errors`-kentän kategoriat). Osoitteet: `#mallit[/ryhmä]`, `#koodausagentit`, `#tyokalut[/osa-alue]`, `#muutokset` ja
  korttien id:t `m-<kategoria>`, `a-<agentti>`, `t-<osa-alue>-<työkalu>`; vanhat ryhmä- (`#teksti`, `#video`…) ja osa-alue-ankkurit
  (`#markkinointi`…) toimivat. Linkitetty kortti, jonka suodatin tai haku piilottaa, tuodaan näkyviin ja välähtää.
  Piirretään vain aktiivinen välilehti (muut tyhjennetään, joten id:t ovat dokumentissa kerran), haku odottaa 120 ms,
  "+", "Näytä kaikki" ja tehtävävalinta päivittävät vain oman kohtansa, ja rankingit/kaaviopisteet/Uutta lasketaan kerran
  datan latauksessa (`derived`). Osoite luetaan yhdessä paikassa (`fromUrl`: alku ja `popstate`, joka laukeaa myös
  #-linkeistä; erillinen `hashchange` ajaisi kaiken kahdesti).
- AI-opas: `scripts/update_models.py` (stdlib) → `data/ai-models.json` →
  `ai.html` renderöi. GitHub Action `update-models.yml` joka toinen päivä,
  secret `AA_API_KEY`. Ks. README.
- Koodausagentit (AI-oppaan välilehti ja ankkuri `#koodausagentit`): `data/coding-agents.json`
  → `ai.html` (`agentsTab()`). Kolme rankingkorttia
  (`AGENT_CARDS`) lasketaan sivulla `aa`-tuloksista ja piirretään samalla `card()`-funktiolla kuin
  mallien kortit (`cat.fmt` muotoilee luvut). Jokaisella ryhmällä on `id`, ja `reveal()` näyttää
  `#ryhmä`-linkin kohteen, vaikka suodatin piilottaisi sen. Dataa päivittää työkalupakin rutiini,
  koska AA:n Coding Agent Index ei ole API:ssa.
- AI-työkalupakki: `data/ai-tools.json` → `ai.html`:n Työkalut-välilehti renderöi (fetch). Dataa
  päivittää ajastettu Claude-pilviagentti (routine) joka toinen päivä ohjeen
  `scripts/UPDATE_TOOLS.md` mukaan, ja `scripts/validate_tools.py` tarkistaa sen ennen
  committia. Ei API-avainta eikä GitHub Actionia.
- YO-tutkan käyttöliittymän pääversio on tämä repo (päätös 19.10.2026); datan lähde on `~/sovellukset/yo-tutka/`
  (data + koosta.py), jonka `index.html` on vain koonti- ja esikatselukopio; tänne tuodaan
  vain data README:n komennolla.
- **YO-tutka (19.10.2026, julkinen-17…24):** oikea head (ennen kääreen jäänne: tyylit ja title bodyssa), sivun `:root` vain
  tokenilohkosta poikkeavat (`--line-2`, kevät/syksy, `--h0…5`). Aineen yläosassa SVG-tutka (aiheet säteinä: ulompi alue
  todennäköisyys, sisempi oma osaaminen `yo-practice`-arvioista, säde suodattaa), valitun aiheen tietopaneeli rivin alla
  (kuvaus, esiintymiset kerroittain, perustelu, osaaminen, Harjoittele + Pikatesti), syvälinkit `#<aine>[/<aihe>]` historiaan
  (`pushState`, `popstate`), trendinuolet (painotettu vs. tasainen ≥ 10 %-yks., `TREND`), seuraavan kokeen laskuri (`EXAMS`,
  YTL:n alustava aikataulu, **päivitä joka kausi**; `validate_practice.py` tarkistaa avaimet ja varoittaa, kun kaikki päivät ovat
  menneet), tulostettava kertauslista (`#printlist`, `@media print`). Eyebrow lasketaan datasta. Paneelin runko piirretään kerran
  aineen/painotuksen vaihtuessa (`renderAll`); aihe, lajittelu ja "Näytä kaikki" piirtävät vain aiheet, tutkan ja kartan
  (`paintTopics`), haku ja aihe vain piilottavat tehtäviä ja päivittävät laskurit (`filterSessions`), joten hakukenttä ei koskaan
  tuhoudu. Kerrat rakennetaan kokonaan kerran aineen vaihtuessa, jotta selaimen oma haku (Ctrl+F) löytää kaikki tehtävät (katselmointi
  19.10.: laiskasti rakennetut rungot piilottivat ne). Vain käyttäjän oma avaus/sulkeminen muistetaan (`state.open`, summaryn klikkaus).
  Toisen välilehden pistemuutos piirtää vain pisteistä riippuvat osat ja vain, jos aineen pisteet muuttuivat (`rescore`). Kertauslistan
  tulostustyyli on voimassa vain napin kautta (`html.print-list`); Ctrl+P tulostaa sivun. `stats()` laskee yhdellä
  kierroksella molemmat todennäköisyydet (trendi = ero) ja on välimuistissa (aine | painotus | vain vahvistetut). DOM-järjestys on
  sama kaikilla leveyksillä ja puhelimelle sopiva (otsake → hallinnat → Harjoittele seuraavaksi → tutka → aiheet + kartta →
  kerrat → lähdetilanne); puhelimella 5 aihetta + "Näytä kaikki" ja ainevalikko.
- **YO-yläpalkki `<!-- yo-nav v1 -->`** (Tutka · Harjoittele · Kertaus (n) · Edistyminen · Tili): kanoninen kopio
  `scripts/yo-nav.html`, molemmissa YO-sivuissa identtisenä (`check_tokens.py` vertaa, `--write` kopioi). Sivut kertovat palkille
  `<html>`-attribuuteilla `data-yo-page`, `data-yo-subject` ja `data-yo-due`, ja palkki seuraa niitä `MutationObserver`illa (ei URL-
  jäsennystä eikä omaa reittitaulua). Kertausten "erääntynyt tänään" -sääntö on palkin `window.yoIsDue` (harjoittelun lista käyttää
  samaa). Palkki lukee `yo-practice`-avaimen vain latautuessa, `storage`-tapahtumassa (avain täsmää) ja bfcache-paluussa; harjoittelu
  julkaisee määrän muistista jokaisen tallennuksen jälkeen (`publishDue`). Linkit ovat `kt-tab`-tyylisiä (`aria-current=page`),
  cross-document View Transitions (`view-transition-name: yonav`, pois reduced motionilla). Harjoittelussa `#/kertaus` vie
  kertauslistaan; harjoittelun murupolusta poistettiin palkin kanssa päällekkäiset linkit.
- YO-harjoittelu (`/yo-harjoittelu`): Abitti-tyylinen vastauseditori (digabi/MathQuill +
  MathJax CDN:stä), vihjeet ja malliratkaisut, itsearvio, kertauslista, koesimulaatio ja
  apuvälinepaneeli (Mafy-taulukot, GeoGebra, Desmos upotettuina). Tehtävälistan se hakee
  `yo-tutka.html`:n `yo-data`-lohkosta fetchillä; harjoitussisältö on
  `data/practice/<aine>/<kerta>.json` (kirjoitusohje `scripts/PRACTICE_CONTENT.md`,
  tarkistus `scripts/validate_practice.py`, kopiointitarkistus `scripts/check_overlap.py`).
  Vastaukset (IndexedDB) ja arviot (localStorage `yo-practice`) ovat vain käyttäjän selaimessa.
  YO-tutka lukee samat arviot "Harjoittele seuraavaksi" -listaan.
  Pikatesti (`#/pika/<aine>/<aihe>`, myös tutkan listasta) arpoo aiheen tehtävän, ensisijaisesti
  arvioimattoman. Edistyminen (`#/edistyminen`) piirtää `S.history`-arviohistoriasta aineittain
  osaamisen ajan mittaan (käsin kirjoitettu SVG, ei kaaviokirjastoa) ja listaa koesimulaatioiden
  `sim.result`-pisteet. Lähteet itse hakeva kopiointitarkistus: `scripts/recheck_overlap.py`.
- Käyttäjätilit (`#/tili`, `/tietosuoja`): Supabase Auth (sähköposti + salasana, vahvistus- ja
  palautuslinkit Resendin SMTP:n kautta) ja Postgres-taulut `practice_state` + `practice_answers`
  (`supabase/schema.sql`, rivitason suojaus). Kirjautuneena `syncAll()` yhdistää palvelimen kopion
  paikalliseen (`mergeState`/`mergeAnswer`, samat säännöt kuin varmuuskopiossa) ja lähettää tuloksen.
  Muutokset lähtevät 3 s viiveellä (`onPersist`, `onAnswerSaved`). Tilit ovat piilossa, kunnes
  `SUPABASE`-vakiossa on osoite ja julkinen avain. Käyttöönotto: `supabase/README.md`.

- Hyppymittari (`/hyppymittari`): kopio `~/sovellukset/hyppymittari/`:sta (README:n rsync-komento),
  ei muokata täällä. Oma ulkoasu (lime) tarkoituksella – kameran päälle piirretty luuranko tarvitsee
  sen; `← koirosvg.com`-paluulinkki on mukana. MediaPipe Pose + mallit tiedostoina (~26 Mt).

## Known sharp edges (don't regress these)
- **Hyppymittari tarvitsee `vercel.json`:n CSP-otsakkeen `connect-src 'self'`.** Mukana tuleva
  MediaPipe lähettää käyttötilastoja `odml.pa.googleapis.com`:iin; otsake estää sen (sivu lupaa,
  ettei mitään lähetetä). Älä poista otsaketta äläkä laajenna sitä koko sivustolle ilman testiä.
- **Hyppymittari näkyy osoitteessa `/hyppymittari` ilman loppukauttaviivaa** (`trailingSlash:false`).
  Sivun `<head>`-skripti asettaa `<base href="/hyppymittari/">`, muuten suhteelliset polut
  (`jump-analysis.js`, `vendor/`, `models/`) osoittaisivat juureen. Älä vaihda `trailingSlash`ia.
- **YO-yläpalkkia muutetaan vain tiedostossa `scripts/yo-nav.html`**, sitten `python3 scripts/check_tokens.py --write` (build kaatuu,
  jos kopio eroaa). Uusi reitti tai sivu ei vaadi palkkiin muutosta: sivu asettaa `data-yo-page`/`data-yo-subject`.
- **YO-tutka ei koskaan kirjoita `yo-practice`-avaimeen** (yläpalkki ja tutka vain lukevat): Supabase-synkka ja `mergeState`
  omistavat sen harjoittelussa.
- YO-tutka on `yo-tutka.html`, ei `index.html` – README:n datansiirtokomento
  kirjoittaa siihen. Älä kopioi sovellukset-kansion `index.html`:ää tänne sokeasti.
- Artificial Analysisin ilmainen API vaatii näkyvän attribuution
  (linkki artificialanalysis.ai) – älä poista sitä ai.html:n footerista (näkyy kaikilla välilehdillä).
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
  `stale()` ai.html:ssä varoittaa, jos listan uusin malli on yli 180 päivää vanha.
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
- `validate_tools.py` tarkistaa myös `data/coding-agents.json`:n (max `MAX_AGENT_SWAPS` agenttivaihtoa
  kerralla, `aa`-luvut rajoissa). Rutiinin kehote (trig_012scGEYHeVknUS9bMSjQ7g6) sallii commitoida
  vain nämä kaksi tiedostoa. Jos lisäät rutiinille uuden datatiedoston, päivitä sekä
  `UPDATE_TOOLS.md` että rutiinin kehote, muuten agentti ei saa koskea siihen.
- Koodausagenttien `aa`-luvut ovat AA:n sivuilta (ei API:sta), joten footerin linkki
  artificialanalysis.ai/agents/coding-agents on lähdeviite. Älä poista sitä.
- `vercel.json`:n `buildCommand` ajaa validaattorin jokaisessa deployssa. Epävalidi data
  kaataa deployn ja edellinen versio jää näkyviin. Älä poista sitä.
- `updated` = viimeisin onnistunut tarkistus. Sivu näyttää varoituksen, jos se on yli 5 pv
  vanha (eli ajastus on pysähtynyt). Älä kirjaa hintoihin määräaikaisia kampanjahintoja.
- Kotivalikon kortissa ei ole lukumääriä tarkoituksella, koska ne vanhenisivat automaattisissa
  päivityksissä.
- Työkalupakin linkit renderöidään vain `https://`-alkuisina (`safeUrl`, validaattori
  vaatii saman), ja kaikki teksti menee `esc()`:n läpi. Älä ohita näitä uusissa kentissä.
- `ai.html` hakee datan fetchillä, joten file:// ei toimi.
- **Vanhat AI-osoitteet ovat 308-redirectejä ilman kohteen hashia:** selain säilyttää saapuvan #hashin, kun Locationissa ei
  ole omaa (`/ai-opas#koodausagentit` → `/ai#koodausagentit`). Älä lisää kohteeseen hashia (`/ai#tyokalut` korvaisi saapuvan);
  välilehti kulkee siksi `?tab=tyokalut`-parametrina, jonka sivu siirtää hashiin. Redirectit ajetaan ennen tiedostojärjestelmää.
  `<link rel="canonical">` = `/ai`.
- **AI-oppaan id:t ovat yhdessä hash-nimiavaruudessa:** mallien ryhmät, välilehdet, rankingkortit ja työkalujen osa-alueet
  (data) eivät saa törmätä, ja kortit ovat etuliitteellisiä (`m-`, `a-`, `t-`). `validate_tools.py` (buildissa) hylkää osa-alue-id:n,
  joka on `RESERVED_IDS`issa tai sisältää väliviivan (työkalukortti `t-<osa-alue>-<nimi>` jäsennetään ensimmäisestä viivasta).
  Uusi sivun ankkuri = lisää se `RESERVED_IDS`iin.
- **`.bar` on rankinglistan palkki**: hakupalkki on `.searchbar`. Sama luokkanimi kahdessa paikassa teki listan riveistä
  tahmeita taustalaatikoita (19.10.2026).
- **Fontit omalta palvelimelta (19.10.2026):** `fonts/` + `@font-face` tokenilohkossa. Unboundedin muuttuva fontti kattaa
  painot 600–800 ja JetBrains Monon 500–600, joten 500/400-pyynnöt piirtyvät lähimmällä painolla. Tietosuojaseloste
  kertoo, ettei Google Fontsia ladata; jos lisäät ulkoisen latauksen, päivitä seloste samassa commitissa.
- `*.txt` on `.gitignore`ssa (YTL-lähdetekstit), joten lisenssit ovat `.md`-tiedostoina (`fonts/OFL.md`).
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
  fysiikan ja kemian ratkaisuilla). Älä korjaa tätä `overflow-x:auto`-kääreellä. Samasta syystä `.wrap` on
  `overflow-wrap:anywhere` (pitkät kemialliset nimet otsikoissa), `.card` on `minmax(0,1fr)` ja `.row>label>select`
  on `width:100%` (valikko on muuten pisimmän vaihtoehtonsa levyinen).
- Apuvälinepaneelin laskimet (GeoGebra, Desmos) vievät näppäimistön fokuksen latautuessaan. Sivun
  latautuessa palautettu laskin odottaa siksi "Avaa"-napin painallusta (`showAid(id, restore)`).
- Varmuuskopion palautus (Edistyminen-sivu) lukee ulkopuolisen JSON-tiedoston: jokainen avain tarkistetaan
  (`UNIT_KEY`/`SIM_KEY`), luvut muunnetaan `num()`illa ja vastaukset kulkevat `clean()`in läpi ennen
  IndexedDB:hen tallennusta. Yhdistäminen pitää uudemman tiedon (`at`). Älä tallenna tiedoston arvoja
  sellaisenaan.
- **Käyttäjätilit:** `SUPABASE.url` ja `key` (publishable) ovat julkisia tarkoituksella. Tietojen suoja on
  `supabase/schema.sql`:n RLS-säännöissä: älä koskaan poista niitä äläkä laita `service_role`/secret-avainta
  sivuun, repoon tai GitHub-muuttujiin. Muutokset `schema.sql`:ään ja `supabase/email/`-pohjiin pitää ajaa/liittää
  Supabasen hallintapaneelissa käsin, sillä deploy ei vie niitä minnekään.
- Sähköpostilinkit tuovat `?token_hash=…&type=email|recovery` ja vaativat napin painalluksen ennen `verifyOtp`:ia,
  koska sähköpostipalvelujen linkkiskannerit avaavat linkit. Älä vaihda Supabasen oletuslinkkiin
  (`{{ .ConfirmationURL }}`): se ei toimi toisella laitteella eikä #-reitityksen kanssa.
- **Login CSRF:** sähköpostilinkki (`verifyOtp`) kirjaa sisään sen tilin, jonka linkki on – myös jonkun toisen.
  Siksi synkronointi pysyy pidossa (`held()`, `S.ui.holdUser`), kunnes käyttäjä vahvistaa näytetyn osoitteen,
  paitsi jos sama selain pyysi linkin (`S.ui.pendingEmail`). Ulkoa tulevat aikaleimat rajataan `capAt`illa
  (enintään vuorokausi tulevaisuuteen), muuten väärennetty aikaleima voittaisi jokaisen yhdistämisen.
- `onAuthStateChange`-kutsun sisällä ei saa odottaa supabase-js-kutsuja (lukkiutuu), joten synkronointi käynnistyy
  `setTimeout`illa. Kertausmerkinnöillä on `at` ja poistetut ovat `{gone, at}`-merkintöjä, ettei toinen laite
  palauta niitä. `ANSWER_MAX` (1 Mt) = `practice_answers_size` tietokannassa, ja kiintiö on 15 Mt per käyttäjä.
- Ilmainen Supabase-projekti nukahtaa viikon käyttämättömyyden jälkeen: `.github/workflows/supabase-keepalive.yml`
  pingaa päivittäin repomuuttujilla `SUPABASE_URL`/`SUPABASE_KEY`. supabase-js on lukittu (2.117.2) SRI-tarkisteella.
- `S.history` on ainoa paikka, jossa vanhat arviot säilyvät (`S.scores` pitää vain viimeisimmän). Älä tyhjennä
  sitä arvion korjauksen yhteydessä. Vanhoissa tallennuksissa se luodaan `scores`ista. Raja on 5 000 riviä.
- Koesimulaation vastaukset tallentuvat avaimella `koe|aine|kerta|n|yksikkö`, erillään harjoitusvastauksista.
  "Uusi yritys" poistaa ne. Arviot (`scores`) ovat yhteisiä, ja kertauslista etenee vain, kun kohta on
  erääntynyt (`r.due <= today()`), jotta arvion korjaaminen ei hyppää kertausvälejä yli.
