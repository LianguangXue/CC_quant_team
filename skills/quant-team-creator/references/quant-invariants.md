# Quant System Invariants

> Pre-filled list of 21 invariants applicable to quantitative research and trading projects.
> At project setup, team-lead copies the applicable subset into `<project>/.plans/<project>/docs/invariants.md`.
> Invariants not applicable to a given project (e.g., INV-E1–E4 for pure research projects with no live trading) are omitted at setup time.

Each invariant: **one-line rule + WHY it breaks + automated check status**.

---

## I. Temporal Invariants (highest priority)

### INV-T1: No lookahead bias

At current time `t = Ts_current`, features/signals may only depend on events where `Ts ≤ t`. For tick/L2 data this is the **local receive time**, not exchange time.

**Why**: Using any future information silently inflates backtest Sharpe. A backtest with lookahead is a time machine, not a strategy.

**Check**: walk-forward test harness + `research-validator` [RESEARCH-REVIEW].

---

### INV-T2: Timestamp monotonicity

Within an instrument's OrgData / MarketData / Detailed_Level2_Data / Resampled_Data / Level2_Data, `Ts` must be non-decreasing.

**Why**: Non-monotonic timestamps break order book replay, feature computation, and backtest event ordering.

**Check**: `quant_golden_rules.py` **Q-1** (auto-scan of configured data paths).

---

### INV-T3: Walk-forward only for model training

No random splits on time-series data. Train/val/test split by **time**, always.

**Why**: Random splits leak future information into training. On time-series, observations are not i.i.d.

**Check**: `research-validator` reviews the data-loader code and split configuration.

---

### INV-T4: Feature-available time = `Ts` (local receive time), never `ExchangeTs`

At `Ts`, the event is observable locally; `ExchangeTs` happened strictly earlier but cannot be known until the message arrives at `Ts`.

- Correct pattern: all feature values carry their own `Ts` (equal to the `Ts` of the latest input event). Downstream consumers use features only where `feature.Ts ≤ current_Ts`.
- `ExchangeTs` is fine as a feature **value** (e.g., input to latency-aware models) — just not as the "available-at" timestamp.

**Why**: Using `ExchangeTs` as availability understates latency and leaks information from the exchange-to-local propagation gap into the signal.

**Check**: `research-validator` reviews feature code for any reliance on `ExchangeTs` for timing decisions.

---

## II. Data Integrity

### INV-D1: No survivorship bias

The investable universe at time `t` must include delisted names that were tradeable at `t`.

**Why**: Using only currently-listed names upward-biases backtest results by excluding failed companies.

**Check**: `research-validator` reviews universe construction code and methodology documentation.

---

### INV-D2: Corporate actions applied consistently

Adjusted vs unadjusted prices never mixed within one computation. State explicitly which convention is used.

**Why**: Mixing adjusted and unadjusted prices produces meaningless returns at split/dividend events.

**Check**: `research-validator` + explicit dtype annotation in feature/model code.

---

### INV-D3: No silent NaN in production signals

Any `NaN` in a signal output must be an explicit fill or drop with documented reason. Silent `NaN` is a bug.

**Why**: Downstream position sizing treating NaN as 0 (or worse, propagating) can cause unintended positions.

**Check**: `research-validator` — signal output schema review. (Originally planned as Q-7; deferred to human judgment.)

---

### INV-D4: Decimal precision on prices

`float64` for prices is fine in research; for order sizing and accounting, use Decimal or integer ticks.

**Why**: Floating-point rounding errors compound in position accounting and fill reconciliation.

**Check**: `code-validator` reviews order/position code.

---

## III. Reproducibility

### INV-R1: Every random source seeded

Every `np.random.*`, `random.*`, `torch.*`, `random.choice` etc. must have an explicit seed call in the same file or a parent config.

**Why**: Unseeded randomness means re-running the same code produces different results; research findings cannot be verified.

**Check**: `quant_golden_rules.py` **Q-2** (auto-scan for `import random` / `numpy.random` / `torch` without matching seed call).

---

### INV-R2: Model artifacts versioned

Every trained model saved with: data range + feature set hash + hyperparameters + seed + git commit. Artifact path `artifacts/<model-name>-<timestamp>/`.

**Why**: A model without its training recipe cannot be retrained or audited. Strategy-researcher cannot trust a signal whose model cannot be reproduced.

**Check**: `research-validator` reviews artifact directory contents.

---

### INV-R3: Config-driven experiments

No hardcoded dates / paths / hyperparameters / universe definitions in research scripts. All go through a config file checked into git.

**Why**: Hardcoded constants create silent divergence between experiments; reviewer cannot tell which runs used which setup.

**Check**: `code-validator` during review.

---

## IV. Statistical Discipline

### INV-S1: Multiple-testing awareness

If N features / models / strategies tested and the best selected, report multiple-testing-adjusted significance (Bonferroni, Holm, FDR), not the raw selected one.

**Why**: Testing 100 random features will yield ~5 with p<0.05 by chance. Keeping the best without correction is data-snooping.

**Check**: `research-validator` reviews methodology section of `findings.md`.

---

### INV-S2: Stationarity assumptions documented

If a method assumes stationarity (e.g., linear regression, AR(p) models, correlation estimates), `findings.md` states what regime tests were run (ADF, KPSS, rolling statistics).

**Why**: Non-stationary time series break classical statistical inference; assumed-stationary models can give spurious results.

**Check**: `research-validator` reviews methodology documentation.

---

### INV-S3: Out-of-sample is sacred

OOS data accessed **at most once** per strategy candidate. Repeated OOS peeking = data snooping = in-sample.

Every OOS access logged in `findings.md` with date + motivation.

**Why**: Iterating on OOS feedback turns it into another validation set, destroying its purpose.

**Check**: `research-validator` reviews commit history + `findings.md` OOS access log.

---

## V. Execution Realism

(Applicable to projects with live trading or production-style backtests. Omit for pure research.)

### INV-E1: Slippage modeled

No zero-slippage backtests presented as strategy candidates. Slippage model documented.

**Why**: Zero-slippage backtests inflate returns and understate capacity.

**Check**: `risk-manager` [STRATEGY-RISK] review.

---

### INV-E2: Fees modeled

Commission + stamp duty + exchange fees + market-impact modeled.

**Why**: Fees can erode alpha entirely on high-turnover strategies; ignoring them produces fictional profits.

**Check**: `risk-manager` [STRATEGY-RISK] review.

---

### INV-E3: Trading calendar enforced

No trades on non-trading days / outside session hours / during lunch break (A-share-specific).

**Why**: Trading on days when markets are closed produces impossible PnL; including them is a bug.

**Check**: `quant_golden_rules.py` could optionally check this if `configs/trading_calendar.csv` exists. Currently handled by `risk-manager` + `code-validator`.

---

### INV-E4: Capacity estimated

Every strategy reports capacity estimate: at what AUM slippage eats X% of alpha.

**Why**: A strategy with $100k capacity and $10M target AUM is a losing trade in production.

**Check**: `risk-manager` [CAPACITY] review — hard requirement for `[RISK-OK]` verdict.

---

## VI. Code Hygiene (from user's global CLAUDE.md)

### INV-C1: Type annotations imported

Every `Any` / `Optional` / `Callable` / `Union` / `Dict` / `List` / `Tuple` / `Set` / `Sequence` / `Iterable` used as annotation must appear in a `from typing import ...` statement.

**Why**: Missing import causes `NameError` at runtime — and in research code, this can happen deep in a job and waste hours.

**Check**: `quant_golden_rules.py` **Q-4** (auto-parse every `.py` file).

---

### INV-C2: No stdlib name shadowing

No file in package dirs named `io.py`, `types.py`, `collections.py`, `random.py`, `statistics.py`, `math.py`, `datetime.py`, `logging.py`, `csv.py`, `json.py`.

**Why**: Import shadowing causes `from io import BytesIO` to resolve to your local file, producing cryptic import errors.

**Check**: `quant_golden_rules.py` **Q-3**.

---

### INV-C3: 2-space indent, 120-column line max

Per user's global CLAUDE.md.

**Check**: `code-validator` review (or black/ruff with line-length=120 if added).

---

### INV-C4: Google-style docstrings on public functions

Per user's global CLAUDE.md. Every public function has `Args:` / `Returns:` / `Raises:` blocks (Python); `@param` / `@return` (C++).

**Check**: `code-validator` review.

---

## Summary: Automated vs Manual

| Invariant | Owner |
|-----------|-------|
| INV-T1 (lookahead) | `research-validator` |
| INV-T2 (timestamp monotonic) | **Q-1 auto** |
| INV-T3 (walk-forward) | `research-validator` |
| INV-T4 (feature-available time) | `research-validator` |
| INV-D1 (survivorship) | `research-validator` |
| INV-D2 (corporate actions) | `research-validator` |
| INV-D3 (silent NaN) | `research-validator` |
| INV-D4 (decimal precision) | `code-validator` |
| INV-R1 (seeds) | **Q-2 auto** |
| INV-R2 (artifact versioning) | `research-validator` |
| INV-R3 (config-driven) | `code-validator` |
| INV-S1 (multiple-testing) | `research-validator` |
| INV-S2 (stationarity) | `research-validator` |
| INV-S3 (OOS sacred) | `research-validator` |
| INV-E1 (slippage) | `risk-manager` |
| INV-E2 (fees) | `risk-manager` |
| INV-E3 (trading calendar) | `risk-manager` + `code-validator` |
| INV-E4 (capacity) | `risk-manager` |
| INV-C1 (typing imports) | **Q-4 auto** |
| INV-C2 (stdlib shadowing) | **Q-3 auto** |
| INV-C3 (indent / line width) | `code-validator` |
| INV-C4 (docstrings) | `code-validator` |

Of 21 invariants, **4 are automatically checked** by `quant_golden_rules.py` (Q-1 through Q-4); the remaining 17 require human-reasoning review by one of the three validator roles.

When a `[AUTOMATE]` pattern appears 3+ times in validator findings, team-lead routes a new Q-N check to extend `quant_golden_rules.py`.
