# Richness Check Subagent

## When to spawn

After the report draft is filled into the template and the per-section content is in place, but **before** declaring the report finished, spawn a richness-check subagent. The subagent's job is to decide whether the report has enough figures, tables, formulas, pseudocode, and per-section depth to count as a "rich" experiment report, or whether another revision pass is needed.

This subagent is part of the QA loop described in `SKILL.md` step 6. It runs after `scripts/check_report_richness.py` has produced the static-count JSON and reviews the report alongside that JSON.

## Subagent prompt (copy verbatim into the spawn call)

```text
You are reviewing an experiment report DOCX for richness — whether the report has enough quantitative content (figures, tables, formulas, pseudocode, code excerpts, per-section coverage) to feel like a serious lab report rather than a thin essay.

Inputs:
- Report file: <path-to-report.docx>
- Static richness JSON from scripts/check_report_richness.py: <path-to-richness.json>
- Visualization mandate (per-section minimums): references/visualization-strategy.md
- Code style rules: references/code-and-pseudocode.md
- Report structure: references/report-structure.md

Steps:
1. Read the static richness JSON. Note the counts for figures, tables, formulas, pseudocode blocks, code blocks, and per-section coverage flags. Treat any failed counts as starting candidates for the revision list, but do not stop there.
2. Read the report DOCX text and confirm or override the static counts. The static checker is conservative — it can miss content that uses unusual captions or off-pattern wording. When you override a flag, say which paragraph or section made you change your mind.
3. For each report section, judge whether the visual / quantitative coverage matches the mandate in visualization-strategy.md. Specifically:
   - 3.1 Data preprocessing: distribution / missing-value / correlation / outlier visuals.
   - 3.2 Model methods: architecture diagram, pseudocode, hyperparameter table.
   - 3.3 Parameter comparison: parameter-sweep curves or heatmaps.
   - 3.4 Results: confusion matrix, per-class metric table, comparison bar chart, error analysis.
   - 4 Discussion: cross-method summary table or trade-off chart.
4. Check that pseudocode and core code excerpts use the shaded code-block style (light gray fill, monospaced font, caption above). Plain-text code in body style is a failure.
5. Check that important formulas are editable Word equations and that every formula has a sentence-level explanation nearby.
6. Decide a verdict:
   - "pass" — every per-section mandate is met, total figure / table / formula counts are at or above the thresholds, and code/pseudocode style is correct.
   - "needs_revision" — at least one mandate fails or any style rule is broken.

Return ONLY the JSON object below, with no surrounding prose:

{
  "verdict": "pass" | "needs_revision",
  "counts": {
    "figures": <int>,
    "tables": <int>,
    "formulas": <int>,
    "pseudocode_blocks": <int>,
    "code_blocks": <int>
  },
  "section_coverage": {
    "3.1_preprocessing": "ok" | "weak" | "missing",
    "3.2_methods": "ok" | "weak" | "missing",
    "3.3_parameters": "ok" | "weak" | "missing",
    "3.4_results": "ok" | "weak" | "missing",
    "4_discussion": "ok" | "weak" | "missing"
  },
  "style_issues": [
    "<short string per issue, e.g. 'Algorithm 2 caption present but block is body-styled, not shaded.'>"
  ],
  "revision_list": [
    {
      "priority": "high" | "medium" | "low",
      "section": "<e.g. '3.4_results'>",
      "action": "<concrete imperative — 'Add a confusion matrix subplot grid for the four classifiers.'>"
    }
  ],
  "notes": "<one or two sentences summarizing the overall state.>"
}

If verdict is "pass", revision_list may be empty. If verdict is "needs_revision", revision_list MUST contain at least one item; sort high priority first.

Do not include markdown fences, do not narrate, do not return anything except the JSON object.
```

## How the calling skill consumes the response

- If `verdict == "pass"`: continue to final QA scripts and delivery.
- If `verdict == "needs_revision"`: feed `revision_list` back into the report-writing loop, applying high-priority items first. Generate the missing figures / tables / pseudocode / code blocks, fix the style issues, regenerate the DOCX, then rerun the static richness check and re-spawn the subagent.
- The skill caps the loop at three richness iterations per the policy in `SKILL.md`. After three iterations without "pass", deliver the best draft and report the remaining gaps to the user instead of looping forever.
