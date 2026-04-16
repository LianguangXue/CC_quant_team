# Quant Review Dimensions

> 5 pre-filled review dimensions for quant projects. At project setup (Step 1), team-lead selects the applicable subset based on project type, and weights are confirmed. Reviewers (`code-validator`, `research-validator`, `risk-manager`) score each applicable dimension as STRONG / ADEQUATE / WEAK when producing verdicts.

Stored in project `CLAUDE.md ## Review Dimensions`. Standard checks (security, quality, performance, doc-sync) always apply on top.

---

## Applicability Matrix

| Project Type | RD-1 Correctness | RD-2 Reproducibility | RD-3 Performance | RD-4 Capacity & Risk | RD-5 Observability |
|--------------|:---:|:---:|:---:|:---:|:---:|
| Data pipeline | HIGH | HIGH | MED | — | MED |
| Feature research (HFT/LFT) | **CRITICAL** | HIGH | MED | — | — |
| Model research | **CRITICAL** | **CRITICAL** | MED | — | — |
| Strategy development | **CRITICAL** | HIGH | MED | **CRITICAL** | HIGH |
| Performance engineering | MED | HIGH | **CRITICAL** | — | — |
| Live trading infra | HIGH | HIGH | HIGH | **CRITICAL** | **CRITICAL** |

**CRITICAL** = any WEAK on this dimension is a hard block (verdict cannot be `[OK]`).

---

## RD-1: Research Correctness

**Weight default: CRITICAL for any research/modeling/strategy project**

**Owner**: `research-validator` (primary), `code-validator` (secondary for code-level correctness)

**STRONG calibration**:
- Walk-forward respected, lookahead-free, survivorship-adjusted universe
- All seeds set; reproducible
- OOS untouched except documented final check
- Multiple-testing adjusted where applicable
- Methodology fully reproducible from `findings.md` alone
- Bias checklist: all 7 rows `[OK]`

**ADEQUATE calibration**:
- Minor issues (e.g., seed missing in one script, one OOS peek not logged)
- Methodology sound overall; fixable in one commit
- Bias checklist: at most 1 row `[CONCERN]`

**WEAK calibration**:
- Any INV-T* violation (lookahead, non-monotonic timestamps, random time-series split)
- INV-D1 violation (survivorship)
- INV-S3 violation (repeated OOS peeking)
- Bias checklist: 2+ rows `[CONCERN]` or any `[BLOCK]`
- Backtest result is unreliable

**Hard block on WEAK.** Research-validator's `[BLOCK]` verdict flows into project verdict as WEAK on this dimension.

---

## RD-2: Reproducibility

**Weight default: HIGH (CRITICAL for model research)**

**Owner**: `research-validator` for research artifacts; `code-validator` for code

**STRONG calibration**:
- Config-driven, seed-controlled, fully versioned artifacts
- Artifact path: `artifacts/<name>-<timestamp>/` with data range + feature hash + hyperparams + seed + git commit
- Another team member can rerun in 1 command and match results to ~1e-6 (within floating-point tolerance)
- Environment captured (pyproject.toml / conda env)

**ADEQUATE calibration**:
- Reproducible with some setup (manual data download, env vars documented)
- Results match to reasonable tolerance (~1e-4)

**WEAK calibration**:
- Hardcoded paths / dates / seeds in script body
- No artifact versioning
- Results cannot be reproduced next month
- Missing `requirements.txt` / `environment.yml`

---

## RD-3: Performance

**Weight default: MEDIUM (CRITICAL for perf engineering projects, HIGH for HFT, LOW for pure LFT research)**

**Owner**: `algorithm-engineer` (when consulted), `code-validator` (general review)

**STRONG calibration**:
- Profiled before optimizing (no premature optimization)
- Hot paths use Cython / C++ / pybind11 / Numba where justified
- Memory layout cache-aware where relevant (structs-of-arrays for hot loops)
- Benchmarks documented in `findings.md` (before/after wall time, CPU, memory, correctness check)
- pybind11 signatures match C++ exactly

**ADEQUATE calibration**:
- Pure Python with vectorized numpy/pandas/polars — adequate for current use case
- No profiling done but no known bottleneck
- Performance not the current bottleneck

**WEAK calibration**:
- Obvious inefficiency blocks progress (e.g., 6h pandas loop where vectorized = 30s)
- Optimization done without profile evidence ("cargo cult perf")
- C++/Python signature mismatch (runtime error waiting to happen)
- Optimization claim without benchmark numbers

Only rated WEAK when performance actually matters for the task.

---

## RD-4: Capacity & Risk Awareness

**Weight default: CRITICAL for strategy/live projects, N/A for pure feature/model research**

**Owner**: `risk-manager`

**STRONG calibration**:
- Capacity analyzed at projected AUM + 2× projected AUM
- Slippage modeled (proportional to volume, market impact function documented)
- Fees modeled (commission + stamp duty + exchange + market-impact)
- Risk limits defined (per-position / per-sector / gross / net / turnover)
- Correlation-to-existing-strategies reported
- Tail-risk stress: minimum 3 scenarios (historical crisis + synthetic tail + regulatory shock)
- Circuit breakers defined

**ADEQUATE calibration**:
- Research-stage strategy with clear capacity/risk assumptions documented as "to be refined before deployment"
- Slippage / fees present but simplified
- Some stress scenarios run

**WEAK calibration**:
- Live-ready claim without capacity analysis
- Zero-slippage or zero-fee backtest
- No tail-risk stress
- Unknown correlation to existing live strategies

**Hard block on WEAK for live deployment.** Risk-manager's `[RISK-BLOCK]` verdict flows into project verdict as WEAK.

---

## RD-5: Observability

**Weight default: MEDIUM (HIGH for live strategies, CRITICAL for live trading infra)**

**Owner**: `backend-dev`, `risk-manager`

**STRONG calibration**:
- Structured logs for key decisions (order placement, signal generation, risk overrides)
- PnL attribution decomposition (alpha / slippage / fees / residual)
- Monitoring hooks defined and wired to dashboard
- Live-vs-sim comparison scripted and alerting
- Incident post-mortem workflow established

**ADEQUATE calibration**:
- Basic logging present
- Monitoring designed but not yet wired
- Manual PnL comparison (not automated)

**WEAK calibration**:
- Silent strategy — no way to diagnose if live PnL diverges from sim
- Key events not logged (cannot answer "why did strategy do X?" post-hoc)
- No alerting infrastructure

---

## Selection at Project Setup

During Step 1 consultation, team-lead asks:
1. "What's the project type?" (matches the Applicability Matrix row)
2. "Any dimensions you want to elevate / suppress?" (user override)
3. Confirms final dimension list + weight

The chosen subset is written into `CLAUDE.md ## Review Dimensions` with calibration anchors copied verbatim from this file. Reviewers reference the CLAUDE.md section during every review.

---

## Dimension → Reviewer Mapping

| Dimension | Primary Reviewer | Secondary |
|-----------|-----------------|-----------|
| RD-1 Research Correctness | `research-validator` | `code-validator` |
| RD-2 Reproducibility | `research-validator` | `code-validator` |
| RD-3 Performance | `code-validator` | `algorithm-engineer` (consulted) |
| RD-4 Capacity & Risk | `risk-manager` | — |
| RD-5 Observability | `risk-manager` | `backend-dev` (for infra-level observability) |

When multiple reviewers score the same dimension, the more conservative verdict wins (e.g., if `research-validator` says STRONG and `code-validator` says WEAK on reproducibility, the project verdict for RD-2 is WEAK until resolved).

---

## Scoring Protocol

Every review output includes a dimension score table:

```markdown
| Dimension | Weight | Score | Justification |
|-----------|--------|-------|---------------|
| RD-1 Research Correctness | CRITICAL | STRONG | All 7 bias checks [OK]; walk-forward validated |
| RD-2 Reproducibility | HIGH | ADEQUATE | Seeds set; artifact saved; missing env capture |
| RD-3 Performance | MEDIUM | STRONG | Feature computation 2.3s/day, acceptable |
```

**Verdict rules**:
- Any CRITICAL-weight dimension scored WEAK → verdict is `[BLOCK]`
- Any HIGH-weight dimension scored WEAK → verdict is `[WARN]` (may advance with team-lead approval)
- All dimensions ADEQUATE or above → verdict may be `[OK]`

---

## Anti-Leniency Rule (from CCteam)

When scoring, do NOT rationalize issues away. If you find yourself writing "this is minor" or "probably fine" — stop. Score at face value. The developer can push back; the reviewer's job is to surface, not filter.

Particularly important for `research-validator` — subtle bias findings often feel minor until they're not.
