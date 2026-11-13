---
name: promo-reel-maker
description: Make branded, beat-synced promo videos (Reels/TikTok/Status ads) for a business from its clips, logo and details. Hebrew/RTL first; 9:16 plus 1:1, 4:5, 16:9. Use for סרטון פרסומי, רילס לעסק, or 'make a video like this'.
---

# Promo Reel Maker

Turns a business's raw clips/photos plus a few facts into a polished 20-40 s ad: kinetic gradient typography, a hook with footage playing *inside* the letters, red "problem" stamps that slam in, a logo reveal with a light sweep, service cards, a photo collage, counting stats, an animated checklist with the clip in a card, testimonial card with stars, before/after wipe, offer badge, and a CTA with a chat button, phone number and a tap animation. Cuts snap to the music's beat; whooshes/impacts/pops are placed automatically; audio is loudness-normalized; a cover image is exported. Everything is driven by one JSON brief and rendered by the bundled engine (Python + Pillow + numpy + ffmpeg, no browser). Unchanged scenes are cached, so edits and A/B hook variants re-render only what changed.

## 0. Setup (once per session)

1. Extract the engine from this SKILL.md (no retyping). The skill's base directory is given when the skill loads; if not, find it with `find / -name SKILL.md -path "*promo-reel-maker*" 2>/dev/null | head -1`.
```bash
python3 - "<skill base dir>/SKILL.md" <<'EOF'
import sys, os
s = open(sys.argv[1], encoding="utf-8").read()
code = s.rsplit("<!-- ENGINE:" + "BEGIN -->", 1)[1].rsplit("<!-- ENGINE:" + "END -->", 1)[0]
code = code.split("```python\n", 1)[1].rsplit("```", 1)[0]
p = os.path.expanduser("~/.cache/promo-reel/promo_engine.py")
os.makedirs(os.path.dirname(p), exist_ok=True)
open(p, "w", encoding="utf-8").write(code)
print(p)
EOF
python3 -m py_compile ~/.cache/promo-reel/promo_engine.py && echo engine-ok
```
   Only if SKILL.md is not readable on disk, write the code block in the Engine section verbatim to that path. If py_compile reports an error, fix that line.
2. Check tools: `ffmpeg -version`, `python3 -c "import numpy, PIL; from PIL import features; print(features.check('raqm'))"`. If raqm is False: `pip install python-bidi --break-system-packages` (needed for correct Hebrew order). scipy is optional (only for synthesized fallback SFX); `qrcode` only if a QR is wanted.
3. Fonts (Rubik, Heebo, Secular One, Frank Ruhl, Assistant, Rubik Dirt, Suez One, Karantina, Fredoka, Varela Round) download automatically from Google Fonts on GitHub into ~/.cache/promo_fonts; if blocked, the engine falls back to local Hebrew fonts.

Below, `E=~/.cache/promo-reel/promo_engine.py`.

## 1. Gather inputs

Required: business name; what they offer (list of services/products); who it is for; contact (phone/WhatsApp and/or website); footage (videos/photos or a folder).
Optional: logo PNG (transparent is best; without one the engine draws an emblem from `initials`), brand colors or vibe, tagline, REAL numbers (clients, years, workers, projects, rating), a REAL testimonial, an offer, length (default about 30 s), formats (default 9:16), music vibe.
Ask for missing required items in one short message; don't block on optional ones.

If the user sends a reference video ("make one like this"): analyze it first - contact sheet (`ffmpeg -i ref.mp4 -vf "fps=1,scale=180:-1,tile=12x3" -frames:v 1 ref.jpg`), cut detection (`ffmpeg -i ref.mp4 -vf "select='gt(scene,0.12)',showinfo" -an -f null - 2>&1 | grep -o "pts_time:[0-9.]*"`), and a spectrogram (`showspectrumpic`) to see music vs voice and where SFX hit. Map its structure and pacing onto the scene types below. Imitate structure and pacing only - never reuse another business's brand, logo, footage or copy in the user's video.

## 2. Write the script (the ad formula)

| # | scene type | purpose | example copy | typical dur |
|---|---|---|---|---|
| 1 | hook | stop the scroll with the pain as a question | small "חסרים לך" / big "פועלים?" | 2.2 s |
| 2 | stamp (1-2x) | consequence of the pain | "הפרויקט" + stamp "נתקע"; "כל יום בלי צוות" + "עולה לך כסף" | 1.7-1.9 s |
| 3 | logo | brand + tagline | name + "כוח אדם מקצועי לבנייה" | 2.5 s |
| 4 | services | what you offer, fast cuts | small "צוותים של" / big "טפסנים", "ברזלנים"... (3-6 items) | 0.9-1.1 s each |
| 5 | collage | "we have it all" | "הצוות שחסר לך" / "מוכן לעבודה" | 2.4 s |
| 6 | stats (1-2) | proof - real numbers only | prefix "מעל", 550, label "עובדים מקצועיים" | 2 s each |
| 7 | checklist | 3 benefits, 2-3 words each | "מגיעים מהר", "בלי בירוקרטיה", "עומדים בהתחייבויות" | 3.5-4 s |
| 8 | testimonial / before_after / offer | social proof, result, or deal (pick what is real) | | 2.8-4.2 s |
| 9 | title | who it's for | small "פתרון מיידי" / big "לקבלנים" / big2 "רשומים" | 1.7 s |
| 10 | cta | one clear action | eyebrow, "לקבלת הצעת מחיר", button, phone | 5 s |

Copy rules: Hebrew unless asked otherwise; one idea per scene; big lines short (about 12 characters looks best - longer lines auto-shrink); small lines up to about 25 characters; digits for numbers; total 25-40 s, 10-16 scenes; CTA at least 4 s.
Honesty: never invent numbers, testimonials, client names, certifications or prices. If something is missing, drop that scene, or use an obviously marked placeholder and tell the user it must be replaced before publishing. The CTA button draws a generic chat icon (no third-party logos); naming WhatsApp in the button text is fine.
Unless the user wants to approve copy first, go straight to the preview and show the script together with the preview sheet.

## 3. Prepare footage

- Work on copies in a project folder; keep brief.json next to the media (paths in the brief are relative to it).
- For every clip: `ffprobe` (size, duration, rotation) and a contact sheet (`ffmpeg -i c.mp4 -vf "fps=3,scale=160:-1,tile=8x3" -frames:v 1 c.jpg`) - look at it.
- Burnt-in text, subtitles, watermarks, UI overlays (common in clips taken from social media or other ads): crop them out (`-vf crop=w:h:x:y`) or skip those seconds. Check the whole clip - animated text moves through the frame.
- Casting: hook = the most colorful, high-motion clip (it fills the letters); stamps = problem footage (rendered black-and-white); one clip per service item; stats/checklist = clean, calm shots; CTA = anything (it is blurred).
- The engine handles: landscape/square clips (auto blur-fill), photos (Ken Burns), rotation, best-moment selection when `start` is omitted (most active window, never the same moment twice), clips shorter than their scene (they loop - prefer `"speed": 0.6` slow-mo or a shorter `dur`).
- No footage at all: scenes without a clip render on a branded grid panel. It works, but tell the user real footage converts better.

## 4. Sound

Follow the video-sound-effects skill if it is available (Soundza first, then Openverse/Wikimedia). Save files in `assets/sfx/` and list them in `assets/sfx/CREDITS.md`.

Music: Soundza `search_sounds` with type=music, parts=full_mix, vocals=none, fit_seconds=<video length>, a mood/genre that fits the business (trap/hip-hop for construction and trades, upbeat corporate for services, lo-fi for cafes, cinematic for real estate). If nothing fits, `generate_music` with model="lyria", duration about length+10 s, bpm 120-140, a plain description of business and vibe - and tell the user the music is AI-generated.
Check the track before using it - generated and library tracks often contain breakdowns, near-silent bars or a sparse intro. Print an energy map; skip an intro with `music.start`, and splice out a breakdown that would land under the collage/CTA on strong beat onsets:
```python
import sys, os, wave, numpy as np
sys.path.insert(0, os.path.expanduser("~/.cache/promo-reel")); import promo_engine as pe
x = pe.load_audio("assets/sfx/music.wav", 0, None, loop=False); y = x.mean(1); sr = pe.SR
print(" ".join(f"{t:.2f}:{np.sqrt((y[int(t*sr):int((t+.25)*sr)]**2).mean()):.2f}" for t in np.arange(0, len(y)/sr, .25)))
def splice(c1, c2, out):  # keep [0,c1) + [c2,end); c1/c2 = onsets of strong hits
    a, b = x[:int(c1*sr)], x[int(c2*sr):]; f = int(.008*sr); r = np.linspace(0, 1, f)[:, None]
    z = np.concatenate([a[:-f], a[-f:]*(1-r)+b[:f]*r, b[f:]])
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(z, -1, 1)*32767).astype(np.int16).tobytes())
```
The engine detects tempo and snaps every scene cut to a beat (`beat_sync`, default on).

SFX: the engine fires these names automatically. Proven Soundza picks (download once with `download_sound`; `sync` = the result's sync_ms/1000; `max` trims long files):

| name | fires on | Soundza id (title) | sync | extra |
|---|---|---|---|---|
| whoosh | zoom/whip/slide_up transitions, collage, wipe | cmujffw8b2an6jwenoz4r1gxb (Fast Cable Whoosh) | 0.293 | |
| impact | hook, stamp slam, offer slam | cmujfj249qoihsspc4q3yzwqj (Dark Boom Impact) | 0 | |
| thump | punch/flash cuts | cmvcm7a6809ezelyj5xjojlco (Punch Impact) | 0.064 | |
| pop | checklist ticks, stars | cmvcmbf6rxr815bt4tf7g6xlm (Bubble Pop UI Tap) | 0.054 | |
| click | CTA tap | cmukcwidhpq87pi9kz3rtqlqf (Mouse Click Warm) | 0.005 | |
| ding | counter lands | cmvcmbkdi4e6xbwonobll8ebf (Desk Bell Ding) | 0.315 | max 1.5, gain 0.7 |
| reveal | logo | cmvcm7nb06a2l2llux8dxyn0n (Dramatic Impact Hit) | 0.325 | max 2.5 |
| glitch | glitch transition | cmvcmf2aixr9r14u2pcug3b10 (TV Glitch) | 0 | max 0.35, gain 0.8 |

More options: Soundza pack `video-editing-sound-effects-whooshes-pops-clicks-glitches-and-camera-shutters`. Any SFX file that is missing falls back to a synthesized version, so a video never ships silent. When the video is published, suggest (optional) crediting soundza.com.

## 5. Brief, preview, render

Write `brief.json` (reference below), then:
- `python3 $E brief.json --preview --draft` - contact sheet of every scene (2 frames each) at half size, about 10-20 s. Look at it.
- `python3 $E brief.json --frame 1.2,9,15,21,31` - full-size PNGs at those seconds; look at the busiest moments (hook, collage, checklist, CTA) before the full render.
- `python3 $E brief.json` - final MP4 + `<out>_cover.jpg`. About 1 minute per 15-20 s of 1080x1920 on 2 cores; run it in the foreground with a long timeout. The plan printed first shows each scene's start, length, transition and clip.
- Edits: change the brief and run again - only scenes whose content changed re-render (cache in `<out>_work/`, keyed by scene content and clip file contents). `--draft` writes separate `_draft` files.
- Verify the final: `ffprobe` (duration, h264 + aac), loudness about -14 LUFS (`ffmpeg -i out.mp4 -af ebur128 -f null - 2>&1 | grep "I:"`), and a 1 fps contact sheet - look at it.

## 6. Deliver

Send the MP4 (and cover) with SendUserFile. In the reply: one or two lines, a ready-to-paste post caption (Hebrew, 2-3 lines + CTA + 5-8 hashtags), and offer the cheap extras: 2-3 alternative hooks for A/B testing (`variants` - only the hook re-renders) and other formats (`formats`).

## Brief reference

Example (valid JSON):
```json
{
  "out": "promo.mp4",
  "format": "9x16",
  "theme": {"preset": "gold", "type": "bold"},
  "brand": {"name": "צוותים פלוס", "tagline": "כוח אדם מקצועי לבנייה", "initials": "צפ",
            "logo": "assets/logo.png", "phone": "050-123-4567", "corner_logo": true},
  "music": {"file": "assets/sfx/music_bed.wav", "start": 0, "volume": 0.8, "beat_sync": true},
  "sfx": {"whoosh": {"file": "assets/sfx/soundza-fast-cable-whoosh.wav", "sync": 0.293},
          "impact": "assets/sfx/soundza-dark-boom-impact.wav"},
  "variants": [{"name": "B", "scenes": {"0": {"small": "הפרויקט", "big": "נתקע?"}}}],
  "scenes": [
    {"type": "hook", "small": "חסרים לך", "big": "פועלים?", "clip": "clips/colorful.mp4"},
    {"type": "stamp", "line": "הפרויקט", "stamp": "נתקע", "clip": "clips/empty_site.mp4"},
    {"type": "logo", "clip": {"src": "clips/wall.mp4", "speed": 0.85}},
    {"type": "services", "small": "צוותים של", "per": 1.0, "items": [
      {"text": "טפסנים", "clip": "clips/formwork.mp4"}, {"text": "ברזלנים", "clip": "clips/rebar.mp4"}]},
    {"type": "collage", "small": "הצוות שחסר לך", "big": "מוכן לעבודה", "clips": ["clips/a.mp4", "clips/b.jpg", "clips/c.mp4", "clips/d.mp4"]},
    {"type": "stats", "items": [{"prefix": "מעל", "value": 550, "label": "עובדים מקצועיים", "clip": "clips/e.mp4"}]},
    {"type": "checklist", "clip": "clips/f.mp4", "items": ["מגיעים מהר", "בלי בירוקרטיה", "עומדים בהתחייבויות"]},
    {"type": "title", "small": "פתרון מיידי", "big": "לקבלנים", "big2": "רשומים", "clip": "clips/g.mp4"},
    {"type": "cta", "clip": "clips/f.mp4", "eyebrow": "מיועד לקבלנים רשומים", "headline": "לקבלת הצעת מחיר", "button": "שלחו הודעה בוואטסאפ"}
  ]
}
```

Top-level fields:
- `out` (default promo.mp4); `format`: 9x16 | 1x1 | 4x5 | 16x9; `formats`: list - renders each (suffix _<fmt>); `fps` (30).
- `theme`: `preset` gold | fire | electric | fresh | royal | clean (light) | auto (colors from the logo); color overrides `primary, primary2, hi, accent, bg, text, muted, cta` (hex); `type` (typeset) bold | classic | condensed | elegant | playful | retro; `font_display/font_heavy/font_body/font_stamp` = a .ttf path or a font key.
- `brand`: `name, tagline, initials, logo, phone, website, corner_logo` (small logo top-left on footage scenes).
- `clips`: pool of clips (paths or specs) and/or `clips_dir`: auto-assigned to scenes that have no `clip` key (set `"clip": null` to force the panel).
- `music`: `file, start, volume (0.8), beat_sync (true)`. `voiceover`: `file, at, volume` - music ducks under it.
- `sfx`: true | false | {name: path or {file, sync, max, gain}}; `sfx_volume` (0.55).
- `variants`: [{name, scenes: {"<index in scenes>": {overrides}}}] - extra outputs `<out>_<name>.mp4` sharing the cache.

Clip spec: `"path"` or `{src, start, speed, fit: auto|cover|blur, focus: [x, y], kenburns: in|out, look: {bw, dim, blur, grade, vignette}}`.
Every scene accepts: `dur, transition, clip, look, zoom, audio` (true = keep the clip's own sound, music ducks) and `audio_volume`.

| type | fields | default dur | default transition in |
|---|---|---|---|
| hook | small, big, clip, style video\|plain, backdrop blur\|black, size | 2.2 | cut |
| stamp | line, stamp, clip, bw (true) | 1.9 | glitch |
| logo | clip, name, tagline (default: brand) | 2.5 | zoom |
| title | small, big, big2, size, underline, anim, small_anim | 1.3 | whip |
| services | small, per, items [text or {text, clip, dur}] - expands to titles | per item | whip, then punch |
| collage | small, big, clips (4-6) | 2.4 | zoom |
| counter | prefix, value, num_prefix, suffix, decimals, label, size, clip | 2.0 | slide_up |
| stats | items [counter fields] - expands to counters | 2.0 each | slide_up |
| checklist | items (up to 4, short), title, clip (shown in a card) | 0.5 + 0.7 per item + 1.3 | zoom |
| testimonial | quote, name, role, stars, clip | 4.2 | fade |
| before_after | before, after, labels, wipe_at, caption | 3.6 | whip |
| offer | badge, big, small, note, clip | 2.8 | flash |
| text | lines [str or {text, style small\|body\|big\|accent, anim, size}], clip | 2.0 | punch |
| cta | eyebrow, headline, button (text or false), phone, website, qr (url), logo (true), tap_at, clip | 5.0 | zoom |

Transitions: cut, flash, punch, fade, zoom, whip, slide_up, glitch. Text animations: up, down, fade, pop, zoom, slam, wipe, left, right, none.
Outputs: `<out>.mp4`, `<out>_cover.jpg`, `<out>_preview.jpg`, `<out>_frame_<t>.png`, `<out>_work/` (cache + plan.json with final timings).

## Troubleshooting

- Hebrew letters in reverse order: raqm is missing - install python-bidi.
- A clip shows old captions/watermarks: crop the clip; look at the whole clip, not one frame.
- Visible loop jump: the clip is shorter than its scene - add `speed` < 1 or shorten `dur`.
- A scene lands too long/short after beat snapping: set its `dur` explicitly, or `"beat_sync": false`.
- Text too long: it auto-shrinks; shorten the copy instead for impact.
- Music has a gap under the CTA: re-splice (section 4) or change `music.start`.

## Engine

<!-- ENGINE:BEGIN -->
```python
{{ENGINE}}```
<!-- ENGINE:END -->
