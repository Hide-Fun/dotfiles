#!/usr/bin/env python3
"""Unpack, repack, and inspect DOCX package contents."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import zipfile
from pathlib import Path


REQUIRED_DOCX_PARTS = (
    '[Content_Types].xml',
    'word/document.xml',
)

MODEL_NAME_ENV_VARS = (
    'CODEX_MODEL_NAME',
    'OPENAI_MODEL',
    'MODEL_NAME',
)


def fail(message: str) -> None:
    print(f'[ERROR] {message}', file=sys.stderr)
    raise SystemExit(1)


def ensure_docx_exists(path: Path) -> Path:
    if not path.exists():
        fail(f'DOCX file not found: {path}')
    if not path.is_file():
        fail(f'Path is not a file: {path}')
    return path


def ensure_package_root(path: Path) -> None:
    missing = [part for part in REQUIRED_DOCX_PARTS if not (path / part).exists()]
    if missing:
        fail(
            'Input directory does not look like a DOCX package root. Missing: '
            + ', '.join(missing)
        )


def unpack_docx(input_docx: Path, output_dir: Path, force: bool) -> None:
    ensure_docx_exists(input_docx)

    if output_dir.exists():
        if not force:
            fail(f'Output directory already exists: {output_dir}. Use --force to replace it.')
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(input_docx) as archive:
        archive.extractall(output_dir)

    print(output_dir)


def pack_docx(input_dir: Path, output_docx: Path, force: bool) -> None:
    if not input_dir.exists() or not input_dir.is_dir():
        fail(f'Input directory not found: {input_dir}')

    ensure_package_root(input_dir)

    if output_docx.exists() and not force:
        fail(f'Output file already exists: {output_docx}. Use --force to replace it.')

    output_docx.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_docx, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(input_dir.rglob('*')):
            if path.is_file():
                archive.write(path, arcname=path.relative_to(input_dir).as_posix())

    print(output_docx)


def list_parts(input_docx: Path) -> None:
    ensure_docx_exists(input_docx)

    with zipfile.ZipFile(input_docx) as archive:
        for name in sorted(archive.namelist()):
            print(name)


def build_author_label(model_name: str | None, allow_plain_codex: bool) -> str:
    resolved_model_name = model_name

    if resolved_model_name is None:
        for env_var in MODEL_NAME_ENV_VARS:
            env_value = os.environ.get(env_var)
            if env_value:
                resolved_model_name = env_value
                break

    if resolved_model_name:
        return f'Codex ({resolved_model_name})'

    if allow_plain_codex:
        return 'Codex'

    fail(
        'Model name is required to build the revision author label. '
        'Pass --model-name or set one of: '
        + ', '.join(MODEL_NAME_ENV_VARS)
    )


def print_author_label(model_name: str | None, allow_plain_codex: bool) -> None:
    print(build_author_label(model_name=model_name, allow_plain_codex=allow_plain_codex))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Inspect and repack DOCX package contents.',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    unpack_parser = subparsers.add_parser('unpack', help='Extract a DOCX package')
    unpack_parser.add_argument('input_docx', type=Path)
    unpack_parser.add_argument('--output-dir', type=Path, required=True)
    unpack_parser.add_argument('--force', action='store_true')

    pack_parser = subparsers.add_parser('pack', help='Create a DOCX from an extracted package')
    pack_parser.add_argument('input_dir', type=Path)
    pack_parser.add_argument('--output-docx', type=Path, required=True)
    pack_parser.add_argument('--force', action='store_true')

    list_parser = subparsers.add_parser('list', help='List package members')
    list_parser.add_argument('input_docx', type=Path)

    author_label_parser = subparsers.add_parser(
        'author-label',
        help='Build the Word revision author label for Codex-authored edits',
    )
    author_label_parser.add_argument('--model-name')
    author_label_parser.add_argument('--allow-plain-codex', action='store_true')

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == 'unpack':
        unpack_docx(args.input_docx.resolve(), args.output_dir.resolve(), args.force)
    elif args.command == 'pack':
        pack_docx(args.input_dir.resolve(), args.output_docx.resolve(), args.force)
    elif args.command == 'list':
        list_parts(args.input_docx.resolve())
    elif args.command == 'author-label':
        print_author_label(
            model_name=args.model_name,
            allow_plain_codex=args.allow_plain_codex,
        )
    else:
        fail(f'Unknown command: {args.command}')


if __name__ == '__main__':
    main()
