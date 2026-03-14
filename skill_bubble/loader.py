"""
loader.py — Dynamic skill loading and unloading.

A "loaded" skill means it's active and agents can discover it.
Loading writes the skill's path to a central manifest file that
agents read at startup (similar to a PATH for skills).

Manifest location: ~/.skill-bubble/loaded.json
Format: { "skills": [ { "name": ..., "path": ... }, ... ] }
"""

import json
from pathlib import Path

from skill_bubble import registry

MANIFEST_PATH = Path.home() / ".skill-bubble" / "loaded.json"


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
