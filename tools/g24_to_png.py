#!/usr/bin/env python3
"""
Convert Carnage3D / GTA1 .G24 block textures into PNG texture maps.

Based on the G24 implementation in Carnage3D's StyleData.cpp.

Usage:

    python g24_to_png.py STYLE001.G24

    python g24_to_png.py STYLE001.G24 -o style001.png

    python g24_to_png.py STYLE001.G24 --section side

    python g24_to_png.py STYLE001.G24 --section lid

    python g24_to_png.py STYLE001.G24 --section aux

    python g24_to_png.py STYLE001.G24 --remap 1

    python g24_to_png.py STYLE001.G24 --info

Output:
    A PNG atlas containing 64x64 decoded block textures.

No external Python packages are required.
"""

from __future__ import annotations

import argparse
import math
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Carnage3D / GTA1 constants
# ---------------------------------------------------------------------------

G24_VERSION = 336

TILE_WIDTH = 64
TILE_HEIGHT = 64
TILE_AREA = TILE_WIDTH * TILE_HEIGHT

PAGE_WIDTH = 256
TILES_PER_ROW = PAGE_WIDTH // TILE_WIDTH  # 4

CLUT_PAGE_SIZE = 64 * 1024
PALETTES_PER_CLUT_PAGE = 64
PALETTE_ENTRIES = 256
PALETTE_SIZE = PALETTE_ENTRIES * 4

REMAP_COUNT = 4

# G24 header contains 16 little-endian uint32 values.
HEADER_FORMAT = "<16I"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

@dataclass
class G24Header:
    version_code: int
    side_size: int
    lid_size: int
    aux_size: int
    anim_size: int
    clut_size: int
    tileclut_size: int
    spriteclut_size: int
    newcarclut_size: int
    fontclut_size: int
    palette_index_size: int
    object_info_size: int
    car_size: int
    sprite_info_size: int
    sprite_graphics_size: int
    sprite_numbers_size: int

    @property
    def side_count(self) -> int:
        return self.side_size // TILE_AREA

    @property
    def lid_count(self) -> int:
        return self.lid_size // TILE_AREA

    @property
    def aux_count(self) -> int:
        return self.aux_size // TILE_AREA

    @property
    def total_blocks(self) -> int:
        return self.side_count + self.lid_count + self.aux_count

    @property
    def tile_clut_count(self) -> int:
        return self.tileclut_size // PALETTE_SIZE


def read_header(data: bytes) -> G24Header:
    if len(data) < HEADER_SIZE:
        raise ValueError(
            f"File is too small to contain a G24 header "
            f"({len(data)} bytes)"
        )

    values = struct.unpack_from(HEADER_FORMAT, data, 0)
    header = G24Header(*values)

    if header.version_code != G24_VERSION:
        raise ValueError(
            f"Unsupported G24 version {header.version_code}; "
            f"Carnage3D expects {G24_VERSION}"
        )

    if header.side_size % TILE_AREA != 0:
        raise ValueError("side_size is not a multiple of 4096")

    if header.lid_size % TILE_AREA != 0:
        raise ValueError("lid_size is not a multiple of 4096")

    if header.aux_size % TILE_AREA != 0:
        raise ValueError("aux_size is not a multiple of 4096")

    if header.tileclut_size % PALETTE_SIZE != 0:
        raise ValueError(
            "tileclut_size is not a multiple of 1024"
        )

    return header


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def round_up(value: int, alignment: int) -> int:
    return ((value + alignment - 1) // alignment) * alignment


def read_bytes(data: bytes, offset: int, size: int) -> tuple[bytes, int]:
    end = offset + size

    if end > len(data):
        raise ValueError(
            f"Unexpected end of file at offset {offset:#x}: "
            f"wanted {size} bytes"
        )

    return data[offset:end], end


# ---------------------------------------------------------------------------
# G24 reader
# ---------------------------------------------------------------------------

class G24Reader:
    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()

        self.header = read_header(self.data)

        self.block_pixels: bytes
        self.clut_data: bytes
        self.palette_indices: list[int]

        self._parse()

    def _parse(self) -> None:
        header = self.header
        offset = HEADER_SIZE

        # ---------------------------------------------------------------
        # Block textures
        #
        # Carnage3D's ReadBlockTextures() stores:
        #
        #   side blocks
        #   lid blocks
        #   aux blocks
        #
        # The total number of blocks is padded to a multiple of 4 because
        # textures are stored in 256x256 pages (4x4 64x64 tiles).
        # ---------------------------------------------------------------

        total_blocks = header.total_blocks

        padded_blocks = round_up(total_blocks, TILES_PER_ROW)

        block_texture_size = padded_blocks * TILE_AREA

        self.block_pixels, offset = read_bytes(
            self.data,
            offset,
            block_texture_size,
        )

        # ---------------------------------------------------------------
        # Animation data
        # ---------------------------------------------------------------

        _, offset = read_bytes(
            self.data,
            offset,
            header.anim_size,
        )

        # ---------------------------------------------------------------
        # CLUT / palette data
        #
        # Carnage3D rounds clut_size up to a 64 KiB boundary.
        # ---------------------------------------------------------------

        clut_size_padded = round_up(
            header.clut_size,
            CLUT_PAGE_SIZE,
        )

        self.clut_data, offset = read_bytes(
            self.data,
            offset,
            clut_size_padded,
        )

        # ---------------------------------------------------------------
        # Palette indices
        #
        # Each block has 4 palette/remap indices.
        # ---------------------------------------------------------------

        palette_index_data, offset = read_bytes(
            self.data,
            offset,
            header.palette_index_size,
        )

        if len(palette_index_data) % 2 != 0:
            raise ValueError(
                "palette_index_size is not divisible by 2"
            )

        count = len(palette_index_data) // 2

        self.palette_indices = list(
            struct.unpack(
                f"<{count}H",
                palette_index_data,
            )
        )

        expected = header.total_blocks * REMAP_COUNT

        if len(self.palette_indices) < expected:
            raise ValueError(
                f"Palette index table is too small: "
                f"got {len(self.palette_indices)} entries, "
                f"expected at least {expected}"
            )

    # -------------------------------------------------------------------
    # Block indexing
    # -------------------------------------------------------------------

    def linear_block_index(
        self,
        section: str,
        block_index: int,
    ) -> int:
        """
        Reproduce StyleData::GetBlockTextureLinearIndex().
        """

        if section == "side":

            if not 0 <= block_index < self.header.side_count:
                raise IndexError("side block index out of range")

            return block_index

        if section == "lid":

            if not 0 <= block_index < self.header.lid_count:
                raise IndexError("lid block index out of range")

            return (
                self.header.side_count
                + block_index
            )

        if section == "aux":

            if not 0 <= block_index < self.header.aux_count:
                raise IndexError("aux block index out of range")

            return (
                self.header.side_count
                + self.header.lid_count
                + block_index
            )

        raise ValueError(
            f"Unknown section: {section}"
        )

    # -------------------------------------------------------------------
    # Palette index
    # -------------------------------------------------------------------

    def get_palette_index(
        self,
        linear_block_index: int,
        remap: int,
    ) -> int:
        """
        Reproduce:

            mPaletteIndices[
                4 * blockLinearIndex + remap
            ]
        """

        if not 0 <= remap < REMAP_COUNT:
            raise ValueError(
                "remap must be 0, 1, 2 or 3"
            )

        index = (
            REMAP_COUNT * linear_block_index
            + remap
        )

        if index >= len(self.palette_indices):
            raise IndexError(
                "Palette index points outside palette index table"
            )

        return self.palette_indices[index]

    # -------------------------------------------------------------------
    # Decode one CLUT palette
    # -------------------------------------------------------------------

    def get_palette(
        self,
        palette_index: int,
    ) -> list[tuple[int, int, int, int]]:
        """
        Decode one Carnage3D 256-entry palette.

        G24 CLUT layout:

            64 palettes per 64 KiB page
            256 color rows
            4 bytes per color

        The source file stores colors as:

            B G R A

        Carnage3D converts this to:

            R G B A
        """

        palettes_per_page = PALETTES_PER_CLUT_PAGE

        page_index = (
            palette_index // palettes_per_page
        )

        palette_in_page = (
            palette_index % palettes_per_page
        )

        page_offset = (
            page_index * CLUT_PAGE_SIZE
        )

        if (
            page_offset + CLUT_PAGE_SIZE
            > len(self.clut_data)
        ):
            raise ValueError(
                f"Palette {palette_index} is outside "
                f"the CLUT data"
            )

        palette = []

        for color_index in range(PALETTE_ENTRIES):

            # Carnage3D reads one row containing
            # 64 palettes at a time.
            row_offset = (
                page_offset
                + color_index * (PALETTES_PER_CLUT_PAGE * 4)
            )

            color_offset = (
                row_offset
                + palette_in_page * 4
            )

            b = self.clut_data[color_offset + 0]
            g = self.clut_data[color_offset + 1]
            r = self.clut_data[color_offset + 2]
            a = self.clut_data[color_offset + 3]

            palette.append(
                (r, g, b, a)
            )

        return palette

    # -------------------------------------------------------------------
    # Decode one 64x64 block
    # -------------------------------------------------------------------

    def decode_block(
        self,
        linear_block_index: int,
        remap: int = 0,
    ) -> bytes:
        """
        Decode one 64x64 block to RGBA bytes.

        Carnage3D stores block pixels in pages arranged like:

            +----+----+----+----+
            |  0 |  1 |  2 |  3 |
            +----+----+----+----+
            |  4 |  5 |  6 |  7 |
            +----+----+----+----+
            | .. | .. | .. | .. |
            +----+----+----+----+

        Each tile is 64x64 pixels.

        A row of a tile advances by 4*64 bytes because
        the source page is 256 pixels wide.
        """

        if not (
            0 <= linear_block_index
            < self.header.total_blocks
        ):
            raise IndexError(
                "linear block index out of range"
            )

        palette_index = self.get_palette_index(
            linear_block_index,
            remap,
        )

        palette = self.get_palette(
            palette_index
        )

        block_x = (
            linear_block_index
            % TILES_PER_ROW
        )

        block_y = (
            linear_block_index
            // TILES_PER_ROW
        )

        # Same calculation as Carnage3D:
        #
        # srcOffset =
        #     (blockY * MAP_BLOCK_TEXTURE_AREA * 4)
        #     + (blockX * MAP_BLOCK_TEXTURE_DIMS)

        src_offset = (
            block_y * TILE_AREA * TILES_PER_ROW
            + block_x * TILE_WIDTH
        )

        output = bytearray(
            TILE_AREA * 4
        )

        for y in range(TILE_HEIGHT):

            src_row = (
                src_offset
                + y * PAGE_WIDTH
            )

            dst_row = (
                y * TILE_WIDTH * 4
            )

            for x in range(TILE_WIDTH):

                palette_entry = (
                    self.block_pixels[
                        src_row + x
                    ]
                )

                r, g, b, _ = palette[
                    palette_entry
                ]

                # Carnage3D's RGBA path:
                #
                #   palette index 0 -> alpha 0
                #   anything else    -> alpha 255
                #

                alpha = (
                    0
                    if palette_entry == 0
                    else 255
                )

                dst = (
                    dst_row
                    + x * 4
                )

                output[dst + 0] = r
                output[dst + 1] = g
                output[dst + 2] = b
                output[dst + 3] = alpha

        return bytes(output)


# ---------------------------------------------------------------------------
# PNG writer
#
# Keeps the converter dependency-free.
# ---------------------------------------------------------------------------

def png_chunk(
    chunk_type: bytes,
    payload: bytes,
) -> bytes:

    chunk = (
        chunk_type
        + payload
    )

    crc = zlib.crc32(chunk) & 0xFFFFFFFF

    return (
        struct.pack(">I", len(payload))
        + chunk
        + struct.pack(">I", crc)
    )


def write_png(
    path: Path,
    width: int,
    height: int,
    rgba: bytes,
) -> None:

    expected_size = (
        width
        * height
        * 4
    )

    if len(rgba) != expected_size:
        raise ValueError(
            f"Invalid RGBA buffer size: "
            f"{len(rgba)} != {expected_size}"
        )

    raw = bytearray()

    row_size = width * 4

    for y in range(height):

        # PNG filter type 0: no filtering
        raw.append(0)

        start = y * row_size
        end = start + row_size

        raw.extend(
            rgba[start:end]
        )

    compressed = zlib.compress(
        bytes(raw),
        level=9,
    )

    png = bytearray()

    png.extend(
        b"\x89PNG\r\n\x1a\n"
    )

    # IHDR
    png.extend(
        png_chunk(
            b"IHDR",
            struct.pack(
                ">IIBBBBB",
                width,
                height,
                8,   # bits per channel
                6,   # RGBA
                0,   # compression
                0,   # filter
                0,   # interlace
            ),
        )
    )

    # IDAT
    png.extend(
        png_chunk(
            b"IDAT",
            compressed,
        )
    )

    # IEND
    png.extend(
        png_chunk(
            b"IEND",
            b"",
        )
    )

    path.write_bytes(
        bytes(png)
    )


# ---------------------------------------------------------------------------
# Atlas generation
# ---------------------------------------------------------------------------

def build_atlas(
    reader: G24Reader,
    section: str,
    remap: int,
    columns: int,
) -> tuple[bytes, int, int]:

    if section == "side":
        start = 0
        count = reader.header.side_count

    elif section == "lid":
        start = reader.header.side_count
        count = reader.header.lid_count

    elif section == "aux":
        start = (
            reader.header.side_count
            + reader.header.lid_count
        )
        count = reader.header.aux_count

    elif section == "all":
        start = 0
        count = reader.header.total_blocks

    else:
        raise ValueError(
            f"Unknown section: {section}"
        )

    if count == 0:
        raise ValueError(
            f"No blocks found in section '{section}'"
        )

    rows = math.ceil(
        count / columns
    )

    width = (
        columns
        * TILE_WIDTH
    )

    height = (
        rows
        * TILE_HEIGHT
    )

    atlas = bytearray(
        width
        * height
        * 4
    )

    for atlas_index in range(count):

        linear_index = (
            start
            + atlas_index
        )

        tile = reader.decode_block(
            linear_index,
            remap,
        )

        atlas_x = (
            atlas_index
            % columns
        )

        atlas_y = (
            atlas_index
            // columns
        )

        x = (
            atlas_x
            * TILE_WIDTH
        )

        y = (
            atlas_y
            * TILE_HEIGHT
        )

        for row in range(
            TILE_HEIGHT
        ):

            src = (
                row
                * TILE_WIDTH
                * 4
            )

            dst = (
                (
                    (y + row)
                    * width
                    + x
                )
                * 4
            )

            atlas[
                dst:
                dst + TILE_WIDTH * 4
            ] = tile[
                src:
                src + TILE_WIDTH * 4
            ]

    return (
        bytes(atlas),
        width,
        height,
    )


# ---------------------------------------------------------------------------
# Information
# ---------------------------------------------------------------------------

def print_info(
    reader: G24Reader,
) -> None:

    h = reader.header

    print()
    print("G24 information")
    print("----------------")
    print(f"Version:           {h.version_code}")
    print(f"Side blocks:       {h.side_count}")
    print(f"Lid blocks:        {h.lid_count}")
    print(f"Aux blocks:        {h.aux_count}")
    print(f"Total blocks:      {h.total_blocks}")
    print(f"Tile CLUTs:        {h.tile_clut_count}")
    print(f"Animation bytes:   {h.anim_size}")
    print(f"CLUT bytes:        {h.clut_size}")
    print(
        f"CLUT bytes padded: "
        f"{round_up(h.clut_size, CLUT_PAGE_SIZE)}"
    )
    print(
        f"Palette index data:"
        f" {h.palette_index_size}"
    )
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def create_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Convert Carnage3D/GTA1 .G24 block "
            "textures to PNG."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input .G24 file",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=(
            "Output PNG file. "
            "Defaults to <input>.png"
        ),
    )

    parser.add_argument(
        "--section",
        choices=(
            "all",
            "side",
            "lid",
            "aux",
        ),
        default="all",
        help=(
            "Texture section to export "
            "(default: all)"
        ),
    )

    parser.add_argument(
        "--remap",
        type=int,
        choices=(0, 1, 2, 3),
        default=0,
        help=(
            "Palette/remap index "
            "(default: 0)"
        ),
    )

    parser.add_argument(
        "--columns",
        type=int,
        default=4,
        help=(
            "Number of tiles across the PNG "
            "(default: 4)"
        ),
    )

    parser.add_argument(
        "--info",
        action="store_true",
        help="Print G24 header information",
    )

    return parser


def main() -> int:

    parser = create_parser()
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(
            f"Input file does not exist: "
            f"{args.input}"
        )

    if args.columns <= 0:
        parser.error(
            "--columns must be greater than zero"
        )

    if args.output is None:

        output = args.input.with_suffix(
            ".png"
        )

    else:
        output = args.output

    try:

        reader = G24Reader(
            args.input
        )

        if args.info:
            print_info(reader)

        rgba, width, height = build_atlas(
            reader,
            args.section,
            args.remap,
            args.columns,
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        write_png(
            output,
            width,
            height,
            rgba,
        )

        print(
            f"Created: {output}"
        )

        print(
            f"Size:    {width} x {height}"
        )

        print(
            f"Tiles:   "
            f"{width // TILE_WIDTH} x "
            f"{height // TILE_HEIGHT}"
        )

        print(
            f"Section: {args.section}"
        )

        print(
            f"Remap:   {args.remap}"
        )

        return 0

    except (OSError, ValueError, IndexError) as exc:

        print(
            f"Error: {exc}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )

