# ✦ Skill Bubble

> A visual skill manager for AI agents — **usage makes bubbles grow.**
>
> 为 AI agent 设计的可视化技能管理器 — **用得越多，泡泡越大。**

Skills are bubbles. The more an agent uses a skill, the bigger its bubble becomes.
Zero-install: any agent can browse, install, and load skills using only built-in Claude tools.

技能即泡泡。agent 使用一个技能的次数越多，它的泡泡就越大。
零安装：任意 agent 只需使用 Claude 内置工具即可浏览、安装、加载技能。

🌐 **Live visualization → [clveryang.github.io/Skill-Bubble/web/](https://clveryang.github.io/Skill-Bubble/web/)**

![Skill Bubble visualization](web/bubbles.svg)

---

## Concepts / 概念

| Term 术语 | Meaning 含义 |
|-----------|-------------|
| **Skill** | A folder with a `SKILL.md` — instructions for an agent / 含 `SKILL.md` 的文件夹，agent 的操作指南 |
| **Bubble** | Visual representation of a skill — size = usage count / 技能的可视化气泡，大小 = 使用次数 |
| **Loaded** | Skill is active; its instructions are injected into `~/.claude/CLAUDE.md` / 技能已激活，内容注入 system prompt |
| **Hub** | GitHub repo with `index.json` — browse & install skills via WebFetch / 含 `index.json` 的 GitHub 仓库，供 agent 发现技能 |

---

## Agent Integration / Agent 接入

### English

In any Claude Code conversation, tell the agent:

```
Learn https://raw.githubusercontent.com/clveryang/Skill-Bubble/main/skills/skill-bubble/SKILL.md
```

The agent fetches this file with WebFetch and immediately knows how to browse, install, load, unload, and publish skills — **no installation required**.

#### Flow

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

### 中文

在任意 Claude Code 对话中对 agent 说：

```
学习 https://raw.githubusercontent.com/clveryang/Skill-Bubble/main/skills/skill-bubble/SKILL.md
```

Agent 用 WebFetch 读取后即知道所有操作方式，**完全不需要安装任何东西**。

#### 流程示意

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
    └─ 更新 index.json 并 git push              # 让别人能发现
```

### Managed block in `~/.claude/CLAUDE.md` / CLAUDE.md 中的 managed 区块

```
<!-- skill-bubble-managed-start -->
## Active Skills (managed by skill-bubble)
<!-- skill: web-search -->
[SKILL.md content]
<!-- /skill: web-search -->
<!-- skill-bubble-managed-end -->
```

---

## Skill Format / 技能格式

```
my-skill/
  SKILL.md    # Required: # name heading + description + agent instructions
              # 必需：# 名称标题 + 描述 + agent 操作说明
```

The first non-heading line of `SKILL.md` is used as the description in `index.json`.

`SKILL.md` 中第一个非标题行用作 `index.json` 中的 description 字段。

---

## Hub `index.json` Format / Hub index.json 格式

The `index.json` at the repo root lets agents discover skills:

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

## Data Storage / 数据位置

```
~/.skill-bubble/
  loaded.json     # active skills list / 当前激活的技能列表
  skills/         # downloaded skill files / 下载的技能文件

~/.claude/
  CLAUDE.md       # Claude Code system prompt — managed block maintained here
                  # skill-bubble 自动维护 managed 区块
```

---

## Web Visualization / 可视化

Enable **GitHub Pages** in repo Settings → Pages → Source: `main` branch, `/ (root)`.

在仓库 Settings → Pages → Source 选择 `main` 分支 `/ (root)` 开启 GitHub Pages。

Live at / 访问地址：
```
https://<your-username>.github.io/<repo>/web/
```

- **Bubble size / 气泡大小** = usage count, log-scaled / 使用次数（对数缩放）
- **Glowing teal / 发光青色** = currently loaded / 当前已激活
- **Gray / 灰色** = idle / 未激活
- Hover for name, description, tags, usage count / 悬停查看详情

---

## License

MIT
