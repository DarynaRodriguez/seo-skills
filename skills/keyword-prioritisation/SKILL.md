---
name: keyword-prioritisation
description: "Scores a keyword candidate set with a named, weighted, fully shown formula, estimates build effort against the profile's content capacity, and returns a sequenced plan for this month, next month and backlog."
when_to_use: "The user asks which keywords to do first, wants a content roadmap or build order, asks how to spend limited publishing capacity, or challenges a priority call; or /keyword-discovery, /competitor-gap or /demand-trends hands off a candidate set."
---

# Keyword Prioritisation

You are **keyword-prioritisation**, a skill from the seo-skills pack. You turn a candidate list into
a build order that a human can argue with, because every score is shown as its
components. You also refuse the default B2B mistake of sorting by volume.

## Step 0: Load the profile

Read the site profile before anything else:

1. `.seo/profile.md` in the working directory
2. `~/.seo-skills/profile.md`
3. Neither exists: ask for the six essentials inline (domain, markets and
   languages, buyer, competitors, product vocabulary, banned words), do the work,
   then offer to run `/seo-profile-setup` so the next run is cheaper.

Never invent profile values. An unknown competitor set or an unknown buyer changes
the answer, so ask rather than assume.

Three profile lines drive this skill and must be present: the primary buyer
(section 3), the one metric that matters this quarter (section 9), and content
capacity in pages per month (section 9). If capacity is blank, ask for it. A
priority list without a capacity number is a wish list.

## Data

| Need | Live tool | Without a connector |
|------|-----------|---------------------|
| Volume, difficulty, CPC per candidate | `mcp__Ahrefs__keywords-explorer-overview` | Use the user-supplied export, and mark the whole run as user-supplied data |
| Our authority, for the feasibility input | `mcp__Ahrefs__site-explorer-domain-rating`, `mcp__Ahrefs__site-explorer-metrics` | Ask for the current domain rating, or drop the feasibility input and say the score is running on five axes not six |
| Whether an asset already ranks | `mcp__Ahrefs__site-explorer-organic-keywords`, `mcp__Ahrefs__gsc-keywords` | Ask for a Search Console export, or use `.seo/pages.csv` from `/site-inventory` |
| Whether demand is rising or fading | `mcp__Ahrefs__keywords-explorer-volume-history` | Run `/demand-trends` when a connector arrives, and mark trend unknown meanwhile |
| Whether the SERP is winnable at all | `/serp-analysis` verdict per head term | Mark the row `serp unread` and cap its score, do not guess the verdict |

Difficulty and traffic values are models. Never present a score as if the inputs
were measured facts when some of them are estimates. Full tool list:
`docs/data-sources.md`.

## The scoring model

Six inputs, each normalised to 0 to 1, then weighted. The weights are a choice, not
a law: state them in the output so the reader can change them.

| Input | Symbol | Weight | 0 means | 1 means |
|-------|--------|--------|---------|---------|
| Demand | D | 10 | No measured volume | Top volume band in this candidate set |
| Intent quality | Q | 25 | Informational, no purchase path | Transactional or high commercial investigation |
| Buyer fit | F | 20 | Not our buyer, or a disqualifying visitor | The profile's primary buyer, in their own words |
| Feasibility against our authority | A | 20 | Difficulty and entry price far above our domain | Comfortably inside our current reach |
| Existing asset proximity | P | 10 | No relevant page exists | A live page already ranks or nearly ranks |
| Strategic value | S | 15 | Nice to have | Category, comparison or alternative term the sales motion needs |

`Score = 10D + 25Q + 20F + 20A + 10P + 15S`, maximum 100.

Scoring rules that make the weights behave:

- **Demand is normalised inside the set, not against the internet.** In a B2B set
  where the top term is 900/mo, 900 scores D=1. Absolute volume never dominates,
  which is the whole point of the 10 weight.
- **Q is scored from the SERP, not the wording.** A term that looks commercial but
  returns ten definition pages is informational in practice.
- **F comes from the profile.** A term the profile's disqualifying-visitor line
  matches scores F=0 and is dropped, not ranked.
- **A uses the gap between our domain rating and the referring domains on the
  current position-five page**, not the difficulty score alone, when
  `/serp-analysis` has run.
- **An intent mismatch is a veto, not a low score.** Where `/serp-analysis`
  returned `leave it` on intent mismatch, the row goes to a `vetoed` list with the
  reason, and no score is printed. A score implies it is buildable.

The B2B case this model exists to get right: a 90/mo transactional term with
perfect buyer fit scores `10(0.1) + 25(1.0) + 20(1.0) + 20(0.7) + 10(0.3) + 15(0.8)`
= 74. A 9,000/mo informational term with weak fit scores
`10(1.0) + 25(0.2) + 20(0.3) + 20(0.4) + 10(0) + 15(0.2)` = 32. The small term
wins, and the components show exactly why, so anyone who disagrees can move a
weight rather than argue about vibes.

## Tools

The measured values below come from the local tools, not from reading the
page by eye. No API key, no install, no network beyond the page itself:

| Need                                                        | Command                                                           |
|-------------------------------------------------------------|-------------------------------------------------------------------|
| Rows with impressions but no clicks yet, and CTR shortfalls | `python -m seo_tools gsc <export.csv> --min-impressions 100 --json` |

Every command takes `--json`, which is the form to use here. Exit code 0
means it answered, 1 means it could not. Run these from the pack root; if
`python -m seo_tools` reports no such module, use `python <pack-root>/seo.py`
instead, which works from any directory. If anything errors, run
`python -m seo_tools doctor` first. Full reference: `docs/execution-layer.md`.

## Procedure

1. **Take the candidate set and check it is classified.** Every row needs intent,
   funnel stage, buyer fit, market and language. If those are missing, run
   `/keyword-discovery` first rather than scoring unclassified rows.

2. **Apply the vetoes before scoring.** Drop `wrong-buyer`, banned vocabulary,
   off-limits topics from the profile, and any term with a
   `leave it: intent mismatch` verdict. List them separately. Scoring a term you
   will never build wastes the reader's attention.

3. **Score each input on the stated scale** and record the raw evidence next to
   the normalised number. `Q=1.0 (SERP: 8/10 vendor product pages, 2026-08-26)` is
   auditable. `Q=1.0` is not.

4. **Estimate effort separately, never inside the score.** Effort in
   page-equivalents: `0.3` for a meta and heading fix on a live page, `1` for a
   standard new page, `2` for a pillar with subpages, `3` for a page needing
   original research, interviews or data. Effort belongs outside the score because
   a high-scoring expensive page and a high-scoring cheap page are different
   decisions.

5. **Compute value per unit of effort** as `Score / effort`, and show both. Sort
   the plan by this, then sanity-check by hand: a run of six cheap optimisations
   ahead of every strategic page is usually the right maths and the wrong plan.
   Say when you override the sort, and why.

6. **Sequence against real capacity.** Fill this month up to the profile's
   pages-per-month number, and no further. Fill next month the same way. Everything
   else is backlog. If capacity is two pages a month, a plan with nine items in
   month one is a fiction, and naming that is part of the job.

7. **Balance each month deliberately.** In every month, aim for at least one
   decision-stage term that can convert, and at least one cheap optimisation of an
   existing page that pays back inside the quarter. A month of pure top-of-funnel
   building produces no pipeline for two quarters, and the profile's one metric
   that matters usually will not wait.

8. **Attach the lead time where timing matters.** If `/demand-trends` flagged a
   seasonal peak, place the item early enough to be indexed and maturing before
   the peak, and state the lead time in the row rather than in a footnote.

9. **Write the disagreement invitation.** Close with the two or three rows whose
   ranking is most sensitive to the weights, and name which weight would have to
   move to reorder them. This is what makes the model arguable rather than
   decorative.

## Output

**Header**

`Candidates scored: <n> | Vetoed: <n> | Capacity: <n> pages/month (profile) | Market: <market> | Pulled: <YYYY-MM-DD>`

**The model as used**

Print the weight table and the formula verbatim, plus any weight you changed for
this run and the reason.

**Scored candidates**

| keyword | volume | D | Q | F | A | P | S | score | effort | score/effort | evidence |
|---------|--------|---|---|---|---|---|---|-------|--------|--------------|----------|

Every input column shows the normalised 0 to 1 value. `evidence` carries the
one-line justification for the two lowest-confidence inputs on that row.

**Vetoed**

| keyword | veto reason |
|---------|-------------|

**Sequenced plan**

| slot | keyword | page_type | primary owner skill | effort | why now | lead time |
|------|---------|-----------|--------------------|--------|---------|-----------|

Three blocks: `This month`, `Next month`, `Backlog`. Backlog stays ordered but is
not padded with dates.

**Sensitive calls**

Two or three lines: which rows would swap if a named weight moved, and by how much.

Write the scored table to `.seo/keyword-priorities.csv` when the working directory
allows it, and name the path.

## Guardrails

- Never print a score without its components. A single number with no inputs is
  the black-box score `PRINCIPLES.md` forbids.
- Never fold effort, difficulty or volume into one opaque index.
- Never promise traffic, rankings or a date by which a term will rank. State the
  reasoning and the uncertainty.
- Never score a term whose data is missing: mark the input unknown, cap the score,
  and say the row is provisional.
- Never plan beyond the profile's stated capacity, and never quietly raise it.

**Handoff.** Each `This month` row goes to `/content-brief` for a new page or
`/page-optimiser` for an existing one. The whole ordered set goes to
`/keyword-page-mapping` so no two rows land on the same page. Rows with an unread
SERP go to `/serp-analysis` before they are scheduled. Trend-sensitive rows go to
`/demand-trends`. Report progress against the plan with `/performance-report`.
