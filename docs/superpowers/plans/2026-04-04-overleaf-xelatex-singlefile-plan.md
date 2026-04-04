# Overleaf XeLaTeX Single-File Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a new single-file XeLaTeX document `main_xelatex_rigorous.tex` from the latest thesis markdown, with controlled layout targeting 15-20 pages when exported to WPS PDF.

**Architecture:** Convert markdown to LaTeX using Pandoc as a base layer, then produce a manually curated one-file XeLaTeX wrapper that includes stable section mapping, bibliography handling, font fallback presets, figure/table style normalization, and page-control parameters. Validate compile-readiness and record page-control tuning strategy without altering core research content.

**Tech Stack:** Pandoc, XeLaTeX-compatible LaTeX packages (`xeCJK`, `geometry`, `setspace`, `graphicx`, `booktabs`, `longtable`, `caption`, `hyperref`), Markdown source.

---

### Task 1: Source and Baseline Preparation

**Files:**
- Read: `本科毕业论文-研究报告.md`
- Read: `docs/superpowers/specs/2026-04-04-overleaf-xelatex-singlefile-design.md`
- Read: `overleaf_main_xelatex.txt`
- Read: `overleaf_xelatex_code.txt`

- [ ] **Step 1: Confirm latest markdown source exists and is selected**

Verify `本科毕业论文-研究报告.md` is the only source for export content.

- [ ] **Step 2: Capture baseline export assumptions**

Record expected image files and relative paths used in markdown.

- [ ] **Step 3: Check pandoc availability**

Run `pandoc --version` and confirm conversion tool is available.


### Task 2: Generate Raw LaTeX Body from Markdown

**Files:**
- Create (temporary): `docs/superpowers/notes/2026-04-04-pandoc-body.tex`

- [ ] **Step 1: Run pandoc conversion for body text**

Convert markdown to LaTeX body using Pandoc.

- [ ] **Step 2: Verify conversion preserves formulas/tables/figures**

Spot-check body for:
- math blocks
- table syntax
- `\includegraphics` sections

- [ ] **Step 3: Keep body file as trace artifact**

Save the temporary body under `docs/superpowers/notes/` for reproducibility.


### Task 3: Build Single-File XeLaTeX Main Document

**Files:**
- Create: `main_xelatex_rigorous.tex`

- [ ] **Step 1: Add document preamble and layout packages**

Include:
- `\documentclass[12pt,a4paper]{article}`
- `geometry` margin ~2.5cm
- `setspace` line spacing around 1.3
- tables/figures packages
- hyperlink package

- [ ] **Step 2: Add XeLaTeX font presets with fallback comments**

Provide two manual presets:
- default Fandol
- optional Noto CJK (comment-switch)

- [ ] **Step 3: Embed full body content directly in single file**

Do NOT use `\input{...}` for body; final file must be standalone.

- [ ] **Step 4: Enforce section ordering from spec**

Ensure sequence:
title -> CN abstract -> CN keywords -> EN abstract -> EN keywords -> TOC -> body -> references -> appendix.

- [ ] **Step 5: Normalize figure/table captions and spacing**

Set consistent caption style and table row spacing (`\arraystretch`) for readability.


### Task 4: References and Citation Consistency

**Files:**
- Modify: `main_xelatex_rigorous.tex`

- [ ] **Step 1: Preserve numbered references in continuous order**

Use stable numbered bibliography section compatible with current `[n]` style.

- [ ] **Step 2: Validate citation-number set consistency**

Ensure in-text cited numbers and bibliography item numbers align.

- [ ] **Step 3: Record any numbering fixes if needed**

If renumbering occurs, add a short note in final summary.


### Task 5: Page-Range Control Configuration

**Files:**
- Modify: `main_xelatex_rigorous.tex`

- [ ] **Step 1: Apply initial page-control parameters**

Set default:
- line spacing ~1.30
- image width ~0.82\textwidth
- sensible page breaks before major blocks

- [ ] **Step 2: Encode tuning order in comments**

Document strict order:
1) image width, 2) line spacing, 3) page breaks.

- [ ] **Step 3: Prevent content-loss tuning**

Do not remove substantive paragraphs to force page count.


### Task 6: Compile-Readiness Verification

**Files:**
- Verify: `main_xelatex_rigorous.tex`

- [ ] **Step 1: Run at least one real XeLaTeX compile**

Use local XeLaTeX if available; otherwise use Overleaf XeLaTeX compile and record outcome.

- [ ] **Step 2: Confirm no fatal syntax issues**

Ensure LaTeX structure is complete and balanced.

- [ ] **Step 2.5: Fix-and-recompile loop when first compile fails**

If first compile has fatal errors, fix the identified issues and run compile again until at least one successful non-fatal compile is obtained.

- [ ] **Step 3: Verify image references resolve by relative path assumption**

Check that figure filenames used in LaTeX exist in workspace root.

- [ ] **Step 3.5: Handle missing images per spec**

If any image file is missing, keep the `\includegraphics` line and add an inline comment noting the missing filename.


### Task 6.5: Page-Tuning Stop Rule

**Files:**
- Verify/Modify: `main_xelatex_rigorous.tex`

- [ ] **Step 1: Apply page tuning in strict order**

Tune only in this order:
1) image width, 2) line spacing, 3) page breaks.

- [ ] **Step 2: Enforce maximum two tuning rounds**

After two rounds, stop tuning and prioritize readability.

- [ ] **Step 3: Record out-of-range note if still outside 15-20**

If page count is still outside target, document this explicitly in delivery summary.


### Task 7: Delivery Summary

**Files:**
- Final: `main_xelatex_rigorous.tex`

- [ ] **Step 1: Summarize generated file and usage**

Provide short instructions for Overleaf paste-and-compile.

- [ ] **Step 2: Provide page-control knobs for WPS target**

Give exact parameters user can tweak to stay in 15-20 pages.
