#!/usr/bin/env python3
"""Check every SKILL.md against the repo contract. Run before opening a PR."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
DASHES = re.compile("[‐-―−]")
REQUIRED_SECTIONS = ["## Data", "## Output", "## Guardrails"]

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

    for field in ("name", "description", "when_to_use"):
        if not re.search(rf"^{field}:\s*\S", fm, re.M):
            errors.append(f"{d.name}: frontmatter missing {field}")

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

    for ref in set(re.findall(r"(?<![\w/])/([a-z][a-z0-9-]{3,})(?![\w/.])", text)):
        if ref not in names and ref not in {"seo", "skills"}:
            warnings.append(f"{d.name}: references /{ref}, which is not a skill in this repo")

for doc in ("README.md", "PRINCIPLES.md", "CONTRIBUTING.md", "AGENTS.md"):
    p = ROOT / doc
    if p.exists() and DASHES.search(p.read_text(encoding="utf-8")):
        errors.append(f"{doc}: dash characters found")

print(f"{len(names)} skills checked")
for w in warnings:
    print(f"  warn  {w}")
for e in errors:
    print(f"  ERROR {e}")
print("FAIL" if errors else "PASS")
sys.exit(1 if errors else 0)
