# Pseudocode and Core Code Blocks

Important algorithms in an experiment report should appear twice:

1. As **pseudocode**, expressing the logic without language details so a reader from any background can follow it.
2. As a **core code excerpt**, showing the 20–40 most informative lines of the actual implementation.

Both are rendered as Word paragraphs with a shaded background — never as inline `<w:t>` runs in normal body style, never as screenshots, and never as long verbatim dumps of the whole script.

## Visual style

Both pseudocode and core code blocks share the same OOXML style:

- Font: Consolas 9 pt (fall back to `Courier New` 9 pt when Consolas is unavailable).
- Paragraph background shading: `<w:shd w:val="clear" w:color="auto" w:fill="EFEFEF"/>` (very light gray, prints cleanly in black-and-white).
- Single line spacing (`<w:spacing w:line="240" w:lineRule="auto"/>`) and zero space before / after between lines so the block looks like a continuous box.
- Left and right paragraph indent of 240 twips (about 0.42 cm) so the box is visually inset from the body text.
- No first-line indent — set `<w:ind w:firstLine="0"/>` explicitly to override the body's 1.27 cm indent.
- Optional thin border on all four sides with `single` 0.25 pt in `BFBFBF` if the printer used will reproduce shading poorly; otherwise rely on the fill alone.

A minimal OOXML paragraph for one code line looks like:

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="CodeBlock"/>
    <w:shd w:val="clear" w:color="auto" w:fill="EFEFEF"/>
    <w:ind w:left="240" w:right="240" w:firstLine="0"/>
    <w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>
  </w:pPr>
  <w:r>
    <w:rPr>
      <w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>
      <w:sz w:val="18"/>
    </w:rPr>
    <w:t xml:space="preserve">    for epoch in range(num_epochs):</w:t>
  </w:r>
</w:p>
```

If the report-generation pipeline already defines a `CodeBlock` paragraph style, reuse it instead of inlining the formatting on every paragraph.

## Captions

- Captions appear **above** the block, mirroring the table-caption rule.
- Use `Algorithm 1.`, `Algorithm 2.`, … for pseudocode.
- Use `Code 1.`, `Code 2.`, … for actual implementation excerpts.
- Caption text is bold and not first-line indented.
- Example: `Algorithm 1. K-means with k-means++ initialization.` / `Code 1. Core training loop for the softmax classifier.`

## Pseudocode rules

- Use plain English imperative steps, optionally numbered.
- Math expressions inside pseudocode may use Unicode (`←`, `∑`, `√`, `≤`) or LaTeX-fragment syntax that will be rendered as Office Math when the line is mostly math; mixing inline `← argmax_k` is acceptable as long as no raw `$` or `\(` markers remain.
- Use indentation (4 spaces is fine inside the shaded paragraph) to show control flow.
- Keep pseudocode short — 8 to 25 lines per algorithm. If it grows beyond that, split into sub-algorithms.

Example pseudocode block (rendered with the shaded style above):

```
Algorithm 1. K-means clustering.
Input:  data X ∈ ℝ^{n×d}, cluster count k, max iterations T
Output: cluster assignments z ∈ {1..k}^n, centroids μ
1.  Initialize centroids μ_1..μ_k with k-means++.
2.  for t = 1..T do
3.     for i = 1..n do
4.        z_i ← argmin_j ||x_i − μ_j||²
5.     end for
6.     for j = 1..k do
7.        μ_j ← mean({x_i : z_i = j})
8.     end for
9.     if assignments unchanged then break
10. end for
```

## Core code excerpts

- Show only the 20–40 lines that carry the experiment's idea. Cut imports, argument parsing, logging, and boilerplate.
- Preserve indentation exactly. Do not collapse multi-line statements onto one line.
- Add a short comment line above the excerpt if the surrounding prose does not already explain what the snippet does.
- Use real Python / R / MATLAB / etc. syntax — do not paraphrase. Reviewers should be able to map the excerpt to the source file.
- Keep one excerpt per concept. Three short excerpts (data prep, model fit, evaluation) are usually clearer than one long block.

## When not to use code blocks

- Trivially short statements that the prose already covers ("we used `sklearn.cluster.KMeans` with `n_clusters=4`") do not need a code block.
- Full file dumps belong in an appendix or supplementary material, not the body. The richness checker treats more than ~80 consecutive code lines in the body as a smell.

## Failure modes the QA gate looks for

- Code or pseudocode set in body style with no shading — fails the richness check.
- Captions placed below the block — fails the caption-position rule.
- Algorithm caption present but no shaded paragraphs after it — caption without a body block.
- Pseudocode pasted as raw LaTeX (`\begin{algorithm}` … `\end{algorithm}`) — must be rewritten into the shaded Word paragraphs.
