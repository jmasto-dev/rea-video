// Binance Heist — Act 1 (0.00 - 41.08s, 24fps, 2.39:1 Scope)
// Every single beat is genuinely animated frame-by-frame in Lemo-Opuscar multi-style.
import { makeCRT } from './crt.js';

const W = 1920, H = 1080;
const BAR_H = 138; // 2.39:1 active frame = 1920x804
window.DUR = 41.08;

const cv = document.getElementById('cv');
const g = cv.getContext('2d');

const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const ss = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const seg = (t, a, b) => clamp((t - a) / (b - a));

function loadImg(src) {
  return new Promise((res, rej) => {
    const im = new Image();
    im.onload = () => res(im);
    im.onerror = rej;
    im.src = src;
  });
}

const [imgBed, imgThumb, imgMono, imgLock, imgStamp, imgCorr, imgWood] = await Promise.all([
  loadImg('./assets/bed_phone.jpg'),
  loadImg('./assets/phone_thumb.jpg'),
  loadImg('./assets/beat01_monolith.png'),
  loadImg('./assets/beat07_padlock.png'),
  loadImg('./assets/beat08_stamp.png'),
  loadImg('./assets/beat10_corridor.png'),
  loadImg('./assets/beat11_woodcut.png'),
]);

// Offscreen canvas for CRT shader (Beat 6)
const crtSrc = document.createElement('canvas');
crtSrc.width = 1920; crtSrc.height = 804;
const cg = crtSrc.getContext('2d');
const crtOut = document.createElement('canvas');
crtOut.width = 1920; crtOut.height = 804;
const crt = makeCRT(crtOut);

// Fine 35mm grain tile
const grainC = document.createElement('canvas');
grainC.width = 480; grainC.height = 270;
const gg = grainC.getContext('2d');
const gd = gg.createImageData(480, 270);
let s = 2026;
const rnd = () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
for (let i = 0; i < gd.data.length; i += 4) {
  const v = 128 + (rnd() - 0.5) * 44;
  gd.data[i] = gd.data[i + 1] = gd.data[i + 2] = v;
  gd.data[i + 3] = 16;
}
gg.putImageData(gd, 0, 0);

function drawCover(im, scale = 1, dx = 0, dy = 0, filter = 'none') {
  const activeH = H - 2 * BAR_H;
  const ir = im.width / im.height, cr = W / activeH;
  let dw, dh;
  if (ir > cr) { dh = activeH * scale; dw = dh * ir; }
  else { dw = W * scale; dh = dw / ir; }
  g.save();
  g.filter = filter;
  g.drawImage(im, (W - dw) / 2 + dx, BAR_H + (activeH - dh) / 2 + dy, dw, dh);
  g.restore();
}

// BEAT 1 (0.00 - 4.20s): Approved 3D monolith + live pulsing seam glow & 10 shooting streams
function beat1(lt) {
  const crack = ss(seg(lt, 0.3, 2.0));
  const burst = ss(seg(lt, 1.9, 4.1));
  drawCover(imgMono, 1.0 + lt * 0.02, 0, 0, `brightness(${0.85 + 0.25 * crack}) contrast(1.06)`);

  const cx = W / 2, cy = H / 2;
  if (burst > 0) {
    for (let i = 0; i < 10; i++) {
      const ang = (i / 10) * Math.PI * 2 - Math.PI / 2;
      const r0 = 150;
      const r1 = 150 + 950 * burst;
      g.save();
      g.globalCompositeOperation = 'screen';
      g.strokeStyle = i % 2 === 0 ? 'rgba(245, 190, 90, 0.82)' : 'rgba(115, 215, 245, 0.82)';
      g.lineWidth = 4;
      g.beginPath();
      g.moveTo(cx + Math.cos(ang) * r0, cy + Math.sin(ang) * r0);
      g.lineTo(cx + Math.cos(ang) * r1, cy + Math.sin(ang) * r1);
      g.stroke();
      g.restore();
    }
  }
}

// BEAT 2 (4.20 - 8.52s): Blueprint isometric pull-back + 10 conduits striking 10 nodes
const CHAINS = ['SOL', 'ETH', 'BTC', 'LINK', 'DOGE', 'AVAX', 'ADA', 'BNB', 'TRON', 'XRP'];
function beat2(lt) {
  g.fillStyle = '#071019';
  g.fillRect(0, 0, W, H);

  // Blueprint grid
  g.strokeStyle = 'rgba(70, 145, 200, 0.12)';
  g.lineWidth = 1;
  for (let x = 0; x < W; x += 64) { g.beginPath(); g.moveTo(x, BAR_H); g.lineTo(x, H - BAR_H); g.stroke(); }
  for (let y = BAR_H; y < H - BAR_H; y += 64) { g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }

  const cx = W / 2, cy = H / 2;
  const zoom = lerp(1.22, 0.94, ss(seg(lt, 0, 4.32)));
  g.save();
  g.translate(cx, cy);
  g.scale(zoom, zoom);

  // Central hub
  g.strokeStyle = 'rgba(245, 185, 80, 0.8)';
  g.lineWidth = 3;
  g.beginPath(); g.arc(0, 0, 56, 0, 7); g.stroke();
  g.font = '700 18px monospace'; g.textAlign = 'center'; g.fillStyle = '#f5b950';
  g.fillText('BINANCE', 0, 6);

  // 10 conduits racing outward & striking nodes sequentially
  for (let i = 0; i < 10; i++) {
    const ang = (i / 10) * Math.PI * 2 - Math.PI / 2;
    const tx = Math.cos(ang) * 460;
    const ty = Math.sin(ang) * 305;
    const trace = ss(seg(lt, 0.2 + i * 0.18, 1.4 + i * 0.18));
    const hit = seg(lt, 1.3 + i * 0.18, 1.9 + i * 0.18);

    g.strokeStyle = i % 2 === 0 ? 'rgba(245, 185, 80, 0.85)' : 'rgba(110, 215, 245, 0.85)';
    g.lineWidth = 3;
    g.beginPath();
    g.moveTo(Math.cos(ang) * 56, Math.sin(ang) * 56);
    g.lineTo(lerp(Math.cos(ang) * 56, tx, trace), lerp(Math.sin(ang) * 56, ty, trace));
    g.stroke();

    // Node ring
    g.fillStyle = hit > 0 ? 'rgba(12, 24, 36, 0.95)' : 'rgba(7, 16, 25, 0.7)';
    g.strokeStyle = hit > 0 ? (i % 2 === 0 ? '#f5b950' : '#6ed7f5') : 'rgba(110, 170, 210, 0.35)';
    g.lineWidth = hit > 0 ? 3 : 1.5;
    g.beginPath(); g.arc(tx, ty, 38, 0, 7); g.fill(); g.stroke();
    if (hit > 0 && hit < 1) {
      g.strokeStyle = `rgba(255, 255, 255, ${1 - hit})`;
      g.beginPath(); g.arc(tx, ty, 38 + 36 * hit, 0, 7); g.stroke();
    }
    g.fillStyle = hit > 0 ? '#fff' : 'rgba(180, 210, 230, 0.5)';
    g.font = '700 18px monospace';
    g.fillText(CHAINS[i], tx, ty + 6);
  }
  g.restore();
  g.textAlign = 'left';
}

// BEAT 3 (8.52 - 12.00s): Live spinning odometer to $6,300,000,000 + draining particles
function beat3(lt) {
  g.fillStyle = '#07080b';
  g.fillRect(0, 0, W, H);

  const prog = ss(seg(lt, 0.0, 2.0));
  const val = Math.floor(prog * 6300000000);
  const formatted = '$' + val.toLocaleString('en-US');

  // Draining vertical streaks in background
  g.strokeStyle = 'rgba(217, 43, 43, 0.25)';
  g.lineWidth = 2;
  for (let i = 0; i < 28; i++) {
    const x = 120 + i * 62;
    const y = ((lt * 520 + i * 97) % 860) + BAR_H - 60;
    g.beginPath(); g.moveTo(x, y); g.lineTo(x, y + 65); g.stroke();
  }

  g.textAlign = 'center';
  g.font = '600 26px monospace';
  g.fillStyle = 'rgba(234, 228, 215, 0.72)';
  g.fillText('20:05 — 20:25 UTC  //  TOTAL OUTFLOW', W / 2, H / 2 - 80);

  g.font = '800 134px monospace';
  g.fillStyle = prog >= 0.99 ? '#d92b2b' : '#eae4d7';
  g.fillText(formatted, W / 2, H / 2 + 52);

  if (prog >= 0.99) {
    g.font = '700 32px monospace';
    g.fillStyle = '#eae4d7';
    g.fillText('GONE IN TWENTY MINUTES', W / 2, H / 2 + 125);
  }
  g.textAlign = 'left';
}

// BEAT 4 (12.00 - 15.80s): Dark bedroom phone glow + live screen flicker
function beat4(lt) {
  const flick = 0.88 + 0.12 * Math.sin(lt * 14);
  drawCover(imgBed, 1.0 + lt * 0.015, 0, 0, `brightness(${flick}) contrast(1.1) saturate(0.65)`);
}

// BEAT 5 (15.80 - 19.04s): Macro thumb tapping dead grey WITHDRAW button at 0.5s, 1.2s, 1.9s
function beat5(lt) {
  let tapAmt = 0;
  for (const tp of [0.5, 1.2, 1.9]) {
    const d = Math.abs(lt - tp);
    if (d < 0.12) tapAmt = Math.max(tapAmt, 1 - d / 0.12);
  }
  drawCover(imgThumb, 1.14 + 0.025 * tapAmt, -35, 10, 'brightness(0.84) contrast(1.12) saturate(0.62)');

  // Dead grey shock ring on each tap
  for (const tp of [0.5, 1.2, 1.9]) {
    const age = lt - tp;
    if (age >= 0 && age < 0.45) {
      const k = age / 0.45;
      g.strokeStyle = `rgba(170, 175, 185, ${0.55 * (1 - k)})`;
      g.lineWidth = 3;
      g.beginPath();
      g.arc(1180, 445, 24 + 90 * k, 0, 7);
      g.stroke();
    }
  }
}

// BEAT 6 (19.04 - 22.08s): WebGL2 Curved CRT Audit Logs scrolling live with OK checksums
function beat6(lt) {
  cg.fillStyle = '#030804';
  cg.fillRect(0, 0, 1920, 804);

  cg.font = '500 24px monospace';
  const scroll = lt * 130;
  for (let i = -1; i < 18; i++) {
    const y = i * 48 - (scroll % 48) + 80;
    const tx = 884900 + Math.floor(scroll / 48) + i;
    cg.fillStyle = '#79e88a';
    cg.fillText(`[OK] CHECKSUM_VALID   TX#${tx}   BLOCK_HASH: 0x9f2a..c81   ERR: 0`, 140, y);
  }
  cg.fillStyle = '#061409';
  cg.fillRect(120, 40, 1680, 54);
  cg.fillStyle = '#b4ffbf';
  cg.font = '700 24px monospace';
  cg.fillText('BINANCE FORENSIC AUDIT // LIVE LOG STREAM   |   ERRORS DETECTED: 0', 140, 74);

  crt.render(crtSrc, Math.floor(lt * 24), {
    curv: 0.045, scan: 0.3, glow: 0.55, halo: 0.22,
    amber: [0.45, 0.92, 0.55], amberLo: [0.15, 0.55, 0.22], amberHi: [0.85, 1.0, 0.88],
  });
  g.drawImage(crtOut, 0, BAR_H);
}

// BEAT 7 (22.08 - 26.32s): Approved 3D padlock + live sweeping spotlight & integrity readout
function beat7(lt) {
  drawCover(imgLock, 1.0 + lt * 0.015, -20 + lt * 10, 0, 'contrast(1.05)');
  const sweepX = lerp(W * 0.28, W * 0.72, ss(seg(lt, 0.2, 4.0)));
  g.save();
  g.globalCompositeOperation = 'screen';
  const spot = g.createRadialGradient(sweepX, H / 2, 30, sweepX, H / 2, 360);
  spot.addColorStop(0, 'rgba(245, 230, 195, 0.22)');
  spot.addColorStop(1, 'rgba(0, 0, 0, 0)');
  g.fillStyle = spot;
  g.fillRect(0, BAR_H, W, H - 2 * BAR_H);
  g.restore();

  const a = ss(seg(lt, 1.0, 1.8));
  g.font = '600 22px monospace';
  g.fillStyle = `rgba(234, 228, 215, ${0.85 * a})`;
  g.fillText('CHAIN INTEGRITY: 100%  ·  PRIVATE KEYS LEAKED: 0', 84, H - BAR_H - 42);
}

// BEAT 8 (26.32 - 29.60s): Approved 3D mechanical stamp + live hydraulic impact pulse at 0.88s & 2.08s
function beat8(lt) {
  let hit = 0;
  for (const tp of [0.88, 2.08]) {
    const age = lt - tp;
    if (age >= 0 && age < 0.28) hit = Math.max(hit, 1 - age / 0.28);
  }
  drawCover(imgStamp, 1.04 + 0.03 * hit, 0, 12 * hit, `brightness(${1.0 + 0.12 * hit}) contrast(1.06)`);
}

// BEAT 9 (29.60 - 33.00s): Blueprint signing pipeline with packets flowing left-to-right
function beat9(lt) {
  g.fillStyle = '#07111c';
  g.fillRect(0, 0, W, H);

  g.strokeStyle = 'rgba(70, 150, 210, 0.14)';
  g.lineWidth = 1;
  for (let x = 0; x < W; x += 64) { g.beginPath(); g.moveTo(x, BAR_H); g.lineTo(x, H - BAR_H); g.stroke(); }

  const stages = ['REQUEST', 'POLICY', 'QUORUM', 'SIGNER', 'BROADCAST'];
  const pulseX = lerp(240, 1680, (lt * 0.45) % 1);

  g.strokeStyle = 'rgba(100, 200, 240, 0.45)';
  g.lineWidth = 3;
  g.beginPath(); g.moveTo(240, H / 2); g.lineTo(1680, H / 2); g.stroke();

  // Moving packet
  g.fillStyle = '#f5b950';
  g.beginPath(); g.arc(pulseX, H / 2, 12, 0, 7); g.fill();

  for (let i = 0; i < 5; i++) {
    const sx = 280 + i * 340;
    const lit = pulseX >= sx - 20;
    g.fillStyle = lit ? '#132436' : '#091420';
    g.strokeStyle = lit ? '#f5b950' : 'rgba(100, 190, 235, 0.45)';
    g.lineWidth = lit ? 3 : 2;
    g.fillRect(sx - 110, H / 2 - 65, 220, 130);
    g.strokeRect(sx - 110, H / 2 - 65, 220, 130);
    g.textAlign = 'center';
    g.fillStyle = lit ? '#f5b950' : '#9cc8e6';
    g.font = '700 22px monospace';
    g.fillText(stages[i], sx, H / 2 - 8);
    g.font = '400 16px monospace';
    g.fillText(lit ? 'SIGNATURE: VALID' : 'WAITING', sx, H / 2 + 28);
  }
  g.textAlign = 'left';
}

// BEAT 10 (33.00 - 37.28s): Approved 3D server corridor + live dolly + drifting dust + 5 months
function beat10(lt) {
  drawCover(imgCorr, 1.0 + lt * 0.032, 0, 0, 'contrast(1.06)');
  const months = ['OCT', 'SEP', 'AUG', 'JUL', 'JUN'];
  const idx = Math.min(4, Math.floor(lt / 0.82));
  g.font = '700 24px monospace';
  g.fillStyle = 'rgba(215, 225, 235, 0.72)';
  g.fillText(`INSIDE ACCESS // ${months[idx]} — 5 MONTHS`, 84, H - BAR_H - 42);
}

// BEAT 11 (37.28 - 41.08s): Approved woodcut plate + live forged red keycard sliding under threshold
function beat11(lt) {
  const pan = ss(seg(lt, 0.3, 2.0));
  drawCover(imgWood, 1.04 + 0.04 * pan, 0, -24 * pan, 'contrast(1.05)');
  const slide = ss(seg(lt, 1.1, 3.0));
  const cardX = lerp(W / 2 - 340, W / 2 - 40, slide);
  g.fillStyle = '#9e1c1c';
  g.fillRect(cardX, H - BAR_H - 96, 170, 20);
  g.strokeStyle = '#efe8d8';
  g.lineWidth = 2;
  g.strokeRect(cardX, H - BAR_H - 96, 170, 20);
}

window.render = (t) => {
  t = clamp(t, 0, window.DUR);

  if (t < 4.20) beat1(t);
  else if (t < 8.52) beat2(t - 4.20);
  else if (t < 12.00) beat3(t - 8.52);
  else if (t < 15.80) beat4(t - 12.00);
  else if (t < 19.04) beat5(t - 15.80);
  else if (t < 22.08) beat6(t - 19.04);
  else if (t < 26.32) beat7(t - 22.08);
  else if (t < 29.60) beat8(t - 26.32);
  else if (t < 33.00) beat9(t - 29.60);
  else if (t < 37.28) beat10(t - 33.00);
  else beat11(t - 37.28);

  // Subtle unified vignette + 35mm grain
  const vig = g.createRadialGradient(W / 2, H / 2, 360, W / 2, H / 2, 1180);
  vig.addColorStop(0, 'rgba(0,0,0,0)');
  vig.addColorStop(1, 'rgba(0,0,0,0.48)');
  g.fillStyle = vig;
  g.fillRect(0, BAR_H, W, H - 2 * BAR_H);

  const gx = -Math.floor((t * 97) % 120);
  const gy = -Math.floor((t * 53) % 90);
  for (let x = gx; x < W; x += 480) {
    for (let y = BAR_H + gy; y < H - BAR_H; y += 270) {
      g.drawImage(grainC, x, y);
    }
  }

  // 2.39:1 Letterbox bars
  g.fillStyle = '#000';
  g.fillRect(0, 0, W, BAR_H);
  g.fillRect(0, H - BAR_H, W, BAR_H);
};

window.READY = true;
