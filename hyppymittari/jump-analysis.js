// jump-analysis.js — pure vertical-jump analysis. No DOM, no MediaPipe: the same code runs in
// the app (live camera + video file) and in test-jump.js under JavaScriptCore.
//
// Primary measure is flight time: h = g·T²/8. Takeoff/landing are found from the lowest foot
// point (heels + toes) leaving / returning to the ground line, refined to sub-frame precision by
// extrapolating the first/last airborne samples back to ground level. Hip rise (needs stature for
// the px→cm scale) is a secondary, independent cross-check.

export const G = 9.81;                 // m/s²
export const EYE_RATIO = 0.936;        // eye height / stature (Drillis & Contini)
export const DEFAULT_STATURE_CM = 175;
export const MIN_FLIGHT_S = 0.2;       // ≈ 5 cm; shorter "flights" are running strides or noise
export const MAX_FLIGHT_S = 1.5;       // ≈ 2.8 m; longer means a slowed-down clip
const MIN_VIS = 0.3;
const TAKEOFF_CM = 5;                  // detector: airborne once the feet are this far up…
const LANDED_CM = 2.5;                 // …and landed again below this
const EDGE_FIT_S = 0.045;              // airborne samples within this window of an edge are fitted

// MediaPipe pose landmark indices
export const P = {
  NOSE: 0, L_EYE: 2, R_EYE: 5, L_SH: 11, R_SH: 12, L_EL: 13, R_EL: 14, L_WR: 15, R_WR: 16,
  L_HIP: 23, R_HIP: 24, L_KNEE: 25, R_KNEE: 26, L_ANK: 27, R_ANK: 28,
  L_HEEL: 29, R_HEEL: 30, L_TOE: 31, R_TOE: 32,
};

export const FLAG_TEXT = {
  kneesBent: 'Polvet koukussa alastulossa – lentoaika venyy ja tulos voi olla liian suuri. Laskeudu suorin jaloin päkiöille.',
  armsOff: 'Kädet irtosivat lanteilta – tämä ei ollut puhdas "kädet lanteilla" -hyppy.',
  lowFps: 'Matala kuvataajuus – tarkkuus heikko.',
  feetHidden: 'Jalat eivät näkyneet koko hypyn ajan – tulos epävarma.',
  gravity: 'Lantion lentorata ei vastaa painovoimaa – tarkista pituus asetuksista tai kuvauskulma.',
  slowed: 'Hyppy kesti epäuskottavan kauan – video on todennäköisesti hidastettu. Valitse hidastuskerroin.',
  ground: 'Alastulo eri korkeudelle kuin ponnistus (liikuit kameraa kohti/poispäin tai laskeuduit korokkeelle) – tulos epävarma.',
};
/** Flags that make a result unusable rather than merely uncertain: never saved to history. */
export const BLOCKING_FLAGS = new Set(['slowed']);
export const isSaveable = r => !r.flags.some(f => BLOCKING_FLAGS.has(f));

// ---------- flight-time physics (shared by automatic and manual measurement) ----------

/** Jump height (cm) from flight time T (s): h = g·T²/8. */
export const heightFromFlight = T => (G * T * T / 8) * 100;

/** Error estimate (cm): a sampling term — dh/dT = g·T/4 with ~0.45 frame of combined edge
 *  uncertainty — plus landmark noise (≈ 0.7·σ) plus a 0.5 cm floor for what synthetic tests can't
 *  see (pose-model bias at the feet, toe-off vs. landmark). Without the floor the ± at 240 fps
 *  came out below the test suite's own measured error. */
export const flightErrCm = (T, fps, noiseCm = 0) =>
  fps > 0 ? Math.hypot((G * T / 4) * (0.45 / fps) * 100, 0.7 * noiseCm, 0.5) : NaN;

/** A wrong time base scales the hip arc's apparent gravity by 1/k², so g from the jumps tells how
 *  much a clip is slowed down. Returns the likely factor among 1/2/4/8 when it differs from the
 *  one assumed (`slow`), else null. */
export function slowdownFactor(jumps, slow = 1) {
  const ks = jumps.filter(r => r.impliedG > 0).map(r => Math.sqrt(G / r.impliedG) * slow);
  if (!ks.length) return null;
  const k = median(ks);
  const best = [1, 2, 4, 8].reduce((a, b) => (Math.abs(Math.log(b / k)) < Math.abs(Math.log(a / k)) ? b : a));
  return best !== slow && Math.abs(Math.log(k / best)) < 0.3 ? best : null;
}

// ---------- small numeric helpers ----------

export function quantile(values, q) {
  if (!values.length) return NaN;
  const a = values.slice().sort((x, y) => x - y);
  const pos = (a.length - 1) * q, lo = Math.floor(pos);
  return a[lo] + (a[Math.min(lo + 1, a.length - 1)] - a[lo]) * (pos - lo);
}
export const median = v => quantile(v, 0.5);

function linfit(xs, ys) {                       // least squares y = a + b·x
  const n = xs.length;
  let sx = 0, sy = 0;
  for (let i = 0; i < n; i++) { sx += xs[i]; sy += ys[i]; }
  const mx = sx / n, my = sy / n;
  let num = 0, den = 0;
  for (let i = 0; i < n; i++) { num += (xs[i] - mx) * (ys[i] - my); den += (xs[i] - mx) ** 2; }
  const b = den ? num / den : NaN;
  return { a: my - b * mx, b };
}

function parabolaFit(ts, ys) {                  // least squares y = c + b·u + a·u², u = t − mean(t)
  const n = ts.length, m = ts.reduce((s, t) => s + t, 0) / n;
  let s1 = 0, s2 = 0, s3 = 0, s4 = 0, y0 = 0, y1 = 0, y2 = 0;
  for (let i = 0; i < n; i++) {
    const u = ts[i] - m, u2 = u * u;
    s1 += u; s2 += u2; s3 += u2 * u; s4 += u2 * u2;
    y0 += ys[i]; y1 += ys[i] * u; y2 += ys[i] * u2;
  }
  // Solve the 3×3 normal equations by Cramer's rule.
  const M = [[n, s1, s2], [s1, s2, s3], [s2, s3, s4]], R = [y0, y1, y2];
  const det3 = A => A[0][0] * (A[1][1] * A[2][2] - A[1][2] * A[2][1])
    - A[0][1] * (A[1][0] * A[2][2] - A[1][2] * A[2][0])
    + A[0][2] * (A[1][0] * A[2][1] - A[1][1] * A[2][0]);
  const D = det3(M);
  if (!D) return null;
  const col = k => M.map((row, r) => row.map((v, c) => (c === k ? R[r] : v)));
  const c = det3(col(0)) / D, b = det3(col(1)) / D, a = det3(col(2)) / D;
  return { a, b, c, m };
}

// ---------- per-frame features ----------

/** Reduce one frame of normalized MediaPipe landmarks to the signals the analysis uses
 *  (pixels, y pointing down). Returns null when the feet aren't visible. */
export function frameFeatures(lm, w, h) {
  if (!lm || lm.length < 33) return null;
  const vis = i => (lm[i].visibility ?? 1) >= MIN_VIS;
  const x = i => lm[i].x * w, y = i => lm[i].y * h;
  const feet = [P.L_HEEL, P.R_HEEL, P.L_TOE, P.R_TOE].filter(vis);
  if (feet.length < 2) return null;
  let foot = -Infinity;
  for (const i of feet) foot = Math.max(foot, y(i));
  const hip = (y(P.L_HIP) + y(P.R_HIP)) / 2;
  const hipX = (x(P.L_HIP) + x(P.R_HIP)) / 2;
  const shX = (x(P.L_SH) + x(P.R_SH)) / 2, shY = (y(P.L_SH) + y(P.R_SH)) / 2;
  const torso = Math.hypot(shX - hipX, shY - hip) || 1;
  const wristOff = Math.max(
    Math.hypot(x(P.L_WR) - x(P.L_HIP), y(P.L_WR) - y(P.L_HIP)),
    Math.hypot(x(P.R_WR) - x(P.R_HIP), y(P.R_WR) - y(P.R_HIP)),
  ) / torso;
  return {
    foot,
    hip,
    eye: (y(P.L_EYE) + y(P.R_EYE)) / 2,
    leg: (y(P.L_ANK) + y(P.R_ANK)) / 2 - hip,
    wrist: wristOff,
  };
}

// ---------- edge refinement ----------

// Fit e(τ) = v·τ − (g/2)·τ² to airborne samples next to an edge, where τ is time since takeoff
// (dir = +1) or time until landing (dir = −1). g is in px/s², so gravity only nudges the fit.
function edgeTime(pts, gPx, dir) {
  if (pts.length < 2) return null;
  const u = pts.map(p => dir * p.t), e = pts.map(p => p.e);
  let { a, b } = linfit(u, e);
  if (!(b > 0)) return null;
  let u0 = -a / b;
  for (let it = 0; it < 4; it++) {
    ({ a, b } = linfit(u, e.map((ei, k) => ei + (gPx / 2) * (u[k] - u0) ** 2)));
    if (!(b > 0)) return null;
    u0 = -a / b;
  }
  return dir * u0;
}

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

/** Measure one jump from a sample series. iUp = first clearly airborne sample,
 *  iDown = first clearly landed sample (from JumpDetector). */
export function measureJump(s, iUp, iDown, { statureCm = DEFAULT_STATURE_CM, ref = null, scale: scaleHint = NaN, checkArms = false, maxFlight = MAX_FLIGHT_S } = {}) {
  const has = k => k >= 0 && k < s.length && s[k].f;
  const between = (a, b, all = false) => {
    const out = [];
    for (let k = 0; k < s.length; k++) if (s[k].t >= a && s[k].t <= b && (all || s[k].f)) out.push(k);
    return out;
  };
  const tUp = s[iUp].t, tDown = s[iDown].t;

  const pre = between(tUp - 0.6, tUp - 0.02);
  if (pre.length < 3) return { ok: false, reason: 'feet' };
  // Standing eye-to-floor height in px, from the standing reference or the detector's 3 s window.
  // Never from the pre-takeoff window: that is the countermovement squat, which would shrink the
  // scale and inflate every cm value.
  const scale = ref ? ref.scale : scaleHint;
  if (!(scale > 0)) return { ok: false, reason: 'scale' };
  const cmPx = scale / (EYE_RATIO * statureCm);          // px per cm
  const gPx = G * 100 * cmPx;                            // gravity in px/s²

  // Ground line = median of the ground-contact samples. The 90th percentile only picks out which
  // samples are contacts (run-up strides are airborne); using it directly would bias the ground
  // ~1.3σ low and stretch every flight.
  const groundOf = idx => {
    const v = idx.map(k => s[k].f.foot), p90 = quantile(v, 0.9);
    const contact = v.filter(x => x > p90 - 3 * cmPx);
    return { g: median(contact), contact };
  };
  const { g: gPre, contact } = groundOf(pre);
  const post = between(tDown + 0.02, tDown + 0.4);
  const gPost = post.length >= 3 ? groundOf(post).g : gPre;
  const sigma = 1.4826 * median(contact.map(v => Math.abs(v - gPre)));
  // Only samples clearly above ground (> AIR) are fitted; the ones between 0 and AIR are too
  // easily noise (a grounded sample reading 2 cm high moved a landing by 100 ms before this).
  const AIR = Math.max(4 * cmPx, 6 * sigma);
  const GROUNDED = Math.max(0.7 * cmPx, 2 * sigma);      // "still reads as grounded" level
  const span = between(tUp - 0.6, tDown + 0.4, true).map(k => s[k].t);
  const dtMed = median(span.slice(1).map((t, i) => t - span[i])) || 1 / 30;
  const fitSpan = Math.max(EDGE_FIT_S, 2.2 * dtMed);    // ≥ 3 samples at low frame rates

  const eUp = k => gPre - s[k].f.foot;
  const eDn = k => gPost - s[k].f.foot;

  // Takeoff: first clearly airborne sample j, fitted forward; clamped between the last sample that
  // still reads grounded and j.
  let j = iUp;
  while (j < iDown && (!s[j].f || eUp(j) <= AIR)) j++;
  while (has(j - 1) && eUp(j - 1) > AIR) j--;
  if (j >= iDown) return { ok: false, reason: 'feet' };
  let k0 = j - 1;
  while (k0 >= 0 && (!s[k0].f || eUp(k0) > GROUNDED)) k0--;
  if (k0 < 0) return { ok: false, reason: 'feet' };
  const upPts = [];
  for (let k = j; k < iDown && s[k].t <= s[j].t + fitSpan; k++) if (s[k].f) upPts.push({ t: s[k].t, e: eUp(k) });
  const t0fit = edgeTime(upPts, gPx, +1);
  const T0 = t0fit == null ? (s[k0].t + s[j].t) / 2 : clamp(t0fit, s[k0].t, s[j].t);

  // Landing: last clearly airborne sample, fitted backward; clamped between it and the first
  // sample after it that reads grounded.
  let last = iDown - 1;
  while (last > j && (!s[last].f || eDn(last) <= AIR)) last--;
  let m1 = last + 1;
  while (m1 < s.length && (!s[m1].f || eDn(m1) > GROUNDED)) m1++;
  if (m1 >= s.length) m1 = iDown;
  const dnPts = [];
  for (let k = last; k > j && s[k].t >= s[last].t - fitSpan; k--) if (s[k].f) dnPts.unshift({ t: s[k].t, e: eDn(k) });
  const t1fit = edgeTime(dnPts, gPx, -1);
  const T1 = t1fit == null ? (s[last].t + s[m1].t) / 2 : clamp(t1fit, s[last].t, s[m1].t);

  const T = T1 - T0;
  if (!(T >= MIN_FLIGHT_S)) return { ok: false, reason: 'short', flightMs: T * 1000 };
  const heightCm = heightFromFlight(T);

  const around = between(T0 - 0.2, T1 + 0.2, true);
  const aSpan = around.length > 1 ? s[around[around.length - 1]].t - s[around[0]].t : 0;
  const fps = aSpan > 0 ? (around.length - 1) / aSpan : 0;
  const errCm = flightErrCm(T, fps, sigma / cmPx);

  const flags = [];
  if (T > maxFlight) flags.push('slowed');
  if (fps && fps < 20) flags.push('lowFps');
  if (Math.abs(gPost - gPre) > 6 * cmPx) flags.push('ground');
  const flightIdx = between(T0, T1);
  const expected = Math.max(1, Math.floor(T * fps));
  if (flightIdx.length < 0.75 * expected) flags.push('feetHidden');

  // Leg shortening at touchdown vs. at takeoff → tucked legs inflate flight time.
  if (s[last].f.leg < 0.88 * Math.max(s[j].f.leg, ref ? ref.leg : 0)) flags.push('kneesBent');

  if (checkArms) {
    const armIdx = between(T0 - 0.6, T1);
    if (armIdx.some(k => s[k].f.wrist > 0.6)) flags.push('armsOff');
  }

  // Hip trajectory: apex from a parabola over the middle of the flight; its curvature gives an
  // implied g, which checks the px→cm scale and the time base together.
  let hipApex = NaN, impliedG = NaN;
  const mid = between(T0 + 0.15 * T, T1 - 0.15 * T);
  if (mid.length >= 6) {
    const fit = parabolaFit(mid.map(k => s[k].t), mid.map(k => s[k].f.hip));
    if (fit && fit.a > 0) {
      impliedG = (2 * fit.a) / cmPx / 100;
      const uV = -fit.b / (2 * fit.a);
      if (uV > T0 - fit.m && uV < T1 - fit.m) hipApex = fit.c - (fit.b * fit.b) / (4 * fit.a);
    }
  }
  if (!Number.isFinite(hipApex) && flightIdx.length) hipApex = Math.min(...flightIdx.map(k => s[k].f.hip));
  const hipAt = t => {
    let a = -1, b = -1;
    for (let k = 0; k < s.length; k++) if (s[k].f) { if (s[k].t <= t) a = k; else { b = k; break; } }
    if (a < 0 || b < 0) return NaN;
    return s[a].f.hip + (s[b].f.hip - s[a].f.hip) * (t - s[a].t) / (s[b].t - s[a].t);
  };
  const hipT0 = hipAt(T0);
  const hipRiseCm = ref && Number.isFinite(hipApex) ? (ref.hip - hipApex) / cmPx : NaN;
  const hipTakeoffCm = Number.isFinite(hipApex) ? (hipT0 - hipApex) / cmPx : NaN;
  // The g check needs a hip arc well above landmark noise; on small hops it is just noise.
  if (!(hipTakeoffCm >= 8)) impliedG = NaN;
  if (Number.isFinite(impliedG) && (impliedG < 7 || impliedG > 12.5) && !flags.includes('slowed')) flags.push('gravity');

  // Chart series: foot height and hip rise in cm, time relative to takeoff.
  const chartIdx = between(T0 - 0.8, T1 + 0.5);
  const hipBase = ref ? ref.hip : hipT0;
  const chart = {
    t: chartIdx.map(k => s[k].t - T0),
    foot: chartIdx.map(k => (s[k].t < (T0 + T1) / 2 ? eUp(k) : eDn(k)) / cmPx),
    hip: chartIdx.map(k => (hipBase - s[k].f.hip) / cmPx),
    idx: chartIdx,
  };

  return {
    ok: true, heightCm, flightMs: T * 1000, errCm, fps, t0: T0, t1: T1,
    hipRiseCm, hipTakeoffCm, impliedG, flags, chart,
  };
}

// ---------- streaming detector ----------

/** Feed frames in time order with push(t, features); call flush() at the end of a clip. Emits:
 *  {type:'ready'} {type:'lost'} {type:'takeoff'} {type:'jump', result} {type:'reject', reason, result}.
 *  requireReady: only arm after the person has stood still (standing jumps in live mode).
 *  timeout > maxFlight and a longer riseWindow let video mode still detect, measure and flag a
 *  jump in footage that is slowed down but read as real time (an 8× slow-mo small hop rises 5 cm
 *  in ~0.2 s of clip time). */
export class JumpDetector {
  constructor({ statureCm = DEFAULT_STATURE_CM, requireReady = false, maxFlight = MAX_FLIGHT_S, timeout = null, riseWindow = 0.2, keepAll = false, checkArms = false } = {}) {
    Object.assign(this, { statureCm, requireReady, maxFlight, timeout: timeout ?? maxFlight + 0.5, riseWindow, keepAll, checkArms });
    this.samples = [];
    this.state = 'search';          // search → ready → air → post → (search | ready)
    this.ref = null;                // last standing reference {t, hip, scale, leg}
    this.bestRatio = 0;             // highest (foot−hip)/(foot−eye) of a still window: upright posture
    this.air = null;
    this.ground = NaN;
    this.lastSeen = -Infinity;
  }

  status() {
    if (this.state === 'air' || this.state === 'post') return 'air';
    const last = this.samples[this.samples.length - 1];
    if (!last || !last.f) return 'noPerson';
    return this.state === 'ready' || !this.requireReady ? 'ready' : 'settle';
  }

  _window(i, span) {
    const s = this.samples, out = [], from = s[i].t - span;
    for (let k = i; k >= 0 && s[k].t >= from; k--) if (s[k].f) out.push(s[k]);
    return out;
  }

  push(t, f) {
    const s = this.samples;
    if (s.length && t <= s[s.length - 1].t) return null;   // duplicate / out-of-order frame
    s.push({ t, f });
    const i = s.length - 1;
    if (this.state === 'air') return this._inAir(i);
    if (this.state === 'post') return this._post(i);

    if (!this.keepAll && s.length > 400 && s[0].t < t - 12) s.splice(0, s.length - 300);
    const idx = s.length - 1;

    if (!f) {
      if (t - this.lastSeen > 0.7 && this.state === 'ready') { this.state = 'search'; return { type: 'lost' }; }
      return null;
    }
    this.lastSeen = t;

    const win = this._window(idx, 1.0);
    if (win.length < 4) return null;
    this.ground = quantile(win.map(w => w.f.foot), 0.9);
    // Scale = standing height over the last 3 s: a squat must not shrink the thresholds.
    const scale = quantile(this._window(idx, 3.0).map(w => w.f.foot - w.f.eye), 0.9);
    const cmPx = scale / (EYE_RATIO * this.statureCm);

    let ev = null;
    const st = this._window(idx, 0.5);
    if (st.length >= 5 && t - st[st.length - 1].t >= 0.4) {
      const range = arr => Math.max(...arr) - Math.min(...arr);
      if (range(st.map(w => w.f.foot)) < 3 * cmPx && range(st.map(w => w.f.hip)) < 4 * cmPx) {
        // Standing reference = a still window in upright posture. A held squat (squat jump) is
        // still too; its hip sits lower relative to the eyes, and that ratio doesn't depend on
        // camera distance, unlike any pixel height.
        const ratio = median(st.map(w => (w.f.foot - w.f.hip) / (w.f.foot - w.f.eye)));
        this.bestRatio = Math.max(this.bestRatio, ratio);
        if (ratio >= 0.95 * this.bestRatio) {
          this.ref = { t, hip: median(st.map(w => w.f.hip)), scale: median(st.map(w => w.f.foot - w.f.eye)), leg: median(st.map(w => w.f.leg)) };
        }
        if (this.state === 'search') { this.state = 'ready'; ev = { type: 'ready' }; }
      }
    }

    if (this.requireReady && this.state !== 'ready') return ev;
    const prev = s[idx - 1];
    const up = TAKEOFF_CM * cmPx;
    // A takeoff is fast: the feet must also have risen `up` within the last riseWindow. Slow drift
    // of the ground line (walking, shifting the stance, moving in depth) never passes this.
    const recentLow = Math.max(...this._window(idx, this.riseWindow).map(w => w.f.foot));
    if (prev && prev.f && this.ground - f.foot > up && this.ground - prev.f.foot > up && recentLow - f.foot > up) {
      this.air = { iUp: idx - 1, tUp: prev.t, ground: this.ground, cmPx, scale, peak: 0, pendingDown: null, iDown: null };
      this.state = 'air';
      return { type: 'takeoff' };
    }
    return ev;
  }

  _rest() {
    this.air = null;
    this.state = this.requireReady ? 'search' : 'ready';
  }

  _inAir(i) {
    const a = this.air, smp = this.samples[i];
    if (smp.t - a.tUp > this.timeout) { this._rest(); return { type: 'reject', reason: 'timeout' }; }
    if (!smp.f) return null;
    const e = a.ground - smp.f.foot;
    a.peak = Math.max(a.peak, e);
    // Landed: back at the takeoff ground, or — when the ground line has moved (stepping in
    // depth, landing on a box) — the fall has clearly started and then the feet stopped dead.
    // At the apex the feet are momentarily still too, hence the 30 % descent requirement.
    let stopped = false;
    if (a.peak - e > 0.3 * a.peak) {
      const back = this._window(i, 0.06).filter(w => w !== smp);
      stopped = back.length > 0 && Math.abs(smp.f.foot - back[back.length - 1].f.foot) < 1.5 * a.cmPx;
    }
    if (e < LANDED_CM * a.cmPx || stopped) {
      if (a.pendingDown != null) { a.iDown = a.pendingDown; this.state = 'post'; return this._post(i); }
      a.pendingDown = i;
    } else a.pendingDown = null;
    return null;
  }

  _post(i) {
    const s = this.samples;
    return s[i].t < s[this.air.iDown].t + 0.4 ? null : this._measure();
  }

  /** End of input: measure a jump whose landing was seen but whose post-landing window was cut
   *  short by the end of the clip (measureJump falls back to the takeoff ground). */
  flush() {
    const a = this.air;
    if (!a) return null;
    if (a.iDown == null) a.iDown = a.pendingDown;
    return a.iDown == null ? null : this._measure();
  }

  _measure() {
    const a = this.air, s = this.samples, r = this.ref, tUp = s[a.iUp].t;
    // Scale at the takeoff spot: tallest posture of the last 0.8 s (standing or the extension right
    // before toe-off). A longer window can still hold an earlier, closer camera position; a
    // shorter one may be all squat. The standing reference counts only if it matches (±10 %):
    // same distance and really upright.
    const recent = s.filter(x => x.f && x.t >= tUp - 0.8 && x.t <= tUp).map(x => x.f.foot - x.f.eye);
    const scale = recent.length >= 3 ? quantile(recent, 0.9) : a.scale;
    const ref = r && tUp - r.t < 20 && Math.abs(r.scale / scale - 1) < 0.1 ? r : null;
    const result = measureJump(s, a.iUp, a.iDown, { statureCm: this.statureCm, ref, scale, checkArms: this.checkArms, maxFlight: this.maxFlight });
    this._rest();
    return result.ok ? { type: 'jump', result } : { type: 'reject', reason: result.reason, result };
  }
}

/** Offline: run the detector over a complete, time-ordered sample list. */
export function findJumps(samples, opts = {}) {
  const det = new JumpDetector({ ...opts, keepAll: true });
  const jumps = [];
  for (const smp of samples) {
    const ev = det.push(smp.t, smp.f);
    if (ev && ev.type === 'jump') jumps.push({ ...ev.result, samples: det.samples });
  }
  const ev = det.flush();
  if (ev && ev.type === 'jump') jumps.push({ ...ev.result, samples: det.samples });
  return jumps;
}
