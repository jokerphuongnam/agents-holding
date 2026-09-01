#!/usr/bin/env python3
"""Sync Grok agent frontmatter from Company OS.

Alias for: export_harness.py --to grok

Keeps the existing habit (`sync_agents.py`) while Company OS SoT lives in
`agents.tsv` + `harness/grok.toml`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    here = Path(__file__).resolve().parent
    script = here / "export_harness.py"
    return subprocess.call([sys.executable, str(script), "--to", "grok"])


if __name__ == "__main__":
    raise SystemExit(main())
