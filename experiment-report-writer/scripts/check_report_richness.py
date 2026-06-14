#!/usr/bin/env python3
"""Static richness checker for experiment report DOCX files.

Counts figures, tables, formulas, pseudocode blocks, and code blocks, then
estimates per-section coverage by splitting the report on numbered headings.
Writes a JSON summary to stdout (or --output) and exits 0 when every threshold
is met, 2 when any threshold fails, and 1 on inspection errors.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


WORD_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}

# Sections we expect; keyed by the leading numeric heading we see in the body.
SECTION_KEYS = (
    ("3.1", "3.1_preprocessing"),
    ("3.2", "3.2_methods"),
    ("3.3", "3.3_parameters"),
    ("3.4", "3.4_results"),
    ("4", "4_discussion"),
)

# Per-section keyword bundles. The static checker treats a section as "ok"
# when at least two distinct bundles appear; "weak" with one; "missing" with
# none. The richness subagent gets the final say.
SECTION_KEYWORDS: dict[str, tuple[tuple[str, ...], ...]] = {
    "3.1_preprocessing": (
        ("missing", "missingness", "null"),
        ("distribution", "histogram", "kde", "density"),
        ("correlation", "heatmap", "pearson", "spearman"),
        ("outlier", "boxplot", "violin"),
        ("scaling", "standardiz", "normaliz"),
    ),
    "3.2_methods": (
        ("architecture", "diagram", "flowchart", "pipeline"),
        ("algorithm", "pseudocode"),
        ("hyperparameter", "grid", "search space", "parameter table"),
        ("training curve", "loss curve", "learning curve"),
    ),
    "3.3_parameters": (
        ("sweep", "vs.", "varying", "ablation"),
        ("heatmap", "grid"),
        ("sensitivity", "stability", "seed"),
    ),
    "3.4_results": (
        ("confusion matrix", "confusion-matrix"),
        ("precision", "recall", "f1", "f1-score", "f1 score"),
        ("roc", "auc", "precision-recall"),
        ("feature importance", "permutation", "shap", "coefficient"),
        ("error analysis", "misclassif"),
    ),
    "4_discussion": (
        ("compare", "comparison", "trade-off", "tradeoff"),
        ("limitation", "weakness"),
        ("improvement", "future work"),
    ),
}

# Default thresholds. The CLI lets callers override these per report.
DEFAULT_THRESHOLDS = {
    "min_figures": 8,
    "min_tables": 3,
    "min_formulas": 4,
    "min_pseudocode_blocks": 1,
    "min_code_blocks": 2,
}


@dataclasses.dataclass
class RichnessResult:
    counts: dict[str, int]
    section_coverage: dict[str, str]
    failures: list[str]

    @property
    def passed(self) -> bool:
        return not self.failures


def read_document_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        return zf.read("word/document.xml").decode("utf-8")


def paragraph_text(para: ET.Element) -> str:
    return "".join(node.text or "" for node in para.findall(".//w:t", WORD_NS))


def has_shaded_fill(para: ET.Element) -> bool:
    """Return True when the paragraph carries a non-trivial shading fill.

    The skill's convention is `EFEFEF`, but we accept anything that is not
    `auto`, `none`, or pure white so light styling drift does not break the
    check.
    """
    shd = para.find("./w:pPr/w:shd", WORD_NS)
    if shd is None:
        return False
    fill = shd.attrib.get(f"{{{WORD_NS['w']}}}fill", "").lower()
    if not fill or fill in {"auto", "none", "ffffff"}:
        return False
    return True


def is_monospace_paragraph(para: ET.Element) -> bool:
    """Return True when at least one run uses a monospaced font."""
    monospace_fonts = {"consolas", "courier new", "menlo", "monaco", "source code pro", "dejavu sans mono"}
    for rfonts in para.findall(".//w:rFonts", WORD_NS):
        for attr in ("ascii", "hAnsi", "cs", "eastAsia"):
            value = rfonts.attrib.get(f"{{{WORD_NS['w']}}}{attr}", "").strip().lower()
            if value in monospace_fonts:
                return True
    style = para.find("./w:pPr/w:pStyle", WORD_NS)
    if style is not None:
        val = style.attrib.get(f"{{{WORD_NS['w']}}}val", "").lower()
        if val in {"codeblock", "code", "sourcecode", "pseudocode", "algorithm"}:
            return True
    return False


def count_shaded_code_blocks(root: ET.Element) -> tuple[int, int]:
    """Count contiguous runs of shaded monospace paragraphs.

    Returns (pseudocode_blocks, code_blocks). The two are distinguished by
    looking back for a caption paragraph starting with `Algorithm` vs. `Code`.
    """
    paragraphs = root.findall(".//w:p", WORD_NS)
    blocks: list[tuple[int, int]] = []  # (start_idx, end_idx) inclusive
    in_block = False
    start = 0
    for idx, para in enumerate(paragraphs):
        styled = (has_shaded_fill(para) or is_monospace_paragraph(para)) and paragraph_text(para).strip() != ""
        if styled and not in_block:
            in_block = True
            start = idx
        elif not styled and in_block:
            blocks.append((start, idx - 1))
            in_block = False
    if in_block:
        blocks.append((start, len(paragraphs) - 1))

    pseudocode_blocks = 0
    code_blocks = 0
    for start_idx, _ in blocks:
        # Look back up to 3 paragraphs for a caption.
        kind = "code"
        for back in range(1, 4):
            if start_idx - back < 0:
                break
            prev_text = paragraph_text(paragraphs[start_idx - back]).strip()
            if not prev_text:
                continue
            if re.match(r"^Algorithm\s+\d+", prev_text, flags=re.IGNORECASE):
                kind = "pseudocode"
                break
            if re.match(r"^Code\s+\d+", prev_text, flags=re.IGNORECASE):
                kind = "code"
                break
            # Stop scanning as soon as we hit a non-empty, non-caption paragraph.
            break
        if kind == "pseudocode":
            pseudocode_blocks += 1
        else:
            code_blocks += 1
    return pseudocode_blocks, code_blocks


def count_formulas(xml: str) -> int:
    return xml.count("<m:oMathPara") + xml.count("<m:oMath ") + xml.count("<m:oMath>")


def split_sections(paragraphs: list[ET.Element]) -> dict[str, str]:
    """Bucket paragraph text into the section keys we track.

    Headings start with a number and a dot, e.g. `3.1 Data Loading...`. Anything
    before the first matched heading goes into a "_pre" bucket we drop later.
    """
    buckets: dict[str, list[str]] = {key: [] for _, key in SECTION_KEYS}
    current = None
    for para in paragraphs:
        text = paragraph_text(para).strip()
        if not text:
            continue
        new_key = None
        for prefix, key in SECTION_KEYS:
            if re.match(rf"^{re.escape(prefix)}(?:\.\d+)*\b", text):
                new_key = key
                break
        if new_key is not None:
            current = new_key
            buckets[current].append(text)
            continue
        if current is not None:
            buckets[current].append(text)
    return {key: "\n".join(lines).lower() for key, lines in buckets.items()}


def evaluate_section_coverage(section_text: dict[str, str]) -> dict[str, str]:
    coverage: dict[str, str] = {}
    for _, key in SECTION_KEYS:
        text = section_text.get(key, "")
        if not text:
            coverage[key] = "missing"
            continue
        bundle_hits = 0
        for bundle in SECTION_KEYWORDS[key]:
            if any(term in text for term in bundle):
                bundle_hits += 1
        if bundle_hits >= 2:
            coverage[key] = "ok"
        elif bundle_hits == 1:
            coverage[key] = "weak"
        else:
            coverage[key] = "missing"
    return coverage


def check_report(path: Path, thresholds: dict[str, int]) -> RichnessResult:
    if not path.exists():
        raise FileNotFoundError(f"Report not found: {path}")

    xml = read_document_xml(path)
    root = ET.fromstring(xml)
    paragraphs = root.findall(".//w:p", WORD_NS)
    body_text = "\n".join(paragraph_text(p) for p in paragraphs)

    figures = len(re.findall(r"\bFigure\s+\d+[\.:]", body_text, flags=re.IGNORECASE))
    tables = len(re.findall(r"\bTable\s+\d+[\.:]", body_text, flags=re.IGNORECASE))
    formulas = count_formulas(xml)
    pseudocode_blocks, code_blocks = count_shaded_code_blocks(root)

    counts = {
        "figures": figures,
        "tables": tables,
        "formulas": formulas,
        "pseudocode_blocks": pseudocode_blocks,
        "code_blocks": code_blocks,
    }

    section_text = split_sections(paragraphs)
    coverage = evaluate_section_coverage(section_text)

    failures: list[str] = []
    if figures < thresholds["min_figures"]:
        failures.append(f"figures {figures} < min {thresholds['min_figures']}")
    if tables < thresholds["min_tables"]:
        failures.append(f"tables {tables} < min {thresholds['min_tables']}")
    if formulas < thresholds["min_formulas"]:
        failures.append(f"formulas {formulas} < min {thresholds['min_formulas']}")
    if pseudocode_blocks < thresholds["min_pseudocode_blocks"]:
        failures.append(
            f"pseudocode blocks {pseudocode_blocks} < min {thresholds['min_pseudocode_blocks']}"
        )
    if code_blocks < thresholds["min_code_blocks"]:
        failures.append(f"code blocks {code_blocks} < min {thresholds['min_code_blocks']}")
    for key, status in coverage.items():
        if status == "missing":
            failures.append(f"section {key} has no qualifying visual / analytical content")

    return RichnessResult(counts=counts, section_coverage=coverage, failures=failures)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Generated report .docx")
    parser.add_argument("--min-figures", type=int, default=DEFAULT_THRESHOLDS["min_figures"])
    parser.add_argument("--min-tables", type=int, default=DEFAULT_THRESHOLDS["min_tables"])
    parser.add_argument("--min-formulas", type=int, default=DEFAULT_THRESHOLDS["min_formulas"])
    parser.add_argument(
        "--min-pseudocode-blocks",
        type=int,
        default=DEFAULT_THRESHOLDS["min_pseudocode_blocks"],
    )
    parser.add_argument(
        "--min-code-blocks", type=int, default=DEFAULT_THRESHOLDS["min_code_blocks"]
    )
    parser.add_argument("--output", help="Write JSON to this path instead of stdout")
    args = parser.parse_args(argv)

    thresholds = {
        "min_figures": args.min_figures,
        "min_tables": args.min_tables,
        "min_formulas": args.min_formulas,
        "min_pseudocode_blocks": args.min_pseudocode_blocks,
        "min_code_blocks": args.min_code_blocks,
    }

    try:
        result = check_report(Path(args.report), thresholds)
    except (FileNotFoundError, zipfile.BadZipFile, KeyError, ET.ParseError, UnicodeDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = {
        "report": str(args.report),
        "thresholds": thresholds,
        "counts": result.counts,
        "section_coverage": result.section_coverage,
        "failures": result.failures,
        "verdict": "pass" if result.passed else "needs_revision",
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)

    return 0 if result.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
