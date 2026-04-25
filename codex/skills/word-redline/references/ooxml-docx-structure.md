# DOCX OOXML Structure

Use this reference before low-level edits to `.docx` files.

## Core package parts
- `[Content_Types].xml`
- `_rels/.rels`
- `word/document.xml`
- `word/_rels/document.xml.rels`
- `word/styles.xml`
- `word/settings.xml`

## Common sidecar parts
- `word/comments.xml` for comments
- `word/footnotes.xml` and `word/endnotes.xml` for note content
- `word/header*.xml` and `word/footer*.xml` for page furniture
- `word/numbering.xml` for list definitions
- `word/media/*` for embedded images

## Inspection checklist
1. Find the target text in the correct XML part.
2. Inspect nearby `w:p`, `w:r`, and `w:t` nodes.
3. Look for revision wrappers, comment anchors, bookmarks, or field-code runs nearby.
4. Check whether a related XML part also needs an update.
5. Repack only after confirming the extracted directory root contains `[Content_Types].xml`.

## Editing guidance
- Treat `.docx` as a ZIP package of coordinated XML parts.
- Preserve relative paths inside the archive.
- Avoid broad search-and-replace across the whole package.
- Prefer targeted XML edits around the affected content.
