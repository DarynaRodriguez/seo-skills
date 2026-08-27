## What this changes

<!-- One or two sentences. What is different after this merges? -->

## Why

<!-- The problem, not the solution. If it fixes a bug, what did the bug do? -->

## Checks

- [ ] `python3 scripts/validate.py` passes
- [ ] `python -m unittest discover -s tests -t .` passes
- [ ] `./scripts/sync-plugin.sh` run, and `plugins/` committed if it changed
- [ ] No em dashes or en dashes anywhere (`validate.py` enforces this)
- [ ] Any new number carries its source, sample size and date

## If this adds or changes a skill

- [ ] Follows `docs/skill-template.md`, section order included
- [ ] Between 100 and 300 lines
- [ ] Frontmatter has `name`, `description`, `when_to_use`, `argument-hint`
- [ ] README catalogue row, README support matrix row, and a CHANGELOG entry

## If this adds or changes a tool

- [ ] Standard library only, no new dependency file
- [ ] Logic in a module, argument parsing in `cli.py`
- [ ] Every URL goes through `safety.validate_url`
- [ ] A test per behaviour, and a test for the failure mode
- [ ] Nothing assumes English or a Latin script (see `tests/test_locales.py`)
