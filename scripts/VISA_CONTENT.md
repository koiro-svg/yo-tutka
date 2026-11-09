# Visojen kirjoitusohje (/visa)

Jokainen visapaketti on tiedosto `data/visa/<paketti>.json`, muodossa `{"quizzes":[…]}`. Tarkistus: `python3 scripts/validate_visa.py --draft`
(`--draft` sallii paketin, jota ei vielä ole `data/visa.json`:n `packs`-listassa).

## Alkuperäisyys (ehdoton)
- Aiheet ja listat tehdään omasta päästä ja yleisistä faktoista. **Älä avaa äläkä käytä mallina muita visasivustoja** (JetPunk, Sporcle ym.), älä kopioi
  niiden otsikoita, kysymyksiä tai listoja.
- Faktat tarkistetaan yleisistä lähteistä (Wikipedia, viranomaiset, lajiliitot). Ei laulujen sanoja, ei pitkiä lainauksia.

## Listavisa (kirjoita kaikki)
```json
{"id":"maantieto-euroopan-joet","cat":"maantieto","t":150,
 "title":{"fi":"Euroopan 10 pisintä jokea","en":"10 longest rivers in Europe"},
 "ordered":true,"hintLabel":{"fi":"Sija","en":"Rank"},
 "items":[{"fi":["Volga"],"en":["Volga"],"h":"1"}]}
```
- `id` alkaa paketin nimellä ja on koko sivustolla yksilöllinen. `cat`: `maantieto`, `suomi`, `historia`, `tiede`, `urheilu`, `viihde` tai `yleis`.
- `t` = aika sekunteina: noin 6–8 s kohdetta kohden, vähintään 45.
- `items`: 5–200 kohdetta (yleensä 8–60). `fi` ja `en` ovat listoja: ensimmäinen näytetään, loput ovat hyväksyttäviä vaihtoehtoja (kirjoitusasut, lyhyt muoto, sukunimi).
  Ääkkösiä, isoja kirjaimia, välimerkkejä tai välilyöntejä ei tarvitse toistaa, koska ne normalisoidaan pois.
- `h` = vihje (teksti tai `{"fi":…,"en":…}`), esim. vuosi tai maa. `ordered:true` pitää datan järjestyksen (vihjeet kuten sijat tai vuodet), muuten järjestys on aakkosellinen.
  Jos `h` on käytössä, anna `hintLabel`.
- Samaa vastausta ei saa olla kahdella kohteella (validaattori kaataa). Jos ihmisillä on sama sukunimi, käytä koko nimeä tai jätä vain yksi listaan.

## Monivalinta
```json
{"id":"yleis-1","cat":"yleis","format":"choice","t":180,"title":{"fi":"…","en":"…"},
 "items":[{"q":{"fi":"Mikä on…?","en":"What is…?"},"ok":{"fi":"Oikea","en":"Right"},"no":[{"fi":"Väärä 1","en":"Wrong 1"},{"fi":"Väärä 2","en":"Wrong 2"},{"fi":"Väärä 3","en":"Wrong 3"}]}]}
```
10–25 kysymystä, `t` noin 12 s kysymystä kohden. Väärien vastausten pitää olla uskottavia mutta yksiselitteisesti vääriä.

## Laatu
- Otsikko määrittää joukon täsmällisesti, jotta "kaikki" on tarkistettavissa. Kiistanalaiset rajaukset ratkaistaan otsikossa ("YK:n jäsenmaat", "yli 8000 m:n vuoret").
- **Muuttuvat listat** (ennätykset, hallitsijat, sijoitukset, viimeisimmät voittajat): otsikossa on vuosi tai aikaväli, esim. "1990–2024". Tarkista lähteestä, älä muistista.
- Suomenkieliset nimet ovat vakiintuneita suomenkielisiä nimiä, englanninkieliset vakiintuneita englanninkielisiä. Hyväksy molemmat kirjoitusasut, jos molemmat ovat käytössä.
- Ei loukkaavaa sisältöä, ei yksityishenkilöitä, ei poliittista kannanottoa.
- Jos et ole faktasta varma etkä saa sitä varmistettua, jätä visa pois. Mieluummin vähemmän visoja kuin virheitä.
