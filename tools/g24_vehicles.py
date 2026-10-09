#!/usr/bin/env python3
"""Decode the vehicle records in a Carnage3D/GTA1 STYLE###.G24 file.

The binary layout follows Carnage3D StyleData::ReadVehicles(). This exports
vehicle metadata to JSON and CSV, including sprite-number references, HLS
remaps, physics/spec values, flags, and per-door delta references.

Usage:
    python tools/g24_vehicles.py STYLE001.G24
    python tools/g24_vehicles.py STYLE001.G24 -o vehicles.json
    python tools/g24_vehicles.py STYLE001.G24 --csv vehicles.csv

No third-party packages are required.
"""
from __future__ import annotations

import argparse
import csv
import json
import struct
import sys
from pathlib import Path

from g24_to_png import CLUT_PAGE_SIZE, G24Reader, HEADER_SIZE, round_up

VEHICLE_TYPES = {
    0: "bus",
    1: "front_of_juggernaut",
    2: "back_of_juggernaut",
    3: "motorcycle",
    4: "standard_car",
    8: "train",
    9: "tram",
    13: "boat",
    14: "tank",
}
# Carnage3D constants used by ReadVehicles.
MAX_CAR_REMAPS = 12
MAX_CAR_DOORS = 4
REMAP_8BIT_BYTES = MAX_CAR_REMAPS
FIXED_FIELDS = (
    "mass", "thrust", "tyre_adhesion_x", "tyre_adhesion_y",
    "handbrake_friction", "footbrake_friction", "front_brake_bias",
)
TRAILING_FIXED_FIELDS = ("back_end_slide_value", "handbrake_slide_value")


class Cursor:
    def __init__(self, data: bytes, offset: int, end: int):
        self.data = data
        self.offset = offset
        self.end = end

    def unpack(self, fmt: str, label: str):
        size = struct.calcsize(fmt)
        if self.offset + size > self.end:
            raise ValueError(f"Vehicle record truncated while reading {label} at {self.offset:#x}")
        values = struct.unpack_from(fmt, self.data, self.offset)
        self.offset += size
        return values if len(values) > 1 else values[0]


def locate_vehicle_section(reader: G24Reader) -> tuple[int, int]:
    h = reader.header
    padded_blocks = round_up(h.total_blocks, 4)
    offset = HEADER_SIZE + padded_blocks * 64 * 64
    offset += h.anim_size + round_up(h.clut_size, CLUT_PAGE_SIZE)
    offset += h.palette_index_size + h.object_info_size
    if offset + h.car_size > len(reader.data):
        raise ValueError("Vehicle section extends beyond end of G24 file")
    return offset, h.car_size


def parse_vehicles(data: bytes, offset: int, length: int) -> list[dict]:
    end = offset + length
    vehicles = []
    while offset < end:
        start = offset
        c = Cursor(data, offset, end)

        width, height, depth = c.unpack("<3h", "dimensions")
        sprite_number = c.unpack("<h", "sprite number")
        weight, max_speed, min_speed, acceleration, braking, grip, handling = c.unpack(
            "<7h", "vehicle specs"
        )
        remaps = []
        for remap_index in range(MAX_CAR_REMAPS):
            hue, luminance, saturation = c.unpack("<3h", f"remap {remap_index}")
            remaps.append({"h": hue, "l": luminance, "s": saturation})
        c.unpack(f"<{REMAP_8BIT_BYTES}B", "8-bit remaps")

        type_code = c.unpack("<B", "vehicle type")
        model_id = c.unpack("<B", "model id")
        turning = c.unpack("<B", "turning")
        damageable = c.unpack("<B", "damageable")
        values = list(c.unpack("<4h", "vehicle values"))
        cx, cy = c.unpack("<2b", "centre of mass")
        moment = c.unpack("<i", "moment of inertia")
        fixed = list(c.unpack("<7i", "physics fixed-point values"))
        turn_ratio, drive_wheel_offset, steering_wheel_offset = c.unpack("<3h", "wheel/turn settings")
        trailing_fixed = list(c.unpack("<2i", "slide fixed-point values"))
        flags = c.unpack("<B", "vehicle flags")
        engine, radio, horn, sound_function, fast_change = c.unpack("<5B", "vehicle audio/settings")
        door_count = c.unpack("<h", "door count")
        if door_count < 0 or door_count > MAX_CAR_DOORS:
            raise ValueError(f"Vehicle {len(vehicles)} has invalid door count {door_count}")
        doors = []
        for door_index in range(door_count):
            rpy, rpx, object_id, delta_id = c.unpack("<4h", f"door {door_index}")
            doors.append({"rpy": rpy, "rpx": rpx, "object": object_id, "delta": delta_id})

        consumed = c.offset - start
        if consumed <= 0:
            raise ValueError("Vehicle parser made no progress")
        offset = c.offset
        vehicle_index = len(vehicles)
        vehicles.append({
            "vehicle_index": vehicle_index,
            "record_offset": start,
            "record_size": consumed,
            "dimensions_raw_pixels": {"width": width, "height": height, "depth": depth},
            "sprite_number": sprite_number,
            "weight": weight,
            "max_speed": max_speed,
            "min_speed": min_speed,
            "acceleration": acceleration,
            "braking": braking,
            "grip": grip,
            "handling": handling,
            "hls_remaps": remaps,
            "vehicle_type_code": type_code,
            "vehicle_type": VEHICLE_TYPES.get(type_code, "unknown"),
            "model_id": model_id,
            "turning": turning,
            "damageable": bool(damageable),
            "values": values,
            "centre_of_mass_pixels": {"x": cx, "y": cy},
            "moment_of_inertia": moment,
            "physics": {name: raw / 65536.0 for name, raw in zip(FIXED_FIELDS, fixed)},
            "physics_fixed_raw": dict(zip(FIXED_FIELDS, fixed)),
            "turn_ratio": turn_ratio,
            "drive_wheel_offset": drive_wheel_offset,
            "steering_wheel_offset": steering_wheel_offset,
            "slide_values": {name: raw / 65536.0 for name, raw in zip(TRAILING_FIXED_FIELDS, trailing_fixed)},
            "slide_values_fixed_raw": dict(zip(TRAILING_FIXED_FIELDS, trailing_fixed)),
            "convertible": bool(flags & 1),
            "extra_driving_animation": bool(flags & 2),
            "vehicle_flags_raw": flags,
            "engine": engine,
            "radio": radio,
            "horn": horn,
            "sound_function": sound_function,
            "fast_change_flag": fast_change,
            "doors": doors,
        })
    if offset != end:
        raise ValueError(f"Vehicle section length mismatch: parsed to {offset:#x}, expected {end:#x}")
    return vehicles


def main() -> int:
    parser = argparse.ArgumentParser(description="Decode vehicle records from a GTA1/Carnage3D G24 style file.")
    parser.add_argument("input", type=Path, help="Input STYLE###.G24")
    parser.add_argument("-o", "--output", type=Path, help="JSON output path (default: <input>_vehicles.json)")
    parser.add_argument("--csv", type=Path, help="Also write a flat CSV summary to this path")
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"Input file does not exist: {args.input}")
    output = args.output or args.input.with_name(args.input.stem + "_vehicles.json")
    try:
        reader = G24Reader(args.input)
        offset, length = locate_vehicle_section(reader)
        vehicles = parse_vehicles(reader.data, offset, length)
        document = {
            "source": str(args.input),
            "vehicle_section_offset": offset,
            "vehicle_section_size": length,
            "vehicle_count": len(vehicles),
            "vehicles": vehicles,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        print(f"Vehicles: {len(vehicles)}")
        print(f"JSON: {output}")
        if args.csv:
            args.csv.parent.mkdir(parents=True, exist_ok=True)
            fields = [
                "vehicle_index", "vehicle_type_code", "vehicle_type", "model_id",
                "sprite_number", "weight", "max_speed", "min_speed", "acceleration",
                "braking", "grip", "handling", "damageable", "convertible",
                "extra_driving_animation", "door_count",
            ]
            with args.csv.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                for vehicle in vehicles:
                    row = dict(vehicle)
                    row["door_count"] = len(vehicle["doors"])
                    writer.writerow(row)
            print(f"CSV: {args.csv}")
        return 0
    except (OSError, ValueError, IndexError, struct.error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
