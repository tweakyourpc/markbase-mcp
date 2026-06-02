from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

DEFAULT_MARKBASE_URL = "http://localhost:8733"
CONFIG_ENV_PATH = Path.home() / ".config" / "markbase" / "markbase.env"


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


@mcp.tool()
async def search_knowledge(query: str) -> Any:
    """Search MarkBase before starting a task to see what you already know about a topic."""

    payload = await _request("GET", "/api/search", params={"q": query})
    return _humanize_error(payload)


@mcp.tool()
async def save_note(title: str, content: str, tags: list[str] = []) -> Any:
    """Save a hand-authored markdown note to the MarkBase library."""

    payload = await _request(
        "POST",
        "/api/note",
        json={"title": title, "content": content, "tags": tags},
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


if __name__ == "__main__":
    mcp.run()
