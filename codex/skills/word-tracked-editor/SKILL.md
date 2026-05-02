---
name: word-tracked-editor
description: Edit local Microsoft Word OOXML documents with tracked changes while strictly protecting citation fields. Use when Codex is asked to inspect, revise, comment on, accept, reject, or validate tracked edits in `.docx`, `.docm`, `.dotx`, or `.dotm` files, especially when citation/content-control fields must remain untouched. Do not use for plain Word edits where revision metadata and citation protection do not matter.
---

# Word Tracked Editor

## Purpose

Use this skill to make or evaluate tracked edits in local Word OOXML documents without touching protected `citation` fields. Treat citation protection as a hard invariant, not a convenience preference.

This skill is deliberately conservative. If a requested edit cannot be made while preserving review metadata and protected citation content, stop and explain the exact blocker.

## Core Rules

1. Work local-only. Do not upload documents or call external services.
2. Support native OOXML formats: `.docx`, `.docm`, `.dotx`, `.dotm`.
3. Reject `.doc`, `.dot`, flat XML, and unknown formats unless the user explicitly approves a separate local conversion workflow.
4. Keep the source document untouched unless the user explicitly asks for replacement.
5. Create an edited copy by default, plus any review artifacts needed to verify the change.
6. Preserve existing revisions, comments, relationship IDs, macros, styles, numbering, headers, footers, and non-target package parts.
7. Never edit, comment on, accept, reject, format, delete, or replace content that overlaps a protected `citation` field.
8. Never use raw regex or string replacement over WordprocessingML XML for edits.
9. Prefer structured OOXML manipulation and the narrowest possible changed node span.
10. Validate both schema-level integrity and citation invariants before declaring success.

## Citation Protection

Treat a range as protected when any ancestor or overlapping structured document tag (`w:sdt`) indicates `citation` by:

- `w:tag` equal to `field:citation` or containing an equivalent citation field marker
- `w:alias` equal to `citation`
- `w:dataBinding` pointing to a citation node

Also treat known citation fields from Zotero, EndNote, Mendeley, Word bibliography fields, or repository templates as protected when detected. If detection is ambiguous, fail closed and ask the user to clarify or fix the template.

Before editing:

1. Inspect package XML for citation fields and content controls.
2. Resolve requested locators to concrete OOXML ranges.
3. Check for overlap with protected citation ranges.
4. Reject the operation with a clear `CitationProtected` explanation if any overlap exists.

After editing:

1. Re-scan protected ranges.
2. Compare normalized protected citation fragments or hashes against the pre-edit state.
3. Roll back or discard the edited copy if any citation text, markup, comment anchor, or revision markup changed.

## Workflow

### 1. Inspect

Inspect the document before modifying it:

- identify format and whether it is OOXML
- compute a document hash for conflict detection
- list existing revisions and comments
- locate protected citation/content-control spans
- identify macros, signatures, protection settings, and unsupported parts
- identify the smallest package part(s) needed for the requested edit

Use [references/implementation-spec.md](references/implementation-spec.md) when the request needs concrete API fields, error codes, or validation cases.

### 2. Decide Whether to Proceed

Proceed only if all are true:

- the file is an OOXML Word format
- the edit target can be resolved to stable anchors
- the target does not overlap protected citation spans
- unresolved existing revisions do not overlap the requested edit
- the user has accepted any known signature/protection/macro risks

Stop and ask for confirmation before editing a signed document, a protected document, a macro-enabled document where macro handling is unclear, or a file currently open in Word.

### 3. Edit With Tracked Changes

Represent revisions with WordprocessingML review markup:

- insertion: `w:ins` containing normal runs/text
- deletion: `w:del` containing deleted runs and `w:delText`
- replacement: adjacent deletion plus insertion
- run formatting: `w:rPrChange` with prior properties preserved
- paragraph formatting: `w:pPrChange` with prior properties preserved
- table formatting: `w:tblPrChange` with prior properties preserved
- comment: `comments.xml` plus matching `commentRangeStart`, `commentRangeEnd`, and `commentReference`

Use existing local revision patterns where possible. Do not invent broad rewrites of whole paragraphs when a narrower run-level edit is sufficient.

### 4. Validate

Before returning the result:

1. Confirm the edited package opens without repair prompts if local rendering/opening is available.
2. Verify that tracked changes and comments remain visibly reviewable in Word when Word verification is available.
3. Verify that protected citation fragments are byte-stable or semantically stable according to the pre-edit hash strategy.
4. Verify comments anchor to the intended range.
5. Verify no unrelated package parts changed except expected timestamps, relationship bookkeeping, or explicitly edited parts.
6. State any verification limits plainly.

## Error Policy

Use these names consistently in explanations and JSON-like status summaries:

- `UnsupportedFormat`: non-OOXML or unsupported extension
- `DocumentLocked`: file cannot be opened for exclusive edit
- `DocumentConflict`: current hash differs from the inspected hash
- `RangeResolutionFailed`: locator cannot be resolved
- `RevisionConflict`: requested edit overlaps unresolved existing revisions
- `CitationProtected`: requested operation overlaps protected citation content
- `ValidationFailed`: OOXML or semantic validation failed
- `SignedDocumentModificationDenied`: signature would be invalidated without explicit approval
- `ProtectedDocumentDenied`: document protection prevents a safe edit

## CLI Contract For Implementations

If a local implementation CLI exists, prefer commands shaped like:

```bash
word-tracked-editor inspect request.json
word-tracked-editor apply request.json
word-tracked-editor validate request.json
word-tracked-editor undo request.json
word-tracked-editor redo request.json
```

Expected request fields:

- `requestId`
- `command`
- `document.path`
- `document.expectedHash`
- `actor.displayName`
- `options.outputMode`
- `options.trackFormatting`
- `options.trackMoves`
- `options.preserveExistingRevisions`
- `operations`

No bundled CLI is required by this skill. If no implementation CLI is present in the repository or task context, use careful package-level OOXML editing only for narrow, verifiable changes; otherwise stop and explain that a deterministic implementation is needed.

## Reference

Read [references/implementation-spec.md](references/implementation-spec.md) when you need detailed request/response shapes, supported operations, edge cases, rollout checks, or a stricter test plan.
