#!/usr/bin/env python3
"""Regenerate assets/data/repos.json from _data/repos.yml.

Why this exists
---------------
The home page fetches assets/data/repos.json at runtime to populate the Community
project selector, while every card on the page is rendered from _data/repos.yml.
Those two were maintained by hand and had already drifted (a featured tool that
did not exist in the JSON list, stale platforms). This script makes drift
impossible: run it after every repos.yml edit.

    python scripts/sync_repos_json.py           # rewrite the file
    python scripts/sync_repos_json.py --check   # exit 1 if it would change

The dash normalisation (— and · become ASCII '-') matches what the previous
publisher did, so the JSON stays greppable from a shell.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install pyyaml")

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_data" / "repos.yml"
DST = ROOT / "assets" / "data" / "repos.json"

# Field order is fixed so the diff only ever shows real changes.
FIELDS = [
    "name", "title", "tagline", "platform", "language", "category",
    "featured", "weight", "repo_url", "demo_url", "docs_url",
    "stars", "forks", "open_issues", "created_at", "pushed_at",
]


def ascii_dash(value: str) -> str:
    return value.replace("—", "-").replace("–", "-").replace("·", "-")


def coerce(raw: dict) -> dict:
    """YAML scalars come back as str/int/bool; normalise the ones the UI reads."""
    out = {}
    for key in FIELDS:
        if key not in raw:
            continue
        val = raw[key]
        if key in ("featured",):
            val = bool(val)
        elif key in ("weight", "stars", "forks", "open_issues"):
            # A repo may legitimately omit a count, and YAML turns a bare `null`
            # into None; int(None) would abort the whole sync.
            try:
                val = int(val)
            except (TypeError, ValueError):
                continue
        elif key == "tagline":
            val = ascii_dash(str(val))
        out[key] = val
    return out


def build() -> dict:
    data = yaml.safe_load(SRC.read_text(encoding="utf-8")) or {}
    repos = [coerce(r) for r in (data.get("repos") or [])]
    repos.sort(key=lambda r: r.get("weight", 999))
    # YAML parses bare timestamps into datetime; the JSON copy keeps the string.
    stamp = data.get("generated_at", "")
    if not isinstance(stamp, str):
        stamp = stamp.isoformat()
    return {"generated_at": stamp, "repos": repos}


def render(payload: dict) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail instead of writing")
    args = ap.parse_args()

    new_text = render(build())

    if not DST.exists():
        if args.check:
            print("repos.json is missing — run: python scripts/sync_repos_json.py")
            return 1
        DST.parent.mkdir(parents=True, exist_ok=True)
        DST.write_text(new_text, encoding="utf-8")
        print(f"wrote {DST.relative_to(ROOT)}")
        return 0

    old_text = DST.read_text(encoding="utf-8")

    # Compare parsed content, not raw bytes. Git may hand back the file with CRLF
    # line endings on Windows, and a byte comparison would then report drift on
    # every checkout even when the data is identical.
    try:
        same = json.loads(old_text) == json.loads(new_text)
    except json.JSONDecodeError as exc:
        print(f"{DST.relative_to(ROOT)} is not valid JSON ({exc}) — run: python scripts/sync_repos_json.py")
        return 1 if args.check else _write(new_text, args)

    if same:
        print(f"repos.json is in sync ({DST.relative_to(ROOT)})")
        return 0

    return _write(new_text, args)


def _write(text: str, args) -> int:
    if args.check:
        print("repos.json is OUT OF SYNC with _data/repos.yml — run: python scripts/sync_repos_json.py")
        return 1
    DST.write_text(text, encoding="utf-8")
    print(f"wrote {DST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())