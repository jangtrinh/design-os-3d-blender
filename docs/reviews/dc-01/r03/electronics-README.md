# Desktop companion electronics candidate

The build contains a functional custom carrier design for a purchased Seeed XIAO ESP32-S3 compute board, an Adafruit 5206 face display, a BQ24074 charger module, a protected single-cell battery and a 5 V buck-boost regulator. The carrier has actual nets, pads, tracks and plated-through vias. The compute silicon and the purchased modules are distinct from the custom carrier.

**Fabrication and battery operation remain BLOCKED.** The digital checks establish the recorded circuit connectivity and geometric constraints. They do not establish a qualified battery charging window, operating undervoltage cutoff, component temperatures, or a tested physical assembly.

## Files to open

| File | Purpose |
|---|---|
| `cad/desktop-companion.kicad_pro` | Editable KiCad project with local symbol and footprint libraries. |
| `cad/desktop-companion.kicad_sch` | Functional carrier schematic with component values and named connections. |
| `cad/desktop-companion.kicad_pcb` | Two-layer 54 × 46 × 1.6 mm carrier with four 2.5 mm mounting holes. |
| `cad/desktop-companion.net` | XML netlist for cross-format inspection. |
| `checks.json` | Hash-bound checks on actual saved CAD, plus injected-fault results. |
| `geometry-interface.json`, `control-interface.json` | Component/control envelopes and mechanical world datums; placement revision E05. |
| `pcb-geometry.json` | Actual carrier pad, trace, via and component geometry for native Blender construction. |
| `carrier-pin-map.csv` | Carrier pin numbers, electrical nets and PCB/world coordinates. |
| `system-wiring.json`, `system-wiring.csv` | Thirty-three wire connections: 26 base and seven optional audio wires, with sourced terminal names and proposed cable lengths. |
| `carrier-bom.csv`, `system-bom.csv` | Custom-carrier parts and purchased system modules. |
| `power-budget.json` | Calculated load, charging and heat allowances, with zero physical measurements. |
| `bench-validation.md` | Concrete release prerequisites and required measurements. |
| `sources.md`, `references/receipt.json` | Primary references, conflicting dimensions and downloaded-source hashes. |
| `native-a04/`, `native-checks-latest.json` | Native KiCad10.0.6 ERC and DRC reports: zero violations, zero unconnected items and zero schematic-parity issues. |
| `previews/` | Native schematic and both copper-layer SVGs, with inspected PNG derivatives. |
| `fabrication-candidate/`, `native-export-receipt.json` | Actual native Gerber X2 and separate plated/nonplated drill files, explicitly unreleased for fabrication. |
| `power-switch-geometry.json` | Fourteen actual supplier-DXF hole positions with independently sourced pin identities and world coordinates. |
| `delivery-audit.json`, `delivery-manifest.json` | Final status, native-to-Blender copper identity checks and file hashes, excluding local tool caches. |

## Circuit and power path

The charger is a purchased Adafruit 4755 board using TI BQ24074. Its USB-C socket accepts the proposed dedicated 5 V supply. Its battery connector connects only to the protected pack. Its OUT power-path terminal feeds carrier J1, F1, the Pololu2810 LV service master switch at J4, and the Pololu S7V8F5 buck-boost regulator through J5. The switch's VIN and VOUT connect to J4; its required ground return uses J3 pin2 while the optional amplifier is unpopulated. The regulator returns 5 V to the carrier. A series SS14 diode feeds the XIAO 5 V input; XIAO's 3.3 V output powers the face display and signal pull-ups. Charging can remain active while the service switch is off. The switch is accessed after upper-body removal; it is neither a battery UVLO nor a safety isolator.

XIAO battery pads have no carrier pads or connections. Remove the compute board from its removable sockets before connecting its USB programming cable. The series diode does not authorize simultaneous USB and installed-system operation. The display's `3Vo` output is not connected to XIAO's `3V3` output. Tie the unused display `SD_CS` pin locally to display `3Vo`; display MISO is unused.

The charger board must be configured before use: open its factory `1A` ISET jumper, leave its other ISET-selection jumpers open, connect carrier R4 through J7 to charger JP3 pin 8, and verify the resistance to ground. The selected 3.57 kΩ ±1% resistor gives approximately 249 mA nominal charge current; the source constant and resistor corners give approximately 221–276 mA. Configure EN1 high and EN2 low for the proposed 500 mA input limit. Open the factory THERM bypass and connect a Semitec 103AT-2 through J7/J8 to the pack. Manufacturer-source mapping identifies JP3 pin 9 as THERM and pin 10 as GND.

Connecting that thermistor does not yet qualify the selected pack's 0–45 °C charge window. The thermistor/charger threshold tolerances, attachment lag, fault response and upper cutoff need a released hardware solution and measured verification. The current candidate also lacks a qualified 3.0 V operating shutdown and restart strategy. The pack protection circuit is not a substitute for either requirement.

## Display, button and optional audio

The carrier maps SPI clock to GPIO7, MOSI to GPIO9, display CS to GPIO1, DC to GPIO2, reset to GPIO4 and backlight control to GPIO5. GPIO6 reads the momentary button with an external 10 kΩ pull-up and 100 nF filter. GPIO3, a strapping pin, is left unconnected. GPIO43, GPIO44 and GPIO8 are reserved for optional I2S bit clock, word clock and audio data respectively.

The selected Omron B3F-1002-G has gold contacts rated down to100µA, covering the0.33mA nominal pull-up current. Its6×6mm case and4.3mm overall height share the standard B3F envelope; force is1.76±0.49N and operating pretravel spans0.15–0.45mm. A nominal0.25mm free gap plus0.25mm switch travel does not guarantee worst-case actuation. The retainer/TPU mechanism requires a tolerance-aware adjustable or compliant stop and a physical test. Manufacturer maximum safe overtravel is not provided.

The Adafruit 3006 MAX98357A amplifier and speaker are unpopulated in the base assembly. A speaker part, acoustic opening, power limit and collision-free optional placement have not been qualified. Both bridge-tied speaker outputs must remain isolated from ground. The amplifier's power budget is an optional scenario, not installed hardware acceptance.

## Mechanical interfaces

Use `geometry-interface.json` for the current placement proposal and `pcb-geometry.json` for the actual carrier layout. The carrier transform is world X = PCB X − 27, world Z = 86 − PCB Y, with the component side facing positive Y and the PCB top at Y = 8.8 mm. The geometry export distinguishes body dimensions from assembly allowances.

The selected battery uses the larger linked drawing dimension, 35 ±0.3 mm wide, despite the product text stating 34 mm. The proposed battery body is at Z = 11.5–16.8 mm and its reservation at Z = 10.5–18.5 mm. The charger PCB is at Z = 26.5–28.1 mm. Their 8 mm reservation gap is a packaging choice, not measured thermal isolation. The pack must not be compressed or punctured by mounts, wires or fasteners.

The charger USB-C shell-front XY datum is extracted from manufacturer Eagle footprint geometry: world X = −6.35 mm and world Y = 27.066 mm at the revised charger center Y = 7 mm. Its mating-plane height and the real cable shell insertion envelope remain unmeasured. Preserve the provisional service aperture's adjustment access. The antenna reservation retains its full 25 × 10 × 12 mm dimensions at world (0, 0, 83); this is not a sourced antenna body dimension or an RF-qualified clearance.

The display manufacturer's actual Eagle board supersedes its rounded product dimensions and generic mounting rectangle. The board is 45.72 × 36.83 mm in landscape orientation. Its hole centers relative to the visor are X = −18.415 and +20.32 mm, Z = ±15.875 mm. The source SHA and exact transform are recorded in the interface, rather than stretching tolerances around the older mount pattern.

The regulator's confirmed candidate center is(−15,0,60) with its full14×10×19mm reservation. Its removable support plate and0.6mm insulating pad are intended contacts, separately identified from collision obstacles. The internal service power switch center is(15,22,52), components toward−Y, with an18×7×18mm reservation. Its PCB front isY22.25mm; the rear insulating adhesive pad and integrated support plate are intended contacts requiring physical qualification. Supplier drawings establish its PCB, projection and14 pad locations; slider stroke and physical service access remain unmeasured.

## Verification scope

`check_electronics.py` reconstructs connections from saved schematic pin positions, wires and labels, then compares them with saved PCB pad nets and the XML netlist. It also verifies XIAO hole coordinates against the downloaded official S3 footprint. `check_copper.py` reconstructs actual pad/trace/via copper and checks same-net connectivity, foreign-net gaps of at least 0.254 mm, and edge/hole gaps of at least 0.5 mm. These are custom checks, separate from native KiCad ERC and DRC.

The five injected faults remove ISET copper, reverse diode nets, short the display supply to ground, restore an excessive ISET current, and change a schematic label. All five were detected. The checked carrier contains351 tracks,13 vias,63 electrical pads and19 functional nets plus an isolated strapping-pin NC identity. The custom geometric screen finds a0.285mm minimum foreign-copper gap. Native KiCad10.0.6 attemptA04 independently reports zero ERC violations, zero DRC violations, zero unconnected items and zero schematic-parity issues. The native reports and exported files bind to the final source hashes. Native drill export contains41 plated1.0mm holes,13 plated0.3mm vias and four nonplated2.5mm mounting holes.

Native KiCad was initially absent from the inspected application and command paths. The completed route uses the official KiCad10.0.6 macOS image, byte/hash verified, mounted read-only inside `.tools`, with a successful application code-signature check. Its native CLI ran the electrical checks and exports. `local-tool-receipt.json` records the exact binary and image hash. Project-local parsing tools remain under `.venv`; no system application installation occurred. Historical native attempts retain the real serialization/metadata issues that were corrected before A04.

## Reproduce the candidate

From the repository root on the verified host:

```sh
python3 -m venv builds/desktop-companion/electronics/.venv
builds/desktop-companion/electronics/.venv/bin/python -m pip install -r builds/desktop-companion/electronics/requirements.txt
builds/desktop-companion/electronics/.venv/bin/python builds/desktop-companion/electronics/build_cad.py
builds/desktop-companion/electronics/.venv/bin/python builds/desktop-companion/electronics/package_cad.py
builds/desktop-companion/electronics/.venv/bin/python builds/desktop-companion/electronics/check_electronics.py
python3 builds/desktop-companion/electronics/wiring.py
python3 builds/desktop-companion/electronics/power_budget.py
python3 builds/desktop-companion/electronics/native_checks.py
python3 builds/desktop-companion/electronics/native_export.py
builds/desktop-companion/electronics/.venv/bin/python builds/desktop-companion/electronics/finalize_delivery.py
```

Source changes require new generated CAD, geometry exports and bound checks. Changes only to world placement still require renewed mechanical integration evidence. `.tools` and `.venv` are local tooling caches and are excluded from the deliverable.
