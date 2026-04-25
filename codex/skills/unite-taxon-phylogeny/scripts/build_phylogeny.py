#!/usr/bin/env python3
"""Run an alignment and IQ-TREE workflow chosen by sequence count."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a phylogeny with MAFFT+trimAl+IQ-TREE for larger inputs or PRANK+IQ-TREE for smaller inputs."
    )
    parser.add_argument("--input-fasta", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--seed", type=int, default=100)
    parser.add_argument("--mafft", default="mafft")
    parser.add_argument("--trimal", default="trimAl")
    parser.add_argument("--prank", default="prank")
    parser.add_argument("--iqtree", default="iqtree3")
    return parser.parse_args()


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
                header = line[1:]
                chunks = []
            else:
                chunks.append(line)
    if header is not None:
        records.append((header, "".join(chunks)))
    return records


def sanitize_fasta_headers(input_fasta: Path, output_fasta: Path) -> list[str]:
    seen: set[str] = set()
    sanitized_ids: list[str] = []
    records = parse_fasta(input_fasta)
    with output_fasta.open("w", encoding="utf-8") as handle:
        for raw_header, sequence in records:
            seq_id = raw_header.split()[0]
            if not seq_id:
                raise SystemExit(f"Encountered an empty FASTA identifier in: {input_fasta}")
            if seq_id in seen:
                raise SystemExit(
                    f"Duplicate FASTA identifier after sanitization: {seq_id}. "
                    "Use unique first tokens in every FASTA header."
                )
            seen.add(seq_id)
            sanitized_ids.append(seq_id)
            handle.write(f">{seq_id}\n")
            for i in range(0, len(sequence), 80):
                handle.write(sequence[i : i + 80] + "\n")
    return sanitized_ids


def count_sequences(path: Path) -> int:
    count = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.startswith(">"):
                count += 1
    return count


def run(cmd: list[str], cwd: Path | None = None, stdout_path: Path | None = None) -> None:
    try:
        if stdout_path is None:
            subprocess.run(cmd, check=True, cwd=cwd)
            return
        with stdout_path.open("w", encoding="utf-8") as handle:
            subprocess.run(cmd, check=True, cwd=cwd, stdout=handle)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Command failed: {' '.join(cmd)}") from exc


def main() -> int:
    args = parse_args()
    input_fasta = args.input_fasta.resolve()
    if not input_fasta.exists():
        raise SystemExit(f"Input FASTA not found: {input_fasta}")

    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    sanitized_input = outdir / "input.sanitized.fasta"
    sanitized_ids = sanitize_fasta_headers(input_fasta, sanitized_input)
    seq_count = count_sequences(sanitized_input)
    if seq_count < 3:
        raise SystemExit("At least 3 sequences are required for phylogenetic inference.")

    alignment_dir = outdir / "alignment"
    alignment_dir.mkdir(exist_ok=True)
    iqtree_dir = outdir / "iqtree"
    iqtree_dir.mkdir(exist_ok=True)

    if seq_count >= 50:
        aligned_fasta = alignment_dir / "analysis.mafft.fasta"
        trimmed_fasta = alignment_dir / "analysis.mafft.trimmed.fasta"
        run(
            [args.mafft, "--auto", "--thread", str(args.threads), str(sanitized_input)],
            stdout_path=aligned_fasta,
        )
        run([args.trimal, "-in", str(aligned_fasta), "-out", str(trimmed_fasta), "-automated1"])
        analysis_input = trimmed_fasta
        strategy = "mafft-trimal-iqtree3"
    else:
        prank_prefix = alignment_dir / "analysis"
        run([args.prank, f"-d={sanitized_input}", f"-o={prank_prefix}", "-showall", "-DNA"])
        analysis_input = Path(f"{prank_prefix}.best.fas")
        strategy = "prank-iqtree3"
        if not analysis_input.exists():
            raise SystemExit(f"PRANK output not found: {analysis_input}")

    iqtree_prefix = iqtree_dir / "analysis"
    run(
        [
            args.iqtree,
            "-s",
            str(analysis_input),
            "-m",
            "MFP",
            "-merit",
            "BIC",
            "-nt",
            "AUTO",
            "-ntmax",
            str(args.threads),
            "-seed",
            str(args.seed),
            "-alrt",
            "1000",
            "-bb",
            "1000",
            "-pre",
            str(iqtree_prefix),
            "-redo",
        ]
    )

    manifest = {
        "ok": True,
        "sequence_count": seq_count,
        "strategy": strategy,
        "input_fasta": str(input_fasta),
        "sanitized_input_fasta": str(sanitized_input),
        "sanitized_ids": sanitized_ids,
        "analysis_input": str(analysis_input),
        "iqtree_prefix": str(iqtree_prefix),
        "treefile": str(Path(f"{iqtree_prefix}.treefile")),
        "contree": str(Path(f"{iqtree_prefix}.contree")),
        "iqtree_report": str(Path(f"{iqtree_prefix}.iqtree")),
        "log": str(Path(f"{iqtree_prefix}.log")),
    }
    manifest_path = outdir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    json.dump(manifest, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
