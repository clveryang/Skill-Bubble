"""
hubs.py — GitHub repo-based skill hub catalog.

A hub is a GitHub repo with:
  index.json           ← skill catalog
  skills/<name>/SKILL.md

Hub state persists in ~/.skill-bubble/hubs.json.
Installed skills go to ~/.skill-bubble/skills/{name}/.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from skill_bubble import registry as _registry

HUBS_PATH = Path.home() / ".skill-bubble" / "hubs.json"
SKILLS_INSTALL_DIR = Path.home() / ".skill-bubble" / "skills"


# ── Token ─────────────────────────────────────────────────────────────────────

def _token() -> Optional[str]:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    cfg = Path.home() / ".skill-bubble" / "config.json"
    if cfg.exists():
        data = json.loads(cfg.read_text())
        return data.get("github_token")
    return None


# ── URL parsing ───────────────────────────────────────────────────────────────

def parse_github_url(url: str) -> dict:
    """
    Parse a GitHub repo URL into components.
    Returns {"owner", "repo", "branch", "subpath"}.
    Raises ValueError for non-GitHub URLs.
    """
    url = url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]

    if "github.com" not in url:
        raise ValueError("Only GitHub URLs supported in v1")

    # Strip protocol
    path = url.split("github.com/", 1)[-1]
    parts = path.strip("/").split("/")

    if len(parts) < 2:
        raise ValueError(f"Cannot parse GitHub URL: {url}")

    owner = parts[0]
    repo = parts[1]
    branch = "main"
    subpath = ""

    # Handle /tree/<branch>[/<subpath>]
    if len(parts) >= 4 and parts[2] == "tree":
        branch = parts[3]
        subpath = "/".join(parts[4:]) if len(parts) > 4 else ""

    return {"owner": owner, "repo": repo, "branch": branch, "subpath": subpath}


# ── Hub registry CRUD ─────────────────────────────────────────────────────────

def load_hubs() -> list:
    if not HUBS_PATH.exists():
        return []
    return json.loads(HUBS_PATH.read_text())


def save_hubs(hubs: list) -> None:
    HUBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    HUBS_PATH.write_text(json.dumps(hubs, indent=2))


def add_hub(url: str, name: Optional[str] = None) -> dict:
    """
    Register a new hub by URL. Validates by fetching index.json.
    Returns the hub entry dict.
    Raises ValueError on duplicate name or bad URL.
    Raises RuntimeError if index.json fetch fails.
    """
    parsed = parse_github_url(url)
    owner, repo, branch, subpath = (
        parsed["owner"], parsed["repo"], parsed["branch"], parsed["subpath"]
    )

    # Fetch index.json to validate hub
    index = _fetch_index_raw(owner, repo, branch, subpath)

    # Determine name
    if name is None:
        name = index.get("hub_name") or repo

    hubs = load_hubs()
    if any(h["name"] == name for h in hubs):
        raise ValueError(f"Hub '{name}' already registered")

    entry = {
        "name": name,
        "url": url,
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "subpath": subpath,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    hubs.append(entry)
    save_hubs(hubs)
    return entry


def remove_hub(name: str) -> None:
    hubs = load_hubs()
    new_hubs = [h for h in hubs if h["name"] != name]
    if len(new_hubs) == len(hubs):
        raise KeyError(f"Hub '{name}' not found")
    save_hubs(new_hubs)


def get_hub(name: str) -> Optional[dict]:
    return next((h for h in load_hubs() if h["name"] == name), None)


def list_hubs() -> list:
    return load_hubs()


# ── Catalog fetching ──────────────────────────────────────────────────────────

def _raw_url(owner: str, repo: str, branch: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"


def _fetch_index_raw(owner: str, repo: str, branch: str, subpath: str = "") -> dict:
    """Fetch index.json from a hub repo. Raises RuntimeError on failure."""
    index_path = f"{subpath}/index.json".lstrip("/") if subpath else "index.json"
    raw = _raw_url(owner, repo, branch, index_path)
    try:
        resp = requests.get(raw, timeout=15)
    except requests.Timeout:
        raise RuntimeError("Hub request timed out")
    except requests.RequestException as e:
        raise RuntimeError(f"Hub request failed: {e}")

    if resp.status_code == 404:
        raise RuntimeError("No index.json found. Is this a valid Skill Bubble hub?")
    if not resp.ok:
        raise RuntimeError(
            f"Failed to fetch index.json ({resp.status_code}). "
            "Check repo visibility or add a token with: sb token <your-token>"
        )
    return resp.json()


def fetch_index(hub: dict) -> dict:
    return _fetch_index_raw(hub["owner"], hub["repo"], hub["branch"], hub.get("subpath", ""))


def browse(hub_name: Optional[str] = None, tag: Optional[str] = None) -> list:
    """
    Return skill entries from all (or one) registered hub(s).
    Each entry is augmented with "hub" alias and "installed" bool.
    Warns to stderr and continues if a hub fails.
    """
    hubs = [get_hub(hub_name)] if hub_name else list_hubs()
    hubs = [h for h in hubs if h]  # filter None

    # Collect locally registered skill names for "installed" check
    try:
        local_skills = {s["name"] for s in _registry.list_skills()}
    except Exception:
        local_skills = set()

    results = []
    for hub in hubs:
        try:
            index = fetch_index(hub)
        except Exception as e:
            print(f"Warning: hub '{hub['name']}' failed: {e}", file=sys.stderr)
            continue

        for skill in index.get("skills", []):
            entry = dict(skill)
            entry["hub"] = hub["name"]
            entry["installed"] = entry.get("name") in local_skills
            if tag and tag not in entry.get("tags", []):
                continue
            results.append(entry)

    return results


# ── Installation ──────────────────────────────────────────────────────────────

def install_skill(skill_name: str, hub_name: Optional[str] = None) -> dict:
    """
    Find and install a skill by name from hub(s).
    Returns {"name", "path", "description", "tags", "source_url"}.
    Raises RuntimeError if not found or download fails.
    """
    skills = browse(hub_name)
    entry = next((s for s in skills if s.get("name") == skill_name), None)
    if entry is None:
        where = f"hub '{hub_name}'" if hub_name else "any registered hub"
        raise RuntimeError(f"Skill '{skill_name}' not found in {where}")

    # Resolve hub
    hub = get_hub(entry["hub"])
    skill_path_in_repo = entry.get("path", f"skills/{skill_name}")
    skill_md_path = f"{skill_path_in_repo}/SKILL.md".lstrip("/")

    # Build raw URL
    subpath = hub.get("subpath", "")
    if subpath:
        skill_md_path = f"{subpath}/{skill_md_path}"
    raw = _raw_url(hub["owner"], hub["repo"], hub["branch"], skill_md_path)

    try:
        resp = requests.get(raw, timeout=15)
    except requests.Timeout:
        raise RuntimeError("Hub request timed out")
    except requests.RequestException as e:
        raise RuntimeError(f"Download failed: {e}")

    if resp.status_code == 404:
        raise RuntimeError(
            f"SKILL.md not found at {raw}. "
            "Check repo visibility or add a token with: sb token <your-token>"
        )
    if not resp.ok:
        raise RuntimeError(f"Download failed ({resp.status_code}): {raw}")

    # Write locally
    dest_dir = SKILLS_INSTALL_DIR / skill_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / "SKILL.md").write_text(resp.text)

    source_url = (
        f"https://github.com/{hub['owner']}/{hub['repo']}"
        f"/tree/{hub['branch']}/{skill_path_in_repo}"
    )

    return {
        "name": skill_name,
        "path": str(dest_dir),
        "description": entry.get("description", ""),
        "tags": entry.get("tags", []),
        "source_url": source_url,
    }


# ── Publishing ────────────────────────────────────────────────────────────────

def _github_put_file(
    owner: str, repo: str, branch: str, path: str,
    content: str, message: str, token: str, sha: Optional[str] = None
) -> None:
    """PUT a file via GitHub Contents API (creates or updates)."""
    import base64
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, json=payload, headers=headers, timeout=15)
    if not resp.ok:
        raise RuntimeError(f"GitHub API error ({resp.status_code}): {resp.text[:300]}")


def publish_skill(skill_name: str, hub_name: str, github_token: str) -> str:
    """
    Publish a local skill to a hub repo.
    1. Reads local skill SKILL.md from registry.
    2. PUT to skills/{name}/SKILL.md via GitHub Contents API.
    3. Updates index.json.
    Returns the GitHub URL for the skill.
    Raises PermissionError if no token.
    """
    if not github_token:
        raise PermissionError("Run: sb token <your-token>")

    skill = _registry.get_skill(skill_name)
    if not skill:
        raise KeyError(f"Skill '{skill_name}' not found in local registry")

    hub = get_hub(hub_name)
    if not hub:
        raise KeyError(f"Hub '{hub_name}' not registered")

    owner, repo, branch = hub["owner"], hub["repo"], hub["branch"]
    subpath = hub.get("subpath", "")

    # Read local SKILL.md
    skill_path = Path(skill["path"])
    skill_md_local = skill_path / "SKILL.md" if skill_path.is_dir() else skill_path
    if not skill_md_local.exists():
        raise FileNotFoundError(f"SKILL.md not found at {skill_md_local}")
    skill_content = skill_md_local.read_text()

    # Determine paths in repo
    repo_skill_dir = f"skills/{skill_name}"
    if subpath:
        repo_skill_dir = f"{subpath}/{repo_skill_dir}"
    repo_skill_md = f"{repo_skill_dir}/SKILL.md"

    # Check if file already exists (need sha for update)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{repo_skill_md}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
    }
    existing = requests.get(api_url, headers=headers, timeout=15)
    sha = existing.json().get("sha") if existing.ok else None

    # PUT SKILL.md
    _github_put_file(
        owner, repo, branch, repo_skill_md,
        skill_content,
        f"feat: publish skill {skill_name} via Skill Bubble",
        github_token, sha=sha,
    )

    # Update index.json
    try:
        index = _fetch_index_raw(owner, repo, branch, hub.get("subpath", ""))
    except RuntimeError:
        index = {"hub_name": repo, "skills": []}

    # Upsert skill entry in index
    skills_list = index.get("skills", [])
    existing_entry = next((s for s in skills_list if s.get("name") == skill_name), None)
    if existing_entry:
        existing_entry["description"] = skill.get("description", "")
        existing_entry["tags"] = json.loads(skill.get("tags") or "[]")
        existing_entry["path"] = f"skills/{skill_name}"
    else:
        skills_list.append({
            "name": skill_name,
            "description": skill.get("description", ""),
            "tags": json.loads(skill.get("tags") or "[]"),
            "path": f"skills/{skill_name}",
            "usage_count": 0,
        })
    index["skills"] = skills_list
    index["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Get sha for index.json
    index_path_in_repo = "index.json"
    if subpath:
        index_path_in_repo = f"{subpath}/index.json"
    api_index_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{index_path_in_repo}"
    existing_index = requests.get(api_index_url, headers=headers, timeout=15)
    index_sha = existing_index.json().get("sha") if existing_index.ok else None

    _github_put_file(
        owner, repo, branch, index_path_in_repo,
        json.dumps(index, indent=2),
        f"chore: update index.json for {skill_name}",
        github_token, sha=index_sha,
    )

    return f"https://github.com/{owner}/{repo}/tree/{branch}/skills/{skill_name}"
