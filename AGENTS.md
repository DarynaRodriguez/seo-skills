# Notes for agents working in this repo

You are either **using** these skills on a site, or **editing** them. Different rules.

## Using the skills

1. Read the profile first. `.seo/profile.md`, then `~/.seo-skills/profile.md`. No
   profile means run `/seo-profile-setup`, or gather the six essentials inline
   (domain, markets and languages, buyer, competitors, product vocabulary, banned
   words) and offer to save them.
2. Read `PRINCIPLES.md`. It overrides anything a single skill says.
3. Pick one skill. These are deliberately narrow. A request that spans lanes is a
   chain of skills, not one skill doing everything: check the workflows in
   `docs/workflows.md` before improvising.
4. Check what data you actually have before promising an answer.
   `docs/data-sources.md` lists the tools and, for each, what to do when the
   connector is missing. Missing data is a stated limitation in the output.
5. Write working files to `.seo/` in the project. Never to the repo.

## Editing the skills

- `docs/skill-template.md` is the required shape. Follow the section order.
- Run `python3 scripts/validate.py` before committing. It checks frontmatter,
  section presence, length, sibling references, and dash characters.
- Run `./scripts/sync-plugin.sh` after any change under `skills/` or `profiles/`,
  so the plugin copy in `plugins/seo-skills/` stays current. That directory is
  generated. Never edit it by hand.
- **No em dashes or en dashes anywhere in the repo.** Several skills teach a house
  style that bans them, so the repo practises it. Use commas, colons, or restructure.
- Keep brand, market, and vertical specifics out of skills. If a value would differ
  between two clients, it belongs in the profile.
- Do not add a metric a skill cannot source. Do not add a composite score without
  showing its inputs and weights.
- New skill means a new row in the README catalogue, a new row in the support
  matrix, and a CHANGELOG entry.

## The house voice

Imperative. Specific. No preamble, no flattery, no hedging into uselessness. A
skill that says "consider optimising your content" has failed. A skill that says
"this page targets a transactional term with an informational SERP, so it will not
rank as written: either rewrite it as a guide or move the target to the solution
page" has done its job.
