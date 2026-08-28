# Schema recipes

Copy-paste JSON-LD for `/schema-builder`. Every value in angle brackets is a
placeholder. Replace it with something that is true and visible on the page, or
delete the property. Deleting is always allowed. Inventing never is.

Conventions used here:

- One `<script type="application/ld+json">` per page, containing an `@graph`.
- Stable `@id` values built from the URL plus a fragment, so nodes can reference each
  other instead of repeating themselves.
- ISO 8601 dates with an offset: `2026-08-26T09:00:00+02:00`.
- Absolute URLs everywhere, including images.
- `inLanguage` set from the market's language variant in the profile.

---

## Homepage: Organization and WebSite

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://<domain>/#organization",
      "name": "<Legal or trading brand name, exact capitalisation>",
      "url": "https://<domain>/",
      "logo": {
        "@type": "ImageObject",
        "url": "https://<domain>/<path-to-logo>.png",
        "width": 600,
        "height": 60
      },
      "description": "<One sentence on what the company does. No adjectives.>",
      "foundingDate": "<YYYY>",
      "sameAs": [
        "https://www.linkedin.com/company/<handle>",
        "https://github.com/<handle>"
      ],
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "<street>",
        "addressLocality": "<city>",
        "postalCode": "<code>",
        "addressCountry": "<ISO country code>"
      },
      "contactPoint": {
        "@type": "ContactPoint",
        "contactType": "sales",
        "email": "<address published on the site>",
        "availableLanguage": ["<language>", "<language>"]
      }
    },
    {
      "@type": "WebSite",
      "@id": "https://<domain>/#website",
      "url": "https://<domain>/",
      "name": "<Brand name>",
      "publisher": { "@id": "https://<domain>/#organization" },
      "inLanguage": "<en-GB>"
    }
  ]
}
</script>
```

Add `potentialAction` with a `SearchAction` only if the site has a working internal
search results URL. If it does not, leave it out.

---

## Blog post or article, with breadcrumbs

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Article",
      "@id": "https://<domain>/<path>/#article",
      "headline": "<The visible H1 or article title, under 110 characters>",
      "description": "<One or two sentences summarising the article>",
      "image": ["https://<domain>/<path-to-featured-image>.jpg"],
      "datePublished": "<2026-08-26T09:00:00+02:00>",
      "dateModified": "<2026-08-26T09:00:00+02:00>",
      "inLanguage": "<en-GB>",
      "author": {
        "@type": "Person",
        "name": "<Real name of the person who wrote it>",
        "jobTitle": "<their job title>",
        "url": "https://<domain>/authors/<slug>"
      },
      "publisher": { "@id": "https://<domain>/#organization" },
      "mainEntityOfPage": { "@id": "https://<domain>/<path>/#webpage" }
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://<domain>/<path>/#breadcrumbs",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://<domain>/" },
        { "@type": "ListItem", "position": 2, "name": "<Blog>", "item": "https://<domain>/<blog-path>/" },
        { "@type": "ListItem", "position": 3, "name": "<Article title>" }
      ]
    }
  ]
}
</script>
```

The last breadcrumb item carries no `item`, because it is the current page. If the
byline is not visible on the page, add the byline, then add the markup.

---

## FAQPage

**No rich result.** FAQPage is not in Google's structured data gallery as of
2026-08-28 ([search-gallery](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)). The markup remains valid and correctly
describes a page with a real FAQ, so it is not wrong to publish, but it will not
produce a rich result and should never be sold as doing so.

Only for questions and answers a visitor can read on the page. Answer text should
match the visible answer.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "@id": "https://<domain>/<path>/#faq",
  "inLanguage": "<en-GB>",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "<A question people actually search, exactly as shown on the page>",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "<The visible answer. Plain text or simple HTML. 40 to 100 words.>"
      }
    },
    {
      "@type": "Question",
      "name": "<Second real question>",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "<Second visible answer>"
      }
    }
  ]
}
</script>
```

If the answers live inside an accordion, they still count as visible provided the
text is in the HTML and expandable without navigation. If they are loaded on click
from elsewhere, they do not.

---

## SoftwareApplication, for a product or solution page

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "@id": "https://<domain>/<path>/#software",
  "name": "<Product name, exact capitalisation from the profile>",
  "applicationCategory": "BusinessApplication",
  "applicationSubCategory": "<e.g. Supplier Management>",
  "operatingSystem": "Web browser",
  "description": "<Two sentences on what it does. No adjectives.>",
  "url": "https://<domain>/<path>/",
  "publisher": { "@id": "https://<domain>/#organization" },
  "screenshot": "https://<domain>/<path-to-real-screenshot>.png",
  "featureList": [
    "<A capability the page describes>",
    "<Another capability the page describes>"
  ],
  "offers": {
    "@type": "Offer",
    "price": "<only if a price is shown on the page>",
    "priceCurrency": "<EUR>",
    "url": "https://<domain>/pricing/"
  }
}
</script>
```

No public price means delete the whole `offers` object. Do not substitute
`"price": "0"`, and do not add `aggregateRating` to make the block eligible.

---

## Product, for something that is not software

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "@id": "https://<domain>/<path>/#product",
  "name": "<Product name>",
  "image": ["https://<domain>/<path-to-product-image>.jpg"],
  "description": "<What it is>",
  "sku": "<SKU shown on the page>",
  "brand": { "@id": "https://<domain>/#organization" },
  "offers": {
    "@type": "Offer",
    "price": "<price shown on the page>",
    "priceCurrency": "<EUR>",
    "availability": "https://schema.org/InStock",
    "url": "https://<domain>/<path>/"
  }
}
</script>
```

`review` and `aggregateRating` go in only when real, collected customer reviews are
displayed on this page. First-party ratings on your own marketing page are not
eligible for review rich results, whatever their provenance.

---

## HowTo, for genuinely procedural content

**No rich result.** HowTo is not in Google's structured data gallery as of
2026-08-28 ([search-gallery](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)). Rich results were dropped in 2023 and have not
returned. Valid markup, honest description, no rich result.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "@id": "https://<domain>/<path>/#howto",
  "name": "<How to do the thing, matching the visible H1>",
  "description": "<What the reader will have done by the end>",
  "totalTime": "PT45M",
  "tool": [{ "@type": "HowToTool", "name": "<something the reader needs>" }],
  "step": [
    {
      "@type": "HowToStep",
      "position": 1,
      "name": "<Step heading as it appears on the page>",
      "text": "<What to do, in the words on the page>",
      "url": "https://<domain>/<path>/#step-1",
      "image": "https://<domain>/<path-to-step-image>.png"
    },
    {
      "@type": "HowToStep",
      "position": 2,
      "name": "<Second step heading>",
      "text": "<What to do>",
      "url": "https://<domain>/<path>/#step-2"
    }
  ]
}
</script>
```

A list of benefits is not a `HowTo`. If the page does not contain ordered steps a
reader could follow, use `Article`.

---

## Event, for a webinar or conference

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Event",
  "@id": "https://<domain>/<path>/#event",
  "name": "<Event title>",
  "description": "<What it covers>",
  "startDate": "<2026-09-15T15:00:00+02:00>",
  "endDate": "<2026-09-15T16:00:00+02:00>",
  "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
  "eventStatus": "https://schema.org/EventScheduled",
  "location": {
    "@type": "VirtualLocation",
    "url": "https://<domain>/<path>/"
  },
  "organizer": { "@id": "https://<domain>/#organization" },
  "performer": { "@type": "Person", "name": "<Real speaker name>" },
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "<EUR>",
    "availability": "https://schema.org/InStock",
    "url": "https://<domain>/<path>/",
    "validFrom": "<2026-08-01T09:00:00+02:00>"
  }
}
</script>
```

For a physical event, replace `VirtualLocation` with `Place` and a `PostalAddress`.
After the event, either remove the markup or update `eventStatus`. A past event left
marked as scheduled is stale data.

---

## VideoObject

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "@id": "https://<domain>/<path>/#video",
  "name": "<Video title>",
  "description": "<What the video shows>",
  "thumbnailUrl": ["https://<domain>/<path-to-thumbnail>.jpg"],
  "uploadDate": "<2026-08-26T09:00:00+02:00>",
  "duration": "PT3M20S",
  "embedUrl": "https://<video-host>/embed/<id>",
  "publisher": { "@id": "https://<domain>/#organization" },
  "transcript": "<The transcript text, if it is on the page>"
}
</script>
```

Only mark up a video that is embedded on this page. One `VideoObject` per video, not
one per page with several videos, and never a `VideoObject` for a video linked
elsewhere.

---

## Person, for an author or team page

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "@id": "https://<domain>/authors/<slug>#person",
  "name": "<Real name>",
  "jobTitle": "<Job title>",
  "image": "https://<domain>/<path-to-photo>.jpg",
  "worksFor": { "@id": "https://<domain>/#organization" },
  "sameAs": [
    "https://www.linkedin.com/in/<handle>"
  ],
  "knowsAbout": ["<topic they genuinely write about>"]
}
</script>
```

A `Person` node needs a real person. A brand name, a team alias or a pen name in this
slot is a fabricated author.

---

## Validation checklist

- [ ] Rich Results Test on the live or staged URL: eligibility and errors recorded with the date
- [ ] Schema Markup Validator: no syntax or vocabulary errors
- [ ] Every `@id` resolves to a node that exists in the graph
- [ ] Every URL is absolute and returns 200
- [ ] Every date is ISO 8601 with an offset, and true
- [ ] Every property value appears somewhere on the rendered page
- [ ] No duplicate node of the same type on the page
- [ ] `inLanguage` matches the page's actual language
- [ ] Search Console enhancement report checked after deployment, with the date
