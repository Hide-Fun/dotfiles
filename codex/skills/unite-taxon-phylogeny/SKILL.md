---
name: unite-taxon-phylogeny
description: Screen whether query fungal ITS sequences may belong to a specified taxon using a local UNITE SH release, BLAST thresholds, literature-backed named references, ecology-aware curation, phylogenetic inference, and ggtree visualization. Use when Codex needs to build a BLAST database from sh_general_release_dynamic FASTA files, recover candidate query sequences with pident above 90 and qcov above 90, add named outgroup pairs, collect SH and non-SH accessions from user literature, retain ErM, EcM, and OrM comparison lineages when relevant, choose MAFFT plus trimAl plus IQ-TREE or PRANK plus IQ-TREE based on sequence count, and render full plus focused trees with species-forward, ecology-tagged labels plus a verified legend.
---

# UNITE Taxon Phylogeny

## Operating rules

- Confirm or ask for these four inputs before starting:
  - query FASTA path
  - target taxon name
  - `sh_general_release_dynamic*.fasta` path
  - trusted source directory or file paths, including PDFs and supplementary files
- Treat the BLAST screen as a recall-oriented filter, not as final taxonomic identification.
- Keep query sequences, user-provided references, UNITE SH references, and GenBank references distinguishable in metadata from the start.
- Use exactly 2 named outgroup sequences. Do not use unnamed public records as outgroups.
- If the chosen outgroup pair is not monophyletic after tree inference, stop, revise outgroup choice, and rerun. Do not silently fall back to unnamed outgroups.
- If the user provides literature, extract accession numbers from the main text, figures, and supplementary files and retrieve those accession sequences instead of relying only on SH representatives.
- Prefer fewer high-confidence references over many redundant or weakly annotated records, but do not undersample relevant ErM, EcM, or OrM comparison lineages when they are available and biologically relevant.
- Use species-forward labels for named references and outgroups. For unresolved taxa, use `Genus sp.` rather than pretending to have species-level certainty.
- When `ecology_mode` is defensible, include it directly in `display_label` as a compact suffix such as `[EcM]`, `[ErM]`, `[OrM]`, `[endophyte]`, or `[unknown]`. Do not leave ecology information only in a metadata column.
- Do not accept a plotted result until the exported PDF or PNG has a visible, non-clipped legend whose entries match the actual `source` categories shown in the tree.
- State clearly when the result is unresolved because support is low, references conflict, or the marker lacks resolution.
- If the current plotting script fails to show the legend correctly or drops required label information, treat that as an unfinished workflow and fix the plotting inputs or script before delivering the result.

## Required tools

- Local executables: `makeblastdb`, `blastn`, `mafft`, `trimAl`, `prank`, `iqtree3`, `Rscript`
- R packages for plotting: `ape`, `ggtree`, `ggplot2`, `treeio`, `readr`, `dplyr`, `tibble`
- Optional but recommended R packages for label styling: `ggbipartite`, `marquee`

## Workflow

### 1. Screen query sequences with a local UNITE SH BLAST database

- Use `python scripts/local_unite_taxon_screen.py`.
- This script:
  - builds a nucleotide BLAST database from the supplied UNITE SH FASTA if needed
  - runs `blastn` against the query FASTA
  - keeps hits whose subject label contains the target taxon string and passes `pident > 90` and `qcov > 90`
  - writes candidate query IDs, candidate query FASTA, all filtered hits, and a summary JSON

Example:

```bash
python scripts/local_unite_taxon_screen.py \
  --query-fasta data/query.fasta \
  --unite-fasta data/sh_general_release_dynamic_19.02.2025_dev.fasta \
  --taxon "Hyaloscypha" \
  --outdir results/blast_screen
```

### 2. Curate reference sequences critically

- Start from the candidate query FASTA and retrieve references for the target clade, plausible sister clades, and ecology-relevant comparison lineages.
- Load `references/source-priority.md` before deciding what to keep.
- Extract accession numbers from user-provided literature, including figure labels and supplementary files.
- When the literature provides a GenBank or INSDC accession, retrieve that accession sequence directly and keep it distinguishable from any matching UNITE SH representative.
- Select exactly 2 outgroup sequences during curation.
- Choose outgroups from outside the focal candidate clade but close enough to stabilize rooting and interpretation.
- Outgroups must be named sequences. First try named sequences from user literature or GenBank; second try named sequences from UNITE.
- The 2 outgroups must be suitable for rooting as a pair; if they are not treated as a monophyletic outgroup in the inferred tree, stop, revise outgroup choice, and rerun.
- Prefer this evidence order:
  - user-provided literature with explicit voucher or culture linkage
  - sequences tied to experimentally verified nutritional mode
  - UNITE SH representatives with stable taxonomy
  - GenBank accessions with voucher, isolate, or publication support
- When relevant to the focal taxon, retain named ErM, EcM, and OrM references intentionally rather than keeping only the nearest BLAST hits. Aim for at least 2 named representatives per relevant ecology mode when trusted sources make that possible.
- Within Sebacinales-focused work, prioritize named anchors such as `Sebacina incrustans`, `Helvellosebacina`, `Serendipita "vermifera"`, and, when available in trusted sources, `Serendipita indica` and `Serendipita williamsii`.
- Keep plausible sister taxa and alternative named placements, not only the currently favored focal name, so the tree can falsify the working hypothesis.
- Use the Life Science Research plugin when NCBI retrieval is needed:
  - `research-router-skill` for ambiguous retrieval plans
  - `ncbi-entrez-skill` for nucleotide, PubMed, or taxonomy searches
  - `ncbi-datasets-skill` for assembly or taxonomy metadata when needed
  - `ncbi-blast-skill` only when remote BLAST is preferable to local screening
- Do not collapse contradictory reference labels into a single taxon without noting the conflict.
- Mark the 2 outgroups explicitly in metadata as `source = outgroup`, or save them in an `outgroup_ids.txt` file.

### 3. Build the phylogeny

- Combine candidate queries and curated references into one FASTA.
- Use `python scripts/build_phylogeny.py`.
- The script sanitizes FASTA headers to their first whitespace-delimited token before alignment, so use stable unique IDs there.
- Decision rule:
  - sequence count `>= 50`: `mafft --auto` -> `trimAl -automated1` -> `iqtree3`
  - sequence count `< 50`: `prank -showall -DNA` -> `iqtree3`

Example:

```bash
python scripts/build_phylogeny.py \
  --input-fasta results/combined.fasta \
  --outdir results/phylogeny \
  --threads 8
```

- The script writes a manifest JSON describing the chosen strategy, key artifact paths, and the final treefile.

### 4. Prepare metadata for plotting

- Create a TSV matching `references/metadata-schema.md`.
- At minimum, include:
  - `tip_id`
  - `display_label`
  - `source`
- Mark every query explicitly, either with a `query_ids.txt` file or an `is_query` column in metadata.
- Mark exactly 2 tips as outgroups, either with an `outgroup_ids.txt` file or with `source = outgroup` in metadata.
- For named references and outgroups, use species-forward labels such as `Genus species accession [EcM]` or `Genus sp. accession [unknown]` when ecology is relevant or known.
- For query tips, use `query_id + inferred taxon + ecology tag` so the original query identity and ecological interpretation remain visible.
- Include `ecology_mode` whenever it can be defended from the source material, and propagate it into `display_label` rather than storing it only as a separate column.

### 5. Plot full and focused trees with ggtree

- Use `Rscript scripts/focus_plot_tree.R`.
- The plotting script:
  - requires exactly 2 outgroup IDs and roots the tree with them before plotting
  - renders a full tree
  - optionally renders a focused tree that keeps all query tips, the 2 outgroup tips, and the nearest non-query neighbors per query tip
  - adds `geom_treescale()` with width auto-calculated from the rooted tree width, using about 1/10 of total width rounded to a nice scale value
  - formats and displays branch support labels in the style of the cited ggbipartite vignette
  - styles labels in the spirit of the cited ggbipartite vignette at `https://hide-fun.github.io/viz_cophylo/ggbipartite-sciname-tree-ja.html`
- Use the full tree as the primary basis for interpretation. The focus view is only a readability aid and must not override the full tree.
- The standard label style for named references and outgroups is species-first, with accession or stable ID retained after the taxon name and ecology tags appended when defensible.
- Check the exported figure itself, not only the code path. A correct run still fails the workflow if the legend is absent, clipped, duplicated, or inconsistent with the plotted tip colors.
- Prefer legends that show only categories actually present in the plotted dataset, in a stable order, so the figure remains readable after focused pruning.

Example:

```bash
Rscript scripts/focus_plot_tree.R \
  --treefile results/phylogeny/iqtree/analysis.treefile \
  --metadata results/combined_metadata.tsv \
  --query-ids results/blast_screen/candidate_query_ids.txt \
  --outgroup-ids results/curation/outgroup_ids.txt \
  --out-prefix results/plots/hyaloscypha \
  --focus-mode nearest \
  --neighbors-per-query 15
```

## Interpretation checklist

- Are the query sequences monophyletic or at least concentrated within the focal taxon?
- Are the closest non-query neighbors consistent with the claimed taxon, or do they support an alternative explanation?
- Are the supporting references high-confidence, or are they mostly self-referential GenBank labels?
- Do named literature-backed references and SH-only references support the same placement, or do they point to different interpretations?
- Are the 2 outgroups outside the focal clade and suitable for stable rooting, rather than arbitrarily distant or mislabeled?
- Are the key internal branches supported strongly enough after applying fixed support thresholds, rather than relying on unsupported topology?
- Does the nutritional mode claim come from direct evidence, or is it inferred only from taxonomy?
- Is ecology-mode sampling balanced enough that ErM, EcM, or OrM enrichment is not just an artifact of the reference panel?
- Are short or gap-heavy query sequences shifting position across reasonable reference sets or sensitivity analyses?
- Does pruning change the apparent conclusion? If yes, rely on the full tree first.

## Failure modes to surface explicitly

- BLAST recall can miss divergent but relevant references when the taxon name is absent from subject labels.
- `pident > 90` and `qcov > 90` are heuristic thresholds, not validation thresholds.
- Dense near-duplicate references can make a taxon appear more stable than it is.
- A named outgroup pair may be unavailable or may fail to behave as a monophyletic outgroup.
- Literature may mention relevant taxa but omit retrievable accession numbers, forcing heavier reliance on SH representatives.
- Ecology-mode sampling can be imbalanced and distort apparent stability within Sebacinaceae or Serendipitaceae.
- Short ITS fragments can leave query sequences with more than 50% gaps or ambiguity after alignment, making placements unstable.
- A single-marker ITS tree may be insufficient for species-level claims in difficult groups.
- Public database labels can lag behind current taxonomy or propagate earlier misidentifications.

## References

- Load `references/source-priority.md` when curating references.
- Load `references/metadata-schema.md` when preparing the metadata TSV for plotting.
