#!/usr/bin/env python3
"""Validate data/ai-tools.json before it is committed.

Usage: python3 scripts/validate_tools.py
Also runs as Vercel's buildCommand, so invalid data never replaces the live deploy.
Compares against the version live on LIVE_URL (fallback: origin/main) to block
runaway rewrites: areas must stay the same and only MAX_SWAPS tools may be
added/removed per update, unless `revision` is raised (manual restructuring only).
Standard library only. Exit code 1 on any error.
"""
import json, pathlib, re, subprocess, sys, datetime, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ai-tools.json"
LIVE_URL = "https://koirosvg.com/data/ai-tools.json"
KINDS = {"avustaa", "automatisoi"}
FI = {"hyvä", "kohtalainen", "heikko", "?"}
LIMITS = {"name": 70, "vendor": 60, "bestFor": 170, "why": 420, "price": 150}
TEXT_MAX = 300         # starter, area and change texts
MAX_SWAPS = 8          # tools added + removed across the whole page per run
MAX_CHANGES = 20


def text(v, lim=TEXT_MAX):
    """Non-empty plain string within the length limit and without HTML brackets."""
    return isinstance(v, str) and bool(v.strip()) and len(v) <= lim and not re.search(r"[<>]", v)


def validate(d, errors):
    err = errors.append

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
            if not re.fullmatch(r"https://[^\s\"'<>]+", str(t.get("url", ""))):
                err(f"{aid}/{n}: url must be https")
            if t.get("kind") not in KINDS:
                err(f"{aid}/{n}: kind must be one of {sorted(KINDS)}")
            if t.get("fi") not in FI:
                err(f"{aid}/{n}: fi must be one of {sorted(FI)}")
            if not isinstance(t.get("pick"), bool):
                err(f"{aid}/{n}: pick must be true/false")


def tool_keys(d):
    return {(a["id"], t["name"].lower()) for a in d["areas"] for t in a["tools"]}


def live_version():
    """(source, data) of the currently published version, or None if unavailable."""
    try:
        req = urllib.request.Request(LIVE_URL, headers={"User-Agent": "koirosvg-validate"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return LIVE_URL, json.load(r)
    except Exception:
        pass
    r = subprocess.run(["git", "show", "origin/main:data/ai-tools.json"], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode == 0:
        return "origin/main", json.loads(r.stdout)
    return None


def main():
    errors = []
    d = json.loads(DATA.read_text(encoding="utf-8"))
    validate(d, errors)
    live = None if errors else live_version()
    if live and d["revision"] > live[1].get("revision", 0):
        print(f"note: revision raised, structural comparison with {live[0]} skipped")
    elif live:
        ref, old = live
        if [a["id"] for a in old["areas"]] != [a["id"] for a in d["areas"]]:
            errors.append(f"area ids or their order differ from {ref}; raise revision for manual restructuring")
        swaps = len(tool_keys(old) ^ tool_keys(d))
        if swaps > MAX_SWAPS:
            errors.append(f"{swaps} tools added/removed vs {ref} (max {MAX_SWAPS})")
    elif not errors:
        print("note: live version unavailable, structural comparison skipped")
    if errors:
        print("INVALID:\n- " + "\n- ".join(errors))
        sys.exit(1)
    n = sum(len(a["tools"]) for a in d["areas"])
    print(f"OK: {len(d['areas'])} areas, {n} tools, {len(d['changes'])} changes, updated {d['updated']}")


if __name__ == "__main__":
    main()
