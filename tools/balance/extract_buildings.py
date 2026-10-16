#!/usr/bin/env python3
"""Derive ep-balance facts from the official wiki's stable building and recipe JSON."""

import argparse
import json
import math
from pathlib import Path

CLOCK_EXPONENT = math.log2(2.5)
BOOST_EXPONENT = 2.0


def stable_records(table: dict):
    """Selects the stable record for each wiki class."""
    for key, variants in table.items():
        stable = [record for record in variants if record.get("stable")]
        if len(stable) > 1:
            raise ValueError(f"multiple stable records for {key}")
        if stable:
            yield key, stable[0]


def building_key(descriptor: str) -> str:
    """Converts the wiki descriptor identifier to the building identifier used by scenarios."""
    if not descriptor.startswith("Desc_"):
        raise ValueError(f"not a building descriptor: {descriptor}")
    return "Build_" + descriptor.removeprefix("Desc_")


def extract(building_data: dict, recipe_data: dict, source: str) -> dict:
    """Extracts power facts without evaluating the simulation core's rules."""
    recipes = {}
    variable_buildings = set()
    for key, record in stable_records(recipe_data):
        if record.get("maxPower") is None or record["maxPower"] <= 0:
            continue
        building = building_key(record["producedIn"][0])
        variable_buildings.add(building)
        recipes[key] = {
            "name": record["name"],
            "building": building,
            "durationSeconds": record["duration"],
            "minMegawatts": record["minPower"],
            "maxMegawatts": record["maxPower"],
        }
    buildings = {}
    for descriptor, record in stable_records(building_data):
        if not descriptor.startswith("Desc_") and not (record["powerUsage"] or record["powerGenerated"]):
            continue
        key = building_key(descriptor)
        if not (record["powerUsage"] or record["powerGenerated"] or key in variable_buildings):
            continue
        buildings[key] = {
            "name": record["name"],
            "powerMegawatts": record["powerUsage"],
            "generatorMegawatts": record["powerGenerated"],
            "powerExponent": CLOCK_EXPONENT if record["overclockable"] else 1.0,
            "boostExponent": BOOST_EXPONENT,
        }
    if variable_buildings - buildings.keys():
        raise ValueError("variable recipes reference missing stable buildings")
    return {"source": source, "buildings": dict(sorted(buildings.items())),
            "variableRecipes": dict(sorted(recipes.items()))}


def main() -> None:
    """Reads downloaded wiki data and writes the derived fact table."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("buildings", type=Path)
    parser.add_argument("recipes", type=Path)
    parser.add_argument("--source", required=True, help="wiki URLs and revision identifiers")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    table = extract(json.loads(args.buildings.read_text()), json.loads(args.recipes.read_text()), args.source)
    args.output.write_text(json.dumps(table, indent=2) + "\n")


if __name__ == "__main__":
    main()
