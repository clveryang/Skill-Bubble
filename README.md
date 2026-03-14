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

### 快速接入（新 agent 视角）

任意一个 agent 拿到你的 GitHub repo URL，就能浏览、安装、激活技能，无需运行任何本地服务。

#### 第一步：注册 hub

```bash
# 用你的 GitHub 仓库地址注册为技能仓库
sb hub add https://github.com/clveryang/Skill-Bubble

# 也可以指定别名
sb hub add https://github.com/clveryang/Skill-Bubble --name my-hub
```

**前提**：仓库根目录需要有 `index.json`（通过 `sb export && git push` 生成，详见下方）。

#### 第二步：查看可下载的技能

```bash
# 浏览所有已注册 hub 上的技能
sb browse

# 只看某个 hub
sb browse --hub my-hub

# 按标签过滤
sb browse --tag search

# 输出原始 JSON（方便 agent 解析）
sb browse --json
```

#### 第三步：安装技能

```bash
# 从 hub 安装（下载到 ~/skills/<name>/）
sb install web-search

# 安装后立即激活
sb install web-search --load
```

#### 第四步：激活 / 查看已加载的技能

```bash
# 激活一个技能（写入 ~/.claude/CLAUDE.md，下次 Claude Code 启动自动注入）
sb load web-search

# 查看当前已激活的技能
sb ls --loaded
```

`sb load` 会做两件事：
1. 把技能路径写入 `~/.skill-bubble/loaded.json`（供 agent 启动时读取）
2. 把技能的 `SKILL.md` 内容注入 `~/.claude/CLAUDE.md` 的 managed 区块，使其进入 Claude Code 的 system prompt

```
~/.claude/CLAUDE.md（自动维护区块）:

<!-- skill-bubble-managed-start -->
## Active Skills (managed by skill-bubble)

<!-- skill: web-search -->
[SKILL.md 内容]
<!-- /skill: web-search -->
<!-- skill-bubble-managed-end -->
```

#### 第五步：卸载技能

```bash
# 停用一个技能（从 CLAUDE.md 和 loaded.json 中移除）
sb unload web-search

# 彻底删除注册记录
sb remove web-search
```

卸载后，若 managed 区块为空，`~/.claude/CLAUDE.md` 中的整个区块会自动清除。

#### 第六步：上传本地技能到 hub

```bash
# 先保存 GitHub token（只需设置一次）
sb token ghp_xxxxxxxxxxxx

# 把本地技能发布到指定 hub（通过 GitHub Contents API 写入）
sb publish my-skill --to my-hub

# 发布后更新 hub 的 index.json（让其他 agent 能发现新技能）
sb export
git add index.json web/
git commit -m "chore: publish my-skill"
git push
```

---

### 完整流程示意

```
[新 agent]
    │
    ├─ sb hub add https://github.com/clveryang/Skill-Bubble
    ├─ sb browse                    # 看有哪些技能
    ├─ sb install web-search        # 下载到本地
    ├─ sb load web-search           # 激活 → 注入 CLAUDE.md
    │
    └─ (重启 Claude Code)           # system prompt 自动包含 web-search 说明

[想分享自己技能的 agent]
    │
    ├─ sb add ./my-awesome-skill    # 注册本地技能
    ├─ sb publish my-awesome-skill --to my-hub   # 上传到 hub
    └─ sb export && git push        # 更新 index.json 让别人能发现
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
