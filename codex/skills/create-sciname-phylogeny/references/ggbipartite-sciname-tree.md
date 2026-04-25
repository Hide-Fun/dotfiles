# ggbipartite Scientific-Name Tree Pattern

Source: https://hide-fun.github.io/viz_cophylo/ggbipartite-sciname-tree-ja.html

Use this reference when adapting the bundled script or writing custom R code with `ape`, `ggtree`, `marquee`, and `ggbipartite`.

## Required R Packages

```r
library(tidyverse)
library(ape)
library(ggtree)
library(marquee)
library(ggbipartite)
```

Core functions:

- `style_tree_label()`: style mixed tree labels, including scientific names and project-specific tokens.
- `style_sciname()`: style scientific names only.
- `format_node_support()`: filter and format support labels.
- `geom_tipmarquee()`: render Markdown tip labels.
- `geom_nodemarquee()`: render Markdown node labels.
- `geom_treescale()`: add a branch-length scale bar.

## Label Preparation

Normalize labels before plotting:

```r
tree_pretty <- tree_rooted
tree_pretty$tip.label <- tree_rooted$tip.label |>
  stringr::str_replace_all("_ORM_", "_(ORM)_") |>
  stringr::str_remove("\\.1$") |>
  ggbipartite::style_tree_label(last_taxon_rank = "genus")
```

For custom handling, convert to a tibble, mutate `label`, then convert back:

```r
tree_pretty <- ape::read.tree("path/to/your_tree.treefile") |>
  tidytree::as_tibble() |>
  dplyr::mutate(
    label = stringr::str_replace_all(.data$label, "_ORM_", "_(ORM)_"),
    label = stringr::str_remove(.data$label, "\\.1$"),
    label = dplyr::case_when(
      stringr::str_detect(.data$label, "mycobiont") ~
        ggbipartite::style_tree_label(.data$label),
      stringr::str_detect(
        .data$label,
        "^\\d+(?:\\.\\d+)?/\\d+(?:\\.\\d+)?$"
      ) ~ .data$label,
      .default = ggbipartite::style_sciname(.data$label)
    )
  ) |>
  tidytree::as.phylo()
```

## Node Support

Use fixed thresholds for figure-to-figure comparability:

```r
tree_pretty$node.label <- ggbipartite::format_node_support(
  x = tree_rooted$node.label,
  sh_alrt_cutoff = 80,
  boot_cutoff = 95
)
```

Interpretation details:

- Two-value labels such as `90/94` are treated as `SH-aLRT/UFBoot`.
- Values below threshold become `missing_mark`.
- If both values fail, the label becomes empty.
- One-value labels require an explicit `single_value = "ufboot"` or `"sh_alrt"` decision.
- `keep_na = TRUE` preserves missing labels.

## Standard Left-to-Right Plot

```r
base_tree <- ggtree::ggtree(tree_pretty) +
  ggplot2::scale_x_continuous(
    expand = ggplot2::expansion(mult = c(0, 0.30))
  )

p <- base_tree +
  ggbipartite::geom_tipmarquee(
    align = FALSE,
    hjust = 0,
    linetype = "dotted",
    linesize = 0.35,
    size = 3.2,
    family = "Arial"
  ) +
  ggbipartite::geom_nodemarquee(
    mapping = ggplot2::aes(label = label),
    hjust = 1,
    vjust = -0.4,
    size = 2.6
  ) +
  ggplot2::coord_cartesian(clip = "off")
```

## Clipping Control

Long labels need x-axis expansion, not only `plot.margin`:

```r
ggtree::ggtree(tree_pretty) +
  ggbipartite::geom_tipmarquee(align = FALSE, hjust = 0) +
  ggplot2::scale_x_continuous(
    expand = ggplot2::expansion(mult = c(0, right_expand))
  ) +
  ggplot2::coord_cartesian(clip = "off")
```

After each render, open the exported image and inspect all label edges. Do not rely on the absence of R warnings or errors: tip labels can be clipped even when `ggsave()` succeeds. Tune the label-side expansion in small steps and keep the smallest value that prevents clipping:

- Normal left-to-right tree: tune the second value in `expansion(mult = c(0, right_expand))`.
- Reversed tree: tune the first value in `expansion(mult = c(left_expand, 0))`.
- If labels still collide or crowd the edge, reduce `size`, increase `width`, or shorten nonessential accession text only after preserving a raw-to-styled label preview.
- If labels already fit and x-axis whitespace is broad, decrease the expansion and rerender. Broad expansion is not a valid substitute for visual checking.

## Lower Scale Bar

Add a scale bar under the tree with `ggtree::geom_treescale()`. Choose a bar width close to one tenth of the tree body's horizontal span, then round it to a readable value. With branch lengths:

```r
tree_span <- diff(range(ape::node.depth.edgelength(tree_pretty)))
scale_width <- signif(tree_span / 10, digits = 1)

p <- p +
  ggtree::geom_treescale(
    y = 0,
    width = scale_width,
    offset = 0.35,
    linesize = 0.5,
    fontsize = 3,
    family = "Arial"
  )
```

If the tree has no usable branch lengths, use `ape::node.depth(tree_pretty, method = 2)` as a fallback span; be explicit that the scale then reflects plotting depth rather than molecular distance.

Always open the exported figure after adding the scale bar. Check that the bar sits below the tree body, the numeric width label is legible, and the bar does not collide with branches, support labels, tip labels, or the plot edge. Adjust `y`, `x`, output height, and label-side expansion, then rerender until the placement is visually acceptable.

## Saving

Export PDF and SVG by default for manuscript and editing workflows. Use explicit devices so output is reproducible across environments:

```r
ggplot2::ggsave(
  "tree.pdf",
  p,
  width = 8,
  height = 6,
  device = grDevices::cairo_pdf
)

ggplot2::ggsave(
  "tree.svg",
  p,
  width = 8,
  height = 6,
  device = grDevices::svg
)
```

## Reversed Panel

Use this for a right-side panel where labels extend leftward:

```r
ggtree::ggtree(tree_pretty) +
  ggbipartite::geom_tipmarquee(
    align = FALSE,
    hjust = 1,
    linetype = "dotted",
    linesize = 0.35,
    size = 3.2,
    family = "Arial"
  ) +
  ggbipartite::geom_nodemarquee(
    mapping = ggplot2::aes(label = label),
    hjust = 0,
    vjust = -0.4,
    size = 2.6
  ) +
  ggplot2::coord_cartesian(clip = "off") +
  ggplot2::scale_x_reverse(
    expand = ggplot2::expansion(mult = c(0.30, 0))
  )
```

## Validation Points

- Check that scientific names are italicized, while qualifiers such as `cf.` and support values remain plain.
- Confirm that tip-label alignment is off unless aligned labels were explicitly requested.
- Open the output image every time and confirm that no tip label is clipped at the left or right edge.
- Confirm that x-axis expansion is necessary and sufficient: lower it when labels fit with unnecessary empty space.
- Confirm that the lower `geom_treescale()` bar is visible, readable, and not overlapping the tree body.
- Confirm that the scale-bar width is a rounded value close to one tenth of the tree's horizontal branch-length span.
- If any label is clipped, increase the label-side expansion before changing plot margins.
- Preview raw and styled labels before exporting.
- Confirm whether `mycobiont_of_...` labels should use `last_taxon_rank = "genus"` or another rank.
- Treat rooting as an analytic decision, not a plotting tweak.
- Document support thresholds in captions or figure notes.
