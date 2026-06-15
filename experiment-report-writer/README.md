# experiment-report-writer

A Claude Code skill that turns a school experiment template, the lab requirements, your code, and your data into a polished English experiment report — without rebuilding the cover page and without losing any of the school template's formatting.

It was built for Shenzhen University's machine-learning lab template, but the workflow generalises to any university lab template that has a fixed cover page and a four-section body (Purposes / Methods / Process / Conclusion).

---

## What it does

Given a working directory containing roughly:

```
.
├── 2026机器学习实验报告模板(1).docx       # SZU-style template
├── Task <N>.pdf                          # lab requirements
├── <data files>                          # csv / xlsx / images
└── <code>                                # .py / .ipynb
```

…the skill drives Claude through:

1. **Reading the requirements** (PDF / DOCX / DOC) without ever passing them as `document` content blocks — important for non-Claude API backends (GLM, GPT-via-proxy, OpenRouter routers, …) which reject that content type.
2. **Understanding the experiment** — code top-to-bottom, dataset shape, class balance, missingness — before writing anything.
3. **Planning** the report section-by-section: what figures, tables, formulas, pseudocode, core code each subsection should contain.
4. **Implementing**: producing the figures with a scientific-publication style (SciencePlots / IEEE), three-line tables, shaded code blocks, Office Math equations.
5. **QA gate** — three deterministic checks plus an optional richness subagent that can loop back into Implement up to three times until coverage is good.

The output is one `.docx` that opens cleanly in Word / WPS / LibreOffice and keeps the original cover page byte-for-byte.

---

## When to invoke

Trigger phrases that match the skill's `description`:

- "帮我写实验报告 / 编写本次实验报告 / 把代码和报告做完"
- "fill in the experiment report DOCX"
- "generate a report from this template + code + data"
- "verify the experiment report formatting"

The skill auto-scans the working directory before asking you anything, so dropping it into a folder and saying *"帮我用这个 skill 完成实验报告"* is enough.

---

## Workflow phases

```
1. Prepare      Convert legacy .doc → high-fidelity .docx through LibreOffice.
                Copy the master, never overwrite it.

2. Understand   Read the PDF requirements with read_pdf_text.py.
                Read the template structure with inspect_docx.py.
                Read the code top-to-bottom; probe the dataset shape.
                (Do NOT use the Read tool on .pdf / .docx — see below.)

3. Plan         Per-section list of figures, tables, formulas, pseudocode,
                core code excerpts. Cover every stage of the experiment.

4. Implement    Run code, produce figures, build the DOCX from the template
                copy via OOXML. Three-line tables, 1.27 cm first-line indent,
                shaded code blocks (EFEFEF, Consolas 9pt), Office Math.

5. QA loop      Three checkers + optional richness subagent.
                If verdict = needs_revision, apply high-priority fixes,
                rebuild, recheck. Cap at 3 iterations.
```

The full prompt contract that pins these constraints down for delegated subagents lives in `SKILL.md` → "Prompt Contract For Report Generation".

---

## Reading binary documents — the non-Claude-backend rule

**Never use the `Read` tool on `.pdf`, `.docx`, or `.doc`.**

The `Read` tool wraps binary documents into a `document` content block. Official Anthropic Claude models support that block (they parse the file natively). Most third-party Anthropic-compatible backends (GLM-5.1, OpenRouter relays, deepseek proxies, …) **reject it with HTTP 400**, which kills the session.

Use the scripted text-only path instead:

| File type | Use |
|---|---|
| `.pdf` | `python scripts/read_pdf_text.py file.pdf` |
| `.docx` | `python scripts/inspect_docx.py file.docx` |
| `.doc` (legacy) | Convert with `scripts/convert_doc_to_docx.sh` first |
| `.py`, `.ipynb`, `.md`, `.txt`, `.csv` | `Read` tool is fine |

`read_pdf_text.py` falls back through `pdftotext` → `pdfminer.six` → `pypdf`, so as long as one of those three is reachable on `pip` you get clean text on stdout.

---

## Layout

```
experiment-report-writer/
├── SKILL.md                          The skill itself (Claude reads this first).
├── README.md                         You are here.
├── references/                       Loaded into context as needed.
│   ├── report-structure.md           Section-by-section content rules.
│   ├── word-formatting.md            Typography, three-line tables, indent rules.
│   ├── visualization-strategy.md     Per-section visualization mandate +
│   │                                 SciencePlots / ProPlot stack.
│   ├── code-and-pseudocode.md        Shaded code-block style + caption rules.
│   ├── visual-review-prompt.md       Quick visual-coverage prompt.
│   └── richness-check-prompt.md      Verbatim subagent prompt for QA loop.
├── scripts/
│   ├── read_pdf_text.py              Binary-safe PDF → text extractor.
│   ├── inspect_docx.py               DOCX text + structure dump.
│   ├── prepare_master_template.sh    LibreOffice-driven .doc → .docx with
│   │                                 page-frame fidelity.
│   ├── convert_doc_to_docx.sh        Plain .doc → .docx converter.
│   ├── latex_to_docx_math.py         LaTeX fragment → Office Math DOCX.
│   ├── validate_report_docx.py       Section / LaTeX / three-line table /
│   │                                 first-line-indent checker.
│   ├── report_quality_harness.py     Equation / depth / cover-fidelity audit.
│   └── check_report_richness.py      Counts figures, tables, formulas, code
│                                     blocks; per-section coverage; exit 2 on
│                                     fail (used by the richness loop).
└── tests/                            Unit tests for every script (24 cases).
```

---

## Scripts reference

### `read_pdf_text.py` — read PDFs without `document` blocks

```bash
python scripts/read_pdf_text.py path/to/lab.pdf            # text on stdout
python scripts/read_pdf_text.py path/to/lab.pdf --output lab.txt
python scripts/read_pdf_text.py path/to/lab.pdf --json     # {path, text}
```

Use this **instead of** the `Read` tool whenever a PDF is involved. Falls back through `pdftotext` (Poppler), `pdfminer.six`, then `pypdf` / `PyPDF2`.

### `inspect_docx.py` — read DOCX text + structure

```bash
python scripts/inspect_docx.py path/to/template.docx
python scripts/inspect_docx.py path/to/template.docx --json
```

Returns paragraph / table / drawing / picture counts plus the full text. Use it to understand the template before editing it.

### `prepare_master_template.sh` — high-fidelity `.doc` → `.docx`

```bash
scripts/prepare_master_template.sh template.doc out_dir/
```

Wraps `soffice --convert-to docx` in headless mode with a private user-installation directory so the conversion is deterministic, and optionally renders a PDF preview so you can visually confirm the cover frame survived. Falls back to telling you to ask the user for a manually-saved `.docx` when LibreOffice is broken — *not* to `textutil`, which silently drops form borders.

### `latex_to_docx_math.py` — LaTeX → Office Math

```bash
python scripts/latex_to_docx_math.py "P(y=k|x) = \\frac{\\exp(w_k^\\top x)}{\\sum_j \\exp(w_j^\\top x)}" out.docx
```

Produces a one-paragraph DOCX containing an editable Word equation. Useful when you want to test a single formula round-trip before integrating it into the report.

### `validate_report_docx.py` — structural validator

```bash
python scripts/validate_report_docx.py 实验二_2024280331_辛彦泽.docx
```

Checks:

- The four required sections exist.
- No raw LaTeX delimiters (`$`, `\(`, `\[`, …) survived.
- Body paragraphs use first-line indentation (`w:firstLine` ≥ 720 twips).
- Every captioned data table is in three-line style (top rule, header–body separator, bottom rule; no inner verticals or extra horizontals).
- Plain-text formula leakage: hard error when no Word equation is present, warning when one already is (since `argmax` / `ℝ^d` / `‖w‖` in prose is fine alongside real Office Math).

Frame tables (cover, footer review box, layout-only outer tables) are skipped — only tables with a `Table N.` caption are checked.

Exit 0 = OK, 1 = errors. Warnings go to stderr.

### `report_quality_harness.py` — depth + fidelity audit

```bash
python scripts/report_quality_harness.py 实验二.docx \
    --require-szubox \
    --template 2026机器学习实验报告模板.docx \
    --min-figures 12 \
    --min-tables 4 \
    --require-visual-analysis
```

Checks:

- At least one editable Office Math equation is present.
- Body word count ≥ `--min-body-words` (default 900).
- Figure / table caption counts ≥ `--min-figures` / `--min-tables`.
- (Optional) Cover signature matches the template byte-for-byte — fails the report if your generator silently rebuilt the first page.
- (Optional) Visual-analysis vocabulary is dense enough (`distribution`, `confusion matrix`, `error analysis`, …).
- (Optional) Shenzhen University cover + footer anchors are intact (`--require-szubox`).

Pseudocode-style text (in shaded paragraphs) is excluded from the plain-formula check, so `exp(z_k)` inside `Algorithm 1` does not get flagged.

### `check_report_richness.py` — richness gate

```bash
python scripts/check_report_richness.py 实验二.docx
python scripts/check_report_richness.py 实验二.docx \
    --min-figures 10 --min-tables 4 --min-formulas 5
```

Counts figures, tables, formulas, pseudocode blocks, and code blocks; estimates per-section coverage by splitting on numbered headings (`3.1` / `3.2` / `3.3` / `3.4` / `4`) and matching keyword bundles for each section's mandate.

Exit codes:

- `0` — every threshold met (`verdict: pass`).
- `2` — at least one threshold failed (`verdict: needs_revision`); the JSON `failures` array tells you which.
- `1` — couldn't read the DOCX.

Output is JSON on stdout (or `--output file`); the richness-check subagent (see `references/richness-check-prompt.md`) takes that JSON plus the DOCX and returns a structured revision list.

Default thresholds suit a four-method ML report:

```
min_figures            8
min_tables             3
min_formulas           4
min_pseudocode_blocks  1
min_code_blocks        2
```

---

## QA loop

After the report draft is filled in, run the full gate:

```bash
python scripts/validate_report_docx.py     "$REPORT"
python scripts/report_quality_harness.py   "$REPORT" --require-szubox \
                                                     --min-figures 12 \
                                                     --min-tables 4 \
                                                     --require-visual-analysis
python scripts/check_report_richness.py    "$REPORT"
```

If `check_report_richness.py` exits 2, spawn the richness subagent with the prompt in `references/richness-check-prompt.md`, hand it the report path and the JSON output, and act on the returned `revision_list` (high priority first). Then rebuild and recheck. Cap the loop at three iterations — after three, deliver the best draft and report the remaining gaps to the user.

If LibreOffice is available, also do a visual render-check:

```bash
soffice --headless --convert-to pdf "$REPORT"
# inspect every page for cover damage, overflow, broken tables, blank gaps
```

When rendering is unavailable, say so in the delivery note instead of pretending the visual gate passed.

---

## Conventions enforced by the skill

| Element | Rule |
|---|---|
| Body font | Times New Roman, 10.5 pt / Chinese size 5 |
| Body paragraph indent | 1.27 cm first-line (720 twips); not on headings, captions, code, or table cells |
| Headings | Bold, numbered (`2.1`, `3.1.1`, …), kept with next |
| Tables | Three-line style: top 1.5 pt, header separator 0.75 pt, bottom 1.5 pt, no inner borders. Caption above. |
| Figures | Saved at 300 dpi, scientific style (SciencePlots `science` + `no-latex` when installed, manual rcParams fallback otherwise). Caption below. |
| Formulas | Office Math (`m:oMath` / `m:oMathPara`) for important formulas, centered, equation number `(1)`, `(2)` … at the right. No raw LaTeX delimiters in visible text. |
| Code blocks | Shaded EFEFEF, Consolas 9 pt, single line spacing, 240-twip side indent, no first-line indent. Caption `Algorithm N.` / `Code N.` above. |
| Cover page | Untouched. Generators that rebuild the cover are rejected by `--template` cover-signature comparison. |

---

## Tests

```bash
cd experiment-report-writer
python -m pytest tests/
```

Currently 24 tests across 5 files:

- `test_validate_report_docx.py` — three-line table accept/reject, indent accept/reject, raw LaTeX, missing section.
- `test_report_quality_harness.py` — depth, equations, cover-signature, visual-analysis vocabulary, formula warnings.
- `test_check_report_richness.py` — rich report passes, thin report fails, CLI exit code.
- `test_latex_to_docx_math.py` — LaTeX → Office Math round-trip.
- `test_script_contracts.py` — `prepare_master_template.sh` requires LibreOffice, the converter has no `textutil` fallback, SKILL.md mentions the right scripts and forbids `Read` on binary documents.

---

## Quick start

```bash
# 1. Drop the skill next to your experiment.
cd /path/to/your/experiment
git clone <this-repo>/experiment-report-writer .

# 2. Tell Claude what to do.
# In Claude Code:
#   "帮我用 ./experiment-report-writer 完成本次实验代码和报告"

# 3. Skill scans the directory, asks for missing student metadata only,
#    runs Understand → Plan → Implement → QA, and writes 实验X_<student>.docx.

# 4. Re-run any single QA check whenever you tweak the report:
python experiment-report-writer/scripts/check_report_richness.py 实验X.docx
```

---

## License

Personal-use skill; reuse and adapt freely.
