"""repo-roast CLI."""
import argparse
import json
import sys

from repo_roast.core import TOOL_NAME, TOOL_VERSION, roast


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="repo-roast",
        description="Let an AI roast (and improve) your repo.",
    )
    ap.add_argument(
        "--version", action="version", version=f"{TOOL_NAME} {TOOL_VERSION}"
    )
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument(
        "--no-llm",
        action="store_true",
        help="heuristic roast only (no model)",
    )
    ap.add_argument("--format", choices=["table", "json"], default="table")
    a = ap.parse_args(argv)
    try:
        res = roast(a.repo, use_llm=not a.no_llm)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"error: unexpected failure — {exc}", file=sys.stderr)
        return 1
    if a.format == "json":
        print(json.dumps(res, indent=2))
        return 0
    print(f"[{TOOL_NAME}] {a.repo}  score={res['score']}/100\n")
    print(res["roast"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
