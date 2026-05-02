# Word Tracked Editor Implementation Spec

This reference distills the design requirements for a local Codex skill that edits Word OOXML documents with tracked changes while enforcing protected `citation` fields.

## Architecture

- Primary implementation: Open XML / WordprocessingML package editing.
- Avoid Office Interop as a default path because unattended Word automation is UI-dependent and fragile.
- Treat commercial document libraries as optional alternatives only when licensing and revision semantics are acceptable.
- Keep all document processing local.
- Do not implement external HTTP calls.

## Supported Formats

| Extension | Status | Notes |
|---|---|---|
| `.docx` | required | main target |
| Strict `.docx` | required read, test write-back | normalize to Transitional only if needed |
| `.docm` | required | preserve VBA parts; do not execute macros |
| `.dotx` | recommended | prefer new output rather than in-place overwrite |
| `.dotm` | recommended | preserve macros; do not execute |
| `.doc` / `.dot` | unsupported by default | require explicit local conversion workflow |
| flat Word XML | out of scope for v1 | separate utility only |

## Public Operations

| Operation | Requirement | OOXML representation |
|---|---|---|
| `insert_text` | required | `w:ins` with child runs |
| `delete_range` | required | `w:del` with `w:delText` |
| `replace_text` | required | deletion plus insertion |
| `apply_format` | required | `w:rPrChange`, `w:pPrChange`, or `w:tblPrChange` |
| `add_comment` | required | comments part plus comment anchors |
| `accept_changes` | required | remove accepted revision wrappers according to type |
| `reject_changes` | required | restore prior content/properties according to type |
| `move_block` | experimental | `moveFrom` / `moveTo`; default off |

## Request Shape

```json
{
  "requestId": "req-20260502-001",
  "command": "apply",
  "document": {
    "path": "docs/sample.docx",
    "expectedHash": "sha256:...",
    "formatHint": "docx"
  },
  "actor": {
    "displayName": "AI Editor",
    "machineUser": "researcher01"
  },
  "options": {
    "outputMode": "newfile",
    "trackFormatting": true,
    "trackMoves": false,
    "preserveExistingRevisions": true,
    "failOnProtectedFieldOverlap": true
  },
  "operations": []
}
```

`failOnProtectedFieldOverlap` is not a real option for callers to weaken; it must always behave as `true`.

## Locator Shape

Supported locator kinds:

- `contentControlTag`
- `bookmark`
- `nodePath`
- `textQuote`

Supported views:

- `final`
- `original`

Default part:

- `mainDocument`

For v1, write only to the main document body unless the implementation has explicit coverage for headers, footers, footnotes, endnotes, comments, text boxes, and DrawingML text.

## Citation Detection

Required structural checks:

- `w:sdtPr/w:tag` equals `field:citation`
- `w:sdtPr/w:alias` equals `citation`
- `w:sdtPr/w:dataBinding` points to a citation node
- known citation field constructs from Zotero, EndNote, Mendeley, or Word bibliography fields

Migration-only heuristics:

- table header named `citation`
- label `citation:` followed by a single paragraph or cell
- repository-specific template convention

If heuristic detection yields multiple plausible targets, fail closed instead of guessing.

## Revision Semantics

Preserve existing review metadata:

- keep existing revision IDs stable
- allocate new revision IDs from current maximum plus one
- preserve existing authors and dates
- preserve comments and anchor IDs outside the edited range
- preserve package parts unrelated to the edit

Fail closed when a normal edit overlaps unresolved revisions. Ask the user to accept/reject first, or perform an explicit revision operation.

## Validation

Schema validation:

- run the best available Open XML validator or package-level consistency checks
- treat repair prompts from Word/LibreOffice as failure

Semantic validation:

- protected citation fragments remain unchanged
- comment ranges start and end correctly
- `w:ins` / `w:del` wrappers are well nested
- deleted text uses `w:delText`
- formatting changes preserve prior properties in `*PrChange`
- existing macro and signature parts are not touched unless explicitly approved

## Concurrency And Rollback

- Prefer single-document, single-writer execution.
- Use exclusive file opening or a logical lock file where possible.
- Use `document.expectedHash` to detect stale edits.
- Write to a temp file, validate, then replace or deliver a separate output file.
- Keep a backup/history path before any in-place replacement.
- Implement undo as backup restoration, not Word UI undo.

## Error Codes

| Code | Meaning | Retryable |
|---|---|---|
| `UnsupportedFormat` | unsupported file type | no |
| `DocumentLocked` | exclusive edit unavailable | yes |
| `DocumentConflict` | expected hash mismatch | yes |
| `RangeResolutionFailed` | locator not resolved | conditional |
| `RevisionConflict` | unresolved revision overlap | conditional |
| `CitationProtected` | protected citation overlap | no |
| `ValidationFailed` | schema or semantic failure | conditional |
| `SignedDocumentModificationDenied` | signature would be invalidated | no |
| `ProtectedDocumentDenied` | document protection blocks safe edit | conditional |
| `InternalError` | unexpected implementation failure | conditional |

## Test Matrix

Unit tests:

- insertion creates `w:ins`
- deletion creates `w:del` and `w:delText`
- run formatting creates `w:rPrChange`
- paragraph formatting creates `w:pPrChange`
- table formatting creates `w:tblPrChange`
- comments create consistent IDs and anchors
- citation overlap returns `CitationProtected`
- split `w:t` text resolves correctly
- unresolved revision overlap returns `RevisionConflict`
- invalid OOXML is rejected

Integration tests:

- `.docx` replace plus comment opens in Word with visible markup
- `.docm` body edit preserves VBA parts
- Strict `.docx` can be read and written back safely
- tagged/locked citation SDTs reject all operations
- open file returns `DocumentLocked`
- failed validation preserves original file
- signed documents reject by default
- protected documents reject or require explicit override

End-to-end tests:

- inspect -> apply -> validate returns consistent hashes
- inspect -> apply -> undo -> redo preserves expected state
- 100-operation batch preserves revision and comment integrity
- research manuscript template edit leaves citation fields unchanged
- existing tracked changes remain visible after new edits
- edit over unresolved revision fails closed

## Rollout Checklist

- `SKILL.md` installed in an auto-discovered skill directory
- target templates use tagged/locked citation SDTs
- unsupported formats reject cleanly
- validation catches schema and citation mutation failures
- rollback/history is tested
- concurrency conflict detection is tested
- macro, signature, and protection policies are documented
- output verification states what was and was not verified
