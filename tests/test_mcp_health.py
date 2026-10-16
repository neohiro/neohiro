"""Tests for `mcp_health`, the MCP handshake prober.

The prober exists to answer "does this server actually work", and the only way
to test that honestly is to run real MCP servers against it. These tests run a
small Python MCP server as a subprocess, so they are hermetic: no `npx`, no
network, no installed packages, and therefore no flakes when a registry is slow.

Each server mode exercises one failure mode that a naive probe misreports as a
generic hang:

* ``banner``     — chatty stdout that must be skipped, not parsed
* ``error``      — a JSON-RPC error object, which is a verdict not a crash
* ``exit``       — a process that dies before replying
* ``hang``       — a process that accepts input and never answers
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp_health import (
    McpClient,
    McpProbeError,
    ProbeResult,
    format_report,
    load_jsonc,
    probe,
    probe_all,
    resolve_command,
    strip_jsonc,
)

# A conformant-enough MCP server. `notifications/initialized` carries no id and
# is skipped, which is also what exercises the prober's correlation logic.
FAKE_SERVER = """
import json
import sys
import time

MODE = sys.argv[1]

TOOLS = [
    {
        "name": "read_file",
        "description": "Read a file",
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "write_file",
        "description": "Write a file",
        "annotations": {"readOnlyHint": False, "destructiveHint": True},
    },
    {"name": "mystery_tool", "description": "No annotations at all"},
]

if MODE == "banner":
    print("fake-mcp starting up")
    print("listening on stdio")
    sys.stdout.flush()

if MODE == "exit":
    sys.exit(3)

if MODE == "hang":
    time.sleep(300)

for raw in sys.stdin:
    raw = raw.strip()
    if not raw:
        continue
    try:
        message = json.loads(raw)
    except ValueError:
        continue
    method = message.get("method")
    mid = message.get("id")
    if mid is None:
        continue
    if MODE == "error":
        # A JSON-RPC error object is a *verdict*: the server answered and said
        # no. It must be reported as a rejection, not as a transport failure.
        print(json.dumps({
            "jsonrpc": "2.0", "id": mid,
            "error": {"code": -32603, "message": "Method not found"},
        }))
        sys.stdout.flush()
        continue
    if method == "initialize":
        result = {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "fake-mcp", "version": "1.2.3"},
        }
    elif method == "tools/list":
        result = {"tools": TOOLS}
    else:
        print(json.dumps({
            "jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": "Method not found"},
        }))
        sys.stdout.flush()
        continue
    print(json.dumps({"jsonrpc": "2.0", "id": mid, "result": result}))
    sys.stdout.flush()
"""


def write_server(tmp_path: Path, mode: str) -> list[str]:
    script = tmp_path / "fake_mcp.py"
    script.write_text(FAKE_SERVER, encoding="utf-8")
    return [sys.executable, str(script), mode]


class TestAHealthyServer:
    def test_the_handshake_succeeds_and_reports_the_server(self, tmp_path):
        result = probe("fake", write_server(tmp_path, "ok"), timeout=30)

        assert result.ok
        assert result.error == ""
        assert result.server_name == "fake-mcp"
        assert result.server_version == "1.2.3"
        assert result.protocol_version == "2025-06-18"
        assert result.elapsed_s > 0

    def test_it_lists_every_tool(self, tmp_path):
        result = probe("fake", write_server(tmp_path, "ok"), timeout=30)

        assert result.tool_count == 3
        assert result.tool_names == ["read_file", "write_file", "mystery_tool"]

    def test_it_reads_annotations_rather_than_guessing(self, tmp_path):
        result = probe("fake", write_server(tmp_path, "ok"), timeout=30)
        tools = {tool.name: tool for tool in result.tools}

        assert tools["read_file"].read_only is True
        assert tools["read_file"].mutating is False
        assert tools["write_file"].read_only is False
        assert tools["write_file"].mutating is True
        assert tools["write_file"].destructive is True

    def test_an_unannotated_tool_is_unknown_not_assumed_safe(self, tmp_path):
        """`readOnlyHint` is a hint; silence is not consent.

        Defaulting a missing hint to "safe" is how a write-capable server gets
        trusted, so absence has to stay `None` all the way to the report.
        """
        result = probe("fake", write_server(tmp_path, "ok"), timeout=30)
        tools = {tool.name: tool for tool in result.tools}

        assert tools["mystery_tool"].read_only is None
        assert tools["mystery_tool"].mutating is None
        assert result.unannotated_tools() == ["mystery_tool"]


class TestServersThatMisbehave:
    def test_a_chatty_server_is_probed_not_rejected(self, tmp_path):
        """Banner lines on stdout must be skipped.

        A server that greets on stdout is normal, and rejecting it would report
        a working server as broken. The noise is counted so the report can show
        it, but it is not a failure.
        """
        result = probe("fake", write_server(tmp_path, "banner"), timeout=30)

        assert result.ok
        assert result.tool_count == 3
        assert result.stdout_noise_lines == 2

    def test_a_jsonrpc_error_is_a_verdict_not_a_crash(self, tmp_path):
        result = probe("fake", write_server(tmp_path, "error"), timeout=30)

        assert not result.ok
        assert "Method not found" in result.error

    def test_a_process_that_dies_is_reported_as_exited(self, tmp_path):
        result = probe("fake", write_server(tmp_path, "exit"), timeout=30)

        assert not result.ok
        assert "exited" in result.error
        assert "3" in result.error

    def test_a_silent_server_times_out_rather_than_hanging_forever(self, tmp_path):
        started = pytest.importorskip("time")
        begin = started.monotonic()
        result = probe("fake", write_server(tmp_path, "hang"), timeout=2.0)
        elapsed = started.monotonic() - begin

        assert not result.ok
        assert "timed out" in result.error
        # A timeout that does not actually bound the wait is the bug this
        # guards; the generous ceiling absorbs CI scheduling noise.
        assert elapsed < 60


class TestJsoncReading:
    """The config reader is the CLI's only entry point and had no coverage.

    A `//` comment that is not actually stripped still parses as a syntax error
    at best, and these configs are comment-heavy by nature, so this is the path
    every invocation depends on.
    """

    def test_a_line_comment_is_removed(self):
        raw = '{\n  // a line comment\n  "a": 1\n}'
        assert load_jsonc(raw) == {"a": 1}

    def test_a_block_comment_is_removed(self):
        raw = '{/* block */ "a": 1}'
        assert load_jsonc(raw) == {"a": 1}

    def test_a_multiline_block_comment_is_removed(self):
        raw = '{\n  /* one\n     two\n     three */\n  "a": 1\n}'
        assert load_jsonc(raw) == {"a": 1}

    def test_a_url_inside_a_string_is_not_a_comment(self):
        """The classic false positive: `https://` is not a line comment."""
        raw = '{"url": "https://example.com/x"}'
        assert load_jsonc(raw) == {"url": "https://example.com/x"}

    def test_a_comment_marker_inside_a_string_survives(self):
        raw = '{"pattern": "/* not a comment */"}'
        assert load_jsonc(raw) == {"pattern": "/* not a comment */"}

    def test_an_escaped_quote_does_not_end_the_string(self):
        raw = '{"a": "say \\"hi\\" // not a comment"}'
        assert load_jsonc(raw) == {"a": 'say "hi" // not a comment'}

    def test_an_escaped_backslash_before_a_quote_is_handled(self):
        # "\\\\" is a literal backslash, so the quote after it *does* close the
        # string. Getting this backwards truncates the document.
        raw = '{"a": "back\\\\", "b": 2}'
        assert load_jsonc(raw) == {"a": "back\\", "b": 2}

    def test_a_trailing_comma_is_tolerated(self):
        assert load_jsonc('{"a": 1,}') == {"a": 1}

    def test_a_trailing_comma_in_an_array_is_tolerated(self):
        assert load_jsonc('{"a": [1, 2,]}') == {"a": [1, 2]}

    def test_a_comma_inside_a_string_is_not_dropped(self):
        assert load_jsonc('{"a": "x,", "b": 1}') == {"a": "x,", "b": 1}

    def test_line_numbers_survive_comment_removal(self):
        """A parse error must point at the operator's actual file.

        Collapsing a comment onto one line would renumber everything after it,
        so the reported line would not exist in the config being edited.
        """
        raw = '{\n  "a": 1,\n  // note\n  "b": ,\n}'
        with pytest.raises(json.JSONDecodeError) as excinfo:
            json.loads(strip_jsonc(raw))
        assert excinfo.value.lineno == 4

    def test_a_block_comment_keeps_the_lines_it_spanned(self):
        raw = '{\n/* a\nb\nc */\n"x": 1\n}'
        stripped = strip_jsonc(raw)
        assert stripped.count("\n") == raw.count("\n")

    def test_plain_json_still_works(self):
        assert load_jsonc('{"mcp": {"a": {"command": ["npx"]}}}') == {
            "mcp": {"a": {"command": ["npx"]}}
        }

    def test_invalid_json_raises_the_prober_error(self):
        with pytest.raises(McpProbeError, match="not valid JSON"):
            load_jsonc("{not json at all")

    def test_a_non_object_document_is_rejected(self):
        with pytest.raises(McpProbeError, match="top level"):
            load_jsonc("[1, 2, 3]")


class TestCommandResolution:
    def test_a_bare_string_command_is_rejected_with_guidance(self):
        """`command: "npx -y pkg"` must not iterate into single characters."""
        with pytest.raises(McpProbeError, match="array of strings"):
            resolve_command("npx -y pkg")  # type: ignore[arg-type]

    def test_an_empty_argument_is_rejected(self):
        with pytest.raises(McpProbeError, match="non-empty string"):
            resolve_command(["npx", ""])

    def test_a_missing_executable_is_rejected_before_spawning(self):
        """A typo'd package name must not masquerade as a hung server."""
        with pytest.raises(McpProbeError, match="not on PATH"):
            resolve_command(["definitely-not-a-real-binary-xyzzy"])

    def test_an_empty_command_is_rejected(self):
        with pytest.raises(McpProbeError, match="empty command"):
            resolve_command([])

    def test_a_missing_absolute_path_is_rejected(self):
        with pytest.raises(McpProbeError, match="not found"):
            resolve_command(["/nonexistent/path/to/binary"])

    def test_an_absolute_executable_passes_through(self):
        """The interpreter running the tests is an absolute path with a suffix."""
        assert resolve_command([sys.executable]) == [sys.executable]

    def test_a_bare_name_resolves_to_a_launchable_path(self):
        """The bug this pins: on Windows `npx` is `npx.cmd`.

        `shutil.which` happily reports success for the bare name, so a prober
        that does not rewrite argv[0] hands CreateProcess a name it refuses to
        run and every server fails identically with WinError 2 — a config
        problem reported as a fleet of broken packages.
        """
        import shutil

        located = shutil.which("python") or shutil.which("python3")
        if located is None:  # pragma: no cover - interpreter is always present
            pytest.skip("no python on PATH")

        resolved = resolve_command(["python"])[0]

        assert Path(resolved).exists()
        assert os.path.splitext(resolved)[1].lower() in {"", ".exe", ".cmd", ".bat"}
        if os.name == "nt":
            assert Path(resolved).suffix != "", (
                "a bare command name was returned on Windows; it cannot be "
                "executed without its shim extension"
            )

    def test_a_resolved_command_actually_starts(self, tmp_path):
        """End-to-end: the name resolution survives contact with Popen."""
        server = write_server(tmp_path, "ok")

        result = probe("fake", server, timeout=30)

        assert result.ok, result.error


class TestSweeps:
    def test_disabled_servers_are_skipped_entirely(self, tmp_path):
        servers = {
            "off": {
                "command": ["definitely-not-a-real-binary-xyzzy"],
                "enabled": False,
            }
        }
        assert probe_all(servers, timeout=5) == []

    def test_a_malformed_entry_is_reported_instead_of_raising(self):
        servers = {"broken": {"type": "remote", "url": "https://example.com"}}

        results = probe_all(servers, timeout=5)

        assert len(results) == 1
        assert not results[0].ok
        assert "malformed" in results[0].error

    def test_a_non_string_argument_is_treated_as_malformed(self):
        results = probe_all({"broken": {"command": ["npx", 7]}}, timeout=5)

        assert len(results) == 1
        assert not results[0].ok

    def test_a_non_object_entry_is_reported_rather_than_crashing(self):
        """One bad entry must not abort the sweep.

        A bare string where an object belongs is a plausible hand-edit, and
        `spec.get` on it raises AttributeError — which would take down every
        other server's verdict with it.
        """
        results = probe_all({"bad": "npx -y pkg"}, timeout=5)

        assert len(results) == 1
        assert not results[0].ok
        assert "must be an object" in results[0].error

    def test_the_sweep_reports_every_server_despite_failures(self, tmp_path):
        """The value of a sweep is the comparison.

        Aborting on the first failure would hide the servers that do work, which
        is the part the operator needs to decide what to keep.
        """
        good = write_server(tmp_path, "ok")
        servers = {
            "good": {"command": good},
            "dead": {"command": write_server(tmp_path, "exit")},
            "other-good": {"command": good},
        }

        results = probe_all(servers, timeout=30)
        by_name = {result.name: result for result in results}

        assert set(by_name) == {"good", "dead", "other-good"}
        assert by_name["good"].ok
        assert not by_name["dead"].ok
        assert by_name["other-good"].ok


class TestReporting:
    def test_a_pass_line_carries_the_tool_count_and_protocol(self):
        report = format_report(
            [
                ProbeResult(
                    name="context7",
                    command=["npx", "ctx"],
                    ok=True,
                    tool_count=2,
                    tools=[],
                    server_name="Context7",
                    server_version="1.0.0",
                    protocol_version="2025-06-18",
                    elapsed_s=1.25,
                )
            ]
        )

        assert "PASS" in report
        assert "context7" in report
        assert "2 tools" in report
        assert "2025-06-18" in report

    def test_a_fail_line_shows_the_reason(self):
        report = format_report(
            [
                ProbeResult(
                    name="dead",
                    command=["nope"],
                    ok=False,
                    error="not on PATH: nope",
                )
            ]
        )

        assert "FAIL" in report
        assert "not on PATH: nope" in report

    def test_the_report_flags_unannotated_tools_and_noise(self):
        from mcp_health import ToolInfo

        report = format_report(
            [
                ProbeResult(
                    name="noisy",
                    command=["x"],
                    ok=True,
                    tools=[ToolInfo(name="mystery_tool")],
                    stdout_noise_lines=4,
                )
            ]
        )

        assert "no readOnlyHint" in report
        assert "mystery_tool" in report
        assert "non-JSON stdout" in report

    def test_the_report_survives_an_empty_sweep(self):
        assert format_report([]) == ""


class TestCredentialsAreNotLeaked:
    def test_a_secret_env_var_is_not_echoed_in_the_result(self, tmp_path):
        """A probe result gets pasted into issues.

        Env values must never reach it; only the variable name is meaningful for
        diagnosis, and only the key set is recorded at all.
        """
        result = probe(
            "fake",
            write_server(tmp_path, "ok"),
            env={"GITHUB_TOKEN": "ghp_supersecretvalue"},
            timeout=30,
        )

        assert result.ok
        assert "ghp_supersecretvalue" not in json.dumps(result.to_dict())

    def test_the_child_inherits_the_path_so_npx_can_resolve(self):
        """Env overlay must not replace the environment.

        A naive `{**overlay}` build would hand the child a PATH-free environment
        and every package-based server would fail to launch for a reason that
        has nothing to do with the server.
        """
        client = McpClient([sys.executable], env={"EXTRA": "1"})
        env = client._child_env()  # asserting the boundary, not testing privates

        assert env["EXTRA"] == "1"
        assert env.get("PATH") == os.environ.get("PATH")
