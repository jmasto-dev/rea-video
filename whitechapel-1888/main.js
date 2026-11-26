// Whitechapel, 1888 — Artistic True Crime in Woodcut Print
import { clamp, lerp, ss, mulberry } from '/core/lib.js';
import * as WC from './engine/index.js';
import * as S from './stage.js';
import { curl } from './trans.js';

const W = 1920, H = 1080;
window.DUR = 45.0;
const cv = document.getElementById('cv');
const g = cv.getContext('2d');
const seg = (t, a, b) => clamp((t - a) / (b - a));

await document.fonts.ready;

// Pre-build woodcut strokes for each plate (deterministic, seeded)
const PW = 1848, PH = 912;

// Plate 1: Victorian Whitechapel rooftops, cobbled alley, gaslight rays
const P1 = (() => {
  const roofs = [];
  const R = mulberry(1888);
  for (let i = 0; i < 11; i++) {
    const x = i * 175 - 40, h = 240 + (i % 3) * 70 + R() * 40;
    const roof = [[x, 640], [x, 640 - h], [x + 88, 640 - h - 90], [x + 178, 640 - h], [x + 178, 640]];
    roofs.push(WC.shape([roof], {
      tone: () => (xx, yy) => clamp(0.75 - (yy - (640 - h - 90)) / 320 * 0.65),
      dir: (xx) => xx < x + 88 ? 2.4 : 0.7,
      sp: 7, lo: 0.25, hi: 0.85, halo: 3, seed: 10 + i,
      reveal: { t0: 0.4 + i * 0.12, t1: 1.4 + i * 0.12, key: (xx, yy) => 0.4 + i * 0.12 },
    }));
  }
  const gasRays = WC.rays(1320, 410, {
    n: 52, r0: 18, r1: 310, w0: 12, w1: 1.5, seed: 99,
    reveal: { t0: 1.5, t1: 3.5, key: (x, y) => Math.hypot(x - 1320, y - 410) },
  });
  const cobbles = WC.flecks(
    Array.from({ length: 140 }, (_, i) => [120 + (i * 47 + R() * 35) % 1620, 665 + R() * 220]),
    { r: [4, 14], seed: 303, reveal: { t0: 2.0, t1: 4.0, key: (x, y) => y } }
  );
  const skyFog = WC.flecks(
    Array.from({ length: 120 }, () => [R() * PW, 40 + R() * 280]),
    { r: [2, 6], seed: 404, reveal: { t0: 0.5, t1: 3.0, key: () => R() } }
  );
  return { roofs, gasRays, cobbles, skyFog };
})();

// Plate 2: The Footsteps — Victorian archway & top-hatted figure vanishing
const P2 = (() => {
  const R = mulberry(1889);
  const arch = WC.shape([
    [[0, 0], [PW, 0], [PW, PH], [1420, PH], [1420, 420], [924, 150], [428, 420], [428, PH], [0, PH]]
  ], {
    tone: () => (x, y) => clamp(0.78 - Math.hypot(x - 924, y - 480) / 1100),
    dir: () => 1.57, sp: 9, lo: 0.2, hi: 0.75, halo: 5, seed: 55,
    reveal: { t0: 0.2, t1: 2.0, key: (x, y) => y },
  });
  const figure = WC.shape([
    [[885, 360], [963, 360], [955, 420], [975, 425], [873, 425], [893, 420]],
    [[895, 428], [953, 428], [1005, 710], [843, 710]],
  ], {
    tone: () => (x) => clamp(0.85 - (x - 843) / 162 * 0.9),
    dir: () => 0.4, sp: 6, lo: 0.5, hi: 0.95, halo: 4, seed: 77,
    reveal: { t0: 1.5, t1: 2.8, key: (x, y) => y },
  });
  const steps = WC.flecks(
    [[870, 760], [935, 795], [880, 835], [950, 875]],
    { r: [8, 13], seed: 88, reveal: { t0: 2.5, t1: 4.5, key: (x, y) => y } }
  );
  const rain = WC.flecks(
    Array.from({ length: 160 }, () => [430 + R() * 980, 180 + R() * 680]),
    { r: [2, 5], seed: 91, reveal: { t0: 0.6, t1: 3.0, key: () => R() } }
  );
  return { arch, figure, steps, rain };
})();

// Plate 3: Five Dates carved one by one
const P3_DATES = [
  { t: 19.0, label: 'AUG 31', sub: 'BUCK’S ROW', x: 260 },
  { t: 20.6, label: 'SEP 8',  sub: 'HANBURY ST', x: 590 },
  { t: 22.2, label: 'SEP 30', sub: 'BERNER ST',  x: 924 },
  { t: 23.8, label: 'SEP 30', sub: 'MITRE SQ',   x: 1258 },
  { t: 25.4, label: 'NOV 9',  sub: 'MILLER’S CT', x: 1588 },
];

const [UP_C, upG] = WC.canvas(W, H);
const [DN_C, dnG] = WC.canvas(W, H);

const VO = [
  { t: 1.0,  d: 6.8, text: 'Autumn 1888. Beneath the gaslights of Whitechapel, London held its breath.' },
  { t: 9.8,  d: 7.4, text: 'Between August and November, five victims fell in the narrow alleys of the East End.' },
  { t: 19.2, d: 7.8, text: 'Scotland Yard flooded the streets, yet the killer left no face—only a name signed in blood.' },
  { t: 29.0, d: 7.5, text: '“From Hell.” Then, as abruptly as the terror began, the footsteps vanished into the fog.' },
  { t: 38.0, d: 5.5, text: 'More than a century later, the block remains unfinished.' },
];

window.EV = [
  { t: 0.4,  type: 'gouge' },
  { t: 2.0,  type: 'lantern' },
  { t: 9.0,  type: 'peel' },
  { t: 11.2, type: 'step' },
  { t: 18.5, type: 'thump' },
  ...P3_DATES.map(d => ({ t: d.t, type: 'tally' })),
  { t: 28.0, type: 'silence' },
  { t: 30.8, type: 'peel' },
  { t: 37.0, type: 'thump' },
];

function drawPlate1(lt, cam, outOff = false) {
  S.begin(cam);
  WC.drawStrokes(S.m, P1.skyFog, { t: lt, color: '#fff' });
  for (const r of P1.roofs) r.draw(S.m, lt);
  if (!outOff) WC.drawStrokes(S.m, P1.gasRays, { t: lt, color: '#fff' });
  WC.drawStrokes(S.m, P1.cobbles, { t: lt, color: '#fff' });

  // Carved title in the upper black wood block
  const tk = seg(lt, 0.8, 3.2);
  if (tk > 0) {
    S.m.save();
    S.m.font = '400 108px "IM Fell English SC"'; S.m.fillStyle = '#fff';
    S.m.beginPath(); S.m.rect(90, 60, 1100 * tk, 180); S.m.clip();
    S.m.fillText('WHITECHAPEL · 1888', 95, 175);
    S.m.restore();
  }

  // Single oxblood colour plate on the carved gaslight rays
  if (!outOff && lt > 1.8) {
    const k = seg(lt, 1.8, 3.5);
    const gr = S.c.createRadialGradient(1320, 410, 10, 1320, 410, 320 * k);
    gr.addColorStop(0, 'rgba(0,0,0,0.95)');
    gr.addColorStop(1, 'rgba(0,0,0,0)');
    S.c.fillStyle = gr;
    S.c.beginPath(); S.c.arc(1320, 410, 320 * k, 0, 7); S.c.fill();
  }
  S.end();
}

function drawPlate2(lt, cam) {
  S.begin(cam);
  P2.arch.draw(S.m, lt);
  WC.drawStrokes(S.m, P2.rain, { t: lt, color: '#fff' });
  P2.figure.draw(S.m, lt);
  WC.drawStrokes(S.m, P2.steps, { t: lt, color: '#fff' });
  // Oxblood glow on the wet cobble footprints
  if (lt > 2.5) {
    for (const [fx, fy] of [[870, 760], [935, 795], [880, 835], [950, 875]]) {
      const k = seg(lt, 2.5 + (fy - 750) / 80, 3.2 + (fy - 750) / 80);
      if (k <= 0) continue;
      S.c.fillStyle = `rgba(0,0,0,${0.85 * k})`;
      S.c.beginPath(); S.c.arc(fx, fy, 18 * k, 0, 7); S.c.fill();
    }
  }
  S.end();
}

function drawPlate3(lt, cam) {
  S.begin(cam);
  for (let i = 0; i < P3_DATES.length; i++) {
    const d = P3_DATES[i], k = seg(18.5 + lt, d.t, d.t + 0.8);
    if (k <= 0) continue;
    // Vertical carved tally slash
    S.m.strokeStyle = '#fff'; S.m.lineWidth = 14; S.m.lineCap = 'round';
    S.m.beginPath(); S.m.moveTo(d.x - 18, 220); S.m.lineTo(lerp(d.x - 18, d.x + 18, k), lerp(220, 560, k)); S.m.stroke();
    // Oxblood colour plate behind each carved tally
    S.c.fillStyle = `rgba(0,0,0,${0.9 * k})`;
    S.c.beginPath(); S.c.arc(d.x, 390, 58 * k, 0, 7); S.c.fill();
    // Carved date & street in the wood
    if (k > 0.5) {
      const a = seg(k, 0.5, 1.0);
      S.m.fillStyle = `rgba(255,255,255,${a})`;
      S.m.font = '400 44px "IM Fell English SC"'; S.m.textAlign = 'center';
      S.m.fillText(d.label, d.x, 650);
      S.m.font = '400 26px "IM Fell English"';
      S.m.fillText(d.sub, d.x, 700);
    }
  }
  S.end();
}

function drawPlate4Block(lt, mirror) {
  S.begin({ x: PW / 2, y: PH / 2, z: 1.0 }, { full: mirror, mirror });
  if (mirror) {
    S.m.fillStyle = '#000';
    S.m.fillRect(-4000, -4000, 12000, 12000);
  }
  // Carved border + "FROM HELL"
  S.m.strokeStyle = '#fff'; S.m.lineWidth = 6;
  S.m.strokeRect(380, 220, 1088, 460);
  S.m.fillStyle = '#fff'; S.m.textAlign = 'center';
  S.m.font = '400 132px "IM Fell English SC"';
  S.m.fillText('FROM HELL', PW / 2, 455);
  S.m.font = 'italic 400 36px "IM Fell English"';
  S.m.fillText('Whitechapel · Oct 1888', PW / 2, 545);
  // Single oxblood wax seal
  if (!mirror && lt > 2.2) {
    const sk = seg(lt, 2.2, 2.8);
    S.m.fillStyle = '#fff'; S.m.beginPath(); S.m.arc(1300, 560, 54 * sk, 0, 7); S.m.fill();
    S.c.fillStyle = `rgba(0,0,0,${0.95 * sk})`; S.c.beginPath(); S.c.arc(1300, 560, 62 * sk, 0, 7); S.c.fill();
  }
  S.end();
}

function activeCap(t) {
  for (const v of VO) if (t >= v.t && t <= v.t + v.d) return v.text;
  return '';
}

window.render = (t) => {
  t = clamp(t, 0, 45.0);
  const inkSeed = Math.floor(t * 12) * 0.13;
  const cap = activeCap(t);

  // Plate 1 (0 - 9.0 s)
  if (t < 9.0) {
    const cam = { x: PW / 2, y: PH / 2, z: 1.0 + t * 0.008 };
    drawPlate1(t, cam, false);
    S.caption(cap);
    S.print(g, { mode: 0, inkSeed, seed: 1, edge: 1, plateAmt: 1, inkAmt: 1, grainAng: 0.05 });
  }
  // Paper Peel Transition (9.0 - 9.8 s)
  else if (t < 9.8) {
    const p = seg(t, 9.0, 9.8);
    drawPlate2(0.8, { x: PW / 2, y: PH / 2, z: 1.0 });
    S.print(g, { mode: 0, inkSeed, seed: 2, edge: 1, plateAmt: 1, inkAmt: 1 });
    drawPlate1(9.0, { x: PW / 2, y: PH / 2, z: 1.07 }, false);
    S.print(upG, { mode: 0, inkSeed, seed: 1, edge: 1, plateAmt: 1, inkAmt: 1 });
    dnG.fillStyle = '#e8dfc9'; dnG.fillRect(0, 0, W, H);
    curl(g, UP_C, DN_C, lerp(W, -400, p * p), 140);
  }
  // Plate 2 (9.8 - 18.5 s)
  else if (t < 18.5) {
    const lt = t - 9.8;
    const cam = { x: PW / 2, y: PH / 2, z: 1.0 + lt * 0.015 };
    drawPlate2(lt, cam);
    S.caption(cap);
    S.print(g, { mode: 0, inkSeed, seed: 2, edge: 1, plateAmt: 1, inkAmt: 1, grainAng: -0.04 });
  }
  // Plate 3 (18.5 - 28.0 s) — Hard cut (new impression, 2 frames misregistration)
  else if (t < 28.0) {
    const lt = t - 18.5;
    drawPlate3(lt, { x: PW / 2, y: PH / 2, z: 1.0 });
    S.caption(cap);
    const mis = lt < 0.1 ? [8, -5] : [3, 2];
    S.print(g, { mode: 0, inkSeed, seed: 3, edge: 1, plateAmt: 1, inkAmt: 1, reg: mis });
  }
  // Plate 4 (28.0 - 37.0 s) — Mirrored Woodblock -> True Print via Peel
  else if (t < 37.0) {
    const lt = t - 28.0;
    if (lt < 2.8) {
      // Show the carved black glossy woodblock itself (mirrored)
      drawPlate4Block(lt, true);
      S.print(g, { mode: 1, inkSeed, seed: 4, edge: 1, plateAmt: 0, inkAmt: 1, sheen: 0.8 });
    } else if (lt < 3.6) {
      const p = seg(lt, 2.8, 3.6);
      drawPlate4Block(lt, false);
      S.caption(cap);
      S.print(g, { mode: 0, inkSeed, seed: 4, edge: 1, plateAmt: 1, inkAmt: 1 });
      drawPlate4Block(2.8, true);
      S.print(upG, { mode: 1, inkSeed, seed: 4, edge: 1, plateAmt: 0, inkAmt: 1, sheen: 0.8 });
      dnG.fillStyle = '#e8dfc9'; dnG.fillRect(0, 0, W, H);
      curl(g, UP_C, DN_C, lerp(W, -400, p * p), 140);
    } else {
      drawPlate4Block(lt, false);
      S.caption(cap);
      S.print(g, { mode: 0, inkSeed, seed: 4, edge: 1, plateAmt: 1, inkAmt: 1 });
    }
  }
  // Plate 5 (37.0 - 45.0 s) — The Unsolved Corner (gaslight goes out)
  else {
    const lt = t - 37.0;
    const cam = { x: PW / 2, y: PH / 2, z: 1.06 - lt * 0.01 };
    drawPlate1(8.0, cam, true); // gaslight off -> uncarved dark corner
    S.caption(cap);
    S.print(g, { mode: 0, inkSeed, seed: 5, edge: 1, plateAmt: 0, inkAmt: 1 });
  }
};

window.TEXTS = (t) => {
  const out = [];
  if (t >= 3.5 && t < 9.0) out.push({ id: 'title', text: 'WHITECHAPEL · 1888', x0: 95, y0: 60, x1: 1100, y1: 200 });
  if (t >= 31.8 && t < 37.0) out.push({ id: 'hell', text: 'FROM HELL', x0: 400, y0: 320, x1: 1400, y1: 480 });
  return out;
};

window.READY = true;
