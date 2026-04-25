# Source Priority

Use this file when selecting reference sequences or interpreting conflicts.

## Priority order

1. User-provided literature-backed named sequences with voucher, culture, specimen, or isolate linkage
2. Named sequences tied to experimentally verified nutritional mode or host association
3. UNITE representatives or well-supported SH members linked to stable named taxa
4. GenBank named records with voucher or publication support
5. Unnamed public records used only as contextual in-group references, never as outgroups

## Critical checks

- Check whether the name is current or merely inherited from older annotations.
- If the literature provides an accession, retrieve that accession sequence directly instead of substituting only an SH representative.
- Prefer one representative per redundant near-identical cluster unless within-clade sampling is biologically necessary.
- Keep sister taxa and plausible alternatives, not only the focal taxon, so the tree can falsify the working hypothesis.
- Select exactly 2 outgroup sequences and record why they are suitable as outgroups rather than focal references.
- Outgroups must be named sequences.
- Prefer a pair that is expected to behave as a monophyletic outgroup relative to the focal clade; otherwise rooting will be unstable or fail.
- If the first outgroup pair fails monophyly in the inferred tree, stop, revise the pair, and rerun. Do not fall back to unnamed public records.
- When relevant to the focal taxon, retain named ErM, EcM, and OrM representatives intentionally so ecology-mode sampling is not distorted by BLAST proximity alone.
- Separate direct evidence from inferred evidence. A sequence from an ericoid root sample is not automatically an ericoid mycorrhizal symbiont.
- If multiple sources disagree, keep the disagreement visible in metadata rather than silently harmonizing labels.
- If ecology evidence is part of the interpretation, keep it visible in the plotted `display_label`; do not hide it only in `ecology_mode`.

## Minimum metadata to retain per reference

- accession or stable sequence ID
- claimed taxon
- source class: `user_literature`, `verified_mode`, `unite`, `genbank`, or `other`
- `ecology_mode`: `ErM`, `EcM`, `OrM`, `endophyte`, or `unknown`
- `name_status`: `named` or `unresolved`
- if used as an outgroup, record `source = outgroup` and note the justification
- evidence note
- citation or file path
- a `display_label` that preserves the defensible ecology tag used in the figure

## What not to do

- Do not trust a GenBank label merely because it matches the working hypothesis.
- Do not let BLAST top hits determine the final reference panel without phylogenetic context.
- Do not overpopulate a single subclade while undersampling competing lineages.
- Do not use unnamed public records as outgroups.
- Do not replace retrievable literature accessions with SH representatives when the accession sequence itself can be obtained.
