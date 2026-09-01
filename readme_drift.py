"""neohiro/readme_drift.py — verify that canonical READMEs in the workspace
match the upstream `master` branch byte-for-byte.

Catches the failure mode where a local `neohiro/<file>.md` (or any other
canonical surface) silently diverges from upstream because the local edit was
never pushed, or the local is a stale shadow of an org repo.

Usage:
    python neohiro/readme_drift.py           # human output, exit 1 on drift
    python neohiro/readme_drift.py --json    # machine output
    python neohiro/readme_drift.py --strict  # exit 2 on any warnings (e.g. offline)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# (local_relpath, upstream_path_on_master, expected_owner_repo, description)
SURFACES: list[tuple[str, str, str, str]] = [
    (
        "neohiro/README.md",
        "README.md",
        "neohiro/neohiro",
        "Profile README (METAPOD)",
    ),
    (
        "neohiro/.github/profile/README.md",
        ".github/profile/README.md",
        "neohiro/neohiro",
        "Org-profile README (neohiro)",
    ),
]

GH_RAW = "https://raw.githubusercontent.com/{owner_repo}/master/{path}"


def _fetch_raw(owner_repo: str, path: str, timeout: float = 15.0) -> bytes | None:
    """Fetch raw bytes from raw.githubusercontent.com.

    Returns None on any network/4xx/5xx error; callers should treat None
    as a warning, not a failure (offline doctor must not become a hard fail).
    """
    url = GH_RAW.format(owner_repo=owner_repo, path=path)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def _check_surface(workspace: Path, rel: str, upstream_path: str,
                   owner_repo: str, desc: str, timeout: float) -> dict:
    """Compare one local file to its master-branch upstream counterpart."""
    local_path = workspace / rel
    finding: dict = {
        "surface": desc,
        "local": rel,
        "upstream": f"{owner_repo}/master/{upstream_path}",
        "ok": False,
        "reason": "",
    }
    if not local_path.exists():
        finding["reason"] = f"local file missing: {local_path}"
        return finding
    try:
        local_bytes = local_path.read_bytes()
    except OSError as e:
        finding["reason"] = f"local read error: {e}"
        return finding
    remote = _fetch_raw(owner_repo, upstream_path, timeout=timeout)
    if remote is None:
        finding["ok"] = True  # offline → not a failure, just unverifiable
        finding["reason"] = "offline or upstream unreachable; skipped"
        return finding
    if local_bytes == remote:
        finding["ok"] = True
        finding["reason"] = "byte-identical to master"
        return finding
    # Report diff size + first byte offset to aid debugging without dumping content
    min_len = min(len(local_bytes), len(remote))
    first_diff = next(
        (i for i in range(min_len) if local_bytes[i] != remote[i]),
        min_len,
    )
    finding["reason"] = (
        f"drift: local {len(local_bytes)}B vs remote {len(remote)}B "
        f"(first diff @ byte {first_diff})"
    )
    return finding


def run(workspace: Path, timeout: float = 15.0) -> list[dict]:
    """Run drift check on every registered surface; return one finding per."""
    return [
        _check_surface(workspace, rel, up, ore, desc, timeout)
        for rel, up, ore, desc in SURFACES
    ]


def _format_text(findings: list[dict]) -> str:
    lines = ["neohiro readme-drift:"]
    for f in findings:
        marker = "OK  " if f["ok"] else "DRIFT"
        lines.append(f"  [{marker}] {f['surface']}: {f['reason']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="readme-drift",
        description="Verify canonical READMEs match upstream master byte-for-byte",
    )
    parser.add_argument("--workspace", default=os.environ.get("NEOHIRO_WORKSPACE"),
                        help="workspace root (default: $NEOHIRO_WORKSPACE or cwd)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--strict", action="store_true",
                        help="exit 2 on offline warnings (default: exit 0)")
    parser.add_argument("--timeout", type=float, default=15.0,
                        help="network timeout in seconds (default 15)")
    args = parser.parse_args()

    workspace = Path(args.workspace) if args.workspace else Path.cwd()
    findings = run(workspace, timeout=args.timeout)
    drift_count = sum(1 for f in findings if not f["ok"])
    offline_count = sum(1 for f in findings if "offline" in f["reason"])

    if args.json:
        print(json.dumps({
            "ok": drift_count == 0,
            "drift": drift_count,
            "offline": offline_count,
            "findings": findings,
        }, indent=2))
    else:
        print(_format_text(findings))

    if drift_count:
        return 1
    if args.strict and offline_count:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
