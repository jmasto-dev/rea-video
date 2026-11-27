// Shared Halftone-Dossier Level-10 Studio Engine (100% Visual DNA Locked to Act 1)
// Exposes global `window.Engine` for Act 1 .. Act 6.
(() => {
  const NS = 'http://www.w3.org/2000/svg';

  const C = {
    paper:  '#F4ECDD',
    cream:  '#FFF4E2',
    navy:   '#1D2340',
    night:  '#18203F',
    night2: '#2A3568',
    night3: '#121833',
    blue:   '#2E55D6',
    sky:    '#6BA4FF',
    pink:   '#FF5A87',
    yellow: '#FFC628',
    orange: '#F58A34',
    red:    '#E8384F',
    skin:   '#F7C9A1',
    skin2:  '#E2AE84',
    mint:   '#56C29E',
    teal:   '#2F8F78',
    wood:   '#C98A4B',
    woodDk: '#9C6231',
    slate:  '#425180',
  };

  const F = {
    serif: "'Noto Serif SC', Georgia, serif",
    bagel: "'Bagel Fat One', Impact, sans-serif",
    mono:  "'JetBrains Mono', monospace",
  };

  const FPS = 24;

  // ---------- Basic SVG & Math Helpers ----------
  function el(tag, attrs = {}, parent = null) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function txt(parent, str, attrs = {}) {
    const e = el('text', attrs, parent);
    e.textContent = str;
    return e;
  }
  function tf(e, x = 0, y = 0, s = 1, r = 0, sy) {
    e.setAttribute(
      'transform',
      `translate(${x.toFixed(2)} ${y.toFixed(2)}) rotate(${r.toFixed(2)}) scale(${s.toFixed(4)} ${(sy ?? s).toFixed(4)})`
    );
  }
  function op(e, o) { e.setAttribute('opacity', Math.max(0, Math.min(1, o)).toFixed(3)); }
  function show(e, v) { e.style.display = v ? '' : 'none'; }

  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const seg = (t, a, b) => clamp((t - a) / Math.max(0.0001, b - a));
  const lerp = (a, b, p) => a + (b - a) * p;
  const smooth = p => p * p * (3 - 2 * p);
  const E = {
    out:  p => 1 - Math.pow(1 - clamp(p), 3),
    in:   p => Math.pow(clamp(p), 3),
    io:   p => { const c = clamp(p); return c < 0.5 ? 4 * c * c * c : 1 - Math.pow(-2 * c + 2, 3) / 2; },
    back: p => { const c = clamp(p), s = 1.85; return 1 + (s + 1) * Math.pow(c - 1, 3) + s * Math.pow(c - 1, 2); },
  };
  function rng(seed) {
    return () => {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  // Hand-drawn slight ink wobble helpers (zero runtime filter overhead)
  function wRect(parent, x, y, w, h, attrs = {}, seed = 1, wob = 1.6) {
    const r = rng(seed);
    const j = () => (r() - 0.5) * wob;
    const mx = x + w / 2, my = y + h / 2;
    const d = `M${(x + j()).toFixed(1)},${(y + j()).toFixed(1)} `
      + `Q${(mx + j()).toFixed(1)},${(y + j()).toFixed(1)} ${(x + w + j()).toFixed(1)},${(y + j()).toFixed(1)} `
      + `Q${(x + w + j()).toFixed(1)},${(my + j()).toFixed(1)} ${(x + w + j()).toFixed(1)},${(y + h + j()).toFixed(1)} `
      + `Q${(mx + j()).toFixed(1)},${(y + h + j()).toFixed(1)} ${(x + j()).toFixed(1)},${(y + h + j()).toFixed(1)} `
      + `Q${(x + j()).toFixed(1)},${(my + j()).toFixed(1)} ${(x + j()).toFixed(1)},${(y + j()).toFixed(1)} Z`;
    return el('path', { d, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', ...attrs }, parent);
  }
  function wLine(parent, x1, y1, x2, y2, attrs = {}, seed = 1, wob = 2.0) {
    const r = rng(seed);
    const mx = (x1 + x2) / 2 + (r() - 0.5) * wob;
    const my = (y1 + y2) / 2 + (r() - 0.5) * wob;
    const d = `M${x1.toFixed(1)},${y1.toFixed(1)} Q${mx.toFixed(1)},${my.toFixed(1)} ${x2.toFixed(1)},${y2.toFixed(1)}`;
    return el('path', { d, fill: 'none', 'stroke-linecap': 'round', ...attrs }, parent);
  }

  // ---------- Typography ----------
  const mctx = document.createElement('canvas').getContext('2d');
  function measure(str, size, family, weight = 900) {
    mctx.font = `${weight} ${size}px ${family}`;
    return mctx.measureText(str).width;
  }

  function chars(parent, str, o) {
    const { x, y, size, family = F.serif, weight = 900, fill = C.navy, anchor = 'start', ls = 0, shadow, stroke, sw = 0 } = o;
    const g = el('g', {}, parent);
    const arr = [...str];
    const widths = arr.map(c => measure(c, size, family, weight));
    const total = widths.reduce((a, b) => a + b, 0) + ls * Math.max(0, arr.length - 1);
    let cx = anchor === 'middle' ? x - total / 2 : anchor === 'end' ? x - total : x;
    const items = arr.map((ch, i) => {
      const cg = el('g', {}, g);
      const base = { x: 0, y: 0, 'font-size': size, 'font-family': family, 'font-weight': weight, 'text-anchor': 'middle' };
      if (shadow) txt(cg, ch, { ...base, x: shadow.dx, y: shadow.dy, fill: shadow.fill, class: 'mul' });
      const st = stroke ? { stroke, 'stroke-width': sw, 'paint-order': 'stroke', 'stroke-linejoin': 'round' } : {};
      txt(cg, ch, { ...base, fill, ...st });
      const it = { g: cg, x: cx + widths[i] / 2, y, w: widths[i], size };
      cx += widths[i] + ls;
      tf(cg, it.x, it.y);
      return it;
    });
    return { g, items, total };
  }

  function charsPop(c, t, t0, stagger = 0.028, d = 0.30, from = 46) {
    c.items.forEach((it, i) => {
      const s = t0 + i * stagger;
      const p = seg(t, s, s + d);
      const h = it.size * 0.35;
      if (t < s) { op(it.g, 0); return; }
      op(it.g, 1);
      const sc = E.back(p);
      const sq = 1 + 0.18 * Math.sin(p * Math.PI) * (1 - p);
      it.g.setAttribute(
        'transform',
        `translate(${it.x} ${it.y + from * (1 - E.out(p))}) translate(0 ${-h}) scale(${(sc / sq).toFixed(3)} ${(sc * sq).toFixed(3)}) translate(0 ${h})`
      );
    });
  }

  // ---------- Fast Pre-Baked Halftone Dot Fields (Canvas -> <image> for crisp zero-stall Ben-Day tones) ----------
  function halftone(parent, { x0 = 0, y0 = 0, w = 1920, h = 1080, step = 24, angle = 15, color, f, maxK = 0.60, opacity = 1 }) {
    const scale = 0.5; // 960x540 buffer scaled cleanly to w x h keeps edges crisp & fast
    const cw = Math.max(4, Math.round(w * scale)), ch = Math.max(4, Math.round(h * scale));
    const cv = document.createElement('canvas');
    cv.width = cw; cv.height = ch;
    const ctx = cv.getContext('2d');
    ctx.fillStyle = color;
    const a = angle * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a);
    const n = Math.ceil(Math.hypot(w, h) / step / 2) + 2;
    ctx.beginPath();
    for (let i = -n; i <= n; i++) {
      for (let j = -n; j <= n; j++) {
        const u = i * step, v = j * step;
        const x = w / 2 + u * ca - v * sa;
        const y = h / 2 + u * sa + v * ca;
        if (x < -step || x > w + step || y < -step || y > h + step) continue;
        const r = clamp(f(x0 + x, y0 + y), 0, 1) * step * maxK;
        if (r < 0.8) continue;
        const sx = x * scale, sy = y * scale, sr = r * scale;
        ctx.moveTo(sx + sr, sy);
        ctx.arc(sx, sy, sr, 0, Math.PI * 2);
      }
    }
    ctx.fill();
    const url = cv.toDataURL('image/png');
    return el('image', { x: x0, y: y0, width: w, height: h, href: url, opacity }, parent);
  }

  // SVG Ben-Day Pattern definitions for sharp geometric cones & shapes
  function injectDefs(svg) {
    const defs = svg.querySelector('defs') || el('defs', {}, svg);
    // Fast single-octave 10fps line boil for characters & key animated props ONLY
    // (Paper stipple tooth is pre-baked onto #paper ONCE at init for 3x render speedup!)
    defs.innerHTML = `
      <filter id="boil" x="-10%" y="-10%" width="120%" height="120%">
        <feTurbulence id="boilT" type="fractalNoise" baseFrequency="0.022" numOctaves="1" seed="1" result="w"/>
        <feDisplacementMap in="SourceGraphic" in2="w" scale="3.4" xChannelSelector="R" yChannelSelector="G"/>
      </filter>
      <filter id="stampInk" x="-12%" y="-12%" width="124%" height="124%">
        <feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="2" seed="11" result="w"/>
        <feDisplacementMap in="SourceGraphic" in2="w" scale="6.5" xChannelSelector="R" yChannelSelector="G" result="d"/>
        <feTurbulence type="fractalNoise" baseFrequency="0.58" numOctaves="2" seed="21" result="g"/>
        <feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -9 6.0" result="gm"/>
        <feComposite in="d" in2="gm" operator="in"/>
      </filter>
      <pattern id="patDotsGold" width="22" height="22" patternUnits="userSpaceOnUse" patternTransform="rotate(18)">
        <circle cx="11" cy="11" r="4.6" fill="${C.yellow}" opacity="0.55"/>
      </pattern>
      <pattern id="patDotsBlue" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="rotate(25)">
        <circle cx="10" cy="10" r="4.0" fill="${C.blue}" opacity="0.38"/>
      </pattern>
      <pattern id="patDotsNavy" width="18" height="18" patternUnits="userSpaceOnUse" patternTransform="rotate(15)">
        <circle cx="9" cy="9" r="3.2" fill="${C.navy}" opacity="0.22"/>
      </pattern>
      <pattern id="patDotsRed" width="22" height="22" patternUnits="userSpaceOnUse" patternTransform="rotate(32)">
        <circle cx="11" cy="11" r="4.2" fill="${C.red}" opacity="0.45"/>
      </pattern>
      <pattern id="patDotsMint" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="rotate(12)">
        <circle cx="10" cy="10" r="4.0" fill="${C.mint}" opacity="0.40"/>
      </pattern>
      <pattern id="patStripeDanger" width="44" height="24" patternUnits="userSpaceOnUse" patternTransform="rotate(-35)">
        <rect width="22" height="24" fill="${C.yellow}"/>
        <rect x="22" width="22" height="24" fill="${C.navy}"/>
      </pattern>
      <clipPath id="frameClip"><rect width="1920" height="1080"/></clipPath>
    `;
  }

  // ---------- Stamps & Cash ----------
  function makeStamp(parent, label, color = C.red, w = 440, h = 132, fontSize = 54) {
    const g = el('g', { filter: 'url(#stampInk)' }, parent);
    el('rect', { x: -w / 2, y: -h / 2, width: w, height: h, rx: 14, fill: 'none', stroke: color, 'stroke-width': 11 }, g);
    el('rect', { x: -w / 2 + 12, y: -h / 2 + 12, width: w - 24, height: h - 24, rx: 8, fill: 'none', stroke: color, 'stroke-width': 4 }, g);
    txt(g, label, { x: 0, y: Math.round(fontSize * 0.36), 'text-anchor': 'middle', 'font-family': F.bagel, 'font-size': fontSize, fill: color });
    op(g, 0);
    return g;
  }

  function stampAnim(st, t, t0, x, y, rot = -10) {
    if (t < t0) { op(st, 0); return; }
    const p = seg(t, t0, t0 + 0.11);
    const bounce = p < 1 ? lerp(2.5, 1.0, p * p) : 1.0 + Math.sin((t - t0 - 0.11) * 28) * 0.04 * Math.max(0, 1 - (t - t0 - 0.11) / 0.25);
    op(st, 0.94);
    tf(st, x, y, bounce, rot);
  }

  function billNote(parent, { boil = false, label = '$' } = {}) {
    const g = el('g', boil ? { filter: 'url(#boil)' } : {}, parent);
    el('rect', { x: -34, y: -18, width: 68, height: 36, rx: 4, fill: C.mint, stroke: C.navy, 'stroke-width': 4 }, g);
    el('circle', { cx: 0, cy: 0, r: 12, fill: C.cream, opacity: 0.45 }, g);
    txt(g, label, { x: 0, y: 8, 'text-anchor': 'middle', 'font-family': F.mono, 'font-size': 21, 'font-weight': 800, fill: C.navy });
    return g;
  }

  // ---------- Paper Print Texture (Mottling + Risograph Tooth Stipple + Fold + Vignette) ----------
  function buildPaper(cv) {
    const ctx = cv.getContext('2d');
    const r = rng(7);
    // Low-frequency warm paper mottling
    const small = document.createElement('canvas'); small.width = 96; small.height = 54;
    const sctx = small.getContext('2d');
    const sim = sctx.createImageData(96, 54);
    for (let i = 0; i < sim.data.length; i += 4) {
      const v = 240 + r() * 15;
      sim.data[i] = v; sim.data[i + 1] = v - 2; sim.data[i + 2] = v - 6; sim.data[i + 3] = 255;
    }
    sctx.putImageData(sim, 0, 0);
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(small, 0, 0, 1920, 1080);

    // Subtle tileable risograph stipple tooth pattern baked ONCE (gives Act 1's iconic tactile ink grain across every flat fill!)
    const tile = document.createElement('canvas'); tile.width = 240; tile.height = 240;
    const tctx = tile.getContext('2d');
    const tim = tctx.createImageData(240, 240);
    for (let i = 0; i < tim.data.length; i += 4) {
      const k = r();
      if (k < 0.085) { // subtle paper ink tooth speck
        tim.data[i] = 212; tim.data[i + 1] = 204; tim.data[i + 2] = 190; tim.data[i + 3] = 115;
      } else {
        tim.data[i + 3] = 0;
      }
    }
    tctx.putImageData(tim, 0, 0);
    ctx.fillStyle = ctx.createPattern(tile, 'repeat');
    ctx.fillRect(0, 0, 1920, 1080);

    // Subtle central archive crease
    ctx.fillStyle = 'rgba(29,35,64,0.035)';
    ctx.fillRect(958, 0, 3, 1080);
    ctx.fillStyle = 'rgba(255,255,255,0.08)';
    ctx.fillRect(961, 0, 2, 1080);

    // Warm edge vignette
    const gr = ctx.createRadialGradient(960, 540, 440, 960, 540, 1200);
    gr.addColorStop(0, 'rgba(255,255,255,0)');
    gr.addColorStop(1, 'rgba(115,95,72,0.30)');
    ctx.fillStyle = gr;
    ctx.fillRect(0, 0, 1920, 1080);
  }

  function drawFx(cv, frame) {
    const ctx = cv.getContext('2d');
    const w = cv.width, h = cv.height;
    ctx.clearRect(0, 0, w, h);
    const r = rng(1000 + Math.floor(frame / 2));
    ctx.fillStyle = 'rgba(255,248,235,0.55)';
    for (let i = 0; i < 160; i++) {
      ctx.fillRect(r() * w, r() * h, 1.5, 1.5);
    }
    ctx.fillStyle = 'rgba(29,35,64,0.22)';
    for (let i = 0; i < 45; i++) {
      ctx.fillRect(r() * w, r() * h, 1.5, 1.5);
    }
  }

  // ---------- Articulated Level-10 Character Rig (Exact Act 1 DNA) ----------
  function personRig(parent, {
    shirt = C.blue, hair = C.navy, hairStyle = 'crop',
    glasses = false, tie = null, badge = false, headset = false,
    mode = 'desk', expression = 'neutral'
  } = {}) {
    const g = el('g', { filter: 'url(#boil)' }, parent);
    const S = { stroke: C.navy, 'stroke-width': 7, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' };

    if (mode === 'bed') {
      el('rect', { x: -245, y: 15, width: 490, height: 325, rx: 18, fill: C.night2, ...S }, g);
      el('rect', { x: -175, y: 50, width: 350, height: 120, rx: 28, fill: C.cream, ...S }, g);
    }

    // Back/left arm slot
    const lArmG = el('g', {}, g);
    // Torso
    const bodyG = el('g', {}, g);
    el('path', { d: 'M -115 260 C -115 120 -75 88 0 88 C 75 88 115 120 115 260 Z', fill: shirt, ...S }, bodyG);
    el('path', { d: 'M -36 90 L 0 128 L 36 90', fill: 'none', ...S }, bodyG);
    if (tie) el('polygon', { points: '-12,126 12,126 18,220 0,242 -18,220', fill: tie, ...S }, bodyG);
    if (badge) {
      el('rect', { x: 34, y: 148, width: 64, height: 34, rx: 6, fill: C.yellow, ...S }, bodyG);
      el('line', { x1: 46, y1: 165, x2: 86, y2: 165, stroke: C.navy, 'stroke-width': 4 }, bodyG);
    }

    if (mode === 'bed') {
      el('rect', { x: -255, y: 215, width: 510, height: 155, rx: 16, fill: C.blue, ...S }, g);
    }

    // Articulated arms helper
    function drawArm(targetG, sx, sy, ex, ey, hx, hy) {
      targetG.innerHTML = '';
      el('path', { d: `M ${sx} ${sy} Q ${ex} ${ey} ${hx} ${hy}`, fill: 'none', stroke: C.navy, 'stroke-width': 38, 'stroke-linecap': 'round' }, targetG);
      el('path', { d: `M ${sx} ${sy} Q ${ex} ${ey} ${hx} ${hy}`, fill: 'none', stroke: shirt, 'stroke-width': 24, 'stroke-linecap': 'round' }, targetG);
      el('circle', { cx: hx, cy: hy, r: 21, fill: C.skin, ...S }, targetG);
    }
    const rArmG = el('g', {}, g);
    // Default natural poses
    if (mode === 'bed') {
      drawArm(lArmG, -102, 145, -148, 205, -62, 232);
      drawArm(rArmG, 102, 145, 148, 205, 62, 232);
    } else if (mode === 'analyst') {
      drawArm(lArmG, -104, 142, -172, 42, -92, -72);
      drawArm(rArmG, 104, 142, 175, 170, 238, 102);
    } else {
      drawArm(lArmG, -102, 145, -155, 195, -95, 240);
      drawArm(rArmG, 102, 145, 155, 195, 95, 240);
    }

    // Head group (can nod/tilt independently)
    const headG = el('g', {}, g);
    el('rect', { x: -24, y: 60, width: 48, height: 42, fill: C.skin, ...S }, headG);
    el('circle', { cx: -86, cy: 2, r: 20, fill: C.skin, ...S }, headG);
    el('circle', { cx: 86, cy: 2, r: 20, fill: C.skin, ...S }, headG);
    el('rect', { x: -84, y: -96, width: 168, height: 176, rx: 76, fill: C.skin, ...S }, headG);

    // Hairstyles (varied so Engineers #1, #2, #3, Security, HR, CEO look unmistakable!)
    if (hairStyle === 'wavy') {
      el('path', { d: 'M -88 -15 C -96 -112 -22 -130 42 -118 C 94 -108 96 -36 86 -14 C 58 -50 18 -64 -18 -46 C -48 -62 -72 -44 -88 -15 Z', fill: hair, ...S }, headG);
    } else if (hairStyle === 'bob') {
      el('path', { d: 'M -92 48 C -98 -115 -18 -124 20 -122 C 95 -118 98 15 92 48 C 82 28 76 -45 64 -54 C 15 -42 -42 -42 -66 -54 C -78 -40 -82 25 -92 48 Z', fill: hair, ...S }, headG);
    } else if (hairStyle === 'slick') {
      el('path', { d: 'M -84 -32 C -84 -108 8 -122 65 -102 C 94 -92 92 -42 84 -30 C 48 -58 -36 -56 -84 -32 Z', fill: hair, ...S }, headG);
    } else {
      el('path', { d: 'M -86 -22 C -92 -106 -20 -122 30 -116 C 85 -110 92 -45 86 -22 C 55 -56 -40 -56 -86 -22 Z', fill: hair, ...S }, headG);
    }

    if (headset) {
      el('path', { d: 'M -92 -8 C -92 -112 92 -112 92 -8', fill: 'none', stroke: C.navy, 'stroke-width': 11, 'stroke-linecap': 'round' }, headG);
      el('rect', { x: -102, y: -22, width: 22, height: 50, rx: 8, fill: C.orange, ...S }, headG);
      el('path', { d: 'M -92 22 Q -78 58 -24 54', fill: 'none', stroke: C.navy, 'stroke-width': 6, 'stroke-linecap': 'round' }, headG);
    }

    // Eyes (with blink lids)
    const pupils = [];
    const lids = [];
    for (const ex of [-34, 34]) {
      el('ellipse', { cx: ex, cy: -8, rx: 22, ry: 26, fill: C.cream, ...S }, headG);
      const p = el('circle', { cx: ex + 4, cy: -8, r: 9, fill: C.navy }, headG);
      const hi = el('circle', { cx: ex + 7, cy: -13, r: 3.5, fill: C.cream }, headG);
      const lid = el('rect', { x: ex - 24, y: -36, width: 48, height: 0, rx: 6, fill: C.skin, stroke: C.navy, 'stroke-width': 4 }, headG);
      op(lid, 0);
      pupils.push({ p, hi, baseX: ex + 4 });
      lids.push(lid);
    }
    if (glasses) {
      for (const ex of [-34, 34]) el('rect', { x: ex - 28, y: -32, width: 56, height: 46, rx: 8, fill: 'none', stroke: C.navy, 'stroke-width': 6 }, headG);
      el('line', { x1: -6, y1: -10, x2: 6, y2: -10, stroke: C.navy, 'stroke-width': 6 }, headG);
    }

    // Brows + Mouth + Optional Sweat
    const browD = expression === 'confused'
      ? 'M -58 -40 Q -34 -64 -12 -46 M 12 -40 Q 34 -34 58 -44'
      : expression === 'worried' || expression === 'shocked'
      ? 'M -58 -48 Q -34 -62 -12 -42 M 12 -42 Q 34 -62 58 -48'
      : 'M -58 -44 Q -34 -56 -12 -44 M 12 -44 Q 34 -56 58 -44';
    el('path', { d: browD, fill: 'none', ...S }, headG);

    if (expression === 'confused' || expression === 'worried') {
      el('path', { d: 'M -22 48 Q 0 34 22 48', fill: 'none', ...S }, headG);
    } else if (expression === 'smile' || expression === 'proud') {
      el('path', { d: 'M -24 38 Q 0 60 24 38', fill: 'none', ...S }, headG);
    } else if (expression === 'shocked') {
      el('ellipse', { cx: 0, cy: 46, rx: 18, ry: 13, fill: C.navy }, headG);
    } else {
      el('line', { x1: -18, y1: 44, x2: 18, y2: 44, ...S }, headG);
    }

    const sweat = el('path', { d: 'M 96 -52 C 110 -26 112 -8 96 -8 C 80 -8 82 -26 96 -52 Z', fill: '#7AD7F0', ...S }, headG);
    op(sweat, expression === 'shocked' || expression === 'worried' ? 1 : 0);

    function setState({ lookX = 0, lookY = 0, blink = false, headRot = 0, headDy = 0, sweatOn = null, lArm = null, rArm = null } = {}) {
      tf(headG, 0, headDy, 1, headRot);
      pupils.forEach(({ p, hi, baseX }) => {
        p.setAttribute('cx', (baseX + lookX).toFixed(1));
        p.setAttribute('cy', (-8 + lookY).toFixed(1));
        hi.setAttribute('cx', (baseX + 3 + lookX).toFixed(1));
        hi.setAttribute('cy', (-13 + lookY).toFixed(1));
      });
      lids.forEach(lid => {
        op(lid, blink ? 1 : 0);
        lid.setAttribute('height', blink ? 54 : 0);
      });
      if (sweatOn !== null) op(sweat, sweatOn ? 1 : 0);
      if (lArm) drawArm(lArmG, ...lArm);
      if (rArm) drawArm(rArmG, ...rArm);
    }

    return { g, headG, bodyG, lArmG, rArmG, sweat, setState };
  }

  // ---------- Stylized Exhibit / Capture Mounting Kit ----------
  function mountCapture(parent, src, { x, y, w, h, tag = 'EXHIBIT', dark = false, tape = true } = {}) {
    const g = el('g', {}, parent);
    const S = { stroke: C.navy, 'stroke-width': 6, 'stroke-linejoin': 'round' };
    // Offset misregistered paper shadow
    el('rect', { x: x + 12, y: y + 12, width: w, height: h, rx: 10, fill: dark ? '#0B0F22' : C.navy, class: 'mul', opacity: dark ? 0.55 : 0.25 }, g);
    // White/cream archival frame
    el('rect', { x, y, width: w, height: h, rx: 10, fill: C.cream, ...S }, g);
    // Capture image
    const img = el('image', { x: x + 8, y: y + 8, width: w - 16, height: h - 16, href: src, preserveAspectRatio: 'xMidYMid meet' }, g);
    // Exhibit ID chip at top-left
    el('rect', { x: x + 16, y: y - 18, width: Math.max(135, tag.length * 14 + 34), height: 34, rx: 6, fill: C.yellow, stroke: C.navy, 'stroke-width': 4 }, g);
    txt(g, tag, { x: x + 28, y: y + 5, 'font-family': F.mono, 'font-size': 18, 'font-weight': 800, fill: C.navy });
    if (tape) {
      el('rect', { x: x + w - 95, y: y - 14, width: 78, height: 26, rx: 3, fill: C.paper, stroke: C.navy, 'stroke-width': 3, opacity: 0.9, transform: `rotate(8 ${x + w - 56} ${y})` }, g);
    }
    return { g, img };
  }

  function cursorRig(parent) {
    const g = el('g', {}, parent);
    el('polygon', { points: '0,0 0,44 13,34 22,52 31,47 22,29 36,29', fill: C.cream, stroke: C.navy, 'stroke-width': 4, 'stroke-linejoin': 'round' }, g);
    return g;
  }

  function clickRipple(parent, x, y, color = C.red) {
    const c = el('circle', { cx: x, cy: y, r: 8, fill: 'none', stroke: color, 'stroke-width': 6 }, parent);
    op(c, 0);
    return (t, t0) => {
      if (t < t0 || t > t0 + 0.45) { op(c, 0); return; }
      const p = (t - t0) / 0.45;
      c.setAttribute('r', (12 + p * 60).toFixed(1));
      op(c, 1 - p);
    };
  }

  // ---------- LEVEL-10 ARCHITECTURAL DECOR BUILDERS (100% Exact Act 1 Halftone-Dossier Aesthetic!) ----------

  // 1. Binance Vault Atrium Hall (for 1B, 5A, etc.)
  function decorVaultHall(parent, { groundY = 840 } = {}) {
    const g = el('g', {}, parent);
    const S = { stroke: C.navy, 'stroke-width': 5, 'stroke-linejoin': 'round' };
    el('rect', { width: 1920, height: 1080, fill: C.night }, g);
    halftone(g, { color: C.night2, step: 26, angle: 16, f: (x, y) => 0.56 - Math.hypot(x - 960, y - 500) / 1450 });

    // Perspective ribbed steel wall panels
    for (let x = 180; x <= 1740; x += 260) {
      wLine(g, x, 0, x, groundY, { stroke: C.night2, 'stroke-width': 4 }, x);
      for (const ry of [120, 320, 520, 720]) {
        el('circle', { cx: x + 16, cy: ry, r: 4, fill: C.slate }, g);
      }
    }
    // Steel ceiling truss girder
    el('rect', { x: 0, y: 0, width: 1920, height: 74, fill: C.night3, stroke: C.navy, 'stroke-width': 5 }, g);
    for (let x = 60; x < 1920; x += 180) {
      el('line', { x1: x, y1: 0, x2: x + 90, y2: 74, stroke: C.night2, 'stroke-width': 5 }, g);
      el('line', { x1: x + 90, y1: 74, x2: x + 180, y2: 0, stroke: C.night2, 'stroke-width': 5 }, g);
    }

    // Two industrial overhead cage pendant lamps placed cleanly clear of top-left headline zone
    for (const lx of [795, 1495]) {
      el('polygon', { points: `${lx - 26},74 ${lx + 26},74 ${lx + 240},${groundY} ${lx - 240},${groundY}`, fill: 'url(#patDotsGold)', opacity: 0.28 }, g);
      el('line', { x1: lx, y1: 0, x2: lx, y2: 112, stroke: C.cream, 'stroke-width': 4 }, g);
      el('path', { d: `M ${lx - 50} 134 C ${lx - 42} 98 ${lx + 42} 98 ${lx + 50} 134 Z`, fill: C.yellow, ...S }, g);
      el('rect', { x: lx - 20, y: 134, width: 40, height: 14, rx: 6, fill: C.cream, ...S }, g);
    }

    // Wall-mounted CCTV camera + red LED on right pilaster
    const camG = el('g', {}, g);
    el('rect', { x: 1620, y: 88, width: 20, height: 44, fill: C.slate, ...S }, camG);
    el('polygon', { points: '1630,110 1538,136 1548,172 1640,146', fill: C.cream, ...S }, camG);
    const camLed = el('circle', { cx: 1560, cy: 144, r: 6, fill: C.red }, camG);

    // Perspective tiled marble/obsidian floor + safety yellow plinth trim
    el('rect', { x: 0, y: groundY, width: 1920, height: 1080 - groundY, fill: C.night3 }, g);
    el('rect', { x: 0, y: groundY - 12, width: 1920, height: 16, fill: 'url(#patStripeDanger)', stroke: C.navy, 'stroke-width': 4 }, g);
    for (let i = -5; i <= 5; i++) {
      el('line', { x1: 960 + i * 165, y1: groundY + 4, x2: 960 + i * 310, y2: 1080, stroke: C.night2, 'stroke-width': 3 }, g);
    }
    el('line', { x1: 0, y1: groundY + 95, x2: 1920, y2: groundY + 95, stroke: C.night2, 'stroke-width': 3 }, g);
    el('line', { x1: 0, y1: groundY + 175, x2: 1920, y2: groundY + 175, stroke: C.night2, 'stroke-width': 3 }, g);

    return { g, camG, camLed };
  }

  // 2. Full Night Bedroom Interior (for 1D)
  function decorBedroomNight(parent, { clockText = '8:25 PM' } = {}) {
    const g = el('g', {}, parent);
    const S = { stroke: C.navy, 'stroke-width': 6, 'stroke-linejoin': 'round' };
    el('rect', { width: 1920, height: 1080, fill: C.night }, g);
    // Subtle vertical wallpaper panels
    for (let x = 0; x < 1920; x += 120) {
      el('rect', { x, y: 0, width: 60, height: 830, fill: C.night2, opacity: 0.25 }, g);
    }
    halftone(g, { color: C.blue, step: 26, angle: 16, f: (x, y) => clamp(0.38 - Math.hypot(x - 1350, y - 500) / 1100) });

    // Bedroom Window with city skyline, crescent moon & halftone moonlight beam
    el('polygon', { points: '880,150 1180,150 1050,830 700,830', fill: 'url(#patDotsBlue)', opacity: 0.45 }, g);
    wRect(g, 880, 145, 310, 340, { fill: C.night3, ...S }, 11);
    // Lit skyline buildings outside window
    for (const [bx, bh] of [[896, 130], [952, 190], [1015, 110], [1072, 165], [1128, 120]]) {
      el('rect', { x: bx, y: 478 - bh, width: 48, height: bh, fill: C.night2, stroke: C.navy, 'stroke-width': 3 }, g);
      el('rect', { x: bx + 12, y: 478 - bh + 22, width: 10, height: 12, fill: C.yellow, opacity: 0.85 }, g);
      el('rect', { x: bx + 28, y: 478 - bh + 52, width: 10, height: 12, fill: C.yellow, opacity: 0.65 }, g);
    }
    // Crescent moon
    el('circle', { cx: 955, cy: 215, r: 30, fill: C.yellow }, g);
    el('circle', { cx: 969, cy: 207, r: 26, fill: C.night3 }, g);
    // Window cross-frame & parted curtains
    el('line', { x1: 1035, y1: 145, x2: 1035, y2: 485, stroke: C.navy, 'stroke-width': 8 }, g);
    el('line', { x1: 880, y1: 315, x2: 1190, y2: 315, stroke: C.navy, 'stroke-width': 8 }, g);
    wRect(g, 855, 132, 360, 22, { rx: 6, fill: C.wood, ...S }, 12);

    // Framed Wall Poster on left above bed
    wRect(g, 190, 210, 190, 220, { rx: 8, fill: C.cream, ...S }, 13);
    el('rect', { x: 215, y: 235, width: 140, height: 130, fill: C.pink, stroke: C.navy, 'stroke-width': 4 }, g);
    txt(g, 'HODL', { x: 285, y: 312, 'text-anchor': 'middle', 'font-family': F.bagel, 'font-size': 42, fill: C.cream });

    // Wooden floor + baseboard + bedside rug
    el('rect', { x: 0, y: 815, width: 1920, height: 30, fill: C.woodDk, stroke: C.navy, 'stroke-width': 5 }, g);
    el('rect', { x: 0, y: 845, width: 1920, height: 235, fill: C.wood, stroke: C.navy, 'stroke-width': 5 }, g);
    for (const fy of [900, 960, 1025]) el('line', { x1: 0, y1: fy, x2: 1920, y2: fy, stroke: C.woodDk, 'stroke-width': 3 }, g);
    el('ellipse', { cx: 520, cy: 960, rx: 410, ry: 72, fill: C.pink, stroke: C.navy, 'stroke-width': 6 }, g);
    el('ellipse', { cx: 520, cy: 960, rx: 320, ry: 46, fill: 'none', stroke: C.yellow, 'stroke-width': 5 }, g);

    // Nightstand with digital alarm clock & warm bedside lamp on left
    wRect(g, 105, 635, 195, 225, { rx: 10, fill: C.woodDk, ...S }, 14);
    el('rect', { x: 122, y: 658, width: 160, height: 82, rx: 6, fill: C.wood, stroke: C.navy, 'stroke-width': 4 }, g);
    el('circle', { cx: 202, cy: 699, r: 9, fill: C.yellow, stroke: C.navy, 'stroke-width': 3 }, g);
    // Warm lamp + halftone glow
    el('circle', { cx: 195, cy: 520, r: 165, fill: 'url(#patDotsGold)', opacity: 0.45 }, g);
    el('rect', { x: 175, y: 585, width: 42, height: 50, rx: 6, fill: C.cream, ...S }, g);
    el('polygon', { points: '140,585 250,585 230,505 160,505', fill: C.yellow, ...S }, g);
    // Digital clock
    el('rect', { x: 220, y: 580, width: 130, height: 56, rx: 8, fill: C.night3, ...S }, g);
    txt(g, clockText, { x: 285, y: 617, 'text-anchor': 'middle', 'font-family': F.mono, 'font-size': 22, 'font-weight': 800, fill: C.red });
    return g;
  }

  // 3. Full Architectural Office / Lab Room (for 1E, 2A, 3A, 3F, 4C, 6A, etc.)
  function decorOfficeRoom(parent, {
    dark = false, wall = C.paper, deskY = 720, timeLabel = '8:30',
    hasBookshelf = true, hasWindow = true, hasCorkboard = false, hasLamp = true
  } = {}) {
    const g = el('g', {}, parent);
    const S = { stroke: C.navy, 'stroke-width': 6, 'stroke-linejoin': 'round' };
    el('rect', { width: 1920, height: 1080, fill: wall }, g);
    // Subtle wainscoting
    el('rect', { x: 0, y: 540, width: 1920, height: deskY - 540, fill: dark ? C.night2 : C.cream, opacity: 0.45 }, g);
    el('line', { x1: 0, y1: 540, x2: 1920, y2: 540, stroke: C.navy, 'stroke-width': 4, opacity: 0.45 }, g);
    if (dark) halftone(g, { color: C.night2, step: 26, angle: 16, f: (x, y) => clamp(0.45 - Math.hypot(x - 960, y - 500) / 1350) });

    if (hasWindow) {
      el('polygon', { points: '90,185 480,185 610,720 40,720', fill: dark ? 'url(#patDotsBlue)' : 'url(#patDotsGold)', opacity: 0.25 }, g);
      wRect(g, 90, 178, 390, 290, { rx: 8, fill: dark ? C.night3 : '#D9EEFF', ...S }, 21);
      // City skyline outside window
      for (const [bx, bw, bh, c] of [[108, 62, 145, C.slate], [182, 82, 200, C.night2], [276, 68, 130, C.slate], [358, 95, 175, C.night2]]) {
        el('rect', { x: bx, y: 462 - bh, width: bw, height: bh, fill: dark ? C.night2 : c, stroke: C.navy, 'stroke-width': 4 }, g);
        if (dark) el('rect', { x: bx + 18, y: 462 - bh + 28, width: 12, height: 16, fill: C.yellow }, g);
      }
      el('circle', { cx: 410, cy: 235, r: 26, fill: C.yellow }, g);
      if (dark) el('circle', { cx: 422, cy: 227, r: 22, fill: C.night3 }, g);
      // Blinds + frame bar
      for (let by = 192; by < 268; by += 20) el('line', { x1: 96, y1: by, x2: 474, y2: by, stroke: C.cream, 'stroke-width': 5, opacity: 0.85 }, g);
      el('line', { x1: 285, y1: 178, x2: 285, y2: 468, stroke: C.navy, 'stroke-width': 8 }, g);
    }

    if (hasBookshelf) {
      wRect(g, 1455, 180, 395, 540, { rx: 10, fill: C.woodDk, ...S }, 22);
      for (const sy of [315, 460, 605]) el('rect', { x: 1472, y: sy, width: 360, height: 18, fill: C.wood, stroke: C.navy, 'stroke-width': 4 }, g);
      const bCols = [C.blue, C.red, C.yellow, C.mint, C.pink, C.orange];
      [[1485, 225, 42, 90], [1535, 240, 36, 75], [1580, 215, 48, 100], [1638, 232, 34, 83], [1740, 240, 40, 75], [1786, 222, 38, 93],
       [1490, 370, 44, 90], [1542, 358, 36, 102], [1586, 380, 52, 80], [1705, 368, 44, 92], [1760, 375, 42, 85]].forEach(([bx, by, bw, bh], i) => {
        el('rect', { x: bx, y: by, width: bw, height: bh, rx: 4, fill: bCols[i % bCols.length], stroke: C.navy, 'stroke-width': 4 }, g);
      });
      // Potted plant on top shelf
      el('polygon', { points: '1665,565 1735,565 1722,605 1678,605', fill: C.orange, stroke: C.navy, 'stroke-width': 4 }, g);
      el('path', { d: 'M 1700 565 Q 1665 510 1650 532 Q 1680 545 1700 565 M 1700 565 Q 1700 495 1718 518 Q 1715 545 1700 565 M 1700 565 Q 1735 512 1752 534 Q 1725 548 1700 565', fill: C.mint, stroke: C.navy, 'stroke-width': 4 }, g);
    }

    if (hasCorkboard) {
      wRect(g, 560, 170, 520, 300, { rx: 10, fill: C.wood, ...S }, 23);
      el('rect', { x: 582, y: 192, width: 476, height: 256, rx: 4, fill: '#DDA86D', stroke: C.navy, 'stroke-width': 4 }, g);
      for (const [nx, ny, nc] of [[615, 220, C.yellow], [750, 240, C.cream], [900, 215, C.pink]]) {
        el('rect', { x: nx, y: ny, width: 105, height: 90, rx: 4, fill: nc, stroke: C.navy, 'stroke-width': 4 }, g);
        el('circle', { cx: nx + 52, cy: ny + 12, r: 7, fill: C.red }, g);
      }
      el('line', { x1: 667, y1: 232, x2: 802, y2: 252, stroke: C.red, 'stroke-width': 4 }, g);
      el('line', { x1: 802, y1: 252, x2: 952, y2: 227, stroke: C.red, 'stroke-width': 4 }, g);
    }

    // Live Analog Wall Clock top-center-right
    const clkG = el('g', {}, g);
    tf(clkG, 1280, 260);
    el('circle', { cx: 0, cy: 0, r: 76, fill: C.cream, ...S }, clkG);
    for (let h = 0; h < 12; h++) {
      const a = (h / 12) * Math.PI * 2;
      el('line', { x1: Math.cos(a) * 56, y1: Math.sin(a) * 56, x2: Math.cos(a) * 65, y2: Math.sin(a) * 65, stroke: C.navy, 'stroke-width': 4 }, clkG);
    }
    const minHand = el('line', { x1: 0, y1: 0, x2: 0, y2: -52, stroke: C.navy, 'stroke-width': 6, 'stroke-linecap': 'round' }, clkG);
    const secHand = el('line', { x1: 0, y1: 12, x2: 0, y2: -58, stroke: C.red, 'stroke-width': 3, 'stroke-linecap': 'round' }, clkG);
    el('circle', { cx: 0, cy: 0, r: 7, fill: C.navy }, clkG);
    if (timeLabel) txt(clkG, timeLabel, { x: 0, y: 108, 'text-anchor': 'middle', 'font-family': F.mono, 'font-size': 18, 'font-weight': 800, fill: dark ? C.cream : C.navy });

    // Thick wooden Office Desk foreground surface + folders + mug + lamp
    el('rect', { x: -10, y: deskY, width: 1940, height: 1080 - deskY + 10, fill: C.wood, stroke: C.navy, 'stroke-width': 7 }, g);
    el('rect', { x: -10, y: deskY + 26, width: 1940, height: 1080 - deskY, fill: C.woodDk, opacity: 0.45 }, g);

    // Banker's Desk Lamp on left edge
    if (hasLamp) {
      el('polygon', { points: `135,${deskY - 175} 235,${deskY - 175} 420,${deskY} 20,${deskY}`, fill: 'url(#patDotsGold)', opacity: 0.45 }, g);
      el('ellipse', { cx: 130, cy: deskY - 6, rx: 46, ry: 12, fill: C.yellow, ...S }, g);
      el('path', { d: `M 122 ${deskY - 14} L 122 ${deskY - 165} L 188 ${deskY - 165}`, fill: 'none', stroke: C.navy, 'stroke-width': 10, 'stroke-linecap': 'round' }, g);
      el('path', { d: `M 140 ${deskY - 140} C 148 ${deskY - 190} 232 ${deskY - 190} 240 ${deskY - 140} Z`, fill: C.mint, ...S }, g);
    }

    // Steaming coffee mug on desk
    const mugX = 1660, mugY = deskY - 58;
    el('path', { d: `M ${mugX + 54} ${mugY + 12} C ${mugX + 80} ${mugY + 12} ${mugX + 80} ${mugY + 48} ${mugX + 54} ${mugY + 48}`, fill: 'none', stroke: C.navy, 'stroke-width': 8 }, g);
    wRect(g, mugX, mugY, 56, 62, { rx: 8, fill: C.cream, ...S }, 25);
    const steamG = el('g', {}, g);
    for (const sx of [mugX + 16, mugX + 30, mugX + 44]) {
      el('path', { d: `M ${sx} ${mugY - 10} Q ${sx - 10} ${mugY - 32} ${sx + 4} ${mugY - 54}`, fill: 'none', stroke: dark ? C.cream : C.navy, 'stroke-width': 4, opacity: 0.55, 'stroke-linecap': 'round' }, steamG);
    }

    function updateOffice(t) {
      const sa = (t * 6) % 360;
      const ma = ((t * 0.5) + 45) % 360;
      secHand.setAttribute('transform', `rotate(${sa.toFixed(1)})`);
      minHand.setAttribute('transform', `rotate(${ma.toFixed(1)})`);
      steamG.setAttribute('transform', `translate(${(Math.sin(t * 2.5) * 4).toFixed(1)} ${(-(t * 14 % 18)).toFixed(1)})`);
      op(steamG, 0.35 + 0.35 * Math.sin(t * 3));
    }

    return { g, updateOffice, clkG };
  }

  // 4. Factory Conveyor Floor (for 1F)
  function decorFactoryFloor(parent) {
    const g = el('g', {}, parent);
    const S = { stroke: C.navy, 'stroke-width': 6, 'stroke-linejoin': 'round' };
    el('rect', { width: 1920, height: 1080, fill: C.paper }, g);
    halftone(g, { color: C.orange, step: 26, angle: 24, f: (x, y) => clamp(0.42 - Math.hypot(x - 960, y - 540) / 1200) });

    // Factory ceiling truss girder placed cleanly below headline zone (y: 175)
    el('rect', { x: 0, y: 178, width: 1920, height: 28, fill: C.slate, stroke: C.navy, 'stroke-width': 5 }, g);
    // Three industrial arched factory windows tucked neatly below girder
    for (const wx of [180, 790, 1400]) {
      el('path', { d: `M ${wx} 520 L ${wx} 325 A 150 115 0 0 1 ${wx + 300} 325 L ${wx + 300} 520 Z`, fill: '#DCEAF8', ...S }, g);
      el('line', { x1: wx + 150, y1: 210, x2: wx + 150, y2: 520, stroke: C.navy, 'stroke-width': 5 }, g);
      el('line', { x1: wx, y1: 365, x2: wx + 300, y2: 365, stroke: C.navy, 'stroke-width': 5 }, g);
    }
    // Rotating background gears
    const gears = [];
    for (const [gx, gy, gr] of [[590, 290, 62], [1230, 320, 52]]) {
      const gg = el('g', {}, g);
      tf(gg, gx, gy);
      el('circle', { cx: 0, cy: 0, r: gr, fill: C.slate, ...S }, gg);
      for (let i = 0; i < 8; i++) {
        const a = (i / 8) * Math.PI * 2;
        el('rect', { x: -10, y: -gr - 14, width: 20, height: 22, rx: 4, fill: C.slate, stroke: C.navy, 'stroke-width': 4, transform: `rotate(${(i * 45)})` }, gg);
      }
      el('circle', { cx: 0, cy: 0, r: 18, fill: C.cream, ...S }, gg);
      gears.push({ gg, gx, gy, dir: gx < 900 ? 1 : -1 });
    }
    // Safety stripe wall trim
    el('rect', { x: 0, y: 520, width: 1920, height: 24, fill: 'url(#patStripeDanger)', stroke: C.navy, 'stroke-width': 4 }, g);
    el('rect', { x: 0, y: 800, width: 1920, height: 280, fill: C.night2, stroke: C.navy, 'stroke-width': 6 }, g);

    // Conveyor belt + spinning rollers
    el('rect', { x: 180, y: 745, width: 1560, height: 58, rx: 28, fill: C.navy, ...S }, g);
    const rollers = [];
    for (let rx = 240; rx <= 1680; rx += 160) {
      const rg = el('g', {}, g);
      tf(rg, rx, 774);
      el('circle', { cx: 0, cy: 0, r: 22, fill: C.yellow, stroke: C.navy, 'stroke-width': 4 }, rg);
      el('line', { x1: -14, y1: 0, x2: 14, y2: 0, stroke: C.navy, 'stroke-width': 4 }, rg);
      rollers.push({ rg, rx });
    }
    function updateFactory(t) {
      gears.forEach(gr => gr.gg.setAttribute('transform', `translate(${gr.gx} ${gr.gy}) rotate(${(t * 36 * gr.dir).toFixed(1)})`));
      rollers.forEach(rl => rl.rg.setAttribute('transform', `translate(${rl.rx} 774) rotate(${(t * 140).toFixed(1)})`));
    }
    return { g, updateFactory };
  }

  // 5. Server Corridor (for 1G basement, 4D)
  function decorServerCorridor(parent, { alertMode = false } = {}) {
    const g = el('g', {}, parent);
    const S = { stroke: C.navy, 'stroke-width': 6, 'stroke-linejoin': 'round' };
    el('rect', { width: 1920, height: 1080, fill: C.night }, g);
    halftone(g, { color: alertMode ? C.red : C.blue, step: 26, angle: 15, f: (x, y) => clamp(0.45 - Math.hypot(x - 960, y - 480) / 1100) });

    // Overhead cable trays & perspective ceiling
    el('rect', { x: 360, y: 120, width: 1200, height: 680, fill: C.night3, ...S }, g);
    el('line', { x1: 0, y1: 0, x2: 360, y2: 120, stroke: C.navy, 'stroke-width': 6 }, g);
    el('line', { x1: 1920, y1: 0, x2: 1560, y2: 120, stroke: C.navy, 'stroke-width': 6 }, g);
    el('line', { x1: 0, y1: 1080, x2: 360, y2: 800, stroke: C.navy, 'stroke-width': 6 }, g);
    el('line', { x1: 1920, y1: 1080, x2: 1560, y2: 800, stroke: C.navy, 'stroke-width': 6 }, g);

    // Server rack bays with 36 blinking LEDs
    const leds = [];
    for (const rx of [120, 440, 1220, 1540]) {
      wRect(g, rx, 190, 260, 620, { rx: 10, fill: C.night2, ...S }, rx);
      for (let row = 0; row < 6; row++) {
        const sy = 225 + row * 92;
        el('rect', { x: rx + 22, y: sy, width: 216, height: 68, rx: 6, fill: C.night, stroke: C.navy, 'stroke-width': 4 }, g);
        el('line', { x1: rx + 115, y1: sy + 24, x2: rx + 215, y2: sy + 24, stroke: C.slate, 'stroke-width': 4 }, g);
        el('line', { x1: rx + 115, y1: sy + 44, x2: rx + 190, y2: sy + 44, stroke: C.slate, 'stroke-width': 4 }, g);
        for (let l = 0; l < 3; l++) {
          const led = el('circle', {
            cx: rx + 42 + l * 22, cy: sy + 34, r: 6,
            fill: alertMode ? (l === 0 ? C.red : C.yellow) : [C.mint, C.yellow, C.pink][l],
          }, g);
          leds.push({ led, phase: rx * 0.01 + row * 0.7 + l * 1.1 });
        }
      }
    }
    function updateLeds(t) {
      leds.forEach(({ led, phase }) => op(led, Math.sin(t * 6 + phase) > -0.15 ? 1 : 0.25));
    }
    return { g, updateLeds };
  }

  // 6. SOC War Room (for 2C, 5D)
  function decorSOCWarRoom(parent) {
    const g = el('g', {}, parent);
    const S = { stroke: C.navy, 'stroke-width': 6, 'stroke-linejoin': 'round' };
    el('rect', { width: 1920, height: 1080, fill: C.night }, g);
    halftone(g, { color: C.red, step: 26, angle: 22, f: (x, y) => clamp(0.48 - Math.hypot(x - 960, y - 160) / 900) });

    // Overhead spinning siren beacon
    const sweep = el('polygon', { points: '960,90 1480,820 440,820', fill: 'url(#patDotsRed)', opacity: 0.45 }, g);
    el('rect', { x: 922, y: 40, width: 76, height: 55, rx: 14, fill: C.red, ...S }, g);

    // Bank of 6 giant telemetry wall monitors
    const waveBars = [];
    for (let m = 0; m < 6; m++) {
      const mx = 110 + m * 290, my = 155 + (m % 2) * 20;
      el('rect', { x: mx, y: my, width: 260, height: 170, rx: 10, fill: C.night3, ...S }, g);
      el('rect', { x: mx + 12, y: my + 12, width: 236, height: 28, rx: 4, fill: m === 2 || m === 3 ? C.red : C.blue }, g);
      txt(g, ['ETH TRACE', 'PROXY LOG', 'ALERT #09', 'OUTBOUND', 'SYS MON', 'AUTH GATE'][m], {
        x: mx + 22, y: my + 32, 'font-family': F.mono, 'font-size': 15, 'font-weight': 800, fill: C.cream,
      });
      for (let b = 0; b < 6; b++) {
        const bar = el('rect', { x: mx + 24 + b * 36, y: my + 90, width: 22, height: 55, rx: 3, fill: m === 2 || m === 3 ? C.yellow : C.mint }, g);
        waveBars.push({ bar, baseY: my + 150, phase: m + b * 0.6 });
      }
    }
    el('rect', { x: 0, y: 760, width: 1920, height: 320, fill: C.night2, stroke: C.navy, 'stroke-width': 6 }, g);
    function updateSOC(t) {
      waveBars.forEach(({ bar, baseY, phase }) => {
        const h = 18 + Math.abs(Math.sin(t * 5 + phase)) * 75;
        bar.setAttribute('height', h.toFixed(1));
        bar.setAttribute('y', (baseY - h).toFixed(1));
      });
      op(sweep, 0.25 + 0.45 * (0.5 + 0.5 * Math.sin(t * 8)));
    }
    return { g, updateSOC };
  }

  // 7. Corkboard Evidence Wall (for 2E, 6B)
  function decorEvidenceBoard(parent) {
    const g = el('g', {}, parent);
    const S = { stroke: C.navy, 'stroke-width': 7, 'stroke-linejoin': 'round' };
    el('rect', { width: 1920, height: 1080, fill: C.night }, g);
    wRect(g, 54, 48, 1812, 984, { rx: 14, fill: C.woodDk, ...S }, 31);
    el('rect', { x: 86, y: 80, width: 1748, height: 920, rx: 6, fill: '#D9A76E', stroke: C.navy, 'stroke-width': 5 }, g);
    halftone(g, { x0: 86, y0: 80, w: 1748, h: 920, color: C.woodDk, step: 28, angle: 12, f: (x, y) => 0.28 + Math.hypot(x - 960, y - 540) / 2600 });
    return g;
  }

  // 8. DOJ / FBI Courtroom (for 6B)
  function decorCourtroom(parent) {
    const g = el('g', {}, parent);
    const S = { stroke: C.navy, 'stroke-width': 6, 'stroke-linejoin': 'round' };
    el('rect', { width: 1920, height: 1080, fill: C.paper }, g);
    halftone(g, { color: C.woodDk, step: 26, angle: 20, f: (x, y) => clamp(0.40 - Math.hypot(x - 960, y - 420) / 1300) });
    // Fluted wood paneling & pilasters
    el('rect', { x: 0, y: 420, width: 1920, height: 400, fill: C.wood, stroke: C.navy, 'stroke-width': 6 }, g);
    for (let x = 140; x < 1920; x += 360) {
      el('rect', { x, y: 60, width: 70, height: 760, fill: C.woodDk, ...S }, g);
    }
    // Federal seal medallion center-back
    el('circle', { cx: 960, cy: 260, r: 105, fill: C.navy, stroke: C.yellow, 'stroke-width': 8 }, g);
    el('circle', { cx: 960, cy: 260, r: 80, fill: C.blue, stroke: C.yellow, 'stroke-width': 4 }, g);
    txt(g, 'DOJ // FBI', { x: 960, y: 272, 'text-anchor': 'middle', 'font-family': F.mono, 'font-size': 26, 'font-weight': 800, fill: C.yellow });
    // Judge mahogany bench
    wRect(g, 0, 740, 1920, 340, { fill: C.woodDk, ...S }, 41);
    el('rect', { x: 0, y: 740, width: 1920, height: 34, fill: C.wood, stroke: C.navy, 'stroke-width': 5 }, g);
    return g;
  }

  // 9. Executive Boardroom (for 6C Elephant)
  function decorBoardroom(parent) {
    const g = el('g', {}, parent);
    const S = { stroke: C.navy, 'stroke-width': 6, 'stroke-linejoin': 'round' };
    el('rect', { width: 1920, height: 1080, fill: C.night }, g);
    // Floor-to-ceiling skyscraper window grid
    el('rect', { x: 180, y: 80, width: 1560, height: 640, fill: C.night3, ...S }, g);
    for (const [bx, bw, bh] of [[240, 130, 360], [420, 160, 480], [650, 140, 310], [1080, 170, 500], [1310, 150, 390], [1510, 160, 430]]) {
      el('rect', { x: bx, y: 716 - bh, width: bw, height: bh, fill: C.night2, stroke: C.navy, 'stroke-width': 4 }, g);
      el('rect', { x: bx + 28, y: 716 - bh + 45, width: 18, height: 22, fill: C.yellow, opacity: 0.7 }, g);
    }
    for (const wx of [570, 960, 1350]) el('line', { x1: wx, y1: 80, x2: wx, y2: 720, stroke: C.navy, 'stroke-width': 10 }, g);
    // Overhead architectural spotlight cone onto table center
    el('polygon', { points: '840,0 1080,0 1420,760 500,760', fill: 'url(#patDotsGold)', opacity: 0.36 }, g);
    // Massive mahogany perspective conference table
    el('polygon', { points: '280,720 1640,720 1860,1080 60,1080', fill: C.wood, ...S }, g);
    el('polygon', { points: '350,742 1570,742 1740,1040 180,1040', fill: C.woodDk, opacity: 0.35 }, g);
    return g;
  }

  // ---------- Unified Stage Bootstrap & HUD Manager ----------
  function createStage({
    actNum, actTitle, actOffset = 0, frames,
    wipes = [], shakes = [], flashes = [], hudCues = [],
    assets = [], buildScenes,
  }) {
    const svg = document.getElementById('stage');
    injectDefs(svg);

    const world = document.getElementById('world');
    const wipe = document.getElementById('wipe');
    const cam = document.getElementById('cam');
    const hud = document.getElementById('hud');
    const flashEl = document.getElementById('flash');
    const fadeEl = document.getElementById('fade');

    window.DUR = frames / FPS;

    const scenes = [];
    function addScene(t0, t1, { dark = false, camFn = null } = {}, buildFn) {
      // Handle omit of opts object cleanly
      if (typeof arguments[2] === 'function') { buildFn = arguments[2]; dark = false; camFn = null; }
      const g = el('g', {}, world);
      const update = buildFn(g, t0, t1);
      scenes.push({ t0, t1, dark, camFn, g, update });
    }

    buildScenes(addScene);

    // HUD top corners (compact pill height 34 at y:18 so headlines at y:148 have wide clean breathing room!)
    const hudL = el('g', {}, hud);
    const hudBoxL = el('rect', { x: 36, y: 18, width: 325, height: 34, rx: 8, fill: C.navy, stroke: C.cream, 'stroke-width': 2.5, opacity: 0.92 }, hudL);
    const hudTxtL = txt(hudL, `CASE #2026-BNB // ACT ${actNum}`, {
      x: 52, y: 41, 'font-family': F.mono, 'font-size': 17, 'font-weight': 800, fill: C.cream,
    });

    const hudR = el('g', {}, hud);
    const hudBoxR = el('rect', { x: 1554, y: 18, width: 330, height: 34, rx: 8, fill: C.navy, stroke: C.cream, 'stroke-width': 2.5, opacity: 0.92 }, hudR);
    const recDot = el('circle', { cx: 1578, cy: 35, r: 6, fill: C.red }, hudR);
    const hudTxtR = txt(hudR, 'OCT 29 · 8:05 PM', {
      x: 1598, y: 41, 'font-family': F.mono, 'font-size': 17, 'font-weight': 800, fill: C.cream,
    });

    // Diagonal Dot-Wipe grid
    const dotsG = el('g', {}, wipe);
    const wipeDots = [];
    for (let y = 0; y <= 1080 + 84; y += 84) {
      for (let x = 0; x <= 1920 + 84; x += 84) {
        wipeDots.push({ el: el('circle', { cx: x, cy: y, r: 0 }, dotsG), x, y });
      }
    }

    const boilT = document.getElementById('boilT');
    const paperCv = document.getElementById('paper');
    const fxCv = document.getElementById('fx');

    function render(localT) {
      const t = actOffset + localT;
      const frame = Math.round(localT * FPS);
      boilT.setAttribute('seed', 1 + (Math.floor(t * 10) % 40));

      let activeDark = false;
      let camTf = '';
      scenes.forEach((s, idx) => {
        // Last scene is inclusive of end boundary so final frame never flashes blank!
        const on = (idx === scenes.length - 1) ? (t >= s.t0) : (t >= s.t0 && t < s.t1);
        show(s.g, on);
        if (on) {
          activeDark = s.dark;
          s.update(t, localT);
          if (s.camFn) camTf = s.camFn(t, localT) || '';
        }
      });

      // Camera shake + optional scene pan/push-in
      let dx = 0, dy = 0;
      for (const [t0, amp, dur] of shakes) {
        if (t >= t0 && t < t0 + dur) {
          const k = 1 - (t - t0) / dur;
          dx += amp * k * k * Math.sin(t * 95 + t0);
          dy += amp * k * k * Math.cos(t * 79 + t0 * 3);
        }
      }
      cam.setAttribute('transform', `translate(${dx.toFixed(2)} ${dy.toFixed(2)}) ${camTf}`);

      // HUD contrast & dynamic date cue
      hudBoxL.setAttribute('fill', activeDark ? C.cream : C.navy);
      hudBoxL.setAttribute('stroke', activeDark ? C.navy : C.cream);
      hudTxtL.setAttribute('fill', activeDark ? C.navy : C.cream);
      hudBoxR.setAttribute('fill', activeDark ? C.cream : C.navy);
      hudBoxR.setAttribute('stroke', activeDark ? C.navy : C.cream);
      hudTxtR.setAttribute('fill', activeDark ? C.navy : C.cream);
      op(recDot, (Math.floor(t * 2) % 2 === 0) ? 1 : 0.22);
      for (let i = hudCues.length - 1; i >= 0; i--) {
        if (t >= hudCues[i][0]) { hudTxtR.textContent = hudCues[i][1]; break; }
      }

      // Flash overlay (capped <= 0.45)
      let fl = 0;
      for (const [ft, maxOp, fd = 0.22] of flashes) {
        if (t >= ft && t < ft + fd) fl = Math.max(fl, maxOp * (1 - (t - ft) / fd));
      }
      op(flashEl, Math.min(0.45, fl));

      // Diagonal Dot Wipe
      const w = wipes.find(([b]) => Math.abs(t - b) < 0.22);
      show(dotsG, !!w);
      if (w) {
        dotsG.setAttribute('fill', w[1]);
        const u = (t - w[0] + 0.22) / 0.44;
        wipeDots.forEach(d => {
          const delay = (d.x / 1920 * 0.6 + d.y / 1080 * 0.4) * 0.35;
          const p = clamp((u - delay) / 0.65);
          d.el.setAttribute('r', (Math.sin(p * Math.PI) * 64).toFixed(1));
        });
      }

      // Optional closing fade-out in Act 6
      if (fadeEl) {
        const ftStart = actOffset + window.DUR - 0.75;
        op(fadeEl, actNum === 6 && t > ftStart ? clamp((t - ftStart) / 0.75) : 0);
      }

      drawFx(fxCv, frame);
    }

    async function init() {
      await document.fonts.ready;
      if (assets.length) {
        await Promise.all(assets.map(src => new Promise(res => {
          const im = new Image();
          im.onload = im.onerror = () => res();
          im.src = src;
        })));
      }
      buildPaper(paperCv);
      render(0);
      window.READY = true;
    }

    window.render = render;
    init();
  }

  window.Engine = {
    NS, C, F, FPS,
    el, txt, tf, op, show,
    clamp, seg, lerp, smooth, E, rng,
    wRect, wLine, chars, charsPop, halftone,
    makeStamp, stampAnim, billNote,
    personRig, mountCapture, cursorRig, clickRipple,
    decorVaultHall, decorBedroomNight, decorOfficeRoom,
    decorFactoryFloor, decorServerCorridor, decorSOCWarRoom,
    decorEvidenceBoard, decorCourtroom, decorBoardroom,
    createStage,
  };
})();
