#!/usr/bin/env python3
"""Checks data/visa.json (quizzes of /visa). Run by vercel.json's buildCommand; bad data fails the deploy.
`norm` must stay identical to norm() in visa.html: a typed answer matches when the normalized strings are equal, so two
items of one quiz must never share a normalized answer."""
import json
import pathlib
import sys
import unicodedata

PATH = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'visa.json'
COUNTRY_COUNT = 197


def norm(s):
    s = unicodedata.normalize('NFD', s)
    return ''.join(ch for ch in s.lower() if unicodedata.category(ch)[0] in 'LN')


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


def main():
    data = json.loads(PATH.read_text(encoding='utf-8'))
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
    seen = set()
    for q in data['quizzes']:
        qid = q['id']
        if qid in seen:
            bad.append(f'{qid}: duplicate quiz id')
        seen.add(qid)
        if q['cat'] not in data['cats']:
            bad.append(f"{qid}: unknown category {q['cat']}")
        if not (isinstance(q['t'], int) and q['t'] > 0):
            bad.append(f'{qid}: bad time limit')
        if not (q['title'].get('fi') and q['title'].get('en')):
            bad.append(f'{qid}: title needs fi and en')
        missing = set(q.get('ids', [])) - set(ids)
        if missing:
            bad.append(f'{qid}: unknown ids {sorted(missing)}')
        items = items_of(q, data)
        if not items:
            bad.append(f'{qid}: no items')
        owner = {}
        for i, it in enumerate(items):
            aliases = {norm(a) for a in it['fi'] + it['en']}
            if '' in aliases:
                bad.append(f'{qid}[{i}]: answer normalizes to nothing')
            for a in aliases:
                if a in owner:
                    bad.append(f'{qid}: "{a}" answers both item {owner[a]} and item {i}')
                owner[a] = i
    for line in bad:
        print('validate_visa:', line, file=sys.stderr)
    if not bad:
        print(f"validate_visa: {len(data['quizzes'])} quizzes ok")
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
