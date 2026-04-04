# Thesis Report Rigorous Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a defense-ready, rigorously validated revision of `本科毕业论文-研究报告.md` by fixing implementation inconsistencies, re-running experiments, regenerating figures, and updating all Chapter 4 evidence tables/text with traceable results.

**Architecture:** Execute a strict evidence pipeline: (1) code audit/fix for MTM/RWMH consistency, (2) deterministic experiment runs with logged configs and seeds, (3) 5-run repeatability aggregation, (4) convergence diagnostics extraction, (5) synchronized report rewrite with traceability matrix. No fabricated values are allowed; if core runs fail, stop and report blockers.

**Tech Stack:** Python (`numpy`, `scipy`, `matplotlib`), repository scripts (`src/mcmc_optimized.py`, `src/mcmc_advanced.py`, `src/visualization_optimized.py`), Markdown editing.

---

### Task 1: Environment and Baseline Capture

**Files:**
- Create: `docs/superpowers/notes/2026-04-04-rigorous-run-log.md`
- Read: `src/mcmc_optimized.py`
- Read: `src/mcmc_option_pricing.py`
- Read: `src/mcmc_advanced.py`
- Read: `本科毕业论文-研究报告.md`

- [ ] **Step 1: Capture runtime environment metadata**

Run and record:
- `python --version`
- package versions (`numpy`, `scipy`, `matplotlib`)
- current branch/commit hash

- [ ] **Step 2: Snapshot current report evidence state**

Record current values of table 4-1/4-2/4-3, figure references, and Chapter 4 conclusions in run-log notes for before/after comparison.

- [ ] **Step 3: Build recommendation checklist table**

In run-log notes, add 10-row checklist (from spec mapping) with columns: recommendation, action path, status.


### Task 2: Audit and Fix Core Algorithm Consistency

**Files:**
- Modify: `src/mcmc_optimized.py`
- Modify: `src/mcmc_option_pricing.py`
- Modify (if needed for consistency): `src/mcmc_advanced.py`

- [ ] **Step 1: Inspect RWMH acceptance-ratio naming and expression consistency**

Ensure variable naming and formula expression are clear and consistent with report notation (e.g., log-ratio semantics).

- [ ] **Step 2: Inspect MTM weighted selection and auxiliary-point acceptance logic**

Verify:
- proposal weights computation
- selected/backup candidate handling
- acceptance-ratio expression consistency with documented algorithm

- [ ] **Step 3: Apply minimal corrective edits if mismatch is found**

Only change what is required for correctness/consistency; avoid unrelated refactors.

- [ ] **Step 4: Run script smoke test after edits**

Run: `python src/mcmc_optimized.py`
Expected: script completes and prints comparison outputs.


### Task 3: Main Experiment Run and Structured Output Extraction

**Files:**
- Create: `docs/superpowers/notes/2026-04-04-main-experiment-results.csv`
- Update notes: `docs/superpowers/notes/2026-04-04-rigorous-run-log.md`

- [ ] **Step 1: Run main experiment with fixed seed 42**

Run `python src/mcmc_optimized.py` and capture outputs to log file.

- [ ] **Step 1.5: Enforce and record fixed experiment configs**

Explicitly verify and record these configs in run-log and report appendix section:
- main comparison: `n_samples=20000`, `burn_in=n_samples//4`, `proposal_std=0.3`
- baseline comparison: `n_samples=50000`, `burn_in=n_samples//4`
- repeatability seeds: `42,43,44,45,46`

- [ ] **Step 2: Extract required metrics into CSV**

For each method (RWMH, MTM-K2, MTM-K4, optionally K8):
- price
- absolute error
- acceptance rate
- runtime
- IAT
- ESS

- [ ] **Step 3: Fill traceability fields in notes**

Add script path, parameter config, seed, and timestamp for each extracted row.


### Task 4: 5-Run Repeatability Experiments (Seeds 42-46)

**Files:**
- Create: `docs/superpowers/notes/2026-04-04-repeatability-results.csv`
- Update: `docs/superpowers/notes/2026-04-04-rigorous-run-log.md`

- [ ] **Step 1: Execute 5 independent runs with seeds 42~46**

Collect per-run metrics for RWMH and MTM-K4 at minimum.

- [ ] **Step 2: Aggregate by algorithm x metric**

Compute mean and standard deviation for price estimate and key diagnostics.

- [ ] **Step 3: Record repeatability conclusion criterion**

Document direction-consistency check (e.g., MTM-K4 IAT lower than RWMH across runs) and whether criterion is satisfied.


### Task 5: Convergence Diagnostics Evidence

**Files:**
- Update: `docs/superpowers/notes/2026-04-04-rigorous-run-log.md`

- [ ] **Step 1: Run advanced diagnostics script**

Run: `python src/mcmc_advanced.py`

- [ ] **Step 2: Extract Geweke values and apply threshold**

Apply pass threshold `|z| < 1.96` and record pass/fail per method.

- [ ] **Step 3: Optionally compute/report R-hat if available**

If R-hat is not directly available in code, explicitly record fallback to Geweke-only evidence per spec.

- [ ] **Step 4: Apply convergence acceptance rules**

Record pass/fail with thresholds:
- Geweke: `|z| < 1.96`
- R-hat (when computed): `R-hat < 1.01`


### Task 6: Regenerate and Validate Figures

**Files:**
- Generated/updated images: `comprehensive_analysis.png`, `speedup_curves.png` (and other produced files)
- Update: `docs/superpowers/notes/2026-04-04-rigorous-run-log.md`

- [ ] **Step 1: Run visualization script**

Run: `python src/visualization_optimized.py`

- [ ] **Step 2: Verify image files exist and are up-to-date**

Record file names and timestamps in run-log notes.

- [ ] **Step 3: Build figure-reference map for report update**

Map each report figure citation to an actual file.


### Task 7: Rewrite Report with New Evidence

**Files:**
- Modify: `本科毕业论文-研究报告.md`

- [ ] **Step 1: Update Section 2.3 target distribution mathematics**

Add explicit density expression for \(\ln S_T\) normal distribution and clarify sampling variable definition.

- [ ] **Step 1.5: Update Section 3.2 formulas and pseudocode consistency**

Revise 3.2 algorithm pseudocode and acceptance-probability expressions so that text exactly matches final code implementation for RWMH/MTM.

- [ ] **Step 2: Update tables 4-1, 4-2, 4-3 with latest values**

Include:
- updated core metrics from Task 3
- `价格均值±std` from Task 4 in Table 4-1

- [ ] **Step 3: Add robustness and diagnostics statements**

Update Sections 4.2, 4.6, 4.7, 5.2 with evidence-backed statements:
- MTM estimate near analytical solution (if supported)
- 5-run repeatability result
- convergence evidence threshold outcome
- serial implementation cost tradeoff

- [ ] **Step 3.5: Handle optional literature micro-expansion in 1.2**

Either:
- add 1-2 sentences in Section 1.2 on frontier limitations (e.g., 2025 MTM limitation and HMC context), or
- explicitly mark as “optional item intentionally skipped” in run-log with justification.

- [ ] **Step 4: Unify figure/table numbering and references**

Ensure all cited figures/tables exist and numbering is consistent.

- [ ] **Step 4.5: Remove duplicate/invalid figure references**

Delete duplicate citations and any reference that does not map to a real generated image file.

- [ ] **Step 5: Preserve existing mandatory formatting constraints**

Keep report without `#` character and maintain academic style.


### Task 8: Traceability Matrix and Final Verification

**Files:**
- Create: `docs/superpowers/notes/2026-04-04-traceability-matrix.md`
- Verify: `本科毕业论文-研究报告.md`

- [ ] **Step 1: Create section-to-evidence matrix**

For sections 2.3, 4.2, 4.3, 4.5, 4.6, 5.2 include:
- section paragraph
- table/figure id
- script source
- config
- seed
- timestamp

- [ ] **Step 2: Verify statistical acceptance criteria**

Check and record:
- Geweke threshold status
- MTM-K4 vs RWMH IAT directional consistency

- [ ] **Step 3: Verify report integrity constraints**

Check:
- no `#` character in report
- all three Chapter 4 tables populated
- all figure paths valid

- [ ] **Step 4: Execute failure-degrade order and stop condition check**

Validate execution followed spec order:
1. must-have: main experiment + table updates
2. secondary: 5-run repeatability
3. optional: R-hat
If must-have failed at any point, verify workflow stopped and reported (no fabricated data).


### Task 9: Handoff Summary

**Files:**
- Final outputs:
  - `本科毕业论文-研究报告.md`
  - `docs/superpowers/notes/2026-04-04-rigorous-run-log.md`
  - `docs/superpowers/notes/2026-04-04-main-experiment-results.csv`
  - `docs/superpowers/notes/2026-04-04-repeatability-results.csv`
  - `docs/superpowers/notes/2026-04-04-traceability-matrix.md`

- [ ] **Step 1: Report recommendation checklist completion status**

Mark 10/10 recommendation items with exact file/section locations.

- [ ] **Step 2: Summarize what changed and what evidence supports each claim**

Provide a concise defense-oriented summary for immediate user review.
