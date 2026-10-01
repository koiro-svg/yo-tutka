# koirosvg.com

Staattinen sivusto Vercelissä, ei build-vaihetta eikä riippuvuuksia.

| Polku | Tiedosto | Mikä |
|---|---|---|
| `/` | `index.html` | Kotivalikko |
| `/ai-opas` | `ai-opas.html` | AI-malliopas: paras malli per käyttötarkoitus |
| `/yo-tutka` | `yo-tutka.html` | YO-tutka |
| `/yo-harjoittelu` | `yo-harjoittelu.html` | YO-tehtävien harjoittelu: kaavaeditori, vihjeet, malliratkaisut, pikatesti, koesimulaatio, edistyminen |

## AI-malliopas – automaattinen päivitys
- `.github/workflows/update-models.yml` ajaa joka toinen päivä (04:17 UTC) skriptin
  `scripts/update_models.py`, joka hakee rankingit Artificial Analysisin ilmaisesta
  API:sta ja kirjoittaa `data/ai-models.json`. Muutos committataan mainiin → Vercel julkaisee.
- API-avain on GitHub-secretissä `AA_API_KEY` (ei koskaan repossa).
- Käsin ajo: GitHubissa Actions → "Päivitä AI-mallidata" → Run workflow,
  tai lokaalisti `AA_API_KEY=... python3 scripts/update_models.py`.
- Jos jokin API-kutsu epäonnistuu, sen kategorian edellinen data säilyy.
- Kategorioiden otsikot ja vinkit ovat `ai-opas.html`:n `CATS`-listassa, laskenta skriptissä.

## YO-tutka

Tämä on **julkaisurepo**. Lähdedata ja koontiskripti ovat `~/sovellukset/yo-tutka/`
(`data/<aine>.json` + `koosta.py`) — älä muokkaa kysymysdataa suoraan tähän tiedostoon.

## Datan päivitys sovellukset-kansiosta
1. Muokkaa lähdedataa: `~/sovellukset/yo-tutka/data/<aine>.json`
   (uusi tutkintokerta lisätään aineen `sessions`-listaan).
2. Koosta sovellukset-kansiossa:
   ```sh
   cd ~/sovellukset/yo-tutka && python3 koosta.py
   ```
3. Siirrä upotettu data tähän repoon. Koko tiedostoa **ei** kopioida, koska tämän
   repon `yo-tutka.html` on kääritty täydeksi HTML-dokumentiksi (doctype, head, body)
   ja sovellukset-versio ei. Komento vaihtaa vain `yo-data`-lohkon ja koontipäivän:
   ```sh
   cd ~/projects/yo-tutka && python3 - <<'PY'
   import re, pathlib
   src = pathlib.Path.home().joinpath('sovellukset/yo-tutka/index.html').read_text(encoding='utf-8')
   dst = pathlib.Path('yo-tutka.html'); html = dst.read_text(encoding='utf-8')
   for pat in (r'<script id="yo-data" type="application/json">.*?</script>', r"window\.YO_BUILT \|\| '[^']*'"):
       new = re.search(pat, src, re.S).group(0)
       html, n = re.subn(pat, lambda m: new, html, count=1, flags=re.S)
       assert n == 1, pat
   dst.write_text(html, encoding='utf-8')
   print('ok')
   PY
   ```
4. Testaa lokaalisti: avaa `yo-tutka.html` selaimessa (tai `npx serve .`).
5. Julkaise:
   ```sh
   git add yo-tutka.html && git commit -m "Lisää <tutkintokerta> <aine>" && git push
   ```
   Vercel julkaisee main-haaran pushin automaattisesti tuotantoon (~30 s).

Jos muutat ulkoasua tai logiikkaa, tee muutos ensin sovellukset-kansion `index.html`:ään (täällä `yo-tutka.html`)
ja tuo se tänne käsin — yllä oleva komento siirtää vain datan.

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

## Haarat
Muissa haaroissa tehdyt pushit saavat oman preview-osoitteen, eivät mene tuotantoon.
