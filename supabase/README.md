# YO-harjoittelun käyttäjätilit (Supabase + Resend) – käyttöönotto

Tilit näkyvät sivulla vasta, kun `yo-harjoittelu.html`:n `SUPABASE`-vakioon on lisätty projektin
osoite ja julkinen avain. Siihen asti sivu toimii kuten ennenkin (kaikki vain selaimessa).

## 1. Supabase-projekti
1. supabase.com → luo tili → **New project**: nimi `yo-harjoittelu`, alue **Central EU (Frankfurt)**,
   vahva tietokantasalasana salasanamanageriin, Free-taso.
2. **SQL Editor → New query** → liitä `supabase/schema.sql` kokonaan → **Run**. (Voi ajaa uudelleen.)
3. **Authentication → Sign In / Providers → Email**: Email päällä, **Confirm email** päällä,
   **Minimum password length 10**.
4. **Authentication → URL Configuration**: Site URL `https://koirosvg.com`,
   Redirect URLs: lisää `https://koirosvg.com/yo-harjoittelu`.
5. **Authentication → Emails → Templates**:
   - *Confirm signup*: aihe `Vahvista YO-harjoittelun tili`, sisältö `email/confirm-signup.html`.
   - *Reset Password*: aihe `YO-harjoittelun salasanan vaihto`, sisältö `email/reset-password.html`.
6. **Project Settings → API Keys**: kopioi **Project URL** ja **Publishable key** (`sb_publishable_…`).
   Nämä ovat julkisia ja menevät sivun koodiin. **Älä koskaan** anna tai julkaise `secret`/`service_role`-avainta.

## 2. Resend (sähköpostit)
1. resend.com → luo tili → **Domains → Add domain** `koirosvg.com`.
2. Resend näyttää DNS-tietueet (MX, SPF-TXT, DKIM-TXT). Lisää ne Verceliin: vercel.com → Domains →
   koirosvg.com → DNS Records (tai anna ne Claudelle lisättäväksi) → paina Resendissä **Verify**.
3. **API Keys → Create API key** (Sending access, domain koirosvg.com).

## 3. Supabase lähettää Resendin kautta
**Authentication → Emails → SMTP Settings → Enable custom SMTP**:
| Kenttä | Arvo |
|---|---|
| Sender email | `noreply@koirosvg.com` |
| Sender name | `YO-harjoittelu` |
| Host | `smtp.resend.com` |
| Port | `465` |
| Username | `resend` |
| Password | Resendin API-avain |

Ilman tätä Supabase lähettää vain muutaman viestin tunnissa, eikä rekisteröinti toimi muille.

## 4. Kytkentä sivuun (Claude tekee)
- `yo-harjoittelu.html`: `const SUPABASE = { url: '<Project URL>', key: '<Publishable key>' };`
- GitHub-repon muuttujat `SUPABASE_URL` ja `SUPABASE_KEY` (`gh variable set …`) → päivittäinen
  `supabase-keepalive.yml` estää ilmaisen projektin nukahtamisen.
- `tietosuoja.html`: rekisterinpitäjän yhteystieto.

## 5. Testi ennen kuin kerrot muille
1. Luo tili omalla sähköpostilla → vahvistusviesti tulee → linkki → **Vahvista** → olet sisällä.
2. Arvioi jokin tehtävä ja kirjoita vastaus → kirjaudu toisella laitteella → sama edistyminen näkyy.
3. *Unohtunut salasana* → viesti → uusi salasana → toinen laite kirjautuu ulos.
4. *Poista tili* testitililtä → Supabase → Authentication → Users: käyttäjä on poissa.

## Seuranta
Supabase → Reports näyttää tietokannan koon (ilmaistaso 500 Mt). Jokaisella käyttäjällä on 15 Mt:n
vastauskiintiö (`practice_answers_quota`) ja yksi vastaus saa olla enintään 1 Mt kuvineen.
