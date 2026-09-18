"""neohiro/check_eol.py — enforce LF line endings on text files across the
workspace.

Prevents the failure mode where a Windows tool (PowerShell, VS Code, etc.)
silently writes CRLF and the resulting 1-byte-per-line drift is invisible
to `git diff` under default `core.autocrlf=false` configurations.

Default scope: every tracked text file under the four org repos and the
top-level workspace directories, excluding vendored or binary paths.

Usage:
    python neohiro/check_eol.py            # human output, exit 1 on CRLF
    python neohiro/check_eol.py --json     # machine output
    python neohiro/check_eol.py --fix  # rewrite CRLF → LF in place
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from contextlib import suppress
from pathlib import Path

# Text extensions that should always be LF. Binary is auto-detected by NUL byte.
TEXT_EXTS = {
    ".md", ".txt", ".yml", ".yaml", ".json", ".jsonl", ".csv", ".tsv",
    ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs",
    ".ps1", ".psm1", ".psd1", ".sh", ".bash", ".zsh", ".fish",
    ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".xml", ".xsl", ".xsd", ".svg",
    ".toml", ".ini", ".cfg", ".conf", ".env", ".properties",
    ".rb", ".go", ".rs", ".java", ".kt", ".swift", ".c", ".cc", ".cpp", ".h", ".hpp",
    ".sql", ".graphql", ".proto",
}

# Top-level workspace directories to scan by default.
DEFAULT_SCAN_ROOTS = [
    "Brain", "Heart", "Mouth", "Mind", "userdata", "neohiro", "private-assistant",
    "voicemail", "killswitch", "iot", "monetization", "news", "links", "links-secret",
    "network", "linux", "windows", "openstageisland", "openstageisland.github.io",
    "frenzypenguin-media", "frenzypenguin-media.github.io",
    "transhumanists", "transhumanists.github.io",
    "repo-audit", "neohiro-doctor", "docs",
]

EXCLUDE_DIR_NAMES = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", "target", ".pytest_cache", ".ruff_cache",
    "vendor", "third_party", "thirdparty",
    ".tox", ".nox", ".mypy_cache", ".pyright_cache", ".eggs",
    "htmlcov", ".coverage", "coverage", ".cache", ".idea", ".vscode",
}


def _is_binary(path: Path, sniff_bytes: int = 4096) -> bool:
    """Heuristic: any NUL byte in the first 4 KB → binary."""
    try:
        with path.open("rb") as f:
            chunk = f.read(sniff_bytes)
    except OSError:
        return True
    return b"\x00" in chunk


def _is_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTS and not _is_binary(path)


def _iter_text_files(workspace: Path, roots: list[str]) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    resolved_workspace = workspace.resolve()

    # Normalise to forward-slash for separator-safe prefix checks; Windows uses
    # backslashes in resolved paths.
    def _norm(p: Path) -> str:
        return str(p.resolve()).replace("\\", "/")

    ws_norm = _norm(resolved_workspace)

    def _is_inside_workspace(candidate: Path) -> bool:
        """True if candidate is the workspace itself or a descendant."""
        c_norm = _norm(candidate)
        return c_norm == ws_norm or c_norm.startswith(ws_norm + "/")

    for root in roots:
        rp = workspace / root
        if not rp.exists():
            continue
        try:
            resolved_root = rp.resolve()
        except OSError:
            continue
        if not _is_inside_workspace(resolved_root):
            continue  # outside workspace (includes symlink-escape paths)
        for p in rp.rglob("*"):
            if not p.is_file():
                continue
            # Skip symlinks: they may loop or point outside the workspace.
            if p.is_symlink():
                continue
            if any(part in EXCLUDE_DIR_NAMES for part in p.parts):
                continue
            if p in seen:
                continue
            seen.add(p)
            if _is_text(p):
                out.append(p)
    return out


def _scan_file(path: Path) -> dict | None:
    try:
        data = path.read_bytes()
    except OSError as e:
        return {"file": str(path), "rule": "read", "message": str(e)}
    if b"\r\n" not in data:
        return None
    crlf_count = data.count(b"\r\n")
    return {
        "file": str(path),
        "rule": "crlf",
        "message": f"{crlf_count} CRLF line ending(s) found; expected LF",
    }


def _fix_file(path: Path) -> bool:
    """Rewrite CRLF → LF atomically. Returns True if file was modified.

    Uses a NamedTemporaryFile + os.replace() so the original is never partially
    written: replace() is atomic on POSIX and committed-on-close on Windows.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if b"\r\n" not in data:
        return False
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=path.name, dir=path.parent, delete=False,
        ) as tmp:
            tmp.write(data.replace(b"\r\n", b"\n"))
            tmp_name = tmp.name
        os.replace(tmp_name, path)
        return True
    except OSError:
        with suppress(NameError):
            os.remove(tmp_name)
        return False


def run(workspace: Path, roots: list[str], fix: bool = False) -> list[dict]:
    findings: list[dict] = []
    for p in _iter_text_files(workspace, roots):
        if fix:
            if _fix_file(p):
                findings.append({
                    "file": str(p),
                    "rule": "crlf-fixed",
                    "message": "rewrote CRLF → LF",
                })
            continue
        f = _scan_file(p)
        if f is not None:
            findings.append(f)
    return findings


def main() -> int:
    with suppress(AttributeError, OSError):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(
        prog="check-eol",
        description="Enforce LF line endings on text files",
    )
    parser.add_argument("--workspace", default=os.environ.get("NEOHIRO_WORKSPACE"),
                        help="workspace root (default: $NEOHIRO_WORKSPACE or cwd)")
    parser.add_argument("--root", action="append", default=None,
                        help="scan root (repeatable); default: built-in list")
    parser.add_argument("--fix", action="store_true", help="rewrite CRLF → LF in place")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    workspace = Path(args.workspace) if args.workspace else Path.cwd()
    roots = args.root if args.root else DEFAULT_SCAN_ROOTS
    findings = run(workspace, roots, fix=args.fix)

    if args.json:
        print(json.dumps({
            "ok": not findings,
            "fix": args.fix,
            "count": len(findings),
            "findings": findings,
        }, indent=2))
    else:
        action = "fixed" if args.fix else "found"
        print(f"neohiro check-eol: {action} {len(findings)} CRLF issue(s)")
        for f in findings[:50]:
            print(f"  {f['file']}: {f['message']}")
        if len(findings) > 50:
            print(f"  ... and {len(findings) - 50} more")

    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
