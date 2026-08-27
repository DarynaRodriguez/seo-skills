#!/usr/bin/env python3
"""Path-independent launcher for the execution layer.

`python -m seo_tools ...` needs the pack root to be the working directory. That
is fine in a clone, and wrong everywhere else: installed as a plugin, the agent's
working directory is the user's project, and the module would not be found.

This script puts its own directory on sys.path first, so it works from anywhere:

    python /path/to/seo-skills/seo.py page https://example.com

Same commands, same flags, same exit codes as `python -m seo_tools`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seo_tools.cli import main  # noqa: E402  (import after the path is set)

if __name__ == "__main__":
    sys.exit(main())
