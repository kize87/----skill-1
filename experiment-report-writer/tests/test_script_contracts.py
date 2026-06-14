import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ScriptContractsTest(unittest.TestCase):
    def test_prepare_master_template_requires_libreoffice(self):
        text = (ROOT / "scripts" / "prepare_master_template.sh").read_text()

        self.assertIn("LibreOffice is required for high-fidelity template preparation", text)
        self.assertIn("--convert-to docx", text)
        self.assertIn("--convert-to pdf", text)
        self.assertIn("-env:UserInstallation=", text)
        self.assertIn("provide a Word/WPS-saved .docx master", text)

    def test_converter_has_no_fallback_mode(self):
        text = (ROOT / "scripts" / "convert_doc_to_docx.sh").read_text()

        self.assertIn("--require-libreoffice", text)
        self.assertIn("refusing textutil fallback", text)
        self.assertIn("provide a Word/WPS-saved .docx master", text)

    def test_skill_mentions_formula_and_visual_review_workflows(self):
        skill = (ROOT / "SKILL.md").read_text()

        self.assertIn("latex_to_docx_math.py", skill)
        self.assertIn("visualization-strategy.md", skill)
        # Richness QA loop with subagent replaced the older "AI-style reviewer"
        # pass; we still want the SKILL.md to advertise an automated visual
        # / quantitative review step before delivery.
        self.assertIn("check_report_richness.py", skill)
        self.assertIn("richness-check-prompt.md", skill)

    def test_visualization_references_exist(self):
        self.assertTrue((ROOT / "references" / "visualization-strategy.md").exists())
        self.assertTrue((ROOT / "references" / "visual-review-prompt.md").exists())
        self.assertTrue((ROOT / "references" / "code-and-pseudocode.md").exists())
        self.assertTrue((ROOT / "references" / "richness-check-prompt.md").exists())


if __name__ == "__main__":
    unittest.main()
