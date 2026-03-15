# ✦ Skill Bubble

> A visual skill manager for AI agents — **usage makes bubbles grow.**

[中文版 README](README.zh.md)

Skills are bubbles. The more an agent uses a skill, the bigger its bubble becomes.
Zero-install: any agent can browse, install, and load skills using only built-in Claude tools.

🌐 **Live visualization → [clveryang.github.io/Skill-Bubble/web/](https://clveryang.github.io/Skill-Bubble/web/)**

![Skill Bubble visualization](web/bubbles.svg)

---

## Quick Start

In any Claude Code conversation, tell the agent:

```
Learn https://raw.githubusercontent.com/clveryang/Skill-Bubble/main/skills/skill-bubble/SKILL.md
```

The agent fetches this file with WebFetch and immediately knows how to browse, install, load, unload, and publish skills — **no installation required**.

---

## Usage

After the agent has learned `skill-bubble`, you can ask it to perform any of the following operations by typing naturally. Examples below.

### Browse available skills

```
Browse skills on Skill Bubble hub
```
```
What skills are available?
```

The agent fetches `index.json` and lists all skills with name, description, and tags.

---

### Install a skill

```
Install the web-search skill
```

The agent downloads `skills/web-search/SKILL.md` and saves it to `~/.skill-bubble/skills/web-search/SKILL.md`.

---

### Load a skill (activate for all future sessions)

```
Load the web-search skill
```

The agent injects the skill's content into `~/.claude/CLAUDE.md` inside a managed block:

```
<!-- skill-bubble-managed-start -->
## Active Skills (managed by skill-bubble)
<!-- skill: web-search -->
[SKILL.md content]
<!-- /skill: web-search -->
<!-- skill-bubble-managed-end -->
```

Loaded skills are active in every Claude Code session automatically.

---

### View loaded skills

```
Show me which skills are loaded
```

The agent reads `~/.skill-bubble/loaded.json`.

---

### Unload a skill

```
Unload the web-search skill
```

The agent removes the skill's block from `~/.claude/CLAUDE.md` and updates `loaded.json`.

---

### Upload a skill to the hub

Requires a GitHub personal access token with `repo` scope.

```
Upload my skill at ~/.skill-bubble/skills/my-skill/SKILL.md to the hub.
My GitHub token is ghp_xxxx
```

The agent will:
1. PUT the `SKILL.md` file to GitHub via the Contents API
2. GET `index.json`, append the new entry, and PUT it back — so the skill is immediately discoverable via Browse

---

## Concepts

| Term | Meaning |
|------|---------|
| **Skill** | A folder with a `SKILL.md` — instructions for an agent |
| **Bubble** | Visual representation of a skill — size = usage count |
| **Loaded** | Skill is active; its instructions are injected into `~/.claude/CLAUDE.md` |
| **Hub** | GitHub repo with `index.json` — browse & install skills via WebFetch |

---

## Skill Format

```
my-skill/
  SKILL.md    # Required: # name heading + description + agent instructions
```

The first non-heading line of `SKILL.md` is used as the description in `index.json`.

---

## Hub `index.json` Format

```json
{
  "hub_name": "Skill-Bubble",
  "updated_at": "2026-01-01T00:00:00Z",
  "skills": [
    {
      "name": "web-search",
      "description": "Search the web using DuckDuckGo",
      "tags": ["search", "web"],
      "path": "skills/web-search",
      "usage_count": 42
    }
  ]
}
```

---

## Data Storage

```
~/.skill-bubble/
  loaded.json     # active skills list
  skills/         # downloaded skill files

~/.claude/
  CLAUDE.md       # Claude Code system prompt — managed block maintained here
```

---

## Web Visualization

Enable **GitHub Pages** in repo Settings → Pages → Source: `main` branch, `/ (root)`.

Live at:
```
https://<your-username>.github.io/<repo>/web/
```

- **Bubble size** = usage count (log-scaled)
- **Glowing teal** = currently loaded
- **Gray** = idle
- Hover for name, description, tags, and usage count

---

## License

MIT
