#!/usr/bin/env python3
"""Prove the CK-001 E02 electrical verifier rejects representative dangerous mutations."""
import argparse
import copy
import json
from pathlib import Path

import verify

HERE = Path(__file__).resolve().parent


def rejected(name, mutate):
    docs = copy.deepcopy(verify.load_documents())
    mutate(docs)
    try:
        verify.validate(docs)
    except verify.DesignError as exc:
        return {"id": name, "status": "pass", "rejected_with": str(exc)}
    raise AssertionError(f"negative control unexpectedly passed: {name}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--report", type=Path); args = ap.parse_args()
    rows = [
        rejected("usb_data_short", lambda d: d["logical-netlist"]["usb"]["data_minus"].update(mcu_pin="USB_DP")),
        rejected("missing_key_diode", lambda d: d["logical-netlist"]["matrix"]["keys"][17].update(diode="")),
        rejected("usb_cc_missing_rd", lambda d: d["logical-netlist"]["usb"]["cc2"].update(rd_ohm=0)),
        rejected("power_limit_over_500mA", lambda d: d["power-budget"]["input_current_limit"]["datasheet_table_current_limit_mA"].update(max=650)),
        rejected("gpio_reuse", lambda d: d["logical-netlist"]["encoders"][0].update(a_pin="GP0")),
        rejected("rgb_common_cathode_regression", lambda d: d["logical-netlist"]["rgb"].update(
            led_mpn="19-237B/R6GHBHC-C01/2T", led_topology="common cathode to SWx",
            led_pins={"common_cathode":4,"anodes":{"red":2,"green":1,"blue":3}})),
    ]
    out = {"schema_version":1,"design_id":"CK-001-E02","status":"PASS_NEGATIVE_CONTROLS_E02","controls":rows,
           "supersedes":{"design_id":"CK-001-E01","reason":"adds explicit common-cathode regression falsifier"}}
    raw = json.dumps(out, indent=2, allow_nan=False) + "\n"
    if args.report:
        path = args.report.resolve()
        if not path.is_relative_to(HERE): raise ValueError("report must stay in electrical namespace")
        with path.open("x", encoding="utf-8") as handle: handle.write(raw)
    print(json.dumps({"status":out["status"],"controls":len(rows),"report":str(args.report) if args.report else None}))


if __name__ == "__main__": main()
