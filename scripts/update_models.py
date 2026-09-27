#!/usr/bin/env python3
"""Fetch model rankings from the Artificial Analysis free API and write data/ai-models.json.

Usage: AA_API_KEY=... python3 scripts/update_models.py
Standard library only. A category whose fetch fails keeps its previous data,
so a flaky API never blanks the live page.
"""
import json, os, pathlib, sys, urllib.request, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ai-models.json"
BASE = "https://artificialanalysis.ai/api/v2/data"
TOP_N = 8

PRETTY = {"tau2": "τ²-Bench", "tau_banking": "τ-Banking", "terminalbench_hard": "Terminal-Bench Hard", "terminalbench_v2_1": "Terminal-Bench 2.1"}

MEDIA = {
    "kuva": "media/text-to-image",
    "kuvanmuokkaus": "media/image-editing",
    "video": "media/text-to-video",
    "kuvasta-video": "media/image-to-video",
    "puhe": "media/text-to-speech",
}


def fetch(path, key):
    req = urllib.request.Request(f"{BASE}/{path}", headers={"x-api-key": key, "User-Agent": "koirosvg-ai-opas"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = json.load(r)
    rows = body.get("data", body) if isinstance(body, dict) else body
    if not isinstance(rows, list):
        raise ValueError(f"{path}: unexpected response shape")
    return rows


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


# Benchmark-based text categories: id -> (label, candidate evaluation keys).
# When several keys are listed, the ones nearly all current top models have run are
# averaged (see shared_keys), so every model in a list is scored on the same tests.
BENCH = {
    "yleis": ("Intelligence Index", ["artificial_analysis_intelligence_index"]),
    "koodaus": ("Coding Index", ["artificial_analysis_coding_index"]),
    "matikka": ("Math Index", ["artificial_analysis_math_index"]),
    "automaatio": ("Agenttitestit", ["terminalbench_v2_1", "terminalbench_hard"]),
    "asiakaspalvelu": ("Asiakaspalveluagentit", ["tau2", "tau_banking"]),
    "ohjeet": ("IFBench", ["ifbench"]),
    "pitkat-dokumentit": ("Long Context Reasoning (AA-LCR)", ["lcr"]),
    "tiede": ("GPQA Diamond", ["gpqa"]),
    "vaikeimmat": ("Humanity's Last Exam", ["hle"]),
}


def shared_keys(rows, candidates, frontier=20):
    """Of the candidate keys, those that >= 80 % of the top models (by intelligence) have.
    Measured on the top models so new releases aren't excluded by a retired test."""
    def ev(m):
        return m.get("evaluations") or {}
    ranked = sorted((m for m in rows if num(ev(m).get("artificial_analysis_intelligence_index")) is not None),
                    key=lambda m: -ev(m)["artificial_analysis_intelligence_index"])[:frontier]
    counts = {k: sum(num(ev(m).get(k)) is not None for m in ranked) for k in candidates}
    if not ranked or not any(counts.values()):
        return []
    keys = [k for k in candidates if counts[k] >= 0.8 * len(ranked)]
    return keys or [max(counts, key=counts.get)]


def pct(v):
    return v * 100 if v <= 1 else v


def llm_categories(rows):
    cats = {}
    enriched = []
    for m in rows:
        ev = m.get("evaluations") or {}
        pr = m.get("pricing") or {}
        enriched.append((m, ev, num(ev.get("artificial_analysis_intelligence_index")),
                         num(pr.get("price_1m_blended_3_to_1")),
                         num(m.get("median_output_tokens_per_second"))))

    for cid, (label, candidates) in BENCH.items():
        keys = shared_keys(rows, candidates)
        its = []
        for m, ev, intel, price, speed in enriched:
            vals = [num(ev.get(k)) for k in keys]
            if keys and None not in vals:
                its.append(item(m, sum(map(pct, vals)) / len(vals), price=price, speed=speed, intelligence=intel))
        its.sort(key=lambda x: -x["score"])
        if len(candidates) > 1:
            label += ": " + " + ".join(PRETTY.get(k, k) for k in keys)
        cats[cid] = {"metric": label, "items": top(its)}

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
        t = num(m.get("median_time_to_first_answer_token"))
        if intel is not None and t and intel >= 0.6 * best:
            lat.append(item(m, t, price=price, speed=speed, intelligence=intel))
    lat.sort(key=lambda x: x["score"])
    cats["viive"] = {"metric": "sekuntia ensimmäiseen vastaussanaan (vähintään 60 % kärjen älykkyydestä)",
                     "items": top(lat), "lowerIsBetter": True, "unit": "s"}
    return cats


def media_category(rows):
    its = [item(m, num(m.get("elo"))) for m in rows if num(m.get("elo")) is not None]
    its.sort(key=lambda x: -x["score"])
    cat = {"metric": "Arena ELO", "items": top(its)}
    # Per style/subject breakdowns (include_categories=true), e.g. "Text & Typography".
    sub = {}
    for m in rows:
        for c in m.get("categories") or []:
            elo = num(c.get("elo"))
            label = next((v for k, v in c.items() if k.endswith("_category") and v), None)
            if elo is not None and label:
                sub.setdefault(label, []).append(item(m, elo))
    if sub:
        cat["subcategories"] = {k: top(sorted(v, key=lambda x: -x["score"])) for k, v in sorted(sub.items())}
    return cat


def inspect(key):
    """Print field names and coverage only (no values) to plan new categories."""
    rows = fetch("llms/models", key)
    print("LLM-malleja:", len(rows))
    cov = {}
    for m in rows:
        for k, v in m.items():
            if not isinstance(v, dict):
                cov[k] = cov.get(k, 0) + (v is not None)
        for group in ("evaluations", "pricing"):
            for k, v in (m.get(group) or {}).items():
                cov[f"{group}.{k}"] = cov.get(f"{group}.{k}", 0) + (num(v) is not None)
    for k, c in sorted(cov.items()):
        print(f"  {k}: {c}")
    for cid, path in MEDIA.items():
        rows = fetch(path + "?include_categories=true", key)
        print(f"{cid}: {len(rows)} mallia, kentät {sorted(rows[0]) if rows else []}")
        cats = {}
        for m in rows:
            for c in m.get("categories") or []:
                label = " / ".join(f"{k}={v}" for k, v in c.items() if k.endswith("_category") and v)
                cats[label] = cats.get(label, 0) + 1
        for label, c in sorted(cats.items()):
            print(f"    {label}: {c}")


def main():
    key = os.environ.get("AA_API_KEY")
    if not key:
        sys.exit("AA_API_KEY puuttuu")
    if "--inspect" in sys.argv:
        return inspect(key)
    prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    cats = dict(prev.get("categories", {}))
    errors = []

    try:
        cats.update(llm_categories(fetch("llms/models", key)))
    except Exception as e:  # keep previous LLM data
        errors.append(f"llms: {e}")
    for cid, path in MEDIA.items():
        try:
            cats[cid] = media_category(fetch(path + "?include_categories=true", key))
        except Exception as e:
            errors.append(f"{cid}: {e}")

    if len(errors) == 1 + len(MEDIA):
        sys.exit("Kaikki haut epäonnistuivat:\n" + "\n".join(errors))

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    out = {"updated": now, "source": "https://artificialanalysis.ai/", "errors": errors, "categories": cats}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"ok: {len(cats)} kategoriaa, {len(errors)} virhettä")
    for e in errors:
        print("  ", e)


if __name__ == "__main__":
    main()
