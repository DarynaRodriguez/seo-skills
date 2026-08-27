# Skill frontmatter, and where it is portable

Every skill in this repo carries four fields:

```yaml
---
name: meta-writer
description: "What the skill does, written so a routing model can match it."
when_to_use: "The user asks for X, Y or Z; or another skill hands off <thing>."
argument-hint: "[url or keyword]"
---
```

`scripts/validate.py` requires all four and rejects any key outside a known set,
because an unrecognised key is ignored silently. A misspelled `when_to_use` costs
a skill its trigger phrases and nothing tells you.

## What each field does

| Field | Effect |
|-------|--------|
| `name` | The command name. Must match the directory |
| `description` | What a routing model reads to decide whether this skill applies. Put the key use case first |
| `when_to_use` | Appended to `description` in the skill listing, so trigger phrases belong here. The two together are capped at 1,536 characters |
| `argument-hint` | Shown in the `/` menu during autocomplete. Tells the reader whether the skill wants a URL, a keyword, or a CSV |

Two fields are deliberately absent:

- **`user-invocable`** defaults to `true`, so every skill here is already
  reachable as `/skill-name`. Setting it explicitly would be noise. Set it to
  `false` only for a skill that is background knowledge rather than an action.
- **`disable-model-invocation`** would stop the agent choosing a skill on its own.
  These skills are meant to be chosen, so it stays off. A future skill that
  publishes or overwrites anything is the case for turning it on.

## The portability limit

Claude Code accepts every field it documents. Other distribution paths do not,
and they fail with a hard error rather than ignoring the extra key:

```
Unexpected key(s) in SKILL.md frontmatter: argument-hint.
Allowed properties are: allowed-tools, compatibility, description, license, metadata, name
```

| Path | Fields allowed |
|------|----------------|
| Claude Code at any level, **including plugin skills** | Every documented field |
| A direct claude.ai skill upload, the Skills API, `package_skill.py` | `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools` |

So, concretely, for this pack:

- **Installing as a plugin works everywhere**, which is the documented route in
  the README for Claude.ai, Cowork and Claude Code. Plugin skills get every field.
- **Copying one SKILL.md into a direct claude.ai upload will fail**, because
  `when_to_use` and `argument-hint` are not in the portable six. This is not
  hypothetical: it is a hard error, not a warning.

If you need a single skill on one of those paths, strip the two Claude Code
fields and fold the trigger phrases into `description`, which is where they end
up anyway:

```yaml
---
name: meta-writer
description: "Writes meta titles and descriptions that fit the pixel budget. Use when the user asks for meta titles, page titles, snippet copy or a title rewrite."
---
```

Nothing in the repo does this automatically. If it becomes a real need, the right
answer is a flag on `scripts/sync-plugin.sh` that emits a spec-clean copy, not
hand-editing 26 files.

## Adding a field

1. Check it against the Claude Code frontmatter reference first, and check which
   distribution paths accept it.
2. Add it to `ALLOWED_FRONTMATTER` in `scripts/validate.py`, and to
   `REQUIRED_FRONTMATTER` only if every skill genuinely needs it.
3. Add a row to the table above saying what it does and where it is portable.
4. Run `python3 scripts/validate.py` and `./scripts/sync-plugin.sh`.
