# `g24_to_png.py` Tool Manual

## Overview

`g24_to_png.py` converts Carnage3D / GTA1 `.G24` texture files into standard PNG texture atlases.

The converter is designed around the texture-loading implementation used by Carnage3D and understands the following `.G24` components:

* 64×64 indexed block textures
* Side, lid, and auxiliary texture sections
* 256×256 texture pages
* 256-entry color lookup tables (CLUTs)
* Four palette/remap variants per block
* Transparent palette index `0`
* BGRA palette storage

The generated PNG files can be used for inspecting the original Carnage3D artwork and as source material for the TypeScript/Babylon.js port.

---

## Location

Recommended location in the repository:

```text
tools/
└── g24_to_png.py
```

The tool does not require any third-party Python packages.

It uses only the Python standard library.

---

## Requirements

Python 3.10 or newer is recommended.

Check the installed version:

```bash
python --version
```

or:

```bash
python3 --version
```

No `pip install` step is required.

---

# Basic Usage

The simplest invocation is:

```bash
python tools/g24_to_png.py STYLE001.G24
```

The PNG is written next to the source file:

```text
STYLE001.G24
STYLE001.png
```

The default conversion exports all available block textures using:

```text
section = all
remap = 0
columns = 4
```

---

# Command-Line Syntax

```text
python tools/g24_to_png.py INPUT [OPTIONS]
```

### Positional argument

```text
INPUT
```

Path to the source `.G24` file.

Example:

```bash
python tools/g24_to_png.py carnage/data/STYLE001.G24
```

---

# Options

## `-o`, `--output`

Specify the output PNG filename.

Example:

```bash
python tools/g24_to_png.py \
    STYLE001.G24 \
    --output public/assets/textures/STYLE001.png
```

Short form:

```bash
python tools/g24_to_png.py STYLE001.G24 -o STYLE001.png
```

When this option is omitted, the tool replaces the `.G24` extension with `.png`.

---

## `--section`

Select which texture section should be exported.

Available values:

```text
all
side
lid
aux
```

Default:

```text
all
```

### Export all textures

```bash
python tools/g24_to_png.py STYLE001.G24 \
    --section all
```

The atlas contains:

```text
side → lid → aux
```

in the original linear block order.

### Export side textures

```bash
python tools/g24_to_png.py STYLE001.G24 \
    --section side \
    -o STYLE001_side.png
```

### Export lid textures

```bash
python tools/g24_to_png.py STYLE001.G24 \
    --section lid \
    -o STYLE001_lid.png
```

### Export auxiliary textures

```bash
python tools/g24_to_png.py STYLE001.G24 \
    --section aux \
    -o STYLE001_aux.png
```

Separating the sections is recommended when building texture assets for the TypeScript port.

---

# `--remap`

Select which palette/remap variant to use.

Valid values:

```text
0
1
2
3
```

Default:

```text
0
```

Example:

```bash
python tools/g24_to_png.py STYLE001.G24 \
    --remap 1 \
    -o STYLE001_remap1.png
```

Each block has four palette indices.

The converter accesses them using the equivalent of:

```text
4 * blockLinearIndex + remap
```

Therefore:

```text
--remap 0 → first palette
--remap 1 → second palette
--remap 2 → third palette
--remap 3 → fourth palette
```

Different remaps may represent different colour variants of the same source texture.

---

# `--columns`

Controls how many 64×64 tiles are placed across the generated PNG.

Default:

```text
4
```

The default value preserves the native G24 page width:

```text
4 × 64 = 256 pixels
```

Example:

```bash
python tools/g24_to_png.py STYLE001.G24 \
    --columns 8 \
    -o STYLE001_wide.png
```

With 8 columns, the resulting atlas will be:

```text
8 × 64 = 512 pixels wide
```

The tile order itself does not change; only the presentation of the atlas changes.

For reproducing the original G24 layout, use:

```bash
--columns 4
```

---

# `--info`

Print information about the `.G24` file without requiring the user to inspect the binary format manually.

Example:

```bash
python tools/g24_to_png.py STYLE001.G24 --info
```

Example output:

```text
G24 information
----------------
Version:           336
Side blocks:      195
Lid blocks:       154
Aux blocks:        37
Total blocks:     386
Tile CLUTs:      1544
Animation bytes:  41
CLUT bytes:      991232
CLUT bytes padded: 1048576
Palette index data: 4458
```

This information is useful for checking whether a `.G24` file has been parsed correctly.

---

# Output Atlas Layout

Each decoded block is:

```text
64 × 64 pixels
```

With the default four-column layout, the atlas is:

```text
256 pixels wide
```

For a file containing 386 blocks:

```text
386 / 4 = 96.5
```

Therefore the converter needs:

```text
97 rows
```

and the output dimensions are:

```text
256 × 6208
```

because:

```text
97 × 64 = 6208
```

The last row contains two unused tile positions.

---

# Texture Section Order

For `--section all`, block indices are laid out as:

```text
Side blocks
    ↓
Lid blocks
    ↓
Auxiliary blocks
```

For example, if the file contains:

```text
195 side blocks
154 lid blocks
37 aux blocks
```

the linear texture ranges are:

```text
0   – 194    Side
195 – 348    Lid
349 – 385    Aux
```

This ordering is important when matching generated atlas tiles with Carnage3D block indices.

---

# G24 Texture Format

The converter is specifically intended for the G24 format used by Carnage3D.

## Header

The G24 header consists of 16 little-endian 32-bit unsigned integers:

```text
16 × uint32 = 64 bytes
```

The first value is the format/version code.

Carnage3D G24 files use:

```text
336
```

The script therefore expects:

```python
HEADER_FORMAT = "<16I"
G24_VERSION = 336
```

---

# Block Texture Storage

Block textures are stored as 8-bit palette indices.

Each block is:

```text
64 × 64 = 4096 bytes
```

The source format packs four 64×64 blocks across a 256-pixel-wide page.

Conceptually:

```text
+--------+--------+--------+--------+
|  tile  |  tile  |  tile  |  tile  |
|   0    |   1    |   2    |   3    |
+--------+--------+--------+--------+
|  tile  |  tile  |  tile  |  tile  |
|   4    |   5    |   6    |   7    |
+--------+--------+--------+--------+
|        ...                        |
+-----------------------------------+
```

The converter extracts the correct 64×64 region from this arrangement before converting the palette indices to RGBA pixels.

---

# Palette / CLUT Handling

G24 textures are palette indexed.

A pixel in the texture does not directly contain an RGB colour.

Instead it contains a value:

```text
0–255
```

which refers to an entry in a 256-colour palette.

The tool resolves the palette using the block's palette/remap index.

The CLUT structure contains:

```text
64 palettes per 64 KiB page
256 entries per palette
4 bytes per entry
```

The source colour order is:

```text
B G R A
```

The converter converts this to PNG's:

```text
R G B A
```

---

# Transparency

Carnage3D uses palette index `0` as transparent for the RGBA texture path.

The converter therefore produces:

```text
palette index 0 → alpha = 0
all other indices → alpha = 255
```

The generated PNG is a true RGBA PNG.

This means transparent areas should remain transparent when opened in an image editor or loaded into Babylon.js.

---

# Examples

## Convert a complete G24 file

```bash
python tools/g24_to_png.py \
    carnage/data/STYLE001.G24
```

Output:

```text
carnage/data/STYLE001.png
```

---

## Convert directly into the runtime asset directory

```bash
python tools/g24_to_png.py \
    carnage/data/STYLE001.G24 \
    -o public/assets/textures/STYLE001.png
```

This is useful when generating assets for the browser version of Carnage3D.

---

## Export side textures

```bash
python tools/g24_to_png.py \
    carnage/data/STYLE001.G24 \
    --section side \
    -o public/assets/textures/STYLE001_side.png
```

---

## Export lid textures

```bash
python tools/g24_to_png.py \
    carnage/data/STYLE001.G24 \
    --section lid \
    -o public/assets/textures/STYLE001_lid.png
```

---

## Export auxiliary textures

```bash
python tools/g24_to_png.py \
    carnage/data/STYLE001.G24 \
    --section aux \
    -o public/assets/textures/STYLE001_aux.png
```

---

## Export another palette remap

```bash
python tools/g24_to_png.py \
    STYLE001.G24 \
    --remap 2 \
    -o STYLE001_remap2.png
```

---

## Inspect a file before converting it

```bash
python tools/g24_to_png.py \
    STYLE001.G24 \
    --info
```

---

## Generate a wider atlas

```bash
python tools/g24_to_png.py \
    STYLE001.G24 \
    --columns 8 \
    -o STYLE001_8col.png
```

---

# Recommended Asset Workflow

For the TypeScript port, a useful workflow is:

```text
carnage/
    original G24 files
          │
          ▼
tools/g24_to_png.py
          │
          ▼
public/assets/textures/
    STYLE001_side.png
    STYLE001_lid.png
    STYLE001_aux.png
```

The original `.G24` files should remain in the source/reference tree.

The generated PNG files should be treated as runtime/browser assets.

This keeps the browser build independent from the original binary texture format.

---

# Babylon.js Integration

Generated PNG files can be loaded by the Phase 2 asset pipeline.

For example:

```typescript
const texture = new BABYLON.Texture(
  './assets/textures/STYLE001_side.png',
  scene,
);
```

The project uses relative runtime paths so that assets work correctly when deployed below a GitHub Pages project path.

Use:

```text
./assets/...
```

rather than:

```text
/assets/...
```

---

# Troubleshooting

## `G24Header.__init__()` receives too many arguments

Make sure the header format is:

```python
HEADER_FORMAT = "<16I"
```

not:

```python
HEADER_FORMAT = "<17I"
```

The G24 header contains 16 32-bit values.

---

## `Unsupported G24 version`

Example:

```text
Error: Unsupported G24 version 123; Carnage3D expects 336
```

The input file is either:

* not a Carnage3D G24 file,
* a different generation/version of the format, or
* being read from the wrong file.

---

## `side_size is not a multiple of 4096`

Each block is:

```text
64 × 64 = 4096 bytes
```

A valid block texture section should therefore have a size divisible by 4096.

---

## Palette outside CLUT data

Example:

```text
Error: Palette 12345 is outside the CLUT data
```

This usually indicates one of:

* the file is not the expected G24 format,
* the header was interpreted incorrectly,
* the file is truncated,
* the CLUT data is corrupt.

---

## The PNG looks completely wrong

Check:

```bash
python tools/g24_to_png.py STYLE001.G24 --info
```

Then verify the reported:

```text
Version
Side blocks
Lid blocks
Aux blocks
Total blocks
CLUT bytes
Palette index data
```

Also try each remap:

```bash
python tools/g24_to_png.py STYLE001.G24 --remap 0 -o remap0.png
python tools/g24_to_png.py STYLE001.G24 --remap 1 -o remap1.png
python tools/g24_to_png.py STYLE001.G24 --remap 2 -o remap2.png
python tools/g24_to_png.py STYLE001.G24 --remap 3 -o remap3.png
```

Different remaps can produce different colour variants.

---

# Return Codes

The tool returns:

```text
0
```

when conversion succeeds.

It returns:

```text
1
```

when an input/output or format error occurs.

This makes the script suitable for use in shell scripts and CI pipelines.

Example:

```bash
python tools/g24_to_png.py STYLE001.G24

if [ $? -ne 0 ]; then
    echo "G24 conversion failed"
    exit 1
fi
```

---

# Design Notes

The converter intentionally has no dependency on Pillow or another image-processing package.

PNG output is written directly using:

```python
struct
zlib
```

This makes the tool:

* portable
* easy to run in CI
* easy to run from GitHub Actions
* independent of Python package installation
* suitable for asset-generation workflows

The decoding logic is kept separate from PNG generation so the G24 reader can later be reused for other exporters.

---

# Future Improvements

Potential future additions include:

* Export every block as an individual PNG.
* Generate one atlas for side, lid, and aux textures automatically.
* Generate JSON atlas metadata.
* Include original block indices in filenames.
* Export all four palette/remap variants at once.
* Generate Babylon.js-compatible texture metadata.
* Add batch processing for an entire directory of `.G24` files.
* Add validation against known Carnage3D texture samples.
* Add preview/contact-sheet generation.
* Preserve palette index data in optional metadata.

---

# Example Complete Workflow

```bash
# Inspect the source file
python tools/g24_to_png.py \
    carnage/data/STYLE001.G24 \
    --info

# Generate the complete texture atlas
python tools/g24_to_png.py \
    carnage/data/STYLE001.G24 \
    --section all \
    --remap 0 \
    --columns 4 \
    -o public/assets/textures/STYLE001.png
```

Result:

```text
public/assets/textures/
└── STYLE001.png
```

For the example file containing 195 side blocks, 154 lid blocks, and 37 auxiliary blocks:

```text
Total blocks: 386
Atlas columns: 4
Atlas rows: 97
Tile size: 64 × 64
PNG size: 256 × 6208
```

The generated atlas preserves the original linear block ordering and converts the indexed G24 texture data into standard RGBA PNG pixels.
