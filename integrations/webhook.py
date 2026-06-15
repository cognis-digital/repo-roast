#!/usr/bin/env python3
"""Minimal, dependency-free webhook forwarder for Cognis findings.

Reads JSON findings on stdin and POSTs them to a URL (SIEM/Slack/Jira bridge).
Usage:  <tool> scan . --format json | python integrations/webhook.py --url URL
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--header", action="append", default=[], help="Key: Value")
    ap.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="HTTP timeout in seconds (default: 15)",
    )
    args = ap.parse_args()

    raw = sys.stdin.read()
    if not raw.strip():
        print("error: stdin is empty — nothing to post", file=sys.stderr)
        return 2

    # Validate that stdin is parseable JSON before sending.
    try:
        json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"error: stdin is not valid JSON — {exc}", file=sys.stderr)
        return 2

    payload = raw.encode("utf-8")

    # Validate header format early so we fail before touching the network.
    parsed_headers: list[tuple[str, str]] = []
    for h in args.header:
        if ":" not in h:
            print(
                f"error: --header {h!r} has no colon separator (expected 'Key: Value')",
                file=sys.stderr,
            )
            return 2
        k, _, v = h.partition(":")
        if not k.strip():
            print(
                f"error: --header {h!r} has an empty key",
                file=sys.stderr,
            )
            return 2
        parsed_headers.append((k.strip(), v.strip()))

    req = urllib.request.Request(args.url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in parsed_headers:
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as r:
            print(f"posted {len(payload)} bytes -> {r.status}")
        return 0
    except urllib.error.HTTPError as exc:
        print(f"webhook error: HTTP {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"webhook error: {exc.reason}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"webhook error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
