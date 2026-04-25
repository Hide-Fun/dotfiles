#!/usr/bin/env python3
"""Create a deterministic, lossy Markdown snapshot from a DOCX for git diff review."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

try:
    from docx import Document
    from docx.document import Document as DocxDocument
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph
except ModuleNotFoundError:
    print(
        '[ERROR] python-docx is not installed. Install `python-docx` or use a coarse fallback such as `textutil -convert txt -stdout input.docx > snapshot.md`.',
        file=sys.stderr,
    )
    raise SystemExit(1)

LOSSY_NOTICE = (
    '<!-- Lossy git-diff snapshot. Source of truth: DOCX. '
    'This file is for review and commit diffs only. -->'
)


def fail(message: str) -> None:
    print(f'[ERROR] {message}', file=sys.stderr)
    raise SystemExit(1)


def normalize_text(text: str) -> str:
    text = text.replace('\xa0', ' ')
    text = text.replace('\r', '\n')
    text = text.replace('\v', '\n')
    text = text.replace('\f', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' *\n *', ' <br> ', text)
    return text.strip()


def parse_heading_level(style_name: str) -> int | None:
    match = re.search(r'(\d+)', style_name)
    if not match:
        return None
    level = int(match.group(1))
    return max(1, min(level, 6))


def render_paragraph(paragraph: Paragraph) -> list[str]:
    text = normalize_text(paragraph.text)
    if not text:
        return []

    style_name = paragraph.style.name if paragraph.style is not None else ''
    style_lower = style_name.lower()

    if style_lower == 'title':
        return [f'# {text}']
    if 'subtitle' in style_lower:
        return [f'## {text}']
    if style_lower.startswith('heading'):
        level = parse_heading_level(style_name) or 2
        return [f"{'#' * level} {text}"]
    if style_lower.startswith('list bullet'):
        return [f'- {text}']
    if style_lower.startswith('list number'):
        return [f'1. {text}']

    return [text]


def cell_text(cell) -> str:
    parts = []
    for paragraph in cell.paragraphs:
        text = normalize_text(paragraph.text)
        if text:
            parts.append(text)
    return ' <br> '.join(parts)


def escape_pipe(text: str) -> str:
    return text.replace('|', '\\|')


def render_table(table: Table) -> list[str]:
    rows = []
    for row in table.rows:
        cells = [escape_pipe(cell_text(cell)) for cell in row.cells]
        rows.append(cells)

    if not rows:
        return []

    max_cols = max(len(row) for row in rows)
    padded_rows = [row + [''] * (max_cols - len(row)) for row in rows]
    header = padded_rows[0]
    separator = ['---'] * max_cols

    lines = [
        '| ' + ' | '.join(header) + ' |',
        '| ' + ' | '.join(separator) + ' |',
    ]
    for row in padded_rows[1:]:
        lines.append('| ' + ' | '.join(row) + ' |')
    return lines


def iter_block_items(document: DocxDocument):
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def document_has_tracked_markup(docx_path: Path) -> bool:
    with zipfile.ZipFile(docx_path) as archive:
        names = set(archive.namelist())
        document_xml = archive.read('word/document.xml').decode('utf-8', errors='ignore')
        settings_xml = ''
        if 'word/settings.xml' in names:
            settings_xml = archive.read('word/settings.xml').decode('utf-8', errors='ignore')

    return (
        '<w:ins ' in document_xml
        or '<w:del ' in document_xml
        or '<w:trackRevisions' in settings_xml
    )


def build_snapshot_with_python_docx(docx_path: Path) -> str:
    document = Document(docx_path)
    blocks: list[str] = [LOSSY_NOTICE, '']

    for item in iter_block_items(document):
        if isinstance(item, Paragraph):
            rendered = render_paragraph(item)
        else:
            rendered = render_table(item)

        if not rendered:
            continue

        blocks.extend(rendered)
        blocks.append('')

    while blocks and blocks[-1] == '':
        blocks.pop()

    return '\n'.join(blocks) + '\n'


def build_snapshot_with_textutil(docx_path: Path) -> str:
    textutil = shutil.which('textutil')
    if textutil is None:
        fail('`textutil` is not available, so a tracked-change-safe text snapshot cannot be generated.')

    completed = subprocess.run(
        [textutil, '-convert', 'txt', '-stdout', str(docx_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    text = completed.stdout.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('\x0c', '\n\n---\n\n')
    text = text.strip()

    return '\n'.join([LOSSY_NOTICE, '', text, ''])


def build_snapshot(docx_path: Path) -> str:
    if shutil.which('textutil') is not None:
        return build_snapshot_with_textutil(docx_path)
    return build_snapshot_with_python_docx(docx_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Create a git-friendly Markdown snapshot from a DOCX file.',
    )
    parser.add_argument('input_docx', type=Path)
    parser.add_argument('--output', type=Path, help='Write the Markdown snapshot to this path.')
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_docx = args.input_docx.resolve()
    if not input_docx.exists() or not input_docx.is_file():
        fail(f'DOCX file not found: {input_docx}')

    markdown = build_snapshot(input_docx)

    if args.output is None:
        sys.stdout.write(markdown)
        return

    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown)
    print(output_path)


if __name__ == '__main__':
    main()
