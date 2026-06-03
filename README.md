# markbase-mcp

MCP server companion for MarkBase. It gives Claude Code, Codex CLI, and Gemini CLI shared access to your personal knowledge library, and now includes Phase 3 project-aware context.

## Prerequisites

- Python 3.10+
- MarkBase must be running
- `pip install -r requirements.txt`

## Setup

1. Clone or place this repo wherever you keep local companion tools.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the MCP server:
   ```bash
   ./start-mcp.sh
   ```
4. Configure your CLI tool using one of these files:
   - Claude Code: `config-examples/claude_code.json`
   - Codex CLI: `config-examples/codex.json`
   - Gemini CLI: `config-examples/gemini.json`

If your MCP client does not expose workspace roots to the server, set a stable project override in the MCP config:

```json
{
  "env": {
    "MARKBASE_URL": "http://localhost:8733",
    "MARKBASE_PROJECT": "markbase"
  }
}
```

## Tools

- `search_knowledge(query: str)`
  - Search MarkBase before starting a task to see what you already know about a topic.
- `save_note(title: str, content: str, tags: list[str] = [])`
  - Save a hand-authored markdown note to the MarkBase library.
- `read_item(path: str)`
  - Read the full markdown content and metadata for a specific MarkBase item.
- `list_library(source_type: str = None, channel: str = None)`
  - Browse the full MarkBase library index.
- `ingest_url(url: str)`
  - Submit a YouTube or web URL to the MarkBase ingestion queue.
- `resolve_project(project_name: str | None = None, cwd: str | None = None)`
  - Resolve the active project from an explicit name, env override, or MCP workspace roots.
- `tag_item_for_project(path: str, project_name: str | None = None, cwd: str | None = None)`
  - Apply the resolved project tag to an existing library item.
- `project_context(project_name: str | None = None, cwd: str | None = None, limit: int = 5, include_content: bool = True)`
  - Return one bundled context payload for the resolved project.

## Resources

- `markbase://project-context/current`
  - JSON bundle for the current MCP client project, using workspace roots when available.
- `markbase://project-context/{project_name}`
  - JSON bundle for a named project.

## Prompts

- `bootstrap_project_context(project_name: str | None = None)`
  - Returns an agent-ready briefing that includes the bundled MarkBase project context.

## How project detection works

The server resolves the active project in this order:

1. Explicit `project_name` argument
2. Env overrides such as `MARKBASE_PROJECT` or `PROJECT_NAME`
3. MCP client workspace roots via `roots/list`
4. Fallback root paths such as `MARKBASE_PROJECT_ROOT`, `PROJECT_ROOT`, `INIT_CWD`, or `PWD`

The canonical project tag format is `#project-name`.

## Phase 3 status

Phase 3 is implemented:

- Project tags are first-class through standard MarkBase tags such as `#markbase`, `#homelab`, or `#work`.
- The MCP server can resolve the active project automatically from client roots or explicit overrides.
- Multiple tagged items can be bundled into one context payload with `project_context(...)`.
- The same context is also exposed as MCP resources and a bootstrap prompt for clients that consume those surfaces.
- Shared MarkBase usage works by pointing multiple machines or users at the same MarkBase instance and library.

## Workflow examples

- Before starting a task:
  - `project_context()`
  - Or read `markbase://project-context/current`
  - Or use `bootstrap_project_context()`

- Tag an item for the current repo:
  - `tag_item_for_project("notes/til-yt-dlp")`

- Save a project-specific discovery:
  - `save_note("TIL", "yt-dlp flat playlist flag...", ["yt-dlp", "youtube", "#markbase"])`

- Build the library without leaving the terminal:
  - `ingest_url("https://youtube.com/@craftcomputing")`

## Notes

This repo remains a thin companion layer over MarkBase’s HTTP API. The project-aware behavior is implemented in the MCP layer, not by adding a second indexing system.
