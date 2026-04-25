#!/usr/bin/env python3
"""Add first-pass reliability tiers to a sequence-candidate CSV/TSV table."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Iterable


TYPE_RE = re.compile(
    r"\b(holo|iso|lecto|neo|epi|para|syn)type\b|"
    r"\btype (specimen|material|strain)\b|"
    r"\bex[- ]?type\b|\bex type\b",
    re.IGNORECASE,
)
UNITE_RE = re.compile(r"\bSH\d{5,}(?:\.\d+[A-Z]{0,3})?\b|\bUNITE\b", re.IGNORECASE)
CBS_RE = re.compile(r"\bCBS\s*[-:]?\s*[A-Za-z0-9][A-Za-z0-9_.-]*\b", re.IGNORECASE)
UNKNOWN_TAXON_RE = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(sp\.|cf\.|aff\.|uncultured|unidentified|environmental|clone|endophyte|mycorrhizal)"
    r"(?![A-Za-z0-9])",
    re.IGNORECASE,
)
MISSING_RE = re.compile(r"^\s*(na|n/a|none|null|unknown|not available|unavailable|-)?\s*$", re.IGNORECASE)


def normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")


def row_value(row: dict[str, str], names: Iterable[str]) -> str:
    for name in names:
        value = row.get(normalize_key(name), "")
        if value and not MISSING_RE.match(value):
            return value.strip()
    return ""


def joined_values(row: dict[str, str], names: Iterable[str]) -> str:
    return " | ".join(v for v in (row_value(row, [name]) for name in names) if v)


def parse_float(value: str) -> float | None:
    if not value:
        return None
    try:
        return float(value.replace("%", "").strip())
    except ValueError:
        return None


def has_type_evidence(row: dict[str, str]) -> bool:
    text = joined_values(row, ["type_status", "source", "notes", "rationale", "title"])
    return bool(TYPE_RE.search(text))


def has_unite_evidence(row: dict[str, str]) -> bool:
    text = joined_values(row, ["unite_sh", "species_hypothesis", "source", "notes", "title"])
    return bool(UNITE_RE.search(text))


def has_cbs_evidence(row: dict[str, str]) -> bool:
    text = joined_values(row, ["culture_collection", "strain", "isolate", "source", "notes", "title"])
    return bool(CBS_RE.search(text))


def has_voucher(row: dict[str, str]) -> bool:
    text = joined_values(
        row,
        [
            "voucher",
            "specimen_voucher",
            "bio_material",
            "culture_collection",
            "herbarium",
            "material_sample",
        ],
    )
    return bool(text)


def has_host(row: dict[str, str]) -> bool:
    text = row_value(row, ["host", "isolation_source", "source_host"])
    return bool(text)


def unknown_taxon(row: dict[str, str]) -> bool:
    text = joined_values(row, ["organism", "taxon", "title", "species"])
    return bool(UNKNOWN_TAXON_RE.search(text))


def blast_close(row: dict[str, str], min_identity: float, min_query_cover: float, max_evalue: float) -> bool:
    identity = parse_float(row_value(row, ["blast_identity", "identity", "pident", "percent_identity"]))
    query_cover = parse_float(row_value(row, ["blast_query_cover", "qcov", "query_cover", "query_coverage"]))
    evalue = parse_float(row_value(row, ["blast_evalue", "evalue"]))

    if identity is None:
        return False
    if identity < min_identity:
        return False
    if query_cover is not None and query_cover < min_query_cover:
        return False
    if evalue is not None and evalue > max_evalue:
        return False
    return True


def score_row(row: dict[str, str], args: argparse.Namespace) -> dict[str, str]:
    type_flag = has_type_evidence(row)
    unite_flag = has_unite_evidence(row)
    cbs_flag = has_cbs_evidence(row)
    voucher_flag = has_voucher(row)
    host_flag = has_host(row)
    unknown_flag = unknown_taxon(row)
    close_flag = blast_close(row, args.min_identity, args.min_query_cover, args.max_evalue)

    flags = []
    for flag, label in [
        (type_flag, "type"),
        (unite_flag, "unite_sh"),
        (cbs_flag, "cbs"),
        (close_flag, "blast_close"),
        (voucher_flag, "voucher"),
        (host_flag, "host"),
        (unknown_flag, "unknown_taxon"),
    ]:
        if flag:
            flags.append(label)

    if type_flag or unite_flag or cbs_flag:
        tier = "high"
        decision = "include_anchor"
        score = 3
    elif close_flag and voucher_flag:
        tier = "medium"
        decision = "include_if_needed_close_voucher"
        score = 2
    elif close_flag and host_flag and unknown_flag:
        tier = "low"
        decision = "include_only_if_needed_host_known"
        score = 1
    else:
        tier = "unranked"
        decision = "review_or_deprioritize"
        score = 0

    caveats = []
    if close_flag is False and not (type_flag or unite_flag or cbs_flag):
        caveats.append("BLAST closeness not established by provided metrics")
    if tier == "high" and not close_flag:
        caveats.append("anchor evidence present; verify marker overlap and relevance")
    if unknown_flag and tier != "low":
        caveats.append("taxon name unresolved")
    if not voucher_flag and tier == "medium":
        caveats.append("voucher evidence should be rechecked")

    row["tier"] = tier
    row["selection_score"] = str(score)
    row["decision"] = decision
    row["evidence_flags"] = ",".join(flags)
    row["score_caveats"] = "; ".join(caveats)
    return row


def sniff_dialect(path: Path) -> csv.Dialect:
    sample = path.read_text(encoding="utf-8-sig")[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t")
    except csv.Error:
        return csv.excel_tab if "\t" in sample else csv.excel


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]], csv.Dialect]:
    dialect = sniff_dialect(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        if not reader.fieldnames:
            raise SystemExit("Input table has no header row.")
        fieldnames = [normalize_key(name) for name in reader.fieldnames]
        rows = []
        for raw in reader:
            rows.append({normalize_key(k): (v or "").strip() for k, v in raw.items()})
    return fieldnames, rows, dialect


def write_rows(path: Path | None, fieldnames: list[str], rows: list[dict[str, str]], delimiter: str) -> None:
    extras = ["tier", "selection_score", "decision", "evidence_flags", "score_caveats"]
    output_fields = fieldnames + [field for field in extras if field not in fieldnames]
    handle = path.open("w", newline="", encoding="utf-8") if path else sys.stdout
    try:
        writer = csv.DictWriter(handle, fieldnames=output_fields, delimiter=delimiter, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if path:
            handle.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Candidate CSV/TSV table.")
    parser.add_argument("-o", "--output", type=Path, help="Output CSV/TSV path. Defaults to stdout.")
    parser.add_argument("--min-identity", type=float, default=97.0, help="Minimum BLAST percent identity.")
    parser.add_argument("--min-query-cover", type=float, default=80.0, help="Minimum BLAST query cover percent.")
    parser.add_argument("--max-evalue", type=float, default=1e-20, help="Maximum accepted BLAST e-value.")
    parser.add_argument("--delimiter", choices=[",", "tab"], help="Output delimiter. Defaults to input style.")
    args = parser.parse_args()

    fieldnames, rows, dialect = read_rows(args.input)
    scored = [score_row(row, args) for row in rows]
    delimiter = "\t" if args.delimiter == "tab" or (args.delimiter is None and dialect.delimiter == "\t") else ","
    write_rows(args.output, fieldnames, scored, delimiter)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
