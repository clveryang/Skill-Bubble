"""
loader.py — Dynamic skill loading and unloading.

A "loaded" skill means it's active and agents can discover it.
Loading writes the skill's path to a central manifest file that
agents read at startup (similar to a PATH for skills).

Manifest location: ~/.skill-bubble/loaded.json
Format: { "skills": [ { "name": ..., "path": ... }, ... ] }
"""

import json
import re
from pathlib import Path

from skill_bubble import registry

MANIFEST_PATH = Path.home() / ".skill-bubble" / "loaded.json"

# ── CLAUDE.md helpers ─────────────────────────────────────────────────────────

CLAUDE_MD = Path.home() / ".claude" / "CLAUDE.md"
_BLOCK_START = "<!-- skill-bubble-managed-start -->"
_BLOCK_END   = "<!-- skill-bubble-managed-end -->"


def _skill_tag(name: str) -> str:
    return f"<!-- skill: {name} -->"


def _skill_end(name: str) -> str:
    return f"<!-- /skill: {name} -->"


def _read_claude_md() -> str:
    if CLAUDE_MD.exists():
        return CLAUDE_MD.read_text()
    return ""


def _write_claude_md(content: str) -> None:
    CLAUDE_MD.parent.mkdir(parents=True, exist_ok=True)
    CLAUDE_MD.write_text(content)


def _upsert_skill_in_claude_md(name: str, skill_content: str) -> None:
    """Insert or replace a skill block inside the managed section of CLAUDE.md."""
    content = _read_claude_md()
    skill_block = f"{_skill_tag(name)}\n{skill_content}\n{_skill_end(name)}"

    if _BLOCK_START not in content:
        # No managed block yet — append one
        sep = "\n\n" if content and not content.endswith("\n\n") else ""
        managed = (
            f"{_BLOCK_START}\n"
            f"## Active Skills (managed by skill-bubble)\n\n"
            f"{skill_block}\n"
            f"{_BLOCK_END}\n"
        )
        _write_claude_md(content + sep + managed)
        return

    # Extract the block boundaries
    start_idx = content.index(_BLOCK_START)
    end_idx   = content.index(_BLOCK_END, start_idx) + len(_BLOCK_END)
    block = content[start_idx:end_idx]

    # Remove existing entry for this skill (if any)
    tag_pattern = re.compile(
        re.escape(_skill_tag(name)) + r".*?" + re.escape(_skill_end(name)),
        re.DOTALL,
    )
    block = tag_pattern.sub("", block)

    # Insert new skill block just before the end marker
    block = block.replace(_BLOCK_END, f"{skill_block}\n{_BLOCK_END}")

    # Clean up any double blank lines inside the block
    block = re.sub(r"\n{3,}", "\n\n", block)

    _write_claude_md(content[:start_idx] + block + content[end_idx:])


def _remove_skill_from_claude_md(name: str) -> None:
    """Remove a skill block from CLAUDE.md; clean up managed section if empty."""
    content = _read_claude_md()
    if _BLOCK_START not in content:
        return

    start_idx = content.index(_BLOCK_START)
    end_idx   = content.index(_BLOCK_END, start_idx) + len(_BLOCK_END)
    block = content[start_idx:end_idx]

    tag_pattern = re.compile(
        re.escape(_skill_tag(name)) + r".*?" + re.escape(_skill_end(name)),
        re.DOTALL,
    )
    block = tag_pattern.sub("", block)

    # If the managed block is now empty (only header + delimiters), remove it
    inner = block[len(_BLOCK_START):-len(_BLOCK_END)].strip()
    # Strip the optional header line
    inner_no_header = re.sub(r"^## Active Skills \(managed by skill-bubble\)", "", inner).strip()
    if not inner_no_header:
        # Remove entire managed block (and any leading blank lines before it)
        _write_claude_md(
            re.sub(r"\n*" + re.escape(content[start_idx:end_idx]), "", content)
        )
        return

    block = re.sub(r"\n{3,}", "\n\n", block)
    _write_claude_md(content[:start_idx] + block + content[end_idx:])


def _read_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {"skills": []}


def _write_manifest(data: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(data, indent=2))


def load_skill(name: str) -> dict:
    """
    Mark skill as loaded. Returns skill dict.
    Raises KeyError if skill not found.
    """
    skill = registry.get_skill(name)
    if not skill:
        raise KeyError(f"Skill '{name}' not found in registry.")

    registry.set_loaded(name, True)
    registry.record_usage(name)

    manifest = _read_manifest()
    # Remove any existing entry for this skill, then add fresh
    manifest["skills"] = [s for s in manifest["skills"] if s["name"] != name]
    manifest["skills"].append({"name": name, "path": skill["path"]})
    _write_manifest(manifest)

    # Sync to ~/.claude/CLAUDE.md so skill is injected into Claude Code context
    skill_path = Path(skill["path"])
    skill_md = skill_path / "SKILL.md" if skill_path.is_dir() else skill_path
    if skill_md.exists():
        _upsert_skill_in_claude_md(name, skill_md.read_text().strip())

    return registry.get_skill(name)


def unload_skill(name: str) -> None:
    """
    Mark skill as unloaded / deactivate it.
    Raises KeyError if skill not found.
    """
    skill = registry.get_skill(name)
    if not skill:
        raise KeyError(f"Skill '{name}' not found in registry.")

    registry.set_loaded(name, False)

    manifest = _read_manifest()
    manifest["skills"] = [s for s in manifest["skills"] if s["name"] != name]
    _write_manifest(manifest)

    # Remove from ~/.claude/CLAUDE.md
    _remove_skill_from_claude_md(name)


def active_skills() -> list[dict]:
    """Return list of currently loaded skills from the manifest."""
    return _read_manifest().get("skills", [])


def sync_from_manifest() -> None:
    """
    Re-sync the registry loaded state from the manifest file.
    Useful after manual edits or agent restarts.
    """
    manifest = _read_manifest()
    loaded_names = {s["name"] for s in manifest["skills"]}
    for skill in registry.list_skills():
        should_be_loaded = skill["name"] in loaded_names
        if bool(skill["loaded"]) != should_be_loaded:
            registry.set_loaded(skill["name"], should_be_loaded)
