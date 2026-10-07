#!/usr/bin/env python3
"""
Render one transparent top-down PNG for each height level of a GTA1/Carnage3D .CMP map.

Each PNG is 256x256 map cells at 64 pixels per cell (16384x16384).
Pixels for cells without a block at that height remain fully transparent.

A matching .txt file is written for every layer with the number of map
cells using each G24 lid texture.

The G24 decoder is reused from tools/g24_to_png.py.

Usage:
    python tools/cmp_to_png.py public/assets/data/NYC.CMP
    python tools/cmp_to_png.py public/assets/data/NYC.CMP -o nyc
    python tools/cmp_to_png.py public/assets/data/NYC.CMP --output-dir maps
"""

from __future__ import annotations

import argparse
import struct
import sys
import zlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from g24_to_png import G24Reader


CMP_VERSION = 331
MAP_DIMENSIONS = 256
MAP_LAYERS_COUNT = 6
TILE_SIZE = 64

CMP_HEADER_FORMAT = "<7I"
CMP_HEADER_SIZE = struct.calcsize(CMP_HEADER_FORMAT)
BLOCK_INFO_SIZE = 8


@dataclass(frozen=True)
class MapBlock:
    lid: int
    lid_rotation: int
    flip_top_bottom: bool
    flip_left_right: bool


def read_cmp(path: Path) -> tuple[int, list[int], list[int], list[MapBlock]]:
    print(f"[1/3] Reading CMP: {path}", flush=True)
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
        struct.unpack_from(f"<{column_size // 2}H", data, offset)
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

    _ = route_size, object_pos_size, nav_data_size

    print(
        f"      version={version}, style={style_number:03d}, "
        f"blocks={len(blocks):,}, columns={len(column_data):,}",
        flush=True,
    )
    return style_number, base_tiles, column_data, blocks


def decompress_map_layers(
    base_tiles: list[int],
    column_data: list[int],
    blocks: list[MapBlock],
) -> list[list[MapBlock | None]]:
    """
    Reconstruct every map layer.

    The result is [height][cell], where height 0 is the lowest map layer
    and height 5 is the highest.
    """
    print("[2/3] Decompressing map layers...", flush=True)

    layers: list[list[MapBlock | None]] = [
        [None] * (MAP_DIMENSIONS * MAP_DIMENSIONS)
        for _ in range(MAP_LAYERS_COUNT)
    ]

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

            for layer in range(height):
                column_element = column_index + 1 + layer
                if column_element >= len(column_data):
                    raise ValueError(f"Column at ({x}, {y}) is truncated")

                block_index = column_data[column_element]
                if block_index >= len(blocks):
                    raise ValueError(
                        f"Column at ({x}, {y}) references invalid block {block_index}"
                    )

                layers[empty_layers + layer][cell] = blocks[block_index]

        print(f"      map row {y + 1:3d}/{MAP_DIMENSIONS}", flush=True)

    return layers


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

            if rotation == 1:
                sx, sy = y, TILE_SIZE - 1 - x
            elif rotation == 2:
                sx, sy = TILE_SIZE - 1 - x, TILE_SIZE - 1 - y
            elif rotation == 3:
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


def write_layer_png(
    path: Path,
    layer: list[MapBlock | None],
    reader: G24Reader,
    remap: int,
    layer_number: int,
    skip_textures: set[int],
) -> tuple[int, Counter[int]]:
    """Write one transparent RGBA PNG and count cells by G24 lid texture."""
    width = MAP_DIMENSIONS * TILE_SIZE
    height = MAP_DIMENSIONS * TILE_SIZE
    compressor = zlib.compressobj(level=6)
    texture_counts: Counter[int] = Counter()

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
                block = layer[map_y * MAP_DIMENSIONS + map_x]

                if (
                    block is None
                    or block.lid >= reader.header.lid_count
                    or block.lid in skip_textures
                ):
                    decoded_tiles.append(None)
                    continue

                texture_counts[block.lid] += 1
                linear_lid_index = reader.linear_block_index("lid", block.lid)
                tile = reader.decode_block(linear_lid_index, remap)
                decoded_tiles.append(
                    transform_tile(
                        tile,
                        block.lid_rotation,
                        block.flip_top_bottom,
                        block.flip_left_right,
                    )
                )

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

                compressed = compressor.compress(b"\x00" + bytes(row))
                if compressed:
                    output.write(png_chunk(b"IDAT", compressed))

            print(
                f"      layer {layer_number + 1}/{MAP_LAYERS_COUNT}, "
                f"row {map_y + 1:3d}/{MAP_DIMENSIONS}",
                flush=True,
            )

        compressed = compressor.flush()
        if compressed:
            output.write(png_chunk(b"IDAT", compressed))

        output.write(png_chunk(b"IEND", b""))

    return sum(texture_counts.values()), texture_counts


def write_texture_report(
    path: Path,
    layer_number: int,
    texture_counts: Counter[int],
) -> None:
    """Write one text report listing every texture used by this layer."""
    total = sum(texture_counts.values())

    with path.open("w", encoding="utf-8") as report:
        report.write(f"Layer {layer_number + 1}\n")
        report.write(f"Total populated cells: {total:,}\n")
        report.write(f"Unique textures: {len(texture_counts):,}\n")
        report.write("\n")
        report.write("Texture ID\tTile count\n")
        report.write("----------\t----------\n")

        for texture_id, count in sorted(
            texture_counts.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            report.write(f"{texture_id}\t{count:,}\n")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render one transparent top-down PNG per height level "
            "from a GTA1/Carnage3D .CMP map."
        )
    )
    parser.add_argument("input", type=Path, help="Input .CMP file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output prefix or .png path. Default: <input>_layer_N.png",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for layer PNGs and TXT reports (default: alongside the input)",
    )
    parser.add_argument(
        "--style",
        type=Path,
        help="G24 style file; defaults to STYLE###.G24 beside the CMP file",
    )
    parser.add_argument(
        "--remap",
        type=int,
        choices=(0, 1, 2, 3),
        default=0,
        help="Palette/remap index (default: 0)",
    )
    parser.add_argument(
        "--skip-texture",
        type=int,
        action="append",
        default=[],
        metavar="ID",
        help=(
            "Make this G24 lid texture transparent. Repeat the option to "
            "skip multiple texture IDs."
        ),
    )
    return parser


def layer_output_path(
    input_path: Path,
    output: Path | None,
    output_dir: Path | None,
    layer_number: int,
) -> Path:
    if output_dir is not None:
        return output_dir / f"{input_path.stem}_layer_{layer_number + 1}.png"

    if output is None:
        return input_path.with_name(
            f"{input_path.stem}_layer_{layer_number + 1}.png"
        )

    if output.suffix.lower() == ".png":
        return output.with_name(
            f"{output.stem}_layer_{layer_number + 1}.png"
        )

    return output.parent / f"{output.name}_layer_{layer_number + 1}.png"


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"Input file does not exist: {args.input}")
    if args.output is not None and args.output_dir is not None:
        parser.error("--output and --output-dir cannot be used together")

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

        print(f"[3/3] Loading style: {style_path}", flush=True)
        reader = G24Reader(style_path)

        layers = decompress_map_layers(
            base_tiles,
            column_data,
            blocks,
        )

        skip_textures = set(args.skip_texture)
        if skip_textures:
            print(
                "Skipping textures: "
                + ", ".join(str(texture_id) for texture_id in sorted(skip_textures)),
                flush=True,
            )

        total_populated = 0

        for layer_number, layer in enumerate(layers):
            output_path = layer_output_path(
                args.input,
                args.output,
                args.output_dir,
                layer_number,
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)

            report_path = output_path.with_suffix(".txt")

            print(
                f"Rendering layer {layer_number + 1}/{MAP_LAYERS_COUNT}: "
                f"{output_path}",
                flush=True,
            )

            populated, texture_counts = write_layer_png(
                output_path,
                layer,
                reader,
                args.remap,
                layer_number,
                skip_textures,
            )

            write_texture_report(
                report_path,
                layer_number,
                texture_counts,
            )

            total_populated += populated

            print(
                f"      complete: {populated:,} populated cells, "
                f"{len(texture_counts):,} unique textures",
                flush=True,
            )
            print(f"      report:   {report_path}", flush=True)

        print("Done.")
        print(f"Created: {MAP_LAYERS_COUNT} layer PNGs + {MAP_LAYERS_COUNT} TXT reports")
        print(
            f"Size:    {MAP_DIMENSIONS * TILE_SIZE} x "
            f"{MAP_DIMENSIONS * TILE_SIZE}"
        )
        print(f"Style:   {style_path}")
        print(f"Remap:   {args.remap}")
        print(
            "Skipped: "
            + (", ".join(str(texture_id) for texture_id in sorted(skip_textures))
               if skip_textures else "none")
        )
        print(f"Cells:   {total_populated:,} block placements across all layers")

        return 0

    except (OSError, ValueError, IndexError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
