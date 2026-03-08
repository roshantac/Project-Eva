"""Built-in tools (filesystem, time, skills) registered via decorator."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import ToolResult
from .tool_registry import tool

# Base directory for file operations (sandbox). All paths resolved under this.
try:
    from main_config import BASE_DIR as _BASE_DIR
    _TOOLS_BASE_DIR = Path(_BASE_DIR)
except ImportError:
    _TOOLS_BASE_DIR = Path.cwd()


def _resolve_path(path_str: str) -> Path | None:
    """Resolve path under _TOOLS_BASE_DIR; return None if escapes."""
    if not path_str or not path_str.strip():
        path = _TOOLS_BASE_DIR
    else:
        path = (_TOOLS_BASE_DIR / path_str.strip()).resolve()
    try:
        path.relative_to(_TOOLS_BASE_DIR.resolve())
    except ValueError:
        return None
    return path


@tool(
    name="get_time",
    description="Get the current UTC date and time in ISO format. Use when the user asks for the time, date, or current moment.",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
async def get_time(params: dict[str, Any]) -> ToolResult:
    now = datetime.now(timezone.utc).isoformat()
    return ToolResult(success=True, content=now)


@tool(
    name="list_dir",
    description="List entries in a directory (like ls). Use to see files and folders in a given path. Path is relative to the project base.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path (relative to project base). Default: current base.",
                "default": ".",
            },
        },
        "required": [],
    },
)
async def list_dir(params: dict[str, Any]) -> ToolResult:
    path = _resolve_path(params.get("path") or ".")
    if path is None:
        return ToolResult(success=False, error="Path is outside allowed base.")
    if not path.is_dir():
        return ToolResult(success=False, error=f"Not a directory: {path}")
    try:
        entries = await asyncio.to_thread(sorted, path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        lines = [f"{'d' if e.is_dir() else '-'}  {e.name}" for e in entries]
        return ToolResult(success=True, content="\n".join(lines) if lines else "(empty)")
    except OSError as e:
        return ToolResult(success=False, error=str(e))


@tool(
    name="search_dir",
    description="Search for files or directories whose name matches a pattern (substring or glob). Use to find files by name.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory to search in (relative to project base).",
                "default": ".",
            },
            "pattern": {
                "type": "string",
                "description": "Substring to match in names, or glob pattern (e.g. *.py).",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return.",
                "default": 50,
            },
        },
        "required": ["pattern"],
    },
)
async def search_dir(params: dict[str, Any]) -> ToolResult:
    base = _resolve_path(params.get("path") or ".")
    if base is None:
        return ToolResult(success=False, error="Path is outside allowed base.")
    if not base.is_dir():
        return ToolResult(success=False, error=f"Not a directory: {base}")
    pattern = (params.get("pattern") or "").strip()
    if not pattern:
        return ToolResult(success=False, error="pattern is required.")
    max_results = params.get("max_results") or 50
    if not isinstance(max_results, int) or max_results < 1:
        max_results = 50

    use_glob = "*" in pattern or "?" in pattern

    def _search() -> list[str]:
        out: list[str] = []
        try:
            for p in base.rglob("*"):
                if len(out) >= max_results:
                    break
                try:
                    rel = p.relative_to(base)
                except ValueError:
                    continue
                if use_glob:
                    if p.match(pattern):
                        out.append(str(rel))
                else:
                    if pattern.lower() in p.name.lower():
                        out.append(str(rel))
        except OSError:
            pass
        return out[:max_results]

    try:
        results = await asyncio.to_thread(_search)
        return ToolResult(success=True, content="\n".join(results) if results else "No matches.")
    except Exception as e:
        return ToolResult(success=False, error=str(e))


@tool(
    name="read_file",
    description="Read the contents of a file. Use when you need to see the contents of a specific file. Path is relative to the project base.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path (relative to project base)."},
            "limit": {
                "type": "integer",
                "description": "Maximum number of lines to return (optional).",
            },
        },
        "required": ["path"],
    },
)
async def read_file(params: dict[str, Any]) -> ToolResult:
    path = _resolve_path(params.get("path") or "")
    if path is None:
        return ToolResult(success=False, error="Path is outside allowed base.")
    if not path.is_file():
        return ToolResult(success=False, error=f"Not a file or not found: {path}")
    limit = params.get("limit")
    try:
        text = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="replace")
        if limit is not None and isinstance(limit, int) and limit > 0:
            lines = text.splitlines()
            text = "\n".join(lines[: limit])
            if len(lines) > limit:
                text += f"\n... ({len(lines) - limit} more lines)"
        return ToolResult(success=True, content=text)
    except OSError as e:
        return ToolResult(success=False, error=str(e))


@tool(
    name="write_file",
    description="Write content to a file. Creates the file if it does not exist; overwrites if it does. Path is relative to the project base.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path (relative to project base)."},
            "content": {"type": "string", "description": "Content to write."},
        },
        "required": ["path", "content"],
    },
)
async def write_file(params: dict[str, Any]) -> ToolResult:
    path = _resolve_path(params.get("path") or "")
    if path is None:
        return ToolResult(success=False, error="Path is outside allowed base.")
    content = params.get("content")
    if content is None:
        content = ""
    if not isinstance(content, str):
        content = str(content)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_text, content, encoding="utf-8")
        return ToolResult(success=True, content=f"Wrote {len(content)} characters to {path.name}")
    except OSError as e:
        return ToolResult(success=False, error=str(e))


# ---------------------------------------------------------------------------
# Skills tools (AgentSkills / OpenClaw / Claude Code compatible)
# ---------------------------------------------------------------------------

def _get_skills_dirs() -> list[Path]:
    """Return skill root directories: project skills/ then optional ~/.eva/skills."""
    roots: list[Path] = []
    project_skills = _TOOLS_BASE_DIR / "skills"
    if project_skills.is_dir():
        roots.append(project_skills)
    home_eva = Path.home() / ".eva" / "skills"
    if home_eva.is_dir():
        roots.append(home_eva)
    return roots


def _list_skill_names() -> list[tuple[str, str]]:
    """Return (name, path) for each skill (directory containing SKILL.md)."""
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for root in _get_skills_dirs():
        try:
            for d in root.iterdir():
                if not d.is_dir():
                    continue
                skill_md = d / "SKILL.md"
                if skill_md.is_file():
                    name = d.name
                    if name not in seen:
                        seen.add(name)
                        out.append((name, str(skill_md)))
        except OSError:
            pass
    return out


def _read_skill_content(skill_path: str) -> str | None:
    """Read SKILL.md content; return None if not found."""
    try:
        return Path(skill_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


@tool(
    name="list_skills",
    description="List available skills. Skills are instruction sets (SKILL.md) the agent can follow. Use this to discover what skills exist before reading one.",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
async def list_skills(params: dict[str, Any]) -> ToolResult:
    skills = await asyncio.to_thread(_list_skill_names)
    if not skills:
        return ToolResult(success=True, content="No skills found. Add skills in project skills/ or ~/.eva/skills/<name>/SKILL.md")
    lines = [f"- {name}" for name, _ in skills]
    return ToolResult(success=True, content="Available skills:\n" + "\n".join(lines))


@tool(
    name="read_skill",
    description="Read a skill by name. Returns the full SKILL.md content (frontmatter + instructions). Use after list_skills to load a skill and follow its instructions.",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Skill name (directory name under skills/).",
            },
        },
        "required": ["name"],
    },
)
async def read_skill(params: dict[str, Any]) -> ToolResult:
    name = (params.get("name") or "").strip()
    if not name:
        return ToolResult(success=False, error="name is required.")
    if re.search(r"[^\w\-]", name):
        return ToolResult(success=False, error="Skill name may only contain letters, numbers, hyphens, underscores.")
    skills = await asyncio.to_thread(_list_skill_names)
    path = None
    for n, p in skills:
        if n == name:
            path = p
            break
    if not path:
        return ToolResult(success=False, error=f"Skill not found: {name}. Use list_skills to see available skills.")
    content = await asyncio.to_thread(_read_skill_content, path)
    if content is None:
        return ToolResult(success=False, error=f"Could not read skill file: {path}")
    return ToolResult(success=True, content=content)
