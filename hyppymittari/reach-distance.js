// reach-distance.js — touch height ("vertical reach") and horizontal jumps (standing long jump,
// standing triple jump, five bounds) from side-view pose samples. Pure, like jump-analysis.js:
// no DOM, no MediaPipe; samples are {t, f: frameFeatures(...)} in frame pixels.
//
// Both measure positions, not times, so both need a scale. The reliable one is a calibration the
// user taps into the frame (a known height for reach, two floor marks a known distance apart for
// distance). Without it they fall back to the stature-based scale and say so (`uncalibrated`).
import { quantile, median, parabolaFit, cmPxFromScale, DEFAULT_STATURE_CM, JumpDetector } from './jump-analysis.js';

export const REACH_FLAG_TEXT = {
  uncalibrated: 'Ei kalibrointia – mittakaava arvioitu pituudestasi, virhe voi olla ±5 %. Merkitse lattia ja viite kuvaan.',
  hand: 'Kättä ei tunnistettu hypyn huipulla.',
};
export const DIST_FLAG_TEXT = {
  uncalibrated: 'Ei kalibrointia – mittakaava arvioitu pituudestasi, virhe voi olla ±5 %. Merkitse kaksi lattiapistettä kuvaan.',
  count: 'Loikkien määrä ei vastaa lajia – tarkista, että koko suoritus näkyy kuvassa.',
  landing: 'Alastuloa ei nähty kunnolla – kantapäät eivät näkyneet alastulon hetkellä.',
  feet: 'Jalkaterät eivät näkyneet ponnistuksessa.',
};

const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1];
const len = a => Math.hypot(a[0], a[1]);

// ---------- calibration ----------

/** Reach: floor point `a` and reference point `b` (px), the reference `cm` above the floor.
 *  Heights are vertical in the image (level camera): the two taps rarely share an x — the floor is
 *  tapped at the takeoff spot, the rim where it is — and measuring along the line between them
 *  would tilt the axis and stretch the scale (a 250 px offset cost 30 cm). */
export function verticalScale(cal) {
  if (!cal || !cal.a || !cal.b || !(cal.cm > 0)) return null;
  const px = cal.a[1] - cal.b[1];
  if (px < 20) return null;
  return { floor: cal.a, pxPerCm: px / cal.cm, refPx: px };
}

/** Distance: two floor points `a`, `b` (px) `cm` apart along the jump line. */
export function floorScale(cal) {
  if (!cal || !cal.a || !cal.b || !(cal.cm > 0)) return null;
  const d = sub(cal.b, cal.a), px = len(d);
  if (px < 20) return null;
  return { a: cal.a, u: [d[0] / px, d[1] / px], pxPerCm: px / cal.cm, refPx: px };
}

/** Stature-based fallback scale (px per cm) and ground line from a set of samples. */
function fallbackScale(samples, statureCm) {
  const fs = samples.filter(s => s.f);
  return {
    pxPerCm: cmPxFromScale(quantile(fs.map(s => s.f.foot - s.f.eye), 0.9), statureCm),
    ground: quantile(fs.map(s => s.f.foot), 0.9),
  };
}

// ---------- touch height ----------

/** Highest fingertip during one jump (from JumpDetector / findJumps), in cm above the floor. */
export function measureReach(samples, jump, { cal = null, statureCm = DEFAULT_STATURE_CM, targetCm = 305 } = {}) {
  const win = samples.filter(s => s.f && s.f.tip && s.t >= jump.t0 - 0.05 && s.t <= jump.t1 + 0.05);
  if (win.length < 3) return { ok: false, reason: 'hand' };
  // The jump's time-base flags matter here too: a slowed clip is still unusable.
  const flags = jump.flags.filter(f => f === 'slowed' || f === 'lowFps');
  const vs = verticalScale(cal);
  let toCm;
  if (vs) toCm = p => (vs.floor[1] - p[1]) / vs.pxPerCm;
  else {
    flags.push('uncalibrated');
    const fb = fallbackScale(samples.filter(s => s.t >= jump.t0 - 0.8 && s.t <= jump.t0), statureCm);
    toCm = p => (fb.ground - p[1]) / fb.pxPerCm;
  }
  // Rough top = max of a 3-sample running median (one misplaced hand can't set the record), then a
  // parabola over ±0.1 s around it: the maximum of many noisy samples is biased upward, and the
  // fingertip extrapolation roughly doubles the landmark noise.
  const h = win.map(s => toCm(s.f.tip));
  let best = -Infinity, bi = 0;
  for (let i = 1; i < h.length - 1; i++) {
    const m = median([h[i - 1], h[i], h[i + 1]]);
    if (m > best) { best = m; bi = i; }
  }
  const near = win.map((s, i) => i).filter(i => Math.abs(win[i].t - win[bi].t) <= 0.1);
  if (near.length >= 5) {
    const fit = parabolaFit(near.map(i => win[i].t), near.map(i => h[i]));
    const tv = fit && fit.a < 0 ? fit.m - fit.b / (2 * fit.a) : NaN;
    if (Math.abs(tv - win[bi].t) <= 0.1) best = fit.c - (fit.b * fit.b) / (4 * fit.a);
  }
  // Tap precision (~4 px over the reference span) scales with the height; the fingertip model and
  // landmark noise add ~3.5 cm. Uncalibrated, the stature scale is good to ~5 %.
  const errCm = Math.hypot(vs ? best * 4 / vs.refPx : best * 0.05, 3.5);
  return {
    ok: true, kind: 'reach', touchCm: best, marginCm: best - targetCm, targetCm,
    tTouch: win[bi].t, tipAt: win[bi].f.tip, jumpCm: jump.heightCm, flightMs: jump.flightMs, fps: jump.fps,
    impliedG: jump.impliedG, errCm, flags, t0: jump.t0, t1: jump.t1,
  };
}

/** Offline: every jump in a clip with its touch height — including {ok:false} ones (hand not seen),
 *  so the caller can say why nothing was measured. */
export function findReaches(samples, { cal = null, statureCm = DEFAULT_STATURE_CM, targetCm = 305, ...detOpts } = {}) {
  const det = new JumpDetector({ statureCm, ...detOpts, keepAll: true });
  const out = [];
  const take = ev => {
    if (!ev || ev.type !== 'jump') return;
    out.push({ ...measureReach(det.samples, ev.result, { cal, statureCm, targetCm }), samples: det.samples });
  };
  for (const smp of samples) take(det.push(smp.t, smp.f));
  take(det.flush());
  return out;
}

// ---------- horizontal jumps ----------

export const CONTACT_CM = 4;      // lowest foot point this close to the floor = on the ground
export const AIR_CM = 8;          // …and this far above it = in the air
const MIN_FLIGHT_S = 0.18;       // bound flights are ≥ 0.25 s; jogging strides and noise are shorter
const MIN_PEAK_CM = 15;          // …and lift the feet ≥ 30 cm; a jog lifts them ~10 cm
const START_STANCE_S = 0.4;      // all three events start from a standing stance
const MIN_CONTACT_S = 0.07;      // shorter ground "contacts" inside a flight are landmark dips
export const END_CONTACT_S = 0.6; // a ground contact this long ends the attempt (bound contacts are ~0.2 s)
const FOOT_CM = 25;               // heel–toe distance when one of the two isn't visible

/** Scale + jump direction from the calibration (or stature), and the floor line fitted to the
 *  athlete's own ground contacts. The tapped line itself is not used for heights: a few pixels of
 *  tap error tilt it, and extrapolated 7 m down the runway that hid single-leg contacts. */
function geometry(samples, cal, statureCm) {
  const fs = floorScale(cal);
  const fb = fs ? null : fallbackScale(samples, statureCm);
  const pxPerCm = fs ? fs.pxPerCm : fb.pxPerCm;
  const along = fs ? p => dot(sub(p, fs.a), fs.u) / fs.pxPerCm : p => p[0] / fb.pxPerCm;
  // Lowest foot point of each frame; fit y = α + β·x to those that sit on the floor, iterating from
  // a level line at the bottom envelope. (Taps only give scale + direction.)
  const lows = [];
  for (const s of samples) {
    if (!s.f || !s.f.sides) continue;
    let lp = null;
    for (const sd of s.f.sides) for (const q of [sd.toe, sd.heel]) if (q && (!lp || q[1] > lp[1])) lp = q;
    if (lp) lows.push(lp);
  }
  let alpha = quantile(lows.map(q => q[1]), 0.8), beta = 0;
  for (let it = 0; it < 4; it++) {
    const on = lows.filter(q => alpha + beta * q[0] - q[1] < CONTACT_CM * pxPerCm);
    if (on.length < 5) break;
    const mx = on.reduce((a, q) => a + q[0], 0) / on.length, my = on.reduce((a, q) => a + q[1], 0) / on.length;
    let sxx = 0, sxy = 0;
    for (const q of on) { sxx += (q[0] - mx) ** 2; sxy += (q[0] - mx) * (q[1] - my); }
    beta = sxx > 1 ? sxy / sxx : 0;
    alpha = my - beta * mx;
  }
  return {
    calibrated: !!fs, refPx: fs ? fs.refPx : NaN, along,
    height: p => (alpha + beta * p[0] - p[1]) / pxPerCm,
  };
}

/** Per-frame rows: each visible foot's toe/heel position along the line and height (cm). */
function footRows(samples, geo) {
  const rows = [];
  for (const s of samples) {
    if (!s.f || !s.f.sides || !s.f.sides.length) continue;
    const sides = s.f.sides.map(sd => {
      const toe = sd.toe && { s: geo.along(sd.toe), h: geo.height(sd.toe) };
      const heel = sd.heel && { s: geo.along(sd.heel), h: geo.height(sd.heel) };
      return { toe, heel, low: Math.min(toe ? toe.h : Infinity, heel ? heel.h : Infinity) };
    });
    rows.push({ t: s.t, sides, low: Math.min(...sides.map(sd => sd.low)), hip: geo.along([s.f.hipX, s.f.hip]) });
  }
  return rows;
}

/** Feet on the ground in a row: every foot within CONTACT_CM of the lowest one. */
const contactFeet = (row, base) => row.sides.filter(sd => sd.low - base < CONTACT_CM && sd.low - row.low < CONTACT_CM);

/** Every attempt (a run of flights separated by short contacts) in a sample series.
 *  expected: number of flights the event has (1 long jump, 3 triple, 5 five bounds). */
export function measureDistances(samples, { cal = null, expected = 1, statureCm = DEFAULT_STATURE_CM } = {}) {
  const geo = geometry(samples, cal, statureCm);
  const rows = footRows(samples, geo);
  if (rows.length < 5) return [];
  // The foot landmarks sit a little above the floor even when standing: the 20th percentile of the
  // lowest point is that contact level (contacts dominate any clip that starts and ends standing).
  const base = quantile(rows.map(r => r.low), 0.2);

  // Contact / air with hysteresis, then flight segments.
  const air = [];
  let state = false;
  for (const r of rows) {
    const e = r.low - base;
    if (!state && e > AIR_CM) state = true;
    else if (state && e < CONTACT_CM) state = false;
    air.push(state);
  }
  // A real ground contact lasts ≥ 0.1 s even in bounding; a shorter "contact" between two airborne
  // stretches is a landmark dip, and splitting a flight there breaks the bound count.
  for (let i = 1; i < rows.length; i++) {
    if (air[i] || !air[i - 1]) continue;
    let j = i;
    while (j < rows.length && !air[j]) j++;
    if (j < rows.length && rows[j].t - rows[i - 1].t < MIN_CONTACT_S) for (let k = i; k < j; k++) air[k] = true;
    i = j;
  }
  const flights = [];
  for (let i = 0; i < rows.length; i++) {
    if (!air[i] || (i && air[i - 1])) continue;
    let j = i;
    while (j + 1 < rows.length && air[j + 1]) j++;
    const dur = (j + 1 < rows.length ? rows[j + 1].t : rows[j].t) - (i ? rows[i - 1].t : rows[i].t);
    let peak = 0;
    for (let k = i; k <= j; k++) peak = Math.max(peak, rows[k].low - base);
    if (dur >= MIN_FLIGHT_S && peak >= MIN_PEAK_CM && i > 0 && j + 1 < rows.length) flights.push({ i, j });
    i = j;
  }

  // Group flights into attempts: a ground contact longer than END_CONTACT_S ends one. An attempt
  // must start from a standing stance (jogging back to the line is not an attempt), and only the
  // event's own number of bounds counts — a recovery hop after the landing is not part of it.
  // Stance = the unbroken ground contact right before a flight (any airborne frame breaks it, so
  // the short jog steps the flight filter dropped still count against it).
  const stance = f => { let k = f.i - 1; while (k > 0 && !air[k - 1]) k--; return rows[f.i - 1].t - rows[k].t; };
  const attempts = [];
  for (const f of flights) {
    const last = attempts[attempts.length - 1];
    if (last && rows[f.i].t - rows[last[last.length - 1].j].t < END_CONTACT_S) last.push(f);
    else if (stance(f) >= START_STANCE_S) attempts.push([f]);
  }

  return attempts.map(fl => measureAttempt(rows, fl.slice(0, expected), base, geo, expected));
}

function measureAttempt(rows, fl, base, geo, expected) {
  const flags = geo.calibrated ? [] : ['uncalibrated'];
  if (fl.length < expected) flags.push('count');
  const first = fl[0], lastF = fl[fl.length - 1];
  const before = rows[first.i - 1], after = rows[lastF.j + 1];
  const dir = after.hip - before.hip >= 0 ? 1 : -1;

  // Takeoff point of a contact = the front-most toe of the feet on the ground in its last frame
  // (the toe is the pivot at toe-off). The swinging leg is in the air, so it's never counted.
  // If the very last frame already reads airborne-ish, step back (≤ 0.15 s) to one on the ground.
  const toeAt = end => {
    for (let k = end; k >= 0 && rows[k].t >= rows[end].t - 0.15; k--) {
      const pts = contactFeet(rows[k], base)
        .map(sd => (sd.toe ? sd.toe.s : sd.heel ? sd.heel.s + dir * FOOT_CM : NaN)).filter(Number.isFinite);
      if (pts.length) return dir > 0 ? Math.max(...pts) : Math.min(...pts);
    }
    return NaN;
  };
  const marks = [toeAt(first.i - 1)];
  for (let k = 1; k < fl.length; k++) marks.push(toeAt(fl[k].i - 1));

  // Landing = the rear-most heel of the feet on the ground in the first 0.15 s of the final contact
  // (the nearest mark to the takeoff, like a judge measures).
  let landing = NaN;
  for (let k = lastF.j + 1; k < rows.length && rows[k].t <= after.t + 0.15; k++) {
    for (const sd of contactFeet(rows[k], base)) {
      const s = sd.heel ? sd.heel.s : sd.toe ? sd.toe.s - dir * FOOT_CM : NaN;
      if (Number.isFinite(s) && (!Number.isFinite(landing) || dir * s < dir * landing)) landing = s;
    }
  }
  if (!marks.every(Number.isFinite)) return { ok: false, reason: 'feet', flags: ['feet'] };
  if (!Number.isFinite(landing)) return { ok: false, reason: 'landing', flags: ['landing'] };
  marks.push(landing);

  const phases = marks.slice(1).map((m, k) => dir * (m - marks[k]));
  const distCm = dir * (landing - marks[0]);
  // Tap precision (~4 px over the A–B span) scales with the distance; each end point's foot
  // landmark adds ~3 cm. Uncalibrated, the stature scale is good to ~5 %.
  const errCm = Math.hypot(geo.calibrated ? distCm * 4 / geo.refPx : distCm * 0.05, 4);
  const span = rows[lastF.j + 1].t - rows[first.i - 1].t;
  return {
    ok: true, kind: 'dist', distCm, phases, flights: fl.length, expected, errCm, flags,
    marks: marks.map(m => dir * (m - marks[0])),             // cm from the takeoff toe, for the diagram
    t0: before.t, t1: after.t, fps: span > 0 ? (lastF.j - first.i + 2) / span : 0,
  };
}

/** Streaming (live camera): decides when an attempt is over, then measures it offline. */
export class DistanceTracker {
  constructor({ expected = 1, cal = null, statureCm = DEFAULT_STATURE_CM } = {}) {
    Object.assign(this, { expected, cal, statureCm });
    this.samples = [];
    this.airSince = null;
    this.lastAir = -Infinity;
    this.from = -Infinity;     // samples before this belong to an attempt already reported
  }

  status() {
    const last = this.samples[this.samples.length - 1];
    if (!last || !last.f) return 'noPerson';
    return this.lastAir > this.from && last.t - this.lastAir < END_CONTACT_S ? 'air' : 'ready';
  }

  push(t, f) {
    const s = this.samples;
    if (s.length && t <= s[s.length - 1].t) return null;
    s.push({ t, f });
    if (s.length > 2000 || (s.length > 300 && s[0].t < t - 30)) s.splice(0, s.length - 1200);
    if (!f) return null;
    // Rough air test (the precise one runs in measureDistances): lowest foot vs. the ground line of
    // the last 2 s, scaled by standing height.
    const recent = s.filter(x => x.f && x.t > t - 2 && x.t > this.from);
    if (recent.length < 5) return null;
    const fb = fallbackScale(recent, this.statureCm);
    const up = sm => sm && sm.f && fb.ground - sm.f.foot > AIR_CM * fb.pxPerCm;
    if (up(s[s.length - 1]) && up(s[s.length - 2])) this.lastAir = t;   // two frames: one glitch isn't a flight
    else if (this.lastAir > this.from && t - this.lastAir >= END_CONTACT_S + 0.2) return this.flush(t);
    return null;
  }

  /** Measure everything since the last report (also called at the end of a clip). */
  flush(t = Infinity) {
    if (!(this.lastAir > this.from)) return null;
    const win = this.samples.filter(x => x.t > this.from);
    this.from = Math.min(t, this.samples[this.samples.length - 1].t);
    const all = measureDistances(win, { cal: this.cal, expected: this.expected, statureCm: this.statureCm });
    const ok = all.filter(r => r.ok);
    if (ok.length) return { type: 'dist', result: ok[ok.length - 1] };
    // Silent when there was no attempt at all (a stumble, a step); only a real attempt that
    // couldn't be measured is worth telling the athlete about.
    return all.length ? { type: 'reject', reason: 'distance' } : null;
  }
}
