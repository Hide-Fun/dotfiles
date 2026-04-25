# Curation Manifest Schema

Use this schema for `curation_manifest.tsv`, written during reference selection.

## File name

- Save as `curation_manifest.tsv` inside the curation directory for the run.

## Required columns

- `stable_id`: exact stable ID used in the combined FASTA and downstream metadata
- `source_class`: one of `query`, `outgroup`, `user_literature`, `verified_mode`, `unite`, `genbank`, or `other`
- `claimed_taxon`
- `retained_or_excluded`: must be `retained` or `excluded`
- `evidence_note`
- `citation_or_file`
- `rationale`
- `curator`
- `decision_date`

## Minimal example

```tsv
stable_id	source_class	claimed_taxon	retained_or_excluded	evidence_note	citation_or_file	rationale	curator	decision_date
otu_0001	query	Oidiodendron	retained	query sequence	ident_merged2.csv	carried forward as candidate	Hidefungi	2026-04-21
OID_AF062798	unite	Oidiodendron majus	retained	UNITE named reference	AF062798	retained as focal reference	Hidefungi	2026-04-21
OUT_AF062810	outgroup	Myxotrichum arcticum	excluded	non-monophyletic outgroup pair	AF062810	excluded after rooting failure	Hidefungi	2026-04-21
```

## Practical notes

- Record exclusions as well as retained references. Silent dropping weakens reproducibility.
- Do not collapse contradictory labels into a harmonized name without documenting that conflict in `evidence_note` or `rationale`.
- If outgroup choice changes after an initial plotting attempt, record both the rejected and retained decisions.
