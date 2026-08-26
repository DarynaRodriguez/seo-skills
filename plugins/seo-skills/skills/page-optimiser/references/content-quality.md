# Content quality: text, image and video

Reference for `/page-optimiser`. Also usable directly by `/content-brief` when a
brief needs to name a quality bar, and by `/geo-rewrite` when extraction quality is
the question.

Metadata being technically correct is not quality. A senior buyer leaves a page
that is generic, unsupported or visually cheap, and no title rewrite recovers that
visit. Every standard below is checkable by looking at the page.

---

## The core test

Would the buyer named in the profile, who arrived from the target query, find this
page specific, useful and worth two minutes of their working day? If the answer is
no, quality work comes before optimisation work. Optimising a page nobody wants to
read moves nothing.

Apply the test per section, not per page. Most weak pages are two strong sections
and four filler ones.

---

## Text quality

### Failure patterns to flag and fix

**Filler openings.** "In today's fast-changing market" and "X has evolved
significantly over the past decade" spend the reader's first impression on nothing.
Cut them entirely. Lead with the answer to the query or the value of the page.

**Definition-dodging.** A page that introduces a concept and explains it three
paragraphs later loses both readers and answer engines. Define first, in a sentence
that stands alone without the paragraph around it.

**Passive constructions where active exists.** "Invoices can be reconciled by the
platform" against "the platform reconciles invoices". The active version is shorter,
clearer, and names the actor, which matters for extraction as well as reading.

**Unsupported claims.** "Dramatically reduces cost" with no number. Three options in
order of preference: attach a real number with its source and date, replace with a
specific capability that is verifiably true, or cut the claim. Softening it into a
vaguer claim is not one of the options.

**Feature lists with no outcome.** "Supplier records, compliance workflows, contract
storage" tells a buyer nothing. Pair each feature with the change it makes: what
someone stops doing, or finds out earlier, or stops paying for.

**Recycled phrasing across pages.** If the homepage, the solution page and a blog
post describe the product in the same three sentences, each page is weaker and the
set looks thin. Every page needs its own narrative built for its own query.

**Unnamed subjects.** "Our platform", "the solution", "we" repeated where the brand
or product name would work. Named entities adjacent to their capabilities are what
answer engines can attribute. See `/geo-rewrite`.

**Length mismatched to intent.** A solution page at 150 words is thin. A guide at
600 words is a stub. Neither is fixed by a word count target: fix it by answering
the questions the intent implies, then stopping.

**AI writing tells.** Tricolon everywhere, sentences that begin by restating the
heading, paragraphs that end by summarising themselves, hedged non-claims, and the
profile's banned word list. Also the profile's banned characters, which for many
brands includes the em dash and en dash in body copy.

### Text quality checklist

- [ ] Opening does not set a scene, state the obvious or define the industry
- [ ] The target query is answered above the fold, in text, not implied
- [ ] Every claim carries a number, a named customer, a named capability, or a citation with a date
- [ ] Nothing on the page is a claim the profile lists as not signed off
- [ ] Active voice wherever it is available
- [ ] No banned words, no banned characters, correct language variant throughout
- [ ] Every feature mentioned is paired with the outcome it produces
- [ ] Copy is unique to this page, with no blocks recycled from other pages
- [ ] Key sentences are self-contained and make sense lifted out of context
- [ ] Concepts are defined at first use, in one sentence
- [ ] Product and brand names appear next to the capabilities they own
- [ ] Length matches intent, and no section exists to add length
- [ ] Reading level suits the profile's buyer: precise, not padded, not jargon soup
- [ ] External citations point to sources that buyer already trusts, per the profile

---

## Image quality

Every image is either earning its place by building trust, explaining a concept or
showing the product, or it is page weight that dilutes the message.

### Product screenshots and interface images

- Show the current version of the product. An outdated interface reads as an
  abandoned product, and a wireframe reads as a product that does not exist.
- Show a realistic scenario with plausible data, not an empty demo tenant. An
  interface with three rows of placeholder text convinces nobody.
- Annotate or caption when the point of the screenshot is not obvious in two
  seconds. Captions are read by people and indexed as page text.
- Alt text describes the specific thing visible: "supplier onboarding queue showing
  eight vendors and their certificate status" rather than "dashboard".

### Data visualisations and diagrams

- Vector or high resolution. A blurry chart signals a low production bar for
  everything else on the page.
- Every chart carries a title, labelled axes or segments, an n where relevant, and a
  source with a date if the data is not the brand's own.
- Alt text describes the insight, not the chart type: "bar chart showing cycle time
  falling from 21 days to 9 days across 30 customers, 2026" rather than "bar chart".
- A diagram that only restates a list in boxes should be a list.

### Photography

- Avoid generic stock: handshakes, laptops on white desks, teams laughing in glass
  meeting rooms. It adds no information and lowers perceived quality.
- Prefer real assets: customer sites, the team, the product in use, events.
- If stock is unavoidable, choose abstract or subject-relevant imagery over staged
  business scenes.

### File quality and delivery

- Upload at display size. A 3000px hero in a 600px slot wastes bandwidth and delays
  the largest contentful paint.
- Modern formats (WebP or AVIF) where the platform supports them.
- Explicit width and height, so the layout does not shift while images load.
- Lazy-load everything below the fold, and never lazy-load the hero image.
- Never carry meaningful text only inside an image. Search engines and answer
  engines cannot rely on reading it, and neither can screen readers.
- Decorative images take `alt=""`. Meaningful images never do.

### Image quality checklist

- [ ] Product images show the current interface in a realistic, labelled context
- [ ] No generic stock photography on money pages or posts
- [ ] Every data visualisation has a title, labels and a dated source
- [ ] Alt text is specific and describes content or insight, not subject category
- [ ] Images are sized for display, in a modern format, with explicit dimensions
- [ ] Below-fold images lazy-loaded, hero image not
- [ ] No meaningful text delivered only as an image
- [ ] Decorative images carry empty alt, meaningful images carry real alt

---

## Video quality

Video raises time on page and trust, and can earn rich results when marked up
correctly. A broken or dated video costs more than no video.

### When video earns its place

| Video type | Where it belongs | Length |
|-----------|------------------|--------|
| Product walkthrough | Solution and use case pages | 2 to 5 minutes |
| Customer testimonial | Case studies, solution pages | 60 to 120 seconds |
| Concept explainer | Guides, pillar pages | 60 to 90 seconds |
| Webinar or talk recording | Resource hub, with a transcript | As recorded, with chapters |

### Technical requirements

- Accurate captions on every video. Accessibility requirement first, indexable text
  second.
- `VideoObject` markup with `name`, `description`, `thumbnailUrl`, `uploadDate`, and
  `contentUrl` or `embedUrl`. Only for videos that are actually on the page. See
  `/schema-builder`.
- Never autoplay with sound. If a video sits in the hero, use a poster image with a
  play control so it does not delay the largest contentful paint or shift layout.
- Host on a video platform rather than serving large files from the CMS asset store,
  and lazy-load the embed so it does not load for readers who never press play.
- A transcript on the page for anything over 60 seconds. It is the only version of
  the content that text-based retrieval can use.

### Quality signals to assess

- Production: audio clarity first, lighting second. Bad audio ends the view.
- Currency: an old interface in a demo is worse than no demo.
- Structure: the video answers the page's question in the first 20 seconds.
- Next step: the video ends with one specific action, not a logo card.

### Video quality checklist

- [ ] Accurate captions present
- [ ] `VideoObject` markup present and truthful
- [ ] No autoplay with sound, no layout shift, hero video behind a poster image
- [ ] Embed lazy-loaded, video not served from the CMS asset store
- [ ] Transcript on the page for anything over 60 seconds
- [ ] Interface shown is the current one
- [ ] Video answers the page's question early, and ends with one clear next step

---

## Rating scale

Rate each pass and say what makes it that rating.

| Rating | Meaning |
|--------|---------|
| Strong | Meets the standards. No action needed this cycle. |
| Needs work | Real issues, none of them stopping the page from being useful. Fix in the normal queue. |
| Blocking | The page should not be promoted, linked to or optimised until this is fixed. Unsupported claims, dated product imagery, and copy recycled across pages all land here. |

A blocking rating is a finding, not a formatting problem. Say it plainly, name the
fix, and name who owns it.
