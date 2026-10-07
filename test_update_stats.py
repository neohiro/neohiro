"""Regression tests for update_stats.py.

update_stats.py is the only thing that writes stats.svg, which renders on the
profile README. It runs unattended on a schedule, so a failure is invisible
until someone notices a stale card. It had no tests; these cover the parts that
have actually broken:

  * `sys` was used but never imported, so the language-failure warning -- the
    diagnostic added to explain a broken card -- raised NameError and took the
    whole job down. The warning path only runs when a /languages call fails, so
    this could not surface until the card was already wrong.
  * gh_paginate must return every page, not just the first 100.

No network: `gh` is replaced with a stub, and the module is executed for real so
the assertions cover the actual top-level script rather than a copy of it.
"""
import ast
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

# Resolve relative to this file, not an absolute path. A hardcoded local clone
# path made every test fail in CI with FileNotFoundError, because the checkout
# lives somewhere else entirely on a runner.
REPO = Path(__file__).resolve().parent
SCRIPT = REPO / "update_stats.py"


class TestStaticSafety(unittest.TestCase):
    """Cheap checks that catch the class of bug where a name is used but never
    imported -- a NameError that only fires on an error path."""

    def test_no_undefined_module_references(self):
        """Every `sys.X` / `os.X` style attribute access must resolve to an import."""
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                imported |= {a.asname or a.name for a in node.names}

        used = {
            node.value.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
        }
        # Names that are locals/params rather than modules.
        modules_used = used & {"sys", "os", "re", "json", "subprocess", "pathlib"}
        missing = {m for m in modules_used if m not in imported}
        self.assertEqual(
            missing,
            set(),
            f"update_stats.py references module(s) it never imports: {sorted(missing)}. "
            f"This raises NameError the first time that code path runs. "
            f"(imports present: {sorted(imported)})",
        )


def _run_generator(tmpdir, overrides=None, *, languages_fail_for=()):
    """Execute update_stats.py for real with `gh` stubbed, in tmpdir.

    Any /languages call whose repo is in languages_fail_for returns non-zero,
    to exercise the warning path. `overrides` maps an endpoint fragment to a
    replacement payload, for probing unexpected API shapes.
    Returns (svg_bytes_or_None, stderr_text). stderr is captured so the
    language-failure warning can be asserted on directly.
    """
    overrides = overrides or {}
    real_run = subprocess.run

    def fake_run(cmd, *a, **kw):
        # Only intercept gh invocations; let anything else through.
        if not cmd or cmd[0] != "gh":
            return real_run(cmd, *a, **kw)

        endpoint = cmd[-1]

        def emit(payload):
            return mock.Mock(
                returncode=0,
                stdout=json.dumps(payload).encode("utf-8"),
                stderr=b"",
            )

        for fragment, payload in overrides.items():
            if fragment in endpoint:
                return emit(payload)

        if endpoint.startswith("/graphql") or "graphql" in cmd:
            return emit({"data": {"user": {"contributionsCollection": {
                "contributionCalendar": {"totalContributions": 1234}}}}})

        if "/languages" in endpoint:
            repo = endpoint.split("/")[3]
            if repo in languages_fail_for:
                return mock.Mock(returncode=1, stdout=b"", stderr=b"gh: Not Found")
            return emit({"Python": 1000})

        if "/repos" in endpoint and "/users" not in endpoint:
            return emit({})

        if endpoint.startswith("/users/neohiro/repos"):
            repos = [
                {"name": f"repo{i}", "fork": False, "stargazers_count": i}
                for i in range(1, 4)
            ]
            if "--slurp" in cmd:
                # gh --slurp: one array per page. Split across two pages so the
                # flatten logic is exercised.
                mid = len(repos) // 2
                return emit([repos[:mid], repos[mid:]])
            return emit(repos)

        if "/search/commits" in endpoint:
            return emit({"total_count": 42})

        if endpoint.startswith("/users/neohiro"):
            return emit({"followers": 7})

        return emit({})

    with mock.patch.object(subprocess, "run", side_effect=fake_run), \
                                       mock.patch.object(sys, "argv", ["update_stats.py"]):
        # Run in tmpdir so stats.svg is written there, not in the repo.
        old = Path.cwd()
        os.chdir(tmpdir)
        buf = io.StringIO()
        try:
            spec = importlib.util.spec_from_file_location("update_stats_under_test", SCRIPT)
            mod = importlib.util.module_from_spec(spec)
            # The language-failure warning goes to stderr; capture it so it can
            # be asserted on instead of only inferred from the SVG.
            with contextlib.redirect_stderr(buf):
                spec.loader.exec_module(mod)
        finally:
            os.chdir(old)

    svg = Path(tmpdir) / "stats.svg"
    # Read BYTES, not text: read_text() applies universal-newline translation and
    # would silently rewrite CRLF to LF, so a text-mode assertion about line
    # endings can never fail regardless of what the script wrote.
    return (svg.read_bytes() if svg.exists() else None), buf.getvalue()


class TestGenerator(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_runs_clean_when_all_languages_succeed(self):
        svg, _err = _run_generator(self.tmp)
        self.assertIsNotNone(svg, "stats.svg was not written")
        self.assertIn(b"<svg", svg)
        self.assertIn(b"Agent-assisted commits", svg)

    def test_language_failure_warns_instead_of_crashing(self):
        """The regression: this used to raise NameError on `sys` and kill the run.

        A broken /languages call must degrade the card to fewer languages and
        still exit 0, so a single bad repo cannot stop the weekly refresh. It
        must also say something on stderr -- a silent partial card is exactly
        the failure this warning exists to make visible.
        """
        svg, err = _run_generator(self.tmp, languages_fail_for=("repo1", "repo2"))
        self.assertIsNotNone(svg, "stats.svg must still be written when languages fail")
        self.assertIn(b"<svg", svg)
        self.assertIn("languages unavailable for 2/3 repos", err)
        # The offending repos should be named, not just counted.
        self.assertIn("repo1", err)
        self.assertIn("repo2", err)

    def test_warning_is_truncated_to_a_readable_number_of_lines(self):
        """A long failure list must not dump every repo into the log."""
        svg, err = _run_generator(
            self.tmp,
            overrides={
                "/users/neohiro/repos": [
                    [{"name": f"repo{i}", "fork": False, "stargazers_count": i} for i in range(12)]
                ]
            },
            languages_fail_for=tuple(f"repo{i}" for i in range(12)),
        )
        self.assertIsNotNone(svg)
        self.assertIn("languages unavailable for 12/12 repos", err)
        # Header + at most 5 detail lines.
        detail = [l for l in err.splitlines() if l.strip().startswith("repo")]
        self.assertLessEqual(len(detail), 5, "warning must not be unbounded")
        self.assertEqual(len(detail), 5, "the first 5 failures should be named")

    def test_flattens_all_pages(self):
        """gh_paginate must return every page, not just the first."""
        svg, _err = _run_generator(self.tmp)
        # 3 repos across 2 pages; if only page 1 survived, the count would be 1.
        self.assertIn(b">3<", svg.replace(b" ", b""), "expected 3 repositories")

    def test_writes_lf_only(self):
        """check_eol.py requires LF; CRLF here would diff noisily every run.

        Asserted on raw bytes -- see _run_generator. A text-mode read would
        normalise CRLF away and make this assertion unfalsifiable.
        """
        svg, err = _run_generator(self.tmp)
        self.assertIsNotNone(svg)
        self.assertNotIn(b"\r\n", svg, "stats.svg must be LF-only")

    def test_all_repos_failing_languages_still_writes_card(self):
        """Total language failure must degrade to an empty panel, not a crash.

        Every /languages call failing is the extreme version of the rename /
        deleted-repo case. The card should still render so the README keeps a
        current snapshot rather than freezing on the last good one.
        """
        svg, err = _run_generator(
            self.tmp, languages_fail_for=("repo1", "repo2", "repo3")
        )
        self.assertIsNotNone(svg, "card must still render when no languages resolve")
        self.assertIn(b"<svg", svg)
        self.assertIn(b"No language data yet", svg)

    def test_zero_repos_does_not_divide_by_zero(self):
        """An account with no public repos must not crash on total_lb.

        total_lb is used as a divisor for language percentages; the `or 1`
        guard exists for this, so prove it holds.
        """
        svg, err = _run_generator(
            self.tmp, overrides={"/users/neohiro/repos": [[]]}
        )
        self.assertIsNotNone(svg, "card must render with zero repos")
        self.assertIn(b"No language data yet", svg)
        self.assertNotIn(b"NaN", svg, "no NaN may leak into the rendered card")
        self.assertNotIn(b"Infinity", svg)

    def test_single_page_response_is_handled(self):
        """--slurp returns [[...]] even for one page; it must not double-wrap."""
        svg, err = _run_generator(
            self.tmp,
            overrides={
                "/users/neohiro/repos": [
                    [{"name": "solo", "fork": False, "stargazers_count": 7}]
                ]
            },
        )
        self.assertIsNotNone(svg)
        self.assertIn(b">1<", svg.replace(b" ", b""), "expected 1 repository")

    def test_fork_repos_are_excluded(self):
        """Forks must not inflate star and repo totals."""
        svg, err = _run_generator(
            self.tmp,
            overrides={
                "/users/neohiro/repos": [
                    [
                        {"name": "mine", "fork": False, "stargazers_count": 10},
                        {"name": "forked", "fork": True, "stargazers_count": 999},
                    ]
                ]
            },
        )
        self.assertIsNotNone(svg)
        text = svg.decode("utf-8")
        self.assertIn(">10<", text, "only the source repo's stars should count")
        self.assertNotIn("999", text, "fork stars must not be counted")


if __name__ == "__main__":
    unittest.main(verbosity=2)