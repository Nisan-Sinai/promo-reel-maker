#!/usr/bin/env python3
"""Build the installable skill from its sources.

src/SKILL.template.md + src/promo_engine.py  ->  skill/promo-reel-maker/SKILL.md
and dist/promo-reel-maker.zip (ready to upload as a Claude skill).

The engine is embedded inside SKILL.md, so the skill is a single self-contained file.
The build checks that the engine extracted back out of SKILL.md is byte-identical to the source.
"""
import pathlib
import py_compile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "src" / "SKILL.template.md"
ENGINE = ROOT / "src" / "promo_engine.py"
OUT = ROOT / "skill" / "promo-reel-maker" / "SKILL.md"
DIST = ROOT / "dist" / "promo-reel-maker.zip"


def extract(md: str) -> str:
    """Same extraction the skill performs at runtime (see SKILL.md, section 0)."""
    code = md.rsplit("<!-- ENGINE:" + "BEGIN -->", 1)[1].rsplit("<!-- ENGINE:" + "END -->", 1)[0]
    return code.split("```python\n", 1)[1].rsplit("```", 1)[0]


def main():
    py_compile.compile(str(ENGINE), doraise=True)
    tpl = TEMPLATE.read_text(encoding="utf-8")
    eng = ENGINE.read_text(encoding="utf-8")
    if not eng.endswith("\n"):
        eng += "\n"
    assert tpl.count("{{ENGINE}}") == 1, "template must contain exactly one {{ENGINE}} placeholder"
    md = tpl.replace("{{ENGINE}}", eng)
    assert extract(md) == eng, "engine round-trip mismatch"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(md, encoding="utf-8")
    DIST.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DIST, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(OUT, "promo-reel-maker/SKILL.md")
    print(f"built {OUT.relative_to(ROOT)} ({len(md):,} chars) and {DIST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
