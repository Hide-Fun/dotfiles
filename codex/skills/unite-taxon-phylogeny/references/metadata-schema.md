# Metadata Schema

Use this schema for the TSV consumed by `scripts/focus_plot_tree.R`.

## Required columns

- `tip_id`: exact tip ID in the FASTA and tree
- `display_label`: label shown in the figure; include ecology tags when defensible
- `source`: one of `query`, `outgroup`, `user_literature`, `verified_mode`, `unite`, `genbank`, `other`

## Optional columns

- `is_query`: `TRUE` or `FALSE`; used when no external query ID file is supplied
- `is_outgroup`: `TRUE` or `FALSE`; used when no external outgroup ID file is supplied
- `claimed_taxon`: asserted name used during curation
- `evidence_note`: short provenance note
- `citation`: literature key, DOI, accession, or file path
- `ecology_mode`: one of `ErM`, `EcM`, `OrM`, `endophyte`, or `unknown`
- `name_status`: `named` or `unresolved`

## Minimal example

```tsv
tip_id	display_label	source	is_query	claimed_taxon	evidence_note	ecology_mode	name_status
q001	q001 Hyaloscypha sp. [unknown]	query	TRUE	Hyaloscypha sp.	query sequence	unknown	unresolved
OUT001	Tulasnella helicospora UDB0373541 [unknown]	outgroup	FALSE	Tulasnella helicospora	named outgroup selected for stable rooting	unknown	named
UDB12345	Hyaloscypha hepaticicola OR123456 [ErM]	genbank	FALSE	Hyaloscypha hepaticicola	voucher-backed GenBank record	ErM	named
OR123456	Hyaloscypha sp. OR123456 [unknown]	unite	FALSE	Hyaloscypha sp.	UNITE representative without defensible species name	unknown	unresolved
```

## Practical notes

- `tip_id` must stay unchanged across FASTA, alignment, and tree inference.
- `scripts/build_phylogeny.py` keeps only the first whitespace-delimited token from each FASTA header, so place the stable ID first.
- Keep `display_label` human-readable, but dense enough to preserve both taxonomic and ecological interpretation in the figure.
- For named references and outgroups, prefer `Genus species accession [EcM]` or `Genus sp. accession [unknown]`.
- For query tips, prefer `query_id + inferred taxon + ecology tag` so the original query provenance stays visible.
- If `ecology_mode` is known or explicitly relevant, propagate it into `display_label` as `[ErM]`, `[EcM]`, `[OrM]`, `[endophyte]`, or `[unknown]`.
- Supply exactly 2 outgroup IDs, either via `source = outgroup`, `is_outgroup = TRUE`, or an external `outgroup_ids.txt`.
- The plotting step assumes those 2 IDs can serve as a monophyletic outgroup pair for rooting.
- Outgroups should be named taxa rather than anonymous environmental records.
- Use the most specific defensible `claimed_taxon`: species name first, otherwise genus-level `Genus sp.`, otherwise the nearest higher-rank name that can be defended.
- If a record belongs to multiple evidence classes, prefer the most defensible one and document the rest in `evidence_note`.
