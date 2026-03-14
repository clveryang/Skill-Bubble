# ✦ Skill Bubble

> A visual skill manager for AI agents — **usage makes bubbles grow.**

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

在任意 Claude Code 对话中对 agent 说：

```
学习 https://raw.githubusercontent.com/clveryang/Skill-Bubble/main/skills/skill-bubble/SKILL.md
```

Agent 用 WebFetch 读取后即知道所有操作方式，**完全不需要安装任何东西**。

### 流程示意

```
[新 agent]
    │
    ├─ WebFetch skills/skill-bubble/SKILL.md   # 学习操作手册
    ├─ WebFetch index.json                      # 浏览可用技能
    ├─ WebFetch skills/{name}/SKILL.md          # 下载技能
    ├─ Write ~/.skill-bubble/skills/{name}/     # 保存到本地
    ├─ Edit ~/.skill-bubble/loaded.json         # 记录已加载
    └─ Edit ~/.claude/CLAUDE.md                 # 注入 system prompt

[想分享自己技能的 agent]
    │
    ├─ PUT GitHub Contents API                  # 上传 SKILL.md
    └─ 手动更新 index.json 并 git push           # 让别人能发现
```

### managed 区块（自动维护在 `~/.claude/CLAUDE.md`）

```
<!-- skill-bubble-managed-start -->
## Active Skills (managed by skill-bubble)
<!-- skill: web-search -->
[SKILL.md 内容]
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

## Hub index.json 格式

仓库根目录的 `index.json` 供 agent 发现技能：

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

## 底层数据位置

```
~/.skill-bubble/
  loaded.json     # 当前激活的技能列表
  skills/         # 下载的技能文件

~/.claude/
  CLAUDE.md       # Claude Code system prompt — skill-bubble 自动维护 managed 区块
```

---

## Web Visualization

Enable **GitHub Pages** in repo Settings → Pages → Source: `main` branch, `/ (root)`.

Live at:
```
https://<your-username>.github.io/<repo>/web/
```

- **Bubble size** = usage count (log-scaled)
- **Glowing / teal** = currently loaded
- **Gray** = idle
- Hover for name, description, tags, and usage count

---

## License

MIT
