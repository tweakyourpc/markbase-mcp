import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import httpx
from mcp.server.fastmcp import Context, FastMCP

DEFAULT_MARKBASE_URL = "http://localhost:8733"
CONFIG_ENV_PATH = Path.home() / ".config" / "markbase" / "markbase.env"
PROJECT_ENV_VARS = (
    "MARKBASE_PROJECT",
    "PROJECT_NAME",
    "CODEX_PROJECT_NAME",
    "CLAUDE_PROJECT_NAME",
)
PROJECT_ROOT_ENV_VARS = (
    "MARKBASE_PROJECT_ROOT",
    "PROJECT_ROOT",
    "CODEX_PROJECT_ROOT",
    "CLAUDE_PROJECT_DIR",
    "INIT_CWD",
    "PWD",
)


def _load_markbase_url() -> str:
    config_url = ""
    if CONFIG_ENV_PATH.exists():
        for line in CONFIG_ENV_PATH.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip() == "MARKBASE_URL":
                config_url = value.strip().strip('"').strip("'")
                break
    return os.getenv("MARKBASE_URL") or config_url or DEFAULT_MARKBASE_URL


MARKBASE_URL = _load_markbase_url().rstrip("/")
mcp = FastMCP("markbase")
NOTE_CREATED_VIA = "markbase-mcp"
NOTE_DEFAULT_AUTHORSHIP = "agent-authored"
NOTE_DEFAULT_AI_PROCESSING = "none"


async def _request(method: str, path: str, **kwargs: Any) -> Any:
    url = f"{MARKBASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        return {
            "error": (
                f"MarkBase is unreachable or returned an error at {MARKBASE_URL}. "
                f"Details: {exc}"
            )
        }


def _humanize_error(payload: Any) -> Any:
    if isinstance(payload, dict) and "error" in payload:
        return payload["error"]
    return payload


def _yaml_scalar(value: str) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def _content_with_note_provenance(
    content: str,
    authorship: str = NOTE_DEFAULT_AUTHORSHIP,
    ai_processing: str = NOTE_DEFAULT_AI_PROCESSING,
) -> str:
    body = content or ""
    resolved_authorship = authorship or NOTE_DEFAULT_AUTHORSHIP
    resolved_ai_processing = ai_processing or NOTE_DEFAULT_AI_PROCESSING
    front_matter = "\n".join(
        [
            "---",
            f"created_via: {_yaml_scalar(NOTE_CREATED_VIA)}",
            f"authorship: {_yaml_scalar(resolved_authorship)}",
            f"ai_processing: {_yaml_scalar(resolved_ai_processing)}",
            "---",
            "",
        ]
    )
    return f"{front_matter}{body}"


def _save_note_payload(
    title: str,
    content: str,
    tags: list[str] | None = None,
    authorship: str = NOTE_DEFAULT_AUTHORSHIP,
    ai_processing: str = NOTE_DEFAULT_AI_PROCESSING,
) -> dict[str, Any]:
    resolved_authorship = authorship or NOTE_DEFAULT_AUTHORSHIP
    resolved_ai_processing = ai_processing or NOTE_DEFAULT_AI_PROCESSING
    return {
        "title": title,
        "content": _content_with_note_provenance(
            content,
            authorship=resolved_authorship,
            ai_processing=resolved_ai_processing,
        ),
        "tags": tags or [],
        "created_via": NOTE_CREATED_VIA,
        "authorship": resolved_authorship,
        "ai_processing": resolved_ai_processing,
    }


def _normalize_project_name(value: str) -> str:
    value = re.sub(r"^[#\s]+", "", (value or "").strip().lower())
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value


def _candidate_root_paths(cwd: str | None = None) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(path_value: str | None, source: str) -> None:
        raw = (path_value or "").strip()
        if not raw:
            return
        try:
            resolved = str(Path(raw).expanduser().resolve())
        except OSError:
            return
        if resolved in seen:
            return
        seen.add(resolved)
        candidates.append((resolved, source))

    add(cwd, "argument:cwd")
    for key in PROJECT_ROOT_ENV_VARS:
        add(os.getenv(key), f"env:{key}")
    return candidates


async def _roots_from_context(ctx: Context | None) -> list[dict[str, str | None]]:
    if ctx is None:
        return []
    try:
        result = await ctx.request_context.session.list_roots()
    except Exception:
        return []

    roots: list[dict[str, str | None]] = []
    for root in result.roots:
        uri = str(root.uri)
        parsed = urlparse(uri)
        if parsed.scheme != "file":
            continue
        path = unquote(parsed.path or "")
        if not path:
            continue
        try:
            resolved = str(Path(path).expanduser().resolve())
        except OSError:
            continue
        roots.append(
            {
                "uri": uri,
                "path": resolved,
                "name": root.name,
            }
        )
    return roots


async def _resolve_project_context(
    project_name: str | None = None,
    cwd: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    candidate_name = (project_name or "").strip()
    source = "argument:project_name"

    if not candidate_name:
        for key in PROJECT_ENV_VARS:
            value = (os.getenv(key) or "").strip()
            if value:
                candidate_name = value
                source = f"env:{key}"
                break

    roots = await _roots_from_context(ctx)

    root_path = None
    root_source = None
    if roots:
        root_path = roots[0]["path"]
        root_source = "mcp:roots"
    else:
        candidate_roots = _candidate_root_paths(cwd=cwd)
        if candidate_roots:
            root_path, root_source = candidate_roots[0]

    if not candidate_name and root_path:
        candidate_name = Path(root_path).name
        source = root_source or "root"

    normalized = _normalize_project_name(candidate_name)
    return {
        "project_name": candidate_name,
        "normalized_project_name": normalized,
        "project_tag": f"#{normalized}" if normalized else "",
        "source": source if normalized else "unresolved",
        "project_root": root_path,
        "project_root_source": root_source,
        "roots": roots,
    }


def _score_project_item(item: dict[str, Any], project_tag: str) -> tuple[int, str]:
    tags = [str(tag).strip().lower() for tag in item.get("tags") or []]
    score = 0
    if project_tag and project_tag.lower() in tags:
        score += 3
    if item.get("source_type") == "note":
        score += 1
    recency = str(item.get("date_ingested") or "")
    return (score, recency)


async def _library_items() -> list[dict[str, Any]]:
    payload = await _request("GET", "/api/library")
    payload = _humanize_error(payload)
    if isinstance(payload, str):
        raise RuntimeError(payload)
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected MarkBase library payload")
    return [item for item in payload.get("items", []) if isinstance(item, dict)]


async def _read_project_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bundled: list[dict[str, Any]] = []
    for item in items:
        path = item.get("path")
        if not isinstance(path, str) or not path:
            continue
        payload = await _request("GET", f"/api/item/{path}")
        payload = _humanize_error(payload)
        if isinstance(payload, dict) and "metadata" in payload:
            bundled.append(payload)
    return bundled


async def _project_context_payload(
    project_name: str | None = None,
    cwd: str | None = None,
    limit: int = 5,
    include_content: bool = True,
    ctx: Context | None = None,
) -> dict[str, Any]:
    context = await _resolve_project_context(project_name=project_name, cwd=cwd, ctx=ctx)
    project_tag = context["project_tag"]
    if not project_tag:
        return {
            "error": (
                "Could not resolve a project tag. Pass project_name explicitly, set "
                "MARKBASE_PROJECT / PROJECT_NAME, or use a client that exposes workspace roots."
            )
        }

    try:
        items = await _library_items()
    except RuntimeError as exc:
        return {"error": str(exc)}

    matching = [
        item
        for item in items
        if project_tag.lower() in {str(tag).strip().lower() for tag in item.get("tags") or []}
    ]
    matching.sort(key=lambda item: _score_project_item(item, project_tag), reverse=True)
    selected = matching[: max(1, min(limit, 20))]

    response: dict[str, Any] = {
        "project": context,
        "total_matches": len(matching),
        "items": selected,
    }
    if include_content:
        response["bundle"] = await _read_project_items(selected)
    return response


@mcp.tool()
async def search_knowledge(query: str) -> Any:
    """Search MarkBase before starting a task to see what you already know about a topic."""

    payload = await _request("GET", "/api/search", params={"q": query})
    return _humanize_error(payload)


@mcp.tool()
async def save_note(
    title: str,
    content: str,
    tags: list[str] = [],
    authorship: str = NOTE_DEFAULT_AUTHORSHIP,
) -> Any:
    """Save an agent-authored markdown note to the MarkBase library."""

    payload = await _request(
        "POST",
        "/api/note",
        json=_save_note_payload(title=title, content=content, tags=tags, authorship=authorship),
    )
    return _humanize_error(payload)


@mcp.tool()
async def read_item(path: str) -> Any:
    """Read the full markdown content and metadata for a specific MarkBase item."""

    payload = await _request("GET", f"/api/item/{path}")
    return _humanize_error(payload)


@mcp.tool()
async def list_library(source_type: str | None = None, channel: str | None = None) -> Any:
    """Browse the full MarkBase library index, optionally filtered by source type or channel."""

    params: dict[str, str] = {}
    if source_type:
        params["source_type"] = source_type
    if channel:
        params["channel"] = channel
    payload = await _request("GET", "/api/library", params=params)
    return _humanize_error(payload)


@mcp.tool()
async def ingest_url(url: str) -> Any:
    """Submit a YouTube or web URL to the MarkBase ingestion queue."""

    payload = await _request("POST", "/api/ingest", json={"url": url})
    return _humanize_error(payload)


@mcp.tool()
async def resolve_project(
    project_name: str | None = None,
    cwd: str | None = None,
    ctx: Context | None = None,
) -> Any:
    """Resolve the current project name from an explicit value, env override, or client workspace roots."""

    context = await _resolve_project_context(project_name=project_name, cwd=cwd, ctx=ctx)
    if not context["project_tag"]:
        return {
            "error": (
                "Could not resolve a project name. Pass project_name explicitly, set "
                "MARKBASE_PROJECT / PROJECT_NAME, or use a client that exposes workspace roots."
            )
        }
    return context


@mcp.tool()
async def tag_item_for_project(
    path: str,
    project_name: str | None = None,
    cwd: str | None = None,
    ctx: Context | None = None,
) -> Any:
    """Apply the resolved project tag (for example #markbase) to a MarkBase item."""

    context = await _resolve_project_context(project_name=project_name, cwd=cwd, ctx=ctx)
    project_tag = context["project_tag"]
    if not project_tag:
        return {
            "error": (
                "Could not resolve a project tag. Pass project_name explicitly, set "
                "MARKBASE_PROJECT / PROJECT_NAME, or use a client that exposes workspace roots."
            )
        }

    payload = await _request("POST", "/api/tag", json={"path": path, "add": project_tag})
    payload = _humanize_error(payload)
    if isinstance(payload, dict):
        payload["project"] = context
    return payload


@mcp.tool()
async def project_context(
    project_name: str | None = None,
    cwd: str | None = None,
    limit: int = 5,
    include_content: bool = True,
    ctx: Context | None = None,
) -> Any:
    """Bundle the most relevant library items for the current project into one MCP response."""

    return await _project_context_payload(
        project_name=project_name,
        cwd=cwd,
        limit=limit,
        include_content=include_content,
        ctx=ctx,
    )


@mcp.resource(
    "markbase://project-context/current",
    name="current_project_context",
    title="Current Project Context",
    description="Bundled MarkBase context for the current MCP client project.",
    mime_type="application/json",
)
async def current_project_context_resource(ctx: Context) -> str:
    payload = await _project_context_payload(limit=8, include_content=True, ctx=ctx)
    return json.dumps(payload, indent=2, ensure_ascii=False)


@mcp.resource(
    "markbase://project-context/{project_name}",
    name="named_project_context",
    title="Named Project Context",
    description="Bundled MarkBase context for a specific project tag.",
    mime_type="application/json",
)
async def named_project_context_resource(project_name: str, ctx: Context) -> str:
    payload = await _project_context_payload(
        project_name=project_name,
        limit=8,
        include_content=True,
        ctx=ctx,
    )
    return json.dumps(payload, indent=2, ensure_ascii=False)


@mcp.prompt(
    name="bootstrap_project_context",
    title="Bootstrap Project Context",
    description="Return an agent-ready briefing for the current project using MarkBase tags and bundled items.",
)
async def bootstrap_project_context(project_name: str | None = None, ctx: Context | None = None) -> str:
    payload = await _project_context_payload(
        project_name=project_name,
        limit=8,
        include_content=True,
        ctx=ctx,
    )
    return (
        "Use this MarkBase project context as prior knowledge for the current task. "
        "Treat it as user-curated background, prefer it when relevant, and mention uncertainty if it conflicts with the codebase or newer facts.\n\n"
        f"{json.dumps(payload, indent=2, ensure_ascii=False)}"
    )


if __name__ == "__main__":
    mcp.run()
