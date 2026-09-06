"""Published fastener dimension tables (mm) with explicit provenance strings.

Nothing here is derived or interpolated. A size absent from a table is reported
as unchecked, never guessed.
"""
from __future__ import annotations

# ISO 273:1979 clearance holes for bolts and screws. (close, medium, coarse)
ISO273_CLEARANCE = {
    "M2": (2.2, 2.4, 2.6), "M2.5": (2.7, 2.9, 3.1), "M3": (3.2, 3.4, 3.6),
    "M4": (4.3, 4.5, 4.8), "M5": (5.3, 5.5, 5.8), "M6": (6.4, 6.6, 7.0),
    "M8": (8.4, 9.0, 10.0), "M10": (10.5, 11.0, 12.0), "M12": (13.0, 13.5, 14.5),
}
ISO273_SOURCE = "ISO 273:1979 clearance holes for bolts and screws, series %s, mm"

# ISO 4762 socket head cap screws: head diameter dk(max), head height k(max).
ISO4762_HEAD = {
    "M2": (3.8, 2.0), "M2.5": (4.5, 2.5), "M3": (5.5, 3.0), "M4": (7.0, 4.0),
    "M5": (8.5, 5.0), "M6": (10.0, 6.0), "M8": (13.0, 8.0), "M10": (16.0, 10.0),
    "M12": (18.0, 12.0),
}
ISO4762_SOURCE = "ISO 4762 socket head cap screw head dimensions dk(max)/k(max), mm"

# Counterbore diameter for ISO 4762 heads.
DIN974_COUNTERBORE = {
    "M3": 6.5, "M4": 8.0, "M5": 9.5, "M6": 11.0, "M8": 15.0, "M10": 18.0, "M12": 20.0,
}
DIN974_SOURCE = "DIN 974-1 counterbore diameter for ISO 4762 socket head cap screws, mm"

# Heat-set brass insert bosses. Promoted verbatim from
# scripts/verify-3dprint-tolerances.py HEATSET_SPECS (CNC Kitchen / Ruthex).
HEATSET = {
    "M2": {"pilot_d": 3.2, "depth": 4.2, "min_boss_d": 5.2},
    "M2.5": {"pilot_d": 3.6, "depth": 5.2, "min_boss_d": 6.2},
    "M3": {"pilot_d": 4.0, "depth": 7.0, "min_boss_d": 7.8},
    "M4": {"pilot_d": 5.6, "depth": 9.5, "min_boss_d": 10.0},
    "M5": {"pilot_d": 6.4, "depth": 11.0, "min_boss_d": 11.5},
}
HEATSET_SOURCE = ("CNC Kitchen / Ruthex heat-set insert boss table, promoted from "
                  "scripts/verify-3dprint-tolerances.py HEATSET_SPECS, mm")

_SERIES = {"close": 0, "medium": 1, "coarse": 2}


def expected_hole_diameter(fastener):
    """-> (diameter_mm | None, table_source, note).

    diameter_mm None means: this standard/size pair is not in any local table,
    so the gate reports the fastener check as unchecked instead of inventing it.
    """
    std = (fastener.get("standard") or "").strip()
    size = (fastener.get("size") or "").strip().upper()
    if std in ("ISO 273", "ISO 4762"):
        series = (fastener.get("series") or "medium").lower()
        if series not in _SERIES:
            return None, ISO273_SOURCE % series, "unknown ISO 273 series %r" % series
        row = ISO273_CLEARANCE.get(size)
        src = ISO273_SOURCE % series
        if row is None:
            return None, src, "size %s absent from the local ISO 273 table" % size
        return row[_SERIES[series]], src, "clearance hole for %s %s" % (std, size)
    if std == "heatset":
        row = HEATSET.get(size)
        if row is None:
            return None, HEATSET_SOURCE, "size %s absent from the local heat-set table" % size
        return row["pilot_d"], HEATSET_SOURCE, "heat-set insert pilot bore for %s" % size
    return None, "", "unknown fastener standard %r" % std


def heatset_min_depth(size):
    row = HEATSET.get((size or "").strip().upper())
    return (row["depth"], HEATSET_SOURCE) if row else (None, HEATSET_SOURCE)
