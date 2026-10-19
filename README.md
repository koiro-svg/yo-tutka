# koirosvg.com

Staattinen sivusto Vercelissä, ei riippuvuuksia. Vercelin build ajaa vain tarkistukset (`vercel.json`: `validate_tools.py`,
`validate_practice.py`, `check_tokens.py`, `yo_index.py`).

| Polku | Tiedosto | Mikä |
|---|---|---|
| `/` | `index.html` | Kotivalikko |
| `/ai` | `ai.html` | AI-opas: välilehdet Mallit, Koodausagentit ja Työkalut. Vanhat `/ai-opas` ja `/ai-tyokalut` ovat 308-uudelleenohjauksia tänne (#-ankkurit toimivat) |
| `/yo-tutka` | `yo-tutka.html` | YO-tutka (`/yo` on lyhyt osoite: 307-uudelleenohjaus tänne, ?parametrit ja #aine/aihe säilyvät) |
| `/yo-harjoittelu` | `yo-harjoittelu.html` | YO-tehtävien harjoittelu: kaavaeditori, vihjeet, malliratkaisut, pikatesti, koesimulaatio, edistyminen |
| `/tietosuoja` | `tietosuoja.html` | YO-harjoittelun käyttäjätilien tietosuojaseloste |
| `/hyppymittari` | `hyppymittari/index.html` | Hyppymittari: vertikaalihypyn korkeus kameralla (MediaPipe, laitteella) |

## AI-malliopas – automaattinen päivitys
- `.github/workflows/update-models.yml` ajaa joka toinen päivä (04:17 UTC) skriptin
  `scripts/update_models.py`, joka hakee rankingit Artificial Analysisin ilmaisesta
  API:sta ja kirjoittaa `data/ai-models.json`. Muutos committataan mainiin → Vercel julkaisee.
- API-avain on GitHub-secretissä `AA_API_KEY` (ei koskaan repossa).
- Käsin ajo: GitHubissa Actions → "Päivitä AI-mallidata" → Run workflow,
  tai lokaalisti `AA_API_KEY=... python3 scripts/update_models.py`.
- Jos jokin API-kutsu epäonnistuu, sen kategorian edellinen data säilyy.
- Kategorioiden otsikot ja vinkit ovat `ai.html`:n `CATS`-listassa, laskenta skriptissä.
- Koodausagentit (`#koodausagentit`) tulevat tiedostosta `data/coding-agents.json`. Artificial
  Analysisin Coding Agent Index ei ole API:ssa, joten sitä päivittää AI-työkalupakin
  Claude-rutiini (`scripts/UPDATE_TOOLS.md`), ja `scripts/validate_tools.py` tarkistaa myös sen.

## YO-tutka

Tämä on **julkaisurepo ja käyttöliittymän pääversio** (`yo-tutka.html`, päätös 19.10.2026): ulkoasu ja logiikka
muutetaan täällä. Lähdedata ja koontiskripti ovat `~/sovellukset/yo-tutka/` (`data/<aine>.json` + `koosta.py`), jossa
ei enää ole omaa käyttöliittymäkopiota. Älä muokkaa kysymysdataa suoraan tähän tiedostoon.

## Datan päivitys sovellukset-kansiosta
1. Muokkaa lähdedataa: `~/sovellukset/yo-tutka/data/<aine>.json`
   (uusi tutkintokerta lisätään aineen `sessions`-listaan).
2. Koosta:
   ```sh
   cd ~/sovellukset/yo-tutka && python3 koosta.py
   ```
   Skripti kirjoittaa datan suoraan tämän repon `yo-tutka.html`:n `yo-data`-lohkoon ja koontipäivän
   (`window.YO_BUILT`, vain jos data muuttui), ja ajaa lopuksi `python3 scripts/yo_index.py --write`, joka päivittää
   datasta johdetut tiedostot: hakuindeksin `data/yo-topics.json` ja etusivun YO-kortin `data-yo-built`-päivän
   (tutkan tuoreusrengas). Build kaatuu, jos ne eivät vastaa `yo-tutka.html`:ää.
3. Testaa lokaalisti pienellä palvelimella (esim. `python3 -m http.server` ja `/yo-tutka.html`).
4. Julkaise:
   ```sh
   git add yo-tutka.html data/yo-topics.json index.html && git commit -m "Lisää <tutkintokerta> <aine>" && git push
   ```
   Vercel julkaisee main-haaran pushin automaattisesti tuotantoon (~30 s).

## YO-harjoittelu – vihjeet ja malliratkaisut
- Sisältö: `data/practice/<aine>/<kerta>.json`, yksi tiedosto per aine ja tutkintokerta.
  Kirjoitusohje ja tekijänoikeussäännöt: `scripts/PRACTICE_CONTENT.md`.
- Tarkistus ennen committia:
  ```sh
  python3 scripts/validate_practice.py                 # rakenne, vihjemäärät, pisteet (ajetaan myös Vercelin buildissa)
  python3 scripts/check_overlap.py <tiedosto.json> <koeteksti.txt> <hvp.txt>   # ei kopioitua tekstiä
  ```
  Kaavojen LaTeX-tarkistus MathJaxilla (`scripts/check_tex.mjs`) vaatii Noden: ohje tiedoston alussa.
- Uusi tutkintokerta: lisää ensin YO-tutkaan (yllä), sitten harjoitussisältö ohjeen mukaan.

## Hyppymittari – päivitys sovellukset-kansiosta

Lähde on `~/sovellukset/hyppymittari/` (testit, CLAUDE.md, README siellä). Tänne kopioidaan
vain ajettavat tiedostot:

```sh
rsync -a --delete --exclude '/test-*.js' --exclude '/test.sh' --exclude '/CLAUDE.md' \
  --exclude '/README.md' --exclude '.DS_Store' ~/sovellukset/hyppymittari/ hyppymittari/
```

Ankkuroi poissulkemiset (`/README.md`), muuten MediaPipen lisenssitiedosto
`vendor/mediapipe/README.md` jää pois.

## YO-harjoittelu – käyttäjätilit
Supabase (tilit ja tiedot, EU) + Resend (sähköpostit). Käyttöönotto-ohje, tietokanta ja sähköpostipohjat:
`supabase/`. Tilit näkyvät sivulla vasta, kun `yo-harjoittelu.html`:n `SUPABASE`-vakio on täytetty.

## Haarat
Muissa haaroissa tehdyt pushit saavat oman preview-osoitteen, eivät mene tuotantoon.
