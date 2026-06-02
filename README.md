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
  - Use when you want to answer “what do I already know about X?” before starting work.
- `save_note(title: str, content: str, tags: list[str] = [])`
  - Use to save research findings, explanations, snippets, or links discovered mid-session.
- `read_item(path: str)`
  - Use after search to read the full markdown content of a specific item.
- `list_library(source_type: str = None, channel: str = None)`
  - Use to browse what is already in the library before searching.
- `ingest_url(url: str)`
  - Use to add a YouTube video, channel, or web page to MarkBase without leaving the terminal.

## How it works

One MarkBase library plus one MCP server means Claude Code, Codex CLI, and Gemini CLI all share the same brain. This repo does not modify MarkBase. It is a thin companion layer that talks to an already-running MarkBase instance over its existing HTTP API.

## Workflow examples

- Before starting a task:
  - `search_knowledge("proxmox PCIe passthrough")`
  - This can surface your existing CraftComputing transcripts before you start solving the problem again.

- Mid-session discovery:
  - `save_note("TIL", "yt-dlp flat playlist flag...", ["yt-dlp", "youtube"])`
  - This saves the discovery instantly into MarkBase.

- Building the library without leaving the terminal:
  - `ingest_url("https://youtube.com/@craftcomputing")`
  - This submits the channel to MarkBase’s ingestion queue.

## Roadmap

This is Phase 2 of MarkBase, the personal RAG layer. Phase 3 will add tag-based context bundles and project-aware auto-injection of relevant library items at session start.
