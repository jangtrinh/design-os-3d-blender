# CK-001 first-article and bench procedure

These are proposed project pilot-screening requirements. They are not a claim of
external certification, a material data sheet, a lifetime qualification or completed
physical work. `bench-records.json` deliberately contains no measurements.

## Start with the real interfaces

Obtain the exact selected switch, encoder and screws. Preserve packaging, lot and
part numbers. Measure the switch's surrounding dust/actuator structure before
trying the custom 6.4 mm boss. The B prototype enlarged a static cover opening;
that modification does not establish factory-switch compatibility. A drawing of
the male cross alone is insufficient to approve the whole cap.

Inspect the actual free stroke and hard stop. The source KS-33 range is 2.8 to
3.2 mm. Do not force a shorter-stroke factory switch to 3.2 mm. The digital design
and an unloaded test fixture need clearance through the maximum design envelope;
the assembled physical switch is checked at its own measured stop.

## Fabricate and identify the fit ladder

The native specimen set contains K01..K09 cross-receiver variants, D01..D03 open
D-profile gauges, G01..G03 guide sleeves and P01 nominal 2 mm guide pin. STL master
coordinates are local to each specimen; display copies are only for identification.
The verified Revision-B keycap STL is a separate baseline control with its original
4.12 / 1.22 / 1.40 mm receiver, not a proven physical fit.

Mark bags or trays with the specimen IDs before separating them from the process
batch. Record actual polymer/alloy grade, batch, machine, orientation, build or
machining settings, support strategy, washing/curing or conditioning, tool offsets
and finishing. Do not sand a receiver without recording the material removed.
SLS/printed calibration results do not transfer automatically to machined POM-C,
injection-molded PBT or a different resin/process.

Use the actual intended male part. Inspect dimensions first and start with a safe
clearance candidate. Some ladder entries intentionally cover an interference
region; stop if they cannot start squarely or if the surrounding switch structure
contacts the boss. The correct production receiver is selected from measured force
and wear behavior, then must be regenerated and reverified as a new design revision.

## Record forces, not just "fits"

Use a calibrated force gauge with a fixture that supports the switch housing and
pulls axially through the cap. Record the force/displacement trace, peak installation
force, initial removal force and removal after 50 service cycles on the same five
specimens. Note cracks, whitening, loose switch retention, irreversible stem damage
or permanent distortion, even when a numeric force happens to lie in the window.

For knob retention, first establish a safe set-screw torque on material-matched
coupons. Apply a 10 N axial load and a separate 0.05 N m torsional load for 10 s.
Record slip and damage on all five interfaces. The screw maker's maximum torque is
an upper screw limit, not an assembly setting or a prediction of the knob thread's
strip torque. The set-screw tip should contact the shaft flat, not the round surface.

Destructively characterize spare post/thread specimens before choosing assembly
torque. Record the first limiting joint failure, which may be thread strip, screw
fracture, floor pull-through or post fracture. Its uncertainty-adjusted torque
margin must exceed the proposed assembly setting by the project criterion. This
is a joint failure margin; do not label an earlier screw fracture as a measured
thread strip torque. Repeat on the intended alloy, tap class and surface finish;
a brass-pilot CAD hole is not an actual female thread.

## Guides, board supports and the assembled product

Cycle three guide/spacebar assemblies through at least 10,000 screening strokes,
including offset presses. Log sticking/return failures and lateral play after the
run. This is a screening checkpoint, not lifetime certification.

Load daughterboard supports in all three axes while monitoring permanent shift,
fastener damage and electrical continuity. Confirm service-tool access before
closing the case. Check that the acrylic has a positive axial locating/retention
scheme and thermal clearance, rather than relying on a coincident CAD surface.

After schematic, PCB and firmware prerequisites are complete, use a current-limited
USB source and a logged current/voltage fixture. Test both Type-C plug orientations,
pre-enumeration, all-white RGB, suspend/resume, reconnect and fault recovery. Exercise
every key individually, combinations that expose ghosting, and each encoder in both
directions at slow and fast turns. Preserve host event logs and firmware identity.

Measure regulator, driver and externally touchable temperatures after at least one
hour at the declared full-load condition. Record ambient, cable/source voltage and
RGB command. Do not convert a component's maximum rating into a normal operating
temperature target. Internal junction temperature and PCB thermal design need their
own analysis in addition to touch-surface measurements.

## Data format and replay

Each observation records `metric`, `sample_serial`, `hardware_mpn`, `material_lot`,
`operator`, timezone-aware `measured_at`, `instrument_id`, `value`, `unit`, stated
`uncertainty`, `damage_observed`, the required test `conditions`, and a `raw_record`
path/SHA256 pin. Damage is inspected, not assumed absent. The strip-margin ratio
also records both raw torques and their uncertainties under `derivation`; its
instrument is calibrated in N m, and the reported ratio interval must include the
worst-case propagated torque intervals.
Destructive thread specimens must record the observed limiting failure mode and
expected damage; functional specimens must remain undamaged. For a nonnegative
slip/current magnitude, a zero reading is allowed and its upper uncertainty bound
must satisfy the maximum; negative measured magnitudes are rejected.
Instrument entries include ID, unit, calibrated range, validity dates and a pinned
calibration record. Store raw traces and certificates inside this project before
referencing them. The checker verifies file identity; it cannot authenticate a lab.

Only set `origin` to `physical_measurement` for actual physical records. Bind the
record set to the exact SHA256 of the generated `design-snapshot.json`. A change to
a receiver, screw, process, PCB or firmware invalidates the affected evidence.
The checker rejects missing samples, changed raw files, inconsistent units,
out-of-range instruments, expired calibration and uncertainty intervals crossing
an acceptance boundary. Synthetic unit-test values are never bench measurements.

An evidence-complete result applies only to the declared pilot scope. Regulatory
assessment, production process control and reliability objectives are separate
engineering decisions; no certificate or supplier approval is generated here.

## Frozen configurations and instrumented test conditions

Before collecting release evidence, create a new snapshot with a timezone-aware
`frozen_at`, explicit `design_inputs` roles and per-specimen `test_configurations`.
Each configuration names its supported metrics, exact hardware MPN, pinned process
record and applicable manufacturer screw torque limit. Each observation references
that `configuration_id` and must postdate the freeze. PA12, POM-C, aluminum and
brass specimens must not be combined under an unspecified global process string.

Each required condition is a measurement object with `value`, `uncertainty`,
`instrument_id` and pinned `raw_record`. Forces, torque, elapsed time, temperature
and cycle/event counts need their own appropriate calibrated/logged evidence.
Installation, initial removal and post-service removal use the same five specimens
in that temporal order; axial and torsional knob tests likewise retain specimen,
hardware, material-lot and process identity.

The legacy metric ID `post_strip_margin` is retained for file compatibility, but
its derivation now uses `joint_failure_torque_Nm`, `failure_uncertainty_Nm`,
`assembly_torque_Nm` and `assembly_uncertainty_Nm`. The assembly torque plus its
uncertainty must not exceed the selected screw limit in the frozen configuration.

An assessment records the snapshot, bench records, raw/calibration/process pins
and assessment time. Call `validate_assessment()` before relying on a previously
written report; it re-hashes the evidence and recomputes the predicates. Digital
prerequisites must bind the same source hashes and carry explicit acceptance
fields. These checks still cannot authenticate measurement honesty, a laboratory
or unobserved operating conditions; independent engineering review remains needed.
