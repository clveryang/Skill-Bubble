"""
registry.py — SQLite-backed skill registry.

Each skill entry tracks:
  - name, path, description, tags
  - usage_count  (bubble size)
  - last_used    (ISO timestamp)
  - loaded       (bool — is skill currently active?)
  - source_url   (for sharing / fetching from hub)
"""

import json
import math
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path.home() / ".skill-bubble" / "registry.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    _ensure_schema(con)
    return con


def _ensure_schema(con: sqlite3.Connection) -> None:
    con.executescript("""
        CREATE TABLE IF NOT EXISTS skills (
            name        TEXT PRIMARY KEY,
            path        TEXT NOT NULL,
            description TEXT DEFAULT '',
            tags        TEXT DEFAULT '[]',
            usage_count INTEGER DEFAULT 0,
            last_used   TEXT DEFAULT NULL,
            loaded      INTEGER DEFAULT 0,
            source_url  TEXT DEFAULT NULL,
            created_at  TEXT NOT NULL
        );
    """)
    con.commit()


# ── CRUD ──────────────────────────────────────────────────────────────────────

def add_skill(name: str, path: str, description: str = "",
              tags: list[str] | None = None, source_url: str | None = None) -> None:
    """Register a skill. Raises ValueError if name already taken."""
    with _conn() as con:
        existing = con.execute("SELECT name FROM skills WHERE name=?", (name,)).fetchone()
        if existing:
            raise ValueError(f"Skill '{name}' already registered. Use a different name.")
        con.execute(
            "INSERT INTO skills (name,path,description,tags,source_url,created_at) "
            "VALUES (?,?,?,?,?,?)",
            (name, str(path), description,
             json.dumps(tags or []), source_url,
             datetime.now(timezone.utc).isoformat())
        )


def remove_skill(name: str) -> None:
    """Unregister a skill by name."""
    with _conn() as con:
        con.execute("DELETE FROM skills WHERE name=?", (name,))


def get_skill(name: str) -> Optional[dict]:
    with _conn() as con:
        row = con.execute("SELECT * FROM skills WHERE name=?", (name,)).fetchone()
        return dict(row) if row else None


def list_skills(loaded_only: bool = False) -> list[dict]:
    with _conn() as con:
        q = "SELECT * FROM skills"
        if loaded_only:
            q += " WHERE loaded=1"
        q += " ORDER BY usage_count DESC, name"
        return [dict(r) for r in con.execute(q).fetchall()]


def record_usage(name: str) -> None:
    """Increment usage counter and update last_used timestamp."""
    with _conn() as con:
        con.execute(
            "UPDATE skills SET usage_count=usage_count+1, last_used=? WHERE name=?",
            (datetime.now(timezone.utc).isoformat(), name)
        )


def set_loaded(name: str, loaded: bool) -> None:
    with _conn() as con:
        con.execute("UPDATE skills SET loaded=? WHERE name=?", (int(loaded), name))


def update_skill(name: str, **kwargs) -> None:
    allowed = {"description", "tags", "source_url", "path"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    if "tags" in fields and isinstance(fields["tags"], list):
        fields["tags"] = json.dumps(fields["tags"])
    sets = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [name]
    with _conn() as con:
        con.execute(f"UPDATE skills SET {sets} WHERE name=?", vals)


# ── Bubble math ───────────────────────────────────────────────────────────────

MIN_RADIUS = 30   # px
MAX_RADIUS = 120  # px


def bubble_radius(usage_count: int, max_usage: int) -> int:
    """Map usage_count → bubble radius (px), log-scaled."""
    if max_usage == 0:
        return MIN_RADIUS
    ratio = math.log1p(usage_count) / math.log1p(max(max_usage, 1))
    return int(MIN_RADIUS + ratio * (MAX_RADIUS - MIN_RADIUS))


def bubble_data() -> list[dict]:
    """Return all skills enriched with bubble size for the UI."""
    skills = list_skills()
    max_usage = max((s["usage_count"] for s in skills), default=0)
    result = []
    for s in skills:
        d = dict(s)
        d["tags"] = json.loads(d.get("tags") or "[]")
        d["radius"] = bubble_radius(s["usage_count"], max_usage)
        result.append(d)
    return result
