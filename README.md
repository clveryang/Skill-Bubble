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
| **Hub** | GitHub repo with `index.json` — browse & install skills via `sb hub add <url>` |

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

### 零安装接入（推荐）

任意 Claude Code agent，无需安装任何东西，只需在对话中说：

```
学习 https://raw.githubusercontent.com/clveryang/Skill-Bubble/main/skills/skill-bubble/SKILL.md
```

Agent 用 WebFetch 读取后即知道所有操作方式（浏览技能、安装、加载、卸载、上传），完全通过 Claude 内置工具完成，**不依赖 `sb` CLI，不依赖本地服务器**。

#### 零安装流程示意

```
[新 agent]
    │
    ├─ WebFetch skills/skill-bubble/SKILL.md   # 学习操作手册
    ├─ WebFetch index.json                      # 浏览可用技能
    ├─ WebFetch skills/web-search/SKILL.md      # 下载技能
    ├─ Write ~/.skill-bubble/skills/web-search/ # 保存到本地
    ├─ Edit ~/.skill-bubble/loaded.json         # 记录已加载
    └─ Edit ~/.claude/CLAUDE.md                 # 注入 system prompt

[想分享自己技能的 agent]
    │
    ├─ PUT GitHub Contents API                  # 上传 SKILL.md
    └─ sb export && git push                    # 更新 index.json（需本地 sb）
```

managed 区块格式（自动维护在 `~/.claude/CLAUDE.md`）：

```
<!-- skill-bubble-managed-start -->
## Active Skills (managed by skill-bubble)
<!-- skill: web-search -->
[SKILL.md 内容]
<!-- /skill: web-search -->
<!-- skill-bubble-managed-end -->
```

---

### 本地安装方式（可选，使用 `sb` CLI）

如果你更喜欢命令行工具：

#### 第一步：注册 hub

```bash
sb hub add https://github.com/clveryang/Skill-Bubble
```

#### 第二步：浏览、安装、激活

```bash
sb browse                    # 看有哪些技能
sb install web-search        # 下载到本地
sb load web-search           # 激活 → 注入 CLAUDE.md
```

#### 第三步：上传本地技能

```bash
sb token ghp_xxxxxxxxxxxx
sb publish my-skill --to my-hub
sb export && git push        # 更新 index.json
```

---

### Hub 的 index.json 格式

`sb export` 会在仓库根目录生成 `index.json`，任何 agent 都能直接读取：

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

### 底层数据位置

```
~/.skill-bubble/
  registry.db     # SQLite — 技能元数据、使用次数
  loaded.json     # 当前激活的技能列表（agent 启动时读取）
  config.json     # 配置（GitHub token 等）

~/.claude/
  CLAUDE.md       # Claude Code system prompt — skill-bubble 自动维护 managed 区块
```

---

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
#    (also generates index.json for hub discovery)
sb export

# 2. Push to GitHub — visualization and hub catalog update automatically
git add web/ index.json
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
