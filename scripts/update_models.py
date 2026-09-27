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
    d = {"name": m.get("name") or m.get("slug") or "?", "creator": creator(m),
         "score": round(score, 2), "released": m.get("release_date")}
    d.update({k: round(v, 2) for k, v in extra.items() if v is not None})
    return d


def top(items, n=TOP_N):
    seen, out = set(), []
    for it in items:
        if it["name"] in seen:
            continue
        seen.add(it["name"])
        out.append(it)
        if len(out) == n:
            break
    return out


def agentic_metric(ev):
    """Prefer a dedicated agentic index; fall back to agentic benchmarks, then intelligence."""
    for k, v in ev.items():
        if "agentic" in k and num(v) is not None:
            return k, v
    parts = [(k, num(v)) for k, v in ev.items()
             if any(s in k for s in ("tau2", "terminalbench", "terminal_bench")) and num(v) is not None]
    if parts:
        vals = [v * 100 if v <= 1 else v for _, v in parts]
        return "+".join(k for k, _ in parts), sum(vals) / len(vals)
    return None, None


def llm_categories(rows):
    cats = {}
    enriched = []
    for m in rows:
        ev = m.get("evaluations") or {}
        pr = m.get("pricing") or {}
        enriched.append((m, ev, num(ev.get("artificial_analysis_intelligence_index")),
                         num(pr.get("price_1m_blended_3_to_1")),
                         num(m.get("median_output_tokens_per_second"))))

    def ranked(cid, metric_label, key_fn):
        its = []
        for m, ev, intel, price, speed in enriched:
            s = key_fn(ev)
            if s is not None:
                its.append(item(m, s, price=price, speed=speed, intelligence=intel))
        its.sort(key=lambda x: -x["score"])
        cats[cid] = {"metric": metric_label, "items": top(its)}

    ranked("yleis", "Intelligence Index", lambda ev: num(ev.get("artificial_analysis_intelligence_index")))
    ranked("koodaus", "Coding Index", lambda ev: num(ev.get("artificial_analysis_coding_index")))
    ranked("matikka", "Math Index", lambda ev: num(ev.get("artificial_analysis_math_index")))

    used = set()
    def agentic(ev):
        k, v = agentic_metric(ev)
        if k:
            used.add(k)
        return v
    ranked("automaatio", "agentti", agentic)
    if cats["automaatio"]["items"]:
        cats["automaatio"]["metric"] = ", ".join(sorted(used))
    else:  # no agentic data in the free API: fall back to general intelligence, labelled honestly
        cats["automaatio"] = dict(cats["yleis"], metric="Intelligence Index (agenttimittaria ei saatavilla)")

    best = max((i for _, _, i, _, _ in enriched if i is not None), default=0)
    value = [item(m, price, price=price, speed=speed, intelligence=intel)
             for m, _, intel, price, speed in enriched
             if intel is not None and price and intel >= 0.8 * best]
    value.sort(key=lambda x: x["score"])
    cats["hinta-laatu"] = {"metric": "$ / 1M tokenia (vähintään 80 % kärjen älykkyydestä)", "items": top(value), "lowerIsBetter": True}

    fast = [item(m, speed, price=price, speed=speed, intelligence=intel)
            for m, _, intel, price, speed in enriched
            if intel is not None and speed and intel >= 0.7 * best]
    fast.sort(key=lambda x: -x["score"])
    cats["nopeus"] = {"metric": "tokenia / s (vähintään 70 % kärjen älykkyydestä)", "items": top(fast)}
    return cats


def media_category(rows):
    its = [item(m, num(m.get("elo"))) for m in rows if num(m.get("elo")) is not None]
    its.sort(key=lambda x: -x["score"])
    return {"metric": "Arena ELO", "items": top(its)}


def main():
    key = os.environ.get("AA_API_KEY")
    if not key:
        sys.exit("AA_API_KEY puuttuu")
    prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    cats = dict(prev.get("categories", {}))
    errors = []

    try:
        cats.update(llm_categories(fetch("llms/models", key)))
    except Exception as e:  # keep previous LLM data
        errors.append(f"llms: {e}")
    for cid, path in MEDIA.items():
        try:
            cats[cid] = media_category(fetch(path, key))
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
