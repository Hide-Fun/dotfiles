#!/usr/bin/env python3
"""Audit Quarto/QMD files for hardcoded citations and manual references."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

HEADING_RE = re.compile(
    r"^(#{2,6})\s*(?:References|参考文献|参考文献（References）)\s*$",
    re.MULTILINE,
)
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
QUARTO_CITE_RE = re.compile(r"(?<![\w/])@([A-Za-z0-9_:.#$%&\-+?<>~/]+)")
PAREN_CITATION_RE = re.compile(r"[（(]([^()（）]*?[12][0-9]{3}[a-z]?[^()（）]*?)[）)]")
IN_TEXT_CITATION_RE = re.compile(
    r"(?<!@)\b([A-Z][A-Za-z'` .,&-]*?)\s*[\(（]\s*([12][0-9]{3}[a-z]?)\s*[\)）]"
)
YEAR_RE = re.compile(r"\b([12][0-9]{3}[a-z]?)\b")
ENTRY_START_RE = re.compile(r"^@[\w-]+\s*\{\s*([^,]+),", re.MULTILINE)
REFERENCE_START_RE = re.compile(r"^[A-Z][^\n]{0,120}\([12][0-9]{3}[a-z]?\)")


@dataclass
class CitationCandidate:
    raw: str
    author_hint: str
    year: str
    candidate_citekey: str
    matched_keys: list[str]


@dataclass
class ReferenceCandidate:
    raw: str
    author_hint: str
    year: str
    doi: str | None
    candidate_citekey: str
    matched_keys: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--all-qmd", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--sample-size", type=int, default=5)
    return parser.parse_args()


def normalize_token(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", stripped.lower())


def author_aliases(text: str) -> set[str]:
    cleaned = re.sub(r"\bet al\.?\b", "", text, flags=re.IGNORECASE)
    cleaned = cleaned.replace("&", " and ")
    first_chunk = re.split(r"\band\b", cleaned, maxsplit=1, flags=re.IGNORECASE)[0]
    first_chunk = first_chunk.strip(" ,;:.()[]{}")
    if not first_chunk:
        return set()
    full_alias = normalize_token(first_chunk)
    parts = [normalize_token(part) for part in re.split(r"\s+", first_chunk) if part]
    aliases = {alias for alias in (full_alias, parts[-1] if parts else "") if alias}
    return aliases


def suggested_citekey(author_hint: str, year: str) -> str:
    aliases = sorted(author_aliases(author_hint), key=len, reverse=True)
    lead = aliases[0] if aliases else "ref"
    return f"{lead}{year}"


def match_keys(author_hint: str, year: str, signature_map: dict[str, list[str]]) -> list[str]:
    keys: set[str] = set()
    for alias in author_aliases(author_hint):
        keys.update(signature_map.get(f"{alias}{year}", []))
    return sorted(keys)


def parse_quarto_config(project_root: Path) -> tuple[str | None, list[str]]:
    config_path = project_root / "_quarto.yml"
    if not config_path.exists():
        return None, []

    bibliography = None
    chapters: list[str] = []
    lines = config_path.read_text(encoding="utf-8").splitlines()
    in_book = False
    in_chapters = False

    for line in lines:
        if not line.strip():
            continue
        if re.match(r"^bibliography:\s*", line):
            bibliography = line.split(":", 1)[1].strip()
        if re.match(r"^book:\s*$", line):
            in_book = True
            in_chapters = False
            continue
        if in_book and re.match(r"^\S", line):
            in_book = False
            in_chapters = False
        if in_book and re.match(r"^\s{2}chapters:\s*$", line):
            in_chapters = True
            continue
        if in_chapters and re.match(r"^\s{4}-\s+", line):
            chapters.append(line.split("-", 1)[1].strip())
            continue
        if in_chapters and not re.match(r"^\s{4}-\s+", line):
            in_chapters = False

    return bibliography, chapters


def iter_bib_entries(text: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    positions = [match.start() for match in re.finditer(r"@", text)]

    for start in positions:
        brace_start = text.find("{", start)
        if brace_start == -1:
            continue
        depth = 0
        for index in range(brace_start, len(text)):
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    entry = text[start : index + 1]
                    header = ENTRY_START_RE.search(entry)
                    if header:
                        entries.append((header.group(1).strip(), entry))
                    break
    return entries


def field_value(entry: str, field: str) -> str | None:
    pattern = re.compile(
        rf"\b{re.escape(field)}\s*=\s*(\{{.*?\}}|\".*?\"|[^,\n]+)",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(entry)
    if not match:
        return None
    value = match.group(1).strip().strip(",")
    if value.startswith("{") and value.endswith("}"):
        value = value[1:-1]
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return re.sub(r"\s+", " ", value).strip()


def build_signature_map(bib_path: Path) -> tuple[list[str], dict[str, list[str]]]:
    if not bib_path.exists():
        return [], {}

    text = bib_path.read_text(encoding="utf-8")
    keys: list[str] = []
    signature_map: dict[str, list[str]] = {}

    for key, entry in iter_bib_entries(text):
        keys.append(key)
        author = field_value(entry, "author") or ""
        year = field_value(entry, "year") or ""
        if not year:
            date = field_value(entry, "date") or ""
            year_match = YEAR_RE.search(date)
            year = year_match.group(1) if year_match else ""
        if not author or not year:
            continue
        for alias in author_aliases(author):
            signature_map.setdefault(f"{alias}{year}", []).append(key)

    return keys, signature_map


def split_citation_segments(text: str) -> list[tuple[str, str]]:
    segments: list[tuple[str, str]] = []
    for match in PAREN_CITATION_RE.finditer(text):
        content = match.group(1)
        if "@" in content:
            continue
        for segment in re.split(r"[;；]", content):
            item = segment.strip()
            parsed = parse_author_year(item)
            if parsed:
                segments.append(parsed)
    for match in IN_TEXT_CITATION_RE.finditer(text):
        author = match.group(1).strip()
        year = match.group(2)
        parsed = parse_author_year(f"{author} {year}")
        if parsed:
            segments.append(parsed)
    return segments


def parse_author_year(text: str) -> tuple[str, str] | None:
    cleaned = re.sub(r"\s+", " ", text).strip(" ,;:.")
    match = re.search(r"(.+?)\s+([12][0-9]{3}[a-z]?)$", cleaned)
    if not match:
        return None
    author_hint = match.group(1).strip()
    year = match.group(2)
    if not author_hint or len(author_hint) < 2:
        return None
    return author_hint, year


def extract_reference_block(text: str) -> tuple[str | None, list[str]]:
    heading = HEADING_RE.search(text)
    if not heading:
        return None, []
    block = text[heading.end() :].strip()
    if not block:
        return heading.group(0).strip(), []
    entries: list[str] = []
    paragraphs = re.split(r"\n\s*\n", block)
    for paragraph in paragraphs:
        lines = []
        for line in paragraph.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if re.fullmatch(r"[-–—]{3,}", stripped):
                continue
            lines.append(stripped.rstrip("\\").strip())
        if not lines:
            continue

        start_count = sum(bool(REFERENCE_START_RE.match(line)) for line in lines)
        if start_count >= 2:
            current = ""
            for line in lines:
                if REFERENCE_START_RE.match(line):
                    if current:
                        entries.append(current)
                    current = line
                elif current:
                    current = f"{current} {line}".strip()
                else:
                    current = line
            if current:
                entries.append(current)
        else:
            entries.append(" ".join(lines).strip())
    return heading.group(0).strip(), entries


def audit_file(path: Path, signature_map: dict[str, list[str]], sample_size: int) -> dict:
    text = path.read_text(encoding="utf-8")
    heading, raw_entries = extract_reference_block(text)

    citation_candidates: list[CitationCandidate] = []
    seen_citations: set[tuple[str, str]] = set()
    for author_hint, year in split_citation_segments(text):
        dedupe_key = (author_hint, year)
        if dedupe_key in seen_citations:
            continue
        seen_citations.add(dedupe_key)
        citation_candidates.append(
            CitationCandidate(
                raw=f"{author_hint} {year}",
                author_hint=author_hint,
                year=year,
                candidate_citekey=suggested_citekey(author_hint, year),
                matched_keys=match_keys(author_hint, year, signature_map),
            )
        )

    reference_candidates: list[ReferenceCandidate] = []
    for entry in raw_entries:
        year_match = YEAR_RE.search(entry)
        if not year_match:
            continue
        year = year_match.group(1)
        author_hint = entry[: year_match.start()].strip(" ,;:.")
        doi_match = DOI_RE.search(entry)
        reference_candidates.append(
            ReferenceCandidate(
                raw=entry,
                author_hint=author_hint,
                year=year,
                doi=doi_match.group(0) if doi_match else None,
                candidate_citekey=suggested_citekey(author_hint, year),
                matched_keys=match_keys(author_hint, year, signature_map),
            )
        )

    unmatched_citations = [item for item in citation_candidates if not item.matched_keys]
    unmatched_references = [item for item in reference_candidates if not item.matched_keys]

    return {
        "path": str(path),
        "existing_quarto_citations": len(set(QUARTO_CITE_RE.findall(text))),
        "doi_count": len(set(match.group(0) for match in DOI_RE.finditer(text))),
        "manual_reference_heading": heading,
        "manual_reference_entries": len(reference_candidates),
        "hardcoded_citation_candidates": len(citation_candidates),
        "matched_hardcoded_citations": sum(bool(item.matched_keys) for item in citation_candidates),
        "matched_manual_references": sum(bool(item.matched_keys) for item in reference_candidates),
        "sample_unmatched_citations": [asdict(item) for item in unmatched_citations[:sample_size]],
        "sample_unmatched_manual_references": [asdict(item) for item in unmatched_references[:sample_size]],
        "sample_doi_references": [
            asdict(item) for item in reference_candidates if item.doi
        ][:sample_size],
    }


def target_qmd_files(project_root: Path, all_qmd: bool, chapters: list[str]) -> list[Path]:
    if all_qmd:
        return sorted(project_root.rglob("*.qmd"))
    if chapters:
        return [project_root / chapter for chapter in chapters if (project_root / chapter).exists()]
    return sorted(project_root.glob("*.qmd"))


def markdown_report(report: dict) -> str:
    lines = [
        f"Project root: {report['project_root']}",
        f"Bibliography: {report['bibliography'] or '(not found)'}",
        f"Target files: {report['target_mode']} ({len(report['files'])} files)",
        f"BibTeX keys: {report['bib_key_count']}",
        "",
    ]

    for file_report in report["files"]:
        lines.append(f"## {file_report['path']}")
        lines.append(f"- existing Quarto citations: {file_report['existing_quarto_citations']}")
        lines.append(
            f"- hardcoded citation candidates: {file_report['hardcoded_citation_candidates']} "
            f"(matched to existing bib: {file_report['matched_hardcoded_citations']})"
        )
        lines.append(
            f"- manual references: {file_report['manual_reference_entries']} "
            f"(matched to existing bib: {file_report['matched_manual_references']})"
        )
        lines.append(f"- DOI count in file: {file_report['doi_count']}")
        lines.append(
            f"- manual reference heading: {file_report['manual_reference_heading'] or '(none)'}"
        )
        if file_report["sample_unmatched_citations"]:
            lines.append("- sample unmatched citations:")
            for item in file_report["sample_unmatched_citations"]:
                lines.append(
                    f"  - {item['raw']} -> {item['candidate_citekey']} "
                    f"(matches: {', '.join(item['matched_keys']) or 'none'})"
                )
        if file_report["sample_unmatched_manual_references"]:
            lines.append("- sample unmatched manual references:")
            for item in file_report["sample_unmatched_manual_references"]:
                doi_note = f", doi: {item['doi']}" if item["doi"] else ""
                lines.append(
                    f"  - {item['candidate_citekey']} ({item['year']}){doi_note}: {item['raw']}"
                )
        lines.append("")

    return "\n".join(lines).rstrip()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    bibliography, chapters = parse_quarto_config(project_root)
    bib_path = project_root / bibliography if bibliography else project_root / "references.bib"
    bib_keys, signature_map = build_signature_map(bib_path)
    files = target_qmd_files(project_root, args.all_qmd, chapters)

    report = {
        "project_root": str(project_root),
        "bibliography": str(bib_path) if bib_path.exists() else None,
        "target_mode": "all-qmd" if args.all_qmd else "book.chapters",
        "bib_key_count": len(bib_keys),
        "files": [audit_file(path, signature_map, args.sample_size) for path in files],
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(markdown_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
