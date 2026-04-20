"""repo-roast core — an AI roasts (and constructively critiques) your repo/README."""
from __future__ import annotations
import json, os, urllib.request
from pathlib import Path
TOOL_NAME = "repo-roast"; TOOL_VERSION = "0.1.0"
ENDPOINT = os.environ.get("ROAST_ENDPOINT", "http://127.0.0.1:8774/v1/chat/completions")  # fleet 'uncensored'

def signals(repo: str) -> dict:
    p = Path(repo)
    readme = next((p / n for n in ("README.md", "readme.md") if (p / n).exists()), None)
    return {
        "has_readme": bool(readme),
        "readme_len": len(readme.read_text(encoding="utf-8", errors="ignore")) if readme else 0,
        "has_tests": any(p.rglob("test_*.py")) or (p / "tests").exists(),
        "has_ci": (p / ".github" / "workflows").exists(),
        "has_license": any((p / n).exists() for n in ("LICENSE", "LICENSE.md")),
        "has_docker": (p / "Dockerfile").exists(),
    }

def heuristic_score(s: dict) -> int:
    return sum([s["has_readme"], s["readme_len"] > 300, s["has_tests"], s["has_ci"], s["has_license"], s["has_docker"]]) * 16

def roast(repo: str, use_llm: bool = True) -> dict:
    s = signals(repo); score = heuristic_score(s)
    out = {"tool": TOOL_NAME, "repo": repo, "signals": s, "score": min(100, score)}
    if use_llm:
        try:
            msg = [{"role": "user", "content": f"Roast this repo lovingly, then give 3 concrete fixes. Signals: {json.dumps(s)}"}]
            body = json.dumps({"messages": msg, "temperature": 0.9, "max_tokens": 400}).encode()
            req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                out["roast"] = json.loads(r.read())["choices"][0]["message"]["content"]
        except Exception:
            out["roast"] = _canned(s)
    else:
        out["roast"] = _canned(s)
    return out

def _canned(s: dict) -> str:
    bits = []
    if not s["has_readme"] or s["readme_len"] < 300: bits.append("Your README could fit in a tweet. Sell it.")
    if not s["has_tests"]: bits.append("No tests? Bold. The bugs say thanks.")
    if not s["has_ci"]: bits.append("No CI — 'works on my machine' energy.")
    if not s["has_license"]: bits.append("No LICENSE; legally it's Schrödinger's code.")
    if not s["has_docker"]: bits.append("No Dockerfile; setup is a choose-your-own-adventure.")
    return " ".join(bits) or "Honestly? This repo is clean. Annoyingly clean. Ship it."
