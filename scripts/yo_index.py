#!/usr/bin/env python3
"""Files generated from yo-tutka.html's yo-data block and build date (window.YO_BUILT), so they can never drift from it:
- data/yo-topics.json: subjects and topics (id, name, description) for the site search (site-search.js, julkinen-6),
- index.html's data-yo-built="YYYY-MM-DD" on the YO card: the radar blip's freshness (julkinen-5) without loading the
  400 KB page.
Fails (exit 1) when either differs from what yo-tutka.html gives; `--write` regenerates both. Run by vercel.json's
buildCommand and by ~/sovellukset/yo-tutka/koosta.py after it has written the data. Standard library only."""
import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPICS = ROOT / 'data' / 'yo-topics.json'
HOME = ROOT / 'index.html'
BUILT_ATTR = re.compile(r'data-yo-built="[^"]*"')


def expected():
    html = (ROOT / 'yo-tutka.html').read_text(encoding='utf-8')
    data = json.loads(re.search(r'<script id="yo-data" type="application/json">(.*?)</script>', html, re.S).group(1).replace('<\\/', '</'))
    d, m, y = re.search(r"window\.YO_BUILT \|\| '(\d{1,2})\.(\d{1,2})\.(\d{4})'", html).groups()
    built = datetime.date(int(y), int(m), int(d)).isoformat()
    topics = {'built': built, 'subjects': [
        {'id': s['id'], 'name': s['name'], 'topics': [{'id': t['id'], 'name': t['name'], 'description': t.get('description') or ''} for t in s.get('topics') or []]}
        for s in data]}
    return built, json.dumps(topics, ensure_ascii=False, indent=1) + '\n'


def main():
    write = '--write' in sys.argv
    built, topics = expected()
    home = HOME.read_text(encoding='utf-8')
    if len(BUILT_ATTR.findall(home)) != 1:
        print('yo_index: index.html needs exactly one data-yo-built attribute', file=sys.stderr)
        return 1
    new_home = BUILT_ATTR.sub(f'data-yo-built="{built}"', home)
    old_topics = TOPICS.read_text(encoding='utf-8') if TOPICS.exists() else ''
    stale = [p.name for p, old, new in ((TOPICS, old_topics, topics), (HOME, home, new_home)) if old != new]
    if stale and write:
        TOPICS.write_text(topics, encoding='utf-8')
        HOME.write_text(new_home, encoding='utf-8')
        print(f'yo_index: updated {", ".join(stale)} from yo-tutka.html')
    elif stale:
        print(f'yo_index: {", ".join(stale)} differ from yo-tutka.html (run python3 scripts/yo_index.py --write)', file=sys.stderr)
        return 1
    else:
        print(f'yo_index: ok (data built {built})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
