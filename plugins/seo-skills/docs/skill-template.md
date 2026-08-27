# How a skill in this repo is written

Every skill in this repo follows the same shape. If you are adding one, copy this
structure. If you are an agent generating one, follow it exactly.

## File location

`skills/<skill-name>/SKILL.md`, plus optional `references/*.md` for detail that
would bloat the main file.

## Frontmatter

```yaml
---
name: skill-name
description: "One sentence on what the skill does, written so a routing model can match it. Include the concrete artefacts it produces."
when_to_use: "The user asks for X, Y or Z; or another seo-skills skill hands off <thing>."
argument-hint: "[url]"
---
```

`name` matches the directory. `description`, `when_to_use` and `argument-hint`
are quoted single-line strings. All four are required, and `scripts/validate.py`
rejects any other key, because an unrecognised key is ignored silently rather
than reported.

`argument-hint` is what the `/` menu shows during autocomplete, so it names what
the skill wants: `[url]`, `[keyword]`, `[export.csv]`. Not every field is portable
to every distribution path: see `docs/frontmatter.md` before adding one.

## Body sections, in this order

### 1. Title and one-line identity

```
# Skill Name

You are **skill-name**, a skill from the seo-skills pack. <One or two sentences on the job and its
edge: what this skill decides that a generic prompt would not.>
```

### 2. Load the profile

Every skill starts by loading the site profile so its output is specific, not generic:

```
## Step 0: Load the profile

Read the site profile before anything else:

1. `.seo/profile.md` in the working directory
2. `~/.seo-skills/profile.md`
3. Neither exists: ask for the six essentials inline (domain, markets and
   languages, buyer, competitors, product vocabulary, banned words), do the work,
   then offer to run `/seo-profile-setup` so the next run is cheaper.

Never invent profile values. An unknown competitor set or an unknown buyer changes
the answer, so ask rather than assume.
```

Exception: `seo-profile-setup` and `site-inventory` write the profile, so they say
so instead.

### 3. Data sources

State exactly which live tools the skill uses and what it does without them:

```
## Data

| Need | Live tool | Without a connector |
|------|-----------|---------------------|
| ... | `mcp__Ahrefs__keywords-explorer-overview` | Ask the user to paste an export, and label every figure as user-supplied |
```

Rules that apply to every skill:

- Never invent a metric. Every number in an output carries its source and the date
  it was pulled.
- When a connector is missing, say so in the output rather than estimating volumes,
  difficulty, or visibility from memory.
- Ahrefs monetary values are USD cents. Divide by 100 to display.
- Peec `visibility`, `share_of_voice` and `retrieved_percentage` are 0 to 1 ratios,
  multiply by 100 for display. `sentiment` is 0 to 100. `retrieval_rate` and
  `citation_rate` are averages, not percentages, and can exceed 1.0: print as-is.

Full tool list: `docs/data-sources.md`.

### 4. Procedure

Numbered steps, imperative voice ("Pull the SERP overview", not "You should pull").
Each step says what to do and what decision comes out of it. Include the judgement
calls, not just the mechanics: this is where the skill earns its keep.

### 5. Output

Show the exact table or block the skill returns, with column headers spelled out.
Deliverables are markdown by default so a human can paste them anywhere. Say where
a file is written when the skill writes one (`.seo/` for working state).

### 6. Guardrails

Close with the skill's own hard limits, on top of `PRINCIPLES.md`. At minimum:

- What this skill must never claim.
- The handoff: which skill takes over next, by name.

## House style

- Length: 120 to 250 lines. Move depth into `references/`.
- Imperative voice. No "as an AI". No preamble about being helpful.
- Every checklist item is checkable by looking at a page or a data table.
- Copy the skill produces obeys the profile's language variant and banned words,
  including the em dash ban when the profile sets one.
- Tables over prose for anything with more than three parallel items.
- Name sibling skills with a leading slash (`/meta-writer`) when handing off.
