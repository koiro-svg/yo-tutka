# koirosvg.com (repo koiro-svg/yo-tutka)

Mikä tämä on: koirosvg.com-sivuston julkaisurepo. Kotivalikko (`index.html`) ja työkalut:
AI-opas (`ai.html`: mallit, koodausagentit ja työkalut), YO-tutka (`yo-tutka.html`) ja sen harjoitusosio
YO-harjoittelu (`yo-harjoittelu.html`), Hyppymittari ja Visakaksintaisto (`visa.html`). Repo on **julkinen**.

## Build & run
- Ei buildia. `python3 -m http.server` repon juuressa ja avaa `/ai.html`
  (AI-opas hakee `data/*.json`:n fetchillä, joten file:// ei toimi; `/ai`-polut ja redirectit vaativat Vercelin tai
  pienen palvelimen, joka tekee `cleanUrls`in ja `vercel.json`:n redirectit).
- Vercel julkaisee mainin automaattisesti; `vercel.json`:n `cleanUrls` tekee `/ai` ja `/yo-tutka` -polut, ja 308-redirectit
  ohjaavat vanhat `/ai-opas` → `/ai` ja `/ai-tyokalut` → `/ai?tab=tyokalut` (selain säilyttää #hashin, koska kohteessa ei ole omaa).
  Lyhyt osoite `/yo` → `/yo-tutka` on 307 (ks. sharp edges).
- Build ajaa vain tarkistukset: `validate_tools.py`, `validate_practice.py`, `check_tokens.py`, `yo_index.py` ja `validate_visa.py`.

## Arkkitehtuuri
- Jokainen sivu on itsenäinen tiedosto (CSS/JS sisällä). Kaikki sivut käyttävät samaa tarkoituksella aina tummaa
  "tutka"-teemaa. **Yhteinen tokenilohko `/* koiro-tokens v2 */`** (fontit, värit, säteet, `kt-`-komponentit: välilehti,
  nappi, kenttä, tilarivi, huomautus, välähdys, sivustohaun osumalista `kt-hits`) on jokaisen sivun ensimmäisen `<style>`-lohkon alussa. Kanoninen kopio on
  `scripts/koiro-tokens.css`; `scripts/check_tokens.py` (buildissa, kaikki juuren `*.html`-sivut) kaataa deployn, jos kopio
  puuttuu tai eroaa (`--write` päivittää). Lohkossa ovat myös yhteiset perussäännöt (`box-sizing`, `:focus-visible`, `[hidden]`).
  Tokenit ovat `:where(:root)`issa, joten sivun oma `:root` voittaa (YO-sivut käyttävät vielä omiaan, tietosuoja ei). Fontit ovat
  omalla palvelimella (`fonts/`, latin-osajoukot, OFL, `fonts/OFL.md`), ei Google Fontsia. Kotivalikossa lisäksi
  canvas-tutka-animaatio. Työkalusivuilla on `← koirosvg.com`-paluulinkki (AI-oppaassa ja tietosuojassa `.crumb` mastheadissa,
  YO-sivuilla yläpalkin `.home`) – pidä se jokaisessa uudessa sivussa.
- **Kotivalikko (19.10.2026, julkinen-1…7):** neljä korttia (AI-opas `/ai`, YO-tutka, Hyppymittari, Visakaksintaisto) ja tutkan pisteet samoilla
  nimillä. Pisteet ovat oikeita `<a>`-linkkejä canvasin päällä (%-sijainti samasta kulma/säde-laskusta), kortin hover/fokus
  kääntää viivan sen pisteeseen ja pisteen hover korostaa korttia. AI-kortti hakee `data/ai-models.json`:sta yleiskategorian
  kärjen ja päivitysajan (haun epäonnistuessa ei mitään). Pisteen rengas kertoo sisällön tuoreuden (julkinen-5: täysi ympyrä
  = juuri päivitetty, kutistuu log-asteikolla ~puolessa vuodessa tyhjäksi; alle 2 pv vanha piste "pingaa"; tooltip "päivitetty N
  sitten"): AI `ai-models.json`:n `updated`, YO kortin `data-yo-built` (datan koontipäivä, `yo_index.py` pitää sen samana kuin
  `yo-tutka.html`:n `YO_BUILT`). Hyppymittarilla ei ole rehellistä päivityspäivää (sovellus, ei päivittyvää dataa), joten sen
  piste on neutraali (ei rengasta). YO-kortti lukee vain tämän selaimen `yo-practice`-avaimen (kerrattavat tänään + osaaminen)
  eikä koskaan kirjoita siihen; kun kertauksia on erääntynyt, kortti vie suoraan kertauskierrokseen `/yo-harjoittelu#/kertaus`.
  Haku (`/` tai ⌘K) on yhteinen YO-yläpalkin kanssa: `site-search.js` (ES-moduuli, ainoa sivujen yhteinen skriptitiedosto)
  ladataan `import()`illa ensimmäisellä näppäilyllä, ja se hakee datan ensimmäisellä haulla (etusivu antaa oman
  `ai-models.json`-hakunsa, joten pyyntö tehdään kerran): mallit, agentit, työkalut ja YO-aineet/-aiheet (`data/yo-topics.json`
  → `/yo-tutka#<aine>/<aihe>`). AI-linkit kulkevat raakanimellä (`#a-Cursor`, `#t-<osa-alue>-<nimi>`); id-muodon omistaa
  `ai.html` (`parseHash` slugittaa nimen), joten etusivulla ei ole kopiota. Puhelimella tutka on pieni otsikon vieressä.
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
  #-linkeistä; erillinen `hashchange` ajaisi kaiken kahdesti). Haku ja tyyppisuodatin ovat kyselyssä (`?q=…&kind=automatisoi`,
  `urlFor`, julkinen-15): tyyppivalinta on oma historiamerkintänsä, ja haku kirjautuu historiaan yhtenä merkintänä, kun
  kirjoittaminen asettuu (1 s) tai Enterillä (`commitQ`), joten Takaisin käy haut ja suodattimet läpi.
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
  (vain `data/*.json` + `koosta.py`, ei käyttöliittymäkopiota). `koosta.py` kirjoittaa datan suoraan tämän repon
  `yo-tutka.html`:n `yo-data`-lohkoon ja `YO_BUILT`-päivään ja ajaa `scripts/yo_index.py --write`:n (README).
- **YO-tutka (19.10.2026, julkinen-17…24):** oikea head (ennen kääreen jäänne: tyylit ja title bodyssa), sivun `:root` vain
  tokenilohkosta poikkeavat (`--line-2`, kevät/syksy, `--h0…5`). Aineen yläosassa SVG-tutka (aiheet säteinä: ulompi alue
  todennäköisyys, sisempi oma osaaminen `yo-practice`-arvioista, säde suodattaa), valitun aiheen tietopaneeli rivin alla
  (kuvaus, esiintymiset kerroittain, perustelu, osaaminen, Harjoittele + Pikatesti), syvälinkit `#<aine>[/<aihe>]` historiaan
  (`pushState`, `popstate`), trendinuolet (painotettu vs. tasainen ≥ 10 %-yks., `TREND`), seuraavan kokeen laskuri (`EXAMS`,
  YTL:n alustava aikataulu, **päivitä joka kausi**; `validate_practice.py` tarkistaa avaimet ja varoittaa, kun kaikki päivät ovat
  menneet), tulostettava kertauslista (`#printlist`, `@media print`). Eyebrow lasketaan datasta. Paneelin runko piirretään kerran
  aineen vaihtuessa (`renderAll`); aihe, lajittelu ja "Näytä kaikki" piirtävät vain aiheet, tutkan ja kartan
  (`paintTopics`), haku ja aihe vain piilottavat tehtäviä ja päivittävät laskurit (`filterSessions`), joten hakukenttä ei koskaan
  tuhoudu. Painotus ja "Vain vahvistetut" eivät piirrä runkoa uudelleen (julkinen-23): `restat` laskee tilastot ja `paintStats`
  päivittää luvut, tyyppipalkit ja taulukon paikallaan. Aiherivit ovat avaimellisia (`rows`: aihe-id → `<tr>`, `fillRow`) ja niitä
  siirretään vain järjestyksen muuttuessa (`moveTo`: `moveBefore`, jos selain tukee), lämpökartta ja tutka rakennetaan uudelleen
  vain datan tai järjestyksen muuttuessa (`drawn`), muuten vain korostus seuraa aihetta; tehtävämäärä- (`.bar`),
  todennäköisyys- (`.pbar`) ja tyyppipalkit animoivat leveytensä (ei reduced motionilla), ja avatut kerrat, skrollaus ja fokus
  säilyvät. Tämän sivun linkit `#`-osoitteeseen (yläpalkin haun osumat) käsitellään paikallaan kuten Takaisin, ja aiheen
  syvälinkki vierittää rivin näkyviin (`showTopic`). Kerrat rakennetaan kokonaan kerran aineen vaihtuessa, jotta selaimen oma haku (Ctrl+F) löytää kaikki tehtävät (katselmointi
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
  kertauskierrokseen; harjoittelun murupolusta poistettiin palkin kanssa päällekkäiset linkit. Palkin Haku-nappi tai ⌘K (Apple) / Ctrl+K (muut)
  avaa palkin alle saman sivustohaun kuin etusivulla (`site-search.js`, julkinen-6; ei `/`-pikanäppäintä, koska sitä kirjoitetaan
  kaavoihin); Enter "klikkaa" ensimmäistä osumaa, jotta YO-tutkan oma linkinkäsittely ehtii, Esc sulkee.
- **YO-harjoittelu (19.10.2026, julkinen-25…33):** kertauskierros `#/kertaus` (tänään erääntyneet kohdat peräkkäin, sama määrä kuin listassa
  ja palkissa, kohta tunnistetaan yksikköä myöten; tyhjä kierros vaihtaa osoitteen pois `#/kertaus`ista, ettei synkan uudelleenpiirto
  aloita kierrosta; kierros on vain muistissa tällä käynnillä, ei `S`:ssä, joten se ei vanhene eikä siirry muihin välilehtiin; kertauspalkki
  tehtävänäkymässä, `route()` merkitsee palkkiin "Kertaus"), etusivulla päivän tavoite (1/3/5, `S.ui.goal`; tänään arvioidut eri kohdat, korjattu arvio lasketaan kerran) ja putki
  `S.history`-aikaleimoista (`historyDays()`: päiväkooste, jota myös kalenteri käyttää; välimuisti tyhjenee jokaisessa `persistLocal`issa ja toisen välilehden
  tallennuksessa, koska 5 000 rivin rajalla historia muuttuu pituuden pysyessä samana; kalenterikin laskee eri kohdat), "Harjoittele seuraavaksi" (sama todennäköisyys × heikkous kuin tutkassa), tehtävälistan haku (120 ms viive), aihe- ja
  tilasuodattimet (rivien tiedot JS-taulukossa `rowInfo`, ei data-attribuuteissa; suodattimet säilyvät saman aineen
  uudelleenpiirrossa `listState`issa, esim. taustasynkan jälkeen) ja tilapalkki rivin reunassa (`scoreCls`), Edistyminen-sivulla 16 viikon harjoituskalenteri (päivän napautus listaa tehtävät),
  koesimulaation arvosana-arvio (`GRADES`: YTL:n julkaisemat pisterajat 2021S–2026K kaikille yhden kokeen aineille, pelkät luvut;
  2026S puuttuu, kunnes YTL julkaisee sen marraskuussa; äidinkielelle ei arviota, koska sillä on kaksi erillistä koetta), vastauksen alla tallennustila ("Tallennettu tähän laitteeseen 12.03 ✓", kirjautuneena synkan tila,
  yksityisen ikkunan varoitus; synkan tila on vastauskohtainen: `acct.synced` = palvelimella olevan kopion aika (`pushAnswer`, `mergeAnswer`,
  `syncAll`), muuten "synkronoidaan pian" tai virhetila; `markSaved` asettaa ajan, `paintSaved` vain piirtää; rivi ei ole aria-live) ja vihjeportaat (avatut askeleet merkitty, "Käytit 2 vihjettä" lasketaan portaista, ei tallenneta).
  Lataus: `<link rel=preload href=/yo-tutka as=fetch crossorigin>` (attribuutit vastaavat `loadMeta`n fetchiä, muuten haku tehdään
  kahdesti) ja luurankokortit ennen dataa.
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
  ei muokata täällä. Oma ulkoasu tarkoituksella ("stadion yöllä": tartan-punainen toiminnoille, LED-keltainen vain tuloksille,
  valkoinen luuranko kameran päällä); `← koirosvg.com`-paluulinkki on mukana. MediaPipe Pose + mallit tiedostoina (~26 Mt).
  19.10.2026 lähtien myös asennettava verkoton sovellus (`sw.js`, `manifest.webmanifest`, `icons/`), sarjatila, kaukonäyttö,
  kehityskäyrä tavoitteineen, toisto, vertailu, jakokuva ja varmuuskopio – kaikki laitteella, ei verkkokutsuja.
- **Visakaksintaisto (`/visa`, 9.11.2026):** 1v1-tietovisat ("kirjoita kaikki" aikarajalla), huone linkillä tai 4 merkin koodilla (`#ABCD`), ei tiliä, enintään 8
  pelaajaa, chat. Pelitavat `parallel` (omat listat) ja `race` (yhteinen lista, ensimmäinen saa). Yksi tiedosto + `data/visa.json` (maat pääkaupunkeineen ja visat; maavisat johdetaan
  `countries`-taulusta, `buildItems`), `scripts/validate_visa.py` buildissa. Reaaliaika: Supabase Realtime Broadcast + Presence kanavalla `visa:<koodi>` samassa projektissa kuin
  tilit. Pelit, nimimerkit ja chat eivät tallennu palvelimelle; ainoa pysyvä tieto on Suosituimmat-listan anonyymi päiväkohtainen laskuri `visa_plays`. Vetäjä = aikaisin `joined`, ja rooli siirtyy automaattisesti seuraavalle. Vetäjä ratkaisee kilpajaon ja lähettää lopputuloksen;
  voitot ja ennätykset vain selaimessa (`visa-v1`). Sisältö on omaa: faktoja omin nimin, ei JetPunkin visatekstejä, nimeä tai ulkoasua.
  Muodot (`format`): `list` (kirjoita kaikki), `flags` (sama moottori, vihjeenä lippukuva `flags/<iso>.svg`), `map` ja `choice` (yksi kohde kerrallaan, `target()`, järjestys `seq`:stä siemennetty). Visat ovat `data/visa.json`:ssa ja
  paketeissa `data/visa/<paketti>.json` (kirjoitusohje `scripts/VISA_CONTENT.md`; paketti pitää lisätä `packs`-listaan). Lobbyssa haku, aihe- ja muotosuodatin, arvonta ja Suosituimmat (`visa_trending`, näkyy vasta kun `supabase/schema.sql`:n visa-osa on ajettu).
  Lippukuvat: flag-icons (MIT, `flags/LICENSE.md`). Kartta `data/visa-map.json`: Natural Earth 50m (public domain), projisoitu ja yksinkertaistettu kertaluonteisella skriptillä; `b` = rajat, `c` = merkkipallo liian pienelle maalle.

## Known sharp edges (don't regress these)
- **Ilme v2 (10.11.2026): sivun kuva, sävy ja syvyys tulevat tokenilohkosta.** Jokaisen juurisivun `<html data-page="…">`
  (koti, ai, yo-tutka, yo-harjoittelu, visa, tietosuoja) valitsee `--kt-tone`n ja `--kt-hero`n (`img/hero/<sivu>[-s].webp?v=1`,
  ≤ 700 px = `-s`), ja `html[data-page] body{background:…}` maalaa kuvan sivun yläosaan ja häivyttää sen `--bg`:hen; sivun oma
  `body{background}` häviää spesifisyydellä. Kuva on taustassa, ei elementissä (ei asettelua, ei tekstin päällä). Teksti voittaa
  kuvan: kirkas kuva = nosta sivun `--kt-veil`iä. Kotivalikon kortit käyttävät samoja `-s`-kuvia (`.tool[data-blip]{--art}`) ja
  kortin sävyä `--tone`. Kuvat: Higgsfield (GPT Image 2.6), kehotteet ja `derive.sh` ovat `~/projects/koirosvg-uudistus/ilme-2026-11/art/`
  (ei tässä repossa); kuvissa ei ole tekstiä, kasvoja eikä henkilötietoja. `img/` on välimuistissa vuoden (`vercel.json`), joten
  muutettu kuva = nosta `?v=` tokenilohkossa ja `index.html`:n korteissa. Uusi juurisivu = `data-page` + rivi tokenilohkoon +
  `python3 scripts/check_tokens.py --write`. Hyppymittari on kopioitu sovellus omalla ilmeellään: sitä tämä ei koske.
- **Visan vastaushyväksyntä (`longerAvailable`):** vastaus, joka on toisen vielä löytämättömän vastauksen alku, odottaa 700 ms tai Enteriä ("Niger"/"Nigeria"), myös saman kohteen pidemmän nimen
  kohdalla ("Saturn"/"Saturnus"). Muuten sanan loppu jää kenttään ja seuraavat vastaukset eivät enää täsmää.
- **Karttavisan zoom käyttää persentiilejä (`buildMap`):** Venäjä ja merentakaiset alueet zoomaisivat muuten maanosan koko maailmaksi.
- **Vastausmerkinnät (`claims`) vetäjältä tai pelaajalta itseltään:** vetäjän uudelleenlatauksen aikana sijainen myöntää vastauksia, joten muulta kuin vetäjältä kelpaavat vain lähettäjän omat. `applyClaim` on ensimmäinen voittaa, ja lopullisen tilan kertoo vetäjän `end`.
- **Karttakohde ei saa jäädä rajauksen ulkopuolelle:** `buildMap` laajentaa näkymää, jos saarivaltio jäisi persentiilien ulkopuolelle. Muuten täyttä tulosta ei voisi saada.
- **Lippujen järjestys on sekoitettu (`G.order`), ei aakkosissa:** aakkosjärjestys antaisi vastaukset vihjeenä.
- **`replaceChildren` on natiivi eikä suodata arvoja:** ehdolliset lapset menevät `fill()`in kautta, muuten sivulle tulostuu sana "false".
- **`norm()` on kahdessa paikassa:** `visa.html` ja `scripts/validate_visa.py` (yhden visan kahdella kohteella ei saa olla samaa normalisoitua vastausta). Muuta molempia kerralla.
- **Visan viestit ovat toisten selainten syötettä:** `onMessage`-polku tarkistaa indeksit, ajat ja nimet, ja kaikki teksti menee `textContent`in kautta (`h()`), ei `innerHTML`:llä. Pelin tulokset
  perustuvat pelaajien luottamukseen (kaverien kesken), joten rankingia ei saa rakentaa niiden päälle.
- **Broadcast ei takaa toimitusta:** visa korjaa itsensä (`repair`: absoluuttinen tila 3 s välein tilan muuttuessa ja 15 s välein muuten, koska jokainen broadcast kuluttaa Realtime-kiintiötä kerran per vastaanottaja; odottavat claimit uudelleen, `end` kolmesti, vahtiajastimet ajan loppuessa). Älä poista näitä, vaikka testissä kaikki viestit menisivät perille.
- **Uusi pelaaja sijoittuu aina muiden jälkeen (`track`):** `track` odottaa ensimmäistä presence-synkkaa (varalla `TRACK_WAIT_MS`), muuten väärässä ajassa oleva laite veisi vetäjän roolin. `joined`-arvo säilyy vain uudelleenlatauksen yli, ja `leaveRoom` tyhjentää sen.
- **Vetäjän uudelleenlataus:** ladattu vetäjä on ilman peliä, joten sen `hello`on vastaa myös se, joka pitää lähettäjää vetäjänä, ja ensimmäinen snapshot kelpaa keneltä tahansa (`R.synced`). Vetäjä lähettää aloituksen jälkeen snapshotin kahdesti, koska muuten `start`in hävittänyt pelaaja jäisi koko pelin ulkopuolelle.
- **Poissaolo ei ole poistuminen:** `maybeFinish` odottaa `GONE_GRACE_MS`, ennen kuin presencestä kadonnut pelaaja lakkaa estämästä pelin loppua; muuten uudelleenlataus päättäisi pelin.
- **Nimimerkit ovat avaimia vain `h2hKey`-etuliitteellä:** `constructor` tai `__proto__` kaatoi muuten `applyEnd`in ja jäädytti tulosnäkymän.
- **Monistettu välilehti perii `sessionStorage`n:** `BroadcastChannel`-tarkistus (`TAB_CHECK_MS`) antaa sille uuden pelaaja-id:n, ja uudelleenlataus säilyttää vanhan.
- **Hyppymittari tarvitsee `vercel.json`:n CSP-otsakkeen `connect-src 'self'`.** Mukana tuleva
  MediaPipe lähettää käyttötilastoja `odml.pa.googleapis.com`:iin; otsake estää sen (sivu lupaa,
  ettei mitään lähetetä). Älä poista otsaketta äläkä laajenna sitä koko sivustolle ilman testiä.
- **Hyppymittarin service worker tarvitsee `vercel.json`:n `Service-Worker-Allowed: /hyppymittari` -otsakkeen** (`/hyppymittari/sw.js`):
  sivu on `/hyppymittari` ilman kauttaviivaa, eli `sw.js`:n oletusalueen `/hyppymittari/` ulkopuolella, joten se rekisteröidään
  alueella `/hyppymittari`. Ilman otsaketta rekisteröinti epäonnistuu hiljaa (sovellus toimii verkossa, ei verkotta).
  `Cache-Control: no-cache` pitää päivitykset tuoreina. CSP-otsake koskee myös workeria (`connect-src 'self'`), ja se hakee vain
  omasta osoitteesta.
- **Hyppymittari näkyy osoitteessa `/hyppymittari` ilman loppukauttaviivaa** (`trailingSlash:false`).
  Sivun `<head>`-skripti asettaa `<base href="/hyppymittari/">`, muuten suhteelliset polut
  (`jump-analysis.js`, `vendor/`, `models/`) osoittaisivat juureen. Älä vaihda `trailingSlash`ia.
- **YO-yläpalkkia muutetaan vain tiedostossa `scripts/yo-nav.html`**, sitten `python3 scripts/check_tokens.py --write` (build kaatuu,
  jos kopio eroaa). Uusi reitti tai sivu ei vaadi palkkiin muutosta: sivu asettaa `data-yo-page`/`data-yo-subject`.
- **YO-tutka ei koskaan kirjoita `yo-practice`-avaimeen** (yläpalkki ja tutka vain lukevat): Supabase-synkka ja `mergeState`
  omistavat sen harjoittelussa.
- **`yo-tutka.html`:n `yo-data`-lohkoa ja `YO_BUILT`-päivää kirjoittaa vain `~/sovellukset/yo-tutka/koosta.py`**, ja niistä
  johdetaan `data/yo-topics.json` (haku) ja `index.html`:n `data-yo-built` (tutkan tuoreus). `scripts/yo_index.py` (buildissa)
  kaataa deployn, jos ne eroavat (`--write` päivittää; koosta.py ajaa sen). Koosta.py ei vaihda päivää, jos data ei muuttunut,
  joten tuoreusrengas kertoo datan oikean iän.
- **Hyppymittarin tutkapiste on tarkoituksella neutraali** (ei tuoreusrengasta): sillä ei ole rehellistä päivityspäivää
  (`sw.js`:n `VERSION` on välimuistiversio, tiedostojen mtime on checkoutin aika). Älä keksi sille päivää.
- **`/yo` → `/yo-tutka` on 307 (`permanent:false`) tarkoituksella**: lyhyt osoite voi myöhemmin osoittaa muualle, ja selain
  välimuistittaisi 308:n pysyvästi. Vercel välittää kyselyn kohteeseen, ja selain säilyttää #hashin, koska kohteessa ei ole omaa.
- **`site-search.js` on ainoa sivujen yhteinen skriptitiedosto** (etusivu ja YO-palkki, `import()`, ei buildia). Sen
  osumalinkit ovat raakoja (`/ai#a-<nimi>`, `/yo-tutka#<aine>/<aihe>`): sivut omistavat id-muotonsa.
- **Sivustohaun katselmoinnin korjaukset (19.10.2026):** epäonnistunut datahaku nollaa indeksin, joten seuraava haku yrittää
  uudelleen (muuten YO-aiheet puuttuivat koko sivun eliniän). Enter seuraa vain nykyisen haun (`hits.dataset.q`) ensimmäistä
  oikeaa osumaa, ei "Ei osumia" -rivin AI-opas-linkkiä eikä edellisen haun osumaa. YO-palkin pikanäppäin on Applella vain ⌘K,
  koska Macin Ctrl+K poistaa tekstikentässä rivin loppuun (vastauseditori). Haku-napin avoin tila tarvitsee valitsimen
  `.yonav .kt-tab.find[aria-expanded=true]`, muuten `.kt-tab:not(:hover)…`-sääntö voittaa ja reunus katoaa.
- **YO-tutkan `#`-linkit ja latauksen vieritys:** `applyHash` ajaa lopuksi `syncUrl(true)`, ettei tuntematon aine/aihe jää
  osoitteeseen. Sivu vierittää aiheen riviin vain saapuvasta linkistä (`navigation.type === 'navigate'`), ei uudelleenlatauksessa
  eikä Takaisin-napilla, jolloin selain palauttaa vierityksen.
- **YO-tutkan aihetaulukkoa ei piirretä `innerHTML`:llä uudelleen suodattimen vaihtuessa** (julkinen-23): rivit ovat
  avaimellisia ja `renderAll` nollaa `rows`/`drawn` vain aineen vaihtuessa (eri aineilla voi olla sama aihe-id). Siirretty rivi
  voi menettää fokuksen, joten `keepFocus` palauttaa sen myös silloin, kun elementti on yhä sivulla.
- **AI-oppaan haku ei kirjoita historiaan joka näppäilyllä** (julkinen-15): `commitQ` vertaa osoitteen `q`:ta `ui.q`:hon ja
  tekee yhden `pushState`n; `fromUrl` tyhjentää odottavat ajastimet, ettei Takaisin-napin jälkeen kirjaudu vanha haku.
- Artificial Analysisin ilmainen API vaatii näkyvän attribuution
  (linkki artificialanalysis.ai) – älä poista sitä ai.html:n footerista (näkyy kaikilla välilehdillä).
- `update_models.py` säilyttää epäonnistuneen kategorian vanhan datan; älä muuta
  sitä kirjoittamaan tyhjää listaa virheen sattuessa.
- Tekstikategoriat ovat `BENCH`-taulussa (update_models.py). Jos testiä ei löydy, lista jää
  tyhjäksi ("Ei dataa vielä") – älä korvaa sitä toisella mittarilla hiljaa.
- `coverage` = osuus top 20 -malleista, joilla on testin tulos. Alle 0,5 → sivulla varoitus.
- AA poisti `/api/v2/data/*`:n 4.11.2026 (410 Gone). Ilmaiset osoitteet ovat `…/models/free`: niissä ei ole yksittäisiä testejä,
  sekoitettua hintaa eikä mediamallien julkaisupäiviä. Sekoitettu hinta lasketaan itse (`blended`, 3:1). Coding- ja Agentic-indeksit
  ovat aina null, joten koodausmallien listaa ei ole (koodaukseen: Koodausagentit-välilehti). `data/media-seen.json` muistaa kategorioittain, milloin mediamalli
  nähtiin ensi kerran (`seen`, UUSI-merkki); kategorian ensimmäinen haku kirjoittaa tyhjät päivät, ettei kaikkia sen malleja merkitä uusiksi.
  Tyhjä vastaus ei saa korvata listaa, jossa on dataa (`fresh`-silmukka).
  Yksi päivitysajo kuluttaa noin 13 pyyntöä ja ilmaiskiintiö on 100 / 24 h: älä aja workflow'ta testiksi montaa kertaa päivässä (429 → osa listoista jää vanhaan).
- API-avain vain GitHub-secretissä. Repo on julkinen.
- Samasta mallista tulee API:sta monta versiota ("Claude Opus 5.5 (Adaptive Reasoning, Max
  Effort…)"). `item()` pilkkoo sulkeiden edestä ja `top()` pitää vain parhaan version –
  muuten yksi malli täyttää koko listan.
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
  `yo-harjoittelu.html`:lle, `yo-tutka.html`:n `practiceScores()`:lle, YO-palkille ja etusivun YO-kortille.
  Muuta kaikkia kerralla.
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
- **YO-harjoittelun työkalupalkki rivittyy** (ei vaakaskrollia): 19 yleisintä merkkiä näkyy aina, loput "Lisää merkkejä" -napin
  takana (`.rare`, `COMMON_CHARS`). Korkeus riippuu leveydestä, joten `ResizeObserver` ajaa `syncToolbarHeight`in (muuten sticky-osat
  jäävät palkin alle ikkunaa kavennettaessa). Kosketusnäytöllä palkki on alhaalla näppäimistön yläpuolella (`visualViewport`, `placeToolbar`),
  `--toolbar-h` on silloin 0 ja sivulle tulee alapehmuste; napit 40 px. Napit estävät yhä `mousedown`in oletuksen.
- **Ainoa sallittu sisäkkäinen/kiinteäkorkuinen alue on apuvälinepaneeli** (`.aids`: GeoGebra/Desmos-kehykset tarvitsevat kiinteän
  korkeuden; puhelimella 68vh alapaneeli, jonka "Muut"-välilehti voi vieritä). Näyttökaavat eivät enää vieri sivuttain vaan
  kutistuvat sarakkeeseen kuten rivinsisäiset. Kelluva Apuvälineet-nappi saa sivulle alapehmusteen alle 1100 px:ssä.
- **`GRADES` päivitetään käsin**, kun YTL julkaisee uuden kerran pisterajat (pelkät luvut, ei YTL:n tekstiä), ja vain YTL:n omalta
  pisterajasivulta (ylioppilastutkinto.fi/…/pisterajat/pisterajat-<kausi>-<vuosi>; syksyn sivun osoitteessa voi olla pääte, esim.
  `-syksy-2025-0`). Englanti = pitkä oppimäärä (max 299), muut 120. Älä arvioi tai interpoloi puuttuvaa kertaa: rivi puuttuu, kunnes YTL
  julkaisee sen, ja sivu sanoo "pisterajoja ei ole vielä taulukossa". Yksi kerta per rivi, lähdesivu rivin lopussa
  (`'2026K': { aine: [L, E, M, C, B, A], … },  // https://www.ylioppilastutkinto.fi/fi/tutkinnon-suorittaminen/pisterajat/…`):
  `validate_practice.py` (buildissa) jäsentää rivit ja vaatii oikeat aine- ja kerta-id:t, kuusi laskevaa lukua, L-rajan ≤ kokeen maksimi
  (harjoitussisällön osioista laskettuna kuten sivu) ja YTL:n lähdeosoitteen, ja hylkää kahden kokeen aineen (osioilla `group`);
  sivukin ohittaa arvion ryhmäsimulaatiossa.
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
- **Kosketussäännöt ovat tokenilohkossa (10.11.2026):** `@media (pointer:coarse)` nostaa kentät (`.kt-input`, `select`, `textarea`) 16 px:iin (iOS zoomaa muuten), `.kt-tab`in 44 px:iin ja `.kt-btn.sm`in 40 px:iin. Työpöydän tiheys ei muutu. Sivun oma luokkasääntö (`font:inherit`, `font-size`) voittaa yhä, joten uusi kenttä tarkistetaan kosketusemulaatiolla.
- **`site-search.js`:n `PAGES` = sivuston omat sivut haussa**, mukana myös silloin kun datahaut epäonnistuvat. Uusi juurisivu = rivi `PAGES`iin ja `sitemap.xml`:ään. `hitsHtml(found, q)` pysyy kaksiparametrisena (YO-palkki); datavirhe kulkee `found.partial`-lippuna, ja silloin näytetään 'Haku ei saanut kaikkea dataa', ei 'Ei osumia'.
- **`404.html` on juurisivu:** siinä on tokenilohko ja `data-page="404"` (käyttää kotivalikon kuvaa), ja `check_tokens.py` vaatii lohkon. Vercel tarjoaa sen mistä tahansa polusta, joten kaikki sen osoitteet ovat absoluuttisia (`/ai`, ei `ai`).
- **`robots.txt` on `.gitignore`n `*.txt`-säännön alla:** tiedosto pitää lisätä `git add -f robots.txt` tai poikkeuksella `!robots.txt`, muuten se ei päädy deployhin.
- **Kotivalikon tutkan nimi kääntyy pisteen vasemmalle puolelle, kun se ei mahdu canvasiin** (`draw()`: `measureText`, 3 % varaa kallistukselle). Uuden pisteen kulmaa valitessa tarkista, ettei käännetty nimi osu toisen pisteen päälle.
- **Kotivalikon lukko on 44 × 44 px:n osuma-alue** (`right:-6px; bottom:-50px`), ikoni samassa kohdassa kuin ennen; bodyn alapehmuste 56 px kattaa sen. Älä pienennä pehmustetta alle 50 px:n, muuten sivulle tulee ylimääräistä vieritystä.
- **Kortit ovat 2 × 2 alkaen 700 px:stä** (`.tools`), ei `auto-fit`: kolmen sarakkeen rivi jätti neljännen kortin yksin. Viides työkalu = mieti ruudukko uudelleen.
- **`vercel.json`:n koko sivuston otsakkeissa ei ole CSP:tä tarkoituksella** (vain nosniff ja Referrer-Policy): toinen `Content-Security-Policy` voisi korvata hyppymittarin `connect-src 'self'` -otsakkeen.
- **AI-oppaan Takaisin ilman #-osaa palaa Mallit-välilehdelle** (`fromUrl`: `location.hash.length > 1 ? ui.tab : 'mallit'`). `?tab=` luetaan ennen oletusta ja tuntematon # säilyttää välilehden; `validate_tools.py` vahtii rivin.
- **"Ilmainen vaihtoehto" luetaan vain hinnan alusta** (`isFree`: `/^ilmainen(?!\s+kokeilu)/i`, sama sääntö `validate_tools.py`:n `is_free`). "Ilmainen kokeilu" ja "7 vrk ilmainen kokeilu" eivät ole ilmaisia; älä palauta `/ilmai/`-hakua. Muuta molempia kerralla.
- **`TASKS`-rivin `tool` nimeää osa-alueen työkalun nimen alulla** (puhe, musiikki → ElevenLabs), ja varalla on osa-alueen pick. Validaattori jäsentää TASKS-rivit regexillä: pidä kenttäjärjestys id, label, cat, area, agent, tool ja yksi rivi per tehtävä.
- **AI-oppaan vertailupalkki on kiinteä, joten `paintCompare` asettaa bodyn alapehmusteen palkin korkeuden mukaan.** Puhelimella (≤ 700 px) palkki on kaksirivinen ruudukko; älä palauta `flex-wrap`ia, joka pinosi sen 183 px laatikoksi sisällön päälle.
- **AI-oppaan kosketussäännöt ovat sivun omassa `@media (pointer:coarse)` -lohkossa** (kentät 16 px, kohteet 44/40 px, `+` ja `#` näkymättömällä `::after`-laajennuksella), eivät tokenilohkossa. `getBoundingClientRect` ei näe `::after`-laajennusta.
- **AI-oppaan pisteet: alle 100 yhdellä desimaalilla, ELO ja nopeudet kokonaislukuina** (`fmt`). Agentti-indeksillä on oma `fmt` (kokonaisluku pysyy kokonaislukuna). Hinnat muodossa `8,00 $` (`usd`).
- **AI-oppaan datan uudelleenyritys (`loadAll`) lataa vain epäonnistuneet lähteet eikä aja `fromUrl`ia**, joten sivu ei vieritä uudelleen. `sessionStorage`-avain `ai-ui` (vertailu, tehtävä, painotus) on vain mukavuus: luku ja kirjoitus try/catchissa.
- **YO-tutkan haun palaute on `#queryHits`-linkin `textContent`** (10.11.2026): `filterSessions` päivittää vain sen ja yhden tyhjätilan (`#noHits`), hakukenttää ei piirretä uudelleen. Suodatuksen aikana osumattomat kerrat ovat `hidden`; älä palauta kertakohtaista "Ei suodatukseen osuvia" -riviä.
- **Käsin suljettu kerta pysyy kiinni (`state.closed`)**: `filterSessions` avaa osumakerrat vain, jos käyttäjä ei ole sulkenut niitä; `setSubject`, `setTopic` ja kartan solu nollaavat. Älä palaa pelkkään `state.open`iin.
- **Trendinuoli lasketaan raakaosuuksista** (`stats()`: painotettu Σw·x/Σw − tasainen osumat/n), ei tasoitetuista todennäköisyyksistä: prioreilla on eri paino (Σw ≈ 5,5 vs n = 11), mikä piilotti ja synnytti nuolia rajalla. Todennäköisyydet käyttävät yhä Jeffreysin prioria.
- **`practiceScores` ohittaa rikkinäiset arviot ja rajaa `p`:n välille 0…max**: vanha varmuuskopio tai käsin muokattu `yo-practice` piirsi muuten osaamismonikulmion ulos kuvasta ("osaat −83 %"). Tutka ei edelleenkään kirjoita avaimeen.
- **Tutkan puhelinasettelu (≤ 560 px) on numeroidut säteet + nimilista `.rkey`**, ja tutka piirretään uudelleen, kun `NARROW`/`WIDE`-mediakysely vaihtuu (`drawn.st = null`). Nimien pituus (30 merkkiä) on sallittu vain ≥ 900 px: kapeammalla pitkät nimet tekevät sivulle vaakaskrollin.
- **Esiintymiskartta on yksi sarkainpysähdys** (roving tabindex, nuolinäppäimet): solut ovat `tabindex=-1` ja vain yksi `0`. Älä palauta `tabindex=0` joka solulle (≈ 200 sarkainpysähdystä).
- **YO-sivujen kosketussäännöt ovat `@media (pointer:coarse)`-lohkossa** (kentät 16 px, kohteet 40–44 px, YO-palkki 44 px `scripts/yo-nav.html`:ssä): työpöydän tiheys ei muutu. Uusi kenttä tai nappi tutkan hallintarivillä lisätään myös sinne.
- **"Vain vahvistetut kerrat" ja ainenapin n/n näkyvät vain, kun aineella on vahvistamattomia kertoja**; muuten ainenapissa on päivät kokeeseen (`examDays`, `EXAMS`).
- **YO-harjoittelu, Tyhjennä tämä selain:** `wipeBrowser()` asettaa ensin `wiped = true` (sen jälkeen `persistLocal()` ja `idb` eivät kirjoita mitään), poistaa `yo-practice`- ja `yo-practice-auth*`-avaimet, sessionStoragen ja IndexedDB-kannan ja lataa sivun ilman hashia. Älä palauta `location.replace(pathname + '#/')`-muotoa: pelkkä hashin vaihto ajaa `route()`n, joka tallentaa muistissa olevan tilan takaisin. Uusi tallennusavain tai kanta = lisää se `wipeBrowser()`iin ja `validate_practice.py`:n `check_page_wipe`-listaan.
- YO-harjoittelu: kun `yo-practice` poistuu toisessa välilehdessä (`storage`-tapahtuma, `newValue === null`), sivu lopettaa tallennukset ja latautuu uudelleen; IndexedDB-yhteys suljetaan `onversionchange`ssa, muuten kannan poisto jää jumiin.
- YO-harjoittelu: `/* pure:start */ … /* pure:end */` -lohkon funktiot (`normalizeSave`, `monthLabels`, `countedTasks`, `pikaLive`) ajetaan nodessa `validate_practice.py`:n `check_page_logic`-testissä (ohitetaan huomautuksella, jos nodea ei ole). Lohkoon ei saa tulla DOM- tai tilaviittauksia; älä nimeä kommentteja uudelleen.
- YO-harjoittelu, koesimulaatio: pisteisiin lasketaan osiosta vain `answer` ensimmäistä valittua tehtävää (`countedTasks`), ja arvosana-arvio näytetään vasta, kun kaikki lasketut kohdat on arvioitu. `sim.result`in muoto (`total`, `totalMax`, `assessed`) on ennallaan.
- YO-harjoittelu: pikatesti (`S.ui.pika`) on voimassa 2 h viimeisestä arvonnasta (`at`), eikä sen palkkia näytetä kertauskierroksen aikana. Palkit poistetaan oman nappinsa kautta (`closest('.pikabar')`), ei ensimmäisen `.pikabar`in mukaan.
- YO-harjoittelu, kosketus: `@media (pointer:coarse)` nostaa napit, suodattimet, pistenapit ja kentät 44 px:iin ja kentät 16 px:iin (`.wrap input/select/textarea`); työpöydän tiheys (nappi 33 px) on tarkoituksella ennallaan.
- **Karttavisan napautus kulkee `pickMapTarget`in kautta (10.11.2026):** svg:llä on yksi click-käsittelijä; pieni maa (`c`-pallo tai alle `MAP_SMALL_PX` ruudulla) voittaa lähimpänä keskipisteenä `MAP_REACH_TOUCH`/`MAP_REACH_MOUSE` säteellä, ja jos säteellä on useampi pieni maa, ensimmäinen napautus vain lähentää (`setZoom`, pallot säilyttävät ruutukokonsa). Älä palauta maakohtaisia click-käsittelijöitä: Balkanin keskipisteet ovat puhelimella 4 px välein eikä täyttä tulosta saa. Jo löydetyn maan napautus ei lukitse.
- **Karttamaille ei `<title>`-elementtiä pelin aikana:** `buildMap` lisää nimen vain kun `G.over`, muuten hover paljastaa vastauksen.
- **Vahtiajastimen tulos on alustava (`G.provisional`):** vieraan oma lasku ei kirjaudu `h2h`:hon, `P.seen`iin eikä omaksi ennätykseksi (`P.best`: ennätystä ei koskaan lasketa, joten alustava liian suuri tulos olisi jäänyt pysyvästi; katselmointi 10.11.2026), ja vetäjän `end` tai snapshotin `last` (vain vetäjältä, sama `seq`) korvaa sen.
- **Vetäjän snapshot saa vain aikaistaa kelloa:** `applySnapshot` siirtää `startAt`ia vain, jos vetäjän `elapsed` on yli 1,5 s edellä (nukkunut puhelin). Verkkoviive saa vetäjän ajan näyttämään vain pienemmältä, joten toiseen suuntaan korjaaminen antaisi lisäaikaa.
- **Oma peli on tallessa `sessionStorage`ssa (`visa-game-<koodi>`):** `restoreGame` palauttaa sen vain, kun huoneessa ei ole muita eikä snapshotia ole tullut (`R.synced`), eli toisen pelaajan tila voittaa aina. `applyEnd` ja `leaveRoom` poistavat tallenteen.
- **Monivalinnan näyttöviive (`G.revealing`) on vain rinnakkain-tilassa:** `paintTarget` ei vaihda kysymystä viiveen aikana ja `nextChoice` hoitaa `markDone`n. Kilpajaossa kysymys jää auki kuten ennen. `applyEnd` tyhjentää ajastimen.
- **`visa-v1` siivotaan ladattaessa:** väärän tyyppinen `best`/`h2h`/`seen` heitti ennen `renderHome`ssa ja näkyi virheenä "Visojen lataus epäonnistui". Uusi kenttä tallenteeseen = lisää sille tyyppitarkistus samaan kohtaan.
- **Sama sisältö ei saa olla kahdessa visassa:** `validate_visa.py`n `content_key` (muoto + ensimmäiset fi-vastaukset, monivalinnassa kysymykset) kaataa buildin. Lista-, lippu- ja karttavisa samoista maista ovat eri pelejä, siksi muoto on avaimessa.
- **Aulan aloituspalkki (`.startbar`) on sivun ainoa tarttuva alapalkki:** `position:sticky` asetuskortin sisällä, ei oma vieritysalue. `renderResults`in ehdolliset lapset menevät `fill()`in kautta (sivulle tulostui jo kerran "false").
- **Visan kartta: tarkka osuma voittaa lähennyksen, ja ruuhkaksi lasketaan vain vielä löytämättömät pienet maat** (`available(i)`; pelin jälkeen kaikki). Ennen katselmointia 10.11.2026 jokainen napautus Balkanilla lähensi ensin, vaikka jäljellä oli yksi maa.
- **Visan näppäimet paljastuksen aikana:** ei koskaan ⌘/Ctrl/Alt-yhdistelmää (⌘1 vaihtaa selaimen välilehteä) eikä kenttään kirjoitettua merkkiä (nimimerkki, chat); Enter ja välilyönti jäävät fokusoidulle napille; numerolla ohitus odottaa saman `REVEAL_SKIP_MS`:n kuin napautus.
- **YO-tutka: tyhjä lämpökartan solu ("·") ei avaa kertaa**, jonka suodatin juuri piilotti: se valitsee aiheen ja vierittää kertojen listan alkuun (`openCell`).
- **YO-harjoittelu: `armConfirm` palauttaa `disarm`in.** Koesimulaation Palauta-nappi puretaan aina, kun valinnat muuttuvat (`updateCounts`): muuten toinen napautus 4 s:n sisällä palautti kokeen vanhan varoituksen perusteella.
- **AI-opas: `MODELS_CRON` (ai.html) on kopio `update-models.yml`:n cronista**, ja `validate_tools.py` kaataa buildin, jos ne eroavat (sivu ennustaa siitä seuraavan päivityksen). Pisteiden tarkkuus on listakohtainen (`fmt`: lista, jossa on ≥ 100, on kokonaislukuja koko matkan). `.kt-tab.cmpb` pitää oman 36 px:n korkeutensa (`min-height`), koska tokenilohkon 44 px:n välilehtisääntö osuisi siihenkin.
- **Jakokuvilla (`img/og-*.jpg`) on `?v=` kuten muillakin kuvilla**, koska `/img/` on välimuistissa vuoden: uusi kuva = nosta versio jokaisen sivun `og:image`- ja `twitter:image`-riveillä.
