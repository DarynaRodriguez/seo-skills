"""A robots.txt parser that answers the question the AI visibility lane needs.

Python ships urllib.robotparser, and it is not usable here: it does not
implement wildcard or end-anchor matching the way Google does, it has no notion
of longest-match precedence, and it cannot tell you which group matched. Since
"is GPTBot allowed to read this page" is the whole question for
/ai-crawler-access, the matching has to be right and it has to be auditable.

Implements the rules in RFC 9309: group selection by the most specific
user-agent match, then longest-match wins between allow and disallow, with a
tie going to allow. Supports `*` and `$`.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlsplit, unquote

# The crawlers worth naming, grouped by who operates them and what blocking one
# actually costs. Blocking a training crawler and blocking the crawler that
# fetches a page to answer a live question are completely different decisions,
# and conflating them is the most common mistake in this area.
AI_AGENTS: Dict[str, Dict[str, str]] = {
    "GPTBot": {
        "operator": "OpenAI",
        "purpose": "training",
        "cost_of_blocking": "Excluded from future model training data. No effect on ChatGPT answering about you today.",
    },
    "OAI-SearchBot": {
        "operator": "OpenAI",
        "purpose": "search index",
        "cost_of_blocking": "Removed from the ChatGPT search index. This is the one that costs you citations.",
    },
    "ChatGPT-User": {
        "operator": "OpenAI",
        "purpose": "live fetch",
        "cost_of_blocking": "ChatGPT cannot open your page when a user asks it to. Costs citations in-session.",
    },
    "ClaudeBot": {
        "operator": "Anthropic",
        "purpose": "training",
        "cost_of_blocking": "Excluded from future model training data.",
    },
    "Claude-User": {
        "operator": "Anthropic",
        "purpose": "live fetch",
        "cost_of_blocking": "Claude cannot open your page on a user's behalf.",
    },
    "Claude-SearchBot": {
        "operator": "Anthropic",
        "purpose": "search index",
        "cost_of_blocking": "Removed from the index Claude search draws on.",
    },
    "PerplexityBot": {
        "operator": "Perplexity",
        "purpose": "search index",
        "cost_of_blocking": "Removed from the Perplexity index. Direct citation loss.",
    },
    "Perplexity-User": {
        "operator": "Perplexity",
        "purpose": "live fetch",
        "cost_of_blocking": "Perplexity cannot open your page for a user request.",
    },
    "Google-Extended": {
        "operator": "Google",
        "purpose": "training and grounding",
        "cost_of_blocking": "Excluded from Gemini training and grounding. Does NOT affect Google Search "
        "ranking or AI Overviews, which use Googlebot.",
    },
    "Googlebot": {
        "operator": "Google",
        "purpose": "search index",
        "cost_of_blocking": "Removed from Google Search, and from AI Overviews with it. Almost never intended.",
    },
    "Bingbot": {
        "operator": "Microsoft",
        "purpose": "search index",
        "cost_of_blocking": "Removed from Bing, and from Copilot which draws on it.",
    },
    "CCBot": {
        "operator": "Common Crawl",
        "purpose": "open crawl corpus",
        "cost_of_blocking": "Excluded from the corpus many models and tools train on downstream.",
    },
    "Applebot-Extended": {
        "operator": "Apple",
        "purpose": "training",
        "cost_of_blocking": "Excluded from Apple Intelligence training. Applebot itself still indexes for Siri and Spotlight.",
    },
    "meta-externalagent": {
        "operator": "Meta",
        "purpose": "training",
        "cost_of_blocking": "Excluded from Meta AI training data.",
    },
    "Amazonbot": {
        "operator": "Amazon",
        "purpose": "search index and training",
        "cost_of_blocking": "Excluded from Alexa answers and Amazon training data.",
    },
    "Bytespider": {
        "operator": "ByteDance",
        "purpose": "training",
        "cost_of_blocking": "Excluded from ByteDance training data. Widely blocked for ignoring crawl-delay.",
    },
    "MistralAI-User": {
        "operator": "Mistral",
        "purpose": "live fetch",
        "cost_of_blocking": "Le Chat cannot open your page for a user request.",
    },
    "cohere-ai": {
        "operator": "Cohere",
        "purpose": "training",
        "cost_of_blocking": "Excluded from Cohere training data.",
    },
    # Engines that dominate a specific market. Absent from most AI-crawler lists,
    # which are written from a US or Western European point of view, and decisive
    # in the markets they serve. A profile that names one of these markets should
    # be reading these rows first.
    "YandexBot": {
        "operator": "Yandex",
        "purpose": "search index",
        "cost_of_blocking": "Removed from Yandex, the leading engine in Russia and much of the CIS.",
    },
    "Baiduspider": {
        "operator": "Baidu",
        "purpose": "search index",
        "cost_of_blocking": "Removed from Baidu, the leading engine in mainland China.",
    },
    "Yeti": {
        "operator": "Naver",
        "purpose": "search index",
        "cost_of_blocking": "Removed from Naver, which leads search in South Korea.",
    },
    "SeznamBot": {
        "operator": "Seznam",
        "purpose": "search index",
        "cost_of_blocking": "Removed from Seznam, a significant engine in the Czech Republic.",
    },
    "Applebot": {
        "operator": "Apple",
        "purpose": "search index",
        "cost_of_blocking": "Removed from Siri and Spotlight suggestions. Distinct from "
        "Applebot-Extended, which governs Apple Intelligence training only.",
    },
    "PetalBot": {
        "operator": "Huawei",
        "purpose": "search index",
        "cost_of_blocking": "Removed from Petal Search on Huawei devices.",
    },
}

LIVE_FETCH_AGENTS = tuple(k for k, v in AI_AGENTS.items() if v["purpose"] == "live fetch")
SEARCH_INDEX_AGENTS = tuple(k for k, v in AI_AGENTS.items() if "search index" in v["purpose"])


class Rule:
    __slots__ = ("allow", "pattern", "raw")

    def __init__(self, allow: bool, raw: str) -> None:
        self.allow = allow
        self.raw = raw
        self.pattern = _compile(raw)

    @property
    def length(self) -> int:
        """Match specificity, per RFC 9309: the length of the path pattern."""
        return len(self.raw)

    def matches(self, path: str) -> bool:
        return bool(self.pattern.match(path))


def _compile(pattern: str) -> "re.Pattern":
    """Translate a robots.txt path pattern into a regex.

    `*` is any run of characters, `$` at the end anchors, everything else is
    literal. Matching is a prefix match unless anchored.
    """
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    out = []
    for char in body:
        if char == "*":
            out.append(".*")
        else:
            out.append(re.escape(char))
    return re.compile("^" + "".join(out) + ("$" if anchored else ""))


class RobotsTxt:
    """Parsed robots.txt, with group selection and longest-match evaluation."""

    def __init__(self, text: str, status: int = 200, url: str = "") -> None:
        self.text = text or ""
        self.status = status
        self.url = url
        self.groups: Dict[str, List[Rule]] = {}
        self.sitemaps: List[str] = []
        self.crawl_delay: Dict[str, str] = {}
        self.unknown_directives: List[str] = []
        self._parse()

    def _parse(self) -> None:
        current: List[str] = []
        # A blank line ends a group only after rules have been seen, so
        # consecutive user-agent lines stack into one group.
        seen_rule = False
        for raw_line in self.text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            if ":" not in line:
                self.unknown_directives.append(raw_line.strip())
                continue
            field, _, value = line.partition(":")
            field = field.strip().lower()
            value = value.strip()

            if field == "user-agent":
                if seen_rule:
                    current = []
                    seen_rule = False
                agent = value.lower()
                current.append(agent)
                self.groups.setdefault(agent, [])
            elif field in ("allow", "disallow"):
                seen_rule = True
                if not current:
                    # Rules before any user-agent line apply to nobody. Record
                    # it, because it is a common and silent authoring mistake.
                    self.unknown_directives.append(raw_line.strip())
                    continue
                if field == "disallow" and value == "":
                    # "Disallow:" with no path means allow everything.
                    continue
                for agent in current:
                    self.groups[agent].append(Rule(field == "allow", value))
            elif field == "sitemap":
                self.sitemaps.append(urljoin(self.url or "", value))
            elif field == "crawl-delay":
                for agent in current or ["*"]:
                    self.crawl_delay[agent] = value
            else:
                self.unknown_directives.append(raw_line.strip())

    def group_for(self, user_agent: str) -> Tuple[Optional[str], List[Rule]]:
        """The group that governs `user_agent`, by most specific name match.

        Returns the matched group name and its rules. A missing agent falls back
        to `*`, and if there is no `*` group either the agent is unrestricted.
        """
        target = user_agent.lower()
        best: Optional[str] = None
        for name in self.groups:
            if name == "*":
                continue
            if name == target or (target.startswith(name) and len(name) > 1):
                if best is None or len(name) > len(best):
                    best = name
        if best is not None:
            return best, self.groups[best]
        if "*" in self.groups:
            return "*", self.groups["*"]
        return None, []

    def can_fetch(self, user_agent: str, url: str) -> Dict[str, object]:
        """Whether `user_agent` may fetch `url`, and which rule decided it."""
        if self.status in (401, 403):
            return {
                "allowed": False,
                "reason": "robots.txt returned {}, which RFC 9309 treats as disallow all.".format(self.status),
                "matched_group": None,
                "matched_rule": None,
            }
        if self.status >= 400:
            return {
                "allowed": True,
                "reason": "robots.txt returned {}, treated as no restrictions.".format(self.status),
                "matched_group": None,
                "matched_rule": None,
            }

        split = urlsplit(url)
        path = unquote(split.path or "/")
        if split.query:
            path = "{}?{}".format(path, split.query)

        group_name, rules = self.group_for(user_agent)
        if not rules:
            return {
                "allowed": True,
                "reason": "No group applies to {}.".format(user_agent),
                "matched_group": group_name,
                "matched_rule": None,
            }

        winner: Optional[Rule] = None
        for rule in rules:
            if not rule.matches(path):
                continue
            if winner is None:
                winner = rule
                continue
            if rule.length > winner.length:
                winner = rule
            elif rule.length == winner.length and rule.allow:
                # Equal specificity goes to allow.
                winner = rule

        if winner is None:
            return {
                "allowed": True,
                "reason": "No rule in group {!r} matches {}.".format(group_name, path),
                "matched_group": group_name,
                "matched_rule": None,
            }
        return {
            "allowed": winner.allow,
            "reason": "{}: {} in group {!r} is the longest match for {}.".format(
                "Allow" if winner.allow else "Disallow",
                winner.raw or "(empty)",
                group_name,
                path,
            ),
            "matched_group": group_name,
            "matched_rule": ("Allow" if winner.allow else "Disallow") + ": " + winner.raw,
        }

    def audit_ai_agents(self, url: str) -> Dict[str, object]:
        """Every agent in AI_AGENTS evaluated against one URL.

        Separates blocked live-fetch and search-index crawlers from blocked
        training crawlers, because only the first group costs citations, and a
        report that blends them tells the reader nothing actionable.
        """
        rows = []
        for name, meta in AI_AGENTS.items():
            verdict = self.can_fetch(name, url)
            rows.append(
                {
                    "agent": name,
                    "operator": meta["operator"],
                    "purpose": meta["purpose"],
                    "allowed": verdict["allowed"],
                    "reason": verdict["reason"],
                    "matched_group": verdict["matched_group"],
                    "matched_rule": verdict["matched_rule"],
                    "cost_of_blocking": meta["cost_of_blocking"] if not verdict["allowed"] else None,
                }
            )
        blocked = [r for r in rows if not r["allowed"]]
        return {
            "url": url,
            "robots_status": self.status,
            "agents": rows,
            "blocked_count": len(blocked),
            "blocked_live_fetch": [r["agent"] for r in blocked if r["purpose"] == "live fetch"],
            "blocked_search_index": [r["agent"] for r in blocked if "search index" in str(r["purpose"])],
            "blocked_training": [r["agent"] for r in blocked if r["purpose"] == "training"],
            "sitemaps": self.sitemaps,
            "rules_before_any_user_agent": self.unknown_directives,
        }


def robots_url_for(url: str) -> str:
    """The robots.txt that governs a URL. Per host and scheme, not per path."""
    split = urlsplit(url)
    port = ":{}".format(split.port) if split.port and split.port not in (80, 443) else ""
    return "{}://{}{}/robots.txt".format(split.scheme, split.hostname, port)
