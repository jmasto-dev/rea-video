// Cinema Arc 1 (2.39:1 Anamorphic, 48.0s, 24fps) — Fincher / Chernobyl / Mr. Robot
const W = 1920, H = 1080;
const BAR_H = 138; // 2.39:1 scope letterbox inside 1920x1080 (1920x804 active frame)
window.DUR = 48.0;

const cv = document.getElementById('cv');
const g = cv.getContext('2d');

const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const ss = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const seg = (t, a, b) => clamp((t - a) / (b - a));

await document.fonts.ready;

function loadImg(src) {
  return new Promise((res, rej) => {
    const im = new Image();
    im.onload = () => res(im);
    im.onerror = rej;
    im.src = src;
  });
}

const [imgBed, imgThumb, imgDay, imgClock] = await Promise.all([
  loadImg('./assets/photos/bed_phone.jpg'),
  loadImg('./assets/photos/phone_thumb.jpg'),
  loadImg('./assets/photos/day_macbook.jpg'),
  loadImg('./assets/photos/clock_desk.jpg'),
]);

// Pre-render fine film grain tile for subtle 35mm texture
const grainC = document.createElement('canvas');
grainC.width = 480; grainC.height = 270;
const gg = grainC.getContext('2d');
const gData = gg.createImageData(480, 270);
let seed = 1337;
const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
for (let i = 0; i < gData.data.length; i += 4) {
  const v = 128 + (rnd() - 0.5) * 46;
  gData.data[i] = gData.data[i + 1] = gData.data[i + 2] = v;
  gData.data[i + 3] = 16;
}
gg.putImageData(gData, 0, 0);

function drawCover(im, scale = 1, dx = 0, dy = 0, filter = 'none') {
  const ir = im.width / im.height;
  const cr = W / H;
  let dw, dh;
  if (ir > cr) { dh = H * scale; dw = dh * ir; }
  else { dw = W * scale; dh = dw / ir; }
  g.save();
  g.filter = filter;
  g.drawImage(im, (W - dw) / 2 + dx, (H - dh) / 2 + dy, dw, dh);
  g.restore();
}

// Sequence 1a (0.0 - 3.5s): Fincher dark doorway & distant monitor flicker
function drawSeq1a(t) {
  const flick = 0.5 + 0.5 * Math.sin(t * (7 + t * 9)) * Math.cos(t * 19);
  drawCover(imgClock, 1.0 + t * 0.012, 110, 0, `brightness(${0.52 + 0.12 * flick}) contrast(1.18) saturate(0.55)`);

  // Cold blue-white monitor spill pulsing across the dark room
  const glow = g.createRadialGradient(920, 480, 20, 920, 480, 620);
  glow.addColorStop(0, `rgba(120, 175, 235, ${0.14 + 0.16 * flick})`);
  glow.addColorStop(1, 'rgba(5, 7, 10, 0)');
  g.fillStyle = glow;
  g.fillRect(0, 0, W, H);

  // Heavy dark foreground doorway frame (Fincher negative space)
  const door = g.createLinearGradient(0, 0, 620, 0);
  door.addColorStop(0, '#020304');
  door.addColorStop(0.72, '#020304');
  door.addColorStop(1, 'rgba(2, 3, 4, 0)');
  g.fillStyle = door;
  g.fillRect(0, 0, 620, H);
  g.fillStyle = '#020304';
  g.fillRect(1660, 0, 260, H);
}

// Sequence 1b (3.5 - 7.5s): Optical macro LCD pixels + vertical ledger scroll + glossy reflection
function drawSeq1b(lt) {
  g.fillStyle = '#040608';
  g.fillRect(0, 0, W, H);

  const speed = 180 + lt * 210;
  const scrollY = (lt * speed) % 64;

  // Glossy desk reflection in lower third
  g.save();
  for (let row = -2; row < 15; row++) {
    const y = row * 56 - scrollY + 120;
    const isOut = (row % 3 === 0);
    // Chromatic aberration edge tint
    g.font = '500 32px "IBM Plex Mono"';
    g.fillStyle = 'rgba(220, 70, 70, 0.25)';
    g.fillText(`0x8f4a..92c1   TRANSFER   ${isOut ? '-42,800,000' : '-18,450,000'} USD   CONFIRMED`, 157, y);
    g.fillStyle = 'rgba(70, 180, 240, 0.25)';
    g.fillText(`0x8f4a..92c1   TRANSFER   ${isOut ? '-42,800,000' : '-18,450,000'} USD   CONFIRMED`, 163, y);
    g.fillStyle = isOut ? 'rgba(225, 236, 248, 0.86)' : 'rgba(155, 185, 215, 0.55)';
    g.fillText(`0x8f4a..92c1   TRANSFER   ${isOut ? '-42,800,000' : '-18,450,000'} USD   CONFIRMED`, 160, y);
  }
  g.restore();

  // LCD subpixel mesh overlay
  g.fillStyle = 'rgba(0, 0, 0, 0.32)';
  for (let y = BAR_H; y < H - BAR_H; y += 6) {
    g.fillRect(0, y, W, 2);
  }
  for (let x = 0; x < W; x += 9) {
    g.fillRect(x, BAR_H, 2, H - 2 * BAR_H);
  }

  // Glossy bottom reflection band
  const refl = g.createLinearGradient(0, 680, 0, H - BAR_H);
  refl.addColorStop(0, 'rgba(15, 24, 34, 0.0)');
  refl.addColorStop(0.3, 'rgba(15, 24, 34, 0.72)');
  refl.addColorStop(1, 'rgba(4, 6, 8, 0.96)');
  g.fillStyle = refl;
  g.fillRect(0, 680, W, H - BAR_H - 680);
}

// Sequence 2 (7.5 - 13.5s): Symmetrical 3D Data Center aisle backward dolly + surgical lower-left type
function drawSeq2(lt) {
  g.fillStyle = '#06080b';
  g.fillRect(0, 0, W, H);

  const cx = W / 2, cy = H / 2 - 10;
  const dolly = lt * 0.55; // smooth relentless backward dolly

  // Subtle cold floor reflection
  const flr = g.createLinearGradient(0, cy, 0, H - BAR_H);
  flr.addColorStop(0, '#07090d');
  flr.addColorStop(1, '#10151d');
  g.fillStyle = flr;
  g.fillRect(0, cy, W, H - BAR_H - cy);

  // Infinite symmetrical server racks in 1-point perspective
  const N_RACKS = 22;
  for (let i = N_RACKS; i >= 1; i--) {
    const z = i - (dolly % 1);
    const s = 1 / Math.max(0.25, z * 0.42);
    const rw = 420 * s;
    const rh = 620 * s;
    const gap = 310 * s;
    const fog = clamp(1 - z / N_RACKS);

    for (const side of [-1, 1]) {
      const rx = side < 0 ? cx - gap - rw : cx + gap;
      const ry = cy - rh * 0.52;
      g.fillStyle = `rgba(14, 18, 24, ${0.3 + 0.7 * fog})`;
      g.fillRect(rx, ry, rw, rh);
      g.strokeStyle = `rgba(40, 52, 68, ${0.25 * fog})`;
      g.lineWidth = Math.max(1, 2 * s);
      g.strokeRect(rx, ry, rw, rh);

      // Calm white & green status LEDs (no red alarms)
      const rows = 10;
      for (let r = 1; r < rows; r++) {
        const ly = ry + (rh / rows) * r;
        const blink = ((i * 7 + r * 3 + Math.floor(lt * 3)) % 5 === 0) ? 0.9 : 0.35;
        g.fillStyle = (r % 3 === 0)
          ? `rgba(120, 215, 165, ${blink * fog})`
          : `rgba(215, 230, 245, ${blink * 0.75 * fog})`;
        const lx = side < 0 ? rx + rw * 0.82 : rx + rw * 0.14;
        g.fillRect(lx, ly, Math.max(2, 5 * s), Math.max(2, 3 * s));
      }
    }
  }

  // Surgical lower-left cinema credit typography
  const a1 = ss(seg(lt, 0.6, 1.4));
  const a2 = ss(seg(lt, 1.4, 2.2));
  g.save();
  g.font = '400 22px "IBM Plex Mono"';
  g.fillStyle = `rgba(235, 240, 245, ${0.78 * a1})`;
  g.fillText('20:05 — 20:25 UTC', 84, H - BAR_H - 86);
  g.font = '500 32px "IBM Plex Mono"';
  g.fillStyle = `rgba(255, 255, 255, ${0.95 * a2})`;
  g.fillText('-$6,300,000,000', 84, H - BAR_H - 42);
  g.restore();
}

// Sequence 3 (13.5 - 19.0s): Intimate bedside phone -> grazing angle thumb tap
function drawSeq3(lt) {
  if (lt < 3.0) {
    drawCover(imgBed, 1.0 + lt * 0.015, 0, 0, 'contrast(1.1) saturate(0.65) brightness(0.88)');
  } else {
    const t2 = lt - 3.0;
    const tap = (Math.abs(t2 - 0.5) < 0.08 || Math.abs(t2 - 1.2) < 0.08) ? 1.012 : 1.0;
    drawCover(imgThumb, 1.18 * tap, -40, 10, 'contrast(1.12) saturate(0.6) brightness(0.82)');
  }
}

// Sequence 4 (19.0 - 27.0s): 10-deg grazing glide over printed audit paper + optical rack focus
function drawSeq4(lt) {
  g.fillStyle = '#090a0c';
  g.fillRect(0, 0, W, H);

  // Hard white blade of light across dark paper surface
  const beam = g.createLinearGradient(300, 180, 1600, 900);
  beam.addColorStop(0, '#121316');
  beam.addColorStop(0.35, '#ded8cb');
  beam.addColorStop(0.68, '#d4cebf');
  beam.addColorStop(1, '#101114');
  g.fillStyle = beam;
  g.fillRect(0, BAR_H, W, H - 2 * BAR_H);

  // Rack focus curve: 0 -> focus line 1; 1 -> focus line 2
  const rack = ss(seg(lt, 3.2, 4.4));
  const blur1 = rack * 7.5;
  const blur2 = (1 - rack) * 7.5;
  const gx = lerp(40, -50, lt / 8.0);

  g.save();
  g.filter = `blur(${blur1.toFixed(1)}px)`;
  g.font = '500 42px "IBM Plex Mono"';
  g.fillStyle = '#181a1d';
  g.fillText('01 // NETWORK INTEGRITY: VERIFIED', 380 + gx, 430);
  g.font = '400 24px "IBM Plex Mono"';
  g.fillStyle = 'rgba(24,26,29,0.65)';
  g.fillText('CONSENSUS NODES: 100% NOMINAL  ·  BLOCK HASH VALID', 380 + gx, 474);
  g.restore();

  g.save();
  g.filter = `blur(${blur2.toFixed(1)}px)`;
  g.font = '500 42px "IBM Plex Mono"';
  g.fillStyle = '#181a1d';
  g.fillText('02 // KEY EXPOSURE: NULL', 460 + gx, 630);
  g.font = '400 24px "IBM Plex Mono"';
  g.fillStyle = 'rgba(24,26,29,0.65)';
  g.fillText('COLD & HOT SIGNING SHARDS: ZERO BREACHES RECORDED', 460 + gx, 674);
  g.restore();
}

// Sequence 5 (27.0 - 34.0s): Severance / Mr. Robot monochrome terminal (valid status vs draining millions)
function drawSeq5(lt) {
  g.fillStyle = '#060809';
  g.fillRect(0, 0, W, H);

  g.strokeStyle = 'rgba(180, 210, 195, 0.18)';
  g.lineWidth = 2;
  g.strokeRect(220, 190, 1480, 700);

  // Header
  g.font = '500 22px "IBM Plex Mono"';
  g.fillStyle = 'rgba(180, 210, 195, 0.72)';
  g.fillText('INTERNAL AUTH DAEMON // VAULT_CORE_01', 260, 245);
  g.fillRect(260, 265, 1400, 1);

  // Top: calm valid signatures
  const step = Math.floor(lt * 1.4);
  for (let i = 0; i < 4; i++) {
    const y = 325 + i * 52;
    g.font = '400 26px "IBM Plex Mono"';
    g.fillStyle = i === 3 ? 'rgba(195, 245, 215, 0.95)' : 'rgba(165, 195, 180, 0.55)';
    g.fillText(`TX#${884917 + step + i}   QUORUM: 3/3   SIGNATURE: VALID — INTERNAL`, 260, y);
  }

  // Divider
  g.fillStyle = 'rgba(180, 210, 195, 0.14)';
  g.fillRect(260, 560, 1400, 1);

  // Bottom: quiet outgoing millions
  const drains = [
    '-42,000,000.00 USD  →  0x44b1...09e2',
    '-118,400,000.00 USD →  bc1q88...11aa',
    '-310,950,000.00 USD →  TR7NHq...Lj6t',
  ];
  for (let i = 0; i < 3; i++) {
    g.font = '500 28px "IBM Plex Mono"';
    g.fillStyle = 'rgba(225, 230, 235, 0.85)';
    g.fillText(drains[(i + step) % 3], 260, 635 + i * 56);
  }
}

// Sequence 6 (34.0 - 48.0s): Nocturnal open space freeze -> brutal daylight MacBook cut -> JUNE.
function drawSeq6(lt) {
  if (lt < 5.5) {
    // Architectural nocturnal empty open-space office (4 rows of desks, 1 standby monitor)
    g.fillStyle = '#040609';
    g.fillRect(0, 0, W, H);

    // Distant night skyline bokeh behind floor-to-ceiling glass
    g.fillStyle = '#080c12';
    g.fillRect(80, 140, 1760, 460);
    for (let b = 0; b < 38; b++) {
      const bx = 120 + (b * 47) % 1680;
      const by = 260 + ((b * 83) % 240);
      g.fillStyle = `rgba(210, 225, 245, ${0.08 + (b % 4) * 0.04})`;
      g.beginPath(); g.arc(bx, by, 2 + (b % 3), 0, 7); g.fill();
    }
    // Glass mullions
    g.fillStyle = '#030406';
    for (let m = 120; m < W; m += 340) {
      g.fillRect(m, 140, 12, 480);
    }

    // 4 perspective rows of dark desks + 1 glowing standby monitor in the back
    for (let r = 0; r < 4; r++) {
      const p = r / 3;
      const y = lerp(520, 810, p);
      const dw = lerp(1100, 1840, p);
      const dx = (W - dw) / 2;
      g.fillStyle = `rgb(${8 + r * 2}, ${10 + r * 2}, ${14 + r * 2})`;
      g.fillRect(dx, y, dw, 14 + r * 4);
      for (let c = 0; c < 4; c++) {
        const mx = dx + dw * (0.14 + c * 0.24);
        const mw = lerp(58, 98, p);
        const mh = lerp(34, 58, p);
        const isLit = (r === 0 && c === 2);
        if (isLit) {
          const mg = g.createRadialGradient(mx + mw / 2, y - mh / 2, 6, mx + mw / 2, y - mh / 2, 160);
          mg.addColorStop(0, 'rgba(130, 190, 245, 0.35)');
          mg.addColorStop(1, 'rgba(130, 190, 245, 0)');
          g.fillStyle = mg;
          g.fillRect(mx - 140, y - 180, 340, 300);
          g.fillStyle = 'rgba(180, 220, 255, 0.88)';
        } else {
          g.fillStyle = '#07090d';
        }
        g.fillRect(mx, y - mh - 4, mw, mh);
      }
    }
  } else if (lt < 10.1) {
    // Brutal daylight cut: ordinary morning MacBook + coffee mug
    const t2 = lt - 5.5;
    drawCover(imgDay, 1.0 + t2 * 0.025, 0, 0, 'contrast(1.03) saturate(0.95) brightness(1.04)');
  } else {
    // Hard cut to matte black + JUNE.
    g.fillStyle = '#070809';
    g.fillRect(0, 0, W, H);
    const a = ss(seg(lt, 10.5, 11.1));
    g.font = '400 76px "Cormorant Garamond", serif';
    g.fillStyle = `rgba(235, 232, 224, ${a})`;
    g.textAlign = 'center';
    g.fillText('J U N E .', W / 2, H / 2 + 24);
    g.textAlign = 'left';
  }
}

window.render = (t) => {
  t = clamp(t, 0, window.DUR);

  if (t < 3.5) drawSeq1a(t);
  else if (t < 7.5) drawSeq1b(t - 3.5);
  else if (t < 13.5) drawSeq2(t - 7.5);
  else if (t < 19.0) drawSeq3(t - 13.5);
  else if (t < 27.0) drawSeq4(t - 19.0);
  else if (t < 34.0) drawSeq5(t - 27.0);
  else drawSeq6(t - 34.0);

  // Subtle optical vignette inside the 2.39:1 frame
  const vig = g.createRadialGradient(W / 2, H / 2, 340, W / 2, H / 2, 1180);
  vig.addColorStop(0, 'rgba(0,0,0,0)');
  vig.addColorStop(1, 'rgba(0,0,0,0.52)');
  g.fillStyle = vig;
  g.fillRect(0, BAR_H, W, H - 2 * BAR_H);

  // Fine 35mm film grain
  const gx = -Math.floor((t * 97) % 120);
  const gy = -Math.floor((t * 53) % 90);
  for (let x = gx; x < W; x += 480) {
    for (let y = BAR_H + gy; y < H - BAR_H; y += 270) {
      g.drawImage(grainC, x, y);
    }
  }

  // 2.39:1 Anamorphic Cinema Letterbox Bars
  g.fillStyle = '#000';
  g.fillRect(0, 0, W, BAR_H);
  g.fillRect(0, H - BAR_H, W, BAR_H);
};

window.READY = true;
