# ✦ Skill Bubble

> 为 AI agent 设计的可视化技能管理器 — **用得越多，泡泡越大。**

[English README](README.md)

技能即泡泡。agent 使用一个技能的次数越多，它的泡泡就越大。
零安装：任意 agent 只需使用 Claude 内置工具即可浏览、安装、加载技能。

🌐 **可视化地址 → [clveryang.github.io/Skill-Bubble/web/](https://clveryang.github.io/Skill-Bubble/web/)**

![Skill Bubble 可视化](web/bubbles.svg)

---

## 快速开始

在任意 Claude Code 对话中对 agent 说：

```
学习 https://raw.githubusercontent.com/clveryang/Skill-Bubble/main/skills/skill-bubble/SKILL.md
```

Agent 用 WebFetch 读取后即知道所有操作方式，**完全不需要安装任何东西**。

---

## 用法

让 agent 学习 `skill-bubble` 后，直接用自然语言下达指令即可。以下是各操作的示例。

### 浏览可用技能

```
浏览 Skill Bubble 上的技能
```
```
有哪些技能可以用？
```

Agent 获取 `index.json` 并列出所有技能的名称、描述和标签。

---

### 安装技能

```
安装 web-search 技能
```

Agent 下载 `skills/web-search/SKILL.md` 并保存到 `~/.skill-bubble/skills/web-search/SKILL.md`。

---

### 加载技能（在所有后续会话中激活）

```
加载 web-search 技能
```

Agent 将技能内容注入 `~/.claude/CLAUDE.md` 的 managed 区块：

```
<!-- skill-bubble-managed-start -->
## Active Skills (managed by skill-bubble)
<!-- skill: web-search -->
[SKILL.md 内容]
<!-- /skill: web-search -->
<!-- skill-bubble-managed-end -->
```

加载后的技能在每次 Claude Code 会话中自动生效。

---

### 查看已加载的技能

```
显示哪些技能已经加载了
```

Agent 读取 `~/.skill-bubble/loaded.json`。

---

### 卸载技能

```
卸载 web-search 技能
```

Agent 从 `~/.claude/CLAUDE.md` 中移除该技能的区块，并更新 `loaded.json`。

---

### 上传技能到 Hub

需要有 `repo` 权限的 GitHub personal access token。

```
把 ~/.skill-bubble/skills/my-skill/SKILL.md 上传到 hub。
我的 GitHub token 是 ghp_xxxx
```

Agent 会自动完成：
1. 通过 GitHub Contents API 的 PUT 接口上传 `SKILL.md`
2. GET `index.json`，追加新条目，再 PUT 回去 — 上传后立即可以被 Browse 发现

---

## 概念

| 术语 | 含义 |
|------|------|
| **Skill（技能）** | 含 `SKILL.md` 的文件夹，agent 的操作指南 |
| **Bubble（泡泡）** | 技能的可视化气泡，大小 = 使用次数 |
| **Loaded（已加载）** | 技能已激活，内容注入 `~/.claude/CLAUDE.md` 进入 system prompt |
| **Hub（仓库）** | 含 `index.json` 的 GitHub 仓库，供 agent 通过 WebFetch 发现技能 |

---

## 技能格式

```
my-skill/
  SKILL.md    # 必需：# 名称标题 + 描述 + agent 操作说明
```

`SKILL.md` 中第一个非标题行用作 `index.json` 中的 description 字段。

---

## Hub index.json 格式

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

## 数据位置

```
~/.skill-bubble/
  loaded.json     # 当前激活的技能列表
  skills/         # 下载的技能文件

~/.claude/
  CLAUDE.md       # Claude Code system prompt — skill-bubble 自动维护 managed 区块
```

---

## 可视化

在仓库 Settings → Pages → Source 选择 `main` 分支 `/ (root)` 开启 GitHub Pages。

访问地址：
```
https://<your-username>.github.io/<repo>/web/
```

- **气泡大小** = 使用次数（对数缩放）
- **发光青色** = 当前已激活
- **灰色** = 未激活
- 悬停查看名称、描述、标签、使用次数

---

## License

MIT
