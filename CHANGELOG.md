# Changelog

All notable changes to `cc-quant-team` are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows SemVer-ish: patch = typos/wording, minor = new check or role tweak, major = breaking role/file-structure change.

---

## [0.1.3] — 2026-04-16

### Added
- **Milestone Consolidation protocol** for team-lead (SKILL.md + CLAUDE.md template):
  - Step 1: Consolidate scattered agent findings into root `findings.md` as `[MILESTONE]` entries with key metrics, conclusions, and links
  - Step 2: Extract durable knowledge (schemas, interfaces, capacity, metrics) into relevant `docs/` file (`data-schemas.md` / `pipeline-flow.md` / `strategy-contracts.md` / `invariants.md`)
  - Step 3: Update `docs/index.md` with new section/line ranges
- Team-lead bookkeeping now explicitly owns **5 root files**: `task_plan.md`, `progress.md`, `findings.md`, `decisions.md`, `team-snapshot.md` (was 2 before)
- Self-check expanded from 4 to 7 items (adds findings consolidation, docs currency, team-snapshot staleness)

### Changed
- CLAUDE.md bookkeeping table expanded: 5 files × 7 event triggers

---

## [0.1.2] — 2026-04-16

### Added
- **Team-Lead Bookkeeping Protocol (MANDATORY)** in SKILL.md: trigger→file→content table, progress.md entry format template, and ~5-interaction self-check
- Phase Advancement strengthened from "read and advance" to **READ → WRITE → ADVANCE** — each phase boundary now has mandatory writes to `task_plan.md` + `progress.md` before advancing
- CLAUDE.md template: Team-Lead Bookkeeping condensed table (survives context compression)
- CLAUDE.md Key Protocols: "Team-lead bookkeeping" and "Team-lead self-check" placed at top of table for maximum visibility after compaction

### Fixed
- Team-lead was previously not updating project-level files as the project progressed. After context compression, project-level state was lost, leaving only scattered agent files with no coherent picture.

---

## [0.1.1] — 2026-04-16

### Added
- **Progress Tracking (MANDATORY)** section in agent onboarding: agents MUST break tasks into 5-15 min sub-steps and append to `progress.md` immediately after each sub-step (not at task end)
- Progress-entry format template with fields: Step / Status / What I did / Output / Duration / Next
- Anti-patterns explicitly called out (empty progress.md, single vague entry, late batched update)
- "Receive task → decompose → confirm" protocol: agents must write sub-step checklist to `task_plan.md` before starting; acknowledgement to team-lead includes the checklist

### Fixed
- Agents were completing whole tasks without writing any progress. This made it impossible for team-lead to check status or for successor agents to pick up where they left off.

---

## [0.1.0] — 2026-04-16

Initial release.

### Added
- Plugin metadata (`plugin.json`, `marketplace.json`) under name `cc-quant-team`
- LICENSE: MIT with attribution to CCteam-creator upstream
- `SKILL.md` (572 lines) — 5-step setup flow adapted from CCteam-creator v1.4.3:
  - Quant-specific triggers (quant team / research team / hft team / lft team / strategy team)
  - 11-role recommendation table
  - Quant phase flow (Data → Features → Models → Strategy → Risk → Live)
  - 3 mandatory gates: research-validator, risk-manager, reproducibility
- `references/roles.md` (462 lines) — 11 quant role definitions:
  - backend-dev, frontend-dev (lazy)
  - algorithm-engineer (volume multi-instance)
  - hft-researcher / lft-researcher (direction multi-instance)
  - data-engineer
  - model-researcher (opus)
  - strategy-researcher (opus)
  - code-validator
  - research-validator (opus)
  - risk-manager (opus)
- `references/quant-invariants.md` (275 lines) — 21 pre-filled invariants:
  - Temporal (T1-T4): lookahead, timestamp monotonicity, walk-forward, Ts vs ExchangeTs
  - Data (D1-D4): survivorship, corporate actions, silent NaN, decimal precision
  - Reproducibility (R1-R3): seeds, artifact versioning, config-driven
  - Statistical (S1-S3): multiple-testing, stationarity, OOS sacred
  - Execution (E1-E4): slippage, fees, trading calendar, capacity
  - Code hygiene (C1-C4): typing imports, stdlib shadowing, indent/width, docstrings
- `references/quant-review-dimensions.md` (209 lines) — 5 review dimensions with STRONG / ADEQUATE / WEAK calibration + applicability matrix for 6 project types
- `references/templates.md` (1583 lines) — Quant-adapted CCteam templates:
  - CLAUDE.md with 11-role roster, 5 review dimensions, 4 pre-seeded Style Decisions, 2 seed Known Pitfalls
  - 9 task-folder templates (task, perf, research, pipeline, model, strategy, review, test, research-review, risk)
  - docs/ templates (pipeline-flow, data-schemas, strategy-contracts, invariants)
  - team-snapshot.md template
- `references/onboarding.md` (723 lines) — Common template + 11 role-specific onboarding prompts
- `scripts/common_checks.py` (437 lines) — 4 universal checks (U-1 through U-4)
- `scripts/quant_golden_rules.py` (587 lines) — 5 quant-specific checks (Q-1 through Q-5, all AST-based where applicable)

### Self-tested
- `common_checks.py` against repo itself: 0 FAIL, 0 WARN
- `quant_golden_rules.py` against repo itself: 0 FAIL, 0 WARN, 2 expected SKIP
