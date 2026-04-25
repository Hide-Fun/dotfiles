# Run Manifest Schema

Use this schema for the run-level manifest saved in the run output directory.

## File names

- Primary path: `run_manifest.json`
- Backward-compatible alias from step 1: `summary.json`

Both files should contain the same payload unless a future workflow deliberately separates them.

## Required fields

- `run_id`: stable identifier for the run; use the dedicated run directory name when possible
- `query_fasta_path`
- `query_fasta_sha256`
- `unite_fasta_path`
- `unite_fasta_sha256`
- `target_taxon`
- `tool_versions`
- `command_lines`
- `output_paths`

## Required screening fields

- `blast_task`
- `max_target_seqs`
- `threads`
- `pident_gt`
- `qcov_gt`

## Recommended additional fields

- `created_at`
- `database_prefix`
- `database_built`
- `command_line`
- `candidate_query_count`
- `matched_hit_count`

## Minimum `tool_versions` object

```json
{
  "script": "0.2.0",
  "makeblastdb": "makeblastdb: 2.x.x+",
  "blastn": "blastn: 2.x.x+"
}
```

## Minimum `command_lines` object

```json
{
  "driver": "python scripts/local_unite_taxon_screen.py ...",
  "makeblastdb": "makeblastdb ...",
  "blastn": "blastn ..."
}
```

## Minimum `output_paths` object

```json
{
  "database_prefix": "results/run_001/blast_screen/blastdb/unite_sh",
  "db_fingerprint_json": "results/run_001/blast_screen/blastdb/unite_sh.fingerprint.json",
  "blast_tsv": "results/run_001/blast_screen/blast.tsv",
  "candidate_hits_tsv": "results/run_001/blast_screen/candidate_hits.tsv",
  "candidate_query_ids": "results/run_001/blast_screen/candidate_query_ids.txt",
  "candidate_queries_fasta": "results/run_001/blast_screen/candidate_queries.fasta",
  "summary_json": "results/run_001/blast_screen/summary.json",
  "run_manifest_json": "results/run_001/blast_screen/run_manifest.json"
}
```

## Practical notes

- Treat the manifest as part of the scientific audit trail, not as disposable logging.
- Do not reuse the same outdir for a new run. Create a new run directory and therefore a new `run_id`.
- If the BLAST database is reused, the manifest must still record the current UNITE FASTA path and SHA256.
