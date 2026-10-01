// Dev-only LaTeX check (not part of the site or build). Run in a temp dir:
//   cd "$(mktemp -d)" && npm i mathjax-full@3.2.2 && cp <repo>/scripts/check_tex.mjs . && node check_tex.mjs <repo>/data/practice/<aine>/<kerta>.json
import fs from 'node:fs';
import { mathjax } from 'mathjax-full/js/mathjax.js';
import { TeX } from 'mathjax-full/js/input/tex.js';
import { SVG } from 'mathjax-full/js/output/svg.js';
import { liteAdaptor } from 'mathjax-full/js/adaptors/liteAdaptor.js';
import { RegisterHTMLHandler } from 'mathjax-full/js/handlers/html.js';
import { AllPackages } from 'mathjax-full/js/input/tex/AllPackages.js';

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
// Only what the browser's tex-svg.js has (built in + autoload), so an unavailable macro fails here too.
const BROWSER = ['base', 'ams', 'newcommand', 'require', 'autoload', 'configmacros', 'action', 'amscd', 'bbox', 'boldsymbol', 'braket',
  'cancel', 'color', 'enclose', 'extpfeil', 'html', 'mhchem', 'unicode', 'verb'];
const tex = new TeX({ packages: AllPackages.filter(p => BROWSER.includes(p)) });
const doc = mathjax.document('', { InputJax: tex, OutputJax: new SVG({ fontCache: 'none' }) });

const FIELDS = ['intro', 'prompt', 'hints', 'solution', 'answer'];
function* strings(task) {
  for (const k of FIELDS) if (task[k] != null) yield* [].concat(task[k]).map(v => [k, v]);
  for (const u of task.units || []) for (const k of FIELDS) if (u[k] != null) yield* [].concat(u[k]).map(v => [`${u.id || '-'}.${k}`, v]);
}
// Same delimiters as md() in yo-harjoittelu.html and MATH_RE in validate_practice.py.
function formulas(s) {
  const out = []; const re = /\$\$([\s\S]+?)\$\$|(?<!\\)\$([^$\n]+?)(?<!\\)\$/g; let m;
  while ((m = re.exec(s))) out.push(m[1] ?? m[2]);
  if (/(?<!\\)\$/.test(s.replace(re, ''))) out.push({ unbalanced: true });
  return out;
}

let bad = 0, total = 0;
for (const file of process.argv.slice(2)) {
  const data = JSON.parse(fs.readFileSync(file, 'utf8'));
  for (const task of data.tasks || []) for (const [where, s] of strings(task)) {
    if (typeof s !== 'string') continue;
    for (const f of formulas(s)) {
      total++;
      if (f.unbalanced) { bad++; console.log(`${file} tehtävä ${task.n} ${where}: pariton $-merkki`); continue; }
      try {
        const node = doc.convert(f, { display: false });
        const err = adaptor.outerHTML(node).match(/data-mjx-error="([^"]*)"/);
        if (err) throw new Error(err[1]);
      } catch (e) { bad++; console.log(`${file} tehtävä ${task.n} ${where}: ${e.message} :: ${f.slice(0, 80)}`); }
    }
  }
}
console.log(`${total} kaavaa, ${bad} virhettä`);
process.exit(bad ? 1 : 0);
