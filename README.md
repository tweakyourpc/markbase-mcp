![MarkBase hero](docs/markbase.png)

# markbase-mcp
MCP server companion for MarkBase, gives Claude Code, Codex CLI, and Gemini CLI shared access to your personal knowledge library.

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

## Tools
- `search_knowledge(query: str)`
  - Use when you want to answer "what do I already know about X?" before starting work.
- `save_note(title: str, content: str, tags: list[str] = [])`
  - Use to save research findings, explanations, snippets, or links discovered mid-session.
- `read_item(path: str)`
  - Use after search to read the full markdown content of a specific item.
- `list_library(source_type: str = None, channel: str = None)`
  - Use to browse what is already in the library before searching.
- `ingest_url(url: str)`
  - Use to add a YouTube video, channel, or web page to MarkBase without leaving the terminal.
- `resolve_project(project_name: str = None, cwd: str = None)`
  - Use to resolve the active project from an explicit name, environment override, or MCP workspace roots.
- `tag_item_for_project(path: str, project_name: str = None, cwd: str = None)`
  - Use to apply the current project tag to an existing library item.
- `project_context(project_name: str = None, cwd: str = None, limit: int = 5, include_content: bool = True)`
  - Use at the start of a session to load everything tagged for your current project as a single context bundle.

## Resources
- `markbase://project-context/current`
  - JSON bundle for the current project, resolved from MCP client workspace roots.
- `markbase://project-context/{project_name}`
  - JSON bundle for a named project.

## Prompts
- `bootstrap_project_context(project_name: str = None)`
  - Returns an agent-ready briefing with the full bundled project context. Call this at the start of any session.

## How it works
One MarkBase library plus one MCP server means Claude Code, Codex CLI, and Gemini CLI all share the same brain. This repo does not modify MarkBase. It is a thin companion layer that talks to an already-running MarkBase instance over its existing HTTP API.

## How project detection works
The server resolves the active project in this order:
1. Explicit `project_name` argument
2. Environment overrides (`MARKBASE_PROJECT` or `PROJECT_NAME`)
3. MCP client workspace roots via `roots/list`
4. Fallback paths (`MARKBASE_PROJECT_ROOT`, `PROJECT_ROOT`, `INIT_CWD`, `PWD`)

The canonical project tag format is `#project-name`.

## Workflow examples
- Before starting a task:
  - `project_context()` loads everything tagged for your current project automatically.
- Search for something specific:
  - `search_knowledge("proxmox PCIe passthrough")` surfaces matching transcripts and notes instantly.
- Tag an item for the current project:
  - `tag_item_for_project("notes/til-yt-dlp")`
- Mid-session discovery:
  - `save_note("TIL", "yt-dlp flat playlist flag...", ["yt-dlp", "youtube", "#markbase"])`
- Building the library without leaving the terminal:
  - `ingest_url("https://youtube.com/@handle")` submits the channel to the ingestion queue.
