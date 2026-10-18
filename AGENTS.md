# Coding Agent Specialization

Active MCP servers configured in this project:

- **context7** (`https://mcp.context7.com/mcp`) — Live version-correct library docs. Use when touching new APIs/frameworks to avoid hallucinated imports.
- **filesystem** (`@modelcontextprotocol/server-filesystem`) — Scoped file operations on this repo.
- **sequential-thinking** (`@modelcontextprotocol/server-sequential-thinking`) — Structured step-by-step reasoning for complex problems.
- **everything** (`@modelcontextprotocol/server-everything`) — General reference/test tools.
- **git** (`mcp-server-git`) — Repository history/diffs (disabled by default; enable with `opencode mcp connect git` when needed).
- **fetch** (`mcp-server-fetch`) — DISABLED: deprecated due to reliability issues. Use `scrapling` (scraping/extraction) + `playwright` (JS/full-page retrieval) + `context7` (library docs) instead.
- **memory** (`@modelcontextprotocol/server-memory`) — Persistent knowledge graph across sessions.
- **scrapling** (`scrapling.cli mcp`) — DISABLED: installed (`scrapling-0.5`) but `orjson` DLL blocked by App Control → `<frozen runpy>` crash on import. Library usable directly; MCP server blocked until policy/whitelist fixed.
- **github** (`@modelcontextprotocol/server-github`) — Full repo/PR/issue access (disabled; needs `GITHUB_TOKEN`).
- **playwright** (`@playwright/mcp`) — Full browser/page-level retrieval (JS-heavy pages, screenshots, DOM inspect).
- **time** (`mcp_server_time`) — Timestamps.

## Usage patterns
- Unknown API? Call `context7` first: ask for docs on the specific library/version.
- Multi-step task? Use `sequential-thinking` to plan, then execute with `filesystem`/`bash`.
- Large changes? Use `git` to inspect history/blame before editing.

Auth notes: Set `CONTEXT7_API_KEY` env var for context7 if rate limits hit (free tier works without it for light use; key improves reliability).
