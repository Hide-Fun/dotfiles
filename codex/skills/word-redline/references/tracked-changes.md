# Tracked Changes Guide

Use this reference when Word review metadata must survive the edit.

## Goal
Preserve native Microsoft Word revision markup instead of flattening changes into ordinary text.

## High-risk reminder
- A `.docx` can remain readable while tracked changes have already been flattened or made invisible.
- XML well-formedness, ZIP integrity, and plain-text extraction are not sufficient validation for review-history preservation.
- When review history matters, Word-side verification is part of the task, not an optional extra.

## Inspect first
1. Unpack the `.docx` package.
2. Find the real XML part that contains the target text.
3. Inspect the surrounding paragraph and run structure before editing.
4. Check whether the document already contains `w:ins`, `w:del`, comments, footnotes, citation fields, or other review-related sidecar parts.

## Elements to preserve
- `w:ins` for inserted content
- `w:del` for deleted content
- `w:commentRangeStart`, `w:commentRangeEnd`, and `w:commentReference` for comment anchors
- `w:author`, `w:date`, `w:id`, and similar revision metadata already present in the file
- `word/comments.xml` and related relationships when comments exist
- `word/settings.xml`, especially when the file already uses `w:trackRevisions`
- `w:fldChar`, `w:instrText`, and field result runs used by Zotero or other citation managers

## Safe editing rules
- Duplicate the original file before editing.
- Mirror the exact local XML pattern already used in the document.
- Edit the smallest possible XML region around the requested change.
- Preserve namespace declarations and relationship targets.
- When Codex creates a new tracked change or comment, set the author label to `Codex (<model-name>)`.
- Do not silently fall back to a plain `Codex` author label if the concrete model name is unavailable.
- Repack from the extracted DOCX root, not from its parent directory.
- Reopen the file after each meaningful revision and verify that the review markup still appears.
- Verify in Word with `Review -> All Markup` before concluding that tracked changes survived.
- If a change would touch a citation field, ask the user first. The default is to leave citation fields untouched.
- When the prose needs a new citation but citation fields should not be edited, use a placeholder such as `(ref)` or `XXXX et al.` and leave the final bibliographic insertion to the user.

## Common failure modes
- Replacing a whole paragraph and silently deleting `w:ins` or `w:del` wrappers
- Renumbering comment IDs without updating every reference
- Editing `word/document.xml` when the text really lives in a header, footer, footnote, or textbox
- Repacking the wrong directory level and producing a corrupt DOCX
- Saving through a toolchain that strips or normalizes review metadata
- Breaking a Zotero or other citation field by editing inside `w:instrText`, `w:fldChar`, or mismatched field-result runs
- Opening successfully in Word while revision history is no longer visible because markup was flattened or the file is being checked in the wrong display mode

## Decision rule
If you cannot explain how the proposed edit preserves the surrounding review markup and any nearby citation fields, stop and tell the user that the change is risky.
