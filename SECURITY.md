# Security

## Reporting an issue

Open a private security advisory on this repository's Security tab, or open a
normal issue if the problem is not sensitive. Please do not post credentials or
private site data in a public issue.

## What these skills touch

The skills in this repo are markdown instructions. They hold no credentials and
make no network calls of their own. Anything they read or write happens through
your agent's own tools and connectors, under your agent's own permissions.

Two things are worth knowing before you run them on a client site:

**API connectors are yours.** Ahrefs and Peec AI access comes from MCP connectors
you authorise in your own agent. Nothing in this repo stores or transmits a key.
Revoking access in the connector revokes it for the skills.

**Working files are local and unencrypted.** `.seo/profile.md`, `pages.csv` and
the keyword files are plain text in your project directory. A profile can contain
commercially sensitive material: buyer research, competitor assessments, claims
legal has blocked. `.gitignore` excludes `.seo/` by default. Keep it that way on
a public repo, and treat a committed profile as published.

**No skill publishes anything on its own.** Every skill that touches live pages,
redirects, or de-indexing is written to stop at a recommendation and require a
named human. If you wire one into an automated pipeline that publishes without
review, that is your risk, and `PRINCIPLES.md` says why we think it is a bad idea.

## What the tools defend against, and what they do not

`docs/security.md` is the detail: the SSRF guard and every notation it refuses,
the decompression caps, XML handling, why no credential can reach an error
message, the prompt-injection rule for fetched content, and an honest list of what
is out of scope, DNS rebinding included.

Run the security regressions with:

```bash
python -m unittest tests.test_security -v
```
