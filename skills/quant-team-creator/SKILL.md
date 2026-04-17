---
name: quant-team-creator
description: >
  Set up a multi-agent quantitative research and trading team with file-based planning.
  Use when: (1) user asks to start a new complex quant project with a team, (2) user says
  "set up quant team", "create quant team", "build a research team", "start quant project",
  (3) user invokes /quant-team-creator with a project name, (4) user wants to organize
  a multi-phase quant project with parallel agent workers and persistent progress tracking.
  Creates TeamCreate, planning files (.plans/project/), per-agent work directories,
  pre-filled quant invariants and review dimensions, and spawns configured teammates.
  TRIGGER on: "quant team", "research team", "trading team", "start quant project",
  "set up quant team", "build a quant team", "organize quant project", "hft team",
  "lft team", "strategy team".
  IMPORTANT: You (team-lead) MUST read all reference files directly — do NOT delegate to subagents.
  NOTE: After initial setup, you can add new teammates at any time — just spawn a new Agent
  with the team_name and follow the same onboarding pattern. The team is not locked after creation.
---

# Quant Team Project Setup

Set up a multi-agent quantitative research and trading team for complex projects, using
persistent files for planning and progress tracking. This skill is a quant-adapted fork
of CCteam-creator — same file-based infrastructure, team-lead control plane, and harness
mechanisms, but specialized for quant research, trading strategy development, HFT/LFT
feature engineering, C++/Python performance work, and risk management.

## Prerequisites

**Before starting Step 1**, you (team-lead) MUST read all reference files directly into your own context:

```
Read references/onboarding.md
Read references/templates.md
Read references/roles.md
Read references/quant-invariants.md
Read references/quant-review-dimensions.md
```

Do NOT delegate this to a subagent (Explore, general-purpose, etc.). Subagents return
summaries, losing critical detail — you need the full templates and onboarding prompts
to generate files and spawn agents correctly.

## Process

**Step 0 Update Check (auto)**: Background version fetch + one-line notification if newer version exists
**Step 0 Detect (auto)**: Check if `.plans/` exists → if yes, offer to resume existing project
1. **Requirements Consultation** — Introduce the quant team mechanism and gather quant-specific requirements
2. **Confirm the Plan** — Summarize requirements and let the user confirm the team configuration
3. Create planning files (including per-agent subdirectories)
4. Create the team + spawn agents
5. Confirm setup + guide user to compact context

## Step 0 Update Check: Version Self-Check (Auto — Before Anything Else, ~2s)

Before any other step, perform a lightweight version check. **No user consent needed, do not ask any questions.**

1. **Remote version**: WebFetch `https://raw.githubusercontent.com/LianguangXue/CC_quant_team/master/.claude-plugin/plugin.json` with prompt: "What is the value of the version field? Respond with just the version string."
2. **Local version**: Use Bash to read local plugin.json (try these paths in order, use the first that exists):

   ```bash
   cat ~/.claude/plugins/cache/cc-quant-team/CC_quant_team/*/.claude-plugin/plugin.json 2>/dev/null || \
   cat ~/.claude/skills/quant-team-creator/.claude-plugin/plugin.json 2>/dev/null
   ```

   Extract the version field from the output.
3. **Compare**:
   - **remote ≤ local**, OR **WebFetch failed**, OR **local plugin.json not found** → **completely silent**, proceed to the next step
   - **remote > local** → print **one** notification line:
     > ℹ️ A newer quant-team-creator version is available (<local> → <remote>). It will auto-apply on next Claude Code startup. Continuing with <local> in this session.

**Hard rules**:
- ❌ Do NOT ask the user "continue with old version?"
- ❌ Do NOT attempt to Bash-update the plugin cache yourself
- ❌ Do NOT render the version check as a visible task in TodoWrite
- ❌ If the network fails, do NOT retry
- ✅ At most one notification line, then **immediately** proceed to the next step

## Step 0 Detect: Detect Existing Project (Auto — Before Anything Else)

Before starting setup, check if `.plans/` directory exists in the current working directory.

**If `.plans/` exists**:
1. Read the project CLAUDE.md (auto-loaded) to get the team roster and project context
2. Scan `.plans/` for project directories — if multiple, list them
3. Tell the user: "I found an existing project [name] with [roster]. Resume this project or start a new one?"
4. **If resume**:
   a. Check if `.plans/<project>/team-snapshot.md` exists
   b. **If snapshot exists**: Read the snapshot header metadata. Compare skill source file timestamps against snapshot generation time:
      - **Source files unchanged** → use cached onboarding prompts from snapshot to spawn agents directly
      - **Source files changed** → inform user and let them decide: fast resume vs re-read skill files
   c. **If no snapshot**: Fall back to reading all skill reference files to rebuild onboarding prompts, then spawn agents
   d. After spawning, check TaskList / read progress files to pick up where things left off
5. **If new**: Proceed to Step 1 as normal

**If `.plans/` does not exist**: Skip directly to Step 1.

## Step 1: Requirements Consultation (Talk First, Then Act)

**Goal of this step**: Help the user fully understand how the quant team works, while
gathering their actual quant project requirements. Do not rush to create files or teams.

### 1.1 Introduce the Quant Team Mechanism

In a natural, conversational tone (do not copy this text verbatim — adapt to context),
explain the following points:

**What a quant team is**:
- You (Claude) act as team-lead, simultaneously directing multiple AI agents working in parallel
- Team-lead is the **main conversation control plane**, not a spawned teammate
- Each agent has a clearly defined quant role (research, modeling, strategy, engineering, risk, validation)
- Agents communicate directly with each other (e.g., hft-researcher reaching out to research-validator directly)
- All progress is persisted via the file system, so context loss is not a concern

**When it's a good fit**:
- Multi-stage quant pipeline projects (data ingestion + feature engineering + modeling + strategy + risk)
- Parallel feature research (multiple hft/lft researchers exploring different feature families)
- C++/Python performance engineering alongside quant research
- Pre-production strategy validation with formal research-correctness and risk gates
- Long-running research projects that need reproducible experiment tracking

**When it's NOT a good fit**:
- One-off ad-hoc analysis or exploratory data analysis
- Single-script feature prototyping (no downstream dependencies)
- Simple bug fixes or config changes in an existing quant codebase

**How it works**:
- The team-lead (you) assigns tasks, coordinates progress, and makes decisions
- The team-lead also owns user alignment, phase transitions, and durable operating rules
- Each agent has its own working directory (`.plans/<project>/`), recording tasks, findings, progress
- Agents escalate blockers to team-lead, who provides direction after review
- After research/development, outputs pass mandatory gates:
  - Research outputs (features, models) → `research-validator` gate
  - Strategies → `risk-manager` gate before live deployment
  - Code → `code-validator` review for large features/modules

### 1.2 Gather User Requirements

After the introduction, learn the following through conversation:

1. **Working language** — Observe the language the user communicates in. If they use English, the team responds in English; if Chinese, team responds in Chinese. Match the language in CLAUDE.md and onboarding prompts accordingly
2. **Project type** — Which of these best describes the project?
   - **Data pipeline** (raw data → parquet, schema design, ETL)
   - **Feature research** (HFT tick-level features, LFT daily/minute features, or both)
   - **Model research** (ML/DL signal generation, alpha modeling)
   - **Strategy development** (portfolio construction, execution, simulator)
   - **Performance engineering** (C++ acceleration, pybind11, memory optimization)
   - **Live trading infra** (exchange connectivity, order management, monitoring)
   - **Mixed** (spans multiple of the above)
3. **Frequency focus** — HFT (tick/L2) / MFT (minute) / LFT (daily+) / mixed?
4. **Data sources** — What data is the team working with? (e.g., Datayes L2, tick data, daily OHLCV, fundamentals, alternative data). Confirm paths and formats.
5. **What the user wants to accomplish** — Project goals, deliverables, success criteria
6. **Current state** — Greenfield or existing codebase? Which repos are involved? (BitebitQuant Tool/Data/Structure repos? Strategy repo? New repo?)
7. **Going-to-production scope** — Research only? Or will strategies go live? (Determines whether `risk-manager` gate and `backend-dev` live-infra roles are needed)
8. **User involvement** — Do they want to be involved in every decision, or prefer the team to work autonomously?
9. **Special requirements** — Deadlines, capacity targets, Sharpe/MaxDD bars, regulatory constraints
10. **Quality priorities** — Which review dimensions matter most? (See §1.3 Review Dimensions)

**Note**: Do not fire all questions at once. Follow up naturally based on the user's answers.
If the user's requirements are already clear, you may skip some questions.

### 1.3 Recommend a Team Configuration

Based on the user's needs, recommend an appropriate combination of roles. Explain each
role's purpose and why you're recommending it.

Available quant roles (full roster in [references/roles.md](references/roles.md)):

| Role | Name | Model | Multi-instance | When to include |
|------|------|-------|----------------|-----------------|
| Backend Dev | `backend-dev` | sonnet | no | Live trading infra, exchange API, order DB, realtime feed |
| Frontend Dev | `frontend-dev` | sonnet | no | **Lazy** — only when viz/dashboard needed |
| Algorithm Engineer | `algorithm-engineer` | sonnet | yes (volume) | C++/Python perf work, pybind11, memory optimization |
| HFT Researcher | `hft-researcher` | sonnet | yes (direction) | Tick-level / L2 feature engineering |
| LFT Researcher | `lft-researcher` | sonnet | yes (direction) | Daily/minute feature engineering |
| Data Engineer | `data-engineer` | sonnet | no | Historical pipeline, parquet schemas, data quality |
| Model Researcher | `model-researcher` | opus | no | DL/ML signal/alpha modeling |
| Strategy Researcher | `strategy-researcher` | opus | no | Portfolio construction, execution, simulator |
| Code Validator | `code-validator` | sonnet | no | Code review + writes corner-case tests |
| Research Validator | `research-validator` | opus | no | Lookahead / survivorship / leakage / overfitting checks |
| Risk Manager | `risk-manager` | opus | no | Fund verification, strategy risk, monitoring |

> **Model default**: `sonnet` for most roles. `opus` for `model-researcher`, `strategy-researcher`,
> `research-validator`, and `risk-manager` — these require deep reasoning (signal design,
> multi-factor tradeoffs, subtle bias detection, tail-risk analysis). Cost-justified because
> a missed lookahead bias or risk miscalibration costs far more than opus tokens.

See [references/roles.md](references/roles.md) for detailed role definitions.

**Recommendation principles**:
- **More roles is not always better** — choose based on actual project needs
- **Minimal research team (2-3 agents)**: 1 researcher + `research-validator` + optionally `data-engineer` — for pure feature research projects
- **Full research-to-production (6-8 agents)**: `data-engineer` + 1-2 researchers + `model-researcher` + `strategy-researcher` + `research-validator` + `risk-manager` + `code-validator`
- **Performance-focused (3-4 agents)**: 1-2 `algorithm-engineer` + `code-validator` + the role owning the slow code
- **Live-trading (full team)**: all of the above + `backend-dev` + `risk-manager` (mandatory for live)
- **Multi-instance researchers**: Spawn multiple when research workload is large enough to benefit from parallelism:
  - **Volume splitting** (e.g., `algorithm-engineer-1` optimizes feature pipeline, `algorithm-engineer-2` optimizes orderbook reconstruction)
  - **Direction splitting** (e.g., `hft-researcher-microstructure`, `hft-researcher-orderflow`)
  - Name by number for volume splits, by focus for direction splits
  - **Anti-pattern**: Do NOT split when direction B depends on A's output
- **`research-validator` is mandatory** for any project producing features, models, or signals. This is the single most important gate for preventing subtle quant bugs
- **`risk-manager` is mandatory** for any strategy going to live trading
- **`code-validator` recommended** for teams with 4+ agents or long-running projects — for small teams, team-lead can absorb code review directly
- **Custom roles**: Users can define additional roles (e.g., `ml-infra-engineer`, `tca-analyst`). Provide: name, responsibilities, model, subagent_type.

### 1.4 What Users Can Customize

Inform the user that the following can all be adjusted as needed:

- **Role composition**: Which roles to include
- **Multi-instance count**: How many instances of each multi-instance-capable role (researchers, algorithm-engineer)
- **Custom roles**: If standard roles don't cover the need, new roles can be defined
- **Task phases**: How many phases and the goal of each
- **Technical decisions**: Language (Python/C++/Cython), frameworks (PyTorch/JAX/XGBoost/LightGBM), data format (parquet/pkl.gz), simulator choice
- **Review dimensions**: Which of the 5 pre-filled dimensions apply (Research Correctness / Reproducibility / Performance / Capacity & Risk / Observability). Default weights can be adjusted
- **Invariants**: Which of the 21 pre-filled quant invariants apply. Team-lead may remove invariants that don't apply (e.g., INV-E1–E4 for pure research projects with no live trading)
- **Data paths** for `quant_golden_rules.py` (Q-1 timestamp monotonicity check)

Team-lead = the main conversation (you). Do not generate a team-lead agent.

If the user is improving an **existing quant team system** rather than starting from scratch,
explicitly decide whether the change belongs in:

- the current project's docs only, or
- the `CC_quant_team` source templates themselves

Rule of thumb:

- project-specific workflow tweaks → update project docs
- durable team protocol changes (role boundaries, onboarding, invariants list, review
  dimensions, golden rules, CLAUDE.md template) → update `CC_quant_team` first

Do not recommend immediately rebuilding an active team unless the template changes are
already written back and a phase boundary has been chosen.

## Step 2: Confirm the Plan

After thorough discussion, use AskUserQuestion to get final user confirmation on:

- **Project name**: Short, ASCII, kebab-case (e.g., `alpha-v3`, `hft-orderflow`, `data-pipeline`)
- **Brief description**: 1-2 sentences
- **Confirmed role list**: Which roles are participating, with multi-instance counts for researchers/engineers
- **Initial phase plan**: A rough breakdown of the project's key phases (e.g., Phase 0 Data Prep / Phase 1 Feature Research / Phase 2 Modeling / Phase 3 Strategy / Phase 4 Risk Review)
- **Selected review dimensions**: Which of the 5 apply, with weights confirmed
- **Selected invariants**: Which of the 21 apply (default: all)
- **Data path configuration**: For Q-1 check (data dirs to scan)

Only proceed to the creation steps after the user confirms.

## Step 3: Create Planning Files

See [references/templates.md](references/templates.md) for file templates.

### Directory Structure

```
.plans/<project>/
  task_plan.md                -- Main plan (lean navigation map, not encyclopedia)
  findings.md                 -- Team-level summary
  progress.md                 -- Work log (archive old entries when bloated)
  decisions.md                -- Architecture decision log
  docs/                       -- Project knowledge base
    index.md                  -- Navigation map with sections & line ranges
    pipeline-flow.md          -- Quant pipeline: data → features → models → signals → strategy → execution
    data-schemas.md           -- All data artifact schemas (raw, features, signals, models, orders)
    strategy-contracts.md     -- Signal → position → order interface (if live trading in scope)
    invariants.md             -- Pre-filled with 21 quant invariants (trimmed per project)
  archive/                    -- Archived history (old progress, old plans)

  <agent-name>/               -- One directory per agent
    task_plan.md              -- Agent task list
    findings.md               -- INDEX only (keep lean, no content dumping)
    progress.md               -- Agent work log (archive old entries when bloated)
    <prefix>-<task>/          -- Task folder (one per assigned task)
      task_plan.md / findings.md / progress.md
```

### Task Folder Pattern (All Roles)

Every role creates task folders when assigned distinct tasks. The root `findings.md` serves
as an **index** — linking to each task-specific findings file instead of dumping everything
into one giant document.

| Role | Folder Prefix | Example |
|------|--------------|---------|
| backend-dev / frontend-dev | `task-` | `task-ctp-client/`, `task-dashboard/` |
| algorithm-engineer | `perf-` | `perf-orderbook-reconstruction/`, `perf-feature-rolling-ops/` |
| hft-researcher / lft-researcher | `research-` | `research-orderflow-imbalance/`, `research-momentum-factor/` |
| data-engineer | `pipeline-` | `pipeline-datayes-l2/`, `pipeline-daily-fundamentals/` |
| model-researcher | `model-` | `model-lgbm-alpha-v1/`, `model-lstm-intraday/` |
| strategy-researcher | `strategy-` | `strategy-momentum-v2/`, `strategy-hft-market-making/` |
| code-validator | `review-` or `test-` | `review-orderbook-cpp/`, `test-feature-pipeline/` |
| research-validator | `research-review-` | `research-review-orderflow-imbalance/` |
| risk-manager | `risk-` | `risk-momentum-v2-preflight/`, `risk-live-monitoring-setup/` |

Quick one-off notes (small bug fixes, config changes) can go directly in root files without a task folder.

## Step 3.5: Generate Project CLAUDE.md

CLAUDE.md in the project working directory is **always loaded into the main session's context**
by Claude Code. This is the mechanism that keeps team-lead operational knowledge persistent
across context compressions.

### What to Generate

Create (or append to) a `CLAUDE.md` file in the **project working directory** (not inside `.plans/`).

See [references/templates.md](references/templates.md) for the CLAUDE.md template. The template must be **dynamically filled**:
- Only list the roles that were confirmed in Step 2
- Fill in the project name and directory paths
- Include custom roles if defined
- Pre-fill Review Dimensions with the subset selected in Step 1
- Pre-fill Style Decisions with user's global CLAUDE.md rules (SD-1 to SD-4 from quant template)

### If CLAUDE.md Already Exists

If the project directory already has a CLAUDE.md, **append** the team operations section at
the end (with a clear separator), do not overwrite the existing content.

### Why This Matters

Without this file, after context compression the team-lead loses all knowledge of:
- Which agents exist and their names
- How to dispatch tasks and check status
- Core protocols (3-Strike handling, research-validator gate, risk-manager gate)

The CLAUDE.md solves this by keeping a concise operations guide permanently in context.

### docs/index.md — Dynamic Navigation Map

In Step 3, also create `docs/index.md` — a detailed navigation map showing each doc's sections
and line ranges. This file is maintained by code-validator (or custodian if added) and actively
Read by agents when they need to find specific information.

See [references/templates.md](references/templates.md) for the docs/index.md template.

### When to Update CLAUDE.md

CLAUDE.md is a **living document**, not a one-time generation. Update it when:
- A recurring failure pattern is captured (→ append to `## Known Pitfalls`)
- Team roster changes (agent added/removed/rebuilt)
- A new protocol is established mid-project
- An architecture decision affects team workflow
- A new invariant is discovered (→ append to `docs/invariants.md`, reference from CLAUDE.md)

Do NOT put task-level details here — only durable operational knowledge.

## Step 3.6: Quant Harness Setup (Mandatory for Quant Projects)

Set up the enforcement infrastructure — this is the core of making research errors
mechanically catchable.

### Copy Check Scripts

Copy both bundled scripts from this skill into the project:

```bash
mkdir -p <project>/scripts
cp <skill-path>/scripts/common_checks.py <project>/scripts/common_checks.py
cp <skill-path>/scripts/quant_golden_rules.py <project>/scripts/quant_golden_rules.py
```

Then configure the bottom of `quant_golden_rules.py` for this project:

```python
# ---- Project configuration ----
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIRS = [...]                    # Python package dirs (e.g., ["Tool", "Data", "StockBook"])
DATA_PATHS = [                      # For Q-1 timestamp monotonicity check
  {"path": "...", "format": "parquet", "ts_col": "Ts"},
  {"path": "...", "format": "pkl.gz", "ts_col": "Ts"},
]
RESEARCH_DIRS = [...]               # For Q-2 unseeded randomness check
PROD_DIRS = [...]                   # For U-3 debug leftovers check
EXEMPT_DIRS = ["tests", "notebooks", "archive"]
Q1_SAMPLE_RATE = 1                  # Files sampled per date/path (0 = all)
Q1_ENABLED = True                   # Disable if data dirs not mounted
```

### Check Inventory (9 checks)

**Universal (common_checks.py)**:
- U-1 File Size: files >800 lines WARN, >1200 FAIL
- U-2 Hardcoded Secrets: regex for API keys, tokens, passwords, broker IDs
- U-3 Debug Leftovers: `print(`, `breakpoint()`, `pdb.set_trace()` in prod dirs (not tests/notebooks)
- U-4 Doc Freshness: docs/ files stale vs source code commits

**Quant-specific (quant_golden_rules.py)**:
- Q-1 Timestamp Monotonicity: `Ts` non-decreasing per instrument per date in all configured data paths (parquet + pkl.gz)
- Q-2 Unseeded Randomness: `numpy.random` / `random` / `torch` imports without seed call
- Q-3 Stdlib Name Shadowing: no files named `io.py`, `types.py`, `random.py`, `collections.py`, etc.
- Q-4 Type Annotation Imports: every `Any`/`Optional`/`Callable`/etc. used as annotation must be in `from typing import ...`
- Q-5 `pd.read_csv` Without dtype: WARN on `pd.read_csv(...)` calls without `dtype=` argument

### Pre-Fill docs/invariants.md

Copy the full quant invariants list from `references/quant-invariants.md` into the project's `docs/invariants.md`. During Step 1 consultation, team-lead confirmed which invariants apply — remove the ones that don't (e.g., INV-E1–E4 for pure research projects).

### CI Script Skeleton

Create `scripts/run_ci.py`:

```python
import sys
from common_checks import check_all as common_check_all
from quant_golden_rules import check_all as quant_check_all

if __name__ == "__main__":
    exit_code = max(common_check_all(), quant_check_all())
    sys.exit(exit_code)
```

Devs add project-specific checks as they write tests. The skeleton does not need to be
complete at project start — it grows as the project grows. But **the file must exist from
day one**, otherwise no one will create it later.

### Check Script Error Message Standard

All check scripts MUST produce agent-readable error messages: `[WHAT] + [WHERE] + [HOW TO FIX]`.

```
# GOOD: agent can directly fix this
[Q-4 TYPING-IMPORT] Tool/stats.py:42 uses Optional but `from typing import Optional` is missing
  File: Tool/stats.py:42
  Symbol used: Optional
  FIX: Add `Optional` to the existing `from typing import ...` statement at line 8,
       OR add a new line: `from typing import Optional`
```

Add the CI command to the project CLAUDE.md Key Protocols table so it survives context compression.

## Step 4: Create Team + Spawn Agents

1. `TeamCreate(team_name: "<project>")`
2. Create tasks via TaskCreate — each with a one-line scope + acceptance criteria + `.plans/` path in the description. Set dependencies (`addBlockedBy`) and owners (`owner`) via TaskUpdate. Specify input/output to minimize inter-agent information loss
3. Spawn each role in parallel, `run_in_background: true`

See [references/onboarding.md](references/onboarding.md) for the onboarding prompt for each role.

4. **Generate team snapshot**: After all agents are spawned, write `.plans/<project>/team-snapshot.md` containing the rendered onboarding prompts and skill file timestamps. This enables fast resume without re-reading all skill files.

## Step 5: Confirm + Compact

Show the user a table of team members and the file locations.

Then **guide the user to run `/compact`** to free up context.

### MUST warn the user before compaction

> **After compaction, team-lead may "lose memory"** — forgetting teammate names, operational protocols, and the current project context. This is normal behavior of Claude Code's compaction.
>
> **If I (team-lead) seem confused after compaction, just tell me one sentence**:
>
> > "Read `.plans/<project>/team-snapshot.md` to restore team state"
>
> This makes me reload the full team roster and all onboarding prompts, returning to a working state immediately.

## Key Rules

- **Dual-system, no duplication**: `.plans/` files are the source of truth (persistent); native TaskCreate is the live dispatch layer. TaskCreate description = one-line summary + `.plans/` path
- **Team-lead is the control plane**: the main conversation owns user alignment, task decomposition, phase gates, main-plan maintenance, CLAUDE.md upkeep
- **Context recovery**: After an agent is compacted, it must first read its task folder's files
- **All roles use task folders**: Every assigned task gets a dedicated folder; root findings.md is an index
- **Code review trigger**: Call `code-validator` after completing a feature/new module; small changes do not require review
- **Research-Validator Gate (quant-mandatory)**: Every feature, model, or signal output MUST pass `research-validator` review before downstream use. This is a hard gate — no exceptions. Subtle bias errors (lookahead, survivorship, leakage) are the #1 cause of quant losses, and they're invisible without an independent check
- **Risk-Manager Gate (quant-mandatory for live)**: Every strategy MUST pass `risk-manager` review before going live. Risk-manager reviews: capacity, slippage modeling, fee modeling, tail-scenario stress, correlation to existing strategies, circuit breakers, monitoring setup
- **Reproducibility Gate**: Every model artifact must be saved with: data range + feature set hash + hyperparameters + seed + git commit. Non-reproducible models cannot be promoted to strategy layer
- **Spawn in parallel**: Launch all independent agents simultaneously
- **No standalone subagents after team exists**: Once the team is created, ALL work goes through teammates via SendMessage. Only exception: spawning a new teammate to permanently join the team
- **Peer Review**: researcher reaches out to research-validator directly; dev reaches out to code-validator directly; strategy-researcher reaches out to risk-manager directly — without going through team-lead
- **Code is the source of truth**: Documentation follows the code. Devs MUST update `docs/data-schemas.md`, `docs/pipeline-flow.md`, and `docs/strategy-contracts.md` when code changes — undocumented schemas do not exist for other agents
- **Invariant-first for high-risk boundaries**: Recurring bugs should be promoted from Known Pitfalls to `docs/invariants.md`, then converted to automated tests. research-validator / risk-manager are second line of defense; automated tests are first
- **Pattern → Automation pipeline**: When research-validator tags `[AUTOMATE]` on a recurring pattern → team-lead adds a new check (Q-6, Q-7, …) to `quant_golden_rules.py`. If the check is universal-quant, flag `[TEAM-PROTOCOL]` for template sync back to `CC_quant_team`
- **Anti-bloat principle**: Root findings.md is a pure index. progress.md should be archived when it gets too long
- **CI gate before review**: When CI script exists, dev must run it and confirm all checks pass before submitting for review. CI failure = task not complete
- **Template-first for durable workflow changes**: if a discovered improvement affects role definitions, onboarding, CLAUDE.md structure, invariants, or golden rules, update `CC_quant_team` source files before recommending a rebuild
- **Rebuild at phase boundaries**: do not rebuild an active team mid-stream unless necessary
- **No archiving**: Completed task folders stay in place — mark `Status: complete` in the root findings.md index
- **Assumption audit**: Every harness component encodes an assumption about model limitations. Audit at major model upgrades or phase boundaries
- **Delegate everything delegable**: team-lead does NOT self-execute — dispatch to the appropriate role

## Team-Lead Operations Guide

### Applying planning-with-files in a Team Context

The core idea behind planning-with-files is: **file system = disk, context = memory, important things must be written to disk**.

In a quant team project, this principle operates at three levels:

| Level | Owner | File Location | Focus |
|-------|-------|--------------|-------|
| Project Global | team-lead | `.plans/<project>/task_plan.md` | Phase progress, pipeline decisions, task assignments |
| Agent Level | Each agent individually | `.plans/<project>/<agent>/` | Task index, general notes, work log |
| Task Level | Each agent | `.plans/<project>/<agent>/<prefix>-<name>/` | Detailed steps, findings, and progress for a specific task |

### Team Status Check (team-lead Self-Check)

Proactively check at these moments:

**Quick scan** (read each agent's progress.md in parallel):
```
Read .plans/<project>/data-engineer/progress.md
Read .plans/<project>/hft-researcher/progress.md
Read .plans/<project>/model-researcher/progress.md
...（adjust for actual roles）
```

**Deep dive** (read findings.md when something seems off):
```
Read .plans/<project>/<agent-name>/findings.md
```

**Gate status check** (specific to quant):
```
Read .plans/<project>/research-validator/findings.md   -- which outputs are blocked/approved
Read .plans/<project>/risk-manager/findings.md          -- which strategies have passed risk gate
```

**Decision alignment**:
```
Read .plans/<project>/task_plan.md
```

Reading order: **progress → findings → task_plan → gate status**

### Message Delivery Timing Constraint (Critical)

`SendMessage` to a spawned teammate is delivered **only when the recipient is idle** (between turns). You cannot interrupt a running agent — messages queue until its current turn ends.

**Consequences for dispatch**:
1. **Front-load everything** in the initial message
2. **No mid-course correction** on a running agent
3. **Granularity tradeoff**: smaller tasks = more checkpoints, more overhead; larger tasks = fewer roundtrips, longer blindness
4. **"How's it going?" pings do not work mid-task**: read `progress.md` / `findings.md` directly
5. **Files are live, messages are not**

### Team-Lead Owns the Control Plane

The team-lead is responsible for:
- user requirement alignment and scope control
- task decomposition with explicit inputs, outputs, and acceptance criteria
- maintaining `.plans/<project>/task_plan.md`, `decisions.md`, and project `CLAUDE.md`
- deciding phase gates: data → research → modeling → strategy → risk → (live)
- enforcing research-validator gate and risk-manager gate
- capturing user taste preferences in Style Decisions
- deciding whether a workflow change is project-local or should be written back into `CC_quant_team`

### Team-Lead Bookkeeping Protocol (MANDATORY)

**Team-lead MUST keep project-level files current.** Agents write to their own dirs;
team-lead writes to the project root. If team-lead doesn't write, there is no project-level
record — only scattered agent files with no coherent picture.

**Team-lead owns 5 root-level files** (agents write to their own dirs; these are project-global):

| File | Purpose | Team-lead role |
|------|---------|---------------|
| `task_plan.md` | Navigation map: phases, task summary, gate status | Primary author. Update §4 / §5 / §6 on every dispatch / completion / phase change |
| `progress.md` | Chronological log of what happened across the team | Append after every significant event (dispatch, completion, verdict, decision, phase) |
| `findings.md` | Cross-team findings consolidation, tagged by source agent | Consolidate important findings from agents at milestones (see Milestone Consolidation below) |
| `decisions.md` | Architecture / pipeline / tool-choice decisions with rationale | New D<N> entry for every non-trivial decision |
| `team-snapshot.md` | Cached onboarding prompts + roster for fast resume | Regenerate when roster changes, at phase boundaries, or when skill source files update |

**When to update — event-driven triggers:**

| Trigger | task_plan.md | progress.md | findings.md | decisions.md | team-snapshot.md |
|---------|:---:|:---:|:---:|:---:|:---:|
| Dispatch a task | §4: add row | append | — | — | — |
| Agent reports completion | §4: mark done | append with verdict | — | — | — |
| Validator verdict | §6: gate status | append | — | — | — |
| Architecture decision | — | append | — | new D<N> | — |
| Phase boundary | §5: phase status | phase summary | **consolidate** (see below) | — | check staleness |
| Roster change | — | append | — | — | **regenerate** |
| New Known Pitfall | — | append | — | — | — |
| Session resume | — | status summary | — | — | check staleness |
| User requests status | — | — | — | — | — |
| **Milestone reached** | — | append | **consolidate** (see below) | if applicable | — |

### Milestone Consolidation (findings.md + docs/)

**At phase boundaries or whenever significant work completes** (a feature family validated, a model finalized, a strategy backtested), team-lead must consolidate:

**Step 1 — Consolidate findings.md**: Read each agent's relevant task-folder findings.md. Extract the **key results, metrics, and conclusions** that matter at the project level. Write a consolidated entry to the main `.plans/<project>/findings.md`:

```
## [MILESTONE] <date> — Phase 2 Feature Research Complete

### Source: team-lead (consolidated from agent findings)

**Features Delivered:**
- Orderflow imbalance family (hft-researcher-orderflow): IC=0.04, rank-IC=0.05, coverage=95%
  - Full report: hft-researcher-orderflow/research-orderflow-imbalance/findings.md
  - Research-validator verdict: [OK] (2026-04-15)
- Momentum factor (lft-researcher): IC=0.03, turnover=0.8, coverage=92%
  - Full report: lft-researcher/research-momentum-factor/findings.md
  - Research-validator verdict: [OK] (2026-04-16)

**Key Technical Decisions:**
- Used Ts (local receive time) not ExchangeTs for all features (INV-T4 compliant)
- OrgData schema frozen as of 2026-04-10 — no further changes until Phase 4

**Blocked / Deferred:**
- Queue position features deferred to Phase 4 (needs StockBook L3 data not yet available)

**Metrics Summary:**
| Feature | IC | Rank-IC | Turnover | Coverage | Validator |
|---------|-----|---------|----------|----------|-----------|
| orderflow_imbalance | 0.04 | 0.05 | 0.6 | 0.95 | [OK] |
| momentum_60d | 0.03 | 0.04 | 0.8 | 0.92 | [OK] |
```

**Step 2 — Update docs/ when milestone reveals important details**: If the milestone produced knowledge that downstream agents need (schema details, interface specifics, performance characteristics, capacity numbers), **create or update the relevant docs/ file** with those details:

| What was learned | Where to put it |
|-----------------|-----------------|
| Feature schema details (columns, dtypes, lookback, NaN handling) | `docs/data-schemas.md` §Features |
| Pipeline latency / throughput numbers from data-engineer | `docs/pipeline-flow.md` §Latency Budgets |
| Model training results + signal output format | `docs/data-schemas.md` §Models + §Signals |
| Strategy backtest metrics + execution model | `docs/strategy-contracts.md` |
| Capacity / risk limits from risk-manager | `docs/strategy-contracts.md` §Risk Limits |
| Newly discovered invariant | `docs/invariants.md` |

**This is NOT copying agent findings verbatim.** Team-lead reads agent findings, extracts the durable knowledge (schemas, metrics, interfaces, constraints), and writes it to the appropriate docs/ file in a structured format that future agents can consume.

**Step 3 — Update docs/index.md**: If any docs/ file was created or significantly changed, update `docs/index.md` with the new section names and line ranges.

**Why this matters**: Agent task-folder findings are detailed but scattered. Without consolidation, the next phase's agents (e.g., model-researcher starting Phase 3) must read 5 different agent directories to understand what features exist. Consolidated findings.md + updated docs/ give them one place to look.

**Format for team-lead progress.md entries:**
```
## <date> — <session title or phase>

### Dispatched
- T5 → hft-researcher-orderflow: orderflow imbalance feature family
- T6 → data-engineer: validate OrgData for 2023H1

### Completed
- T3 (algorithm-engineer): orderbook reconstruction optimized 18.9× — code-validator [OK]
- T4 (lft-researcher): momentum factor — research-validator [CONCERN], needs regime test

### Gate Updates
- research-validator: orderflow-imbalance → [OK]
- risk-manager: momentum-v2 → [RISK-WARN] (capacity concerns at >$30M)

### Decisions
- D4: Use LightGBM over LSTM for alpha-v1 (see decisions.md)

### Milestone Consolidation
- Wrote [MILESTONE] Phase 2 summary to findings.md
- Updated docs/data-schemas.md §Features with orderflow + momentum schemas
- Updated docs/index.md line ranges

### Phase Status
- Phase 2 (Feature Research): 3/5 feature families complete, 2 in progress
- Next milestone: all features research-validator [OK] before Phase 3

### Next Actions
- Wait for hft-researcher-orderflow T5 completion
- Dispatch momentum regime-test to lft-researcher after T4 fix
```

**Self-check (every ~5 interactions with agents or user):**
1. Is `task_plan.md` §4 Task Summary current? (no stale in_progress rows for finished tasks)
2. Is `task_plan.md` §6 Gate Status current?
3. Did I log the last dispatch/completion in `progress.md`?
4. Is `findings.md` up to date? (any agent completions since last consolidation?)
5. Are `docs/` files current with the latest schemas/interfaces/metrics?
6. Does `CLAUDE.md` still reflect actual roster and protocols?
7. Is `team-snapshot.md` stale? (roster changed since last generation?)

If any answer is "no" — update the file NOW before doing anything else.

### Handling Agent 3-Strike Escalations

When an agent reports "3 failures, escalating to team-lead":
1. Read the attempted steps recorded in its progress.md
2. Assess whether the main plan needs to be revised
3. Provide a clear new direction, or reassign the task
4. **Guardrail check**: Will this failure pattern recur?
   - If YES for this project → append to CLAUDE.md `## Known Pitfalls`
   - If YES for future teams → also record `[TEAM-PROTOCOL]` and consider template update
   - If NO (one-off) → no further action

### Phase Advancement Cadence

Each phase advancement has 3 mandatory steps: **READ → WRITE → ADVANCE**.

- **Data phase complete**:
  1. Read data-engineer findings
  2. Confirm `docs/data-schemas.md` current
  3. **Write** to task_plan.md (§5: update phase status) + progress.md (phase summary) + task_plan.md §4 (mark data tasks complete)
  4. Advance to research

- **Research phase complete**:
  1. Read research-validator findings → confirm all outputs `[OK]`
  2. **Write** to task_plan.md (§5 + §6 gate status) + progress.md (which features approved, which blocked)
  3. Advance to modeling

- **Modeling phase complete**:
  1. Read model-researcher findings → confirm artifacts versioned
  2. **Write** to task_plan.md (§5 + §6) + progress.md (model metrics summary, artifact paths)
  3. Advance to strategy

- **Strategy phase complete**:
  1. Read strategy-researcher findings
  2. **Write** to task_plan.md (§5) + progress.md (backtest metrics summary)
  3. Dispatch to risk-manager

- **Risk review complete**:
  1. Read risk-manager verdict
  2. **Write** to task_plan.md (§6 gate status) + progress.md (verdict + conditions)
  3. If `[RISK-OK]` → advance to live; if `[RISK-BLOCK]` → back to strategy

- **All done**:
  1. Read each agent's progress.md in parallel, confirm all tasks marked complete
  2. **Write** final summary to progress.md + update task_plan.md §5 to COMPLETE

**Phase boundary health check** (do this BEFORE writing phase-advance entries):
- Are all agent root findings.md indexes up to date?
- Are there stale `in_progress` tasks in TaskList? → update task_plan.md §4
- Does main task_plan.md phase status match actual progress?
- Is `docs/data-schemas.md` synced with code?
- Have research-validator and risk-manager gates been exercised for every output that crossed the boundary?
- Is `team-snapshot.md` still current? (if roster changed during this phase, regenerate)
