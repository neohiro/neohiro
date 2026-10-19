#!/usr/bin/env python3
"""Fail if the site references a file that is not in the repository.

What it checks
--------------
Every reference the build resolves out of the working tree, in files Jekyll can
actually render:

  * ``{% include foo.html %}``      -> ``_includes/foo.html`` must exist
  * ``href="/assets/x.css"``        -> that file must exist
  * ``<img src="/images/x.png">``   -> that file must exist
  * ``<a href="/privacy/">``        -> a page must build to that path

Reachability
------------
Only files reachable from a layout or a page are checked, following the include
graph. A partial no layout includes never renders, so a dangling reference
inside one is inert: openstageisland's ``theme.html`` links
``/assets/css/main.css``, a file that site does not have, but nothing includes
it. Failing on that would be a false positive, and a gate that cries wolf gets
routed around.

File or page
------------
Decided by the extension, not by the directory. ``/images/x.png`` is a file the
deploy must serve even though it is not under ``/assets/``, and ``/privacy/`` is
a page Jekyll generates from markdown. This distinction decides whether a miss
fails the run or merely warns, so it has to be right in both directions.

Why it exists
-------------
This has broken these sites more than once, and always the same way. A layout
gains ``{% include return-to-site.html %}``, or a stylesheet link is added, and
the file is written on the machine that made the change but never committed.

The symptom differs by kind, which is why it survives review:

  - A missing **include** aborts the build:
    ``Liquid Exception: Could not locate the included file``. Loud, but only on
    CI, and only once someone merges.
  - A missing **stylesheet** breaks nothing at all. Jekyll does not validate
    link targets, so the page renders unstyled and the build is green. This is
    how the Ecosystem Network footer ended up as a wall of plain divs on three
    of the four sites.
  - A missing **page** produces a 404 and a green build.

The first two only ever show up in CI. Running this before merge puts the
failure on the change that caused it, on the machine that caused it.

What it deliberately does not check
-----------------------------------
Anchor targets within a page (``#featured-tools``) and external URLs. Those are
real, but they need a rendered document or a network, and this runs offline in
under a second. Mixed in here they would drown the real failures.

Routes are reported but do **not** fail the run
----------------------------------------------
``/privacy/`` resolves against a page that may not exist yet, and a stale route
is a content bug rather than a build-integrity one. More importantly, this
repository already has routes that 404 (``/dashboard/`` is linked from the nav
and the auth dock and does not exist). If that failed the check then no pull
request could ever go green -- least of all the ones that would fix it. So
dangling routes are printed as warnings and the exit code stays 0.

Includes and assets are the opposite: both have been build-breaking or
silently-unstyled here, and neither can be satisfied by a page that has not been
written yet. Those fail.

Usage:

    python scripts/verify_references.py            # check the working tree
    python scripts/verify_references.py --verbose  # list every resolved ref

Exits 0 when no include or asset is missing, 1 with one line per offender.
Stdlib only: no gem, no pip install, no lockfile to drift.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Directories whose contents Jekyll copies verbatim. A /assets/... link that
# points outside these, or at something absent, is a dangling reference.
INCLUDE_RE = re.compile(r"\{%-?\s*include\s+([A-Za-z0-9_.\-/]+)")
RELATIVE_URL_RE = re.compile(
    r"""(?:href|src)\s*=\s*["']\{\{\s*['"]([^'"]+)['"]\s*\|\s*relative_url\s*\}\}"""
)
# Root-absolute paths written as plain strings, with or without a Liquid filter:
# <img src="/assets/x.png">, <a href="/privacy/">. Deliberately one pattern, not
# an assets pattern and a routes pattern -- classify() decides which it is, and
# splitting the match here is what previously misfiled /images/*.png as a route.
PLAIN_ROOT_RE = re.compile(r"""(?:href|src)\s*=\s*["'](/[^"'#?]*)["']""")

# Never treated as references to this site.
EXTERNAL_PREFIXES = ("http://", "https://", "//", "mailto:", "tel:", "data:", "#")

SOURCE_GLOBS = ("_layouts/*.html", "_includes/*.html", "*.md", "pages/**/*.md")

# A root-absolute reference ending in a filename extension is a file the build
# must be able to serve, wherever it lives. Matching only /assets/ got this
# wrong: openstageisland links /images/destination-image.png from three places,
# and it was being classified as a page route -- so a missing image would have
# been reported as a content warning instead of failing the run.
_HAS_EXTENSION = re.compile(r"\.[A-Za-z0-9]{2,5}$")

# Directories Jekyll copies verbatim; a reference into one is a file, not a route.
STATIC_DIRS = ("assets/", "images/", "img/", "files/", "static/", "data/")


def is_external(ref: str) -> bool:
    return ref.startswith(EXTERNAL_PREFIXES) or "{{" in ref or "{%" in ref


def has_fragment(ref: str) -> bool:
    """True for a same-page link like /#featured-tools.

    These are targets inside a document, not paths this script can resolve, and
    the docstring says so. Matched explicitly rather than relying on the route
    patterns to exclude '#', which they do not reliably do.
    """
    return "#" in ref


def classify(ref: str) -> str:
    """Decide whether a root-absolute reference is a file or a page.

    An extension is the signal. `/images/x.png` and `/assets/y.css` are files
    the deploy must serve; `/privacy/` and `/tos/` are pages Jekyll generates
    from markdown. Getting this backwards is not a cosmetic difference -- a
    missing file has to fail the run and a stale route must not, or the gate
    either breaks every pull request or misses the silent failures.
    """
    bare = ref.split("?", 1)[0].split("#", 1)[0]
    if _HAS_EXTENSION.search(bare):
        return "asset"
    if any(bare.startswith("/" + d) or bare.lstrip("/").startswith(d) for d in STATIC_DIRS):
        # An extensionless path inside a static directory is still a file
        # reference; treat it as one so a typo there is not filed under routes.
        return "asset"
    return "route"


def reachable_sources() -> set[Path]:
    """Files Jekyll can actually render, from the include graph.

    Only these are checked. A partial no layout includes never renders, so a
    dangling reference inside one is inert -- openstageisland's theme.html links
    /assets/css/main.css, a file that site does not have, but no layout includes
    it and the link never reaches a browser. Failing the build on that would be
    a false positive, and a gate that cries wolf gets ignored.
    """
    roots: list[Path] = []
    for pattern in ("_layouts/*.html", "*.md", "pages/**/*.md"):
        roots.extend(sorted(ROOT.glob(pattern)))

    seen: set[Path] = set()
    queue = list(roots)
    while queue:
        current = queue.pop()
        if current in seen or not current.is_file():
            continue
        seen.add(current)
        text = current.read_text(encoding="utf-8", errors="replace")
        for target in INCLUDE_RE.findall(text):
            if "/" in target:
                continue
            queue.append(ROOT / "_includes" / target)
    return seen


def built_paths() -> set[str]:
    """Every path Jekyll can emit, as a URL path with a leading slash.

    ``privacy.md`` builds to ``/privacy/``; ``privacy/index.html`` builds to
    ``/privacy/``. Both are accepted so a link written either way resolves, which
    is what stops this check crying wolf over the dozen ``/privacy/`` and
    ``/tos/`` links the footer partials carry.
    """
    out: set[str] = set()
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(("_site/", ".git/", "node_modules/", "vendor/", "_includes/", "_layouts/")):
            continue
        if path.suffix.lower() not in (".md", ".html", ".htm"):
            continue
        stem = rel[: -len(path.suffix)]
        if stem == "index":
            out.add("/")
        out.add("/" + stem)
        out.add("/" + stem + "/")
        if stem.endswith("/index"):
            trimmed = stem[: -len("/index")]
            out.add("/" + trimmed)
            out.add("/" + trimmed + "/")
    return out


def asset_exists(ref: str) -> bool:
    rel = ref.lstrip("/")
    return (ROOT / rel).is_file()


def check(verbose: bool) -> tuple[list[str], list[str]]:
    routes = built_paths()
    problems: list[str] = []
    warnings: list[str] = []
    seen: set[tuple[str, str]] = set()
    checked = 0
    sources = reachable_sources()

    for source in sorted(sources):
        text = source.read_text(encoding="utf-8", errors="replace")
        rel_source = source.relative_to(ROOT).as_posix()

        def report(ref: str, kind: str, ok: bool, detail: str = "") -> None:
            """Record one reference.

            `kind` decides whether a miss is fatal. Includes and assets are;
            routes are not -- see the module docstring for why gating on routes
            would make this check unmergeable rather than useful.
            """
            nonlocal checked
            checked += 1
            key = (rel_source, ref)
            if key in seen:
                return
            seen.add(key)
            if ok:
                if verbose:
                    print(f"  ok   {rel_source}: {kind} {ref}")
                return
            message = f"{rel_source}: {kind} {ref} {detail}".rstrip()
            (warnings if kind == "route" else problems).append(message)

        def report_root(ref: str) -> None:
            """Classify and record a root-absolute reference."""
            kind = classify(ref)
            if kind == "asset":
                report(ref, "asset", asset_exists(ref))
            else:
                report(ref, "route", ref in routes or ref.rstrip("/") + "/" in routes)

        for target in INCLUDE_RE.findall(text):
            if "/" in target:
                # A path, not a partial name; Jekyll resolves those directly.
                report(target, "include-path", (ROOT / target).is_file())
                continue
            partial = ROOT / "_includes" / target
            report(target, "include", partial.is_file(), "(expected _includes/%s)" % target)

        for ref in RELATIVE_URL_RE.findall(text):
            if is_external(ref) or has_fragment(ref):
                continue
            report_root(ref)

        for ref in PLAIN_ROOT_RE.findall(text):
            if is_external(ref) or has_fragment(ref):
                continue
            report_root(ref)

    print(f"verify_references: {checked} reference(s) checked across "
          f"{len(sources)} reachable source file(s)")
    return problems, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument(
        "--strict-routes",
        action="store_true",
        help="also fail on dangling routes (off by default; see module docstring)",
    )
    args = ap.parse_args()

    problems, warnings = check(args.verbose)

    # Fatal findings first. The dangling-route warnings are printed after (or
    # not at all on success) so that reading this output top-down puts the thing
    # that broke the build above the thing that is merely worth knowing.
    if problems:
        print(
            f"\n{len(problems)} include(s) or asset(s) point at something that is "
            f"not in this repository:\n",
            file=sys.stderr,
        )
        for problem in sorted(set(problems)):
            print(f"  - {problem}", file=sys.stderr)
        print(
            "\nA file can be present in your working tree and still be missing "
            "here.\nThat is the usual cause: the change was never committed, so "
            "CI\nbuilds a tree that does not contain it.",
            file=sys.stderr,
        )
    elif args.verbose or not warnings:
        print("verify_references: every include and asset resolves")

    if warnings:
        stream = sys.stderr if args.strict_routes else sys.stdout
        label = "FAILED" if args.strict_routes else "warning"
        print(f"\n{len(warnings)} dangling route(s) ({label}, not failing the run):",
              file=stream)
        for warning in sorted(set(warnings)):
            print(f"  - {warning}", file=stream)
        if not args.strict_routes:
            print("  Routes are not gated on: a stale link is a content bug, and "
                  "this\n  repository already has some. Includes and assets are "
                  "gated on.", file=sys.stdout)

    return 1 if (problems or (args.strict_routes and warnings)) else 0


if __name__ == "__main__":
    raise SystemExit(main())