---
name: experiment-report-writer
description: Use when the user asks to write, fill, generate, polish, or verify a university experiment report from Word templates, lab requirements, code, datasets, figures, formulas, or reference reports, especially for English reports based on Shenzhen University-style lab report templates.
---

# Experiment Report Writer

## Purpose

Generate polished English experiment reports from lab requirements, code, data, and a Word template while preserving the original report cover and form layout. Treat the template as the source of truth for page structure; copy and locally fill it instead of recreating the whole document.

## Required Skill Order

1. Load a Word document skill first (`docx` or `documents`) before reading or editing `.doc`/`.docx` files.
2. Use this skill to drive report-specific discovery, planning, writing, formatting, and QA.
3. Use `references/report-structure.md` for section content rules.
4. Use `references/word-formatting.md` before editing tables, paragraphs, formulas, figures, or the final DOCX.
5. Use `references/visualization-strategy.md` when deciding whether to create a figure, table, metric plot, or profiling artifact.
6. Use `references/code-and-pseudocode.md` before inserting any pseudocode or core code excerpt.
7. Use `references/richness-check-prompt.md` when entering the post-draft richness QA loop.

## Inputs To Discover

Scan the working directory before asking the user questions. Identify:

- Template files: names containing `template`, `模板`, `实验报告模板`, `.doc`, or `.docx`.
- Completed reference reports: names containing student IDs, names, `实验`, or reports with substantial body text.
- Lab requirements: `.docx`, `.pdf`, `.md`, `.txt`, assignment docs, or task descriptions.
- Code and data: Python notebooks/scripts, source files, datasets, generated images, logs, CSV/XLSX outputs.

Ignore Word lock files beginning with `.~`.

## Workflow

The workflow has five phases: **Prepare**, **Understand**, **Plan**, **Implement**, **QA loop**. Do not skip Understand or Plan to save time — when the report turns out shallow, the cause is almost always a phase that was rushed here.

### 1. Prepare the template safely

- Convert legacy `.doc` templates with LibreOffice using `scripts/prepare_master_template.sh`. Do not use `textutil` for final template preparation when form borders or page frames matter.
- Do not overwrite the original template.
- Inspect the template structure before editing; preserve cover-page fields and layout.
- If the template is a school form, start from a copied template document and edit that copy. Do not create a new blank document that imitates the cover page.
- If LibreOffice conversion still loses the outer frame, stop and ask for a manually saved high-fidelity `.docx` master from Word/WPS.

### 2. Understand the experiment deeply (do not start coding yet)

This phase is required even when the user is in a hurry. The goal is to internalize the experiment so the rest of the work is informed, not improvised.

- Read the lab requirements in full. If they are in Chinese, translate them and preserve every concrete task, dataset, model, parameter, submission constraint, and expected output.
- Read the existing code top-to-bottom — not just the entry script. Map out the data path, preprocessing transforms, model definitions, training loop, evaluation, and any plotting helpers.
- Inspect the data shape: number of samples, feature columns and dtypes, class balance, missing-value pattern, value ranges. Run small probes (`df.head()`, `df.describe()`, `df.info()`, value counts) when needed.
- Read any existing reference report or completed sample to learn the tone, depth, and figure style the user expects.
- Write a short internal "experiment brief" noting: what the assignment really asks for, what the code already does, what the data looks like, and where the gaps are. Keep this brief in your context for the next phase; do not paste it into the final report verbatim.

### 3. Plan the report (visualizations, formulas, code, structure)

Before writing or generating anything, draft a per-section plan so the implementation phase has a concrete checklist.

For every subsection 3.1 → 4, list:

- The figures and tables it will contain. Use the per-section mandate in `references/visualization-strategy.md` as the minimum bar, then add more whenever the data supports it. Cover **every stage** — data preprocessing distribution / missingness / correlation, model architecture, training curves, parameter sweeps, confusion matrices, per-class metrics, error analysis, method comparison.
- The formulas that need to be editable Word equations and which ones are central enough to deserve a full display equation with a number.
- The pseudocode and core-code excerpts to include, one per non-trivial method, rendered with the shaded style from `references/code-and-pseudocode.md`.
- The narrative claim each visual is meant to support — every figure must answer a question; if you cannot state the question, drop the figure.

Cross-check the plan against the data: if a planned figure cannot be produced because the data does not support it, replace it with the closest informative alternative rather than dropping it silently.

### 4. Implement: code, visuals, and report draft

- Run code as needed to produce missing figures, metrics, and result tables. Reuse existing generated outputs only when they clearly match the current code.
- Use the scientific-style plot stack from `references/visualization-strategy.md`. Auto-install `SciencePlots` and `proplot` on first use; fall back to the manual style block in that reference if installation is blocked.
- Generate visualizations for **every section in the plan**, including data preprocessing analyses (distributions, missingness, correlations, outlier plots) and not only end-of-pipeline result charts. Prefer a slightly oversized visual set; pruning happens in the QA loop, not here.
- Draft the report body in English, four sections, numbered subsections (`2.1`, `2.2`, `3.1`, `3.1.1`, …).
- Write in a college lab-report tone: clear, technically accurate, not over-polished or marketing-like. Prefer depth over speed — substantial method explanations, parameter reasoning, result interpretation, and limitations. Avoid one-paragraph algorithm summaries.
- Keep formulas as LaTeX fragments while drafting. Convert them into editable Word equations before finalizing the DOCX.
- Copy the LibreOffice-prepared high-fidelity master `.docx` to a new output `.docx` and fill the report body inside the corresponding report area. Keep the cover page unchanged except for fields the user explicitly wants filled.
- Body text uses Times New Roman, Chinese size 5 / 10.5 pt, with 1.27 cm first-line indent on body paragraphs. Headings and subheadings are bold. See `references/word-formatting.md` for the full typography and indentation rules.
- Tables use the three-line style described in `references/word-formatting.md`: visible top rule, header / body separator, bottom rule; no inner vertical or extra horizontal lines. Captions go above the table.
- Pseudocode and core code excerpts use the shaded code-block style described in `references/code-and-pseudocode.md`. Captions (`Algorithm 1.`, `Code 1.`) go above the block. Do not paste raw LaTeX `algorithm` environments or whole-file dumps.
- Insert important formulas as Office Math (`m:oMath` / `m:oMathPara`). Do not leave plain text such as `exp(w_k^T x+b_k)` for important formulas, and do not leave `$`, `\(`, `\)`, raw braces, or uncompiled equation syntax in visible text. Center display formulas; right-align equation numbers.
- Figure captions go below figures. Use real Word tables for tabular data.
- Do not use `python-docx`, `docx-js`, or Pandoc to rebuild the whole report when a template is provided. Use deterministic OOXML edits against the copied master, or use those libraries only for helper fragments that are merged into the copied master.

### 5. QA loop with richness gate

Run these checks in order. The richness gate may loop back into phases 3–4 up to **three times** before delivering.

1. `scripts/validate_report_docx.py` — required sections, raw LaTeX leakage, three-line table borders, body indentation, formula style.
2. `scripts/report_quality_harness.py` — editable equations, minimum report depth, optional cover/template signature preservation. For Shenzhen University templates use `--require-szubox`; when a converted master `.docx` is available, pass it with `--template`; for multi-model ML reports set `--min-figures` and `--min-tables` to the expected counts; set `--require-visual-analysis` when the report should include dense comparative analysis.
3. `scripts/check_report_richness.py` — counts figures, tables, formulas, pseudocode blocks, code blocks, and per-section coverage. Default thresholds assume a normal four-method ML report; override via flags when the experiment is smaller or larger. Exit code 2 means the richness bar is not met.
4. **Richness subagent** — spawn a subagent with the prompt in `references/richness-check-prompt.md`, passing the report path and the JSON from `check_report_richness.py`. The subagent returns a verdict (`pass` / `needs_revision`) plus a prioritized revision list.
5. If the verdict is `needs_revision`:
   - Apply the high-priority revisions: add the missing figures / tables / pseudocode / code / formulas, fix style issues.
   - Regenerate the affected sections of the DOCX.
   - Rerun steps 1–4. Cap at three revision iterations; after three, deliver the best draft and report the remaining gaps to the user explicitly instead of looping further.
6. If LibreOffice/Word rendering is available, render pages and visually inspect every page for cover damage, content overflow, broken tables, figure placement, large blank gaps, and strange spacing. If rendering is unavailable, state that only structural QA was completed.

## Helper Scripts

- `scripts/inspect_docx.py`: Extract text and basic OOXML structure from a `.docx`.
- `scripts/validate_report_docx.py`: Check required sections, common report formatting hazards, three-line table borders, and body first-line indentation.
- `scripts/report_quality_harness.py`: Check editable equations, minimum report depth, and optional cover/template signature preservation.
- `scripts/check_report_richness.py`: Count figures, tables, formulas, pseudocode and code blocks; estimate per-section coverage; emit JSON for the richness subagent.
- `scripts/prepare_master_template.sh`: Convert a legacy `.doc` template through LibreOffice and optionally render preview artifacts.
- `scripts/latex_to_docx_math.py`: Convert LaTeX formula fragments to a DOCX containing editable Word math.
- `scripts/convert_doc_to_docx.sh`: Convert `.doc` to `.docx` with available local tools.

## Prompt Contract For Report Generation

When delegating or starting a report generation task, include these constraints verbatim:

```text
Use the provided Word template as the base document. Prepare a high-fidelity master DOCX with LibreOffice when the source is .doc. Copy that master and fill the copy; do not rebuild the cover page or simulate the template in a new document. Preserve the first page, outer report frame, and report form layout.

Before writing any code or report text, complete an Understand phase (read requirements, read all code, inspect the data shape, read any reference report) and a Plan phase (per-section list of figures, tables, formulas, pseudocode, and core code excerpts). Skipping these phases produces shallow reports.

Write a deep English experiment report. Spend time reading the requirements, code, data outputs, and figures. The report should include detailed algorithm principles, parameter choices, formulas, experiment process, result interpretation, method comparison, limitations, and possible improvements.

Generate visualizations for every section, including data preprocessing (distribution, missingness, correlation, outlier visualization), model methods (architecture diagram + pseudocode), parameter comparison (sweep curves, heatmaps), and results (confusion matrices, per-class metrics, comparison charts, error analysis). Prefer a slightly oversized visual set first and prune only redundant ones afterward.

Use a scientific-style plotting stack: SciencePlots (Nature / IEEE styles) or ProPlot when available; auto-install on first use. Fall back to the manual matplotlib serif / inward-tick / no-top-spine style block from references/visualization-strategy.md if installation is blocked. Save figures at 300 dpi minimum.

All tables in the report use the three-line table style: visible top rule, header–body separator, bottom rule; no inner vertical or inner horizontal borders. Body paragraphs use Times New Roman 10.5 pt with 1.27 cm first-line indentation; figure / table / code captions and headings are not indented.

Pseudocode and core code excerpts must use the shaded code-block style from references/code-and-pseudocode.md: light gray fill (EFEFEF), Consolas 9 pt monospace, single line spacing, captions on top using `Algorithm 1.` / `Code 1.`. Plain-style code in the body or screenshot code is not acceptable.

Important formulas must be editable Word equations, not plain text or screenshots. Formula-like text such as exp(w_k^T x+b_k), argmax_y, sum_i, product_i, and ||x-y|| must be converted into Office Math equations when used as important formulas. Draft formulas first in LaTeX if that makes the reasoning clearer, then convert them to Word equations before finalizing. Do not ship the LaTeX delimiters or visible symbol artifacts.

After the draft is filled in, run the QA gate: validate_report_docx.py, report_quality_harness.py, and check_report_richness.py. Then spawn the richness-check subagent (see references/richness-check-prompt.md). If the subagent returns "needs_revision", apply the high-priority revisions and rerun the gate. Cap the loop at three richness iterations; after three, deliver the best draft and explicitly list any remaining gaps. For Shenzhen University templates, include --require-szubox. Render the final report with LibreOffice and inspect page images; if visual render QA is unavailable, say so explicitly.
```

## Stop Conditions

Ask the user only when a required preference cannot be discovered from files, such as the exact experiment date, student metadata, or whether to install missing runtime dependencies that the auto-install policy is not allowed to handle. Do not ask where files are until after scanning the working directory. Do not skip the Understand or Plan phase to "save time" — they are the cheapest insurance against a shallow report.
