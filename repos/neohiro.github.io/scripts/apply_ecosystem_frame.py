#!/usr/bin/env python3
"""Apply the Ecosystem Network frame changes to a neohiro checkout.

Operates on the three files that differ from the template-shared source of
truth, and removes the two superseded copies of the frame that are already in
the repository:

  1. _layouts/default.html          - link the stylesheet, pass current="neohiro"
  2. _includes/footer-button-row.html - drop the inlined duplicate of the frame
  3. assets/css/main.css            - drop the 25 superseded .ecosystem-* rules

Run from the site root:

    python scripts/apply_ecosystem_frame.py [--check]

--check reports what would change and exits 1 if anything is left to do, without
writing, so it can be used as a gate.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CSS_LINK = """  <link rel="stylesheet" href="{{ '/assets/css/ecosystem-network.css' | relative_url }}">"""
INCLUDE_OLD = '{% include footer-button-row.html org="neohiro" %}{% include ecosystem-network.html %}'
INCLUDE_NEW = '{% include footer-button-row.html org="neohiro" %}{% include ecosystem-network.html current="neohiro" %}'

DEDUP_NOTE = """  {# The Ecosystem Network grid lives in ecosystem-network.html and is included once
     by _layouts/default.html directly after this file. It used to be inlined
     here as well, so every page rendered the frame twice. #}
"""

problems: list[str] = []
changed: list[str] = []


def read(rel: str) -> str:
    # newline="" disables universal-newline translation. Without it Python turns
    # the file's CRLF into LF on the way in and the whole file shows up in the
    # diff as rewritten, when the only real change is the removed block.
    # These files are stored with CRLF despite .gitattributes saying eol=lf, so
    # this matters here.
    return (ROOT / rel).read_text(encoding="utf-8", newline="")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8", newline="")


def newline_of(text: str) -> str:
    """The line ending this file already uses, so inserted lines match."""
    return "\r\n" if "\r\n" in text else "\n"


def step_layout(text: str) -> str:
    if CSS_LINK in text:
        return text
    if INCLUDE_NEW in text:
        problems.append("_layouts/default.html: stylesheet link not found")
        return text
    anchor = "  <link rel=\"stylesheet\" href=\"{{ '/assets/css/auth-bar.css' | relative_url }}\">"
    if anchor not in text:
        problems.append("_layouts/default.html: no auth-bar.css link to anchor after")
        return text
    nl = newline_of(text)
    text = text.replace(anchor, anchor + nl + CSS_LINK, 1)
    changed.append("_layouts/default.html: added stylesheet link")
    return text


def step_include_current(text: str) -> str:
    if INCLUDE_NEW in text:
        return text
    if INCLUDE_OLD not in text:
        problems.append("_layouts/default.html: expected include line not found")
        return text
    changed.append('_layouts/default.html: passes current="neohiro"')
    return text.replace(INCLUDE_OLD, INCLUDE_NEW, 1)


def strip_filler(html: str) -> str:
    """Drop the inlined copy of the frame from footer-button-row.html.

    Bounded by its own comment markers so the edit cannot run past the frame
    into the quick-links columns that follow it.
    """
    start = html.find("  <!-- Ecosystem Network -->")
    if start == -1:
        return html
    end = html.find("  <!-- Quick Links")
    if end == -1 or end < start:
        problems.append(
            "footer-button-row.html: found the frame but not the marker that "
            "ends it; refusing to guess where to cut"
        )
        return html
    removed = html[start:end]
    opens = removed.count("<div")
    closes = removed.count("</div>")
    if opens != closes:
        problems.append(
            f"footer-button-row.html: the region has {opens} <div> and "
            f"{closes} </div>; refusing to cut an unbalanced region"
        )
        return html
    changed.append(
        f"footer-button-row.html: removed the inlined duplicate frame "
        f"({opens} divs)"
    )
    nl = newline_of(html)
    return html[:start] + DEDUP_NOTE.replace("\n", nl) + nl + html[end:]


def strip_css(css: str) -> str:
    """Drop the .footer-ecosystem* / .ecosystem-* rules now in ecosystem-network.css.

    Removes from the first .footer-ecosystem rule up to .footer-columns, which
    is the block's original extent. Refuses if the CSS in that range belongs to
    anything other than the frame.
    """
    lines = css.split("\n")
    starts = [i for i, l in enumerate(lines) if l.strip() == ".footer-ecosystem {"]
    ends = [i for i, l in enumerate(lines) if l.strip() == ".footer-columns {"]

    # The frame's rules live in ecosystem-network.css now, so their absence here
    # is the finished state, not a problem to refuse over. .footer-columns is
    # unrelated footer furniture and stays either way.
    if not starts:
        return css
    if len(starts) != 1 or len(ends) != 1:
        problems.append(
            f"main.css: expected exactly one .footer-ecosystem and one "
            f".footer-columns rule, found {len(starts)} and {len(ends)}"
        )
        return css
    start, end = starts[0], ends[0]
    if start >= end:
        problems.append("main.css: .footer-columns appears before .footer-ecosystem")
        return css

    stray = [
        l for l in lines[start:end]
        if l.strip() and not l.startswith((" ", "}", "/*", "*", "@", "."))
    ]
    if stray:
        problems.append(f"main.css: unexpected content in the frame block: {stray[:3]}")
        return css
    if "ecosystem" not in "\n".join(lines[start:end]):
        problems.append("main.css: the region to remove has no .ecosystem-* rules")
        return css

    changed.append(f"main.css: removed {end - start} superseded .ecosystem-* lines")
    return "\n".join(lines[:start] + lines[end:])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, do not write")
    args = ap.parse_args()

    if not (ROOT / "assets/css/ecosystem-network.css").is_file():
        problems.append("assets/css/ecosystem-network.css is missing; copy it from template-shared first")

    layout = step_include_current(step_layout(read("_layouts/default.html")))
    row = strip_filler(read("_includes/footer-button-row.html"))
    css = strip_css(read("assets/css/main.css"))

    if problems:
        print("ecosystem frame: refusing to finish", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    if not changed:
        print("ecosystem frame: already applied, nothing to do")
        return 0

    for c in changed:
        print(f"  {c}")
    if args.check:
        print(f"ecosystem frame: {len(changed)} change(s) pending")
        return 1

    write("_layouts/default.html", layout)
    write("_includes/footer-button-row.html", row)
    write("assets/css/main.css", css)
    print(f"ecosystem frame: applied {len(changed)} change(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
