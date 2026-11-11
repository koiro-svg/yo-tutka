#!/usr/bin/env python3
"""Fetch model rankings from the Artificial Analysis free API and write data/ai-models.json.

Usage: AA_API_KEY=... python3 scripts/update_models.py
Standard library only. A category whose fetch fails keeps its previous data,
so a flaky API never blanks the live page. Each run also records the day's top names per category in
data/ai-history.json (the page's trend arrows and "kärjessä N pv").
"""
import collections, json, os, pathlib, re, sys, urllib.request, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ai-models.json"
HIST = ROOT / "data" / "ai-history.json"  # {"days": [{"date", "top": {category: [names best-first]}}]}
HIST_DAYS = 90
SEEN = ROOT / "data" / "media-seen.json"  # category -> media model id -> first day seen; the free API has no media release dates
BASE = "https://artificialanalysis.ai/api/v2"
LLM_PATH = "language/models/free"
TOP_N = 8

# Category id -> endpoint. Scored by Arena ELO unless listed in SCORING.
MEDIA = {
    "kuva": "text-to-image",
    "kuvanmuokkaus": "image-editing",
    "video": "text-to-video",
    "kuvasta-video": "image-to-video",
    "video-aani": "text-to-video-audio",
    "kuvasta-video-aani": "image-to-video-audio",
    "puhe": "text-to-speech",
    "musiikki": "music/with-vocals",
    "musiikki-instrumentaali": "music/instrumental",
    "puheentunnistus": "speech-to-text",
    "puheagentti": "speech-to-speech",
}
ELO = ("elo", 1, {"metric": "Arena ELO"})
# Category id -> (score field, multiplier, category metadata). WER and τ-Voice are 0–1 fractions.
SCORING = {
    "puheentunnistus": ("aa_wer_index", 100, {"metric": "AA-WER (sanavirheet)", "lowerIsBetter": True, "unit": "%"}),
    "puheagentti": ("tau_voice_score", 100, {"metric": "τ-Voice"}),
}
MAX_PAGES = 60  # the quota is 100 requests per 24 h; a stuck has_more must not use it all


def media_path(cid):
    return f"media/{MEDIA[cid]}/models/free"


def fetch(path, key):
    """All rows of a list endpoint; the language endpoint is paginated, the media ones are not."""
    rows = []
    for page in range(1, MAX_PAGES + 1):
        url = f"{BASE}/{path}" + (f"?page={page}" if page > 1 else "")
        req = urllib.request.Request(url, headers={"x-api-key": key, "User-Agent": "koirosvg-ai-opas"})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.load(r)
        if not isinstance(body, dict) or not isinstance(body.get("data"), list):
            raise ValueError(f"{path}: unexpected response shape")
        rows += body["data"]
        if not (body.get("pagination") or {}).get("has_more"):
            return rows
    raise ValueError(f"{path}: yli {MAX_PAGES} sivua")


def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def creator(m):
    c = m.get("model_creator") or {}
    return c.get("name") if isinstance(c, dict) else str(c)


def item(m, score, **extra):
    full = m.get("name") or m.get("slug") or "?"
    base, _, variant = full.partition(" (")
    d = {"name": base, "creator": creator(m), "score": round(score, 2)}
    if m.get("release_date"):  # media models have none on the free API
        d["released"] = m["release_date"]
    if variant:  # e.g. "Adaptive Reasoning, Max Effort)" -> shown as a hint, not part of the name
        d["variant"] = variant.rstrip(")")
    d.update({k: round(v, 2) for k, v in extra.items() if v is not None})
    return d


def top(items, n=TOP_N):
    """Items arrive best-first; keep only the best variant of each base model."""
    seen, out = set(), []
    for it in items:
        if it["name"] in seen:
            continue
        seen.add(it["name"])
        out.append(it)
        if len(out) == n:
            break
    return out


# Text categories: id -> (label, evaluation key). The free API has these indexes only;
# AA no longer publishes the Coding and Agentic indexes and per-test scores are Pro-only.
BENCH = {
    "yleis": ("Intelligence Index", "artificial_analysis_intelligence_index"),
    "strategia": ("Strategy & Ops Index", "artificial_analysis_strategy_and_ops_index"),
    "rahoitus": ("Finance & Accounting Index", "artificial_analysis_finance_and_accounting_index"),
    "juridiikka": ("Legal Index", "artificial_analysis_legal_index"),
    "terveys": ("Healthcare & Medical Index", "artificial_analysis_healthcare_and_medical_index"),
    "insinoori": ("Engineering Index", "artificial_analysis_engineering_index"),
    "taloustiede": ("Economics Index", "artificial_analysis_economics_index"),
}


def blended(pr):
    """AA's 3:1 input:output blend; the free API only returns the two prices separately."""
    i, o = num(pr.get("price_1m_input_tokens")), num(pr.get("price_1m_output_tokens"))
    return (3 * i + o) / 4 if i is not None and o is not None else None


def llm_categories(rows):
    cats = {}
    enriched = []
    for m in rows:
        ev = m.get("evaluations") or {}
        enriched.append((m, ev, num(ev.get("artificial_analysis_intelligence_index")),
                         blended(m.get("pricing") or {}),
                         num((m.get("performance") or {}).get("median_output_tokens_per_second"))))

    ranked = sorted((e for e in enriched if e[2] is not None), key=lambda e: -e[2])[:20]
    frontier = [ev for _, ev, *_ in ranked]  # coverage = share of these top models with the score
    for cid, (label, key) in BENCH.items():
        its = [item(m, v, price=price, speed=speed, intelligence=intel)
               for m, ev, intel, price, speed in enriched if (v := num(ev.get(key))) is not None]
        its.sort(key=lambda x: -x["score"])
        has = sum(num(ev.get(key)) is not None for ev in frontier)
        cats[cid] = {"metric": label, "items": top(its), "coverage": round(has / len(frontier), 2) if frontier else 0}

    best = max((i for _, _, i, _, _ in enriched if i is not None), default=0)

    def cheapest(cid, share, label):
        its = [item(m, price, price=price, speed=speed, intelligence=intel)
               for m, _, intel, price, speed in enriched
               if intel is not None and price and intel >= share * best]
        its.sort(key=lambda x: x["score"])
        cats[cid] = {"metric": label, "items": top(its), "lowerIsBetter": True, "unit": "$"}

    cheapest("hinta-laatu", 0.8, "$ / 1M tokenia (vähintään 80 % kärjen älykkyydestä)")
    cheapest("budjetti", 0.6, "$ / 1M tokenia (vähintään 60 % kärjen älykkyydestä)")

    fast = [item(m, speed, price=price, speed=speed, intelligence=intel)
            for m, _, intel, price, speed in enriched
            if intel is not None and speed and intel >= 0.7 * best]
    fast.sort(key=lambda x: -x["score"])
    cats["nopeus"] = {"metric": "tokenia / s (vähintään 70 % kärjen älykkyydestä)", "items": top(fast)}

    lat = []
    for m, _, intel, price, speed in enriched:
        t = num((m.get("performance") or {}).get("median_time_to_first_answer_token_seconds"))
        if intel is not None and t and intel >= 0.6 * best:
            lat.append(item(m, t, price=price, speed=speed, intelligence=intel))
    lat.sort(key=lambda x: x["score"])
    cats["viive"] = {"metric": "sekuntia ensimmäiseen vastaussanaan (vähintään 60 % kärjen älykkyydestä)",
                     "items": top(lat), "lowerIsBetter": True, "unit": "s"}
    return cats


def media_category(rows, cid, seen):
    field, scale, meta = SCORING.get(cid, ELO)
    its = []
    for m in rows:
        score = num(m.get(field))
        if score is None:
            continue
        it = item(m, score * scale)
        if seen.get(m["id"]):
            it["seen"] = seen[m["id"]]
        its.append(it)
    its.sort(key=lambda x: x["score"] if meta.get("lowerIsBetter") else -x["score"])
    return {**meta, "items": top(its)}


def inspect(key):
    """Print field names and coverage only (no values) to plan new categories."""
    rows = fetch(LLM_PATH, key)
    print("LLM-malleja:", len(rows))
    cov = {}
    for m in rows:
        for k, v in m.items():
            if not isinstance(v, dict):
                cov[k] = cov.get(k, 0) + (v is not None)
        for group in ("evaluations", "pricing", "performance"):
            for k, v in (m.get(group) or {}).items():
                cov[f"{group}.{k}"] = cov.get(f"{group}.{k}", 0) + (num(v) is not None)
    for k, c in sorted(cov.items()):
        print(f"  {k}: {c}")
    for cid in MEDIA:
        rows = fetch(media_path(cid), key)
        numeric = collections.Counter(k for m in rows for k, v in m.items() if num(v) is not None)
        print(f"{cid}: {len(rows)} mallia, numeeriset {dict(numeric)}")


ISO_DAY = re.compile(r"\d{4}-\d\d-\d\d")


def history_add(hist, day, cats, keep=HIST_DAYS):
    """The history with `day`'s top names per category: one entry per day (a rerun replaces it), oldest first,
    entries older than `keep` days dropped. Categories with an empty list are left out of the day."""
    stored = hist.get("days") if isinstance(hist, dict) else None
    # Only ISO days (YYYY-MM-DD): the cutoff compares strings, and '2026-1-5' would sort after every real day and stay.
    days = [d for d in (stored if isinstance(stored, list) else [])
            if isinstance(d, dict) and isinstance(d.get("date"), str) and ISO_DAY.fullmatch(d["date"]) and isinstance(d.get("top"), dict) and d["date"] != day]
    top = {}
    for cid, c in sorted(cats.items()):
        names = [it["name"] for it in (c.get("items") or []) if isinstance(it, dict) and isinstance(it.get("name"), str)]
        if names:
            top[cid] = names
    days.append({"date": day, "top": top})
    cutoff = (datetime.date.fromisoformat(day) - datetime.timedelta(days=keep - 1)).isoformat()
    return {"days": sorted((d for d in days if d["date"] >= cutoff), key=lambda d: d["date"])}


def history_json(hist):
    """One line per day, so a run's diff is one added (and maybe one dropped) line."""
    rows = ",\n".join(json.dumps(d, ensure_ascii=False, separators=(",", ":")) for d in hist["days"])
    return '{"days": [\n' + rows + "\n]}\n"


def read_history():
    """A broken history file must not stop the rankings update: it starts over (and says so in the log)."""
    try:
        return json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {}
    except (ValueError, OSError) as e:
        print(f"   {HIST.name} ei kelpaa ({e}), aloitetaan alusta")
        return {}


KNOWN = set(BENCH) | set(MEDIA) | {"hinta-laatu", "budjetti", "nopeus", "viive"}


def main():
    key = os.environ.get("AA_API_KEY")
    if not key:
        sys.exit("AA_API_KEY puuttuu")
    if "--inspect" in sys.argv:
        return inspect(key)
    prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    cats = {k: v for k, v in prev.get("categories", {}).items() if k in KNOWN}
    errors = []
    seen = json.loads(SEEN.read_text(encoding="utf-8")) if SEEN.exists() else {}
    now = datetime.datetime.now(datetime.timezone.utc)
    today = now.strftime("%Y-%m-%d")

    fresh = {}
    try:
        fresh.update(llm_categories(fetch(LLM_PATH, key)))
    except Exception as e:  # keep previous LLM data
        errors.append(f"llms: {e}")
    for cid in MEDIA:
        try:
            rows = fetch(media_path(cid), key)
            known = seen.setdefault(cid, {})
            first_fetch = not known  # a new endpoint's existing models aren't all new
            for m in rows:
                known.setdefault(m["id"], "" if first_fetch else today)
            fresh[cid] = media_category(rows, cid, known)
        except Exception as e:
            errors.append(f"{cid}: {e}")

    if not any(c["items"] for c in fresh.values()):
        sys.exit("Kaikki haut epäonnistuivat:\n" + "\n".join(errors))
    for cid, cat in fresh.items():  # an empty result must not blank a list that has data
        if cat["items"] or cid not in cats:
            cats[cid] = cat
        else:
            errors.append(f"{cid}: ei tuloksia")

    out = {"updated": now.strftime("%Y-%m-%dT%H:%MZ"), "source": "https://artificialanalysis.ai/", "errors": errors, "categories": cats}
    OUT.parent.mkdir(exist_ok=True)
    SEEN.write_text(json.dumps(seen, ensure_ascii=False, indent=0, sort_keys=True) + "\n", encoding="utf-8")
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # History: only the categories measured in THIS run (a failed or empty fetch keeps yesterday's list in `cats`,
    # and recording it under today would show a streak that was never measured). It runs after the rankings are
    # written and can never fail the job: an error here is logged and the rankings update still gets committed.
    try:
        measured = {cid: cat for cid, cat in fresh.items() if cat.get("items")}
        HIST.write_text(history_json(history_add(read_history(), today, measured)), encoding="utf-8")
    except Exception as e:  # noqa: BLE001 - the history is an extra, never a reason to lose the run
        errors.append(f"historia: {e}")
    print(f"ok: {len(cats)} kategoriaa, {len(errors)} virhettä")
    for e in errors:
        print("  ", e)


if __name__ == "__main__":
    main()
