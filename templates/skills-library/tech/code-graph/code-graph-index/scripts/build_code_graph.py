#!/usr/bin/env python3
"""DEPRECATED — forwards to Code Prism pointer sync.

The homemade path/import walker is retired. Company code-graph staff uses
Code Prism (`prism analyze` + `prism-mcp` tools) as SoT.

This shim keeps old `--root` / `--out` call sites working by delegating to
`sync_prism_pointer.py`.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

print(
    "warning: build_code_graph.py is deprecated; using Code Prism via sync_prism_pointer.py",
    file=sys.stderr,
)

target = Path(__file__).with_name("sync_prism_pointer.py")
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name="__main__")
