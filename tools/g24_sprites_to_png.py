#!/usr/bin/env python3
"""Extract G24 sprite graphics and sprite delta variants to RGBA PNGs.

Reuses G24Reader and write_png from g24_to_png.py. Sprite metadata, graphics
pages, CLUT references, and delta streams are read from the same G24 archive.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

from g24_to_png import (
    CLUT_PAGE_SIZE, G24Reader, HEADER_SIZE, PAGE_WIDTH, PALETTE_SIZE,
    round_up, write_png,
)

PAGE_SIZE = PAGE_WIDTH * PAGE_WIDTH
SPRITE_TYPE_NAMES = (
    "car", "ped", "code_obj", "map_obj", "user", "font", "moped",
    "bike", "bus", "train", "tram", "boat", "tank", "wbus",
)


@dataclass
class Delta:
    size: int
    offset: int


@dataclass
class Sprite:
    index: int
    width: int
    height: int
    delta_count: int
    size: int
    clut: int
    page_x: int
    page_y: int
    page_number: int
    deltas: list[Delta]


def checked_slice(data: bytes, offset: int, size: int, label: str) -> bytes:
    if offset < 0 or size < 0 or offset + size > len(data):
        raise ValueError(f"Truncated G24 while reading {label} at {offset:#x}")
    return data[offset:offset + size]


def parse_sprite_sections(reader: G24Reader) -> tuple[bytes, list[Sprite], list[int]]:
    """Locate sprite records and graphics using the G24 header section sizes."""
    h = reader.header
    padded_blocks = round_up(h.total_blocks, 4)
    offset = HEADER_SIZE + padded_blocks * 64 * 64
    offset += h.anim_size + round_up(h.clut_size, CLUT_PAGE_SIZE)
    palette_data = checked_slice(reader.data, offset, h.palette_index_size, "palette indices")
    if len(palette_data) % 2:
        raise ValueError("Palette index section has odd byte length")
    palette_indices = list(struct.unpack(f"<{len(palette_data) // 2}H", palette_data))
    reader.palette_indices = palette_indices

    offset += h.palette_index_size + h.object_info_size + h.car_size
    sprite_info_data = checked_slice(reader.data, offset, h.sprite_info_size, "sprite metadata")
    offset += h.sprite_info_size
    graphics = checked_slice(reader.data, offset, h.sprite_graphics_size, "sprite graphics")
    offset += h.sprite_graphics_size
    counts_data = checked_slice(reader.data, offset, h.sprite_numbers_size, "sprite type counts")
    if len(counts_data) < len(SPRITE_TYPE_NAMES) * 2:
        raise ValueError("Sprite type-count section is too small")
    counts = list(struct.unpack_from(f"<{len(SPRITE_TYPE_NAMES)}H", counts_data))

    sprites: list[Sprite] = []
    cursor = 0
    while cursor < len(sprite_info_data):
        if cursor + 12 > len(sprite_info_data):
            raise ValueError(f"Truncated sprite metadata at {cursor:#x}")
        width, height, delta_count, _reserved, size, clut, page_x, page_y, page_number = (
            struct.unpack_from("<BBBBHHBBH", sprite_info_data, cursor)
        )
        cursor += 12
        deltas = []
        for _ in range(delta_count):
            if cursor + 6 > len(sprite_info_data):
                raise ValueError(f"Truncated delta metadata for sprite {len(sprites)}")
            delta_size, delta_offset = struct.unpack_from("<Hi", sprite_info_data, cursor)
            cursor += 6
            deltas.append(Delta(delta_size, delta_offset))
        sprites.append(Sprite(
            len(sprites), width, height, delta_count, size, clut,
            page_x, page_y, page_number, deltas,
        ))
    return graphics, sprites, counts


def palette_for_sprite(reader: G24Reader, sprite: Sprite, remap: int):
    """Resolve the sprite CLUT; remap 1-3 selects a vehicle/pedestrian remap CLUT."""
    h = reader.header
    tile_cluts = h.tileclut_size // PALETTE_SIZE
    sprite_cluts = h.spriteclut_size // PALETTE_SIZE
    remap_cluts = h.newcarclut_size // PALETTE_SIZE
    if not 0 <= sprite.clut < sprite_cluts:
        raise ValueError(f"Invalid sprite CLUT {sprite.clut}")
    if remap:
        # Carnage3D's sprite-remap lookup starts after tile and sprite CLUTs.
        remap_index = tile_cluts + sprite_cluts + remap
        if remap >= remap_cluts or remap_index >= len(reader.palette_indices):
            raise ValueError(f"Sprite remap {remap} is unavailable")
        palette_index = reader.palette_indices[remap_index]
    else:
        index = tile_cluts + sprite.clut
        if index >= len(reader.palette_indices):
            raise ValueError(f"Sprite CLUT index {index} is outside palette table")
        palette_index = reader.palette_indices[index]
    return reader.get_palette(palette_index)


def indexed_page_to_rgba(indexed: bytes, palette) -> bytearray:
    rgba = bytearray(len(indexed) * 4)
    for i, value in enumerate(indexed):
        r, g, b, _a = palette[value]
        p = i * 4
        rgba[p:p + 4] = bytes((r, g, b, 0 if value == 0 else 255))
    return rgba


def apply_delta_to_page(graphics: bytes, delta: Delta, page: bytearray, sprite_index: int) -> None:
    """Apply a Carnage3D delta stream to an indexed 256x256 page."""
    cursor = delta.offset
    end = cursor + delta.size
    if cursor < 0 or end > len(graphics):
        raise ValueError(f"Sprite {sprite_index} delta points outside graphics section")
    destination = 0
    while cursor < end:
        if cursor + 3 > end:
            raise ValueError(f"Malformed delta command for sprite {sprite_index}")
        skip, run_length = struct.unpack_from("<HB", graphics, cursor)
        cursor += 3
        if run_length == 0 or cursor + run_length > end:
            raise ValueError(f"Invalid delta run for sprite {sprite_index}")
        destination += skip
        if destination + run_length > len(page):
            raise ValueError(f"Delta writes outside sprite page {sprite_index}")
        page[destination:destination + run_length] = graphics[cursor:cursor + run_length]
        destination += run_length
        cursor += run_length


def crop_page(page: bytes | bytearray, sprite: Sprite) -> bytes:
    if sprite.width <= 0 or sprite.height <= 0:
        raise ValueError(f"Invalid sprite dimensions {sprite.width}x{sprite.height}")
    if sprite.page_x + sprite.width > PAGE_WIDTH or sprite.page_y + sprite.height > PAGE_WIDTH:
        raise ValueError(f"Sprite {sprite.index} exceeds its 256x256 page")
    cropped = bytearray(sprite.width * sprite.height)
    for y in range(sprite.height):
        src = (sprite.page_y + y) * PAGE_WIDTH + sprite.page_x
        dst = y * sprite.width
        cropped[dst:dst + sprite.width] = page[src:src + sprite.width]
    return bytes(cropped)


def category_for_index(index: int, counts: list[int]) -> tuple[str, int]:
    offset = 0
    for name, count in zip(SPRITE_TYPE_NAMES, counts):
        if index < offset + count:
            return name, index - offset
        offset += count
    return "unknown", index


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract G24 sprite graphics and sprite delta variants to transparent PNGs."
    )
    parser.add_argument("input", type=Path, help="Input STYLE###.G24 file")
    parser.add_argument("-o", "--output-dir", type=Path, help="Output directory (default: <input>_sprites)")
    parser.add_argument("--remap", type=int, choices=(0, 1, 2, 3), default=0,
                        help="Sprite palette remap index (default: 0)")
    parser.add_argument("--no-deltas", action="store_true", help="Export base sprites only")
    parser.add_argument("--metadata-only", action="store_true", help="Write sprites.json without PNGs")
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"Input file does not exist: {args.input}")
    output_dir = args.output_dir or args.input.with_name(args.input.stem + "_sprites")

    try:
        reader = G24Reader(args.input)
        graphics, sprites, counts = parse_sprite_sections(reader)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Sprite graphics: {len(graphics):,} bytes")
        print(f"Sprite records:  {len(sprites):,}")
        for name, count in zip(SPRITE_TYPE_NAMES, counts):
            print(f"  {name:10s} {count:5d}")

        metadata = []
        png_count = 0
        for sprite in sprites:
            category, category_index = category_for_index(sprite.index, counts)
            stem = f"sprite_{sprite.index:04d}_{category}_{category_index:03d}"
            metadata.append({
                "index": sprite.index, "category": category,
                "category_index": category_index, "width": sprite.width,
                "height": sprite.height, "clut": sprite.clut,
                "page": sprite.page_number, "page_x": sprite.page_x,
                "page_y": sprite.page_y,
                "deltas": [{"size": d.size, "offset": d.offset} for d in sprite.deltas],
            })
            if args.metadata_only:
                continue
            try:
                palette = palette_for_sprite(reader, sprite, args.remap)
                page_start = sprite.page_number * PAGE_SIZE
                page = bytearray(checked_slice(graphics, page_start, PAGE_SIZE, f"sprite {sprite.index} page"))
                base_indices = crop_page(page, sprite)
                base_rgba = indexed_page_to_rgba(base_indices, palette)
                base_path = output_dir / f"{stem}_base.png"
                write_png(base_path, sprite.width, sprite.height, base_rgba)
                png_count += 1

                if not args.no_deltas:
                    for delta_index, delta in enumerate(sprite.deltas):
                        variant_page = bytearray(page)
                        apply_delta_to_page(graphics, delta, variant_page, sprite.index)
                        variant_indices = crop_page(variant_page, sprite)
                        variant_rgba = indexed_page_to_rgba(variant_indices, palette)
                        variant_path = output_dir / f"{stem}_delta_{delta_index:02d}.png"
                        write_png(variant_path, sprite.width, sprite.height, variant_rgba)
                        png_count += 1
            except (ValueError, IndexError) as exc:
                print(f"Warning: skipped sprite {sprite.index}: {exc}", file=sys.stderr)

        (output_dir / "sprites.json").write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
        )
        print("Metadata:", output_dir / "sprites.json")
        print(f"PNG files: {png_count:,}")
        print("Output:", output_dir)
        return 0
    except (OSError, ValueError, IndexError, struct.error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
