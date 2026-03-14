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

    def do_GET(self):
        if self.path == "/api/skills":
            self._json_response(200, registry.bubble_data())
        elif self.path == "/api/hubs/skills":
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
        if self.path == "/api/install":
            from skill_bubble import hubs as hubs_module
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
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
        else:
            self.send_response(404)
            self.end_headers()


def open_web_ui(port: int = 7410) -> None:
    """Start a local web server and open the bubble UI in the browser."""
    server = http.server.HTTPServer(("127.0.0.1", port), _BubbleHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}/"
    console.print(f"[cyan]✦ Bubble UI →[/cyan] [link={url}]{url}[/link]")
    webbrowser.open(url)
    console.print("[dim]Press Ctrl+C to stop the server.[/dim]")
    try:
        thread.join()
    except KeyboardInterrupt:
        server.shutdown()
        console.print("\n[dim]Server stopped.[/dim]")
