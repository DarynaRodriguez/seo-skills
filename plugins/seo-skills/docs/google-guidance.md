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
