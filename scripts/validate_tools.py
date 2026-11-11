#!/usr/bin/env python3
"""Validate data/ai-tools.json and data/coding-agents.json before they are committed.

Usage: python3 scripts/validate_tools.py
Also runs as Vercel's buildCommand, so invalid data never replaces the live deploy.
Compares against the version live on koirosvg.com (fallback: origin/main) to block
runaway rewrites: areas must stay the same and only MAX_SWAPS tools (MAX_AGENT_SWAPS
coding agents) may be added/removed per update, unless `revision` is raised
(manual restructuring only). Standard library only. Exit code 1 on any error.
"""
import json, pathlib, re, subprocess, sys, datetime, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ai-tools.json"
MODELS = ROOT / "data" / "ai-models.json"
AGENTS = ROOT / "data" / "coding-agents.json"
LIVE = "https://koirosvg.com/"
KINDS = {"avustaa", "automatisoi"}
FI = {"hyvä", "kohtalainen", "heikko", "?"}
LIMITS = {"name": 70, "vendor": 60, "bestFor": 170, "why": 420, "price": 150}
TEXT_MAX = 300         # starter, area and change texts
MAX_SWAPS = 8          # tools added + removed across the whole page per run
MAX_CHANGES = 20
SURFACES = {"cli", "ide", "app", "web", "cloud"}
AGENT_LIMITS = {"name": 40, "vendor": 60, "models": 160, "price": 150, "bestFor": 170, "why": 420}
MAX_AGENT_SWAPS = 3    # coding agents added + removed per run


# ai.html's own anchors (tabs, model groups, ranking cards); an area id must not shadow them.
RESERVED_IDS = {"mallit", "tyokalut", "muutokset", "koodausagentit", "teksti", "hinta", "kuva", "video", "aani",
                "agent-index", "agent-cost", "agent-speed", "compare", "news", "status", "areas", "tasks", "budget",
                "answer", "q", "tabs", "datastate", "cmpbar"}


def text(v, lim=TEXT_MAX):
    """Non-empty plain string within the length limit and without HTML brackets."""
    return isinstance(v, str) and bool(v.strip()) and len(v) <= lim and not re.search(r"[<>]", v)


def https(v):
    return bool(re.fullmatch(r"https://[^\s\"'<>]+", str(v)))


def num(v, lo, hi):
    """A real number (not bool) with lo < v <= hi."""
    return isinstance(v, (int, float)) and not isinstance(v, bool) and lo < v <= hi


def validate_header(d, err):
    """`updated` (ISO 8601 with timezone, not in the future) and integer `revision`."""
    try:
        updated = datetime.datetime.fromisoformat(d["updated"].replace("Z", "+00:00"))
        if updated.tzinfo is None:
            err("updated must include a timezone, e.g. 2026-09-30T04:20:00Z")
        elif updated > datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1):
            err("updated is in the future")
    except (KeyError, ValueError, AttributeError):
        err("updated missing or not ISO 8601")
    if not isinstance(d.get("revision"), int):
        err("revision must be an integer")


def validate(d, errors):
    err = errors.append
    validate_header(d, err)

    starter = d.get("starter")
    if not isinstance(starter, list) or not 3 <= len(starter) <= 6:
        err("starter must have 3-6 items")
    else:
        for s in starter:
            for k in ("role", "name", "why"):
                if not text(s.get(k)):
                    err(f"starter {k} missing, too long or has < >")

    changes = d.get("changes")
    if not isinstance(changes, list) or len(changes) > MAX_CHANGES:
        err(f"changes must be a list of at most {MAX_CHANGES}")
    else:
        dates = []
        for c in changes:
            try:
                datetime.date.fromisoformat(str(c.get("date", "")))
            except ValueError:
                err(f"change has bad date (YYYY-MM-DD): {c!r}")
            if not text(c.get("text")) or len(c["text"]) < 10:
                err(f"change text missing, too long or has < >: {c!r}")
            dates.append(c.get("date", ""))
        if dates != sorted(dates, reverse=True):
            err("changes must be newest first")

    areas = d.get("areas")
    if not isinstance(areas, list) or not 10 <= len(areas) <= 18:
        err("areas must have 10-18 items")
        return
    ids = set()
    for a in areas:
        aid = a.get("id", "")
        # ai.html shares one #hash namespace: no hyphen (tool cards are t-<area>-<name>) and no page id.
        if not re.fullmatch(r"[a-z0-9]+", aid) or aid in ids or aid in RESERVED_IDS:
            err(f"bad, duplicate or reserved area id: {aid!r}")
        ids.add(aid)
        for k in ("title", "intro"):
            if not text(a.get(k)):
                err(f"{aid}: {k} missing, too long or has < >")
        tools = a.get("tools")
        if not isinstance(tools, list) or not 3 <= len(tools) <= 7:
            err(f"{aid}: must have 3-7 tools")
            continue
        if sum(t.get("pick") is True for t in tools) != 1:
            err(f"{aid}: exactly one tool must have pick=true")
        names = set()
        for t in tools:
            n = t.get("name", "")
            if n.lower() in names:
                err(f"{aid}: duplicate tool {n!r}")
            names.add(n.lower())
            for k, lim in LIMITS.items():
                if not text(t.get(k), lim):
                    err(f"{aid}/{n}: {k} missing, longer than {lim} or has < >")
            if not https(t.get("url", "")):
                err(f"{aid}/{n}: url must be https")
            if t.get("kind") not in KINDS:
                err(f"{aid}/{n}: kind must be one of {sorted(KINDS)}")
            if t.get("fi") not in FI:
                err(f"{aid}/{n}: fi must be one of {sorted(FI)}")
            if not isinstance(t.get("pick"), bool):
                err(f"{aid}/{n}: pick must be true/false")


def validate_agents(d, errors):
    err = errors.append
    validate_header(d, err)
    for k, lim in (("indexName", 60), ("indexEvals", 120)):
        if not text(d.get(k), lim):
            err(f"{k} missing, longer than {lim} or has < >")
    if not https(d.get("source", "")):
        err("source must be https")
    agents = d.get("agents")
    if not isinstance(agents, list) or not 4 <= len(agents) <= 12:
        err("agents must have 4-12 items")
        return
    names = set()
    for a in agents:
        n = a.get("name", "")
        if n.lower() in names:
            err(f"duplicate agent {n!r}")
        names.add(n.lower())
        for k, lim in AGENT_LIMITS.items():
            if not text(a.get(k), lim):
                err(f"{n}: {k} missing, longer than {lim} or has < >")
        if not https(a.get("url", "")):
            err(f"{n}: url must be https")
        s = a.get("surfaces")
        if not isinstance(s, list) or not s or len(set(s)) != len(s) or not set(s) <= SURFACES:
            err(f"{n}: surfaces must be a non-empty list of unique {sorted(SURFACES)}")
        if not isinstance(a.get("openSource"), bool):
            err(f"{n}: openSource must be true/false")
        if a.get("repo") is not None and not https(a["repo"]):
            err(f"{n}: repo must be https or null")
        aa = a.get("aa")
        if aa is not None and not (isinstance(aa, dict) and num(aa.get("index"), 0, 100)
                                   and num(aa.get("costPerTask"), 0, 1000)
                                   and num(aa.get("minutesPerTask"), 0, 1440) and text(aa.get("model"), 60)):
            err(f"{n}: aa must be null or have index 0-100, costPerTask (USD), minutesPerTask and model")
    if sum(a.get("aa") is not None for a in agents) < 3:
        err("at least 3 agents need aa results")


def tool_keys(d):
    return {(a["id"], t["name"].lower()) for a in d["areas"] for t in a["tools"]}


def agent_names(d):
    return {a["name"].lower() for a in d["agents"]}


live_down = False   # after one failed fetch, skip the network for the other file


def live_version(name):
    """(source, data) of the currently published data/<name>, or None if unavailable."""
    global live_down
    url = LIVE + "data/" + name
    if not live_down:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "koirosvg-validate"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return url, json.load(r)
        except urllib.error.HTTPError:
            pass    # host is up, file is not published yet
        except Exception:
            live_down = True
    r = subprocess.run(["git", "show", f"origin/main:data/{name}"], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode == 0:
        return "origin/main", json.loads(r.stdout)
    return None


def compare(path, d, errors, check):
    """Run check(ref, old, d, errors) against the live version unless revision was raised."""
    live = live_version(path.name)
    if live and d["revision"] > live[1].get("revision", 0):
        print(f"note: {path.name} revision raised, structural comparison with {live[0]} skipped")
    elif live:
        check(*live, d, errors)
    else:
        print(f"note: live {path.name} unavailable, structural comparison skipped")


def check_tools(ref, old, d, errors):
    if [a["id"] for a in old["areas"]] != [a["id"] for a in d["areas"]]:
        errors.append(f"area ids or their order differ from {ref}; raise revision for manual restructuring")
    swaps = len(tool_keys(old) ^ tool_keys(d))
    if swaps > MAX_SWAPS:
        errors.append(f"{swaps} tools added/removed vs {ref} (max {MAX_SWAPS})")


def check_agents(ref, old, d, errors):
    swaps = len(agent_names(old) ^ agent_names(d))
    if swaps > MAX_AGENT_SWAPS:
        errors.append(f"{swaps} coding agents added/removed vs {ref} (max {MAX_AGENT_SWAPS})")


PAGE = ROOT / "ai.html"
TASK_RE = re.compile(r"\{id:'([\w-]+)', label:'[^']*'(?:, cat:'[\w-]+')?, area:'(\w+)'(?:, agent:true)?(?:, tool:'([^']+)')?\},")
# ai.html's isFree(): a price that starts with "Ilmainen" is a free tier, "Ilmainen kokeilu" is a trial.
FREE_JS = r"/^ilmainen(?!\s+kokeilu)/i"
FREE_RE = re.compile(r"^ilmainen(?!\s+kokeilu)", re.I)


def is_free(price):
    return bool(FREE_RE.match(str(price or "").strip()))


def tool_free(t):
    """ai.html's toolFree(): the tool's own `free` flag wins, the price text is the fallback."""
    return t["free"] if isinstance(t.get("free"), bool) else is_free(t.get("price"))


def check_free(d):
    """Warnings (never errors) for the optional `free` flag: wrong type, or a flag the price text contradicts."""
    warnings = []
    for a in d["areas"]:
        for t in a["tools"]:
            n, f, price = t["name"], t.get("free"), str(t.get("price", ""))
            if f is None:
                continue
            if not isinstance(f, bool):
                warnings.append(f"{a['id']}/{n}: free must be true/false (ignored, the page reads the price text)")
            # A free tier, not a trial (UPDATE_TOOLS.md): "Ilmainen kokeilu" or "7 vrk ilmainen kokeilu" alone is no free tier.
            elif f and not re.search(r"ilmai(?!\w*\s+kokeilu)|(?<![\d,.])0 [€$]", price, re.I):
                warnings.append(f"{a['id']}/{n}: free=true but the price text names no free tier ({price!r})")
            elif not f and is_free(price):
                warnings.append(f"{a['id']}/{n}: free=false but the price starts with a free tier ({price!r})")
    return warnings


# A model name in a tool's name: a family ("GPT Image", "Kling") followed by a version ("2.5", "v4").
VERSION_RE = re.compile(r"^(.*?[a-z].*?)[\s-]+v?(\d+(?:\.\d+)*)(?![\d.])", re.I)


def version_key(v):
    return tuple(int(x) for x in v.split("."))


def family(name):
    """(family, version) of a model name, e.g. 'GPT Image 2.6 Sunburst' -> ('gpt image', (2, 6)); None without a version."""
    m = VERSION_RE.match(name.strip())
    if not m:
        return None
    fam = re.sub(r"[\s-]+", " ", m.group(1)).strip().lower()
    return (fam, version_key(m.group(2))) if fam else None


def check_versions(d, models):
    """Warn (never fail) when a tool's name names an older version of a model family the rankings already list.

    Example: tool "GPT Image 2.5 (ChatGPT)" while ai-models.json ranks "GPT Image 2.6 Sunburst"."""
    newest = {}
    for c in (models.get("categories") or {}).values():
        for it in c.get("items") or []:
            fv = family(str(it.get("name", "")))
            if fv and (fv[0] not in newest or fv[1] > newest[fv[0]][0]):
                newest[fv[0]] = (fv[1], it["name"])
    warnings = []
    for a in d["areas"]:
        for t in a["tools"]:
            name = re.sub(r"[\s-]+", " ", t["name"]).lower()
            for fam, (ver, model) in newest.items():
                for m in re.finditer(r"(?<![a-z0-9])" + re.escape(fam) + r" v?(\d+(?:\.\d+)*)(?![\d.])", name):
                    if version_key(m.group(1)) < ver:
                        warnings.append(f"{a['id']}/{t['name']}: names {fam} {m.group(1)}, the rankings already list {model!r}")
    return warnings


def load_models():
    """ai-models.json for the version check, or None (the check is advisory, so a broken file only warns)."""
    try:
        m = json.loads(MODELS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    # Only the shape the check reads: a dict of categories whose items are dicts (anything else: no version check).
    cats = m.get("categories") if isinstance(m, dict) else None
    if not isinstance(cats, dict) or not all(isinstance(c, dict) and isinstance(c.get("items", []), list) and all(isinstance(i, dict) for i in c.get("items", [])) for c in cats.values()):
        return None
    return m


def check_history():
    """data/ai-history.json (update_models.py, ai-F3): warnings only, the page skips bad rows and works without the file."""
    path = MODELS.parent / "ai-history.json"
    if not path.exists():
        return ["data/ai-history.json missing: the models tab shows no rank changes"]
    try:
        days = json.loads(path.read_text(encoding="utf-8"))["days"]
    except (OSError, ValueError, KeyError, TypeError):
        return ["data/ai-history.json unreadable: the models tab shows no rank changes"]
    if not isinstance(days, list):   # e.g. {"days": null}: a warning, never a crash of the build
        return ["data/ai-history.json: days is not a list (the models tab shows no rank changes)"]
    bad = [d for d in days if not (isinstance(d, dict) and isinstance(d.get("date"), str)
                                   and re.fullmatch(r"\d{4}-\d\d-\d\d", d["date"]) and isinstance(d.get("top"), dict))]
    dates = [d["date"] for d in days if d not in bad]
    out = [f"data/ai-history.json: {len(bad)} malformed day(s) (the page skips them)"] if bad else []
    if dates != sorted(set(dates)):
        out.append("data/ai-history.json: days must be unique and oldest first")
    return out


def check_page(d, errors):
    """ai.html's "Mitä haluat tehdä?" wiring against the data, and guards for logic fixed on 10.11.2026.

    Returns warnings (printed, never fail the build: the page falls back to the area's pick)."""
    page, warnings = PAGE.read_text(encoding="utf-8"), []
    block = page.split("const TASKS = [", 1)[-1].split("];", 1)[0]
    rows = [ln.strip() for ln in block.splitlines() if ln.strip().startswith("{id:")]
    tasks = [TASK_RE.fullmatch(r) for r in rows]
    if not rows or not all(tasks):
        errors.append("ai.html: TASKS rows are not in the shape validate_tools.py reads (id, label, cat, area, agent, tool)")
        return warnings
    areas = {a["id"]: a for a in d["areas"]}
    for tid, area, tool in (m.groups() for m in tasks):
        if area not in areas:
            errors.append(f"ai.html: task {tid!r} points to area {area!r}, which is not in ai-tools.json")
        elif tool and not any(t["name"].lower().startswith(tool.lower()) for t in areas[area]["tools"]):
            warnings.append(f"ai.html: task {tid!r} names tool {tool!r}, not found in area {area!r} (the page shows the area's pick)")
    if FREE_JS not in page:
        errors.append("ai.html: isFree() must stay " + FREE_JS + " (a free trial is not a free alternative)")
    if "location.hash.length > 1 ? ui.tab : 'mallit'" not in page:
        errors.append("ai.html: fromUrl() must fall back to the first tab when the URL has no #hash (Back to /ai)")
    # The page forecasts the next models update from a copy of the workflow's cron: the two must be the same line.
    flow = ROOT / ".github" / "workflows" / "update-models.yml"
    cron = re.search(r'cron:\s*"([^"]+)"', flow.read_text(encoding="utf-8")) if flow.exists() else None
    if cron and f"const MODELS_CRON = '{cron.group(1)}';" not in page:
        errors.append(f"ai.html: MODELS_CRON must equal the cron in update-models.yml ({cron.group(1)!r})")
    cases = {"Ilmainen · Pro 20 $/kk": True, "Ilmainen (rajattu)": True, "ilmainen 1 000 krediittiä": True,
             "Ilmainen kokeilu · Creator ~29 $/kk": False, "7 vrk ilmainen kokeilu · Hobby 40 $/kk": False,
             "Rajattu ilmaisversiossa": False, "299 $/kk, 3 000 ilmaista": False, "": False}
    for price, want in cases.items():
        if is_free(price) != want:
            errors.append(f"is_free({price!r}) should be {want}")
    if "area.tools.find(toolFree)" not in page:
        errors.append("ai.html: answerHtml() must pick the free alternative with toolFree() (the `free` flag before the price text)")
    vcases = {("GPT Image 2.5 (ChatGPT)", "GPT Image 2.6 Sunburst"): True, ("Kling 4.0", "Kling 3.0 Omni"): False,
              ("ChatGPT", "GPT-6.1 Sol"): False, ("Veo 3.1 / Flow", "Veo 3.2"): True, ("Suno v5", "Suno v6-mini"): True}
    for (tool, model), want in vcases.items():
        got = check_versions({"areas": [{"id": "x", "tools": [{"name": tool}]}]},
                             {"categories": {"c": {"items": [{"name": model}]}}})
        if bool(got) != want:
            errors.append(f"check_versions({tool!r} vs {model!r}) should {'' if want else 'not '}warn")
    models = load_models()
    if models is None:
        warnings.append("data/ai-models.json unreadable: tool names were not checked against the rankings")
    else:
        warnings += check_versions(d, models)
    return warnings + check_free(d) + check_history()


def main():
    errors, loaded = [], []
    for path, check, structure in ((DATA, validate, check_tools), (AGENTS, validate_agents, check_agents)):
        d, errs = json.loads(path.read_text(encoding="utf-8")), []
        check(d, errs)
        if not errs:
            compare(path, d, errs, structure)
        errors += [f"{path.name}: {e}" for e in errs]
        loaded.append(d)
    d, g = loaded
    warnings = check_page(d, errors) if not errors else []
    for w in warnings:
        print("warning: " + w)
    if errors:
        print("INVALID:\n- " + "\n- ".join(errors))
        sys.exit(1)
    n = sum(len(a["tools"]) for a in d["areas"])
    print(f"OK: {len(d['areas'])} areas, {n} tools, {len(d['changes'])} changes, updated {d['updated']}")
    print(f"OK: {len(g['agents'])} coding agents, updated {g['updated']}")
    free = sum(1 for a in d["areas"] if any(tool_free(t) for t in a["tools"]))
    print(f"OK: ai.html tasks match the data ({free}/{len(d['areas'])} areas have a free tool)")


if __name__ == "__main__":
    main()
