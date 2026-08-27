"""Entry point so `python -m seo_tools` works from a clone with no install."""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
