import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_report_richness.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_report_richness", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def make_docx(path, body_xml):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            (
                "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
                "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
                "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
                "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
                "<Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>"
                "</Types>"
            ),
        )
        zf.writestr("word/document.xml", body_xml)


def para(text):
    return f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"


def shaded_code_para(text):
    return (
        "<w:p>"
        "<w:pPr>"
        "<w:shd w:val=\"clear\" w:color=\"auto\" w:fill=\"EFEFEF\"/>"
        "</w:pPr>"
        "<w:r>"
        "<w:rPr><w:rFonts w:ascii=\"Consolas\" w:hAnsi=\"Consolas\"/></w:rPr>"
        f"<w:t xml:space=\"preserve\">{text}</w:t>"
        "</w:r>"
        "</w:p>"
    )


def math_para():
    return (
        f"<w:p><m:oMathPara xmlns:m=\"{M_NS}\"><m:oMath><m:r><m:t>x</m:t></m:r></m:oMath></m:oMathPara></w:p>"
    )


def document(*paragraphs):
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        f"<w:document xmlns:w=\"{W_NS}\" xmlns:m=\"{M_NS}\"><w:body>"
        + "".join(paragraphs)
        + "</w:body></w:document>"
    )


def rich_report_paragraphs():
    """Build a paragraph list that should clear the default thresholds."""
    paragraphs = [
        para("1. Experimental Purposes and Requirements"),
        para("2. Algorithms or Models Used"),
        # Section 3.1 — preprocessing keywords across multiple bundles.
        para("3.1 Data Loading and Preprocessing"),
        para(
            "We inspected the missingness pattern, plotted feature distributions, "
            "and computed the Pearson correlation matrix. Outlier detection used boxplots."
        ),
        para("Figure 1. Class distribution"),
        para("Figure 2. Missing-value heatmap"),
        para("Figure 3. Numeric distributions"),
        para("Table 1. Train/test split summary"),
        # Section 3.2 — methods + pseudocode + hyperparameter table.
        para("3.2 Model and Algorithm Experiment"),
        para(
            "We document the architecture diagram, list the hyperparameter grid, "
            "and trace the training curve. The pseudocode below summarizes the algorithm."
        ),
        para("Algorithm 1. K-means with k-means++ initialization"),
        shaded_code_para("for epoch in range(num_epochs):"),
        shaded_code_para("    update_centroids(X, z)"),
        para("Code 1. Core training loop"),
        shaded_code_para("model.fit(X_train, y_train)"),
        shaded_code_para("preds = model.predict(X_test)"),
        para("Code 2. Evaluation snippet"),
        shaded_code_para("acc = (preds == y_test).mean()"),
        shaded_code_para("print(classification_report(y_test, preds))"),
        para("Figure 4. Architecture diagram"),
        para("Figure 5. Training curves"),
        para("Table 2. Hyperparameter grid"),
        # Section 3.3 — sweep + heatmap + sensitivity.
        para("3.3 Parameter Comparison"),
        para(
            "We swept k vs. accuracy, drew a heatmap over (k, eps), and report a "
            "sensitivity boxplot across seeds."
        ),
        para("Figure 6. Parameter sweep curves"),
        # Section 3.4 — confusion + per-class metrics + ROC + error analysis.
        para("3.4 Result Visualization and Analysis"),
        para(
            "Confusion matrix per classifier, per-class precision recall f1 scores, "
            "ROC curves, and an error analysis surface where misclassifications cluster."
        ),
        para("Figure 7. Confusion matrices"),
        para("Figure 8. ROC curves"),
        para("Table 3. Per-class precision recall F1"),
        # Section 4 — comparison + limitation + future work.
        para("4. Discussion and Conclusions"),
        para(
            "We compare the four methods, list their limitations, and propose future "
            "work and improvements."
        ),
        # Formulas
        math_para(),
        math_para(),
        math_para(),
        math_para(),
    ]
    return paragraphs


class CheckReportRichnessTest(unittest.TestCase):
    def test_rich_report_passes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docx = pathlib.Path(tmp) / "rich.docx"
            make_docx(docx, document(*rich_report_paragraphs()))

            result = module.check_report(docx, module.DEFAULT_THRESHOLDS)

        self.assertTrue(result.passed, result.failures)
        self.assertGreaterEqual(result.counts["figures"], 8)
        self.assertGreaterEqual(result.counts["tables"], 3)
        self.assertGreaterEqual(result.counts["formulas"], 4)
        self.assertGreaterEqual(result.counts["pseudocode_blocks"], 1)
        self.assertGreaterEqual(result.counts["code_blocks"], 1)
        for status in result.section_coverage.values():
            self.assertNotEqual(status, "missing")

    def test_thin_report_fails(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docx = pathlib.Path(tmp) / "thin.docx"
            make_docx(
                docx,
                document(
                    para("1. Experimental Purposes and Requirements"),
                    para("2. Algorithms or Models Used"),
                    para("3. Experiment Contents and Process"),
                    para("Figure 1. Only one"),
                    para("4. Discussion and Conclusions"),
                ),
            )

            result = module.check_report(docx, module.DEFAULT_THRESHOLDS)

        self.assertFalse(result.passed)
        self.assertTrue(any("figures" in f for f in result.failures))
        self.assertTrue(any("formulas" in f for f in result.failures))

    def test_cli_exit_code_2_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx = pathlib.Path(tmp) / "thin.docx"
            make_docx(
                docx,
                document(
                    para("1. Experimental Purposes and Requirements"),
                    para("2. Algorithms or Models Used"),
                    para("3. Experiment Contents and Process"),
                    para("4. Discussion and Conclusions"),
                ),
            )

            proc = subprocess.run(
                [sys.executable, str(SCRIPT), str(docx)],
                capture_output=True,
                text=True,
            )

        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["verdict"], "needs_revision")
        self.assertIn("counts", payload)


if __name__ == "__main__":
    unittest.main()
