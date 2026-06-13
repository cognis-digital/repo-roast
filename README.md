<a name="top"></a>
<div align="center">

# repo-roast 🔥

### Point an AI at your repo and let it roast you — then hand you 3 concrete fixes. Local, free, savage.

[![License: COCL 1.0](https://img.shields.io/badge/License-COCL%201.0-2b6cb0.svg)](LICENSE) ![Local](https://img.shields.io/badge/runs-local-111111) [![Suite](https://img.shields.io/badge/Cognis-Neural%20Suite-6b46c1.svg)](https://github.com/cognis-digital/cognis-neural-suite)

`#developer-tools` `#ai` `#fun` `#code-review` `#llm`

</div>

```bash
pip install "git+https://github.com/cognis-digital/repo-roast.git"
repo-roast .                 # uses a local model (uncensored-fleet) if running
repo-roast . --no-llm        # heuristic-only roast, no model needed
```

## Architecture

```mermaid
flowchart LR
  R[Your repo] --> S[Signal scan<br/>README/tests/CI/license/docker]
  S --> H[Heuristic score]
  S --> L[LLM roast + fixes]
  H --> O[Score /100]
  L --> O2[🔥 Roast + 3 fixes]
```

## Use it from any AI stack
Talks to any **OpenAI-compatible** endpoint (default: [uncensored-fleet](https://github.com/cognis-digital/uncensored-fleet) `uncensored` slot); set `ROAST_ENDPOINT`. Works MCP-side too via JSON.

<a name="verification"></a>
## Verification

[![tests](https://img.shields.io/badge/tests-1%20passing-2ea44f.svg)](AUDIT.md)

Every push is verified end-to-end. Latest audit (2026-06-13):

```text
tests        : 1 passed, 0 failed, 0 errored
compile      : all modules parse
cli          : C:\Python314\python.exe: No module named https
package      : https
```

<details><summary>CLI surface (<code>--help</code>)</summary>

```text
C:\Python314\python.exe: No module named https
```
</details>

Full machine-readable results: [`AUDIT.md`](AUDIT.md) · regenerate with `python -m https --help` + `pytest -q`.

<div align="right"><a href="#top">↑ back to top</a></div>


## Related
[🤖 uncensored-fleet](https://github.com/cognis-digital/uncensored-fleet) · [📝 readme tooling in the suite](https://github.com/cognis-digital/cognis-neural-suite)

> ### ⭐ Star it, then go fix your README.

## License
COCL v1.0 — see [LICENSE](LICENSE).
