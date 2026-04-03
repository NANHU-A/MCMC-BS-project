# Remove Hash Symbols And Humanize Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `本科毕业论文-研究报告.md` so it contains zero `#` characters and reads more naturally while preserving academic rigor and factual fidelity.

**Architecture:** Perform a controlled single-file rewrite: first normalize heading presentation from Markdown-heading syntax to plain-text heading lines, then run expression-level polishing on paragraphs without changing numeric results, formulas, citations, or conclusion logic. Finish with strict verification (`#` count, structure check, fidelity check).

**Tech Stack:** Markdown editing, regex/content verification via grep, manual text QA.

---

### Task 1: Baseline Capture

**Files:**
- Read: `本科毕业论文-研究报告.md`
- Reference: `docs/superpowers/specs/2026-04-03-remove-hash-and-humanize-report-design.md`

- [ ] **Step 1: Snapshot key invariants before editing**

Record the following from current file:
- section order
- table count
- figure reference count
- formula block count
- references count

- [ ] **Step 2: Build protected-facts checklist**

Create a temporary checklist in working notes containing:
- all numeric result values in Chapter 4 tables
- all source path tags
- chapter titles and sequence


### Task 2: Remove All `#` Characters

**Files:**
- Modify: `本科毕业论文-研究报告.md`

- [ ] **Step 1: Replace Markdown heading syntax with plain text headings**

Examples:
- `# 标题` -> `标题`
- `## 第1章 绪论` -> `第1章 绪论`
- `### 1.1 研究背景与意义` -> `1.1 研究背景与意义`

- [ ] **Step 2: Remove any remaining literal `#` symbols**

Apply explicit edge-case handling:
- code block comment hash symbols (rewrite as plain text or remove code block if not needed)
- terms like `C#` -> `C Sharp`
- URL anchors containing `#` -> non-anchor URL or plain text citation form
- any literal hash in prose -> semantic replacement (e.g., “序号/编号”)

- [ ] **Step 3: Verify zero `#` count**

Run a search command and confirm there are no matches for `#`.


### Task 3: Humanize Writing While Preserving Rigor

**Files:**
- Modify: `本科毕业论文-研究报告.md`

- [ ] **Step 1: Smooth overly rigid/template phrasing**

Rewrite mechanical expressions into natural academic Chinese, keeping terminology accurate.

- [ ] **Step 2: Improve sentence rhythm and paragraph flow**

Split overlong sentences and improve transitions using evidence-first or conclusion-first style where appropriate.

Apply explicit style constraints:
- sentence length target: <=40 Chinese characters (or split long sentences)
- one main claim per paragraph
- prefer conclusion-first then evidence explanation
- keep source traceability wording intact

- [ ] **Step 3: Keep bilingual abstract academically natural**

Polish Chinese and English abstracts for readability without weakening precision.

- [ ] **Step 4: Preserve all protected facts**

Ensure no change to:
- numeric results
- formulas' mathematical meaning
- source path annotations
- final conclusions


### Task 4: Structural And Fidelity Verification

**Files:**
- Verify: `本科毕业论文-研究报告.md`

- [ ] **Step 1: Verify required structure still exists**

Check sections remain present in this order:
- title
- 中文摘要
- Abstract
- 第1章~第5章
- 参考文献
- 附录

- [ ] **Step 2: Verify quantitative content against baseline**

Compare with Task 1 baseline counts and require exact equality for:
- table count
- figure reference count
- formula count
- reference entry count

Also confirm these counts are not below project DoD minima.

- [ ] **Step 3: Verify zero `#` across full file**

Search the file and confirm count is zero.

- [ ] **Step 4: Final read-through for natural tone**

Confirm style is human and fluent but remains thesis-appropriate and evidence-driven.

- [ ] **Step 5: Protected-facts diff check**

Manually compare Chapter 4 numeric tables, source-path tags, and conclusion statements against Task 1 protected checklist; no factual drift allowed.


### Task 5: Handoff

**Files:**
- Final: `本科毕业论文-研究报告.md`

- [ ] **Step 1: Report what changed**

Summarize:
- heading format conversion
- language polishing scope
- verification outcomes

- [ ] **Step 2: Offer optional next actions**

Options:
- produce WPS-friendly version with manual page-break markers
- output a “final-print” copy without inline source tags
- generate答辩口语版提纲 from the revised report
