#!/usr/bin/env python3
"""Generate CK-001 E02 electrical authority artifacts from the frozen B layout."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parents[1]


def write_new(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError(path)
    text = value if isinstance(value, str) else json.dumps(value, indent=2, allow_nan=False) + "\n"
    path.write_text(text, encoding="utf-8")


def keys_from_layout(layout):
    x0, y0 = layout["main_origin_mm"]
    keys = []
    for row, labels in enumerate(layout["main_rows"]):
        for col, label in enumerate(labels):
            keys.append((label, [x0 + col * layout["pitch_x_mm"], y0 - row * layout["pitch_y_mm"]]))
    for item in layout["bottom_row"]:
        keys.append((item["label"], [x0 + item["column"] * layout["pitch_x_mm"], y0 - 3 * layout["pitch_y_mm"]]))
    macro = layout["rear_macros"]
    for i in range(macro["count"]):
        keys.append(("dot", [macro["origin_mm"][0] + i * macro["pitch_mm"], macro["origin_mm"][1]]))
    for xy in layout["left_macros_mm"]:
        keys.append(("dot", xy))
    return keys


def bom():
    def part(refs, qty, mpn, maker, role, source, status="DESIGN_SELECTED"):
        return {"refs": refs, "qty": qty, "mpn": mpn, "manufacturer": maker, "role": role,
                "source": source, "status": status}
    return {"schema_version": 1, "design_id": "CK-001-E02", "currency": None,
            "procurement_status": "NOT_ORDERED", "items": [
        part("U1", 1, "RP2040", "Raspberry Pi", "USB MCU, matrix/encoder/I2C control", "raspberry-pi-rp2040-hardware-design-r2"),
        part("U2", 1, "W25Q128JVSIQ", "Winbond", "128-Mbit QSPI flash", "raspberry-pi-rp2040-hardware-design-r2"),
        part("U3", 1, "TLV75533PDBVR", "Texas Instruments", "SYS_5V to 3.3 V ceramic-stable LDO", "ti-tlv755p"),
        part("U4", 1, "TPS2553DBVR-1", "Texas Instruments", "latch-off input current limiter", "ti-tps2553-1"),
        part("U5", 1, "IS31FL3741A-QFLS4-TR", "Lumissil", "39x9 RGB matrix driver", "lumissil-is31fl3741a-rev-d"),
        part("U6", 1, "USBLC6-2SC6", "STMicroelectronics", "USB2 D+/D-/VBUS ESD", "st-usblc6-2sc6"),
        part("U7", 1, "TPS61023DRLR", "Texas Instruments", "SYS_5V to RGB_5V1 synchronous boost", "ti-tps61023"),
        part("L1", 1, "XEL4030-102MEC", "Coilcraft", "1 uH RGB boost inductor", "coilcraft-xel4030-102"),
        part("J1", 1, "USB4105-GF-A-120", "GCT", "USB 2.0 Type-C receptacle", "gct-usb4105", "FOOTPRINT_ECAD_PENDING"),
        part("Y1", 1, "ABM8-272-T3", "Abracon", "12 MHz RP2040 crystal", "raspberry-pi-rp2040-hardware-design-r2"),
        part("SW00-SW57", 58, "KS-33H10B050NN-Y24", "Gateron", "key switches", "gateron-ks33-red-v2", "FOOTPRINT_ORIENTATION_PENDING"),
        part("D00-D57", 58, "BAS316,115", "Nexperia", "per-key matrix diodes", "nexperia-bas316"),
        part("ENC1-ENC5", 5, "PEC11R-1215F-N0024", "Bourns", "24-detent/24-PPR quadrature encoders, no switch", "bourns-pec11r-rev-11-23", "FOOTPRINT_ECAD_PENDING"),
        part("LED000-LED106", 107, "19-237A/BHR6GHC-A01/2T", "Everlight", "common-anode RGB LEDs; pin 3 common anode, pins 1/2/4 red/green/blue cathodes", "everlight-19-237a-a01"),
        part("RCC1,RCC2", 2, "5.1k 1%", "GENERIC", "USB-C Rd", "microchip-usbc-device-guidance"),
        part("RUSB1,RUSB2", 2, "27R 1%", "GENERIC", "USB D+/D- source termination", "raspberry-pi-rp2040-hardware-design-r2"),
        part("RILIM", 1, "66.5k 1%", "GENERIC", "TPS2553-1 400 mA nominal current-limit setting", "ti-tps2553-1-design"),
        part("RFAULT", 1, "10k 1%", "GENERIC", "FAULT pull-up to 3V3", "ti-tps2553-1"),
        part("RI2C1,RI2C2", 2, "4.7k 1%", "GENERIC", "I2C pull-ups to 3V3", "lumissil-is31fl3741a-rev-d"),
        part("RSDB", 1, "100k 1%", "GENERIC", "RGB SDB default-off pull-down", "lumissil-is31fl3741a-rev-d"),
        part("RISET", 1, "120k 1%", "GENERIC", "RGB hardware peak-current limit", "lumissil-is31fl3741a-rev-d"),
        part("RBOOST_TOP", 1, "750k 1%", "GENERIC", "TPS61023 feedback top resistor", "ti-tps61023"),
        part("RBOOST_BOTTOM", 1, "100k 1%", "GENERIC", "TPS61023 feedback bottom resistor", "ti-tps61023"),
        part("RLED_R01-RLED_R13", 13, "51R 1%", "GENERIC", "red CS-line series resistors", "lumissil-is31fl3741a-rev-d"),
        part("RLED_GB01-RLED_GB26", 26, "20R 1%", "GENERIC", "green/blue CS-line series resistors", "lumissil-is31fl3741a-rev-d"),
        part("RENC_PU01-RENC_PU10", 10, "10k 1%", "GENERIC", "encoder A/B pull-ups to 3V3", "bourns-pec11r-rev-11-23"),
        part("RENC_SER01-RENC_SER10", 10, "10k 1%", "GENERIC", "encoder A/B series filters", "bourns-pec11r-rev-11-23"),
        part("CENC01-CENC10", 10, "10nF X7R", "GENERIC", "encoder A/B filter capacitors", "bourns-pec11r-rev-11-23"),
        part("CX1,CX2", 2, "15pF C0G", "GENERIC", "crystal load capacitors", "raspberry-pi-rp2040-hardware-design-r2"),
        part("RX1", 1, "1k 1%", "GENERIC", "crystal damping resistor", "raspberry-pi-rp2040-hardware-design-r2"),
        part("RBOOT", 1, "1k 1%", "GENERIC", "BOOTSEL/QSPI_SS protection resistor", "raspberry-pi-rp2040-hardware-design-r2"),
        part("C3V3_IN,C3V3_OUT", 2, "4.7uF X5R/X7R 10V", "GENERIC", "TLV75533P input/output capacitors; >=1uF effective required", "ti-tlv755p"),
        part("CBOOST_IN", 1, "10uF X5R/X7R 10V", "GENERIC", "TPS61023 input capacitor", "ti-tps61023"),
        part("CBOOST_OUT1,CBOOST_OUT2", 2, "22uF X5R/X7R 10V", "GENERIC", "TPS61023 output capacitors; verify >=10uF combined effective at bias", "ti-tps61023", "DIELECTRIC_DERATING_ECAD_PENDING"),
        part("CVREG_IN,CVREG_OUT", 2, "1uF X5R", "GENERIC", "RP2040 internal regulator capacitors", "raspberry-pi-rp2040-hardware-design-r2"),
        part("CU1_01-CU1_08", 8, "100nF X7R", "GENERIC", "RP2040 supply decoupling allocation", "raspberry-pi-rp2040-hardware-design-r2", "PLACEMENT_ECAD_PENDING"),
        part("CU2", 1, "100nF X7R", "GENERIC", "QSPI flash decoupling", "raspberry-pi-rp2040-hardware-design-r2"),
        part("CU5_1-CU5_3", 3, "1uF X5R", "GENERIC", "IS31FL3741A AVCC/PVCC local bulk", "lumissil-is31fl3741a-rev-d"),
        part("CU5_4-CU5_6", 3, "100nF X7R", "GENERIC", "IS31FL3741A AVCC/PVCC decoupling", "lumissil-is31fl3741a-rev-d")
    ]}


def main():
    layout = json.loads((BUILD / "layout.json").read_text())
    source_keys = keys_from_layout(layout)
    assert len(source_keys) == 58
    rows = [f"GP{i}" for i in range(6)]
    cols = [f"GP{i}" for i in range(6, 16)]
    keys = []
    for i, (label, xy) in enumerate(source_keys):
        keys.append({"id": f"RK_KEY_{i:02d}", "label": label, "xy_mm": [round(v, 4) for v in xy],
                     "matrix": [i // 10, i % 10], "switch": f"SW{i:02d}", "diode": f"D{i:02d}",
                     "topology": "COL -> switch -> diode anode; diode cathode -> ROW"})
    encoder_pins = [(16,17),(20,21),(22,23),(24,25),(26,27)]
    encoders = [{"id": f"ENC{i+1}", "mpn": "PEC11R-1215F-N0024", "a_pin": f"GP{a}", "b_pin": f"GP{b}",
                 "common": "GND", "filter": {"pullup_ohm": 10000, "pullup_rail": "3V3", "series_ohm": 10000,
                 "cap_to_ground_nF": 10}, "detents": 24, "ppr": 24, "push_switch": False}
                for i, (a,b) in enumerate(encoder_pins)]
    leds = []
    for i in range(107):
        slot, sw = i % 13, i // 13 + 1
        leds.append({"id": f"LED{i:03d}", "source": "key" if i < 58 else "perimeter",
                     "source_index": i if i < 58 else i - 58, "sw": sw,
                     "cs": {"r": slot * 3 + 1, "g": slot * 3 + 2, "b": slot * 3 + 3}})
    netlist = {
        "schema_version": 1, "design_id": "CK-001-E02", "authority": "DESIGN_AUTHORITY_LOGICAL_NOT_ECAD",
        "matrix": {"rows": 6, "cols": 10, "row_pins": rows, "col_pins": cols, "diode_direction": "COL2ROW",
                   "diode_cathode": "ROW", "keys": keys, "unused_cells": [[5,8],[5,9]]},
        "encoders": encoders,
        "usb": {"connector": "USB4105-GF-A-120", "device_mode_only": True,
                "cc1": {"rd_ohm": 5100, "tolerance_percent": 1, "to": "GND"},
                "cc2": {"rd_ohm": 5100, "tolerance_percent": 1, "to": "GND"},
                "sbu1": "NC", "sbu2": "NC", "esd": "USBLC6-2SC6",
                "data_plus": {"connector_pins": ["A6","B6"], "esd_channel": 1, "series_ohm": 27, "mcu_pin": "USB_DP"},
                "data_minus": {"connector_pins": ["A7","B7"], "esd_channel": 2, "series_ohm": 27, "mcu_pin": "USB_DM"},
                "shield": {"net": "USB_SHIELD", "pcb_emc_connection": "ECAD_BENCH_PENDING"}},
        "i2c": {"bus": "I2C1", "sda": "GP18", "scl": "GP19", "pullup_rail": "3V3", "pullup_ohm": 4700,
                "frequency_hz": 400000, "devices": [{"ref": "U5", "address_7bit": "0x30", "addr_pin": "GND"}]},
        "rgb": {"driver": "IS31FL3741A-QFLS4-TR", "supply": "RGB_5V1", "sdb_pin": "GP28", "sdb_pulldown_ohm": 100000,
                "riset_ohm": 120000, "led_mpn": "19-237A/BHR6GHC-A01/2T",
                "led_topology": "SWx source -> common anode pin 3; cathodes red/green/blue pins 1/2/4 -> CS sinks",
                "led_pins": {"common_anode": 3, "cathodes": {"red": 1, "green": 2, "blue": 4}},
                "led_count": 107, "mapping": leds},
        "power": {"input": "VBUS_RAW", "switch": "TPS2553DBVR-1", "output": "SYS_5V", "rilim_ohm": 66500,
                  "fault_pin": "GP29", "fault_pullup": "3V3", "regulator": "TLV75533PDBVR", "logic_rail": "3V3",
                  "rgb_boost": {"device":"TPS61023DRLR","input":"SYS_5V","output":"RGB_5V1","enable":"SYS_5V",
                                "fb_top_ohm":750000,"fb_bottom_ohm":100000,"inductor":"XEL4030-102MEC",
                                "input_cap_uF":10,"output_caps_uF":[22,22]},
                  "rp2040_core_rail": "1V1", "direct_power_shorts_allowed": []},
        "controller": {"mcu": "RP2040", "flash": "W25Q128JVSIQ", "crystal_hz": 12000000,
                       "qspi": "dedicated RP2040 pins", "swd": "dedicated RP2040 pins"}
    }
    firmware = {"schema_version": 1, "design_id": "CK-001-E02", "mcu": "RP2040", "qmk_board": "GENERIC_RP_RP2040",
                "bootloader": "rp2040", "flash_boot_stage": "RP2040_FLASH_GENERIC_03H",
                "matrix": {"rows": rows, "cols": cols, "diode_direction": "COL2ROW", "keys": [{"id": k["id"], "matrix": k["matrix"]} for k in keys]},
                "encoders": [{"id": e["id"], "a_pin": e["a_pin"], "b_pin": e["b_pin"], "gray_edges_per_detent": 4} for e in encoders],
                "i2c": {"driver": "I2CD1", "sda": "GP18", "scl": "GP19", "frequency_hz": 400000},
                "rgb": {"driver": "is31fl3741", "address": "0x30", "sdb_pin": "GP28", "pwm_hz": 29000,
                        "global_current_default": 128, "software_max_brightness": 128, "led_count": 107,
                        "led_mpn": "19-237A/BHR6GHC-A01/2T",
                        "led_polarity": "common_anode"},
                "power_fault_pin": "GP29", "usb": {"max_power_descriptor_mA": 500, "wait_for_enumeration": True,
                "vid": None, "pid": None, "release_blocker": "Reserve/assign a product USB VID/PID before product firmware release."},
                "default_encoder_actions": {"ENC1": ["KC_VOLD","KC_VOLU"], "ENC2": ["KC_PGDN","KC_PGUP"],
                "ENC3": ["RGB_SAD","RGB_SAI"], "ENC4": ["RGB_HUD","RGB_HUI"], "ENC5": ["RGB_VAD","RGB_VAI"]}}
    pin_map = []
    for i, pin in enumerate(rows):
        pin_map.append({"pin":pin,"owner":f"MATRIX_ROW_{i}","runtime_mode":"scan output-low or inactive high-impedance",
                        "boot_requirement":"do not actively drive before matrix initialization"})
    for i, pin in enumerate(cols):
        pin_map.append({"pin":pin,"owner":f"MATRIX_COL_{i}","runtime_mode":"digital input with pull-up",
                        "boot_requirement":"input/high-impedance acceptable"})
    for e in encoders:
        for side, label in (("a_pin", "A"), ("b_pin", "B")):
            pin_map.append({"pin":e[side],"owner":e["id"]+"."+label,"runtime_mode":"filtered digital input",
                            "boot_requirement":"input/high-impedance; external 10k pull-up to 3V3"})
    pin_map += [
        {"pin":"GP18","owner":"I2C1_SDA","runtime_mode":"I2C open-drain alternate function","boot_requirement":"external 4.7k pull-up to 3V3"},
        {"pin":"GP19","owner":"I2C1_SCL","runtime_mode":"I2C open-drain alternate function","boot_requirement":"external 4.7k pull-up to 3V3"},
        {"pin":"GP28","owner":"RGB_SDB","runtime_mode":"digital output; high enables IS31FL3741A","boot_requirement":"100k hardware pull-down keeps LEDs disabled until firmware explicitly drives high"},
        {"pin":"GP29","owner":"POWER_FAULT_N","runtime_mode":"digital input","boot_requirement":"external 10k pull-up to 3V3; TPS2553-1 open-drain fault source"},
    ]
    pin_map.sort(key=lambda row:int(row["pin"].removeprefix("GP")))
    write_new("bom.json", bom())
    write_new("logical-netlist.json", netlist)
    write_new("firmware-config.json", firmware)
    write_new("pin-map.json", {"schema_version":1,"design_id":"CK-001-E02","mcu":"RP2040","gpio_spares":0,"pins":pin_map,
                                "dedicated_non_gpio":{"usb":["USB_DP","USB_DM"],"debug":["SWDIO","SWCLK"],"flash":["QSPI_SS","QSPI_SCLK","QSPI_SD0","QSPI_SD1","QSPI_SD2","QSPI_SD3"]}})
    qmk_layout = [{"matrix": k["matrix"], "x": round((k["xy_mm"][0]+130)/18.8,3), "y": round((40-k["xy_mm"][1])/17,3)} for k in keys]
    write_new("firmware/qmk/info.json", {"keyboard_name":"CK-001 E02 development hardware contract", "manufacturer":"DESIGN:OS",
        "maintainer":"Jang", "processor":"RP2040", "bootloader":"rp2040", "diode_direction":"COL2ROW",
        "matrix_pins":{"rows":rows,"cols":cols}, "usb":{"max_power":500}, "layouts":{"LAYOUT":{"layout":qmk_layout}},
        "release_status":"USB VID/PID intentionally absent; full QMK build not performed on this host."})
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="820" viewBox="0 0 1400 820"><style>text{font:15px system-ui} .h{font:bold 22px system-ui}.b{fill:#f8f8f8;stroke:#222;stroke-width:2}.n{stroke:#222;stroke-width:2;fill:none}.s{font:12px system-ui;fill:#444}</style><text x="40" y="42" class="h">CK-001 E02 logical schematic — derived view, NOT ERC / NOT PCB</text><rect x="40" y="90" width="250" height="220" class="b"/><text x="60" y="120" class="h">USB-C + power</text><text x="60" y="150">J1 USB4105-GF-A-120</text><text x="60" y="175">CC1/CC2: 5.1k → GND</text><text x="60" y="200">U6 USBLC6-2SC6</text><text x="60" y="225">U4 TPS2553DBVR-1</text><text x="60" y="250">66.5k RILIM → SYS_5V</text><text x="60" y="275">U3 TLV75533PDBVR → 3V3</text><text x="60" y="300">U7 TPS61023DRLR → RGB_5V1</text><path d="M290 180H380" class="n"/><text x="300" y="170" class="s">D+/D- 27R</text><rect x="380" y="80" width="300" height="240" class="b"/><text x="400" y="115" class="h">U1 RP2040</text><text x="400" y="145">GP0..5 rows · GP6..15 cols</text><text x="400" y="170">GP16/17,20..27 encoder A/B</text><text x="400" y="195">GP18 SDA · GP19 SCL</text><text x="400" y="220">GP28 RGB SDB · GP29 FAULT</text><text x="400" y="245">U2 W25Q128JVSIQ QSPI</text><text x="400" y="270">Y1 ABM8-272-T3 12MHz</text><text x="400" y="295">30/30 GPIO explicitly owned</text><path d="M530 320V400" class="n"/><rect x="350" y="400" width="360" height="190" class="b"/><text x="370" y="435" class="h">58-key matrix 6×10</text><text x="370" y="470">58 × KS-33H10B050NN-Y24</text><text x="370" y="500">58 × BAS316,115</text><text x="370" y="530">COL → switch → diode A; diode K → ROW</text><text x="370" y="560">unused matrix cells: R5C8, R5C9</text><path d="M680 180H820" class="n"/><text x="700" y="170" class="s">I2C1, 3V3 pullups</text><rect x="820" y="80" width="390" height="250" class="b"/><text x="840" y="115" class="h">U5 IS31FL3741A</text><text x="840" y="145">RGB_5V1 · addr 0x30 · 29kHz</text><text x="840" y="175">RISET 120k 1% · GP28 SDB + 100k pulldown</text><text x="840" y="205">U7 boost: 750k/100k FB · L1 1uH</text><text x="840" y="235">107 × Everlight 19-237A A01 common-anode RGB</text><text x="840" y="265">SW → pin3 common anode; CS → R/G/B pins1/2/4</text><text x="840" y="295">321/351 matrix channels used</text><path d="M680 260H760V480H820" class="n"/><rect x="820" y="400" width="360" height="190" class="b"/><text x="840" y="435" class="h">5 × PEC11R encoders</text><text x="840" y="470">PEC11R-1215F-N0024</text><text x="840" y="500">A/B each: 10k pull-up 3V3</text><text x="840" y="530">+ 10k series + 10nF to GND</text><text x="840" y="560">C terminal → GND; no push switch</text><text x="40" y="760" class="s">Physical footprints, routed PCB, ERC, DRC, USB current measurements and bench qualification remain separate release gates.</text></svg>'''
    write_new("logical-schematic.svg", svg)


if __name__ == "__main__":
    main()
