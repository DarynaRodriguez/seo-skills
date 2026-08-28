# Google's documentation is the source of record

Every recommendation in this pack traces to Google Search Central where Google has
documented a position. Where Google is silent, the pack says so and reasons from
evidence. Where the pack disagrees with Google, it says that too, and says why.

This file exists because SEO advice ages badly and folklore outlives the reason for
it. A rule nobody can source is a rule nobody can check.

**Fetched 2026-08-28.** Re-check before trusting anything here: Google edits these
pages, and the AI optimization guide was last updated 2026-07-10.

## The sources

| Topic | Page |
|-------|------|
| Optimizing for AI features | [ai-optimization-guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) |
| AI Overviews and AI Mode controls | [appearance/ai-features](https://developers.google.com/search/docs/appearance/ai-features) |
| Titles | [appearance/title-link](https://developers.google.com/search/docs/appearance/title-link) |
| Snippets and meta descriptions | [appearance/snippet](https://developers.google.com/search/docs/appearance/snippet) |
| Spam policies | [essentials/spam-policies](https://developers.google.com/search/docs/essentials/spam-policies) |
| JavaScript and rendering | [javascript-seo-basics](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics) |
| Structured data policies | [sd-policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies) |
| Which rich results exist | [search-gallery](https://developers.google.com/search/docs/appearance/structured-data/search-gallery) |
| The schema.org vocabulary and its data model | [schema.org/docs](https://schema.org/docs/documents.html), [datamodel](https://schema.org/docs/datamodel.html) |
| Page experience and ranking | [page-experience](https://developers.google.com/search/docs/appearance/page-experience) |
| How Core Web Vitals are measured | [PageSpeed Insights](https://developers.google.com/speed/docs/insights/v5/about) |
| Performance technique | [web.dev/performance](https://web.dev/performance) |
| Accessibility technique | [web.dev/accessibility](https://web.dev/accessibility) |
| E-E-A-T and content quality | [creating-helpful-content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content) |
| What Search Console's numbers mean | [performance data](https://support.google.com/webmasters/answer/7042828) |
| The IndexNow protocol | [indexnow.org](https://www.indexnow.org/documentation) |

## What Google says, and what this pack does about it

### There is no character limit on titles or descriptions

Google states there is no limit on the length of a `<title>` element or a meta
description, and that both are truncated in results "to fit the device width".
Neither is described as a ranking factor anywhere in those pages.

**So this pack measures pixels, not characters.** `seo.py meta` returns a width in
pixels with a `method` string naming how it was derived, because "fits the device
width" is a question about rendering, not about counting. The old folk rules of 60
characters and 155 characters are not Google's, have never been Google's, and are
wrong in both directions: 60 characters of Cyrillic is far wider than 60 of Latin,
and the pack's own width tables show it.

A width finding says a title will be truncated. It never says a title is
"too long", and it never implies a ranking effect.

### Optimizing for AI features is optimizing for Search

Google's position is direct: the best practices for SEO continue to apply, because
the generative AI features are built on the core Search ranking and quality systems.
It describes AEO and GEO as SEO reframed rather than as separate disciplines, and
says there are no additional requirements to appear in AI Overviews or AI Mode.

**So no skill here may sell an AI-specific technique as a separate lever.** The AI
skills in this pack exist because the *reporting* differs, not because the work does.

### Things Google explicitly says you do not need

Each of these is a live myth, and each is named in the AI optimization guide:

- **`llms.txt` and similar AI text files.** Google says these are ignored by Search
  and offer neither harm nor help. `/ai-crawler-access` already treats it as an
  optional convention with no measured gain; it now cites this.
- **Breaking content into small pieces for AI.** Google says there is no such
  requirement, and warns that generating separate content per query variation runs
  into the scaled content abuse policy.
- **A particular page length.** Google says there is no ideal page length.
- **Writing in a special way for generative AI.** Google says the systems understand
  synonyms and that chasing every long-tail variant is unnecessary.
- **Structured data, for AI features specifically.** Google says it is not required
  for generative AI search. It remains how rich results are earned, which is a
  different claim, and `/schema-builder` should make only that claim.
- **Inauthentic mentions.** Google says seeking them across the web is less helpful
  than it seems. `/citation-gap` is about earning genuine editorial citations, which
  is a different activity, but the skill must not read as a mention-acquisition
  programme.

### JavaScript, rendering, and soft 404s

Googlebot renders JavaScript using an evergreen Chromium, and indexes the rendered
HTML. Rendering is queued, and Google says a page may wait "a few seconds" or
considerably longer.

Google still recommends server-side rendering or pre-rendering, and gives the reason
this pack cares about: not all bots run JavaScript. That is the whole basis of the
`requires_js` finding. It is a real problem for non-Google fetchers, and a
performance and latency question for Google, not a claim that Google cannot see the
page.

**For single-page apps, Google documents the soft 404 fix**, because returning a
real status code from a client-side route is impractical. Either redirect to a URL
that serves a genuine 404, or inject `<meta name="robots" content="noindex">` on the
error view. A skill recommending "return a real 404" to an SPA team is giving advice
Google itself calls impractical.

### Scaled content abuse, and what it does and does not cover

Google's policy targets many pages made mainly to manipulate rankings rather than to
help people. Using generative AI to produce them is named as an example. Using AI is
not itself the violation; producing bulk low-value pages is.

**This matters for a pack that automates SEO work.** Nothing here should help
generate pages at scale without a person deciding each one is worth publishing. That
is why `seo-brief-writer` can return `do_not_publish`, and why `/content-brief`
refuses to brief a page whose angle nobody can name.

## Structured data: two sources, and only one of them draws lines

Schema.org and Google answer different questions, and conflating them is the most
common structured-data mistake in this field.

**Schema.org defines the vocabulary and requires nothing.** Its data model is
deliberately flexible: no property is ever required, an entity may carry properties
from several types at once, extra and unrecognised properties are allowed, and even
supplying text where an object is expected is explicitly not an error
([datamodel](https://schema.org/docs/datamodel.html)). Validators may warn, but the
project states they are not obliged to treat unexpected structures as errors.

**Google decides eligibility, and that is where "required" comes from.** Items
missing required properties are not eligible for rich results, markup must describe
content visible to readers, misleading markup can draw a manual action, and JSON-LD
is the recommended format
([sd-policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)).

So this pack says "required by Google for that rich result" and never "required".
A missing property is an eligibility problem, not a validity error. Telling someone
their markup is invalid when schema.org is perfectly happy with it sends them to fix
something that was already correct.

**Features get removed.** As of 2026-08-28, `FAQPage`, `HowTo` and `Book` have no
entry in the structured data gallery
([search-gallery](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)).
`seo_tools/audits.py` carries that list with the date it was checked, because a
stale "no rich result" note is the same defect as a stale "use this" note. Re-check
before trusting it in either direction.

**And structured data is not the route into an AI answer.** Google says it is not
required for generative AI search. It earns rich results, which is a real and
separate prize.

## Performance: real, measurable, and routinely oversold

The thresholds are not in dispute, and this pack uses them exactly as published:
LCP good at 2.5s or less, INP at 200ms or less, CLS at 0.1 or less, read at the
75th percentile of real users
([PageSpeed Insights](https://developers.google.com/speed/docs/insights/v5/about)).

**Field data and lab data answer different questions.** Field data is CrUX: real
users over a trailing 28 days. Lab data is Lighthouse: one simulated load on a
mid-tier device. They legitimately disagree, and where they do, the field data
describes your users and the lab data explains why. Quote which one you used.

**What Google actually claims about ranking**, and the pack must not exceed it:
Core Web Vitals are used by its ranking systems, and there is no single page
experience signal, good scores do not guarantee a top ranking, and Search shows the
most relevant content even where the page experience is sub-par
([page-experience](https://developers.google.com/search/docs/appearance/page-experience)).

So performance is worth doing because slow pages lose people and lose conversions,
and because it is one input among many to ranking. A team promised a ranking jump
and handed a conversion lift has still been misled.

**This pack cannot measure any of it.** `seo.py` is standard library only and never
renders, so every Core Web Vital comes from a provider or is reported as unknown.
It is never estimated.

## Accessibility: the pack already checks four criteria and never said so

Four of the checks here are WCAG success criteria that happen to also matter for
parsing, and each now carries its criterion and level in the finding:

| Check | Criterion |
|-------|-----------|
| `images.missing_alt` | 1.1.1 Non-text Content (Level A) |
| `heading.level_skipped` | 1.3.1 Info and Relationships (Level A) |
| `lang.missing` | 3.1.1 Language of Page (Level A) |
| `mobile.no_viewport` | 1.4.10 Reflow (Level AA) |

web.dev's guidance is that semantic HTML is the cornerstone, and its named
practices are structured documents, text alternatives, captions, visible focus
styling, adequate tap targets, accessible forms and a sensible heading structure
([web.dev/accessibility](https://web.dev/accessibility)).

**Four criteria is a floor, not a verdict.** Contrast, keyboard navigation, focus
order, ARIA correctness, tap target size, form error handling, captions and motion
control are all invisible to markup parsing, and each fails real users.
`/accessibility-audit` reports what was checked, names every category that was not,
and never calls a page accessible.

Accessibility is not a documented Google ranking factor and no skill here claims it
is. It is worth doing because more people can then use the page, and in many
jurisdictions because it is required by law.

## E-E-A-T, and the two things everyone gets wrong about it

Experience, Expertise, Authoritativeness, Trustworthiness
([creating-helpful-content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)).

**It is not a ranking factor.** Google states that E-E-A-T itself is not a specific
ranking factor, and that its systems use a mix of signals which tend to identify
content with good E-E-A-T. So it is a lens for judging a page, never a lever to
pull. No skill here may write "improve E-E-A-T to rank".

**Trust is the one that matters.** Google's wording is that of these aspects trust
is most important, that the others contribute to trust, and that content does not
necessarily have to demonstrate all of them. A page thin on Experience can still be
excellent. A page nobody has reason to believe cannot.

Google frames the self-assessment as **who, how and why**: who wrote it, how it was
made including whether automation is disclosed, and why it exists at all. All three
are checkable by looking at the page, which is what makes them usable in an audit
rather than a philosophy.

**One naming collision to avoid.** "Authority" in `/internal-linking` and
`/competitor-gap` means link equity and domain rating. "Authoritativeness" here
means whether a reader has reason to believe the page. Different concepts, and
blurring them produces advice to build links when the actual problem is an
anonymous byline.

`skills/page-optimiser/references/content-quality.md` carries the applied version,
in trust order, with what to flag on a live page.

## Search Console: the only real traffic number, and four ways to misread it

Search Console is the one source in this pack that reports traffic a site actually
received. Everything else is a model. That makes its quirks worth knowing, because
each one produces a plausible wrong answer rather than an error
([performance data](https://support.google.com/webmasters/answer/7042828)).

**Position is not additive.** It is the topmost placement seen, averaged per query.
A plain mean across rows weights a nine-impression query the same as a
ninety-thousand-impression one. `seo_tools/gsc.py` returns
`avg_position_impression_weighted` and names it that way, which is the least wrong
summary available and still discards the distribution.

**Position is not a rank.** Position 11 can be a desktop knowledge panel, the first
result on page two, or the second image row on mobile. Comparing position across
years without accounting for layout changes compares two different things.

**Rows do not sum to totals.** Group by query or by page and the numbers will not
reconcile with the property total, because one result element can carry several
URLs and is counted once per property and once per URL. A report whose rows do not
add up is not necessarily broken.

**Low-frequency queries are anonymised away.** Query-level clicks are a floor, not
the truth, and the gap is largest exactly where a long tail matters most.

The practical rule for this pack: weight findings by clicks, which are countable,
and treat position as a direction rather than a measurement.

## Other engines document themselves, and IndexNow is not a Google lever

Google's docs say nothing about other engines, and have no reason to. Where this
pack covers Bing, Naver, Seznam or the AI fetchers, the source is each operator's
own documentation, and the pack says which.

**IndexNow** is worth knowing precisely because its name suggests more than it
delivers ([protocol](https://www.indexnow.org/documentation)):

- **Google is not a participant.** It tested the protocol and never adopted it.
  Recommending IndexNow to fix a Google indexing problem is the single most likely
  error here, and the name invites it.
- **Participants are Bing, Yandex, Seznam, Naver and Yep.** Submitting to one
  shares the URL with the others. Through Bing it reaches Copilot, which is the
  part that matters for AI visibility work.
- The implementation is a key file at the domain root and either a GET per URL or
  a POST carrying up to 10,000. Cheap enough that the usual objection is ownership
  rather than cost.

`/indexation-check` carries it as a step, framed as a discovery fix for those
engines and explicitly not for Google.

## What is not a source of truth

Worth stating, because the alternative is a pack that quietly mixes evidence with
folklore:

- **Correlation studies** describe what co-occurs, not what causes. `/citation-gap`
  uses one, and it is legitimate as evidence about how answers get assembled and
  illegitimate as a mechanism. Label it that way wherever it appears.
- **Vendor ranking-factor lists** are marketing built on correlation. They are not
  sources of record and nothing here should cite one as though they were.
- **Blog consensus**, including good blogs. If a claim only exists because people
  repeat it, it goes in the folklore bin. The 60-character title rule lived there
  for a decade.
- **This pack's own past output.** An audit is evidence about one site on one day,
  not a general rule.

The test in `AGENTS.md` stands: cite a primary source, cite an operator's own docs,
or label it as this pack's judgement.

## Where this pack goes beyond Google

Google documents what it does; it does not document what other engines do, and it
has no reason to. These are the places the pack reasons past Google, and each is
labelled as such rather than dressed up as guidance:

- **Non-Google engines.** Google's docs say nothing about ChatGPT, Perplexity, Claude
  or Copilot fetchers, or about Yandex, Baidu, Naver and Seznam. The crawler tables
  in `seo_tools/robots.py` come from each operator's own documentation.
- **Pixel widths.** Google says truncation fits the device width but publishes no
  width table. The pack derives widths from font metrics and labels every number as
  an estimate rather than a render.
- **Severity.** Google does not grade issues. The critical, warning and info scale
  here is the pack's own judgement about what breaks a page versus what tidies it.
- **Traffic weighting.** Ranking findings by clicks at risk is a prioritisation
  choice, not a Google recommendation.

## The rule for contributors

If a skill states a threshold, a limit, or a "best practice", one of three things
must be true:

1. It cites a Google page, and the citation says what the skill says it says.
2. It cites another operator's own documentation, for something Google does not cover.
3. It is labelled as this pack's judgement, in the skill's own voice.

Anything else is folklore, and folklore is what this file exists to keep out.
