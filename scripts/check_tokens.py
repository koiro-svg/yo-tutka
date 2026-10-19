#!/usr/bin/env python3
"""Shared blocks that every page (or a group of pages) carries verbatim, each with one canonical copy:
- /* koiro-tokens v2 */ … /* /koiro-tokens */ at the start of every root page's first <style> (scripts/koiro-tokens.css),
- <!-- yo-nav v1 … <!-- /yo-nav --> in the two YO pages (scripts/yo-nav.html).
Fails (exit 1) when a page lacks a block or its copy differs from the canonical one; `--write` copies the canonical
blocks into the pages. Run by vercel.json's buildCommand."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHARED = [
    (re.compile(r'/\* koiro-tokens v2.*?/\* /koiro-tokens \*/', re.S), 'scripts/koiro-tokens.css',
     sorted(p.name for p in ROOT.glob('*.html'))),   # every root page (hyppymittari/ is a copied app)
    (re.compile(r'<!-- yo-nav v1.*?<!-- /yo-nav -->', re.S), 'scripts/yo-nav.html', ['yo-tutka.html', 'yo-harjoittelu.html']),
]


def main():
    write = '--write' in sys.argv
    bad, n = [], 0
    for block, canon_path, pages in SHARED:
        canon = (ROOT / canon_path).read_text(encoding='utf-8').strip()
        for name in pages:
            path = ROOT / name
            text = path.read_text(encoding='utf-8')
            found = block.findall(text)
            if len(found) != 1:
                bad.append(f'{name}: {len(found)} copies of {canon_path} (expected 1)')
            elif found[0].strip() != canon:
                if write:
                    path.write_text(block.sub(lambda _: canon, text, count=1), encoding='utf-8')
                    print(f'{name}: updated from {canon_path}')
                else:
                    bad.append(f'{name}: differs from {canon_path} (run --write)')
            n += 1
    for line in bad:
        print('check_tokens:', line, file=sys.stderr)
    if not bad:
        print(f'check_tokens: {n} shared blocks ok')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
