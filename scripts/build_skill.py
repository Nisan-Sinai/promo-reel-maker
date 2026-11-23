#!/usr/bin/env python3
"""Build the installable skill from its sources.

src/SKILL.template.md + src/promo_engine.py + src/promo_web.py  ->  skill/promo-reel-maker/SKILL.md
and dist/promo-reel-maker.zip (ready to upload as a Claude skill).

The engine and the web renderer are embedded inside SKILL.md, so the skill is a single self-contained file.
The build checks that the code extracted back out of SKILL.md is byte-identical to the sources.
"""
import pathlib
import unicodedata
import py_compile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "src" / "SKILL.template.md"
ENGINE = ROOT / "src" / "promo_engine.py"
WEB = ROOT / "src" / "promo_web.py"
OUT = ROOT / "skill" / "promo-reel-maker" / "SKILL.md"
DIST = ROOT / "dist" / "promo-reel-maker.zip"


def extract(md: str, tag: str = "ENGINE") -> str:
    """Same extraction the skill performs at runtime (see SKILL.md, section 0)."""
    code = md.rsplit("<!-- " + tag + ":" + "BEGIN -->", 1)[1].rsplit("<!-- " + tag + ":" + "END -->", 1)[0]
    return code.split("```python\n", 1)[1].rsplit("```", 1)[0]


def main():
    tpl = TEMPLATE.read_text(encoding="utf-8")
    md = tpl
    for tag, path in (("ENGINE", ENGINE), ("WEB", WEB)):
        py_compile.compile(str(path), doraise=True)
        code = path.read_text(encoding="utf-8")
        if not code.endswith("\n"):
            code += "\n"
        assert "```" not in code, f"{path.name} must not contain a code fence"
        assert tpl.count("{{" + tag + "}}") == 1, f"template must contain exactly one {{{{{tag}}}}} placeholder"
        md = md.replace("{{" + tag + "}}", code)
    for tag, path in (("ENGINE", ENGINE), ("WEB", WEB)):
        code = path.read_text(encoding="utf-8")
        assert extract(md, tag) == (code if code.endswith("\n") else code + "\n"), f"{tag} round-trip mismatch"
    # Invisible or unassigned characters get dropped when the skill is copied through other tools,
    # which silently changes the code (this broke is_rtl once). Keep the built file free of them.
    bad = sorted({f"U+{ord(ch):04X}" for ch in md if unicodedata.category(ch) in ("Cf", "Cn", "Co")})
    assert not bad, f"invisible/unassigned characters in SKILL.md: {bad}"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(md, encoding="utf-8")
    DIST.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DIST, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(OUT, "promo-reel-maker/SKILL.md")
    print(f"built {OUT.relative_to(ROOT)} ({len(md):,} chars) and {DIST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
