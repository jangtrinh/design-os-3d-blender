# CK-001 E01 electrical design review

Date: 2026-09-17  
Scope: revision-B electrical architecture and executable logical/firmware evidence for the 58-key, five-encoder CK-001 prototype.

## Disposition

**Electrical design state: NOT_READY for manufacture.** The work below closes the previous "illustrative electronics only" gap to a concrete component/pin/net design with host-verifiable rules. It does not create an ERC-passed schematic, routed PCB, DRC result, Gerber set or electrically tested keyboard.

Authoritative status: `builds/reference-keyboard/manufacturing/electrical/status.json`.

Current verified host evidence:

- logical authority verifier: `PASS_LOGICAL_HOST_VERIFICATION`, 31 checks;
- negative controls: `PASS_NEGATIVE_CONTROLS`, five deliberately broken designs rejected;
- portable firmware core: `PASS_HOST_C_LOGIC` with `-Wall -Wextra -Werror`;
- ARM compile: `PASS_ARMV6M_CORE_OBJECT`, actual Cortex-M0+ ELF relocatable object, not linked firmware;
- KiCad ERC/PCB/DRC/Gerber: blocked because KiCad is not installed on this host;
- QMK target build: blocked because QMK and the ARM GCC/QMK dependency stack are not installed;
- physical current, USB, thermal, switch/encoder/LED operation: blocked pending a prototype and bench measurements.

Freeze note: the electrical core/power artifacts are frozen at this handoff. The
subsequent C-series keycap/skirt correction is mechanical geometry work and does not
change the E01 GPIO, matrix, encoder, USB, power or firmware contract. Three modeled
`RK_STATUS_*` LEDs remain visual meshes only; E01 does not wire or populate them and
all 30 RP2040 GPIOs already have explicit owners.

## Revision binding

E01 is pinned to the current B inputs by SHA-256 in `authority.json`:

- `layout.json`: `e5fdef446f3c5eef4b5e4f2e9467c585290421cebdc0e663e0a349d12a9ad6d6`;
- `interfaces.json`: `7509c9941b05ef3d9eaa4f48b4b893639bcfb9163beb34a0b1e3e1dbd548aa24`;
- B03 mesh inventory: `2d949bab09c5f1d4acaec14b247d2c883fe7bc74e6c17c4fb906c55c0701a0fa`.

The inventory contract contains 58 keys, five encoder bodies, 58 key RGB emitters and 49 perimeter RGB emitters. E01 therefore owns 107 logical RGB positions. The three modeled `RK_STATUS_*` meshes remain illustrative and are intentionally **not electrically populated or wired in E01**.

## Controller and GPIO ownership

Controller: RP2040 QFN-56 + W25Q128JVSIQ QSPI flash + ABM8-272-T3 12 MHz crystal. USB uses the RP2040 dedicated USB D+/D- pins and does not consume GPIO.

| Function | RP2040 ownership |
|---|---|
| Matrix rows R0..R5 | GP0..GP5 |
| Matrix columns C0..C9 | GP6..GP15 |
| Encoder 1 A/B | GP16 / GP17 |
| I2C1 SDA / SCL | GP18 / GP19 |
| Encoder 2 A/B | GP20 / GP21 |
| Encoder 3 A/B | GP22 / GP23 |
| Encoder 4 A/B | GP24 / GP25 |
| Encoder 5 A/B | GP26 / GP27 |
| RGB driver SDB | GP28 |
| TPS2553-1 FAULT | GP29 |

All 30 general-purpose GPIOs are owned exactly once. There are no spare GPIOs in E01. Adding discrete status LEDs, encoder push buttons or another peripheral therefore requires a later architecture revision or an I/O-expansion decision.

`pin-map.json` makes the direction/boot contract machine-readable: rows are scan outputs that may only drive low while active, columns and encoders are inputs, GP18/19 are open-drain I2C alternate functions, GP28 is RGB enable with a hardware default-low state, and GP29 is the externally pulled-up power-fault input.

## Key matrix

`logical-netlist.json` defines a 6×10 matrix with 58 populated cells. `RK_KEY_00..RK_KEY_57` map deterministically to `[index // 10, index % 10]`; R5C8 and R5C9 are the only empty cells.

Each key selects:

- one Gateron `KS-33H10B050NN-Y24` logical switch;
- one Nexperia `BAS316,115` SOD323 diode;
- `COL2ROW` topology: column → switch → diode anode; diode cathode/mark → row.

The Gateron manufacturer drawing is the source for the chosen switch family. **Its board-hole orientation is not yet released as an ECAD footprint.** The current Blender switch-pin proxies are illustrative and are not PCB-land authority.

## Encoders

All five controls select Bourns `PEC11R-1215F-N0024`: terminal configuration 1, 24 detents, 15 mm flatted shaft, no push switch, 24 PPR.

Each A/B input uses the manufacturer-suggested network adapted to 3.3 V RP2040 logic:

- 10 kΩ pull-up to 3V3;
- 10 kΩ series resistor;
- 10 nF to ground/common;
- encoder common terminal to ground.

The portable C core implements a four-edge quadrature Gray decoder. Host tests cover clockwise, counter-clockwise, bounce reversal, invalid two-bit transitions and key-matrix bounds. The exact PEC11R PCB terminal land pattern still requires ECAD instantiation and physical verification.

## USB-C and protection

Selected interface:

- GCT `USB4105-GF-A-120`, 16-contact USB 2.0 Type-C receptacle;
- CC1 and CC2 each have an independent 5.1 kΩ 1% Rd to ground;
- SBU1/SBU2 are not connected;
- ST `USBLC6-2SC6` protects D+/D- and VBUS;
- RP2040 D+/D- each use 27 Ω source termination;
- PCB routing target remains 90 Ω differential per the RP2040 hardware guide.

USB shield/chassis EMC treatment is explicitly `ECAD_BENCH_PENDING`. No USB-IF compliance or certification is claimed. VID/PID is intentionally unassigned in the firmware contract and is a release blocker.

## Power architecture

The initial NCP1117 proposal was rejected during review: worst-case dropout and capacitor ESR constraints were a poor fit for a USB-powered product. E01 now uses:

1. `VBUS_RAW` → TI `TPS2553DBVR-1` latch-off power switch/current limiter → `SYS_5V`.
2. `SYS_5V` → TI `TLV75533PDBVR` → `3V3` for RP2040/flash/logic.
3. `SYS_5V` → TI `TPS61023DRLR` synchronous boost → `RGB_5V1` for the LED driver.
4. The boost remains enabled whenever `SYS_5V` is present; IS31FL3741A SDB has a 100 kΩ hardware pull-down and GP28 enables lighting later. This avoids leaving the RGB driver VCC off while its I2C lines are pulled to 3.3 V.

### Input current limit

`TPS2553DBVR-1` uses 66.5 kΩ 1% RILIM. TI's table gives 351.2 / 396.7 / 448.7 mA minimum/nominal/maximum current-limit values. GP29 reads the open-drain active-low FAULT signal through a 10 kΩ 3V3 pull-up.

### 3.3 V rail

`TLV75533PDBVR` is rated for 1.45–5.5 V input and has 238 mV maximum dropout at 500 mA for the 3.3 V version. It is stable with a 1 µF ceramic output capacitor. E01 specifies 4.7 µF X5R/X7R on input and output; physical capacitor part numbers/derating are an ECAD procurement item.

### RGB boost rail

`TPS61023DRLR` uses:

- Rtop = 750 kΩ 1%, Rbottom = 100 kΩ 1%;
- datasheet PWM VREF = 580 / 595 / 610 mV min/typ/max;
- calculated rail including resistor tolerance: **4.84386 / 5.05750 / 5.27743 V** min/nom/max;
- Coilcraft `XEL4030-102MEC`, 1.0 µH ±20%, 9 A saturation;
- 10 µF X5R/X7R input capacitor;
- 2×22 µF X5R/X7R output capacitors, with combined effective capacitance required to remain ≥10 µF at operating bias.

The driver absolute operating target stays below its 5.5 V rated supply limit. A design calculation using 0.7 µH for extra inductance-tolerance margin produces ~0.780 A peak inductor current, far below the selected 9 A saturation rating. This does not replace switch-node layout, ripple or thermal measurement.

## RGB driver and current budget

Selected driver: Lumissil `IS31FL3741A-QFLS4-TR`, 39×9 matrix, 351 channels / up to 117 RGB packages. E01 uses 107 packages = 321 unique channel pairs in `logical-netlist.json`.

The frozen BOM currently names Everlight `19-237B/R6GHBHC-C01/2T`. Its manufacturer
datasheet shows pin 4 as the shared negative node, i.e. a common-cathode RGB package.
That selection is **not electrically released** with the present IS31FL3741A matrix
topology: Lumissil describes the device as `39 Current Sink × 9 SW`, and its
IS31FL3741A evaluation-board BOM uses Everlight `19-237/R6GHBHC-A01/2T` for the RGB
array rather than this C01 device. Because core/BOM/netlist files are frozen in this
handoff, E01 records this as a concrete ECAD correction/reselection blocker instead
of silently changing the design authority. The RGB package polarity and exact
replacement MPN must be resolved before schematic/ERC work can be called current.

The C01 electrical data remains useful only for the already-recorded 5 mA Vf screening
numbers (2.2/3.3/3.3 V max for R/G/B); it is not a released package choice. The
Lumissil reference series-resistor values used in the current calculation are 51 Ω
red and 20 Ω green/blue.

Hardware RISET is **120 kΩ 1%**. Recomputing the Lumissil current equation at GCC=SL=255 and applying the datasheet max/typ current ratio plus 1% low-RSET tolerance gives:

- nominal full-scale peak channel: 3.16678 mA;
- conservative full-scale peak channel: 3.45467 mA;
- 39 concurrently active sink channels: 134.732 mA;
- average per LED at full PWM through the scan duty: ~0.341 mA.

At the calculated minimum RGB rail, using 3.3 V maximum green/blue Vf plus the declared 20 Ω series drop and Lumissil maximum sink/switch headroom, calculated remaining path margin is **0.12477 V**. This is positive but small enough that board voltage drop and temperature still require bench confirmation.

Firmware starts with global current 128/255 and software brightness cap 128. Hardware SDB stays low during boot until firmware explicitly enables RGB.

### Worst-case input budget used for design screening

The machine-readable calculation uses these declared assumptions:

- VBUS stress point at receptacle: 4.35 V;
- TPS2553 path resistance: 85 mΩ design value;
- boost output: calculated maximum 5.27743 V;
- conversion efficiency: 85% engineering assumption, not a guaranteed minimum;
- RGB: 39-channel conservative current + 20 mA driver allocation;
- complete 3V3 load: 80 mA engineering allocation.

Iterating the TPS2553 voltage drop gives 4.32432 V at the boost input, 222.16 mA boost input current and **302.16 mA total VBUS budget**, leaving **49.04 mA** to the 351.2 mA minimum current-limit threshold. The margin is useful for design screening but still depends on unverified load and efficiency assumptions.

Pre-enumeration current remains a hard bench gate. `RGB SDB = low` is a design mechanism, not measured proof that the complete device powers up below 100 mA.

## Firmware contract

`firmware-config.json` and `firmware/qmk/info.json` bind the exact 58-key matrix, five encoder pin pairs, I2C1 GP18/GP19, 107 RGB positions and RP2040 target. The QMK scaffold selects:

- `BOARD = GENERIC_RP_RP2040`;
- `BOOTLOADER = rp2040`;
- `RGB_MATRIX_DRIVER = is31fl3741`;
- COL2ROW matrix pins matching the netlist;
- IS31FL3741 address 0x30, GP28 SDB, 29 kHz mode;
- max software brightness 128.

The machine-readable RGB SW/CS table is complete in `logical-netlist.json`. A QMK-native `g_is31fl3741_leds`/`g_led_config` integration unit is not yet generated or target-built, so the QMK hardware contract is not a release firmware binary.

The table also still carries the frozen C01 package/polarity declaration noted above;
therefore its channel indexing is logical evidence, not a schematic/ERC-compatible
RGB implementation until the LED polarity/MPN is corrected and the generated table
is rebuilt from that corrected authority.

## Executed verification

Commands executed on `jangtrinhs-MacBook-Pro-2.local` in `/Users/jang/Products/design-os-3d-blender`:

```text
python3 builds/reference-keyboard/manufacturing/electrical/verify.py --report .../verification.json
-> PASS_LOGICAL_HOST_VERIFICATION, 31 checks

python3 builds/reference-keyboard/manufacturing/electrical/negative_controls.py --report .../negative-controls.json
-> PASS_NEGATIVE_CONTROLS, 5 controls

/usr/bin/gcc -std=c11 -Wall -Wextra -Werror ck001_logic.c test_logic.c ...
-> CK001_LOGIC_PASS gray_cw=1 gray_ccw=-1 matrix=58

/usr/bin/clang --target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -ffreestanding -fno-builtin -Wall -Wextra -Werror -c ck001_logic.c ...
-> ELF 32-bit LSB relocatable, ARM, EABI5
```

ARM object SHA-256: `4afe34f1a9645d7e552b72a65f08f5f7c6444b3cdf5c7201065f4dfc5726d6e3`.

Negative controls prove the verifier rejects:

1. D+/D- short/reused USB PHY pin;
2. missing per-key diode;
3. missing/incorrect USB-C CC Rd;
4. input current-limit evidence exceeding 500 mA;
5. RP2040 GPIO reuse.

The derived `logical-schematic.svg` is machine-generated from the same design generator and explicitly labelled **NOT ERC / NOT PCB**.

## Toolchain capability actually observed

No executable was found for KiCad/kicad-cli/eeschema/pcbnew in PATH or the checked common `/Applications/KiCad...` locations. QMK, `arm-none-eabi-gcc`, CMake and Ninja were also absent. Python, Node, Apple Clang/GCC aliases are available. Apple Clang can emit an ARMv6-M relocatable object for the freestanding control core, but this does not supply the RP2040 SDK/QMK dependency graph or linker/startup/USB/UF2 stages.

Therefore no ERC, PCB routing, DRC, Gerber or full QMK firmware PASS is recorded.

## Manufacturing blockers that remain

Manufacture stays **BLOCKED** until at least:

- instantiate selected symbols/footprints in an ECAD schematic and run actual ERC;
- correct/reselect the RGB LED package so its polarity is electrically compatible with the selected IS31FL3741A SW/current-sink topology, then regenerate the frozen logical RGB authority from that corrected choice;
- decide whether the three visual `RK_STATUS_*` indicators are omitted permanently or added through a later electrical architecture revision; E01 has no spare GPIO assigned to them;
- verify Gateron switch PCB orientation against the manufacturer drawing and a physical part;
- instantiate the exact PEC11R terminal-configuration-1 land pattern, USB4105 land pattern, RP2040/QSPI/crystal/power footprints and RGB driver layout;
- place components against the real CK-001 board outline, holes, case, encoder carriers and USB opening;
- route USB 90 Ω differential pair and switching-power loops; run PCB DRC and impedance review;
- select exact capacitor/resistor package/voltage/derating MPNs where BOM still says generic;
- generate and target-build the QMK RGB channel table/keymap, assign a legitimate USB VID/PID and produce an actual firmware image;
- measure pre-enumeration current, all-white RGB load, RGB_5V1 ripple/regulation, 3V3 rail, TPS2553 trip/latch behavior, encoder waveforms/bounce, USB enumeration and suspend/resume;
- perform ESD/EMC, thermal and repeated physical switch/encoder/USB operation checks appropriate to the intended product;
- complete board-level continuity/short inspection and powered bench tests on assembled prototypes.

No current file claims a fabrication-ready PCB, electrical functional keyboard or manufacture acceptance.

## Primary sources

Machine-readable source details and purpose are in `source-registry.json`. Current primary sources include:

- Raspberry Pi RP2040 hardware design guide: `https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf`
- Raspberry Pi RP2040 documentation: `https://www.raspberrypi.com/documentation/microcontrollers/microcontroller-chips.html`
- QMK RP2040, matrix and IS31FL3741 docs: `https://docs.qmk.fm/platformdev_rp2040`, `https://docs.qmk.fm/config_options`, `https://docs.qmk.fm/drivers/is31fl3741`
- Bourns PEC11R datasheet: `https://www.bourns.com/docs/Product-Datasheets/pec11R.pdf`
- Gateron KS-33H10B050NN-Y24 drawing: `https://gateron.com/u_file/2311/10/file/GATERONKS-33LowProfile20RedSwitchBlackBottomHousing-KS-33H10B050NN-Y24.pdf`
- Lumissil IS31FL3741A: `https://www.lumissil.com/assets/pdf/core/IS31FL3741A_DS.pdf`
- Everlight 19-237B RGB: `https://www.everlight.com/wp-content/uploads/2021/02/19-237B-R6GHBHC-C01-2T.pdf`
- GCT USB4105: `https://gct.co/connector/usb4105`
- ST USBLC6-2: `https://www.st.com/en/protections-and-emi-filters/usblc6-2.html`
- TI TPS2553-1: `https://www.ti.com/product/TPS2553-1`
- TI TLV75533PDBVR: `https://www.ti.com/product/TLV755P/part-details/TLV75533PDBVR`
- TI TPS61023: `https://www.ti.com/product/TPS61023`
- Coilcraft XEL4030-102: `https://www.coilcraft.com/en-us/products/power/high-voltage-inductors/xel/xel4030/xel4030-102/`
- Nexperia BAS316: `https://www.nexperia.com/product/BAS316`

## Verdict

`continue` for the named correction plus ECAD/PCB/prototype work. The electrical design
is concrete enough to carry forward its matrix/encoder/USB/power contracts, while the
RGB package polarity selection, ERC/DRC, target firmware and physical bench gates keep
release/manufacture blocked.
