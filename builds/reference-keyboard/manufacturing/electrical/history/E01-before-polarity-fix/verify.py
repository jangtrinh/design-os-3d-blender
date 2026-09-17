#!/usr/bin/env python3
"""Host-side consistency checks for CK-001 E01 logical electrical authority."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


class DesignError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise DesignError(message)


def load(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_documents(base=HERE):
    names = ("authority", "logical-netlist", "firmware-config", "pin-map", "power-budget", "bom", "source-registry", "status")
    return {name: load(base / f"{name}.json") for name in names}


def gpio_owners(net):
    owners = []
    for i, pin in enumerate(net["matrix"]["row_pins"]): owners.append((pin, f"row{i}"))
    for i, pin in enumerate(net["matrix"]["col_pins"]): owners.append((pin, f"col{i}"))
    for encoder in net["encoders"]:
        owners += [(encoder["a_pin"], encoder["id"] + ".A"), (encoder["b_pin"], encoder["id"] + ".B")]
    owners += [(net["i2c"]["sda"], "i2c.sda"), (net["i2c"]["scl"], "i2c.scl"),
               (net["rgb"]["sdb_pin"], "rgb.sdb"), (net["power"]["fault_pin"], "power.fault")]
    return owners


def validate(documents=None):
    d = documents or load_documents()
    a, n, fw, pinmap, power, bom, sources, status = (d[k] for k in
        ("authority", "logical-netlist", "firmware-config", "pin-map", "power-budget", "bom", "source-registry", "status"))
    checks = []
    def check(name, condition, evidence):
        need(condition, f"{name}: {evidence}")
        checks.append({"id": name, "status": "pass", "evidence": evidence})

    check("identity", all(x.get("design_id") == "CK-001-E01" for x in (a,n,fw,bom,status)), "design_id CK-001-E01")
    for role, pin in a["build_binding"].items():
        if role == "observed_counts": continue
        path = (ROOT / pin["path"]).resolve()
        check("binding_" + role, path.is_relative_to(ROOT) and path.is_file() and digest(path) == pin["sha256"], pin["path"])
    counts = a["build_binding"]["observed_counts"]
    check("source_counts", counts == {"keys":58,"encoders":5,"key_rgb":58,"perimeter_rgb":49,"rgb_total":107}, counts)

    matrix = n["matrix"]; keys = matrix["keys"]
    cells = [tuple(k["matrix"]) for k in keys]
    check("matrix_shape", (matrix["rows"], matrix["cols"], len(keys)) == (6,10,58), [matrix["rows"],matrix["cols"],len(keys)])
    check("matrix_cells_unique", len(set(cells)) == 58 and all(0 <= r < 6 and 0 <= c < 10 for r,c in cells), len(set(cells)))
    check("matrix_sparse_cells", sorted(map(tuple,matrix["unused_cells"])) == [(5,8),(5,9)] and set(cells) | {(5,8),(5,9)} == {(r,c) for r in range(6) for c in range(10)}, matrix["unused_cells"])
    check("diodes", matrix["diode_direction"] == "COL2ROW" and matrix["diode_cathode"] == "ROW" and
          len({k["diode"] for k in keys}) == 58 and all(k["diode"] and "diode cathode -> ROW" in k["topology"] for k in keys), "58 unique BAS316 logical diodes COL2ROW")
    layout = load(ROOT / "builds/reference-keyboard/layout.json")
    check("key_binding", [k["id"] for k in keys] == [f"RK_KEY_{i:02d}" for i in range(58)] and
          fw["matrix"]["keys"] == [{"id":k["id"],"matrix":k["matrix"]} for k in keys] and
          layout["key_travel_mm"] == 3.0, "58 current-B keys; firmware matrix map identical")

    owners = gpio_owners(n); pins = [p for p,_ in owners]
    expected = {f"GP{i}" for i in range(30)}
    check("gpio_ownership", len(pins) == 30 and len(set(pins)) == 30 and set(pins) == expected, owners)
    map_pins = pinmap["pins"]
    check("gpio_modes", len(map_pins) == 30 and {x["pin"] for x in map_pins} == expected and len({x["owner"] for x in map_pins}) == 30 and
          next(x for x in map_pins if x["pin"] == "GP28")["boot_requirement"].startswith("100k hardware pull-down") and
          next(x for x in map_pins if x["pin"] == "GP29")["runtime_mode"] == "digital input",
          "30 explicit runtime/boot I/O contracts; GP28 hardware-off, GP29 fault input")
    enc = n["encoders"]
    check("encoders", len(enc) == 5 and all(not e["push_switch"] and e["mpn"] == "PEC11R-1215F-N0024" for e in enc), "5 direct quadrature encoders, no push switches")
    check("encoder_filters", all(e["filter"] == {"pullup_ohm":10000,"pullup_rail":"3V3","series_ohm":10000,"cap_to_ground_nF":10} for e in enc), "10k pull-up + 10k series + 10nF per A/B")

    usb = n["usb"]
    check("usb_cc", all(usb[x] == {"rd_ohm":5100,"tolerance_percent":1,"to":"GND"} for x in ("cc1","cc2")) and usb["sbu1"] == usb["sbu2"] == "NC", "two independent 5.1k Rd; SBU NC")
    check("usb_data", usb["esd"] == "USBLC6-2SC6" and usb["data_plus"]["series_ohm"] == usb["data_minus"]["series_ohm"] == 27 and
          {usb["data_plus"]["mcu_pin"],usb["data_minus"]["mcu_pin"]} == {"USB_DP","USB_DM"}, "USB2 ESD + 27R source termination")
    check("i2c", n["i2c"] == {"bus":"I2C1","sda":"GP18","scl":"GP19","pullup_rail":"3V3","pullup_ohm":4700,"frequency_hz":400000,"devices":[{"ref":"U5","address_7bit":"0x30","addr_pin":"GND"}]}, "3V3 I2C1; U5 address 0x30")

    rgb = n["rgb"]; mapping = rgb["mapping"]
    channels = [(x["sw"],x["cs"][c]) for x in mapping for c in ("r","g","b")]
    check("rgb_mapping", len(mapping) == 107 and len(channels) == 321 and len(set(channels)) == 321 and all(1 <= sw <= 9 and 1 <= cs <= 39 for sw,cs in channels), "107 RGB / 321 unique channels")
    check("rgb_hardware", rgb["driver"] == "IS31FL3741A-QFLS4-TR" and rgb["supply"] == "RGB_5V1" and rgb["riset_ohm"] == 120000 and rgb["sdb_pulldown_ohm"] == 100000, "120k RISET; RGB_5V1; SDB 100k default-off")
    nominal = 383 / 120 * (255/256) * (255/256)
    conservative = nominal * (41.04/38) / .99
    check("rgb_current_math", abs(power["rgb_driver"]["hardware_full_scale_peak_channel_nominal_mA"]-nominal) < 1e-4 and
          abs(power["rgb_driver"]["hardware_full_scale_peak_channel_conservative_mA"]-conservative) < 1e-4 and conservative < 5.0,
          {"nominal_mA":round(nominal,5),"conservative_mA":round(conservative,5)})
    limit = power["input_current_limit"]["datasheet_table_current_limit_mA"]
    boost = n["power"]["rgb_boost"]
    pboost = power["rgb_boost"]
    check("logic_regulator", n["power"]["regulator"] == "TLV75533PDBVR" and power["logic_regulator"]["device"] == "TLV75533PDBVR" and power["logic_regulator"]["output_cap_uF"] >= 1, "TLV75533PDBVR, ceramic-stable LDO")
    fb_tolerance = pboost["feedback_resistor_tolerance_percent"] / 100
    rtop, rbot = boost["fb_top_ohm"], boost["fb_bottom_ohm"]
    vref = pboost["vref_pwm_mV"]
    vout_min = vref["min"] / 1000 * (1 + rtop * (1-fb_tolerance) / (rbot * (1+fb_tolerance)))
    vout_nom = vref["typ"] / 1000 * (1 + rtop / rbot)
    vout_max = vref["max"] / 1000 * (1 + rtop * (1+fb_tolerance) / (rbot * (1-fb_tolerance)))
    check("rgb_boost", boost["device"] == "TPS61023DRLR" and boost["output"] == "RGB_5V1" and rtop == 750000 and rbot == 100000 and boost["inductor"] == "XEL4030-102MEC" and vout_max < 5.5, {"min":round(vout_min,5),"nominal":round(vout_nom,5),"max":round(vout_max,5)})
    check("rgb_boost_voltage_math", all(abs(pboost["calculated_output_V"][k]-v) < 2e-5 for k,v in (("min",vout_min),("nominal",vout_nom),("max",vout_max))), pboost["calculated_output_V"])
    gb_margin = vout_min - (power["rgb_driver"]["worst_green_blue_vf_V"] + power["rgb_driver"]["sink_series_ohm"]["green"]*conservative/1000 + power["rgb_driver"]["driver_sink_headroom_max_V"] + power["rgb_driver"]["driver_switch_headroom_max_V"])
    check("rgb_green_blue_headroom", gb_margin > .1 and abs(power["rgb_driver"]["green_blue_path_margin_at_min_calculated_rail_V"]-gb_margin) < 2e-5, round(gb_margin,5))
    vbus_min = power["usb"]["vbus_stress_min_at_receptacle_V"]
    efficiency = pboost["efficiency_budget_assumption"]
    line_current = conservative * power["rgb_driver"]["max_active_sink_channels_per_scan_line"]
    boost_out_A = (line_current + power["rgb_driver"]["driver_overhead_engineering_allocation_mA"]) / 1000
    logic_A = power["logic_budget"]["engineering_allocation_mA"] / 1000
    total_A = .30
    for _ in range(20):
        vin = vbus_min - total_A * power["input_current_limit"]["r_on_mohm_design"] / 1000
        boost_in_A = vout_max * boost_out_A / (vin * efficiency)
        total_A = boost_in_A + logic_A
    duty = 1 - vin / vout_max
    ripple_A = vin * duty / (pboost["inductor_design_calculation_uH"] * 1e-6 * 1e6)
    peak_A = boost_in_A + ripple_A/2
    worst = power["worst_case_input_budget"]
    check("power_budget_math", abs(worst["total_vbus_mA"]-total_A*1000) < .02 and abs(worst["sys5_after_switch_V"]-vin) < 2e-5 and abs(worst["boost_input_mA"]-boost_in_A*1000) < .02, {"total_vbus_mA":round(total_A*1000,3),"sys5_V":round(vin,5)})
    check("boost_inductor_margin", peak_A < pboost["inductor_datasheet_isat_A"] and abs(pboost["calculated_peak_inductor_current_A"]-peak_A) < .001, {"calculated_peak_A":round(peak_A,4),"isat_A":pboost["inductor_datasheet_isat_A"]})
    check("power_limit", n["power"]["switch"] == "TPS2553DBVR-1" and n["power"]["rilim_ohm"] == 66500 and limit["max"] < 500 and power["worst_case_input_budget"]["total_vbus_mA"] < limit["min"] and status["release_state"] == "NOT_READY", {"limit":limit,"budget_mA":power["worst_case_input_budget"]["total_vbus_mA"]})

    source_ids = {s["id"] for s in sources["sources"]}
    check("bom_sources", all(i["source"] in source_ids for i in bom["items"]), f"{len(bom['items'])} BOM lines have registered sources")
    check("firmware_binding", fw["matrix"]["rows"] == matrix["row_pins"] and fw["matrix"]["cols"] == matrix["col_pins"] and
          fw["rgb"]["led_count"] == 107 and fw["usb"]["vid"] is None and fw["usb"]["pid"] is None,
          "firmware pins/counts match; VID/PID intentionally unassigned")
    qmk = load(HERE / "firmware/qmk/info.json")
    config = (HERE / "firmware/qmk/config.h").read_text()
    check("qmk_scaffold", qmk["processor"] == "RP2040" and qmk["matrix_pins"] == {"rows":matrix["row_pins"],"cols":matrix["col_pins"]} and
          len(qmk["layouts"]["LAYOUT"]["layout"]) == 58 and "#define RGB_MATRIX_LED_COUNT 107" in config and
          "#define IS31FL3741_SDB_PIN GP28" in config, "QMK scaffold mirrors 58-key pin/RGB contract")
    svg = (HERE / "logical-schematic.svg").read_text()
    check("derived_schematic", "NOT ERC / NOT PCB" in svg and "58-key matrix 6×10" in svg and "107 × Everlight" in svg,
          "derived SVG is explicitly non-ERC and shows matrix/RGB architecture")
    check("release_blockers", status["states"]["erc"].startswith("BLOCKED") and status["states"]["drc"].startswith("BLOCKED") and
          status["states"]["manufacture"] == "BLOCKED" and power["usb"]["pre_enumeration_status"] == "BENCH_REQUIRED",
          "ERC/DRC/bench/manufacture remain blocked")
    return {"schema_version":1,"design_id":"CK-001-E01","status":"PASS_LOGICAL_HOST_VERIFICATION","checks":checks,
            "limits":["Not ERC/DRC, routed PCB, USB-IF certification, firmware target build or physical bench evidence."]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--report", type=Path); args = ap.parse_args()
    result = validate()
    raw = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.report:
        path = args.report.resolve(); need(path.is_relative_to(HERE), "report must stay in electrical namespace")
        with path.open("x", encoding="utf-8") as handle: handle.write(raw)
    print(json.dumps({"status":result["status"],"checks":len(result["checks"]),"report":str(args.report) if args.report else None}))


if __name__ == "__main__": main()
