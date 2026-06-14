#!/usr/bin/env python3
"""Validate common structural hazards in generated experiment report DOCX files."""

from __future__ import annotations

import argparse
import dataclasses
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

REQUIRED_SECTIONS = (
    "Experimental Purposes and Requirements",
    "Algorithms or Models Used",
    "Experiment Contents and Process",
    "Discussion and Conclusions",
)

RAW_MARKERS = ("$", "\\(", "\\)", "\\[", "\\]")
PLAIN_FORMULA_PATTERNS = (
    r"\bexp\s*\(",
    r"\bargmax\b",
    r"\bsum[_\(]",
    r"\bprod(?:uct)?[_\(]",
    r"\^\s*[A-Za-z0-9_]",
    r"\|\|.*\|\|",
)


@dataclasses.dataclass
class ValidationResult:
    path: Path
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def extract_document_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        return zf.read("word/document.xml").decode("utf-8")


def extract_text(path: Path) -> str:
    xml = extract_document_xml(path)
    root = ET.fromstring(xml)
    paragraphs = []
    for para in root.findall(".//w:p", WORD_NS):
        text = "".join(node.text or "" for node in para.findall(".//w:t", WORD_NS))
        if text.strip():
            paragraphs.append(text)
    return "\n".join(paragraphs)


def _paragraph_text(para: ET.Element) -> str:
    return "".join(node.text or "" for node in para.findall(".//w:t", WORD_NS))


def _looks_like_heading(text: str) -> bool:
    """Numbered heading like `3.1 Foo` or `2.1.1 Bar`."""
    return bool(re.match(r"^\d+(?:\.\d+)+\s+\S", text)) or bool(re.match(r"^[1-4]\s+\S", text))


def _looks_like_caption(text: str) -> bool:
    return bool(
        re.match(r"^\s*(Figure|Table|Algorithm|Code)\s+\d+[\.:]", text, flags=re.IGNORECASE)
    )


def _has_first_line_indent(para: ET.Element) -> bool:
    ind = para.find("./w:pPr/w:ind", WORD_NS)
    if ind is None:
        return False
    for attr in ("firstLine", "start", "left"):
        value = ind.attrib.get(f"{{{WORD_NS['w']}}}{attr}")
        if value and value not in ("0", "0pt"):
            try:
                if int(value) > 0:
                    return True
            except ValueError:
                continue
    return False


def _has_visible_border(border: ET.Element | None) -> bool:
    if border is None:
        return False
    val = border.attrib.get(f"{{{WORD_NS['w']}}}val", "")
    if val in ("nil", "none", ""):
        return False
    sz = border.attrib.get(f"{{{WORD_NS['w']}}}sz", "0")
    try:
        return int(sz) > 0
    except ValueError:
        return True


def _check_three_line_table(table: ET.Element) -> list[str]:
    """Return a list of issues for a single Word table."""
    issues: list[str] = []

    tbl_borders = table.find("./w:tblPr/w:tblBorders", WORD_NS)
    if tbl_borders is not None:
        for inner in ("insideH", "insideV", "left", "right"):
            elem = tbl_borders.find(f"w:{inner}", WORD_NS)
            if _has_visible_border(elem):
                issues.append(f"table-level inner/side border `{inner}` is visible")

    rows = table.findall("./w:tr", WORD_NS)
    if not rows:
        return issues

    # Inspect every cell — any visible left/right/insideH/insideV border breaks
    # the three-line look.
    for row_idx, row in enumerate(rows):
        is_first = row_idx == 0
        is_last = row_idx == len(rows) - 1
        for cell in row.findall("./w:tc", WORD_NS):
            tc_borders = cell.find("./w:tcPr/w:tcBorders", WORD_NS)
            if tc_borders is None:
                # Inheriting from tblBorders; we already inspected those.
                continue
            for side in ("left", "right", "insideH", "insideV"):
                if _has_visible_border(tc_borders.find(f"w:{side}", WORD_NS)):
                    issues.append(f"row {row_idx + 1} has visible `{side}` cell border")
            # Inner horizontal: any non-first row's top, any non-last row's bottom
            top = tc_borders.find("w:top", WORD_NS)
            if not is_first and _has_visible_border(top):
                issues.append(f"row {row_idx + 1} has visible top border (should be nil for body rows)")
            bottom = tc_borders.find("w:bottom", WORD_NS)
            if not is_last and row_idx != 0 and _has_visible_border(bottom):
                # Allow header bottom (row 0); flag every other inner bottom.
                issues.append(
                    f"row {row_idx + 1} has visible bottom border (only header row 1 and last row may keep it)"
                )

    return issues


def _check_body_indentation(paragraphs: list[ET.Element]) -> tuple[int, int]:
    """Return (indented_count, candidate_count) for body paragraphs.

    A "candidate" is a non-empty paragraph that is not a heading, caption,
    table-cell paragraph, or shaded code paragraph.
    """
    indented = 0
    candidates = 0
    for para in paragraphs:
        text = _paragraph_text(para).strip()
        if not text or len(text) < 30:
            continue
        if _looks_like_heading(text) or _looks_like_caption(text):
            continue
        # Skip if inside a table cell — find the nearest ancestor `w:tc`. ET
        # does not give parents directly, so use a marker on the element tree.
        if para.get("_in_table"):
            continue
        # Skip shaded code paragraphs.
        shd = para.find("./w:pPr/w:shd", WORD_NS)
        if shd is not None:
            fill = shd.attrib.get(f"{{{WORD_NS['w']}}}fill", "").lower()
            if fill and fill not in {"auto", "none", "ffffff"}:
                continue
        candidates += 1
        if _has_first_line_indent(para):
            indented += 1
    return indented, candidates


def _annotate_table_paragraphs(root: ET.Element) -> None:
    """Tag every `w:p` that lives inside a `w:tbl` so the indent check can skip them."""
    for tbl in root.findall(".//w:tbl", WORD_NS):
        for para in tbl.findall(".//w:p", WORD_NS):
            para.set("_in_table", "1")


def has_section(text: str, section: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).lower()
    target = section.lower()
    if target in normalized:
        return True
    if section == "Experiment Contents and Process":
        return "experimental contents" in normalized and "process" in normalized
    return False


def validate_docx(path: str | Path) -> ValidationResult:
    path = Path(path)
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return ValidationResult(path, [f"File not found: {path}"], warnings)
    if path.suffix.lower() != ".docx":
        errors.append("Output must be a .docx file for structural validation")
        return ValidationResult(path, errors, warnings)

    try:
        text = extract_text(path)
        xml = extract_document_xml(path)
        root = ET.fromstring(xml)
    except (KeyError, zipfile.BadZipFile, ET.ParseError, UnicodeDecodeError) as exc:
        errors.append(f"Could not read DOCX structure: {exc}")
        return ValidationResult(path, errors, warnings)

    for section in REQUIRED_SECTIONS:
        if not has_section(text, section):
            errors.append(f"Missing section: {section}")

    for marker in RAW_MARKERS:
        if marker in text:
            errors.append(f"Raw LaTeX/math marker found: {marker}")

    has_word_equation = "<m:oMath" in xml or "<m:oMathPara" in xml
    if any(re.search(pattern, text) for pattern in PLAIN_FORMULA_PATTERNS) and not has_word_equation:
        errors.append("Formula-like plain text found but no editable Word equation object detected")

    if re.search(r"(?<!\\)\{[^{}\n]{1,80}\}", text):
        warnings.append("Brace-delimited text found; confirm it is not uncompiled LaTeX")

    if not re.search(r"Figure\s+\d+[\.:]", text, flags=re.IGNORECASE):
        warnings.append("No figure captions found")

    if "Table" in text and not re.search(r"Table\s+\d+[\.:]", text, flags=re.IGNORECASE):
        warnings.append("Table text found but no numbered table caption detected")

    if "<w:tbl" not in xml and re.search(r"\bTable\s+\d+[\.:]", text, flags=re.IGNORECASE):
        warnings.append("Table caption found but no Word table structure detected")

    if re.search(r" {6,}", text):
        warnings.append("Long visible space run found")

    # Three-line table check.
    tables = root.findall(".//w:tbl", WORD_NS)
    for table_idx, table in enumerate(tables, start=1):
        for issue in _check_three_line_table(table):
            errors.append(f"Table {table_idx} not in three-line style: {issue}")

    # First-line indent check on body paragraphs.
    _annotate_table_paragraphs(root)
    paragraphs = root.findall(".//w:p", WORD_NS)
    indented, candidates = _check_body_indentation(paragraphs)
    if candidates >= 5:
        ratio = indented / candidates
        if ratio < 0.6:
            errors.append(
                f"Body paragraphs missing 1.27cm first-line indent ({indented}/{candidates}"
                f" indented, ratio {ratio:.2f})"
            )
        elif ratio < 0.85:
            warnings.append(
                f"Body paragraph indentation is inconsistent ({indented}/{candidates} indented)"
            )

    return ValidationResult(path, errors, warnings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", help="Generated experiment report .docx")
    args = parser.parse_args(argv)

    result = validate_docx(args.docx)
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    for warning in result.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if result.ok:
        print(f"OK: {result.path}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
