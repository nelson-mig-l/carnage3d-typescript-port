#!/usr/bin/env python3
"""
Render a top-down PNG preview of a GTA1/Carnage3D .CMP map.

For every 256x256 map cell the script decompresses the CMP column,
selects the highest occupied block, and renders that block's lid/top
texture from the corresponding G24 style file.

The G24 decoder is reused from tools/g24_to_png.py.

Usage:
    python tools/cmp_to_png.py public/assets/data/NYC.CMP
    python tools/cmp_to_png.py public/assets/data/NYC.CMP -o nyc_top.png

By default the style file is inferred from the CMP header:
    STYLE%03d.G24
"""

from __future__ import annotations

import argparse
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path

from g24_to_png import G24Reader


CMP_VERSION = 331
MAP_DIMENSIONS = 256
MAP_LAYERS_COUNT = 6
TILE_SIZE = 64

CMP_HEADER_FORMAT = "<7I"
CMP_HEADER_SIZE = struct.calcsize(CMP_HEADER_FORMAT)
BLOCK_INFO_SIZE = 8  # uint16 type_map + six uint8 values


@dataclass(frozen=True)
class MapBlock:
    lid: int
    lid_rotation: int
    flip_top_bottom: bool
    flip_left_right: bool


def read_cmp(
    path: Path,
) -> tuple[int, list[int], list[int], list[MapBlock]]:
    data = path.read_bytes()

    if len(data) < CMP_HEADER_SIZE:
        raise ValueError(f"File is too small to contain a CMP header: {path}")

    (
        version,
        numbers,
        route_size,
        object_pos_size,
        column_size,
        block_size,
        nav_data_size,
    ) = struct.unpack_from(CMP_HEADER_FORMAT, data)

    if version != CMP_VERSION:
        raise ValueError(
            f"Unsupported CMP version {version}; Carnage3D expects {CMP_VERSION}"
        )

    # GTA1 stores the style number in the first byte of the union.
    style_number = numbers & 0xFF
    offset = CMP_HEADER_SIZE

    base_size = MAP_DIMENSIONS * MAP_DIMENSIONS * 4
    if offset + base_size > len(data):
        raise ValueError("CMP is truncated while reading base map data")

    base_tiles = list(
        struct.unpack_from(
            f"<{MAP_DIMENSIONS * MAP_DIMENSIONS}I",
            data,
            offset,
        )
    )
    offset += base_size

    if column_size % 2:
        raise ValueError("CMP column_size is not divisible by 2")

    if offset + column_size > len(data):
        raise ValueError("CMP is truncated while reading column data")

    column_data = list(
        struct.unpack_from(
            f"<{column_size // 2}H",
            data,
            offset,
        )
    )
    offset += column_size

    if block_size % BLOCK_INFO_SIZE:
        raise ValueError("CMP block_size is not divisible by 8")

    if offset + block_size > len(data):
        raise ValueError("CMP is truncated while reading block data")

    blocks: list[MapBlock] = []

    for block_offset in range(offset, offset + block_size, BLOCK_INFO_SIZE):
        type_map, type_map_ext, _west, _east, _north, _south, lid = (
            struct.unpack_from("<H6B", data, block_offset)
        )

        blocks.append(
            MapBlock(
                lid=lid,
                lid_rotation=(type_map >> 14) & 0x03,
                flip_top_bottom=(type_map_ext & 0x20) != 0,
                flip_left_right=(type_map_ext & 0x40) != 0,
            )
        )

    # The remaining CMP sections are not needed for this static preview.
    _ = route_size, object_pos_size, nav_data_size

    return style_number, base_tiles, column_data, blocks


def decompress_top_blocks(
    base_tiles: list[int],
    column_data: list[int],
    blocks: list[MapBlock],
) -> list[MapBlock | None]:
    """
    Reproduce GameMapManager::ReadCompressedMapData() and select the
    highest occupied block in every map column.
    """

    top_blocks: list[MapBlock | None] = [
        None
    ] * (MAP_DIMENSIONS * MAP_DIMENSIONS)

    for y in range(MAP_DIMENSIONS):
        for x in range(MAP_DIMENSIONS):
            cell = y * MAP_DIMENSIONS + x
            base_offset = base_tiles[cell]

            if base_offset % 2:
                raise ValueError(
                    f"Invalid base tile offset at ({x}, {y}): {base_offset}"
                )

            column_index = base_offset // 2
            if column_index >= len(column_data):
                raise ValueError(
                    f"Base tile at ({x}, {y}) points outside column data: "
                    f"{column_index}"
                )

            empty_layers = column_data[column_index]
            height = MAP_LAYERS_COUNT - empty_layers

            if height <= 0:
                continue

            if height > MAP_LAYERS_COUNT:
                raise ValueError(
                    f"Invalid column height at ({x}, {y}): {height}"
                )

            # In the original decompression loop:
            #
            #   srcBlock = columnData[columnElement + columnHeight - tilez]
            #
            # with tilez=0 being the highest map layer. Therefore this is
            # the topmost occupied block.
            top_index = column_index + height
            if top_index >= len(column_data):
                raise ValueError(
                    f"Column at ({x}, {y}) is truncated"
                )

            block_index = column_data[top_index]
            if block_index >= len(blocks):
                raise ValueError(
                    f"Column at ({x}, {y}) references invalid block {block_index}"
                )

            top_blocks[cell] = blocks[block_index]

    return top_blocks


def transform_tile(
    tile: bytes,
    rotation: int,
    flip_top_bottom: bool,
    flip_left_right: bool,
) -> bytes:
    """Apply the CMP lid rotation and flip flags to one 64x64 RGBA tile."""

    if len(tile) != TILE_SIZE * TILE_SIZE * 4:
        raise ValueError("Expected a 64x64 RGBA tile")

    output = bytearray(len(tile))

    for y in range(TILE_SIZE):
        for x in range(TILE_SIZE):
            sx, sy = x, y

            if rotation == 1:       # 90 degrees clockwise
                sx, sy = y, TILE_SIZE - 1 - x
            elif rotation == 2:     # 180 degrees
                sx, sy = TILE_SIZE - 1 - x, TILE_SIZE - 1 - y
            elif rotation == 3:     # 270 degrees clockwise
                sx, sy = TILE_SIZE - 1 - y, x

            if flip_left_right:
                sx = TILE_SIZE - 1 - sx

            if flip_top_bottom:
                sy = TILE_SIZE - 1 - sy

            src = (sy * TILE_SIZE + sx) * 4
            dst = (y * TILE_SIZE + x) * 4
            output[dst:dst + 4] = tile[src:src + 4]

    return bytes(output)


def png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    chunk = chunk_type + payload
    return (
        struct.pack(">I", len(payload))
        + chunk
        + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)
    )


def write_map_png(
    path: Path,
    top_blocks: list[MapBlock | None],
    reader: G24Reader,
    remap: int,
) -> None:
    """
    Write the 256x256 cell map at 64 pixels per cell.

    Output dimensions are therefore 16384x16384. PNG scanlines are
    streamed through zlib instead of building the complete RGBA image
    in memory.
    """

    width = MAP_DIMENSIONS * TILE_SIZE
    height = MAP_DIMENSIONS * TILE_SIZE
    compressor = zlib.compressobj(level=6)

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("wb") as output:
        output.write(b"\x89PNG\r\n\x1a\n")
        output.write(
            png_chunk(
                b"IHDR",
                struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0),
            )
        )

        for map_y in range(MAP_DIMENSIONS):
            decoded_tiles: list[bytes | None] = []

            for map_x in range(MAP_DIMENSIONS):
                block = top_blocks[map_y * MAP_DIMENSIONS + map_x]

                if block is None:
                    decoded_tiles.append(None)
                    continue

                if block.lid >= reader.header.lid_count:
                    decoded_tiles.append(None)
                    continue

                linear_lid_index = reader.linear_block_index("lid", block.lid)
                tile = reader.decode_block(linear_lid_index, remap)

                tile = transform_tile(
                    tile,
                    block.lid_rotation,
                    block.flip_top_bottom,
                    block.flip_left_right,
                )

                decoded_tiles.append(tile)

            for texture_y in range(TILE_SIZE):
                row = bytearray(width * 4)

                for map_x, tile in enumerate(decoded_tiles):
                    if tile is None:
                        continue

                    src = texture_y * TILE_SIZE * 4
                    dst = map_x * TILE_SIZE * 4
                    row[dst:dst + TILE_SIZE * 4] = tile[
                        src:src + TILE_SIZE * 4
                    ]

                scanline = b"\x00" + bytes(row)
                compressed = compressor.compress(scanline)
                if compressed:
                    output.write(png_chunk(b"IDAT", compressed))

        compressed = compressor.flush()
        if compressed:
            output.write(png_chunk(b"IDAT", compressed))

        output.write(png_chunk(b"IEND", b""))


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render a top-down PNG preview from a GTA1/Carnage3D .CMP map."
        )
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input .CMP file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output PNG (default: <input>_top.png)",
    )
    parser.add_argument(
        "--style",
        type=Path,
        help=(
            "G24 style file; defaults to STYLE%03d.G24 "
            "beside the CMP file"
        ),
    )
    parser.add_argument(
        "--remap",
        type=int,
        choices=(0, 1, 2, 3),
        default=0,
        help="Palette/remap index (default: 0)",
    )
    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"Input file does not exist: {args.input}")

    try:
        style_number, base_tiles, column_data, blocks = read_cmp(args.input)

        style_path = args.style
        if style_path is None:
            style_path = args.input.with_name(
                f"STYLE{style_number:03d}.G24"
            )

        if not style_path.is_file():
            raise ValueError(
                f"G24 style file does not exist: {style_path}. "
                "Use --style to specify the corresponding G24 file."
            )

        output = args.output or args.input.with_name(
            f"{args.input.stem}_top.png"
        )

        reader = G24Reader(style_path)
        top_blocks = decompress_top_blocks(
            base_tiles,
            column_data,
            blocks,
        )

        write_map_png(
            output,
            top_blocks,
            reader,
            args.remap,
        )

        populated = sum(block is not None for block in top_blocks)

        print(f"Created: {output}")
        print(f"Size:    {MAP_DIMENSIONS * TILE_SIZE} x {MAP_DIMENSIONS * TILE_SIZE}")
        print(f"Cells:   {MAP_DIMENSIONS} x {MAP_DIMENSIONS}")
        print(f"Filled:  {populated}")
        print(f"Style:   {style_path}")
        print(f"Remap:   {args.remap}")

        return 0

    except (OSError, ValueError, IndexError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
