"""Verify that an MCP server actually speaks MCP, not merely that npx resolved.

``npx <pkg> --help`` proves a package exists. It does not prove the package is an
MCP server: the process may exit 0 after printing a banner, may log its banner to
stdout where a JSON-RPC parser will choke, or may hang waiting for a handshake
that never arrives. This module does the handshake for real — ``initialize``,
``notifications/initialized``, ``tools/list`` — over the stdio transport, and
reports what came back.

Transport notes that matter and are easy to get wrong:

* MCP stdio is **newline-delimited JSON-RPC 2.0**. It is not LSP framing; there
  is no ``Content-Length`` header.
* A server is entitled to print banners and progress lines on stdout. Skipping
  undecodable lines instead of aborting is the difference between "this server
  is broken" and "this server is chatty".
* On Windows a bare ``npx`` resolves to ``npx.cmd``, which ``CreateProcess``
  will not run without a shell. We append the extension rather than reaching for
  ``shell=True``, because a shell would re-introduce the quoting and injection
  problems that avoiding it is for.

Credentials are never echoed. Env values are reported as key names only, so a
config can be pasted into a bug report.
"""

from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import threading
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self

#: Latest revision this module speaks. Servers negotiate downwards; whatever
#: they return in ``initialize`` is reported as ``protocol_version``.
PROTOCOL_VERSION = "2025-06-18"

DEFAULT_TIMEOUT = 90.0

#: Windows ships these as `.cmd`/`.bat` shims rather than executables.
_SHIM_SUFFIXES = (".cmd", ".bat") if os.name == "nt" else ()


class McpProbeError(RuntimeError):
    """The probe could not reach a verdict.

    Distinct from a server that answered and said no: a raised error means we
    never got to ask, so the config is at fault rather than the package.
    """


@dataclass(frozen=True)
class ToolInfo:
    """One entry from ``tools/list``.

    Only the fields an operator actually triages: whether the model can invoke
    it, whether it changes state, and its context cost. The schema itself can be
    thousands of tokens and is deliberately dropped — the whole reason to check
    a server is to decide whether to keep it, and the schema does not inform
    that.
    """

    name: str
    description: str = ""
    read_only: bool | None = None
    destructive: bool | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ToolInfo:
        annotations = payload.get("annotations")
        if not isinstance(annotations, dict):
            annotations = {}
        description = payload.get("description")
        return cls(
            name=str(payload.get("name", "")),
            description=description if isinstance(description, str) else "",
            read_only=_optional_bool(annotations.get("readOnlyHint")),
            destructive=_optional_bool(annotations.get("destructiveHint")),
        )

    @property
    def mutating(self) -> bool | None:
        """Whether the tool can change state.

        ``readOnlyHint`` is a hint, so an absent value is reported as unknown
        rather than assumed safe. Servers that annotate honestly let this drive
        how much a given server needs to be trusted.
        """
        return None if self.read_only is None else not self.read_only


@dataclass
class ProbeResult:
    """Verdict for a single server."""

    name: str
    command: Sequence[str]
    ok: bool
    tool_count: int = 0
    tools: list[ToolInfo] = field(default_factory=list)
    server_name: str = ""
    server_version: str = ""
    protocol_version: str = ""
    elapsed_s: float = 0.0
    error: str = ""
    stderr_tail: str = ""
    stdout_noise_lines: int = 0

    @property
    def tool_names(self) -> list[str]:
        return [tool.name for tool in self.tools]

    def unannotated_tools(self) -> list[str]:
        """Tools that advertise no ``readOnlyHint``.

        These are the ones a human has to read the description of before
        granting a server filesystem or network write access.
        """
        return [tool.name for tool in self.tools if tool.read_only is None]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "command": list(self.command),
            "ok": self.ok,
            "tool_count": self.tool_count,
            "tools": [tool.name for tool in self.tools],
            "unannotated_tools": self.unannotated_tools(),
            "server_name": self.server_name,
            "server_version": self.server_version,
            "protocol_version": self.protocol_version,
            "elapsed_s": round(self.elapsed_s, 3),
            "error": self.error,
            "stderr_tail": self.stderr_tail,
            "stdout_noise_lines": self.stdout_noise_lines,
        }


def _optional_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def resolve_command(command: Sequence[str]) -> list[str]:
    """Make ``command`` runnable on this platform.

    Appends a Windows shim extension when one is required and absent. Raises
    :class:`McpProbeError` when nothing resolvable is on ``PATH``, which is the
    single most common authoring mistake (a typo'd package name looks exactly
    like a hung server otherwise).
    """
    if not command:
        raise McpProbeError("empty command")
    if isinstance(command, str):
        # A string here is the single most likely authoring mistake, and it is a
        # dangerous one to pass through: iterating "npx -y pkg" yields
        # ['n','p','x',' ','-','y',...], so the probe would quietly try to run a
        # binary called "n" and report a nonsensical PATH error instead of the
        # real mistake.
        raise McpProbeError(
            "command must be an array of strings, not a string; "
            'use ["npx", "-y", "package"]'
        )
    parts = list(command)
    for index, part in enumerate(parts):
        if not isinstance(part, str) or not part.strip():
            raise McpProbeError(
                f"command[{index}] must be a non-empty string, got {part!r}"
            )
    executable = parts[0]
    # `os.altsep` matters on Windows: a forward-slash absolute path such as
    # "/opt/tool" contains no os.sep, so testing os.sep alone would fall through
    # to the PATH branch and blame the environment for a bad path.
    separators = (os.sep, os.altsep) if os.altsep else (os.sep,)
    if Path(executable).is_absolute() or any(sep in executable for sep in separators):
        candidate = Path(executable)
        if candidate.suffix:
            if candidate.exists():
                return parts
        else:
            for suffix in (*_SHIM_SUFFIXES, ""):
                if Path(f"{executable}{suffix}").exists():
                    parts[0] = f"{executable}{suffix}"
                    return parts
        raise McpProbeError(f"executable not found: {executable}")

    located = shutil.which(executable)
    if located is None:
        for suffix in _SHIM_SUFFIXES:
            if shutil.which(f"{executable}{suffix}") is not None:
                parts[0] = f"{executable}{suffix}"
                break
        else:
            raise McpProbeError(f"not on PATH: {executable}")
    else:
        # which() succeeds for "npx" by locating npx.cmd, but the name that gets
        # handed to CreateProcess must be the resolved path: a bare "npx" fails
        # with WinError 2 because CreateProcess will not run a shim. Rewriting
        # to the located path is what makes the PATH branch work at all on
        # Windows, and it is a no-op on POSIX.
        parts[0] = located
    return parts


class _LinePump(threading.Thread):
    """Drain one pipe into a queue, forever, so the child never blocks on write.

    The alternative — reading a pipe only when we expect a reply — deadlocks the
    moment a server logs more than a pipe buffer's worth (64 KiB on Windows)
    before answering. A server is allowed to be verbose, so both pipes get a
    dedicated pump for the process lifetime.
    """

    def __init__(self, stream: Any, sink: queue.Queue[str | None]) -> None:
        super().__init__(daemon=True)
        self._stream = stream
        self._sink = sink

    def run(self) -> None:
        try:
            for line in self._stream:
                self._sink.put(line)
        except (ValueError, OSError):
            # Pipe closed underneath us during teardown; expected.
            pass
        finally:
            # None is the EOF sentinel, and it must be None: "" is a legal
            # blank line that the reader skips, so an empty-string sentinel
            # would be silently discarded and a crashed server would look
            # exactly like a server that accepts input and never replies.
            self._sink.put(None)


class McpClient:
    """A minimal MCP stdio client, scoped to probing one server."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        env: dict[str, str] | None = None,
        cwd: str | os.PathLike[str] | None = None,
    ) -> None:
        self.command = resolve_command(command)
        self._env_overlay = dict(env or {})
        self._cwd = str(cwd) if cwd is not None else None
        self._proc: subprocess.Popen[str] | None = None
        self._responses: queue.Queue[str | None] = queue.Queue()
        self._stderr: queue.Queue[str | None] = queue.Queue()
        self._noise = 0
        self._pumps: list[_LinePump] = []
        self._next_id = 0

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _child_env(self) -> dict[str, str]:
        # A server inherits the parent environment; we only overlay declared
        # values. PATH is required or npx cannot find anything.
        env = dict(os.environ)
        env.update(self._env_overlay)
        if os.name == "nt" and "PATHEXT" not in env:
            env["PATHEXT"] = ".COM;.EXE;.BAT;.CMD"
        return env

    def start(self) -> None:
        try:
            self._proc = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self._cwd,
                env=self._child_env(),
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as exc:
            raise McpProbeError(f"could not start {self.command[0]}: {exc}") from exc

        assert self._proc.stdout is not None
        assert self._proc.stderr is not None
        self._pumps = [
            _LinePump(self._proc.stdout, self._responses),
            _LinePump(self._proc.stderr, self._stderr),
        ]
        for pump in self._pumps:
            pump.start()

    def close(self) -> None:
        proc = self._proc
        if proc is None:
            return
        try:
            if proc.stdin is not None and not proc.stdin.closed:
                proc.stdin.close()
        except OSError:
            pass
        if proc.poll() is None:
            self._terminate(proc)
        for pump in self._pumps:
            pump.join(timeout=2.0)
        for stream in (proc.stdout, proc.stderr, proc.stdin):
            if stream is not None and not stream.closed:
                try:
                    stream.close()
                except OSError:
                    pass
        self._proc = None

    @staticmethod
    def _terminate(proc: subprocess.Popen[str]) -> None:
        """Kill the whole tree.

        ``npx`` spawns node, which spawns the server. Killing only the direct
        child leaves the grandchild holding the stdio pipes, and the next
        ``opencode`` start then fails on an already-bound pipe or an orphaned
        port. Windows has no ``process_group`` semantics for this, so taskkill is
        the mechanism; POSIX gets start_new_session plus a group kill.
        """
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    capture_output=True,
                    timeout=15,
                    check=False,
                )
            else:
                import signal

                os.killpg(proc.pid, signal.SIGKILL)
        except (OSError, subprocess.SubprocessError):
            proc.kill()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    def _send(self, payload: dict[str, Any]) -> None:
        proc = self._proc
        if proc is None or proc.stdin is None:
            raise McpProbeError("client not started")
        if proc.poll() is not None:
            raise McpProbeError(
                f"server exited with code {proc.returncode} before replying"
            )
        try:
            proc.stdin.write(json.dumps(payload) + "\n")
            proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise McpProbeError(f"server closed stdin: {exc}") from exc

    def _await(self, request_id: int, deadline: float) -> dict[str, Any]:
        """Return the response for ``request_id``, tolerating unrelated traffic.

        Servers may emit notifications and log lines before answering, and some
        emit requests of their own (sampling, roots). Anything that is not our
        correlated response is dropped rather than treated as failure.
        """
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise McpProbeError(f"timed out waiting for response id={request_id}")
            try:
                line = self._responses.get(timeout=remaining)
            except queue.Empty:
                continue
            if line is None:
                raise McpProbeError(
                    f"server exited (code {self._exit_code()}) without replying"
                )

            text = line.strip()
            if not text:
                continue
            try:
                message = json.loads(text)
            except json.JSONDecodeError:
                # Banner, progress bar, or a stray write to stdout. Counted so
                # the report can flag a server that is polluting the channel.
                self._noise += 1
                continue
            if not isinstance(message, dict):
                self._noise += 1
                continue
            if message.get("id") != request_id:
                continue
            if "error" in message:
                error = message["error"]
                if isinstance(error, dict):
                    detail = error.get("message") or json.dumps(error)
                else:
                    detail = str(error)
                raise McpProbeError(f"server returned an error: {detail}")
            result = message.get("result")
            if not isinstance(result, dict):
                raise McpProbeError("response had no result object")
            return result

    @property
    def noise_lines(self) -> int:
        """Non-JSON lines seen on stdout so far (banners, progress output)."""
        return self._noise

    def _exit_code(self, grace: float = 3.0) -> str:
        """Best-effort exit code for a server that stopped replying.

        EOF on stdout does not imply the child has been reaped — on Windows the
        last write handle closes a moment before the process object is
        collectable, so a bare ``poll()`` reports "still running" for a process
        that is demonstrably gone. EOF has already told us the pipe is closed, so
        a short bounded wait cannot hang, and it is the difference between
        "exited with code 3" and "exited with code None" in the report.
        """
        proc = self._proc
        if proc is None:
            return "unknown"
        code = proc.poll()
        if code is not None:
            return str(code)
        try:
            code = proc.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            return "unknown (still running)"
        return str(code)

    def request(
        self, method: str, params: dict[str, Any] | None = None, *, timeout: float
    ) -> dict[str, Any]:
        self._next_id += 1
        request_id = self._next_id
        self._send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params if params is not None else {},
            }
        )
        return self._await(request_id, time.monotonic() + timeout)

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

    def stderr_tail(self, limit: int = 5, width: int = 200) -> str:
        """Last few stderr lines, for diagnosing a failed probe.

        Bounded on both count and width: stderr from a failing ``npx`` routinely
        includes an absolute path and a stack trace, and an unbounded dump is
        how a probe turns into a log-flooding CI job.
        """
        collected: list[str] = []
        while True:
            try:
                line = self._stderr.get_nowait()
            except queue.Empty:
                break
            if line is None:
                break
            if line.strip():
                collected.append(line.rstrip())
        return "\n".join(collected[-limit:])[-width * limit :]


def probe(
    name: str,
    command: Sequence[str],
    *,
    env: dict[str, str] | None = None,
    cwd: str | os.PathLike[str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> ProbeResult:
    """Handshake with one MCP server and report what it exposes.

    Never raises for a server-side problem — a server that fails is a result, not
    an exception, so a sweep of twenty servers reports twenty verdicts instead of
    stopping at the first bad one. :class:`McpProbeError` is reserved for a
    malformed ``command``.
    """
    result = ProbeResult(name=name, command=list(command), ok=False)
    started = time.monotonic()
    client = McpClient(command, env=env, cwd=cwd)
    try:
        client.start()
    except McpProbeError as exc:
        result.error = str(exc)
        result.elapsed_s = time.monotonic() - started
        return result

    try:
        init = client.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"roots": {"listChanged": False}},
                "clientInfo": {"name": "mcp_health", "version": PROTOCOL_VERSION},
            },
            timeout=timeout,
        )
        # Required by the spec before the server will honour other requests.
        client.notify("notifications/initialized")

        info = init.get("serverInfo")
        if isinstance(info, dict):
            result.server_name = str(info.get("name", ""))
            result.server_version = str(info.get("version", ""))
        result.protocol_version = str(init.get("protocolVersion", ""))

        listed = client.request("tools/list", {}, timeout=timeout)
        tools = listed.get("tools")
        result.tools = [
            ToolInfo.from_payload(entry)
            for entry in (tools if isinstance(tools, list) else [])
            if isinstance(entry, dict)
        ]
        result.tool_count = len(result.tools)
        result.ok = True
    except McpProbeError as exc:
        result.error = str(exc)
    except Exception as exc:  # noqa: BLE001 - see below
        # Deliberately broad. A sweep is only useful if it reports every server,
        # so an unforeseen failure in one must be recorded as that server's
        # verdict rather than aborting the remaining probes. Control-flow
        # exceptions (KeyboardInterrupt, SystemExit) derive from BaseException
        # and still propagate, so an interrupt is never swallowed.
        result.error = f"unexpected {type(exc).__name__}: {exc}"
    finally:
        result.elapsed_s = time.monotonic() - started
        result.stderr_tail = client.stderr_tail()
        result.stdout_noise_lines = client.noise_lines
        client.close()

    return result


def probe_all(
    servers: dict[str, dict[str, Any]], *, timeout: float = DEFAULT_TIMEOUT
) -> list[ProbeResult]:
    """Probe every server in an opencode ``mcp`` block.

    Entries that cannot start at all are reported alongside the rest rather than
    aborting the sweep, because the interesting output is the comparison.
    """
    results: list[ProbeResult] = []
    for name, spec in servers.items():
        if not isinstance(spec, dict):
            results.append(
                ProbeResult(
                    name=str(name),
                    command=[],
                    ok=False,
                    error=f"entry must be an object, got {type(spec).__name__}",
                )
            )
            continue
        if not spec.get("enabled", True):
            continue
        command = spec.get("command")
        if not isinstance(command, list) or not all(
            isinstance(part, str) for part in command
        ):
            results.append(
                ProbeResult(
                    name=name,
                    command=[],
                    ok=False,
                    error="missing or malformed command array",
                )
            )
            continue
        results.append(
            probe(
                name,
                command,
                env=spec.get("environment") or {},
                cwd=spec.get("cwd"),
                timeout=timeout,
            )
        )
    return results


def format_report(results: Iterable[ProbeResult]) -> str:
    """Human-readable table, one line per server plus its tool roster."""
    lines: list[str] = []
    for result in results:
        mark = "PASS" if result.ok else "FAIL"
        if result.ok:
            summary = (
                f"{result.tool_count} tools "
                f"[{result.server_name or '?'} "
                f"{result.server_version or '?'} "
                f"proto {result.protocol_version or '?'}] "
                f"{result.elapsed_s:.1f}s"
            )
        else:
            summary = result.error
        lines.append(f"{mark}  {result.name:<18} {summary}")
        if result.tools:
            lines.append(f"      tools: {', '.join(result.tool_names)}")
        unannotated = result.unannotated_tools()
        if unannotated:
            lines.append(
                f"      no readOnlyHint: {len(unannotated)} "
                f"({', '.join(unannotated[:6])}"
                f"{'...' if len(unannotated) > 6 else ''})"
            )
        if result.stdout_noise_lines:
            lines.append(
                f"      note: {result.stdout_noise_lines} non-JSON stdout line(s) "
                "skipped during handshake"
            )
        if result.stderr_tail:
            lines.append(f"      stderr: {result.stderr_tail}")
    return "\n".join(lines)


def strip_jsonc(raw: str) -> str:
    """Remove JSONC comments, leaving valid JSON.

    Comment text is replaced by whitespace of the same line structure so that
    line numbers in any resulting :class:`json.JSONDecodeError` still point at
    the right line of the *original* config — otherwise a malformed config
    reports an error at a line that does not exist in the file the operator is
    looking at.

    Scanning is string-aware: ``"https://example.com"`` and a regex-looking
    value must survive, and a quote inside a comment must not open a string that
    swallows the rest of the file.
    """
    out: list[str] = []
    index = 0
    length = len(raw)
    in_string = False
    escaped = False

    while index < length:
        char = raw[index]
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            out.append(char)
            index += 1
            continue

        if char == "/" and index + 1 < length:
            following = raw[index + 1]
            if following == "/":
                end = raw.find("\n", index)
                end = length if end == -1 else end
                out.append(" ")
                index = end
                continue
            if following == "*":
                end = raw.find("*/", index + 2)
                end = length if end == -1 else end + 2
                # Keep the newlines a multi-line comment spanned.
                out.append("".join("\n" if c == "\n" else " " for c in raw[index:end]))
                index = end
                continue

        out.append(char)
        index += 1

    return "".join(out)


def drop_trailing_commas(text: str) -> str:
    """Remove a comma that sits immediately before ``}`` or ``]``.

    opencode's own parser accepts trailing commas, so a config it loads without
    complaint would make this tool fail. Tolerating them keeps the two parsers
    in agreement instead of rejecting a file the agent is actively using.
    String-aware, for the same reason as :func:`strip_jsonc`.
    """
    chars = list(text)
    length = len(chars)
    in_string = False
    escaped = False
    index = 0

    while index < length:
        char = chars[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            index += 1
            continue

        if char == ",":
            probe = index + 1
            while probe < length and chars[probe].isspace():
                probe += 1
            if probe < length and chars[probe] in "}]":
                chars[index] = " "
                index += 1
                continue

        index += 1

    return "".join(chars)


def load_jsonc(raw: str) -> dict[str, Any]:
    """Parse a ``.json``/``.jsonc`` config into a dict.

    Raises :class:`McpProbeError` rather than :class:`json.JSONDecodeError` so a
    caller can treat every configuration problem as one failure mode.
    """
    try:
        document = json.loads(drop_trailing_commas(strip_jsonc(raw)))
    except json.JSONDecodeError as exc:
        raise McpProbeError(f"config is not valid JSON/JSONC: {exc}") from exc
    if not isinstance(document, dict):
        raise McpProbeError("config must be a JSON object at the top level")
    return document


if __name__ == "__main__":  # pragma: no cover - operator entry point
    import argparse

    parser = argparse.ArgumentParser(
        description="Handshake-probe MCP servers from an opencode config."
    )
    parser.add_argument("config", help="path to opencode.jsonc / opencode.json")
    parser.add_argument("--only", help="comma-separated server names to probe")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    try:
        raw = Path(args.config).read_text(encoding="utf-8")
    except OSError as exc:
        parser.error(f"cannot read {args.config}: {exc}")
    try:
        document = load_jsonc(raw)
    except McpProbeError as exc:
        parser.error(str(exc))

    servers = document.get("mcp") or {}
    if not isinstance(servers, dict):
        parser.error("'mcp' must be an object keyed by server name")
    if args.only:
        wanted = {name.strip() for name in args.only.split(",")}
        servers = {k: v for k, v in servers.items() if k in wanted}

    results = probe_all(servers, timeout=args.timeout)
    if args.json:
        print(json.dumps([result.to_dict() for result in results], indent=2))
    else:
        print(format_report(results))
    raise SystemExit(0 if all(result.ok for result in results) else 1)
