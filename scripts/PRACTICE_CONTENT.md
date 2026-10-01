# Harjoitussisällön kirjoitusohje (vihjeet ja malliratkaisut)

Koskee tiedostoja `data/practice/<aine>/<kerta>.json`, jotka `harjoittele.html` näyttää.
Yksi tiedosto = yhden aineen yksi tutkintokerta. Tehtävien numerot (`n`), pisteet ja
otsikot tulevat YO-tutkan datasta (`yo-tutka.html`:n `yo-data`-lohko). Tämä tiedosto
lisää niihin harjoitussisällön. Tarkista aina lopuksi:

```sh
python3 scripts/validate_practice.py data/practice/<aine>/<kerta>.json
```

## Tekijänoikeus (ehdoton)
YTL:n koetehtäviä ei saa julkaista verkossa ilman lupaa, ja repo on julkinen.
- **Älä kopioi tehtävänantoa sanasta sanaan.** Kirjoita `prompt` omin sanoin ja lyhyesti:
  mitä kysytään ja mitä lähtötietoja tarvitaan. Luvut, kaavat, yhtälöt ja reaktioyhtälöt
  saa mainita, koska ilman niitä tehtävää ei voi ratkaista.
- **Älä koskaan kopioi aineistoja**: artikkeleita, kaunokirjallisia katkelmia,
  kuullun tai luetun tekstejä, kuvia, taulukoita tai videoiden sisältöä. Viittaa niihin
  ("ks. alkuperäisen tehtävän kuva / aineisto B"). Enintään muutaman sanan lainaus on
  sallittu, kun se on vastauksen kannalta välttämätön.
- Malliratkaisut ja vihjeet ovat omaa tekstiä. Älä kopioi MAFYn, YTL:n tai muiden
  mallivastauksia. YTL:n hyvän vastauksen piirteitä (HVP) saa käyttää tarkistukseen ja
  sisällön pohjana, mutta kirjoita teksti itse.

## Rakenne

```json
{
  "subject": "pitka-matematiikka",
  "session": "2026S",
  "examUrl": "https://files.mafy.fi/Yo-kokeet/2026S_MAA/index.html",
  "gradingUrl": "https://tiedostot.ylioppilastutkinto.fi/kokeet/2026-09-24_M_fi/grading-instructions.html",
  "exam": {
    "minutes": 360,
    "sections": [
      { "title": "A-osa", "tasks": ["1", "2", "3", "4", "5", "6"], "answer": 6, "note": "Vastaa kaikkiin." },
      { "title": "B1-osa", "tasks": ["7", "8", "9", "10"], "answer": 2 }
    ]
  },
  "tasks": [
    {
      "n": "1",
      "intro": "Yhteiset lähtötiedot omin sanoin (valinnainen).",
      "units": [
        {
          "id": "1.1",
          "points": 2,
          "prompt": "Mitä tässä kohdassa kysytään, omin sanoin.",
          "hints": ["Yksi vihje, koska kohta on enintään 4 pistettä."],
          "solution": "Vaiheittainen malliratkaisu.",
          "answer": "$19\\,\\%$",
          "check": "hvp+laskettu"
        }
      ]
    }
  ]
}
```

- `examUrl`: paras julkinen osoite, josta tehtävät näkee alkuperäisinä. MAFY-aineissa
  `files.mafy.fi/Yo-kokeet/...`, muissa Yle Abitreenit. `gradingUrl`: YTL:n HVP-sivu, jos
  sellainen on. Käytä YO-tutkan `sources`-listan osoitteita, ja jos ne eivät toimi, etsi
  toimiva osoite.
- `exam`: kokeen rakenne koesimulaatiota varten, luettuna **tämän kerran**
  kokeen ohjeista. Jokainen tehtävä kuuluu täsmälleen yhteen osioon. `answer` on se määrä
  tehtäviä, joihin osiossa vastataan (valinnaisuus). `minutes` on kokeen kesto; jos kestoa
  ei mainita kokeen ohjeissa, käytä 360 (kaikki YO-kokeet ovat 6 h).
  Äidinkielessä on kaksi erillistä koetta (lukutaito, kirjoitustaito) eri päivinä: anna
  jokaiselle osiolle `"group": "lukutaito"` tai `"group": "kirjoitustaito"`, jolloin
  koesimulaatio tekee ne erikseen. Osiolla voi olla omat `examUrl`, `gradingUrl` ja `minutes`,
  jotka ohittavat tiedoston yleiset (esim. kirjoitustaidon omat linkit).
- `note`: lyhyt ohje osion valinnoista ja rajoista (merkkimäärät, ohjelmat). Ei URL-osoitteita:
  linkit kuuluvat `examUrl`/`gradingUrl`-kenttiin.
- `tasks`: yksi alkio jokaiselle YO-tutkan tehtävälle samalla `n`:llä, ei ylimääräisiä.

## Yksiköt (`units`) ja vihjemäärä
Yksikkö on kohta, jolle annetaan omat vihjeet ja oma ratkaisu.
- Jos alakohdat ovat **toisistaan riippumattomia**, jokainen alakohta on oma yksikkö
  (`id` = "a", "b" tai "1.1", kuten alkuperäisessä).
- Jos alakohdat **nojaavat toisiinsa** (b käyttää a:n tulosta), tai tehtävässä ei ole
  alakohtia, koko tehtävä on yksi yksikkö (`id` = "").
- Monivalintasarjat (esim. matematiikan A-osan monivalinnat, englannin kuullun ja luetun
  osiot, fysiikan väittämät) ovat yksi yksikkö. Samoin englannin sekatehtävät (monivalintoja ja
  avoimia kysymyksiä samassa osiossa). Ratkaisu listaa jokaisen kohdan vastauksen
  ja lyhyen perustelun. Vihje 2 saa olla lyhyt lista "kohta kohdalta mihin keskittyä".
  `answer` on tiivis avain: `1.1 C · 1.2 A · 1.3 vastaus suomeksi`.
- **Monivalinnan kirjaimet:** kokeessa ei ole kirjaimia. A = ylin vaihtoehto sellaisessa järjestyksessä
  kuin ne ovat alkuperäisessä koenäkymässä, B = toinen jne. Mainitse ratkaisussa lisäksi oikean
  vaihtoehdon sisältö lyhyesti suomeksi, jotta vastauksen voi tarkistaa, vaikka järjestys vaihtelisi.
- **Nimeämättömät alakohdat:** jos kokeessa ei ole a/b-kohtia, mutta HVP jakaa pisteet
  osiin (a, b, c), käytä HVP:n jakoa ja id:itä "a", "b"… vain niille osille, jotka ovat
  riippumattomia. Jos osa nojaa edelliseen (c käyttää b:n tulosta) tai HVP antaa pisteitä
  yhteisestä mallinnuksesta, pidä koko tehtävä yhtenä yksikkönä.
- **Kaksitasoiset kohdat** (esim. 2.1 → 2.1.1–2.1.3 à 1 p): yksikkö on ylempi taso (2.1), eli
  kokonaisuus, jossa kysytään yksi asia. Alimman tason täydennyskentät ovat sen sisällä.
- **Lyhytvastaussarjat** (täydennys, pelkkä lopputulos): jokainen itsenäinen kysymys (1.1, 1.2 …)
  on oma yksikkö. Monivalintasarja on yksi yksikkö (ks. yllä).
- Yksiköiden pisteiden summa = tehtävän pisteet.
- **Vihjemäärä pisteiden mukaan:** yksikkö ≤ 4 p → täsmälleen 1 vihje; ≥ 5 p → täsmälleen 2.
  - Vihje 1 on kevyt ja kertoo mistä aloittaa: mikä käsite, mikä kaava tai mikä
    lähestymistapa.
  - Vihje 2 on vahvempi ja antaa avainaskeleen tai välituloksen, mutta ei loppuvastausta.
  - Jos vihjeitä on vain yksi, sen taso on näiden välissä.

## Tekstimuoto
Kentät `intro`, `prompt`, `hints[]`, `solution` ja `answer` ovat kevyttä Markdownia:
- tyhjä rivi = uusi kappale, `**lihava**`, `*kursiivi*`
- listat rivin alussa: `- ` tai `1. `
- kaavat LaTeXina: `$...$` rivin sisällä, `$$...$$` omalla rivillään
- kemia: `$\ce{H2SO4}$`, `$\ce{A + B -> C}$` (mhchem)
- numeroitu lista saa alkaa muusta kuin 1:stä (esim. väliotsikon jälkeen `4. `), numerointi säilyy
- lihavoinnin sisällä saa olla kaava: `**Vastaus: $x=2$**`
- ei HTML:ää eikä väliotsikoita (`#`). Dollarimerkki tekstinä kirjoitetaan `\$`.
- JSONissa kenoviiva tuplataan: `"$\\frac{1}{2}$"`.

Kieli on suomi kaikissa aineissa. Englannin kirjoitelman malliteksti on englanniksi.

## Malliratkaisun sisältö aineittain
- **Matematiikka, fysiikka, kemia:** numeroidut vaiheet ja perustelut niin kuin YTL ne
  odottaa: käytetyt kaavat, sijoitukset, yksiköt ja merkitsevät numerot.
  Loppuvastaus lihavoituna ja myös `answer`-kentässä. Lopuksi saa lisätä kappaleen
  `**Sudenkuoppa:**`, jossa on tyypillinen virhe.
- **Selitys- ja todistusyksiköt kaikissa aineissa** (myös matematiikan "perustele", "osoita"):
  "Hyvä vastaus sisältää" -lista ja esimerkkivastaus tai todistus vaiheittain. `answer`
  jätetään pois, jos loppuvastausta ei ole. `check` on `hvp`, jos sisältö täsmää HVP:hen.
- **Aineistotaulukot ja -kuvat:** taulukkoa tai kuvaa ei kopioida. Vihjeessä ja ratkaisussa saa
  mainita aineistosta lasketut välitulokset (esim. regressiokertoimet) ja arvojen välin
  (esim. "noin 100–300 min"), koska ne ovat omaa laskentaa, eivät aineiston toisto.
- **Biologia ja kemian/fysiikan selitystehtävät:** "Hyvä vastaus sisältää" -lista
  keskeisistä asioista ja sen perään lyhyt esimerkkivastaus omin sanoin.
- **Englanti:** kuullun ja luetun osioissa ratkaisu on vastausavain kohta kohdalta
  (monivalinnan kirjain tai suomenkielinen vastaus) ja perustelu, eli missä kohtaa
  tekstiä/äänitettä vastaus on, kuvailtuna, ei lainattuna. Rakenneosiossa oikeat muodot ja
  kielioppisääntö. Kirjoitelmassa malliteksti annetulla pituudella (700–1 300 merkkiä ilman
  välilyöntejä) sekä lyhyt lista siitä, mikä tekee siitä hyvän.
- **Kaikki aineet:** `**Sudenkuoppa:**`-kappale (tyypillinen virhe) on sallittu ja toivottu.
  Tekstissä tehtäviin viitataan alkuperäisellä numeroinnilla (tehtävä 3, aineisto 1.A); `n` on
  vain tunniste. `answer` jätetään pois kirjoitelmista ja laajoista analyyseistä.
- **Äidinkieli:** lukutaidossa analyysin runko ja keskeiset havainnot, jotka hyvä
  vastaus tekee aineistosta, sekä esimerkkikappale. Kirjoitustaidossa 2–3 rajausta
  tai näkökulmaa, rakennemalli (otsikko, johdanto, käsittelyn jaksot, lopetus) ja
  esimerkkijohdanto. Aineistojen käytön ohje, eli mitä aineistoja voisi käyttää ja
  miten, mutta ei lainauksia.

## Tarkistusskriptit
- `python3 scripts/validate_practice.py <tiedosto>`: rakenne, vihjemäärät, pisteet, `$`-parit.
- `scripts/check_tex.mjs`: jokainen kaava MathJaxilla (ohje tiedoston alussa, vaatii Noden).
- `python3 scripts/check_overlap.py`: kopioitu teksti (ks. Tekijänoikeustarkistus).

## Tarkistus (`check`)
Kirjaa jokaiseen yksikköön, miten vastaus on varmistettu:
- `hvp`: loppuvastaus täsmää YTL:n hyvän vastauksen piirteisiin.
- `laskettu`: loppuvastaus on laskettu koneellisesti (esim.
  `uv run --with sympy python3 tarkistus.py`).
- `hvp+laskettu`: molemmat.
- `malli`: yksikössä ei ole yhtä oikeaa vastausta (kirjoitelma, essee, laaja analyysi). Malliteksti on
  esimerkki, ja se on kirjoitettu HVP:n arviointikriteerien mukaan.
- `ei`: ei varmistettu (esim. HVP puuttuu eikä vastausta voi laskea). Käytä rehellisesti.

Matematiikassa, fysiikassa ja kemiassa jokainen numeerinen loppuvastaus lasketaan
koneellisesti. Jos se on ristiriidassa HVP:n kanssa, selvitä syy ennen kirjaamista.

## Lähteiden lukeminen
- Koenäkymä (`files.mafy.fi/Yo-kokeet/<kerta>_<AINE>/index.html`, Yle Abitreenit) on staattista
  HTML:ää; kaavat ovat LaTeXina tekstissä. Liitteet (taulukot) ovat usein sivulla
  `…/attachments/index.html` HTML-taulukkona, kuvat `attachments/`-kansiossa.
- HVP-sivun kaavat ovat MathJax-SVG-kuvia; kaavan teksti on SVG:n `<title>`-elementissä.
- Hae curlilla ja poista tagit Pythonilla (`<style>`/`<script>` pois, sitten tagit, sitten
  `html.unescape`). Kuvat voi ladata ja katsoa.
- Yle Abitreenit: tehtävät ja vaihtoehdot ovat `index.html`:ssä, tekstiaineistot
  `attachments/index.html`:ssä ja äänitteet ja videot `attachments/*.mp3|webm`-tiedostoissa. HVP:ssä on
  usein vain oikeat vastaukset.
- **Kuullun ymmärtämisen äänitteet** saa litteroida omaan käyttöön scratch-hakemistoon
  (esim. `uvx --from mlx-whisper mlx_whisper <tiedosto> --language en --output-dir <scratch>`),
  jotta perustelut osuvat oikeaan kohtaan. Litteraattia ei koskaan julkaista eikä kopioida JSONiin.
- **Lainaukset:** vastaussanan, alleviivatun sanan tai idiomin saa mainita, koska ilman sitä
  ratkaisua ei voi antaa. Alkuperäistä kysymystä (myös suomenkielistä) ei toisteta, vaan se
  muotoillaan uudelleen.

## Tekijänoikeustarkistus (pakollinen)
Vertaa lopuksi jokaista tekstikenttää alkuperäiseen koetekstiin ja HVP:hen: etsi yhteiset
**6 sanan jaksot** (sanat pieniksi kirjaimiksi, välimerkit pois). Kaavoja ja lukuja ei
lasketa. Muotoile jokainen osuma uudelleen, kunnes osumia ei ole. Ainoa poikkeus ovat aineistojen
lähdeviitteet (tekijä ja otsikko), joita saa käyttää sellaisenaan:

Lähdetekstit tallennetaan repon ulkopuolelle (scratch- tai tmp-hakemistoon), koska ne ovat YTL:n
tekijänoikeuden alaisia ja repo on julkinen. `.gitignore` estää `*.txt`-tiedostot varmuuden vuoksi.

```sh
python3 scripts/check_overlap.py data/practice/<aine>/<kerta>.json /tmp/…/koeteksti.txt /tmp/…/hvp.txt
```
