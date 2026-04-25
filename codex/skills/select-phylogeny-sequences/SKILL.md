---
name: select-phylogeny-sequences
description: Select, verify, tier, and document nucleotide sequence records for phylogenetic inference from user-provided taxa or query sequences. Use when Codex needs to collect candidate GenBank/UNITE/CBS/voucher/host-associated records, run or interpret BLAST-neighbor searches, choose reliable ingroup/outgroup sequences, and produce a defensible sequence-selection table for taxonomy, fungal ITS/LSU/SSU/TEF/RPB phylogenies, or similar molecular systematics work.
---

# Select Phylogeny Sequences

## Core Workflow

1. Define scope before searching: focal taxon/taxa, marker region, query FASTA or accession, intended ingroup/outgroup, and whether the goal is species delimitation, placement, or broad context.
2. Use Life Science Research plugin skills as the default retrieval layer:
   - Use `life-science-research:ncbi-blast-skill` for query-neighbor discovery.
   - Use `life-science-research:ncbi-entrez-skill` for GenBank Nucleotide metadata, FASTA/XML fetches, publications, and source qualifiers.
   - Use `life-science-research:ncbi-datasets-skill` only when assembly/BioSample context is needed.
   - Use `life-science-research:research-router-skill` when the request mixes literature, taxonomy, datasets, and sequence retrieval.
3. Build a candidate table. Always record accession, organism, marker, length, source database, retrieval date, BLAST metrics if applicable, voucher/culture/host fields, and the exact evidence supporting the tier.
4. Assign reliability tiers using `references/selection-rubric.md`. Do not treat a BLAST title or species label alone as reliable evidence.
5. Prefer a balanced final set: type/UNITE/CBS anchors first, close voucher-backed BLAST neighbors next, host-known unnamed neighbors only when analytically necessary, plus explicit outgroups.
6. Report exclusions and caveats. Flag short, non-overlapping, duplicate, chimeric, environmental-only, or taxonomically inconsistent records rather than silently dropping them.

## Reliability Tiers

- High reliability: type-derived material, UNITE Species Hypothesis match, or CBS/Westerdijk culture collection evidence.
- Medium reliability and analytically needed: close BLAST neighbor to the query and a specimen voucher, culture collection, or comparable persistent voucher is documented.
- Low reliability but analytically needed: close BLAST neighbor to the query, species name unresolved or absent, but host is clearly documented.

Use high-reliability records as taxonomic anchors even when they are not the closest BLAST hits, but verify marker identity and alignment overlap. Use low-reliability records only to test placement, host association, or unsampled diversity; never use them as nomenclatural anchors.

## Output Contract

Return a concise table plus a short critical synthesis. Include these columns when possible:

`include`, `tier`, `accession`, `organism`, `marker`, `length_bp`, `blast_identity`, `blast_query_cover`, `type_or_ex_type`, `unite_sh`, `culture_collection`, `voucher`, `host`, `source`, `rationale`, `caveats`.

After the table, state:

- why the selected set is sufficient for the user's phylogenetic goal
- which records are weak or only included for analytical coverage
- which taxa or evidence classes remain missing
- whether additional BLAST/UNITE/CBS/literature checks are needed before inference

## Bundled Resources

- Read `references/selection-rubric.md` when applying the tier rules, resolving ambiguous metadata, or drafting the final table.
- Use `scripts/score_candidates.py` after a candidate CSV/TSV is assembled to add first-pass tier, decision, and evidence-flag columns. Treat its output as triage, not as the final authority.
