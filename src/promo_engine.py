#!/usr/bin/env python3
"""promo_engine.py - branded short-form promo videos (Hebrew/RTL first) from a JSON brief.
Usage:
  python3 promo_engine.py brief.json [--out out.mp4] [--format 9x16|1x1|4x5|16x9]
                          [--preview] [--frame SECONDS] [--draft] [--workers N]
Needs: python3, numpy, Pillow (with raqm for RTL; else pip install python-bidi), ffmpeg.
"""
import argparse, glob, hashlib, json, math, os, re, shutil, subprocess, sys, time, wave
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

VERSION = "4.1.0"
SEED_SALT = "3.0.0"  # frozen: keeps random choices stable across engine versions
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
SR = 48000
RAQM = features.check("raqm")
if not RAQM:
    try:
        from bidi.algorithm import get_display
    except Exception:
        try:
            from bidi import get_display
        except Exception:
            get_display = lambda s: s[::-1]

FORMATS = {"9x16": (1080, 1920), "1x1": (1080, 1080), "4x5": (1080, 1350), "16x9": (1920, 1080)}
THEMES = {
    "gold":     dict(bg="#0F0E0C", primary="#F2C14E", primary2="#A8701A", hi="#FFF0C2", accent="#E0252B", text="#FFFFFF", muted="#D9CFBC", cta="#25D366"),
    "fire":     dict(bg="#140805", primary="#FF8A1E", primary2="#D8290B", hi="#FFE0A8", accent="#FFD000", text="#FFFFFF", muted="#F3D5C8", cta="#25D366"),
    "electric": dict(bg="#06122A", primary="#3FE0FF", primary2="#1E5BFF", hi="#D8FAFF", accent="#FF3D71", text="#FFFFFF", muted="#BFD3F2", cta="#25D366"),
    "fresh":    dict(bg="#07140D", primary="#B9F23F", primary2="#22A85A", hi="#F0FFD0", accent="#FF5A36", text="#FFFFFF", muted="#CDE8D2", cta="#25D366"),
    "royal":    dict(bg="#140A26", primary="#FF77DD", primary2="#7B3FF2", hi="#FFE3F7", accent="#FFD166", text="#FFFFFF", muted="#E2D4F7", cta="#25D366"),
    "neon":     dict(bg="#120B24", primary="#FF8A1F", primary2="#8B5CF6", hi="#FFC680", accent="#C4A1FF", text="#FFFFFF", muted="#B8AED6", cta="#25D366"),
    "tech":     dict(bg="#05070B", primary="#53E4FF", primary2="#8C6CFF", hi="#9AF1FF", accent="#D7C4A0", text="#F5F8FB", muted="#9AA7B7", cta="#25D366"),
    "clean":    dict(bg="#F3F5F9", primary="#1F6FEB", primary2="#0A3A8C", hi="#8FC2FF", accent="#E5484D", text="#0D1321", muted="#46536A", cta="#25D366"),
}
GF = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
FONT_FILES = {
    "rubik": "rubik/Rubik[wght].ttf", "heebo": "heebo/Heebo[wght].ttf", "secular": "secularone/SecularOne-Regular.ttf",
    "frank": "frankruhllibre/FrankRuhlLibre[wght].ttf", "assistant": "assistant/Assistant[wght].ttf",
    "rubikdirt": "rubikdirt/RubikDirt-Regular.ttf", "suez": "suezone/SuezOne-Regular.ttf",
    "karantina": "karantina/Karantina-Bold.ttf", "fredoka": "fredoka/Fredoka[wdth,wght].ttf",
    "varela": "varelaround/VarelaRound-Regular.ttf",
    "notosans": "notosanshebrew/NotoSansHebrew[wdth,wght].ttf", "geistmono": "geistmono/GeistMono[wght].ttf",
    "geist": "geist/Geist[wght].ttf",
}
TYPESETS = {
    "bold":      dict(display=("rubik", 900), heavy=("heebo", 800), body=("heebo", 600), stamp=("rubikdirt", 0)),
    "classic":   dict(display=("secular", 0), heavy=("heebo", 800), body=("heebo", 600), stamp=("rubikdirt", 0)),
    "condensed": dict(display=("karantina", 0), heavy=("heebo", 800), body=("heebo", 600), stamp=("rubikdirt", 0)),
    "elegant":   dict(display=("frank", 900), heavy=("assistant", 800), body=("assistant", 600), stamp=("frank", 900)),
    "playful":   dict(display=("fredoka", 700), heavy=("fredoka", 600), body=("varela", 0), stamp=("rubikdirt", 0)),
    "retro":     dict(display=("suez", 0), heavy=("heebo", 800), body=("heebo", 600), stamp=("rubikdirt", 0)),
    "tech":      dict(display=("notosans", 900), heavy=("notosans", 800), body=("notosans", 500), stamp=("rubikdirt", 0)),
}
for _t in TYPESETS.values():
    _t.setdefault("mono", ("geistmono", 600))
GRADES = {
    "natural": {},
    "bright": {"bright": 1.05, "contrast": 1.08, "sat": 1.12, "warm": 0.03},
    "warm":   {"bright": 1.03, "contrast": 1.06, "sat": 1.10, "warm": 0.07},
    "cool":   {"bright": 1.03, "contrast": 1.08, "sat": 1.08, "warm": -0.05},
    "punchy": {"bright": 1.02, "contrast": 1.16, "sat": 1.25, "warm": 0.02},
}
# text-safe band (top, bottom) as a fraction of height; "reels" keeps clear of the Reels/TikTok UI
SAFE = {"reels": (0.13, 0.76), "tiktok": (0.12, 0.74), "ads": (0.14, 0.65), "full": (0.06, 0.94)}
# platform -> (format, safe band, recommended length in seconds)
PLATFORMS = {"reels": ("9x16", "reels", (15, 30)), "tiktok": ("9x16", "tiktok", (15, 35)),
             "shorts": ("9x16", "reels", (15, 45)), "stories": ("9x16", "reels", (5, 15)),
             "ads": ("9x16", "ads", (6, 30)), "feed": ("4x5", "full", (10, 30)), "square": ("1x1", "full", (10, 30)),
             "youtube": ("16x9", "full", (30, 120)), "promo": ("16x9", "full", (30, 90))}
FONT_DIR = os.path.expanduser("~/.cache/promo_fonts")
PHOTO_EXT = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


def _label_font():
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
    except Exception:
        return ImageFont.load_default()


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# ----------------------------------------------------------------- fonts & text
def font_path(key):
    if os.path.isfile(key):
        return key
    rel = FONT_FILES.get(key, key)
    p = os.path.join(FONT_DIR, os.path.basename(rel))
    if os.path.exists(p):
        return p
    os.makedirs(FONT_DIR, exist_ok=True)
    url = GF + rel.replace("[", "%5B").replace("]", "%5D")
    if subprocess.run(["curl", "-fsSL", "-o", p, url]).returncode == 0 and os.path.getsize(p) > 1000:
        return p
    log(f"[font] could not fetch {key}; falling back to a local Hebrew font")
    out = subprocess.run(["fc-list", ":lang=he", "file"], capture_output=True, text=True).stdout.split("\n")
    cands = [l.split(":")[0] for l in out if l.strip()]
    bold = [c for c in cands if "Bold" in c]
    return (bold or cands or ["DejaVuSans-Bold.ttf"])[0]


_FC = {}


def get_font(spec, size):
    key, weight = spec
    k = (key, weight, int(size))
    if k not in _FC:
        f = ImageFont.truetype(font_path(key), int(size))
        if weight:
            try:
                axes = f.get_variation_axes()
                vals = [a["default"] for a in axes]
                for i, a in enumerate(axes):
                    if a["name"] in (b"Weight", "Weight"):
                        vals[i] = max(a["minimum"], min(a["maximum"], weight))
                f.set_variation_by_axes(vals)
            except Exception:
                pass
        _FC[k] = f
    return _FC[k]


def is_rtl(s):
    return any(0x0590 <= ord(c) <= 0x05FF or 0xFB1D <= ord(c) <= 0xFB4F or 0x0600 <= ord(c) <= 0x06FF for c in s)


def _kw(s):
    if not RAQM:
        return {}
    return dict(direction="rtl", language="he") if is_rtl(s) else dict(direction="ltr")


def _vis(s):
    return get_display(s) if (not RAQM and is_rtl(s)) else s


def line_mask(text, f):
    t = _vis(text)
    kw = _kw(text)
    l, tp, r, b = f.getbbox(t, **kw)
    pad = 4
    im = Image.new("L", (r - l + 2 * pad, b - tp + 2 * pad))
    ImageDraw.Draw(im).text((pad - l, pad - tp), t, font=f, fill=255, **kw)
    return im


def _greedy(words, f, max_w):
    out, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if cur and f.getlength(_vis(cand), **_kw(cand)) > max_w:
            out.append(cur)
            cur = w
        else:
            cur = cand
    out.append(cur)
    return out


def wrap_text(text, f, max_w, balance=True):
    """Word wrap; with balance the paragraph keeps the greedy line count but the lines are evened out, so no
    single word is left alone on the last line."""
    out = []
    for para in text.split("\n"):
        words = para.split()
        lines = _greedy(words, f, max_w)
        if balance and len(lines) > 1:
            lo = max(f.getlength(_vis(w), **_kw(w)) for w in words)
            hi = max_w
            for _ in range(14):
                mid = (lo + hi) / 2
                if len(_greedy(words, f, mid)) <= len(lines):
                    hi = mid
                else:
                    lo = mid
            lines = _greedy(words, f, hi + 0.5)
        out += lines
    return "\n".join(out)


def text_mask(text, f, gap=0.14):
    lines = [line_mask(l, f) for l in str(text).split("\n") if l.strip()] or [Image.new("L", (2, 2))]
    w = max(m.width for m in lines)
    g = int(f.size * gap)
    h = sum(m.height for m in lines) + g * (len(lines) - 1)
    im = Image.new("L", (w, h))
    y = 0
    for m in lines:
        im.paste(m, ((w - m.width) // 2, y))
        y += m.height + g
    return im


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def gradient_fill(mask, stops):
    h = max(1, mask.height)
    pos = np.linspace(0, 1, len(stops))
    ys = np.linspace(0, 1, h)
    cols = np.stack([np.interp(ys, pos, [c[i] for c in stops]) for i in range(3)], 1)
    arr = np.repeat(cols[:, None, :], mask.width, 1).astype(np.uint8)
    im = Image.fromarray(arr, "RGB").convert("RGBA")
    im.putalpha(mask)
    return im


def finish(fill_img, mask, shadow=0.55, stroke=0, stroke_rgb=(0, 0, 0), glow=None, U=1.0):
    pad = int(26 * U) + stroke
    W, H = mask.width + 2 * pad, mask.height + 2 * pad
    out = Image.new("RGBA", (W, H))
    big = Image.new("L", (W, H))
    big.paste(mask, (pad, pad))
    if shadow:
        sh = big.filter(ImageFilter.GaussianBlur(10 * U)).point(lambda v: int(v * shadow))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.putalpha(sh)
        out.alpha_composite(layer, (0, int(6 * U)))
    if glow:
        gl = big.filter(ImageFilter.GaussianBlur(16 * U)).point(lambda v: int(v * 0.6))
        layer = Image.new("RGBA", (W, H), glow + (0,))
        layer.putalpha(gl)
        out.alpha_composite(layer)
    if stroke:
        ring = big.filter(ImageFilter.MaxFilter(stroke * 2 + 1))
        layer = Image.new("RGBA", (W, H), stroke_rgb + (0,))
        layer.putalpha(ring)
        out.alpha_composite(layer)
    out.alpha_composite(fill_img, (pad, pad))
    return out


# ----------------------------------------------------------------- context
class Ctx:
    def __init__(self, brief, fmt, draft=False):
        self.brief, self.fmt, self.draft = brief, fmt, draft
        W, H = FORMATS[fmt]
        sc_ = float(brief.get("scale", 1))
        W, H = int(W * sc_) // 2 * 2, int(H * sc_) // 2 * 2
        if draft:
            W, H = W // 2 // 2 * 2, H // 2 // 2 * 2
        self.W, self.H, self.fps = W, H, int(brief.get("fps", 30))
        self.U = min(W, H) / 1080.0
        self.land = W > H
        th = dict(brief.get("theme", {}))
        preset = th.get("preset", "gold")
        base = dict(THEMES["gold"])
        if preset == "auto":
            base.update(theme_from_logo(brief.get("brand", {}).get("logo")))
        else:
            base.update(THEMES.get(preset, THEMES["gold"]))
        base.update({k: v for k, v in th.items() if k in base})
        self.c = {k: hexrgb(v) for k, v in base.items()}
        self.light = sum(self.c["bg"]) > 380
        ts = dict(TYPESETS.get(th.get("type", "bold"), TYPESETS["bold"]))
        for role in ("display", "heavy", "body", "stamp", "mono"):
            if th.get("font_" + role):
                v = th["font_" + role]
                ts[role] = (v, 0) if isinstance(v, str) else tuple(v)
        self.ts = ts
        self.grad = [self.c["hi"], self.c["primary"], self.c["primary2"]]
        plat = PLATFORMS.get(brief.get("platform", ""), (None, "reels", None))
        mt = {"9x16": SAFE.get(brief.get("safe", plat[1]), SAFE["reels"]), "4x5": (0.07, 0.90), "1x1": (0.07, 0.93),
              "16x9": (0.08, 0.92)}[fmt]
        self.bg_style = th.get("bg_style", "grid")
        self.drift = float(th.get("drift", 0.035 if self.bg_style != "grid" else 0.0))
        self._pstatic = None
        self.captions = []
        self.caption_words = []
        self.grade = dict(GRADES.get(th.get("grade", "bright"), {}))
        self.top, self.bot = int(mt[0] * H), int(mt[1] * H)
        self.cy = (self.top + self.bot) // 2
        self.brand = brief.get("brand", {})
        self._panel = None
        self._logo = None
        # motion style: "premium" (smooth, cinematic) or "hype" (beat hits, shake, glitch; energy 1-3)
        fx = brief.get("fx", 0)
        style, energy = None, 0
        if isinstance(fx, dict):
            style, energy = fx.get("style"), fx.get("energy", 0)
        elif isinstance(fx, str):
            v = fx.lower().strip()
            if v in ("premium", "pro", "cinematic", "smooth"):
                style = "premium"
            else:
                energy = {"off": 0, "none": 0, "low": 1, "medium": 2, "high": 2, "hype": 2, "crazy": 3, "max": 3}.get(v, 0)
        else:
            energy = fx or 0
        if style is None and energy:
            style = "hype"
        if style == "hype" and not energy:
            energy = 2
        self.premium = style == "premium"
        self.energy = int(max(0, min(3, float(energy or 0)))) if style == "hype" else 0

    def font(self, role, size):
        return get_font(self.ts[role], size * self.U)

    def T(self, text, role="body", size=60, color=None, grad=False, shadow=0.55, stroke=0, stroke_rgb=(0, 0, 0),
          max_w=None, glow=None, wrap=False):
        max_w = max_w or self.W * (0.62 if self.land else 0.88)
        if role == "mono" and is_rtl(text):
            role = "heavy"
        f = self.font(role, size)
        if wrap:
            text = wrap_text(str(text), f, max_w)
        m = text_mask(text, f)
        if m.width > max_w:
            f = self.font(role, size * max_w / m.width * 0.98)
            m = text_mask(text, f)
        fill = gradient_fill(m, self.grad if grad is True else grad) if grad else \
            Image.new("RGBA", m.size, (color or self.c["text"]) + (0,))
        if not grad:
            fill.putalpha(m)
        return finish(fill, m, shadow, int(stroke * self.U), stroke_rgb, glow, self.U)

    def panel(self):
        if self._panel is None:
            W, H, U = self.W, self.H, self.U
            bg = np.array(self.c["bg"], np.float32)
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            img = np.ones((H, W, 3), np.float32) * bg
            step = max(8, int(64 * U))
            grid = ((xx % step) < max(1, U * 1.5)) | ((yy % step) < max(1, U * 1.5))
            lc = np.array((0, 0, 0) if self.light else (255, 255, 255), np.float32)
            img[grid] = img[grid] * 0.93 + lc * 0.07
            d = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.28) / H) ** 2)
            glow = np.clip(1 - d * 2.2, 0, 1)[..., None] ** 2
            img = img * (1 - glow * 0.22) + np.array(self.c["primary"], np.float32) * glow * 0.22
            v = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
            vig = np.clip(1 - np.clip(v - 0.65, 0, 1) * (0.25 if self.light else 0.55), 0, 1)[..., None]
            self._panel = np.clip(img * vig, 0, 255).astype(np.uint8)
        return self._panel

    def panel_frame(self, T):
        """Animated motion-graphics background (theme bg_style "tech"): drifting brand-colour glows, a fine grid,
        floating particles and grain. Continuous across scenes because it is driven by global time T."""
        if self.bg_style == "grid":
            return self.panel()
        W, H, U = self.W, self.H, self.U
        if self._pstatic is None:
            bg = np.array(self.c["bg"], np.float32)
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            img = np.ones((H, W, 3), np.float32) * bg
            step = max(8, int(72 * U))
            grid = ((xx % step) < max(1, U * 1.2)) | ((yy % step) < max(1, U * 1.2))
            fade = np.clip(1 - np.abs(yy / H - 0.5) * 1.6, 0.15, 1)
            lc = np.array((255, 255, 255) if not self.light else (0, 0, 0), np.float32)
            img[grid] = img[grid] * (1 - 0.045 * fade[grid][:, None]) + lc * 0.045 * fade[grid][:, None]
            v = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
            img *= np.clip(1 - np.clip(v - 0.6, 0, 1) * 0.6, 0, 1)[..., None]
            img += np.random.default_rng(11).normal(0, 1.8, (H, W, 1)).astype(np.float32)
            self._pstatic = img
            sw, sh = max(8, W // 8), max(8, H // 8)
            gy, gx = np.mgrid[0:sh, 0:sw].astype(np.float32)
            self._g = (gx / sw, gy / sh)
            rng = np.random.default_rng(5)
            n = int(46 * (W * H) / (1080 * 1920)) + 12
            self._parts = np.stack([rng.random(n), rng.random(n), rng.uniform(0.01, 0.035, n), rng.uniform(0.6, 1.6, n),
                                    rng.uniform(0, 6.28, n)], 1)
            r = max(3, int(9 * U))
            yy2, xx2 = np.mgrid[-r:r + 1, -r:r + 1].astype(np.float32)
            dot = np.exp(-(xx2 ** 2 + yy2 ** 2) / (r * r * 0.18))
            spr = np.zeros((2 * r + 1, 2 * r + 1, 4), np.uint8)
            spr[..., :3] = self.c["hi"]
            spr[..., 3] = (dot * 255).astype(np.uint8)
            self._dot = spr
        gx, gy = self._g
        c = self.c
        g = np.zeros(gx.shape + (3,), np.float32)
        for (bx, by, r, col, al) in ((0.2 + 0.18 * math.sin(T * 0.21), 0.22 + 0.1 * math.cos(T * 0.17), 0.5, c["primary"], 0.2),
                                     (0.82 + 0.12 * math.cos(T * 0.16), 0.74 + 0.1 * math.sin(T * 0.19), 0.55, c["primary2"], 0.24),
                                     (0.5 + 0.3 * math.sin(T * 0.11), 0.5 + 0.25 * math.cos(T * 0.13), 0.35, c["accent"], 0.06)):
            d = (gx - bx) ** 2 + ((gy - by) * 0.56) ** 2
            g += np.exp(-d / (r * r * 0.25))[..., None] * np.array(col, np.float32) * al
        up = np.asarray(Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32)
        out = np.clip(self._pstatic + up, 0, 255).astype(np.uint8)
        for (x0, y0, spd, sz, ph) in self._parts:
            y = (y0 - spd * T) % 1.0
            x = x0 + 0.012 * math.sin(T * 0.7 + ph)
            a = 0.25 + 0.35 * (0.5 + 0.5 * math.sin(T * sz * 2 + ph))
            over(out, self._dot, x * W, y * H, a)
        return out

    def on_panel(self):
        return self.c["text"]

    def logo(self):
        if self._logo is None:
            p = self.brand.get("logo")
            if p and os.path.exists(p):
                im = Image.open(p).convert("RGBA")
                if self.brand.get("logo_bg", "auto") == "auto":
                    im = knock_out_corners(im)
                bb = im.getchannel("A").getbbox()
                self._logo = im.crop(bb) if bb else im
            else:
                self._logo = auto_emblem(self)
        return self._logo


def knock_out_corners(im, tol=14):
    """Opaque logos (app icons, JPG exports) sit on a flat square. Make only that flat background - the region
    connected to the four corners within `tol` of the corner colour - transparent; the logo pixels are untouched.
    Skipped when the image already has transparency, the corners differ, or the region would be most of the image."""
    a = np.asarray(im)
    if a[..., 3].min() < 250:
        return im
    rgb = a[..., :3].astype(int)
    h, w = rgb.shape[:2]
    cs = [rgb[0, 0], rgb[0, w - 1], rgb[h - 1, 0], rgb[h - 1, w - 1]]
    if max(np.abs(c - cs[0]).max() for c in cs) > tol:
        return im
    m = Image.fromarray(((np.abs(rgb - cs[0]).max(2) <= tol) * 255).astype(np.uint8)).copy()
    for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        ImageDraw.floodfill(m, xy, 128)
    bgm = np.asarray(m) == 128
    if bgm.mean() > 0.45 or bgm.mean() < 0.002:
        return im
    al = Image.fromarray(np.where(bgm, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    out = im.copy()
    out.putalpha(al)
    return out


def theme_from_logo(path):
    if not path or not os.path.exists(path):
        return {}
    im = Image.open(path).convert("RGBA").resize((96, 96))
    px = [p for p in im.getdata() if p[3] > 128]
    best, score = None, 0
    import colorsys
    from collections import Counter
    cnt = Counter((r // 16 * 16, g // 16 * 16, b // 16 * 16) for r, g, b, a in px)
    for (r, g, b), n in cnt.items():
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        sc = n * (s ** 1.5) * (v > 0.3)
        if sc > score:
            best, score = (h, s, v), sc
    if not best:
        return {}
    h, s, v = best
    hx = lambda hh, ss, vv: "#%02X%02X%02X" % tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hh, ss, vv))
    return dict(primary=hx(h, max(s, 0.55), max(v, 0.85)), primary2=hx(h, min(1, s + 0.15), v * 0.6),
                hi=hx(h, s * 0.35, 1.0), bg=hx(h, 0.45, 0.07))


def auto_emblem(ctx):
    name = ctx.brand.get("name", "")
    ini = ctx.brand.get("initials") or "".join(w[0] for w in name.split()[:2]) or "★"
    S = int(300 * ctx.U)
    im = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(im)
    r = int(S * 0.46)
    d.ellipse((S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r), outline=ctx.c["primary"], width=max(3, int(10 * ctx.U)))
    d.ellipse((S / 2 - r * 0.84, S / 2 - r * 0.84, S / 2 + r * 0.84, S / 2 + r * 0.84), outline=ctx.c["primary2"],
              width=max(2, int(3 * ctx.U)))
    m = text_mask(ini, ctx.font("display", 150))
    if m.width > S * 0.62:
        m = m.resize((int(S * 0.62), int(m.height * S * 0.62 / m.width)))
    g = gradient_fill(m, ctx.grad)
    im.alpha_composite(g, ((S - m.width) // 2, (S - m.height) // 2))
    return im


# ----------------------------------------------------------------- media
def probe(src):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:stream_side_data=rotation:stream_tags=rotate:format=duration",
                        "-of", "json", src], capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    st = (j.get("streams") or [{}])[0]
    w, h = st.get("width", 1080), st.get("height", 1920)
    rot = 0
    for sd in st.get("side_data_list", []) or []:
        rot = int(sd.get("rotation", 0) or 0)
    rot = rot or int((st.get("tags") or {}).get("rotate", 0) or 0)
    if abs(rot) in (90, 270):
        w, h = h, w
    return w, h, float((j.get("format") or {}).get("duration", 0) or 0)


def norm_clip(c):
    if c is None:
        return None
    return {"src": c} if isinstance(c, str) else dict(c)


def is_photo(src):
    return src.lower().endswith(PHOTO_EXT)


def fit_chain(spec, W, H, sw, sh):
    fit = spec.get("fit", "auto")
    if fit == "auto":
        fit = "cover" if abs((sw / sh) / (W / H) - 1) < 0.45 else "blur"
    fx, fy = spec.get("focus", [0.5, 0.5])
    cover = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}:(iw-{W})*{fx}:(ih-{H})*{fy}"
    if fit == "cover":
        return cover
    return (f"split[a][b];[a]{cover},gblur=sigma=30,colorlevels=romax=0.6:gomax=0.6:bomax=0.6[bg];"
            f"[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2")


def look_chain(look):
    f = []
    if look.get("bw"):
        f.append("hue=s=0,eq=contrast=1.18")
    elif look.get("grade", True):
        br = (float(look.get("bright", 1.0)) - 1.0) * 0.5
        f.append(f"eq=contrast={look.get('contrast', 1.06)}:saturation={look.get('sat', 1.18)}:brightness={br:.3f}")
        w = float(look.get("warm", 0))
        if abs(w) > 0.001:
            f.append(f"colorbalance=rm={w:.3f}:gm={w * 0.3:.3f}:bm={-w:.3f}")
    if look.get("blur"):
        f.append(f"gblur=sigma={look['blur']}")
    dim = look.get("dim", 1.0)
    if dim < 0.999:
        f.append(f"colorlevels=romax={dim}:gomax={dim}:bomax={dim}")
    if look.get("vignette", True):
        f.append("vignette=angle=PI/5")
    return ",".join(f)


def pil_look(im, look):
    from PIL import ImageEnhance
    if look.get("bw"):
        im = ImageEnhance.Contrast(im.convert("L").convert("RGB")).enhance(1.18)
    elif look.get("grade", True):
        im = ImageEnhance.Color(ImageEnhance.Contrast(im).enhance(look.get("contrast", 1.06))).enhance(look.get("sat", 1.18))
        if abs(float(look.get("bright", 1.0)) - 1) > 0.001:
            im = ImageEnhance.Brightness(im).enhance(float(look["bright"]))
        w = float(look.get("warm", 0))
        if abs(w) > 0.001:
            r, g, b = im.split()
            r = r.point(lambda v: min(255, int(v * (1 + w))))
            b = b.point(lambda v: max(0, int(v * (1 - w))))
            im = Image.merge("RGB", (r, g, b))
    if look.get("blur"):
        im = im.filter(ImageFilter.GaussianBlur(look["blur"]))
    dim = look.get("dim", 1.0)
    if dim < 0.999:
        im = im.point(lambda v: int(v * dim))
    return im


def ease_move(p):
    """Camera-move easing: mostly constant speed (so cuts land mid-move) with a soft start."""
    return 0.75 * p + 0.25 * e_inout(p) if p < 1 else 1.0


PHOTO_MOVES = ("push", "pull", "pan_left", "pan_right", "pan_up", "pan_down", "drift", "still")


class Reader:
    """Sequential frames of a clip/photo at WxH, starting t seconds into the scene.
    Photos get a camera move (spec "move"): push | pull | pan_left | pan_right | pan_up | pan_down | drift | still | auto.
    auto pans across wide photos in a tall frame (and vice versa) instead of cropping them, otherwise pushes in."""

    def __init__(self, spec, W, H, fps, n, t0=0.0, look=None, zoom=0.0, seed=0):
        self.spec, self.W, self.H, self.fps, self.n = spec, W, H, fps, n
        self.look, self.zoom, self.k = look or {}, zoom, int(round(t0 * fps))
        self.proc, self.img = None, None
        src = spec["src"]
        rng = np.random.default_rng(seed)
        if is_photo(src):
            from PIL import ImageOps
            im = ImageOps.exif_transpose(Image.open(src).convert("RGB"))
            iw, ih = im.size
            move = spec.get("move") or {"in": "push", "out": "pull"}.get(spec.get("kenburns"), "auto")
            ar_i, ar_f = iw / ih, W / H
            if move == "auto":
                if ar_i > ar_f * 1.3:
                    move = "pan_left" if rng.random() < 0.5 else "pan_right"
                elif ar_i < ar_f / 1.3:
                    move = "pan_down" if rng.random() < 0.5 else "pan_up"
                else:
                    move = "push" if rng.random() < 0.65 else "pull"
            self.move = move
            margin = 1.04 if move.startswith("pan") else 1.02
            s = max(W / iw, H / ih) * margin
            big = im.resize((max(W, round(iw * s)), max(H, round(ih * s))), Image.LANCZOS)
            self.img = pil_look(big, self.look)
            self.amt = float(spec.get("amount", 0.13))
            self.focus = spec.get("focus", [0.5, 0.45])
            self.speed = float(spec.get("pan_speed", 0.2))
            self.dur = max(0.5, n / fps)
            ang = rng.uniform(0, 6.28)
            self.drift = (math.cos(ang), math.sin(ang))
        else:
            sw, sh, _ = probe(src)
            speed = float(spec.get("speed", 1.0))
            ss = float(spec.get("start", 0)) + t0 * speed
            self.ew, self.eh = W + W % 2, H + H % 2
            vf = fit_chain(spec, self.ew, self.eh, sw, sh)
            lk = look_chain(self.look)
            chain = (f"[0:v]setpts=PTS/{speed},{vf}" if "split" in vf else f"setpts=PTS/{speed},{vf}")
            if lk:
                chain += "," + lk
            chain += f",fps={fps},format=rgb24"
            cmd = [FFMPEG, "-v", "error", "-stream_loop", "-1", "-ss", f"{ss:.3f}", "-i", src, "-an"]
            cmd += (["-filter_complex", chain] if "split" in vf else ["-vf", chain])
            cmd += ["-frames:v", str(max(1, n - self.k + 2)), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self.last = None

    def _photo(self, p):
        W, H = self.W, self.H
        iw, ih = self.img.size
        q = ease_move(p)
        mv, amt = self.move, self.amt
        z = 1.0
        fx, fy = self.focus
        cx, cy = iw * fx, ih * fy
        if mv == "push":
            z = 1 + amt * q
        elif mv == "pull":
            z = 1 + amt * (1 - q)
        elif mv == "drift":
            z = 1 + amt * 0.6
        elif mv.startswith("pan"):
            z = 1 + 0.035 * q
            horiz = mv in ("pan_left", "pan_right")
            span = (iw - W / z) if horiz else (ih - H / z)
            travel = min(max(0.0, span), self.speed * (W if horiz else H) * self.dur)
            d = (q - 0.5) * travel * (1 if mv in ("pan_right", "pan_down") else -1)
            if horiz:
                cx += d
            else:
                cy += d
        cw, ch = W / z, H / z
        if mv == "drift":
            cx += self.drift[0] * (q - 0.5) * (iw - cw) * 0.8
            cy += self.drift[1] * (q - 0.5) * (ih - ch) * 0.8
        cx = min(max(cx, cw / 2), iw - cw / 2)
        cy = min(max(cy, ch / 2), ih - ch / 2)
        a = cw / W
        fr = self.img.transform((W, H), Image.AFFINE, (a, 0, cx - cw / 2, 0, a, cy - ch / 2), Image.BICUBIC)
        return np.array(fr)

    def next(self):
        W, H = self.W, self.H
        p = self.k / max(1, self.n - 1)
        self.k += 1
        if self.img is not None:
            return self._photo(min(1.0, p))
        ew, eh = self.ew, self.eh
        buf = self.proc.stdout.read(ew * eh * 3)
        if len(buf) < ew * eh * 3:
            fr = self.last if self.last is not None else np.zeros((H, W, 3), np.uint8)
        else:
            fr = np.frombuffer(buf, np.uint8).reshape(eh, ew, 3)[:H, :W].copy()
        self.last = fr
        if self.zoom:
            s = 1 + self.zoom * p
            im = Image.fromarray(fr)
            a = 1 / s
            fr = np.array(im.transform((W, H), Image.AFFINE, (a, 0, W * (1 - a) / 2, 0, a, H * (1 - a) / 2), Image.BILINEAR))
        return fr

    def close(self):
        if self.proc:
            try:
                self.proc.stdout.close()
                self.proc.kill()
                self.proc.wait()
            except Exception:
                pass


def grab_still(spec, W, H, t=0.5):
    src = spec["src"]
    if is_photo(src):
        from PIL import ImageOps
        im = ImageOps.exif_transpose(Image.open(src).convert("RGB"))
        return ImageOps.fit(im, (W, H), Image.LANCZOS)
    r = Reader(spec, W, H, 30, 1, t0=t, look={"vignette": False})
    fr = r.next()
    r.close()
    return Image.fromarray(fr)


def activity(src, cache):
    if src in cache:
        return cache[src]
    cmd = [FFMPEG, "-v", "error", "-i", src, "-an", "-vf", "fps=4,scale=48:48,format=gray", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, 48 * 48).astype(np.float32) if raw else np.zeros((1, 2304))
    diff = np.abs(np.diff(a, axis=0)).mean(1) if len(a) > 1 else np.zeros(1)
    bright = a.mean(1)[1:] if len(a) > 1 else np.ones(1)
    score = diff * np.clip(bright / 60, 0, 1)
    cache[src] = score.tolist()
    return cache[src]


def best_start(src, dur, cache, used):
    if is_photo(src):
        return 0.0
    _, _, D = probe(src)
    if D <= dur + 0.6:
        return 0.0
    s = np.array(activity(src, cache))
    w = max(1, int(dur * 4))
    if len(s) <= w:
        return 0.0
    win = np.convolve(s, np.ones(w), "valid")
    t = np.arange(len(win)) / 4.0
    ok = (t >= 0.3) & (t + dur <= D - 0.2)
    for a, b in used.get(src, []):
        ok &= (t + dur <= a) | (t >= b)
    if not ok.any():
        ok = (t >= 0.3) & (t + dur <= D - 0.2)
    if not ok.any():
        return 0.0
    win = np.where(ok, win, -1)
    st = float(t[int(np.argmax(win))])
    used.setdefault(src, []).append((st, st + dur))
    return st


# ----------------------------------------------------------------- compositing & animation
def over(dst, src, x, y, a=1.0):
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0 or a <= 0.003:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    al = s[..., 3:4].astype(np.float32) * (min(a, 1.0) / 255.0)
    d = dst[y0:y1, x0:x1]
    d[:] = (d * (1 - al) + s[..., :3] * al).astype(np.uint8)


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def e_cubic(p):
    return 1 - (1 - p) ** 3


def e_back(p, s=1.7):
    p -= 1
    return p * p * ((s + 1) * p + s) + 1


def e_expo(p):
    return 1 if p >= 1 else 1 - 2 ** (-10 * p)


def e_inout(p):
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def beat_env(ctx, t):
    """1 on a beat of the current scene, decaying over about 0.15 s (0 without fx energy or music)."""
    bs = getattr(ctx, "_beats_now", None)
    if not bs:
        return 0.0
    last = None
    for b in bs:
        if b <= t:
            last = b
        else:
            break
    return math.exp(-(t - last) / 0.13) if last is not None else 0.0


class Sprite:
    def __init__(self, img, cx, cy, t0=0.0, anim="up", d=0.35, rtl=True, pulse=0.0, scale_fn=None):
        self.img, self.cx, self.cy, self.t0, self.anim, self.d = img, cx, cy, t0, anim, d
        self.arr = np.asarray(img)
        self.rtl, self.pulse, self.scale_fn = rtl, pulse, scale_fn

    def _pose(self, t, ctx):
        """Energy-mode pose (fx energy >= 2): bigger, overshooting entrances, then the element keeps floating
        and bounces on the beat. Returns (alpha, dx, dy, scale, progress) or None before the entrance."""
        if t < self.t0:
            return None
        p = clamp((t - self.t0) / self.d)
        U, k = ctx.U, self.anim
        a, dx, dy, s = 1.0, 0.0, 0.0, 1.0
        if k in ("up", "down"):
            e = e_back(p, 2.0)
            a, dy = clamp(p * 2.5), (1 - e) * 170 * U * (1 if k == "up" else -1)
        elif k in ("left", "right"):
            e = e_back(p, 2.0)
            a, dx = clamp(p * 2.5), (1 - e) * 220 * U * (-1 if k == "left" else 1)
        elif k in ("pop", "fade"):
            a, s = clamp(p * 3), 0.25 + 0.75 * e_back(p, 2.6)
        elif k == "zoom":
            a, s = clamp(p * 2.5), 1.9 - 0.9 * e_back(p, 1.8)
        elif k == "slam":
            a, s = clamp(p * 4), 3.0 - 2.0 * (p * p)
        if p >= 1:
            ph = self.cx * 0.013 + self.cy * 0.007
            dy += math.sin(t * 2.4 + ph) * 5 * U
            s *= 1 + 0.008 * math.sin(t * 1.7 + ph)
        s *= 1 + 0.035 * (ctx.energy / 2.0) * beat_env(ctx, t)
        if self.pulse and p >= 1:
            s *= 1 + self.pulse * math.sin((t - self.t0 - self.d) * 6.0)
        if self.scale_fn:
            s *= self.scale_fn(t)
        ry = rx = 0.0
        if self.arr.shape[0] * self.arr.shape[1] >= 0.03 * ctx.W * ctx.H:
            # big elements (cards, large tags, buttons) flip in and keep swaying in 3D
            ph = self.cx * 0.011 + self.cy * 0.005
            if k != "slam" and p < 1:
                ry = (1 - e_back(p, 1.6)) * 70 * (1 if self.cx <= ctx.W / 2 else -1)
            ry += 5 * math.sin(t * 1.4 + ph)
            rx = 2.5 * math.sin(t * 1.1 + ph * 1.3)
        return a, dx, dy, s, p, ry, rx

    def _blit(self, out, s, dx, dy, a, ry=0.0, rx=0.0):
        arr, img = self.arr, self.img
        h, w = arr.shape[:2]
        if abs(s - 1) > 0.004:
            nw, nh = max(1, int(w * s)), max(1, int(h * s))
            img = self.img.resize((nw, nh), Image.BILINEAR)
            arr = np.asarray(img)
            h, w = nh, nw
        if abs(ry) > 0.05 or abs(rx) > 0.05:
            img = tilt(img.convert("RGBA") if img.mode != "RGBA" else img, ry, rx)
            arr = np.asarray(img)
            h, w = arr.shape[:2]
        over(out, arr, self.cx - w / 2 + dx, self.cy - h / 2 + dy, a)

    def _pose_premium(self, t, ctx):
        """Premium pose: slower, smooth expo ease, small travel; big elements tilt in once in 3D, then hold."""
        if t < self.t0:
            return None
        d = max(self.d, 0.55)
        p = clamp((t - self.t0) / d)
        e = e_expo(p)
        U, k = ctx.U, self.anim
        a, dx, dy, s = clamp(p * 2.2), 0.0, 0.0, 1.0
        if k in ("up", "down"):
            dy = (1 - e) * 60 * U * (1 if k == "up" else -1)
        elif k in ("left", "right"):
            dx = (1 - e) * 80 * U * (-1 if k == "left" else 1)
        elif k in ("pop", "fade"):
            s = 0.92 + 0.08 * e
        elif k == "zoom":
            s = 1.1 - 0.1 * e
        elif k == "slam":
            a, s = clamp(p * 3), 1.25 - 0.25 * e
        if self.pulse and p >= 1:
            s *= 1 + self.pulse * math.sin((t - self.t0 - d) * 6.0)
        if self.scale_fn:
            s *= self.scale_fn(t)
        ry = rx = 0.0
        if self.arr.shape[0] * self.arr.shape[1] >= 0.03 * ctx.W * ctx.H and k != "slam":
            ry, rx = (1 - e) * 22 * (1 if self.cx <= ctx.W / 2 else -1), (1 - e) * 8
        return a, dx, dy, s, p, ry, rx, d

    def _sheen(self, out, t, ctx, d):
        """One soft light sweep across a big element after it lands."""
        q = (t - self.t0 - d - 0.1) / 0.75
        if not 0 < q < 1:
            return
        h, w = self.arr.shape[:2]
        if getattr(self, "_u", None) is None:
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            self._u = (xx + (h - yy) * 0.5) / (w + h * 0.5)
        c = -0.2 + 1.4 * e_inout(q)
        band = np.exp(-((self._u - c) / 0.07) ** 2) * (self.arr[..., 3].astype(np.float32) / 255.0) * 0.32
        sh = np.zeros((h, w, 4), np.uint8)
        sh[..., :3] = 255
        sh[..., 3] = (band * 255).astype(np.uint8)
        over(out, sh, self.cx - w / 2, self.cy - h / 2)

    def draw(self, out, t, ctx, bgf=None):
        if getattr(ctx, "premium", False) and self.anim not in ("none", "wipe"):
            pose = self._pose_premium(t, ctx)
            if pose is None:
                return
            a, dx, dy, s, p, ry, rx, d = pose
            if p < 1:
                prev = self._pose_premium(t - 1.0 / ctx.fps, ctx)
                if prev is not None:
                    vx, vy = abs(dx - prev[1]), abs(dy - prev[2])
                    if max(vx, vy) >= 2:
                        img = self.img
                        if abs(s - 1) > 0.004:
                            img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BILINEAR)
                        if abs(ry) > 0.05 or abs(rx) > 0.05:
                            img = tilt(img, ry, rx)
                        arr = hblur(np.asarray(img), int(max(vx, vy) * 1.5), 0 if vy >= vx else 1)
                        over(out, arr, self.cx - arr.shape[1] / 2 + dx, self.cy - arr.shape[0] / 2 + dy, a)
                        return
            self._blit(out, s, dx, dy, a, ry, rx)
            if p >= 1 and self.arr.shape[0] * self.arr.shape[1] >= 0.03 * ctx.W * ctx.H and abs(s - 1) <= 0.004:
                self._sheen(out, t, ctx, d)
            return
        if getattr(ctx, "energy", 0) >= 2 and self.anim not in ("none", "wipe"):
            pose = self._pose(t, ctx)
            if pose is None:
                return
            if pose[4] < 1:
                for j, ga in ((3, 0.12), (2, 0.22), (1, 0.38)):
                    g = self._pose(t - 0.03 * j, ctx)
                    if g is not None:
                        self._blit(out, g[3], g[1], g[2], g[0] * ga, g[5], g[6])
            self._blit(out, pose[3], pose[1], pose[2], pose[0], pose[5], pose[6])
            return
        if t < self.t0 and self.anim != "none":
            return
        p = clamp((t - self.t0) / self.d) if self.anim != "none" else 1.0
        a, dx, dy, s, rev = 1.0, 0.0, 0.0, 1.0, 1.0
        U, k = ctx.U, self.anim
        if k == "up":
            e = e_cubic(p); a = e; dy = (1 - e) * 70 * U
        elif k == "down":
            e = e_cubic(p); a = e; dy = -(1 - e) * 70 * U
        elif k == "fade":
            a = e_cubic(p)
        elif k == "pop":
            a = clamp(p * 3); s = 0.55 + 0.45 * e_back(p)
        elif k == "zoom":
            e = e_cubic(p); a = e; s = 1.35 - 0.35 * e
        elif k == "slam":
            a = clamp(p * 4); s = 2.4 - 1.4 * (p * p)
        elif k == "wipe":
            rev = e_cubic(p)
        elif k in ("left", "right"):
            e = e_cubic(p); a = e; dx = (1 - e) * 90 * U * (-1 if k == "left" else 1)
        if self.pulse and p >= 1:
            s *= 1 + self.pulse * math.sin((t - self.t0 - self.d) * 6.0)
        if self.scale_fn:
            s *= self.scale_fn(t)
        arr = self.arr
        h, w = arr.shape[:2]
        if abs(s - 1) > 0.004:
            nw, nh = max(1, int(w * s)), max(1, int(h * s))
            arr = np.asarray(self.img.resize((nw, nh), Image.BILINEAR))
            h, w = nh, nw
        x = self.cx - w / 2 + dx
        if rev < 0.999:
            vis = max(1, int(w * rev))
            if self.rtl:
                arr = arr[:, w - vis:]
                x += w - vis
            else:
                arr = arr[:, :vis]
        over(out, arr, x, self.cy - h / 2 + dy, a)


class Fn:
    def __init__(self, f):
        self.f = f

    def draw(self, out, t, ctx, bgf=None):
        self.f(out, t, bgf)


def stack(items, cy, max_h, gaps):
    """items: list of PIL images (or None); returns list of (img, cy) centred on cy, scaled to fit max_h."""
    items = [i for i in items if i is not None]
    gaps = list(gaps)[:max(0, len(items) - 1)] + [0] * max(0, len(items) - 1 - len(gaps))
    tot = sum(i.height for i in items) + sum(gaps)
    if tot > max_h:
        f = max_h / tot
        items = [i.resize((max(1, int(i.width * f)), max(1, int(i.height * f))), Image.LANCZOS) for i in items]
        gaps = [g * f for g in gaps]
        tot = max_h
    y = cy - tot / 2
    out = []
    for i, im in enumerate(items):
        out.append((im, y + im.height / 2))
        y += im.height + (gaps[i] if i < len(gaps) else 0)
    return out


def rounded_mask(w, h, r):
    m = Image.new("L", (w, h))
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


def shadow_box(w, h, r, U, alpha=0.6):
    pad = int(40 * U)
    m = Image.new("L", (w + 2 * pad, h + 2 * pad))
    ImageDraw.Draw(m).rounded_rectangle((pad, pad + 10 * U, pad + w, pad + h + 10 * U), r, fill=int(255 * alpha))
    m = m.filter(ImageFilter.GaussianBlur(18 * U))
    im = Image.new("RGBA", m.size, (0, 0, 0, 0))
    im.putalpha(m)
    return im


def underline(ctx, w):
    U = ctx.U
    h = max(3, int(9 * U))
    im = Image.new("L", (int(w), h))
    d = ImageDraw.Draw(im)
    solid = w * 0.62
    d.rounded_rectangle((w - solid, 0, w, h - 1), h // 2, fill=255)
    x = w - solid - 14 * U
    while x > 0:
        d.rounded_rectangle((max(0, x - 26 * U), 0, x, h - 1), h // 2, fill=255)
        x -= 40 * U
    return finish(gradient_fill(im, ctx.grad), im, 0.4, U=U)


def check_icon(ctx, R, prog, filled):
    S = int(R * 2 + 6)
    im = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(im)
    c = S / 2
    if filled:
        d.ellipse((c - R, c - R, c + R, c + R), fill=ctx.c["primary"])
    else:
        d.ellipse((c - R, c - R, c + R, c + R), outline=ctx.c["primary"], width=max(2, int(R * 0.16)))
    if prog > 0:
        pts = [(c - R * 0.45, c + R * 0.02), (c - R * 0.12, c + R * 0.34), (c + R * 0.48, c - R * 0.3)]
        L1 = math.dist(pts[0], pts[1]); L2 = math.dist(pts[1], pts[2]); Lt = (L1 + L2) * prog
        seg = [pts[0]]
        if Lt <= L1:
            seg.append((pts[0][0] + (pts[1][0] - pts[0][0]) * Lt / L1, pts[0][1] + (pts[1][1] - pts[0][1]) * Lt / L1))
        else:
            q = (Lt - L1) / L2
            seg += [pts[1], (pts[1][0] + (pts[2][0] - pts[1][0]) * q, pts[1][1] + (pts[2][1] - pts[1][1]) * q)]
        d.line(seg, fill=ctx.c["bg"] if not ctx.light else (255, 255, 255), width=max(3, int(R * 0.2)), joint="curve")
    return im


def star(ctx, R):
    S = int(R * 2 + 4)
    m = Image.new("L", (S, S))
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = R if i % 2 == 0 else R * 0.45
        pts.append((S / 2 + r * math.cos(ang), S / 2 + r * math.sin(ang)))
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return finish(gradient_fill(m, ctx.grad), m, 0.4, U=ctx.U)


def chat_icon(size, color):
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    s = size
    d.ellipse((s * 0.06, s * 0.06, s * 0.94, s * 0.86), outline=color, width=max(2, int(s * 0.09)))
    d.polygon([(s * 0.12, s * 0.97), (s * 0.2, s * 0.66), (s * 0.4, s * 0.8)], fill=color)
    for i in range(3):
        cx = s * (0.32 + 0.18 * i)
        d.ellipse((cx - s * 0.05, s * 0.41, cx + s * 0.05, s * 0.51), fill=color)
    return im


def button(ctx, text, color=None, icon=True):
    U = ctx.U
    color = color or ctx.c["cta"]
    m = text_mask(text, ctx.font("heavy", 50))
    ic = int(m.height * 1.25) if icon else 0
    h = int(max(m.height, ic) + 44 * U)
    w = int(m.width + ic + (26 * U if icon else 0) + 80 * U)
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=color)
    hl = Image.new("L", (w, h))
    ImageDraw.Draw(hl).rounded_rectangle((3, 3, w - 4, h // 2), h // 2, fill=40)
    white = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    white.putalpha(hl)
    im.alpha_composite(white)
    txt = Image.new("RGBA", m.size, (255, 255, 255, 0))
    txt.putalpha(m)
    rtl = is_rtl(text)
    icx = int(w - 40 * U - ic) if rtl else int(40 * U)
    tx = int(icx - 26 * U - m.width) if rtl else int(icx + ic + 26 * U)
    if icon:
        im.alpha_composite(chat_icon(ic, (255, 255, 255, 255)), (icx, (h - ic) // 2))
    else:
        tx = (w - m.width) // 2
    if not icon or ink_for(color) != (255, 255, 255):
        txt = Image.new("RGBA", m.size, ink_for(color) + (0,))
        txt.putalpha(m)
    im.alpha_composite(txt, (tx, (h - m.height) // 2))
    return finish(im, im.getchannel("A"), 0.5, U=U)


def make_stamp(ctx, text, color=None):
    U = ctx.U
    color = color or ctx.c["accent"]
    m = text_mask(text, ctx.font("stamp", 130))
    pad, bw = int(30 * U), max(4, int(10 * U))
    w, h = m.width + 2 * pad + 2 * bw, m.height + 2 * pad + 2 * bw
    a = Image.new("L", (w, h))
    d = ImageDraw.Draw(a)
    d.rounded_rectangle((bw // 2, bw // 2, w - bw // 2, h - bw // 2), int(16 * U), outline=255, width=bw)
    a.paste(255, (pad + bw, pad + bw), m)
    rng = np.random.default_rng(len(text))
    n = rng.random((max(2, h // 8), max(2, w // 8))).astype(np.float32)
    n = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255.0
    grit = np.clip(0.55 + n * 0.7, 0, 1) * (rng.random((h, w)) > 0.06)
    a = Image.fromarray((np.array(a) * grit).astype(np.uint8))
    im = Image.new("RGBA", (w, h), color + (0,))
    im.putalpha(a)
    im = im.rotate(6, Image.BICUBIC, expand=True)
    return finish(im, im.getchannel("A"), 0.35, U=U)


def qr_image(ctx, data, size):
    try:
        import qrcode
    except Exception:
        log("[qr] pip install qrcode to enable QR codes")
        return None
    q = qrcode.QRCode(border=2, box_size=10)
    q.add_data(data)
    q.make(fit=True)
    im = q.make_image(fill_color="black", back_color="white").convert("RGBA").resize((size, size), Image.NEAREST)
    m = rounded_mask(size, size, int(size * 0.08))
    im.putalpha(m)
    return im


# ----------------------------------------------------------------- v2 building blocks: icons, pills, boxed text, scrims
def word_mask(text, f):
    """Mask of one word on a shared baseline, so words of a line line up when placed one by one."""
    t, kw = _vis(text), _kw(text)
    l, tp, r, b = f.getbbox(t, anchor="ms", **kw)
    asc, desc = f.getmetrics()
    pad = 4
    im = Image.new("L", (max(2, r - l + 2 * pad), asc + desc + 2 * pad))
    ImageDraw.Draw(im).text((pad - l, pad + asc), t, font=f, fill=255, anchor="ms", **kw)
    return im


ICONS = ("pin", "people", "bed", "view", "waves", "star", "check", "home", "snow", "wifi", "parking", "sun", "heart",
         "calendar", "chat", "key", "book", "kitchen", "sparkle", "pool", "coffee", "clock", "phone",
         "web", "cart", "layers", "bolt", "gear", "code", "chip", "chart", "rocket", "search", "lock")


def icon_mask(name, size):
    S = max(8, int(size * 4))
    m = Image.new("L", (S, S))
    d = ImageDraw.Draw(m)
    w = max(2, int(S * 0.085))
    P = lambda x, y: (x * S, y * S)

    def wave(y, amp=0.045, x0=0.08, x1=0.92):
        pts = [P(x, y + amp * math.sin((x - x0) / (x1 - x0) * 4 * math.pi)) for x in np.linspace(x0, x1, 40)]
        d.line(pts, fill=255, width=w, joint="curve")
    if name == "pin":
        r = S * 0.3
        cx, cy = S / 2, S * 0.38
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
        d.polygon([(cx - r * 0.87, cy + r * 0.5), (cx + r * 0.87, cy + r * 0.5), (cx, S * 0.95)], fill=255)
        rr = r * 0.42
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=0)
    elif name == "people":
        for x, k, col in ((0.34, 0.82, 255), (0.62, 1.0, 0), (0.62, 1.0, 255)):
            g = 0.035 if col == 0 else 0
            r = S * (0.12 * k + g)
            d.ellipse((S * x - r, S * 0.3 - r, S * x + r, S * 0.3 + r), fill=col)
            bw = S * (0.24 * k + g)
            d.pieslice((S * x - bw, S * 0.5 - g * S, S * x + bw, S * (0.5 + 0.5 * k) + bw * 0.6), 180, 360, fill=col)
    elif name == "bed":
        d.rounded_rectangle((*P(0.08, 0.28), *P(0.17, 0.86)), int(S * 0.03), fill=255)
        d.rectangle((*P(0.08, 0.6), *P(0.92, 0.74)), fill=255)
        d.rectangle((*P(0.84, 0.6), *P(0.92, 0.86)), fill=255)
        d.rounded_rectangle((*P(0.21, 0.45), *P(0.4, 0.57)), int(S * 0.04), fill=255)
        d.rounded_rectangle((*P(0.43, 0.43), *P(0.92, 0.57)), int(S * 0.04), fill=255)
    elif name == "view":
        d.polygon([P(0.04, 0.6), P(0.34, 0.2), P(0.52, 0.44), P(0.66, 0.3), P(0.96, 0.6)], fill=255)
        wave(0.72)
        wave(0.86)
    elif name == "waves" or name == "pool":
        for y in (0.38, 0.58, 0.78):
            wave(y)
        if name == "pool":
            m2 = Image.new("L", (S, S))
            d2 = ImageDraw.Draw(m2)
            for x in (0.3, 0.55):
                d2.line([P(x, 0.08), P(x, 0.5)], fill=255, width=w)
            for y in (0.18, 0.32):
                d2.line([P(0.3, y), P(0.55, y)], fill=255, width=w)
            m.paste(255, (0, 0), m2)
    elif name in ("star", "sparkle"):
        pts = []
        n = 5 if name == "star" else 4
        for i in range(n * 2):
            a = -math.pi / 2 + i * math.pi / n
            r = 0.46 if i % 2 == 0 else (0.2 if name == "star" else 0.12)
            pts.append(P(0.5 + r * math.cos(a), 0.52 + r * math.sin(a)))
        d.polygon(pts, fill=255)
    elif name == "check":
        d.ellipse((*P(0.06, 0.06), *P(0.94, 0.94)), outline=255, width=w)
        d.line([P(0.28, 0.52), P(0.44, 0.67), P(0.73, 0.36)], fill=255, width=int(w * 1.3), joint="curve")
    elif name == "home":
        d.polygon([P(0.5, 0.1), P(0.94, 0.48), P(0.82, 0.48), P(0.82, 0.9), P(0.18, 0.9), P(0.18, 0.48), P(0.06, 0.48)], fill=255)
        d.rectangle((*P(0.42, 0.62), *P(0.58, 0.9)), fill=0)
    elif name == "snow":
        for a in (0, 60, 120):
            r = math.radians(a)
            dx, dy = 0.42 * math.cos(r), 0.42 * math.sin(r)
            d.line([P(0.5 - dx, 0.5 - dy), P(0.5 + dx, 0.5 + dy)], fill=255, width=w)
            for sgn in (1, -1):
                bx, by = 0.5 + sgn * dx * 0.62, 0.5 + sgn * dy * 0.62
                for off in (0.5, -0.5):
                    rr = r + off * (1 if sgn > 0 else -1) + (math.pi if sgn < 0 else 0)
                    d.line([P(bx, by), P(bx + 0.14 * math.cos(rr + math.pi), by + 0.14 * math.sin(rr + math.pi))], fill=255, width=w)
    elif name == "wifi":
        for r in (0.42, 0.29, 0.16):
            d.arc((*P(0.5 - r, 0.78 - r), *P(0.5 + r, 0.78 + r)), 225, 315, fill=255, width=w)
        d.ellipse((*P(0.44, 0.72), *P(0.56, 0.84)), fill=255)
    elif name == "parking":
        d.rounded_rectangle((*P(0.08, 0.08), *P(0.92, 0.92)), int(S * 0.18), outline=255, width=w)
        try:
            fP = ImageFont.truetype("DejaVuSans-Bold.ttf", int(S * 0.62))
            d.text(P(0.5, 0.52), "P", font=fP, fill=255, anchor="mm")
        except Exception:
            pass
    elif name == "sun":
        d.ellipse((*P(0.31, 0.31), *P(0.69, 0.69)), fill=255)
        for i in range(8):
            a = i * math.pi / 4
            d.line([P(0.5 + 0.28 * math.cos(a), 0.5 + 0.28 * math.sin(a)), P(0.5 + 0.44 * math.cos(a), 0.5 + 0.44 * math.sin(a))],
                   fill=255, width=w)
    elif name == "heart":
        d.ellipse((*P(0.08, 0.14), *P(0.52, 0.56)), fill=255)
        d.ellipse((*P(0.48, 0.14), *P(0.92, 0.56)), fill=255)
        d.polygon([P(0.1, 0.44), P(0.9, 0.44), P(0.5, 0.9)], fill=255)
    elif name == "calendar":
        d.rounded_rectangle((*P(0.08, 0.16), *P(0.92, 0.92)), int(S * 0.1), outline=255, width=w)
        d.rectangle((*P(0.08, 0.2), *P(0.92, 0.38)), fill=255)
        for x in (0.3, 0.7):
            d.line([P(x, 0.06), P(x, 0.26)], fill=255, width=w)
        for i in range(3):
            for j in range(2):
                d.rectangle((*P(0.22 + i * 0.22, 0.5 + j * 0.18), *P(0.34 + i * 0.22, 0.6 + j * 0.18)), fill=255)
    elif name in ("chat", "phone"):
        d.rounded_rectangle((*P(0.06, 0.1), *P(0.94, 0.72)), int(S * 0.2), fill=255)
        d.polygon([P(0.2, 0.62), P(0.42, 0.68), P(0.16, 0.92)], fill=255)
        for x in (0.32, 0.5, 0.68):
            d.ellipse((*P(x - 0.06, 0.35), *P(x + 0.06, 0.47)), fill=0)
    elif name == "key":
        d.ellipse((*P(0.06, 0.28), *P(0.46, 0.68)), fill=255)
        d.ellipse((*P(0.17, 0.39), *P(0.35, 0.57)), fill=0)
        d.rectangle((*P(0.42, 0.43), *P(0.94, 0.53)), fill=255)
        d.rectangle((*P(0.72, 0.53), *P(0.8, 0.68)), fill=255)
        d.rectangle((*P(0.85, 0.53), *P(0.93, 0.64)), fill=255)
    elif name == "book":
        d.polygon([P(0.06, 0.2), P(0.47, 0.28), P(0.47, 0.88), P(0.06, 0.8)], fill=255)
        d.polygon([P(0.94, 0.2), P(0.53, 0.28), P(0.53, 0.88), P(0.94, 0.8)], fill=255)
    elif name == "kitchen":
        d.rounded_rectangle((*P(0.16, 0.42), *P(0.84, 0.88)), int(S * 0.08), fill=255)
        d.rectangle((*P(0.1, 0.36), *P(0.9, 0.44)), fill=255)
        d.rectangle((*P(0.04, 0.5), *P(0.18, 0.58)), fill=255)
        d.rectangle((*P(0.82, 0.5), *P(0.96, 0.58)), fill=255)
        for x in (0.36, 0.5, 0.64):
            d.line([P(x, 0.08), P(x + 0.03, 0.18), P(x, 0.28)], fill=255, width=int(w * 0.7))
    elif name == "coffee":
        d.rounded_rectangle((*P(0.12, 0.38), *P(0.7, 0.9)), int(S * 0.1), fill=255)
        d.arc((*P(0.58, 0.46), *P(0.92, 0.76)), 270, 90, fill=255, width=w)
        for x in (0.28, 0.42, 0.56):
            d.line([P(x, 0.08), P(x + 0.03, 0.18), P(x, 0.3)], fill=255, width=int(w * 0.7))
    elif name == "clock":
        d.ellipse((*P(0.06, 0.06), *P(0.94, 0.94)), outline=255, width=w)
        d.line([P(0.5, 0.5), P(0.5, 0.24)], fill=255, width=w)
        d.line([P(0.5, 0.5), P(0.7, 0.6)], fill=255, width=w)
    elif name == "web":
        d.rounded_rectangle((*P(0.06, 0.14), *P(0.94, 0.86)), int(S * 0.1), outline=255, width=w)
        d.rectangle((*P(0.06, 0.16), *P(0.94, 0.34)), fill=255)
        for x in (0.16, 0.26, 0.36):
            d.ellipse((*P(x - 0.035, 0.215), *P(x + 0.035, 0.285)), fill=0)
        d.rounded_rectangle((*P(0.18, 0.46), *P(0.48, 0.74)), int(S * 0.03), fill=255)
        for y in (0.48, 0.6, 0.72):
            d.line([P(0.56, y), P(0.82, y)], fill=255, width=int(w * 0.8))
    elif name == "cart":
        d.line([P(0.04, 0.16), P(0.18, 0.16), P(0.3, 0.64), P(0.82, 0.64), P(0.92, 0.3), P(0.24, 0.3)], fill=255, width=w, joint="curve")
        for x in (0.36, 0.74):
            d.ellipse((*P(x - 0.08, 0.74), *P(x + 0.08, 0.9)), fill=255)
    elif name == "layers":
        for k, y in enumerate((0.62, 0.46, 0.3)):
            pts = [P(0.5, y - 0.2), P(0.94, y), P(0.5, y + 0.2), P(0.06, y)]
            if k < 2:
                d.polygon(pts, outline=255, width=w)
            else:
                d.polygon(pts, fill=255)
    elif name == "bolt":
        d.polygon([P(0.6, 0.04), P(0.16, 0.56), P(0.46, 0.56), P(0.38, 0.96), P(0.84, 0.42), P(0.54, 0.42)], fill=255)
    elif name == "gear":
        for i in range(8):
            a = i * math.pi / 4
            cx, cy = 0.5 + 0.36 * math.cos(a), 0.5 + 0.36 * math.sin(a)
            d.rounded_rectangle((*P(cx - 0.09, cy - 0.09), *P(cx + 0.09, cy + 0.09)), int(S * 0.025), fill=255)
        d.ellipse((*P(0.17, 0.17), *P(0.83, 0.83)), fill=255)
        d.ellipse((*P(0.37, 0.37), *P(0.63, 0.63)), fill=0)
    elif name == "code":
        d.line([P(0.3, 0.24), P(0.08, 0.5), P(0.3, 0.76)], fill=255, width=int(w * 1.2), joint="curve")
        d.line([P(0.7, 0.24), P(0.92, 0.5), P(0.7, 0.76)], fill=255, width=int(w * 1.2), joint="curve")
        d.line([P(0.58, 0.14), P(0.42, 0.86)], fill=255, width=int(w * 1.1))
    elif name == "chip":
        d.rounded_rectangle((*P(0.22, 0.22), *P(0.78, 0.78)), int(S * 0.08), outline=255, width=w)
        d.rounded_rectangle((*P(0.36, 0.36), *P(0.64, 0.64)), int(S * 0.04), fill=255)
        for t in (0.34, 0.5, 0.66):
            for a, b in (((t, 0.04), (t, 0.2)), ((t, 0.8), (t, 0.96)), ((0.04, t), (0.2, t)), ((0.8, t), (0.96, t))):
                d.line([P(*a), P(*b)], fill=255, width=int(w * 0.8))
    elif name == "chart":
        for i, hgt in enumerate((0.3, 0.52, 0.42, 0.7)):
            x = 0.1 + i * 0.21
            d.rounded_rectangle((*P(x, 0.9 - hgt), *P(x + 0.14, 0.9)), int(S * 0.03), fill=255)
        d.line([P(0.06, 0.94), P(0.94, 0.94)], fill=255, width=int(w * 0.8))
    elif name == "rocket":
        d.polygon([P(0.5, 0.04), P(0.68, 0.3), P(0.68, 0.68), P(0.32, 0.68), P(0.32, 0.3)], fill=255)
        d.ellipse((*P(0.42, 0.28), *P(0.58, 0.44)), fill=0)
        d.polygon([P(0.32, 0.46), P(0.14, 0.72), P(0.32, 0.66)], fill=255)
        d.polygon([P(0.68, 0.46), P(0.86, 0.72), P(0.68, 0.66)], fill=255)
        d.polygon([P(0.4, 0.72), P(0.6, 0.72), P(0.5, 0.96)], fill=255)
    elif name == "search":
        d.ellipse((*P(0.08, 0.08), *P(0.64, 0.64)), outline=255, width=int(w * 1.15))
        d.line([P(0.58, 0.58), P(0.9, 0.9)], fill=255, width=int(w * 1.6))
    elif name == "lock":
        d.rounded_rectangle((*P(0.16, 0.44), *P(0.84, 0.92)), int(S * 0.08), fill=255)
        d.arc((*P(0.28, 0.1), *P(0.72, 0.62)), 180, 360, fill=255, width=w)
        d.line([P(0.28, 0.36), P(0.28, 0.46)], fill=255, width=w)
        d.line([P(0.72, 0.36), P(0.72, 0.46)], fill=255, width=w)
        d.ellipse((*P(0.44, 0.58), *P(0.56, 0.7)), fill=0)
    return m.resize((max(1, int(size)), max(1, int(size))), Image.LANCZOS)


def icon_img(name, size, color):
    m = icon_mask(name, size)
    im = Image.new("RGBA", m.size, tuple(color[:3]) + (0,))
    im.putalpha(m)
    return im


def ink_for(rgb):
    return (20, 18, 16) if (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) > 150 else (255, 255, 255)


def pill(ctx, text, icon=None, size=46, bg=(255, 255, 255, 240), fg=None, icon_bg=None):
    """Rounded label with an optional icon disc - for locations and feature tags."""
    U = ctx.U
    fg = fg or ink_for(bg)
    m = line_mask(text, ctx.font("heavy", size))
    h = int(m.height + 30 * U)
    ic = int(h * 0.76) if icon else 0
    padx, gap = int(26 * U), (int(12 * U) if icon else 0)
    w = m.width + 2 * padx + ic + gap - (int(14 * U) if icon else 0)
    im = Image.new("RGBA", (w, h))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=tuple(bg))
    rtl = is_rtl(text)
    if icon:
        icb = icon_bg or ctx.c["primary"]
        icx = w - int(8 * U) - ic if rtl else int(8 * U)
        disc = Image.new("RGBA", (ic, ic))
        ImageDraw.Draw(disc).ellipse((0, 0, ic - 1, ic - 1), fill=tuple(icb) + (255,))
        g = icon_img(icon, int(ic * 0.58), ink_for(icb))
        disc.alpha_composite(g, ((ic - g.width) // 2, (ic - g.height) // 2))
        im.alpha_composite(disc, (icx, (h - ic) // 2))
        tx = icx - gap - m.width if rtl else icx + ic + gap
    else:
        tx = padx
    lay = Image.new("RGBA", m.size, tuple(fg) + (0,))
    lay.putalpha(m)
    im.alpha_composite(lay, (int(tx), (h - m.height) // 2))
    return finish(im, im.getchannel("A"), 0.45, U=U)


def boxed(ctx, text, size=110, role="display", bg=None, fg=None, max_w=None):
    """Text on solid rounded boxes, one per line (short-form caption style): readable on any photo."""
    U = ctx.U
    bg = tuple(bg or ctx.c["primary"])
    fg = tuple(fg or ink_for(bg))
    max_w = max_w or ctx.W * (0.6 if ctx.land else 0.88)
    padx, pady = int(size * 0.3 * U), int(size * 0.1 * U)
    f = ctx.font(role, size)
    text = wrap_text(str(text), f, max_w - 2 * padx)
    lines = [line_mask(l, f) for l in text.split("\n") if l.strip()]
    wmax = max(m.width for m in lines) + 2 * padx
    if wmax > max_w:
        f = ctx.font(role, size * max_w / wmax * 0.98)
        lines = [line_mask(l, f) for l in text.split("\n") if l.strip()]
    gap = int(8 * U)
    boxes = [(m.width + 2 * padx, m.height + 2 * pady) for m in lines]
    W_ = max(b[0] for b in boxes)
    H_ = sum(b[1] for b in boxes) + gap * (len(boxes) - 1)
    im = Image.new("RGBA", (W_, H_))
    d = ImageDraw.Draw(im)
    y = 0
    for m, (bw, bh) in zip(lines, boxes):
        x = (W_ - bw) // 2
        d.rounded_rectangle((x, y, x + bw - 1, y + bh - 1), int(min(bh * 0.28, 30 * U)), fill=bg + (255,))
        lay = Image.new("RGBA", m.size, fg + (0,))
        lay.putalpha(m)
        im.alpha_composite(lay, (x + padx, y + pady))
        y += bh + gap
    return finish(im, im.getchannel("A"), 0.4, U=U)


def scrim_el(ctx, where="bottom", strength=0.6, frac=0.5, t0=0.0):
    """Soft dark gradient behind text so the footage itself stays bright (no full-frame dimming)."""
    H, W = ctx.H, ctx.W
    y = np.linspace(0, 1, H)
    if where == "bottom":
        a = np.clip((y - (1 - frac)) / frac, 0, 1) ** 1.3
    elif where == "top":
        a = np.clip((frac - y) / frac, 0, 1) ** 1.3
    else:
        a = np.exp(-((y - 0.5) / max(0.05, frac / 2)) ** 2)
    a = a * strength
    rows = np.nonzero(a > 0.004)[0]
    if not len(rows):
        return Fn(lambda out, t, bgf: None)
    y0, y1 = int(rows[0]), int(rows[-1]) + 1
    arr = np.zeros((y1 - y0, W, 4), np.uint8)
    arr[..., 3] = (a[y0:y1, None] * 255).astype(np.uint8)
    return Fn(lambda out, t, bgf: over(out, arr, 0, y0, clamp((t - t0) / 0.25 + 0.4)))


def word_sprites(ctx, text, cx, cy, t0, role="display", size=120, grad=True, color=(255, 255, 255), max_w=None,
                 stagger=0.08, anim="pop", d=0.3, shadow=0.7, highlight=()):
    """One sprite per word (RTL aware, shared baseline) for word-by-word reveals. Returns (sprites, height)."""
    U = ctx.U
    max_w = max_w or ctx.W * (0.6 if ctx.land else 0.88)
    f = ctx.font(role, size)
    words = str(text).split()
    masks = [word_mask(w, f) for w in words]
    if masks and max(m.width for m in masks) > max_w:
        f = ctx.font(role, size * max_w / max(m.width for m in masks) * 0.97)
        masks = [word_mask(w, f) for w in words]
    sp = f.getlength(" ")
    total = sum(m.width for m in masks) + sp * max(0, len(masks) - 1)
    nl = max(1, math.ceil(total / max_w))
    target = min(max_w, total / nl * 1.12 + sp)
    lines, cur, cw = [], [], 0
    for w, m in zip(words, masks):
        if cur and cw + sp + m.width > target:
            lines.append(cur)
            cur, cw = [], 0
        cur.append((w, m))
        cw += (sp if cw else 0) + m.width
    if cur:
        lines.append(cur)
    lh = max(m.height for m in masks) * 0.92 if masks else 0
    tot = lh * len(lines)
    rtl = is_rtl(text)
    out, i = [], 0
    y = cy - tot / 2 + lh / 2
    for ln in lines:
        lw = sum(m.width for _, m in ln) + sp * (len(ln) - 1)
        x = cx + lw / 2 if rtl else cx - lw / 2
        for w, m in ln:
            g = grad or any(h and h in w for h in highlight)
            fill = gradient_fill(m, ctx.grad if g is True else g) if g else Image.new("RGBA", m.size, tuple(color) + (0,))
            if not g:
                fill.putalpha(m)
            img = finish(fill, m, shadow, U=U)
            wcx = x - m.width / 2 if rtl else x + m.width / 2
            out.append(Sprite(img, wcx, y, t0 + stagger * i, anim, d))
            x = x - m.width - sp if rtl else x + m.width + sp
            i += 1
        y += lh
    return out, tot


def glass_row(ctx, text, icon, width=None, size=56):
    U = ctx.U
    m = word_mask(text, ctx.font("heavy", size))
    h = int(m.height + 30 * U)
    ic = int(h * 0.72)
    w = int(width or (m.width + ic + 90 * U))
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), int(26 * U), fill=(12, 14, 18, 196), outline=(255, 255, 255, 46),
                        width=max(1, int(2 * U)))
    rtl = is_rtl(text)
    icx = w - int(16 * U) - ic if rtl else int(16 * U)
    disc = Image.new("RGBA", (ic, ic))
    ImageDraw.Draw(disc).ellipse((0, 0, ic - 1, ic - 1), fill=ctx.c["primary"] + (255,))
    g = icon_img(icon or "check", int(ic * 0.58), ink_for(ctx.c["primary"]))
    disc.alpha_composite(g, ((ic - g.width) // 2, (ic - g.height) // 2))
    im.alpha_composite(disc, (icx, (h - ic) // 2))
    lay = Image.new("RGBA", m.size, (255, 255, 255, 0))
    lay.putalpha(m)
    tx = icx - int(22 * U) - m.width if rtl else icx + ic + int(22 * U)
    im.alpha_composite(lay, (int(tx), (h - m.height) // 2))
    return finish(im, im.getchannel("A"), 0.5, U=U)


def place_block(ctx, items, where, gaps):
    """Stack images in the text-safe band: where = bottom | top | center. Returns [(img, cy)]."""
    items = [i for i in items if i is not None]
    if not items:
        return []
    tot = sum(i.height for i in items) + sum(gaps[:len(items) - 1])
    if where == "bottom":
        cy = ctx.bot - tot / 2
    elif where == "top":
        cy = ctx.top + tot / 2
    else:
        cy = ctx.cy
    return stack(items, cy, ctx.bot - ctx.top, gaps)


# ----------------------------------------------------------------- scene builders
def clip_bg(sc, look, zoom=0.05):
    c = sc.get("clip")
    if not c:
        return {"kind": "panel"}
    lk = dict(look)
    lk.update(c.get("look", {}) if isinstance(c, dict) else {})
    lk.update(sc.get("look", {}))
    return {"kind": "clip", "clip": c, "look": lk, "zoom": sc.get("zoom", zoom)}


def fg_for(ctx, bg):
    return ctx.on_panel() if bg["kind"] == "panel" else (255, 255, 255)


def b_hook(sc, ctx):
    U, W = ctx.U, ctx.W
    big, small = sc.get("big", ""), sc.get("small")
    video_text = sc.get("clip") and sc.get("style", "video") == "video"
    els, sfx = [], [(0.04, "impact", float(sc.get("impact", 0.9)))]
    if sc.get("style") == "box":
        bg = clip_bg(sc, {}, 0.1) if sc.get("clip") else {"kind": "panel"}
        els.append(scrim_el(ctx, "center", sc.get("scrim", 0.4), 0.6))
        sm = pill(ctx, small, sc.get("icon"), 50) if small else None
        bx = boxed(ctx, big, sc.get("size", 132))
        lay = place_block(ctx, [sm, bx], sc.get("pos", "center"), [int(-8 * U)])
        if sm:
            els.append(Sprite(lay[0][0], W / 2, lay[0][1], 0.0, "down", 0.28))
        els.append(Sprite(lay[-1][0], W / 2, lay[-1][1], 0.06, sc.get("anim", "pop"), 0.34))
        return bg, els, sfx
    if video_text:
        bg = {"kind": "clip", "clip": sc["clip"], "look": {"grade": True, "vignette": False}, "zoom": 0.08, "hide": True}
        f = ctx.font("display", sc.get("size", 250 if not ctx.land else 210))
        m = text_mask(big, f)
        if m.width > W * 0.9:
            m = m.resize((int(W * 0.9), int(m.height * W * 0.9 / m.width)), Image.LANCZOS)
        gp = int(40 * U)
        mp = Image.new("L", (m.width + 2 * gp, m.height + 2 * gp))
        mp.paste(m, (gp, gp))
        m = mp
        st = max(2, int(5 * U))
        ring = m.filter(ImageFilter.MaxFilter(st * 2 + 1))
        mh = m.height
        sm = ctx.T(small, "heavy", 84) if small else None
        lay = stack([sm, Image.new("L", (m.width, mh))], ctx.cy, ctx.bot - ctx.top, [int(10 * U)])
        ycen = lay[-1][1]
        M0 = np.asarray(m, np.float32) / 255.0
        R0 = np.asarray(ring, np.float32) / 255.0
        col = np.array(ctx.c["primary"], np.float32)
        glow = np.asarray(ring.filter(ImageFilter.GaussianBlur(14 * U)), np.float32) / 255.0 * 0.5

        backdrop = sc.get("backdrop", "blur")

        def vt(out, t, bgf):
            if backdrop == "blur":
                sm_ = Image.fromarray(bgf).resize((max(1, W // 10), max(1, out.shape[0] // 10)), Image.BILINEAR)
                sm_ = sm_.filter(ImageFilter.GaussianBlur(3)).resize((W, out.shape[0]), Image.BILINEAR)
                out[:] = (np.asarray(sm_, np.float32) * 0.22).astype(np.uint8)
            p = clamp(t / 0.45)
            s = 1.22 - 0.22 * e_cubic(p)
            a = clamp(p * 2.5)
            Mm, Rr, Gg = M0, R0, glow
            if abs(s - 1) > 0.004:
                sz = (max(1, int(m.width * s)), max(1, int(m.height * s)))
                Mm = np.asarray(m.resize(sz, Image.BILINEAR), np.float32) / 255.0
                Rr = np.asarray(ring.resize(sz, Image.BILINEAR), np.float32) / 255.0
                Gg = np.asarray(Image.fromarray((glow * 255).astype(np.uint8)).resize(sz), np.float32) / 255.0
            h, w = Mm.shape
            x, y = int(W / 2 - w / 2), int(ycen - h / 2)
            x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, out.shape[0])
            sl = (slice(y0 - y, y1 - y), slice(x0 - x, x1 - x))
            reg = out[y0:y1, x0:x1].astype(np.float32)
            tex = np.clip(bgf[y0:y1, x0:x1].astype(np.float32) * 1.15 + 10, 0, 255)
            g = Gg[sl][..., None] * a
            reg = reg * (1 - g) + col * g
            rr = Rr[sl][..., None] * a
            reg = reg * (1 - rr) + col * rr
            mm = Mm[sl][..., None] * a
            reg = reg * (1 - mm) + tex * mm
            out[y0:y1, x0:x1] = reg.astype(np.uint8)
        els.append(Fn(vt))
        if sm:
            els.append(Sprite(sm, W / 2, lay[0][1], 0.22, "down"))
    else:
        bg = clip_bg(sc, {"dim": 0.6}, 0.08) if sc.get("clip") else {"kind": "black"}
        sm = ctx.T(small, "heavy", 84, color=fg_for(ctx, bg)) if small else None
        bg_im = ctx.T(big, "display", 240, grad=True, glow=ctx.c["primary"])
        lay = stack([sm, bg_im], ctx.cy, ctx.bot - ctx.top, [int(10 * U)])
        if sm:
            els.append(Sprite(lay[0][0], W / 2, lay[0][1], 0.2, "down"))
        els.append(Sprite(lay[-1][0], W / 2, lay[-1][1], 0.0, "zoom", 0.45))
    return bg, els, sfx


def b_stamp(sc, ctx):
    bg = clip_bg(sc, {"bw": sc.get("bw", True), "dim": 0.72}, 0.07)
    line = ctx.T(sc["line"], "heavy", 80, color=fg_for(ctx, bg)) if sc.get("line") else None
    st = make_stamp(ctx, sc.get("stamp", ""))
    lay = stack([line, st], ctx.cy, ctx.bot - ctx.top, [int(6 * ctx.U)])
    els = []
    ts = 0.5 if line else 0.15
    if line:
        els.append(Sprite(lay[0][0], ctx.W / 2, lay[0][1], 0.08, "up"))
    els.append(Sprite(lay[-1][0], ctx.W / 2, lay[-1][1], ts, "slam", 0.16))
    return bg, els, [(ts + 0.12, "impact", 1.0)], {"shake": (ts + 0.16, 0.2)}


def b_logo(sc, ctx):
    U, W = ctx.U, ctx.W
    bg = clip_bg(sc, {"dim": 0.5}, 0.06)
    lg = ctx.logo()
    mw, mh = W * (0.5 if not ctx.land else 0.3), (ctx.bot - ctx.top) * 0.36
    f = min(mw / lg.width, mh / lg.height)
    lg = lg.resize((max(1, int(lg.width * f)), max(1, int(lg.height * f))), Image.LANCZOS)
    lg = finish(lg, lg.getchannel("A"), 0.5, U=U)
    name = ctx.T(sc.get("name", ctx.brand.get("name", "")), "display", 120, grad=True) if (sc.get("name") or ctx.brand.get("name")) else None
    tag = sc.get("tagline", ctx.brand.get("tagline"))
    tg = ctx.T(tag, "body", sc.get("tagline_size", 56), color=fg_for(ctx, bg)) if tag else None
    lay = stack([lg, name, tg], ctx.cy, ctx.bot - ctx.top, [int(30 * U), int(4 * U)])
    els = [Sprite(lay[0][0], W / 2, lay[0][1], 0.05, "zoom", 0.5)]
    la = np.asarray(lay[0][0])[..., 3].astype(np.float32) / 255.0
    lh, lw = la.shape
    yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32)
    field = xx + yy * 0.6
    lcx, lcy = W / 2, lay[0][1]

    def shine(out, t, bgf):
        p = (t - 0.65) / 0.7
        if not 0 <= p <= 1:
            return
        pos = -lw * 0.3 + p * (lw * 1.6 + lh * 0.6)
        band = np.exp(-((field - pos) / (lw * 0.07)) ** 2) * la * 0.75
        rgba = np.zeros((lh, lw, 4), np.uint8)
        rgba[..., :3] = 255
        rgba[..., 3] = (band * 255).astype(np.uint8)
        over(out, rgba, lcx - lw / 2, lcy - lh / 2)
    els.append(Fn(shine))
    if sc.get("burst", ctx.bg_style != "grid"):
        els.insert(0, burst_fx(ctx, W / 2, lay[0][1], 0.12))
    i = 1
    if name:
        els.append(Sprite(lay[i][0], W / 2, lay[i][1], 0.35, "up")); i += 1
    if tg:
        els.append(Sprite(lay[i][0], W / 2, lay[i][1], 0.55, "up"))
    return bg, els, [(0.4, "reveal", 0.6)]


def b_title(sc, ctx):
    U, W = ctx.U, ctx.W
    bg = clip_bg(sc, {"dim": 0.78}, 0.06)
    fg = fg_for(ctx, bg)
    sm = ctx.T(sc["small"], "heavy", 72, color=fg) if sc.get("small") else None
    bigs = [ctx.T(b, "display", sc.get("size", 180), grad=True) for b in [sc.get("big"), sc.get("big2")] if b]
    ul = underline(ctx, max(b.width for b in bigs) * 0.8) if bigs and sc.get("underline", True) else None
    items = ([sm] if sm else []) + bigs + ([ul] if ul else [])
    gaps = ([int(2 * U)] if sm else []) + [int(-18 * U)] * (len(bigs) - 1) + ([int(4 * U)] if ul else [])
    lay = stack(items, ctx.cy, ctx.bot - ctx.top, gaps)
    els, i = [], 0
    if sm:
        els.append(Sprite(lay[0][0], W / 2, lay[0][1], 0.0, sc.get("small_anim", "down"))); i = 1
    for j in range(len(bigs)):
        els.append(Sprite(lay[i][0], W / 2, lay[i][1], 0.06 + 0.14 * j, sc.get("anim", "pop"), 0.32)); i += 1
    if ul:
        els.append(Sprite(lay[i][0], W / 2, lay[i][1], 0.25, "wipe", 0.4))
    return bg, els, []


def b_collage(sc, ctx):
    U, W, H = ctx.U, ctx.W, ctx.H
    clips = [norm_clip(c) for c in sc.get("clips", [])]
    n = len(clips)
    cols, rows = (3, 2) if ctx.land else ((2, 3) if H / W > 1.5 else (2, 2) if n < 6 else (3, 2))
    rows = min(rows, max(1, math.ceil(n / cols)))
    m, g = 24 * U, 14 * U
    cw, ch = (W - 2 * m - (cols - 1) * g) / cols, (H - 2 * m - (rows - 1) * g) / rows
    els = []
    rr = int(22 * U)
    for i, c in enumerate(clips[:cols * rows]):
        r_, k_ = divmod(i, cols)
        im = grab_still(c, int(cw), int(ch), 0.5).convert("RGBA")
        im = pil_look(im.convert("RGB"), dict(ctx.grade, grade=True)).convert("RGBA")
        im.putalpha(rounded_mask(im.width, im.height, rr))
        x = W - m - (k_ + 1) * cw - k_ * g + cw / 2
        y = m + r_ * (ch + g) + ch / 2
        els.append(Sprite(im, x, y, 0.05 * i, "pop", 0.32))
    fg = (255, 255, 255)
    sm = ctx.T(sc["small"], "heavy", 72, color=fg) if sc.get("small") else None
    big = ctx.T(sc["big"], "display", 170, grad=True) if sc.get("big") else None
    lay = stack([sm, big], ctx.cy, ctx.bot - ctx.top, [int(4 * U)])
    if lay:
        th = sum(l[0].height for l in lay) + 220 * U
        band = np.zeros((int(th), W, 4), np.uint8)
        yy = np.linspace(-1, 1, int(th))
        band[..., 3] = (np.clip(1 - np.abs(yy) ** 6, 0, 1) * 225)[:, None].astype(np.uint8)
        band[..., :3] = np.array(ctx.c["bg"] if not ctx.light else (10, 10, 10), np.uint8)
        cyb = (lay[0][1] - lay[0][0].height / 2 + lay[-1][1] + lay[-1][0].height / 2) / 2
        els.append(Sprite(Image.fromarray(band, "RGBA"), W / 2, cyb, 0.35, "fade", 0.3))
        for j, (im, cy) in enumerate(lay):
            els.append(Sprite(im, W / 2, cy, 0.42 + 0.12 * j, "pop" if j else "down"))
    return {"kind": "panel"}, els, [(0.4, "whoosh", 0.4)]


def fmt_num(v, dec):
    return f"{v:,.{dec}f}" if dec else f"{int(round(v)):,}"


def b_counter(sc, ctx):
    U, W = ctx.U, ctx.W
    bg = clip_bg(sc, {"dim": 0.68}, 0.06)
    fg = fg_for(ctx, bg)
    val = float(sc.get("value", 100))
    dec = int(sc.get("decimals", 0 if float(val).is_integer() else 1))
    suf, pre_n = sc.get("suffix", ""), sc.get("num_prefix", "")
    pre = ctx.T(sc["prefix"], "heavy", 70, color=fg) if sc.get("prefix") else None
    lab = ctx.T(sc["label"], "heavy", 64, color=fg, wrap=True) if sc.get("label") else None
    size = sc.get("size", 260)
    full = ctx.T(pre_n + fmt_num(val, dec) + suf, "display", size, grad=True)
    lay = stack([pre, full, lab], ctx.cy, ctx.bot - ctx.top, [int(-6 * U), int(-6 * U)])
    els, i = [], 0
    if pre:
        els.append(Sprite(lay[0][0], W / 2, lay[0][1], 0.05, "down")); i = 1
    ncy, nscale = lay[i][1], lay[i][0].height / full.height
    cache = {}

    def num(out, t, bgf):
        p = clamp((t - 0.12) / 1.25)
        txt = pre_n + fmt_num(val * e_expo(p) if p < 1 else val, dec) + suf
        if txt not in cache:
            im = ctx.T(txt, "display", size * nscale, grad=True)
            cache[txt] = np.asarray(im)
        arr = cache[txt]
        a = clamp((t - 0.05) / 0.2)
        s = 0.8 + 0.2 * e_back(clamp((t - 0.05) / 0.35))
        if abs(s - 1) > 0.004:
            img = Image.fromarray(arr).resize((int(arr.shape[1] * s), int(arr.shape[0] * s)), Image.BILINEAR)
            arr = np.asarray(img)
        over(out, arr, W / 2 - arr.shape[1] / 2, ncy - arr.shape[0] / 2, a)
    els.append(Fn(num))
    if lab:
        els.append(Sprite(lay[-1][0], W / 2, lay[-1][1], 0.3, "up"))
    return bg, els, [(1.3, "ding", 0.55)]


class CardClip:
    """A clip playing inside a rounded card (own decoder)."""

    def __init__(self, ctx, spec, w, h, cx, cy, t0=0.0, anim="up", n=1, radius=36):
        spec = dict(spec)
        spec.setdefault("fit", "cover")
        self.ctx, self.spec, self.w, self.h, self.cx, self.cy = ctx, spec, int(w), int(h), cx, cy
        self.t0, self.anim, self.n, self.r = t0, anim, n, int(radius * ctx.U)
        self.reader = None
        self.mask = np.asarray(rounded_mask(self.w, self.h, self.r), np.uint8)
        self.sh = np.asarray(shadow_box(self.w, self.h, self.r, ctx.U))
        b = Image.new("RGBA", (self.w, self.h))
        ImageDraw.Draw(b).rounded_rectangle((0, 0, self.w - 1, self.h - 1), self.r, outline=ctx.c["primary"] + (170,),
                                            width=max(2, int(3 * ctx.U)))
        self.border = np.asarray(b)

    def draw(self, out, t, ctx, bgf=None):
        if self.reader is None:
            self.reader = Reader(self.spec, self.w, self.h, ctx.fps, self.n, t0=max(0, t),
                                 look=dict(ctx.grade, grade=True, vignette=False), zoom=0.04)
        fr = self.reader.next()
        if t < self.t0:
            return
        p = clamp((t - self.t0) / 0.45)
        e = e_cubic(p)
        a, dy, s = e, (1 - e) * 80 * ctx.U, 0.92 + 0.08 * e
        rgba = np.dstack([fr, self.mask])
        if abs(s - 1) > 0.004:
            img = Image.fromarray(rgba, "RGBA").resize((int(self.w * s), int(self.h * s)), Image.BILINEAR)
            rgba = np.asarray(img)
        h, w = rgba.shape[:2]
        over(out, self.sh, self.cx - self.sh.shape[1] / 2, self.cy - self.sh.shape[0] / 2 + dy, a)
        over(out, rgba, self.cx - w / 2, self.cy - h / 2 + dy, a)
        if s > 0.995:
            over(out, self.border, self.cx - self.w / 2, self.cy - self.h / 2 + dy, a)


def b_checklist(sc, ctx):
    U, W, H = ctx.U, ctx.W, ctx.H
    items = sc.get("items", [])
    fg = ctx.on_panel()
    els, sfx = [], []
    side = W / H >= 0.95
    rows = [ctx.T(it, "heavy", 62, color=fg, max_w=W * (0.38 if side else 0.7)) for it in items]
    title = ctx.T(sc["title"], "display", 96, grad=True) if sc.get("title") else None
    R = 30 * U
    if side:
        ch_ = min(H * 0.78, W * 0.5 / 0.8)
        card = (W * 0.27, H * 0.5, ch_ * 0.8, ch_)
        list_cx = W * 0.66
        list_top = ctx.cy
    else:
        cw = W * 0.66
        rows_h = (max([r.height for r in rows] + [0]) + 18 * U) * len(rows) + (title.height + 20 * U if title else 0)
        chh = max(H * 0.2, min(cw * 1.25, (ctx.bot - ctx.top) * 0.52, ctx.bot - ctx.top - rows_h - 60 * U))
        grp = (chh + 50 * U if sc.get("clip") else 0) + rows_h
        gtop = ctx.top + max(0, (ctx.bot - ctx.top - grp) / 2)
        card = (W / 2, gtop + chh / 2, cw, chh)
        list_cx = W / 2
        list_top = None
    if sc.get("clip"):
        els.append(CardClip(ctx, norm_clip(sc["clip"]), card[2], card[3], card[0], card[1], 0.0, n=int(sc["_dur"] * ctx.fps)))
    rh = max(r.height for r in rows) + 18 * U if rows else 0
    block_h = (title.height + 20 * U if title else 0) + rh * len(rows)
    if side:
        y = list_top - block_h / 2
    else:
        y = card[1] + card[3] / 2 + 50 * U if sc.get("clip") else ctx.cy - block_h / 2
    if title:
        els.append(Sprite(title, list_cx, y + title.height / 2, 0.25, "up"))
        y += title.height + 20 * U
    widest = max([r.width for r in rows] + [1]) + 2 * R + 20 * U
    for i, r in enumerate(rows):
        ti = 0.5 + 0.7 * i
        rtl = is_rtl(items[i])
        cy = y + rh * i + rh / 2
        icx = list_cx + widest / 2 - R if rtl else list_cx - widest / 2 + R
        tx = icx - R - 14 * U - r.width / 2 if rtl else icx + R + 14 * U + r.width / 2

        def icon(out, t, bgf, ti=ti, icx=icx, cy=cy):
            if t < ti:
                return
            p = clamp((t - ti) / 0.25)
            s = 0.5 + 0.5 * e_back(p)
            pc = clamp((t - ti - 0.22) / 0.22)
            im = check_icon(ctx, R * s, pc, pc > 0)
            over(out, np.asarray(im), icx - im.width / 2, cy - im.height / 2, clamp(p * 3))
        els.append(Fn(icon))
        els.append(Sprite(r, tx, cy, ti + 0.1, "right" if rtl else "left", 0.35))
        sfx.append((ti + 0.22, "pop", 0.65))
    return {"kind": "panel"}, els, sfx


def b_testimonial(sc, ctx):
    U, W = ctx.U, ctx.W
    bg = clip_bg(sc, {"dim": 0.45, "blur": 14}, 0.05)
    cw = W * (0.55 if ctx.land else 0.9)
    q = ctx.T(sc.get("quote", ""), "body", 62, color=(255, 255, 255), max_w=cw - 90 * U, wrap=True, shadow=0)
    nm = ctx.T(sc.get("name", ""), "heavy", 52, grad=True, shadow=0) if sc.get("name") else None
    rl = ctx.T(sc.get("role", ""), "body", 40, color=ctx.c["muted"], shadow=0) if sc.get("role") else None
    stars = int(sc.get("stars", 5))
    sR = 34 * U
    inner = [Image.new("L", (10, int(sR * 2.2))), q, nm, rl]
    gaps = [int(26 * U), int(20 * U), int(2 * U)]
    content_h = sum(i.height for i in inner if i is not None) + sum(gaps[:len([i for i in inner if i is not None]) - 1])
    ch = content_h + 110 * U
    card = Image.new("RGBA", (int(cw), int(ch)))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), int(36 * U), fill=(12, 12, 14, 205), outline=ctx.c["primary"] + (140,),
                        width=max(2, int(3 * U)))
    qm = ctx.T("”", "display", 220, grad=True, shadow=0)
    card = finish(card, card.getchannel("A"), 0.5, U=U)
    els = [Sprite(card, W / 2, ctx.cy, 0.0, "up", 0.4)]
    top = ctx.cy - ch / 2
    els.append(Sprite(qm, W / 2 + cw / 2 - 80 * U, top + 30 * U, 0.2, "pop"))
    lay = stack(inner, ctx.cy, ch, gaps)
    stimg = star(ctx, sR)
    for k in range(stars):
        x = W / 2 + (k - (stars - 1) / 2) * sR * 2.3
        els.append(Sprite(stimg, x, lay[0][1], 0.35 + 0.08 * k, "pop", 0.3))
    for j, (im, cy) in enumerate(lay[1:]):
        els.append(Sprite(im, W / 2, cy, 0.75 + 0.2 * j, "up"))
    return bg, els, [(0.35 + 0.08 * k + 0.1, "pop", 0.35) for k in range(stars)]


def b_before_after(sc, ctx):
    U, W, H = ctx.U, ctx.W, ctx.H
    bspec = norm_clip(sc.get("before"))
    aspec = norm_clip(sc.get("after"))
    bg = {"kind": "clip", "clip": bspec, "look": {"grade": True}, "zoom": 0.03}
    labels = sc.get("labels", ["לפני", "אחרי"])
    tw = sc.get("wipe_at", 1.2)
    st = {"r": None}
    lab = [ctx.T(l, "heavy", 60, color=(255, 255, 255), shadow=0) for l in labels]

    def pill(im, color):
        w, h = int(im.width + 50 * U), int(im.height + 24 * U)
        p = Image.new("RGBA", (w, h))
        ImageDraw.Draw(p).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=color)
        p.alpha_composite(im, ((w - im.width) // 2, (h - im.height) // 2))
        return np.asarray(finish(p, p.getchannel("A"), 0.5, U=U))
    pills = [pill(lab[0], (20, 20, 20, 200)), pill(lab[1], ctx.c["primary2"] + (230,))]

    def wipe(out, t, bgf):
        if st["r"] is None:
            st["r"] = Reader(aspec, W, H, ctx.fps, int(sc["_dur"] * ctx.fps), t0=max(0, t), look={"grade": True}, zoom=0.03)
        af = st["r"].next()
        p = e_inout(clamp((t - tw) / 0.9))
        x = int(W * (1 - p))
        if p > 0:
            out[:, x:] = af[:, x:]
            lw = max(3, int(6 * U))
            out[:, max(0, x - lw // 2):min(W, x + lw // 2)] = 255
            if 0 < p < 1:
                hR = int(42 * U)
                hd = Image.new("RGBA", (hR * 2, hR * 2))
                dd = ImageDraw.Draw(hd)
                dd.ellipse((0, 0, hR * 2 - 1, hR * 2 - 1), fill=(255, 255, 255, 255))
                dd.polygon([(hR * 0.55, hR), (hR * 0.85, hR * 0.7), (hR * 0.85, hR * 1.3)], fill=(30, 30, 30, 255))
                dd.polygon([(hR * 1.45, hR), (hR * 1.15, hR * 0.7), (hR * 1.15, hR * 1.3)], fill=(30, 30, 30, 255))
                over(out, np.asarray(hd), x - hR, H / 2 - hR)
        pl = pills[1] if p > 0.5 else pills[0]
        over(out, pl, W / 2 - pl.shape[1] / 2, ctx.top + 20 * U, clamp(t / 0.3))
    els = [Fn(wipe)]
    if sc.get("caption"):
        cap = ctx.T(sc["caption"], "display", 110, grad=True)
        els.append(Sprite(cap, W / 2, ctx.bot - cap.height / 2, tw + 1.0, "pop"))
    return bg, els, [(tw + 0.1, "whoosh", 0.7)]


def b_offer(sc, ctx):
    U, W = ctx.U, ctx.W
    bg = clip_bg(sc, {"dim": 0.6}, 0.06)
    fg = fg_for(ctx, bg)
    badge = None
    if sc.get("badge"):
        t = ctx.T(sc["badge"], "heavy", 58, color=(255, 255, 255), shadow=0)
        w, h = int(t.width + 60 * U), int(t.height + 26 * U)
        badge = Image.new("RGBA", (w, h))
        ImageDraw.Draw(badge).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=ctx.c["accent"])
        badge.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2))
        badge = badge.rotate(4, Image.BICUBIC, expand=True)
        badge = finish(badge, badge.getchannel("A"), 0.5, U=U)
    big = ctx.T(sc.get("big", ""), "display", 200, grad=True)
    sm = ctx.T(sc["small"], "heavy", 68, color=fg) if sc.get("small") else None
    note = ctx.T(sc["note"], "body", 46, color=ctx.c["muted"] if bg["kind"] == "panel" else (235, 235, 235)) if sc.get("note") else None
    lay = stack([badge, big, sm, note], ctx.cy, ctx.bot - ctx.top, [int(14 * U), int(0), int(10 * U)])
    els, i = [], 0
    if badge:
        els.append(Sprite(lay[0][0], W / 2, lay[0][1], 0.05, "pop", 0.35, pulse=0.04)); i = 1
    els.append(Sprite(lay[i][0], W / 2, lay[i][1], 0.3, "slam", 0.16)); i += 1
    if sm:
        els.append(Sprite(lay[i][0], W / 2, lay[i][1], 0.6, "up")); i += 1
    if note:
        els.append(Sprite(lay[i][0], W / 2, lay[i][1], 0.8, "fade"))
    return bg, els, [(0.42, "impact", 0.9)], {"shake": (0.46, 0.18)}


def b_text(sc, ctx):
    U, W = ctx.U, ctx.W
    bg = clip_bg(sc, {"dim": 0.62}, 0.06)
    fg = fg_for(ctx, bg)
    sty = {"small": ("heavy", 70, False), "body": ("body", 58, False), "big": ("display", 170, True),
           "accent": ("display", 130, [ctx.c["accent"], ctx.c["accent"]])}
    ims, anims = [], []
    for ln in sc.get("lines", []):
        ln = {"text": ln} if isinstance(ln, str) else ln
        role, size, grad = sty.get(ln.get("style", "big"), sty["big"])
        ims.append(ctx.T(ln["text"], role, ln.get("size", size), color=fg, grad=grad, wrap=True))
        anims.append(ln.get("anim", "pop" if grad else "up"))
    lay = stack(ims, ctx.cy, ctx.bot - ctx.top, [int(8 * U)] * len(ims))
    els = [Sprite(im, W / 2, cy, 0.05 + 0.22 * j, anims[j]) for j, (im, cy) in enumerate(lay)]
    return bg, els, []


def b_cta(sc, ctx):
    U, W = ctx.U, ctx.W
    bg = clip_bg(sc, {"dim": 0.5, "blur": 12}, 0.05)
    fg = fg_for(ctx, bg)
    br = ctx.brand
    lg = None
    if sc.get("logo", True):
        lg = ctx.logo()
        mw, mh = W * (0.42 if not ctx.land else 0.2), (ctx.bot - ctx.top) * 0.17
        f = min(mw / lg.width, mh / lg.height)
        lg = lg.resize((max(1, int(lg.width * f)), max(1, int(lg.height * f))), Image.LANCZOS)
        lg = finish(lg, lg.getchannel("A"), 0.5, U=U)
    eb = ctx.T(sc["eyebrow"], "heavy", sc.get("eyebrow_size", 46), grad=True) if sc.get("eyebrow") else None
    hl = ctx.T(sc.get("headline", "לפרטים נוספים"), "heavy", sc.get("headline_size", 92), color=fg, wrap=True)
    bt = button(ctx, sc.get("button", "שלחו הודעה בוואטסאפ"), ctx.c["primary"] if sc.get("button_style") == "primary" else None,
                icon=sc.get("button_icon", True)) if sc.get("button", True) else None
    ph = ctx.T(sc.get("phone", br.get("phone", "")), "display", 116, grad=True) if (sc.get("phone") or br.get("phone")) else None
    web = ctx.T(sc.get("website", br.get("website")), "body", 44, color=fg) if (sc.get("website") or br.get("website")) else None
    qr = qr_image(ctx, sc["qr"], int(220 * U)) if sc.get("qr") else None
    items = [lg, eb, hl, bt, ph, web, qr]
    gaps_all = [36, 6, 30, 30, 10, 24]
    present = [i for i, it in enumerate(items) if it is not None]
    gaps = [int(gaps_all[present[k]] * U) for k in range(len(present) - 1)]
    lay = stack([items[i] for i in present], ctx.cy, ctx.bot - ctx.top, gaps)
    pos = dict(zip(present, lay))
    t_tap = sc.get("tap_at", 1.7)
    els, t0 = [], 0.05
    for i in present:
        im, cy = pos[i]
        if i == 3:
            def press(t):
                p = (t - t_tap) / 0.22
                return 1 - 0.07 * math.sin(math.pi * p) if 0 <= p <= 1 else 1.0
            els.append(Sprite(im, W / 2, cy, t0, "pop", 0.35, pulse=0.025, scale_fn=press))
            bcy, bw, bh = cy, im.width, im.height
        else:
            els.append(Sprite(im, W / 2, cy, t0, "zoom" if i == 0 else "up", 0.4))
        t0 += 0.16
    sfx = []
    if bt is not None:
        def tap(out, t, bgf):
            d = t - t_tap
            fx, fy = W / 2 + bw * 0.18, bcy
            if -0.55 < d < 0.35:
                q = clamp((d + 0.55) / 0.5)
                e = e_cubic(q)
                x, y = fx + (1 - e) * 160 * U, fy + (1 - e) * 220 * U
                r = 34 * U * (1 - 0.25 * clamp(d / 0.12) if d > 0 else 1)
                S = int(r * 2 + 30 * U)
                im = Image.new("RGBA", (S, S))
                dd = ImageDraw.Draw(im)
                dd.ellipse((S / 2 - r - 6 * U, S / 2 - r - 6 * U, S / 2 + r + 6 * U, S / 2 + r + 6 * U), fill=(0, 0, 0, 70))
                dd.ellipse((S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r), fill=(255, 255, 255, 235))
                over(out, np.asarray(im), x - S / 2, y - S / 2, clamp(q * 3) * (1 - clamp((d - 0.15) / 0.2)))
            for k in range(2):
                dk = d - 0.08 * k
                if 0 < dk < 0.7:
                    rr = (bh * 0.5) + dk / 0.7 * bw * 0.45
                    S = int(rr * 2 + 8)
                    im = Image.new("RGBA", (S, S))
                    ImageDraw.Draw(im).ellipse((4, 4, S - 4, S - 4), outline=(255, 255, 255, int(200 * (1 - dk / 0.7))),
                                                width=max(2, int(5 * U)))
                    over(out, np.asarray(im), fx - S / 2, fy - S / 2)
        els.append(Fn(tap))
        sfx.append((t_tap, "click", 0.9))
    return bg, els, sfx


def b_showcase(sc, ctx):
    """Bright full-frame footage + label pill + headline + sub in the safe band. The v2 workhorse scene."""
    U, W = ctx.U, ctx.W
    bg = clip_bg(sc, {}, sc.get("zoom", 0.05))
    where, style = sc.get("pos", "bottom"), sc.get("style", "box")
    els, sfx = [], []
    sc_strength = sc.get("scrim", 0.42 if style == "box" else 0.62)
    if sc_strength:
        els.append(scrim_el(ctx, where if where != "center" else "center", sc_strength, 0.5 if where != "center" else 0.5))
    label = pill(ctx, sc["label"], sc.get("icon"), sc.get("label_size", 52)) if sc.get("label") else None
    title_img, words = None, None
    tsize = sc.get("size", 108 if style == "box" else 128)
    if sc.get("title"):
        if style == "box":
            title_img = boxed(ctx, sc["title"], tsize, bg=sc.get("box_color") and hexrgb(sc["box_color"]))
        else:
            words = sc["title"]
            title_img = Image.new("RGBA", (10, int(word_sprites(ctx, words, 0, 0, 0, size=tsize)[1] + 20 * U)))
    sub = ctx.T(sc["sub"], "heavy", sc.get("sub_size", 54), color=(255, 255, 255), wrap=True, shadow=0.85) if sc.get("sub") else None
    lay = place_block(ctx, [label, title_img, sub], where, [int(-10 * U), int(-12 * U)])
    i = 0
    if label:
        els.append(Sprite(lay[0][0], W / 2, lay[0][1], 0.06, "right" if is_rtl(sc["label"]) else "left", 0.32))
        sfx.append((0.08, "pop", 0.45))
        i = 1
    if title_img is not None:
        cy = lay[i][1]
        if words:
            sp, _ = word_sprites(ctx, words, W / 2, cy, 0.16, size=tsize, grad=sc.get("grad", False),
                                 anim=sc.get("anim", "pop"), stagger=sc.get("stagger", 0.08),
                                 highlight=sc.get("highlight", ()), shadow=0.85)
            els += sp
        else:
            els.append(Sprite(lay[i][0], W / 2, cy, 0.14, sc.get("anim", "wipe"), 0.36))
        i += 1
    if sub:
        els.append(Sprite(lay[i][0], W / 2, lay[i][1], 0.42, "up"))
    return bg, els, sfx


def b_features(sc, ctx):
    """Icon + text rows on glass cards over the footage (amenities, benefits, specs)."""
    U, W = ctx.U, ctx.W
    bg = clip_bg(sc, {"dim": sc.get("dim", 0.82)}, 0.05)
    items = [({"text": it, "icon": "check"} if isinstance(it, str) else it) for it in sc.get("items", [])][:6]
    widest = 0
    probe = [line_mask(it["text"], ctx.font("heavy", sc.get("size", 62))) for it in items]
    if probe:
        widest = max(m.width for m in probe)
    rw = min(W * 0.9, max(W * 0.78, widest + 210 * U))
    rows = [glass_row(ctx, it["text"], it.get("icon", "check"), rw, sc.get("size", 62)) for it in items]
    title = boxed(ctx, sc["title"], sc.get("title_size", 86)) if sc.get("title") else None
    els = [scrim_el(ctx, "center", 0.35, 0.8)]
    lay = place_block(ctx, [title] + rows, sc.get("pos", "center"),
                      ([int(6 * U)] if title else []) + [int(-30 * U)] * len(rows))
    sfx, k = [], 0
    if title:
        els.append(Sprite(lay[0][0], W / 2, lay[0][1], 0.05, "pop", 0.32))
        k = 1
    for j, (im, cy) in enumerate(lay[k:]):
        t = 0.35 + 0.32 * j
        rtl = is_rtl(items[j]["text"])
        els.append(Sprite(im, W / 2, cy, t, "right" if rtl else "left", 0.32))
        sfx.append((t + 0.05, "pop", 0.5))
    return bg, els, sfx


def b_location(sc, ctx):
    """Map pin drops onto the footage with a ripple, then the place name and an optional headline."""
    U, W, H = ctx.U, ctx.W, ctx.H
    bg = clip_bg(sc, {}, 0.06)
    els = [scrim_el(ctx, "center", 0.32, 0.7)]
    ps = int(170 * U)
    pin = icon_img("pin", ps, ctx.c["primary"])
    dot = Image.new("RGBA", pin.size)
    r = ps * 0.3 * 0.42
    ImageDraw.Draw(dot).ellipse((ps / 2 - r, ps * 0.38 - r, ps / 2 + r, ps * 0.38 + r), fill=(255, 255, 255, 255))
    pin.alpha_composite(dot)
    pin = finish(pin, pin.getchannel("A"), 0.6, U=U)
    pa = np.asarray(pin)
    pl = pill(ctx, sc["place"], None, 50) if sc.get("place") else None
    title = boxed(ctx, sc["title"], sc.get("size", 100)) if sc.get("title") else None
    lay = place_block(ctx, [pin, pl, title], sc.get("pos", "center"), [int(-6 * U), int(-6 * U)])
    pin_cy = lay[0][1]
    tip_y = pin_cy - pin.height / 2 + int(26 * U) + ps * 0.95
    t_land = 0.42

    def drop(out, t, bgf):
        if t < 0.1:
            return
        p = clamp((t - 0.1) / (t_land - 0.1))
        dy = -(1 - e_back(p, 1.3)) * H * 0.22
        over(out, pa, W / 2 - pa.shape[1] / 2, pin_cy - pa.shape[0] / 2 + dy, clamp(p * 3))
        for k in range(2):
            dk = t - t_land - 0.16 * k
            if 0 < dk < 0.9:
                rx = 24 * U + dk * 280 * U
                ry = rx * 0.32
                S_ = (int(rx * 2 + 12), int(ry * 2 + 12))
                im = Image.new("RGBA", S_)
                ImageDraw.Draw(im).ellipse((6, 6, S_[0] - 6, S_[1] - 6), outline=(255, 255, 255, int(220 * (1 - dk / 0.9))),
                                           width=max(2, int(5 * U)))
                over(out, np.asarray(im), W / 2 - S_[0] / 2, tip_y - S_[1] / 2)
    els.insert(1, Fn(drop))
    i = 1
    if pl:
        els.append(Sprite(lay[i][0], W / 2, lay[i][1], 0.62, "up"))
        i += 1
    if title:
        els.append(Sprite(lay[i][0], W / 2, lay[i][1], 0.82, sc.get("anim", "wipe"), 0.36))
    return bg, els, [(t_land - 0.02, "thump", 0.55), (0.64, "pop", 0.4)]


# ----------------------------------------------------------------- v3 motion graphics: 3D tilt, UI mockups, devices
def _persp_coeffs(dst, src):
    A, B = [], []
    for (x, y), (X, Y) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -X * x, -X * y])
        B.append(X)
        A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
        B.append(Y)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def tilt(img, ry=0.0, rx=0.0, dist=2.4):
    """Fake 3D: rotate a flat RGBA card around its vertical (ry) and horizontal (rx) axis, in degrees."""
    if abs(ry) < 0.05 and abs(rx) < 0.05:
        return img
    w, h = img.size
    d = dist * max(w, h)
    ay, ax = math.radians(ry), math.radians(rx)
    pts = []
    for (x, y) in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        x1, z1 = x * math.cos(ay), x * math.sin(ay)
        y1, z2 = y * math.cos(ax) - z1 * math.sin(ax), y * math.sin(ax) + z1 * math.cos(ax)
        f = d / (d + z2)
        pts.append((x1 * f, y1 * f))
    mx, my = min(p[0] for p in pts), min(p[1] for p in pts)
    dst = [(p[0] - mx, p[1] - my) for p in pts]
    bw, bh = int(math.ceil(max(p[0] for p in dst))) + 1, int(math.ceil(max(p[1] for p in dst))) + 1
    co = _persp_coeffs(dst, [(0, 0), (w, 0), (w, h), (0, h)])
    return img.transform((bw, bh), Image.PERSPECTIVE, co, Image.BICUBIC)


def tilt_mapper(w, h, ry=0.0, rx=0.0, dist=2.4):
    """Point mapping that matches tilt(): (x, y) in the flat w x h image -> position in the tilted image."""
    if abs(ry) < 0.05 and abs(rx) < 0.05:
        return lambda x, y: (x, y)
    d = dist * max(w, h)
    ay, ax = math.radians(ry), math.radians(rx)

    def raw(x, y):
        x1, z1 = x * math.cos(ay), x * math.sin(ay)
        y1, z2 = y * math.cos(ax) - z1 * math.sin(ax), y * math.sin(ax) + z1 * math.cos(ax)
        f = d / (d + z2)
        return x1 * f, y1 * f
    pts = [raw(x, y) for (x, y) in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    mx, my = min(q[0] for q in pts), min(q[1] for q in pts)

    def f_(x, y):
        X, Y = raw(x - w / 2, y - h / 2)
        return X - mx, Y - my
    return f_


def card_quad(cx, cy, w, h, ry=0.0, rx=0.0, dist=2.4):
    """Corners (TL, TR, BR, BL) of a w x h card centred at (cx, cy), rotated in 3D like tilt()."""
    d = dist * max(w, h)
    ay, ax = math.radians(ry), math.radians(rx)
    out = []
    for (x, y) in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        x1, z1 = x * math.cos(ay), x * math.sin(ay)
        y1, z2 = y * math.cos(ax) - z1 * math.sin(ax), y * math.sin(ax) + z1 * math.cos(ax)
        f = d / (d + z2)
        out.append((cx + x1 * f, cy + y1 * f))
    return out


def pop_box(fr):
    """The most detailed block of a screenshot (headline, card, form) for the pop-out effect: (x0, y0, x1, y1)."""
    h, w = fr.shape[:2]
    gw = 96
    gh = max(8, int(gw * h / w))
    g_ = np.asarray(Image.fromarray(fr).convert("L").resize((gw, gh), Image.BILINEAR), np.float32)
    g = np.abs(np.diff(g_, axis=0))[:, :-1] + np.abs(np.diff(g_, axis=1))[:-1]
    sh_, sw_ = g.shape
    I = np.pad(g.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    best, bb = -1.0, (int(w * 0.25), int(h * 0.3), int(w * 0.75), int(h * 0.6))
    for fw in (0.42, 0.52, 0.62):
        bw = max(4, int(sw_ * fw))
        for ar in (0.4, 0.6, 0.85):
            bh = min(int(sh_ * 0.6), max(4, int(bw * ar)))
            for y0 in range(1, sh_ - bh, 2):
                for x0 in range(1, sw_ - bw, 2):
                    tot = I[y0 + bh, x0 + bw] - I[y0, x0 + bw] - I[y0 + bh, x0] + I[y0, x0]
                    cxn = (x0 + bw / 2) / sw_ - 0.5
                    cyn = (y0 + bh / 2) / sh_ - 0.5
                    sc = tot / (bw * bh) ** 0.7 * (1 - 0.9 * (cxn * cxn + cyn * cyn))
                    if y0 < sh_ * 0.1:
                        sc *= 0.6
                    if sc > best:
                        best, bb = sc, (x0, y0, x0 + bw, y0 + bh)
    if best < 0:
        return bb
    # grow each edge while it still cuts through detail (text, photos), so the piece ends on calm space
    x0, y0, x1, y1 = bb
    dens = (I[y1, x1] - I[y0, x1] - I[y1, x0] + I[y0, x0]) / max(1, (x1 - x0) * (y1 - y0))
    lim = 0.35 * dens
    for _ in range(sw_ + sh_):
        grown = False
        if x0 > 0 and g[y0:y1, x0 - 1].mean() > lim and (x1 - x0) < sw_ * 0.85:
            x0 -= 1
            grown = True
        if x1 < sw_ and g[y0:y1, x1 - 1 if x1 == sw_ else x1].mean() > lim and (x1 - x0) < sw_ * 0.85:
            x1 += 1
            grown = True
        if y0 > 0 and g[y0 - 1, x0:x1].mean() > lim and (y1 - y0) < sh_ * 0.7:
            y0 -= 1
            grown = True
        if y1 < sh_ and g[y1 - 1 if y1 == sh_ else y1, x0:x1].mean() > lim and (y1 - y0) < sh_ * 0.7:
            y1 += 1
            grown = True
        if not grown:
            break
    x0, y0, x1, y1 = max(0, x0 - 1), max(0, y0 - 1), min(sw_, x1 + 1), min(sh_, y1 + 1)
    return (int(x0 * w / sw_), int(y0 * h / sh_), int(x1 * w / sw_), int(y1 * h / sh_))


def _txt(ctx, text, role, px, color):
    if role == "mono" and is_rtl(text):
        role = "heavy"
    m = line_mask(text, get_font(ctx.ts[role], px))
    lay = Image.new("RGBA", m.size, tuple(color[:3]) + (0,))
    lay.putalpha(m)
    return lay


def ui_mock(ctx, w, h, kind="dashboard", title="", p=1.0):
    """Illustrative app screen in brand colours (no real data): dashboard | crm | flow | shop. p animates it in."""
    c = ctx.c
    s = w / 600.0
    surf, card, line = (13, 17, 25), (22, 28, 40), (40, 50, 66)
    im = Image.new("RGBA", (w, h), surf + (255,))
    d = ImageDraw.Draw(im)
    pad = int(24 * s)
    d.rectangle((0, 0, w, int(92 * s)), fill=(17, 22, 32, 255))
    if title:
        t = _txt(ctx, title, "heavy", int(34 * s), c["text"])
        im.alpha_composite(t, (w - pad - t.width, int(46 * s - t.height / 2)))
    d.ellipse((pad, int(30 * s), pad + int(34 * s), int(64 * s)), fill=c["primary"] + (255,))
    y0 = int(112 * s)
    q = e_cubic(clamp(p))
    if kind == "dashboard":
        cw = (w - 2 * pad - 2 * int(14 * s)) // 3
        for i in range(3):
            x = w - pad - (i + 1) * cw - i * int(14 * s)
            d.rounded_rectangle((x, y0, x + cw, y0 + int(150 * s)), int(18 * s), fill=card + (255,))
            d.rounded_rectangle((x + int(16 * s), y0 + int(18 * s), x + int(cw * 0.55), y0 + int(32 * s)), 6, fill=line + (255,))
            col = (c["primary"], c["primary2"], c["accent"])[i]
            pts = [(x + int(16 * s) + j * (cw - int(32 * s)) / 7, y0 + int(120 * s) - int((22 + 40 * abs(math.sin(j * 1.3 + i))) * s * q))
                   for j in range(8)]
            d.line(pts, fill=col + (255,), width=max(2, int(5 * s)), joint="curve")
        y1 = y0 + int(176 * s)
        d.rounded_rectangle((pad, y1, w - pad, y1 + int(300 * s)), int(20 * s), fill=card + (255,))
        bars = [0.35, 0.55, 0.45, 0.75, 0.6, 0.9, 0.8]
        bw = (w - 2 * pad - int(60 * s)) / len(bars)
        for j, b in enumerate(bars):
            bh = int(230 * s * b * clamp(q * 1.4 - j * 0.06))
            x = w - pad - int(30 * s) - (j + 1) * bw
            g = pe_grad_box(int(bw * 0.62), max(1, bh), [c["hi"], c["primary"], c["primary2"]])
            im.alpha_composite(g, (int(x + bw * 0.19), y1 + int(270 * s) - bh))
        y2 = y1 + int(326 * s)
        for r in range(6):
            yy = y2 + r * int(86 * s)
            if yy + int(70 * s) > h - pad:
                break
            d.rounded_rectangle((pad, yy, w - pad, yy + int(70 * s)), int(16 * s), fill=card + (255,))
            d.ellipse((w - pad - int(58 * s), yy + int(15 * s), w - pad - int(18 * s), yy + int(55 * s)), fill=line + (255,))
            d.rounded_rectangle((w - pad - int(260 * s), yy + int(22 * s), w - pad - int(76 * s), yy + int(34 * s)), 6, fill=(70, 82, 100, 255))
            d.rounded_rectangle((w - pad - int(200 * s), yy + int(42 * s), w - pad - int(76 * s), yy + int(52 * s)), 5, fill=line + (255,))
            col = (c["primary"], c["primary2"], c["accent"])[r % 3]
            d.rounded_rectangle((pad + int(18 * s), yy + int(22 * s), pad + int(110 * s), yy + int(48 * s)), int(13 * s), fill=col + (255,))
    elif kind == "crm":
        cols = 3
        cw = (w - 2 * pad - (cols - 1) * int(12 * s)) // cols
        for i in range(cols):
            x = w - pad - (i + 1) * cw - i * int(12 * s)
            d.rounded_rectangle((x, y0, x + cw, h - pad), int(16 * s), fill=(17, 22, 32, 255))
            col = (c["primary"], c["primary2"], c["accent"])[i]
            d.rounded_rectangle((x + int(12 * s), y0 + int(14 * s), x + cw - int(12 * s), y0 + int(22 * s)), 4, fill=col + (255,))
            n = 4 - i
            for k in range(n):
                yy = y0 + int(44 * s) + k * int(150 * s)
                off = int((1 - clamp(q * 1.5 - k * 0.15 - i * 0.1)) * 60 * s)
                d.rounded_rectangle((x + int(10 * s), yy + off, x + cw - int(10 * s), yy + int(132 * s) + off), int(14 * s), fill=card + (255,))
                d.rounded_rectangle((x + int(26 * s), yy + int(24 * s) + off, x + cw - int(26 * s), yy + int(38 * s) + off), 6, fill=(78, 90, 110, 255))
                d.rounded_rectangle((x + int(56 * s), yy + int(52 * s) + off, x + cw - int(26 * s), yy + int(62 * s) + off), 5, fill=line + (255,))
                d.rounded_rectangle((x + cw - int(96 * s), yy + int(86 * s) + off, x + cw - int(26 * s), yy + int(110 * s) + off), int(12 * s), fill=col + (200,))
    elif kind == "flow":
        names = ["chat", "people", "calendar", "check"]
        nodes = [(0.72, 0.2), (0.3, 0.42), (0.7, 0.64), (0.32, 0.86)]
        pts = [(w * x, y0 + (h - y0) * y) for x, y in nodes]
        seg = q * (len(pts) - 1)
        for i in range(len(pts) - 1):
            f = clamp(seg - i)
            if f <= 0:
                continue
            (xa, ya), (xb, yb) = pts[i], pts[i + 1]
            curve = [(xa + (xb - xa) * u, ya + (yb - ya) * (3 * u * u - 2 * u * u * u)) for u in np.linspace(0, f, 24)]
            d.line(curve, fill=c["primary"] + (255,), width=max(2, int(6 * s)), joint="curve")
        for i, (x, y) in enumerate(pts):
            if seg < i - 0.05:
                continue
            r = int(70 * s)
            d.rounded_rectangle((x - r * 1.5, y - r, x + r * 1.5, y + r), int(26 * s), fill=card + (255,), outline=c["primary"] + (160,), width=max(1, int(3 * s)))
            g = icon_img(names[i], int(r * 0.9), c["primary"])
            im.alpha_composite(g, (int(x - g.width / 2), int(y - g.height / 2)))
    else:  # shop
        cw = (w - 2 * pad - int(14 * s)) // 2
        for k in range(6):
            i, j = k % 2, k // 2
            x = w - pad - (i + 1) * cw - i * int(14 * s)
            yy = y0 + j * int(330 * s)
            if yy + int(310 * s) > h - pad:
                break
            off = int((1 - clamp(q * 1.6 - k * 0.12)) * 70 * s)
            d.rounded_rectangle((x, yy + off, x + cw, yy + int(310 * s) + off), int(18 * s), fill=card + (255,))
            g = pe_grad_box(cw - int(24 * s), int(190 * s), [c["primary2"], c["primary"]])
            im.alpha_composite(g, (x + int(12 * s), yy + int(12 * s) + off))
            d.rounded_rectangle((x + int(18 * s), yy + int(222 * s) + off, x + cw - int(40 * s), yy + int(238 * s) + off), 6, fill=(78, 90, 110, 255))
            d.rounded_rectangle((x + cw - int(110 * s), yy + int(258 * s) + off, x + cw - int(18 * s), yy + int(290 * s) + off), int(14 * s), fill=c["accent"] + (255,))
    return im


def pe_grad_box(w, h, stops, radius=6):
    m = Image.new("L", (max(1, w), max(1, h)))
    ImageDraw.Draw(m).rounded_rectangle((0, 0, m.width - 1, m.height - 1), min(radius, m.width // 2, m.height // 2), fill=255)
    return gradient_fill(m, stops)


def device_img(ctx, kind, screen, width):
    """Phone or laptop frame around an RGBA screen image (resized to fit)."""
    c = ctx.c
    W = int(width)
    if kind == "laptop":
        sw = int(W * 0.84)
        sh = int(sw * 0.625)
        bez = int(W * 0.022)
        lid = Image.new("RGBA", (sw + 2 * bez, sh + 2 * bez))
        d = ImageDraw.Draw(lid)
        d.rounded_rectangle((0, 0, lid.width - 1, lid.height - 1), int(bez * 1.4), fill=(10, 12, 16, 255), outline=c["primary"] + (110,), width=max(1, bez // 6))
        lid.alpha_composite(ImageOps_fit(screen, (sw, sh)), (bez, bez))
        base_h = int(W * 0.045)
        out = Image.new("RGBA", (W, lid.height + base_h))
        out.alpha_composite(lid, ((W - lid.width) // 2, 0))
        ImageDraw.Draw(out).polygon([(0, out.height - 1), (W - 1, out.height - 1), (W - (W - lid.width) // 2 + bez, lid.height),
                                     ((W - lid.width) // 2 - bez, lid.height)], fill=(34, 40, 52, 255))
        out.info["screen"] = ((W - lid.width) // 2 + bez, bez, sw, sh)
        return out
    h = int(W * 2.05)
    bez = int(W * 0.035)
    out = Image.new("RGBA", (W, h))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((0, 0, W - 1, h - 1), int(W * 0.15), fill=(10, 12, 16, 255), outline=c["primary"] + (120,), width=max(1, int(W * 0.008)))
    sw, sh = W - 2 * bez, h - 2 * bez
    scr = ImageOps_fit(screen, (sw, sh))
    scr.putalpha(Image.fromarray(np.minimum(np.asarray(scr.getchannel("A")), np.asarray(rounded_mask(sw, sh, int(W * 0.12))))))
    out.alpha_composite(scr, (bez, bez))
    pw, ph = int(W * 0.3), int(W * 0.075)
    d.rounded_rectangle(((W - pw) // 2, bez + int(W * 0.03), (W + pw) // 2, bez + int(W * 0.03) + ph), ph // 2, fill=(0, 0, 0, 255))
    out.info["screen"] = (bez, bez, sw, sh)
    return out


def ImageOps_fit(im, size):
    from PIL import ImageOps
    return ImageOps.fit(im.convert("RGBA"), (max(1, size[0]), max(1, size[1])), Image.LANCZOS)


def glow_blob(ctx, w, h, color, alpha=0.55):
    m = Image.new("L", (int(w), int(h)))
    ImageDraw.Draw(m).ellipse((w * 0.15, h * 0.15, w * 0.85, h * 0.85), fill=int(255 * alpha))
    m = m.filter(ImageFilter.GaussianBlur(min(w, h) * 0.12))
    im = Image.new("RGBA", m.size, tuple(color) + (0,))
    im.putalpha(m)
    return np.asarray(im)


def b_device(sc, ctx):
    """Phone/laptop mockup that rises in with a 3D tilt, floats, and plays an animated UI or a screenshot."""
    U, W, H = ctx.U, ctx.W, ctx.H
    bg = clip_bg(sc, {"dim": 0.5, "blur": 10}, 0.04) if sc.get("clip") else {"kind": "panel"}
    kind = sc.get("device", "phone")
    dw = W * (0.5 if kind == "phone" else 0.9) * float(sc.get("device_scale", 1.0)) * (0.62 if ctx.land else 1)
    if kind == "phone":
        sw, sh = int(dw * 0.93), int(dw * 2.05 - dw * 0.07)
    else:
        sw, sh = int(dw * 0.84), int(dw * 0.84 * 0.625)
    shot = Image.open(sc["image"]).convert("RGBA") if sc.get("image") else None
    cache = {}

    def device_at(p):
        k = 24 if shot is not None else int(round(clamp(p) * 24))
        if k not in cache:
            scr = shot if shot is not None else ui_mock(ctx, sw, sh, sc.get("ui", "dashboard"), sc.get("ui_title", ""), k / 24)
            cache[k] = device_img(ctx, kind, scr, dw)
        return cache[k]
    label = pill(ctx, sc["label"], sc.get("icon"), 48) if sc.get("label") else None
    title = None
    if sc.get("title"):
        title = boxed(ctx, sc["title"], sc.get("size", 96)) if sc.get("style", "box") == "box" else \
            ctx.T(sc["title"], "display", sc.get("size", 110), grad=True, wrap=True)
    top_items = [i for i in (label, title) if i is not None]
    lay = place_block(ctx, top_items, "top", [int(-8 * U)]) if top_items else []
    text_bottom = (lay[-1][1] + lay[-1][0].height / 2) if lay else ctx.top
    d0 = device_at(1.0)
    dev_cy = (text_bottom + ctx.H * 0.96) / 2 if not ctx.land else H * 0.55
    gl = glow_blob(ctx, d0.width * 1.5, d0.height * 0.9, ctx.c["primary"], 0.5)
    base_ry = float(sc.get("tilt", -12))

    def draw(out, t, bgf):
        p = clamp(t / 0.75)
        e = e_cubic(p)
        a = clamp(p * 2.5)
        over(out, gl, W / 2 - gl.shape[1] / 2, dev_cy - gl.shape[0] / 2, a * (0.75 + 0.25 * math.sin(t * 2)))
        dev = device_at(clamp((t - 0.35) / 1.3))
        ry = base_ry + (1 - e) * 22 + 2.5 * math.sin(t * 1.3)
        rx = (1 - e) * 14 + 1.5 * math.sin(t * 0.9)
        im = tilt(dev, ry, rx)
        dy = (1 - e) * H * 0.3 + math.sin(t * 1.6) * 8 * U
        over(out, np.asarray(im), W / 2 - im.width / 2, dev_cy - im.height / 2 + dy, a)
    els = [Fn(draw)]
    for j, (im, cy) in enumerate(lay):
        els.append(Sprite(im, W / 2, cy, 0.1 + 0.18 * j, "wipe" if (j == len(lay) - 1 and title is not None and sc.get("style", "box") == "box") else "down", 0.34))
    if sc.get("note"):
        nt = ctx.T(sc["note"], "body", sc.get("note_size", 30), color=ctx.c.get("muted", (160, 170, 185)), shadow=0.4)
        side = W * 0.045 + nt.width / 2 if is_rtl(sc["note"]) else W * 0.955 - nt.width / 2
        els.append(Sprite(nt, side, min(dev_cy + d0.height * 0.22, ctx.bot - nt.height), 0.6, "fade", 0.4))
    return bg, els, [(0.05, "whoosh", 0.45)]


def reveal_line(img, cx, cy, t0, d=0.45):
    """Text line that slides up out of an invisible mask (classic motion-graphics reveal)."""
    arr = np.asarray(img)
    h, w = arr.shape[:2]

    def f(out, t, bgf):
        if t < t0:
            return
        p = e_expo(clamp((t - t0) / d))
        off = int((1 - p) * h * 0.92)
        if h - off <= 0:
            return
        over(out, arr[:h - off], cx - w / 2, cy - h / 2 + off, clamp(p * 1.6))
    return Fn(f)


def b_kinetic(sc, ctx):
    """Kinetic typography: lines rise out of masks one after another; accent lines get the brand gradient and an underline sweep."""
    U, W = ctx.U, ctx.W
    bg = clip_bg(sc, {"dim": 0.45, "blur": 8}, 0.05) if sc.get("clip") else {"kind": "panel"}
    acc = [ctx.c["hi"], ctx.c["primary"], ctx.c["primary2"]]
    imgs, styles, specs = [], [], []
    if sc.get("kicker"):
        imgs.append(ctx.T(sc["kicker"], "mono", sc.get("kicker_size", 38), color=ctx.c["primary"], shadow=0.3))
        styles.append("kicker")
        specs.append({})
    for ln in sc.get("lines", []):
        ln = {"text": ln} if isinstance(ln, str) else ln
        st = ln.get("style", "big")
        if st == "accent":
            im = ctx.T(ln["text"], "display", ln.get("size", 150), grad=acc, wrap=ln.get("wrap", False), glow=ctx.c["primary"])
        elif st == "small":
            im = ctx.T(ln["text"], "heavy", ln.get("size", 62), color=ctx.c["muted"], wrap=ln.get("wrap", False))
        elif st == "mono":
            im = ctx.T(ln["text"], "mono", ln.get("size", 40), color=ctx.c["primary"])
        elif st == "box":
            im = boxed(ctx, ln["text"], ln.get("size", 110))
        else:
            im = ctx.T(ln["text"], "display", ln.get("size", 150), color=ctx.c["text"] if bg["kind"] == "panel" else (255, 255, 255), wrap=ln.get("wrap", False))
        imgs.append(im)
        styles.append(st)
        specs.append(ln)
    lay = place_block(ctx, imgs, sc.get("pos", "center"), [int(-30 * U)] * len(imgs))
    els = []
    if sc.get("clip"):
        els.append(scrim_el(ctx, "center", 0.35, 0.7))
    st0, stag = float(sc.get("start", 0.06)), float(sc.get("stagger", 0.16))
    hot = ctx.energy >= 2
    if hot:
        stag = max(stag, 0.22)
    hits = []
    for j, ((im, cy), st, spec) in enumerate(zip(lay, styles, specs)):
        t0 = st0 + stag * j
        if hot:
            els.append(Sprite(im, W / 2, cy, t0, "slam", 0.26))
            hits.append((t0 + 0.2, "thump", 0.35))
        else:
            els.append(reveal_line(im, W / 2, cy, t0))
        if st == "accent" and sc.get("underline", True) and spec.get("underline", True):
            uw, uh = int(im.width * 0.62), max(3, int(8 * U))
            bar = np.asarray(pe_grad_box(uw, uh, [ctx.c["primary"], ctx.c["primary2"]], uh // 2))
            ty = cy + im.height / 2 - int(18 * U)

            def ul(out, t, bgf, t0=t0, bar=bar, uw=uw, ty=ty):
                p = e_cubic(clamp((t - t0 - 0.3) / 0.45))
                vis = int(uw * p)
                if vis > 1:
                    over(out, bar[:, uw - vis:], W / 2 + uw / 2 - vis, ty)
            els.append(Fn(ul))
    return bg, els, [(st0 + 0.02, "whoosh", 0.3)] + hits


def card_img(ctx, item, w, h, idx):
    U, c = ctx.U, ctx.c
    im = Image.new("RGBA", (int(w), int(h)))
    d = ImageDraw.Draw(im)
    r = int(30 * U)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=(16, 21, 30, 236))
    rg = Image.new("L", im.size)
    ImageDraw.Draw(rg).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, outline=200, width=max(2, int(3 * U)))
    im.alpha_composite(gradient_fill(rg, [c["primary"], c["primary2"]]))
    rtl = item.get("_rtl", is_rtl(item.get("title", "")))
    ic = int(min(w, h) * 0.3)
    disc = Image.new("RGBA", (ic, ic))
    ImageDraw.Draw(disc).ellipse((0, 0, ic - 1, ic - 1), fill=c["primary"] + (255,))
    g = icon_img(item.get("icon", "sparkle"), int(ic * 0.56), ink_for(c["primary"]))
    disc.alpha_composite(g, ((ic - g.width) // 2, (ic - g.height) // 2))
    pad = int(26 * U)
    im.alpha_composite(disc, (im.width - pad - ic if rtl else pad, pad))
    num = _txt(ctx, f"{idx + 1:02d}", "mono", int(30 * U), c["muted"])
    im.alpha_composite(num, (pad if rtl else im.width - pad - num.width, pad))
    f = ctx.font("heavy", item.get("size", 48))
    txt = wrap_text(item.get("title", ""), f, w - 2 * pad)
    tm = text_mask(txt, f)
    if tm.width > w - 2 * pad:
        f = ctx.font("heavy", item.get("size", 48) * (w - 2 * pad) / tm.width * 0.97)
        tm = text_mask(txt, f)
    lay = Image.new("RGBA", tm.size, c["text"] + (0,))
    lay.putalpha(tm)
    sub = _txt(ctx, item["text"], "body", int(30 * U), c["muted"]) if item.get("text") else None
    yb = im.height - pad - (sub.height + int(6 * U) if sub else 0)
    im.alpha_composite(lay, (im.width - pad - tm.width if rtl else pad, yb - tm.height))
    if sub:
        sub = sub if sub.width <= w - 2 * pad else sub.resize((int(w - 2 * pad), int(sub.height * (w - 2 * pad) / sub.width)))
        im.alpha_composite(sub, (im.width - pad - sub.width if rtl else pad, yb + int(6 * U)))
    return finish(im, im.getchannel("A"), 0.55, U=U)


def b_cards(sc, ctx):
    """Grid of glass cards (icon, number, title, line) that rise in with a 3D tilt - services, products, offers."""
    U, W, H = ctx.U, ctx.W, ctx.H
    bg = clip_bg(sc, {"dim": 0.4, "blur": 12}, 0.04) if sc.get("clip") else {"kind": "panel"}
    items = [({"title": it} if isinstance(it, str) else it) for it in sc.get("items", [])][:6]
    cols = int(sc.get("cols", 3 if ctx.land else 2))
    rows = max(1, math.ceil(len(items) / cols))
    gap = 22 * U
    head = []
    if sc.get("kicker"):
        head.append(ctx.T(sc["kicker"], "mono", sc.get("kicker_size", 40), color=ctx.c["primary"], shadow=0.3))
    if sc.get("title"):
        head.append(ctx.T(sc["title"], "display", sc.get("title_size", 96), color=ctx.c["text"], wrap=True))
    hh = sum(i.height for i in head) - 30 * U * max(0, len(head) - 1)
    gw = W * (0.9 if not ctx.land else 0.8)
    cw = (gw - gap * (cols - 1)) / cols
    avail = ctx.bot - ctx.top - hh - 30 * U
    ch = min(cw * float(sc.get("card_ratio", 0.9)), (avail - gap * (rows - 1)) / rows)
    grid_rtl = sc.get("rtl", is_rtl(" ".join(str(it.get("title", "")) for it in items) + str(sc.get("title", ""))))
    imgs = [card_img(ctx, dict(it, _rtl=grid_rtl), cw, ch, i) for i, it in enumerate(items)]
    P = imgs[0].width - cw if imgs else 0
    block = hh + 30 * U + rows * ch + (rows - 1) * gap
    y = ctx.cy - block / 2
    els = []
    for j, im in enumerate(head):
        els.append(reveal_line(im, W / 2, y + im.height / 2, 0.05 + 0.12 * j))
        y += im.height - 30 * U
    y += 30 * U + 26 * U
    sfx = []
    for i, im in enumerate(imgs):
        r_, k_ = divmod(i, cols)
        x = W / 2 + gw / 2 - cw / 2 - k_ * (cw + gap) if grid_rtl else W / 2 - gw / 2 + cw / 2 + k_ * (cw + gap)
        cy = y + r_ * (ch + gap) + ch / 2
        ti = 0.3 + 0.12 * i

        def draw(out, t, bgf, im=im, x=x, cy=cy, ti=ti, i=i):
            if t < ti:
                return
            p = clamp((t - ti) / 0.5)
            e = e_cubic(p)
            img = tilt(im, 0, (1 - e) * 38) if p < 1 else im
            dy = (1 - e) * 110 * U + (math.sin(t * 1.4 + i) * 4 * U if p >= 1 else 0)
            over(out, np.asarray(img), x - img.width / 2, cy - img.height / 2 + dy, clamp(p * 2.2))
        els.append(Fn(draw))
        sfx.append((ti + 0.05, "pop", 0.4))
    if sc.get("highlight", True) and imgs:
        # after the grid lands, a light passes over each card in reading order (keeps a long hold alive)
        g = int(22 * U)
        r = int(30 * U)
        hl = Image.new("RGBA", (int(cw) + 2 * g, int(ch) + 2 * g))
        ImageDraw.Draw(hl).rounded_rectangle((g, g, g + int(cw) - 1, g + int(ch) - 1), r, outline=ctx.c["hi"] + (255,),
                                             width=max(2, int(4 * U)))
        glow = hl.filter(ImageFilter.GaussianBlur(9 * U))
        hl = Image.alpha_composite(glow, hl)
        ha = np.asarray(hl)
        t_hl = 0.3 + 0.12 * len(imgs) + 0.55
        step = float(sc.get("highlight_step", 0.32))
        for i in range(len(imgs)):
            r_, k_ = divmod(i, cols)
            x = W / 2 + gw / 2 - cw / 2 - k_ * (cw + gap) if grid_rtl else W / 2 - gw / 2 + cw / 2 + k_ * (cw + gap)
            cy = y + r_ * (ch + gap) + ch / 2

            def hdraw(out, t, bgf, x=x, cy=cy, i=i):
                u = (t - t_hl - i * step) / 0.7
                if 0 < u < 1:
                    over(out, ha, x - ha.shape[1] / 2, cy - ha.shape[0] / 2 + math.sin(t * 1.4 + i) * 4 * U,
                         math.sin(math.pi * u) ** 2)
            els.append(Fn(hdraw))
    return bg, els, sfx


def b_steps(sc, ctx):
    """Process timeline: a line draws down, numbered nodes pop as it reaches them, each step's text slides in."""
    U, W = ctx.U, ctx.W
    bg = clip_bg(sc, {"dim": 0.4, "blur": 12}, 0.04) if sc.get("clip") else {"kind": "panel"}
    items = [({"title": it} if isinstance(it, str) else it) for it in sc.get("items", [])][:5]
    rtl = is_rtl(" ".join(i.get("title", "") for i in items)) if items else True
    head = ctx.T(sc["title"], "display", sc.get("title_size", 96), color=ctx.c["text"], wrap=True) if sc.get("title") else None
    rows = []
    for it in items:
        t1 = ctx.T(it.get("title", ""), "heavy", it.get("size", 60), color=ctx.c["text"], shadow=0.4, max_w=W * 0.62)
        t2 = ctx.T(it["text"], "body", 36, color=ctx.c["muted"], shadow=0.3, max_w=W * 0.62, wrap=True) if it.get("text") else None
        rows.append((t1, t2))
    rh = max((r[0].height + (r[1].height - 40 * U if r[1] else 0)) for r in rows) if rows else 0
    step = rh + 18 * U
    block = (head.height if head else 0) + step * len(rows)
    y = ctx.cy - block / 2
    els, sfx = [], []
    if head:
        els.append(reveal_line(head, W / 2, y + head.height / 2, 0.05))
        y += head.height
    lx = W * (0.86 if rtl else 0.14)
    nr = 34 * U
    ys = [y + step * i + step / 2 for i in range(len(rows))]
    per = float(sc.get("per", 0.55))
    t_nodes = [0.35 + per * i for i in range(len(rows))]
    bar_w = max(3, int(6 * U))

    def line(out, t, bgf):
        if len(ys) < 2:
            return
        p = clamp((t - t_nodes[0]) / max(0.01, t_nodes[-1] - t_nodes[0]))
        y1 = ys[0] + (ys[-1] - ys[0]) * p
        hgt = int(y1 - ys[0])
        if hgt > 1:
            g = np.asarray(pe_grad_box(bar_w, hgt, [ctx.c["primary"], ctx.c["primary2"]], bar_w // 2))
            over(out, g, lx - bar_w / 2, ys[0])
    els.append(Fn(line))
    for i, (cy, (t1, t2)) in enumerate(zip(ys, rows)):
        ti = t_nodes[i]
        node = Image.new("RGBA", (int(nr * 2 + 8), int(nr * 2 + 8)))
        ImageDraw.Draw(node).ellipse((4, 4, node.width - 4, node.height - 4), fill=ctx.c["primary"] + (255,))
        num = _txt(ctx, f"{i + 1:02d}", "mono", int(28 * U), ink_for(ctx.c["primary"]))
        node.alpha_composite(num, ((node.width - num.width) // 2, (node.height - num.height) // 2))
        node = finish(node, node.getchannel("A"), 0.4, glow=ctx.c["primary"], U=U)
        els.append(Sprite(node, lx, cy, ti, "pop", 0.3))
        tx_edge = lx - nr - 30 * U if rtl else lx + nr + 30 * U
        c1 = tx_edge - t1.width / 2 if rtl else tx_edge + t1.width / 2
        y1 = cy - (t2.height / 2 - 20 * U if t2 else 0)
        els.append(Sprite(t1, c1, y1, ti + 0.06, "right" if rtl else "left", 0.32))
        if t2:
            c2 = tx_edge - t2.width / 2 if rtl else tx_edge + t2.width / 2
            els.append(Sprite(t2, c2, y1 + t1.height / 2 + t2.height / 2 - 44 * U, ti + 0.14, "fade", 0.32))
        sfx.append((ti + 0.02, "pop", 0.45))
    return bg, els, sfx


def burst_fx(ctx, cx, cy, t0=0.12, n=28, color=None):
    """Expanding ring + particles flying out from a point (logo reveals, big moments)."""
    U = ctx.U
    color = color or ctx.c["primary"]
    rng = np.random.default_rng(3)
    dirs = [(math.cos(a), math.sin(a), rng.uniform(0.6, 1.0)) for a in np.linspace(0, 2 * math.pi, n, endpoint=False) + rng.uniform(0, 0.2, n)]
    r = max(3, int(7 * U))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1].astype(np.float32)
    dot = np.zeros((2 * r + 1, 2 * r + 1, 4), np.uint8)
    dot[..., :3] = ctx.c["hi"]
    dot[..., 3] = (np.exp(-(xx ** 2 + yy ** 2) / (r * r * 0.25)) * 255).astype(np.uint8)
    R = min(ctx.W, ctx.H) * 0.48

    def f(out, t, bgf):
        p = (t - t0) / 0.9
        if not 0 <= p <= 1:
            return
        e = e_expo(p)
        rad = 40 * U + e * R
        S = int(rad * 2 + 16)
        if S < 4000:
            im = Image.new("RGBA", (S, S))
            ImageDraw.Draw(im).ellipse((8, 8, S - 8, S - 8), outline=tuple(color) + (int(200 * (1 - p)),), width=max(2, int(5 * U)))
            over(out, np.asarray(im), cx - S / 2, cy - S / 2)
        for (dx, dy, k) in dirs:
            over(out, dot, cx + dx * e * R * k - r, cy + dy * e * R * k - r, (1 - p) * 0.9)
    return Fn(f)


# ----------------------------------------------------------------- v3.1: neon tags, prompt bar, contrast, gallery, proof wall, bundle
def glow_wrap(img, color, U, radius=18, strength=0.9, shadow=0.35):
    """Pad an RGBA image and add a coloured neon glow (two blur radii) plus a soft drop shadow."""
    pad = int(radius * 2.2 * U) + 4
    W_, H_ = img.width + 2 * pad, img.height + 2 * pad
    a = Image.new("L", (W_, H_))
    a.paste(img.getchannel("A"), (pad, pad))
    out = Image.new("RGBA", (W_, H_))
    if shadow:
        sh = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
        sh.putalpha(a.filter(ImageFilter.GaussianBlur(10 * U)).point(lambda v: int(v * shadow)))
        out.alpha_composite(sh, (0, int(6 * U)))
    for r, k in ((radius, strength), (radius * 0.4, strength * 0.8)):
        gl = Image.new("RGBA", (W_, H_), tuple(color) + (0,))
        gl.putalpha(a.filter(ImageFilter.GaussianBlur(max(1, r * U))).point(lambda v, k=k: min(255, int(v * k))))
        out.alpha_composite(gl)
    out.alpha_composite(img, (pad, pad))
    return out


def mark_img(kind, size, color):
    """Stroked ✕ or ✓ mark as an RGBA image."""
    S = max(8, int(size * 4))
    m = Image.new("L", (S, S))
    d = ImageDraw.Draw(m)
    w = max(2, int(S * 0.13))
    if kind == "x":
        d.line([(S * 0.2, S * 0.2), (S * 0.8, S * 0.8)], fill=255, width=w)
        d.line([(S * 0.8, S * 0.2), (S * 0.2, S * 0.8)], fill=255, width=w)
    else:
        d.line([(S * 0.12, S * 0.56), (S * 0.4, S * 0.82), (S * 0.9, S * 0.2)], fill=255, width=w, joint="curve")
    m = m.resize((max(1, int(size)), max(1, int(size))), Image.LANCZOS)
    im = Image.new("RGBA", m.size, tuple(color) + (0,))
    im.putalpha(m)
    return im


def neon_pill(ctx, text, mark=None, color=None, size=60):
    """Neon tag: glowing outline, tinted glass fill, text and an optional ✕/✓ mark at the reading start."""
    U = ctx.U
    color = tuple(color or ctx.c["primary2"])
    tc = tuple(int(c + (255 - c) * 0.35) for c in color)
    m = line_mask(text, ctx.font("heavy", size))
    h = int(m.height + 36 * U)
    mk = int(m.height * 0.62) if mark else 0
    gap = int(16 * U) if mark else 0
    padx = int(30 * U)
    w = m.width + 2 * padx + mk + gap
    bw = max(2, int(4.5 * U))
    im = Image.new("RGBA", (w, h))
    ImageDraw.Draw(im).rounded_rectangle((bw // 2, bw // 2, w - 1 - bw // 2, h - 1 - bw // 2), int(18 * U),
                                         outline=color + (255,), width=bw,
                                         fill=(color[0] // 9, color[1] // 9, color[2] // 9, 150))
    rtl = is_rtl(text)
    txt = Image.new("RGBA", m.size, tc + (0,))
    txt.putalpha(m)
    if mark:
        mx = w - padx - mk if rtl else padx
        im.alpha_composite(mark_img(mark, mk, tc), (int(mx), (h - mk) // 2))
        tx = mx - gap - m.width if rtl else mx + mk + gap
    else:
        tx = padx
    im.alpha_composite(txt, (int(tx), (h - m.height) // 2))
    return glow_wrap(im, color, U)


def rich_text(ctx, text, size=52, role="heavy", color=(255, 255, 255), hl_color=None, highlight=(), max_w=None,
              align="center"):
    """Multi-line text as one image; words containing a highlight term (or digits, with highlight="digits") get hl_color."""
    hl_color = tuple(hl_color or ctx.c["primary"])
    max_w = max_w or ctx.W * 0.8
    f = ctx.font(role, size)
    words = str(text).split()
    if not words:
        return Image.new("RGBA", (2, 2))
    masks = [word_mask(w, f) for w in words]
    if max(m.width for m in masks) > max_w:
        f = ctx.font(role, size * max_w / max(m.width for m in masks) * 0.97)
        masks = [word_mask(w, f) for w in words]
    sp = f.getlength(" ")

    def split(limit):
        ls, cur, cw = [], [], 0
        for w, m in zip(words, masks):
            if cur and cw + sp + m.width > limit:
                ls.append(cur)
                cur, cw = [], 0
            cur.append((w, m))
            cw += (sp if cw else 0) + m.width
        if cur:
            ls.append(cur)
        return ls
    lines = split(max_w)
    if len(lines) > 1:
        lo, hi = max(m.width for m in masks), max_w
        for _ in range(14):
            mid = (lo + hi) / 2
            if len(split(mid)) <= len(lines):
                hi = mid
            else:
                lo = mid
        lines = split(hi + 0.5)
    lh = int(max(m.height for m in masks) * 0.9)
    widths = [sum(m.width for _, m in ln) + sp * (len(ln) - 1) for ln in lines]
    Wt, Ht = int(max(widths)) + 2, lh * (len(lines) - 1) + max(m.height for m in masks)
    im = Image.new("RGBA", (Wt, Ht))
    rtl = is_rtl(text)
    hl = tuple(highlight) if not isinstance(highlight, str) else ()
    y = 0
    for ln, lw in zip(lines, widths):
        x0 = (Wt - lw) / 2 if align == "center" else (Wt - lw if rtl else 0)
        x = x0 + lw if rtl else x0
        for w, m in ln:
            hot = any(h and h in w for h in hl) or (highlight == "digits" and any(ch.isdigit() for ch in w))
            lay = Image.new("RGBA", m.size, (hl_color if hot else tuple(color)) + (0,))
            lay.putalpha(m)
            im.alpha_composite(lay, (int(x - m.width if rtl else x), int(y)))
            x = x - m.width - sp if rtl else x + m.width + sp
        y += lh
    return im


def prompt_fn(ctx, text, cx, cy, t0, cps=14.0, width=None):
    """Chat input bar that slides in and types `text` letter by letter with a blinking caret and a send button.
    Returns (element, sfx list, time the typing ends)."""
    U = ctx.U
    w, h = int(width or ctx.W * 0.82), int(96 * U)
    rtl = is_rtl(text)
    base = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=(250, 250, 252, 255))
    r = int(h * 0.33)
    bcx = h * 0.52 if rtl else w - h * 0.52
    d.ellipse((bcx - r, h / 2 - r, bcx + r, h / 2 + r), fill=ctx.c["primary"] + (255,))
    s_, dr = r * 0.5, (-1 if rtl else 1)
    d.polygon([(bcx + dr * s_, h / 2), (bcx - dr * s_ * 0.7, h / 2 - s_ * 0.85), (bcx - dr * s_ * 0.7, h / 2 + s_ * 0.85)],
              fill=ink_for(ctx.c["primary"]) + (255,))
    pad = int(26 * U)
    base = np.asarray(finish(base, base.getchannel("A"), 0.55, U=U))
    f = ctx.font("heavy", 44)
    tstart = t0 + 0.3
    cache = {}
    t_end = tstart + len(text) / cps

    def draw(out, t, bgf):
        if t < t0:
            return
        p = e_cubic(clamp((t - t0) / 0.3))
        y = cy - base.shape[0] / 2 + (1 - p) * 60 * U
        over(out, base, cx - base.shape[1] / 2, y, p)
        n = int(clamp((t - tstart) * cps, 0, len(text)))
        sub = text[:n]
        if sub not in cache:
            cache[sub] = line_mask(sub, f) if sub.strip() else None
        m = cache[sub]
        right = cx + w / 2 - 44 * U
        left = cx - w / 2 + 44 * U
        tw = m.width if m is not None else 0
        tx = right - tw if rtl else left
        if m is not None:
            lay = Image.new("RGBA", m.size, (28, 26, 40, 0))
            lay.putalpha(m)
            over(out, np.asarray(lay), tx, y + pad + h / 2 - m.height / 2, p)
        if (t < t_end + 0.2) or int(t * 2.2) % 2 == 0:
            cxr = tx - 6 * U if rtl else tx + tw + 4 * U
            car = np.zeros((int(h * 0.5), max(2, int(4 * U)), 4), np.uint8)
            car[..., :3] = ctx.c["primary"]
            car[..., 3] = 255
            over(out, car, cxr, y + pad + h * 0.25, p)
    sfx = [(tstart + k / cps, "type", 0.35) for k in range(0, len(text), 2) if text[k].strip()]
    return Fn(draw), sfx, t_end


def b_contrast(sc, ctx):
    """What you don't need (✕) and the one thing you do (✓): neon tags appear one by one; optional chat bar that types
    a prompt and captions that change when the ✓ lands."""
    U, W = ctx.U, ctx.W
    bg = clip_bg(sc, {"dim": 0.5, "blur": 12}, 0.04) if sc.get("clip") else {"kind": "panel"}
    items = [({"text": it} if isinstance(it, str) else it) for it in sc.get("items", [])]
    per, st = float(sc.get("per", 0.55)), float(sc.get("start", 0.15))
    imgs = []
    for it in items:
        good = it.get("mark", "x") == "check"
        imgs.append(neon_pill(ctx, it["text"], it.get("mark", "x"), ctx.c["primary"] if good else ctx.c["primary2"],
                              it.get("size", 90 if good else 76)))
    band = ctx.bot - ctx.top
    has_prompt = bool(sc.get("prompt"))
    tags_cy = ctx.top + band * (0.27 if has_prompt else 0.42)
    lay = stack(imgs, tags_cy, band * 0.48, [int(6 * U)] * max(0, len(imgs) - 1))
    els, sfx = [], []
    t_check = None
    for i, ((im, cy), it) in enumerate(zip(lay, items)):
        ti = st + per * i
        good = it.get("mark", "x") == "check"
        els.append(Sprite(im, W / 2 + (0 if good else (-1) ** i * 10 * U), cy, ti, "slam" if good else "pop", 0.32 if good else 0.3))
        sfx.append((ti + 0.02, "thump" if good else "pop", 0.6 if good else 0.45))
        if good and t_check is None:
            t_check = ti
    if has_prompt:
        el, psfx, _ = prompt_fn(ctx, sc["prompt"], W / 2, ctx.top + band * 0.66, float(sc.get("prompt_at", st + 0.2)),
                                float(sc.get("cps", 14)))
        els.append(el)
        sfx += psfx
    caps = [c for c in (sc.get("caption"), sc.get("caption2")) if c]
    only2 = bool(sc.get("caption2")) and not sc.get("caption")
    if only2:
        caps = ["", sc["caption2"]]
    if caps:
        hl = sc.get("highlight", ())
        c1 = rich_text(ctx, caps[1] if only2 else caps[0], sc.get("caption_size", 46), "heavy",
                       ctx.on_panel() if bg["kind"] == "panel" else (255, 255, 255), highlight=hl, max_w=W * 0.86)
        c1 = finish(c1, c1.getchannel("A"), 0.6, U=U)
        ccy = ctx.bot - c1.height / 2 - 10 * U
        t_sw = (t_check if t_check is not None else st + per * len(items)) if len(caps) > 1 else 1e9
        c2 = None
        if len(caps) > 1:
            c2 = rich_text(ctx, caps[1], sc.get("caption_size", 46), "heavy", ctx.on_panel() if bg["kind"] == "panel" else (255, 255, 255),
                           highlight=hl, max_w=W * 0.86)
            c2 = np.asarray(finish(c2, c2.getchannel("A"), 0.6, U=U))
        a1 = np.asarray(c1)

        def cap(out, t, bgf):
            if t < 0.2 or (only2 and t < t_sw):
                return
            if only2:
                q = clamp((t - t_sw) / 0.25)
                over(out, c2, W / 2 - c2.shape[1] / 2, ccy - c2.shape[0] / 2 + (1 - e_cubic(q)) * 20 * U, q)
                return
            if t < t_sw:
                over(out, a1, W / 2 - a1.shape[1] / 2, ccy - a1.shape[0] / 2, clamp((t - 0.2) / 0.3))
            else:
                q = clamp((t - t_sw) / 0.25)
                if q < 1:
                    over(out, a1, W / 2 - a1.shape[1] / 2, ccy - a1.shape[0] / 2, 1 - q)
                over(out, c2, W / 2 - c2.shape[1] / 2, ccy - c2.shape[0] / 2 + (1 - e_cubic(q)) * 20 * U, q)
        els.append(Fn(cap))
    return bg, els, sfx


def b_gallery(sc, ctx):
    """Fast portfolio reel inside a 3D phone (or laptop): each item's screenshot or video for `per` seconds, with an
    01/20 counter, a top label (what was asked for) and a bottom tag (what it is). Tall screenshots scroll."""
    U, W, H = ctx.U, ctx.W, ctx.H
    bg = clip_bg(sc, {"dim": 0.5, "blur": 12}, 0.04) if sc.get("clip") else {"kind": "panel"}
    items = [({"src": it} if isinstance(it, str) else dict(it)) for it in sc.get("items", [])]
    n = max(1, len(items))
    per, t_in = float(sc.get("per", 0.7)), 0.45
    kind = sc.get("device", "phone")
    dw = W * ((0.5 if ctx.premium else 0.46) if kind == "phone" else 0.86) * float(sc.get("device_scale", 1.0)) * (0.62 if ctx.land else 1)
    if kind == "phone":
        sw, sh = int(dw * 0.93), int(dw * 2.05 - dw * 0.07)
    else:
        sw, sh = int(dw * 0.84), int(dw * 0.84 * 0.625)
    total = sc.get("_dur", t_in + per * n + 0.6)
    readers, last = {}, {}

    def idx(t):
        return 0 if t < t_in + per else min(n - 1, int((t - t_in) / per))

    def start_of(i):
        return 0.0 if i == 0 else t_in + i * per

    def frame_of(i, t):
        if i not in readers:
            spec = norm_clip(items[i]["src"])
            spec.setdefault("fit", "cover")
            if pops[i] is not None and pops[i]["box"] and is_photo(spec["src"]):
                spec.setdefault("move", "still")
            if is_photo(spec["src"]) and "move" not in spec:
                iw, ih = Image.open(spec["src"]).size
                if ih / iw > (sh / sw) * 1.15:
                    spec["move"], spec["pan_speed"] = "pan_down", spec.get("pan_speed", 0.55)
                else:
                    spec["move"], spec["amount"] = "push", spec.get("amount", 0.06)
            dur_i = (total - start_of(i)) if i == n - 1 else (start_of(i + 1) - start_of(i))
            readers[i] = Reader(spec, sw, sh, ctx.fps, int(dur_i * ctx.fps) + 4, t0=max(0.0, t - start_of(i)),
                                look={}, zoom=0.0, seed=i)
        fr = readers[i].next()
        last[i] = fr
        return fr
    muted = ctx.c.get("muted", (170, 170, 190))
    head_cache = {}

    def heads(i):
        if i not in head_cache:
            it = items[i]
            num = ctx.T(f"{i + 1:02d}", "display", 104, grad=True, shadow=0.4)
            tot = ctx.T(f"/{n:02d}", "heavy", 42, color=muted, shadow=0.3)
            cnt = Image.new("RGBA", (num.width + tot.width - int(30 * U), max(num.height, tot.height)))
            cnt.alpha_composite(num, (0, 0))
            cnt.alpha_composite(tot, (num.width - int(30 * U), num.height - tot.height - int(6 * U)))
            if not it.get("label"):
                lab = None
            elif headline:
                lab = rich_text(ctx, it["label"], sc.get("label_size", 72), "display", ctx.c["text"],
                                highlight=it.get("highlight", ()), max_w=W * 0.86)
                lab = finish(lab, lab.getchannel("A"), 0.6, U=U)
            else:
                lab = pill(ctx, it["label"], None, sc.get("label_size", 44 if ctx.premium else 38), bg=ctx.c["primary"] + (255,),
                           fg=ink_for(ctx.c["primary"]))
            tag = pill(ctx, it["tag"], it.get("icon", "web"), 34, bg=(18, 14, 32, 238), fg=(255, 255, 255)) if it.get("tag") else None
            head_cache[i] = (np.asarray(cnt), np.asarray(lab) if lab else None, np.asarray(tag) if tag else None)
        return head_cache[i]
    kick = ctx.T(sc["kicker"], "mono", 30, color=muted, shadow=0.3) if sc.get("kicker") else None
    kick = np.asarray(kick) if kick is not None else None
    d0 = device_img(ctx, kind, Image.new("RGBA", (sw, sh), (20, 20, 28, 255)), dw)
    headline = sc.get("label_style", "pill" if (kind == "phone" or ctx.land) else "headline") == "headline"
    dev_cy = ctx.top + (ctx.bot - ctx.top) * (0.58 if kind == "phone" else (0.43 if headline else 0.55))
    pop_cfg = sc.get("pop", True if ctx.energy >= 2 else ("alternate" if ctx.premium else None))
    lift_t = 0.55 if ctx.premium else 0.34

    def pop_of(i):
        v = items[i].get("pop")
        if v is None and pop_cfg:
            v = (i % 2 == 0) if pop_cfg == "alternate" else bool(pop_cfg)
        if not v:
            return None
        d_ = v if isinstance(v, dict) else {}
        return {"box": d_.get("box"), "at": float(d_.get("at", 0.3 if ctx.premium else 0.22)),
                "scale": float(d_.get("scale", 1.35 if ctx.premium else 1.8)), "radius": d_.get("radius")}
    pops = [pop_of(i) for i in range(n)]
    pop_boxes = {}

    def draw_pop(out, i, u, fr, dev, im, ry, rx, ox_, oy_, dur_i):
        pp = pops[i]
        if pp is None or u < pp["at"]:
            return
        if i not in pop_boxes:
            src_piece = None
            spec_i = norm_clip(items[i]["src"])
            if pp["box"] and is_photo(spec_i["src"]) and spec_i.get("move", "still") == "still":
                # an exact element box (e.g. measured in the browser): cut the piece from the original at full
                # resolution and map it onto the screen the way Reader frames a still photo
                b = pp["box"]
                from PIL import ImageOps
                src_im = ImageOps.exif_transpose(Image.open(spec_i["src"])).convert("RGB")
                iw, ih = src_im.size
                fh, fw_ = fr.shape[:2]
                sc_ = max(fw_ / iw, fh / ih) * 1.02
                bw_, bh_ = max(fw_, round(iw * sc_)), max(fh, round(ih * sc_))
                fxf, fyf = spec_i.get("focus", [0.5, 0.45])
                cxs = min(max(bw_ * fxf, fw_ / 2), bw_ - fw_ / 2)
                cys = min(max(bh_ * fyf, fh / 2), bh_ - fh / 2)
                mx_, my_ = bw_ / iw, bh_ / ih
                pop_boxes[i] = (int(b[0] * iw * mx_ - (cxs - fw_ / 2)), int(b[1] * ih * my_ - (cys - fh / 2)),
                                int(b[2] * iw * mx_ - (cxs - fw_ / 2)), int(b[3] * ih * my_ - (cys - fh / 2)))
                src_piece = src_im.crop((int(b[0] * iw), int(b[1] * ih), int(b[2] * iw), int(b[3] * ih)))
                if pp.get("radius") is not None:
                    pp["_r"] = max(2, int(float(pp["radius"]) * iw))
            elif pp["box"]:
                b = pp["box"]
                pop_boxes[i] = (int(b[0] * fr.shape[1]), int(b[1] * fr.shape[0]), int(b[2] * fr.shape[1]), int(b[3] * fr.shape[0]))
            else:
                pop_boxes[i] = pop_box(fr)
            pp["_piece"] = src_piece
        x0, y0, x1, y1 = pop_boxes[i]
        if x1 - x0 < 8 or y1 - y0 < 8:
            return
        sx, sy, ssw, ssh = dev.info["screen"]
        kx, ky = ssw / fr.shape[1], ssh / fr.shape[0]
        mp = tilt_mapper(dev.width, dev.height, ry, rx)

        def to_out(a, b):
            X, Y = mp(sx + a * kx, sy + b * ky)
            return X + ox_, Y + oy_
        q0 = [to_out(x0, y0), to_out(x1, y0), to_out(x1, y1), to_out(x0, y1)]
        lp = clamp((u - pp["at"]) / lift_t)
        e, ea = (e_expo(lp), e_cubic(lp)) if ctx.premium else (e_back(lp), e_cubic(lp))
        fa = 1.0 if i == n - 1 else clamp((dur_i - u) / 0.1)
        if fa <= 0:
            return
        w0 = math.hypot(q0[1][0] - q0[0][0], q0[1][1] - q0[0][1])
        h0 = math.hypot(q0[3][0] - q0[0][0], q0[3][1] - q0[0][1])
        wt = min(W * 0.86, w0 * pp["scale"])
        ht = wt * h0 / max(1.0, w0)
        cap = H * (0.42 if ctx.premium else 0.34)
        if ht > cap:
            wt, ht = wt * cap / ht, cap
        side = 1 if i % 2 else -1
        cx0 = sum(q[0] for q in q0) / 4
        cy0 = sum(q[1] for q in q0) / 4
        if ctx.premium:
            # glide out toward the viewer and past the side of the device, with a gentle 3D turn
            out_x = cx0 + (1 if cx0 >= W / 2 else -1) * W * 0.12
            cxt = min(max(out_x, W * 0.03 + wt / 2), W * 0.97 - wt / 2)
            cyt = min(max(cy0 - H * 0.02, ctx.top + ht / 2 + 10 * U), ctx.bot - ht / 2)
            q1 = card_quad(cxt, cyt, wt, ht, (-10 if cxt >= W / 2 else 10), -4)
        else:
            cxt = min(max(W / 2 + side * W * 0.05, W * 0.03 + wt / 2), W * 0.97 - wt / 2)
            # rise until the piece sticks out over the top edge of the device
            cyt = max(ctx.top + ht / 2 + 10 * U, min(cy0 - H * 0.06, oy_ + ht * 0.3))
            q1 = card_quad(cxt, cyt, wt, ht, -side * 14, -8)
        q = [(a[0] + (b[0] - a[0]) * e, a[1] + (b[1] - a[1]) * e) for a, b in zip(q0, q1)]
        # the piece itself (full resolution when cut from the original), with its real corner radius
        if pp.get("_piece") is not None:
            piece = pp["_piece"].convert("RGBA")
        else:
            piece = Image.fromarray(np.ascontiguousarray(fr[y0:y1, x0:x1])).convert("RGBA")
        rr = pp.get("_r") or max(4, int(min(piece.width, piece.height) * 0.06))
        piece.putalpha(rounded_mask(piece.width, piece.height, rr))
        if not ctx.premium:
            ImageDraw.Draw(piece).rounded_rectangle((0, 0, piece.width - 1, piece.height - 1), rr, outline=(255, 255, 255, 235),
                                                    width=max(2, int(3 * piece.width / max(1.0, wt))))
        # the slot it leaves behind: the same rounded shape, darkened
        hx0, hy0 = int(min(x for x, _ in q0)) - 1, int(min(y for _, y in q0)) - 1
        hx1, hy1 = int(max(x for x, _ in q0)) + 2, int(max(y for _, y in q0)) + 2
        hco = _persp_coeffs([(x - hx0, y - hy0) for x, y in q0], [(0, 0), (piece.width, 0), (piece.width, piece.height), (0, piece.height)])
        ha_ = piece.getchannel("A").transform((max(1, hx1 - hx0), max(1, hy1 - hy0)), Image.PERSPECTIVE, hco, Image.BILINEAR)
        hole = Image.new("RGBA", ha_.size, (6, 6, 12, 0))
        hole.putalpha(ha_)
        over(out, np.asarray(hole), hx0, hy0, (0.38 if ctx.premium else 0.75) * ea * fa)
        bx0, by0 = int(min(x for x, _ in q)) - 2, int(min(y for _, y in q)) - 2
        bx1, by1 = int(max(x for x, _ in q)) + 3, int(max(y for _, y in q)) + 3
        co = _persp_coeffs([(x - bx0, y - by0) for x, y in q], [(0, 0), (piece.width, 0), (piece.width, piece.height), (0, piece.height)])
        wp = piece.transform((max(1, bx1 - bx0), max(1, by1 - by0)), Image.PERSPECTIVE, co, Image.BICUBIC)
        pad = int(40 * U)
        al = Image.new("L", (wp.width + 2 * pad, wp.height + 2 * pad))
        al.paste(wp.getchannel("A"), (pad, pad))
        blur = al.filter(ImageFilter.GaussianBlur((26 if ctx.premium else 18) * U))
        shd = Image.new("RGBA", al.size, (0, 0, 0, 0))
        shd.putalpha(blur.point(lambda v: int(v * (0.7 if ctx.premium else 0.6))))
        over(out, np.asarray(shd), bx0 - pad + (14 if ctx.premium else 20) * U * ea, by0 - pad + (40 if ctx.premium else 44) * U * ea, ea * fa)
        glw = Image.new("RGBA", al.size, ctx.c["primary"] + (0,))
        glw.putalpha(al.filter(ImageFilter.GaussianBlur((16 if ctx.premium else 10) * U)).point(lambda v: int(v * (0.3 if ctx.premium else 0.8))))
        over(out, np.asarray(glw), bx0 - pad, by0 - pad, ea * fa)
        over(out, np.asarray(wp), bx0, by0, fa)
    head_y = ctx.top + 40 * U
    gl = glow_blob(ctx, d0.width * 1.5, d0.height * 0.9, ctx.c["primary2"], 0.45)
    swing = float(sc.get("swing", 4 if ctx.premium else 9))

    def draw(out, t, bgf):
        i = idx(t)
        u = t - start_of(i)
        fr = frame_of(i, t)
        if i > 0 and u < 0.14 and (i - 1) in last:
            k = int(e_cubic(u / 0.14) * sh)
            if 0 < k < sh:
                fr = np.concatenate([last[i - 1][k:], fr[:k]], 0)
        p = clamp(t / 0.55)
        e = e_cubic(p)
        a = clamp(p * 2.5)
        over(out, gl, W / 2 - gl.shape[1] / 2, dev_cy - gl.shape[0] / 2, a * 0.9)
        dev = device_img(ctx, kind, Image.fromarray(fr).convert("RGBA"), dw)
        tgt = swing * (1 if i % 2 else -1)
        prv = swing * (1 if (i - 1) % 2 else -1) if i else -swing * 2.4
        ry = prv + (tgt - prv) * (e_inout(clamp(u / 0.6)) if ctx.premium else e_cubic(clamp(u / 0.3))) + 1.2 * math.sin(t * 1.3)
        rx = 4 + (1 - e) * 16 + 1.5 * math.sin(t * 0.9)
        im = tilt(dev, ry, rx)
        dy = (1 - e) * H * 0.3 + math.sin(t * 1.6) * 6 * U
        over(out, np.asarray(im), W / 2 - im.width / 2, dev_cy - im.height / 2 + dy, a)
        pop_args = (i, u, fr, dev, im, ry, rx, W / 2 - im.width / 2, dev_cy - im.height / 2 + dy,
                    (total - start_of(i)) if i == n - 1 else (start_of(i + 1) - start_of(i)))
        cnt, lab, tag = heads(i)
        bump = 1.0 if u > 0.18 else 0.85 + 0.15 * e_back(u / 0.18)
        ha = clamp((t - 0.15) / 0.3)
        if kick is not None:
            over(out, kick, W * 0.06, head_y - kick.shape[0] * 0.7, ha)
        over(out, cnt, W * 0.06, head_y + (kick.shape[0] * 0.25 if kick is not None else 0), ha)
        dev_bot = dev_cy + d0.height * 0.5 + dy
        if headline and lab is not None:
            ly = dev_bot + (tag.shape[0] * 0.5 if tag is not None else 0) + 34 * U + lab.shape[0] / 2
            q = e_cubic(clamp(u / 0.22)) if i > 0 else 1.0
            over(out, lab, W / 2 - lab.shape[1] / 2, ly + (1 - q) * 26 * U, ha * clamp(q * 1.6))
            lab = None
        for arr, x, y in ((lab, W * 0.94, head_y + cnt.shape[0] * 0.55), (tag, W / 2, dev_bot)):
            if arr is None:
                continue
            if bump < 0.999:
                img = Image.fromarray(arr).resize((max(1, int(arr.shape[1] * bump)), max(1, int(arr.shape[0] * bump))), Image.BILINEAR)
                arr = np.asarray(img)
            cx_ = x - arr.shape[1] / 2 if x > W * 0.6 else x
            over(out, arr, cx_ - arr.shape[1] / 2, y - arr.shape[0] / 2, ha)
        draw_pop(out, *pop_args)
    sfx = [(0.05, "whoosh", 0.45)] + [(start_of(i), "click", 0.35) for i in range(1, n)]
    sfx += [(start_of(i) + pops[i]["at"], "whoosh" if ctx.premium else "pop", 0.25 if ctx.premium else 0.5)
            for i in range(n) if pops[i] is not None]
    return bg, [Fn(draw)], sfx


def b_wall(sc, ctx):
    """Proof wall: screenshots tiled on a 3D-tilted wall the camera glides across, a title, and quote cards popping in
    one at a time. Use real screenshots and real quotes only."""
    from PIL import ImageOps
    U, W, H = ctx.U, ctx.W, ctx.H
    bg = {"kind": "panel"}
    srcs = [norm_clip(x)["src"] for x in sc.get("images", [])]
    cols, rows = int(sc.get("cols", 6)), int(sc.get("rows", 5))
    tw = int(W * float(sc.get("tile_w", 0.27)))
    th = int(tw * float(sc.get("tile_ratio", 1.9)))
    gap = int(18 * U)
    canvas = Image.new("RGBA", (cols * (tw + gap) + gap, rows * (th + gap) + gap))
    rmask = rounded_mask(tw, th, int(18 * U))
    tiles = {}
    rng = np.random.default_rng(7)
    order = []
    while len(order) < cols * rows and srcs:
        order += list(rng.permutation(len(srcs)))
    dim = float(sc.get("wall_dim", 0.6))
    for k in range(cols * rows if srcs else 0):
        s_ = srcs[order[k]]
        if s_ not in tiles:
            im = ImageOps.fit(ImageOps.exif_transpose(Image.open(s_)).convert("RGB"), (tw, th), Image.LANCZOS, centering=(0.5, 0.0))
            arr = (np.asarray(im).astype(np.float32) * dim).astype(np.uint8)
            t_ = Image.fromarray(arr).convert("RGBA")
            t_.putalpha(rmask)
            tiles[s_] = t_
        r_, c_ = divmod(k, cols)
        canvas.alpha_composite(tiles[s_], (gap + c_ * (tw + gap), gap + r_ * (th + gap)))
    warped = tilt(canvas, float(sc.get("wall_ry", -14)), float(sc.get("wall_rx", 32)), dist=1.8)
    sc_ = max(W * 1.45 / max(1, warped.width), H * 1.4 / max(1, warped.height))
    warped = warped.resize((max(1, int(warped.width * sc_)), max(1, int(warped.height * sc_))), Image.LANCZOS)
    wall = np.asarray(warped)
    dur = sc.get("_dur", 6.0)
    els = []

    def wall_fn(out, t, bgf):
        q = t / max(0.1, dur)
        x = W / 2 - wall.shape[1] / 2 + (q - 0.5) * W * 0.12
        y = H * 0.56 - wall.shape[0] / 2 + (0.5 - q) * H * 0.22
        over(out, wall, x, y, clamp(t / 0.5))
    els.append(Fn(wall_fn))
    els.append(scrim_el(ctx, "top", 0.75, 0.42))
    head = []
    if sc.get("title"):
        ti = rich_text(ctx, sc["title"], sc.get("title_size", 96), "display", ctx.c["text"],
                       highlight=sc.get("title_highlight", "digits"), max_w=W * 0.88)
        head.append(finish(ti, ti.getchannel("A"), 0.6, U=U))
    if sc.get("sub"):
        head.append(ctx.T(sc["sub"], "heavy", 44, color=ctx.c.get("muted", (200, 200, 210)), shadow=0.6))
    y = ctx.top + 10 * U
    for j, im in enumerate(head):
        els.append(reveal_line(im, W / 2, y + im.height / 2, 0.1 + 0.15 * j))
        y += im.height - 26 * U
    quotes = [({"text": q} if isinstance(q, str) else q) for q in sc.get("quotes", [])]
    t_q0, per_q = float(sc.get("quotes_at", 0.9)), float(sc.get("per_quote", 1.9))
    cw = W * 0.86
    pad = int(34 * U)
    cards = []
    for q in quotes:
        body = rich_text(ctx, q["text"], q.get("size", 50), "heavy", (255, 255, 255), highlight=q.get("highlight", ()),
                         max_w=cw - 2 * pad, align="start")
        hdr = None
        lab = q.get("label", sc.get("quote_label"))
        if lab:
            hdr = rich_text(ctx, lab, 30, "heavy", ctx.c["primary"], max_w=cw - 2 * pad, align="start")
        who = ctx.T("— " + q["who"], "body", 32, color=ctx.c.get("muted", (200, 200, 210)), shadow=0) if q.get("who") else None
        hh = (hdr.height + int(10 * U)) if hdr else 0
        wh = (who.height - int(30 * U)) if who else 0
        ch = int(hh + body.height + wh + 2 * pad)
        card = Image.new("RGBA", (int(cw), ch))
        dd = ImageDraw.Draw(card)
        dd.rounded_rectangle((0, 0, card.width - 1, ch - 1), int(28 * U), fill=(24, 18, 46, 240),
                             outline=ctx.c["primary2"] + (140,), width=max(2, int(2.5 * U)))
        rtl = is_rtl(q["text"])
        yy = pad
        if hdr:
            card.alpha_composite(hdr, (int(card.width - pad - hdr.width) if rtl else pad, yy))
            yy += hdr.height + int(10 * U)
        card.alpha_composite(body, (int(card.width - pad - body.width) if rtl else pad, yy))
        yy += body.height
        if who:
            card.alpha_composite(who, (int(card.width - pad - who.width + 26 * U) if rtl else pad - int(26 * U), yy - int(26 * U)))
        cards.append(np.asarray(finish(card, card.getchannel("A"), 0.6, U=U)))
    qcy = ctx.cy + (ctx.bot - ctx.cy) * 0.2

    def quotes_fn(out, t, bgf):
        if not cards:
            return
        k = int((t - t_q0) // per_q)
        if t < t_q0:
            return
        k = min(k, len(cards) - 1)
        u = t - t_q0 - k * per_q
        arr = cards[k]
        p = clamp(u / 0.3)
        s_ = 0.9 + 0.1 * e_back(p)
        a = clamp(p * 2)
        if k < len(cards) - 1 and u > per_q - 0.15:
            a *= clamp((per_q - u) / 0.15)
        if s_ < 0.999:
            arr = np.asarray(Image.fromarray(arr).resize((max(1, int(arr.shape[1] * s_)), max(1, int(arr.shape[0] * s_))), Image.BILINEAR))
        over(out, arr, W / 2 - arr.shape[1] / 2, qcy - arr.shape[0] / 2, a)
    els.append(Fn(quotes_fn))
    sfx = [(0.05, "whoosh", 0.4)] + [(t_q0 + k * per_q + 0.02, "pop", 0.5) for k in range(len(cards))]
    return bg, els, sfx


def bundle_card(ctx, it, w):
    """Light product card: thumbnail, title, line and tag pills (offers, packages, products)."""
    from PIL import ImageOps
    U = ctx.U
    pad = int(36 * U)
    rtl = is_rtl(it.get("title", "") + it.get("text", ""))
    thumb = None
    if it.get("image") and os.path.exists(it["image"]):
        tsz = int(w * 0.3)
        ti = ImageOps.fit(ImageOps.exif_transpose(Image.open(it["image"])).convert("RGBA"), (tsz, int(tsz * 0.78)), Image.LANCZOS)
        ti.putalpha(Image.fromarray(np.minimum(np.asarray(ti.getchannel("A")), np.asarray(rounded_mask(ti.width, ti.height, int(20 * U))))))
        thumb = finish(ti, ti.getchannel("A"), 0.5, U=U).rotate(-6 if rtl else 6, Image.BICUBIC, expand=True)
    tw_ = w - 2 * pad - (thumb.width - int(40 * U) if thumb else 0)
    title = rich_text(ctx, it.get("title", ""), it.get("size", 66), "display", (26, 20, 44), max_w=tw_, align="start")
    text = rich_text(ctx, it["text"], 36, "body", (78, 70, 98), max_w=tw_, align="start") if it.get("text") else None
    tags = [pill(ctx, (tg if isinstance(tg, str) else tg.get("text", "")), (None if isinstance(tg, str) else tg.get("icon")),
                 30, bg=(26, 20, 44, 255), fg=(255, 255, 255)) for tg in it.get("tags", [])]
    tag_h = max((t_.height for t_ in tags), default=0)
    th_ = title.height + (text.height + int(8 * U) if text else 0) + (tag_h - int(30 * U) if tags else 0)
    h = int(max(th_, thumb.height - int(40 * U) if thumb else 0) + 2 * pad)
    card = Image.new("RGBA", (int(w), h))
    ImageDraw.Draw(card).rounded_rectangle((0, 0, card.width - 1, h - 1), int(34 * U), fill=(251, 246, 236, 255),
                                           outline=(255, 255, 255, 255), width=max(1, int(2 * U)))
    xr = card.width - pad
    y = pad
    for im in (title, text):
        if im is None:
            continue
        card.alpha_composite(im, (int(xr - im.width) if rtl else pad, y))
        y += im.height + int(8 * U)
    x = xr
    for tg in tags:
        px = int(x - tg.width + 26 * U) if rtl else int(pad + (xr - x) - 26 * U)
        card.alpha_composite(tg, (max(0, min(card.width - tg.width, px)), int(y - 26 * U)))
        x -= tg.width - int(40 * U)
    if thumb:
        card.alpha_composite(thumb, (int(pad - 20 * U) if rtl else int(card.width - thumb.width - pad + 20 * U),
                                     max(0, (h - thumb.height) // 2)))
    return finish(card, card.getchannel("A"), 0.6, U=U)


def b_bundle(sc, ctx):
    """Product / package cards that land one after another, joined by a "+" (what the customer gets)."""
    U, W = ctx.U, ctx.W
    bg = clip_bg(sc, {"dim": 0.5, "blur": 12}, 0.04) if sc.get("clip") else {"kind": "panel"}
    items = [it for it in sc.get("items", []) if isinstance(it, dict)][:3]
    cards = [bundle_card(ctx, it, W * 0.86) for it in items]
    plus = None
    if len(cards) > 1:
        r = int(34 * U)
        pl = Image.new("RGBA", (2 * r, 2 * r))
        dd = ImageDraw.Draw(pl)
        dd.ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=ctx.c["primary"] + (255,))
        lw = max(3, int(7 * U))
        dd.line([(r, r * 0.5), (r, r * 1.5)], fill=ink_for(ctx.c["primary"]) + (255,), width=lw)
        dd.line([(r * 0.5, r), (r * 1.5, r)], fill=ink_for(ctx.c["primary"]) + (255,), width=lw)
        plus = finish(pl, pl.getchannel("A"), 0.5, glow=ctx.c["primary"], U=U)
    seq = []
    for i, c in enumerate(cards):
        if i and plus is not None:
            seq.append(plus)
        seq.append(c)
    title = ctx.T(sc["title"], "display", sc.get("title_size", 90), grad=True, wrap=True) if sc.get("title") else None
    items_all = ([title] if title else []) + seq
    lay = stack(items_all, ctx.cy, ctx.bot - ctx.top, [int(-30 * U)] * max(0, len(items_all) - 1))
    els, sfx, t0 = [], [], 0.15
    for im, cy in lay:
        is_plus = plus is not None and im is plus
        els.append(Sprite(im, W / 2, cy, t0, "pop" if is_plus else "up", 0.3 if is_plus else 0.45))
        sfx.append((t0 + 0.02, "pop" if is_plus else "whoosh", 0.5 if is_plus else 0.35))
        t0 += 0.25 if is_plus else 0.45
    return bg, els, sfx


BUILDERS = {"hook": b_hook, "stamp": b_stamp, "logo": b_logo, "title": b_title, "collage": b_collage,
            "showcase": b_showcase, "features": b_features, "location": b_location,
            "kinetic": b_kinetic, "cards": b_cards, "steps": b_steps, "device": b_device,
            "contrast": b_contrast, "gallery": b_gallery, "wall": b_wall, "bundle": b_bundle,
            "counter": b_counter, "checklist": b_checklist, "testimonial": b_testimonial,
            "before_after": b_before_after, "offer": b_offer, "text": b_text, "cta": b_cta}
DEFAULT_DUR = {"kinetic": 2.2, "device": 3.0, "showcase": 2.0, "location": 2.6, "hook": 2.2, "stamp": 1.9, "logo": 2.5, "title": 1.3, "collage": 2.4, "counter": 2.0,
               "testimonial": 4.2, "before_after": 3.6, "offer": 2.8, "text": 2.0, "cta": 5.0}
DEFAULT_TRANS = {"kinetic": "blur", "cards": "zoom", "steps": "slide_up", "device": "zoom",
                 "contrast": "blur", "gallery": "zoom", "wall": "blur", "bundle": "slide_up",
                 "showcase": "slide", "features": "zoom", "location": "zoom", "hook": "cut", "stamp": "glitch", "logo": "zoom", "title": "whip", "collage": "zoom",
                 "counter": "slide_up", "checklist": "zoom", "testimonial": "fade", "before_after": "whip",
                 "offer": "flash", "text": "punch", "cta": "zoom"}
TRANS_SFX = {"zoom": "whoosh", "whip": "whoosh", "slide": "whoosh", "slide_up": "whoosh", "glitch": "glitch", "flash": "thump", "punch": "thump",
             "cube": "whoosh", "spin": "whoosh", "zoom_blur": "whoosh", "slices": "whoosh", "shape": "whoosh", "diamond": "whoosh",
             "push": "whoosh", "zoom_through": "whoosh"}
TRANS_LEN = {"flash": 6, "zoom": 9, "whip": 9, "slide": 9, "slide_up": 9, "glitch": 7, "punch": 8, "fade": 9,
             "leak": 14, "blur": 10, "cube": 15, "spin": 10, "zoom_blur": 10, "slices": 12, "shape": 12, "diamond": 12,
             "push": 14, "zoom_through": 14}
# transitions rotated through automatically when fx energy >= 2 (scenes without their own transition)
CRAZY_TRANS = ["cube", "zoom_blur", "slices", "spin", "shape", "whip", "diamond", "glitch"]
# premium style: one consistent family, chosen by what the next scene is (scenes without their own transition)
PREMIUM_TRANS = {"gallery": "zoom_through", "wall": "zoom_through", "cta": "zoom_through", "logo": "zoom_through",
                 "bundle": "cube", "cards": "cube", "device": "cube"}


# ----------------------------------------------------------------- transitions
def hblur(a, k, axis=1):
    if k < 2:
        return a
    f = a.astype(np.float32)
    h = k // 2
    pad = [(0, 0)] * 3
    pad[axis] = (h + 1, k - h)
    c = np.cumsum(np.pad(f, pad, mode="edge"), axis=axis)
    n = a.shape[axis]
    s1, s2 = [slice(None)] * 3, [slice(None)] * 3
    s1[axis], s2[axis] = slice(k, k + n), slice(0, n)
    return ((c[tuple(s1)] - c[tuple(s2)]) / k).astype(np.uint8)


def scale_frame(fr, s):
    H, W = fr.shape[:2]
    a = 1 / s
    return np.array(Image.fromarray(fr).transform((W, H), Image.AFFINE, (a, 0, W * (1 - a) / 2, 0, a, H * (1 - a) / 2), Image.BILINEAR))


def affine_frame(fr, s=1.0, rot=0.0, dx=0.0, dy=0.0):
    """Scale (about the centre), rotate (degrees) and shift a frame; the scale is raised as needed so no edge shows."""
    H, W = fr.shape[:2]
    a = math.radians(rot)
    ca, sa = math.cos(a), abs(math.sin(a))
    s = max(s, max(ca + H / W * sa, ca + W / H * sa) + 2 * max(abs(dx) / W, abs(dy) / H))
    c, sn = math.cos(-a) / s, math.sin(-a) / s
    cx, cy = W / 2, H / 2
    A = (c, -sn, cx - c * (cx + dx) + sn * (cy + dy), sn, c, cy - sn * (cx + dx) - c * (cy + dy))
    return np.asarray(Image.fromarray(fr).transform((W, H), Image.AFFINE, A, Image.BILINEAR))


_DIST = {}


def _dist_map(W, H, kind):
    """Distance from the frame centre, 1.0 at the corners (circle) or along the diagonal edges (diamond)."""
    key = (W, H, kind)
    if key not in _DIST:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        cx, cy = W / 2, H / 2
        if kind == "diamond":
            _DIST[key] = (np.abs(xx - cx) + np.abs(yy - cy)) / (cx + cy)
        else:
            _DIST[key] = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / math.hypot(cx, cy)
    return _DIST[key]


def bg_energy(out, T, t, ctx):
    """Energy background (fx energy >= 2): light streaks rising across the frame and a ring that bursts from the
    centre on every beat, both in the theme colour and brighter on the beat. T = global time, t = scene time."""
    W, H, U = ctx.W, ctx.H, ctx.U
    w2, h2 = max(2, W // 2), max(2, H // 2)
    if getattr(ctx, "_streaks", None) is None:
        ctx._streaks = np.random.default_rng(3).random((14, 5))
    m = Image.new("L", (w2, h2))
    d = ImageDraw.Draw(m)
    b = beat_env(ctx, t)
    gain = 0.55 + 0.45 * b
    ang = math.radians(-16)
    for prm in ctx._streaks:
        speed = 0.5 + 1.3 * prm[0]
        L = (0.18 + 0.4 * prm[1]) * h2
        x = prm[2] * (w2 * 1.3) - w2 * 0.15
        y = h2 * 1.3 - ((prm[3] + T * speed) % 1.0) * h2 * 1.9
        width = max(1, int((1 + 3 * prm[4]) * U))
        d.line([(x, y), (x + L * math.sin(ang), y + L * math.cos(ang))], fill=int((70 + 130 * prm[4]) * gain), width=width)
    for bt in getattr(ctx, "_beats_now", []):
        x_ = t - bt
        if 0 <= x_ < 0.55:
            r = (0.05 + x_ / 0.55 * 0.85) * h2 * 0.75
            d.ellipse((w2 / 2 - r, h2 / 2 - r, w2 / 2 + r, h2 / 2 + r), outline=int(170 * (1 - x_ / 0.55)), width=max(1, int(3 * U)))
    m = m.filter(ImageFilter.GaussianBlur(1.3)).resize((W, H), Image.BILINEAR)
    col = (np.array(ctx.c["primary"], np.float32) * 0.65 + 255 * 0.35) / 255.0
    add = np.asarray(m, np.float32)[..., None] * col
    return np.clip(out.astype(np.float32) + add, 0, 255).astype(np.uint8)


def camera_fx(out, t, hits, ctx):
    """Energy FX: zoom punches on beats and hits, camera shake and a chromatic split on strong hits."""
    E = ctx.energy / 2.0
    s, dx, dy, rot, ch = 1.0, 0.0, 0.0, 0.0, 0.0
    glitch = None
    for (th, strong, ph) in hits:
        x = t - th
        if x < 0 or x > 0.7:
            continue
        s += (0.08 if strong else (0.045 if strong is None else 0.03)) * E * math.exp(-x / 0.11)
        if strong:
            se = math.exp(-x / 0.14)
            dx += 22 * ctx.U * E * se * (0.6 * math.sin(2 * math.pi * 17 * x + ph) + 0.4 * math.sin(2 * math.pi * 29 * x + 2 * ph))
            dy += 16 * ctx.U * E * se * (0.6 * math.sin(2 * math.pi * 19 * x + 3 * ph) + 0.4 * math.sin(2 * math.pi * 31 * x + ph))
            rot += 1.0 * E * se * math.sin(2 * math.pi * 11 * x + 5 * ph)
            ch = max(ch, 10 * ctx.U * E * math.exp(-x / 0.07))
            if x < 0.07:
                glitch = (x, ph)
    s = min(s, 1.2)
    if s - 1 < 1e-3 and abs(dx) < 0.3 and abs(dy) < 0.3 and abs(rot) < 0.02 and ch < 0.5:
        return out
    out = affine_frame(out, s, rot, dx, dy)
    c = int(round(ch))
    if c >= 1 or glitch:
        o = out.copy()
        if c >= 1:
            o[:, c:, 0] = out[:, :-c, 0]
            o[:, :-c, 2] = out[:, c:, 2]
        if glitch:
            H, W = o.shape[:2]
            g_ = np.random.default_rng(int(glitch[1] * 1000) + int(glitch[0] * 300))
            for _ in range(2 + ctx.energy):
                y0 = int(g_.integers(0, max(1, H - 20)))
                hh = int(g_.integers(max(4, int(H * 0.01)), max(5, int(H * 0.05))))
                o[y0:y0 + hh] = np.roll(o[y0:y0 + hh], int(g_.integers(-50, 50) * ctx.U), 1)
            if ctx.energy >= 3:
                f = 0.3 * math.exp(-glitch[0] / 0.035)
                o = (o * (1 - f) + 255 * f).astype(np.uint8)
        out = o
    return out


def transition(kind, out, prev, k, U, rng, ctx=None):
    m = TRANS_LEN.get(kind, 0)
    if kind == "cut" or k >= m:
        return out
    p = (k + 1) / (m + 1)
    H, W = out.shape[:2]
    if kind == "flash":
        a = (1 - p) ** 2 * 0.9
        return (out * (1 - a) + 255 * a).astype(np.uint8)
    if kind == "punch":
        return scale_frame(out, 1 + 0.12 * (1 - e_cubic(p)))
    if prev is None:
        return out
    if kind == "fade":
        return (prev * (1 - p) + out * p).astype(np.uint8)
    if kind == "zoom":
        e = e_inout(p)
        a = scale_frame(prev, 1 + 0.6 * e)
        b = scale_frame(out, 1.25 - 0.25 * e)
        mix = (a * (1 - e) + b * e).astype(np.uint8)
        return hblur(hblur(mix, int(30 * U * math.sin(math.pi * p)), 1), int(30 * U * math.sin(math.pi * p)), 0)
    if kind == "whip":
        e = e_inout(p)
        off = int(W * e)
        fr = np.empty_like(out)
        fr[:, off:] = prev[:, :W - off]
        fr[:, :off] = out[:, W - off:]
        return hblur(fr, int(120 * U * math.sin(math.pi * p)), 1)
    if kind == "slide_up":
        e = e_inout(p)
        off = int(H * e)
        fr = np.empty_like(out)
        fr[:H - off] = prev[off:]
        fr[H - off:] = out[:off]
        return hblur(fr, int(110 * U * math.sin(math.pi * p)), 0)
    if kind == "slide":
        e = e_inout(p)
        off = int(W * e)
        fr = np.empty_like(out)
        fr[:, off:] = prev[:, :W - off]
        fr[:, :off] = out[:, W - off:]
        return hblur(fr, int(26 * U * math.sin(math.pi * p)), 1)
    if kind == "blur":
        e = e_inout(p)
        mix = (prev * (1 - e) + out * e).astype(np.uint8)
        k = int(46 * U * math.sin(math.pi * p))
        return hblur(hblur(mix, k, 1), k, 0)
    if kind == "leak":
        e = e_inout(p)
        base = prev.astype(np.float32) * (1 - e) + out.astype(np.float32) * e
        sw, sh = max(8, W // 10), max(8, H // 10)
        yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
        xx /= sw
        yy /= sh
        g = np.zeros((sh, sw, 3), np.float32)
        for (bx, by, r, col) in ((-0.3 + 1.5 * p, 0.35, 0.5, (255, 196, 120)), (1.2 - 1.3 * p, 0.72, 0.42, (255, 120, 70))):
            d2 = ((xx - bx) ** 2 + ((yy - by) * 0.6) ** 2) / (r * r)
            g += np.exp(-d2 * 2.2)[..., None] * np.array(col, np.float32)
        g = np.clip(g * (math.sin(math.pi * p) ** 1.3) * 0.95, 0, 255)
        g = np.asarray(Image.fromarray(g.astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32)
        return np.clip(255 - (255 - base) * (255 - g) / 255, 0, 255).astype(np.uint8)
    if kind == "glitch":
        base = prev if p < 0.45 else out
        fr = base.copy()
        sh = int(26 * U * (1 - p))
        fr[..., 0] = np.roll(base[..., 0], sh, 1)
        fr[..., 2] = np.roll(base[..., 2], -sh, 1)
        for _ in range(7):
            y0 = int(rng.integers(0, H - 10))
            h = int(rng.integers(8, max(9, int(H * 0.06))))
            fr[y0:y0 + h] = np.roll(fr[y0:y0 + h], int(rng.integers(-60, 60) * U), 1)
        return fr
    if kind == "push":
        e = e_inout(p)
        off = int(W * e)
        fr = np.empty_like(out)
        fr[:, off:] = prev[:, :W - off]
        fr[:, :off] = out[:, W - off:]
        return hblur(fr, int(60 * U * math.sin(math.pi * p) ** 2), 1)
    if kind == "zoom_through":
        e = e_inout(p)
        a = scale_frame(prev, 1 + 0.4 * e)
        b = scale_frame(out, 1.15 - 0.15 * e)
        m = e_inout(clamp((p - 0.25) / 0.5))
        mix = (a.astype(np.float32) * (1 - m) + b.astype(np.float32) * m).astype(np.uint8)
        k = int(18 * U * math.sin(math.pi * p) ** 2)
        return hblur(hblur(mix, k, 1), k, 0)
    if kind == "cube":
        th = math.pi / 2 * e_inout(p)
        D = 2.2 * W * (1 + 0.3 * math.sin(math.pi * p))
        Zc = D + W / 2

        def proj(x, y, z):
            x2, z2 = x * math.cos(th) - z * math.sin(th), x * math.sin(th) + z * math.cos(th)
            f = D / (Zc + z2)
            return (W / 2 + x2 * f, H / 2 + y * f)
        small = Image.fromarray(out).resize((max(1, W // 24), max(1, H // 24)), Image.BILINEAR)
        canvas = small.resize((W, H), Image.BILINEAR).point(lambda v: int(v * 0.3))
        hw, hh = W / 2, H / 2
        for img, pts, lit in ((prev, [(-hw, -hh, -hw), (hw, -hh, -hw), (hw, hh, -hw), (-hw, hh, -hw)], math.cos(th)),
                              (out, [(-hw, -hh, hw), (-hw, -hh, -hw), (-hw, hh, -hw), (-hw, hh, hw)], math.sin(th))):
            if lit < 0.03:
                continue
            co = _persp_coeffs([proj(*pt) for pt in pts], [(0, 0), (W, 0), (W, H), (0, H)])
            src = Image.fromarray((img.astype(np.float32) * (0.35 + 0.65 * lit)).astype(np.uint8))
            mask = Image.new("L", (W, H), 255).transform((W, H), Image.PERSPECTIVE, co, Image.BILINEAR)
            canvas.paste(src.transform((W, H), Image.PERSPECTIVE, co, Image.BILINEAR), (0, 0), mask)
        return np.asarray(canvas)
    if kind == "spin":
        e = e_inout(p)
        v = math.sin(math.pi * p)
        if p < 0.5:
            src, ang, s = prev, 30 * (2 * e), 1 + 0.45 * (2 * e)
        else:
            src, ang, s = out, -30 * (2 - 2 * e), 1 + 0.45 * (2 - 2 * e)
        acc = np.zeros((H, W, 3), np.float32)
        for d in (-1, 0, 1):
            acc += affine_frame(src, s, ang + d * 6 * v)
        return (acc / 3).astype(np.uint8)
    if kind == "zoom_blur":
        if p < 0.5:
            q, src = p / 0.5, prev
        else:
            q, src = (1 - p) / 0.5, out
        z = 1 + 2.4 * q * q
        acc = np.zeros((H, W, 3), np.float32)
        for j in range(5):
            acc += scale_frame(src, z * (1 + 0.12 * q * j / 4))
        acc /= 5
        fl = 0.4 * math.exp(-((p - 0.5) / 0.1) ** 2)
        return np.clip(acc * (1 - fl) + 255 * fl, 0, 255).astype(np.uint8)
    if kind == "slices":
        n = 6
        fr = prev.copy()
        for j in range(n):
            x0, x1 = W * (n - 1 - j) // n, W * (n - j) // n
            pj = clamp((p - j * 0.07) / (1 - (n - 1) * 0.07))
            if pj <= 0:
                continue
            off = int((1 - e_cubic(pj)) * H) * (1 if j % 2 else -1)
            if off >= 0:
                fr[off:, x0:x1] = out[:H - off, x0:x1]
            else:
                fr[:H + off, x0:x1] = out[-off:, x0:x1]
        return fr
    if kind in ("shape", "diamond"):
        d = _dist_map(W, H, kind)
        r = e_inout(p) * 1.08
        m_ = np.clip((r - d) / 0.006 + 0.5, 0, 1)[..., None]
        fr = prev.astype(np.float32) * (1 - m_) + out.astype(np.float32) * m_
        col = np.array(ctx.c["primary"] if ctx is not None else (255, 255, 255), np.float32)
        a1 = np.clip(1 - np.abs(d - r) / 0.016, 0, 1)[..., None]
        a2 = np.clip(1 - np.abs(d - r * 0.8) / 0.006, 0, 1)[..., None] * 0.9
        fr = fr * (1 - a1) + col * a1
        fr = fr * (1 - a2) + 255 * a2
        return np.clip(fr, 0, 255).astype(np.uint8)
    return out


# ----------------------------------------------------------------- planning
def expand(scenes):
    out = []
    for sc in scenes:
        t = sc.get("type")
        if t == "services":
            for j, it in enumerate(sc.get("items", [])):
                it = {"text": it} if isinstance(it, str) else it
                s = {"type": "title", "small": sc.get("small"), "big": it["text"], "clip": it.get("clip"),
                     "dur": it.get("dur", sc.get("per", 1.1)), "small_anim": "down" if j == 0 else "none",
                     **({"beats": it.get("beats", sc["beats_per"])} if sc.get("beats_per") else {}),
                     "transition": sc.get("transition", "whip" if j == 0 else "punch")}
                if it.get("say") or (j == 0 and sc.get("say")):
                    s["say"] = it.get("say") or sc["say"]
                out.append(s)
        elif t == "stats":
            for j, it in enumerate(sc.get("items", [])):
                s = {"type": "counter", **it}
                s.setdefault("transition", "slide_up")
                if j == 0 and sc.get("say") and not it.get("say"):
                    s["say"] = sc["say"]
                out.append(s)
        else:
            out.append(dict(sc))
    return out


NEEDS_CLIP = {"showcase", "features", "location", "hook", "stamp", "logo", "title", "counter", "checklist", "offer", "text", "cta", "testimonial"}


def assign_clips(scenes, pool):
    pool = [norm_clip(c) for c in pool]
    if not pool:
        return
    i, last = 0, None
    for sc in scenes:
        t = sc["type"]
        if t == "collage" and not sc.get("clips"):
            sc["clips"] = [pool[(i + k) % len(pool)] for k in range(6)]
            i += 6
        elif t in NEEDS_CLIP and "clip" not in sc:
            c = pool[i % len(pool)]
            if last is not None and c["src"] == last and len(pool) > 1:
                i += 1
                c = pool[i % len(pool)]
            sc["clip"] = dict(c)
            i += 1
        if sc.get("clip"):
            last = norm_clip(sc["clip"])["src"]


def detect_beats(y):
    hop, nf = 512, 2048
    if len(y) < nf * 4:
        return np.array([]), 0
    frames = 1 + (len(y) - nf) // hop
    idx = np.arange(nf)[None, :] + hop * np.arange(frames)[:, None]
    S = np.abs(np.fft.rfft(y[idx] * np.hanning(nf), axis=1))
    L = np.log1p(10 * S)
    flux = np.maximum(0, np.diff(L, axis=0)).sum(1)
    fe = SR / hop
    w = int(fe * 0.5)
    flux = np.maximum(0, flux - np.convolve(flux, np.ones(w) / w, "same"))
    env = flux / (flux.max() + 1e-9)
    ac = np.correlate(env, env, "full")[len(env) - 1:]
    lags = np.arange(1, len(ac))
    bpm = 60 * fe / lags
    ok = (bpm >= 70) & (bpm <= 180)
    wgt = np.exp(-0.5 * (np.log2(bpm / 120) / 0.9) ** 2)
    sc = np.where(ok, ac[1:] * wgt, 0)
    P = lags[int(np.argmax(sc))]
    best, bphi = -1, 0
    for phi in range(int(P)):
        s = env[phi::P].sum()
        if s > best:
            best, bphi = s, phi
    beats = []
    r = int(fe * 0.07)
    for b in np.arange(bphi, len(env), P):
        lo, hi = max(0, int(b) - r), min(len(env), int(b) + r + 1)
        beats.append(lo + int(np.argmax(env[lo:hi])))
    return np.array(beats) / fe + nf / 2 / SR, 60 * fe / P


def load_audio(path, start=0.0, dur=None, loop=True):
    cmd = [FFMPEG, "-v", "error"] + (["-stream_loop", "-1"] if loop else []) + ["-ss", str(start), "-i", path]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def make_plan(brief, ctx, workdir):
    scenes = expand(brief["scenes"])
    pool = list(brief.get("clips", []))
    if brief.get("clips_dir"):
        pool += sorted(f for f in glob.glob(os.path.join(brief["clips_dir"], "*"))
                       if f.lower().endswith(PHOTO_EXT + (".mp4", ".mov", ".m4v", ".webm", ".mkv")))
    assign_clips(scenes, pool)
    durs = [float(sc.get("dur", DEFAULT_DUR.get(sc["type"], 2.0))) for sc in scenes]
    for i, sc in enumerate(scenes):
        if sc["type"] == "checklist" and "dur" not in sc:
            durs[i] = 0.5 + 0.7 * len(sc.get("items", [])) + 1.3
        if sc["type"] == "features" and "dur" not in sc:
            durs[i] = 0.6 + 0.32 * len(sc.get("items", [])) + 1.5
        if sc["type"] == "cards" and "dur" not in sc:
            durs[i] = 0.8 + 0.12 * len(sc.get("items", [])) + 1.8
        if sc["type"] == "steps" and "dur" not in sc:
            durs[i] = 0.6 + float(sc.get("per", 0.55)) * len(sc.get("items", [])) + 1.4
        if sc["type"] == "gallery" and "dur" not in sc:
            durs[i] = 0.45 + float(sc.get("per", 0.7)) * len(sc.get("items", [])) + 0.6
        if sc["type"] == "contrast" and "dur" not in sc:
            d_ = float(sc.get("start", 0.15)) + float(sc.get("per", 0.55)) * len(sc.get("items", [])) + 1.4
            if sc.get("prompt"):
                d_ = max(d_, float(sc.get("prompt_at", 0.35)) + 0.3 + len(sc["prompt"]) / float(sc.get("cps", 14)) + 1.2)
            durs[i] = d_
        if sc["type"] == "wall" and "dur" not in sc:
            durs[i] = max(3.0, float(sc.get("quotes_at", 0.9)) + float(sc.get("per_quote", 1.9)) * len(sc.get("quotes", [])) + 0.6)
        if sc["type"] == "bundle" and "dur" not in sc:
            durs[i] = 0.2 + 0.55 * len(sc.get("items", [])) + 2.2
    segs = (brief.get("_narr") or {}).get("segs") or {}
    tail = float((brief.get("voiceover") or {}).get("tail", 0.35))
    mins = [0.0] * len(scenes)
    for i in range(len(scenes)):
        sg = segs.get(i)
        if sg:
            mins[i] = sg["lead"] + sg["len"] + tail
            durs[i] = max(durs[i], mins[i])
    mus = brief.get("music") or {}
    beats = np.array([])
    if mus.get("file") and mus.get("beat_sync", True) and os.path.exists(mus["file"]):
        y = load_audio(mus["file"], float(mus.get("start", 0)), sum(durs) * 1.5 + 5).mean(1)
        beats, bpm = detect_beats(y)
        log(f"[music] ~{bpm:.0f} BPM, {len(beats)} beats")
        if len(beats) and bpm:
            for i, sc in enumerate(scenes):
                if sc.get("beats"):
                    durs[i] = max(float(sc["beats"]) * 60.0 / bpm, mins[i])
    if len(beats):
        t, nd = 0.0, []
        for i, d in enumerate(durs):
            if i == len(durs) - 1:
                nd.append(d)
                break
            c = beats[(beats > t + max(0.6, 0.72 * d, mins[i])) & (beats < t + 1.45 * d + 0.25)]
            nt = float(c[np.argmin(np.abs(c - (t + d)))]) if len(c) else t + d
            nd.append(nt - t)
            t = nt
        durs = nd
    cache_p = os.path.join(workdir, "activity.json")
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    used = {}
    bounds = np.round(np.cumsum([0] + durs) * ctx.fps).astype(int)
    prev_key = prev_seed = ""
    for i, sc in enumerate(scenes):
        sc["_n"] = int(bounds[i + 1] - bounds[i])
        sc["_dur"] = sc["_n"] / ctx.fps
        sc["_t0"] = bounds[i] / ctx.fps
        if ctx.premium:
            sc["_premium"] = 1
            if i and "transition" not in sc:
                sc["transition"] = PREMIUM_TRANS.get(sc["type"], "push")
        if ctx.energy:
            sc["_energy"] = ctx.energy
            if len(beats):
                b = beats[(beats >= sc["_t0"] - 1e-3) & (beats < sc["_t0"] + sc["_dur"] - 0.05)] - sc["_t0"]
                sc["_beats"] = [round(float(x), 3) for x in b]
            if i and ctx.energy >= 2 and "transition" not in sc:
                sc["transition"] = CRAZY_TRANS[(i - 1) % len(CRAZY_TRANS)]
        sc.setdefault("transition", DEFAULT_TRANS.get(sc["type"], "cut") if i else "cut")
        if segs.get(i):
            sc["_say"] = {"file": segs[i]["file"], "lead": segs[i]["lead"], "text": segs[i]["text"]}
        for key in ("clip", "before", "after"):
            if sc.get(key):
                c = norm_clip(sc[key])
                if "start" not in c:
                    c["start"] = best_start(c["src"], sc["_dur"], cache, used)
                sc[key] = c
        if sc.get("clips"):
            sc["clips"] = [norm_clip(c) for c in sc["clips"]]
        srcs = [norm_clip(sc[k])["src"] for k in ("clip", "before", "after") if sc.get(k)] + \
               [c["src"] for c in sc.get("clips", [])] + [ctx.brand.get("logo") or ""]
        media = [sc.get("image")] + list(sc.get("images") or []) + \
                [(it.get("src") or it.get("image")) for it in (sc.get("items") or []) if isinstance(it, dict)]
        srcs += [norm_clip(x)["src"] if isinstance(x, dict) else x for x in media if isinstance(x, (str, dict)) and x]
        stamp = [(f, os.path.getmtime(f), os.path.getsize(f)) for f in srcs if f and os.path.exists(f)]
        caps = [c for c in ctx.captions if c["s"] < sc["_t0"] + sc["_dur"] and c["e"] > sc["_t0"]]
        def key_for(ver, prev):
            return hashlib.md5(json.dumps([ver, stamp, ctx.W, ctx.H, ctx.fps, ctx.c, ctx.ts, brief.get("brand", {}),
                                           {k: v for k, v in sc.items() if k not in ("_t0", "_seed")}, caps, ctx.bg_style,
                                           ctx.drift, ctx.top, ctx.bot,
                                           round(sc["_t0"], 3) if (ctx.bg_style != "grid" or caps) else 0,
                                           prev if sc["transition"] not in ("cut", "flash", "punch") else ""],
                                          sort_keys=True, default=str).encode()).hexdigest()[:12]
        h = key_for(VERSION, prev_key)
        # random choices (drift, sparkles) are seeded independently of the engine version, so the same brief
        # looks the same after an engine upgrade; only the cache key changes
        seed_h = key_for(SEED_SALT, prev_seed)
        sc["_seed"] = int(seed_h, 16)
        sc["_key"] = h
        prev_key, prev_seed = h, seed_h
    json.dump(cache, open(cache_p, "w"))
    return scenes


# ----------------------------------------------------------------- rendering
def build(sc, ctx):
    r = BUILDERS[sc["type"]](sc, ctx)
    bg, els, sfx = r[:3]
    extra = r[3] if len(r) > 3 else {}
    if ctx.brand.get("corner_logo") and sc["type"] not in ("hook", "logo", "cta", "collage") and \
            (bg.get("kind") == "clip" or ctx.bg_style != "grid") and sc.get("corner_logo", True):
        lg = ctx.logo()
        h = 80 * ctx.U
        lg = lg.resize((max(1, int(lg.width * h / lg.height)), int(h)), Image.LANCZOS)
        lg = finish(lg, lg.getchannel("A"), 0.5, U=ctx.U)
        els.append(Sprite(lg, 40 * ctx.U + lg.width / 2, ctx.top * 0.55 + lg.height / 2, 0.0, "none"))
    return bg, els, sfx, extra


def frames(sc, ctx, k0=0, count=None, prev=None):
    n = sc["_n"]
    count = n - k0 if count is None else count
    bg, els, sfx_ev, extra = build(sc, ctx)
    W, H = ctx.W, ctx.H
    reader = None
    hits = []
    if ctx.energy and sc.get("fx", True) is not False:
        raw = [(0.0, True)] if sc["_t0"] > 0 else []
        for (tt, name, g) in sfx_ev:
            if name in ("impact", "thump", "reveal"):
                raw.append((tt, True))
            elif name in ("pop", "click") and ctx.energy >= 2:
                raw.append((tt, False))
        if ctx.energy >= 2:
            raw += [(b, None if j % 2 == 0 else False) for j, b in enumerate(sc.get("_beats", []))]
        rng_h = np.random.default_rng(sc["_seed"] % 2 ** 32 + 77)
        for tt, st in sorted(raw):
            if hits and tt - hits[-1][0] < 0.06:
                prev_st = hits[-1][1]
                hits[-1] = (hits[-1][0], True if (prev_st or st) else (None if None in (prev_st, st) else False), hits[-1][2])
            else:
                hits.append((tt, st, float(rng_h.uniform(0, 2 * math.pi))))
    if bg["kind"] == "clip":
        lk = dict(ctx.grade)
        lk.update(bg.get("look") or {})
        reader = Reader(norm_clip(bg["clip"]), W, H, ctx.fps, n, t0=k0 / ctx.fps, look=lk,
                        zoom=bg.get("zoom", 0.05), seed=sc["_seed"] % 1000)
    animated = bg["kind"] == "panel" and ctx.bg_style != "grid"
    base = ctx.panel() if (bg["kind"] == "panel" and not animated) else np.zeros((H, W, 3), np.uint8)
    rng = np.random.default_rng(sc["_seed"] % 2 ** 32)
    shake = extra.get("shake")
    drift = float(sc.get("drift", ctx.drift if sc["type"] not in ("collage", "device") else 0))
    ctx._beats_now = sc.get("_beats", []) if ctx.energy >= 2 else []
    live_bg = ctx.energy >= 2 and bg["kind"] == "panel" and sc.get("fx", True) is not False
    try:
        for k in range(k0, k0 + count):
            t = k / ctx.fps
            pnow = ctx.panel_frame(sc["_t0"] + t) if animated else base
            bgf = reader.next() if reader else pnow
            out = pnow.copy() if (bg.get("hide") or reader is None) else bgf.copy()
            if live_bg:
                out = bg_energy(out, sc["_t0"] + t, t, ctx)
            for el in els:
                el.draw(out, t, ctx, bgf)
            if shake and shake[0] <= t < shake[0] + shake[1]:
                amp = 14 * ctx.U * (1 - (t - shake[0]) / shake[1])
                out = np.roll(out, (int(rng.uniform(-amp, amp)), int(rng.uniform(-amp, amp))), (0, 1))
            if drift > 0:
                z = 1 + drift * (0.5 - 0.5 * math.cos(math.pi * min(1.0, t / max(0.1, sc["_dur"]))))
                cw_, ch_ = W / z, H / z
                x0_, y0_ = (W - cw_) / 2, (H - ch_) / 2
                out = np.array(Image.fromarray(out).resize((W, H), Image.BILINEAR, box=(x0_, y0_, x0_ + cw_, y0_ + ch_)))
            if hits:
                out = camera_fx(out, t, hits, ctx)
            elif ctx.premium and sc["_t0"] > 0 and t < 0.9 and sc.get("fx", True) is not False:
                out = affine_frame(out, 1 + 0.03 * (1 - e_cubic(t / 0.9)))
            if ctx.captions:
                draw_captions(out, sc["_t0"] + t, ctx)
            out = transition(sc["transition"], out, prev, k, ctx.U, rng, ctx)
            yield out
    finally:
        if reader:
            reader.close()
        for el in els:
            if isinstance(el, CardClip) and el.reader:
                el.reader.close()


def render_scene(args):
    i, sc, ctx, workdir, prev_path = args
    path = os.path.join(workdir, f"s{i:02d}_{sc['_key']}.mp4")
    if os.path.exists(path):
        return path, False
    prev = np.array(Image.open(prev_path)) if prev_path and os.path.exists(prev_path) else None
    tmp = path[:-4] + ".tmp.mp4"
    crf, preset = ("26", "ultrafast") if ctx.draft else ("18", "veryfast")
    enc = subprocess.Popen([FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ctx.W}x{ctx.H}",
                            "-r", str(ctx.fps), "-i", "-", "-c:v", "libx264", "-preset", preset, "-crf", crf,
                            "-pix_fmt", "yuv420p", "-r", str(ctx.fps), tmp], stdin=subprocess.PIPE)
    for fr in frames(sc, ctx, prev=prev):
        enc.stdin.write(fr.tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError(f"encode failed for scene {i}")
    os.replace(tmp, path)
    return path, True


def last_frame_path(i, sc, ctx, workdir):
    p = os.path.join(workdir, f"s{i:02d}_{sc['_key']}_last.png")
    if not os.path.exists(p):
        fr = next(frames(sc, ctx, k0=sc["_n"] - 1, count=1))
        Image.fromarray(fr).save(p)
    return p


# ----------------------------------------------------------------- audio
def synth(name):
    import zlib
    rng = np.random.default_rng(zlib.crc32(name.encode()))
    t_ = lambda d: np.arange(int(d * SR)) / SR
    if name == "whoosh":
        d = 0.55
        t = t_(d)
        n = rng.standard_normal(len(t))
        p = t / d
        fc = 250 * (14 ** np.clip(p / 0.72, 0, 1)) * np.where(p > 0.72, 1 - (p - 0.72) * 2, 1)
        from scipy.signal import butter, sosfilt
        y = np.zeros_like(n)
        seg = 512
        for s in range(0, len(n), seg):
            f = float(np.clip(fc[s], 120, 9000))
            sos = butter(2, [f * 0.5, min(f * 1.8, SR / 2 - 100)], "bandpass", fs=SR, output="sos")
            y[s:s + seg] = sosfilt(sos, n[max(0, s - 2048):s + seg])[-len(n[s:s + seg]):]
        env = np.where(p < 0.72, (p / 0.72) ** 2.2, np.exp(-(p - 0.72) * 14))
        y = y * env
        pan = 0.2 + 0.6 * p
        st = np.stack([y * np.cos(pan * np.pi / 2), y * np.sin(pan * np.pi / 2)], 1)
        return st / (np.abs(st).max() + 1e-9) * 0.8, 0.4
    if name in ("impact", "thump"):
        d = 1.1 if name == "impact" else 0.35
        t = t_(d)
        f = 40 + 90 * np.exp(-t * 18)
        ph = 2 * np.pi * np.cumsum(f) / SR
        y = np.sin(ph) * np.exp(-t * (3.2 if name == "impact" else 11))
        if name == "impact":
            nz = rng.standard_normal(len(t)) * np.exp(-t * 40) * 0.5
            from scipy.signal import butter, sosfilt
            y += sosfilt(butter(2, 2500, "low", fs=SR, output="sos"), nz)
        y = np.tanh(y * 1.8)
        return np.stack([y, y], 1) * 0.9, 0.0
    if name == "pop":
        t = t_(0.12)
        f = 500 + 900 * (1 - np.exp(-t * 60))
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 45)
        return np.stack([y, y], 1) * 0.6, 0.0
    if name == "type":
        t = t_(0.05)
        y = rng.standard_normal(len(t)) * np.exp(-t * 260) * 0.5 + np.sin(2 * np.pi * 3800 * t) * np.exp(-t * 180) * 0.25
        return np.stack([y, y], 1) * 0.5, 0.0
    if name == "click":
        t = t_(0.08)
        y = rng.standard_normal(len(t)) * np.exp(-t * 400) * 0.6 + np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 90) * 0.5
        return np.stack([y, y], 1) * 0.8, 0.0
    if name == "ding":
        t = t_(1.2)
        y = (np.sin(2 * np.pi * 1318.5 * t) * np.exp(-t * 4) + 0.6 * np.sin(2 * np.pi * 1975.5 * t) * np.exp(-t * 6)
             + 0.3 * np.sin(2 * np.pi * 2637 * t) * np.exp(-t * 9)) * np.minimum(1, t * 300)
        return np.stack([y, y], 1) * 0.45, 0.0
    if name in ("shimmer", "reveal"):
        out = np.zeros((int(0.9 * SR), 2))
        for k in range(9):
            st = int(rng.uniform(0, 0.45) * SR)
            f = rng.uniform(2200, 5200)
            t = t_(0.4)
            y = np.sin(2 * np.pi * f * t) * np.exp(-t * 12) * 0.25
            pan = rng.uniform(0.1, 0.9)
            out[st:st + len(t), 0] += y * (1 - pan)
            out[st:st + len(t), 1] += y * pan
        return out, 0.0
    if name == "glitch":
        out = []
        for k in range(8):
            t = t_(0.03)
            f = rng.uniform(150, 2400)
            y = np.sign(np.sin(2 * np.pi * f * t)) * rng.uniform(0.2, 0.5)
            y = np.round(y * 6) / 6
            out.append(y)
        y = np.concatenate(out)
        return np.stack([y, np.roll(y, 40)], 1) * 0.5, 0.05
    return np.zeros((10, 2)), 0.0


def build_audio(brief, scenes, ctx, out_wav):
    total = sum(sc["_dur"] for sc in scenes)
    N = int(total * SR) + 1
    mix = np.zeros((N, 2), np.float32)
    mus = brief.get("music") or {}
    if mus.get("file") and os.path.exists(mus["file"]):
        m = load_audio(mus["file"], float(mus.get("start", 0)), total + 0.1)[:N] * float(mus.get("volume", 0.8))
        fo = int(min(1.4, total * 0.2) * SR)
        m[-fo:] *= np.linspace(1, 0, fo)[:, None] if len(m) >= fo else 1
        music = np.zeros((N, 2), np.float32)
        music[:len(m)] = m
    else:
        music = np.zeros((N, 2), np.float32)
    voice = np.zeros((N, 2), np.float32)
    vo = brief.get("voiceover") or {}
    if vo.get("file") and os.path.exists(vo["file"]):
        v = load_audio(vo["file"], 0, total, loop=False) * float(vo.get("volume", 1.0))
        s = int(float(vo.get("at", 0)) * SR)
        v = v[:max(0, N - s)]
        voice[s:s + len(v)] += v
    for sc in scenes:
        sy = sc.get("_say")
        if sy and os.path.exists(sy["file"]):
            v = load_audio(sy["file"], 0, None, loop=False) * float(vo.get("volume", 1.0))
            s = int((sc["_t0"] + sy["lead"]) * SR)
            v = v[:max(0, N - s)]
            voice[s:s + len(v)] += v
    for sc in scenes:
        if sc.get("audio") and sc.get("clip") and not is_photo(norm_clip(sc["clip"])["src"]):
            c = norm_clip(sc["clip"])
            a = load_audio(c["src"], c.get("start", 0), sc["_dur"], loop=False) * float(sc.get("audio_volume", 1.0))
            s = int(sc["_t0"] * SR)
            a = a[:max(0, N - s)]
            voice[s:s + len(a)] += a
    if np.abs(voice).max() > 0.01:
        env = np.abs(voice).mean(1)
        k = int(0.08 * SR)
        env = np.convolve(env, np.ones(k) / k, "same")
        duck = 1 - float(vo.get("duck", 0.7)) * np.clip(env / 0.03, 0, 1)
        k2 = int(0.25 * SR)
        duck = np.convolve(duck, np.ones(k2) / k2, "same")
        music *= duck[:, None]
    mix += music + voice
    sfx_cfg = brief.get("sfx", True)
    if sfx_cfg:
        custom = sfx_cfg if isinstance(sfx_cfg, dict) else {}
        bank = {}

        def get(name):
            if name not in bank:
                cfg = custom.get(name)
                cfg = {"file": cfg} if isinstance(cfg, str) else (cfg or {})
                if cfg.get("file") and os.path.exists(cfg["file"]):
                    y = load_audio(cfg["file"], 0, None, loop=False)
                    if cfg.get("max"):
                        y = y[:int(float(cfg["max"]) * SR)].copy()
                        f = min(len(y), int(0.05 * SR))
                        y[-f:] *= np.linspace(1, 0, f)[:, None]
                    bank[name] = (y * float(cfg.get("gain", 1.0)), float(cfg.get("sync", 0)))
                else:
                    if cfg:
                        log(f"[sfx] missing file for {name}; using built-in fallback")
                    bank[name] = synth(name)
            return bank[name]
        gain = float(brief.get("sfx_volume", 0.55))
        for i, sc in enumerate(scenes):
            if "_sfx" in sc:  # set by the web renderer
                ev = list(sc["_sfx"])
            else:
                ev = list(build(sc, ctx)[2]) if sc["type"] not in ("collage",) else [(0.4, "whoosh", 0.4)]
            tr = sc.get("transition")
            if i and tr in TRANS_SFX:
                ev.append((0.0, TRANS_SFX[tr], 0.6))
            if i and ctx.energy >= 2 and tr not in ("flash", "punch"):
                ev.append((0.0, "thump", 0.25 + 0.1 * ctx.energy))
            for (tt, name, g) in ev:
                y, lead = get(name)
                if tt > sc["_dur"]:
                    continue
                s = int((sc["_t0"] + tt - lead) * SR)
                if s < 0:
                    y = y[-s:]
                    s = 0
                if s >= N:
                    continue
                e = min(N, s + len(y))
                mix[s:e] += y[:e - s] * g * gain
    peak = np.abs(mix).max()
    if peak > 0.98:
        mix = np.tanh(mix / peak * 1.2) * 0.95
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ----------------------------------------------------------------- v3: voiceover captions
def _runs(v):
    out, st = [], None
    for i, x in enumerate(list(v) + [False]):
        if x and st is None:
            st = i
        elif not x and st is not None:
            out.append((st, i))
            st = None
    return out


def voiced(y, hop=0.01):
    m = y.mean(1) if y.ndim > 1 else y
    h = int(SR * hop)
    n = len(m) // h
    if n == 0:
        return np.zeros(0, bool)
    r = np.sqrt((m[:n * h].reshape(n, h) ** 2).mean(1) + 1e-12)
    v = r > max(np.percentile(r, 95) * 0.16, 0.003)
    for a, b in _runs(~v):
        if b - a < 15 and a > 0 and b < n:
            v[a:b] = True
    for a, b in _runs(v):
        if b - a < 6:
            v[a:b] = False
    return v


def _spread(ws, idx, hop):
    """Spread words over the voiced frame indices idx, weighted by word length."""
    tot = sum(len(w) + 1 for w in ws) or 1
    out, c = [], 0.0
    for w in ws:
        c1 = c + (len(w) + 1) / tot
        i0 = idx[min(len(idx) - 1, int(c * len(idx)))]
        i1 = idx[min(len(idx) - 1, max(int(c * len(idx)), int(math.ceil(c1 * len(idx))) - 1))]
        out.append((w, i0 * hop, (i1 + 1) * hop))
        c = c1
    return out


def align_text(text, y, hop=0.01):
    """Align the script's words to the recording without a speech model: phrases (split at punctuation) are matched
    to the voiced stretches between pauses, then words are spread inside each phrase by length. When the number of
    pauses does not match the phrases, phrase starts are snapped to the nearest voiced-run start (within 0.6 s)."""
    ws = text.split()
    v = voiced(y, hop)
    idx_all = np.nonzero(v)[0]
    if len(idx_all) < 5 or not ws:
        return _spread(ws, np.arange(max(1, len(v))), hop)
    runs = _runs(v)
    merged = [list(runs[0])]
    for a_, b_ in runs[1:]:
        if a_ - merged[-1][1] < int(0.25 / hop):
            merged[-1][1] = b_
        else:
            merged.append([a_, b_])
    phrases, cur = [], []
    for w in ws:
        cur.append(w)
        if w[-1:] in ".,!?;:…":
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    if len(phrases) == len(merged):
        out = []
        for ph, (a_, b_) in zip(phrases, merged):
            out += _spread(ph, np.arange(a_, b_), hop)
        return out
    out = _spread(ws, idx_all, hop)
    starts = [a_ * hop for a_, _ in merged]
    k = 0
    for ph in phrases:
        t0 = out[k][1]
        near = min(starts, key=lambda s_: abs(s_ - t0))
        if abs(near - t0) <= 0.6 and near > t0:
            shift = near - t0
            for j in range(k, k + len(ph)):
                w_, a_, b_ = out[j]
                out[j] = (w_, a_ + shift, b_ + shift)
        k += len(ph)
    return out

def build_captions(brief, with_words=False):
    """Captions for a recorded voiceover: voiceover {file, text, at, captions: true}. Returns [{text, s, e}] in video time
    (and, with_words, the word timings of each caption for the web renderer)."""
    vo = brief.get("voiceover") or {}
    if not (vo.get("text") and vo.get("file") and os.path.exists(vo["file"]) and vo.get("captions", True)):
        return ([], []) if with_words else []
    y = load_audio(vo["file"], 0, None, loop=False)
    at = float(vo.get("at", 0))
    words = [(w, a + at, b + at) for w, a, b in align_text(vo["text"], y)]
    return chunk_captions(words, vo, with_words)


def chunk_captions(words, vo, with_words=False):
    maxw, maxc = int(vo.get("words_per_caption", 3)), int(vo.get("caption_chars", 18))
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= maxw or sum(len(x[0]) + 1 for x in cur) + len(w[0]) > maxc or w[1] - cur[-1][2] > 0.45):
            chunks.append(cur)
            cur = []
        cur.append(w)
        if w[0][-1:] in ".,!?;:":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        nxt = chunks[i + 1][0][1] if i + 1 < len(chunks) else 1e9
        out.append({"text": " ".join(w for w, _, _ in c), "s": round(c[0][1] - 0.04, 3), "e": round(min(nxt - 0.04, c[-1][2] + 0.5), 3)})
    if with_words:
        return out, [[[w, round(a, 3), round(b, 3)] for w, a, b in c] for c in chunks]
    return out


# ----------------------------------------------------------------- v4.1: generated narration (text to speech)
TTS_AUTO = ["gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts"]  # free tier of the Gemini API
TTS_STYLE = ("a native Israeli Hebrew commercial voice-over artist: warm, confident and energetic, "
             "clear diction, natural modern Hebrew pronunciation, upbeat medium-fast pace")
TTS_HOST = "generativelanguage.googleapis.com"


class TTSError(Exception):
    pass


def tts_conf(brief):
    """Narration settings, or None when the brief asks for no generated narration."""
    vo = brief.get("voiceover") or {}
    lines = [sc.get("say") for sc in expand(brief.get("scenes", [])) if sc.get("say")]
    t = vo.get("tts")
    if not lines and not (t and vo.get("text") and not vo.get("file")):
        return None
    t = {"voice": t} if isinstance(t, str) else dict(t or {})
    eng = t.get("engine", "gemini")
    return {"engine": eng, "model": t.get("model", "auto"), "voice": t.get("voice", "" if eng == "elevenlabs" else "Puck"),
            "style": t.get("style", TTS_STYLE), "rate": float(t.get("rate", 1.0)), "key_file": t.get("key_file"),
            "per_line": bool(t.get("per_line", False)), "lines": lines}


def tts_key(conf, base_dir="."):
    """The engine's API key from the environment or a key file. Never printed or written anywhere."""
    el = conf.get("engine") == "elevenlabs"
    for k in (("ELEVENLABS_API_KEY", "XI_API_KEY") if el else ("GEMINI_API_KEY", "GOOGLE_API_KEY")):
        if os.environ.get(k, "").strip():
            return os.environ[k].strip()
    for p in (conf.get("key_file"), "~/.config/promo-reel/" + ("elevenlabs_key" if el else "gemini_key")):
        if p:
            p = os.path.expanduser(p)
            p = p if os.path.isabs(p) else os.path.join(base_dir, p)
            if os.path.exists(p):
                k = open(p, encoding="utf-8").read().strip()
                if k:
                    return k
    return None


def _http_post(url, body, key, timeout=240, key_header="x-goog-api-key", raw=False):
    import urllib.request
    import urllib.error
    host = url.split("/")[2]
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if body is not None else "GET",
                                 headers={"Content-Type": "application/json", key_header: key})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                b = r.read()
                return b if raw else json.loads(b.decode("utf-8"))
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")
            if e.headers.get("X-Proxy-Error") or "no rule allows host" in msg or "agent proxy" in msg:
                raise TTSError(f"the network blocks {host} - add it to the allowed domains "
                               "(claude.ai: Settings > Capabilities) and try again") from None
            if e.code == 429 and attempt < 2:
                m = re.search(r'"retryDelay":\s*"(\d+)', msg)
                wait = min(65, int(m.group(1)) + 2 if m else 20)
                log(f"[tts] rate limit - waiting {wait}s")
                time.sleep(wait)
                continue
            if "unusual" in msg.lower():
                raise TTSError(f"{host} turned off free-tier use from this network (it treats the workspace proxy "
                               "like a VPN) - use the other engine") from None
            try:
                j_ = json.loads(msg)
                er = j_.get("error") or j_.get("detail") or {}
                detail = (er.get("message", "") if isinstance(er, dict) else str(er))[:240]
            except Exception:
                detail = msg[:240]
            raise TTSError(f"HTTP {e.code}: {detail}") from None
        except urllib.error.URLError as e:
            r_ = str(e.reason)
            if "403" in r_ or "Tunnel" in r_:
                raise TTSError(f"the network blocks {host} - add it to the allowed domains "
                               "(claude.ai: Settings > Capabilities) and try again") from None
            raise TTSError(f"network error: {r_[:200]}") from None
    raise TTSError("rate limit - try again in a minute")


def _audio_from(data_b64, mime):
    import base64
    import io
    raw = base64.b64decode(data_b64)
    if raw[:4] == b"RIFF":
        with wave.open(io.BytesIO(raw)) as w:
            return np.frombuffer(w.readframes(w.getnframes()), np.int16).copy(), w.getframerate()
    m = re.search(r"rate=(\d+)", mime or "")
    return np.frombuffer(raw, np.int16).copy(), int(m.group(1)) if m else 24000


def tts_gemini(text, voice, style, model, key):
    """One Gemini TTS call. Returns (int16 mono samples, sample rate)."""
    if model.startswith("gemini-3.8"):
        body = {"model": model, "input": [{"type": "user_input", "content": [{"type": "text", "text": text,
                "annotations": [{"type": "speech_metadata", "style": style}]}]}],
                "response_format": {"type": "audio"}, "generation_config": {"speech_config": [{"voice": voice}]}}
        r = _http_post(f"https://{TTS_HOST}/v1beta/interactions", body, key)
        for st in reversed(r.get("steps", [])):
            for c in st.get("content", []):
                if c.get("type") == "audio" and c.get("data"):
                    return _audio_from(c["data"], c.get("mime_type"))
        raise TTSError("no audio in the response")
    prompt = (f"Read the following Hebrew advertisement script aloud, exactly as written and nothing else. "
              f"Delivery: {style}.\n\n{text}")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    r = _http_post(f"https://{TTS_HOST}/v1beta/models/{model}:generateContent", body, key)
    for c in r.get("candidates", []):
        for part in (c.get("content") or {}).get("parts", []):
            d = part.get("inlineData") or part.get("inline_data")
            if d and d.get("data"):
                return _audio_from(d["data"], d.get("mimeType") or d.get("mime_type"))
    fr = (r.get("candidates") or [{}])[0].get("finishReason")
    raise TTSError(f"no audio in the response{' (' + fr + ')' if fr else ''}")


EL_HOST = "api.elevenlabs.io"


def tts_elevenlabs(text, voice, model, key, lang="he"):
    """One ElevenLabs call (voice = voice id or name). Returns (int16 mono samples, sample rate)."""
    vid = voice
    if not re.fullmatch(r"[A-Za-z0-9]{20}", voice or ""):
        r = _http_post(f"https://{EL_HOST}/v1/voices", None, key, key_header="xi-api-key")
        vs = r.get("voices", [])
        hit = [v for v in vs if v.get("name", "").lower().startswith((voice or "").lower())] if voice else vs
        if not hit:
            raise TTSError(f"no ElevenLabs voice named '{voice}' (have: {', '.join(v.get('name', '') for v in vs[:12])})")
        vid = hit[0]["voice_id"]
    body = {"text": text, "model_id": model, "language_code": lang}
    mp3 = _http_post(f"https://{EL_HOST}/v1/text-to-speech/{vid}?output_format=mp3_44100_128", body, key,
                     key_header="xi-api-key", raw=True)
    dec = subprocess.run([FFMPEG, "-v", "error", "-i", "-", "-f", "s16le", "-ac", "1", "-ar", "44100", "-"],
                         input=mp3, capture_output=True).stdout
    if not dec:
        raise TTSError("ElevenLabs returned no audio")
    return np.frombuffer(dec, np.int16).copy(), 44100


def tts_synthetic(text):
    """Offline stand-in voice for tests: speech-like syllables, about 13 characters per second."""
    rate = 24000
    rng = np.random.default_rng(len(text))
    out = []
    for ph in re.split(r"(?<=[.,!?;:])\s+|\n+", text.strip()):
        n = max(1, len(ph.replace(" ", "")) // 2)
        for _ in range(n):
            d = 0.12 + 0.05 * rng.random()
            t = np.arange(int(rate * d)) / rate
            f0 = 140 + 40 * rng.random()
            out.append(0.35 * np.sin(2 * np.pi * f0 * t) * np.sin(np.pi * t / d) ** 2 * (1 + 0.3 * np.sin(2 * np.pi * 3 * f0 * t)))
            out.append(np.zeros(int(rate * 0.03)))
        out.append(np.zeros(int(rate * 0.45)))
    y = np.concatenate(out)
    return (y / max(1e-6, np.abs(y).max()) * 0.7 * 32767).astype(np.int16), rate


def tts_say(text, conf, key):
    """Synthesize text with the configured engine; returns (int16 samples, rate, model used)."""
    if conf["engine"] == "synthetic":
        return (*tts_synthetic(text), "synthetic")
    if conf["engine"] == "elevenlabs":
        models = ["eleven_v4", "eleven_v3"] if conf["model"] == "auto" else [conf["model"]]
        err = None
        for m in models:
            try:
                y, rate = tts_elevenlabs(text, conf["voice"], m, key)
                return y, rate, m
            except TTSError as e:
                err = e
                if "HTTP 400" in str(e) or "HTTP 404" in str(e) or "HTTP 422" in str(e):
                    continue
                raise
        raise err
    if conf["engine"] != "gemini":
        raise TTSError(f"unknown tts engine '{conf['engine']}' (use gemini or elevenlabs)")
    models = TTS_AUTO if conf["model"] == "auto" else [conf["model"]]
    err = None
    for m in models:
        try:
            y, rate = tts_gemini(text, conf["voice"], conf["style"], m, key)
            return y, rate, m
        except TTSError as e:
            err = e
            if "HTTP 404" in str(e) or "HTTP 400" in str(e) and "model" in str(e).lower():
                continue
            raise
    raise err


def _save_wav(path, y, rate):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(np.asarray(y, np.int16).tobytes())


def _trim(y, rate, pad=0.05):
    """Cut leading/trailing silence and level the voice (peak about -3 dBFS)."""
    f = y.astype(np.float32) / 32768.0
    h = max(1, int(rate * 0.01))
    n = len(f) // h
    if n == 0:
        return y
    rms = np.sqrt((f[:n * h].reshape(n, h) ** 2).mean(1) + 1e-12)
    on = np.nonzero(rms > max(rms.max() * 0.05, 0.004))[0]
    if len(on):
        a, b = max(0, on[0] * h - int(pad * rate)), min(len(f), (on[-1] + 1) * h + int(pad * rate))
        f = f[a:b]
    f = f / max(1e-6, np.abs(f).max()) * 0.7
    return (f * 32767).astype(np.int16)


def _split_lines(y, rate, lines):
    """Cut one narration take into len(lines) pieces at its longest pauses. None when the pauses do not fit."""
    n = len(lines)
    if n == 1:
        return [(0, len(y))]
    f = y.astype(np.float32) / 32768.0
    hop = 0.01
    h = int(rate * hop)
    m = len(f) // h
    rms = np.sqrt((f[:m * h].reshape(m, h) ** 2).mean(1) + 1e-12)
    v = rms > max(np.percentile(rms, 95) * 0.08, 0.003)
    gaps = [(a, b) for a, b in _runs(~v) if a > 0 and b < m and b - a >= 15]
    if len(gaps) < n - 1:
        return None
    # expected cut points from the text lengths: pick, in order, the longest pause near each one
    tot = sum(len(x) for x in lines)
    voiced_total = int(v.sum()) or 1
    cum = np.cumsum(v)
    cuts, used = [], set()
    acc = 0
    for k in range(n - 1):
        acc += len(lines[k])
        target = acc / tot * voiced_total
        best, score = None, -1e9
        for j, (a, b) in enumerate(gaps):
            if j in used or (cuts and a <= cuts[-1][1]):
                continue
            dist = abs(cum[a] - target) / voiced_total
            sc_ = (b - a) / 100.0 - 4.0 * dist
            if sc_ > score:
                best, score = j, sc_
        if best is None:
            return None
        used.add(best)
        cuts.append(gaps[best])
    bounds = [0] + [int((a + b) / 2 * h) for a, b in cuts] + [len(y)]
    pieces = [(bounds[i], bounds[i + 1]) for i in range(n)]
    # sanity: each piece within 0.4x-2.5x of its share of the text
    total = len(y)
    for (a, b), ln in zip(pieces, lines):
        share = len(ln) / tot
        if not 0.4 * share <= (b - a) / total <= 2.5 * share:
            return None
    return pieces


def _atempo(path, rate_mul):
    if abs(rate_mul - 1) < 0.01:
        return
    tmp = path + ".tmp.wav"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", path, "-filter:a", f"atempo={rate_mul:.3f}", tmp], check=True)
    os.replace(tmp, path)


def prepare_narration(brief, base_dir="."):
    """Generate the narration (cached by script, voice and style) and record it in the brief:
    scene lines -> brief['_narr']['segs'] {expanded scene index: {file, len, lead, text}};
    one continuous script (voiceover.text + voiceover.tts) -> voiceover.file."""
    conf = tts_conf(brief)
    if not conf:
        return None
    vo = brief.setdefault("voiceover", {})
    scenes = expand(brief.get("scenes", []))
    per_scene = bool(conf["lines"])
    lines = conf["lines"] if per_scene else [vo["text"]]
    h = hashlib.md5(json.dumps([conf["engine"], conf["model"], conf["voice"], conf["style"], conf["rate"], lines,
                                conf["per_line"]], ensure_ascii=False).encode()).hexdigest()[:14]
    cdir = os.path.join(os.path.expanduser("~/.cache/promo-reel/tts"), h)
    meta_p = os.path.join(cdir, "meta.json")
    if os.path.exists(meta_p):
        meta = json.load(open(meta_p, encoding="utf-8"))
        log(f"[tts] cached narration ({meta['model']}, voice {conf['voice']})")
    else:
        key = tts_key(conf, base_dir) if conf["engine"] in ("gemini", "elevenlabs") else None
        if conf["engine"] == "gemini" and not key:
            raise TTSError("no Gemini API key: set GEMINI_API_KEY or save the key in ~/.config/promo-reel/gemini_key "
                           "(free at aistudio.google.com, no credit card)")
        if conf["engine"] == "elevenlabs" and not key:
            raise TTSError("no ElevenLabs API key: set ELEVENLABS_API_KEY or save the key in "
                           "~/.config/promo-reel/elevenlabs_key (elevenlabs.io > Developers > API keys)")
        files, model = [], None
        pieces = None
        if len(lines) > 1 and not conf["per_line"]:
            log(f"[tts] generating {len(lines)} lines in one take (voice {conf['voice']})")
            y, rate, model = tts_say("\n\n".join(lines), conf, key)
            pieces = _split_lines(y, rate, lines)
            if pieces is None:
                log("[tts] the pauses in the take did not match the lines - generating each line separately")
        if pieces is not None:
            for k, (a, b) in enumerate(pieces):
                p = os.path.join(cdir, f"line{k:02d}.wav")
                _save_wav(p, _trim(y[a:b], rate), rate)
                files.append(p)
        else:
            for k, ln in enumerate(lines):
                if len(lines) > 1:
                    log(f"[tts] line {k + 1}/{len(lines)}")
                y, rate, model = tts_say(ln, conf, key)
                p = os.path.join(cdir, f"line{k:02d}.wav")
                _save_wav(p, _trim(y, rate), rate)
                files.append(p)
        for p in files:
            _atempo(p, conf["rate"])
        meta = {"model": model, "files": files, "lens": [], "lines": lines}
        for p in files:
            with wave.open(p) as w:
                meta["lens"].append(round(w.getnframes() / w.getframerate(), 3))
        json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False)
        log(f"[tts] narration ready: {sum(meta['lens']):.1f}s ({model}) - AI-generated voice")
    if not per_scene:
        vo["file"] = meta["files"][0]
        vo.setdefault("at", 0.3)
        return meta
    segs, k = {}, 0
    lead0 = float(vo.get("lead", 0.15))
    for i, sc in enumerate(scenes):
        if sc.get("say"):
            segs[i] = {"file": meta["files"][k], "len": meta["lens"][k], "text": sc["say"],
                       "lead": float(sc.get("say_at", max(lead0, 0.3) if i == 0 else lead0))}
            k += 1
    brief["_narr"] = {"segs": segs}
    return meta


def scene_captions(scenes, vo):
    """Captions for scene lines, placed at each scene's line."""
    words = []
    for sc in scenes:
        sy = sc.get("_say")
        if sy and os.path.exists(sy["file"]):
            y = load_audio(sy["file"], 0, None, loop=False)
            off = sc["_t0"] + sy["lead"]
            words += [(w, a + off, b + off) for w, a, b in align_text(sy["text"], y)]
    return chunk_captions(words, vo, True) if words else ([], [])


def plan_with_narration(brief, ctx, workdir, base_dir="."):
    """make_plan plus narration: generated lines lengthen their scenes, and captions follow the plan."""
    prepare_narration(brief, base_dir)
    vo = brief.get("voiceover") or {}
    ctx.captions, ctx.caption_words = build_captions(brief, True)
    scenes = make_plan(brief, ctx, workdir)
    if (brief.get("_narr") or {}).get("segs") and vo.get("captions", True):
        ctx.captions, ctx.caption_words = scene_captions(scenes, vo)
        scenes = make_plan(brief, ctx, workdir)  # scene keys include the captions they show
    return scenes


def caption_cy(ctx, h):
    """Vertical centre of the caption box: voiceover.caption_y (fraction of the height) or just inside the bottom of the safe band."""
    y = (ctx.brief.get("voiceover") or {}).get("caption_y")
    return float(y) * ctx.H if y else ctx.bot - h * 0.6


def draw_captions(out, T, ctx):
    for c in ctx.captions:
        if c["s"] <= T < c["e"]:
            cache = ctx.__dict__.setdefault("_capcache", {})
            if c["text"] not in cache:
                cache[c["text"]] = boxed(ctx, c["text"], ctx.brief.get("voiceover", {}).get("caption_size", 64), role="heavy",
                                         bg=(10, 10, 12), fg=(255, 255, 255))
            im = cache[c["text"]]
            p = clamp((T - c["s"]) / 0.12)
            s_ = 0.86 + 0.14 * e_back(p)
            im2 = im.resize((max(1, int(im.width * s_)), max(1, int(im.height * s_))), Image.BILINEAR) if s_ < 0.995 else im
            cy = caption_cy(ctx, im.height)
            over(out, np.asarray(im2), ctx.W / 2 - im2.width / 2, cy - im2.height / 2, clamp(p * 3))
            return


# ----------------------------------------------------------------- v3: brief loading, validation, recovery
KNOWN_TYPES = set(BUILDERS) | {"services", "stats"}
REQUIRED = {"hook": ["big"], "stamp": ["stamp"], "kinetic": ["lines"], "cards": ["items"], "steps": ["items"],
            "features": ["items"], "checklist": ["items"], "services": ["items"], "stats": ["items"],
            "before_after": ["before", "after"], "collage": [], "counter": ["value"],
            "contrast": ["items"], "gallery": ["items"], "wall": ["images"], "bundle": ["items"]}


def load_brief(path):
    """Read a brief and apply its brand kit (brand_kit: kit.json from --brand-from) and platform defaults."""
    brief = json.load(open(path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(path))
    kit_p = brief.get("brand_kit")
    if kit_p:
        kp = kit_p if os.path.isabs(kit_p) else os.path.join(base, kit_p)
        if os.path.exists(kp):
            kit = json.load(open(kp, encoding="utf-8"))
            kdir = os.path.dirname(os.path.abspath(kp))
            kb = dict(kit.get("brand", {}))
            if kb.get("logo") and not os.path.isabs(kb["logo"]):
                kb["logo"] = os.path.relpath(os.path.join(kdir, kb["logo"]), base)
            brief["theme"] = {**kit.get("theme", {}), **brief.get("theme", {})}
            brief["brand"] = {**kb, **brief.get("brand", {})}
        else:
            log(f"[brand] brand_kit {kit_p} not found - using the brief's own theme")
    plat = PLATFORMS.get(brief.get("platform", ""))
    if plat and "format" not in brief:
        brief["format"] = plat[0]
    return brief


def validate(brief):
    """Catch broken briefs before rendering. Missing footage falls back to the branded panel (warning), unknown
    scene types and missing required fields are errors."""
    errs, warns = [], []
    scenes = brief.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return ["brief has no scenes"], warns
    for i, sc in enumerate(scenes):
        t = sc.get("type")
        if t not in KNOWN_TYPES:
            errs.append(f"scene {i}: unknown type '{t}' (known: {', '.join(sorted(KNOWN_TYPES))})")
            continue
        for f in REQUIRED.get(t, []):
            if not sc.get(f):
                errs.append(f"scene {i} ({t}): missing '{f}'")
        c = sc.get("clip")
        if c:
            src = norm_clip(c)["src"]
            if not os.path.exists(src):
                warns.append(f"scene {i} ({t}): clip '{src}' not found - using the branded background")
                sc["clip"] = None
        for key in ("before", "after"):
            if sc.get(key) and not os.path.exists(norm_clip(sc[key])["src"]):
                errs.append(f"scene {i} ({t}): {key} '{norm_clip(sc[key])['src']}' not found")
        if sc.get("clips"):
            ok = [c for c in sc["clips"] if os.path.exists(norm_clip(c)["src"])]
            if len(ok) < len(sc["clips"]):
                warns.append(f"scene {i} ({t}): {len(sc['clips']) - len(ok)} collage clip(s) missing - skipped")
            sc["clips"] = ok
        if t == "gallery" and isinstance(sc.get("items"), list):
            keep = [it for it in sc["items"] if os.path.exists(norm_clip(it if isinstance(it, str) else it.get("src", ""))["src"])]
            if len(keep) < len(sc["items"]):
                warns.append(f"scene {i} (gallery): {len(sc['items']) - len(keep)} item(s) missing - skipped")
            sc["items"] = keep
            if not keep:
                errs.append(f"scene {i} (gallery): no item files found")
        if t == "wall" and isinstance(sc.get("images"), list):
            keep = [x for x in sc["images"] if os.path.exists(norm_clip(x)["src"])]
            if len(keep) < len(sc["images"]):
                warns.append(f"scene {i} (wall): {len(sc['images']) - len(keep)} image(s) missing - skipped")
            sc["images"] = keep
            if not keep:
                errs.append(f"scene {i} (wall): no image files found")
        if t == "bundle":
            for it in sc.get("items", []) if isinstance(sc.get("items"), list) else []:
                if isinstance(it, dict) and it.get("image") and not os.path.exists(it["image"]):
                    warns.append(f"scene {i} (bundle): image '{it['image']}' not found - card without picture")
                    it.pop("image")
        if sc.get("image") and not os.path.exists(sc["image"]):
            warns.append(f"scene {i} ({t}): image '{sc['image']}' not found - showing the animated UI instead")
            sc.pop("image")
        for it in sc.get("items", []) if isinstance(sc.get("items"), list) else []:
            if isinstance(it, dict) and it.get("icon") and it["icon"] not in ICONS:
                warns.append(f"scene {i} ({t}): unknown icon '{it['icon']}' - using check")
                it["icon"] = "check"
        if sc.get("icon") and sc["icon"] not in ICONS:
            warns.append(f"scene {i} ({t}): unknown icon '{sc['icon']}' - removed")
            sc.pop("icon")
    mus = brief.get("music") or {}
    if mus.get("file") and not os.path.exists(mus["file"]):
        warns.append(f"music '{mus['file']}' not found - rendering without music")
        brief.pop("music")
    lg = (brief.get("brand") or {}).get("logo")
    if lg and not os.path.exists(lg):
        warns.append(f"logo '{lg}' not found - using an initials emblem")
        brief["brand"].pop("logo")
    vo = brief.get("voiceover") or {}
    if vo.get("file") and not os.path.exists(vo["file"]):
        warns.append(f"voiceover '{vo['file']}' not found - skipped")
        brief.pop("voiceover")
    return errs, warns


# ----------------------------------------------------------------- v3: brand kit extraction
def _hsv(rgb):
    import colorsys
    return colorsys.rgb_to_hsv(*[v / 255 for v in rgb])


def brand_from(src, out_json):
    """Build a brand kit (colours, fonts, logo, name, tagline, contact) from a website folder or repo."""
    import shutil as _sh
    skip = ("node_modules", ".git", ".next", "dist", "build", ".vercel")
    files = []
    for root, dirs, fs in os.walk(src):
        dirs[:] = [d for d in dirs if d not in skip]
        files += [os.path.join(root, f) for f in fs]
    vars_, fonts = {}, []
    for f in files:
        if f.endswith((".css", ".scss")):
            txt = open(f, encoding="utf-8", errors="ignore").read()
            for k, v in re.findall(r"--([\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8})\b", txt):
                vars_.setdefault(k, v)
            fonts += re.findall(r"font-family\s*:\s*([^;]+);", txt) + re.findall(r"--font[\w-]*\s*:\s*([^;]+);", txt)
    man = {}
    for f in files:
        if os.path.basename(f) in ("site.webmanifest", "manifest.json", "manifest.webmanifest"):
            try:
                man = json.load(open(f, encoding="utf-8"))
                break
            except Exception:
                pass
    norm = lambda h: "#" + "".join(ch * 2 for ch in h[1:4]) if len(h) == 4 else h[:7]
    cols = {k: norm(v) for k, v in vars_.items()}
    pick = lambda *names: next((cols[n] for n in names if n in cols), None)
    th = {}
    th["bg"] = pick("background", "bg", "base", "color-bg") or man.get("background_color") or man.get("theme_color")
    th["text"] = pick("foreground", "text", "fg", "color-text")
    th["muted"] = pick("muted", "muted-foreground", "gray", "secondary-text")
    sat = [(k, v) for k, v in cols.items() if _hsv(hexrgb(v))[1] > 0.35 and _hsv(hexrgb(v))[2] > 0.5 and v not in (th["bg"], th["text"])]
    if sat:
        th["primary"] = sat[0][1]
        h0 = _hsv(hexrgb(sat[0][1]))[0]
        other = [v for k, v in sat[1:] if min(abs(_hsv(hexrgb(v))[0] - h0), 1 - abs(_hsv(hexrgb(v))[0] - h0)) > 0.08]
        if other:
            th["primary2"] = other[0]
        soft = [v for k, v in cols.items() if ("soft" in k or "light" in k) and min(abs(_hsv(hexrgb(v))[0] - h0), 1 - abs(_hsv(hexrgb(v))[0] - h0)) < 0.06]
        if soft:
            th["hi"] = soft[0]
    if "accent" in cols and cols["accent"] not in th.values():
        th["accent"] = cols["accent"]
    th = {k: v for k, v in th.items() if v}
    ftxt = " ".join(fonts).lower()
    typeset = "tech" if "noto sans hebrew" in ftxt else "bold" if "rubik" in ftxt else "classic" if "secular" in ftxt else \
        "elegant" if ("frank" in ftxt or "assistant" in ftxt) else "tech" if "heebo" not in ftxt else "bold"
    dark = th.get("bg") and sum(hexrgb(th["bg"])) < 200
    th.update({"type": typeset, "grade": "bright", "bg_style": "tech" if dark else "grid"})
    icons = [f for f in files if f.lower().endswith(".png") and re.search(r"(logo|icon|brand|apple-touch)", os.path.basename(f), re.I)
             and "maskable" not in f]
    logo = None
    if icons:
        best = max(icons, key=lambda f: Image.open(f).size[0] * Image.open(f).size[1])
        os.makedirs(os.path.dirname(os.path.abspath(out_json)) or ".", exist_ok=True)
        logo = os.path.join(os.path.dirname(os.path.abspath(out_json)), "brand_logo.png")
        Image.open(best).convert("RGBA").save(logo)
    text = ""
    for f in files:
        if re.search(r"(^|/)(tests?|__tests__|e2e|fixtures|mocks?)/|\.(test|spec)\.", f):
            continue
        if f.endswith((".ts", ".tsx", ".js", ".json", ".html", ".md")) and os.path.getsize(f) < 2_000_000:
            text += open(f, encoding="utf-8", errors="ignore").read()
    phones = re.findall(r"\b0(?:5\d|[2-4]|[89]|7\d)-?\d{7}\b", text)
    phone = max(set(phones), key=phones.count) if phones else None
    third = ("github.com", "google", "facebook.com", "instagram.com", "linkedin.com", "wa.me", "whatsapp.com", "schema.org",
             "w3.org", "vercel.com", "npmjs", "youtube.com", "twitter.com", "x.com", "tiktok.com", "gstatic", "cloudflare",
             "jsdelivr", "unpkg", "nextjs.org", "react.dev", "supabase.co", "example", "localhost")
    urls = [u for u in re.findall(r"https://[a-z0-9.-]+\.(?:vercel\.app|netlify\.app|co\.il|org\.il|com|net|io|app|dev)\b", text)
            if not any(t in u for t in third)]
    site_hint = [u for u in re.findall(r"(?:SITE_URL|siteUrl|metadataBase)[\s\S]{0,120}?(https://[a-z0-9.-]+\.[a-z.]+)", text)
                 if not any(t in u for t in third)]
    site = site_hint[0] if site_hint else (max(set(urls), key=urls.count) if urls else None)
    kit = {"name": man.get("name") or man.get("short_name"), "description": man.get("description"),
           "theme": th, "brand": {"name": man.get("name"), "tagline": man.get("description"),
                                   "logo": os.path.basename(logo) if logo else None, "phone": phone,
                                   "website": site.replace("https://", "") if site else None},
           "source": os.path.abspath(src), "css_vars": cols, "fonts_found": sorted(set(x.strip() for x in fonts))[:12]}
    kit["brand"] = {k: v for k, v in kit["brand"].items() if v}
    json.dump(kit, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(out_json)
    print(json.dumps({"theme": th, "brand": kit["brand"]}, ensure_ascii=False, indent=1))
    return kit


# ----------------------------------------------------------------- v3: templates and storyboard
TEMPLATES = {
    "property": {"platform": "reels", "theme": {"preset": "gold", "type": "bold", "grade": "bright"},
                 "brand": {"name": "<<business name>>", "phone": "<<phone>>"},
                 "music": {"file": "assets/sfx/music.wav", "volume": 0.85},
                 "scenes": [
                     {"type": "hook", "style": "box", "small": "<<what · where>>", "icon": "pin", "big": "<<promise, 2-4 words>>", "clip": "<<best photo>>", "beats": 4, "impact": 0},
                     {"type": "location", "place": "<<place>>", "title": "<<view / location line>>", "clip": "<<view photo>>", "beats": 5},
                     {"type": "showcase", "label": "<<room>>", "icon": "home", "title": "<<2-3 words>>", "clip": "<<photo>>", "beats": 4},
                     {"type": "showcase", "label": "<<room>>", "icon": "bed", "title": "<<2-3 words>>", "clip": "<<photo>>", "beats": 4},
                     {"type": "features", "title": "<<what you get>>", "clip": "<<calm photo>>", "beats": 8,
                      "items": [{"icon": "people", "text": "<<capacity>>"}, {"icon": "snow", "text": "<<amenity>>"}, {"icon": "pin", "text": "<<location fact>>"}]},
                     {"type": "showcase", "style": "words", "title": "<<emotional line>>", "pos": "center", "clip": "<<photo>>", "beats": 4},
                     {"type": "cta", "clip": "<<photo>>", "logo": False, "headline": "<<action>>", "button": "שלחו הודעה בוואטסאפ", "transition": "leak", "beats": 10}]},
    "service": {"platform": "reels", "theme": {"preset": "fire", "type": "bold", "grade": "punchy"},
                "brand": {"name": "<<business name>>", "tagline": "<<tagline>>", "logo": "<<logo.png>>", "phone": "<<phone>>"},
                "music": {"file": "assets/sfx/music.wav", "volume": 0.8},
                "scenes": [
                    {"type": "hook", "small": "<<pain, part 1>>", "big": "<<pain, 1 word>>?", "clip": "<<colorful clip>>"},
                    {"type": "stamp", "line": "<<consequence>>", "stamp": "<<1-2 words>>", "clip": "<<problem clip>>"},
                    {"type": "logo", "clip": "<<clip>>"},
                    {"type": "services", "small": "<<we offer>>", "items": [{"text": "<<service 1>>", "clip": "<<clip>>"}, {"text": "<<service 2>>", "clip": "<<clip>>"}]},
                    {"type": "checklist", "clip": "<<clip>>", "items": ["<<benefit 1>>", "<<benefit 2>>", "<<benefit 3>>"]},
                    {"type": "cta", "clip": "<<clip>>", "headline": "<<action>>", "button": "שלחו הודעה בוואטסאפ"}]},
    "tech": {"platform": "reels", "brand_kit": "<<brand_kit.json from --brand-from>>",
             "theme": {"preset": "tech", "type": "tech", "bg_style": "tech", "grade": "bright"},
             "music": {"file": "assets/sfx/music.wav", "volume": 0.85},
             "scenes": [
                 {"type": "kinetic", "kicker": "<<SHORT MONO LABEL>>", "lines": ["<<question line 1>>", {"text": "<<accent words>>", "style": "accent"}], "beats": 4, "transition": "cut"},
                 {"type": "kinetic", "lines": [{"text": "<<the turn>>", "style": "small"}, "<<promise line>>"], "beats": 4},
                 {"type": "logo", "burst": True, "beats": 4},
                 {"type": "cards", "kicker": "<<SERVICES>>", "title": "<<what I build>>", "items": [{"icon": "home", "title": "<<service>>"}, {"icon": "people", "title": "<<service>>"}, {"icon": "calendar", "title": "<<service>>"}, {"icon": "sparkle", "title": "<<service>>"}], "beats": 8},
                 {"type": "device", "device": "phone", "ui": "dashboard", "ui_title": "<<app name>>", "label": "<<label>>", "title": "<<result line>>", "beats": 6},
                 {"type": "steps", "title": "<<how it works>>", "items": [{"title": "<<step 1>>"}, {"title": "<<step 2>>"}, {"title": "<<step 3>>"}], "beats": 8},
                 {"type": "cta", "logo": True, "eyebrow": "<<eyebrow>>", "headline": "<<action>>", "button": "שלחו הודעה בוואטסאפ", "beats": 10}]},
}


def storyboard(scenes, brief, ctx, path):
    """Markdown storyboard + timeline of the planned edit (times after beat snapping)."""
    bpm = None
    mus = brief.get("music") or {}
    rows = ["| # | time | len | beats | scene | on-screen copy | visual | transition |", "|---|---|---|---|---|---|---|---|"]
    if mus.get("file") and os.path.exists(mus["file"]):
        y = load_audio(mus["file"], float(mus.get("start", 0)), 30).mean(1)
        _, bpm = detect_beats(y)
    for i, sc in enumerate(scenes):
        copy = " / ".join(str(sc[k]) for k in ("small", "big", "big2", "label", "title", "sub", "place", "kicker", "line", "stamp",
                                                "tagline", "headline", "button", "eyebrow", "note") if sc.get(k))
        if sc.get("lines"):
            copy += " / ".join((l if isinstance(l, str) else l.get("text", "")) for l in sc["lines"])
        if sc.get("items"):
            copy += " [" + "; ".join((it if isinstance(it, str) else it.get("title") or it.get("text") or "") for it in sc["items"]) + "]"
        c = sc.get("clip")
        vis = (norm_clip(c)["src"] + (" · " + norm_clip(c).get("move", "") if norm_clip(c).get("move") else "")) if c else \
            (f"{sc.get('device', 'phone')} · ui {sc.get('ui', 'dashboard')}" if sc["type"] == "device" else f"panel ({ctx.bg_style})")
        bt = f"{sc['_dur'] * bpm / 60:.1f}" if bpm else "-"
        rows.append(f"| {i} | {sc['_t0']:.2f}s | {sc['_dur']:.2f}s | {bt} | {sc['type']} | {copy.replace('|', '/')} | {vis} | {sc.get('transition')} |")
    total = sum(sc["_dur"] for sc in scenes)
    head = f"# Storyboard - {brief.get('out', 'promo.mp4')}\n\n{len(scenes)} scenes, {total:.1f} s, {ctx.W}x{ctx.H}@{ctx.fps}" + \
           (f", music ~{bpm:.0f} BPM" if bpm else "") + "\n\n"
    open(path, "w", encoding="utf-8").write(head + "\n".join(rows) + "\n")
    return path


# ----------------------------------------------------------------- v3: quality assurance
def _ff(args):
    return subprocess.run([FFMPEG, "-hide_banner", "-nostats"] + args, capture_output=True, text=True).stderr


def layout_issues(scenes, ctx):
    """Final-position bounds of every text/graphic sprite: outside the frame = cut off (error), outside the safe band = warning."""
    errs, warns = [], []
    W, H = ctx.W, ctx.H
    side = W * 0.04
    for i, sc in enumerate(scenes):
        try:
            els = build(sc, ctx)[1]
        except Exception as ex:
            errs.append(f"scene {i} ({sc['type']}): build failed: {ex}")
            continue
        caps_band = None
        if any(c["s"] < sc["_t0"] + sc["_dur"] and c["e"] > sc["_t0"] for c in ctx.captions):
            ch = 64 * ctx.U * 1.45 * (ctx.brief.get("voiceover", {}).get("caption_size", 64) / 64)
            cyc = caption_cy(ctx, ch)
            caps_band = (cyc - ch / 2, cyc + ch / 2)
        for el in els:
            if not isinstance(el, Sprite) or el.anim == "none":
                continue
            a = np.asarray(el.img)[..., 3]
            ys, xs = np.nonzero(a > 60)
            if not len(xs):
                continue
            h, w = a.shape
            x0, x1 = el.cx - w / 2 + xs.min(), el.cx - w / 2 + xs.max()
            y0, y1 = el.cy - h / 2 + ys.min(), el.cy - h / 2 + ys.max()
            if sc["type"] == "collage":
                continue
            if caps_band and caps_band[0] < y1 and y0 < caps_band[1] and x0 < W * 0.8 and x1 > W * 0.2:
                warns.append(f"scene {i} ({sc['type']}): scene text under the voiceover captions "
                             f"({y0:.0f}-{y1:.0f}) - set the scene's pos to top/center or voiceover.caption_y")
            if x0 < -1 or y0 < -1 or x1 > W + 1 or y1 > H + 1:
                errs.append(f"scene {i} ({sc['type']}): element cut off at the frame edge ({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f})")
            elif x0 < side or x1 > W - side or y0 < ctx.top - 4 or y1 > ctx.bot + 4:
                warns.append(f"scene {i} ({sc['type']}): element outside the safe band ({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f})")
    return errs, warns


def qa(video, brief, scenes, ctx, creative=None, out_prefix=None):
    """Automatic technical + structural checks with a 0-100 score. The creative part (25 pts) is a reviewer's judgement
    passed in as 5 numbers (hook, clarity, pacing, aesthetics/brand, message/CTA, 0-5 each); it is never auto-filled."""
    rep = {"file": video, "checks": [], "warnings": [], "errors": []}
    pts = 0

    def chk(name, ok, got, max_pts, note=""):
        nonlocal pts
        rep["checks"].append({"check": name, "ok": bool(ok), "value": got, "points": max_pts if ok else 0, "max": max_pts, "note": note})
        pts += max_pts if ok else 0
    if not os.path.exists(video):
        rep["errors"].append("video file missing")
        rep["score"] = 0
        return rep
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", video],
                                   capture_output=True, text=True).stdout or "{}")
    vs = [s for s in pr.get("streams", []) if s.get("codec_type") == "video"]
    au = [s for s in pr.get("streams", []) if s.get("codec_type") == "audio"]
    v = vs[0] if vs else {}
    dur = float(pr.get("format", {}).get("duration", 0) or 0)
    chk("opens; h264 + aac; yuv420p", vs and au and v.get("codec_name") == "h264" and au[0].get("codec_name") == "aac"
        and v.get("pix_fmt") == "yuv420p", f"{v.get('codec_name')}/{au[0].get('codec_name') if au else None}/{v.get('pix_fmt')}", 10)
    fr = v.get("r_frame_rate", "0/1").split("/")
    fps = float(fr[0]) / max(1.0, float(fr[1]))
    chk("resolution, aspect and fps match the plan", (v.get("width"), v.get("height")) == (ctx.W, ctx.H) and abs(fps - ctx.fps) < 0.01,
        f"{v.get('width')}x{v.get('height')}@{fps:g}", 10)
    planned = sum(s["_dur"] for s in scenes)
    chk("duration matches the plan (±0.2 s)", abs(dur - planned) <= 0.2, f"{dur:.2f}s vs {planned:.2f}s", 5)
    blk = _ff(["-i", video, "-vf", "blackdetect=d=0.25:pic_th=0.985:pix_th=0.04", "-an", "-f", "null", "-"])
    blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", blk)
    chk("no unplanned black frames (>0.25 s)", not blacks, [f"{a}-{b}" for a, b in blacks][:5], 10)
    frz = _ff(["-i", video, "-vf", "freezedetect=n=-60dB:d=1.5", "-an", "-f", "null", "-"])
    freezes = re.findall(r"freeze_start: ([\d.]+)", frz)
    chk("no frozen picture (>1.5 s)", not freezes, freezes[:5], 5)
    eb = _ff(["-i", video, "-af", "ebur128=peak=true", "-f", "null", "-"])
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", eb)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", eb)
    lufs = float(I[-1]) if I else None
    peak = float(tp[-1]) if tp else None
    chk("loudness -16..-12 LUFS", lufs is not None and -16 <= lufs <= -12, lufs, 6)
    chk("true peak <= -1.0 dBTP", peak is not None and peak <= -1.0, peak, 4)
    sil = _ff(["-i", video, "-af", "silencedetect=n=-45dB:d=1.0", "-f", "null", "-"])
    silences = re.findall(r"silence_start: ([\d.]+)", sil)
    chk("no silent gaps (>1 s)", not silences, silences[:5], 5)
    le, lw = layout_issues(scenes, ctx)
    rep["errors"] += le
    rep["warnings"] += lw
    chk("no text or graphics cut off at the frame edge", not le, len(le), 5)
    first = scenes[0] if scenes else {}
    chk("hook: first scene is a hook-type scene and <= 3 s", first.get("type") in ("hook", "kinetic", "showcase", "location", "contrast", "counter")
        and first.get("_dur", 9) <= 3.0, f"{first.get('type')} {first.get('_dur', 0):.2f}s", 5)
    last = scenes[-1] if scenes else {}
    chk("ends on a CTA held >= 4 s", last.get("type") == "cta" and last.get("_dur", 0) >= 4.0, f"{last.get('type')} {last.get('_dur', 0):.2f}s", 5)
    shots = sum(max(1, len(sc.get("items", []))) if sc.get("type") == "gallery" else 1 for sc in scenes)
    avg = planned / max(1, shots)
    chk("average shot 1.2-4.0 s", 1.2 <= avg <= 4.0, f"{avg:.2f}s", 5)
    plat = PLATFORMS.get(brief.get("platform", ""))
    if plat and not plat[2][0] <= dur <= plat[2][1]:
        rep["warnings"].append(f"length {dur:.1f}s is outside the usual {plat[2][0]}-{plat[2][1]} s for {brief.get('platform')}")
    rep["auto_points"] = pts
    rep["auto_max"] = 75
    if creative:
        crit = ["hook strength", "clarity / readability", "pacing / rhythm", "aesthetics / brand", "message / CTA"]
        sc_ = [max(0, min(5, float(x))) for x in creative][:5]
        rep["creative"] = dict(zip(crit, sc_))
        rep["score"] = round(pts + sum(sc_))
    else:
        rep["creative"] = None
        rep["score"] = None
        rep["score_auto_only"] = round(pts / 75 * 100)
    if out_prefix:
        sheet = out_prefix + "_qa_sheet.jpg"
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", video, "-vf", "fps=1,scale=180:-1,tile=8x4", "-frames:v", "1", sheet])
        rep["contact_sheet"] = sheet
        md = [f"# QA report - {os.path.basename(video)}", "",
              f"Automatic checks: **{pts}/75**" + (f" · creative review: **{sum(sc_):g}/25** · total **{rep['score']}/100**" if creative else
                                                    " · creative review (25 pts) not scored yet"), "",
              "| check | result | value | points |", "|---|---|---|---|"]
        for c in rep["checks"]:
            md.append(f"| {c['check']} | {'pass' if c['ok'] else 'FAIL'} | {c['value']} | {c['points']}/{c['max']} |")
        if creative:
            md += ["", "Creative review (reviewer's judgement, 0-5 each - subjective, not a measurement):", ""]
            md += [f"- {k}: {v:g}/5" for k, v in rep["creative"].items()]
        for title, lst in (("Errors", rep["errors"]), ("Warnings", rep["warnings"])):
            if lst:
                md += ["", f"## {title}", ""] + [f"- {x}" for x in lst]
        md += ["", f"Contact sheet: {os.path.basename(sheet)}"]
        open(out_prefix + "_qa.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
        json.dump(rep, open(out_prefix + "_qa.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    return rep


RUNS_LOG = os.path.expanduser("~/.cache/promo-reel/runs.jsonl")


def log_run(brief_path, out, scenes, ctx, rep, secs):
    """Production log for learning across jobs: one JSON line per render (never edits the skill itself)."""
    os.makedirs(os.path.dirname(RUNS_LOG), exist_ok=True)
    rec = {"time": __import__("time").strftime("%Y-%m-%d %H:%M"), "engine": VERSION, "brief": os.path.abspath(brief_path),
           "out": os.path.abspath(out), "format": f"{ctx.W}x{ctx.H}", "scenes": [s["type"] for s in scenes],
           "duration": round(sum(s["_dur"] for s in scenes), 2), "render_seconds": round(secs, 1),
           "qa_auto": rep.get("auto_points") if rep else None, "qa_score": rep.get("score") if rep else None,
           "errors": (rep or {}).get("errors", []), "warnings": (rep or {}).get("warnings", [])[:6]}
    with open(RUNS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def history(n=10):
    if not os.path.exists(RUNS_LOG):
        print("no renders logged yet")
        return
    lines = open(RUNS_LOG, encoding="utf-8").read().strip().split("\n")[-n:]
    for l in lines:
        r = json.loads(l)
        print(f"{r['time']}  v{r['engine']}  {os.path.basename(r['out'])}  {r['duration']}s  QA auto {r['qa_auto']}/75"
              f"{'  total ' + str(r['qa_score']) if r['qa_score'] is not None else ''}  errors {len(r['errors'])}  {' > '.join(r['scenes'])}")


def selftest(workers=2):
    """Render every scene type at draft size from synthetic media, then run QA. Prints PASS/FAIL."""
    import tempfile
    d = tempfile.mkdtemp(prefix="promo_selftest_")
    for i, col in enumerate(((40, 120, 200), (200, 140, 60), (60, 160, 110))):
        g = np.linspace(0, 1, 900)[None, :, None] * np.array(col)[None, None, :] + np.linspace(0, 1, 600)[:, None, None] * 60
        Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).save(os.path.join(d, f"p{i}.jpg"))
    subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=720x1280:d=4", "-pix_fmt", "yuv420p",
                    os.path.join(d, "v.mp4")])
    t = np.arange(SR * 30) / SR
    y = 0.4 * np.sin(2 * np.pi * 55 * (t % 0.5)) * np.exp(-(t % 0.5) * 18) + 0.08 * np.sin(2 * np.pi * 330 * t)
    with wave.open(os.path.join(d, "m.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.repeat(y[:, None], 2, 1) * 32767 * 0.8).astype(np.int16).tobytes())
    # synthetic "voice": three voiced phrases separated by pauses, to exercise caption alignment
    tv = np.arange(int(SR * 7.5)) / SR
    env = sum(((tv > a) & (tv < b)).astype(float) for a, b in ((0.6, 2.0), (2.6, 3.8), (4.4, 6.2)))
    vo = env * 0.3 * np.sin(2 * np.pi * 180 * tv) * (0.6 + 0.4 * np.sin(2 * np.pi * 4 * tv))
    with wave.open(os.path.join(d, "vo.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.repeat(vo[:, None], 2, 1) * 32767).astype(np.int16).tobytes())
    brief = {"out": "selftest.mp4", "theme": {"preset": "tech", "type": "tech", "bg_style": "tech"}, "fps": 24,
             "voiceover": {"file": "vo.wav", "text": "שלום לכולם. זה מבחן כתוביות, אוטומטי לגמרי.", "at": 0.5},
             "music_free_version": True,
             "brand": {"name": "בדיקה", "phone": "050-000-0000"}, "music": {"file": "m.wav", "volume": 0.8},
             "scenes": [
                 {"type": "kinetic", "kicker": "SELF TEST", "lines": ["שורה ראשונה", {"text": "מודגש", "style": "accent"}], "dur": 1.2},
                 {"type": "hook", "style": "box", "small": "תווית", "icon": "pin", "big": "כותרת", "clip": "p0.jpg", "dur": 1.0},
                 {"type": "showcase", "label": "סלון", "icon": "home", "title": "מול הנוף", "clip": {"src": "p1.jpg", "move": "pan_left"}, "dur": 1.0},
                 {"type": "showcase", "style": "words", "title": "וידאו אמיתי", "clip": "v.mp4", "dur": 1.0, "transition": "leak"},
                 {"type": "location", "place": "מקום", "title": "כותרת", "clip": "p2.jpg", "dur": 1.2},
                 {"type": "features", "items": [{"icon": "wifi", "text": "אחד"}, {"icon": "snow", "text": "שתיים"}], "dur": 1.4},
                 {"type": "cards", "title": "כרטיסים", "items": [{"icon": "home", "title": "אתרים"}, {"icon": "people", "title": "CRM"}], "dur": 1.4},
                 {"type": "steps", "title": "תהליך", "items": [{"title": "שלב"}, {"title": "שלב"}], "dur": 1.4},
                 {"type": "device", "ui": "flow", "title": "מכשיר", "dur": 1.4},
                 {"type": "contrast", "items": [{"text": "לא", "mark": "x"}, {"text": "כן", "mark": "check"}], "prompt": "בדיקת הקלדה",
                  "caption2": "כיתוב אחרי הסימון", "dur": 1.6},
                 {"type": "gallery", "items": [{"src": "p0.jpg", "label": "תווית", "tag": "תגית"}, {"src": "v.mp4", "label": "וידאו"}],
                  "per": 0.5, "dur": 1.5},
                 {"type": "gallery", "device": "laptop", "items": [{"src": "p1.jpg", "label": "כותרת", "tag": "תגית"}], "dur": 1.0},
                 {"type": "wall", "title": "קיר 3 עבודות", "images": ["p0.jpg", "p1.jpg", "p2.jpg"],
                  "quotes": [{"text": "ציטוט בדיקה", "who": "בדיקה"}], "quotes_at": 0.3, "dur": 1.4},
                 {"type": "bundle", "items": [{"title": "אחד", "text": "שורה", "image": "p2.jpg", "tags": ["תג"]}, {"title": "שתיים"}], "dur": 1.4},
                 {"type": "logo", "dur": 1.0},
                 {"type": "cta", "headline": "צרו קשר", "dur": 1.6}]}
    bp = os.path.join(d, "brief.json")
    json.dump(brief, open(bp, "w"), ensure_ascii=False)
    t0 = __import__("time").time()
    cwd = os.getcwd()
    try:
        run(bp, os.path.join(d, "selftest.mp4"), "9x16", True, workers, False, None, cleanup=True, creative=None, do_qa=True)
    finally:
        os.chdir(cwd)
    rep = json.load(open(os.path.join(d, "selftest_qa.json"))) if os.path.exists(os.path.join(d, "selftest_qa.json")) else {}
    # second pass: the same scenes with fx energy 3 (beat punches, shake, crazy transitions, gallery pop-outs)
    bfx = dict(brief, out="selftest_fx.mp4", fx={"energy": 3}, music_free_version=False)
    bfx.pop("voiceover", None)
    bpx = os.path.join(d, "brief_fx.json")
    json.dump(bfx, open(bpx, "w"), ensure_ascii=False)
    try:
        run(bpx, os.path.join(d, "selftest_fx.mp4"), "9x16", True, workers, False, None, cleanup=True, creative=None, do_qa=True)
    finally:
        os.chdir(cwd)
    qfx = os.path.join(d, "selftest_fx_qa.json")
    rfx = json.load(open(qfx)) if os.path.exists(qfx) else {"errors": ["energy render missing"]}
    rep.setdefault("errors", []).extend("fx pass: " + e for e in rfx.get("errors", []))
    print("fx pass:", "ok" if os.path.exists(os.path.join(d, "selftest_fx.mp4")) and not rfx.get("errors") else "FAILED")
    # third pass: the browser renderer ("renderer": "web") on the scene types it draws
    web_types = ("kinetic", "contrast", "gallery", "wall", "bundle", "logo", "cta")
    bw = dict(brief, out="selftest_web.mp4", renderer="web", music_free_version=False,
              scenes=[dict(sc_) for sc_ in brief["scenes"] if sc_["type"] in web_types])
    # with generated narration (offline stand-in voice): scene lines, longer scenes, captions, ducking
    bw["voiceover"] = {"tts": {"engine": "synthetic"}, "caption_size": 56}
    bw["scenes"][0]["say"] = "בדיקת קריינות ראשונה."
    bw["scenes"][1]["say"] = "שורה שנייה, קצת יותר ארוכה מהראשונה."
    bw["scenes"][-1]["say"] = "וזה הסיום."
    bw["scenes"][3]["items"][0]["pop"] = {"box": [0.2, 0.2, 0.8, 0.6], "scale": 1.3}
    bpw = os.path.join(d, "brief_web.json")
    json.dump(bw, open(bpw, "w"), ensure_ascii=False)
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import promo_web
        prob = promo_web.browser_problem()
    except ImportError:
        prob = "promo_web.py is missing next to promo_engine.py"
    if prob:
        print("web pass: skipped -", prob)
    else:
        try:
            promo_web.run_web(bpw, os.path.join(d, "selftest_web.mp4"), "9x16", True, workers, False, None, do_qa=True)
        finally:
            os.chdir(cwd)
        qw = os.path.join(d, "selftest_web_qa.json")
        rw = json.load(open(qw)) if os.path.exists(qw) else {"errors": ["web render missing"]}
        os.chdir(d)
        try:
            bn = load_brief(bpw)
            cn = Ctx(bn, "9x16", True)
            sn = plan_with_narration(bn, cn, os.path.join(d, "selftest_web_work"), d)
            said = [x for x in sn if x.get("_say")]
            short = [x["type"] for x in said if x["_dur"] < x["_say"]["lead"] + json.load(open(os.path.join(
                os.path.dirname(x["_say"]["file"]), "meta.json")))["lens"][[y["_say"]["file"] for y in said].index(x["_say"]["file"])]]
            print(f"narration: {len(said)} lines, {len(cn.captions)} captions")
            if len(said) != 3 or not cn.captions or short:
                rw.setdefault("errors", []).append(f"narration: {len(said)} lines placed, {len(cn.captions)} captions, "
                                                   f"too short: {short}")
        finally:
            os.chdir(cwd)
        rep.setdefault("errors", []).extend("web pass: " + e for e in rw.get("errors", []))
        print("web pass:", "ok" if os.path.exists(os.path.join(d, "selftest_web.mp4")) and not rw.get("errors") else "FAILED")
    os.chdir(d)
    caps = build_captions(brief)
    os.chdir(cwd)
    print("captions:", " | ".join(f"{c['s']:.2f}-{c['e']:.2f} {c['text']}" for c in caps))
    extra_ok = len(caps) >= 3 and caps[0]["s"] >= 0.9 and os.path.exists(os.path.join(d, "selftest_no_music.mp4"))
    if not extra_ok:
        rep.setdefault("errors", []).append("voiceover captions or the no-music version missing")
    hard = [c["check"] for c in rep.get("checks", []) if not c["ok"] and c["check"] not in
            ("hook: first scene is a hook-type scene and <= 3 s", "ends on a CTA held >= 4 s", "average shot 1.2-4.0 s",
             "duration matches the plan (±0.2 s)", "loudness -16..-12 LUFS", "true peak <= -1.0 dBTP")]
    ok = os.path.exists(os.path.join(d, "selftest.mp4")) and not hard and not rep.get("errors")
    print(f"SELFTEST {'PASS' if ok else 'FAIL'} in {__import__('time').time() - t0:.0f}s  ({d})")
    for c in rep.get("checks", []):
        print(f"  {'ok ' if c['ok'] else 'XX '} {c['check']}: {c['value']}")
    for e in rep.get("errors", []):
        print("  error:", e)
    return 0 if ok else 1


# ----------------------------------------------------------------- main
def run(brief_path, out, fmt, draft, workers, preview, frame_at, workdir=None, cleanup=True, creative=None, do_qa=True,
        plan=False):
    import time as _time
    t_start = _time.time()
    brief = load_brief(brief_path)
    base_dir = os.path.dirname(os.path.abspath(brief_path))
    os.chdir(base_dir)
    errs, warns = validate(brief)
    for w_ in warns:
        log("[warn] " + w_)
    if errs:
        for e_ in errs:
            log("[error] " + e_)
        raise SystemExit(2)
    ctx = Ctx(brief, fmt, draft)
    for r in ctx.ts.values():
        font_path(r[0])
    stem = os.path.splitext(out)[0]
    workdir = workdir or stem + "_work"
    os.makedirs(workdir, exist_ok=True)
    try:
        scenes = plan_with_narration(brief, ctx, workdir, base_dir)
    except TTSError as e:
        log(f"[error] narration: {e}")
        raise SystemExit(2)
    total = sum(s["_dur"] for s in scenes)
    log(f"[plan] {len(scenes)} scenes, {total:.1f}s, {ctx.W}x{ctx.H}@{ctx.fps}")
    for i, s in enumerate(scenes):
        log(f"  {i:02d} {s['_t0']:5.2f}s +{s['_dur']:.2f}s {s['type']:<12} {s.get('transition'):<8} "
            f"{(s.get('clip') or {}).get('src', '') if isinstance(s.get('clip'), dict) else ''}")
    json.dump(scenes, open(os.path.join(workdir, "plan.json"), "w"), ensure_ascii=False, indent=1, default=str)
    if plan:
        print(storyboard(scenes, brief, ctx, stem + "_storyboard.md"))
        le, lw = layout_issues(scenes, ctx)
        for x in le:
            log("[layout error] " + x)
        for x in lw:
            log("[layout warn] " + x)
        return
    if frame_at is not None:
        for fa in [float(x) for x in str(frame_at).split(",") if x.strip()]:
            for i, s in enumerate(scenes):
                if fa < s["_t0"] + s["_dur"] or i == len(scenes) - 1:
                    k = max(0, min(s["_n"] - 1, int((fa - s["_t0"]) * ctx.fps)))
                    prev = np.array(Image.open(last_frame_path(i - 1, scenes[i - 1], ctx, workdir))) if i and k < 12 else None
                    fr = next(frames(s, ctx, k0=k, count=1, prev=prev))
                    p = f"{stem}_frame_{fa:.2f}.png"
                    Image.fromarray(fr).save(p)
                    print(p)
                    break
        return
    if preview:
        thumbs = []
        tw = 270 if not ctx.land else 400
        for i, s in enumerate(scenes):
            for q in (0.5, 0.97):
                fr = next(frames(s, ctx, k0=min(s["_n"] - 1, int(s["_n"] * q)), count=1))
                im = Image.fromarray(fr)
                im = im.resize((tw, int(tw * ctx.H / ctx.W)))
                ImageDraw.Draw(im).text((8, 6), f"{i} {s['type']} {s['_t0'] + s['_dur'] * q:.1f}s", fill=(255, 255, 0),
                                        font=_label_font())
                thumbs.append(im)
        cols = 8 if not ctx.land else 4
        rows = math.ceil(len(thumbs) / cols)
        sheet = Image.new("RGB", (cols * tw, rows * thumbs[0].height), (30, 30, 30))
        for j, im in enumerate(thumbs):
            sheet.paste(im, ((j % cols) * tw, (j // cols) * im.height))
        p = stem + "_preview.jpg"
        sheet.save(p, quality=88)
        print(p)
        return
    jobs = []
    for i, s in enumerate(scenes):
        prev_p = last_frame_path(i - 1, scenes[i - 1], ctx, workdir) if i and s["transition"] not in ("cut", "flash", "punch") else None
        jobs.append((i, s, ctx, workdir, prev_p))
    paths = [None] * len(jobs)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for (p, new), j in zip(ex.map(render_scene, jobs), jobs):
            paths[j[0]] = p
            log(f"[scene {j[0]:02d}] {'rendered' if new else 'cached'}")
    lst = os.path.join(workdir, "concat.txt")
    with open(lst, "w") as f:
        for p in paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
    vid = os.path.join(workdir, "video.mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    wav = os.path.join(workdir, "mix.wav")
    build_audio(brief, scenes, ctx, wav)
    tmp = stem + ".tmp.mp4"
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", vid, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out)
    if brief.get("music_free_version"):
        nm = stem + "_no_music.mp4"
        b2 = dict(brief)
        b2.pop("music", None)
        wav2 = os.path.join(workdir, "mix_nomusic.wav")
        build_audio(b2, scenes, ctx, wav2)
        subprocess.run([FFMPEG, "-y", "-v", "error", "-i", vid, "-i", wav2, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                        "-shortest", "-movflags", "+faststart", nm], check=True)
        print(nm)
    ci = min(len(scenes) - 1, int(brief.get("cover_scene", 0)))
    cov = next(frames(scenes[ci], ctx, k0=min(scenes[ci]["_n"] - 1, int(scenes[ci]["_n"] * 0.7)), count=1))
    Image.fromarray(cov).save(stem + "_cover.jpg", quality=92)
    if cleanup:
        keep = {os.path.abspath(p) for p in paths}
        for f in glob.glob(os.path.join(workdir, "s[0-9][0-9]_*.mp4")):
            if os.path.abspath(f) not in keep:
                os.remove(f)
        keep_last = {p[:-4] + "_last.png" for p in keep}
        for f in glob.glob(os.path.join(workdir, "s[0-9][0-9]_*_last.png")):
            if os.path.abspath(f) not in keep_last:
                os.remove(f)
    print(out)
    rep = None
    if do_qa and brief.get("qa", True):
        rep = qa(out, brief, scenes, ctx, creative, stem)
        log(f"[qa] automatic {rep['auto_points']}/75" + (f", total {rep['score']}/100" if rep.get("score") is not None else
                                                          " (creative review pending)") +
            f", {len(rep['errors'])} errors, {len(rep['warnings'])} warnings -> {stem}_qa.md")
    try:
        log_run(brief_path, out, scenes, ctx, rep, _time.time() - t_start)
    except Exception as ex:
        log(f"[log] could not write the production log: {ex}")


def qa_only(brief_path, video, fmt, draft, creative):
    brief = load_brief(brief_path)
    os.chdir(os.path.dirname(os.path.abspath(brief_path)))
    validate(brief)
    ctx = Ctx(brief, fmt, draft)
    stem = os.path.splitext(video)[0]
    scenes = plan_with_narration(brief, ctx, stem + "_work" if os.path.isdir(stem + "_work") else os.path.dirname(os.path.abspath(video)))
    rep = qa(video, brief, scenes, ctx, creative, stem)
    print(stem + "_qa.md")
    print(json.dumps({k: rep[k] for k in ("auto_points", "score", "creative", "errors", "warnings") if k in rep}, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description="promo_engine v" + VERSION)
    ap.add_argument("brief", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--format")
    ap.add_argument("--draft", action="store_true", help="half resolution, fast encode")
    ap.add_argument("--preview", action="store_true", help="contact sheet only")
    ap.add_argument("--frame", help="render full-size frames at these seconds, e.g. 1.5,8,20")
    ap.add_argument("--plan", action="store_true", help="write <out>_storyboard.md and check the layout, no render")
    ap.add_argument("--qa", metavar="VIDEO", help="run QA on an already rendered video")
    ap.add_argument("--creative", help="reviewer scores 0-5: hook,clarity,pacing,aesthetics,message e.g. 5,4,5,4,5")
    ap.add_argument("--no-qa", action="store_true")
    ap.add_argument("--new", choices=sorted(TEMPLATES), help="print a starter brief")
    ap.add_argument("--brand-from", metavar="DIR", help="extract a brand kit from a website folder/repo")
    ap.add_argument("--kit", default="brand_kit.json", help="output path for --brand-from")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--history", action="store_true", help="show the production log")
    ap.add_argument("--workers", type=int, default=max(1, min(4, os.cpu_count() or 2)))
    ap.add_argument("--variant", help="name of a variant in brief['variants'] to apply")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest(a.workers))
    if a.history:
        return history()
    if a.new:
        print(json.dumps(TEMPLATES[a.new], ensure_ascii=False, indent=1))
        return
    if a.brand_from:
        brand_from(a.brand_from, a.kit)
        return
    if not a.brief:
        ap.error("a brief.json is required")
    creative = [x for x in a.creative.split(",")] if a.creative else None
    brief = load_brief(a.brief)
    fmts = [a.format] if a.format else brief.get("formats", [brief.get("format", "9x16")])
    if a.qa:
        return qa_only(a.brief, os.path.abspath(a.qa), fmts[0], a.draft, creative)
    variants = [None]
    if a.variant:
        variants = [a.variant]
    elif brief.get("variants") and not (a.preview or a.frame is not None or a.plan):
        variants = [None] + [v["name"] for v in brief["variants"]]
    raw = json.load(open(a.brief, encoding="utf-8"))
    for fmt in fmts:
        for var in variants:
            bp = os.path.abspath(a.brief)
            if var:
                b2 = json.loads(json.dumps(raw))
                v = next(v for v in raw["variants"] if v["name"] == var)
                for idx, ov in v.get("scenes", {}).items():
                    b2["scenes"][int(idx)].update(ov)
                bp = os.path.join(os.path.dirname(bp), f".brief_{var}.json")
                json.dump(b2, open(bp, "w"), ensure_ascii=False)
            out = a.out or brief.get("out", "promo.mp4")
            stem, ext = os.path.splitext(os.path.abspath(out if os.path.isabs(out) else os.path.join(os.path.dirname(os.path.abspath(a.brief)), out)))
            if len(fmts) > 1 or fmt != brief.get("format", "9x16"):
                stem += "_" + fmt
            if a.draft:
                stem += "_draft"
            wd = stem + "_work"
            if var:
                stem += "_" + var
            if load_brief(bp).get("renderer") == "web":
                # the browser renderer (promo_web.py, next to this file): CSS 3D, motion blur, sharp type
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                import promo_web
                promo_web.run_web(bp, stem + ext, fmt, a.draft, a.workers, a.preview, a.frame, wd, creative=creative,
                                  do_qa=not a.no_qa, plan=a.plan)
                continue
            run(bp, stem + ext, fmt, a.draft, a.workers, a.preview, a.frame, wd, cleanup=len(variants) == 1,
                creative=creative, do_qa=not a.no_qa, plan=a.plan)


if __name__ == "__main__":
    main()
