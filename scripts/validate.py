#!/usr/bin/env python3
"""Check every SKILL.md against the repo contract. Run before opening a PR."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
DASHES = re.compile("[‐-―−]")
REQUIRED_SECTIONS = ["## Data", "## Output", "## Guardrails"]
FENCE = re.compile(r"```.*?```", re.S)

# Frontmatter this repo uses. `name` and `description` are the only two the
# portable Agent Skills spec allows; `when_to_use` and `argument-hint` are read
# by Claude Code and by plugin installs, which is how this pack is distributed.
# See docs/frontmatter.md before adding to this set.
REQUIRED_FRONTMATTER = ("name", "description", "when_to_use", "argument-hint")
ALLOWED_FRONTMATTER = {
    "name",
    "description",
    "when_to_use",
    "argument-hint",
    "license",
    "metadata",
    "compatibility",
    "allowed-tools",
}

errors = []
warnings = []
names = {p.name for p in SKILLS.iterdir() if p.is_dir()}

for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
    f = d / "SKILL.md"
    if not f.exists():
        errors.append(f"{d.name}: no SKILL.md")
        continue
    text = f.read_text(encoding="utf-8")

    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        errors.append(f"{d.name}: missing YAML frontmatter")
        continue
    fm = m.group(1)

    for field in REQUIRED_FRONTMATTER:
        if not re.search(rf"^{field}:\s*\S", fm, re.M):
            errors.append(f"{d.name}: frontmatter missing {field}")

    # Catch a typo in a key before it ships. Claude Code ignores an unknown key
    # silently, so a misspelled `when_to_use` costs the skill its trigger phrases
    # and nothing says so.
    for key in re.findall(r"^([A-Za-z][\w-]*):", fm, re.M):
        if key not in ALLOWED_FRONTMATTER:
            errors.append(
                f"{d.name}: frontmatter key {key!r} is not one this repo uses. "
                f"Allowed: {', '.join(sorted(ALLOWED_FRONTMATTER))}"
            )

    declared = re.search(r"^name:\s*(.+)$", fm, re.M)
    if declared and declared.group(1).strip().strip('"') != d.name:
        errors.append(f"{d.name}: frontmatter name does not match directory")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            warnings.append(f"{d.name}: no '{section}' section")

    if "Step 0" not in text:
        warnings.append(f"{d.name}: no Step 0 profile load")

    lines = text.count("\n") + 1
    if not 100 <= lines <= 300:
        warnings.append(f"{d.name}: {lines} lines, outside the 100 to 300 band")

    for path in [f, *sorted(d.rglob("references/*.md"))]:
        body = path.read_text(encoding="utf-8")
        if DASHES.search(body):
            bad = sorted(set(DASHES.findall(body)))
            errors.append(f"{path.relative_to(ROOT)}: dash characters found {bad}")

    # Sibling references are checked in prose only. Fenced blocks hold example
    # output, which legitimately contains URL paths like /pricing that look
    # exactly like a skill reference and are not one.
    prose = FENCE.sub("", text)
    for ref in set(re.findall(r"(?<![\w/])/([a-z][a-z0-9-]{3,})(?![\w/.])", prose)):
        if ref not in names and ref not in {"seo", "skills"}:
            warnings.append(f"{d.name}: references /{ref}, which is not a skill in this repo")

for doc in ("README.md", "PRINCIPLES.md", "CONTRIBUTING.md", "AGENTS.md"):
    p = ROOT / doc
    if p.exists() and DASHES.search(p.read_text(encoding="utf-8")):
        errors.append(f"{doc}: dash characters found")

# Every `python -m seo_tools <command>` a skill tells the reader to run has to be
# a command the CLI actually has. Without this check a skill can promise a tool
# that does not exist, which is the failure mode the execution layer exists to
# remove in the first place.
TOOL_CALL = re.compile(r"python -m seo_tools\s+([a-z][a-z0-9-]*)")
sys.path.insert(0, str(ROOT))
try:
    from seo_tools.cli import build_parser

    actions = build_parser()._subparsers._group_actions[0]  # noqa: SLF001
    commands = set(actions.choices)
except Exception as exc:  # the CLI failing to import is itself an error
    commands = set()
    errors.append(f"could not import seo_tools.cli to check tool references: {exc}")

if commands:
    referenced = set()
    for path in [*sorted(SKILLS.rglob("SKILL.md")), *sorted((ROOT / "docs").glob("*.md"))]:
        for command in TOOL_CALL.findall(path.read_text(encoding="utf-8")):
            referenced.add(command)
            if command not in commands:
                errors.append(
                    f"{path.relative_to(ROOT)}: refers to `python -m seo_tools {command}`, "
                    f"which is not a command. Known: {', '.join(sorted(commands))}"
                )
    undocumented = commands - referenced - {"doctor"}
    if undocumented:
        warnings.append(
            f"commands no skill or doc mentions: {', '.join(sorted(undocumented))}"
        )


# -- agents ---------------------------------------------------------------
# Agent frontmatter is a different contract from skill frontmatter, and an
# unrecognised key there is ignored just as silently. Fields per the Claude Code
# subagent reference; `name` and `description` are the only required two.
AGENTS = ROOT / "agents"
AGENT_REQUIRED = ("name", "description")
AGENT_ALLOWED = {
    "name", "description", "tools", "disallowedTools", "model", "permissionMode",
    "maxTurns", "skills", "mcpServers", "hooks", "memory", "background", "effort",
    "isolation", "color", "initialPrompt",
}
AGENT_MODELS = {"sonnet", "opus", "haiku", "fable", "inherit"}
KNOWN_TOOLS = {
    "Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebFetch", "WebSearch",
    "Agent", "Task", "TodoWrite", "NotebookEdit", "SendMessage",
}

agent_names = set()
if AGENTS.is_dir():
    for f in sorted(AGENTS.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n", text, re.S)
        if not m:
            errors.append(f"agents/{f.name}: missing YAML frontmatter")
            continue
        fm = m.group(1)

        for field in AGENT_REQUIRED:
            if not re.search(rf"^{field}:\s*\S", fm, re.M):
                errors.append(f"agents/{f.name}: frontmatter missing {field}")

        for key in re.findall(r"^([A-Za-z][\w-]*):", fm, re.M):
            if key not in AGENT_ALLOWED:
                errors.append(
                    f"agents/{f.name}: frontmatter key {key!r} is not a subagent field. "
                    f"Allowed: {', '.join(sorted(AGENT_ALLOWED))}"
                )

        declared = re.search(r"^name:\s*(.+)$", fm, re.M)
        if declared:
            value = declared.group(1).strip().strip('"')
            agent_names.add(value)
            if value != f.stem:
                warnings.append(
                    f"agents/{f.name}: name is {value!r} but the file is {f.stem!r}. "
                    "Allowed, but confusing."
                )
            if ":" in value:
                errors.append(f"agents/{f.name}: name may not contain a colon")

        model = re.search(r"^model:\s*(.+)$", fm, re.M)
        if model:
            value = model.group(1).strip().strip('"')
            if value not in AGENT_MODELS and not value.startswith("claude-"):
                errors.append(
                    f"agents/{f.name}: model {value!r} is not one of "
                    f"{', '.join(sorted(AGENT_MODELS))} or a full model id"
                )

        tools = re.search(r"^tools:\s*(.+)$", fm, re.M)
        if tools:
            for tool in [x.strip() for x in tools.group(1).split(",") if x.strip()]:
                base = tool.split("(")[0].strip()
                if base not in KNOWN_TOOLS:
                    warnings.append(f"agents/{f.name}: tool {base!r} is not one this repo knows about")

        # An agent that promises to write a file has to say where.
        if "Write" in (tools.group(1) if tools else "") and "output_dir" not in text:
            warnings.append(f"agents/{f.name}: can Write but names no output directory")

        for command in TOOL_CALL.findall(text):
            if commands and command not in commands:
                errors.append(
                    f"agents/{f.name}: refers to `python -m seo_tools {command}`, "
                    "which is not a command"
                )

    # Every agent should be reachable from a skill, or nothing will ever run it.
    skill_text = "\n".join(
        p.read_text(encoding="utf-8") for p in SKILLS.rglob("SKILL.md")
    )
    for name in sorted(agent_names):
        if name not in skill_text:
            warnings.append(f"agent {name!r} is not mentioned by any skill, so nothing invokes it")

print(
    f"{len(names)} skills checked, {len(agent_names)} agents, "
    f"{len(commands)} tool commands available"
)
for w in warnings:
    print(f"  warn  {w}")
for e in errors:
    print(f"  ERROR {e}")
print("FAIL" if errors else "PASS")
sys.exit(1 if errors else 0)
