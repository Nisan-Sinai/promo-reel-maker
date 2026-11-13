#!/usr/bin/env python3
"""promo_engine.py - branded short-form promo videos (Hebrew/RTL first) from a JSON brief.
Usage:
  python3 promo_engine.py brief.json [--out out.mp4] [--format 9x16|1x1|4x5|16x9]
                          [--preview] [--frame SECONDS] [--draft] [--workers N]
Needs: python3, numpy, Pillow (with raqm for RTL; else pip install python-bidi), ffmpeg.
"""
import argparse, glob, hashlib, json, math, os, shutil, subprocess, sys, wave
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

VERSION = "1.0.1"
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
    "clean":    dict(bg="#F3F5F9", primary="#1F6FEB", primary2="#0A3A8C", hi="#8FC2FF", accent="#E5484D", text="#0D1321", muted="#46536A", cta="#25D366"),
}
GF = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
FONT_FILES = {
    "rubik": "rubik/Rubik[wght].ttf", "heebo": "heebo/Heebo[wght].ttf", "secular": "secularone/SecularOne-Regular.ttf",
    "frank": "frankruhllibre/FrankRuhlLibre[wght].ttf", "assistant": "assistant/Assistant[wght].ttf",
    "rubikdirt": "rubikdirt/RubikDirt-Regular.ttf", "suez": "suezone/SuezOne-Regular.ttf",
    "karantina": "karantina/Karantina-Bold.ttf", "fredoka": "fredoka/Fredoka[wdth,wght].ttf",
    "varela": "varelaround/VarelaRound-Regular.ttf",
}
TYPESETS = {
    "bold":      dict(display=("rubik", 900), heavy=("heebo", 800), body=("heebo", 600), stamp=("rubikdirt", 0)),
    "classic":   dict(display=("secular", 0), heavy=("heebo", 800), body=("heebo", 600), stamp=("rubikdirt", 0)),
    "condensed": dict(display=("karantina", 0), heavy=("heebo", 800), body=("heebo", 600), stamp=("rubikdirt", 0)),
    "elegant":   dict(display=("frank", 900), heavy=("assistant", 800), body=("assistant", 600), stamp=("frank", 900)),
    "playful":   dict(display=("fredoka", 700), heavy=("fredoka", 600), body=("varela", 0), stamp=("rubikdirt", 0)),
    "retro":     dict(display=("suez", 0), heavy=("heebo", 800), body=("heebo", 600), stamp=("rubikdirt", 0)),
}
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


def wrap_text(text, f, max_w):
    out = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            cand = (cur + " " + w).strip()
            if cur and f.getlength(_vis(cand), **_kw(cand)) > max_w:
                out.append(cur)
                cur = w
            else:
                cur = cand
        out.append(cur)
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
        if draft:
            W, H = W // 2, H // 2
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
        for role in ("display", "heavy", "body", "stamp"):
            if th.get("font_" + role):
                v = th["font_" + role]
                ts[role] = (v, 0) if isinstance(v, str) else tuple(v)
        self.ts = ts
        self.grad = [self.c["hi"], self.c["primary"], self.c["primary2"]]
        mt = {"9x16": (0.11, 0.80), "4x5": (0.07, 0.90), "1x1": (0.07, 0.93), "16x9": (0.08, 0.92)}[fmt]
        self.top, self.bot = int(mt[0] * H), int(mt[1] * H)
        self.cy = (self.top + self.bot) // 2
        self.brand = brief.get("brand", {})
        self._panel = None
        self._logo = None

    def font(self, role, size):
        return get_font(self.ts[role], size * self.U)

    def T(self, text, role="body", size=60, color=None, grad=False, shadow=0.55, stroke=0, stroke_rgb=(0, 0, 0),
          max_w=None, glow=None, wrap=False):
        max_w = max_w or self.W * (0.62 if self.land else 0.88)
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

    def on_panel(self):
        return self.c["text"]

    def logo(self):
        if self._logo is None:
            p = self.brand.get("logo")
            if p and os.path.exists(p):
                im = Image.open(p).convert("RGBA")
                bb = im.getchannel("A").getbbox()
                self._logo = im.crop(bb) if bb else im
            else:
                self._logo = auto_emblem(self)
        return self._logo


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
    ini = ctx.brand.get("initials") or "".join(w[0] for w in name.split()[:2]) or "\u2605"
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
        f.append("eq=contrast=1.06:saturation=1.18")
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
        im = ImageEnhance.Color(ImageEnhance.Contrast(im).enhance(1.06)).enhance(1.18)
    if look.get("blur"):
        im = im.filter(ImageFilter.GaussianBlur(look["blur"]))
    dim = look.get("dim", 1.0)
    if dim < 0.999:
        im = im.point(lambda v: int(v * dim))
    return im


class Reader:
    """Sequential frames of a clip/photo at WxH, starting t seconds into the scene."""

    def __init__(self, spec, W, H, fps, n, t0=0.0, look=None, zoom=0.0, seed=0):
        self.spec, self.W, self.H, self.fps, self.n = spec, W, H, fps, n
        self.look, self.zoom, self.k = look or {}, zoom, int(round(t0 * fps))
        self.proc, self.img = None, None
        src = spec["src"]
        rng = np.random.default_rng(seed)
        if is_photo(src):
            im = Image.open(src).convert("RGB")
            from PIL import ImageOps
            im = ImageOps.exif_transpose(im)
            s = 1.18
            im = ImageOps.fit(im, (int(W * s), int(H * s)), Image.LANCZOS)
            self.img = pil_look(im, self.look)
            z = spec.get("kenburns", "in" if rng.random() < 0.6 else "out")
            self.z0, self.z1 = (1.0, 1.12) if z == "in" else (1.12, 1.0)
            ang = rng.uniform(0, 6.28)
            self.pan = (math.cos(ang) * 0.04, math.sin(ang) * 0.04)
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

    def next(self):
        W, H = self.W, self.H
        p = self.k / max(1, self.n - 1)
        self.k += 1
        if self.img is not None:
            z = self.z0 + (self.z1 - self.z0) * p
            iw, ih = self.img.size
            cw, ch = W / z * (iw / (W * 1.18)), H / z * (ih / (H * 1.18))
            cx = iw / 2 + self.pan[0] * iw * (p - 0.5)
            cy = ih / 2 + self.pan[1] * ih * (p - 0.5)
            a = cw / W
            fr = self.img.transform((W, H), Image.AFFINE, (a, 0, cx - cw / 2, 0, a, cy - ch / 2), Image.BILINEAR)
            return np.array(fr)
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


class Sprite:
    def __init__(self, img, cx, cy, t0=0.0, anim="up", d=0.35, rtl=True, pulse=0.0, scale_fn=None):
        self.img, self.cx, self.cy, self.t0, self.anim, self.d = img, cx, cy, t0, anim, d
        self.arr = np.asarray(img)
        self.rtl, self.pulse, self.scale_fn = rtl, pulse, scale_fn

    def draw(self, out, t, ctx, bgf=None):
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


def button(ctx, text, color=None):
    U = ctx.U
    color = color or ctx.c["cta"]
    m = text_mask(text, ctx.font("heavy", 50))
    ic = int(m.height * 1.25)
    h = int(max(m.height, ic) + 44 * U)
    w = int(m.width + ic + 26 * U + 80 * U)
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
    im.alpha_composite(chat_icon(ic, (255, 255, 255, 255)), (icx, (h - ic) // 2))
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
    els, sfx = [], [(0.04, "impact", 0.9)]
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
    tg = ctx.T(tag, "body", 56, color=fg_for(ctx, bg)) if tag else None
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
        im = pil_look(im.convert("RGB"), {"grade": True}).convert("RGBA")
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
                                 look={"grade": True, "vignette": False}, zoom=0.04)
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
    qm = ctx.T("\u201D", "display", 220, grad=True, shadow=0)
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
    bg = clip_bg(sc, {"dim": 0.42, "blur": 18}, 0.05)
    fg = fg_for(ctx, bg)
    br = ctx.brand
    lg = None
    if sc.get("logo", True):
        lg = ctx.logo()
        mw, mh = W * (0.42 if not ctx.land else 0.2), (ctx.bot - ctx.top) * 0.17
        f = min(mw / lg.width, mh / lg.height)
        lg = lg.resize((max(1, int(lg.width * f)), max(1, int(lg.height * f))), Image.LANCZOS)
        lg = finish(lg, lg.getchannel("A"), 0.5, U=U)
    eb = ctx.T(sc["eyebrow"], "heavy", 46, grad=True) if sc.get("eyebrow") else None
    hl = ctx.T(sc.get("headline", "לפרטים נוספים"), "heavy", 92, color=fg, wrap=True)
    bt = button(ctx, sc.get("button", "שלחו הודעה בוואטסאפ")) if sc.get("button", True) else None
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


BUILDERS = {"hook": b_hook, "stamp": b_stamp, "logo": b_logo, "title": b_title, "collage": b_collage,
            "counter": b_counter, "checklist": b_checklist, "testimonial": b_testimonial,
            "before_after": b_before_after, "offer": b_offer, "text": b_text, "cta": b_cta}
DEFAULT_DUR = {"hook": 2.2, "stamp": 1.9, "logo": 2.5, "title": 1.3, "collage": 2.4, "counter": 2.0,
               "testimonial": 4.2, "before_after": 3.6, "offer": 2.8, "text": 2.0, "cta": 5.0}
DEFAULT_TRANS = {"hook": "cut", "stamp": "glitch", "logo": "zoom", "title": "whip", "collage": "zoom",
                 "counter": "slide_up", "checklist": "zoom", "testimonial": "fade", "before_after": "whip",
                 "offer": "flash", "text": "punch", "cta": "zoom"}
TRANS_SFX = {"zoom": "whoosh", "whip": "whoosh", "slide_up": "whoosh", "glitch": "glitch", "flash": "thump", "punch": "thump"}
TRANS_LEN = {"flash": 6, "zoom": 9, "whip": 9, "slide_up": 9, "glitch": 7, "punch": 8, "fade": 9}


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


def transition(kind, out, prev, k, U, rng):
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
                     "transition": sc.get("transition", "whip" if j == 0 else "punch")}
                out.append(s)
        elif t == "stats":
            for j, it in enumerate(sc.get("items", [])):
                s = {"type": "counter", **it}
                s.setdefault("transition", "slide_up")
                out.append(s)
        else:
            out.append(dict(sc))
    return out


NEEDS_CLIP = {"hook", "stamp", "logo", "title", "counter", "checklist", "offer", "text", "cta", "testimonial"}


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
    mus = brief.get("music") or {}
    beats = np.array([])
    if mus.get("file") and mus.get("beat_sync", True) and os.path.exists(mus["file"]):
        y = load_audio(mus["file"], float(mus.get("start", 0)), sum(durs) * 1.5 + 5).mean(1)
        beats, bpm = detect_beats(y)
        log(f"[music] ~{bpm:.0f} BPM, {len(beats)} beats")
    if len(beats):
        t, nd = 0.0, []
        for i, d in enumerate(durs):
            if i == len(durs) - 1:
                nd.append(d)
                break
            c = beats[(beats > t + max(0.6, 0.72 * d)) & (beats < t + 1.45 * d + 0.25)]
            nt = float(c[np.argmin(np.abs(c - (t + d)))]) if len(c) else t + d
            nd.append(nt - t)
            t = nt
        durs = nd
    cache_p = os.path.join(workdir, "activity.json")
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    used = {}
    bounds = np.round(np.cumsum([0] + durs) * ctx.fps).astype(int)
    prev_key = ""
    for i, sc in enumerate(scenes):
        sc["_n"] = int(bounds[i + 1] - bounds[i])
        sc["_dur"] = sc["_n"] / ctx.fps
        sc["_t0"] = bounds[i] / ctx.fps
        sc.setdefault("transition", DEFAULT_TRANS.get(sc["type"], "cut") if i else "cut")
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
        stamp = [(f, os.path.getmtime(f), os.path.getsize(f)) for f in srcs if f and os.path.exists(f)]
        h = hashlib.md5(json.dumps([VERSION, stamp, ctx.W, ctx.H, ctx.fps, ctx.c, ctx.ts, brief.get("brand", {}),
                                    {k: v for k, v in sc.items() if k != "_t0"},
                                    prev_key if sc["transition"] not in ("cut", "flash", "punch") else ""],
                                   sort_keys=True, default=str).encode()).hexdigest()[:12]
        sc["_key"] = h
        prev_key = h
    json.dump(cache, open(cache_p, "w"))
    return scenes


# ----------------------------------------------------------------- rendering
def build(sc, ctx):
    r = BUILDERS[sc["type"]](sc, ctx)
    bg, els, sfx = r[:3]
    extra = r[3] if len(r) > 3 else {}
    if ctx.brand.get("corner_logo") and sc["type"] not in ("hook", "logo", "cta", "collage") and bg.get("kind") == "clip":
        lg = ctx.logo()
        h = 80 * ctx.U
        lg = lg.resize((max(1, int(lg.width * h / lg.height)), int(h)), Image.LANCZOS)
        lg = finish(lg, lg.getchannel("A"), 0.5, U=ctx.U)
        els.append(Sprite(lg, 40 * ctx.U + lg.width / 2, ctx.top * 0.55 + lg.height / 2, 0.0, "none"))
    return bg, els, sfx, extra


def frames(sc, ctx, k0=0, count=None, prev=None):
    n = sc["_n"]
    count = n - k0 if count is None else count
    bg, els, _, extra = build(sc, ctx)
    W, H = ctx.W, ctx.H
    reader = None
    if bg["kind"] == "clip":
        reader = Reader(norm_clip(bg["clip"]), W, H, ctx.fps, n, t0=k0 / ctx.fps, look=bg.get("look"),
                        zoom=bg.get("zoom", 0.05), seed=int(sc["_key"], 16) % 1000)
    base = ctx.panel() if bg["kind"] == "panel" else np.zeros((H, W, 3), np.uint8)
    rng = np.random.default_rng(int(sc["_key"], 16) % 2 ** 32)
    shake = extra.get("shake")
    try:
        for k in range(k0, k0 + count):
            t = k / ctx.fps
            bgf = reader.next() if reader else base
            out = base.copy() if (bg.get("hide") or reader is None) else bgf.copy()
            for el in els:
                el.draw(out, t, ctx, bgf)
            if shake and shake[0] <= t < shake[0] + shake[1]:
                amp = 14 * ctx.U * (1 - (t - shake[0]) / shake[1])
                out = np.roll(out, (int(rng.uniform(-amp, amp)), int(rng.uniform(-amp, amp))), (0, 1))
            out = transition(sc["transition"], out, prev, k, ctx.U, rng)
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
        duck = 1 - 0.7 * np.clip(env / 0.03, 0, 1)
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
            ev = list(build(sc, ctx)[2]) if sc["type"] not in ("collage",) else [(0.4, "whoosh", 0.4)]
            tr = sc.get("transition")
            if i and tr in TRANS_SFX:
                ev.append((0.0, TRANS_SFX[tr], 0.6))
            for (tt, name, g) in ev:
                y, lead = get(name)
                s = int((sc["_t0"] + tt - lead) * SR)
                if s < 0:
                    y = y[-s:]
                    s = 0
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


# ----------------------------------------------------------------- main
def run(brief_path, out, fmt, draft, workers, preview, frame_at, workdir=None, cleanup=True):
    brief = json.load(open(brief_path))
    base_dir = os.path.dirname(os.path.abspath(brief_path))
    os.chdir(base_dir)
    ctx = Ctx(brief, fmt, draft)
    for r in ctx.ts.values():
        font_path(r[0])
    stem = os.path.splitext(out)[0]
    workdir = workdir or stem + "_work"
    os.makedirs(workdir, exist_ok=True)
    scenes = make_plan(brief, ctx, workdir)
    total = sum(s["_dur"] for s in scenes)
    log(f"[plan] {len(scenes)} scenes, {total:.1f}s, {ctx.W}x{ctx.H}@{ctx.fps}")
    for i, s in enumerate(scenes):
        log(f"  {i:02d} {s['_t0']:5.2f}s +{s['_dur']:.2f}s {s['type']:<12} {s.get('transition'):<8} "
            f"{(s.get('clip') or {}).get('src', '') if isinstance(s.get('clip'), dict) else ''}")
    json.dump(scenes, open(os.path.join(workdir, "plan.json"), "w"), ensure_ascii=False, indent=1, default=str)
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
    cov = next(frames(scenes[0], ctx, k0=min(scenes[0]["_n"] - 1, int(scenes[0]["_n"] * 0.7)), count=1))
    Image.fromarray(cov).save(stem + "_cover.jpg", quality=92)
    if cleanup:
        keep = {os.path.abspath(p) for p in paths}
        for f in glob.glob(os.path.join(workdir, "s[0-9][0-9]_*.mp4")):
            if os.path.abspath(f) not in keep:
                os.remove(f)
    print(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brief")
    ap.add_argument("--out")
    ap.add_argument("--format")
    ap.add_argument("--draft", action="store_true", help="half resolution, fast encode")
    ap.add_argument("--preview", action="store_true", help="contact sheet only")
    ap.add_argument("--frame", help="render full-size frames at these seconds, e.g. 1.5,8,20")
    ap.add_argument("--workers", type=int, default=max(1, min(4, os.cpu_count() or 2)))
    ap.add_argument("--variant", help="name of a variant in brief['variants'] to apply")
    a = ap.parse_args()
    brief = json.load(open(a.brief))
    fmts = [a.format] if a.format else brief.get("formats", [brief.get("format", "9x16")])
    variants = [None]
    if a.variant:
        variants = [a.variant]
    elif brief.get("variants") and not (a.preview or a.frame is not None):
        variants = [None] + [v["name"] for v in brief["variants"]]
    for fmt in fmts:
        for var in variants:
            bp = os.path.abspath(a.brief)
            if var:
                b2 = json.loads(json.dumps(brief))
                v = next(v for v in brief["variants"] if v["name"] == var)
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
            run(bp, stem + ext, fmt, a.draft, a.workers, a.preview, a.frame, wd, cleanup=len(variants) == 1)


if __name__ == "__main__":
    main()
