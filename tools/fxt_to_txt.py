#!/usr/bin/env python3
"""
Decrypt GTA1/Carnage3D .FXT text files and write readable .txt files.

Usage:
    python tools/fxt_to_txt.py path/to/fxt_directory
    python tools/fxt_to_txt.py path/to/fxt_directory --recursive
    python tools/fxt_to_txt.py path/to/file.FXT
    python tools/fxt_to_txt.py path/to/fxt_directory -o path/to/output

The output keeps the original keyed format, one entry per line:
    [car1]Bug

Only Python's standard library is required.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def decrypt_fxt(data: bytes) -> bytes:
    """Decrypt an FXT byte stream using the algorithm documented by Carnage3D."""
    if not data:
        return b""

    first = data[0]
    if first == 0xBF:
        key = 0x63
        offset = -1
    elif first == 0xA6:
        key = 0x67
        offset = 28
    else:
        raise ValueError(
            f"unrecognized FXT encryption marker 0x{first:02X} "
            "(expected 0xBF or 0xA6)"
        )

    output = bytearray()
    pos = 0
    byte_count = 0

    while pos < len(data):
        char = data[pos]
        pos += 1

        if byte_count < 8:
            char = (char - key) & 0xFF
            key = (key << 1) & 0xFF

        byte_count += 1

        # FXT stores some extended Windows-ANSI characters as a two-byte
        # sequence. Remove the marker and shift the following byte by 64.
        if ((char + offset) & 0xFF) == 195:
            if pos >= len(data):
                raise ValueError("truncated FXT extended-character sequence")
            char = (data[pos] + 64) & 0xFF
            pos += 1
            byte_count += 1

        output.append((char + offset) & 0xFF)

    return bytes(output)


def parse_entries(data: bytes) -> list[tuple[str, str]]:
    """Parse decrypted [key]value\\0 entries from an FXT file."""
    entries: list[tuple[str, str]] = []
    pos = 0

    while pos < len(data):
        # The file's final [ ] entry is a sentinel in known FXT files.
        if data[pos:] == b"[]":
            break

        if data[pos:pos + 1] != b"[":
            raise ValueError(f"expected '[' at decrypted byte offset {pos}")

        key_end = data.find(b"]", pos + 1)
        if key_end < 0:
            raise ValueError(f"unterminated key at decrypted byte offset {pos}")

        key_bytes = data[pos + 1:key_end]
        value_start = key_end + 1
        value_end = data.find(b"\0", value_start)
        if value_end < 0:
            # Be tolerant of files whose final value has no NUL terminator.
            value_end = len(data)

        key = key_bytes.decode("cp1252", errors="replace")
        value = data[value_start:value_end].decode("cp1252", errors="replace")
        entries.append((key, value))
        pos = value_end + 1

    return entries


def convert_file(source: Path, destination: Path) -> int:
    encrypted = source.read_bytes()
    decrypted = decrypt_fxt(encrypted)
    entries = parse_entries(decrypted)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as output:
        for key, value in entries:
            output.write(f"[{key}]{value}\n")

    return len(entries)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert GTA1/Carnage3D .FXT text files to readable .txt files."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="an .FXT file or a directory containing .FXT files",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="output .txt file (single input) or destination directory",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="search input directories recursively",
    )
    args = parser.parse_args()

    if not args.input.exists():
        parser.error(f"input does not exist: {args.input}")

    if args.input.is_file():
        if args.input.suffix.lower() != ".fxt":
            parser.error(f"input file must have a .fxt extension: {args.input}")
        files = [args.input]
    elif args.input.is_dir():
        pattern = "**/*" if args.recursive else "*"
        files = sorted(
            path for path in args.input.glob(pattern)
            if path.is_file() and path.suffix.lower() == ".fxt"
        )
    else:
        parser.error(f"input is not a regular file or directory: {args.input}")

    if not files:
        print(f"No .fxt files found in {args.input}", file=sys.stderr)
        return 1

    failures = 0
    total_entries = 0

    for source in files:
        if args.output is None:
            destination = source.with_suffix(".txt")
        elif len(files) == 1 and args.output.suffix.lower() == ".txt":
            destination = args.output
        else:
            destination = args.output / source.with_suffix(".txt").name

        try:
            count = convert_file(source, destination)
            total_entries += count
            print(f"{source} -> {destination} ({count} entries)")
        except (OSError, UnicodeError, ValueError) as exc:
            failures += 1
            print(f"ERROR: {source}: {exc}", file=sys.stderr)

    print(f"Converted {len(files) - failures}/{len(files)} file(s); {total_entries} text entr(y/ies).")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
