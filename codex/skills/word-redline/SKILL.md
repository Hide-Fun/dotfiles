---
name: word-redline
description: Use when Codex needs to (1) edit Microsoft Word `.docx` documents with tracked changes preserved and visibly reviewable in Word, and/or (2) generate lossy Markdown sidecars for mechanical git diff review of DOCX changes. Do not use this skill for ordinary Word editing when revision metadata does not matter.
---

# Word Redline

## Overview
Handle Microsoft Word documents for two narrow purposes only:
1. Edit `.docx` files while preserving tracked changes and keeping those revisions visibly reviewable in Word.
2. Generate lossy Markdown sidecars so DOCX edits can be inspected with mechanical git diffs.

## Expected artifacts
1. Keep the input `.docx` as the untouched source.
2. Produce one edited `.docx` copy such as `revised.docx`.
3. Produce one Markdown snapshot for the input `.docx`.
4. Produce one Markdown snapshot for the revised `.docx`.
5. Treat those three generated artifacts as the default deliverable set for this skill: revised `.docx`, input Markdown, and revised Markdown.

## Scope
1. In scope: tracked-change-preserving edits to existing `.docx` files.
2. In scope: one Markdown snapshot for the input `.docx` and one Markdown snapshot for the revised `.docx`.
3. Out of scope: general Word authoring, ordinary clean-file edits, or layout polish workflows where review metadata is irrelevant.

## Critical warning
1. Tracked changes can disappear silently even when the `.docx` still opens and the visible text looks correct.
2. Never treat a successful open, XML validation, or plain-text extraction as proof that revision history survived.
3. If review metadata matters, default to revision-preserving mode and verify the result in Word with `Review -> All Markup` before declaring success.
4. If Word-side verification is not possible, state clearly that revision-history preservation is unverified.

## Optional local tooling
- The skill must remain usable without extra tools. Raw ZIP and XML inspection is the fallback path.
- Prefer `python-docx` only for snapshot extraction helpers or carefully bounded inspection tasks, not for rewriting tracked-change documents.
- Prefer `lxml` for narrow OOXML edits when available.
- Prefer `soffice` for `docx -> pdf` rendering when visual layout checks matter. On macOS, use `/Applications/LibreOffice.app/Contents/MacOS/soffice` if `soffice` is not on `PATH`.
- If these tools are unavailable, continue with package-level editing and explain the verification limits.
- Do not use `python-docx`, `textutil`, or other convenience tools to rewrite the source document when tracked changes must survive unless you can explain why revision markup will remain intact.

## Git-friendly diff snapshots
1. Before editing a `.docx`, create a lossy Markdown snapshot for the input file with `python3 scripts/docx_to_markdown.py input.docx --output input.snapshot.md`. On macOS this snapshot prefers `textutil` for consistent plain-text extraction.
2. Commit the input Markdown snapshot before the Word edit if you want a clean before/after git diff.
3. Edit the `.docx` into a separate revised copy such as `revised.docx`. Do not overwrite the input file unless the user explicitly asks for that.
4. Create a second Markdown snapshot for the revised file with `python3 scripts/docx_to_markdown.py revised.docx --output revised.snapshot.md`.
5. Review changes by diffing the two Markdown snapshots.
6. Treat the Markdown snapshots as review artifacts only. The `.docx` files remain the source of truth.
7. If `python-docx` is unavailable, use a coarse fallback such as `textutil -convert txt -stdout input.docx > input.snapshot.md`.
8. Do not infer that tracked changes survived just because the Markdown snapshots look correct. The snapshots are lossy and may hide or flatten review markup completely.

## Operating rule
1. Treat every source `.docx` as revision-sensitive unless the user explicitly says tracked changes do not matter.
2. If the task cannot be completed while keeping tracked changes visibly reviewable in Word, stop and say so.
3. Never silently downgrade to a plain edit path.

## Revision author label
1. Any new tracked change or comment authored by Codex must use the label `Codex (<model-name>)` in Word review metadata.
2. Prefer the concrete runtime model identifier when it is available.
3. If the runtime does not expose the model name, stop and ask the user for the label to use rather than silently writing a plain `Codex` author name.
4. Use `python3 scripts/docx_package.py author-label --model-name <model-name>` to generate the exact label when you need a deterministic helper.

## Handle citation fields conservatively
1. Inspect the file for Zotero, EndNote, Mendeley, or other citation fields before editing discussion text, methods text, or any paragraph that may contain references.
2. If a requested change would require touching a citation field or field-coded reference, ask the user first whether citation fields may be edited.
3. Default to not editing citation fields unless the user explicitly approves it.
4. If citation fields are off-limits, edit only the surrounding plain text and leave the field structure untouched.
5. If a revised sentence needs a citation that is not already present, insert a placeholder such as `(ref)` or `XXXX et al.` instead of inventing a concrete citation. The user is responsible for filling the final reference.

## Use confirmation templates
1. Use [references/confirmation-prompts.md](references/confirmation-prompts.md) when you need user confirmation before a risky Word edit.
2. Prefer short, concrete questions that state the exact risk and the default action.
3. When the safe default is to stop, say that explicitly.

## Prepare the working copy
1. Duplicate the source `.docx` before modifying it.
2. Keep one untouched original until the user approves cleanup.
3. Name or place the revised `.docx` so it is clearly distinct from the source file.
4. Generate and keep both Markdown snapshots: one from the source `.docx`, one from the revised `.docx`.
5. Render or inspect the document before editing when layout fidelity matters.
6. Record the target paragraphs, tables, comment ranges, and any citation fields before changing anything.

## Use revision-preserving mode
1. Read [references/tracked-changes.md](references/tracked-changes.md) before editing.
2. Unpack the document package with `python3 scripts/docx_package.py unpack input.docx --output-dir tmp/docx_pkg`.
3. Inspect the smallest XML part that contains the target content before changing it.
4. Mirror the local WordprocessingML pattern already present in the file instead of inventing a new revision structure.
5. Preserve existing `w:ins`, `w:del`, comment anchors, IDs, author fields, timestamps, relationship targets, and citation-field boundaries.
6. For any new `w:ins`, `w:del`, or comment authored by Codex, set the author metadata to `Codex (<model-name>)` rather than reusing another person's name.
7. If the exact model name is not available, stop and get it before writing new review metadata.
8. Edit the narrowest possible XML span. Avoid replacing whole paragraphs or large XML blocks unless the file already uses that pattern.
9. If a requested revision crosses a citation field boundary, stop and ask whether citation fields may be touched.
10. Repack the document with `python3 scripts/docx_package.py pack tmp/docx_pkg --output-docx output.docx`.
11. Reopen and verify that tracked changes and comments are still visible in Word, preferably with `Review -> All Markup` and the Reviewing Pane enabled.
12. If the file opens but revision markup is missing, treat that as a failure, revert to the untouched original, and explain what likely flattened the history.
13. Stop and explain the risk before using a fallback path that may flatten revision metadata.

## Validate the result
1. Confirm that the file opens without repair prompts.
2. Confirm that tracked changes remain visible when they should, not just present in XML.
3. Confirm that comments still point to the intended text.
4. Confirm in Word that new changes created by Codex display the expected author label `Codex (<model-name>)`.
5. Confirm that headers, footers, tables, numbering, cross-references, and citation fields were not damaged by the edit.
6. Confirm in Word that the display mode is `All Markup` before concluding that revisions disappeared.
7. Re-render if visual layout matters.

## Use the bundled resources
- Use [scripts/docx_package.py](scripts/docx_package.py) to unpack, list, and repack DOCX packages without re-writing zip logic each time.
- Use `python3 scripts/docx_package.py author-label --model-name <model-name>` to generate the required Codex revision author label.
- Use [scripts/docx_to_markdown.py](scripts/docx_to_markdown.py) to create deterministic Markdown sidecars for git diff review before and after Word edits.
- Use [references/confirmation-prompts.md](references/confirmation-prompts.md) for short user-facing confirmation templates before risky edits.
- Use [references/tracked-changes.md](references/tracked-changes.md) for revision-markup rules and common failure modes.
- Use [references/ooxml-docx-structure.md](references/ooxml-docx-structure.md) to decide which package parts to inspect before editing.
