"""Specs for the gate fixtures, all derived from specs/examples/bracket-m3.spec.json
so the example stays the single description of the positive part."""
import copy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXAMPLE = os.path.join(ROOT, "specs", "examples", "bracket-m3.spec.json")


def base():
    with open(EXAMPLE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def incomplete():
    """A part with no target dimensions: the contract itself is broken."""
    spec = base()
    del spec["parts"][0]["target_dims_mm"]
    return spec


def calibration():
    """Known bores of 3.4 and 5.0 mm at a tolerance tighter than any print."""
    spec = base()
    part = spec["parts"][0]
    part["target_dims_mm"] = [60.0, 24.0, 6.0]
    part["features"] = [
        {"id": "known34", "type": "hole", "axis": "z", "center_mm": [-15.0, 0.0, 0.0],
         "diameter_mm": 3.4, "tol_mm": 0.05},
        {"id": "known50", "type": "hole", "axis": "z", "center_mm": [15.0, 0.0, 0.0],
         "diameter_mm": 5.0, "tol_mm": 0.05},
    ]
    spec["required_checks"] = ["feature_known34_diameter_mm",
                              "feature_known50_diameter_mm"]
    return spec


def topology_only(dims, shells=1):
    spec = base()
    part = spec["parts"][0]
    part["target_dims_mm"] = list(dims)
    part["tol_mm"] = 0.5
    part["expected_shells"] = shells
    part.pop("features", None)
    part.pop("min_wall_mm", None)
    spec["required_checks"] = ["self_intersection_pairs"]
    return spec


def bed(dims, volume=None, margin=None):
    """A minimal spec (no holes/features) around a box of dims mm, plus
    optional print_volume_mm / brim_margin_mm overrides, for bed-fit tests."""
    spec = base()
    part = spec["parts"][0]
    part["target_dims_mm"] = list(dims)
    part["tol_mm"] = 0.05
    part.pop("features", None)
    part.pop("min_wall_mm", None)
    spec["required_checks"] = []
    if volume is not None:
        spec["print_volume_mm"] = list(volume)
    if margin is not None:
        spec["brim_margin_mm"] = margin
    return spec


def write(spec, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=2)
    return path


def clone(spec):
    return copy.deepcopy(spec)
