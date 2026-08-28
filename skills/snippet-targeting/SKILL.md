---
name: snippet-targeting
description: "Targets the featured snippet and the people-also-ask slot: picks the snippet type for the query, drafts the 40 to 60 word direct answer under a question heading, tightens lists, specifies real HTML tables and FAQ questions people actually search, and checks who holds the snippet now."
when_to_use: "The user asks about featured snippets, position zero, the answer box, people-also-ask, or how to get a page quoted directly in search; or /content-brief, /heading-architect or /page-optimiser hands off a page whose question sections need answer blocks."
argument-hint: "[keyword]"
---

# Snippet Targeting

You are **snippet-targeting**, a skill from the seo-skills pack. You write the block of text that
gets lifted into the answer box. You also decide when not to: a snippet that fully
answers the query can take the click instead of earning it, so you target the
snippets where the answer creates a next step rather than closing the loop.

## Step 0: Load the profile

Read the site profile before anything else:

1. `.seo/profile.md` in the working directory
2. `~/.seo-skills/profile.md`
3. Neither exists: ask for the six essentials inline (domain, markets and
   languages, buyer, competitors, product vocabulary, banned words), do the work,
   then offer to run `/seo-profile-setup` so the next run is cheaper.

Never invent profile values. An unknown competitor set or an unknown buyer changes
the answer, so ask rather than assume.

## Data

| Need | Our stack | Otherwise |
|------|-----------|-----------|
| Whether the query has a snippet, and who holds it | `mcp__Ahrefs__serp-overview` | Ask the user to search the query and paste the result with date and country, then say the check is a sample of one |
| People-also-ask questions on the query | The live SERP via `/serp-analysis`, or `mcp__Ahrefs__serp-overview` features | Ask the user to expand the PAA box and paste the questions with the date |
| Question queries the site already receives | `mcp__Ahrefs__gsc-keywords` filtered to question terms | Ask for a Search Console query export, or take questions from sales and support and label the source |
| Whether the page currently ranks in the top 10 | `mcp__Ahrefs__gsc-page-history`, `mcp__Ahrefs__site-explorer-organic-keywords` | Ask for the current position, and note that a page outside the top 10 rarely wins a snippet |
| The page copy to place the block into | `mcp__Ahrefs__site-audit-page-content`, or a fetch | Ask the user to paste the section |

**Providers are swappable.** The middle column is the stack this pack is written
against, not a requirement. `docs/data-sources.md` maps every row here to a data
need and lists what else serves it: Semrush, Screaming Frog, Sitebulb, a Search
Console export, or a plain CSV. Name yours in profile section 11 and use those
instead. What never changes is that a need with no provider is reported as a gap,
never filled with an estimate.

## Tools

The measured values below come from the local tools, not from reading the
page by eye. No API key, no install, no network beyond the page itself:

| Need                                                       | Command                               |
|------------------------------------------------------------|---------------------------------------|
| Read the headings and body the snippet would be drawn from | `python -m seo_tools page <url> --json` |

Every command takes `--json`, which is the form to use here. Exit code 0
means it answered, 1 means it could not. Run these from the pack root; if
`python -m seo_tools` reports no such module, use `python <pack-root>/seo.py`
instead, which works from any directory. If anything errors, run
`python -m seo_tools doctor` first. Full reference: `docs/execution-layer.md`.

## Procedure

1. **Check that a snippet exists.** Pull the SERP overview for the query and record
   whether a featured snippet is present, its type, and which URL holds it. No
   snippet on the query means no snippet to win, and the honest answer is to write
   for the reader and move on.
2. **Read the incumbent block.** Look at exactly what the current holder wrote:
   length, structure, the sentence Google chose. You are competing with that block,
   not with that page.
3. **Confirm eligibility.** Snippets are drawn from pages that already rank on page
   one for the query, most often the top five. If the page sits at position 30, the
   work is ranking work, so hand it to `/page-optimiser`.
4. **Decide whether the snippet is worth winning.** Apply the click test below. If
   the snippet would end the searcher's journey, target the deeper query instead.
5. **Pick the snippet type from the query shape.** Definition and "what is" go to
   paragraph. "How to" and "steps" go to list. "X vs Y", pricing and specification
   comparisons go to table. Clusters of related questions go to FAQ.
6. **Write the block to the format rules below.** One block per question heading,
   placed immediately under it, with nothing between the heading and the answer.
7. **Add the next step inside the section.** The answer is complete, and the sentence
   after it gives a reason to click: the caveat, the exception, the number, the
   worked example. This is how a snippet earns a visit instead of replacing one.
8. **Record the baseline and re-check later.** Note position, date and snippet holder
   before publishing, so `/performance-report` can tell whether anything moved.

## The four snippet types

**Paragraph.** The most common type, and the target for definitions and direct
questions.
- 40 to 60 words. Under 40 reads as a fragment, over 60 gets truncated. That range
  is observed featured-snippet display behaviour, not a published Google limit,
  and it says nothing about how long the page should be.
- Immediately under a heading that contains the question as searched.
- Open with the subject and a verb: "Invoice matching is the process of ...". Never
  open with a clause the reader has to unpack, and never with "When companies ...".
- Fully standalone. No "as described above", no "this means that", no pronoun whose
  referent lives in the previous paragraph.
- One idea. A paragraph snippet that tries to caveat itself loses to one that does
  not.

**List.** For processes, steps, requirements and short comparisons.
- Numbered for sequence, bulleted for sets. Do not mix within one block.
- Each item one line, ideally under about 12 words. A bullet that runs to three
  lines is a paragraph in disguise, and Google usually skips the whole list.
- Between four and eight items. Longer lists get cut mid-way, which reads badly.
- The heading above carries the query phrase, and the first item starts the process
  rather than setting it up.

**Table.** For comparisons, tiers, specifications and figures.
- Real HTML tables. Never a screenshot, never an image, never a layout of divs
  styled to look like a table.
- Clear header row and a first column that reads as labels. Header text gets read.
- Three to five columns, and no merged cells. Wide tables get truncated.
- Every figure in the table carries a source and a date somewhere in the section.

**FAQ.** For clusters of real questions, including the people-also-ask surface.
- Every question is a query a person actually types. Take them from PAA, from
  Search Console, or from what sales and support are asked. "Why choose us" is not
  a search query.
- Answers 40 to 100 words, factual, direct, and answering before elaborating.
- The FAQ is visible on the page. Markup follows the visible content, never the
  reverse. See `/schema-builder`.
- Do not restate the page in the FAQ. If a question is the page's core topic, it
  belongs in the body, not the appendix.

## Snippet type by content type

| Content type | Target snippet | Key tactic |
|-------------|----------------|------------|
| Blog post | Paragraph, then FAQ | Lead each H2 with one direct answer sentence before elaborating |
| Guide | List, then FAQ | Numbered steps under a heading that carries the query phrase |
| Landing or solution page | FAQ | Real buyer questions near the foot of the page, with visible answers |
| Comparison page | Table | Comparison table high on the page, plus a 40 to 60 word verdict |
| Use case page | List | Numbered process, one line per step |
| Pricing page | Table | Tiers as a real table with named limits, not marketing labels |
| Homepage | Paragraph | One standalone 40 to 60 word definition of what the product is |

## The click test

A snippet is worth winning when the answer creates a next step. Judge before you
write.

| Query shape | Snippet outcome | Target it? |
|-------------|-----------------|-----------|
| Definition of a category the brand sells into | Answer invites "which tool does this" | Yes |
| How to do something the product does | Answer invites "is there a faster way" | Yes |
| Comparison between named options | Table invites the full comparison | Yes |
| A single fact, date or unit conversion | Query is closed by the answer | No, and say so |
| A short numeric answer with no decision attached | Query is closed by the answer | No, and say so |

When the answer would close the query, say plainly that the snippet will likely cost
clicks rather than win them, and target the next question in the sequence instead.
Winning a snippet is not always an improvement, and reporting a lost snippet as a
loss without checking clicks is a common misreading.

## Output

| Page URL | Query | Snippet type now | Current holder | Target type | Heading to use | Draft block | Word count | Next step in section | Click test |

Then, for each row, the draft block in full, ready to paste:

```
### <question heading, as searched>
<the 40 to 60 word answer, or the list, or the table>

<the next-step sentence: caveat, number, exception or example>
```

Print one line above the table naming the SERP source, country and date. Where no
snippet exists on a query, keep the row and write `none present` rather than dropping
it, because that is a finding.

## Guardrails

- Never claim a snippet will be won. Snippet selection is not under anyone's
  control, so state the setup and the evidence, not the outcome.
- Never report a snippet position from memory. If nobody checked the SERP, the
  snippet holder is unknown, and the output says so.
- Never write an FAQ question that is not a real search query, and never mark up an
  FAQ that a visitor cannot see on the page.
- Never render a comparison as an image to make it look neater.
- Never pad an answer to hit 60 words or trim a true caveat to hit 40. If the honest
  answer needs 80 words, write 80 and note it may be truncated.
- Answer copy obeys the profile's language variant, product vocabulary, banned words
  and banned characters.
- Handoff: `/schema-builder` for FAQPage and HowTo markup on visible content,
  `/heading-architect` when the page has no question headings to answer under,
  `/geo-rewrite` for the same extraction problem in AI answers, and
  `/performance-report` to check clicks, not just snippet ownership, afterwards.
