---
name: "promo-reel-maker"
description: "Make branded, beat-synced promo videos (Reels/TikTok/Shorts/Status ads, YouTube promos) for a business from its clips, photos or website/brand repo: kinetic typography, motion graphics, device mockups, portfolio galleries, proof walls and 3D pop-outs, an optional Chrome renderer for cinematic motion, automatic QA report. Hebrew/RTL first; 9:16 plus 1:1, 4:5, 16:9, up to 4K. Use for סרטון פרסומי, רילס לעסק, סרטון מיתוג, or 'make a video like this'."
---

# Promo Reel Maker

Turns a business's raw clips/photos plus a few facts into a polished 20-40 s ad: kinetic gradient typography, a hook with footage playing *inside* the letters, red "problem" stamps that slam in, a logo reveal with a light sweep, service cards, a photo collage, counting stats, an animated checklist with the clip in a card, testimonial card with stars, before/after wipe, offer badge, and a CTA with a chat button, phone number and a tap animation. Cuts snap to the music's beat; whooshes/impacts/pops are placed automatically; audio is loudness-normalized; a cover image is exported. Everything is driven by one JSON brief and rendered by the bundled engine (Python + Pillow + numpy + ffmpeg), or - for the motion-graphics scenes - by an optional browser renderer that draws every frame in Chrome. Unchanged scenes are cached, so edits and A/B hook variants re-render only what changed.

Version 2 adds what the strongest short-form ads do: photos get real camera moves (wide shots pan across instead of being cropped), footage stays bright with soft scrims and boxed caption-style text instead of a dimmed frame, a `showcase` scene for one-feature-per-shot tours, `features` (icon rows on glass), `location` (map-pin drop), a boxed hook, slide / light-leak / blur transitions, colour grades, Reels safe zones and scene lengths set in beats.

Version 3 adds brand and tech motion graphics that need no footage (Formula C): an animated brand background (moving glows, particles, slow camera push), kinetic typography with mask reveals, glass service cards with a highlight pass, a process timeline, phone/laptop mockups with animated illustrative UI or a real screenshot, a logo burst. It also adds a creative-planning step with a storyboard (`--plan`), platform presets, brand kits extracted from a website or repo (`--brand-from`), captions for a recorded voiceover, brief validation with recovery, an automatic QA report with a 0-100 score (`--qa`), a production log (`--history`), starter templates (`--new`) and a self-test (`--selftest`). v1 and v2 briefs keep rendering with the same scenes and style (multi-line text is now balanced across lines).

Version 3.1 adds the neon course/agency ad (Formula D): `contrast` (✕ what they use today, ✓ the answer, a chat bar that types a request, a caption that switches when the ✓ lands), `gallery` (a fast portfolio reel of real screenshots or clips inside a 3D phone or laptop, with a 01/07 counter and labels), `wall` (all the work on a tilted 3D wall, with quote cards for real testimonials), `bundle` (1-3 offer cards joined by "+"), a `neon` colour preset, a typing sound, and a solid pill CTA button (`button_style`, `button_icon`). v3.0 briefs render pixel-identical.

Version 3.2 adds motion styles (`fx`). `premium`: smooth, cinematic motion - elements ease in with a soft blur, cards turn gently in 3D with a light sheen, the camera settles slowly, and scenes change with push, zoom-through and cube transitions. `hype` (energy 1-3): zoom punches on the beat, camera shake, colour split and glitch on hits, a live background and fast 3D transitions (`cube`, `spin`, `zoom_blur`, `slices`, `shape`, `diamond`). Both add pop-outs to `gallery`: a block of a screenshot (a product card, a dashboard, a chat bubble) lifts out of the phone or laptop screen toward the viewer, with its real rounded corners. Without `fx`, every older brief renders pixel-identical.

Version 4 adds a second renderer, `"renderer": "web"`. The same engine plans the video, snaps it to the beat, mixes the sound, makes the cover and runs QA, but every frame of the motion-graphics scenes (kinetic, title, contrast, gallery, wall, bundle, counter/stat, logo, cta) is drawn by Chrome: real CSS 3D (phones and laptops that turn, cards that lift off the screen), sub-pixel motion with motion blur, sharp type and soft shadows. It is clearly more polished than the classic renderer and is the recommended choice for Formula D. It needs Playwright and a Chrome or Chromium browser in the workspace; when they are missing, or a brief uses a scene type it does not draw yet, the video renders with the classic renderer in the premium style automatically. The classic renderer and every older brief are unchanged.

## 0. Setup (once per session)

1. Extract the engine and the web renderer from this SKILL.md (no retyping). The skill's base directory is given when the skill loads; if not, find it with `find / -name SKILL.md -path "*promo-reel-maker*" 2>/dev/null | head -1`.
```bash
python3 - "<skill base dir>/SKILL.md" <<'EOF'
import sys, os
s = open(sys.argv[1], encoding="utf-8").read()
for tag, name in (("ENGINE", "promo_engine.py"), ("WEB", "promo_web.py")):
    code = s.rsplit("<!-- " + tag + ":" + "BEGIN -->", 1)[1].rsplit("<!-- " + tag + ":" + "END -->", 1)[0]
    code = code.split("```python\n", 1)[1].rsplit("```", 1)[0]
    p = os.path.expanduser("~/.cache/promo-reel/" + name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(code)
    print(p)
EOF
python3 -m py_compile ~/.cache/promo-reel/promo_engine.py ~/.cache/promo-reel/promo_web.py && echo engine-ok
```
   Only if SKILL.md is not readable on disk, write the code blocks in the Engine and Web renderer sections verbatim to those paths (promo_web.py must sit next to promo_engine.py). If py_compile reports an error, fix that line.
2. Check tools: `ffmpeg -version`, `python3 -c "import numpy, PIL; from PIL import features; print(features.check('raqm'))"`. If raqm is False: `pip install python-bidi --break-system-packages` (needed for correct Hebrew order). scipy is optional (only for synthesized fallback SFX); `qrcode` only if a QR is wanted.
3. Fonts (Rubik, Heebo, Secular One, Frank Ruhl, Assistant, Rubik Dirt, Suez One, Karantina, Fredoka, Varela Round, Noto Sans Hebrew, Geist, Geist Mono) download automatically from Google Fonts on GitHub into ~/.cache/promo_fonts; if blocked, the engine falls back to local Hebrew fonts.
4. Web renderer (needed only for `"renderer": "web"`): `python3 -c "import playwright" 2>/dev/null || pip install playwright --break-system-packages`, then `python3 ~/.cache/promo-reel/promo_web.py --check`. It uses a system Chrome (`/usr/bin/google-chrome`, Chromium, or the path in the `CHROME` environment variable). If it reports that no browser could start, try `python3 -m playwright install chromium` once; if the download is blocked, carry on - briefs with `"renderer": "web"` then render with the classic renderer in the premium style, and tell the user the video used the fallback.
5. Optional (about 1-2 minutes): `python3 $E --selftest` renders every scene type from synthetic media at draft size three times - as is, with `fx` energy 3 (every transition, camera hits, pop-outs), and with the web renderer (skipped, with the reason, when Chrome is not available) - and runs QA on each. It must print `fx pass: ok`, `web pass: ok` (or `skipped`) and `SELFTEST PASS` (the short test CTA is expected to miss the 4 s rule). Run it after any change to the engine.

Below, `E=~/.cache/promo-reel/promo_engine.py`.

## 1. Gather inputs

Required: business name; what they offer (list of services/products); who it is for; contact (phone/WhatsApp and/or website); footage (videos/photos or a folder) - or, for brand/tech videos, the brand's website or repo.
Optional: logo PNG (transparent is best; an opaque square icon also works - its flat background corners are removed automatically; without a logo the engine draws an emblem from `initials`), brand colors or vibe, tagline, REAL numbers (clients, years, workers, projects, rating), a REAL testimonial, an offer, length (default about 30 s), platform/formats (default Reels 9:16), music vibe, a recorded voiceover with its exact text.
Ask for missing required items in one short message; don't block on optional ones.

Brand kit from official assets: when the brand has a website folder or repo (clone a public repo with `git clone --depth 1 <url>`), run `python3 $E --brand-from <dir> --kit brand_kit.json`. It reads CSS colour variables, font families, the web manifest (name, description), the largest logo/icon PNG (saved as brand_logo.png next to the kit), the most frequent phone number and the site URL (from SITE_URL/metadataBase, skipping tests and third-party domains). Check the printed kit against the source - never invent brand details or swap the logo - then point the brief at it with `"brand_kit": "brand_kit.json"`. Copy for the video should come from the site's own text (hero line, services, process, CTA); read it from the content files. Respect what the site says about itself (e.g. "prices quoted after discovery" means no prices in the video).

If the user sends a reference video ("make one like this"): analyze it first - contact sheet (`ffmpeg -i ref.mp4 -vf "fps=1,scale=180:-1,tile=12x3" -frames:v 1 ref.jpg`), cut detection (`ffmpeg -i ref.mp4 -vf "select='gt(scene,0.12)',showinfo" -an -f null - 2>&1 | grep -o "pts_time:[0-9.]*"`), and a spectrogram (`showspectrumpic`) to see music vs voice and where SFX hit. Map its structure and pacing onto the scene types below (neon motion-graphics ads with ✕/✓ tags, a portfolio counter or a wall of screenshots → Formula D). Imitate structure and pacing only - never reuse another business's brand, logo, footage, screenshots, testimonials or copy in the user's video.

## 1b. Creative plan (before writing the brief)

Write a short `creative_plan.md` in the project folder (it is a working file, not a deliverable):
1. Goal (leads, bookings, awareness), audience, platform and length.
2. Two or three distinct concepts, each as a table row: concept, the hook in the first 2.5 s, strengths, weaknesses. Different concepts differ in the opening and the story arc, not just in colours.
3. Pick one and say why in two sentences (hook strength for muted viewers, clarity, what real assets exist).
4. The script and timeline: scene, time, on-screen copy - from the formulas in section 2.
Then write the brief and run `python3 $E brief.json --plan`: it prints the beat-snapped plan, writes `<out>_storyboard.md` (time, length, beats, copy, visual and transition per scene) and checks every text/graphic element against the frame edges and the platform's safe band - without rendering. Fix any layout error before previewing. Show the plan and storyboard to the user only if they want to approve copy first; never present a plan, storyboard or still frames as if they were the finished video.

## 2. Write the script

What the strongest short-form ads have in common (research, Nov 2026):
- The first 1.5-3 s decide reach. Open on the single best visual, bright and already moving, with the hook text on screen by 0.3 s. No logo intro, no black frames, no slow fade-in.
- Most people watch muted: every scene carries its message in on-screen text short enough to read at a glance.
- 15-30 s gets the best completion. One idea per shot, about 2-4 beats each, every cut on a beat.
- Sell the experience, not a listing: the view, coffee on the balcony, the bed - one feature per shot with a 1-3 word label.
- Keep text in the safe band: the Reels/TikTok interface covers roughly the top 13% and bottom 24% (ads: bottom 35%).
- End on one clear action (WhatsApp/phone), held long enough to read.
- Long holds need motion: a slow camera push, a highlight passing over cards, elements that keep floating. A frame where nothing moves for more than about 1.5 s reads as a slideshow.

### Formula A - photo-led: apartments, vacation rentals, venues, shops, restaurants, products

| # | scene | purpose | example copy | beats (~118 BPM) |
|---|---|---|---|---|
| 1 | hook, style box | best visual + promise | small "דירת נופש · קו ראשון לכנרת" (icon pin) / big "תתעוררו מול הכנרת" | 4 |
| 2 | location | where it is | place "קו ראשון לכנרת" / title "נוף פנורמי לכל הכנרת" | 5 |
| 3-7 | showcase (3-6x) | the tour, one feature each | label "סלון מרווח" (icon home) / title "מול הנוף" | 3-4 each; one 2-beat shot with no text adds rhythm |
| 8 | features | the facts that decide | 4-6 icon rows: capacity, amenities, location | 8 |
| 9 | showcase, style words | emotional close | "הנוף, השקט, והכל במקום אחד" with highlight on 1-2 words | 4 |
| 10 | cta | one action | eyebrow, headline, button, phone | 10 |

Shot order: best shot first, then where it is, then inside (living → bedrooms → kitchen → outdoor), then the facts, then the feeling, then the action. Showcase titles: 2-3 words. Use the boxed style on photos; `style: words` (white words, highlighted key words) for the emotional line over a calm shot.

### Formula B - services (problem → solution)

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

### Formula C - brand / tech motion graphics (no footage needed): software, agencies, SaaS, studios, personal brands

Theme: `{"preset": "tech", "type": "tech", "bg_style": "tech"}` or a brand kit. Start from `python3 $E --new tech`.

| # | scene | purpose | example copy (Nisan Sinai Technologies) | beats (~120 BPM) |
|---|---|---|---|---|
| 1 | kinetic | pain as a question, 3-4 deliberate lines, last one accent | העסק שלך / עדיין רץ / **על אקסל** / **ווואטסאפ?** | 4-5 |
| 2 | kinetic | the turn | small "יש דרך אחרת." / טכנולוגיה / accent "שמסדרת את העסק." | 4 |
| 3 | logo (burst) | brand + one-line tagline | name + "אתרים, חנויות ומערכות לעסקים בכל הארץ" | 6 |
| 4 | kinetic | the promise (the site's hero line) | אני בונה את / accent הטכנולוגיה / שהעסק שלך צריך. | 5 |
| 5 | cards | what you build (4-6 services, icon + 2-4 words) | kicker "WEB · CRM · ERP · AUTOMATION", title "מה אני בונה" | 9-10 |
| 6 | device | the product feeling: phone/laptop with animated UI or a REAL screenshot | label "מערכות CRM" / title "לקוחות ולידים במערכת אחת", note "*המחשה" | 6-7 |
| 7 | steps | how working together goes (3-4 steps) | "מהרעיון למערכת שעובדת." | 9-10 |
| 8 | cta | one action | eyebrow "יש לך רעיון?" / "בואו נבנה משהו מעולה" / WhatsApp / phone / site | 12-13 |

Kinetic lines are design lines: each one stays on one line and shrinks to fit (set `"wrap": true` on a line to allow wrapping), so break the copy into lines yourself, 2-3 words each. Mono kickers are for Latin labels (WEB · CRM); Hebrew kickers automatically use the heavy font. The device scene's built-in UI (dashboard, crm, flow, shop) is abstract shapes in brand colours with no numbers: label it with `note` ("*המחשה") unless it shows a real screenshot (`image`), and never put invented data, client names or results in a screenshot.

### Formula D - neon course / agency ad: portfolio, proof and offer (courses, studios, freelancers, agencies)

Built from the user's REAL work: screenshots of their own sites or apps, clips of their products, real messages from clients. Theme: the brand kit's colours, or `{"preset": "neon", "type": "tech", "bg_style": "tech"}` (dark violet with orange/purple neon) when the brand has none. Render it with `"renderer": "web"` (section 2c) whenever the web check passes; otherwise add `"fx": {"style": "premium"}` to the classic renderer.

| # | scene | purpose | example copy (Nisan Sinai Technologies) | length |
|---|---|---|---|---|
| 1 | kinetic (or counter with a REAL number) | hook: the pain as a question | העסק שלך / עדיין רץ על / accent אקסל? | 4 beats |
| 2 | contrast | ✕ what they use today, ✓ the answer; the chat bar types the request; caption2 lands with the ✓ | ✕ אקסל, ✕ וואטסאפים, ✓ מערכת אחת; prompt "אני צריך אתר עם הזמנות אונליין"; caption2 "טכנולוגיה שמסדרת את העסק." | auto, about 3.5 s |
| 3 | gallery | the portfolio at speed: one screenshot or clip per item with a counter, what was built (label) and which project (tag) | 7 items, per 0.85; laptop for desktop screenshots, phone for mobile ones | 0.45 + per × items + 0.6 |
| 4 | wall | proof: every screenshot on a tilted wall plus a title; quote cards only from real messages | "מערכות שכבר עובדות בעולם האמיתי." | 3.5 s, + 1.9 s per quote |
| 5 | bundle | what you sell: 1-3 offer/service cards joined by "+" | "אתרים וחנויות אונליין" + "מערכות CRM ו-ERP" | auto, about 3.5 s |
| 6 | kinetic | the promise | אני בונה את / accent הטכנולוגיה / שהעסק שלך צריך. | 5 beats |
| 7 | cta | logo, one action; `button_style: primary` + `button_icon: false` gives a solid pill like a course ad | "בואו נבנה משהו מעולה" | ≥ 4 s |

Real assets only: gallery and wall items are the user's own work - label demo or concept projects as such in the tag (the demo used "Shel-Yah · פרויקט הדגמה", the site's own wording); a counter shows a real number; quote cards come only from messages the user sends (screenshots or exact text) and is allowed to publish - never invent or "illustrate" a testimonial. If there are no real quotes, the wall shows the work itself. Never copy the reference ad's brand, screenshots, testimonials or copy.
Screenshots: when a browser is available, open the user's own sites, decline cookie banners (the privacy-preserving choice), scroll to the hero and to two or three key sections and take screenshots; close the tabs you opened. Remove the mouse cursor and browser-extension icons from each screenshot (`cv2.inpaint` on a small mask, or crop). Use desktop screenshots in the laptop (`device: laptop`; the label becomes a large headline under it) and tall mobile screenshots in the phone (they scroll automatically). `focus` [x, y] in an item's `src` aims the crop. Phone screenshots: if the browser window cannot be made phone-sized, load the site inside a same-origin iframe 430 px wide (scaled up for sharpness) and capture it in parts, stitched top to bottom. Pop-outs look best when the box is the real element: read its `getBoundingClientRect()` and computed `border-radius` in the browser and divide by the page width/height, so the lifted piece has exactly the card's edges and corners. On the wall set `tile_ratio` to the screenshots' height/width (0.45 for desktop screenshots, 1.9-2.2 for mobile) and `tile_w` 0.5 for wide tiles.

Copy rules: Hebrew unless asked otherwise; one idea per scene; big lines short (about 12 characters looks best - longer lines auto-shrink); small lines up to about 25 characters; digits for numbers; total 15-30 s for Formulas A, C and D, 25-40 s for Formula B; CTA at least 4 s. Multi-line text is balanced automatically (no single word left on the last line).
Honesty: never invent numbers, testimonials, client names, certifications or prices. If something is missing, drop that scene, or use an obviously marked placeholder and tell the user it must be replaced before publishing. The CTA button draws a generic chat icon (no third-party logos); naming WhatsApp in the button text is fine.
Unless the user wants to approve copy first, go straight to the preview and show the script together with the preview sheet.

### Platforms

Set `"platform"` and the engine picks the format, the safe band and the length check (QA warns outside the range). One 9:16 master usually serves Reels, TikTok and Shorts; render other formats with `formats`.

| platform | format | text safe band (top-bottom of height) | recommended length |
|---|---|---|---|
| reels (Instagram/Facebook Reels) | 9x16 | 13%-76% | 15-30 s |
| tiktok | 9x16 | 12%-74% | 15-35 s |
| shorts (YouTube) | 9x16 | 13%-76% | 15-45 s |
| stories / WhatsApp status | 9x16 | 13%-76% | 5-15 s |
| ads (paid placements) | 9x16 | 14%-65% | 6-30 s |
| feed | 4x5 | 6%-94% | 10-30 s |
| square | 1x1 | 6%-94% | 10-30 s |
| youtube / promo (brand film, explainer) | 16x9 | 6%-94% | 30-120 s |

Resolution: 1080 wide by default (1080x1920 for 9:16, 1920x1080 for 16:9). `"scale": 2` renders 4K (2160x3840 / 3840x2160) with vector-sharp text; it takes about 4 times as long, so render 4K only when it is asked for, after the 1080 version is approved.

### 2c. Motion style and renderer

Two independent choices, both optional:

| setting | what it does | when |
|---|---|---|
| no `fx` (default) | the calm v3.1 motion, pixel-identical to older versions | existing briefs, photo-led ads |
| `"fx": {"style": "premium"}` | smooth, cinematic motion: soft-blur entrances, gentle 3D card turns with a sheen, a slow camera settle, push / zoom-through / cube transitions chosen by the next scene, gallery pop-outs with real corners | brand, tech and portfolio ads; the classic fallback of the web renderer |
| `"fx": {"energy": 1-3}` (or "low" / "high" / "crazy") | hype: punches and shake on hits, live background, fast 3D transitions rotated automatically, every gallery item pops out | loud, short pieces with strong music; energy 2 for Reels, 3 only for very short loud clips |
| `"renderer": "web"` | every frame of the motion-graphics scenes drawn by Chrome with real 3D, motion blur and sharp type; the premium style is implied | Formula D and any video built only from the scene types listed below |

Hype levels: 1 - a zoom punch, camera shake and a brief colour split on every cut and impact sound; 2 - level 1 stronger, a punch on every beat, glitch bands on hits, light streaks and a ring burst on brand backgrounds, elements that slam in with a motion trail and keep bouncing to the beat, transitions rotated through cube, zoom_blur, slices, spin, shape, whip, diamond and glitch, a thump under each cut; 3 - level 2 at full strength with a white flash on hits. A calm scene can opt out with `"fx": false`. Feedback from real use: viewers read hype as amateurish when it runs for a whole ad - prefer premium (or the web renderer) for brands, and use hype only when the user asks for it.

Web renderer details:
- Draws: kinetic, title, contrast, gallery (phone or laptop, with pop-outs), wall, bundle, counter / stat / stats, logo, cta. Any other scene type, or voiceover captions, sends the whole brief to the classic renderer (premium style) with a log line saying why - mixing renderers inside one video is not supported.
- Transitions: push, push_up, zoom_through, cube, shape, diamond, fade, blur, flash, cut; the classic names map onto them (zoom, punch, spin, glitch → zoom_through; whip, slide → push; slide_up, slices → push_up; leak → fade).
- Top-level fields: `motion_blur` (samples per frame, 4; 1 with `--draft`; only moving frames take extra samples), `shutter` (0.5 of a frame).
- Same commands as the classic renderer (`--plan`, `--preview`, `--frame`, `--draft`, `--qa`), same QA, cover and music-free version. Pop-outs are kept inside the frame automatically (a too-large `scale` is reduced). It has no scene cache: every full render redraws every frame, so look at `--frame` stills first.
- Speed: about 5-6 minutes for 30 s of 1080x1920 on 2 cores (about 0.2 s per capture); `--draft` (half size, no motion blur) about 1 minute. Run it in the foreground with a long timeout.
- `python3 ~/.cache/promo-reel/promo_web.py --check` says whether Chrome can start here.

## 3. Prepare footage

- Work on copies in a project folder; keep brief.json next to the media (paths in the brief are relative to it).
- For every clip: `ffprobe` (size, duration, rotation) and a contact sheet (`ffmpeg -i c.mp4 -vf "fps=3,scale=160:-1,tile=8x3" -frames:v 1 c.jpg`) - look at it.
- Burnt-in text, subtitles, watermarks, UI overlays (common in clips taken from social media or other ads): crop them out (`-vf crop=w:h:x:y`) or skip those seconds. Check the whole clip - animated text moves through the frame.
- Casting: hook = the most colorful, high-motion clip (it fills the letters); stamps = problem footage (rendered black-and-white); one clip per service item; stats/checklist = clean, calm shots; CTA = anything (it is blurred).
- Photos get a virtual camera move (clip spec `move`): wide photos in a tall frame pan across the whole picture instead of being cropped, others push in. Vary moves between neighbouring scenes (push, pan_left, pull, pan_right, drift) and aim with `focus` [x, y]. Never leave a photo static.
- The engine handles: landscape/square clips (auto blur-fill), photos (camera moves), rotation, best-moment selection when `start` is omitted (most active window, never the same moment twice), clips shorter than their scene (they loop - prefer `"speed": 0.6` slow-mo or a shorter `dur`).
- No footage at all: use Formula C on the animated brand background (`bg_style: tech`), or scenes without a clip render on a branded grid panel. Tell the user real footage or real product screenshots convert better.
- Missing files never crash a render: a missing clip falls back to the branded background, a missing screenshot to the animated UI, a missing logo to the initials emblem, missing music to SFX only - each with a `[warn]` line. Unknown scene types and missing required fields stop the render with a clear `[error]` before anything is drawn.

## 4. Sound

Follow the video-sound-effects skill if it is available (Soundza first, then Openverse/Wikimedia). Save files in `assets/sfx/` and list them in `assets/sfx/CREDITS.md`. Use only free, licensed sources (Soundza's license allows commercial use) - never ripped commercial music.

Music: Soundza `search_sounds` with type=music, parts=full_mix, vocals=none, fit_seconds=<video length>, a mood/genre that fits the business (trap/hip-hop for construction and trades, upbeat corporate for services, modern tech/electronic for software, lo-fi for cafes, cinematic for real estate). If nothing fits, `generate_music` with model="lyria", duration about length+10 s, bpm 120-140, a plain description of business and vibe - and tell the user the music is AI-generated (catalog tracks can be AI-generated too: check `ai_content`).
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
Loop-based library tracks usually repeat their strongest section: find the onsets of its first hit (`pe.detect_beats(y)` plus a 20 ms energy scan around the jump) and join two copies of that section, so the whole video runs on the high-energy part.
Pick a track with a clear beat: 110-128 BPM for listings, products and services; 60-90 BPM only for slow luxury pieces. Ambient pads with no drums make a cut-on-beat edit feel like a slideshow - don't use them for ads. If nothing in the catalog fits, generate one: `generate_music` with model "stable", looping true, bpm 118 and a plain description (genre, drums, lead instruments, mood); "lyria" gives full tracks but sometimes fails, so fall back to "stable". Generated loops often drop energy in their second half - keep the strongest 8 bars and repeat them (bar = loop length / bars):
```python
import sys, os, wave, numpy as np
sys.path.insert(0, os.path.expanduser("~/.cache/promo-reel")); import promo_engine as pe
x = pe.load_audio("assets/sfx/loop.wav", 0, None, loop=False); sr = pe.SR
bar = len(x) / sr / 16                      # 16 = the loop's bar count from generate_music
seg = x[:int(round(8 * bar * sr))]; f = int(.006 * sr); r = np.linspace(0, 1, f)[:, None]; out = seg.copy()
for _ in range(2):
    out = np.concatenate([out[:-f], out[-f:] * (1 - r) + seg[:f] * r, seg[f:]])
with wave.open("assets/sfx/music.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
```
The engine detects tempo and snaps every scene cut to a beat (`beat_sync`, default on). Give scenes a length in beats (`"beats": 4`) instead of seconds so the edit locks to the music.

SFX: the engine fires these names automatically. Proven Soundza picks (download once with `download_sound`; `sync` = the result's sync_ms/1000; `max` trims long files):

| name | fires on | Soundza id (title) | sync | extra |
|---|---|---|---|---|
| whoosh | zoom/whip/slide_up transitions, collage, wipe, device | cmujffw8b2an6jwenoz4r1gxb (Fast Cable Whoosh) | 0.293 | |
| impact | hook, stamp slam, offer slam | cmujfj249qoihsspc4q3yzwqj (Dark Boom Impact) | 0 | |
| thump | punch/flash cuts | cmvcm7a6809ezelyj5xjojlco (Punch Impact) | 0.064 | |
| pop | checklist ticks, stars, cards, steps | cmvcmbf6rxr815bt4tf7g6xlm (Bubble Pop UI Tap) | 0.054 | |
| click | CTA tap | cmukcwidhpq87pi9kz3rtqlqf (Mouse Click Warm) | 0.005 | |
| ding | counter lands | cmvcmbkdi4e6xbwonobll8ebf (Desk Bell Ding) | 0.315 | max 1.5, gain 0.7 |
| reveal | logo | cmvcm7nb06a2l2llux8dxyn0n (Dramatic Impact Hit) | 0.325 | max 2.5 |
| glitch | glitch transition | cmvcmf2aixr9r14u2pcug3b10 (TV Glitch) | 0 | max 0.35, gain 0.8 |
| type | chat-bar typing (contrast `prompt`), every second character | synthesized by default (short tick); any short keyboard-click file works | 0 | gain 0.5 |

Formula D scenes also fire: pop (✕ tags, quote cards), thump (the ✓ tag), click (each gallery item), whoosh (gallery and wall entrances).

More options: Soundza pack `video-editing-sound-effects-whooshes-pops-clicks-glitches-and-camera-shutters`. Any SFX file that is missing falls back to a synthesized version, so a video never ships silent. When the video is published, suggest (optional) crediting soundza.com.

Voiceover and captions: there is no text-to-speech in this engine; check whether the session has a TTS tool, and if not, ask the user for a recorded voiceover (phone recording is fine) plus its exact text. Brief: `"voiceover": {"file": "assets/vo.wav", "text": "<exact words>", "at": 0.3, "volume": 1.0}`. The engine aligns the words to the recording without a speech model (phrases, split at punctuation, are matched to the stretches of speech between pauses, and words are spread by length inside each phrase - so punctuate the text where the speaker pauses), shows them as boxed captions 1-3 words at a time in the safe band, and ducks the music under the voice. Check the caption timing on `--frame` stills at a few spoken moments; if a caption runs early or late, split the text at the pause or adjust `at`. Fields: `words_per_caption` (3), `caption_chars` (18), `caption_size` (64), `caption_y` (centre as a fraction of the height; default just inside the bottom of the safe band), `captions` (true). With captions on, keep scene text at `pos` top or center - `--plan` warns about every scene whose text sits under the captions. Never guess what someone says in a recording - captions come only from text the user gave.

## 5. Brief, preview, render, QA

Write `brief.json` (reference below; starters: `python3 $E --new property|service|tech > brief.json`, then replace every `<<...>>`), then:
- `python3 $E brief.json --plan` - storyboard + layout check, no render (section 1b).
- `python3 $E brief.json --preview --draft` - contact sheet of every scene (2 frames each) at half size, a few seconds. Look at it.
- `python3 $E brief.json --frame 1.2,9,15,21,31` - full-size PNGs at those seconds; look at the busiest moments (hook, cards, device, CTA) before the full render. Check: Hebrew reads in order, no single word alone on a line, nothing touches the frame edge, text is outside the platform's UI zones.
- `python3 $E brief.json` - final MP4 + `<out>_cover.jpg`, then automatic QA. About 1 minute per 30 s of 1080x1920 on 2 cores with the classic renderer (about 2.5 minutes with hype energy 2, 5-6 minutes with the web renderer); run it in the foreground with a long timeout. The plan printed first shows each scene's start, length, transition and clip.
- Edits: change the brief and run again - only scenes whose content changed re-render (cache in `<out>_work/`, keyed by scene content, clip file contents, theme and engine version). A scene's cache also depends on the scene before it (transitions blend from its last frame). `--draft` writes separate `_draft` files. After editing the engine itself, delete `<out>_work/` so no stale scene is reused.

Automatic QA (written after every render unless `--no-qa` or `"qa": false`; run it alone with `python3 $E brief.json --qa out.mp4`): `<out>_qa.md`, `<out>_qa.json` and `<out>_qa_sheet.jpg` (1 frame per second).

| part | check (measured) | points |
|---|---|---|
| technical | file opens, h264 + aac, yuv420p | 10 |
| technical | resolution, aspect and fps match the plan | 10 |
| technical | duration matches the plan (±0.2 s) | 5 |
| technical | no unplanned black frames over 0.25 s (ffmpeg blackdetect) | 10 |
| technical | no frozen picture over 1.5 s (freezedetect) | 5 |
| technical | loudness -16 to -12 LUFS; true peak ≤ -1 dBTP (ebur128) | 6 + 4 |
| technical | no silent gap over 1 s (silencedetect) | 5 |
| technical | no text/graphic cut off at the frame edge (element bounds); elements outside the safe band are listed as warnings | 5 |
| structure | first scene is a hook type (hook, kinetic, showcase, location, contrast, counter) and ≤ 3 s; ends on a CTA held ≥ 4 s; average shot 1.2-4 s (each gallery item counts as a shot) | 5 + 5 + 5 |
| creative | hook strength, clarity/readability, pacing/rhythm, aesthetics/brand, message/CTA - 0-5 each | 25 |

The first 75 points are measured. The creative 25 are a reviewer's judgement: watch the QA sheet and the key frames, score honestly, and record it with `python3 $E brief.json --qa out.mp4 --creative 4,5,4,4,5`. The report labels it as subjective; when reporting to the user, give the measured part and the judgement separately and never present the total as objective proof of quality. Target: measured 75/75 with no errors, total 90 or more. Below that: fix the cause in the brief (copy length, line breaks, scene length, music section, layout) and re-render - only changed scenes re-render. Also look at the frames around every cut (`ffmpeg -ss <cut±0.1> -i out.mp4 -frames:v 1`) - QA does not judge whether a transition looks good.

## 6. Deliver

Send the MP4 and a preview image (8 key frames from the final file, or the cover) with SendUserFile, plus the QA report when the user asked for one. In the reply: one or two lines, a ready-to-paste post caption (Hebrew, 2-3 lines + CTA + 5-8 hashtags), and offer the cheap extras: 2-3 alternative hooks for A/B testing (`variants` - only the hook re-renders) and other formats (`formats`). Never post, upload or publish the video, or push changes to a repository, without the user's explicit approval.

## 7. Limits (say them plainly instead of faking them)

- No text-to-speech or voice cloning in the engine; voiceover only from a recording the user supplies (or a TTS tool the session actually has).
- No generative video and no stock-footage downloads: visuals are the user's footage/photos/screenshots, motion graphics and the illustrative device UI.
- No paid tools: budget 0 - no credits, subscriptions or charges. Music and SFX come from free licensed libraries (Soundza); say when a track is AI-generated.
- The illustrative UI is not a real product: label it, or use real screenshots.
- 4K is supported (`scale: 2`) but slow; render it only when asked.
- Font downloads and Soundza need network access; without it the engine uses local Hebrew fonts and synthesized SFX.

## 8. Maintenance and versioning

- The engine prints its version (`--help` header; `VERSION` in the code) and every render appends one line to `~/.cache/promo-reel/runs.jsonl` (brief, output, scenes, duration, render time, QA score, errors, warnings). `python3 $E --history` shows the last renders - use it to spot recurring problems across jobs.
- Lessons from a job go into that log or the conversation, not straight into this file. Change the skill only through a reviewed update: back up the current SKILL.md, change the engine and docs, run `--selftest` and a real render of an old brief (backward compatibility), then propose the update for the user to save. Never delete a working scene type, field or option; add new behaviour behind new fields or defaults that leave older briefs unchanged. Random choices (background drift, particles) are seeded from the scene content with a frozen salt (`SEED_SALT`), not from `VERSION`, so the same brief looks the same after an engine upgrade - check this by rendering `--frame` stills of an old brief with the previous and the new engine and comparing pixels (expect a difference of 0). The web renderer has its own version (`WEB_VERSION` in promo_web.py, printed in the plan line) and is covered by the self-test's web pass.

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

Formula A example (scenes only; top-level fields as above, plus `"theme": {"preset": "gold", "type": "bold", "grade": "bright"}`):
```json
"scenes": [
  {"type": "hook", "style": "box", "small": "דירת נופש · קו ראשון לכנרת", "icon": "pin", "big": "תתעוררו מול הכנרת",
   "clip": {"src": "clips/view.jpg", "move": "pan_right", "pan_speed": 0.16}, "beats": 4, "impact": 0},
  {"type": "location", "place": "קו ראשון לכנרת", "title": "נוף פנורמי לכל הכנרת", "clip": {"src": "clips/view2.jpg", "move": "push"}, "beats": 5},
  {"type": "showcase", "label": "סלון מרווח", "icon": "home", "title": "מול הנוף", "clip": {"src": "clips/living.jpg", "move": "pan_left"}, "beats": 4},
  {"type": "showcase", "label": "מטבח", "icon": "kitchen", "title": "מאובזר קומפלט", "clip": "clips/kitchen.jpg", "beats": 4},
  {"type": "showcase", "clip": {"src": "clips/bedroom2.jpg", "move": "pull"}, "beats": 2, "scrim": 0},
  {"type": "features", "title": "מה מחכה לכם", "clip": {"src": "clips/view3.jpg", "move": "drift"}, "beats": 8, "transition": "blur",
   "items": [{"icon": "people", "text": "מתאימה עד 10 נפשות"}, {"icon": "view", "text": "נוף פנורמי לכל הכנרת"}, {"icon": "book", "text": "אזור דתי"}]},
  {"type": "showcase", "style": "words", "title": "הנוף, השקט, והכל במקום אחד", "highlight": ["השקט", "אחד"], "pos": "center", "clip": "clips/balcony.jpg", "beats": 4},
  {"type": "cta", "clip": "clips/view.jpg", "logo": false, "eyebrow": "חופשה של שלווה ונוף", "headline": "להזמנות ופרטים", "button": "שלחו הודעה בוואטסאפ", "transition": "leak", "beats": 10}
]
```

Formula C example - the tested acceptance brief (Nisan Sinai Technologies, 29.8 s, QA 75/75):
```json
{
  "out": "nisan_sinai_reel.mp4", "platform": "reels", "format": "9x16", "brand_kit": "brand_kit.json",
  "theme": {"preset": "tech", "type": "tech", "bg_style": "tech", "grade": "bright"},
  "brand": {"website": "nisan-sinai-technologies.vercel.app", "corner_logo": true},
  "music": {"file": "assets/sfx/music_edit.wav", "volume": 0.8},
  "scenes": [
    {"type": "kinetic", "lines": ["העסק שלך", "עדיין רץ", {"text": "על אקסל", "style": "accent", "underline": false}, {"text": "ווואטסאפ?", "style": "accent"}], "beats": 5, "transition": "cut"},
    {"type": "kinetic", "lines": [{"text": "יש דרך אחרת.", "style": "small"}, "טכנולוגיה", {"text": "שמסדרת את העסק.", "style": "accent"}], "beats": 4, "transition": "punch", "start": 0, "stagger": 0.13},
    {"type": "logo", "tagline": "אתרים, חנויות ומערכות לעסקים בכל הארץ", "tagline_size": 64, "burst": true, "beats": 6},
    {"type": "kinetic", "lines": ["אני בונה את", {"text": "הטכנולוגיה", "style": "accent"}, "שהעסק שלך צריך."], "beats": 5},
    {"type": "cards", "kicker": "WEB · CRM · ERP · AUTOMATION", "kicker_size": 42, "title": "מה אני בונה", "cols": 2, "beats": 10,
     "items": [{"icon": "web", "title": "אתרים וחנויות אונליין"}, {"icon": "people", "title": "מערכות CRM"}, {"icon": "layers", "title": "מערכות ERP וניהול"},
               {"icon": "bolt", "title": "אוטומציות ואינטגרציות"}, {"icon": "code", "title": "מערכות Web בהתאמה אישית"}, {"icon": "chip", "title": "AI לעסקים"}]},
    {"type": "device", "device": "phone", "ui": "crm", "ui_title": "CRM", "label": "מערכות CRM", "icon": "people", "title": "לקוחות ולידים במערכת אחת", "note": "*המחשה", "device_scale": 0.9, "beats": 7},
    {"type": "steps", "title": "מהרעיון למערכת שעובדת.", "per": 0.55, "beats": 10,
     "items": [{"title": "מבינים את העסק", "size": 68}, {"title": "מתכננים את הפתרון", "size": 68}, {"title": "בונים ובודקים", "size": 68}, {"title": "עולים לאוויר", "size": 68}]},
    {"type": "cta", "logo": true, "eyebrow": "יש לך רעיון?", "eyebrow_size": 60, "headline": "בואו נבנה משהו מעולה", "headline_size": 104, "button": "שלחו הודעה בוואטסאפ", "beats": 13}
  ]
}
```

Formula D example - the tested acceptance brief (Nisan Sinai Technologies, real screenshots of his own sites, 27.3 s, QA 75/75; `sfx` as in the first example):
```json
{
  "out": "nst_results.mp4",
  "platform": "reels",
  "brand_kit": "brand_kit.json",
  "theme": {"preset": "tech", "type": "tech", "bg_style": "tech", "grade": "bright"},
  "brand": {"website": "nisan-sinai-technologies.vercel.app", "corner_logo": true},
  "music": {"file": "assets/sfx/music_edit.wav", "volume": 0.8},
  "scenes": [
    {"type": "kinetic", "lines": ["העסק שלך", "עדיין רץ על", {"text": "אקסל?", "style": "accent"}], "beats": 4},
    {"type": "contrast", "transition": "zoom", "items": [{"text": "אקסל", "mark": "x"}, {"text": "וואטסאפים", "mark": "x"}, {"text": "מערכת אחת", "mark": "check"}], "prompt": "אני צריך אתר עם הזמנות אונליין", "prompt_at": 0.25, "cps": 16, "caption2": "טכנולוגיה שמסדרת את העסק.", "highlight": ["שמסדרת"], "caption_size": 62},
    {"type": "gallery", "device": "laptop", "kicker": "פרויקטים נבחרים", "per": 0.85, "items": [{"src": {"src": "shots/ld_hero.jpg", "focus": [0.6, 0.5]}, "label": "אתר ומערכת הזמנות", "tag": "LD Event Design", "icon": "calendar"}, {"src": {"src": "shots/ld_form.jpg", "focus": [0.5, 0.5]}, "label": "איסוף פניות מהאתר", "tag": "LD Event Design", "icon": "people"}, {"src": {"src": "shots/ld_catalog.jpg", "focus": [0.55, 0.5]}, "label": "חבילות, פריטים וסל הזמנה", "tag": "LD Event Design", "icon": "cart"}, {"src": {"src": "shots/shelyah_hero.jpg", "focus": [0.6, 0.5]}, "label": "חנות אונליין", "tag": "Shel-Yah · פרויקט הדגמה", "icon": "cart"}, {"src": {"src": "shots/shelyah_products.jpg", "focus": [0.55, 0.5]}, "label": "קטלוג וסל קנייה", "tag": "Shel-Yah · פרויקט הדגמה", "icon": "cart"}, {"src": {"src": "shots/rsvp_hero.jpg", "focus": [0.6, 0.5]}, "label": "פלטפורמת אישורי הגעה", "tag": "מערכת אישורי הגעה", "icon": "calendar"}, {"src": {"src": "shots/rsvp_demo.jpg", "focus": [0.5, 0.5]}, "label": "דשבורד בזמן אמת", "tag": "מערכת אישורי הגעה", "icon": "chart"}]},
    {"type": "wall", "title": "מערכות שכבר עובדות בעולם האמיתי.", "title_size": 84, "title_highlight": ["עובדות"], "images": ["shots/ld_hero.jpg", "shots/ld_form.jpg", "shots/ld_items.jpg", "shots/ld_catalog.jpg", "shots/shelyah_hero.jpg", "shots/shelyah_products.jpg", "shots/rsvp_hero.jpg", "shots/rsvp_demo.jpg", "shots/nst_hero.jpg", "shots/nst_services.jpg"], "tile_w": 0.5, "tile_ratio": 0.4525, "cols": 4, "rows": 9, "wall_dim": 0.7, "dur": 3.6},
    {"type": "bundle", "title": "מה אני בונה", "items": [{"title": "אתרים וחנויות אונליין", "text": "אתרי תדמית, דפי נחיתה וחנויות מהירות", "image": "shots/shelyah_hero.jpg", "tags": ["UX/UI", "E-commerce", "SEO"]}, {"title": "מערכות CRM ו-ERP", "text": "לקוחות, לידים, הזמנות ותפעול במערכת אחת", "image": "shots/rsvp_demo.jpg", "tags": ["Leads", "Operations", "Reports"]}]},
    {"type": "kinetic", "lines": ["אני בונה את", {"text": "הטכנולוגיה", "style": "accent"}, "שהעסק שלך צריך."], "beats": 5},
    {"type": "cta", "logo": true, "eyebrow": "יש לך רעיון?", "eyebrow_size": 60, "headline": "בואו נבנה משהו מעולה", "headline_size": 100, "button": "שלחו הודעה בוואטסאפ", "beats": 11}
  ]
}
```

Top-level fields:
- `out` (default promo.mp4); `format`: 9x16 | 1x1 | 4x5 | 16x9; `formats`: list - renders each (suffix _<fmt>); `fps` (30); `platform` (section 2, Platforms) sets the default format, safe band and length check; `scale` (1; 2 = 4K).
- `safe`: reels (default; text between 13% and 76% of the height) | tiktok | ads (bottom 35% kept clear, for paid placements) | full.
- `theme`: `grade` bright (default) | warm | cool | punchy | natural - colour grade for all footage; `preset` gold | fire | electric | fresh | royal | clean (light) | tech (dark, cyan/violet) | neon (dark violet, orange/purple neon) | auto (colors from the logo); color overrides `primary, primary2, hi, accent, bg, text, muted, cta` (hex); `type` (typeset) bold | classic | condensed | elegant | playful | retro | tech (Noto Sans Hebrew + Geist Mono labels); `font_display/font_heavy/font_body/font_stamp/font_mono` = a .ttf path or a font key; `bg_style` grid (default, static branded grid) | tech (animated glows, drifting particles, grid fading at the edges); `drift` = slow camera push per scene (0.035 with bg_style tech, 0 with grid; a scene can set its own `drift`, 0 = off).
- `brand`: `name, tagline, initials, logo, phone, website, corner_logo` (small logo top-left on footage scenes and on the animated background), `logo_bg` auto (default: removes the flat square background of an opaque logo) | keep.
- `brand_kit`: path to a kit from `--brand-from`; its theme and brand fields are defaults the brief can override.
- `clips`: pool of clips (paths or specs) and/or `clips_dir`: auto-assigned to scenes that have no `clip` key (set `"clip": null` to force the panel).
- `music`: `file, start, volume (0.8), beat_sync (true)`. `voiceover`: `file, at, volume, text, captions (true), words_per_caption, caption_chars, caption_size, caption_y` - music ducks under it; `text` turns on captions (section 4).
- `sfx`: true | false | {name: path or {file, sync, max, gain}}; `sfx_volume` (0.55).
- `variants`: [{name, scenes: {"<index in scenes>": {overrides}}}] - extra outputs `<out>_<name>.mp4` sharing the cache.
- `renderer`: classic (default) | web - which renderer draws the frames (section 2c); `motion_blur` (4), `shutter` (0.5) for the web renderer.
- `fx`: {"style": "premium"} | {"energy": 0-3} | "premium" | "low" | "high" | "crazy" - motion style (section 2c); a scene can set `"fx": false` to stay calm.
- `qa` (true): run QA after rendering; `cover_scene` (0): which scene the cover image is taken from; `music_free_version` (false): also write `<out>_no_music.mp4`.

Clip spec: `"path"` or `{src, start, speed, fit: auto|cover|blur, focus: [x, y], move, amount, pan_speed, look: {bw, dim, blur, grade, vignette, bright, contrast, sat, warm}}`. Photo `move`: auto (default) | push | pull | pan_left | pan_right | pan_up | pan_down | drift | still; `amount` = push/pull zoom (0.13); `pan_speed` = frame widths per second (0.2).
Every scene accepts: `dur` or `beats` (length in music beats; needs music), `transition, clip, look, zoom, audio` (true = keep the clip's own sound, music ducks), `audio_volume`, `drift` and `corner_logo` (false hides it on that scene). `services` also takes `beats_per`.

| type | fields | default dur | default transition in |
|---|---|---|---|
| hook | small, big, clip, style box\|video\|plain, icon (box), impact (sfx gain), backdrop blur\|black, size | 2.2 | cut |
| showcase | clip, label, icon, title, sub, style box\|words, pos bottom\|top\|center, size, highlight (words), anim, scrim (0 = none), box_color | 2.0 | slide |
| location | clip, place, title, pos, size | 2.6 | zoom |
| features | items [{icon, text}] (up to 6), title, clip, dim (0.82), size, pos | 0.6 + 0.32 per item + 1.5 | zoom |
| kinetic | lines [str or {text, style big\|accent\|small\|mono\|box, size, underline (accent lines), wrap}], kicker, kicker_size (38), pos center\|top\|bottom, start (0.06), stagger (0.16), underline (true), clip | 2.2 | blur |
| cards | items [{icon, title, text}] (4-6), kicker, kicker_size (40), title, title_size (96), cols (2), card_ratio (0.9), highlight (true), highlight_step (0.32), rtl, clip | 0.8 + 0.12 per card + 1.8 | zoom |
| steps | items [{title, text, size (60)}] (3-5), title, title_size (96), per (0.55 s between steps), clip | 0.6 + per × items + 1.4 | slide_up |
| device | device phone\|laptop, ui dashboard\|crm\|flow\|shop, ui_title, image (real screenshot), label, icon, title, style box\|plain, size, tilt (-12), device_scale (1), note, note_size (30), clip | 3.0 | zoom |
| stamp | line, stamp, clip, bw (true) | 1.9 | glitch |
| logo | clip, name, tagline (default: brand), tagline_size (56), burst (on with bg_style tech) | 2.5 | zoom |
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
| cta | eyebrow, eyebrow_size (46), headline, headline_size (92), button (text or false), button_style cta\|primary (cta = the theme's cta colour), button_icon (true = chat icon; false = centered text pill), phone, website, qr (url), logo (true), tap_at, clip | 5.0 | zoom |
| contrast | items [{text, mark x\|check, size (76 ✕ / 90 ✓)}], per (0.55), start (0.15), prompt (chat bar that types it), prompt_at, cps (14 characters/s), caption (shown until the ✓), caption2 (from the ✓; alone it appears with the ✓), highlight (words), caption_size (46), clip | start + per × items + 1.4, longer with a prompt | blur |
| gallery | items [{src (image or clip spec), label, tag, icon, highlight}], per (0.7), kicker, device phone\|laptop, device_scale (1), swing (9), label_style pill\|headline (headline: laptop in portrait), label_size (72), pop true\|alternate\|false (item `pop`: true\|false\|{box [x0, y0, x1, y1] as fractions of the screenshot, radius (fraction of its width), scale (1.35 premium / 1.8 hype), at}), clip | 0.45 + per × items + 0.6 | zoom |
| wall | images, cols (6), rows (5), tile_w (0.27 of width), tile_ratio (tile height/width, 1.9), wall_dim (0.6), wall_ry (-14), wall_rx (32), title, title_size (96), title_highlight (default: numbers), sub, quotes [{text, highlight, who, label, size}], quote_label, quotes_at (0.9), per_quote (1.9) | max(3, quotes_at + per_quote × quotes + 0.6) | blur |
| bundle | items [{title, text, image, tags [text or {text, icon}], size (66)}] (up to 3), title, title_size (90), clip | 0.2 + 0.55 × items + 2.2 | slide_up |

Transitions: cut, flash, punch, fade, zoom, whip, slide, slide_up, glitch, blur, leak (warm light leak), push (the next scene pushes the last one out), zoom_through (the camera flies through the last scene into the next), cube (3D cube turn), spin (rotating whip with motion blur), zoom_blur (radial zoom through a flash), slices (strips sliding in from alternate sides), shape (circle opening with a ring in the theme colour), diamond (the same with a diamond). Text animations: up, down, fade, pop, zoom, slam, wipe, left, right, none.
Icons (label, place, features, cards): pin, people, bed, view, waves, pool, star, sparkle, check, home, snow (air conditioning), wifi, parking, sun, heart, calendar, chat, phone, key, book, kitchen, coffee, clock, web, cart, layers, bolt, gear, code, chip, chart, rocket, search, lock. An unknown icon falls back to check (with a warning).
Outputs: `<out>.mp4`, `<out>_cover.jpg`, `<out>_qa.md/.json`, `<out>_qa_sheet.jpg`, `<out>_storyboard.md` (`--plan`), `<out>_preview.jpg`, `<out>_frame_<t>.png`, `<out>_work/` (cache + plan.json with final timings).

Command line: `python3 $E [brief.json] [--out FILE] [--format F] [--draft] [--preview] [--frame T,T] [--plan] [--qa VIDEO] [--creative h,c,p,a,m] [--no-qa] [--variant NAME] [--workers N] | --new property|service|tech | --brand-from DIR [--kit FILE] | --selftest | --history`.

## Troubleshooting

- Hebrew letters in reverse order: raqm is missing - install python-bidi.
- A clip shows old captions/watermarks: crop the clip; look at the whole clip, not one frame.
- Visible loop jump: the clip is shorter than its scene - add `speed` < 1 or shorten `dur`.
- A scene lands too long/short after beat snapping: set its `dur` explicitly, or `"beat_sync": false`.
- Text too long: it auto-shrinks; shorten the copy instead for impact.
- Feels like a slideshow: use music with a clear beat, lengths in `beats`, and a different photo `move` on each neighbouring scene; on motion-graphics videos keep `drift` on and the card `highlight` on.
- Text hard to read on a bright photo: use the boxed style (default in showcase/hook box) or raise `scrim`; don't dim the whole frame.
- Music has a gap under the CTA: re-splice (section 4) or change `music.start`.
- A kinetic line came out small: it is one long line shrunk to fit - split it into two lines in the brief.
- An empty moment right after a cut: set the next kinetic scene's `start` to 0 and a shorter `stagger`.
- `[error] scene N: unknown type`: fix the type name (the error lists the valid ones); `[warn]` lines name the file that was replaced by a fallback.
- QA "element outside the safe band": move it with the scene's `pos`, shorten the copy, or accept it for non-text graphics (the warning is informational).
- A gallery screenshot is cut badly: aim it with `focus` in the item's `src` spec, or use the phone for tall screenshots and the laptop for wide ones.
- The wall shows its edges or tiles look stretched: set `tile_ratio` to the screenshots' real height/width and add `rows`; the wall is scaled to cover the frame.
- The typing bar finishes too late: raise `cps` or shorten the `prompt` (the scene grows to fit it).
- `[web] ... rendering with the classic renderer`: the web renderer could not run (Playwright or Chrome missing, or an unsupported scene type) - the line says which; fix it (setup step 4) or accept the premium-style classic render and tell the user.
- A pop-out lifts the wrong part of a screenshot: set the item's `pop` to {"box": [x0, y0, x1, y1], "radius": r} from the real element (Formula D), or `false`.
- Hype motion feels too busy or cheap: switch to `"fx": {"style": "premium"}` or the web renderer; or lower the energy and set `"fx": false` on calm scenes.
- Web renderer text wraps oddly around a hyphen: hyphens between words are made non-breaking automatically; for other breaks, split the line in the brief.
- A logo shows a square box behind it: it is opaque with a non-uniform background; supply a transparent PNG (`logo_bg: keep` turns off the automatic corner removal).

## Engine

<!-- ENGINE:BEGIN -->
```python
#!/usr/bin/env python3
"""promo_engine.py - branded short-form promo videos (Hebrew/RTL first) from a JSON brief.
Usage:
  python3 promo_engine.py brief.json [--out out.mp4] [--format 9x16|1x1|4x5|16x9]
                          [--preview] [--frame SECONDS] [--draft] [--workers N]
Needs: python3, numpy, Pillow (with raqm for RTL; else pip install python-bidi), ffmpeg.
"""
import argparse, glob, hashlib, json, math, os, re, shutil, subprocess, sys, wave
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

VERSION = "4.0.0"
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
                out.append(s)
        elif t == "stats":
            for j, it in enumerate(sc.get("items", [])):
                s = {"type": "counter", **it}
                s.setdefault("transition", "slide_up")
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
    mus = brief.get("music") or {}
    beats = np.array([])
    if mus.get("file") and mus.get("beat_sync", True) and os.path.exists(mus["file"]):
        y = load_audio(mus["file"], float(mus.get("start", 0)), sum(durs) * 1.5 + 5).mean(1)
        beats, bpm = detect_beats(y)
        log(f"[music] ~{bpm:.0f} BPM, {len(beats)} beats")
        if len(beats) and bpm:
            for i, sc in enumerate(scenes):
                if sc.get("beats"):
                    durs[i] = float(sc["beats"]) * 60.0 / bpm
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

def build_captions(brief):
    """Captions for a recorded voiceover: voiceover {file, text, at, captions: true}. Returns [{text, s, e}] in video time."""
    vo = brief.get("voiceover") or {}
    if not (vo.get("text") and vo.get("file") and os.path.exists(vo["file"]) and vo.get("captions", True)):
        return []
    y = load_audio(vo["file"], 0, None, loop=False)
    at = float(vo.get("at", 0))
    words = [(w, a + at, b + at) for w, a, b in align_text(vo["text"], y)]
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
    return out


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
    bw.pop("voiceover", None)
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
    ctx.captions = build_captions(brief)
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
    ctx.captions = build_captions(brief)
    stem = os.path.splitext(video)[0]
    scenes = make_plan(brief, ctx, stem + "_work" if os.path.isdir(stem + "_work") else os.path.dirname(os.path.abspath(video)))
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
```
<!-- ENGINE:END -->

## Web renderer

<!-- WEB:BEGIN -->
```python
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

WEB_VERSION = "4.0.0"
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
    return _html.escape(re.sub(r"(?<=[^\W\d_])-(?=\S)|(?<=\S)-(?=[^\W\d_])", "\u2011", str(s)), quote=True)


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
    corner = ""
    if ctx.brand.get("corner_logo"):
        url, _ = _logo_url(P_)
        corner = f'<img id="cornerlogo" src="{url}">'
    page = f"""<!doctype html><html dir="rtl" lang="he"><head><meta charset="utf-8"><style>{css}</style></head><body>
<div id="stage">{bg_html}<div id="scenes">{"".join(layers)}</div>{corner}<div id="ring"></div><div class="vig"></div><div class="grain"></div>
<div id="flash"></div></div>
<script>window.__U = {P_.U:.5f}; window.__W = {P_.W}; window.__H = {P_.H};
{RUNTIME}
{bg_js}
window.__scenes = [{",".join(defs)}];
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
    if bad or brief.get("voiceover", {}).get("captions"):
        why = f"scene types {', '.join(bad)}" if bad else "voiceover captions"
        return classic(brief_path, out, fmt, draft, workers, preview, frame_at, workdir, creative, do_qa, plan,
                       f"the web renderer does not support {why} yet")
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
    scenes = pe.make_plan(brief, ctx, workdir)
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
```
<!-- WEB:END -->