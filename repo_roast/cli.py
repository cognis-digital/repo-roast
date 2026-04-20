"""repo-roast CLI."""
import argparse, json, sys
from repo_roast.core import roast, TOOL_NAME, TOOL_VERSION
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="repo-roast", description="Let an AI roast (and improve) your repo.")
    ap.add_argument("--version", action="version", version=f"{TOOL_NAME} {TOOL_VERSION}")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--no-llm", action="store_true", help="heuristic roast only (no model)")
    ap.add_argument("--format", choices=["table", "json"], default="table")
    a = ap.parse_args(argv)
    res = roast(a.repo, use_llm=not a.no_llm)
    if a.format == "json": print(json.dumps(res, indent=2)); return 0
    print(f"[{TOOL_NAME}] {a.repo}  score={res['score']}/100\n")
    print(res["roast"])
    return 0
if __name__ == "__main__":
    sys.exit(main())
