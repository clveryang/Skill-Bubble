# ✦ Skill Bubble

> A visual skill manager for AI agents — **usage makes bubbles grow.**

Skills are bubbles. The more an agent uses a skill, the bigger its bubble becomes.
One-click to add, load, share, and discover skills across agents.

🌐 **Live visualization → [clveryang.github.io/Skill-Bubble/web/](https://clveryang.github.io/Skill-Bubble/web/)**

![Skill Bubble visualization](web/bubbles.svg)

---

## Concepts

| Term | Meaning |
|------|---------|
| **Skill** | Any file or folder (script, SKILL.md, Python module, etc.) |
| **Bubble** | Visual representation of a skill — size = usage count |
| **Loaded** | Skill is active; agents can discover it via the manifest |
| **Registry** | Local SQLite DB tracking all skills and their usage |
| **Hub** | GitHub Gist-based sharing — one URL per skill |

---

## Install

```bash
pip install -e .
```

This installs the `sb` command globally.

---

## CLI Quick Reference

```bash
# List all skills (bubble visualization in terminal)
sb ls

# List only loaded/active skills
sb ls --loaded

# Register a skill from a local path (file or folder)
sb add ./path/to/my-skill

# Register with custom name and description
sb add ./path/to/my-skill --name "web-search" --description "Search the web" --tags "search,web"

# Load / activate a skill (adds it to the agent manifest)
sb load web-search

# Unload / deactivate a skill
sb unload web-search

# Record a usage event (agents call this programmatically)
sb use web-search

# Show detailed info about a skill
sb info web-search

# Remove a skill from the registry
sb remove web-search

# Open the bubble visualization in your browser
sb ui

# ── Sharing ──────────────────────────────────────────────────────────────
# Save your GitHub token (needed for sharing)
sb token ghp_xxxxxxxxxxxx

# Share a skill as a GitHub Gist (one-click)
sb share web-search

# Install a skill from a Gist URL
sb fetch https://gist.github.com/user/abc123

# Install and load immediately
sb fetch https://gist.github.com/user/abc123 --load
```

---

## Skill Format

A skill can be **any** of:

```
# Minimal — single file
my-skill.md
my-skill.py
my-skill.sh

# Standard — folder with SKILL.md
my-skill/
  SKILL.md          # Required: name (# heading) + description
  instructions.txt  # Optional: detailed agent instructions
  tools.py          # Optional: helper code

# Rich — anything goes
my-skill/
  SKILL.md
  README.md
  src/
  tests/
```

The first non-heading line of `SKILL.md` or `README.md` is used as the description.

---

## Agent Integration

When a skill is loaded, it's written to:

```
~/.skill-bubble/loaded.json
```

```json
{
  "skills": [
    { "name": "web-search", "path": "/Users/me/skills/web-search" },
    { "name": "code-review", "path": "/Users/me/skills/code-review" }
  ]
}
```

Agents read this manifest at startup to discover available skills.

### Programmatic usage (Python)

```python
from skill_bubble import registry, loader

# Load a skill
loader.load_skill("web-search")

# Record usage (bubble grows!)
registry.record_usage("web-search")

# Get all loaded skills
skills = loader.active_skills()

# Get bubble data for UI
bubbles = registry.bubble_data()
```

---

## Web Visualization

### GitHub Pages (public, auto-hosted)

```bash
# 1. Export your current skill registry to a static snapshot
sb export

# 2. Push to GitHub — visualization updates automatically
git add web/data.json
git commit -m "chore: update skill snapshot"
git push
```

Then enable **GitHub Pages** in your repo Settings → Pages → Source: `main` branch, `/ (root)`.

Your bubble visualization will be live at:
```
https://<your-username>.github.io/<repo>/web/
```

### Local dev server

```bash
sb ui            # opens http://127.0.0.1:7410
sb ui --port 8080
```

- **Bubble size** = usage count (log-scaled)
- **Glowing / teal** = currently loaded
- **Gray** = idle
- **Connected lines** = loaded skills that are active together
- Hover for name, description, tags, and usage count

---

## Data Storage

All data lives in `~/.skill-bubble/`:

```
~/.skill-bubble/
  registry.db     # SQLite — skills, usage counts, metadata
  loaded.json     # Active skills manifest (read by agents)
  config.json     # Settings (GitHub token, etc.)
```

---

## License

MIT
