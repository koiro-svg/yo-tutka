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
        if not re.fullmatch(r"[a-z0-9-]+", aid) or aid in ids:
            err(f"bad or duplicate area id: {aid!r}")
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
    if errors:
        print("INVALID:\n- " + "\n- ".join(errors))
        sys.exit(1)
    n = sum(len(a["tools"]) for a in d["areas"])
    print(f"OK: {len(d['areas'])} areas, {n} tools, {len(d['changes'])} changes, updated {d['updated']}")
    print(f"OK: {len(g['agents'])} coding agents, updated {g['updated']}")


if __name__ == "__main__":
    main()
