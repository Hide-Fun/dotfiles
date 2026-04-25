#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)

usage <- function(status = 0) {
  cat(
    "Usage:\n",
    "  Rscript render_sciname_phylogeny.R --tree input.treefile --out output_stem [options]\n\n",
    "Options:\n",
    "  --tree PATH                    Input Newick or IQ-TREE .treefile\n",
    "  --out PATH                     Output stem or path; extension is replaced by --formats [required]\n",
    "  --formats LIST                 Comma-separated output formats [pdf,svg]\n",
    "  --outgroup LABEL               Optional exact tip label for ape::root()\n",
    "  --align TRUE|FALSE             Align tip labels with guide lines [FALSE]\n",
    "  --reverse TRUE|FALSE           Reverse x axis for right-side panels [FALSE]\n",
    "  --last-taxon-rank VALUE        last_taxon_rank for style_tree_label() [genus]\n",
    "  --sh-cutoff NUMBER             SH-aLRT threshold [80]\n",
    "  --boot-cutoff NUMBER           UFBoot threshold [95]\n",
    "  --single-value ufboot|sh_alrt  Meaning of one-value support labels [ufboot]\n",
    "  --missing-mark TEXT            Mark for failed support components [-]\n",
    "  --drop-accession-version TRUE|FALSE  Remove terminal accession version suffix [TRUE]\n",
    "  --font FAMILY                  Text family [Arial]\n",
    "  --label-size NUMBER            Tip label size [3.2]\n",
    "  --node-size NUMBER             Node label size [2.6]\n",
    "  --offset NUMBER                Tip label offset [0]\n",
    "  --left-expand NUMBER           Lower x-axis expansion; default depends on --reverse\n",
    "  --right-expand NUMBER          Upper x-axis expansion; default depends on --reverse\n",
    "  --treescale TRUE|FALSE         Add geom_treescale() below the tree [TRUE]\n",
    "  --treescale-width NUMBER|auto  Scale bar width; auto uses rounded tree span / 10 [auto]\n",
    "  --treescale-x NUMBER|auto      Scale bar x position [auto]\n",
    "  --treescale-y NUMBER           Scale bar y position [0]\n",
    "  --treescale-line-size NUMBER   Scale bar line size [0.5]\n",
    "  --treescale-font-size NUMBER   Scale bar font size [3.0]\n",
    "  --treescale-offset NUMBER      Vertical offset from bar to width label [0.35]\n",
    "  --width NUMBER                 Output width in inches [8]\n",
    "  --height NUMBER                Output height in inches [6]\n",
    "  --dpi NUMBER                   Raster DPI [300]\n",
    "  --label-preview PATH           Optional CSV of raw and styled tip labels\n",
    "  --help                         Show this help\n",
    sep = ""
  )
  quit(status = status)
}

parse_args <- function(x) {
  opts <- list()
  i <- 1
  while (i <= length(x)) {
    key <- x[[i]]
    if (key %in% c("-h", "--help")) {
      usage(0)
    }
    if (!startsWith(key, "--")) {
      stop("Unexpected argument: ", key, call. = FALSE)
    }
    name <- sub("^--", "", key)
    if (i == length(x) || startsWith(x[[i + 1]], "--")) {
      opts[[name]] <- TRUE
      i <- i + 1
    } else {
      opts[[name]] <- x[[i + 1]]
      i <- i + 2
    }
  }
  opts
}

get_opt <- function(opts, name, default = NULL) {
  value <- opts[[name]]
  if (is.null(value)) default else value
}

as_flag <- function(x, name) {
  if (is.logical(x)) return(x)
  value <- tolower(as.character(x))
  if (value %in% c("true", "t", "1", "yes", "y")) return(TRUE)
  if (value %in% c("false", "f", "0", "no", "n")) return(FALSE)
  stop("Option --", name, " must be TRUE or FALSE.", call. = FALSE)
}

as_number <- function(x, name) {
  value <- suppressWarnings(as.numeric(x))
  if (length(value) != 1 || is.na(value)) {
    stop("Option --", name, " must be numeric.", call. = FALSE)
  }
  value
}

as_number_or_auto <- function(x, name) {
  if (is.null(x)) return(NULL)
  value <- tolower(as.character(x))
  if (value %in% c("auto", "default", "null", "none")) return(NULL)
  as_number(x, name)
}

as_formats <- function(x, name) {
  allowed <- c(
    "png", "pdf", "svg", "eps", "ps", "tex", "jpeg", "jpg", "tiff", "bmp"
  )
  parts <- unlist(strsplit(tolower(as.character(x)), "[,[:space:]]+"))
  parts <- sub("^\\.", "", parts[nzchar(parts)])
  if (!length(parts)) {
    stop("Option --", name, " must contain at least one format.", call. = FALSE)
  }
  invalid <- setdiff(parts, allowed)
  if (length(invalid)) {
    stop(
      "Option --", name, " contains unsupported format(s): ",
      paste(invalid, collapse = ", "),
      call. = FALSE
    )
  }
  unique(parts)
}

require_package <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    stop("Required R package is not installed: ", pkg, call. = FALSE)
  }
}

tree_horizontal_span <- function(phy) {
  depths <- NULL
  if (!is.null(phy$edge.length) &&
      length(phy$edge.length) == nrow(phy$edge) &&
      all(is.finite(phy$edge.length))) {
    depths <- ape::node.depth.edgelength(phy)
  }
  if (is.null(depths) || any(!is.finite(depths))) {
    depths <- ape::node.depth(phy, method = 2)
  }
  finite_depths <- depths[is.finite(depths)]
  if (!length(finite_depths)) return(1)
  span <- diff(range(finite_depths))
  if (!is.finite(span) || span <= 0) 1 else span
}

rounded_treescale_width <- function(span) {
  target <- span / 10
  if (!is.finite(target) || target <= 0) return(1)
  signif(target, digits = 1)
}

output_paths <- function(out_path, formats) {
  out_ext <- tolower(tools::file_ext(out_path))
  out_stem <- out_path
  if (nzchar(out_ext)) {
    out_stem <- sub(paste0("\\.", out_ext, "$"), "", out_path, ignore.case = TRUE)
  }
  paste0(out_stem, ".", formats)
}

save_device_for_ext <- function(ext) {
  switch(
    ext,
    pdf = grDevices::cairo_pdf,
    svg = grDevices::svg,
    NULL
  )
}

if (!length(args)) usage(1)

opts <- parse_args(args)

tree_path <- get_opt(opts, "tree")
out_path <- get_opt(opts, "out")
if (is.null(tree_path) || is.null(out_path)) usage(1)
if (!file.exists(tree_path)) {
  stop("Tree file does not exist: ", tree_path, call. = FALSE)
}
formats <- as_formats(get_opt(opts, "formats", "pdf,svg"), "formats")

for (pkg in c("ape", "ggplot2", "ggtree", "marquee", "ggbipartite", "stringr")) {
  require_package(pkg)
}

align <- as_flag(get_opt(opts, "align", "FALSE"), "align")
reverse_axis <- as_flag(get_opt(opts, "reverse", "FALSE"), "reverse")
drop_accession_version <- as_flag(
  get_opt(opts, "drop-accession-version", "TRUE"),
  "drop-accession-version"
)

last_taxon_rank <- get_opt(opts, "last-taxon-rank", "genus")
if (identical(last_taxon_rank, "") || tolower(last_taxon_rank) == "none") {
  last_taxon_rank <- NA_character_
}

sh_cutoff <- as_number(get_opt(opts, "sh-cutoff", "80"), "sh-cutoff")
boot_cutoff <- as_number(get_opt(opts, "boot-cutoff", "95"), "boot-cutoff")
single_value <- get_opt(opts, "single-value", "ufboot")
if (!single_value %in% c("ufboot", "sh_alrt")) {
  stop("--single-value must be 'ufboot' or 'sh_alrt'.", call. = FALSE)
}

missing_mark <- get_opt(opts, "missing-mark", "-")
font <- get_opt(opts, "font", "Arial")
label_size <- as_number(get_opt(opts, "label-size", "3.2"), "label-size")
node_size <- as_number(get_opt(opts, "node-size", "2.6"), "node-size")
offset <- as_number(get_opt(opts, "offset", "0"), "offset")
width <- as_number(get_opt(opts, "width", "8"), "width")
height <- as_number(get_opt(opts, "height", "6"), "height")
dpi <- as_number(get_opt(opts, "dpi", "300"), "dpi")

left_default <- if (reverse_axis) "0.30" else "0"
right_default <- if (reverse_axis) "0" else "0.30"
left_expand <- as_number(get_opt(opts, "left-expand", left_default), "left-expand")
right_expand <- as_number(get_opt(opts, "right-expand", right_default), "right-expand")
treescale <- as_flag(get_opt(opts, "treescale", "TRUE"), "treescale")
treescale_width_user <- as_number_or_auto(
  get_opt(opts, "treescale-width", "auto"),
  "treescale-width"
)
treescale_x <- as_number_or_auto(get_opt(opts, "treescale-x", "auto"), "treescale-x")
treescale_y <- as_number(get_opt(opts, "treescale-y", "0"), "treescale-y")
treescale_line_size <- as_number(
  get_opt(opts, "treescale-line-size", "0.5"),
  "treescale-line-size"
)
treescale_font_size <- as_number(
  get_opt(opts, "treescale-font-size", "3.0"),
  "treescale-font-size"
)
treescale_offset <- as_number(
  get_opt(opts, "treescale-offset", "0.35"),
  "treescale-offset"
)

tree <- ape::read.tree(tree_path)
if (is.null(tree) || !inherits(tree, "phylo")) {
  stop("Input could not be read as an ape::phylo tree.", call. = FALSE)
}

outgroup <- get_opt(opts, "outgroup")
if (!is.null(outgroup)) {
  if (!outgroup %in% tree$tip.label) {
    stop(
      "--outgroup must exactly match one of the tree tip labels. Missing: ",
      outgroup,
      call. = FALSE
    )
  }
  tree <- ape::root(tree, outgroup = outgroup, resolve.root = TRUE)
}

tree_span <- tree_horizontal_span(tree)
treescale_width <- treescale_width_user
if (is.null(treescale_width)) {
  treescale_width <- rounded_treescale_width(tree_span)
}

tree_pretty <- tree
raw_tip_labels <- tree$tip.label
styled_tip_labels <- raw_tip_labels |>
  stringr::str_replace_all("_ORM_", "_(ORM)_")

if (drop_accession_version) {
  styled_tip_labels <- stringr::str_remove(styled_tip_labels, "\\.\\d+$")
}

styled_tip_labels <- ggbipartite::style_tree_label(
  styled_tip_labels,
  last_taxon_rank = last_taxon_rank
)
tree_pretty$tip.label <- styled_tip_labels

if (is.null(tree$node.label)) {
  tree_pretty$node.label <- rep("", tree$Nnode)
} else {
  tree_pretty$node.label <- ggbipartite::format_node_support(
    x = tree$node.label,
    sh_alrt_cutoff = sh_cutoff,
    boot_cutoff = boot_cutoff,
    missing_mark = missing_mark,
    single_value = single_value
  )
  tree_pretty$node.label[is.na(tree_pretty$node.label)] <- ""
}

label_preview <- data.frame(
  raw_label = raw_tip_labels,
  styled_label = styled_tip_labels,
  stringsAsFactors = FALSE
)

preview_path <- get_opt(opts, "label-preview")
if (!is.null(preview_path)) {
  utils::write.csv(label_preview, preview_path, row.names = FALSE)
}

tip_hjust <- if (reverse_axis) 1 else 0
node_hjust <- if (reverse_axis) 0 else 1

p <- ggtree::ggtree(tree_pretty) +
  ggbipartite::geom_tipmarquee(
    align = align,
    hjust = tip_hjust,
    linetype = "dotted",
    linesize = 0.35,
    size = label_size,
    family = font,
    offset = offset
  ) +
  ggbipartite::geom_nodemarquee(
    mapping = ggplot2::aes(label = label),
    hjust = node_hjust,
    vjust = -0.4,
    size = node_size,
    family = font
  ) +
  ggplot2::coord_cartesian(clip = "off")

if (treescale) {
  p <- p +
    ggtree::geom_treescale(
      x = treescale_x,
      y = treescale_y,
      width = treescale_width,
      offset = treescale_offset,
      linesize = treescale_line_size,
      fontsize = treescale_font_size,
      family = font
    )
}

scale_expand <- ggplot2::expansion(mult = c(left_expand, right_expand))
if (reverse_axis) {
  p <- p + ggplot2::scale_x_reverse(expand = scale_expand)
} else {
  p <- p + ggplot2::scale_x_continuous(expand = scale_expand)
}

for (path in output_paths(out_path, formats)) {
  out_dir <- dirname(path)
  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }

  out_ext <- tolower(tools::file_ext(path))
  ggplot2::ggsave(
    filename = path,
    plot = p,
    width = width,
    height = height,
    dpi = dpi,
    limitsize = FALSE,
    device = save_device_for_ext(out_ext)
  )

  message("Wrote: ", normalizePath(path, mustWork = FALSE))
}
if (treescale) {
  message(
    "Scale bar width: ",
    format(treescale_width, scientific = FALSE, trim = TRUE),
    " (tree horizontal span: ",
    format(tree_span, scientific = FALSE, trim = TRUE),
    ")"
  )
}
if (!is.null(preview_path)) {
  message("Wrote label preview: ", normalizePath(preview_path, mustWork = FALSE))
}
