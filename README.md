# ✦ Skill Bubble

> A visual skill manager for AI agents — **usage makes bubbles grow.**

[中文版 README](README.zh.md)

Skills are bubbles. The more an agent uses a skill, the bigger its bubble becomes.
Zero-install: any agent can browse, install, and load skills using only built-in Claude tools.

🌐 **Live visualization → [clveryang.github.io/Skill-Bubble/web/](https://clveryang.github.io/Skill-Bubble/web/)**

![Skill Bubble visualization](web/bubbles.svg)

---

## Concepts

| Term | Meaning |
|------|---------|
| **Skill** | A folder with a `SKILL.md` — instructions for an agent |
| **Bubble** | Visual representation of a skill — size = usage count |
| **Loaded** | Skill is active; its instructions are injected into `~/.claude/CLAUDE.md` |
| **Hub** | GitHub repo with `index.json` — browse & install skills via WebFetch |

---

## Agent Integration

In any Claude Code conversation, tell the agent:

```
Learn https://raw.githubusercontent.com/clveryang/Skill-Bubble/main/skills/skill-bubble/SKILL.md
```

The agent fetches this file with WebFetch and immediately knows how to browse, install, load, unload, and publish skills — **no installation required**.

### Flow

```
[New agent]
    │
    ├─ WebFetch skills/skill-bubble/SKILL.md   # read the manual
    ├─ WebFetch index.json                      # browse available skills
    ├─ WebFetch skills/{name}/SKILL.md          # download a skill
    ├─ Write ~/.skill-bubble/skills/{name}/     # save locally
    ├─ Edit ~/.skill-bubble/loaded.json         # record as loaded
    └─ Edit ~/.claude/CLAUDE.md                 # inject into system prompt

[Agent sharing a skill]
    │
    ├─ PUT GitHub Contents API                  # upload SKILL.md
    └─ Update index.json and git push           # make it discoverable
```

### Managed block in `~/.claude/CLAUDE.md`

```
<!-- skill-bubble-managed-start -->
## Active Skills (managed by skill-bubble)
<!-- skill: web-search -->
[SKILL.md content]
<!-- /skill: web-search -->
<!-- skill-bubble-managed-end -->
```

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
  "updated_at": "2026-01-01T00:00:00+00:00",
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
