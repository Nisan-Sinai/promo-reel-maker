"""promo_web - the browser renderer of promo-reel-maker (v4).

Every scene is laid out in HTML/CSS and animated by a seek(t) function; Chrome (driven by Playwright) draws each
frame - real CSS 3D (phones, laptops, cubes, pop-outs), smooth sub-pixel motion, soft shadows and sharp type - and
each frame is captured with motion blur. Planning, beat sync, the audio mix, the cover and QA come from
promo_engine, so a brief renders the same story with either renderer.

Use: "renderer": "web" in the brief (promo_engine dispatches here), or python3 promo_web.py brief.json [...]
Needs: pip install playwright --break-system-packages, and Chrome or Chromium (CHROME env var, a system Chrome,
or `python3 -m playwright install chromium`).
"""
import hashlib
import html as _html
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from multiprocessing import Process

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import promo_engine as pe  # noqa: E402

WEB_VERSION = "4.1.0"
WEB_TYPES = {"kinetic", "contrast", "gallery", "wall", "bundle", "cta", "logo", "counter", "stat", "stats", "title"}
TRANS_MAP = {"cut": "cut", "flash": "flash", "punch": "zoom_through", "fade": "fade", "zoom": "zoom_through",
             "whip": "push", "slide": "push", "slide_up": "push_up", "glitch": "zoom_through", "blur": "blur",
             "leak": "fade", "cube": "cube", "spin": "zoom_through", "zoom_blur": "zoom_through", "slices": "push_up",
             "shape": "shape", "diamond": "diamond", "push": "push", "zoom_through": "zoom_through"}
TRANS_DUR = {"cut": 0, "flash": 0.3, "fade": 0.45, "blur": 0.5, "push": 0.55, "push_up": 0.55, "zoom_through": 0.6,
             "cube": 0.75, "shape": 0.65, "diamond": 0.65}
TRANS_SFX = {"push": "whoosh", "push_up": "whoosh", "zoom_through": "whoosh", "cube": "whoosh", "shape": "whoosh",
             "diamond": "whoosh", "flash": "thump"}


def find_chrome():
    for c in (os.environ.get("CHROME"), "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium",
              "/usr/bin/chromium-browser", shutil.which("google-chrome") or "", shutil.which("chromium") or ""):
        if c and os.path.exists(c):
            return c
    return None  # Playwright's own bundled Chromium, if installed


def esc(s):
    # a hyphen between two words (ו-ERP, e-commerce) must not become a line break
    return _html.escape(re.sub(r"(?<=[^\W\d_])-(?=\S)|(?<=\S)-(?=[^\W\d_])", "‑", str(s)), quote=True)


def hexc(c):
    return "#%02x%02x%02x" % tuple(int(v) for v in c[:3])


def rgba(c, a):
    return f"rgba({int(c[0])},{int(c[1])},{int(c[2])},{a})"


def words_html(text, cls="w", hl=(), hl_digits=False):
    """Wrap each word in a span (for word-by-word reveals); words containing a highlight term get class hl."""
    out = []
    for w in str(text).split():
        hot = any(h and h in w for h in hl) or (hl_digits and any(ch.isdigit() for ch in w))
        out.append(f'<span class="{cls}{" hl" if hot else ""}">{esc(w)}</span>')
    return " ".join(out)


class P:
    """Layout and style values of one render, shared by the scene builders."""

    def __init__(self, ctx, workdir):
        self.ctx, self.wd = ctx, workdir
        self.W, self.H, self.U = ctx.W, ctx.H, ctx.U
        self.top, self.bot, self.cy = ctx.top, ctx.bot, ctx.cy
        self.c = ctx.c
        self.land = ctx.land
        self.n_assets = 0

    def u(self, v):
        return f"{v * self.U:.2f}px"

    def asset(self, img, name=None, quality=93):
        """Save a PIL image into the work folder and return its file URL."""
        self.n_assets += 1
        name = name or f"a{self.n_assets:03d}"
        ext = "png" if img.mode == "RGBA" else "jpg"
        p = os.path.join(self.wd, "web", f"{name}.{ext}")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if ext == "png":
            img.save(p)
        else:
            img.convert("RGB").save(p, quality=quality)
        return "file://" + os.path.abspath(p)

    def src(self, path):
        """File URL of a brief media path (relative to the brief folder)."""
        return "file://" + os.path.abspath(path)

    def still(self, spec):
        """Image path for a media spec: photos as they are; for a video, one frame (spec start, else 35% in)."""
        spec = pe.norm_clip(spec)
        src = spec["src"]
        if pe.is_photo(src):
            return src
        dur = pe.probe(src)[2] or 1.0
        at = float(spec.get("start", dur * 0.35))
        p = os.path.join(self.wd, "web", "still_" + hashlib.md5(f"{os.path.abspath(src)}|{at}".encode()).hexdigest()[:12] + ".jpg")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not os.path.exists(p):
            subprocess.run([pe.FFMPEG, "-v", "error", "-y", "-ss", f"{at:.3f}", "-i", src, "-frames:v", "1", "-q:v", "2", p])
        if not os.path.exists(p):
            raise SystemExit(f"[web] could not read a frame from {src}")
        return p


# ----------------------------------------------------------------- runtime (JS)
RUNTIME = r"""
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const prog = (t, t0, d) => d <= 0 ? (t >= t0 ? 1 : 0) : clamp((t - t0) / d);
const lerp = (a, b, p) => a + (b - a) * p;
const expoOut = p => p >= 1 ? 1 : 1 - Math.pow(2, -10 * p);
const cubicOut = p => 1 - Math.pow(1 - p, 3);
const quintOut = p => 1 - Math.pow(1 - p, 5);
const cubicIn = p => p * p * p;
const cubicInOut = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
const sineInOut = p => -(Math.cos(Math.PI * p) - 1) / 2;
const backOut = (p, s = 1.2) => 1 + (s + 1) * Math.pow(p - 1, 3) + s * Math.pow(p - 1, 2);
const $ = id => document.getElementById(id);
const U = window.__U;

// word-by-word reveal: rise from below with a slight 3D tilt, out of a blur
function reveal(el, t, t0, o = {}) {
  if (!el) return;
  const step = o.step ?? 0.07, dur = o.dur ?? 0.65, rise = (o.rise ?? 0.55), out = o.out;
  [...el.querySelectorAll('.w')].forEach((s, i) => {
    const p = prog(t, t0 + i * step, dur), e = expoOut(p);
    let a = clamp(p * 1.8), y = (1 - e) * rise, rx = (1 - e) * (o.tilt ?? 55), b = (1 - cubicOut(p)) * (o.blur ?? 14);
    if (out !== undefined) {
      const q = cubicInOut(prog(t, out + i * 0.035, 0.35));
      a *= 1 - q; y -= q * 0.4; b += q * 10;
    }
    s.style.opacity = a;
    s.style.transform = `translateY(${y}em) rotateX(${rx}deg)`;
    s.style.filter = b > 0.3 ? `blur(${b * U}px)` : 'none';
  });
}
// fade/slide a block in (and optionally out)
function enter(el, t, t0, o = {}) {
  if (!el) return 0;
  const p = prog(t, t0, o.dur ?? 0.7), e = (o.ease ?? expoOut)(p);
  let a = clamp(p * 2), y = (1 - e) * (o.y ?? 40) * U, s = lerp(o.s ?? 0.96, 1, e);
  if (o.out !== undefined) { const q = cubicInOut(prog(t, o.out, o.outDur ?? 0.35)); a *= 1 - q; y -= q * 20 * U; }
  el.style.opacity = a;
  el.style.transform = `${o.base ?? ''} translateY(${y}px) scale(${s})`;
  return e;
}
function typeText(el, text, t, t0, cps) {
  const n = Math.floor(clamp((t - t0) * cps, 0, text.length));
  el.textContent = text.slice(0, n);
  return n >= text.length;
}
function sheen(el, t, t0, dur = 0.9) {
  if (!el) return;
  const p = prog(t, t0, dur);
  el.style.opacity = p > 0 && p < 1 ? 1 : 0;
  el.style.transform = `translateX(${lerp(-130, 130, sineInOut(p))}%) skewX(-18deg)`;
}

// ---- transitions between scene layers (p: 0..1)
function trans(kind, p, a, b) {
  const e = cubicInOut(p);
  if (kind === 'fade') { b.style.opacity = e; }
  else if (kind === 'blur') { a.style.filter = `blur(${24 * e * U}px)`; a.style.opacity = 1 - e; b.style.opacity = e; b.style.transform = `scale(${lerp(1.04, 1, e)})`; }
  else if (kind === 'flash') { b.style.opacity = p > 0.5 ? 1 : 0; $('flash').style.opacity = 1 - Math.abs(p - 0.5) * 2; }
  else if (kind === 'push') { a.style.transform = `translateX(${100 * e}%)`; b.style.transform = `translateX(${-100 + 100 * e}%)`; }
  else if (kind === 'push_up') { a.style.transform = `translateY(${-100 * e}%)`; b.style.transform = `translateY(${100 - 100 * e}%)`; }
  else if (kind === 'zoom_through') {
    a.style.transform = `scale(${1 + 0.6 * e})`; a.style.opacity = 1 - clamp((p - 0.15) / 0.55);
    b.style.transform = `scale(${lerp(0.82, 1, quintOut(p))})`; b.style.opacity = clamp((p - 0.2) / 0.5);
  }
  else if (kind === 'cube') {
    const o = `50% 50% ${-window.__W / 2}px`;
    a.style.transformOrigin = o; b.style.transformOrigin = o;
    a.style.transform = `rotateY(${90 * e}deg)`; b.style.transform = `rotateY(${-90 + 90 * e}deg)`;
    a.style.filter = `brightness(${1 - 0.5 * e})`; b.style.filter = `brightness(${0.5 + 0.5 * e})`;
  }
  else if (kind === 'shape' || kind === 'diamond') {
    const r = 120 * e;
    b.style.clipPath = kind === 'shape' ? `circle(${r * 0.75}% at 50% 50%)`
      : `polygon(50% ${50 - r}%, ${50 + r}% 50%, 50% ${50 + r}%, ${50 - r}% 50%)`;
    const ring = $('ring'); ring.style.opacity = p < 0.98 ? 1 : 0;
    const R = Math.hypot(window.__W, window.__H) * 0.75 * e * 1.2 / 2;
    ring.style.width = ring.style.height = 2 * R + 'px';
    ring.style.borderRadius = kind === 'shape' ? '50%' : '0';
    ring.style.transform = `translate(-50%, -50%) ${kind === 'diamond' ? 'rotate(45deg) scale(0.71)' : ''}`;
  }
}
function resetLayer(el) {
  el.style.transform = ''; el.style.opacity = ''; el.style.filter = ''; el.style.clipPath = ''; el.style.transformOrigin = '';
}

window.seek = function (t) {
  window.__t = t;
  const S = window.__scenes;
  if (window.__bg) window.__bg(t);
  $('flash').style.opacity = 0; $('ring').style.opacity = 0;
  let i = S.length - 1;
  for (let k = 0; k < S.length; k++) if (t < S[k].t0 + S[k].d) { i = k; break; }
  const cur = S[i], lt = t - cur.t0;
  const tr = cur.tr, td = cur.td;
  const inTrans = i > 0 && tr !== 'cut' && lt < td;
  for (let k = 0; k < S.length; k++) {
    const on = k === i || (inTrans && k === i - 1);
    S[k].el.style.display = on ? 'block' : 'none';
    if (on) resetLayer(S[k].el);
  }
  if (inTrans) {
    const pv = S[i - 1];
    pv.fn(t - pv.t0, pv.d);
    cur.fn(lt, cur.d);
    trans(tr, clamp(lt / td), pv.el, cur.el);
    pv.el.style.zIndex = 1; cur.el.style.zIndex = 2;
  } else {
    cur.el.style.zIndex = 2;
    cur.fn(lt, cur.d);
  }
  const cl = $('cornerlogo');
  if (cl) cl.style.opacity = cur.corner ? clamp(lt / 0.5) * 0.92 : 0;
  const C = window.__caps || [];
  for (let k = 0; k < C.length; k++) {
    const c = C[k], el = $('cap' + k);
    const on = t >= c.s && t < c.e;
    el.style.display = on ? 'inline-block' : 'none';
    if (!on) continue;
    const p = clamp((t - c.s) / 0.14), q = clamp((c.e - t) / 0.1);
    el.style.opacity = Math.min(p, q);
    el.style.transform = `translateY(${(1 - expoOut(p)) * 18 * U}px) scale(${lerp(0.94, 1, expoOut(p))})`;
    el.querySelectorAll('.cw').forEach((w, j) => {
      const [, a, b] = c.w[j] || [0, c.s, c.e];
      w.classList.toggle('on', t >= a - 0.02);
      w.classList.toggle('now', t >= a - 0.02 && t < b + 0.05);
    });
  }
  return i;
};

// shrink any .fit text that overflows its box (runs once, after fonts load)
window.__fit = function () {
  document.querySelectorAll('.fit').forEach(el => {
    const max = parseFloat(el.dataset.maxw || el.clientWidth);
    let fs = parseFloat(getComputedStyle(el).fontSize), n = 0;
    while (el.scrollWidth > max + 1 && n++ < 40) { fs *= 0.95; el.style.fontSize = fs + 'px'; }
  });
};
// layout check: text elements that leave the frame or the safe area at a given time
window.__layout = function (t, top, bot) {
  window.seek(t);
  const out = [];
  document.querySelectorAll('.txt').forEach(el => {
    const sc = el.closest('.scene');
    if (!sc || sc.style.display === 'none' || parseFloat(getComputedStyle(el).opacity) < 0.5) return;
    const r = el.getBoundingClientRect();
    if (r.width < 2) return;
    if (r.left < -2 || r.right > window.__W + 2) out.push(['error', el.textContent.trim().slice(0, 40), 'leaves the frame']);
    else if (r.top < top - 4 || r.bottom > bot + 4) out.push(['warn', el.textContent.trim().slice(0, 40), 'outside the safe area']);
  });
  return out;
};
"""

BASE_CSS = r"""
html, body { margin: 0; width: __W__px; height: __H__px; overflow: hidden; background: var(--bg); }
#stage { position: absolute; inset: 0; overflow: hidden; direction: rtl; color: var(--text); font-family: var(--f-body); }
#bgl { position: absolute; inset: 0; }
.bgbase { position: absolute; inset: 0; background: var(--bggrad); }
.glow { position: absolute; border-radius: 50%; will-change: transform; }
.grain { position: absolute; inset: 0; background-image: url(__GRAIN__); opacity: var(--grain); pointer-events: none; }
.vig { position: absolute; inset: 0; background: radial-gradient(ellipse 78% 66% at 50% 48%, transparent 52%, var(--vig) 100%); }
#scenes { position: absolute; inset: 0; perspective: calc(2200px * var(--u)); }
.scene { position: absolute; inset: 0; display: none; backface-visibility: hidden; }
.space { position: absolute; inset: 0; perspective: calc(2200px * var(--u)); perspective-origin: 50% 45%; }
.w { display: inline-block; will-change: transform, opacity, filter; transform-origin: 50% 100%; }
.hl { color: var(--primary); }
.persp { perspective: calc(900px * var(--u)); }
#flash { position: absolute; inset: 0; background: #fff; opacity: 0; z-index: 50; pointer-events: none; }
#ring { position: absolute; left: 50%; top: 50%; width: 10px; height: 10px; border: calc(10px * var(--u)) solid var(--primary);
  box-shadow: 0 0 calc(40px * var(--u)) var(--primary); opacity: 0; z-index: 40; pointer-events: none; box-sizing: border-box; }
#cornerlogo { position: absolute; left: calc(64px * var(--u)); top: calc(var(--top) - 120px * var(--u)); height: calc(84px * var(--u));
  z-index: 30; opacity: 0; }
.grad .w, .grad:not(:has(.w)) { background: linear-gradient(180deg, var(--hi) 0%, var(--primary) 45%, var(--primary2) 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent; }
#caps { position: absolute; left: 5%; right: 5%; z-index: 36; display: flex; justify-content: center; pointer-events: none;
  transform: translateY(-50%); }
.capbox { display: none; padding: .26em .62em .32em; border-radius: .42em; background: rgba(10,12,22,.9);
  box-shadow: 0 calc(18px*var(--u)) calc(44px*var(--u)) rgba(0,0,0,.45), inset 0 0 0 1px rgba(255,255,255,.12);
  font-family: 'R-heavy'; font-weight: 800; line-height: 1.12; color: #fff; text-align: center; direction: rtl;
  text-wrap: balance; max-width: 100%; will-change: transform, opacity; }
.capbox .cw { display: inline-block; opacity: .5; }
.capbox .cw.on { opacity: 1; }
.capbox .cw.now { color: var(--primary); }
.sheen { position: absolute; top: -20%; bottom: -20%; width: 34%; left: 33%; opacity: 0; pointer-events: none;
  background: linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,.38), rgba(255,255,255,0)); }
"""


def grain_png(P):
    rng = np.random.default_rng(11)
    n = (rng.random((256, 256)) * 255).astype(np.uint8)
    im = Image.fromarray(n, "L").convert("RGBA")
    im.putalpha(Image.fromarray((rng.random((256, 256)) * 120).astype(np.uint8), "L"))
    return P.asset(im, "grain")


def fonts_css(ctx):
    out = []
    for role in ("display", "heavy", "body", "mono", "stamp"):
        name, wt = ctx.ts.get(role, ctx.ts["heavy"])
        fp = pe.font_path(name)
        out.append(f'@font-face {{ font-family: "R-{role}"; src: url("file://{os.path.abspath(fp)}"); font-weight: 100 900; }}')
        out.append(f".f-{role} {{ font-family: 'R-{role}', sans-serif; font-weight: {wt or 700}; }}")
    return "\n".join(out)


def root_css(P):
    c, ctx = P.c, P.ctx
    bg = c["bg"]
    light = ctx.light
    lift = tuple(min(255, int(v + (40 if not light else 10))) for v in bg)
    deep = tuple(max(0, int(v * (0.45 if not light else 0.92))) for v in bg)
    v = {"--u": f"{P.U:.4f}", "--W": f"{P.W}px", "--H": f"{P.H}px", "--top": f"{P.top}px", "--bot": f"{P.bot}px",
         "--bg": hexc(bg), "--primary": hexc(c["primary"]), "--primary2": hexc(c["primary2"]), "--hi": hexc(c["hi"]),
         "--accent": hexc(c["accent"]), "--text": hexc(c["text"]), "--muted": hexc(c.get("muted", c["text"])),
         "--cta": hexc(c["cta"]), "--ink": "#141018" if not light else "#141018",
         "--bggrad": f"radial-gradient(120% 75% at 50% 14%, {hexc(lift)} 0%, {hexc(bg)} 52%, {hexc(deep)} 100%)",
         "--grain": "0.07" if not light else "0.05", "--vig": "rgba(0,0,0,.55)" if not light else "rgba(0,0,0,.12)",
         "--f-body": "'R-body', sans-serif"}
    return ":root { " + "; ".join(f"{k}: {val}" for k, val in v.items()) + "; }"


def bg_layer(P):
    """Shared animated background: soft colour glows drifting over the brand gradient (no CSS blur: cheap to render)."""
    c, W, H = P.c, P.W, P.H
    glows = [("g1", c["primary"], 0.30, -0.35 * W, 0.12 * H, 1.0 * W), ("g2", c["primary2"], 0.34, 0.45 * W, 0.52 * H, 0.95 * W),
             ("g3", c["accent"], 0.16, 0.1 * W, -0.25 * H, 0.8 * W)]
    h = ['<div id="bgl"><div class="bgbase"></div>']
    for gid, col, a, x, y, s in glows:
        h.append(f'<div class="glow" id="{gid}" style="left:{x:.0f}px;top:{y:.0f}px;width:{s:.0f}px;height:{s:.0f}px;'
                 f'background:radial-gradient(closest-side, {rgba(col, a)}, {rgba(col, a * 0.45)} 45%, {rgba(col, 0)} 100%)"></div>')
    h.append('</div>')
    js = (f"window.__bg = t => {{ $('g1').style.transform = `translate(${{{90 * P.U}*Math.sin(t*.31)}}px, ${{{70 * P.U}*Math.cos(t*.27)}}px)`;"
          f" $('g2').style.transform = `translate(${{{-80 * P.U}*Math.sin(t*.29+1)}}px, ${{{-60 * P.U}*Math.cos(t*.33)}}px)`;"
          f" $('g3').style.transform = `translate(${{{60 * P.U}*Math.cos(t*.23)}}px, ${{{40 * P.U}*Math.sin(t*.37)}}px)`; }};")
    return "".join(h), js


# ----------------------------------------------------------------- scenes
ICON_X = ('<svg viewBox="0 0 24 24" class="ic"><circle cx="12" cy="12" r="10.5" fill="none" stroke="currentColor" stroke-width="1.8"/>'
          '<path d="M8 8l8 8M16 8l-8 8" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>')
ICON_OK = ('<svg viewBox="0 0 24 24" class="ic"><circle cx="12" cy="12" r="10.5" fill="currentColor" opacity=".18"/>'
           '<circle cx="12" cy="12" r="10.5" fill="none" stroke="currentColor" stroke-width="1.8"/>'
           '<path d="M7 12.5l3.2 3.2L17.2 8.6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>')
ICON_SEND = '<svg viewBox="0 0 24 24"><path d="M4 12l15-7-5 15-2.5-6.2z" fill="currentColor"/></svg>'
ICON_CHAT = ('<svg viewBox="0 0 24 24"><path d="M12 3a9 9 0 0 0-7.8 13.5L3 21l4.6-1.2A9 9 0 1 0 12 3z" fill="none" stroke="currentColor" '
             'stroke-width="2"/><path d="M8.5 9.5c.3 2.6 2.5 4.8 5.1 5.3l1.2-1.3 1.8.8-.4 1.8c-4.2.3-8.3-3.8-8-8l1.8-.4.8 1.8z" fill="currentColor"/></svg>')
ICONS = {"calendar": '<svg viewBox="0 0 24 24"><rect x="3.5" y="5" width="17" height="15" rx="3" fill="none" stroke="currentColor" stroke-width="2"/>'
                     '<path d="M3.5 10h17M8 3v4M16 3v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
         "cart": '<svg viewBox="0 0 24 24"><path d="M3 4h2.5l2.2 10.5h10l2-7.5H7" fill="none" stroke="currentColor" stroke-width="2" '
                 'stroke-linejoin="round"/><circle cx="9.5" cy="19" r="1.6" fill="currentColor"/><circle cx="16.5" cy="19" r="1.6" fill="currentColor"/></svg>',
         "chart": '<svg viewBox="0 0 24 24"><path d="M4 20V10M10 20V4M16 20v-7M21 20H3" stroke="currentColor" stroke-width="2.2" '
                  'stroke-linecap="round"/></svg>',
         "people": '<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.5" fill="none" stroke="currentColor" stroke-width="2"/>'
                   '<path d="M2.5 20c.8-3.8 3.4-5.5 6.5-5.5s5.7 1.7 6.5 5.5M16 4.8a3.4 3.4 0 0 1 0 6.4M18 14.8c2 .8 3.2 2.5 3.6 5" '
                   'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
         "web": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/>'
                '<path d="M3 12h18M12 3c3 3.3 3 14.7 0 18M12 3c-3 3.3-3 14.7 0 18" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>'}

SCENE_CSS = r"""
.ic { width: 1em; height: 1em; flex: none; }
.ctag { position: relative; display: inline-flex; align-items: center; gap: .32em; padding: .26em .62em .3em; border-radius: .34em;
  font-family: 'R-heavy'; font-weight: 800; line-height: 1; white-space: nowrap; will-change: transform, opacity; }
.ctag.x { color: color-mix(in srgb, var(--primary2) 45%, #fff); border: calc(3px*var(--u)) solid var(--primary2);
  background: color-mix(in srgb, var(--primary2) 16%, transparent); box-shadow: 0 0 calc(34px*var(--u)) color-mix(in srgb, var(--primary2) 45%, transparent), inset 0 0 calc(24px*var(--u)) color-mix(in srgb, var(--primary2) 22%, transparent); }
.ctag.ok { color: color-mix(in srgb, var(--primary) 30%, #fff); border: calc(3.5px*var(--u)) solid var(--primary);
  background: color-mix(in srgb, var(--primary) 18%, transparent); }
.ctag .strike { position: absolute; right: .55em; left: .55em; top: 52%; height: calc(5px*var(--u)); border-radius: 3px;
  background: currentColor; transform: scaleX(0); transform-origin: 100% 50%; }
.pbar { position: absolute; left: 8%; width: 84%; height: calc(104px*var(--u)); border-radius: calc(52px*var(--u)); background: #fbfbfd;
  box-shadow: 0 calc(24px*var(--u)) calc(60px*var(--u)) rgba(0,0,0,.45); display: flex; align-items: center; direction: rtl;
  padding: 0 calc(40px*var(--u)) 0 calc(18px*var(--u)); box-sizing: border-box; gap: calc(14px*var(--u)); }
.pbar .ptxt { flex: 1; font-family: 'R-heavy'; font-weight: 700; font-size: calc(42px*var(--u)); color: #1d1a29; white-space: nowrap; overflow: hidden; }
.pbar .caret { display: inline-block; width: calc(4px*var(--u)); height: calc(48px*var(--u)); background: var(--primary); vertical-align: middle; margin-right: 2px; }
.pbar .send { width: calc(72px*var(--u)); height: calc(72px*var(--u)); border-radius: 50%; background: var(--primary); color: #0b0d14; display: grid; place-items: center; flex: none; }
.pbar .send svg { width: 46%; height: 46%; transform: scaleX(-1); }
.cap { position: absolute; left: 6%; right: 6%; text-align: center; font-family: 'R-heavy'; font-weight: 800; line-height: 1.12; text-wrap: balance;
  text-shadow: 0 calc(4px*var(--u)) calc(24px*var(--u)) rgba(0,0,0,.45); }

.dev { position: absolute; transform-style: preserve-3d; will-change: transform; }
.phone { position: absolute; inset: 0; transform-style: preserve-3d;
  background: linear-gradient(150deg, #5d6475 0%, #242833 22%, #0b0d12 56%, #2b303b 100%);
  box-shadow: inset 0 0 0 calc(2px*var(--u)) rgba(255,255,255,.18), inset 0 0 0 calc(9px*var(--u)) #06070b,
    0 calc(70px*var(--u)) calc(130px*var(--u)) rgba(0,0,0,.6); }
.pbtn { position: absolute; width: calc(6px*var(--u)); border-radius: 3px; background: linear-gradient(90deg, #4c5260, #1a1d24); }
.screen { position: absolute; overflow: hidden; background: #000; }
.screen .item { position: absolute; inset: 0; overflow: hidden; will-change: transform; }
.screen img { position: absolute; display: block; max-width: none; }
.island { position: absolute; left: 50%; transform: translateX(-50%); background: #000; z-index: 3; }
.glare { position: absolute; inset: 0; z-index: 4; pointer-events: none;
  background: linear-gradient(118deg, rgba(255,255,255,.15) 0%, rgba(255,255,255,.04) 28%, rgba(255,255,255,0) 42%); }
.lid { position: absolute; transform-style: preserve-3d; background: linear-gradient(160deg, #3c4250, #14171d 60%, #262a33);
  box-shadow: inset 0 0 0 calc(2px*var(--u)) rgba(255,255,255,.14), 0 calc(60px*var(--u)) calc(110px*var(--u)) rgba(0,0,0,.55); }
.deck { position: absolute; background: linear-gradient(180deg, #8a909e 0%, #4a4f5b 35%, #23262d 100%);
  clip-path: polygon(4% 0, 96% 0, 100% 100%, 0 100%); }
.slot { position: absolute; background: #04050a; opacity: 0; z-index: 2; }
.pop { position: absolute; overflow: hidden; will-change: transform; opacity: 0; z-index: 5; }
.pop img { width: 100%; height: 100%; display: block; }
.kick { position: absolute; display: flex; align-items: center; gap: calc(18px*var(--u)); font-family: 'R-body'; font-weight: 600;
  letter-spacing: .16em; color: color-mix(in srgb, var(--text) 62%, transparent); white-space: nowrap; }
.kick i { display: block; width: calc(64px*var(--u)); height: calc(2px*var(--u)); background: linear-gradient(90deg, transparent, var(--primary)); }
.ctr { position: absolute; display: flex; align-items: flex-end; gap: calc(10px*var(--u)); direction: ltr; }
.digits { position: relative; overflow: hidden; }
.digits .col { position: absolute; left: 0; top: 0; font-family: 'R-display'; font-weight: 900; letter-spacing: -.03em; will-change: transform;
  background: linear-gradient(180deg, var(--hi) 0%, var(--primary) 45%, var(--primary2) 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
.ctr .tot { font-family: 'R-heavy'; font-weight: 600; color: color-mix(in srgb, var(--text) 45%, transparent); }
.glab { position: absolute; font-family: 'R-display'; font-weight: 800; line-height: 1.06; text-wrap: balance; }
.gtag { position: absolute; display: flex; align-items: center; gap: calc(14px*var(--u)); padding: calc(16px*var(--u)) calc(30px*var(--u));
  border-radius: calc(40px*var(--u)); background: rgba(16,19,30,.86); box-shadow: inset 0 0 0 1px rgba(255,255,255,.16), 0 calc(20px*var(--u)) calc(40px*var(--u)) rgba(0,0,0,.45);
  font-family: 'R-heavy'; font-weight: 700; font-size: calc(32px*var(--u)); white-space: nowrap; color: #fff; z-index: 6; }
.gtag svg { width: calc(30px*var(--u)); height: calc(30px*var(--u)); color: var(--primary); }
.floor { position: absolute; border-radius: 50%; background: radial-gradient(closest-side, rgba(0,0,0,.72), rgba(0,0,0,0)); }

.plane { position: absolute; transform-style: preserve-3d; display: grid; }
.tile { position: relative; overflow: hidden; }
.tile img { width: 100%; height: 100%; object-fit: cover; object-position: 50% 0; display: block; }
.tile::after { content: ''; position: absolute; inset: 0; background: rgba(0,0,0,var(--dim)); }
.scrim { position: absolute; left: 0; right: 0; top: 0; background: linear-gradient(180deg, var(--bg) 0%, color-mix(in srgb, var(--bg) 70%, transparent) 55%, transparent 100%); }
.qcard { position: absolute; left: 7%; right: 7%; padding: calc(34px*var(--u)) calc(40px*var(--u)); border-radius: calc(30px*var(--u));
  background: rgba(22,17,42,.94); box-shadow: inset 0 0 0 calc(2px*var(--u)) color-mix(in srgb, var(--primary2) 55%, transparent), 0 calc(30px*var(--u)) calc(70px*var(--u)) rgba(0,0,0,.55);
  opacity: 0; text-align: right; }

.bcol { position: absolute; left: 7%; right: 7%; display: flex; flex-direction: column; align-items: center; transform-style: preserve-3d; }
.bcard { position: relative; width: 100%; box-sizing: border-box; display: flex; align-items: center; gap: calc(26px*var(--u));
  padding: calc(36px*var(--u)) calc(40px*var(--u)); border-radius: calc(34px*var(--u)); background: #fbf6ec; color: #1a1430; overflow: hidden;
  box-shadow: 0 calc(34px*var(--u)) calc(80px*var(--u)) rgba(0,0,0,.5), inset 0 0 0 calc(2px*var(--u)) #fff; will-change: transform; }
.bcard .btxt { flex: 1; text-align: right; }
.bcard .bt { font-family: 'R-display'; font-weight: 900; line-height: 1.05; }
.bcard .bd { font-family: 'R-body'; font-weight: 500; color: #4e4762; font-size: calc(34px*var(--u)); margin-top: calc(10px*var(--u)); line-height: 1.3; }
.bcard .tags { display: flex; flex-wrap: wrap; gap: calc(10px*var(--u)); margin-top: calc(18px*var(--u)); }
.bcard .tags span { padding: calc(9px*var(--u)) calc(18px*var(--u)); border-radius: calc(20px*var(--u)); background: #1c1630; color: #fff;
  font-family: 'R-heavy'; font-weight: 700; font-size: calc(24px*var(--u)); direction: ltr; }
.bcard .thumb { width: 30%; aspect-ratio: 1 / 1.05; border-radius: calc(22px*var(--u)); overflow: hidden; flex: none; transform: rotate(-5deg);
  box-shadow: 0 calc(16px*var(--u)) calc(36px*var(--u)) rgba(0,0,0,.35); }
.bcard .thumb img { width: 100%; height: 100%; object-fit: cover; object-position: 50% 0; }
.plus { width: calc(76px*var(--u)); height: calc(76px*var(--u)); border-radius: 50%; background: var(--primary); color: #0b0d14; display: grid; place-items: center;
  font: 900 calc(54px*var(--u))/1 'R-heavy'; box-shadow: 0 0 calc(36px*var(--u)) var(--primary); margin: calc(-12px*var(--u)) 0; z-index: 3; position: relative; }

.ccol { position: absolute; left: 6%; right: 6%; display: flex; flex-direction: column; align-items: center; text-align: center; }
.cbtn { position: relative; display: inline-flex; align-items: center; gap: calc(18px*var(--u)); padding: calc(28px*var(--u)) calc(54px*var(--u));
  border-radius: calc(60px*var(--u)); font-family: 'R-heavy'; font-weight: 800; font-size: calc(44px*var(--u)); overflow: hidden; white-space: nowrap;
  box-shadow: 0 calc(24px*var(--u)) calc(60px*var(--u)) rgba(0,0,0,.45); }
.cbtn svg { width: calc(48px*var(--u)); height: calc(48px*var(--u)); }
.ripple { position: absolute; border-radius: 50%; border: calc(4px*var(--u)) solid #fff; opacity: 0; pointer-events: none; }
.logoimg { display: block; object-fit: contain; }
.lring { position: absolute; border-radius: 50%; border: calc(3px*var(--u)) solid var(--primary); opacity: 0; }
.num { font-family: 'R-display'; font-weight: 900; line-height: 1; direction: ltr; }
.rule { display: flex; align-items: center; gap: calc(16px*var(--u)); color: color-mix(in srgb, var(--text) 55%, transparent);
  font-family: 'R-mono'; font-size: calc(22px*var(--u)); letter-spacing: .3em; }
.rule i { display: block; height: 1px; width: calc(120px*var(--u)); background: currentColor; opacity: .7; }
"""


def _sid(i, name):
    return f"s{i}_{name}"


def w_kinetic(sc, P, i):
    W, U = P.W, P.U
    size0 = float(sc.get("size", 150))
    rows, ids = [], []
    for j, ln in enumerate(sc.get("lines", [])):
        d = {"text": ln} if isinstance(ln, str) else dict(ln)
        st = d.get("style", "")
        sz = float(d.get("size", size0 * (0.55 if st == "small" else 1)))
        cls = "grad" if st in ("accent", "grad") else ""
        extra = ""
        if st == "outline":
            extra = f"color:transparent;-webkit-text-stroke:{3 * U:.1f}px var(--text);"
        if st == "muted":
            extra = "color:var(--muted);"
        lid = _sid(i, f"l{j}")
        ids.append(lid)
        rows.append(f'<div id="{lid}" class="f-display fit txt persp {cls}" data-maxw="{W * 0.88:.0f}" '
                    f'style="font-size:{sz * U:.1f}px;line-height:1.04;white-space:nowrap;{extra}">{words_html(d["text"])}</div>')
    box = _sid(i, "k")
    html = (f'<div id="{box}" style="position:absolute;left:0;right:0;top:{P.top}px;height:{P.bot - P.top}px;display:flex;'
            f'flex-direction:column;justify-content:center;align-items:center;gap:{8 * U:.0f}px;text-align:center">{"".join(rows)}</div>')
    st0, stag = float(sc.get("start", 0.06)), max(0.16, float(sc.get("stagger", 0.2)))
    js = (f"(t, d) => {{ {json.dumps(ids)}.forEach((id, j) => reveal($(id), t, {st0} + j * {stag}, {{step: 0.07}}));"
          f" $('{box}').style.transform = `scale(${{1 + 0.035 * cubicInOut(clamp(t / d))}})`; }}")
    return {"html": html, "js": js, "sfx": [(st0 + 0.02, "whoosh", 0.3)]}


def w_title(sc, P, i):
    lines = []
    if sc.get("small"):
        lines.append({"text": sc["small"], "style": "muted", "size": float(sc.get("small_size", 64))})
    if sc.get("big"):
        lines.append({"text": sc["big"], "size": float(sc.get("size", 150))})
    if sc.get("big2"):
        lines.append({"text": sc["big2"], "style": "accent", "size": float(sc.get("size", 150))})
    return w_kinetic(dict(sc, lines=lines), P, i)


def w_contrast(sc, P, i):
    W, U, c = P.W, P.U, P.c
    items = [({"text": it} if isinstance(it, str) else it) for it in sc.get("items", [])]
    per, st = float(sc.get("per", 0.55)), float(sc.get("start", 0.15))
    band = P.bot - P.top
    has_prompt = bool(sc.get("prompt"))
    tags_cy = P.top + band * (0.27 if has_prompt else 0.42)
    tags, t_check = [], None
    for k, it in enumerate(items):
        good = it.get("mark", "x") == "check"
        sz = float(it.get("size", 90 if good else 76))
        ti = st + per * k
        if good and t_check is None:
            t_check = ti
        tags.append(f'<div id="{_sid(i, f"t{k}")}" class="ctag {"ok" if good else "x"}" style="font-size:{sz * U:.1f}px">'
                    f'{ICON_OK if good else ICON_X}<span class="txt">{esc(it["text"])}</span>{"" if good else "<i class=strike></i>"}</div>')
    t_check = t_check if t_check is not None else st + per * len(items)
    html = [f'<div class="persp" style="position:absolute;left:0;right:0;top:{tags_cy:.0f}px;transform:translateY(-50%);display:flex;'
            f'flex-direction:column;align-items:center;gap:{20 * U:.0f}px">{"".join(tags)}</div>']
    sfx = [(st + per * k + 0.02, "thump" if it.get("mark", "x") == "check" else "pop", 0.6 if it.get("mark", "x") == "check" else 0.45)
           for k, it in enumerate(items)]
    js = [f"const T = {json.dumps([st + per * k for k in range(len(items))])}, G = {json.dumps([it.get('mark', 'x') == 'check' for it in items])};",
          f"T.forEach((ti, k) => {{ const el = $('{_sid(i, 't')}' + k); const p = prog(t, ti, 0.6), e = expoOut(p);",
          " let a = clamp(p * 2.2), s = lerp(0.88, 1, e);",
          f" if (!G[k]) {{ const q = cubicInOut(prog(t, {t_check} + 0.12, 0.45)); el.querySelector('.strike').style.transform = `scaleX(${{q}})`; a *= 1 - 0.5 * q; s *= 1 - 0.04 * q; }}",
          " else { const g = Math.exp(-Math.max(0, t - ti - 0.35) / 0.6) * (t > ti ? 1 : 0);",
          "   el.style.boxShadow = `0 0 ${(40 + 50 * g) * U}px color-mix(in srgb, var(--primary) ${45 + 30 * g}%, transparent), inset 0 0 ${26 * U}px color-mix(in srgb, var(--primary) 25%, transparent)`; }",
          " el.style.opacity = a; el.style.transform = `translateY(${(1 - e) * 46 * U}px) rotateX(${-(1 - e) * 70}deg) scale(${s})`;",
          " el.style.filter = p < 1 ? `blur(${(1 - cubicOut(p)) * 10 * U}px)` : 'none'; });"]
    if has_prompt:
        pa, cps = float(sc.get("prompt_at", st + 0.2)), float(sc.get("cps", 14))
        text = sc["prompt"]
        pid = _sid(i, "pb")
        html.append(f'<div id="{pid}" class="pbar" style="top:{P.top + band * 0.66 - 52 * U:.0f}px"><div class="ptxt">'
                    f'<span id="{_sid(i, "pt")}"></span><span class="caret" id="{_sid(i, "pc")}"></span></div>'
                    f'<div class="send">{ICON_SEND}</div></div>')
        js.append(f"enter($('{pid}'), t, {pa}, {{y: 70, s: 0.94}}); const done = typeText($('{_sid(i, 'pt')}'), {json.dumps(text)}, t, {pa + 0.3}, {cps});"
                  f" $('{_sid(i, 'pc')}').style.opacity = (!done || Math.floor(t * 2.2) % 2 === 0) ? 1 : 0;")
        sfx += [(pa + 0.3 + k / cps, "type", 0.35) for k in range(0, len(text), 2) if text[k].strip()]
    hl = sc.get("highlight", ())
    caps = [(sc.get("caption"), 0.2, t_check if sc.get("caption2") else None), (sc.get("caption2"), t_check + 0.05, None)]
    for k, (txt, tin, tout) in enumerate(caps):
        if not txt:
            continue
        cid = _sid(i, f"c{k}")
        html.append(f'<div id="{cid}" class="cap txt persp" style="bottom:{P.H - P.bot + 10 * U:.0f}px;'
                    f'font-size:{float(sc.get("caption_size", 46)) * U:.1f}px">{words_html(txt, hl=hl)}</div>')
        js.append(f"reveal($('{cid}'), t, {tin}, {{step: 0.06{', out: ' + str(tout) if tout is not None else ''}}});")
    return {"html": "".join(html), "js": "(t, d) => { " + "\n".join(js) + " }", "sfx": [(0.0, "whoosh", 0.25)] + sfx}


def _cover_map(iw, ih, sw, sh, fx, fy):
    k = max(sw / iw, sh / ih)
    dw, dh = iw * k, ih * k
    return k, (sw - dw) * fx, (sh - dh) * fy, dw, dh


def w_gallery(sc, P, i):
    W, H, U, c = P.W, P.H, P.U, P.c
    items = [({"src": it} if isinstance(it, str) else dict(it)) for it in sc.get("items", [])]
    n = max(1, len(items))
    per, t_in = float(sc.get("per", 0.7)), 0.45
    kind = sc.get("device", "phone")
    band = P.bot - P.top
    head_h = 215 * U if kind == "phone" else 190 * U
    starts = [0.0] + [t_in + k * per for k in range(1, n)]
    dur = sc.get("_dur", t_in + per * n + 0.6)
    ends = starts[1:] + [dur]
    if kind == "phone":
        ph_h = min(band - head_h + 110 * U, W * 0.52 * 2.1) * float(sc.get("device_scale", 1))
        dw_, dh_ = ph_h / 2.1, ph_h
        bez = dw_ * 16 / 560
        sx, sy, sw, sh = bez, bez, dw_ - 2 * bez, dh_ - 2 * bez
        dcx, dcy = W / 2, P.top + head_h + dh_ / 2
        rad, srad = dw_ * 0.16, dw_ * 0.132
        dev_inner = (f'<div class="phone" style="border-radius:{rad:.0f}px">'
                     f'<div class="pbtn" style="left:-{4 * U:.0f}px;top:{dh_ * .2:.0f}px;height:{dh_ * .07:.0f}px"></div>'
                     f'<div class="pbtn" style="left:-{4 * U:.0f}px;top:{dh_ * .3:.0f}px;height:{dh_ * .12:.0f}px"></div>'
                     f'<div class="pbtn" style="right:-{4 * U:.0f}px;top:{dh_ * .26:.0f}px;height:{dh_ * .16:.0f}px"></div></div>')
        island = f'<div class="island" style="top:{sh * 0.018:.0f}px;width:{sw * 0.28:.0f}px;height:{sw * 0.083:.0f}px;border-radius:{sw * 0.042:.0f}px"></div>'
        fy_def = 0.0
    else:
        dw_ = W * 0.78 * float(sc.get("device_scale", 1))
        lid_h = dw_ * 0.64
        bez = dw_ * 0.03
        sx, sy, sw, sh = bez, bez, dw_ - 2 * bez, lid_h - 2 * bez
        dh_ = lid_h
        # centre laptop + caption in the free band (a short laptop at the top leaves the bottom empty)
        group = lid_h + dw_ * 0.035 + 70 * U + float(sc.get("label_size", 76)) * U * 1.4
        free = max(0.0, band - head_h - group)
        dcx, dcy = W / 2, P.top + head_h + free * 0.42 + lid_h / 2
        rad, srad = dw_ * 0.03, dw_ * 0.012
        dev_inner = f'<div class="lid" style="position:absolute;inset:0;border-radius:{rad:.0f}px"></div>'
        island = ""
        fy_def = 0.5
    scr = [f'<div class="screen" style="left:{sx:.1f}px;top:{sy:.1f}px;width:{sw:.1f}px;height:{sh:.1f}px;border-radius:{srad:.0f}px">']
    pops, js_items = [], []
    for k, it in enumerate(items):
        spec = pe.norm_clip(it["src"])
        src = P.still(spec)
        im = Image.open(src)
        iw, ih = im.size
        fx, fy = spec.get("focus", [0.5, fy_def])
        tall = ih / iw > (sh / sw) * 1.15
        if tall:
            k_, ox, oy, dwi, dhi = sw / iw, 0.0, 0.0, sw, ih * sw / iw
        else:
            k_, ox, oy, dwi, dhi = _cover_map(iw, ih, sw, sh, fx, fy)
        scroll = max(0.0, min(dhi - sh, sh * 0.7)) if tall else 0.0
        scr.append(f'<div class="item" id="{_sid(i, f"i{k}")}"><img src="{P.src(src)}" style="left:{ox:.1f}px;top:{oy:.1f}px;'
                   f'width:{dwi:.1f}px;height:{dhi:.1f}px" id="{_sid(i, f"im{k}")}"></div>')
        pv = it.get("pop")
        if pv is None and sc.get("pop") not in (None, False):
            pv = True
        pop = None
        if pv:
            pd = pv if isinstance(pv, dict) else {}
            box = pd.get("box")
            if not box:
                arr = np.asarray(im.convert("RGB").resize((max(1, int(iw * 688 / max(iw, ih))), max(1, int(ih * 688 / max(iw, ih))))))
                b = pe.pop_box(arr)
                box = [b[0] / arr.shape[1], b[1] / arr.shape[0], b[2] / arr.shape[1], b[3] / arr.shape[0]]
            bx0, by0, bx1, by1 = box
            piece = im.convert("RGB").crop((int(bx0 * iw), int(by0 * ih), int(bx1 * iw), int(by1 * ih)))
            purl = P.asset(piece, f"pop_{i}_{k}")
            px0, py0 = ox + bx0 * dwi, oy + by0 * dhi
            pw_, ph_ = (bx1 - bx0) * dwi, (by1 - by0) * dhi
            rr = float(pd.get("radius", 0.04 * min(bx1 - bx0, by1 - by0))) * dwi
            at = starts[k] + float(pd.get("at", 1.15 if k == 0 else 0.4))
            back = ends[k] - 0.42 if k < n - 1 else 99
            direction = 1 if (bx0 + bx1) / 2 >= 0.5 else -1
            sc_ = float(pd.get("scale", 1.0))
            pops.append(f'<div class="pop" id="{_sid(i, f"p{k}")}" style="left:{sx + px0:.1f}px;top:{sy + py0:.1f}px;width:{pw_:.1f}px;'
                        f'height:{ph_:.1f}px;border-radius:{rr:.1f}px"><img src="{purl}"></div>')
            scr.append(f'<div class="slot" id="{_sid(i, f"q{k}")}" style="left:{px0:.1f}px;top:{py0:.1f}px;width:{pw_:.1f}px;'
                       f'height:{ph_:.1f}px;border-radius:{rr:.1f}px"></div>')
            out_x = min(W * 0.16, (W - dw_) / 2 + pw_ * 0.25) if kind == "phone" else W * 0.05
            pz, py_ = (340 * U if kind == "phone" else 260 * U), -50 * U
            # keep the popped piece inside the frame: projected size/position under the scene perspective
            f = 2200.0 / (2200.0 - pz / U)
            m = 44 * U
            S = sc_ + 0.05
            if pw_ * S * f > W - 2 * m:
                S = (W - 2 * m) / (pw_ * f)
                sc_ = S - 0.05
            half = pw_ * S * f / 2
            cx0 = dcx - dw_ / 2 + sx + px0 + pw_ / 2
            pc = W / 2 + (cx0 + direction * out_x - W / 2) * f
            pc = min(max(pc, m + half), W - m - half)
            dx = (pc - W / 2) / f - cx0 + W / 2
            pop = {"at": at, "back": back, "x": dx, "z": pz,
                   "y": py_, "ry": -direction * 14, "s": sc_, "dir": direction}
        js_items.append({"s": starts[k], "e": ends[k], "scroll": scroll, "pop": pop})
    scr.append(island + '<div class="glare"></div></div>')
    deck = ""
    if kind != "phone":
        deck = (f'<div class="deck" style="left:-{dw_ * 0.06:.0f}px;right:-{dw_ * 0.06:.0f}px;top:{dh_ - 2:.0f}px;height:{dw_ * 0.035:.0f}px;'
                f'border-radius:0 0 {dw_ * 0.02:.0f}px {dw_ * 0.02:.0f}px"></div>')
    dev = (f'<div class="dev" id="{_sid(i, "dev")}" style="left:{dcx - dw_ / 2:.0f}px;top:{dcy - dh_ / 2:.0f}px;width:{dw_:.0f}px;height:{dh_:.0f}px">'
           f'{dev_inner}{"".join(scr)}{deck}{"".join(pops)}</div>')
    floor = (f'<div class="floor" id="{_sid(i, "fl")}" style="left:{dcx - dw_ * 0.6:.0f}px;width:{dw_ * 1.2:.0f}px;'
             f'top:{dcy + dh_ / 2 - 20 * U:.0f}px;height:{dw_ * 0.2:.0f}px;filter:blur({16 * U:.0f}px)"></div>')
    # header: kicker, counter, labels; tags at the device's bottom edge
    hdr = []
    if sc.get("kicker"):
        hdr.append(f'<div class="kick txt" id="{_sid(i, "kk")}" style="right:{80 * U:.0f}px;top:{P.top + 10 * U:.0f}px;'
                   f'font-size:{30 * U:.1f}px"><i></i><span>{esc(sc["kicker"])}</span></div>')
    lh = 128 * U
    col = "<br>".join(f"{k + 1:02d}" for k in range(n))
    hdr.append(f'<div class="ctr" id="{_sid(i, "ct")}" style="left:{76 * U:.0f}px;top:{P.top - 4 * U:.0f}px">'
               f'<div class="digits" style="width:{150 * U:.0f}px;height:{lh:.0f}px"><div class="col" id="{_sid(i, "cc")}" '
               f'style="font-size:{122 * U:.1f}px;line-height:{lh:.0f}px">{col}</div></div>'
               f'<div class="tot" style="font-size:{38 * U:.1f}px;padding-bottom:{20 * U:.0f}px">/ {n:02d}</div></div>')
    lsize = float(sc.get("label_size", 70 if kind == "phone" else 76))
    for k, it in enumerate(items):
        if it.get("label"):
            if kind == "phone":
                pos = f"right:{80 * U:.0f}px;top:{P.top + 52 * U:.0f}px;width:{W * 0.56:.0f}px;text-align:right"
            else:
                pos = f"left:6%;right:6%;top:{dcy + dh_ / 2 + dw_ * 0.035 + 70 * U:.0f}px;text-align:center"
            hdr.append(f'<div class="glab txt persp" id="{_sid(i, f"l{k}")}" style="{pos};font-size:{lsize * U:.1f}px">'
                       f'{words_html(it["label"], hl=it.get("highlight", ()))}</div>')
        if it.get("tag"):
            ic = ICONS.get(it.get("icon", "web"), ICONS["web"])
            ty = dcy + dh_ / 2 - 34 * U if kind == "phone" else dcy + dh_ / 2 - 30 * U
            hdr.append(f'<div class="gtag txt" id="{_sid(i, f"g{k}")}" style="left:50%;top:{ty:.0f}px;opacity:0">{ic}'
                       f'<span>{esc(it["tag"])}</span></div>')
    html = f'<div class="space">{floor}{dev}</div>' + "".join(hdr)
    base_ry = -9 if kind == "phone" else -5
    js = f"""(t, d) => {{
  const I = {json.dumps(js_items)}, n = {n};
  const pe_ = expoOut(prog(t, 0, 1.1));
  const ry = lerp({base_ry - 26}, {base_ry}, pe_) + 3.2 * Math.sin(t * 0.55), rx = lerp(30, {5 if kind == 'phone' else 8}, pe_) + 1.5 * Math.sin(t * 0.42 + 1);
  const dv = $('{_sid(i, 'dev')}');
  dv.style.transform = `translate3d(0, ${{lerp(520, 0, pe_) * U}}px, ${{lerp(-300, 0, pe_) * U}}px) rotateX(${{rx}}deg) rotateY(${{ry}}deg)`;
  dv.style.opacity = clamp(t / 0.35);
  const fl = $('{_sid(i, 'fl')}'); fl.style.opacity = 0.9 * pe_; fl.style.transform = `scaleX(${{0.7 + 0.3 * pe_}})`;
  let cur = 0; for (let k = 0; k < n; k++) if (t >= I[k].s) cur = k;
  for (let k = 0; k < n; k++) {{
    const el = $('{_sid(i, 'i')}' + k), it = I[k];
    const pin = k === 0 ? 1 : cubicInOut(prog(t, it.s, 0.55)), pout = k < n - 1 ? cubicInOut(prog(t, I[k + 1].s, 0.55)) : 0;
    el.style.display = (k === 0 || t >= it.s - 0.01) && pout < 1 ? 'block' : 'none';
    el.style.transform = `translateY(${{(1 - pin) * 100 - pout * 100}}%)`;
    const im = $('{_sid(i, 'im')}' + k);
    const sp = sineInOut(prog(t, it.s + 0.4, Math.max(0.5, it.e - it.s - 0.4)));
    im.style.transform = it.scroll ? `translateY(${{-it.scroll * sp}}px)` : `scale(${{1 + 0.035 * sp}})`;
    const lab = $('{_sid(i, 'l')}' + k); if (lab) reveal(lab, t, it.s + (k === 0 ? 0.45 : 0.2), {{step: 0.06, out: k < n - 1 ? it.e - 0.25 : undefined}});
    const tg = $('{_sid(i, 'g')}' + k); if (tg) enter(tg, t, it.s + (k === 0 ? 0.6 : 0.3), {{y: 24, out: k < n - 1 ? it.e - 0.2 : undefined, base: 'translateX(-50%)'}});
    const P_ = it.pop; if (P_) {{
      const pp = $('{_sid(i, 'p')}' + k), sl = $('{_sid(i, 'q')}' + k);
      const pu = backOut(prog(t, P_.at, 0.8), 0.85), pa = cubicOut(prog(t, P_.at, 0.55)), pb = cubicInOut(prog(t, P_.back, 0.4));
      const e = pu * (1 - pb), ea = pa * (1 - pb);
      pp.style.opacity = (t < P_.at || pb >= 1) ? 0 : 1;
      pp.style.transform = `translate3d(${{P_.x * e}}px, ${{P_.y * e}}px, ${{P_.z * e}}px) rotateY(${{P_.ry * e}}deg) rotateX(${{6 * e}}deg) scale(${{1 + (P_.s - 1 + 0.05) * e}})`;
      pp.style.boxShadow = `0 ${{(30 + 80 * ea) * U}}px ${{(50 + 100 * ea) * U}}px rgba(0,0,0,${{0.12 + 0.48 * ea}}), 0 0 0 1px rgba(255,255,255,${{0.1 * ea}})`;
      sl.style.opacity = 0.55 * ea;
    }}
  }}
  const cc = $('{_sid(i, 'cc')}');
  let ci = 0; for (let k = 1; k < n; k++) ci += cubicInOut(prog(t, I[k].s - 0.05, 0.5));
  cc.style.transform = `translateY(${{-ci * {lh:.2f}}}px)`;
  enter($('{_sid(i, 'ct')}'), t, 0.2, {{y: 20}});
  const kk = $('{_sid(i, 'kk')}'); if (kk) enter(kk, t, 0.12, {{y: 16}});
}}"""
    sfx = [(0.05, "whoosh", 0.45)] + [(starts[k], "click", 0.35) for k in range(1, n)]
    sfx += [(p["at"], "whoosh", 0.25) for p in [x["pop"] for x in js_items] if p]
    return {"html": html, "js": js, "sfx": sfx}


def w_wall(sc, P, i):
    W, H, U = P.W, P.H, P.U
    srcs = [P.still(x) for x in sc.get("images", [])]
    cols, rows = int(sc.get("cols", 6)), int(sc.get("rows", 5))
    tw = W * float(sc.get("tile_w", 0.27))
    th = tw * float(sc.get("tile_ratio", 1.9))
    gap = 18 * U
    pw, ph = cols * (tw + gap) + gap, rows * (th + gap) + gap
    rng = np.random.default_rng(7)
    order = []
    while len(order) < cols * rows and srcs:
        order += list(rng.permutation(len(srcs)))
    tiles = "".join(f'<div class="tile" style="border-radius:{18 * U:.0f}px"><img src="{P.src(srcs[order[k]])}"></div>'
                    for k in range(cols * rows if srcs else 0))
    scale = max(W * 1.45 / pw, H * 1.4 / ph) * 0.62
    plane = (f'<div class="plane" style="--dim:{1 - float(sc.get("wall_dim", 0.6)):.2f};left:{W / 2 - pw / 2:.0f}px;top:{H * 0.56 - ph / 2:.0f}px;'
             f'width:{pw:.0f}px;height:{ph:.0f}px;grid-template-columns:repeat({cols},{tw:.1f}px);grid-auto-rows:{th:.1f}px;gap:{gap:.1f}px;'
             f'padding:{gap:.1f}px;box-sizing:border-box" id="{_sid(i, "pl")}">{tiles}</div>')
    html = [f'<div style="position:absolute;inset:0;perspective:{1800 * U:.0f}px;perspective-origin:50% 40%">{plane}</div>',
            f'<div class="scrim" style="height:{P.top + 420 * U:.0f}px"></div>']
    js = [f"const pl = $('{_sid(i, 'pl')}'), q = t / d;",
          f"pl.style.transform = `translate(${{(q - 0.5) * {W * 0.1:.1f}}}px, ${{(0.5 - q) * {H * 0.16:.1f}}}px) rotateX({float(sc.get('wall_rx', 32))}deg) "
          f"rotateY({float(sc.get('wall_ry', -14))}deg) rotateZ(-6deg) scale({scale:.4f})`; pl.style.opacity = clamp(t / 0.5);"]
    y = P.top + 10 * U
    if sc.get("title"):
        hl = sc.get("title_highlight", "digits")
        tid = _sid(i, "tt")
        html.append(f'<div id="{tid}" class="f-display txt persp" style="position:absolute;left:6%;right:6%;top:{y:.0f}px;text-align:center;'
                    f'font-size:{float(sc.get("title_size", 96)) * U:.1f}px;line-height:1.06;text-wrap:balance;'
                    f'text-shadow:0 {6 * U:.0f}px {30 * U:.0f}px rgba(0,0,0,.6)">'
                    f'{words_html(sc["title"], hl=(() if isinstance(hl, str) else hl), hl_digits=(hl == "digits"))}</div>')
        js.append(f"reveal($('{tid}'), t, 0.15, {{step: 0.07}});")
    if sc.get("sub"):
        sid = _sid(i, "sb")
        html.append(f'<div id="{sid}" class="txt" style="position:absolute;left:8%;right:8%;top:{y + float(sc.get("title_size", 96)) * U * 2.3:.0f}px;'
                    f'text-align:center;font-family:\'R-heavy\';font-size:{44 * U:.1f}px;color:var(--muted)">{esc(sc["sub"])}</div>')
        js.append(f"enter($('{sid}'), t, 0.5, {{y: 20}});")
    quotes = [({"text": q} if isinstance(q, str) else q) for q in sc.get("quotes", [])]
    t_q0, per_q = float(sc.get("quotes_at", 0.9)), float(sc.get("per_quote", 1.9))
    qcy = P.cy + (P.bot - P.cy) * 0.2
    for k, q in enumerate(quotes):
        lab = q.get("label", sc.get("quote_label"))
        qid = _sid(i, f"qq{k}")
        html.append(f'<div class="qcard" id="{qid}" style="top:{qcy:.0f}px">'
                    + (f'<div style="font-family:\'R-heavy\';font-size:{30 * U:.1f}px;color:var(--primary);margin-bottom:{10 * U:.0f}px">{esc(lab)}</div>' if lab else "")
                    + f'<div class="txt" style="font-family:\'R-heavy\';font-size:{float(q.get("size", 48)) * U:.1f}px;line-height:1.25">'
                      f'{words_html(q["text"], hl=q.get("highlight", ()))}</div>'
                    + (f'<div style="font-family:\'R-body\';font-size:{32 * U:.1f}px;color:var(--muted);margin-top:{14 * U:.0f}px">— {esc(q["who"])}</div>' if q.get("who") else "")
                    + '</div>')
        last = k == len(quotes) - 1
        js.append(f"(() => {{ const el = $('{qid}'), t0 = {t_q0 + k * per_q}; const p = prog(t, t0, 0.5), e = backOut(p, 0.9);"
                  f" let a = clamp(p * 2); {'' if last else f'a *= 1 - cubicInOut(prog(t, t0 + {per_q} - 0.2, 0.2));'}"
                  f" el.style.opacity = a; el.style.transform = `translateY(-50%) translateY(${{(1 - e) * 60 * U}}px) scale(${{lerp(0.9, 1, e)}})`; }})();")
    sfx = [(0.05, "whoosh", 0.4)] + [(t_q0 + k * per_q + 0.02, "pop", 0.5) for k in range(len(quotes))]
    return {"html": "".join(html), "js": "(t, d) => { " + "\n".join(js) + " }", "sfx": sfx}


def w_bundle(sc, P, i):
    W, U = P.W, P.U
    items = [it for it in sc.get("items", []) if isinstance(it, dict)][:3]
    parts, ids = [], []
    if sc.get("title"):
        tid = _sid(i, "bt")
        parts.append(f'<div id="{tid}" class="f-display grad txt persp" style="font-size:{float(sc.get("title_size", 90)) * U:.1f}px;'
                     f'line-height:1.05;margin-bottom:{26 * U:.0f}px;text-align:center">{words_html(sc["title"])}</div>')
    for k, it in enumerate(items):
        if k:
            parts.append(f'<div class="plus" id="{_sid(i, f"pl{k}")}">+</div>')
        thumb = ""
        if it.get("image") and os.path.exists(it["image"]):
            thumb = f'<div class="thumb"><img src="{P.src(P.still(it["image"]))}"></div>'
        tags = "".join(f'<span>{esc(tg if isinstance(tg, str) else tg.get("text", ""))}</span>' for tg in it.get("tags", []))
        cid = _sid(i, f"c{k}")
        ids.append(cid)
        parts.append(f'<div class="bcard" id="{cid}"><div class="btxt"><div class="bt txt" style="font-size:{float(it.get("size", 66)) * U:.1f}px">'
                     f'{esc(it.get("title", ""))}</div>' + (f'<div class="bd">{esc(it["text"])}</div>' if it.get("text") else "")
                     + (f'<div class="tags">{tags}</div>' if tags else "") + f'</div>{thumb}<div class="sheen" id="{cid}_sh"></div></div>')
    html = (f'<div class="bcol persp" style="top:{P.cy:.0f}px;transform:translateY(-50%)">{"".join(parts)}</div>')
    js = [f"reveal($('{_sid(i, 'bt')}'), t, 0.1, {{step: 0.07}});" if sc.get("title") else ""]
    for k, cid in enumerate(ids):
        t0 = 0.3 + 0.5 * k
        side = 1 if k % 2 == 0 else -1
        js.append(f"(() => {{ const el = $('{cid}'); const p = prog(t, {t0}, 0.8), e = expoOut(p); el.style.opacity = clamp(p * 2.4);"
                  f" el.style.transform = `translateY(${{(1 - e) * 80 * U}}px) rotateY(${{(1 - e) * {side * 55}}}deg) rotateX(${{(1 - e) * 12}}deg)"
                  f" scale(${{lerp(0.9, 1, e)}})`; sheen($('{cid}_sh'), t, {t0 + 0.75}, 0.9); }})();")
        if k:
            js.append(f"(() => {{ const el = $('{_sid(i, f'pl{k}')}'); const p = prog(t, {t0 - 0.15}, 0.45), e = backOut(p, 1.6);"
                      f" el.style.opacity = clamp(p * 3); el.style.transform = `scale(${{e}}) rotate(${{(1 - e) * -90}}deg)`; }})();")
    sfx = [(0.3 + 0.5 * k + 0.02, "whoosh", 0.35) for k in range(len(ids))] + [(0.3 + 0.5 * k - 0.13, "pop", 0.45) for k in range(1, len(ids))]
    return {"html": html, "js": "(t, d) => { " + "\n".join(js) + " }", "sfx": sfx}


def _logo_url(P):
    lg = P.ctx.logo()
    return P.asset(lg.convert("RGBA"), "logo"), lg.size


def w_cta(sc, P, i):
    W, U, br = P.W, P.U, P.ctx.brand
    parts, js = [], []
    lid = _sid(i, "lg")
    if sc.get("logo", True):
        url, (lw, lh) = _logo_url(P)
        hgt = 170 * U
        wid = min(W * 0.5, hgt * lw / max(1, lh))
        parts.append(f'<div style="position:relative;width:{wid:.0f}px;height:{hgt:.0f}px;margin-bottom:{30 * U:.0f}px" id="{lid}">'
                     f'<div class="lring" id="{lid}_r" style="left:50%;top:50%;width:{hgt * 1.3:.0f}px;height:{hgt * 1.3:.0f}px;'
                     f'margin:-{hgt * 0.65:.0f}px 0 0 -{hgt * 0.65:.0f}px"></div>'
                     f'<img class="logoimg" src="{url}" style="width:100%;height:100%;filter:drop-shadow(0 0 {24 * U:.0f}px '
                     f'color-mix(in srgb, var(--primary) 50%, transparent))"></div>')
        js.append(f"(() => {{ const el = $('{lid}'), p = prog(t, 0.05, 0.9), e = backOut(p, 1.1); el.style.opacity = clamp(p * 2.5);"
                  f" el.style.transform = `scale(${{lerp(0.55, 1, e)}})`; const r = $('{lid}_r'), q = prog(t, 0.25, 1.1);"
                  f" r.style.opacity = (1 - q) * (q > 0 ? 0.9 : 0); r.style.transform = `scale(${{lerp(0.6, 2.2, cubicOut(q))}})`; }})();")
    if sc.get("eyebrow"):
        eid = _sid(i, "ey")
        parts.append(f'<div id="{eid}" class="txt persp" style="font-family:\'R-heavy\';font-weight:700;font-size:{float(sc.get("eyebrow_size", 46)) * U:.1f}px;'
                     f'color:var(--muted);margin-bottom:{14 * U:.0f}px">{words_html(sc["eyebrow"])}</div>')
        js.append(f"reveal($('{eid}'), t, 0.3, {{step: 0.06}});")
    hid = _sid(i, "hd")
    parts.append(f'<div id="{hid}" class="f-display txt persp" style="font-size:{float(sc.get("headline_size", 92)) * U:.1f}px;line-height:1.05;'
                 f'text-wrap:balance;margin-bottom:{44 * U:.0f}px;text-shadow:0 {6 * U:.0f}px {30 * U:.0f}px rgba(0,0,0,.4)">'
                 f'{words_html(sc.get("headline", "לפרטים נוספים"))}</div>')
    js.append(f"reveal($('{hid}'), t, 0.45, {{step: 0.08}});")
    tap = float(sc.get("tap_at", 1.7))
    if sc.get("button", True):
        col = P.c["primary"] if sc.get("button_style") == "primary" else P.c["cta"]
        ink = "#0b0d14" if sum(col) > 380 else "#ffffff"
        icon = ICON_CHAT if sc.get("button_icon", True) else ""
        bid = _sid(i, "bn")
        parts.append(f'<div class="cbtn" id="{bid}" style="background:{hexc(col)};color:{ink}">{icon}<span class="txt">'
                     f'{esc(sc.get("button", "שלחו הודעה בוואטסאפ"))}</span><div class="sheen" id="{bid}_sh"></div>'
                     f'<div class="ripple" id="{bid}_rp" style="left:50%;top:50%;width:{160 * U:.0f}px;height:{160 * U:.0f}px;margin:-{80 * U:.0f}px"></div></div>')
        js.append(f"(() => {{ const el = $('{bid}'), p = prog(t, 0.9, 0.7), e = backOut(p, 1.3); const tp = prog(t, {tap}, 0.5);"
                  f" const press = 1 - 0.06 * Math.sin(Math.PI * clamp(tp * 2)); el.style.opacity = clamp(p * 3);"
                  f" el.style.transform = `scale(${{lerp(0.7, 1, e) * press}})`; sheen($('{bid}_sh'), t, 1.35, 0.9); sheen($('{bid}_sh'), t, ({tap} + 1.6 < d - 0.6) ? {tap} + 1.6 : 99, 0.9);"
                  f" if (t > 1.35 + 0.9 && t < {tap} + 1.6) $('{bid}_sh').style.opacity = 0;"
                  f" const rp = $('{bid}_rp'); rp.style.opacity = tp > 0 && tp < 1 ? 1 - tp : 0; rp.style.transform = `scale(${{lerp(0.3, 4, cubicOut(tp))}})`; }})();")
    phone = sc.get("phone", br.get("phone", ""))
    if phone:
        pid = _sid(i, "ph")
        parts.append(f'<div id="{pid}" class="txt" style="font-family:\'R-heavy\';font-weight:800;font-size:{70 * U:.1f}px;margin-top:{38 * U:.0f}px;'
                     f'direction:ltr;letter-spacing:.02em">{esc(phone)}</div>')
        js.append(f"enter($('{pid}'), t, 1.1, {{y: 24}});")
    site = sc.get("website", br.get("website"))
    if site:
        wid_ = _sid(i, "ws")
        parts.append(f'<div id="{wid_}" class="txt" style="font-family:\'R-body\';font-size:{32 * U:.1f}px;color:var(--muted);margin-top:{12 * U:.0f}px;'
                     f'direction:ltr">{esc(site)}</div>')
        js.append(f"enter($('{wid_}'), t, 1.25, {{y: 18}});")
    box = _sid(i, "cb")
    html = f'<div class="ccol persp" id="{box}" style="top:{P.cy:.0f}px">{"".join(parts)}</div>'
    js.append(f"$('{box}').style.transform = `translateY(-50%) scale(${{1 + 0.025 * sineInOut(clamp(t / d))}})`;")
    sfx = [(0.05, "reveal", 0.7), (0.9, "pop", 0.4), (tap, "click", 0.6)]
    return {"html": html, "js": "(t, d) => { " + "\n".join(js) + " }", "sfx": sfx, "corner": False}


def w_logo(sc, P, i):
    U, br = P.U, P.ctx.brand
    url, (lw, lh) = _logo_url(P)
    hgt = 300 * U
    wid = min(P.W * 0.7, hgt * lw / max(1, lh))
    lid = _sid(i, "lg")
    parts = [f'<div style="position:relative;width:{wid:.0f}px;height:{hgt:.0f}px" id="{lid}"><div class="lring" id="{lid}_r" '
             f'style="left:50%;top:50%;width:{hgt * 1.25:.0f}px;height:{hgt * 1.25:.0f}px;margin:-{hgt * 0.625:.0f}px 0 0 -{hgt * 0.625:.0f}px"></div>'
             f'<img class="logoimg" src="{url}" style="width:100%;height:100%"></div>']
    js = [f"(() => {{ const el = $('{lid}'), p = prog(t, 0.05, 1.0), e = expoOut(p); el.style.opacity = clamp(p * 2);"
          f" el.style.transform = `scale(${{lerp(0.7, 1, e)}})`; el.style.filter = p < 1 ? `blur(${{(1 - e) * 20 * U}}px)` : 'none';"
          f" const r = $('{lid}_r'), q = prog(t, 0.35, 1.2); r.style.opacity = (1 - q) * (q > 0 ? 0.9 : 0);"
          f" r.style.transform = `scale(${{lerp(0.7, 2.4, cubicOut(q))}})`; }})();"]
    name = sc.get("name", br.get("name", ""))
    if name:
        nid = _sid(i, "nm")
        parts.append(f'<div id="{nid}" class="f-display txt persp" style="font-size:{96 * U:.1f}px;margin-top:{40 * U:.0f}px">{words_html(name)}</div>')
        js.append(f"reveal($('{nid}'), t, 0.5, {{step: 0.08}});")
    tag = sc.get("tagline", br.get("tagline"))
    if tag:
        gid = _sid(i, "tg")
        parts.append(f'<div id="{gid}" class="txt persp" style="font-family:\'R-heavy\';font-size:{float(sc.get("tagline_size", 56)) * U:.1f}px;'
                     f'color:var(--muted);margin-top:{14 * U:.0f}px">{words_html(tag)}</div>')
        js.append(f"reveal($('{gid}'), t, 0.75, {{step: 0.06}});")
    html = f'<div class="ccol persp" style="top:{P.cy:.0f}px;transform:translateY(-50%)">{"".join(parts)}</div>'
    return {"html": html, "js": "(t, d) => { " + "\n".join(js) + " }", "sfx": [(0.05, "reveal", 0.8)], "corner": False}


def w_counter(sc, P, i):
    U = P.U
    val = float(sc.get("value", 100))
    dec = int(sc.get("decimals", 0 if val == int(val) else 1))
    cd = float(sc.get("count_dur", 1.3))
    nid = _sid(i, "n")
    parts = [f'<div class="rule"><i></i><span>{esc(sc.get("kicker", ""))}</span><i></i></div>' if sc.get("kicker") else "",
             f'<div class="num grad" style="font-size:{float(sc.get("size", 260)) * U:.1f}px"><span>{esc(sc.get("num_prefix", ""))}</span>'
             f'<span id="{nid}">0</span><span>{esc(sc.get("suffix", ""))}</span></div>']
    if sc.get("prefix"):
        parts.insert(0, f'<div class="txt" style="font-family:\'R-heavy\';font-size:{60 * U:.1f}px;color:var(--muted)" id="{nid}_pf">{esc(sc["prefix"])}</div>')
    if sc.get("label"):
        parts.append(f'<div class="txt persp" id="{nid}_lb" style="font-family:\'R-heavy\';font-weight:800;font-size:{72 * U:.1f}px;margin-top:{10 * U:.0f}px">'
                     f'{words_html(sc["label"])}</div>')
    html = f'<div class="ccol persp" style="top:{P.cy:.0f}px;transform:translateY(-50%)">{"".join(parts)}</div>'
    js = (f"(t, d) => {{ const p = expoOut(prog(t, 0.15, {cd})); $('{nid}').textContent = ({val} * p).toLocaleString('en-US', "
          f"{{minimumFractionDigits: {dec}, maximumFractionDigits: {dec}}}); const pf = $('{nid}_pf'); if (pf) enter(pf, t, 0.05, {{y: 20}});"
          f" reveal($('{nid}_lb'), t, 0.5, {{step: 0.07}}); }}")
    return {"html": html, "js": js, "sfx": [(0.05, "whoosh", 0.35), (0.15 + cd * 0.85, "ding", 0.6)]}


BUILDERS = {"kinetic": w_kinetic, "title": w_title, "contrast": w_contrast, "gallery": w_gallery, "wall": w_wall,
            "bundle": w_bundle, "cta": w_cta, "logo": w_logo, "counter": w_counter, "stat": w_counter, "stats": w_counter}


# ----------------------------------------------------------------- page
def build_page(scenes, brief, ctx, wd):
    P_ = P(ctx, wd)
    css = "\n".join([fonts_css(ctx), root_css(P_), BASE_CSS.replace("__W__", str(P_.W)).replace("__H__", str(P_.H))
                     .replace("__GRAIN__", grain_png(P_)), SCENE_CSS])
    bg_html, bg_js = bg_layer(P_)
    layers, defs = [], []
    for i, sc in enumerate(scenes):
        r = BUILDERS[sc["type"]](sc, P_, i)
        sc["_sfx"] = r["sfx"]
        kind = TRANS_MAP.get(sc.get("transition", "cut"), "fade") if i else "cut"
        td = min(TRANS_DUR.get(kind, 0.45), max(0.2, sc["_dur"] * 0.4)) if kind != "cut" else 0
        layers.append(f'<div class="scene" id="S{i}">{r["html"]}</div>')
        defs.append(f"{{t0: {sc['_t0']:.4f}, d: {sc['_dur']:.4f}, tr: '{kind}', td: {td:.3f}, el: $('S{i}'), corner: "
                    f"{'true' if r.get('corner', True) else 'false'}, fn: {r['js']}}}")
    caps_html, caps_js = "", "[]"
    if ctx.captions:
        vo = brief.get("voiceover") or {}
        size = float(vo.get("caption_size", 64)) * P_.U
        cy = float(vo["caption_y"]) * P_.H if vo.get("caption_y") else P_.bot - size * 1.45 * 0.6
        words = getattr(ctx, "caption_words", None) or [[[w, c["s"], c["e"]] for w in c["text"].split()] for c in ctx.captions]
        boxes = []
        for k, (c, ws) in enumerate(zip(ctx.captions, words)):
            boxes.append(f'<div class="capbox" id="cap{k}">' + " ".join(f'<span class="cw">{esc(w[0])}</span>' for w in ws) + "</div>")
        caps_html = f'<div id="caps" style="top:{cy:.0f}px;font-size:{size:.1f}px">{"".join(boxes)}</div>'
        caps_js = json.dumps([{"s": c["s"], "e": c["e"], "w": ws} for c, ws in zip(ctx.captions, words)], ensure_ascii=False)
    corner = ""
    if ctx.brand.get("corner_logo"):
        url, _ = _logo_url(P_)
        corner = f'<img id="cornerlogo" src="{url}">'
    page = f"""<!doctype html><html dir="rtl" lang="he"><head><meta charset="utf-8"><style>{css}</style></head><body>
<div id="stage">{bg_html}<div id="scenes">{"".join(layers)}</div>{corner}{caps_html}<div id="ring"></div><div class="vig"></div><div class="grain"></div>
<div id="flash"></div></div>
<script>window.__U = {P_.U:.5f}; window.__W = {P_.W}; window.__H = {P_.H};
{RUNTIME}
{bg_js}
window.__scenes = [{",".join(defs)}];
window.__caps = {caps_js};
window.seek(0);
</script></body></html>"""
    path = os.path.join(wd, "web", "index.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(page)
    return path


CHROME_ARGS = ["--no-sandbox", "--allow-file-access-from-files", "--disable-background-networking", "--disable-component-update",
               "--disable-sync", "--no-first-run", "--disable-default-apps", "--metrics-recording-only", "--mute-audio",
               "--font-render-hinting=none", "--force-color-profile=srgb", "--hide-scrollbars"]


class Page:
    """One Chrome page with the timeline loaded."""

    def __init__(self, html, W, H):
        from playwright.sync_api import sync_playwright
        self.pw = sync_playwright().start()
        exe = find_chrome()
        self.br = self.pw.chromium.launch(executable_path=exe, args=CHROME_ARGS) if exe else self.pw.chromium.launch(args=CHROME_ARGS)
        self.pg = self.br.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        self.pg.goto("file://" + os.path.abspath(html))
        self.pg.evaluate("document.fonts.ready")
        self.pg.wait_for_load_state("networkidle")
        self.pg.evaluate("Promise.all([...document.images].map(i => i.decode().catch(() => 0)))")
        self.pg.evaluate("window.__fit()")

    def grab(self, t, png=False):
        self.pg.evaluate(f"window.seek({t:.5f})")
        b = self.pg.screenshot(type="png") if png else self.pg.screenshot(type="jpeg", quality=93)
        return np.asarray(Image.open(io.BytesIO(b)).convert("RGB"))

    def close(self):
        self.br.close()
        self.pw.stop()


def _render_chunk(html, W, H, fps, frames, samples, shutter, out_path, crf):
    pg = Page(html, W, H)
    ff = subprocess.Popen([pe.FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
                           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", out_path],
                          stdin=subprocess.PIPE)
    S = max(1, int(samples))
    offs = [((s + 0.5) / S - 0.5) * shutter for s in range(S)] if S > 1 else [0.0]
    t_last = time.time()
    for n_done, f in enumerate(frames):
        if S == 1:
            fr = pg.grab(f / fps)
        else:
            a = pg.grab(max(0.0, (f + offs[0]) / fps)).astype(np.float32)
            b = pg.grab(max(0.0, (f + offs[-1]) / fps)).astype(np.float32)
            if S == 2 or np.abs(a[::8, ::8] - b[::8, ::8]).mean() < 0.6:
                fr = (a + b) / 2
            else:
                acc = a + b
                for o in offs[1:-1]:
                    acc += pg.grab(max(0.0, (f + o) / fps))
                fr = acc / S
            fr = np.clip(fr + 0.5, 0, 255).astype(np.uint8)
        ff.stdin.write(np.ascontiguousarray(fr).tobytes())
        if time.time() - t_last > 20:
            pe.log(f"[web] {os.path.basename(out_path)}: {n_done + 1}/{len(frames)} frames")
            t_last = time.time()
    ff.stdin.close()
    ff.wait()
    pg.close()


def render_video(html, ctx, n_frames, workers, samples, shutter, wd, crf=17):
    workers = max(1, min(workers, n_frames // 15 or 1))
    chunks = np.array_split(np.arange(n_frames), workers)
    segs, procs = [], []
    for k, ch in enumerate(chunks):
        seg = os.path.join(wd, f"web_seg{k:02d}.mp4")
        segs.append(seg)
        pr = Process(target=_render_chunk, args=(html, ctx.W, ctx.H, ctx.fps, [int(x) for x in ch], samples, shutter, seg, crf))
        pr.start()
        procs.append(pr)
    for pr in procs:
        pr.join()
        if pr.exitcode != 0:
            raise SystemExit("[web] a render worker failed")
    lst = os.path.join(wd, "web_concat.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{os.path.abspath(s)}'\n")
    vid = os.path.join(wd, "video.mp4")
    subprocess.run([pe.FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    for s in segs:
        os.remove(s)
    return vid


def browser_problem():
    """None when Playwright can start Chrome here, else a short reason."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "Playwright is not installed (pip install playwright --break-system-packages)"
    try:
        with sync_playwright() as pw:
            exe = find_chrome()
            br = pw.chromium.launch(executable_path=exe, args=CHROME_ARGS) if exe else pw.chromium.launch(args=CHROME_ARGS)
            br.close()
    except Exception as e:  # no Chrome, missing system libraries, sandbox limits
        return "Chrome could not start (" + (str(e).strip().splitlines() or ["unknown error"])[0][:160] + ")"
    return None


def classic(brief_path, out, fmt, draft, workers, preview, frame_at, workdir, creative, do_qa, plan, why):
    """Render with the classic engine in its premium style (closest look to the web renderer)."""
    if why:
        pe.log(f"[web] {why} - rendering with the classic renderer (premium style)")
    b = json.load(open(brief_path, encoding="utf-8"))
    b.pop("renderer", None)
    b.setdefault("fx", {"style": "premium"})
    tmp = os.path.join(os.path.dirname(os.path.abspath(brief_path)), "." + os.path.basename(brief_path) + ".classic.json")
    json.dump(b, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    try:
        return pe.run(tmp, out, fmt, draft, workers, preview, frame_at, workdir, creative=creative, do_qa=do_qa, plan=plan)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def unsupported(brief):
    return sorted({sc.get("type") for sc in brief.get("scenes", []) if sc.get("type") not in BUILDERS})


def run_web(brief_path, out, fmt, draft, workers, preview, frame_at, workdir=None, creative=None, do_qa=True, plan=False,
            samples=None):
    t_start = time.time()
    brief_path = os.path.abspath(brief_path)
    brief = pe.load_brief(brief_path)
    base_dir = os.path.dirname(os.path.abspath(brief_path))
    os.chdir(base_dir)
    bad = unsupported(brief)
    if bad:
        return classic(brief_path, out, fmt, draft, workers, preview, frame_at, workdir, creative, do_qa, plan,
                       f"the web renderer does not support scene types {', '.join(bad)} yet")
    if plan:
        return pe.run(brief_path, out, fmt, draft, workers, preview, frame_at, workdir, creative=creative, do_qa=do_qa, plan=True)
    prob = browser_problem()
    if prob:
        return classic(brief_path, out, fmt, draft, workers, preview, frame_at, workdir, creative, do_qa, plan, prob)
    errs, warns = pe.validate(brief)
    for w_ in warns:
        pe.log("[warn] " + w_)
    if errs:
        for e_ in errs:
            pe.log("[error] " + e_)
        raise SystemExit(2)
    brief.setdefault("fx", {"style": "premium"})
    ctx = pe.Ctx(brief, fmt, draft)
    stem = os.path.splitext(out)[0]
    workdir = workdir or stem + "_work"
    os.makedirs(workdir, exist_ok=True)
    try:
        scenes = pe.plan_with_narration(brief, ctx, workdir, base_dir)
    except pe.TTSError as e:
        pe.log(f"[error] narration: {e}")
        raise SystemExit(2)
    total = sum(s["_dur"] for s in scenes)
    pe.log(f"[plan] {len(scenes)} scenes, {total:.1f}s, {ctx.W}x{ctx.H}@{ctx.fps} (web renderer {WEB_VERSION})")
    for i, s in enumerate(scenes):
        pe.log(f"  {i:02d} {s['_t0']:5.2f}s +{s['_dur']:.2f}s {s['type']:<12} {TRANS_MAP.get(s.get('transition'), 'fade') if i else 'cut'}")
    html = build_page(scenes, brief, ctx, workdir)
    if frame_at is not None:
        pg = Page(html, ctx.W, ctx.H)
        for fa in [float(x) for x in str(frame_at).split(",") if x.strip()]:
            p = f"{stem}_frame_{fa:.2f}.png"
            Image.fromarray(pg.grab(fa, png=True)).save(p)
            print(p)
        pg.close()
        return
    if preview:
        pg = Page(html, ctx.W, ctx.H)
        tw = 270 if not ctx.land else 400
        thumbs = []
        for i, s in enumerate(scenes):
            for q in (0.5, 0.97):
                im = Image.fromarray(pg.grab(s["_t0"] + s["_dur"] * q)).resize((tw, int(tw * ctx.H / ctx.W)))
                pe.ImageDraw.Draw(im).text((8, 6), f"{i} {s['type']} {s['_t0'] + s['_dur'] * q:.1f}s", fill=(255, 255, 0), font=pe._label_font())
                thumbs.append(im)
        pg.close()
        cols = 8 if not ctx.land else 4
        rows = math.ceil(len(thumbs) / cols)
        sheet = Image.new("RGB", (cols * tw, rows * thumbs[0].height), (30, 30, 30))
        for j, im in enumerate(thumbs):
            sheet.paste(im, ((j % cols) * tw, (j // cols) * im.height))
        p = stem + "_preview.jpg"
        sheet.save(p, quality=88)
        print(p)
        return
    n_frames = sum(s["_n"] for s in scenes)
    S = int(samples or brief.get("motion_blur", 1 if draft else 4))
    t0 = time.time()
    vid = render_video(html, ctx, n_frames, workers, S, float(brief.get("shutter", 0.5)), workdir)
    pe.log(f"[web] {n_frames} frames in {time.time() - t0:.0f}s ({S} motion-blur samples)")
    wav = os.path.join(workdir, "mix.wav")
    pe.build_audio(brief, scenes, ctx, wav)
    tmp = stem + ".tmp.mp4"
    subprocess.run([pe.FFMPEG, "-y", "-v", "error", "-i", vid, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out)
    if brief.get("music_free_version"):
        b2 = dict(brief)
        b2.pop("music", None)
        wav2 = os.path.join(workdir, "mix_nomusic.wav")
        pe.build_audio(b2, scenes, ctx, wav2)
        nm = stem + "_no_music.mp4"
        subprocess.run([pe.FFMPEG, "-y", "-v", "error", "-i", vid, "-i", wav2, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                        "-shortest", "-movflags", "+faststart", nm], check=True)
        print(nm)
    # cover + layout check in one browser session
    pg = Page(html, ctx.W, ctx.H)
    ci = min(len(scenes) - 1, int(brief.get("cover_scene", 0)))
    Image.fromarray(pg.grab(scenes[ci]["_t0"] + scenes[ci]["_dur"] * 0.7, png=True)).save(stem + "_cover.jpg", quality=92)
    errs_l, warns_l = [], []
    for i, s in enumerate(scenes):
        for kind, txt, why in pg.pg.evaluate(f"window.__layout({s['_t0'] + s['_dur'] * 0.85:.3f}, {ctx.top}, {ctx.bot})"):
            (errs_l if kind == "error" else warns_l).append(f"scene {i} ({s['type']}): '{txt}' {why}")
    pg.close()
    print(out)
    rep = None
    if do_qa and brief.get("qa", True):
        pe.layout_issues = lambda sc_, cx_: (errs_l, warns_l)
        rep = pe.qa(out, brief, scenes, ctx, creative, stem)
        pe.log(f"[qa] automatic {rep['auto_points']}/75" + (f", total {rep['score']}/100" if rep.get("score") is not None else
                                                             " (creative review pending)") +
               f", {len(rep['errors'])} errors, {len(rep['warnings'])} warnings -> {stem}_qa.md")
    try:
        pe.log_run(brief_path, out, scenes, ctx, rep, time.time() - t_start)
    except Exception as ex:
        pe.log(f"[log] could not write the production log: {ex}")


if __name__ == "__main__":
    import argparse
    if sys.argv[1:] == ["--check"]:
        prob = browser_problem()
        print(f"web renderer {WEB_VERSION}: " + (f"NOT ready - {prob}" if prob else f"ready (Chrome: {find_chrome() or 'Playwright Chromium'})"))
        sys.exit(1 if prob else 0)
    ap = argparse.ArgumentParser(description="promo-reel-maker web renderer (python3 promo_web.py --check tests Chrome)")
    ap.add_argument("brief")
    ap.add_argument("--out")
    ap.add_argument("--format", default=None)
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--frame")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--samples", type=int)
    a = ap.parse_args()
    b = pe.load_brief(a.brief)
    fmt = a.format or b.get("format", "9x16")
    o = a.out or b.get("out", "promo.mp4")
    if a.draft:
        o = os.path.splitext(o)[0] + "_draft.mp4"
    run_web(os.path.abspath(a.brief), o, fmt, a.draft, a.workers, a.preview, a.frame, samples=a.samples)
