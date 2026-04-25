# Project Conventions

## Observed Repo Facts

- `_quarto.yml` already sets `bibliography: references.bib`.
- `book.chapters` includes `index.qmd`, `chp1.qmd` ... `chp8.qmd`, and `reference.qmd`.
- `comps/*.qmd` exists, but these files are not part of the Quarto book chapter list.
- `reference.qmd` is currently only a placeholder and does not contain a real bibliography.
- `references.bib` already contains many author-year style keys such as `bidartondo2003`, `jacquemyn2019`, and `merckx2024`.

## Known Anti-Patterns In This Repo

- Inline author-year citations remain in prose, for example `Leake (2005)` or `(Taylor and Bruns 1997; McKendrick et al. 2002)`.
- Several chapters still end with manual `References` / `参考文献` sections.
- Some manual reference lists are translated, abbreviated, or explicitly truncated, so they cannot be treated as ground truth without checking.
- Existing Quarto citations already appear in some chapters, so partial migration has already started.

## Safe Defaults

- Default target set: files listed in `_quarto.yml` under `book.chapters`.
- Default bibliography file: the path declared by `bibliography:` in `_quarto.yml`; in this repo, `references.bib`.
- Default behavior: skip `comps/*.qmd` unless the user explicitly asks for project-wide cleanup beyond the published book.
- Default citekey style: reuse existing keys when possible; otherwise prefer a stable `lead-author + year` form unless the project already dictates a different key.

## High-Risk Cases

- References that have no DOI and only translated titles.
- References where the manual list includes `...`, `【要確認】`, or other signs of incompleteness.
- Same-author same-year collisions that require `a`, `b`, etc.
- Citations embedded in figure captions, footnotes, or translated parenthetical glosses where naive regex replacement can damage prose.

## Recommended Review Questions

- Does the chosen BibTeX entry actually match the cited claim, or only the same author-year signature?
- Is the reference already present under a different citekey in `references.bib`?
- After deleting the manual reference block, does the chapter still render the bibliography in the expected place?
- Did the rewrite preserve narrative vs parenthetical citation style?
