#!/usr/bin/env python3
"""Find 6-word sequences shared between practice content and original exam texts.

Usage: python3 scripts/check_overlap.py data/practice/<aine>/<kerta>.json SOURCE.txt [SOURCE2.txt ...]
SOURCE files are plain-text extractions of the exam view and grading instructions. Keep them OUTSIDE
the repo (scratch directory): the repo is public and the source texts are copyrighted.
Formulas, numbers and one-letter tokens (variables like f, x) are ignored on both sides. Exit code 1 if any shared sequence is found.
"""
import json, re, sys

from validate_practice import MATH_RE, iter_exam_texts, iter_texts

N = 6


def words(text):
    text = MATH_RE.sub(" ", text)
    text = re.sub(r"\\[a-zA-Z]+|[^\w\s]", " ", text.lower())
    # the source keeps formula variables as plain words while the content wraps them in $...$: drop them both sides
    return [w for w in text.split() if len(w) > 1 and not w.isdigit()]


def grams(ws):
    return {" ".join(ws[i:i + N]) for i in range(len(ws) - N + 1)}


def main(path, sources):
    src = set()
    for s in sources:
        src |= grams(words(open(s, encoding="utf-8").read()))
    data = json.load(open(path, encoding="utf-8"))
    hits = 0
    texts = list(iter_exam_texts(data)) + [x for task in data["tasks"] for x in iter_texts(task)]
    for where, text in texts:
        for g in sorted(grams(words(text)) & src):
            hits += 1
            print(f"{where}: \"{g}\"")
    print(f"{hits} yhteistä {N} sanan jaksoa")
    return 1 if hits else 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2:]))
