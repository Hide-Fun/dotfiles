#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(ape)
  library(ggplot2)
  library(ggtree)
  library(readr)
  library(dplyr)
  library(tibble)
  library(stringr)
})

parse_args <- function(args) {
  parsed <- list()
  i <- 1
  while (i <= length(args)) {
    key <- args[[i]]
    if (!startsWith(key, "--")) {
      stop("Unexpected argument: ", key, call. = FALSE)
    }
    key <- sub("^--", "", key)
    if (i == length(args) || startsWith(args[[i + 1]], "--")) {
      parsed[[key]] <- TRUE
      i <- i + 1
    } else {
      parsed[[key]] <- args[[i + 1]]
      i <- i + 2
    }
  }
  parsed
}

value_or <- function(x, default) {
  if (is.null(x) || identical(x, "")) default else x
}

nice_scale_width <- function(x) {
  if (!is.finite(x) || x <= 0) {
    stop("x must be a positive finite number.", call. = FALSE)
  }

  exponent <- floor(log10(x))
  fraction <- x / (10 ^ exponent)

  nice_fraction <- if (fraction <= 1) {
    1
  } else if (fraction <= 2) {
    2
  } else if (fraction <= 5) {
    5
  } else {
    10
  }

  nice_fraction * (10 ^ exponent)
}

tree_total_width <- function(tree) {
  max(node.depth.edgelength(tree))
}

auto_treescale_width <- function(tree, ratio = 0.1) {
  if (!inherits(tree, "phylo")) {
    stop("tree must be a 'phylo' object.", call. = FALSE)
  }
  if (!is.finite(ratio) || ratio <= 0) {
    stop("treescale ratio must be a positive finite number.", call. = FALSE)
  }
  nice_scale_width(tree_total_width(tree) * ratio)
}

format_support_labels <- function(labels) {
  if (is.null(labels)) {
    return(NULL)
  }
  if (requireNamespace("ggbipartite", quietly = TRUE)) {
    return(ggbipartite::format_node_support(labels))
  }
  labels[is.na(labels)] <- ""
  labels
}

style_labels <- function(x) {
  normalized <- str_replace_all(x, "_([A-Z]{2,6})_", "(\\1)")
  if (requireNamespace("ggbipartite", quietly = TRUE)) {
    return(ggbipartite::style_tree_label(normalized, last_taxon_rank = "genus"))
  }
  normalized
}

read_query_ids <- function(path, metadata) {
  if (!is.null(path) && file.exists(path)) {
    ids <- readLines(path, warn = FALSE, encoding = "UTF-8")
    ids <- ids[nzchar(ids)]
    return(unique(ids))
  }
  if ("is_query" %in% names(metadata)) {
    return(metadata$tip_id[as.logical(metadata$is_query)])
  }
  character(0)
}

read_outgroup_ids <- function(path, metadata) {
  if (!is.null(path) && file.exists(path)) {
    ids <- readLines(path, warn = FALSE, encoding = "UTF-8")
    ids <- ids[nzchar(ids)]
    return(unique(ids))
  }
  if ("is_outgroup" %in% names(metadata)) {
    ids <- metadata$tip_id[as.logical(metadata$is_outgroup)]
    ids <- ids[!is.na(ids)]
    return(unique(ids))
  }
  if ("source" %in% names(metadata)) {
    ids <- metadata$tip_id[metadata$source == "outgroup"]
    ids <- ids[!is.na(ids)]
    return(unique(ids))
  }
  character(0)
}

read_metadata <- function(path, tree_tips) {
  if (is.null(path) || !file.exists(path)) {
    return(tibble(
      tip_id = tree_tips,
      display_label = tree_tips,
      source = "reference"
    ))
  }
  metadata <- read_tsv(path, show_col_types = FALSE)
  if (!"tip_id" %in% names(metadata)) {
    stop("Metadata must contain a tip_id column.", call. = FALSE)
  }
  if (!"display_label" %in% names(metadata)) {
    metadata$display_label <- metadata$tip_id
  }
  if (!"source" %in% names(metadata)) {
    metadata$source <- "reference"
  }
  metadata
}

focus_tree <- function(tree, query_ids, outgroup_ids, neighbors_per_query) {
  query_ids <- intersect(query_ids, tree$tip.label)
  outgroup_ids <- intersect(outgroup_ids, tree$tip.label)
  if (length(query_ids) == 0) {
    return(list(tree = tree, kept = tree$tip.label, mode = "full"))
  }
  if (length(query_ids) == length(tree$tip.label)) {
    return(list(tree = tree, kept = tree$tip.label, mode = "all-query"))
  }
  dist_mat <- cophenetic.phylo(tree)
  non_query <- setdiff(tree$tip.label, c(query_ids, outgroup_ids))
  keep <- unique(c(query_ids, outgroup_ids))
  for (q in query_ids) {
    candidates <- non_query[is.finite(dist_mat[q, non_query])]
    if (length(candidates) == 0) {
      next
    }
    ordered <- candidates[order(dist_mat[q, candidates], decreasing = FALSE)]
    keep <- unique(c(keep, head(ordered, neighbors_per_query)))
  }
  list(
    tree = keep.tip(tree, keep),
    kept = keep,
    mode = "nearest"
  )
}

args <- parse_args(commandArgs(trailingOnly = TRUE))

if (isTRUE(args[["help"]])) {
  cat(
    paste(
      c(
        "Usage:",
        "  Rscript focus_plot_tree.R --treefile PATH --out-prefix PREFIX [--metadata PATH] [--query-ids PATH] [--outgroup-ids PATH] [--focus-mode all|nearest] [--neighbors-per-query 15] [--width 11] [--height 8.5] [--font-family sans] [--treescale-ratio 0.1]"
      ),
      collapse = "\n"
    ),
    "\n",
    sep = ""
  )
  quit(save = "no", status = 0)
}

treefile <- value_or(args[["treefile"]], stop("Missing --treefile", call. = FALSE))
out_prefix <- value_or(args[["out-prefix"]], stop("Missing --out-prefix", call. = FALSE))
metadata_path <- value_or(args[["metadata"]], NULL)
query_ids_path <- value_or(args[["query-ids"]], NULL)
outgroup_ids_path <- value_or(args[["outgroup-ids"]], NULL)
focus_mode <- value_or(args[["focus-mode"]], "all")
neighbors_per_query <- as.integer(value_or(args[["neighbors-per-query"]], "15"))
plot_width <- as.numeric(value_or(args[["width"]], "11"))
plot_height <- as.numeric(value_or(args[["height"]], "8.5"))
font_family <- value_or(args[["font-family"]], "sans")
treescale_ratio <- as.numeric(value_or(args[["treescale-ratio"]], "0.1"))

if (!focus_mode %in% c("all", "nearest")) {
  stop("focus-mode must be one of: all, nearest", call. = FALSE)
}

tree <- read.tree(treefile)
metadata <- read_metadata(metadata_path, tree$tip.label)
if (anyDuplicated(metadata$tip_id)) {
  stop("Metadata contains duplicated tip_id values.", call. = FALSE)
}
query_ids <- read_query_ids(query_ids_path, metadata)
outgroup_ids <- read_outgroup_ids(outgroup_ids_path, metadata)

if (length(query_ids) == 0) {
  stop("No query IDs were provided. Supply --query-ids or metadata$is_query.", call. = FALSE)
}
if (length(outgroup_ids) != 2) {
  stop("Exactly 2 outgroup IDs are required. Supply --outgroup-ids or metadata source/is_outgroup.", call. = FALSE)
}
if (!all(outgroup_ids %in% tree$tip.label)) {
  stop("At least one outgroup ID is absent from the tree tip labels.", call. = FALSE)
}
if (any(outgroup_ids %in% query_ids)) {
  stop("Outgroup IDs must not overlap with query IDs.", call. = FALSE)
}

tree <- tryCatch(
  root(tree, outgroup = outgroup_ids, resolve.root = TRUE),
  error = function(e) {
    stop(
      "Failed to root tree with the 2 outgroups. Choose a pair that behaves as a monophyletic outgroup. Original error: ",
      conditionMessage(e),
      call. = FALSE
    )
  }
)

metadata <- metadata %>%
  distinct(tip_id, .keep_all = TRUE) %>%
  mutate(
    source = case_when(
      tip_id %in% query_ids ~ "query",
      tip_id %in% outgroup_ids ~ "outgroup",
      TRUE ~ source
    ),
    display_label = style_labels(display_label)
  )

missing_tips <- setdiff(tree$tip.label, metadata$tip_id)
if (length(missing_tips) > 0) {
  metadata <- bind_rows(
    metadata,
    tibble(
      tip_id = missing_tips,
      display_label = style_labels(missing_tips),
      source = case_when(
        missing_tips %in% query_ids ~ "query",
        missing_tips %in% outgroup_ids ~ "outgroup",
        TRUE ~ "reference"
      )
    )
  )
}

tree_plot <- tree
if (identical(focus_mode, "nearest")) {
  focused <- focus_tree(tree, query_ids, outgroup_ids, neighbors_per_query)
  tree_plot <- focused$tree
  missing_outgroups <- setdiff(outgroup_ids, tree_plot$tip.label)
  if (length(missing_outgroups) > 0) {
    stop(
      "Focused tree dropped required outgroup tip(s): ",
      paste(missing_outgroups, collapse = ", "),
      ". Focused trees must retain all query tips and both outgroup tips.",
      call. = FALSE
    )
  }
}
tree_plot$node.label <- format_support_labels(tree_plot$node.label)

plot_metadata <- metadata %>%
  filter(tip_id %in% tree_plot$tip.label) %>%
  mutate(
    source = case_when(
      source %in% c("query", "outgroup", "user_literature", "verified_mode", "unite", "genbank", "other") ~ source,
      TRUE ~ "other"
    ),
    point_group = case_when(
      source == "query" ~ "query",
      source == "outgroup" ~ "outgroup",
      TRUE ~ "reference"
    )
  )

source_palette <- c(
  query = "#B03A2E",
  outgroup = "#566573",
  user_literature = "#1F618D",
  verified_mode = "#148F77",
  unite = "#117A65",
  genbank = "#9A7D0A",
  other = "#5D6D7E"
)
fill_palette <- c(query = "#B03A2E", outgroup = "#566573", reference = "white")
treescale_width <- auto_treescale_width(tree_plot, ratio = treescale_ratio)
treescale_x <- tree_total_width(tree_plot) * 0.02
treescale_y <- 0.5
treescale_offset <- treescale_width * 0.25
support_nudge_x <- tree_total_width(tree_plot) * 0.01

base_tree <- ggtree(tree_plot) +
  scale_x_continuous(expand = expansion(mult = c(0.08, 0.55)))

if (requireNamespace("ggbipartite", quietly = TRUE)) {
  tree_plot_obj <- base_tree %<+% plot_metadata +
    ggbipartite::geom_tipmarquee(
      aes(label = display_label, color = source),
      align = TRUE,
      hjust = 0,
      linetype = "dotted",
      linesize = 0.35,
      size = 3.2,
      family = font_family
    )
} else {
  tree_plot_obj <- base_tree %<+% plot_metadata +
    geom_tiplab(
      aes(label = display_label, color = source),
      align = TRUE,
      hjust = 0,
      linetype = "dotted",
      linesize = 0.35,
      size = 3.2,
      family = font_family
    )
}

has_support_labels <- !is.null(tree_plot$node.label) &&
  any(nzchar(replace(tree_plot$node.label, is.na(tree_plot$node.label), "")))

if (has_support_labels) {
  if (requireNamespace("ggbipartite", quietly = TRUE)) {
    tree_plot_obj <- tree_plot_obj +
      ggbipartite::geom_nodemarquee(
        mapping = aes(label = label),
        nudge_x = support_nudge_x,
        hjust = 1,
        vjust = -0.4,
        size = 2.6,
        na.rm = TRUE
      )
  } else {
    tree_plot_obj <- tree_plot_obj +
      geom_text2(
        aes(subset = !isTip & !is.na(label) & nzchar(label), label = label),
        nudge_x = support_nudge_x,
        hjust = 1,
        vjust = -0.4,
        size = 2.6,
        family = font_family,
        na.rm = TRUE
      )
  }
}

tree_plot_obj <- tree_plot_obj +
  geom_tippoint(
    aes(fill = point_group),
    shape = 21,
    size = 2.2,
    stroke = 0.2,
    color = "black",
    show.legend = FALSE
  ) +
  scale_color_manual(values = source_palette, drop = FALSE) +
  scale_fill_manual(values = fill_palette, drop = FALSE) +
  guides(
    color = guide_legend(
      override.aes = list(label = "", linetype = 0, shape = 16, size = 3)
    ),
    fill = "none"
  ) +
  geom_treescale(
    x = treescale_x,
    y = treescale_y,
    width = treescale_width,
    offset = treescale_offset,
    offset.label = treescale_offset,
    linesize = 0.5,
    fontsize = 3.2,
    family = font_family
  ) +
  coord_cartesian(clip = "off") +
  theme_tree2() +
  theme(
    plot.margin = margin(5.5, 80, 5.5, 5.5),
    legend.position = "bottom",
    legend.title = element_blank(),
    axis.line.x = element_blank(),
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank(),
    axis.title.x = element_blank()
  )

out_prefix_path <- normalizePath(dirname(out_prefix), mustWork = FALSE)
dir.create(out_prefix_path, recursive = TRUE, showWarnings = FALSE)
pdf_path <- paste0(out_prefix, ".", focus_mode, ".pdf")
png_path <- paste0(out_prefix, ".", focus_mode, ".png")
tips_path <- paste0(out_prefix, ".", focus_mode, ".tips.tsv")

ggsave(pdf_path, tree_plot_obj, width = plot_width, height = plot_height, units = "in")
ggsave(png_path, tree_plot_obj, width = plot_width, height = plot_height, units = "in", dpi = 300)
write_tsv(
  plot_metadata %>%
    transmute(tip_id, display_label, source),
  tips_path
)

cat(
  paste(
    c(
      paste0("treefile\t", treefile),
      paste0("plot_pdf\t", pdf_path),
      paste0("plot_png\t", png_path),
      paste0("tips_tsv\t", tips_path),
      paste0("kept_tip_count\t", length(tree_plot$tip.label)),
      paste0("query_tip_count\t", length(intersect(query_ids, tree_plot$tip.label))),
      paste0("outgroup_ids\t", paste(outgroup_ids, collapse = ",")),
      paste0("treescale_width\t", treescale_width),
      paste0("treescale_ratio\t", treescale_ratio),
      paste0("rooted_with_outgroups\tTRUE")
    ),
    collapse = "\n"
  ),
  "\n",
  sep = ""
)
