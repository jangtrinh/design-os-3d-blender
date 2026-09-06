"""Host-side: compare reports/gui-object-inventory.json (live build) with
reports/rebuild-isolated.json (fresh factory-startup rebuild). Exit 1 on any drift.
Studio/diagnostic objects that only exist in one route are listed, not counted as drift.

only_gui is therefore printed but never fails the run: the GUI scene legitimately carries objects the
pass-01..18 rebuild never creates — the pass-24 / pass-28 film and detail-reel cameras above all, plus
any studio/diagnostic helper made after the rebuild range. An object present only in the isolated
rebuild (only_iso) IS a failure: the rebuild may not invent geometry the live build lacks."""
import json
import os
import sys

B = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
gui = json.load(open(os.path.join(B, "reports", "gui-object-inventory.json")))["inventory"]
iso = json.load(open(os.path.join(B, "reports", "rebuild-isolated.json")))["inventory"]
IGNORE = {"WW_CAM_CONTACT", "WW_CAM_CROP", "WW_CAM_DIAG", "WW_TEST_STRIP"}
only_gui = sorted(set(gui) - set(iso) - IGNORE)
only_iso = sorted(set(iso) - set(gui) - IGNORE)
drift = []
for name in sorted(set(gui) & set(iso)):
    a, b = gui[name], iso[name]
    for key in ("type", "parent", "role", "verts", "material", "modifiers"):
        if a.get(key) != b.get(key):
            drift.append((name, key, a.get(key), b.get(key)))
dups = [n for n in list(gui) + list(iso) if n[-4:-3] == "." and n[-3:].isdigit()]
print(json.dumps({"gui_count": len(gui), "iso_count": len(iso), "only_gui": only_gui, "only_iso": only_iso,
                  "drift": drift, "duplicate_suffix_names": dups}, indent=1))
sys.exit(1 if (only_iso or drift or dups) else 0)
