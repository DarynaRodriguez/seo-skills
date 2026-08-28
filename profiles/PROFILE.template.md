# Site profile

Written by `/seo-profile-setup`. Every skill in the pack reads this first.
Save to `.seo/profile.md` in the project you work in, or `~/.seo-skills/profile.md`
to use it everywhere. Delete any line you cannot answer honestly, and leave the
gap visible: a blank is information, a guess is not.

## How to write an unknown

`<unknown>` on its own tells the next skill that a value is missing and nothing
else. It cannot tell whether to ask a person, run a tool, connect a provider, or
leave it alone, so every skill downstream makes that call again from scratch.

**Qualify it where the reason changes what happens next.** A qualified unknown is
routing information rather than an absence:

| Write | Means |
|-------|-------|
| `<unknown - requires research>` | A skill can find this. Do not ask a person to guess it |
| `<unknown - provider unavailable>` | A tool would answer it and no tool is connected |
| `<unknown - not yet decided>` | A person has to choose, and has not yet |
| `<unknown - not verified>` | Somebody believes this, and nothing has confirmed it |

`<unknown - not verified>` is the one people skip, and it is the most useful.
"I think our AI crawlers are allowed, the platform handles it" is a belief. Written
as "AI crawlers: allowed" it becomes a fact nobody checked, and every skill after it
inherits the error. Written as
`<unknown - not verified, believed allowed via the platform>` it stays a belief and
becomes something `/ai-crawler-access` can settle in one command.

**Never use the qualifier to smuggle in a value.**
`<unknown - probably around 500 a month>` is a guess wearing a disclaimer.

---

## 1. Site

- **Brand name:** <exact capitalisation, as it must always appear>
- **Primary domain:** <example.com>
- **CMS / platform:** <Webflow, HubSpot, WordPress, Next.js, other>
- **Who can publish:** <name and role of the human who approves live changes>
- **Analytics and search data available:** <GSC property, Ahrefs project, Peec project, none>

## 2. Markets

| Market | Language variant | Domain or path | Primary search engine |
|--------|-----------------|----------------|----------------------|
| <UK> | <English, UK spelling> | <example.com/> | <Google google.co.uk> |
| <Germany> | <German, formal Sie> | <example.com/de/> | <Google google.de> |

- **hreflang pairs in use:** <en-gb ↔ de, or none>
- **Market priority order:** <which market's rankings matter most this quarter>

Fill in the search engine column honestly rather than writing Google everywhere.
Nothing in this pack assumes a market: the skills read this table, and a market
served by Yandex, Baidu, Naver or Seznam gets checked against that engine's
crawler instead of Googlebot. Leaving it as Google in a market where Google is not
the leader produces an audit that passes while the site is invisible.

Two notes for the tools, which follow from this table rather than from any default:

- **Script.** Chinese, Japanese, Thai, Lao, Khmer and Burmese do not separate words
  with spaces, so word counts in those markets are reported per character and
  labelled as such. Every title and description decision is made in pixels, never
  in characters, because a 28-character Japanese title fills more of the result
  than a 45-character English one.
- **Search Console exports.** The export header is localised. The tools recognise
  14 languages; anything else is named positionally with `--columns`. See
  `docs/execution-layer.md`.

## 3. Who this is for

**Two shapes. Keep the one that fits and delete the other**, because a buying
committee and a person in a life stage need different questions, and answering the
wrong set produces a profile full of `<unknown>` that is not actually unknown.

<!-- KEEP ONE: business audience -->

- **Primary buyer:** <role, seniority, company size, industry>
- **Secondary buyer or influencer:** <role>
- **The job they are trying to get done:** <in their words, not yours>
- **What disqualifies a visitor:** <who this product is not for>
- **How they search:** <do they search the category, the problem, a competitor, or a compliance term>

<!-- KEEP ONE: consumer audience -->

- **Primary audience:** <who they are, in their own words>
- **Life stage or situation:** <what is true of them right now that makes this relevant, and for how long>
- **Where they are:** <country, city, or a situation such as newly arrived, remote, shift work>
- **The need state:** <what they are trying to sort out, in the words they would use to a friend>
- **What disqualifies a visitor:** <who this is not for>
- **How they search:** <do they search the problem, a procedure or form name, a place, or in a second language>

Note for non-English audiences in a non-English country: **the language they search
in is a real question and often not the language of the site.** Record it here, not
just in section 2, because it decides whether the whole keyword set is viable.

## 4. What we offer

- **Category we compete in:** <the words the audience uses, not internal branding>
- **What it actually does:** <two sentences, no adjectives>
- **How it is paid for, if at all:** <subscription, one-off, free, free pilot, ad supported, grant funded>
- **Proof we can cite:** <named customers or users, verified numbers, certifications, credentials, published sources>
  Keep each entry to something quotable in public. Personal detail written here
  will end up in copy, because an agent reads this as material it may use.
- **Claims we may not make:** <anything legal, medical, financial, security or product has not signed off>

## 5. Product vocabulary

| Always write | Never write |
|-------------|-------------|
| <Product Name> | <product name in lower case, abbreviations> |
| <platform> | <tool, solution, software> |
| <Approved feature name> | <internal codename> |

## 6. Language rules

- **Spelling variant:** <UK English / US English / German>
- **Banned characters:** <em dash, en dash in body copy, none>
- **Banned words and phrases:** <leverage, unlock, seamlessly, game-changer, revolutionise, cutting-edge, robust, in today's fast-paced world>
- **Numbers:** <% with numerals, no spelled-out percentages>
- **Tone in one line:** <how a smart peer would say it out loud>
- **Voice position:** <who the writing sounds like, such as someone who has done this before>
- **Reader address:** <what to call the reader, and what never to call them>

**Voice position and reader address are different fields on purpose.** "Sounds
like another parent who has been through it" is a stance. It does not license
calling every reader "mama", and an agent given only the stance will infer the
address from it and produce exactly the copy the stance was meant to avoid.

## 7. Competitive landscape

**"Competitor" means three different things and downstream skills use them
differently.** Keep them apart. A forum in the product row is how `/competitor-gap`
ends up comparing you to Reddit, and how `/keyword-discovery` tries to pull ranking
data for a Facebook group.

### Product alternatives

What someone would use instead of this. `none` and `<unknown>` are both real
answers, and for a product with no direct equivalent, `none` is the honest one.

| Name | What they do instead | Where they beat us |
|------|---------------------|-------------------|
| <Name> | <the job they solve instead> | <what they are genuinely better at> |

### Organic search competitors

Domains that rank for the terms you want. **Only list a domain here once search data
shows it ranking**, and say what showed it. A name offered in an interview is a
hypothesis, not a search competitor, and promoting it silently puts unverified input
into every skill that reads this.

| Domain | Verified by | Why they show up | Where they beat us |
|--------|-------------|-----------------|-------------------|
| <domain> | <Ahrefs project, SERP read with date, or UNVERIFIED> | <ranks for our category terms> | <domain authority, content depth, brand> |

### Information alternatives

Where the audience gets answers that are not a product: forums, communities,
official sources, group chats. Some you can compete with. Some you should not try
to, and an official source is usually one to cite rather than outrank.

| Source | Why it wins | Can we compete for this query |
|--------|------------|------------------------------|
| <forum, community, official page> | <peer experience, authority, freshness> | <yes, partly, no and we link to it instead> |

### Comparison-content policy

- **Comparison pages we will write:** <which "X alternative" pages are allowed, or none>
- **Decision-support comparisons:** <comparisons between options in the world rather than between products, such as one procedure against another>
- **Competitors we will not name in copy:** <legal or partnership reasons>

## 8. Site structure

- **Pillar pages:** <URL, topic it owns>
- **Solution / product pages:** <URL list or pattern>
- **Blog or resources path:** <example.com/blog/>
- **Pages that must never be indexed:** <thank-you, gated confirmations, internal tools>
- **Privacy-sensitive surfaces:** <anything holding user content: profiles, journals, saved items, community posts, uploads. Name the paths>

  **Privacy outranks any indexation opportunity, without exception.** A route
  that generates thousands of crawlable pages from user content is not a
  programmatic SEO find, it is an incident waiting to be written up. Any skill
  that meets one reports it as a risk and never as an opportunity, whatever the
  traffic maths says.
- **Known redirect chains or legacy paths:** <if any>

## 9. This quarter

- **Primary SEO outcome:** <what should be true that is not true now, in plain words>
- **Success metric:** <the number that would show it, or `<unknown>` if there is not one yet>
- **Target market and language for new work:** <UK English first, DE second>
- **Content capacity:** <pages per month the team can actually publish and review>
- **No-go areas:** <topics, claims, or pages that are off limits>

## 10. AI visibility

- **Engines that matter to this buyer:** <ChatGPT, Google AI Overviews, Perplexity, Copilot, Gemini>
- **Tracked prompt set lives in:** <Peec project, Ahrefs Brand Radar report, spreadsheet, nowhere yet>
- **Aided prompts** (name the brand) and **unaided prompts** (do not) are counted separately. Never merged.
- **Sources this buyer trusts:** <analyst firms, trade press, associations, review sites, communities>

## 11. Data providers

You cannot do this work without data. Which tool supplies it is your choice; that
it is supplied is not. Fill this in and every skill uses what you name here
instead of assuming a vendor.

| Need | Provider | How to reach it |
|------|----------|-----------------|
| crawl | <Screaming Frog> | <weekly export at ~/crawls/latest.csv, read with `seo_tools crawl`> |
| traffic | <Google Search Console> | <manual CSV export, read with `seo_tools gsc`> |
| keywords | <Ahrefs MCP, or Semrush export, or none> | <connector, or where the export lives> |
| serp | <Ahrefs MCP, or manual> | <if manual: paste the top 10 with date and country> |
| backlinks | <Ahrefs MCP, or none> | <> |
| ai-visibility | <Peec AI MCP, or none> | <if none: run the prompts by hand and record engine, locale, date> |
| ai-citations | <Peec AI MCP, or Ahrefs Brand Radar, or none> | <> |
| ai-crawler-hits | <Peec AI, or server logs, or none> | <> |
| vitals | <PageSpeed Insights, or none> | <needs an API key> |
| analytics | <GA4, or none> | <> |

Write `none` where you have nothing. That is a better answer than naming a tool
you do not really have, because it tells the skill to report a gap rather than
attempt the work and quietly degrade.

## 12. Editorial policy

Skip this if the site sells software and the worst outcome of a wrong page is an
unqualified lead. **Fill it in if a page could affect someone's health, money,
legal position or safety**, because on that kind of site "what may we claim" is not
the whole question. How a conclusion is reached is the other half, and it is the
half that decides what a brief may ask for.

The case that makes this concrete: a reader searches for the best hospital to give
birth in. Targeting that intent is right. Answering it with "St Anselm's is the
best" is not, and no list of banned claims catches the difference. What catches it
is a rule saying conclusions are reached by giving the reader transparent criteria
and letting her decide.

- **Evidence standard:** <what counts as support for a factual claim here: an official source, a named professional, a published study, a measured number>
- **Opinion policy:** <may this site rank, rate or recommend one option over another, or does it lay out criteria and let the reader choose>
- **Commercial neutrality:** <may copy endorse a named commercial provider, and what happens where there is an affiliate or partnership>
- **Professional review policy:** <which content requires review, by whom, and whether it is systematic yet. Never describe content as reviewed unless that specific piece was>
- **User experience policy:** <may lived experience appear, and how it is marked so it is never read as a factual or professional claim>
- **Safety boundaries:** <what this site never advises on, and where the reader is sent instead>

**Keep this section short and public.** `Proof we can cite` and this section are
about what the writing may rest on, not a biography. A founder's authority belongs
here as one line and a link, not as a medical history: an agent handed detail will
use it, and a personal ordeal has no business appearing in an article about what to
pack for hospital.

## 13. Local terminology

For a site serving people inside a system whose language they do not fully speak.
Delete it if that is not the case.

These terms are four things at once and each is a different downstream job: the
reader must learn them, they are the words on the forms, they are what she types
into a search box, and they are entities in the content. A pipeline that normalises
them into their English translations is the single most damaging thing it can do to
this kind of site, because the reader needs the word she will actually meet.

| Term | English explanation | Preserve in copy | Search relevance |
|------|--------------------|------------------|------------------|
| <local term> | <plain English gloss> | <yes, and gloss on first use> | <yes, people search this> |

- **Preserve or translate:** <the default, and when to break it>
- **Terms the audience searches in their own language instead:** <where the English word is genuinely the query>

`page` and `robots-sitemap` are always available: the tools in this repo serve
them with no account. Full provider list, per-need alternatives and the unit traps
when switching vendor: `docs/data-sources.md`.
