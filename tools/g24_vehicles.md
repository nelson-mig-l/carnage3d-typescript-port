# `g24_vehicles.py` — Usage and Reference Notes

Decode vehicle records embedded in a GTA1/Carnage3D `STYLE###.G24` style archive. The script follows the vehicle-record layout in Carnage3D's `StyleData::ReadVehicles()` and reuses the project's `G24Reader` from `g24_to_png.py` to locate the vehicle section.

## Requirements

- Python 3
- The script `tools/g24_vehicles.py`
- The existing `tools/g24_to_png.py` module beside it
- A valid `STYLE###.G24` input file

No additional third-party Python packages are required.

## Basic usage

Run from the repository root:

```bash
python tools/g24_vehicles.py path/to/STYLE001.G24
```

By default, JSON is written next to the input file as `STYLE001_vehicles.json`.

### Choose the JSON output path

```bash
python tools/g24_vehicles.py STYLE001.G24 -o output/vehicles.json
```

### Also write a CSV summary

```bash
python tools/g24_vehicles.py STYLE001.G24 --csv output/vehicles.csv
```

Both formats can be specified together:

```bash
python tools/g24_vehicles.py STYLE001.G24 \\
  -o output/vehicles.json \\
  --csv output/vehicles.csv
```

## Output

The JSON document contains the source path, vehicle section offset and size, total vehicle count, and a `vehicles` array. Each vehicle record includes:

- `dimensions_raw_pixels`: width, height, depth as stored in the archive
- `sprite_number`: vehicle-local sprite number (`sprNum` in Carnage3D)
- performance/spec fields: weight, speeds, acceleration, braking, grip, handling
- `hls_remaps`: H/L/S remap triplets
- `vehicle_type_code` and decoded `vehicle_type` label
- `model_id`, `turning`, `damageable`, and `values`
- centre-of-mass coordinates and moment of inertia
- physics fields, both converted from 16.16 fixed-point values and raw integer values
- convertible and extra-driving-animation flags
- engine/radio/horn/sound settings
- `doors`: each door's `rpy`, `rpx`, `object`, and `delta` references
- `record_offset` and `record_size` to help inspect/debug binary records

The CSV is intended as a compact overview; nested remaps, physics values, and door structures are most completely represented in JSON.

## How the decoder was derived

The record reader follows the field sequence in `StyleData::ReadVehicles(std::ifstream& file, int dataLength)`:

1. Three signed 16-bit dimensions, followed by a signed 16-bit sprite number.
2. Seven signed 16-bit performance/spec values.
3. Twelve HLS remap triplets, each with three signed 16-bit values.
4. Twelve skipped 8-bit remap bytes.
5. Vehicle type, model ID, turning and damageability values.
6. Four 16-bit vehicle values, centre-of-mass coordinates, and moment of inertia.
7. Seven 16.16 fixed-point physics values; turn ratio and wheel offsets; two further fixed-point slide values.
8. Convertible/animation flags, five audio/setting bytes, door count, and four signed 16-bit values per door.

The decoder uses the vehicle section size from the G24 header to stop at the correct boundary. It also records each parsed record's byte offset and size, which makes it easier to compare parsing against the C++ reader.

## Important interpretation notes

- `sprite_number` is **not necessarily the absolute sprite metadata index**. Carnage3D calls `GetVehicleSpriteIndex(classID, sprNum)`, which first maps the vehicle class to a sprite category and adds that category's offset. This script exports the stored local number; it does not currently resolve the absolute sprite index.
- `vehicle_type_code` values are mapped from the `switch` in `ReadVehicles`: `0` bus, `1` front juggernaut, `2` back juggernaut, `3` motorcycle, `4` standard car, `8` train, `9` tram, `13` boat, `14` tank. Unknown values are labelled `unknown` rather than silently assigned a known class.
- Physics values read through `READ_FIXEDF32` are represented as raw signed 32-bit integers divided by 65536, alongside the raw values. Check against the C++ conversion macros if you need exact parity for unusual values.
- `dimensions_raw_pixels` preserves the three dimensions as stored. Carnage3D reorders them and converts pixels to metres when assigning `mDimensions`; the JSON deliberately labels these as raw values rather than claiming they are already world units.
- HLS remaps and door delta references are metadata only. This script does not render sprites, apply remaps to sprite pixels, or decode door/damage delta graphics.
- The script should be tested against real style archives and compared with Carnage3D output before being treated as a fully validated decoder.

## Reference material

### Carnage3D source code

- [`StyleData.cpp` — `StyleData::ReadVehicles()` and sprite-index mapping](https://github.com/codenamecpp/carnage3d/blob/master/src/StyleData.cpp): primary reference for vehicle record order, class-code mapping, and `GetVehicleSpriteIndex()` / `GetSpriteIndex()` behavior.
- [`GameDefs.h` — `VehicleInfo`, `CarDoorInfo`, vehicle classes, and constants](https://github.com/codenamecpp/carnage3d/blob/master/src/GameDefs.h): reference for vehicle fields, `MAX_CAR_REMAPS`, `MAX_CAR_DOORS`, and related data structures.

### Existing project tooling

- [`tools/g24_to_png.py`](./g24_to_png.py): reused for G24 header parsing, section sizing, alignment, and locating the vehicle records.
- [`tools/g24_vehicles.py`](./g24_vehicles.py): implementation of this decoder.

## Troubleshooting

- **Input file not found:** check the path and filename casing.
- **Vehicle section extends beyond end of G24 file:** the input may be truncated, use a different G24 variant, or have a section layout that differs from the expected format.
- **Vehicle record truncated / invalid door count:** parsing likely became misaligned or the archive uses a variant layout. Keep the original file unchanged and compare the offsets against Carnage3D's `ReadVehicles()`.
- **Unexpected sprite number:** remember that the stored number is category-local; Carnage3D resolves it through `GetVehicleSpriteIndex()`.

## Source links

- Carnage3D repository: https://github.com/codenamecpp/carnage3d
- Vehicle parser: https://github.com/codenamecpp/carnage3d/blob/master/src/StyleData.cpp
- Vehicle data definitions: https://github.com/codenamecpp/carnage3d/blob/master/src/GameDefs.h

