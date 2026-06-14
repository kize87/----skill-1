# Report Structure Rules

## 1. Experimental Purposes and Requirements

Place the lab requirements here in English. If the source is Chinese, translate it directly and preserve all concrete tasks, datasets, model names, parameter requirements, submission constraints, and expected outputs.

Write this section as:

- A short purpose paragraph explaining the learning goal.
- A numbered or compact requirement list that mirrors the assignment.

Do not invent extra tasks. If a requirement is ambiguous, state the most conservative interpretation in the report notes or ask the user before final generation.

## 2. Algorithms or Models Used

Rename this section only when another discipline clearly needs a better label, such as `Experimental Principles and Methods`, `Circuit Principles Used`, or `Chemical Reactions and Methods Used`.

Include:

- Core methods, algorithms, models, instruments, or theoretical principles used in the experiment.
- Important assumptions and limitations.
- Equations that explain the method or evaluation metric.
- A short explanation after each important formula.
- Why each method is suitable or unsuitable for the current dataset or task.
- Important hyperparameters and why they matter.
- Connections between the theory and the actual code implementation.

Use subsections like:

- `2.1 K-means Clustering`
- `2.2 DBSCAN`
- `2.3 Spectral Clustering`

Keep formulas readable. Important display formulas must become editable Word equations, centered, with equation numbers at the right margin. Inline formulas may remain inline only if they render cleanly without raw LaTeX markers and are not central to the method.

For machine-learning classification reports, do not stop at one-sentence descriptions. Explain the probabilistic meaning of logistic regression or softmax, how distance metrics and feature scaling affect KNN, the Naive Bayes independence assumption, the SVM margin objective and kernel effect, and why macro precision, recall, and F1-score may be more informative than accuracy.

## 3. Experiment Contents and Process

This is the main procedural and result section. Split by experiment, task, or code workflow.

Recommended hierarchy:

- `3.1 Data Loading and Preprocessing`
- `3.2 Model/Algorithm Experiment`
- `3.3 Parameter Comparison`
- `3.4 Result Visualization and Analysis`

For each subsection, include:

- Experimental content/introduction.
- Data collection, preprocessing, environment, and important parameters.
- Process steps derived from the code.
- Results and analysis, with figures or tables near the relevant explanation.
- Interpretation of why each result occurred, not only what the number was.
- Comparisons between methods when the experiment includes multiple methods.

When multiple experiments exist, write each one as a separate numbered subsection. Avoid dumping code unless the assignment explicitly requires code listing. Describe code logic and include only short snippets when necessary.

For normal reports, the body should be substantial. A machine-learning report with four algorithms should usually include several pages of method explanation, experiment process, result discussion, and conclusion. If the draft feels short, deepen it by adding theory-code linkage, parameter reasoning, metric interpretation, confusion-matrix analysis, error analysis, limitations, and possible improvements.

### Required visual coverage per subsection

The richness gate enforces a minimum visual / quantitative bar in every subsection. See `visualization-strategy.md` for the full list; the short version is:

- **3.1 Data Loading and Preprocessing** — class / target distribution chart, missing-value visualization, numeric-feature distribution panel, correlation heatmap when sensible, outlier plot for the features that motivated cleaning steps, and a three-line split summary table.
- **3.2 Model / Algorithm Experiment** — architecture or pipeline diagram, **pseudocode block per non-trivial method** (shaded code style), hyperparameter table, and a training-curve or learning-curve figure when the model is iterative. Include a core-code excerpt for at least one method.
- **3.3 Parameter Comparison** — parameter-sweep curves (one panel per parameter), a heatmap when sweeping two parameters jointly, and a stability / sensitivity boxplot when seeds were varied.
- **3.4 Result Visualization and Analysis** — confusion matrix per classifier, per-class precision / recall / F1 three-line table, overall-metric comparison bar chart, ROC or precision-recall curves when probabilities are available, feature-importance / coefficient / permutation chart, and an error-analysis figure that surfaces which classes or feature regions are most often misclassified.

Each figure or table needs 2–4 sentences of interpretation immediately after it. Tables use the three-line style (top rule, header-body separator, bottom rule; no inner verticals or extra horizontals). Pseudocode and core code excerpts use the shaded style described in `code-and-pseudocode.md`.

## 4. Discussion and Conclusions

Write a concise conclusion in a university student voice:

- Summarize what was implemented or observed.
- Compare the methods or experimental outcomes.
- Explain key reasons behind successes/failures.
- Mention limitations, possible improvements, and what was learned.

Avoid exaggerated claims. Do not use marketing language or unsupported performance statements.

Include at least one cross-method summary table (three-line style) restating the headline numbers, and ideally a trade-off chart (for example accuracy vs. training time, or accuracy vs. robustness). These visuals make the conclusion concrete; without them this section often shrinks into vague prose, which the richness gate flags.
