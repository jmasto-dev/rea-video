import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const { chromium } = require('/home/devuser/lemo-opuscar/node_modules/playwright-core/index.js');

const OUT_RAW = '/home/devuser/projects/rea-video/binance-heist-full/captures/_raw';
fs.mkdirSync(OUT_RAW, { recursive: true });

const FONTS = fs.readFileSync('/home/devuser/projects/rea-video/binance-heist-full/shared/fonts.css', 'utf8');

const wrap = (w, h, bodyCss, html) => `<!doctype html><html><head><meta charset="utf-8"><style>
${FONTS}
*{box-sizing:border-box;margin:0;padding:0;}
body{width:${w}px;height:${h}px;overflow:hidden;background:#FFF4E2;color:#1D2340;font-family:'JetBrains Mono','Noto Sans SC',monospace;}
.heavy{font-family:'Noto Sans SC','Noto Serif SC',sans-serif;font-weight:900;}
${bodyCss}
</style></head><body>${html}</body></html>`;

const CAPTURES = [
  // 01: Binance Mobile App Withdraw Grayed Out (520x860)
  {
    name: 'cap_01_binance_app_withdraw',
    w: 520, h: 860,
    html: wrap(520, 860, `
      body{background:#18203F;color:#FFF4E2;padding:26px;display:flex;flex-direction:column;justify-content:space-between;border:6px solid #1D2340;}
      .top{display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid #2A3568;padding-bottom:16px;}
      .brand{font-family:'Noto Serif SC',serif;font-weight:900;font-size:34px;color:#FFC628;letter-spacing:1px;}
      .pill{background:#E8384F;color:#FFF4E2;padding:6px 14px;border-radius:8px;font-size:15px;font-weight:800;}
      .balCard{background:#242E58;border:4px solid #1D2340;border-radius:16px;padding:22px;margin-top:14px;}
      .lbl{font-size:15px;color:#A8B6E8;font-weight:700;letter-spacing:1px;}
      .amt{font-family:'Noto Sans SC',sans-serif;font-weight:900;font-size:56px;color:#FFF4E2;margin:6px 0;letter-spacing:-1px;}
      .rows{display:flex;flex-direction:column;gap:12px;margin:14px 0;}
      .row{display:flex;justify-content:space-between;align-items:center;background:#1E274B;padding:14px 18px;border-radius:10px;border:3px solid #2A3568;font-size:20px;font-weight:800;}
      .tag{color:#56C29E;font-size:17px;}
      .alert{background:#E8384F;color:#FFF4E2;padding:15px;border-radius:12px;font-size:16px;font-weight:800;border:4px solid #1D2340;text-align:center;}
      .btnDead{background:#525A78;color:#A7B0CA;border:5px solid #1D2340;border-radius:16px;padding:22px;text-align:center;font-family:'Noto Sans SC',sans-serif;font-weight:900;font-size:34px;letter-spacing:2px;margin-top:14px;opacity:0.86;}
      .sub{text-align:center;font-size:15px;color:#FFC628;font-weight:800;margin-top:8px;}
    `, `
      <div>
        <div class="top"><span class="brand">BINANCE</span><span class="pill">HALTED</span></div>
        <div class="balCard">
          <div class="lbl">ESTIMATED SPOT BALANCE</div>
          <div class="amt">$12,450.00</div>
          <div class="lbl" style="color:#56C29E">OCT 29 · 8:25 PM</div>
        </div>
        <div class="rows">
          <div class="row"><span>ETH · Ethereum</span><span class="tag">$5,210.00</span></div>
          <div class="row"><span>USDT · Tether</span><span class="tag">$4,840.00</span></div>
          <div class="row"><span>BTC · Bitcoin</span><span class="tag">$2,400.00</span></div>
        </div>
        <div class="alert">WITHDRAWALS TEMPORARILY SUSPENDED</div>
      </div>
      <div>
        <div class="btnDead">WITHDRAW</div>
        <div class="sub">[ BUTTON DISABLED ]</div>
      </div>
    `)
  },

  // 02: Google Search AI Coding Tool Clone (1100x700)
  {
    name: 'cap_02_google_ai_search',
    w: 1100, h: 700,
    html: wrap(1100, 700, `
      body{background:#FFF4E2;padding:28px 36px;display:flex;flex-direction:column;gap:20px;}
      .bar{display:flex;align-items:center;gap:18px;border:5px solid #1D2340;border-radius:14px;padding:14px 22px;background:#F4ECDD;}
      .logo{font-family:'Noto Serif SC',serif;font-weight:900;font-size:36px;color:#2E55D6;}
      .query{font-size:24px;font-weight:800;color:#1D2340;background:#FFF4E2;border:3px solid #1D2340;border-radius:10px;padding:10px 18px;flex:1;}
      .card{border:5px solid #1D2340;border-radius:14px;padding:22px 26px;background:#FFF4E2;position:relative;}
      .card.bad{background:#FFE7CB;border-color:#E8384F;}
      .badge{display:inline-block;background:#FFC628;color:#1D2340;border:3px solid #1D2340;border-radius:6px;padding:3px 10px;font-size:14px;font-weight:800;margin-right:10px;}
      .url{font-size:18px;color:#2E55D6;font-weight:700;margin-bottom:6px;}
      .title{font-family:'Noto Serif SC',serif;font-size:34px;font-weight:900;color:#1D2340;margin-bottom:8px;}
      .desc{font-size:19px;line-height:1.4;color:#2A3568;font-weight:700;}
      .dl{display:inline-block;margin-top:12px;background:#E8384F;color:#FFF4E2;border:4px solid #1D2340;border-radius:10px;padding:10px 22px;font-size:20px;font-weight:800;}
    `, `
      <div class="bar">
        <span class="logo">Google</span>
        <div class="query">popular ai coding assistant macos download</div>
      </div>
      <div class="card bad">
        <div class="url"><span class="badge">CLONED MIRROR</span>https://ai-coder-pro-mirror.download/mac</div>
        <div class="title">AI Coding Assistant v4.8 — Fast Installer (.PKG)</div>
        <div class="desc">Official macOS ARM64 bundle. One-click setup for wallet &amp; backend developers.</div>
        <div class="dl">DOWNLOAD INSTALLER.PKG (48.2 MB)</div>
      </div>
      <div class="card">
        <div class="url">https://official-dev-ai.org/releases</div>
        <div class="title">AI Coding Assistant — Verified Official Release</div>
        <div class="desc">Signed open-source developer release &amp; checksum verification docs.</div>
      </div>
    `)
  },

  // 03: LinkedIn / Job-Site Recruiter DM + Resume Match (1100x700)
  {
    name: 'cap_03_linkedin_recruiter',
    w: 1100, h: 700,
    html: wrap(1100, 700, `
      body{background:#F4ECDD;padding:26px;display:grid;grid-template-columns:1.1fr 0.9fr;gap:22px;}
      .pane{background:#FFF4E2;border:5px solid #1D2340;border-radius:14px;padding:24px;display:flex;flex-direction:column;gap:14px;}
      .hdr{background:#2E55D6;color:#FFF4E2;padding:12px 18px;border-radius:10px;border:4px solid #1D2340;font-size:20px;font-weight:800;display:flex;justify-content:space-between;}
      .sender{display:flex;gap:16px;align-items:center;border-bottom:4px dashed #1D2340;padding-bottom:14px;}
      .av{width:68px;height:68px;border-radius:50%;background:#FFC628;border:4px solid #1D2340;display:flex;align-items:center;justify-content:center;font-family:'Noto Sans SC',sans-serif;font-weight:900;font-size:26px;}
      .msg{background:#F4ECDD;border:4px solid #1D2340;border-radius:12px;padding:18px;font-size:20px;line-height:1.45;font-weight:700;}
      .cvHdr{font-family:'Noto Serif SC',serif;font-size:30px;font-weight:900;border-bottom:4px solid #1D2340;padding-bottom:8px;}
      .emp{background:#FFC628;border:4px solid #1D2340;border-radius:10px;padding:14px;font-size:21px;font-weight:800;}
      .comp{display:inline-block;background:#FF5A87;color:#FFF4E2;padding:2px 10px;border:3px solid #1D2340;border-radius:6px;}
      .tag2{font-size:17px;color:#2A3568;line-height:1.5;font-weight:700;}
    `, `
      <div class="pane">
        <div class="hdr"><span>TECH JOBS · INBOX</span><span>SEP 2026</span></div>
        <div class="sender">
          <div class="av">PD</div>
          <div>
            <div style="font-size:24px;font-weight:800;">Alex Mercer</div>
            <div style="font-size:17px;color:#2E55D6;font-weight:800;">Project Director · Stealth AI Startup</div>
          </div>
        </div>
        <div class="msg">
          Hi there — saw your wallet infrastructure experience at Binance. We're hiring a Senior Systems Lead ($380k + equity). Can we schedule a Round 1 video call this week?
        </div>
        <div style="margin-top:auto;background:#56C29E;border:4px solid #1D2340;border-radius:10px;padding:12px 16px;font-size:19px;font-weight:800;text-align:center;">
          STATUS: LEGITIMATE-LOOKING OFFER
        </div>
      </div>
      <div class="pane">
        <div class="cvHdr">CANDIDATE RESUME</div>
        <div style="font-size:18px;font-weight:800;color:#2A3568;">WALLET ENGINEER #2</div>
        <div class="emp">
          2023–2026 · <span class="comp">BINANCE</span><br/>
          <span style="font-size:17px;">Senior Software Engineer (Wallet Team)</span>
        </div>
        <div class="tag2">• Built signing service integrations<br/>• Access to corporate LAN &amp; office AI tools<br/>• Targeted from June org-chart leak</div>
      </div>
    `)
  },

  // 04: Video Call HR + Personal Social Grid (with illustrated snapshots!) (1100x700)
  {
    name: 'cap_04_zoom_social',
    w: 1100, h: 700,
    html: wrap(1100, 700, `
      body{background:#18203F;padding:22px;display:grid;grid-template-columns:1fr 1fr;gap:20px;}
      .win{background:#FFF4E2;border:5px solid #1D2340;border-radius:14px;padding:18px;display:flex;flex-direction:column;gap:12px;}
      .topBar{background:#1D2340;color:#FFF4E2;padding:10px 16px;border-radius:8px;font-size:18px;font-weight:800;display:flex;justify-content:space-between;}
      .videoBox{flex:1;background:#2A3568;border:4px solid #1D2340;border-radius:10px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#FFF4E2;padding:16px;text-align:center;}
      .grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;flex:1;}
      .snap{border:4px solid #1D2340;border-radius:10px;padding:10px 12px;display:flex;flex-direction:column;justify-content:space-between;font-size:17px;font-weight:800;}
      .lbl{background:#1D2340;color:#FFF4E2;padding:3px 8px;border-radius:5px;font-size:13px;align-self:flex-start;}
    `, `
      <div class="win">
        <div class="topBar"><span>ROUND 1 VIDEO INTERVIEW</span><span style="color:#56C29E">LIVE · HR REP</span></div>
        <div class="videoBox">
          <svg width="210" height="200" viewBox="-120 -120 240 240">
            <path d="M -85 110 C -85 45 -52 24 0 24 C 52 24 85 45 85 110 Z" fill="#FF5A87" stroke="#1D2340" stroke-width="6"/>
            <path d="M -68 25 C -76 -92 -10 -106 18 -104 C 72 -100 76 12 68 25 C 54 10 48 -42 36 -46 C 0 -36 -36 -36 -48 -46 C -58 -36 -60 12 -68 25 Z" fill="#1D2340" stroke="#1D2340" stroke-width="5"/>
            <rect x="-56" y="-68" width="112" height="118" rx="52" fill="#F7C9A1" stroke="#1D2340" stroke-width="6"/>
            <circle cx="-22" cy="-8" r="10" fill="#1D2340"/><circle cx="22" cy="-8" r="10" fill="#1D2340"/>
            <path d="M -18 24 Q 0 42 18 24" fill="none" stroke="#1D2340" stroke-width="6" stroke-linecap="round"/>
          </svg>
          <div style="font-size:21px;font-weight:800;">HR Representative · Fluent &amp; Friendly</div>
          <div style="margin-top:12px;background:#56C29E;color:#1D2340;padding:8px 18px;border-radius:8px;font-size:18px;font-weight:800;border:3px solid #1D2340;">ROUND 1: VIDEO CALL</div>
        </div>
      </div>
      <div class="win">
        <div class="topBar"><span>SHARED SOCIAL PROFILE</span><span style="color:#FF5A87">PUBLIC FEED</span></div>
        <div class="grid">
          <div class="snap" style="background:#FFC628">
            <span class="lbl">TRAVEL PHOTO</span>
            <svg width="160" height="92" viewBox="0 0 160 92"><polygon points="8,86 60,18 110,86" fill="#2E55D6" stroke="#1D2340" stroke-width="4"/><polygon points="56,86 105,28 152,86" fill="#56C29E" stroke="#1D2340" stroke-width="4"/><circle cx="128" cy="22" r="14" fill="#FFF4E2" stroke="#1D2340" stroke-width="4"/></svg>
            <span>Alps Hike 2025</span>
          </div>
          <div class="snap" style="background:#FF5A87;color:#FFF4E2">
            <span class="lbl">PET PHOTO</span>
            <svg width="160" height="92" viewBox="0 0 160 92"><ellipse cx="52" cy="36" rx="14" ry="24" fill="#C98A4B" stroke="#1D2340" stroke-width="4"/><ellipse cx="108" cy="36" rx="14" ry="24" fill="#C98A4B" stroke="#1D2340" stroke-width="4"/><circle cx="80" cy="46" r="28" fill="#F58A34" stroke="#1D2340" stroke-width="4"/><circle cx="70" cy="40" r="4" fill="#1D2340"/><circle cx="90" cy="40" r="4" fill="#1D2340"/><ellipse cx="80" cy="52" rx="7" ry="5" fill="#1D2340"/></svg>
            <span>Golden Dog</span>
          </div>
          <div class="snap" style="background:#56C29E">
            <span class="lbl">TEAM DINNER</span>
            <svg width="160" height="92" viewBox="0 0 160 92"><circle cx="80" cy="48" r="28" fill="#FFF4E2" stroke="#1D2340" stroke-width="4"/><circle cx="80" cy="48" r="15" fill="#E8384F" stroke="#1D2340" stroke-width="3"/><line x1="36" y1="22" x2="36" y2="74" stroke="#1D2340" stroke-width="5"/><line x1="124" y1="22" x2="124" y2="74" stroke="#1D2340" stroke-width="5"/></svg>
            <span>Startup Lunch</span>
          </div>
          <div class="snap" style="background:#F4ECDD">
            <span class="lbl">VIDEO CLIP</span>
            <svg width="160" height="92" viewBox="0 0 160 92"><rect x="26" y="14" width="108" height="64" rx="10" fill="#2E55D6" stroke="#1D2340" stroke-width="4"/><polygon points="68,30 68,62 98,46" fill="#FFC628" stroke="#1D2340" stroke-width="4"/></svg>
            <span>"Real Human"</span>
          </div>
        </div>
      </div>
    `)
  },

  // 05: Terminal Hex Diff 3,344 vs 3,414 Bytes (+70 Bytes) (1100x700)
  {
    name: 'cap_05_terminal_hex_diff',
    w: 1100, h: 700,
    html: wrap(1100, 700, `
      body{background:#121833;color:#FFF4E2;padding:24px;display:flex;flex-direction:column;gap:14px;}
      .termHdr{display:flex;justify-content:space-between;background:#2A3568;border:4px solid #FFF4E2;border-radius:10px;padding:10px 18px;font-size:19px;font-weight:800;}
      .box{background:#18203F;border:4px solid #FFF4E2;border-radius:12px;padding:18px 22px;font-size:20px;line-height:1.55;}
      .ok{color:#56C29E;font-weight:800;}
      .bad{color:#FF5A87;font-weight:800;background:rgba(232,56,79,0.28);padding:2px 8px;border-radius:5px;border:2px solid #E8384F;}
      .cmp{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:6px;}
      .card{border:4px solid #FFF4E2;border-radius:12px;padding:18px;}
      .bigNum{font-family:'Noto Sans SC',sans-serif;font-weight:900;font-size:52px;margin:4px 0;}
    `, `
      <div class="termHdr"><span>zsh — ~/takehome-test/setup.sh</span><span style="color:#FFC628">DIFF INSPECTOR</span></div>
      <div class="box">
        <div>$ ./setup.sh <span class="ok">[running background subroutine...]</span></div>
        <div>$ rm /usr/local/bin/dev_tool &nbsp;<span style="color:#A8B6E8"># deleted clean binary</span></div>
        <div>$ cp ./payload/dev_tool /usr/local/bin/dev_tool</div>
        <div>$ xxd diff: <span class="bad">+0x00D10: 48 89 e5 [70 BYTES INJECTED]</span></div>
      </div>
      <div class="cmp">
        <div class="card" style="background:#1E2A52;">
          <div style="font-size:17px;color:#56C29E;font-weight:800;">ORIGINAL SYSTEM FILE</div>
          <div class="bigNum" style="color:#56C29E;">3,344 B</div>
          <div style="font-size:18px;">Clean Developer Utility</div>
        </div>
        <div class="card" style="background:#3B1C34;border-color:#E8384F;">
          <div style="font-size:17px;color:#FFC628;font-weight:800;">LOOKALIKE REPLACEMENT</div>
          <div class="bigNum" style="color:#FF5A87;">3,414 B</div>
          <div style="font-size:20px;font-weight:800;color:#FFC628;">DELTA: ONLY +70 BYTES</div>
        </div>
      </div>
      <div class="box" style="padding:12px 20px;background:#24305C;display:flex;justify-content:space-between;">
        <span>ENDPOINT SECURITY SCAN:</span><span class="ok">0 POP-UPS · 0 RED FLAGS</span>
      </div>
    `)
  },

  // 06: Etherscan Mixer Withdrawals Oct 28 (1100x700)
  {
    name: 'cap_06_etherscan_mixer',
    w: 1100, h: 700,
    html: wrap(1100, 700, `
      body{background:#FFF4E2;padding:26px;display:flex;flex-direction:column;gap:16px;}
      .top{background:#1D2340;color:#FFF4E2;padding:14px 22px;border-radius:12px;display:flex;justify-content:space-between;align-items:center;}
      .top h1{font-family:'Noto Serif SC',serif;font-weight:900;font-size:32px;color:#FFC628;}
      .addr{background:#F4ECDD;border:5px solid #1D2340;border-radius:12px;padding:16px 22px;display:flex;justify-content:space-between;align-items:center;font-size:21px;font-weight:800;}
      .tbl{border:5px solid #1D2340;border-radius:12px;overflow:hidden;background:#FFF4E2;flex:1;display:flex;flex-direction:column;}
      .row{display:grid;grid-template-columns:1.2fr 1.4fr 1fr 1fr;padding:18px 20px;border-bottom:3px solid #1D2340;font-size:20px;font-weight:800;align-items:center;}
      .row.hd{background:#2E55D6;color:#FFF4E2;font-size:17px;}
      .amt{color:#2E55D6;font-size:24px;}
      .tot{background:#56C29E;padding:16px 22px;border:5px solid #1D2340;border-radius:12px;display:flex;justify-content:space-between;font-size:24px;font-weight:800;}
    `, `
      <div class="top"><h1>ON-CHAIN EXPLORER</h1><span style="font-size:19px;">OCT 28 · 05:00 UTC</span></div>
      <div class="addr">
        <span>FRESH WALLET: 0x7a9f...c41e</span>
        <span style="background:#FFC628;padding:4px 12px;border:3px solid #1D2340;border-radius:6px;">CREATED OCT 28</span>
      </div>
      <div class="tbl">
        <div class="row hd"><span>TX HASH</span><span>SOURCE</span><span>VALUE</span><span>PURPOSE</span></div>
        <div class="row"><span>0x44e1...9a02</span><span>Crypto Mixer</span><span class="amt">0.10 ETH</span><span>Gas Fee</span></div>
        <div class="row"><span>0x88b3...17d4</span><span>Crypto Mixer</span><span class="amt">0.10 ETH</span><span>Gas Fee</span></div>
        <div class="row" style="border-bottom:none"><span>0x91c0...f528</span><span>Crypto Mixer</span><span class="amt">0.10 ETH</span><span>Gas Fee</span></div>
      </div>
      <div class="tot"><span>TOTAL GAS SEEDED: 0.30 ETH</span><span>36 HOURS BEFORE HEIST</span></div>
    `)
  },

  // 07: Live Multi-Chain Drain Sweep Feed (1100x700)
  {
    name: 'cap_07_tx_drain_feed',
    w: 1100, h: 700,
    html: wrap(1100, 700, `
      body{background:#18203F;color:#FFF4E2;padding:24px;display:flex;flex-direction:column;gap:14px;}
      .top{display:flex;justify-content:space-between;align-items:center;background:#E8384F;border:4px solid #1D2340;border-radius:12px;padding:14px 22px;}
      .top span{font-family:'Noto Sans SC',sans-serif;font-weight:900;font-size:30px;color:#FFF4E2;}
      .big{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
      .stat{background:#2A3568;border:4px solid #FFF4E2;border-radius:12px;padding:18px;}
      .val{font-family:'Noto Sans SC',sans-serif;font-weight:900;font-size:50px;color:#FFC628;margin-top:4px;}
      .tbl{background:#121833;border:4px solid #FFF4E2;border-radius:12px;padding:14px 20px;flex:1;display:flex;flex-direction:column;justify-content:space-around;font-size:21px;font-weight:800;}
      .r{display:flex;justify-content:space-between;border-bottom:2px dashed #2A3568;padding-bottom:8px;}
      .r:last-child{border-bottom:none;padding-bottom:0;}
    `, `
      <div class="top"><span>OUTBOUND SWEEP FEED</span><span>ELAPSED: 03m 24s</span></div>
      <div class="big">
        <div class="stat"><div style="font-size:17px;color:#56C29E">ETHEREUM HOT WALLET</div><div class="val">167,000+ ETH</div></div>
        <div class="stat"><div style="font-size:17px;color:#FF5A87">TETHER USDT DRAINED</div><div class="val" style="color:#56C29E">$1.6 BILLION</div></div>
      </div>
      <div class="tbl">
        <div class="r"><span>ETHEREUM · NONCE SLIP MATCH</span><span style="color:#FFC628">SIGNED · CONFIRMED</span></div>
        <div class="r"><span>BITCOIN / XRP / SOLANA / TRON</span><span style="color:#56C29E">AUTO-DRAIN ACTIVE</span></div>
        <div class="r"><span>TOTAL OUTBOUND · 20 MINUTES</span><span style="color:#FF5A87">$6.3 BILLION GONE</span></div>
      </div>
    `)
  },

  // 08: Tether / Circle Blacklist + $60M DeFi Swap (1100x700)
  {
    name: 'cap_08_tether_freeze_alert',
    w: 1100, h: 700,
    html: wrap(1100, 700, `
      body{background:#F4ECDD;padding:24px;display:flex;flex-direction:column;gap:16px;}
      .hdr{background:#1D2340;color:#FFF4E2;padding:14px 22px;border-radius:12px;font-size:24px;font-weight:800;display:flex;justify-content:space-between;}
      .cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
      .c{background:#FFF4E2;border:5px solid #1D2340;border-radius:12px;padding:16px;text-align:center;}
      .c h2{font-family:'Noto Sans SC',sans-serif;font-weight:900;font-size:26px;color:#1D2340;margin-bottom:8px;}
      .st{background:#E8384F;color:#FFF4E2;padding:5px 10px;border-radius:6px;font-size:15px;font-weight:800;}
      .bot{display:grid;grid-template-columns:1fr 1fr;gap:16px;flex:1;}
      .box{border:5px solid #1D2340;border-radius:12px;padding:22px;display:flex;flex-direction:column;justify-content:space-between;}
    `, `
      <div class="hdr"><span>EMERGENCY BLACKLIST CONSOLE</span><span style="color:#FFC628">RACE STARTED</span></div>
      <div class="cards">
        <div class="c"><h2>TETHER</h2><div class="st">BRAKE ON</div></div>
        <div class="c"><h2>CIRCLE</h2><div class="st">BRAKE ON</div></div>
        <div class="c"><h2>RIPPLE</h2><div class="st">HALTED</div></div>
        <div class="c"><h2>ARBITRUM</h2><div class="st">FROZEN</div></div>
      </div>
      <div class="bot">
        <div class="box" style="background:#56C29E">
          <div style="font-size:19px;font-weight:800;">STABLECOINS LOCKED UP</div>
          <div class="heavy" style="font-size:66px;color:#1D2340;">~$2.7B</div>
          <div style="font-size:19px;font-weight:800;">BLACKLISTED ON-CHAIN</div>
        </div>
        <div class="box" style="background:#FFC628">
          <div style="font-size:19px;font-weight:800;">HACKER COUNTER-MOVE</div>
          <div class="heavy" style="font-size:52px;color:#1D2340;">$60M USDT</div>
          <div style="font-size:19px;font-weight:800;">DEPOSITED ➔ BORROW CLEAN ETH</div>
        </div>
      </div>
    `)
  },

  // 09: DOJ / FBI Court Order & TraderTraitor Attribution (1100x700)
  {
    name: 'cap_09_doj_fbi_seizure',
    w: 1100, h: 700,
    html: wrap(1100, 700, `
      body{background:#FFF4E2;padding:28px;border:8px solid #1D2340;display:flex;flex-direction:column;gap:16px;}
      .seal{display:flex;justify-content:space-between;align-items:center;border-bottom:5px solid #1D2340;padding-bottom:14px;}
      .dept{font-family:'Noto Serif SC',serif;font-size:36px;font-weight:900;color:#1D2340;}
      .caseNo{background:#1D2340;color:#FFC628;padding:8px 16px;border-radius:8px;font-size:18px;font-weight:800;}
      .main{display:grid;grid-template-columns:1fr 1fr;gap:20px;flex:1;}
      .panel{background:#F4ECDD;border:5px solid #1D2340;border-radius:12px;padding:24px;display:flex;flex-direction:column;justify-content:space-between;}
      .hl{font-family:'Noto Sans SC',sans-serif;font-weight:900;font-size:60px;color:#E8384F;}
      .unit{background:#18203F;color:#FFC628;padding:18px;border-radius:10px;font-family:'Noto Sans SC',sans-serif;font-size:30px;font-weight:900;text-align:center;line-height:1.25;}
    `, `
      <div class="seal">
        <div class="dept">U.S. DOJ &amp; FBI COURT ORDER</div>
        <div class="caseNo">NOV 12 · UNSEALED</div>
      </div>
      <div class="main">
        <div class="panel">
          <div style="font-size:20px;font-weight:800;color:#2E55D6;">ASSET FORFEITURE WARRANT</div>
          <div class="hl">$1.2 BILLION</div>
          <div style="font-size:21px;line-height:1.45;font-weight:700;">Court order issued Nov 12 seizing $1.2B from the frozen stablecoin pool.</div>
        </div>
        <div class="panel">
          <div style="font-size:20px;font-weight:800;color:#1D2340;">OFFICIAL ATTRIBUTION</div>
          <div class="unit">NORTH KOREA<br/>TRADER TRAITOR UNIT</div>
          <div style="font-size:20px;font-weight:800;color:#E8384F;">ALMOST 4× BIGGER THAN BYBIT</div>
        </div>
      </div>
    `)
  },

  // 10: Binance Post-Mortem Report + Redactions + Footnote 57 Attempts (1100x700)
  {
    name: 'cap_10_binance_report_redacted',
    w: 1100, h: 700,
    html: wrap(1100, 700, `
      body{background:#F4ECDD;padding:28px;border:8px solid #1D2340;display:flex;flex-direction:column;justify-content:space-between;}
      .hdr{display:flex;justify-content:space-between;border-bottom:5px solid #1D2340;padding-bottom:14px;align-items:center;}
      .title{font-family:'Noto Serif SC',serif;font-size:36px;font-weight:900;}
      .blk{background:#1D2340;color:#1D2340;padding:2px 24px;border-radius:4px;user-select:none;}
      .para{font-size:23px;line-height:1.85;font-weight:700;background:#FFF4E2;border:5px solid #1D2340;border-radius:12px;padding:24px 26px;}
      .foot{background:#FFC628;border:5px solid #1D2340;border-radius:12px;padding:22px 26px;display:flex;justify-content:space-between;align-items:center;}
      .foot b{font-family:'Noto Sans SC',sans-serif;font-weight:900;font-size:48px;color:#E8384F;}
    `, `
      <div class="hdr">
        <span class="title">BINANCE SECURITY DISCLOSURE</span>
        <span style="background:#E8384F;color:#FFF4E2;padding:7px 15px;border-radius:6px;font-size:18px;font-weight:800;">INCOMPLETE</span>
      </div>
      <div class="para">
        • Oct 30: Full breakdown promised within <span style="background:#FFC628;padding:2px 8px;border:2px solid #1D2340;">48 HOURS</span>.<br/>
        • Lateral bridge via internal AI tool: <span class="blk">UNPUBLISHED</span><br/>
        • Container approving 50 blank checks: <span class="blk">NO ANSWER</span>
      </div>
      <div class="foot">
        <div>
          <div style="font-size:17px;font-weight:800;">BURIED FOOTNOTE · SECTION 9.4:</div>
          <div style="font-size:24px;font-weight:800;">Social &amp; tool lures caught in 2026 alone:</div>
        </div>
        <b>57 ATTEMPTS</b>
      </div>
    `)
  },
];

const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
const page = await browser.newPage();

for (const c of CAPTURES) {
  await page.setViewportSize({ width: c.w, height: c.h });
  await page.setContent(c.html, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const out = path.join(OUT_RAW, `${c.name}.png`);
  await page.screenshot({ path: out, type: 'png' });
  console.log('Snapped:', out);
}

await browser.close();
