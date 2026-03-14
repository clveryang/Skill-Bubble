"""
hub.py — One-click share and fetch skills via GitHub Gist.

Share:  packages a skill folder as a .skill zip and uploads to Gist.
Fetch:  downloads a Gist and installs it as a local skill.
"""

import io
import json
import os
import zipfile
from pathlib import Path
from typing import Optional

import requests

GIST_API = "https://api.github.com/gists"


def _token() -> Optional[str]:
    """Try to get GitHub token from env or ~/.skill-bubble/config.json."""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    cfg = Path.home() / ".skill-bubble" / "config.json"
    if cfg.exists():
        data = json.loads(cfg.read_text())
        return data.get("github_token")
    return None


def _headers() -> dict:
    token = _token()
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _zip_skill(skill_path: Path) -> bytes:
    """Zip a skill directory into bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if skill_path.is_file():
            zf.write(skill_path, skill_path.name)
        else:
            for f in skill_path.rglob("*"):
                if f.is_file() and ".git" not in f.parts:
                    zf.write(f, f.relative_to(skill_path.parent))
    return buf.getvalue()


def share_skill(name: str, skill_path: str, description: str = "") -> str:
    """
    Upload skill as a GitHub Gist.
    Returns the Gist URL.
    Raises RuntimeError on failure.
    """
    path = Path(skill_path)
    zip_bytes = _zip_skill(path)

    # Gist files must be text — base64-encode the zip
    import base64
    encoded = base64.b64encode(zip_bytes).decode()
    filename = f"{name}.skill"

    payload = {
        "description": description or f"Skill Bubble: {name}",
        "public": True,
        "files": {
            filename: {"content": encoded},
            "skill-bubble.json": {
                "content": json.dumps({
                    "name": name,
                    "description": description,
                    "skill_file": filename,
                    "encoding": "base64-zip",
                }, indent=2)
            }
        }
    }

    resp = requests.post(GIST_API, json=payload, headers=_headers(), timeout=15)
    if not resp.ok:
        raise RuntimeError(f"Gist upload failed: {resp.status_code} {resp.text[:200]}")

    return resp.json()["html_url"]


def fetch_skill(gist_url: str, install_dir: Path) -> dict:
    """
    Download a skill from a Gist URL and extract to install_dir.
    Returns metadata dict.
    Raises RuntimeError on failure.
    """
    import base64

    # Extract gist ID from URL
    gist_id = gist_url.rstrip("/").split("/")[-1]
    resp = requests.get(f"{GIST_API}/{gist_id}", headers=_headers(), timeout=15)
    if not resp.ok:
        raise RuntimeError(f"Failed to fetch Gist: {resp.status_code}")

    gist = resp.json()
    files = gist.get("files", {})

    # Find metadata
    meta_file = files.get("skill-bubble.json")
    if not meta_file:
        raise RuntimeError("This Gist doesn't look like a Skill Bubble package.")

    meta = json.loads(meta_file["content"])
    skill_filename = meta.get("skill_file")
    if not skill_filename or skill_filename not in files:
        raise RuntimeError(f"Skill file '{skill_filename}' not found in Gist.")

    encoded = files[skill_filename]["content"]
    zip_bytes = base64.b64decode(encoded)

    install_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.extractall(install_dir)

    return meta


def set_github_token(token: str) -> None:
    """Save GitHub token to ~/.skill-bubble/config.json."""
    cfg = Path.home() / ".skill-bubble" / "config.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if cfg.exists():
        data = json.loads(cfg.read_text())
    data["github_token"] = token
    cfg.write_text(json.dumps(data, indent=2))
    cfg.chmod(0o600)
