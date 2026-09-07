"""Shared helpers/constants for the bambu_checks_* modules: the single
result-shape constructor and the two stock Bambu bed sizes used by the
informational bed-fit check."""
from __future__ import annotations

BED_180 = (180.0, 180.0, 180.0)  # A1 mini
BED_256 = (256.0, 256.0, 256.0)  # X1 Carbon / P1S
BBOX_TOLERANCE_MM = 0.01


def result(check_id, status, note, measured=None):
    """One check's report entry: id/status/note/measured, no score field."""
    return {"id": check_id, "status": status, "note": note, "measured": measured or {}}
