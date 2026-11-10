#!/usr/bin/env python3
"""Checks data/visa.json and the quiz packs in data/visa/ (quizzes of /visa). Run by vercel.json's buildCommand; bad data fails the
deploy. `norm` must stay identical to norm() in visa.html: a typed answer matches when the normalized strings are equal, so two
items of one quiz must never share a normalized answer. Writing rules: scripts/VISA_CONTENT.md."""
import json
import pathlib
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAIN = ROOT / 'data' / 'visa.json'
PACKS = ROOT / 'data' / 'visa'
COUNTRY_COUNT = 197
MIN_ITEMS, MAX_ITEMS = 5, 200
OPTION_COUNT = 4


def norm(s):
    s = unicodedata.normalize('NFD', s)
    return ''.join(ch for ch in s.lower() if unicodedata.category(ch)[0] in 'LN')


def is_text(x):
    return isinstance(x, str) and x.strip() != ''


def both(x):
    return isinstance(x, dict) and is_text(x.get('fi')) and is_text(x.get('en'))


def items_of(q, data):
    if 'items' in q:
        return q['items']
    pool = data['countries']
    if 'cont' in q:
        pool = [c for c in pool if c['c'] in q['cont']]
    if 'ids' in q:
        pool = [c for c in pool if c['id'] in q['ids']]
    if q['ans'] == 'name':
        return [{'fi': c['fi'], 'en': c['en']} for c in pool]
    return [{'fi': c['capFi'], 'en': c['capEn']} for c in pool]


def check_list(qid, items, bad):
    owner = {}
    for i, it in enumerate(items):
        if not (isinstance(it.get('fi'), list) and isinstance(it.get('en'), list) and it['fi'] and it['en']
                and all(is_text(a) for a in it['fi'] + it['en'])):
            bad.append(f'{qid}[{i}]: fi and en must be non-empty lists of text')
            continue
        aliases = {norm(a) for a in it['fi'] + it['en']}
        if '' in aliases:
            bad.append(f'{qid}[{i}]: answer normalizes to nothing')
        for a in aliases:
            if a in owner:
                bad.append(f'{qid}: "{a}" answers both item {owner[a]} and item {i}')
            owner[a] = i
        h = it.get('h')
        if h is not None and not (is_text(h) or both(h)):
            bad.append(f'{qid}[{i}]: bad hint')


def check_choice(qid, items, bad):
    for i, it in enumerate(items):
        if not both(it.get('q')) or not both(it.get('ok')):
            bad.append(f'{qid}[{i}]: q and ok need fi and en')
            continue
        no = it.get('no')
        if not (isinstance(no, list) and len(no) == OPTION_COUNT - 1 and all(both(x) for x in no)):
            bad.append(f'{qid}[{i}]: no needs {OPTION_COUNT - 1} wrong options with fi and en')
            continue
        for lang in ('fi', 'en'):
            options = [norm(it['ok'][lang])] + [norm(x[lang]) for x in no]
            if len(set(options)) != OPTION_COUNT:
                bad.append(f'{qid}[{i}]: duplicate option ({lang})')


def content_key(fmt, items):
    """What a quiz asks, without its title: two quizzes with one key are the same quiz twice (suomi-1/suomi-2 world heritage,
    11/2026). The format is part of it, because a list, a flag and a map quiz of the same countries are different games."""
    try:
        if fmt == 'choice':
            return fmt, frozenset(norm(it['q']['fi']) for it in items)
        return fmt, frozenset(norm(it['fi'][0]) for it in items)
    except (KeyError, IndexError, TypeError, AttributeError):
        return None


def main():
    data = json.loads(MAIN.read_text(encoding='utf-8'))
    bad = []
    if len(data['countries']) != COUNTRY_COUNT:
        bad.append(f"{len(data['countries'])} countries, expected {COUNTRY_COUNT}")
    ids = [c['id'] for c in data['countries']]
    if len(set(ids)) != len(ids):
        bad.append('duplicate country id')
    for c in data['countries']:
        if c['c'] not in data['continents']:
            bad.append(f"{c['id']}: unknown continent {c['c']}")
        for k in ('fi', 'en', 'capFi', 'capEn'):
            if not c[k]:
                bad.append(f"{c['id']}: empty {k}")

    shapes = json.loads((ROOT / 'data' / 'visa-map.json').read_text(encoding='utf-8'))['shapes']
    for c in ids:
        if c not in shapes:
            bad.append(f'{c}: missing from visa-map.json')
            continue
        # buildMap needs the bounding box of every target (zoom and the tap area of small countries) and something to draw
        b = shapes[c].get('b')
        if not (isinstance(b, list) and len(b) == 4 and all(isinstance(x, (int, float)) for x in b) and b[0] <= b[2] and b[1] <= b[3]):
            bad.append(f'{c}: visa-map.json needs b = [x0, y0, x1, y1]')
        if not shapes[c].get('d') and not shapes[c].get('c'):
            bad.append(f'{c}: visa-map.json has neither an outline (d) nor a marker (c)')

    listed = data.get('packs', [])
    on_disk = sorted(p.stem for p in PACKS.glob('*.json'))
    for name in set(listed) ^ set(on_disk):
        if '--draft' not in sys.argv:
            bad.append(f'pack {name}: must be both in data/visa/ and in the packs list of data/visa.json')
    quizzes = list(data['quizzes'])
    for name in on_disk:
        try:
            quizzes += json.loads((PACKS / f'{name}.json').read_text(encoding='utf-8'))['quizzes']
        except (ValueError, KeyError) as e:
            bad.append(f'pack {name}: {e}')

    seen = set()
    contents = {}
    for q in quizzes:
        qid = q.get('id', '?')
        if qid in seen:
            bad.append(f'{qid}: duplicate quiz id')
        seen.add(qid)
        if q.get('cat') not in data['cats']:
            bad.append(f"{qid}: unknown category {q.get('cat')}")
        if not (isinstance(q.get('t'), int) and q['t'] > 0):
            bad.append(f'{qid}: bad time limit')
        if not both(q.get('title')):
            bad.append(f'{qid}: title needs fi and en')
        missing = set(q.get('ids', [])) - set(ids)
        if missing:
            bad.append(f'{qid}: unknown ids {sorted(missing)}')
        fmt = q.get('format', 'list')
        if fmt not in ('list', 'choice', 'flags', 'map'):
            bad.append(f'{qid}: unknown format {fmt}')
            continue
        if fmt in ('flags', 'map') and ('items' in q or q.get('ans') != 'name'):
            bad.append(f'{qid}: {fmt} quizzes are built from the country table (ans: name, no items)')
            continue
        items = items_of(q, data)
        if not items:
            bad.append(f'{qid}: no items')
            continue
        if not MIN_ITEMS <= len(items) <= MAX_ITEMS and 'items' in q:
            bad.append(f'{qid}: {len(items)} items, allowed {MIN_ITEMS}-{MAX_ITEMS}')
        if fmt == 'choice':
            check_choice(qid, items, bad)
        else:
            check_list(qid, items, bad)
        key = content_key(fmt, items)
        if key is not None:
            if key in contents:
                bad.append(f'{qid}: same content as {contents[key]} (one quiz twice)')
            contents.setdefault(key, qid)
    for line in bad:
        print('validate_visa:', line, file=sys.stderr)
    if not bad:
        print(f'validate_visa: {len(quizzes)} quizzes ok')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
