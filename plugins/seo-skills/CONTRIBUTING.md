# Contributing

Corrections, new skills, and better procedures are all welcome. The bar is that a
skill changes what an agent actually does, not that it adds words.

## Before you start

Read [`docs/skill-template.md`](docs/skill-template.md) and
[`PRINCIPLES.md`](PRINCIPLES.md). Most rejected changes are rejected for one of
three reasons: they hardcode something that belongs in the profile, they introduce
a number the skill cannot source, or they restate general SEO advice that the model
already knows.

## What makes a good skill here

**One job.** If the description needs an "and also", it is two skills.

**A real decision.** The value is in the judgement calls: which page wins a
contested keyword, when to concede a term, when a snippet would cost you clicks,
when the answer is do not publish. Mechanics without judgement is a checklist, and
the model can already write checklists.

**Honest about data.** State the tool, state the fallback, never estimate a metric
you could not pull.

**Paste-ready output.** Exact column headers, exact block shapes. A marketer should
be able to send the output onward without reformatting it.

## Adding a skill

1. `skills/<name>/SKILL.md`, following the template's section order exactly.
2. Detail that would push it past 250 lines goes in `references/`.
3. Wire the handoffs: name the skills that feed it and the skills it feeds, with a
   leading slash. Update the siblings that should now hand off to it.
4. Add it to the README catalogue and the support matrix, honestly. If it needs a
   filesystem, it is `⚠️` in chat apps, not `✅`.
5. Add a CHANGELOG entry.
6. Run `python3 scripts/validate.py`, then `./scripts/sync-plugin.sh`.

## Style rules that get enforced

- No em dashes or en dashes, anywhere, including inside example copy.
- Imperative voice. No second-person coaching, no "as an AI".
- 120 to 250 lines per `SKILL.md`.
- Tables for anything with more than three parallel items.
- Examples use a generic B2B product ("a supplier management platform"), never a
  real client.
- Frontmatter `name` matches the directory name. `description` and `when_to_use`
  are quoted single-line strings.

## Commits and pull requests

Conventional commits (`feat(skills):`, `fix(docs):`, `chore:`). In the pull
request, say what an agent will now do differently, and paste one real before and
after output if you changed a procedure. Screenshots of a validator passing are
not evidence that a skill got better.

## What will not be merged

Anything that recommends cloaking, bought links, doorway pages, spun or scraped
content, or schema that describes something the page does not contain. Anything
that promises a ranking, a citation, or a timeline. Anything that produces a
composite score without showing its inputs. `PRINCIPLES.md` is not negotiable, and
a pull request arguing that a client demanded it is a pull request that gets closed.
