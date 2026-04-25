#!/usr/bin/env python3
"""Create a local UNITE BLAST database, screen query sequences, and export target-taxon candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_VERSION = "0.2.0"

OUTFMT_FIELDS = [
    "qseqid",
    "sseqid",
    "pident",
    "qcovs",
    "length",
    "mismatch",
    "gapopen",
    "qstart",
    "qend",
    "sstart",
    "send",
    "evalue",
    "bitscore",
    "stitle",
]
OUTFMT = "6 " + " ".join(OUTFMT_FIELDS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a local BLAST database from a UNITE SH fasta and recover candidate query sequences for a target taxon."
    )
    parser.add_argument("--query-fasta", required=True, type=Path)
    parser.add_argument("--unite-fasta", required=True, type=Path)
    parser.add_argument("--taxon", required=True)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--db-prefix", type=Path, default=None)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--pident", type=float, default=90.0)
    parser.add_argument("--qcov", type=float, default=90.0)
    parser.add_argument("--max-target-seqs", type=int, default=50)
    parser.add_argument("--blast-task", default="megablast")
    parser.add_argument("--force-db", action="store_true")
    return parser.parse_args()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^0-9A-Za-z]+", " ", text.lower())).strip()


def blastdb_exists(prefix: Path) -> bool:
    return all(Path(f"{prefix}{suffix}").exists() for suffix in (".nhr", ".nin", ".nsq"))


def iso_now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def format_cmd(cmd: list[str]) -> str:
    return shlex.join(cmd)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def derive_run_id(outdir: Path) -> str:
    if outdir.name:
        return outdir.name
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run-{timestamp}"


def run(cmd: list[str], stdout_path: Path | None = None) -> None:
    try:
        if stdout_path is None:
            subprocess.run(cmd, check=True)
            return
        with stdout_path.open("w", encoding="utf-8") as handle:
            subprocess.run(cmd, check=True, stdout=handle)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Command failed: {' '.join(cmd)}") from exc


def command_output(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    return stdout or stderr


def get_tool_version(tool_name: str) -> str:
    for args in ([tool_name, "-version"], [tool_name, "--version"]):
        try:
            text = command_output(args)
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        if first_line:
            return first_line
    return "unavailable"


def make_makeblastdb_cmd(unite_fasta: Path, db_prefix: Path, title: str) -> list[str]:
    return [
        "makeblastdb",
        "-in",
        str(unite_fasta),
        "-dbtype",
        "nucl",
        "-parse_seqids",
        "-out",
        str(db_prefix),
        "-title",
        title,
    ]


def make_blast_cmd(
    query_fasta: Path,
    db_prefix: Path,
    threads: int,
    max_target_seqs: int,
    blast_task: str,
) -> list[str]:
    return [
        "blastn",
        "-task",
        blast_task,
        "-query",
        str(query_fasta),
        "-db",
        str(db_prefix),
        "-outfmt",
        OUTFMT,
        "-max_target_seqs",
        str(max_target_seqs),
        "-num_threads",
        str(threads),
    ]


def load_fingerprint(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Existing BLAST database found but fingerprint file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Fingerprint file is not valid JSON: {path}") from exc


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def ensure_blastdb(
    unite_fasta: Path,
    db_prefix: Path,
    title: str,
    force: bool,
    unite_fasta_sha256: str,
    fingerprint_path: Path,
    makeblastdb_cmd: list[str],
    makeblastdb_version: str,
) -> bool:
    db_exists = blastdb_exists(db_prefix)
    if db_exists and not force:
        fingerprint = load_fingerprint(fingerprint_path)
        recorded_sha = fingerprint.get("unite_fasta_sha256")
        if recorded_sha != unite_fasta_sha256:
            raise SystemExit(
                "Existing BLAST database fingerprint does not match the current UNITE FASTA "
                f"(expected {recorded_sha}, observed {unite_fasta_sha256}). "
                "Use a new outdir/db-prefix or rerun with --force-db."
            )
        return False

    db_prefix.parent.mkdir(parents=True, exist_ok=True)
    run(makeblastdb_cmd)
    fingerprint = {
        "unite_fasta_path": str(unite_fasta),
        "unite_fasta_sha256": unite_fasta_sha256,
        "db_prefix": str(db_prefix),
        "makeblastdb_version": makeblastdb_version,
        "created_at": iso_now_utc(),
    }
    write_json(fingerprint_path, fingerprint)
    return True


def parse_fasta(path: Path) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    header: str | None = None
    chunks: list[str] = []
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    records.append((header, "".join(chunks)))
                header = line[1:].split()[0]
                chunks = []
            else:
                chunks.append(line)
    if header is not None:
        records.append((header, "".join(chunks)))
    return records


def row_matches_taxon(row: dict[str, str], taxon_token: str) -> bool:
    return any(taxon_token in normalize_text(row.get(field, "")) for field in ("sseqid", "stitle"))


def filter_hits(
    blast_tsv: Path,
    taxon: str,
    min_pident: float,
    min_qcov: float,
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    taxon_token = normalize_text(taxon)
    passing_rows: list[dict[str, str]] = []
    best_by_query: dict[str, dict[str, str]] = {}
    with blast_tsv.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle, fieldnames=OUTFMT_FIELDS, delimiter="\t")
        for row in reader:
            try:
                pident = float(row["pident"])
                qcov = float(row["qcovs"])
                bitscore = float(row["bitscore"])
                evalue = float(row["evalue"])
            except ValueError:
                continue
            if pident <= min_pident or qcov <= min_qcov:
                continue
            if not row_matches_taxon(row, taxon_token):
                continue
            row["_bitscore"] = f"{bitscore:.6f}"
            row["_evalue"] = f"{evalue:.6g}"
            passing_rows.append(row)
            current = best_by_query.get(row["qseqid"])
            if current is None:
                best_by_query[row["qseqid"]] = row
                continue
            current_bitscore = float(current["_bitscore"])
            current_evalue = float(current["_evalue"])
            if bitscore > current_bitscore or (bitscore == current_bitscore and evalue < current_evalue):
                best_by_query[row["qseqid"]] = row
    passing_rows.sort(
        key=lambda row: (
            row["qseqid"],
            -float(row["_bitscore"]),
            float(row["_evalue"]),
        )
    )
    return passing_rows, best_by_query


def write_filtered_hits(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = OUTFMT_FIELDS
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_candidate_queries(
    query_fasta: Path,
    candidate_ids: list[str],
    candidate_fasta: Path,
) -> None:
    selected = set(candidate_ids)
    records = parse_fasta(query_fasta)
    with candidate_fasta.open("w", encoding="utf-8") as handle:
        for seq_id, sequence in records:
            if seq_id not in selected:
                continue
            handle.write(f">{seq_id}\n")
            for i in range(0, len(sequence), 80):
                handle.write(sequence[i : i + 80] + "\n")


def main() -> int:
    args = parse_args()
    query_fasta = args.query_fasta.resolve()
    unite_fasta = args.unite_fasta.resolve()
    if not query_fasta.exists():
        raise SystemExit(f"Query FASTA not found: {query_fasta}")
    if not unite_fasta.exists():
        raise SystemExit(f"UNITE FASTA not found: {unite_fasta}")

    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    run_id = derive_run_id(outdir)
    db_prefix = args.db_prefix.resolve() if args.db_prefix else outdir / "blastdb" / "unite_sh"
    fingerprint_path = Path(f"{db_prefix}.fingerprint.json")
    blast_tsv = outdir / "blast.tsv"
    filtered_tsv = outdir / "candidate_hits.tsv"
    candidate_ids_path = outdir / "candidate_query_ids.txt"
    candidate_fasta = outdir / "candidate_queries.fasta"
    summary_path = outdir / "summary.json"
    run_manifest_path = outdir / "run_manifest.json"

    query_fasta_sha256 = file_sha256(query_fasta)
    unite_fasta_sha256 = file_sha256(unite_fasta)
    makeblastdb_version = get_tool_version("makeblastdb")
    blastn_version = get_tool_version("blastn")
    makeblastdb_cmd = make_makeblastdb_cmd(
        unite_fasta=unite_fasta,
        db_prefix=db_prefix,
        title=f"UNITE SH screen for {args.taxon}",
    )
    blast_cmd = make_blast_cmd(
        query_fasta=query_fasta,
        db_prefix=db_prefix,
        threads=args.threads,
        max_target_seqs=args.max_target_seqs,
        blast_task=args.blast_task,
    )
    db_built = ensure_blastdb(
        unite_fasta=unite_fasta,
        db_prefix=db_prefix,
        title=f"UNITE SH screen for {args.taxon}",
        force=args.force_db,
        unite_fasta_sha256=unite_fasta_sha256,
        fingerprint_path=fingerprint_path,
        makeblastdb_cmd=makeblastdb_cmd,
        makeblastdb_version=makeblastdb_version,
    )
    run(blast_cmd, stdout_path=blast_tsv)

    passing_rows, best_by_query = filter_hits(
        blast_tsv=blast_tsv,
        taxon=args.taxon,
        min_pident=args.pident,
        min_qcov=args.qcov,
    )
    candidate_ids = sorted(best_by_query)
    write_filtered_hits(filtered_tsv, passing_rows)
    candidate_ids_path.write_text("\n".join(candidate_ids) + ("\n" if candidate_ids else ""), encoding="utf-8")
    write_candidate_queries(query_fasta, candidate_ids, candidate_fasta)

    output_paths = {
        "database_prefix": str(db_prefix),
        "db_fingerprint_json": str(fingerprint_path),
        "blast_tsv": str(blast_tsv),
        "candidate_hits_tsv": str(filtered_tsv),
        "candidate_query_ids": str(candidate_ids_path),
        "candidate_queries_fasta": str(candidate_fasta),
        "summary_json": str(summary_path),
        "run_manifest_json": str(run_manifest_path),
    }
    command_lines = {
        "driver": format_cmd([sys.executable, *sys.argv]),
        "makeblastdb": format_cmd(makeblastdb_cmd),
        "blastn": format_cmd(blast_cmd),
    }
    summary = {
        "ok": True,
        "run_id": run_id,
        "created_at": iso_now_utc(),
        "target_taxon": args.taxon,
        "query_fasta_path": str(query_fasta),
        "query_fasta_sha256": query_fasta_sha256,
        "unite_fasta_path": str(unite_fasta),
        "unite_fasta_sha256": unite_fasta_sha256,
        "blast_task": args.blast_task,
        "max_target_seqs": args.max_target_seqs,
        "threads": args.threads,
        "pident_gt": args.pident,
        "qcov_gt": args.qcov,
        "thresholds": {"pident_gt": args.pident, "qcov_gt": args.qcov},
        "database_prefix": str(db_prefix),
        "database_built": db_built,
        "command_line": command_lines["driver"],
        "command_lines": command_lines,
        "tool_versions": {
            "script": SCRIPT_VERSION,
            "makeblastdb": makeblastdb_version,
            "blastn": blastn_version,
        },
        "output_paths": output_paths,
        "blast_tsv": str(blast_tsv),
        "candidate_hits_tsv": str(filtered_tsv),
        "candidate_query_ids": str(candidate_ids_path),
        "candidate_queries_fasta": str(candidate_fasta),
        "candidate_query_count": len(candidate_ids),
        "matched_hit_count": len(passing_rows),
        "best_hits": [
            {
                "qseqid": row["qseqid"],
                "sseqid": row["sseqid"],
                "stitle": row.get("stitle", ""),
                "pident": float(row["pident"]),
                "qcovs": float(row["qcovs"]),
                "evalue": float(row["evalue"]),
                "bitscore": float(row["bitscore"]),
            }
            for row in (best_by_query[qseqid] for qseqid in candidate_ids)
        ],
    }
    write_json(summary_path, summary)
    write_json(run_manifest_path, summary)
    json.dump(summary, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
