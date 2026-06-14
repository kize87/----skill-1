import importlib.util
import pathlib
import sys
import tempfile
import unittest
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_report_docx.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_report_docx", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_docx(path, body_xml):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""")
        zf.writestr("word/document.xml", body_xml)


def paragraph(text):
    return f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"


def indented_paragraph(text):
    return (
        "<w:p>"
        "<w:pPr><w:ind w:firstLine=\"720\"/></w:pPr>"
        f"<w:r><w:t>{text}</w:t></w:r>"
        "</w:p>"
    )


def three_line_table():
    """Two-row Word table with three-line borders only."""
    return (
        "<w:tbl>"
        "<w:tblPr>"
        "<w:tblBorders>"
        "<w:top w:val=\"single\" w:sz=\"12\" w:space=\"0\" w:color=\"auto\"/>"
        "<w:bottom w:val=\"single\" w:sz=\"12\" w:space=\"0\" w:color=\"auto\"/>"
        "<w:left w:val=\"nil\"/>"
        "<w:right w:val=\"nil\"/>"
        "<w:insideH w:val=\"nil\"/>"
        "<w:insideV w:val=\"nil\"/>"
        "</w:tblBorders>"
        "</w:tblPr>"
        "<w:tr>"
        "<w:tc>"
        "<w:tcPr>"
        "<w:tcBorders>"
        "<w:top w:val=\"single\" w:sz=\"12\" w:space=\"0\" w:color=\"auto\"/>"
        "<w:bottom w:val=\"single\" w:sz=\"6\" w:space=\"0\" w:color=\"auto\"/>"
        "<w:left w:val=\"nil\"/>"
        "<w:right w:val=\"nil\"/>"
        "<w:insideH w:val=\"nil\"/>"
        "<w:insideV w:val=\"nil\"/>"
        "</w:tcBorders>"
        "</w:tcPr>"
        "<w:p><w:r><w:t>Method</w:t></w:r></w:p>"
        "</w:tc>"
        "</w:tr>"
        "<w:tr>"
        "<w:tc>"
        "<w:tcPr>"
        "<w:tcBorders>"
        "<w:top w:val=\"nil\"/>"
        "<w:bottom w:val=\"single\" w:sz=\"12\" w:space=\"0\" w:color=\"auto\"/>"
        "<w:left w:val=\"nil\"/>"
        "<w:right w:val=\"nil\"/>"
        "<w:insideH w:val=\"nil\"/>"
        "<w:insideV w:val=\"nil\"/>"
        "</w:tcBorders>"
        "</w:tcPr>"
        "<w:p><w:r><w:t>K-means</w:t></w:r></w:p>"
        "</w:tc>"
        "</w:tr>"
        "</w:tbl>"
    )


def grid_table():
    """Default Table-Grid style table (every border visible)."""
    return (
        "<w:tbl>"
        "<w:tblPr>"
        "<w:tblBorders>"
        "<w:top w:val=\"single\" w:sz=\"4\"/>"
        "<w:bottom w:val=\"single\" w:sz=\"4\"/>"
        "<w:left w:val=\"single\" w:sz=\"4\"/>"
        "<w:right w:val=\"single\" w:sz=\"4\"/>"
        "<w:insideH w:val=\"single\" w:sz=\"4\"/>"
        "<w:insideV w:val=\"single\" w:sz=\"4\"/>"
        "</w:tblBorders>"
        "</w:tblPr>"
        "<w:tr>"
        "<w:tc><w:p><w:r><w:t>Method</w:t></w:r></w:p></w:tc>"
        "</w:tr>"
        "<w:tr>"
        "<w:tc><w:p><w:r><w:t>K-means</w:t></w:r></w:p></w:tc>"
        "</w:tr>"
        "</w:tbl>"
    )


def long_body_paragraphs(n, indented=True):
    text = (
        "This paragraph explains an aspect of the experiment in enough detail that "
        "the validator treats it as a body paragraph candidate for indentation."
    )
    para = indented_paragraph if indented else paragraph
    return [para(text) for _ in range(n)]


def document_xml(*paragraphs):
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    %s
  </w:body>
</w:document>""" % "\n".join(paragraphs)


class ValidateReportDocxTest(unittest.TestCase):
    def test_valid_report_passes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docx = pathlib.Path(tmp) / "valid.docx"
            make_docx(
                docx,
                document_xml(
                    paragraph("Experimental Purposes and Requirements"),
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                    paragraph("4. Discussion and Conclusions"),
                    paragraph("Figure 1. Clustering result"),
                ),
            )

            result = module.validate_docx(docx)

        self.assertTrue(result.ok)
        self.assertEqual(result.errors, [])

    def test_missing_required_section_fails(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docx = pathlib.Path(tmp) / "missing.docx"
            make_docx(
                docx,
                document_xml(
                    paragraph("Experimental Purposes and Requirements"),
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                ),
            )

            result = module.validate_docx(docx)

        self.assertFalse(result.ok)
        self.assertIn("Missing section: Discussion and Conclusions", result.errors)

    def test_raw_latex_markers_fail(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docx = pathlib.Path(tmp) / "latex.docx"
            make_docx(
                docx,
                document_xml(
                    paragraph("Experimental Purposes and Requirements"),
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                    paragraph("4. Discussion and Conclusions"),
                    paragraph("The objective is $J = \\sum_i x_i$."),
                ),
            )

            result = module.validate_docx(docx)

        self.assertFalse(result.ok)
        self.assertIn("Raw LaTeX/math marker found: $", result.errors)

    def test_three_line_table_passes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docx = pathlib.Path(tmp) / "tlt.docx"
            make_docx(
                docx,
                document_xml(
                    paragraph("Experimental Purposes and Requirements"),
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                    paragraph("4. Discussion and Conclusions"),
                    paragraph("Table 1. Method comparison"),
                    three_line_table(),
                ),
            )

            result = module.validate_docx(docx)

        # No three-line-table errors should appear.
        for err in result.errors:
            self.assertNotIn("three-line", err)

    def test_grid_table_fails_three_line_check(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docx = pathlib.Path(tmp) / "grid.docx"
            make_docx(
                docx,
                document_xml(
                    paragraph("Experimental Purposes and Requirements"),
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                    paragraph("4. Discussion and Conclusions"),
                    paragraph("Table 1. Method comparison"),
                    grid_table(),
                ),
            )

            result = module.validate_docx(docx)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("three-line" in err for err in result.errors),
            result.errors,
        )

    def test_missing_indent_fails(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docx = pathlib.Path(tmp) / "noindent.docx"
            make_docx(
                docx,
                document_xml(
                    paragraph("Experimental Purposes and Requirements"),
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                    paragraph("4. Discussion and Conclusions"),
                    *long_body_paragraphs(8, indented=False),
                ),
            )

            result = module.validate_docx(docx)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("first-line indent" in err for err in result.errors),
            result.errors,
        )

    def test_indented_body_passes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docx = pathlib.Path(tmp) / "indented.docx"
            make_docx(
                docx,
                document_xml(
                    paragraph("Experimental Purposes and Requirements"),
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                    paragraph("4. Discussion and Conclusions"),
                    *long_body_paragraphs(8, indented=True),
                ),
            )

            result = module.validate_docx(docx)

        for err in result.errors:
            self.assertNotIn("first-line indent", err)


if __name__ == "__main__":
    unittest.main()
