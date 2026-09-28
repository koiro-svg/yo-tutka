# AI-työkalupakki: automated update instructions

These are the instructions for the scheduled Claude agent that refreshes
`data/ai-tools.json` every other day. The page `ai-tyokalut.html` renders that file.
The repo is **public** and main deploys to https://koirosvg.com automatically, so
everything you push goes live within a minute.

## Goal
Keep every area's list as "the best AI tools for a Finnish small business / solo
entrepreneur right now". Accuracy beats novelty. A run that changes nothing is a
good run if nothing changed in the world.

## Procedure
1. `git pull --ff-only` so you start from the live version.
2. For each area in `data/ai-tools.json`, web-search the last ~2–4 weeks for:
   shutdowns, acquisitions, renames, major launches, pricing changes, and new tools
   that clearly beat an existing entry. Check the current `pick` still deserves it.
   Prefer primary sources (vendor blog, pricing page, help center) and reputable
   press (TechCrunch, The Verge, CNBC, Reuters, Bloomberg). Skip SEO listicles as
   the only source.
3. Edit only what you verified. Every factual change (price, launch, acquisition,
   shutdown, new pick) needs at least one source you actually opened this run;
   surprising claims (acquisitions, shutdowns) need two independent sources.
4. Rules for edits:
   - Never change area `id`s, their order, or add/remove areas, and never touch
     `revision` (it unlocks manual restructuring; the validator blocks the rest).
   - Only a few tools may be added+removed per run (`MAX_SWAPS` in the validator). Replace a tool only if it
     shut down, became irrelevant, or a clearly better alternative exists.
   - A shut-down or acquired-and-discontinued tool must be removed the same run.
   - Exactly one `pick: true` per area. Change the pick only with strong evidence.
   - `kind`: `automatisoi` = runs work by itself once set up, `avustaa` = helps you do it.
   - `fi`: `hyvä` | `kohtalainen` | `heikko` | `?` (Finnish-language quality; `?` if unknown).
   - Prices: current list price, short, e.g. `Ilmainen · Pro 20 $/kk`. No time-limited
     campaign prices. If sources disagree, give a range with `~`.
   - `url`: the tool's official https page. No affiliate or tracking parameters.
   - All text in Finnish, plain and concrete, no hype, no `<` or `>` characters.
     Do not claim anything you could not verify; leave the old text if unsure.
   - `starter`: update only if one of its tools was removed or clearly overtaken.
5. For each notable change, prepend to `changes`:
   `{"date": "YYYY-MM-DD", "text": "one Finnish sentence"}` (newest first; drop the oldest
   beyond `MAX_CHANGES` in the validator). Minor price tweaks do not need an entry.
6. Set `updated` to the current UTC time (ISO 8601, e.g. `2026-09-30T04:20:00Z`),
   even if nothing else changed: it means "verified on this date".
7. Run `python3 scripts/validate_tools.py` (it compares against the live site by itself).
   If it fails, fix the data. If you cannot make it pass, stop without committing.
   Vercel runs the same check on deploy, so invalid data would fail the deploy anyway.
8. Commit only `data/ai-tools.json` to main and push:
   - Changes: `Päivitä AI-työkalupakki: <lyhyt kuvaus>` (Finnish, imperative)
   - Only `updated` changed: `Päivitä AI-työkalupakin tarkistuspäivä`
   Never force-push. If the push is rejected, `git pull --rebase` once and retry;
   if it still fails, stop and report the error.

## Do not
- Touch any file other than `data/ai-tools.json`.
- Invent tools, prices, dates or features.
- Add tools that require unlawful use (e.g. scraping personal data against GDPR)
  or that are clearly aimed at spam.
