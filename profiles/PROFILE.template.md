# Site profile

Written by `/seo-profile-setup`. Every skill in the pack reads this first.
Save to `.seo/profile.md` in the project you work in, or `~/.seo-skills/profile.md`
to use it everywhere. Delete any line you cannot answer honestly, and leave the
gap visible: a blank is information, a guess is not.

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

## 3. Who we sell to

- **Primary buyer:** <role, seniority, company size, industry>
- **Secondary buyer or influencer:** <role>
- **The job they are trying to get done:** <in their words, not yours>
- **What disqualifies a visitor:** <who this product is not for>
- **How they search:** <do they search the category, the problem, a competitor, or a compliance term>

## 4. What we sell

- **Category we compete in:** <the words buyers use, not internal branding>
- **What the product actually does:** <two sentences, no adjectives>
- **Proof we can cite:** <named customers, verified numbers, certifications, analyst mentions>
- **Claims we may not make:** <anything legal, security or product has not signed off>

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

## 7. Competitors

| Competitor | Why they show up | Where they beat us |
|-----------|-----------------|-------------------|
| <Name> | <ranks for our category terms> | <domain authority, content depth, brand> |

- **Comparison pages we will write:** <which "X alternative" pages are allowed>
- **Competitors we will not name in copy:** <legal or partnership reasons>

## 8. Site structure

- **Pillar pages:** <URL, topic it owns>
- **Solution / product pages:** <URL list or pattern>
- **Blog or resources path:** <example.com/blog/>
- **Pages that must never be indexed:** <thank-you, gated confirmations, internal tools>
- **Known redirect chains or legacy paths:** <if any>

## 9. This quarter

- **The one metric that matters:** <qualified demo requests from organic, not sessions>
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

`page` and `robots-sitemap` are always available: the tools in this repo serve
them with no account. Full provider list, per-need alternatives and the unit traps
when switching vendor: `docs/data-sources.md`.
