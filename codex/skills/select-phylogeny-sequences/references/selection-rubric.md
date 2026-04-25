# Sequence Selection Rubric

## Candidate Evidence Fields

Capture one row per accession or sequence record. Preserve raw source wording in a notes/evidence column when possible.

Minimum fields:

- `accession`
- `organism`
- `marker`
- `length_bp`
- `source_database`
- `retrieval_date`
- `blast_identity`
- `blast_query_cover`
- `blast_evalue`
- `type_status`
- `unite_sh`
- `culture_collection`
- `voucher` or `specimen_voucher`
- `host`
- `publication_or_source`
- `rationale`
- `caveats`

## Tier Rules

### High reliability

Assign high reliability when at least one strong anchor is documented:

- type or type-derived material: holotype, isotype, lectotype, neotype, epitype, paratype, syntype, type specimen, ex-type, type strain, ex-type culture, authentic type-derived culture
- UNITE Species Hypothesis evidence: record maps to a UNITE SH identifier; record the SH identifier, UNITE version or DOI when available, and threshold if stated
- CBS/Westerdijk culture collection evidence: source qualifiers, strain fields, culture collection fields, or publication explicitly identify a CBS accession

Critical checks:

- A type-derived sequence can still be unusable if it is the wrong locus, too short, non-overlapping, contaminated, or taxonomically revised.
- A UNITE SH is a clustering/hypothesis anchor, not proof that the displayed species name is correct.
- CBS evidence is strong for traceability, but it does not by itself guarantee current taxonomy.

### Medium reliability and analytically necessary

Assign medium reliability when both conditions hold:

- BLAST indicates close relationship to the query for the same marker and with adequate alignment overlap.
- A persistent voucher, specimen voucher, herbarium number, non-CBS culture collection number, or comparable traceable material identifier is documented.

Use this tier for filling local clades around the query when high-reliability records are absent or sparse.

Critical checks:

- Do not count an isolate name alone as a voucher unless it is tied to a collection, herbarium, specimen, or publication with traceable material.
- Confirm the voucher metadata comes from source qualifiers or the publication, not only from the BLAST hit title.
- Inspect taxonomic consistency when close BLAST hits carry conflicting species names.

### Low reliability but analytically necessary

Assign low reliability when all conditions hold:

- BLAST indicates close relationship to the query.
- Species-level name is absent, unresolved, or generic, such as `sp.`, `cf.`, `aff.`, `uncultured`, `unidentified`, environmental clone, or host-associated endophyte/mycorrhizal label.
- Host is clearly documented in source qualifiers or publication metadata.

Use this tier only when it helps test placement, host association, or unsampled diversity. Do not use it as a nomenclatural or species-identity anchor.

## BLAST Closeness

Use marker-specific judgment. As a starting triage rule for nucleotide markers, require:

- same marker or clearly overlapping homologous region
- query coverage at least 80 percent
- identity at least 97 percent for ITS-like species-level searches, unless the user requests broader placement
- e-value strong enough to be effectively unambiguous for the query length

Relax thresholds only when the goal is broad placement or when the marker evolves slowly. Tighten thresholds for species-level delimitation. Always report the thresholds used.

## Inclusion Priorities

1. Include high-reliability anchors for the focal taxon and nearest named relatives.
2. Include medium-reliability close voucher-backed hits that stabilize the query's local placement.
3. Include a small number of low-reliability host-known close hits only if they test a biologically relevant alternative or fill an otherwise unsampled branch.
4. Include outgroups justified by previous taxonomy, literature, or broader BLAST placement.
5. Avoid redundant accessions from the same isolate/material unless there is a locus-length or quality reason.

## Exclusion And Caution Flags

Flag or exclude records with:

- very short sequence length or poor overlap with the alignment
- excessive ambiguous bases
- likely chimera or mixed-template signal
- source organism inconsistent with voucher, host, publication, or expected clade
- environmental sequence without voucher, host, or clear analytical value
- duplicate submissions from the same material when one representative is enough
- only a BLAST title as evidence for species identity

## Reporting Standard

The final answer should make the evidentiary hierarchy visible. A good selection table lets a reader audit why each sequence was included, which evidence source supports it, and what uncertainty remains. State explicitly when a record is included for topology testing rather than taxonomic naming.
