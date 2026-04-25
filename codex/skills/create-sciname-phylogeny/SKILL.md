---
name: create-sciname-phylogeny
description: Create publication-ready phylogenetic tree figures from Newick, IQ-TREE .treefile, or ape::phylo inputs, with scientific-name tip labels, Markdown italics, node support filtering, aligned or unaligned labels, clipping control, lower geom_treescale scale bars, and optional reversed tree panels. Use when Codex needs to plot or adapt R/ggtree/ggbipartite workflows for readable phylogenetic trees with scientific names, mycobiont-style labels, accession suffix cleanup, SH-aLRT/UFBoot support labels, scale bars, or cophylogeny side panels.
---

# Create Scientific-Name Phylogeny

## Overview

Use this skill to turn an already inferred phylogeny into a readable figure. Do not infer evolutionary relationships from scientific names alone; ask for sequence/alignment/model context or use a separate phylogeny-inference workflow if the user has not provided a tree.

## Quick Start

For a standard Newick or IQ-TREE `.treefile`, first save the exact script used for rendering into the project, then run that project-local script and visually inspect the rendered output:

```bash
mkdir -p scripts
skill_script=/path/to/create-sciname-phylogeny/scripts/render_sciname_phylogeny.R
project_script=scripts/render_sciname_phylogeny.R
if [ ! -e "$project_script" ] || cmp -s "$skill_script" "$project_script"; then
  cp "$skill_script" "$project_script"
  run_script="$project_script"
else
  run_script="scripts/render_sciname_phylogeny.codex-$(date +%Y%m%d-%H%M%S).R"
  cp "$skill_script" "$run_script"
fi
Rscript "$run_script" \
  --tree path/to/tree.treefile \
  --out path/to/tree \
  --sh-cutoff 80 \
  --boot-cutoff 95
```

By default the script writes both `path/to/tree.pdf` and `path/to/tree.svg`. Add `--align TRUE` only when aligned tip labels and guide lines are specifically requested. Add `--outgroup "Tip_label"` only when the outgroup is biologically justified. Add `--reverse TRUE` for a right-side cophylogeny panel whose labels extend to the left.

## Workflow

1. Confirm the input represents a real inferred tree: Newick, `.treefile`, or an in-memory `ape::phylo`. If only taxon names are provided, state that this is not enough for a defensible phylogeny.
2. Save the rendering script used for the run into the project before execution. Resolve the bundled script as `scripts/render_sciname_phylogeny.R` relative to this skill directory, create project `scripts/` if needed, and save an exact copy there. If `scripts/render_sciname_phylogeny.R` already exists and is identical, reuse it. If it exists and differs, do not overwrite it silently; save the bundled script under a distinct timestamped project-local name such as `scripts/render_sciname_phylogeny.codex-YYYYMMDD-HHMMSS.R` and run that exact saved copy. Report which project-local script was used.
3. Check rooting assumptions before changing the tree. Treat rerooting and outgroup choice as biological/model assumptions, not cosmetic layout choices.
4. Normalize tip labels before plotting: restore `_ORM_` to `_(ORM)_` when relevant, remove terminal accession version suffixes only if they are visual clutter, and keep a raw-to-styled label preview.
5. Format labels with `ggbipartite::style_tree_label()` for mixed tree labels or `ggbipartite::style_sciname()` for pure scientific names.
6. Format node support with fixed thresholds, usually `format_node_support(sh_alrt_cutoff = 80, boot_cutoff = 95)`, so figures remain comparable.
7. Draw labels with `geom_tipmarquee()` and `geom_nodemarquee()` so Markdown italics render correctly. Tip labels are not aligned by default; set `--align TRUE` only when the user explicitly wants aligned labels and dotted guide lines.
8. Prevent clipping with the smallest sufficient x-axis expansion, plus `coord_cartesian(clip = "off")`. Start from modest values such as `scale_x_continuous(expand = expansion(mult = c(0, 0.30)))` for normal trees or `scale_x_reverse(expand = expansion(mult = c(0.30, 0)))` for reversed panels, then tune only as far as needed for the longest labels.
9. Add a lower scale bar with `ggtree::geom_treescale()`. Set its width to a rounded value close to one tenth of the tree body's horizontal branch-length span; the script's `--treescale-width auto` does this with one significant digit.
10. Open the rendered image every time and visually inspect it. Do not treat a successful `Rscript` or `ggsave()` run as sufficient validation.
11. If any tip label is clipped, truncated, or too close to the figure edge, increase the label-side expansion (`--right-expand` for normal trees, `--left-expand` for reversed trees), rerender, and inspect again. If labels fit with broad empty x-axis space, decrease the expansion and rerender; the accepted value must be necessary and sufficient, not merely conservative.
12. Check the lower scale bar position against the tree body. If it overlaps branches, labels, or the plot edge, adjust `--treescale-y`, `--treescale-x`, output height, or label expansion, then rerender and inspect again.
13. Verify the final image: all tip labels are fully visible, the scale bar is readable and unobtrusive, node supports are interpretable, italics rendered, optional alignment lines are not visually dominant, and root orientation is documented.

## Script

Use the project-local saved script for repeatable rendering. The bundled script lives at `scripts/render_sciname_phylogeny.R` inside this skill directory, but each run must save the exact script used into the current project before execution. The script reads a tree file, optionally roots it by outgroup, styles tip and node labels, and writes PDF plus SVG by default. PDF output uses `grDevices::cairo_pdf`; SVG output uses `grDevices::svg`. Use `--formats` to request other formats.

Common options:

- `--tree`: input Newick or `.treefile`.
- `--out`: output stem or path; the extension is replaced by `--formats`.
- `--formats pdf,svg`: comma-separated output formats. Default is `pdf,svg`.
- `--outgroup`: optional exact tip label to use with `ape::root()`.
- `--reverse TRUE`: reverse the x axis for a right-side panel.
- `--align TRUE`: opt in to aligned tip labels with dotted guide lines. Default is `FALSE`.
- `--last-taxon-rank genus`: help parse labels such as `mycobiont_of_..._Psathyrella`.
- `--sh-cutoff 80 --boot-cutoff 95`: support display thresholds.
- `--missing-mark -`: replacement mark when one support component fails its threshold.
- `--drop-accession-version TRUE`: remove terminal accession version suffixes such as `.1`.
- `--right-expand 0.30`: starting point for normal left-to-right trees; increase only when labels are clipped or too close to the edge.
- `--left-expand 0.30 --right-expand 0`: starting point for reversed panels; increase only when labels are clipped or too close to the edge.
- `--treescale TRUE`: add a lower `geom_treescale()` bar.
- `--treescale-width auto`: use a rounded value close to one tenth of the tree horizontal span.
- `--treescale-y 0`: move the scale bar vertically when it overlaps the tree body or plot edge.

## Reference

Read `references/ggbipartite-sciname-tree.md` when adapting code by hand, debugging label parsing, tuning support thresholds, preventing label clipping, or building reversed cophylogeny panels.

## Critical Checks

- Do not present a label-styled tree as newly inferred phylogenetic evidence; this workflow is visualization and annotation.
- Save the exact rendering script used for the run inside the project before running it, and report the project-local path in the final answer.
- Always perform a visual check of the exported figure before reporting completion; tip-label clipping is a common failure mode.
- Do not leave x-axis whitespace simply as a safety buffer. Distinguish true plot expansion from branch-length geometry: expansion should be just enough to show labels, while long branches should only be altered when the user explicitly accepts a non-branch-length layout or another biologically justified transformation.
- Always inspect the lower `geom_treescale()` bar; its default position may need adjustment after label expansion, reversing, or changes in figure height.
- Do not reroot without an explicit outgroup or node rationale.
- Be cautious with support labels after rerooting because node order and interpretation can change.
- Verify whether one-value support labels should be interpreted as UFBoot or SH-aLRT before applying thresholds.
- Keep raw labels available in a preview table or sidecar file so styling errors remain auditable.
- Export PDF and SVG unless the user requests otherwise. Use `cairo_pdf` for PDF and `svg` for SVG, not an implicit device guess.
