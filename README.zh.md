# ✦ Skill Bubble

> 为 AI agent 设计的可视化技能管理器 — **用得越多，泡泡越大。**

[English README](README.md)

技能即泡泡。agent 使用一个技能的次数越多，它的泡泡就越大。
零安装：任意 agent 只需使用 Claude 内置工具即可浏览、安装、加载技能。

🌐 **可视化地址 → [clveryang.github.io/Skill-Bubble/web/](https://clveryang.github.io/Skill-Bubble/web/)**

![Skill Bubble 可视化](web/bubbles.svg)

---

## 概念

| 术语 | 含义 |
|------|------|
| **Skill（技能）** | 含 `SKILL.md` 的文件夹，agent 的操作指南 |
| **Bubble（泡泡）** | 技能的可视化气泡，大小 = 使用次数 |
| **Loaded（已加载）** | 技能已激活，内容注入 `~/.claude/CLAUDE.md` 进入 system prompt |
| **Hub（仓库）** | 含 `index.json` 的 GitHub 仓库，供 agent 通过 WebFetch 发现技能 |

---

## Agent 接入

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
    └─ 更新 index.json 并 git push              # 让别人能发现
```

### CLAUDE.md 中的 managed 区块

```
<!-- skill-bubble-managed-start -->
## Active Skills (managed by skill-bubble)
<!-- skill: web-search -->
[SKILL.md 内容]
<!-- /skill: web-search -->
<!-- skill-bubble-managed-end -->
```

---

## 技能格式

```
my-skill/
  SKILL.md    # 必需：# 名称标题 + 描述 + agent 操作说明
```

`SKILL.md` 中第一个非标题行用作 `index.json` 中的 description 字段。

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
