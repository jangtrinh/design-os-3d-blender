"""Aggregator for the 10 phase-04 check predicates. Re-exports every
check_* function from bambu_checks_container.py (checks 1-5) and
bambu_checks_plates.py (checks 6-10) so callers only need
`import bambu_checks as checks`, and defines the fixed run order used by
validate_bambu_3mf.py.
"""
from __future__ import annotations

from bambu_checks_container import (  # noqa: F401 (re-exported)
    check_bambu_project_layout,
    check_build_items_placed,
    check_container_zip,
    check_geometry_resolved,
    check_plate_membership,
)
from bambu_checks_plates import (  # noqa: F401 (re-exported)
    check_bed_fit,
    check_per_plate_bbox_mm,
    check_settings_types,
    check_slice_info_present,
    check_thumbnail_present,
)

CHECK_ORDER = (
    check_container_zip,
    check_bambu_project_layout,
    check_geometry_resolved,
    check_build_items_placed,
    check_plate_membership,
    check_per_plate_bbox_mm,
    check_bed_fit,
    check_settings_types,
    check_slice_info_present,
    check_thumbnail_present,
)
