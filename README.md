markbase-mcp
MCP server companion for MarkBase.

One library. One MCP server. Every AI coding tool shares the same brain.

Gives Claude Code, Codex CLI, and Gemini CLI shared, live access to your personal MarkBase knowledge library. Search what you already know, save discoveries mid-session, inject project context automatically, and build your library without leaving the terminal.
This repo does not modify MarkBase. It is a thin companion layer that talks to a running MarkBase instance over its existing HTTP API.

Prerequisites

Python 3.10+
MarkBase must be running (markbase repo)
pip install -r requirements.txt


Setup

Clone or place this repo wherever you keep local companion tools
Install dependencies:

bashpip install -r requirements.txt

Start the MCP server:

bash./start-mcp.sh

Configure your CLI tool using one of the provided config examples:

Claude Code: config-examples/claude_code.json
Codex CLI: config-examples/codex.json
Gemini CLI: config-examples/gemini.json



If your MCP client does not expose workspace roots to the server, set a stable project override in the MCP config:
json{
  "env": {
    "MARKBASE_URL": "http://localhost:8733",
    "MARKBASE_PROJECT": "my-project"
  }
}

Tools
search_knowledge(query: str)
Search your library before starting a task. Surfaces transcripts, notes, and documents matching your query. Use this to answer "what do I already know about X?" before writing a line of code.
save_note(title: str, content: str, tags: list[str] = [])
Save a hand-authored Markdown note to the library. Use this to capture research findings, code explanations, snippets, or links discovered mid-session.
read_item(path: str)
Read the full Markdown content and metadata for a specific library item. Use this after search_knowledge to read the complete text of a result.
list_library(source_type: str = None, channel: str = None)
Browse the full library index, optionally filtered by source type (youtube_video, doc, note) or channel handle.
ingest_url(url: str)
Submit a YouTube video, channel, or web page to the MarkBase ingestion queue. Use this to add new content to your library without leaving the terminal.
resolve_project(project_name: str = None, cwd: str = None)
Resolve the active project from an explicit name, environment override, or MCP workspace roots.
tag_item_for_project(path: str, project_name: str = None, cwd: str = None)
Apply the resolved project tag to an existing library item.
project_context(project_name: str = None, cwd: str = None, limit: int = 5, include_content: bool = True)
Return one bundled context payload for the resolved project. Use this at the start of a session to load everything relevant to what you are working on.

Resources
markbase://project-context/current
JSON bundle for the current project, resolved automatically from MCP client workspace roots.
markbase://project-context/{project_name}
JSON bundle for a named project.

Prompts
bootstrap_project_context(project_name: str = None)
Returns an agent-ready briefing that includes the full bundled MarkBase project context. Call this at the start of any session to hit the ground running.

How project detection works
The server resolves the active project in this order:

Explicit project_name argument
Environment overrides (MARKBASE_PROJECT or PROJECT_NAME)
MCP client workspace roots via roots/list
Fallback root paths (MARKBASE_PROJECT_ROOT, PROJECT_ROOT, INIT_CWD, PWD)

The canonical project tag format is #project-name.

Workflow examples
Before starting a task:
pythonproject_context()
# or read markbase://project-context/current
# or use bootstrap_project_context()
Injects all items tagged with your current project as context before you start.
Search for something specific:
pythonsearch_knowledge("proxmox PCIe passthrough")
# surfaces your CraftComputing transcripts instantly
Tag an item for the current project:
pythontag_item_for_project("notes/til-yt-dlp")
Save a discovery mid-session:
pythonsave_note("TIL", "yt-dlp flat playlist flag...", ["yt-dlp", "youtube", "#markbase"])
Build your library without leaving the terminal:
pythoningest_url("https://youtube.com/@craftcomputing")

How it works
MarkBase stores everything as plain Markdown and JSON on disk. markbase-mcp wraps the MarkBase HTTP API and exposes it as MCP tools, resources, and prompts. Project awareness lives entirely in this layer, not in a second index or database.
When you call project_context(), the server resolves your active project, queries GET /api/search filtered by the project tag, and bundles the results into a single payload your agent can reason over immediately.

Roadmap
Phase 3 (complete)
Project tags are first-class. The MCP server resolves the active project automatically. Multiple tagged items bundle into one context payload. The same context is available as MCP resources and a bootstrap prompt. Shared MarkBase works by pointing multiple machines or users at the same instance.
Phase 4 (planned)
Shared team knowledge base. Point multiple machines or teammates at the same MarkBase library. One library, shared institutional memory for help desk KBs, engineering team wikis, and onboarding docs.

License
MIT
