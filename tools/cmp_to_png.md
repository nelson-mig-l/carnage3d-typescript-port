# `cmp_to_png.py` Tool Manual

## Overview

`cmp_to_png.py` converts a Carnage3D / GTA1 `.CMP` map into six transparent top-down PNGs, one for each map height level.

The tool:

- Reads the 256×256 map from a `.CMP` file.
- Reconstructs all 6 map layers.
- Uses each block's G24 lid/top texture.
- Preserves lid rotation and flip flags.
- Makes cells without a block transparent.
- Writes a texture-usage report for every layer.
- Can make selected texture IDs transparent with `--skip-texture`.
- Can generate one combined composite map with `--composite`.
- Reuses the G24 decoder from `tools/g24_to_png.py`.

---

## Location

```text
tools/
├── cmp_to_png.py
├── cmp_to_png.md
└── g24_to_png.py
```

Run the script from the repository root.

---

## Requirements

Python 3.10 or newer is recommended.

```bash
python --version
```

No third-party Python packages are required.

---

# Basic Usage

```bash
python tools/cmp_to_png.py public/assets/data/NYC.CMP
```

The tool reads the style number from the CMP header and, unless `--style` is supplied, looks for:

```text
STYLE###.G24
```

beside the CMP file.

The default output is six PNG files and six matching text reports:

```text
NYC_layer_1.png
NYC_layer_1.txt
NYC_layer_2.png
NYC_layer_2.txt
NYC_layer_3.png
NYC_layer_3.txt
NYC_layer_4.png
NYC_layer_4.txt
NYC_layer_5.png
NYC_layer_5.txt
NYC_layer_6.png
NYC_layer_6.txt
```

---

# Command-Line Syntax

```text
python tools/cmp_to_png.py INPUT [OPTIONS]
```

### Positional argument

```text
INPUT
```

Path to the source `.CMP` map.

---

# Output Layers

GTA1 maps contain 6 height levels.

The tool creates one image for every level:

```text
_layer_1.png
_layer_2.png
...
_layer_6.png
```

**Important:** layer 6 is the bottom layer and layer 1 is the top layer. When layers are composited, they are drawn in the order **6 → 5 → 4 → 3 → 2 → 1**, so layer 1 appears above all lower layers.

Every output image represents 256 × 256 map cells. Each cell is rendered as a 64 × 64 pixel tile, making every output image 16384 × 16384 pixels.

---

# Transparency

The PNGs use RGBA pixels.

A cell is fully transparent when:

- There is no block at that height.
- Its texture ID is supplied with `--skip-texture`.

Empty pixels have alpha 0.

This makes the six images suitable for stacking or compositing.

---

# Texture Selection

For every populated cell, the tool reads the block's lid texture ID and decodes the corresponding 64×64 G24 lid texture.

The block's lid rotation, left/right flip, and top/bottom flip are applied before rendering.

---

# Texture Usage Reports

Every PNG has a matching text report. A report contains the number of map cells using each G24 lid texture:

```text
Layer 1
Total populated cells: 42,381
Unique textures: 127

Texture ID    Tile count
----------    ----------
12            8,421
7             6,103
45            3,882
...
```

Textures are sorted from most-used to least-used. The count is the number of map cells, not the number of pixels. Skipped textures are not included in the report.

---

# `-o`, `--output`

Specify an output prefix or PNG path.

```bash
python tools/cmp_to_png.py NYC.CMP -o nyc
```

Creates `nyc_layer_1.png` through `nyc_layer_6.png` and their matching reports.

A `.png` output path also works:

```bash
python tools/cmp_to_png.py NYC.CMP -o output.png
```

This creates `output_layer_1.png` through `output_layer_6.png`, plus the matching reports.

---

# `--output-dir`

Write all generated files into a directory:

```bash
python tools/cmp_to_png.py \
    public/assets/data/NYC.CMP \
    --output-dir maps/NYC
```

Result:

```text
maps/NYC/
├── NYC_layer_1.png
├── NYC_layer_1.txt
├── ...
├── NYC_layer_6.png
└── NYC_layer_6.txt
```

`--output` and `--output-dir` cannot be used together.

---

# `--style`

Specify the G24 style file explicitly:

```bash
python tools/cmp_to_png.py \
    public/assets/data/NYC.CMP \
    --style public/assets/data/STYLE001.G24
```

Use this when the style file is not beside the CMP or has a different filename.

---

# `--remap`

Select the G24 palette/remap variant.

Valid values are `0`, `1`, `2`, and `3`. The default is `0`.

Example:

```bash
python tools/cmp_to_png.py \
    public/assets/data/NYC.CMP \
    --remap 2
```

---

# `--composite`

Generate one additional combined map image containing all six height layers.

```bash
python tools/cmp_to_png.py \
    public/assets/data/NYC.CMP \
    --composite
```

The output is `NYC_composite.png`.

The composite uses this draw order:

```text
TOP
Layer 1
Layer 2
Layer 3
Layer 4
Layer 5
Layer 6
BOTTOM
```

In other words, the renderer draws **layer 6 → 5 → 4 → 3 → 2 → 1**. Layer 6 forms the background, while layer 1 is rendered last and appears above all lower layers.

The composite preserves RGBA transparency and alpha-composites partially transparent pixels. Cells with no block, invalid lid textures, or textures selected by `--skip-texture` remain transparent.

The composite is generated directly from the decoded CMP layers; it does not read the individual layer PNGs back from disk.

### Output naming

With `--composite`, the default output is:

```text
NYC_layer_1.png
...
NYC_layer_6.png
NYC_composite.png
```

With `--output-dir`:

```bash
python tools/cmp_to_png.py NYC.CMP \
    --output-dir maps/NYC \
    --composite
```

the composite is `maps/NYC/NYC_composite.png`.

With `-o`:

```bash
python tools/cmp_to_png.py NYC.CMP -o nyc --composite
```

the composite is `nyc_composite.png`.

The composite uses the same `--style`, `--remap`, and `--skip-texture` settings as the individual layer outputs.

---

# `--skip-texture`

Make one or more G24 texture IDs transparent.

Repeat the option for multiple IDs:

```bash
python tools/cmp_to_png.py \
    public/assets/data/NYC.CMP \
    --skip-texture 12 \
    --skip-texture 45 \
    --skip-texture 103
```

For skipped textures:

- Their map cells are fully transparent.
- They are not included in the texture-count reports.
- Other textures continue to render normally.

The console prints the skipped IDs when conversion starts.

---

# Progress Output

The converter reports progress while processing the map and every output layer.

Example:

```text
[1/3] Reading CMP: public/assets/data/NYC.CMP
      version=331, style=001, blocks=..., columns=...
[2/3] Decompressing map layers...
      map row   1/256
      map row   2/256
      ...
Rendering layer 1/6: NYC_layer_1.png
      layer 1/6, row   1/256
      layer 1/6, row   2/256
      ...
      complete: 42,381 populated cells, 127 unique textures
      report:   NYC_layer_1.txt
```

---

# Examples

## Convert a complete map

```bash
python tools/cmp_to_png.py public/assets/data/NYC.CMP
```

## Specify the style

```bash
python tools/cmp_to_png.py \
    public/assets/data/NYC.CMP \
    --style public/assets/data/STYLE001.G24
```

## Generate into a separate directory

```bash
python tools/cmp_to_png.py \
    public/assets/data/NYC.CMP \
    --output-dir maps/NYC
```

## Use another palette/remap

```bash
python tools/cmp_to_png.py \
    public/assets/data/NYC.CMP \
    --remap 1
```

## Skip several textures

```bash
python tools/cmp_to_png.py \
    public/assets/data/NYC.CMP \
    --skip-texture 12 \
    --skip-texture 45 \
    --skip-texture 103
```

---

# Recommended Workflow

A useful inspection workflow is:

```text
NYC.CMP
   │
   ├── STYLE###.G24
   │
   ▼
tools/cmp_to_png.py
   │
   ├── NYC_layer_1.png
   ├── NYC_layer_1.txt
   ├── NYC_layer_2.png
   ├── NYC_layer_2.txt
   ├── NYC_layer_3.png
   ├── NYC_layer_3.txt
   ├── NYC_layer_4.png
   ├── NYC_layer_4.txt
   ├── NYC_layer_5.png
   ├── NYC_layer_5.txt
   ├── NYC_layer_6.png
   ├── NYC_layer_6.txt
   └── NYC_composite.png
```

The individual PNGs provide the visual representation of each height. The composite provides the complete stacked view. The text files identify which textures dominate each layer.

---

# CMP Format

The converter currently expects the Carnage3D/GTA1 CMP format:

```text
Version: 331
Map:     256 × 256 cells
Layers:  6
```

The CMP stores compressed column information. Each map cell identifies a column containing the occupied block indices for that cell.

The converter reconstructs all occupied layers rather than selecting only the highest block.

---

# Memory and Performance

Each layer is 16384 × 16384 × 4 bytes. A fully expanded RGBA image would require roughly 1 GiB of raw pixel data.

The tool therefore streams PNG scanlines through zlib instead of constructing the entire image in memory.

The six layers are generated sequentially.

---

# Troubleshooting

## Style file not found

Use `--style`:

```bash
python tools/cmp_to_png.py NYC.CMP \
    --style path/to/STYLE001.G24
```

## Unsupported CMP version

The current converter expects version `331`. A different version requires additional format support.

## Conversion appears stuck

Watch the row counter. It reports both map decompression and PNG rendering progress. Because the images are very large, conversion can take a while.

## Large PNG files

Large output is expected because every image is 16384×16384 pixels. Transparent areas generally compress well.

---

# Return Codes

The tool returns `0` on success and `1` when an input, output, or format error occurs.

---

# Relationship to `g24_to_png.py`

The CMP converter reuses the existing G24 reader:

```python
from g24_to_png import G24Reader
```

Conceptually:

```text
CMP map
   │
   ▼
cmp_to_png.py
   │
   └── G24Reader
           │
           ▼
       STYLE###.G24
           │
           ▼
       64×64 lid texture
```

See `tools/g24_to_png.md` for details about the G24 texture format and palette handling.

---

# Future Improvements

Potential additions include:

- Side-texture rendering.
- Map coordinates in texture reports.
- JSON metadata for browser loading.
- Optional downscaled previews.
- Support for additional CMP versions.

---

# Complete Example

```bash
# Generate all six transparent map layers and texture reports.
python tools/cmp_to_png.py \
    public/assets/data/NYC.CMP \
    --output-dir maps/NYC

# Generate again while hiding selected textures.
python tools/cmp_to_png.py \
    public/assets/data/NYC.CMP \
    --output-dir maps/NYC-clean \
    --skip-texture 12 \
    --skip-texture 45 \
    --skip-texture 103
```
