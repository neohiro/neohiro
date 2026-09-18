"""neohiro/readme_drift.py — verify that canonical READMEs in the workspace
match the upstream default branch byte-for-byte.

Catches the failure mode where a local `neohiro/<file>.md` (or any other
canonical surface) silently diverges from upstream because the local edit was
never pushed, or the local is a stale shadow of an org repo.

Usage:
    python neohiro/readme_drift.py           # human output, exit 1 on drift
    python neohiro/readme_drift.py --json   # JSON output (for CI pipelines)
    python neohiro/readme_drift.py --strict  # exit 2 on offline (warn in CI)
    python neohiro/readme_drift.py --quiet  # no output; exit code only (CI)
    GH_TOKEN=gho_... python neohiro/readme_drift.py  # authenticated (5k/hr)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from contextlib import suppress
from pathlib import Path

# (local_relpath, upstream_path_on_default, expected_owner_repo, description)
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

GH_RAW = "https://raw.githubusercontent.com/{owner_repo}/{branch}/{path}"

# Git refname rules: https://git-scm.com/docs/git-check-ref-format
_VALID_BRANCH = re.compile(
    r"^(?!-)"          # cannot begin with - (would look like a flag)
    r"(?!.*\.\.)"      # cannot contain ..
    r"(?!.*//)"        # cannot contain //
    r"(?!.*@\{)"       # cannot contain @{
    r"(?!.*[\\ ])"     # cannot contain backslash or space
    r"[A-Za-z0-9._/-]+"
    r"(?<!/)$"         # cannot end with /
    r"(?<!\.lock)$"    # cannot end with .lock (git ref rule)
)


class _PreservingAuthRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Copy the original request's headers (including Authorization) onto
    redirect targets.

    Default HTTPRedirectHandler builds a fresh Request with only the URL;
    the GH_TOKEN Bearer header would be dropped on a 3xx to
    objects.githubusercontent.com, causing auth-required requests to fail
    silently as "offline".
    """
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        m = req.get_method()
        if not (code in (301, 302, 303, 307, 308) and m in ("GET", "HEAD")):
            raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)
        new_headers = dict(req.header_items())
        new_headers.pop("Host", None)  # urllib will set this from newurl
        return urllib.request.Request(
            newurl, headers=new_headers, method=m,
            unverifiable=True,
        )


_GH_OPENER = urllib.request.build_opener(_PreservingAuthRedirectHandler())


def _fetch_raw(owner_repo: str, path: str, branch: str,
               timeout: float = 15.0) -> bytes | None:
    """Fetch raw bytes from raw.githubusercontent.com.

    Returns None on any network/4xx/5xx error; callers should treat None
    as a warning, not a failure (offline doctor must not become a hard fail).

    If GH_TOKEN is set in the environment, the request is authenticated,
    raising the rate-limit from 60 to 5,000 req/hour per IP.
    """
    url = GH_RAW.format(owner_repo=owner_repo, branch=branch, path=path)
    headers: dict[str, str] = {}
    token = os.environ.get("GH_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with _GH_OPENER.open(req, timeout=timeout) as r:
            return r.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def _validate_branch(branch: str) -> None:
    """Raise ValueError if `branch` is not a valid Git refname component.

    Defense in depth: prevents URL injection / path-traversal via --branch.
    The server (GitHub) would 404 anyway, but rejecting locally gives a faster,
    clearer error message and avoids surfacing weird URLs to any log/audit sink.
    """
    if not branch or not _VALID_BRANCH.match(branch):
        raise ValueError(
            f"invalid branch name: {branch!r} "
            "(expected: non-empty, no '..' or '//', no '@{', no leading '-', "
            "no trailing '/', no '.lock' suffix)"
        )


def _check_surface(workspace: Path, rel: str, upstream_path: str,
                   owner_repo: str, desc: str, branch: str,
                   timeout: float) -> dict:
    """Compare one local file to its upstream default-branch counterpart."""
    local_path = workspace / rel
    finding: dict = {
        "surface": desc,
        "local": rel,
        "upstream": f"{owner_repo}/{branch}/{upstream_path}",
        "status": "error",
        "reason": "",
    }
    if not local_path.exists():
        finding["status"] = "error"
        finding["reason"] = f"local file missing: {local_path}"
        return finding
    try:
        local_bytes = local_path.read_bytes()
    except OSError as e:
        finding["status"] = "error"
        finding["reason"] = f"local read error: {e}"
        return finding
    remote = _fetch_raw(owner_repo, upstream_path, branch, timeout=timeout)
    if remote is None:
        finding["status"] = "offline"
        finding["reason"] = "offline or upstream unreachable; skipped"
        return finding
    if local_bytes == remote:
        finding["status"] = "ok"
        finding["reason"] = f"byte-identical to {branch}"
        return finding
    # Report diff size + first byte offset to aid debugging without dumping content
    min_len = min(len(local_bytes), len(remote))
    first_diff = next(
        (i for i in range(min_len) if local_bytes[i] != remote[i]),
        min_len,
    )
    finding["status"] = "drift"
    finding["reason"] = (
        f"drift: local {len(local_bytes)}B vs remote {len(remote)}B "
        f"(first diff @ byte {first_diff})"
    )
    return finding


def run(workspace: Path, branch: str = "main", timeout: float = 15.0) -> list[dict]:
    """Run drift check on every registered surface; return one finding per."""
    return [
        _check_surface(workspace, rel, up, ore, desc, branch, timeout)
        for rel, up, ore, desc in SURFACES
    ]


def _format_text(findings: list[dict], branch: str = "main") -> str:
    markers = {"ok": "OK  ", "offline": "SKIP", "drift": "DRIFT", "error": "ERR "}
    lines = [f"neohiro readme-drift (default={branch}):"]
    for f in findings:
        marker = markers.get(f.get("status", "error"), "????")
        lines.append(f"  [{marker}] {f['surface']}: {f['reason']}")
    return "\n".join(lines)


def main() -> int:
    with suppress(AttributeError, OSError):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(
        prog="readme-drift",
        description="Verify canonical READMEs match upstream default branch byte-for-byte",
    )
    parser.add_argument("--workspace", default=os.environ.get("NEOHIRO_WORKSPACE"),
                        help="workspace root (default: $NEOHIRO_WORKSPACE or cwd)")
    parser.add_argument("--branch", default="main",
                        help="upstream branch to compare against (default: main)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--strict", action="store_true",
                        help="exit 2 on offline warnings (default: exit 0)")
    parser.add_argument("--quiet", action="store_true",
                        help="suppress output; exit code only (for CI)")
    parser.add_argument("--timeout", type=float, default=15.0,
                        help="network timeout in seconds (default 15)")
    args = parser.parse_args()
    try:
        _validate_branch(args.branch)
    except ValueError as e:
        parser.error(str(e))

    workspace = Path(args.workspace) if args.workspace else Path.cwd()
    findings = run(workspace, branch=args.branch, timeout=args.timeout)
    counts = Counter(f.get("status") for f in findings)
    drift_count = counts.get("drift", 0)
    error_count = counts.get("error", 0)
    offline_count = counts.get("offline", 0)

    if args.json:
        print(json.dumps({
            "ok": drift_count == 0 and error_count == 0,
            "drift": drift_count,
            "error": error_count,
            "offline": offline_count,
            "branch": args.branch,
            "findings": findings,
        }, indent=2))
    elif not args.quiet:
        print(_format_text(findings, branch=args.branch))

    if drift_count or error_count:
        return 1
    if args.strict and offline_count:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
