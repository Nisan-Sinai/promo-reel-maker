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

Version 4.1 adds generated narration: write a line for a scene (`"say"`) and the engine voices the whole script with ElevenLabs or Google's Gemini text-to-speech (both have free tiers), places each line on its scene, makes the scene long enough for it, ducks the music under the voice and shows word-by-word captions - in both renderers. A recorded voiceover still works as before.

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
5. Narration (needed only for generated narration, section 4b): an API key for the engine the brief uses. ElevenLabs: elevenlabs.io > Developers > API keys (a free account; a restricted key with Text to Speech access and Voices read is enough), read from `ELEVENLABS_API_KEY` or `~/.config/promo-reel/elevenlabs_key`. Gemini: aistudio.google.com > Get API key (free, no credit card), read from `GEMINI_API_KEY` or `~/.config/promo-reel/gemini_key`. When the user gives a key in the conversation, or asks Claude to create one in their signed-in browser, write it to that file (`mkdir -p ~/.config/promo-reel && chmod 700 ~/.config/promo-reel`, then the file with mode 600) and never put it in a brief, a log, a commit, memory or a reply. The workspace must be allowed to reach `api.elevenlabs.io` / `generativelanguage.googleapis.com`; if the engine reports that the network blocks it, ask the user to add the domain under claude.ai/settings/capabilities > Create and edit files > Allowed websites > Manage - Claude does not change network settings itself.
6. Optional (about 1-2 minutes): `python3 $E --selftest` renders every scene type from synthetic media at draft size three times - as is, with `fx` energy 3 (every transition, camera hits, pop-outs), and with the web renderer (skipped, with the reason, when Chrome is not available) - and runs QA on each. The web pass also voices three scene lines with an offline stand-in voice (no key needed) to check narration timing and captions. It must print `fx pass: ok`, `web pass: ok` (or `skipped`) and `SELFTEST PASS` (the short test CTA is expected to miss the 4 s rule). Run it after any change to the engine.

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
- Draws: kinetic, title, contrast, gallery (phone or laptop, with pop-outs), wall, bundle, counter / stat / stats, logo, cta, plus narration and voiceover captions (word by word, the spoken word in the theme colour). Any other scene type sends the whole brief to the classic renderer (premium style) with a log line saying why - mixing renderers inside one video is not supported.
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

Voiceover and captions from a recording: when the user has a recorded voiceover (a phone recording is fine), ask for it plus its exact text; for a generated voice see section 4b. Brief: `"voiceover": {"file": "assets/vo.wav", "text": "<exact words>", "at": 0.3, "volume": 1.0}`. The engine aligns the words to the recording without a speech model (phrases, split at punctuation, are matched to the stretches of speech between pauses, and words are spread by length inside each phrase - so punctuate the text where the speaker pauses), shows them as boxed captions 1-3 words at a time in the safe band, and ducks the music under the voice. Check the caption timing on `--frame` stills at a few spoken moments; if a caption runs early or late, split the text at the pause or adjust `at`. Fields: `words_per_caption` (3), `caption_chars` (18), `caption_size` (64), `caption_y` (centre as a fraction of the height; default just inside the bottom of the safe band), `captions` (true). With captions on, keep scene text at `pos` top or center - `--plan` warns about every scene whose text sits under the captions. Never guess what someone says in a recording - captions come only from text the user gave.

## 4b. Narration (generated voice)

For a narrated ad, write one short spoken line per scene in the scene's `say` field (Hebrew unless asked otherwise). The engine sends the whole script to the text-to-speech engine in one take, so the voice and energy stay consistent, cuts it at the pauses between lines and puts each line on its scene `lead` seconds after the cut (0.15 s; 0.3 s on the first scene; per scene `say_at`). A scene that is shorter than its line plus `tail` (0.35 s) is lengthened, then snapped to the beat as usual - so the narration sets the pace. Captions follow each line word by word unless `voiceover.captions` is false. The take is cached (`~/.cache/promo-reel/tts/`) by script, voice and style, so re-renders, drafts and frame stills do not spend the free quota; changing one line regenerates the take.

```json
"voiceover": {"tts": {"engine": "elevenlabs", "voice": "nPczCjzI2devNBz1zQrb"}, "duck": 0.7, "caption_size": 60},
"scenes": [
  {"type": "kinetic", "lines": ["העסק שלך", "עדיין רץ על", {"text": "אקסל?", "style": "accent"}], "say": "העסק שלך עדיין רץ על אקסל?"},
  {"type": "contrast", "items": [...], "say": "במקום אקסל ועשרות וואטסאפים - מערכת אחת שמסדרת הכול."},
  {"type": "cta", "headline": "בואו נבנה משהו מעולה", "say": "שלחו הודעה, ובואו נבנה משהו מעולה."}
]
```

Writing lines that sound right:
- One idea per line, about 2-3 seconds of speech (6-12 words); the on-screen text and the spoken line should say the same thing in different words, not compete. Leave some scenes silent - a gallery or a wall can run under music alone.
- Write numbers, phone numbers and English names the way they should be spoken when it matters ("שלושת אלפים שקל", "אפס חמש שמונה..."); add niqqud only to a word that is read wrong.
- Engines: `"engine": "elevenlabs"` (model `eleven_v4`, then `eleven_v3`; `voice` is a voice id or the start of a voice name from the account's voice list) or `"engine": "gemini"` (default; model `gemini-3.1-flash-tts-preview`, then `gemini-2.5-flash-preview-tts`; `voice` one of 30 prebuilt voices: Puck upbeat (default), Fenrir excitable, Charon informative, Orus / Kore / Alnilam firm, Zephyr / Autonoe bright, Aoede breezy, Sulafat warm, Achird friendly, Algieba / Despina smooth, Gacrux mature). ElevenLabs premade voices that worked from this workspace on the free plan: Brian `nPczCjzI2devNBz1zQrb` (deep), Liam `TX3LPaxmHKxFdv7VOQHJ` (energetic), Jessica `cgSgspJ2msm6clMCkdW9` (bright female) - they are English voices speaking Hebrew; native Hebrew voices from the ElevenLabs library need a paid plan for API use (HTTP 402).
- Choosing a voice: Claude cannot hear audio, so let the user choose by ear - voice the same line with 3-8 candidates and send one short video with a numbered card per voice; use the chosen voice for the video and remember it as the user's default only if they say so.
- `style` (Gemini only) is a plain-English direction for the whole take (energy, warmth, pace, accent); `rate` (0.85-1.2) speeds the finished take without changing pitch, for both engines.
- A continuous script instead of scene lines: `voiceover.text` plus `voiceover.tts` (no `file`) - one take placed at `at`, captions aligned as for a recording.

Free tiers: both engines' free tiers have monthly or daily limits, the takes are cached so re-renders cost nothing, and a free tier's terms can change - when one runs out or refuses (HTTP 401/402/429), say so and offer the other engine. On free tiers the provider may use the text to improve its products, so never put personal or confidential details in a script. Tell the user the narration is an AI-generated voice; never imitate a real person's voice or present the narration as a real person speaking.

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

- Generated narration only through Gemini text-to-speech (prebuilt voices, the user's free API key, section 4b); no voice cloning and no imitation of real people. Without a key or network access to Google, narration needs a recording from the user.
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
- `music`: `file, start, volume (0.8), beat_sync (true)`. `voiceover`: `file, at, volume, text, captions (true), words_per_caption, caption_chars, caption_size, caption_y, duck (0.7 = how far the music dips under the voice), tts {engine (gemini) | elevenlabs, voice (Puck for Gemini), style, rate (1.0), model (auto), key_file, per_line}, lead (0.15), tail (0.35)` - music ducks under it; `text` turns on captions (section 4); `tts` generates the voice (section 4b). Scene fields `say` (the scene's spoken line) and `say_at` (seconds after the cut).
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
- `[error] narration: no ... API key`: setup step 5. `narration: the network blocks <host>`: the user adds the domain to the allowed websites. `HTTP 429` / rate limit: the free quota is used up - wait, switch engine, or render without `say` lines. `HTTP 401/403` with an API-key message: the key is wrong, revoked, or lacks Text to Speech / Voices access. `HTTP 402 ... library voices`: pick a premade voice or the other engine. `turned off free-tier use from this network`: ElevenLabs treated the workspace proxy as a VPN - use Gemini.
- A narrated line is cut in the wrong place or captions drift: add a full stop at the end of every `say` line; set `"tts": {"per_line": true}` to voice each line separately (more requests).
- Narration captions cover scene text at the bottom (a `contrast` caption, a gallery tag): move them with `voiceover.caption_y` (0.2 = near the top) or drop the scene's own caption - the narration already says it.
- `[web] ... rendering with the classic renderer`: the web renderer could not run (Playwright or Chrome missing, or an unsupported scene type) - the line says which; fix it (setup step 4) or accept the premium-style classic render and tell the user.
- A pop-out lifts the wrong part of a screenshot: set the item's `pop` to {"box": [x0, y0, x1, y1], "radius": r} from the real element (Formula D), or `false`.
- Hype motion feels too busy or cheap: switch to `"fx": {"style": "premium"}` or the web renderer; or lower the energy and set `"fx": false` on calm scenes.
- Web renderer text wraps oddly around a hyphen: hyphens between words are made non-breaking automatically; for other breaks, split the line in the brief.
- A logo shows a square box behind it: it is opaque with a non-uniform background; supply a transparent PNG (`logo_bg: keep` turns off the automatic corner removal).

## Engine

<!-- ENGINE:BEGIN -->
```python
{{ENGINE}}```
<!-- ENGINE:END -->

## Web renderer

<!-- WEB:BEGIN -->
```python
{{WEB}}```
<!-- WEB:END -->