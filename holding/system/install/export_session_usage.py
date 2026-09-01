#!/usr/bin/env python3
"""Export final cumulative usage from a Grok session updates.jsonl → usage.json."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def last_usage(updates: Path) -> dict | None:
    last = None
    with updates.open(encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "costUsdTicks" not in line or "inputTokens" not in line:
                continue
            obj = json.loads(line)
            stack = [obj]
            while stack:
                cur = stack.pop()
                if isinstance(cur, dict):
                    if "costUsdTicks" in cur and "inputTokens" in cur:
                        last = cur
                    for v in cur.values():
                        if isinstance(v, (dict, list)):
                            stack.append(v)
                elif isinstance(cur, list):
                    stack.extend(cur)
    return last


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--updates", required=True, help="path to updates.jsonl")
    ap.add_argument("--out", required=True, help="usage.json output")
    ap.add_argument("--role", default="primary")
    ap.add_argument("--session-id", default="")
    args = ap.parse_args()
    u = last_usage(Path(args.updates))
    if not u:
        print("error: no usage snapshot found", flush=True)
        return 1
    out = {
        "role": args.role,
        "session_id": args.session_id,
        "inputTokens": u.get("inputTokens"),
        "outputTokens": u.get("outputTokens"),
        "reasoningTokens": u.get("reasoningTokens"),
        "cachedReadTokens": u.get("cachedReadTokens"),
        "totalTokens": u.get("totalTokens"),
        "modelCalls": u.get("modelCalls"),
        "costUsdTicks": u.get("costUsdTicks"),
        "apiDurationMs": u.get("apiDurationMs"),
    }
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
