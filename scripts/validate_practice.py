#!/usr/bin/env python3
"""Validate practice content in data/practice/<subject>/<session>.json against YO-tutka data.

Usage:
  python3 scripts/validate_practice.py              # every file (also Vercel buildCommand)
  python3 scripts/validate_practice.py FILE [...]   # given files only
Rules are documented in scripts/PRACTICE_CONTENT.md. Standard library only.
"""
import datetime
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Same delimiters as md() in yo-harjoittelu.html: $$...$$ or $...$, where \$ is a literal dollar.
MATH_RE = re.compile(r"\$\$[\s\S]+?\$\$|(?<!\\)\$[^$\n]+?(?<!\\)\$")
CHECKS = {"hvp", "laskettu", "hvp+laskettu", "malli", "ei"}
MAX_PROMPT = 900  # long prompts are a sign of copied task text


def tutka_data():
    html = (ROOT / "yo-tutka.html").read_text(encoding="utf-8")
    m = re.search(r'<script id="yo-data" type="application/json">(.*?)</script>', html, re.S)
    data = json.loads(m.group(1).replace("<\\/", "</"))
    return {s["id"]: {x["id"]: x for x in s["sessions"]} for s in data}


def math_ok(s):
    return not re.search(r"(?<!\\)\$", MATH_RE.sub("", s))


def iter_exam_texts(data):
    """Yield (where, text) for the exam section titles and notes shown on the exam page."""
    for i, sec in enumerate((data.get("exam") or {}).get("sections") or []):
        for k in ("title", "note"):
            if sec.get(k) is not None:
                yield f"exam.sections[{i}].{k}", sec[k]


def iter_texts(task):
    """Yield (where, text) for every Markdown text field of one content task."""
    n = task.get("n")
    if task.get("intro") is not None:
        yield f"tehtävä {n} intro", task["intro"]
    for u in task.get("units") or []:
        w = f"tehtävä {n}{'/' + u['id'] if u.get('id') else ''}"
        for k in ("prompt", "solution", "answer"):
            if u.get(k) is not None:
                yield f"{w} {k}", u[k]
        for i, h in enumerate(u.get("hints") or []):
            yield f"{w} vihje {i + 1}", h


def check_text(err, where, s):
    if not isinstance(s, str) or not s.strip():
        err(f"{where}: tyhjä tai ei tekstiä")
        return
    if re.search(r"<\s*/?\s*[a-zA-Z][^>]*>", MATH_RE.sub("", s)):   # inequalities inside formulas are fine
        err(f"{where}: HTML-tagi tekstissä")
    if not math_ok(s):
        err(f"{where}: pariton $-merkki")
    if re.search(r"\\(href|url|class|style|cssId|data|require)\b", s):   # TeX commands that emit links/attributes
        err(f"{where}: kielletty TeX-komento (\\href, \\class, \\style …)")


def check_urls(err, obj, where):
    for k in ("examUrl", "gradingUrl"):
        if obj.get(k) is not None and not re.fullmatch(r"https://[^\s\"'<>]+", str(obj[k])):
            err(f"{where}{k} ei ole https-osoite")


def validate(path, tutka):
    errors = []
    err = lambda m: errors.append(f"{path.relative_to(ROOT)}: {m}")
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"{path}: JSON ei jäsenny: {e}"]
    subj, sess = path.parent.name, path.stem
    if d.get("subject") != subj or d.get("session") != sess:
        err(f"subject/session ({d.get('subject')}/{d.get('session')}) ≠ polku ({subj}/{sess})")
    session = tutka.get(subj, {}).get(sess)
    if not session:
        return errors + [f"{path}: YO-tutkassa ei ole kertaa {subj}/{sess}"]
    check_urls(err, d, "")
    if not d.get("examUrl"):
        err("examUrl puuttuu")

    tasks = {t["n"]: t for t in session["tasks"]}
    got = [t.get("n") for t in d.get("tasks", [])]
    if sorted(got) != sorted(tasks):
        err(f"tehtävät eivät vastaa YO-tutkaa: puuttuu {sorted(set(tasks) - set(got))}, ylimääräisiä {sorted(set(got) - set(tasks))}")

    exam = d.get("exam") or {}
    if not isinstance(exam.get("minutes"), int) or exam["minutes"] <= 0:
        err("exam.minutes puuttuu")
    seen = []
    for i, sec in enumerate(exam.get("sections") or []):
        ts = sec.get("tasks") or []
        seen += ts
        if not sec.get("title"):
            err(f"exam.sections[{i}]: title puuttuu")
        if not isinstance(sec.get("answer"), int) or not 1 <= sec["answer"] <= len(ts):
            err(f"exam.sections[{i}]: answer ei ole 1..{len(ts)}")
        check_urls(err, sec, f"exam.sections[{i}].")
        exams = {tasks[n].get("exam") for n in ts if n in tasks} - {None}
        if len(exams) > 1:
            err(f"exam.sections[{i}]: osiossa on tehtäviä kahdesta eri kokeesta {sorted(exams)}")
        elif exams and sec.get("group") not in exams:
            err(f"exam.sections[{i}]: group pitää olla {sorted(exams)} (YO-tutkan tehtävien koe)")
        if sec.get("minutes") is not None and (not isinstance(sec["minutes"], int) or sec["minutes"] <= 0):
            err(f"exam.sections[{i}].minutes ei ole positiivinen kokonaisluku")
    if sorted(seen) != sorted(tasks):
        err(f"exam.sections ei kata tehtäviä täsmälleen kerran (osioissa {sorted(seen)})")

    for where, text in iter_exam_texts(d):
        check_text(err, where, text)
    for t in d.get("tasks", []):
        n = t.get("n")
        meta = tasks.get(n)
        units = t.get("units") or []
        if not units:
            err(f"tehtävä {n}: units puuttuu")
            continue
        ids = [u.get("id") for u in units]
        if len(set(ids)) != len(ids):
            err(f"tehtävä {n}: toistuva yksikkö-id")
        if len(units) > 1 and "" in ids:
            err(f"tehtävä {n}: tyhjä id sallittu vain, kun yksikkö on koko tehtävä")
        total = 0
        for u in units:
            w = f"tehtävä {n}{'/' + u['id'] if u.get('id') else ''}"
            p = u.get("points")
            if not isinstance(p, (int, float)) or p <= 0:
                err(f"{w}: points puuttuu")
                continue
            total += p
            hints = u.get("hints") or []
            want = 1 if p <= 4 else 2
            if len(hints) != want:
                err(f"{w}: {len(hints)} vihjettä, pitää olla {want} ({p} p)")
            for k in ("prompt", "solution"):
                if u.get(k) is None:
                    err(f"{w} {k}: puuttuu")
            if len(u.get("prompt") or "") > MAX_PROMPT:
                err(f"{w}: prompt yli {MAX_PROMPT} merkkiä – kirjoita lyhyemmin omin sanoin")
            if u.get("check") not in CHECKS:
                err(f"{w}: check pitää olla jokin {sorted(CHECKS)}")
        if meta and meta.get("points") is not None and abs(total - meta["points"]) > 1e-9:
            err(f"tehtävä {n}: yksiköiden pisteet {total} ≠ tehtävän pisteet {meta['points']}")
        for where, text in iter_texts(t):
            check_text(err, where, text)
    return errors


def check_exams(tutka):
    """yo-tutka.html's EXAMS table (next exam per subject, julkinen-22): keys are subject ids, values real dates.
    Every date in the past only warns (the page then says the date is not updated): a term change must not block deploys."""
    html = (ROOT / "yo-tutka.html").read_text(encoding="utf-8")
    m = re.search(r"const EXAMS = (\{[^}]*\});", html)
    if not m:
        return ["yo-tutka.html: EXAMS-taulua ei löytynyt"]
    exams, errors = json.loads(m.group(1)), []
    for k, v in exams.items():
        if k not in tutka:
            errors.append(f"yo-tutka.html EXAMS: tuntematon aine {k!r}")
        try:
            datetime.date.fromisoformat(v)
        except (TypeError, ValueError):
            errors.append(f"yo-tutka.html EXAMS: {k}: virheellinen päivä {v!r}")
    if not errors and all(datetime.date.fromisoformat(v) < datetime.date.today() for v in exams.values()):
        print("varoitus: yo-tutka.html EXAMS: kaikki koepäivät ovat menneet, päivitä seuraavan kauden päivät")
    return errors


def check_grades(tutka):
    """yo-harjoittelu.html's GRADES table (julkinen-31): YTL's published minimum points for L, E, M, C, B, A per session and
    subject. Keys must be real subjects and sessions, and each row six strictly descending non-negative integers."""
    html = (ROOT / "yo-harjoittelu.html").read_text(encoding="utf-8")
    m = re.search(r"const GRADES = \{\n(.*?)\n  \};", html, re.S)
    if not m:
        return ["yo-harjoittelu.html: GRADES-taulua ei löytynyt"]
    errors = []
    for line in m.group(1).splitlines():
        sm = re.match(r"\s*'(\d{4}[KS])': \{(.*)\},?$", line)
        if not sm:
            errors.append(f"yo-harjoittelu.html GRADES: rivi ei ole muotoa 'kerta': {{ aine: [...] }}: {line.strip()[:60]}")
            continue
        k = sm.group(1)
        for a, nums in re.findall(r"'?([a-z-]+)'?: \[([^\]]*)\]", sm.group(2)):
            b = [int(x) for x in re.findall(r"-?\d+", nums)]
            if a not in tutka or k not in tutka[a]:
                errors.append(f"yo-harjoittelu.html GRADES: {k}/{a}: ainetta tai kertaa ei ole YO-tutkan datassa")
            if len(b) != 6 or any(x < 0 for x in b) or any(x <= y for x, y in zip(b, b[1:])):
                errors.append(f"yo-harjoittelu.html GRADES: {k}/{a}: pitää olla kuusi laskevaa lukua (L, E, M, C, B, A), oli {b}")
    return errors


def main(args):
    tutka = tutka_data()
    files = [pathlib.Path(a).resolve() for a in args] or sorted((ROOT / "data" / "practice").glob("*/*.json"))
    errors = check_exams(tutka) + check_grades(tutka) + [e for f in files for e in validate(f, tutka)]
    for e in errors:
        print(e)
    print(f"{len(files)} tiedostoa, {len(errors)} virhettä")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
