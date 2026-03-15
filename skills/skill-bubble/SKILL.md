# skill-bubble

Skill manager for Claude Code agents — install, load, and share skills via WebFetch and file operations.

---

## Overview

**skill-bubble** lets any Claude Code agent manage skills stored in GitHub repos (hubs). All operations use built-in Claude tools: `WebFetch`, `Read`, `Write`, `Edit`.

Data lives in:
```
~/.skill-bubble/
  loaded.json     # active skills list
  skills/         # downloaded skill files

~/.claude/
  CLAUDE.md       # Claude Code system prompt — skill-bubble maintains a managed block here
```

---

## Operations

### Browse available skills

```
WebFetch → https://raw.githubusercontent.com/clveryang/Skill-Bubble/main/index.json
```

Parse the returned JSON to list skills. Each skill has: `name`, `description`, `tags`, `path`, `usage_count`.

---

### Install a skill

1. Find the skill's `path` from `index.json` (e.g. `"path": "skills/web-search"`)
2. Fetch the SKILL.md:
   ```
   WebFetch → https://raw.githubusercontent.com/clveryang/Skill-Bubble/main/{path}/SKILL.md
   ```
3. Save locally:
   ```
   Write → ~/.skill-bubble/skills/{name}/SKILL.md
   ```

---

### Load a skill (inject into system prompt)

Loading makes a skill active — its instructions appear in every future Claude Code session.

1. Read the skill content:
   ```
   Read → ~/.skill-bubble/skills/{name}/SKILL.md
   ```

2. Update `~/.skill-bubble/loaded.json` — add entry:
   ```json
   [
     { "name": "{name}", "path": "~/.skill-bubble/skills/{name}/SKILL.md" }
   ]
   ```
   If the file doesn't exist, create it with `[]` first, then add the entry.

3. Inject into `~/.claude/CLAUDE.md` — maintain this managed block:
   ```
   <!-- skill-bubble-managed-start -->
   ## Active Skills (managed by skill-bubble)
   <!-- skill: {name} -->
   {contents of SKILL.md}
   <!-- /skill: {name} -->
   <!-- skill-bubble-managed-end -->
   ```
   - If the managed block doesn't exist in CLAUDE.md, append it.
   - If the block exists, insert the new `<!-- skill: {name} --> ... <!-- /skill: {name} -->` section before `<!-- skill-bubble-managed-end -->`.
   - If CLAUDE.md doesn't exist, create it with just the managed block.

---

### View loaded skills

```
Read → ~/.skill-bubble/loaded.json
```

---

### Unload a skill

1. Update `~/.skill-bubble/loaded.json` — remove the entry with matching `name`.

2. Edit `~/.claude/CLAUDE.md` — remove the block:
   ```
   <!-- skill: {name} -->
   ...
   <!-- /skill: {name} -->
   ```

3. If the managed block is now empty (no skill entries remain), remove the entire block:
   ```
   <!-- skill-bubble-managed-start -->
   ## Active Skills (managed by skill-bubble)
   <!-- skill-bubble-managed-end -->
   ```

---

### Upload a skill to the hub

Requires a GitHub personal access token with `repo` scope set in `GITHUB_TOKEN` environment variable (or ask the user to provide it).

1. Read the local SKILL.md you want to publish.
2. Base64-encode the content.
3. PUT to GitHub Contents API:
   ```
   PUT https://api.github.com/repos/clveryang/Skill-Bubble/contents/skills/{name}/SKILL.md
   Headers:
     Authorization: token {GITHUB_TOKEN}
     Content-Type: application/json
   Body:
     {
       "message": "feat: add {name}",
       "content": "{base64_encoded_content}"
     }
   ```
   If the file already exists, include `"sha": "{current_sha}"` in the body (get sha via GET on the same URL first).

4. Update index.json on GitHub:

   a. GET https://api.github.com/repos/clveryang/Skill-Bubble/contents/index.json
      Headers: Authorization: token {GITHUB_TOKEN}
      → Extract `content` (base64) and `sha` from the response.

   b. Decode content (base64 → UTF-8), parse as JSON. Append a new entry to the `skills` array:
      ```json
      {
        "name": "{name}",
        "description": "{one-line description}",
        "tags": [...],
        "path": "skills/{name}",
        "usage_count": 0
      }
      ```
      Also update the top-level `"updated_at"` field to the current UTC time in ISO 8601 format (e.g. `"2026-03-15T12:00:00Z"`).

   c. Re-encode the updated JSON as base64 (UTF-8, no line breaks).

   d. PUT https://api.github.com/repos/clveryang/Skill-Bubble/contents/index.json
      Headers: Authorization: token {GITHUB_TOKEN}, Content-Type: application/json
      Body:
      ```json
      {
        "message": "feat: register {name}",
        "content": "{base64_encoded_updated_json}",
        "sha": "{sha_from_step_a}"
      }
      ```

   After both PUTs succeed, confirm to the user that the skill is published and discoverable.

---

## Zero-install quickstart

In any Claude Code conversation, tell the agent:

```
Learn https://raw.githubusercontent.com/clveryang/Skill-Bubble/main/skills/skill-bubble/SKILL.md
```

The agent fetches this file with WebFetch and immediately knows how to perform all skill management operations without installing anything.

Once learned, the agent supports:
- Browse available skills from the hub index
- Install skills by fetching their SKILL.md and saving locally to ~/.skill-bubble/skills/
- Load skills by injecting them into ~/.claude/CLAUDE.md within a managed block
- View loaded skills via ~/.skill-bubble/loaded.json
- Unload skills by removing them from the managed block and loaded.json
- Upload skills to the hub via GitHub Contents API
