# CC_quant_team

Multi-agent team orchestration for quantitative research and trading projects in Claude Code.

Quant-specialized fork of [CCteam-creator](https://github.com/jessepwj/CCteam-creator) by jessepwj. Keeps the core harness (file-based planning, team-lead control plane, 3-Strike escalation, team-snapshot fast-resume), but replaces web-development roles and checks with quant-specific ones.

## What it does

Turns a single Claude Code session into a coordinated team of quant agents. You talk to the team-lead (the main conversation); team-lead dispatches specialized subagents working in parallel. Progress, findings, and decisions persist in `.plans/<project>/` so nothing is lost across context compressions.

## Team Roster (11 roles)

| Role | Model | Multi-instance | When to include |
|------|-------|---------------:|-----------------|
| `backend-dev` | sonnet | no | Live trading infra (exchange API, order DB) |
| `frontend-dev` | sonnet | no | Dashboard / viz (lazy-loaded) |
| `algorithm-engineer` | sonnet | yes (volume) | C++ / Python perf, pybind11, memory optimization |
| `hft-researcher` | sonnet | yes (direction) | Tick-level / L2 feature engineering |
| `lft-researcher` | sonnet | yes (direction) | Daily / minute feature engineering |
| `data-engineer` | sonnet | no | Historical pipeline, parquet schemas, data quality |
| `model-researcher` | opus | no | DL / ML signal / alpha modeling |
| `strategy-researcher` | opus | no | Portfolio construction, execution, simulator |
| `code-validator` | sonnet | no | Code review + corner-case tests |
| `research-validator` | opus | no | Lookahead / survivorship / leakage / overfitting checks |
| `risk-manager` | opus | no | Fund verification, strategy risk, live monitoring |

Team-lead = the main conversation (you). Not spawned as an agent.

## Quant-specific mechanisms

- **21 pre-filled invariants** covering temporal correctness, data integrity, reproducibility, statistical discipline, execution realism, and code hygiene
- **5 review dimensions**: Research Correctness (CRITICAL) / Reproducibility / Performance / Capacity & Risk / Observability
- **9 automated checks** (4 universal + 5 quant): timestamp monotonicity across parquet + pkl.gz data, unseeded randomness detection, type-annotation import verification, stdlib name shadowing, `pd.read_csv` without dtype
- **Two mandatory gates**: `research-validator` gate before any research output is consumed downstream; `risk-manager` gate before any strategy goes live

## Installation

```
/plugin marketplace add https://github.com/LianguangXue/CC_quant_team
/plugin install cc-quant-team
```

Then invoke with `/quant-team-creator` or natural language:

- "set up a quant team for ..."
- "build a research team ..."
- "start a quant project ..."

## Status

Work in progress. v0.1.0 scaffolding.

## Credits

Based on [CCteam-creator](https://github.com/jessepwj/CCteam-creator) by [@jessepwj](https://github.com/jessepwj). Same MIT license.
