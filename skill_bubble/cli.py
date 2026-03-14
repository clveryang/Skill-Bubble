"""
cli.py — Skill Bubble command-line interface.

Commands:
  sb ls              List all skills (bubble visualization in terminal)
  sb add <path>      Register a skill from a local path
  sb remove <name>   Unregister a skill
  sb load <name>     Dynamically load / activate a skill
  sb unload <name>   Deactivate a skill
  sb use <name>      Record usage (for agents to call)
  sb share <name>    Upload skill to GitHub Gist (one-click share)
  sb fetch <url>     Install a skill from a Gist URL
  sb ui              Open the bubble visualization in the browser
  sb token <token>   Save your GitHub token for sharing
  sb info <name>     Show details about a skill
"""

import json
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from skill_bubble import registry, loader, hub, visualizer

console = Console()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _skill_name_from_path(path: Path) -> str:
    """Guess a skill name from its path."""
    if path.is_file():
        return path.stem
    # Look for SKILL.md to extract name
    skill_md = path / "SKILL.md"
    if skill_md.exists():
        for line in skill_md.read_text().splitlines():
            if line.startswith("# "):
                return line[2:].strip().lower().replace(" ", "-")
    return path.name


def _read_description(path: Path) -> str:
    """Try to read a one-line description from the skill."""
    candidates = [path / "SKILL.md", path / "README.md", path]
    for p in candidates:
        if p.is_file():
            for line in p.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    return line[:120]
    return ""


# ── CLI ───────────────────────────────────────────────────────────────────────

@click.group()
@click.version_option("0.1.0", prog_name="sb")
def cli():
    """
    \b
     ✦ Skill Bubble — visual skill manager for AI agents
     Usage grows bubbles. Skills stay alive.
    """


@cli.command("ls")
@click.option("--loaded", "-l", is_flag=True, help="Show only loaded/active skills.")
def cmd_ls(loaded):
    """List all skills with bubble visualization."""
    visualizer.print_skills_table(loaded_only=loaded)


@cli.command("add")
@click.argument("path", type=click.Path(exists=True))
@click.option("--name", "-n", default=None, help="Override skill name.")
@click.option("--description", "-d", default=None, help="Short description.")
@click.option("--tags", "-t", default="", help="Comma-separated tags.")
@click.option("--load", "auto_load", is_flag=True, help="Load immediately after adding.")
def cmd_add(path, name, description, tags, auto_load):
    """Register a skill from a local PATH (file or folder)."""
    p = Path(path).resolve()
    name = name or _skill_name_from_path(p)
    description = description or _read_description(p)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    try:
        registry.add_skill(name, str(p), description, tag_list)
        console.print(f"[green]✓[/green] Added skill [bold]{name}[/bold]")
        if auto_load:
            loader.load_skill(name)
            console.print(f"[cyan]⚡[/cyan] Loaded [bold]{name}[/bold]")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
        sys.exit(1)


@cli.command("remove")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
def cmd_remove(name, yes):
    """Unregister and remove skill NAME from the registry."""
    skill = registry.get_skill(name)
    if not skill:
        console.print(f"[red]✗[/red] Skill '{name}' not found.")
        sys.exit(1)

    if not yes:
        click.confirm(f"Remove skill '{name}'?", abort=True)

    if skill["loaded"]:
        loader.unload_skill(name)
    registry.remove_skill(name)
    console.print(f"[yellow]✓[/yellow] Removed skill [bold]{name}[/bold]")


@cli.command("load")
@click.argument("name")
def cmd_load(name):
    """Dynamically load / activate skill NAME."""
    try:
        skill = loader.load_skill(name)
        console.print(
            f"[cyan]⚡[/cyan] Loaded [bold]{name}[/bold]  "
            f"(uses: {skill['usage_count']})"
        )
    except KeyError as e:
        console.print(f"[red]✗[/red] {e}")
        sys.exit(1)


@cli.command("unload")
@click.argument("name")
def cmd_unload(name):
    """Deactivate skill NAME without removing it from the registry."""
    try:
        loader.unload_skill(name)
        console.print(f"[yellow]◦[/yellow] Unloaded [bold]{name}[/bold]")
    except KeyError as e:
        console.print(f"[red]✗[/red] {e}")
        sys.exit(1)


@cli.command("use")
@click.argument("name")
def cmd_use(name):
    """Record a usage event for NAME (for agents to call programmatically)."""
    skill = registry.get_skill(name)
    if not skill:
        console.print(f"[red]✗[/red] Skill '{name}' not found.")
        sys.exit(1)
    registry.record_usage(name)
    updated = registry.get_skill(name)
    console.print(
        f"[magenta]✦[/magenta] [bold]{name}[/bold] bubble grew! "
        f"(uses: {updated['usage_count']})"
    )


@cli.command("info")
@click.argument("name")
def cmd_info(name):
    """Show detailed info about skill NAME."""
    skill = registry.get_skill(name)
    if not skill:
        console.print(f"[red]✗[/red] Skill '{name}' not found.")
        sys.exit(1)

    tags = ", ".join(json.loads(skill.get("tags") or "[]")) or "none"
    status = "[green]loaded[/green]" if skill["loaded"] else "[dim]idle[/dim]"

    text = Text()
    text.append(f"Name:        ", style="bold")
    text.append(f"{skill['name']}\n")
    text.append(f"Path:        ", style="bold")
    text.append(f"{skill['path']}\n")
    text.append(f"Description: ", style="bold")
    text.append(f"{skill['description'] or '—'}\n")
    text.append(f"Tags:        ", style="bold")
    text.append(f"{tags}\n")
    text.append(f"Usage:       ", style="bold")
    text.append(f"{skill['usage_count']} times\n")
    text.append(f"Last used:   ", style="bold")
    text.append(f"{skill['last_used'] or 'never'}\n")
    text.append(f"Status:      ", style="bold")

    console.print(Panel(text, title=f"[bold cyan]✦ {name}[/bold cyan]", expand=False))
    console.print(f"  Status: {status}")
    if skill.get("source_url"):
        console.print(f"  Source: [link={skill['source_url']}]{skill['source_url']}[/link]")


@cli.command("share")
@click.argument("name")
@click.option("--description", "-d", default=None, help="Override description for the Gist.")
def cmd_share(name, description):
    """Upload skill NAME to GitHub Gist for one-click sharing."""
    skill = registry.get_skill(name)
    if not skill:
        console.print(f"[red]✗[/red] Skill '{name}' not found.")
        sys.exit(1)

    desc = description or skill.get("description") or ""
    console.print(f"[dim]Uploading {name} to GitHub Gist…[/dim]")

    try:
        url = hub.share_skill(name, skill["path"], desc)
        registry.update_skill(name, source_url=url)
        console.print(f"[green]✓[/green] Shared! → [link={url}]{url}[/link]")
        console.print(f"  Others can install it with:")
        console.print(f"  [bold cyan]sb fetch {url}[/bold cyan]")
    except RuntimeError as e:
        console.print(f"[red]✗[/red] {e}")
        console.print("[dim]Tip: set a GitHub token with: sb token <your-token>[/dim]")
        sys.exit(1)


@cli.command("fetch")
@click.argument("url")
@click.option(
    "--dir", "install_dir",
    default=None,
    help="Directory to install the skill into (default: ~/skills/)."
)
@click.option("--load", "auto_load", is_flag=True, help="Load immediately after installing.")
def cmd_fetch(url, install_dir, auto_load):
    """Install a skill from a Gist URL."""
    base_dir = Path(install_dir) if install_dir else Path.home() / "skills"
    console.print(f"[dim]Fetching skill from {url}…[/dim]")

    try:
        meta = hub.fetch_skill(url, base_dir)
        name = meta.get("name", "unknown")
        desc = meta.get("description", "")
        skill_dir = base_dir / name

        # Register
        try:
            registry.add_skill(name, str(skill_dir), desc, source_url=url)
        except ValueError:
            registry.update_skill(name, path=str(skill_dir), description=desc, source_url=url)

        console.print(f"[green]✓[/green] Installed skill [bold]{name}[/bold] → {skill_dir}")

        if auto_load:
            loader.load_skill(name)
            console.print(f"[cyan]⚡[/cyan] Loaded [bold]{name}[/bold]")

    except RuntimeError as e:
        console.print(f"[red]✗[/red] {e}")
        sys.exit(1)


@cli.command("ui")
@click.option("--port", default=7410, show_default=True, help="Local port for the web UI.")
def cmd_ui(port):
    """Open the bubble visualization in your browser."""
    visualizer.open_web_ui(port=port)


@cli.command("token")
@click.argument("token")
def cmd_token(token):
    """Save your GitHub personal access token for sharing skills."""
    hub.set_github_token(token)
    console.print("[green]✓[/green] GitHub token saved to ~/.skill-bubble/config.json")


@cli.command("sync")
def cmd_sync():
    """Re-sync loaded state from the manifest file."""
    loader.sync_from_manifest()
    console.print("[green]✓[/green] Synced loaded state from manifest.")


if __name__ == "__main__":
    cli()
