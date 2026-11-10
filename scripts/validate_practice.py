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


def tutka_subjects(html=None):
    """The subjects of yo-tutka.html's yo-data block (also scripts/yo_index.py)."""
    html = html or (ROOT / "yo-tutka.html").read_text(encoding="utf-8")
    m = re.search(r'<script id="yo-data" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(m.group(1).replace("<\\/", "</"))


def tutka_data():
    return {s["id"]: {x["id"]: x for x in s["sessions"]} for s in tutka_subjects()}


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


def exam_max(data, session):
    """Maximum points of the simulated exam, as the page counts it (unitsFor): the best `answer` tasks of each section,
    a task's points being the sum of its content units, or YO-tutka's task points without units."""
    tasks = {t["n"]: t for t in session.get("tasks") or []}
    pts = {t["n"]: sum(u.get("points") or 0 for u in t.get("units") or []) for t in data.get("tasks") or [] if t.get("units")}
    return sum(sum(sorted((pts.get(n, (tasks.get(n) or {}).get("points") or 0) for n in sec.get("tasks") or []), reverse=True)[:sec.get("answer") or 0])
               for sec in (data.get("exam") or {}).get("sections") or [])


GRADES_SOURCE = "https://www.ylioppilastutkinto.fi/fi/tutkinnon-suorittaminen/pisterajat/"


def check_grades(tutka):
    """yo-harjoittelu.html's GRADES table (julkinen-31): YTL's published minimum points for L, E, M, C, B, A per session and
    subject. Keys must be real subjects and sessions, each row six strictly descending non-negative integers no higher than
    the exam's maximum, and every session line ends with its YTL source page as a comment."""
    html = (ROOT / "yo-harjoittelu.html").read_text(encoding="utf-8")
    m = re.search(r"const GRADES = \{\n(.*?)\n  \};", html, re.S)
    if not m:
        return ["yo-harjoittelu.html: GRADES-taulua ei löytynyt"]
    errors = []
    for line in m.group(1).splitlines():
        sm = re.match(r"\s*'(\d{4}[KS])': \{(.*)\},\s*// (\S+)$", line)
        if not sm:
            errors.append(f"yo-harjoittelu.html GRADES: rivi ei ole muotoa 'kerta': {{ aine: [...] }},  // YTL:n lähdesivu: {line.strip()[:60]}")
            continue
        k, src = sm.group(1), sm.group(3)
        if not src.startswith(GRADES_SOURCE):
            errors.append(f"yo-harjoittelu.html GRADES: {k}: lähteen pitää olla YTL:n pisterajasivu ({GRADES_SOURCE}…), oli {src}")
        for a, nums in re.findall(r"'?([a-z-]+)'?: \[([^\]]*)\]", sm.group(2)):
            b = [int(x) for x in re.findall(r"-?\d+", nums)]
            if a not in tutka or k not in tutka[a]:
                errors.append(f"yo-harjoittelu.html GRADES: {k}/{a}: ainetta tai kertaa ei ole YO-tutkan datassa")
                continue
            if len(b) != 6 or any(x < 0 for x in b) or any(x <= y for x, y in zip(b, b[1:])):
                errors.append(f"yo-harjoittelu.html GRADES: {k}/{a}: pitää olla kuusi laskevaa lukua (L, E, M, C, B, A), oli {b}")
            practice = ROOT / "data" / "practice" / a / f"{k}.json"
            if not practice.exists():
                continue
            data = json.loads(practice.read_text(encoding="utf-8"))
            if any(sec.get("group") for sec in (data.get("exam") or {}).get("sections") or []):
                errors.append(f"yo-harjoittelu.html GRADES: {k}/{a}: kahden kokeen aineelle ei anneta arviota yhden kokeen pisteistä")
            elif b and b[0] > exam_max(data, tutka[a][k]):
                errors.append(f"yo-harjoittelu.html GRADES: {k}/{a}: L-raja {b[0]} on yli kokeen maksimin {exam_max(data, tutka[a][k])}")
    return errors


PAGE_LOGIC_TESTS = r"""
const assert = require('node:assert/strict');
// normalizeSave: a damaged save never leaves a wrong-typed part behind, unknown fields survive
for (const bad of [{ scores: null }, { review: null }, { sims: 7 }, { ui: [] }, { history: [null, 3, { k: 1, at: 2 }, { k: 'a|b|1|_', at: NaN }] }]) {
  const s = normalizeSave(Object.assign({ v: 1, scores: {}, review: {}, sims: {}, history: null, ui: {} }, bad));
  for (const f of ['scores', 'review', 'sims', 'ui']) assert.ok(plainObj(s[f]), f);
  assert.deepEqual(s.history, []);
}
let s = normalizeSave({ scores: { 'a|b|1|_': { p: 2, max: 6, at: 5 }, 'x': null, 'c|d|2|a': { p: 1, max: 2, at: 3 } }, review: { r: 'x' }, sims: {}, ui: { holdUser: 'u' }, extra: 1 });
assert.deepEqual(Object.keys(s.scores), ['a|b|1|_', 'c|d|2|a']);
assert.deepEqual(s.history.map(e => e.at), [3, 5]);          // seeded from scores, oldest first
assert.deepEqual(s.review, {});
assert.equal(s.ui.holdUser, 'u'); assert.equal(s.extra, 1);
s = normalizeSave({ scores: {}, review: {}, sims: {}, ui: {}, history: [{ k: 'a|b|1|_', p: 1, max: 2, at: 9 }] });
assert.equal(s.history.length, 1);
// monthLabels: a name needs three week columns; 10.11.2026 began 27.7. (heinä, 1 column) and ran into elo
const months = [6, 7, 7, 7, 7, 7, 8, 8, 8, 8, 9, 9, 9, 9, 10, 10];
assert.deepEqual(monthLabels(months), [{ w: 1, month: 7 }, { w: 6, month: 8 }, { w: 10, month: 9 }, { w: 14, month: 10 }]);
assert.deepEqual(monthLabels([6, 6, 6, 7, 7]).map(m => m.w), [0, 3]);
assert.deepEqual(monthLabels([6, 6, 7, 7, 7]).map(m => m.w), [2]);
assert.deepEqual(monthLabels([3, 3, 3]), [{ w: 0, month: 3 }]);
// countedTasks: at most `answer` tasks per section, the first picked ones in exam order
const sections = [{ answer: 4, tasks: ['1', '2', '3', '4'] }, { answer: 3, tasks: ['5', '6', '7', '8', '9'] }, { answer: 3, tasks: ['10', '11', '12', '13'] }];
assert.deepEqual([...countedTasks(sections, new Set(['1', '9', '8', '7', '6', '5', '13']))], ['1', '5', '6', '7', '13']);
assert.deepEqual([...countedTasks(sections, new Set())], []);
assert.deepEqual([...countedTasks(sections, new Set(['2', '3']))], ['2', '3']);
// pikaLive: the quick test lasts one sitting (2 h); saves without a timestamp are over
assert.equal(pikaLive({ at: 1000 }, 1000 + 2 * 36e5 - 1), true);
assert.equal(pikaLive({ at: 1000 }, 1000 + 2 * 36e5), false);
assert.equal(pikaLive({ a: 'x' }, Date.now()), false);
assert.equal(pikaLive(undefined, 0), false);
"""


def check_page_logic():
    """Runs the pure helpers of yo-harjoittelu.html (between the pure:start and pure:end comments) in node against the
    cases above. Without node (not needed for the content checks) the test is skipped with a note."""
    import shutil, subprocess
    html = (ROOT / "yo-harjoittelu.html").read_text(encoding="utf-8")
    m = re.search(r"/\* pure:start.*?\*/(.*?)/\* pure:end \*/", html, re.S)
    if not m:
        return ["yo-harjoittelu.html: pure:start … pure:end -lohkoa ei löytynyt (check_page_logic)"]
    node = shutil.which("node")
    if not node:
        print("check_page_logic: node puuttuu, sivun logiikkatestit ohitettiin")
        return []
    r = subprocess.run([node, "-e", m.group(1) + PAGE_LOGIC_TESTS], capture_output=True, text=True, timeout=60)
    if r.returncode:
        lines = [x for x in r.stderr.splitlines() if x.strip()]
        detail = next((x for x in lines if "Error" in x), lines[0] if lines else "tuntematon virhe")
        return [f"yo-harjoittelu.html: logiikkatesti epäonnistui: {detail.strip()[:300]}"]
    return []


def check_page_wipe():
    """"Tyhjennä tämä selain" must cover every storage the page writes: a new localStorage/sessionStorage key or a new
    IndexedDB database has to be added to wipeBrowser() (and to this list) in the same change."""
    html = (ROOT / "yo-harjoittelu.html").read_text(encoding="utf-8")
    errors = []
    known = {"LS", "AUTH_KEY", "k"}
    for m in re.finditer(r"(?:localStorage|sessionStorage)\.(?:setItem|getItem|removeItem)\(\s*([^,)]+)", html):
        arg = m.group(1).strip()
        if arg not in known and arg != "'yo-practice'":
            errors.append(f"yo-harjoittelu.html: tuntematon tallennusavain {arg}: lisää se wipeBrowser()-funktioon ja check_page_wipe-listaan")
    dbs = set(re.findall(r"indexedDB\.(?:open|deleteDatabase)\('([^']+)'", html))
    if dbs != {"yo-practice"}:
        errors.append(f"yo-harjoittelu.html: IndexedDB-kannat {sorted(dbs)}: wipeBrowser() tyhjentää vain kannan yo-practice")
    for needle in ("if (wiped) return; dayMemo = null;", "const run = (mode, fn) => wiped ? Promise.resolve()", "await idb.wipe();"):
        if needle not in html:
            errors.append(f"yo-harjoittelu.html: tyhjennyksen suoja puuttuu: {needle}")
    return errors


def main(args):
    tutka = tutka_data()
    files = [pathlib.Path(a).resolve() for a in args] or sorted((ROOT / "data" / "practice").glob("*/*.json"))
    errors = check_exams(tutka) + check_grades(tutka) + check_page_logic() + check_page_wipe() + [e for f in files for e in validate(f, tutka)]
    for e in errors:
        print(e)
    print(f"{len(files)} tiedostoa, {len(errors)} virhettä")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
