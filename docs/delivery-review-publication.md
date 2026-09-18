# Publishing a delivered package as a public review page

The build's own delivery folder proves the work to the owner. This procedure turns that
folder into a page the public can read, without letting presentation soften the evidence.
Written from the CK-001 r01/r02 and DC-01 R02/R03 publications (September 2026); every rule
here paid for a rerun, a gate failure or an owner correction.

## The generators, not the HTML

`docs/reviews/<build>/build-media.py` and `build-page.py` take `--source <delivered package>`
and `--out docs/reviews/<build>/<revision>`. One copy of each serves every revision; the
stylesheet and carousel script sit beside them and are inlined so a page also opens from disk.

**Regenerate, never patch.** A published page is 90 KB of generated HTML: a regex edit closed a
`<fieldset>` early and cost five reruns before the static gate reported the last symptom. If the
copy is wrong, change the builder and run it again.

## Numbers come from receipts

Every figure on the page is read from the delivered package at build time. Nothing is retyped:

| Figure | Receipt |
|---|---|
| Part count, material split, plate assignment, bounding size, triangles | `print/package-manifest.json` |
| Gate result, failed parts, missing required checks | `print/final-gate.json` |
| 3MF reopen verdict, STL round-trip | `print/package-check.json` |
| Tracks, vias, pads, ERC/DRC verdicts, negative controls, physical measurements | `electronics/delivery-audit.json` |
| Film duration, frame count, distinct renders, audio | `reports/presentation/video-receipt.json` |
| Render engine, samples, device | `reports/presentation/native-frames.json`, else `renderer-profile.md` |
| Scene and video hashes, part labels | `snapshot.json` |
| Archive bytes, file count, status, physical samples | `completion.json` |

Different revisions record the same fact in different files: R02 named the render engine in the
frame receipt, R03 only in the renderer profile. Read whichever the package carries and
**assert the fact is recorded** — never default a value that would flatter the build.

## Media rules

- Stills and renders publish as progressive JPEG q88; a 1.4 MB PNG becomes 70–140 KB.
- One revision stays around 25 MB. Run directories (1.4 GB, single files over 100 MB), delivery
  packages and manufacturer PDFs stay local; `.gitignore` carries `builds/*/runs/`,
  `builds/*/manufacturing/runs/`, `builds/*/delivery/`, `builds/*/*.zip` and the PDFs.
- Print files become pictures: import each gated STL, lay the thinnest extent up as it would sit
  on a bed, render one clay view, and assert a non-blank result (share of pixels differing from
  the background ≥ 0.02; the real builds measured ≥ 0.31). A disc photographed in its own plane
  reads as a line — that is why the orientation step exists.
- A still with text baked into its pixels gets a cropped copy for cards and carousels; the
  labelled original stays on the evidence page, uncropped. Never retouch inside the frame.
- `media-manifest.json` records every published file with its byte size and SHA-256, so a page's
  claims stay traceable to the bytes a visitor downloads.

## Revisions are added, never overwritten

A newer package is published as its own folder (`r02`, `r03`). The landing card, README row and
`sitemap.xml` point at the current one; the older revision stays online at a lower sitemap
priority, and each footer links the other. Overwriting a published revision destroys the honest
record of what was delivered when.

## Page rules the gate cannot infer

- Cards stack: image on top, text underneath, one column at every width; at most two short
  sentences of body copy.
- Nothing is overlaid on an image — no chip, badge, counter or caption pill inside the frame.
- A shields.io badge carries its own intrinsic width: set `height` only, never `width`, and back
  it with `.badges img{height:28px;width:auto;max-width:100%}`. A fixed width distorts the
  letterforms and it shows at a glance.
- Hero badges name the stack the build was made with. Status facts (`BLOCKED`, sample count,
  gate results) live in the lede, the facts register and the "what this does not prove" section.
- A missing image is a named blank, never a placeholder picture: the page defines its own
  `window.__imgFallback` that reports the missing file. The autofixer's default placeholder
  service has no place on an engineering page.

## Gate ladder, cheapest first

```bash
python3 scripts/check-html-tag-balance.py docs/reviews/<build>/<revision>/index.html
ui gate docs/reviews/<build>/<revision>/index.html --tokens <design.tokens.json>
node scripts/page-checks/check-rules.mjs <file-or-url>   # badge aspect, stacked cards, no overlay
node scripts/page-checks/check-page.mjs  <file-or-url> <out-dir>
# check-page: 1280 and 390 - scrollWidth === innerWidth, every image decoded, Inter and
# JetBrains Mono resolved, 0 console errors, 0 keyframes, no two rules within 40 px, plus a
# screenshot per width. It scrolls the page and the carousel first, so lazy images decode.
```

Run the last two against the **live URL** after the Pages build reports the merge SHA, then look
at the screenshots. Accepted warning: `text-in-image` on shields.io badges, an owner decision.

Two traps cost a round each and are worth remembering: a caption `cite` inherits
`white-space: nowrap`, so a 64-character SHA-256 pushed the phone layout to 607 px until the
rule was overridden; and lazy images inside a horizontal carousel never decode until the track
is scrolled, so the checker scrolls it before asserting.

## What the page may never do

State a physical property. Manufacture stays `BLOCKED` with the sample count visible while
printing, fit, retention, electrical operation, firmware and thermal evidence are absent. A
passing geometry gate, a clean export and a smooth film are digital results; the page says so in
its own section rather than in a footnote.
