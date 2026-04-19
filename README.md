# CC_quant_team

Multi-agent team orchestration for quantitative research and trading projects in Claude Code.

Quant-specialized fork of [CCteam-creator](https://github.com/jessepwj/CCteam-creator) by jessepwj. Keeps the core harness (file-based planning, team-lead control plane, 3-Strike escalation, team-snapshot fast-resume), but replaces web-development roles and checks with quant-specific ones.

**Current version**: 0.1.3

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

## Progress Tracking Discipline

Both team-lead and spawned agents have mandatory progress-tracking protocols.

**Agents**: break tasks into 5-15 min sub-steps and append to `progress.md` *immediately* after each sub-step — not at task end. Anti-patterns (empty progress.md, single vague entry, late batched update) are called out explicitly in the onboarding.

**Team-lead owns 5 root files** at `.plans/<project>/`:

| File | When team-lead updates |
|------|------------------------|
| `task_plan.md` | After every dispatch / completion / verdict / phase change |
| `progress.md` | After every significant event (dispatch, completion, verdict, decision) |
| `findings.md` | At milestones — consolidates scattered agent findings into `[MILESTONE]` entries |
| `decisions.md` | New `D<N>` entry for every non-trivial architecture / pipeline / tool-choice decision |
| `team-snapshot.md` | Regenerated on roster change; staleness-checked at phase boundaries |

**Milestone Consolidation** (at phase boundaries / significant completions):
1. Read agent task-folder findings → synthesize into a `[MILESTONE]` entry in root `findings.md` with key metrics, conclusions, and links
2. Extract durable knowledge (schemas, interfaces, capacity numbers) → update `docs/data-schemas.md` / `docs/pipeline-flow.md` / `docs/strategy-contracts.md` / `docs/invariants.md`
3. Update `docs/index.md` if any docs/ file changed

This means that when Phase 3 starts (say, model-researcher consuming Phase 2 features), everything they need is in *one place* — root findings.md + docs/ — instead of scattered across 5 agent directories.

## Installation

```
/plugin marketplace add https://github.com/LianguangXue/CC_quant_team
/plugin install cc-quant-team
```

Then invoke with `/quant-team-creator` or natural language:

- "set up a quant team for ..."
- "build a research team ..."
- "start a quant project ..."

### Updating

When the plugin is updated upstream, Claude Code auto-fetches on startup. To force-update immediately without restart:

```
/plugin marketplace update cc-quant-team
```

If a team is already running when you update, roster/protocol changes don't propagate to already-spawned agents automatically. Either wait for a phase boundary and rebuild, or hot-patch via `SendMessage` for small protocol tweaks.

## Repository Layout

```
CC_quant_team/
├── .claude-plugin/
│   ├── plugin.json              # cc-quant-team metadata
│   └── marketplace.json
├── skills/quant-team-creator/
│   ├── SKILL.md                 # Skill entry point: 5-step setup flow, team-lead protocol
│   ├── references/
│   │   ├── roles.md             # 11 role definitions + multi-instance rules + team-lead
│   │   ├── onboarding.md        # Common agent template + per-role onboarding prompts
│   │   ├── templates.md         # CLAUDE.md + task folders + docs/ templates
│   │   ├── quant-invariants.md  # 21 pre-filled quant invariants
│   │   └── quant-review-dimensions.md  # 5 review dimensions with calibration
│   └── scripts/
│       ├── common_checks.py     # U-1..U-4 (file size, secrets, debug, doc freshness)
│       └── quant_golden_rules.py # Q-1..Q-5 (timestamp, RNG seed, shadowing, typing, read_csv)
├── docs/images/                 # (for future diagrams)
├── LICENSE                      # MIT (with CCteam attribution)
├── README.md
└── CHANGELOG.md
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Credits

Based on [CCteam-creator](https://github.com/jessepwj/CCteam-creator) by [@jessepwj](https://github.com/jessepwj). Same MIT license.
