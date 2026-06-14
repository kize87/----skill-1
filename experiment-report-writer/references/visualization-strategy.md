# Visualization Strategy

## Principle

Prefer visual evidence whenever it clarifies data, model behavior, or experimental results. A strong experiment report should not only state metrics; it should show the dataset, preprocessing effects, model behavior, errors, comparisons, and interpretation. Every section that touches data or models must contribute at least one figure or table — text-only sections are a smell, not a target.

## Per-Section Visualization Mandate

Treat the items below as the minimum bar. Generate them whenever the data and code support them, then add more when the experiment is richer than the baseline list.

### Section 3.1 — Data Loading and Preprocessing

- Class / target distribution bar chart.
- Missing-value heatmap or missingness bar chart.
- Numeric feature distribution panel (KDE / histogram, grouped by target when classification).
- Categorical frequency plots for the most informative columns.
- Outlier visualization (boxplot or violin) for the features that motivate cleaning steps.
- Train / validation / test split summary table (three-line style).
- Pre- vs. post-preprocessing comparison plot when scaling or transformation matters (for example, the same feature before and after standardization).

### Section 3.2 — Algorithm / Model Experiments

- Method / architecture diagram or flowchart.
- Pseudocode block for each non-trivial algorithm (see `code-and-pseudocode.md`).
- Hyperparameter table summarizing the search grid actually used.
- Training-curve plot (loss / accuracy vs. epoch) when the algorithm is iterative.
- Decision boundary or cluster assignment plot when the input is 2-D / can be projected.

### Section 3.3 — Parameter Comparison

- Parameter sweep curves (metric vs. hyperparameter), one panel per parameter.
- Heatmap when sweeping two hyperparameters jointly.
- Sensitivity / stability box plot if results were repeated across seeds.

### Section 3.4 — Result Visualization and Analysis

- Confusion matrix per classifier (or aggregated subplot grid).
- Per-class precision / recall / F1 three-line table.
- Overall metric comparison bar chart with error bars when seeds were varied.
- ROC and / or precision-recall curves when probabilities are available.
- Feature importance, coefficient magnitude, permutation importance, or SHAP-style explanation chart when the model supports it.
- Error analysis chart that surfaces which classes or feature regions are most often misclassified.
- Side-by-side qualitative example panel (correct vs. wrong predictions) when the data is image / text / signal.

### Section 4 — Discussion and Conclusions

- Method-comparison summary table (three-line) restating the headline numbers.
- Trade-off chart (for example, accuracy vs. training time) when several methods compete.
- Limitations radar / spider chart or weakness summary table when the report contrasts multiple approaches.

## Scientific-Style Plot Stack

Default to a publication-quality look. Prefer libraries that already encode the conventions reviewers expect (serif fonts, ticks pointing inward, minor ticks visible, no top/right spines).

Preferred libraries, in priority order:

1. **SciencePlots** — the Nature / IEEE / Science styles for matplotlib. Activate with `plt.style.use(['science', 'ieee'])` or `['science', 'nature']`.
2. **ProPlot** — clean default theme, easy multi-panel grids, polished color cycles.
3. **seaborn** with `sns.set_theme(context='paper', style='whitegrid', palette='colorblind')` as a robust fallback.
4. **plotly** with the `simple_white` template only when an interactive HTML companion is useful — never as the only artifact, because the Word report needs static images.

### Auto-install policy

If the preferred library is missing, install it on first use rather than silently dropping back to a plain matplotlib style. Use the same Python interpreter that runs the experiment code:

```python
import importlib, subprocess, sys
for pkg in ("scienceplots", "proplot"):
    if importlib.util.find_spec(pkg) is None:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg])
```

If the install fails (offline, locked environment, or pip permissions), fall back to the manual style block below and record the fallback in the visual-review note so the user can decide whether to install later.

### Manual fallback style (when SciencePlots is unavailable)

```python
import matplotlib.pyplot as plt
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "legend.frameon": False,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})
```

## Optional Open-Source Accelerators

Use these when installed or when dependency installation is acceptable:

- `ydata-profiling` / pandas-profiling — fast EDA pass that surfaces distributions, correlations, missing values.
- `Sweetviz` — strong target analysis and train/test comparison.
- `AutoViz` — one-line auto visualization for tabular datasets.
- `DataPrep.EDA` — quick correlation / missingness summaries.
- `missingno` — focused missing-value matrices and dendrograms.
- `yellowbrick` — sklearn-aware visualizers (residuals, ROC, classification reports).

Do not paste entire HTML reports into the Word report. Use them to decide which figures matter, then export or recreate the chosen figures with matplotlib / seaborn / plotly using the scientific-style stack above.

## Figure Quality Rules

- Every figure must answer a concrete question stated in the surrounding text.
- Every figure needs 2–4 sentences of interpretation immediately after it. Empty figure dumps are rejected.
- Save at 300 dpi minimum, vector format (PDF / SVG) when the rendering pipeline can embed it, otherwise high-quality PNG.
- Use a consistent color palette across the whole report. Pick one palette family (for example, `colorblind` or a manually-selected set of 6–8 colors) and reuse it.
- Multi-panel figures are preferred for confusion matrices and per-model metrics — the comparison must be visible at a glance.
- Captions are descriptive, not generic: `Figure 5. Confusion matrices for the four classifiers on the held-out test split (rows: true labels, columns: predictions).` not `Figure 5. Confusion matrices.`
- Avoid screenshots of profiling tools when a clean custom plot can be generated from the same data.

## Visual Coverage Gate

Before final delivery, write a short visual-review note containing:

- Every figure included and the specific claim it supports.
- Missing figures from the per-section mandate above and why they were skipped (not enough data, not applicable, deferred).
- Whether tables could replace or complement any figure.
- Sections where text dominates and a chart, heatmap, or table would communicate the same point with less prose.
- A revision plan if visual coverage is weak.

This note is the input that the richness-check subagent and `scripts/check_report_richness.py` consume during the QA loop.
