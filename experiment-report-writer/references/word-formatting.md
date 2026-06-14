# Word Formatting Rules

## Template Preservation

- Treat the template as the source of truth.
- Copy the template and edit the copy.
- Preserve the cover page unless the user explicitly asks to fill or change cover fields.
- Keep all report body content inside the original report body area.
- Avoid rebuilding the whole document from scratch because this often destroys school template layout.
- Do not recreate the school cover with ordinary paragraphs, spaces, or a blank DOCX. This loses the original form border/page-frame behavior in Word/WPS.
- For legacy `.doc` templates, prepare a high-fidelity master `.docx` with LibreOffice. Avoid `textutil` for final template preparation because it may drop old Word/WPS form borders, page frames, and compatibility layout.
- Use a copy of the LibreOffice-prepared master as the final document base. Insert or replace body content inside that copy.
- Compare the generated report against a converted template with `scripts/report_quality_harness.py --template` when possible.
- If LibreOffice conversion aborts on macOS due to app quarantine/signing, do not fall back to `textutil` for final output. Ask the user to fix LibreOffice permissions/quarantine or provide a manually saved `.docx` master from Word/WPS.
- If the rendered master already lacks the outer report frame, stop and ask for a manually saved `.docx` master from Word/WPS before generating the report.

## Typography

- Body text: Times New Roman, 10.5 pt / Chinese size 5.
- Headings and subheadings: bold.
- Use numbered headings such as `2.1`, `2.2`, `3.1`, `3.1.1`.
- Keep spacing compact and consistent. Remove strange large spaces and empty paragraphs.

## Paragraph indentation

Body paragraphs use first-line indentation of **1.27cm (720 twentieths of a point)**, written as `<w:ind w:firstLine="720"/>` in OOXML. This is the IEEE / ACM convention and reads cleanly in mixed Chinese-English templates.

Apply indentation to:

- Plain narrative paragraphs in sections 1–4.
- The first paragraph after a heading (do not skip the indent there; it makes the heading-to-body relationship clearer in printed reports).

Do not indent:

- Headings and subheading lines.
- Figure captions, table captions, code/pseudocode captions.
- The body of code/pseudocode blocks (use the dedicated code style instead).
- Display equations and equation-number lines.
- The first line inside a table cell.

When you generate paragraphs through OOXML, set `w:ind` on the paragraph properties; do not simulate indentation with leading spaces or tab characters.

## Formulas

- Important formulas must be drafted as LaTeX fragments first, then converted into editable Word equations (`m:oMath` / `m:oMathPara`), not screenshots and not plain text.
- Plain strings such as `exp(w_k^T x+b_k)`, `argmax_y`, `sum_i`, `product_i`, and `||x-y||` are not acceptable for important formulas.
- Visible underscores, carets, raw braces, slash fractions, and LaTeX delimiters mean the formula conversion failed.
- Use `scripts/latex_to_docx_math.py` for isolated formula conversion checks. When inserting formulas into the final report, preserve the resulting Office Math XML rather than copying the visible text.
- Do not leave visible raw LaTeX markers such as `$`, `\(`, `\)`, `\[`, `\]`, or unmatched braces.
- Center important display formulas.
- Put equation numbers at the far right, for example `(1)`, `(2)`.
- Inline formulas are acceptable only when they render cleanly as normal Word equation text.

## Figures

- Insert visualization outputs near the discussion that refers to them.
- Use a clear figure caption below the image, for example `Figure 1. Scatter plots of the five datasets`.
- Keep each figure and its caption together when possible.
- Avoid oversized images that force large blank areas or overflow outside margins.

## Tables

Use real Word tables (`w:tbl`), never plain-text tables made with spaces or tabs. Spreadsheet-derived tables that round-trip through Word's "paste as table" are also acceptable.

### Three-line table style (default)

Academic experiment reports in this template use the **three-line table** convention from scientific publishing. Only horizontal borders are visible; all vertical borders and inner horizontal borders are removed. The three retained borders are:

1. **Top border** — above the header row, 1.5 pt single line.
2. **Header–body separator** — below the header row, 0.75 pt single line.
3. **Bottom border** — below the last data row, 1.5 pt single line.

In OOXML this means each cell sets `<w:tcBorders>` with:

- `top` and `bottom` set to `nil` for body cells (the row-level top/bottom only applies on the first/last rows).
- `left`, `right`, `insideH`, `insideV` set to `nil` everywhere.
- The header row's bottom border set to `single` 0.75 pt.
- The first data row's top border `nil` (the header bottom is the visible separator).
- The last data row's bottom border set to `single` 1.5 pt.
- The first row's top border set to `single` 1.5 pt.

Avoid the default Word "Table Grid" style — its inner gridlines violate the three-line rule. If your generation pipeline starts from `Table Grid`, override the borders explicitly per cell rather than relying on a named style.

### Other table rules

- Put table captions **above** the table, for example `Table 1. Dataset descriptions`. Captions are not first-line indented.
- Set table width, column widths, padding, and wrapping explicitly when generating OOXML.
- Header row text is bold and horizontally centered. Body cell text is left-aligned for strings, right-aligned or decimal-aligned for numbers.
- Add modest cell padding (about 80 twips top/bottom) so text does not touch the rules.
- Check that table text is not clipped or pinned to borders.
- Avoid merged cells unless the data really requires them; the three-line layout assumes a regular grid.

## Final QA Checklist

- Cover page formatting unchanged.
- Required four report sections present.
- Body content is English.
- Headings are numbered and bold.
- Body font is consistent and body paragraphs use 1.27 cm first-line indentation.
- No raw LaTeX syntax visible.
- Editable Word equation objects are present when the report contains important formulas.
- Figures have lower captions.
- Tables have upper captions and use three-line table borders (no inner verticals, no inner horizontals between data rows).
- Pseudocode and core code blocks render with the shaded code style described in `code-and-pseudocode.md`.
- No abnormal large blanks.
- Final `.docx` opens successfully.
- LibreOffice/Word-rendered preview confirms that the first page and outer report frame are still visible.
