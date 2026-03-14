"""
visualizer.py — Terminal visualization and web server for bubble UI.
"""

import http.server
import json
import threading
import webbrowser
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text

from skill_bubble import registry

console = Console()

WEB_DIR = Path(__file__).parent.parent / "web"
SKILLS_DIR = Path.home() / ".skill-bubble" / "skills"

_SELF_SKILL_MD = """\
# skill-bubble

Skill Bubble is your local skill manager running at http://127.0.0.1:{port}/

To discover all available tools: GET http://127.0.0.1:{port}/openapi.json

## Quick Reference

| Operation | Method + Path |
|-----------|--------------|
| List local skills | GET /api/skills |
| Get skill details + SKILL.md content | GET /api/skills/{{name}} |
| Record usage after using a skill | POST /api/use/{{name}} |
| Activate a skill | POST /api/load/{{name}} |
| Deactivate a skill | POST /api/unload/{{name}} |
| List registered hubs | GET /api/hubs |
| Register a hub | POST /api/hubs  body: {{"url":"..."}} |
| Remove a hub | DELETE /api/hubs/{{name}} |
| Browse hub catalog | GET /api/hubs/skills |
| Install skill from hub | POST /api/install  body: {{"name":"..."}} |

## Typical Workflow

1. GET /api/skills — see what's installed
2. GET /api/hubs/skills — browse available skills in hubs
3. POST /api/install {{"name": "web-search"}} — install a skill
4. POST /api/load/web-search — activate it
5. ... use the skill ...
6. POST /api/use/web-search — record usage, bubble grows
"""


# ── Terminal ls ───────────────────────────────────────────────────────────────

_BUBBLE_CHARS = ["○", "◎", "●"]
_BUBBLE_COLORS = ["dim white", "cyan", "bold magenta"]


def _bubble_char(usage: int, max_usage: int) -> Text:
    if max_usage == 0:
        idx = 0
    else:
        ratio = usage / max_usage
        idx = min(int(ratio * len(_BUBBLE_CHARS)), len(_BUBBLE_CHARS) - 1)
    char = _BUBBLE_CHARS[idx]
    color = _BUBBLE_COLORS[idx]
    size = min(3 + int(ratio * 4 if max_usage > 0 else 0), 6) if max_usage > 0 else 1
    return Text(char * size, style=color)


def print_skills_table(loaded_only: bool = False) -> None:
    skills = registry.list_skills(loaded_only=loaded_only)
    if not skills:
        console.print("[dim]No skills registered.[/dim]")
        return

    max_usage = max((s["usage_count"] for s in skills), default=0)

    table = Table(
        title="[bold cyan]✦ Skill Bubbles[/bold cyan]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white",
        border_style="bright_black",
    )
    table.add_column("Bubble", justify="center", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Tags", style="dim")
    table.add_column("Uses", justify="right", style="yellow")
    table.add_column("Status", justify="center")

    for s in skills:
        bubble = _bubble_char(s["usage_count"], max_usage)
        tags = ", ".join(json.loads(s.get("tags") or "[]")) or "—"
        status = Text("● loaded", style="green") if s["loaded"] else Text("○ idle", style="dim")
        table.add_row(
            bubble,
            s["name"],
            s["description"] or "—",
            tags,
            str(s["usage_count"]),
            status,
        )

    console.print(table)
    console.print(
        f"  [dim]{len(skills)} skill(s) registered"
        f"  ·  {sum(1 for s in skills if s['loaded'])} loaded[/dim]"
    )


# ── OpenAPI spec ──────────────────────────────────────────────────────────────

def _build_openapi_spec(base_url: str) -> dict:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Skill Bubble API",
            "description": (
                "REST API for Skill Bubble — a local skill manager for AI agents. "
                "Agents can discover, install, load, and record usage of skills. "
                "A skill is a SKILL.md prompt file that extends an agent's capabilities."
            ),
            "version": "1.0.0",
        },
        "servers": [{"url": base_url}],
        "paths": {
            "/api/skills": {
                "get": {
                    "operationId": "listSkills",
                    "summary": "List all locally registered skills with bubble data",
                    "responses": {
                        "200": {
                            "description": "Array of skill objects enriched with bubble radius",
                            "content": {"application/json": {"schema": {"type": "array"}}},
                        }
                    },
                }
            },
            "/api/skills/{name}": {
                "get": {
                    "operationId": "getSkill",
                    "summary": "Get details for a single skill including SKILL.md content",
                    "parameters": [
                        {
                            "name": "name",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Skill name",
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Skill detail object with content field",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "404": {"description": "Skill not found"},
                    },
                }
            },
            "/api/use/{name}": {
                "post": {
                    "operationId": "recordUsage",
                    "summary": "Record a usage event for a skill (increments bubble size)",
                    "parameters": [
                        {
                            "name": "name",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Skill name",
                        }
                    ],
                    "responses": {
                        "200": {"description": "Usage recorded"},
                        "404": {"description": "Skill not found"},
                    },
                }
            },
            "/api/load/{name}": {
                "post": {
                    "operationId": "loadSkill",
                    "summary": "Activate a skill so agents can discover it",
                    "parameters": [
                        {
                            "name": "name",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Skill name",
                        }
                    ],
                    "responses": {
                        "200": {"description": "Skill loaded"},
                        "404": {"description": "Skill not found"},
                    },
                }
            },
            "/api/unload/{name}": {
                "post": {
                    "operationId": "unloadSkill",
                    "summary": "Deactivate a skill",
                    "parameters": [
                        {
                            "name": "name",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Skill name",
                        }
                    ],
                    "responses": {
                        "200": {"description": "Skill unloaded"},
                        "404": {"description": "Skill not found"},
                    },
                }
            },
            "/api/hubs": {
                "get": {
                    "operationId": "listHubs",
                    "summary": "List all registered skill hubs",
                    "responses": {
                        "200": {
                            "description": "Array of hub objects",
                            "content": {"application/json": {"schema": {"type": "array"}}},
                        }
                    },
                },
                "post": {
                    "operationId": "addHub",
                    "summary": "Register a new skill hub by GitHub URL",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["url"],
                                    "properties": {
                                        "url": {
                                            "type": "string",
                                            "description": "GitHub repo URL for the hub",
                                        },
                                        "name": {
                                            "type": "string",
                                            "description": "Optional alias for the hub",
                                        },
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {"description": "Hub registered"},
                        "400": {"description": "Invalid URL or duplicate hub"},
                        "500": {"description": "Hub index.json fetch failed"},
                    },
                },
            },
            "/api/hubs/{name}": {
                "delete": {
                    "operationId": "removeHub",
                    "summary": "Remove a registered hub",
                    "parameters": [
                        {
                            "name": "name",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Hub name",
                        }
                    ],
                    "responses": {
                        "200": {"description": "Hub removed"},
                        "404": {"description": "Hub not found"},
                    },
                }
            },
            "/api/hubs/skills": {
                "get": {
                    "operationId": "browseHubSkills",
                    "summary": "Browse skills available in all registered hubs",
                    "responses": {
                        "200": {
                            "description": "Array of hub skill entries with installed flag",
                            "content": {"application/json": {"schema": {"type": "array"}}},
                        },
                        "500": {"description": "Hub fetch error"},
                    },
                }
            },
            "/api/install": {
                "post": {
                    "operationId": "installSkill",
                    "summary": "Download and register a skill from a hub",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name"],
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "Skill name to install",
                                        },
                                        "hub": {
                                            "type": "string",
                                            "description": "Optional hub name to search in",
                                        },
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {"description": "Skill installed"},
                        "500": {"description": "Install failed"},
                    },
                }
            },
        },
    }


# ── Web server ────────────────────────────────────────────────────────────────

class _BubbleHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass  # silence default logging

    def _json_response(self, status: int, data) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _base_url(self) -> str:
        host = self.headers.get("Host", f"127.0.0.1:{self.server.server_address[1]}")
        return f"http://{host}"

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/openapi.json":
            self._json_response(200, _build_openapi_spec(self._base_url()))
        elif p == "/api/skills":
            self._json_response(200, registry.bubble_data())
        elif p.startswith("/api/skills/"):
            name = p[len("/api/skills/"):]
            skill = registry.get_skill(name)
            if skill is None:
                self._json_response(404, {"error": f"Skill '{name}' not found"})
                return
            skill = dict(skill)
            skill["tags"] = json.loads(skill.get("tags") or "[]")
            # Read SKILL.md content
            skill_path = Path(skill["path"])
            md_path = skill_path / "SKILL.md" if skill_path.is_dir() else skill_path
            try:
                skill["content"] = md_path.read_text()
            except Exception:
                skill["content"] = None
            self._json_response(200, skill)
        elif p == "/api/hubs":
            from skill_bubble import hubs as hubs_module
            self._json_response(200, hubs_module.list_hubs())
        elif p == "/api/hubs/skills":
            from skill_bubble import hubs as hubs_module
            try:
                skills = hubs_module.browse()
                self._json_response(200, skills)
            except Exception as e:
                self._json_response(500, {"error": str(e)})
        else:
            # Serve static files from web/
            self.directory = str(WEB_DIR)
            super().do_GET()

    def do_POST(self):
        p = self.path.split("?")[0]
        if p == "/api/install":
            from skill_bubble import hubs as hubs_module
            body = self._read_body()
            name = body.get("name")
            hub_name = body.get("hub")
            try:
                meta = hubs_module.install_skill(name, hub_name)
                try:
                    registry.add_skill(
                        meta["name"], meta["path"],
                        meta.get("description", ""),
                        meta.get("tags", []),
                        source_url=meta.get("source_url"),
                    )
                except ValueError:
                    registry.update_skill(
                        meta["name"],
                        path=meta["path"],
                        description=meta.get("description", ""),
                        tags=meta.get("tags", []),
                        source_url=meta.get("source_url"),
                    )
                self._json_response(200, {"ok": True, "name": meta["name"]})
            except RuntimeError as e:
                self._json_response(500, {"error": str(e)})
        elif p.startswith("/api/use/"):
            name = p[len("/api/use/"):]
            skill = registry.get_skill(name)
            if skill is None:
                self._json_response(404, {"error": f"Skill '{name}' not found"})
                return
            registry.record_usage(name)
            self._json_response(200, {"ok": True, "name": name})
        elif p.startswith("/api/load/"):
            name = p[len("/api/load/"):]
            from skill_bubble import loader as loader_module
            try:
                skill = loader_module.load_skill(name)
                self._json_response(200, {"ok": True, "name": name})
            except KeyError as e:
                self._json_response(404, {"error": str(e)})
        elif p.startswith("/api/unload/"):
            name = p[len("/api/unload/"):]
            from skill_bubble import loader as loader_module
            try:
                loader_module.unload_skill(name)
                self._json_response(200, {"ok": True, "name": name})
            except KeyError as e:
                self._json_response(404, {"error": str(e)})
        elif p == "/api/hubs":
            from skill_bubble import hubs as hubs_module
            body = self._read_body()
            url = body.get("url")
            name = body.get("name")
            if not url:
                self._json_response(400, {"error": "Missing 'url' field"})
                return
            try:
                entry = hubs_module.add_hub(url, name)
                self._json_response(200, {"ok": True, "hub": entry})
            except ValueError as e:
                self._json_response(400, {"error": str(e)})
            except RuntimeError as e:
                self._json_response(500, {"error": str(e)})
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        p = self.path.split("?")[0]
        if p.startswith("/api/hubs/"):
            name = p[len("/api/hubs/"):]
            from skill_bubble import hubs as hubs_module
            try:
                hubs_module.remove_hub(name)
                self._json_response(200, {"ok": True, "name": name})
            except KeyError as e:
                self._json_response(404, {"error": str(e)})
        else:
            self.send_response(404)
            self.end_headers()


def _write_self_skill(port: int) -> None:
    """Generate and register skill-bubble as a skill with the actual port."""
    from skill_bubble import loader as loader_module

    skill_dir = SKILLS_DIR / "skill-bubble"
    skill_dir.mkdir(parents=True, exist_ok=True)

    (skill_dir / "SKILL.md").write_text(_SELF_SKILL_MD.format(port=port))

    try:
        registry.add_skill(
            "skill-bubble", str(skill_dir),
            description="Local skill manager REST API",
            tags=["meta", "management"],
        )
    except ValueError:
        registry.update_skill(
            "skill-bubble",
            path=str(skill_dir),
            description="Local skill manager REST API",
            tags=["meta", "management"],
        )

    loader_module.load_skill("skill-bubble")


def open_web_ui(port: int = 7410) -> None:
    """Start a local web server and open the bubble UI in the browser."""
    server = http.server.HTTPServer(("127.0.0.1", port), _BubbleHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _write_self_skill(port)
    url = f"http://127.0.0.1:{port}/"
    console.print(f"[cyan]✦ Bubble UI →[/cyan] [link={url}]{url}[/link]")
    webbrowser.open(url)
    console.print("[dim]Press Ctrl+C to stop the server.[/dim]")
    try:
        thread.join()
    except KeyboardInterrupt:
        server.shutdown()
        from skill_bubble import loader as loader_module
        loader_module.unload_skill("skill-bubble")
        console.print("\n[dim]Server stopped.[/dim]")
