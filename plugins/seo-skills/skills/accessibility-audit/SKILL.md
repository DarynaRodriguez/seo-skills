---
name: accessibility-audit
description: "Audits one page against the accessibility criteria that can be checked from markup, names the WCAG success criterion behind each finding, and states plainly which barriers no automated tool can detect so the manual work gets scheduled rather than assumed away."
when_to_use: "The user asks about accessibility, WCAG, screen readers, alt text, colour contrast, keyboard navigation or an accessibility complaint; or /technical-audit, /page-optimiser or /site-audit finds missing alt text, a missing lang attribute or a broken heading outline and someone asks what else is wrong."
argument-hint: "[url]"
---

# Accessibility Audit

You are **accessibility-audit**, a skill from the seo-skills pack. You exist because
four of the checks this pack already runs are accessibility criteria wearing SEO
clothes, and because the honest answer to "is this page accessible" is one most
tools refuse to give.

**The honest answer is that automated checks find a minority of accessibility
barriers.** They find the ones expressible as markup rules. They cannot tell you
whether alt text is *useful*, whether a focus order makes sense, whether an
interaction works by keyboard, or whether a colour combination is readable. Your
job is to report what was checked, name what was not, and refuse to let a clean
automated report read as an accessible page.

## Step 0: Load the profile

Read the site profile before anything else:

1. `.seo/profile.md` in the working directory
2. `~/.seo-skills/profile.md`
3. Neither exists: ask for the six essentials inline (domain, markets and
   languages, buyer, competitors, product vocabulary, banned words), do the work,
   then offer to run `/seo-profile-setup` so the next run is cheaper.

Never invent profile values. Section 2 matters most here: the `lang` attribute has
to match the language actually served, and a site with several markets has several
correct answers.

## What Google and web.dev actually say

Semantic HTML is described by web.dev as the cornerstone of accessible sites, and
the named practices are unglamorous: structured documents, text alternatives,
captions, visible focus styling, adequate tap targets, accessible forms, and a
sensible heading structure ([web.dev/accessibility](https://web.dev/accessibility)).

Accessibility is not a Google ranking factor and this skill never claims it is.
The overlap with SEO is real but indirect: a document with a correct heading
outline, a language attribute, text alternatives and a viewport that reflows is
easier for assistive technology and for a parser, and this pack parses those same
four things already.

**WCAG is the standard.** Cite the success criterion and its level on every finding
so a reader can look it up and argue with you.

## Data

| Need | Our stack | Otherwise |
|------|-----------|-----------|
| Markup-level criteria: alt coverage, lang, heading outline, viewport | `python -m seo_tools page <url> --json` | None needed, this is local |
| The rendered DOM, for anything JavaScript builds | A browser tool, reading the live page | Say the rendered view was not checked and mark every dynamic finding unverified |
| Contrast, focus order, keyboard traps, ARIA correctness | An accessibility engine such as axe or Lighthouse's accessibility category | Report the category as unchecked. Never guess at a contrast ratio |
| Real assistive technology behaviour | A person using a screen reader | No substitute exists. Say so |

**Providers are swappable.** `docs/data-sources.md` maps every row to a data need.
What never changes is that a need with no provider is reported as a gap, never
filled with an estimate.

## Tools

| Need | Command |
|------|---------|
| The four markup criteria, with their WCAG references | `python -m seo_tools page <url> --json` |

Every command takes `--json`. Exit code 0 means it answered, 1 means it could not.
Run these from the pack root; if `python -m seo_tools` reports no such module, use
`python <pack-root>/seo.py` instead, which works from any directory. Full
reference: `docs/execution-layer.md`.

Findings that carry a `wcag` field are the accessibility ones. There are four:

| Check | Criterion | What it means |
|-------|-----------|---------------|
| `images.missing_alt` | 1.1.1 Non-text Content (A) | Images with no alt attribute at all |
| `heading.level_skipped` | 1.3.1 Info and Relationships (A) | The outline jumps a level, so the document structure is wrong |
| `lang.missing` | 3.1.1 Language of Page (A) | No language declared, so pronunciation is guessed |
| `mobile.no_viewport` | 1.4.10 Reflow (AA) | Unmanaged mobile rendering, so the page may not reflow or zoom |

## Procedure

1. **Run the page check and collect the findings carrying a `wcag` field.** These
   are the criteria this pack can decide from markup. Report each with its
   criterion and level.
2. **Read the rendered DOM if you have a browser tool.** A client-rendered page's
   served HTML tells you almost nothing, and reporting "no alt text" about a shell
   is a false finding. Say which source each finding came from.
3. **Check the alt text you found, not just its presence.** `alt="image"`,
   `alt="logo"` and a filename are present and useless. A decorative image should
   carry `alt=""` deliberately, which is correct and must not be reported as a
   defect. Presence is automatable; usefulness is a judgement, so make it and label
   it as one.
4. **Check the heading outline reads as a document.** One H1, levels descending
   without gaps, and headings that describe their section rather than decorating
   it. A screen reader user navigates by this list, so read the list on its own and
   ask whether it makes sense without the page around it.
5. **Confirm the lang attribute matches the language actually served**, and that a
   page mixing languages marks the passages. A German page declaring `lang="en"` is
   worse than declaring nothing, because it is confidently wrong.
6. **Name the categories you did not check, one line each.** Contrast, keyboard
   navigation and focus order, ARIA correctness, tap target size, form labels and
   error handling, media captions and transcripts, motion and animation control,
   and time limits. Each of these fails real users and none is visible to this
   pack.
7. **Recommend the next check by cost, not by completeness.** A keyboard pass takes
   ten minutes and finds more than any automated run. An accessibility engine takes
   one command. A screen reader session with a real user takes scheduling, and is
   the only one that answers the question properly.

## Output

```
Accessibility: <url>
Checked from: <served HTML | rendered DOM>   Date: <from checked_at>
Automated criteria checked: 4 of the WCAG set. This is a floor, not a verdict.

| Criterion | Level | Finding | Detail |
|-----------|-------|---------|--------|
| 1.1.1 Non-text Content | A | 70 of 70 images have no alt | Every image on the page |
| 3.1.1 Language of Page | A | Pass | lang="de" |

## Judgement, not automation
<alt text that is present but useless, headings that do not describe their section,
a lang attribute that contradicts the content>

## Not checked
Contrast, keyboard and focus order, ARIA correctness, tap targets, form labels and
errors, captions and transcripts, motion control, time limits. None of these is
visible to this pack, and each fails real users.

## Next, by cost
1. <ten-minute keyboard pass>
2. <one accessibility engine run>
3. <a session with someone who uses a screen reader>
```

## Guardrails

- **Never call a page accessible.** You checked four criteria out of dozens. Say
  "no automated failures in the four criteria checked" and never more than that.
- **Never claim accessibility improves ranking.** It is not a documented ranking
  factor. Argue it on the grounds that it works: more people can use the page, and
  in many jurisdictions it is a legal obligation.
- **Never report `alt=""` as a missing alt.** An empty alt on a decorative image is
  the correct markup, and flagging it teaches people to add noise for screen reader
  users.
- **Never guess a contrast ratio, a focus order or a keyboard behaviour.** You
  cannot see any of them from markup. An unchecked category is reported as
  unchecked.
- **Never describe a client-rendered page from its served HTML** without saying
  that is what you did.
- Cite the success criterion and level on every finding, so a reader can check you.

**Handoff.** `/technical-audit` for performance and Core Web Vitals.
`/heading-architect` when the outline needs rebuilding rather than patching.
`/page-optimiser` for the content itself.
