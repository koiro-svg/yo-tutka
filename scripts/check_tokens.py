#!/usr/bin/env python3
"""Every page of koirosvg.com carries the same /* koiro-tokens v2 */ block at the start of its first <style>.
Fails (exit 1) when a page lacks the block or its copy differs from scripts/koiro-tokens.css.
`--write` replaces each page's block with the canonical one. Run by vercel.json's buildCommand."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CANON = (ROOT / 'scripts' / 'koiro-tokens.css').read_text(encoding='utf-8').strip()
PAGES = ['index.html', 'ai.html', 'tietosuoja.html', 'yo-tutka.html', 'yo-harjoittelu.html']
BLOCK = re.compile(r'/\* koiro-tokens v2.*?/\* /koiro-tokens \*/', re.S)


def main():
    write = '--write' in sys.argv
    bad = []
    for name in PAGES:
        path = ROOT / name
        text = path.read_text(encoding='utf-8')
        found = BLOCK.findall(text)
        if len(found) != 1:
            bad.append(f'{name}: {len(found)} koiro-tokens blocks (expected 1)')
            continue
        if found[0].strip() == CANON:
            continue
        if write:
            path.write_text(BLOCK.sub(lambda _: CANON, text, count=1), encoding='utf-8')
            print(f'{name}: updated')
        else:
            bad.append(f'{name}: koiro-tokens block differs from scripts/koiro-tokens.css (run --write)')
    for line in bad:
        print('check_tokens:', line, file=sys.stderr)
    if not bad:
        print(f'check_tokens: {len(PAGES)} pages ok')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
