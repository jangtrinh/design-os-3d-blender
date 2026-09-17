# CK-001 dimensional decisions

This is a native reconstruction/engineering adaptation from the owner images,
not a copied vendor CAD assembly. Latest catalog dimensions govern the candidate:
284 x 92 mm, 32 mm maximum including 2 mm feet, 4 mm lower enclosure, 8 mm acrylic
frame, 1.6 mm PCB, 1.5 mm mounting plate, 16 x 18 mm knobs, 14 mm keycap tops and
9.5 mm keycap height. The earlier 41 mm side annotation is retained as a source
conflict. Weight and printed compliance symbols are not qualification evidence.

The layer stack requires explicit reconciliation: lower case z0..4; acrylic4..12;
PCB11.8..13.4 sits in a0.2 mm seating rebate; plate13.6..15.1 leaves a0.2 mm gap;
the knob's lower3.1 mm is a recessed8.4 mm diameter neck so its barrel seats at15.1
and top reaches30; feet end at-2. This achieves32 mm without barrel/plate overlap.
The neck, rebate, bolt grid, PCB outline, USB location, spacing and key transcription
are local design decisions, not dimensions asserted to be visible in the images.

Four nominal5.4 mm brass spacers stand between base floor z2 and plate underside13.6.
Eight6 mm M3 envelope screws attach at both ends. Their6 mm smooth shanks are a
visual/mechanical envelope only; tapped/helical threads and preload are unqualified.
The diffuser has5.8 mm spacer bores. Plate clearance3.4 mm is an authored requirement.

The drawn~70 keycap/switch quantities describe sets; the interpreted mounted layout
has58 caps:47 main,9 loop and2 nano. Five knobs match the repeated visible control
arrangement. These counts must still be reviewed against the original image bytes.

Known remaining interface gaps: exact switch/socket and retaining features, keycap
stem receiver, D-shaft flat dimension/fit, PCB components/netlist/electrical isolation,
encoder mounting, spacer selection/threads, material process and physical test data.
No print/manufacture or functional-electronics acceptance can follow from this model.
