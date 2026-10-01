#!/usr/bin/env python3
"""Run check_overlap.py for content files against their sources, fetched automatically.

Usage: python3 scripts/recheck_overlap.py [aine/kerta ...]   # default: every file in data/practice/
Sources: examUrl, gradingUrl (file + section level), <exam dir>/attachments/index.html, and the
session's https sources from YO-tutka data. Pages are fetched with curl and stripped to text.
The text cache lives OUTSIDE the repo (~/.cache/yo-practice-sources): the source texts are copyrighted.
Expected leftovers after a clean-up: material citations (author, title), term/name lists, answer words.
"""
import hashlib, html, json, pathlib, re, subprocess, sys

REPO = pathlib.Path(__file__).resolve().parent.parent
CACHE = pathlib.Path.home() / ".cache" / "yo-practice-sources"
CACHE.mkdir(parents=True, exist_ok=True)


def text_of(url):
    f = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".txt")
    if f.exists():
        return f
    r = subprocess.run(["curl", "-sL", "--max-time", "40", "-A", "Mozilla/5.0", url], capture_output=True)
    raw = r.stdout.decode("utf-8", "replace")
    if not raw or ("<html" not in raw.lower() and "<!doctype" not in raw.lower()):
        f.write_text("", encoding="utf-8")
        return f
    s = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    s = re.sub(r"<title>(.*?)</title>", r" \1 ", s, flags=re.S)   # MathJax SVG titles keep formula text
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    f.write_text(re.sub(r"\s+", " ", s), encoding="utf-8")
    return f


def tutka():
    h = (REPO / "yo-tutka.html").read_text(encoding="utf-8")
    d = json.loads(re.search(r'<script id="yo-data" type="application/json">(.*?)</script>', h, re.S).group(1).replace("<\\/", "</"))
    return {(s["id"], x["id"]): x for s in d for x in s["sessions"]}


def urls_for(path, meta):
    d = json.loads(path.read_text(encoding="utf-8"))
    urls = {d.get("examUrl"), d.get("gradingUrl")}
    for sec in (d.get("exam") or {}).get("sections") or []:
        urls |= {sec.get("examUrl"), sec.get("gradingUrl")}
    urls |= {u for u in (meta.get("sources") or []) if u.startswith("https://") and not u.endswith(".pdf")}
    urls.discard(None)
    for u in list(urls):
        if u.endswith("/index.html") and "attachments" not in u:
            urls.add(u.rsplit("/", 1)[0] + "/attachments/index.html")
    return sorted(urls)


def main(only):
    meta = tutka()
    total = 0
    for path in sorted((REPO / "data/practice").glob("*/*.json")):
        key = f"{path.parent.name}/{path.stem}"
        if only and key not in only:
            continue
        srcs = [str(text_of(u)) for u in urls_for(path, meta.get((path.parent.name, path.stem), {}))]
        srcs = [s for s in srcs if pathlib.Path(s).stat().st_size > 200]
        out = subprocess.run([sys.executable, str(REPO / "scripts/check_overlap.py"), str(path), *srcs], capture_output=True, text=True).stdout
        lines = out.strip().splitlines()
        n = int(lines[-1].split()[0]) if lines else -1
        total += max(n, 0)
        print(f"{key}: {n} osumaa ({len(srcs)} lähdettä)")
        for l in lines[:-1]:
            print("   ", l)
    print("yhteensä", total)


if __name__ == "__main__":
    main(set(sys.argv[1:]))
