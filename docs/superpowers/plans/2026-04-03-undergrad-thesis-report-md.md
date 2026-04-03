# Undergraduate Thesis Report Markdown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create one complete thesis-style Markdown report for the `master` branch project content, suitable for a mathematics and statistics undergraduate graduation thesis and expected to export to a 12-16 page WPS PDF.

**Architecture:** Keep implementation to a single final deliverable file (`本科毕业论文-研究报告.md`) plus optional in-file placeholders for figures/tables. Build content by mapping existing `master` code and documented results into a standard thesis narrative: problem-method-experiment-conclusion. Enforce academic style, traceability, and measurable acceptance criteria from the approved spec.

**Tech Stack:** Markdown, existing repository Python source (`src/*.py`), existing README materials, WPS/PDF export workflow.

---

### Task 1: Source-of-Truth Extraction

**Files:**
- Create: `docs/superpowers/notes/2026-04-03-undergrad-thesis-source-notes.md`
- Read: `README.md`
- Read: `README2.md`
- Read: `src/mcmc_option_pricing.py`
- Read: `src/mcmc_optimized.py`
- Read: `src/mcmc_advanced.py`
- Read: `src/visualization_optimized.py`
- Reference spec: `docs/superpowers/specs/2026-04-03-undergrad-thesis-md-design.md`

- [ ] **Step 1: Extract thesis-relevant facts from source files and persist notes**

Create and save `docs/superpowers/notes/2026-04-03-undergrad-thesis-source-notes.md` with a structured table containing:
- Conceptual facts (models, algorithms, metrics)
- Implementation facts (class/function names and purpose)
- Experimental facts (reported numbers and conditions)

- [ ] **Step 2: Apply conflict-resolution rule**

When README narratives conflict with source logic, prioritize `src/*.py` and mark any mismatch explicitly for Chapter 4 discussion.

- [ ] **Step 3: Build citation map**

For each planned chapter subsection, define at least one source path used as evidence.

- [ ] **Step 4: Verify completeness against DoD inputs**

Check that extracted facts can support:
- Bilingual abstract
- Chapters 1-5
- >=8 formulas
- >=3 tables
- >=3 figure references
- >=8 references


### Task 2: Thesis Skeleton Draft (Single File)

**Files:**
- Create: `本科毕业论文-研究报告.md`

- [ ] **Step 1: Create full chapter scaffold in final file**

Add headings for:
- Title
- 中文摘要、中文关键词
- Abstract、Keywords
- 第1章至第5章
- 参考文献
- 附录

- [ ] **Step 2: Insert writing constraints block (temporary)**

At top (temporary), add checklist comments for DoD targets; remove before final polish.

- [ ] **Step 3: Add placeholder anchors for tables/figures/formulas**

Add visible markers like “表4-1”、“图4-1” so later sections fill them consistently.

- [ ] **Step 4: Ensure heading depth is <=3**

Use only `#`, `##`, `###` to stabilize WPS pagination.


### Task 3: Write Chapters 1-2 (Background + Theory)

**Files:**
- Modify: `本科毕业论文-研究报告.md`

- [ ] **Step 1: Write Chapter 1 (绪论) in academic style**

Include:
- 研究背景与意义
- 国内外研究现状（MCMC/MTM/期权定价）
- 研究问题与本文贡献

- [ ] **Step 2: Write Chapter 2 (理论基础)**

Include formulas for:
- Black-Scholes d1/d2 and call price
- Monte Carlo estimator
- MH acceptance probability
- MTM weighted selection and acceptance form (high-level)
- ACF/IAT/ESS definitions

- [ ] **Step 3: Expand formula set to meet DoD (>=8 total)**

Add additional necessary expressions (as appropriate):
- geometric Brownian motion terminal distribution
- discounted payoff definition
- sample mean/variance estimators used in experiments
- speedup ratio definition

- [ ] **Step 4: Ensure Chapter 1-2 visualization/table presence**

Add at least one table or figure reference in each of Chapter 1 and Chapter 2.

- [ ] **Step 5: Add chapter mini-conclusions**

End each chapter with a short paragraph linking to subsequent chapter.

- [ ] **Step 6: Language quality pass**

Remove tutorial expressions and colloquial language. Keep thesis-style formal wording.


### Task 4: Write Chapters 3-4 (Method + Experiments)

**Files:**
- Modify: `本科毕业论文-研究报告.md`

- [ ] **Step 1: Write Chapter 3 with code-path traceability**

For each major method block, cite concrete file/function names from `src/`.

- [ ] **Step 2: Add algorithm pseudocode blocks**

Provide concise pseudocode for:
- RWMH sampling
- MTM sampling
- Experiment evaluation workflow

- [ ] **Step 3: Write Chapter 4 experimental setup**

State parameter settings, sampling size, burn-in policy, and metrics.

- [ ] **Step 4: Write Chapter 4 results + analysis**

Must include:
- >=3 tables (e.g., method comparison, speedup vs K, metric summary)
- >=3 figure references (existing repo plots or placeholders with source labels)
- Explanation of statistical efficiency vs wall-clock efficiency trade-off

- [ ] **Step 5: Add explicit provenance tags for key numbers**

At first numeric mention, annotate source path/config/seed context in text.

- [ ] **Step 6: Ensure Chapter 3-4 visualization/table presence**

Add at least one table or figure reference in each of Chapter 3 and Chapter 4.


### Task 5: Write Chapter 5 + References + Appendix

**Files:**
- Modify: `本科毕业论文-研究报告.md`

- [ ] **Step 1: Write Chapter 5 conclusion and outlook**

Include main findings, limitations, and feasible future work.

- [ ] **Step 2: Add non-placeholder references**

Provide >=8 entries in GB/T 7714-like format, including key MCMC/MTM/Black-Scholes sources.

- [ ] **Step 3: Add reproducibility appendix**

Include:
- branch (`master`)
- key scripts and commands
- major parameters and random seed
- mismatch-resolution rule summary
- key function explanations (module -> function -> role in pipeline)

- [ ] **Step 4: Remove temporary drafting markers**

- [ ] **Step 5: Ensure Chapter 5 visualization/table presence**

Add at least one table or figure reference in Chapter 5 (e.g., findings summary table).

Delete any temporary TODO/check comments used during drafting.


### Task 6: Quality Gate Against DoD

**Files:**
- Verify: `本科毕业论文-研究报告.md`
- Verify: `docs/superpowers/specs/2026-04-03-undergrad-thesis-md-design.md`

- [ ] **Step 1: Hard-count structural requirements**

Confirm file contains all required sections and chapter completeness.

- [ ] **Step 2: Count mandatory elements**

Confirm:
- formulas >=8
- tables >=3
- figure references >=3
- references >=8
- each core chapter includes at least one table or one figure reference

- [ ] **Step 3: Balance check (theory vs experiments ~5:5)**

Confirm Chapter 2 (theory) and Chapter 4 (experiments) have comparable depth/length and neither is significantly underdeveloped.

- [ ] **Step 4: Style and consistency review**

Confirm unified thesis language and no beginner-guide tone.

- [ ] **Step 5: Page-length target check (heuristic)**

Estimate WPS PDF likely within 12-16 pages (hard minimum >=10). If under target, expand Chapter 2/4 rigor; if over target, compress redundancy without deleting required elements.


### Task 7: Handoff

**Files:**
- Final deliverable: `本科毕业论文-研究报告.md`

- [ ] **Step 1: Provide completion summary to user**

List what was included and where.

- [ ] **Step 2: Offer optional next steps**

Options:
- generate figure files and replace placeholders
- convert to school template sections
- prepare defense PPT speaking notes
