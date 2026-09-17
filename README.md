# YO-tutka

Staattinen sivusto (yksi `index.html`), julkaistu Verceliin osoitteeseen koirosvg.com.

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
   repon `index.html` on kääritty täydeksi HTML-dokumentiksi (doctype, head, body)
   ja sovellukset-versio ei. Komento vaihtaa vain `yo-data`-lohkon ja koontipäivän:
   ```sh
   cd ~/projects/yo-tutka && python3 - <<'PY'
   import re, pathlib
   src = pathlib.Path.home().joinpath('sovellukset/yo-tutka/index.html').read_text(encoding='utf-8')
   dst = pathlib.Path('index.html'); html = dst.read_text(encoding='utf-8')
   for pat in (r'<script id="yo-data" type="application/json">.*?</script>', r"window\.YO_BUILT \|\| '[^']*'"):
       new = re.search(pat, src, re.S).group(0)
       html, n = re.subn(pat, lambda m: new, html, count=1, flags=re.S)
       assert n == 1, pat
   dst.write_text(html, encoding='utf-8')
   print('ok')
   PY
   ```
4. Testaa lokaalisti: avaa `index.html` selaimessa (tai `npx serve .`).
5. Julkaise:
   ```sh
   git add index.html && git commit -m "Lisää <tutkintokerta> <aine>" && git push
   ```
   Vercel julkaisee main-haaran pushin automaattisesti tuotantoon (~30 s).

Jos muutat ulkoasua tai logiikkaa, tee muutos ensin sovellukset-kansion `index.html`:ään
ja tuo se tänne käsin — yllä oleva komento siirtää vain datan.

## Haarat
Muissa haaroissa tehdyt pushit saavat oman preview-osoitteen, eivät mene tuotantoon.
