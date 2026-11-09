#!/usr/bin/env python3
"""Fetch model rankings from the Artificial Analysis free API and write data/ai-models.json.

Usage: AA_API_KEY=... python3 scripts/update_models.py
Standard library only. A category whose fetch fails keeps its previous data,
so a flaky API never blanks the live page.
"""
import json, os, pathlib, sys, urllib.request, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ai-models.json"
SEEN = ROOT / "data" / "media-seen.json"  # media model id -> first day seen; the free API has no media release dates
BASE = "https://artificialanalysis.ai/api/v2"
LLM_PATH = "language/models/free"
TOP_N = 8

ARENA = {"metric": "Arena ELO"}
# Category id -> (path, score field, category metadata written to the data file).
MEDIA = {
    "kuva": ("media/text-to-image/models/free", "elo", ARENA),
    "kuvanmuokkaus": ("media/image-editing/models/free", "elo", ARENA),
    "video": ("media/text-to-video/models/free", "elo", ARENA),
    "kuvasta-video": ("media/image-to-video/models/free", "elo", ARENA),
    "video-aani": ("media/text-to-video-audio/models/free", "elo", ARENA),
    "kuvasta-video-aani": ("media/image-to-video-audio/models/free", "elo", ARENA),
    "puhe": ("media/text-to-speech/models/free", "elo", ARENA),
    "musiikki": ("media/music/with-vocals/models/free", "elo", ARENA),
    "musiikki-instrumentaali": ("media/music/instrumental/models/free", "elo", ARENA),
    "puheentunnistus": ("media/speech-to-text/models/free", "aa_wer_index",
                        {"metric": "AA-WER (sanavirheet)", "lowerIsBetter": True, "unit": "%"}),
    "puheagentti": ("media/speech-to-speech/models/free", "tau_voice_score", {"metric": "τ-Voice"}),
}


def fetch(path, key):
    """All rows of a list endpoint; the language endpoint is paginated, the media ones are not."""
    rows, page = [], 1
    while True:
        url = f"{BASE}/{path}" + (f"?page={page}" if page > 1 else "")
        req = urllib.request.Request(url, headers={"x-api-key": key, "User-Agent": "koirosvg-ai-opas"})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.load(r)
        if not isinstance(body, dict) or not isinstance(body.get("data"), list):
            raise ValueError(f"{path}: unexpected response shape")
        rows += body["data"]
        if not (body.get("pagination") or {}).get("has_more"):
            return rows
        page += 1


def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def creator(m):
    c = m.get("model_creator") or {}
    return c.get("name") if isinstance(c, dict) else str(c)


def item(m, score, **extra):
    full = m.get("name") or m.get("slug") or "?"
    base, _, variant = full.partition(" (")
    d = {"name": base, "creator": creator(m),
         "score": round(score, 2), "released": m.get("release_date")}
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


def coverage(rows, key, frontier=20):
    """Share of the top models (by intelligence) that have this score."""
    def ev(m):
        return m.get("evaluations") or {}
    ranked = sorted((m for m in rows if num(ev(m).get("artificial_analysis_intelligence_index")) is not None),
                    key=lambda m: -ev(m)["artificial_analysis_intelligence_index"])[:frontier]
    return round(sum(num(ev(m).get(key)) is not None for m in ranked) / len(ranked), 2) if ranked else 0


def pct(v):
    return v * 100 if v <= 1 else v


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

    for cid, (label, key) in BENCH.items():
        its = [item(m, pct(num(ev.get(key))), price=price, speed=speed, intelligence=intel)
               for m, ev, intel, price, speed in enriched if num(ev.get(key)) is not None]
        its.sort(key=lambda x: -x["score"])
        cats[cid] = {"metric": label, "items": top(its), "coverage": coverage(rows, key)}

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


def media_category(rows, field, meta, seen):
    its = []
    for m in rows:
        score = num(m.get(field))
        if score is None:
            continue
        it = item(m, score)
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
    for cid, (path, _, _) in MEDIA.items():
        rows = fetch(path, key)
        numeric = {k: sum(num(m.get(k)) is not None for m in rows) for m0 in rows[:1] for k in m0}
        print(f"{cid}: {len(rows)} mallia, numeeriset {({k: c for k, c in numeric.items() if c})}")


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
    baseline = not seen  # the first run must not mark every existing model as new
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    try:
        cats.update(llm_categories(fetch(LLM_PATH, key)))
    except Exception as e:  # keep previous LLM data
        errors.append(f"llms: {e}")
    for cid, (path, field, meta) in MEDIA.items():
        try:
            rows = fetch(path, key)
            for m in rows:
                seen.setdefault(m["id"], "" if baseline else today)
            cats[cid] = media_category(rows, field, meta, seen)
        except Exception as e:
            errors.append(f"{cid}: {e}")

    if len(errors) == 1 + len(MEDIA):
        sys.exit("Kaikki haut epäonnistuivat:\n" + "\n".join(errors))

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    out = {"updated": now, "source": "https://artificialanalysis.ai/", "errors": errors, "categories": cats}
    OUT.parent.mkdir(exist_ok=True)
    SEEN.write_text(json.dumps(seen, ensure_ascii=False, indent=0, sort_keys=True) + "\n", encoding="utf-8")
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"ok: {len(cats)} kategoriaa, {len(errors)} virhettä")
    for e in errors:
        print("  ", e)


if __name__ == "__main__":
    main()
