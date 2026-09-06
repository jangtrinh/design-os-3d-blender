# 3D Asset Marketplaces & Libraries for an AI-Driven Blender Pipeline

**Research date: 2026-07-28.** Target stack: Claude + [`ahujasid/blender-mcp`](https://github.com/ahujasid/blender-mcp) (HEAD `da4e16d`, committed 2026-07-21 — repo is actively maintained).

All endpoint behaviour below marked "verified live" was probed by HTTP request on 2026-07-28 from this machine. Everything else is documentation or dated press, cited at the end. Unverifiable claims are tagged `[UNVERIFIED]`.

---

## 0. TL;DR

**Sketchfab is NOT dead.** Epic closed the *Sketchfab Store* (paid marketplace) on 2024-10-22 and folded it into Fab, but the site, the free CC-licensed corpus, the viewer, and — critically — `api.sketchfab.com/v3` including the Download API are all still serving in July 2026. Fab, by contrast, has **no public API** and is therefore useless to an automated pipeline.

The real risk in a Claude-driven pipeline is not Sketchfab dying. It is **license contamination**: Sketchfab's default search happily returns `NonCommercial` and `NoDerivs` models with `isDownloadable: true`, and blender-mcp does not filter them.

---

## 1. Sketchfab in 2026 — alive, degraded, still programmable

### 1.1 What Epic actually did

| Date | Event |
|---|---|
| 2021-07 | Epic Games acquires Sketchfab |
| 2024-09 | Fab Publishing Portal opens for Sketchfab seller migration |
| 2024-10-22 | **Fab launches. Sketchfab Store closes** — existing Store products remain *viewable* but not purchasable |
| 2024-10-22 | Epic states in the same post: Sketchfab "will maintain its download, viewer, and data APIs" |
| 2024-11-22 | Epic reverses the Quixel Bridge/Megascans shutdown after backlash (see §6) |
| 2025-03 | Last substantive Sketchfab community blog post (cultural heritage feature) — the blog has effectively gone quiet |
| 2025-2026 | No shutdown announcement found for sketchfab.com, its APIs, or the free corpus |

The pattern is **commerce migrated, community platform left on life support**. Epic's own wording was that "very little is changing today for most of the Sketchfab community," and that "advanced notice" would precede any discontinuation of free downloadable content. No such notice has been located.

Historians and cultural-heritage institutions ran a public campaign (80.lv coverage, a Change.org petition) over preservation fears; Epic responded publicly in October 2024 that "preserving someone's work is paramount to us." That political cost is a decent structural reason Epic has not pulled the free corpus.

### 1.2 Live endpoint verification (2026-07-28)

```
GET https://sketchfab.com/                                  -> 200
GET https://api.sketchfab.com/v3/search?type=models&q=chair
    &downloadable=true&count=3                              -> 200, real results
GET https://api.sketchfab.com/v3/models/{uid}               -> 200, full metadata
GET https://api.sketchfab.com/v3/models/{uid}/download      -> 401
    {"detail":"Authentication credentials were not provided."}
GET https://api.sketchfab.com/v3/licenses                   -> 200, 10 license objects
GET https://sketchfab.com/oauth2/authorize/                 -> 200 (redirects to login)
GET https://sketchfab.com/developers/data-api/v3            -> 200 (docs live)
GET https://sketchfab.com/settings/password                 -> 200 (API-token page reachable)
```

The `401` on `/download` is the *correct* response for an unauthenticated call — it proves the route exists and is enforcing auth, not that it is gone. OAuth2 authorize endpoint resolves. **The Download API is operational.**

Docs claim "over 1 million free models, available under Creative Commons licenses. Most models allow commercial use." Download formats via API: **glTF, GLB, USDZ only** — source FBX/OBJ are *not* exposed through the API. This matters: you get triangulated glTF, not clean quad source meshes.

No `X-RateLimit-*` headers are returned on search responses; Sketchfab's published rate limits are not documented on the public pages I could reach. `[UNVERIFIED]` — assume conservative throttling and back off on 429.

### 1.3 The license trap (verified, and this is the important part)

Sketchfab search **does** return a `license` object per result, and the `license=<slug>` query filter **works correctly** — verified by cross-checking filtered results against their individual model endpoints:

```
GET /v3/search?type=models&q=chair&downloadable=true&license=cc0
  -> Side Chair             -> cc0, downloadable: True
  -> Chair (England) 1750-60 -> cc0, downloadable: True
  -> Sutherland Chair       -> cc0, downloadable: True
```

But **without** the filter, the first 5 downloadable results for "chair" were:

| Model | License slug | Commercial? | Derivatives? |
|---|---|---|---|
| The Wizard's Chair | `by-nc-nd` | ❌ | ❌ |
| Scifi Chair Concept | `by` | ✅ | ✅ (credit required) |
| Gaming chair "Kiiro" | `by-nc` | ❌ | ✅ |
| Chair | `free-st` | ✅ | ✅ |
| CHAIR | `by` | ✅ | ✅ |

**Three of five were restricted.** `isDownloadable: true` says nothing about commercial rights. An agent that downloads the top search hit will ship a NonCommercial-NoDerivs asset roughly half the time.

Full license vocabulary from `/v3/licenses`: `by`, `by-sa`, `by-nd`, `by-nc`, `by-nc-sa`, `by-nc-nd`, `cc0`, `free-st` (Free Standard), `st` (Standard), `ed` (Editorial).

**Safe slugs for a commercial automated pipeline: `cc0` only** (no attribution burden). `by` and `by-sa` are usable but create a downstream attribution/copyleft obligation the agent must track. Everything with `nc`, `nd`, or `ed` is disqualifying.

### 1.4 Download API guidelines (contractual, not technical)

Sketchfab's own guidelines page requires that an integrating app:

- authenticate the *end user* with their own Sketchfab account (apps needing unattended download must contact Sketchfab for a special arrangement);
- "clearly display the license of the model as well as author attribution," typically username + link to the model;
- ensure "the Creative Commons license and attribution must follow the asset everywhere it is used";
- "clearly mention that downloadable models are provided by Sketchfab."

For an autonomous agent this is awkward: requirement #1 means a personal API token driving an unattended pipeline is arguably outside the intended terms, and requirement #3 means attribution metadata must be carried through your entire asset pipeline, not just logged once.

### 1.5 Is there a Fab API?

**No public one, as of this research.** Epic promised in the October 2024 Sketchfab post that "in 2025, a public download API for Fab is planned." A community thread on the Epic Developer forums (opened 2024-11-04) asking exactly this received **no official Epic answer**. `https://www.fab.com/` returns **403 to non-browser clients** (bot protection), as does the internal listings search path — consistent with a site that has no intent of being machine-read.

**Conclusion: Fab is not programmable. Do not build against it.** `[UNVERIFIED]` whether a private/partner API exists.

---

## 2. What blender-mcp's Sketchfab integration actually does

Two layers: the MCP server (`src/blender_mcp/server.py`) exposing tools to Claude, and the Blender add-on (`addon.py`) doing the HTTP work in-process.

### 2.1 Tool surface (from `server.py`)

| MCP tool | Params | Backing call |
|---|---|---|
| `get_sketchfab_status` | — | `GET /v3/me` with token |
| `search_sketchfab_models` | `query`, `categories`, `count=20`, `downloadable=True` | `GET /v3/search` |
| `get_sketchfab_model_preview` | `uid` | `GET /v3/models/{uid}` → thumbnail |
| `download_sketchfab_model` | `uid`, `target_size` (**required**) | `GET /v3/models/{uid}/download` → glTF zip → import |

Gated behind a `blendermcp_use_sketchfab` scene checkbox; handlers are only registered when enabled.

### 2.2 Auth

Header-token only, **not OAuth**:

```python
headers = {"Authorization": f"Token {api_key}"}
```

Key resolution order (`_get_sketchfab_api_key`): scene prop `blendermcp_sketchfab_api_key` → addon pref `sketchfab_api_key` → env `BLENDERMCP_SKETCHFAB_API_KEY`. The user pastes a personal API token from their Sketchfab account settings. This works today but sits in tension with the Download API guideline that end users authenticate individually (§1.4).

### 2.3 Search params sent

```python
params = {"type": "models", "q": query, "count": count,
          "downloadable": downloadable, "archives_flavours": False}
if categories: params["categories"] = categories
```

**There is no `license` parameter.** The tool cannot restrict the search to CC0/BY at the API level, even though the API supports it.

Mitigating factor: `server.py` *does* surface the license to Claude in the formatted result string —

```python
license_data = model.get("license") or {}
license_label = license_data.get("label", "Unknown")
formatted_output += f"  License: {license_label}\n"
```

— along with author, faceCount and downloadable status. So the model **can** see `CC Attribution-NonCommercial-NoDerivs` and refuse. It just isn't forced to. This is a policy control, not a technical one, and policy controls fail silently.

### 2.4 Download path

`GET /v3/models/{uid}/download` → parse `data["gltf"]["url"]` → fetch zip → extract with **two zip-slip guards** (absolute-path prefix check plus a literal `..` check) → locate `.gltf`/`.glb` → import → normalize so the largest dimension equals `target_size`. The security hardening is genuinely decent. Note the code reads only the `gltf` key; if a model has no glTF flavour it errors out.

### 2.5 Verdict on continued viability

**It works today and there is no evidence it will stop soon.** Failure modes to watch, in order of likelihood:

1. **License leakage** (present, live, ~50% hit rate on unfiltered search) — the only defect that will actually hurt you.
2. Sketchfab tightens or revokes personal-token download access for unattended use.
3. Epic eventually sunsets the free corpus — Epic committed to advance notice, so this should be a warning, not a surprise.

**Recommended patch:** add `license` to the search params and default it to `cc0`. One-line change in `addon.py::search_sketchfab_models` plus a param in `server.py`. This is the single highest-value modification to make for a commercial pipeline.

---

## 3. Poly Haven — the safe default

Non-profit, funded by Patreon. Everything is **CC0**, no exceptions, explicitly including commercial use, redistribution, and AI training. No attribution required (appreciated, not obligatory). The CC0 covers assets only — the site's logos/renders/text are still copyrighted.

### 3.1 Corpus, measured live 2026-07-28

| Type | Count |
|---|---|
| HDRIs | 980 |
| Textures | 786 |
| Models | 521 |
| **Total** | **2,287** |

Top model categories: props (176), nature (110), industrial (97), furniture (85), decorative (76), tools (70), containers (68), plants (57).

### 3.2 API — no key, no auth, no signup

Verified working request/response chain:

```bash
# 1. Asset types
curl https://api.polyhaven.com/types
# -> ["hdris","textures","models"]

# 2. Category histogram
curl "https://api.polyhaven.com/categories/models"
# -> {"all":521,"props":176,"nature":110,...}

# 3. Filtered asset list
curl "https://api.polyhaven.com/assets?type=textures&categories=metal"

# 4. Single asset metadata
curl "https://api.polyhaven.com/info/rusty_metal_grid"
# -> {"name":"Rusty Metal Grid","categories":["wall","metal"],
#     "authors":{"Amal Kumar":"All"},"max_resolution":[16384,16384],
#     "date_published":1728518400, ...}

# 5. Download manifest — resolutions, formats, direct URLs, md5
curl "https://api.polyhaven.com/files/rusty_metal_grid"
# -> keys: Diffuse, nor_dx, nor_gl, blend, gltf, arm, AO, Displacement, Rough, mtlx
#    each -> {"<res>": {"<fmt>": {"url": "...", "size": N, "md5": "..."}}}
```

The `/files/` response nests **resolution → format → {url, size, md5}**, and `blend`/`gltf` entries carry an `include` map of dependent texture files with their own URLs and hashes. Assets are served from `dl.polyhaven.org`. Resolutions go up to 16K on textures and 16K+ on HDRIs — **check `size` before fetching**, an 8K displacement PNG in the sample was 63 MB and a single 8K .blend bundle exceeded 190 MB.

**Rate limits:** none documented, and 12 rapid sequential requests all returned 200. `[UNVERIFIED]` — no published policy. blender-mcp sets `User-Agent: blender-mcp`; do the same courtesy.

### 3.3 Limits

- **Small.** 521 models is a props/environment kit, not a catalogue. You will not find "a 1967 Ford Mustang" or "an orc warrior."
- **No characters, no vehicles, no rigs, no animation.**
- Coverage is deliberately curated toward archviz/environment: rocks, plants, furniture, industrial clutter, containers.
- Quality is uniformly high — real scanned/authored PBR, sane topology, consistent scale — which is the tradeoff for the small size.
- **HDRIs are the standout.** 980 CC0 HDRIs is best-in-class and there is no real competitor for free environment lighting.

blender-mcp hits `/categories/{type}`, `/assets`, and `/files/{id}` — i.e. it uses the API correctly and completely.

---

## 4. BlenderKit

Native Blender add-on (ships in Blender's own add-on list), asset-browser integrated.

### 4.1 Corpus and tiers

Per CG Channel (2025-09-21): **100,000+ total assets, ~48,000 free** — 17,000+ free models, 26,000+ free materials, 2,000+ free HDRIs. Strengths cited: hard-surface assets and 3D plants.

Pricing at that date: **$14.90/mo or $108/yr** for individuals/studios under $100K revenue; **$40/mo or $300/yr** business. Paid unlocks the remaining ~50,000 assets plus 2 GB cloud storage.

### 4.2 Licensing

Two license types: **CC0** and **Royalty-Free (RF)**. Both permit commercial use. Selling renders, animations and games built with the assets is fine. **Not** permitted: reselling the assets themselves, uploading compositions of others' BlenderKit models to other marketplaces, or deriving-and-reselling materials from downloaded texture sets. In short: RF is a *use* license, not a *redistribute* license — fine for a rendered/baked pipeline, wrong for shipping raw source assets.

### 4.3 Programmatic / headless access

The public search API is reachable **without authentication** (verified 2026-07-28):

```bash
curl "https://www.blenderkit.com/api/v1/search/?query=chair&page_size=2"     # -> 200
```

Response fields include `name`, `assetType`, `license` (`cc_zero`, etc.), `isFree`, `isForSale`, `basePrice`, `canDownload`, `files`, `filesSize`, `verificationStatus`, `ratingsMedian`. Query syntax supports field filters — `?query=asset_type:model+is_free:true` works. Result `count` is capped at 10,000 per query, so the API will not tell you the true corpus size (model=10000, material=10000, hdr=10000, brush=6515, scene=4371 — the first three are clearly clamped).

Notably, **`license` and `isFree` are first-class searchable/returnable fields** — better license ergonomics than Sketchfab's integration offers today.

Actual *download* requires an authenticated BlenderKit API key and is normally driven by the add-on. Whether download can be driven cleanly from `blender --background` with a script is `[UNVERIFIED]` — the add-on is designed around the interactive asset browser and asynchronous daemon, and I found no official headless documentation. The add-on itself is GPL (BlenderKit/BlenderKit on GitHub), so the download path is at least readable and adaptable.

### 4.4 AI features

BlenderKit is **not** primarily an AI-generation product. I found no first-party text-to-3D generation feature documented. The 2026 Blender AI plugin landscape (3D-Agent, various text-to-3D add-ons) is a separate ecosystem. `[UNVERIFIED]` whether BlenderKit has added generative features since Sept 2025.

**No blender-mcp integration exists.** Wiring it in would be a meaningful upgrade — it is the largest free, license-tagged, Blender-native corpus available.

---

## 5. Other corpora worth wiring in

### 5.1 ambientCG — CC0, excellent API, textures/materials

**2,004 materials** as of 2026-07-28 (verified). Still actively publishing — the top-popularity asset in my query had `releaseDate: 2026-07-22`. Everything **CC0**.

```bash
curl "https://ambientcg.com/api/v2/full_json?type=Material&limit=2&include=downloadData"
```

Returns `{searchQuery, numberOfResults, nextPageHttp, currentPageHttp, foundAssets[]}`. Per-asset: `assetId`, `releaseDate`, `dataType`, `creationMethod` (e.g. `PBRPhotogrammetry`), `tags[]`, `downloadCount`, `popularityScore`, `displayName`, plus download data when requested. `nextPageHttp` gives you cursor-free pagination for free. No auth, no key. Other `type` values beyond `Material` exist (3D models, HDRIs, substances, decals) — I only verified `Material`.

This is the natural companion to Poly Haven: PH has ~786 textures, ambientCG has ~2,004, both CC0, near-zero overlap in coverage style. **Both should be in the pipeline.**

### 5.2 Poly Pizza — low-poly, CC0/CC-BY, needs a key

The de-facto successor to Google Poly, hosting the archived Google Poly corpus plus new uploads. Site returns 200. API is **v1.1 at `api.poly.pizza`** and **requires a key** (verified: `GET https://api.poly.pizza/v1/search/chair` → `401 {"error":"You need an API key to do that dingus"}`). Keys are free on request from the site.

Endpoints, per the community MCP wrapper (`MatthewHallCom/Poly-Pizza-MCP`): model-by-id, curated lists, keyword search, search with category/license/animation filters, user lookup. Licenses span the full CC range — **CC0, CC-BY, CC-BY-SA, CC-BY-ND, CC-BY-NC, CC-BY-NC-SA, CC-BY-NC-ND** — so the same filtering discipline as Sketchfab applies. The API exposes a license filter, which is the right primitive. Exact auth header name and corpus count `[UNVERIFIED]` (docs page is JS-rendered and returned no extractable content).

**Best for:** stylised/low-poly game props, rapid blockouts, anything where 500-triangle assets are a feature.

### 5.3 Objaverse / Objaverse-XL — a research dataset, not a marketplace

**Objaverse 1.0: ~800K objects. Objaverse-XL: 10M+.** Sources: GitHub, Thingiverse, Sketchfab, Polycam, Smithsonian. Python download API (`pip install objaverse`), Hugging Face hosted, Colab tutorial available.

**The license situation is the whole story.** The *dataset* is ODC-By v1.0; the *objects* are not uniform. AI2's own docs state: "Individual objects in Objaverse-XL are licensed under different licenses." Specifically:

- The Sketchfab-sourced slice inherits per-model CC licenses — including **NC and ND** variants.
- **Polycam data is academic, non-commercial, by request and approval only.**
- GitHub-sourced meshes carry whatever the host repo's license is — frequently unstated, which legally means *all rights reserved*, not permissive.
- Thingiverse is a mix including NC.

There is metadata for filtering (a subsets/metadata guide covering license, category, polycount exists), but the burden is entirely on you, and provenance for the GitHub slice is weak.

**Practical verdict:** Objaverse is excellent as a *retrieval* corpus for research, embeddings, and internal experimentation — 10M objects with CLIP-friendly metadata is unmatched for "find me something roughly like X." It is **poor as a production asset source**: no CDN-quality delivery, wildly variable mesh quality and scale, no normalization, and a licensing surface that cannot be cleared automatically with confidence. Use it to *find* a concept, then source or build the actual shipped asset elsewhere. Do not let an agent auto-ship an Objaverse mesh into a commercial product.

### 5.4 Smithsonian Open Access — CC0, museum-grade, narrow

**2.8M+ items** released at 2020 launch, growing since. CC0 with no attribution or fee required for commercial use; the FAQ correctly warns CC0 covers copyright only — trademark, publicity and third-party rights may still bite.

API is hosted on api.data.gov. Verified live: `GET https://api.si.edu/openaccess/api/v1.0/search?q=chair&api_key=DEMO_KEY` → **200** with real rows. A free data.gov API key lifts the DEMO_KEY quota. Metadata is also mirrored as JSON on GitHub, refreshed weekly — worth using for bulk indexing instead of hammering the API. 3D formats: glTF, glb, obj (150k-decimated and full-res), plus Voyager web scenes.

`3d.si.edu` returned **403 to curl** (bot protection); the API path is the correct machine entry point.

**Coverage is museum objects**: artifacts, specimens, sculpture, historical machinery. Superb for heritage/education/documentary work, irrelevant for game props or archviz. Meshes are scan-derived — dense, unretopologised, often with baked lighting in the texture.

### 5.5 Others, briefly

- **Quaternius, Kenney.nl** — CC0 stylised/low-poly game asset packs. No API; static ZIP downloads. Trivially mirrorable into a local library, which for an automated pipeline is arguably *better* than an API.
- **Free3D, CGTrader free tier, TurboSquid free tier** — heterogeneous licensing, no clean API, bot-protected. Not automatable.

---

## 6. Fab

Epic's unified marketplace, launched 2024-10-22, merging **Sketchfab Store + Quixel Bridge/Megascans + ArtStation Marketplace + Unreal Engine Marketplace**. Web at fab.com plus an integrated tab in the Epic Games Launcher, and a Fab plugin for Blender.

### 6.1 Licensing model

Two tiers: **Fab Standard** (use in all engines and tools, commercial projects allowed) and **Fab Professional** (higher seat/revenue thresholds). Epic's stated position: "When you acquire Quixel content on Fab – whether free or paid – you can use it forever." Acquisition is permanent; entitlements are per-account.

### 6.2 API

**None public.** See §1.5. fab.com returns 403 to non-browser HTTP clients. The 2025 "public download API" promised in Epic's October 2024 Sketchfab post has not materialised in any documentation I could find, and the community thread asking for it went unanswered.

### 6.3 The Megascans saga — resolved, and it ended badly for free users

| Date | Event |
|---|---|
| pre-2024 | Megascans free for Unreal Engine users under the Epic Content License |
| 2024-10 | Fab launches; **Megascans made free to *everyone*, but only until 2024-12-31** |
| 2024-11-22 | After backlash, Epic **restores Quixel.com and Quixel Bridge**; one-click "claim all legacy assets" tool announced |
| 2024-12-31 | **Claim deadline.** Anything claimed by this date is yours permanently under the Epic Content License |
| 2025-01-01 → | "The majority of Megascans will no longer be available for free unlimited use in Unreal Engine projects." Per-asset pricing: 2D/3D assets from **$0.99**, procedural kits **$4.99**, packs **$24.99** |
| 2025-2026 | Fab-in-Launcher supersedes Bridge as primary delivery. Quixel Mixer ships its **final offline version, no further updates**. New Megascans are **Fab-exclusive as of early 2026**; not all legacy assets migrated (some failed quality bar) |

**Net:** if you did not claim the legacy library before 2024-12-31, Megascans is now a paid catalogue with no API. It is out of scope for an automated pipeline regardless of budget, because there is no way to fetch it programmatically.

---

## 7. Licensing decision table

| Source | Licenses | Commercial | Attribution | Redistribute asset | API | Auth | Agent may auto-ship? |
|---|---|---|---|---|---|---|---|
| **Poly Haven** | CC0 only | ✅ | ❌ optional | ✅ | ✅ open | none | ✅ **Yes — unconditional** |
| **ambientCG** | CC0 only | ✅ | ❌ optional | ✅ | ✅ open | none | ✅ **Yes — unconditional** |
| **Smithsonian OA** | CC0 (subset of collection) | ✅ | ❌ optional | ✅ | ✅ | data.gov key | ✅ Yes, if `CC0` flag confirmed per item; check trademark/publicity separately |
| **Sketchfab** `cc0` | CC0 | ✅ | ❌ optional | ✅ | ✅ v3 | user token | ✅ Yes — **only with `license=cc0` filter** |
| **Sketchfab** `by`/`by-sa` | CC-BY / BY-SA | ✅ | ✅ **required** | ✅ (BY-SA: copyleft) | ✅ v3 | user token | ⚠️ Only with automated attribution tracking; BY-SA infects derivatives |
| **Sketchfab** `free-st`/`st` | Sketchfab Standard | ✅ | varies | ❌ | ✅ v3 | user token | ⚠️ Read the Standard terms; no redistribution |
| **Sketchfab** `*-nc`/`*-nd`/`ed` | NC / ND / Editorial | ❌ | ✅ | ❌ | ✅ v3 | user token | ❌ **Never.** Hard block |
| **BlenderKit** CC0 | CC0 | ✅ | ❌ | ✅ | ✅ search open | key for download | ✅ Yes |
| **BlenderKit** RF | Royalty-Free | ✅ | ❌ | ❌ **no resale** | ✅ search open | key + subscription | ⚠️ Yes for rendered/baked output; ❌ for shipping source assets |
| **Poly Pizza** CC0 | CC0 | ✅ | ❌ | ✅ | ✅ v1.1 | free key | ✅ Yes with license filter |
| **Poly Pizza** CC-BY / NC / ND | mixed CC | varies | varies | varies | ✅ v1.1 | free key | ⚠️/❌ Filter at API level |
| **Objaverse / XL** | **heterogeneous**; ODC-By dataset wrapper; per-object CC + unknown + Polycam academic-only | ❓ | ❓ | ❓ | ✅ python | HF / form for Polycam | ❌ **No.** Retrieval/research only |
| **Fab / Megascans** | Fab Standard / Professional | ✅ (paid) | ❌ | ❌ | ❌ **none** | — | ❌ Not automatable |
| **Quaternius / Kenney** | CC0 | ✅ | ❌ | ✅ | ❌ (static ZIPs) | none | ✅ Yes — mirror locally |

**Hard rules for the agent:**
1. Never download from Sketchfab without an explicit `license=` filter set to an allowed slug.
2. Treat `isDownloadable: true` as a *technical* capability, never a *legal* permission.
3. Persist `{source, uid, author, license_slug, url}` alongside every imported asset. Attribution obligations are unrecoverable if you lose provenance at import time.
4. Objaverse output never reaches a shipped artifact without a human license review.

---

## 8. Retrieval vs. generation

blender-mcp ships both: retrieval (Poly Haven, Sketchfab) and generation (Hyper3D Rodin, Hunyuan3D). They are not interchangeable, and the choice is mostly not about quality.

### Retrieve when

**The asset is a real, named, conventional object.** A folding chair, an oil drum, a cobblestone texture, an overcast sky HDRI. These exist, someone scanned or modelled them properly, and a generator will produce a worse, lumpier version at higher cost. Retrieval on Poly Haven is a two-call round trip — sub-second, free, deterministic.

**Topology matters.** Retrieved production assets have deliberate edge flow, sane UVs, real PBR map sets, LODs sometimes. Generated meshes in 2026 are still predominantly marching-cubes-ish or dense triangle soup with vertex-colour or projected textures. If the asset will be deformed, subdivided, animated, or UV-edited downstream, generation is a trap — you will spend more time retopologising than you saved.

**Anything involving lighting.** There is no generative substitute for a 16K measured HDRI. Poly Haven's 980 HDRIs are the single most valuable free resource in this entire document.

**Determinism and reproducibility.** A UID resolves to the same bytes tomorrow. A prompt does not. For a pipeline that must rebuild a scene identically, retrieval is the only defensible choice.

**Cost.** Poly Haven and ambientCG are free and unmetered. Rodin and Hunyuan are metered per generation with daily caps on trial keys.

### Generate when

**The asset does not exist and is specific.** "A ceremonial mask for a fictional civilisation with seven eye slots and coral inlay." No corpus contains this. Searching is a waste of tokens; generate.

**Coverage genuinely fails.** Poly Haven's 521 models cover props and environment. The moment you need a character, a vehicle, a creature, or a branded object, retrieval from the CC0 corpora collapses and your only clean-license options are generation or commissioning.

**License purity is non-negotiable and the corpus is contaminated.** This is the underrated argument for generation. A generated mesh has no upstream CC-BY-NC attached to it. Given §1.3 — half of unfiltered Sketchfab downloadable results are restricted — generation can be the *lower legal risk* path even when a retrievable asset exists. Note the countervailing risk: the training-data provenance of the generator itself is unsettled, and output copyrightability for purely AI-generated work is weak in several jurisdictions. `[UNVERIFIED]` — no stable 2026 case law located. You trade a *known* license constraint for an *unknown* one.

**Iteration speed on form beats fidelity.** Blockouts, greybox, previz, concept exploration. Generate ten variants, pick one, replace it later.

### The rule

> **Retrieve by default. Generate on retrieval failure.**

Concretely, the agent should:
1. Query Poly Haven / ambientCG (CC0, free, instant, zero legal load).
2. Query Sketchfab **with `license=cc0`**, or `by` if attribution can be tracked. Optionally BlenderKit for breadth.
3. Only if 1-2 return nothing semantically adequate, generate.
4. Always prefer retrieval for HDRIs and tiling materials, regardless of step order — generation is not competitive there.

The failure mode to actively design against is the inverse: an agent that generates first because it is a single tool call and "feels" more capable, producing a scene of mushy 200K-triangle blobs when 30 seconds of CC0 retrieval would have given clean, UV'd, correctly-scaled production geometry. Bias the tool descriptions and system prompt toward retrieval explicitly — blender-mcp's `asset_creation_strategy` prompt is the right place to enforce this.

---

## Sources

**Sketchfab / Fab**
- [Sketchfab Update: What You Need To Know Now That Fab's Live](https://sketchfab.com/blogs/community/sketchfab-update-what-you-need-to-know-now-that-fabs-live/) — Sketchfab Community Blog, 2024-10 (store closed 2024-10-22; APIs maintained; Fab download API "planned in 2025")
- [Fab Publishing Portal Open for Sketchfab Migration](https://sketchfab.com/blogs/community/fab-publishing-portal-open-for-sketchfab-migration/) — 2024-09
- [Sketchfab Download API — Developers](https://sketchfab.com/developers/download-api) — glTF/GLB/USDZ, 1M+ free CC models
- [Download API Guidelines](https://sketchfab.com/developers/download-api/guidelines) — attribution and end-user auth requirements
- [Sketchfab Data API v3](https://sketchfab.com/developers/data-api/v3)
- [Epic Games Phases Out SketchFab in 2025, Launches Unified Fab Marketplace](https://www.fabbaloo.com/news/epic-games-phases-out-sketchfab-in-2025-launches-unified-fab-marketplace) — Fabbaloo
- [Historians Aren't Too Happy about the Sketchfab to Fab Migration](https://80.lv/articles/historians-are-concerned-about-epic-games-sketchfab-to-fab-migration) — 80.lv, 2024-10
- [Epic Games responds to controversy over its new Fab marketplace](https://gameworldobserver.com/2024/10/23/fab-marketplace-epic-games-sketchfab-preservation) — Game World Observer, 2024-10-23
- [Petition: Keep Sketchfab Alive](https://www.change.org/p/keep-sketchfab-alive-preserve-open-access-to-3d-art-museum-collections) — Change.org
- [Is there, or will there be a Fab API?](https://forums.unrealengine.com/t/is-there-or-will-there-be-a-fab-api-mostly-for-quixel-as-of-right-now-but-preferably-for-all-assets/2103358) — Epic Dev Community forums, thread opened 2024-11-04, no official reply
- [Fab Transition FAQs](https://support.fab.com/s/article/Fab-Transition-FAQs) — Fab support
- Live endpoint probes against `api.sketchfab.com/v3`, `sketchfab.com`, `www.fab.com` — 2026-07-28

**Quixel / Megascans**
- [Epic has made Megascans free to all – but only until the end of 2024](https://www.cgchannel.com/2024/10/epic-games-has-made-megascans-free-to-all-but-only-until-the-end-of-2024/) — CG Channel, 2024-10 (pricing: $0.99 / $4.99 / $24.99)
- [Quixel Megascans is Back](https://gamefromscratch.com/quixel-megascans-is-back/) — GameFromScratch, restoration 2024-11-22, claim deadline 2024-12-31
- [Quixel to Fab Migration: The Indie Developer's 2026 Survival Guide](https://www.strayspark.studio/blog/quixel-to-fab-migration-indie-developer-survival-guide-2026) — StraySpark, 2026 (Mixer final version, Fab-exclusive new Megascans)
- [Epic Games adds Fab to its launcher with Quixel Bridge features](https://cgpress.org/archives/epic-games-adds-fab-to-its-launcher-with-quixel-bridge-features.html) — CGPress

**blender-mcp**
- [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) — source read at commit `da4e16d2069ce5154eaa2535bf995e843caf5c73`, 2026-07-21; `src/blender_mcp/server.py`, `addon.py`

**Poly Haven**
- [Poly Haven License](https://polyhaven.com/license) — CC0
- `api.polyhaven.com` — `/types`, `/assets`, `/categories/{type}`, `/info/{id}`, `/files/{id}` probed live 2026-07-28

**BlenderKit**
- [Get 48,000 free 3D models, HDRIs and materials from BlenderKit](https://www.cgchannel.com/2025/09/get-over-48000-free-3d-models-materials-and-hdris-from-blenderkit/) — CG Channel, 2025-09-21
- [BlenderKit Licensing FAQ](https://www.blenderkit.com/docs/licenses/licensing-faq/)
- [BlenderKit Terms and Conditions](https://www.blenderkit.com/terms-and-conditions-2021/)
- [BlenderKit/BlenderKit on GitHub](https://github.com/BlenderKit/BlenderKit)
- `www.blenderkit.com/api/v1/search/` probed live 2026-07-28

**ambientCG / Poly Pizza**
- `ambientcg.com/api/v2/full_json` probed live 2026-07-28 — 2,004 Materials
- [Poly Pizza](https://poly.pizza/) and [API docs v1.1](https://poly.pizza/docs/api/v1.1) (JS-rendered, not extractable)
- [MatthewHallCom/Poly-Pizza-MCP](https://github.com/MatthewHallCom/Poly-Pizza-MCP) — endpoint/auth reference
- `api.poly.pizza/v1/search/` probed live 2026-07-28 → 401, key required

**Objaverse**
- [allenai/objaverse-xl](https://github.com/allenai/objaverse-xl) — 10M+ objects, ODC-By v1.0 wrapper, per-object license heterogeneity, Polycam academic restriction
- [Objaverse project site](https://objaverse.allenai.org/) and [Objaverse 1.0 API docs](https://objaverse.allenai.org/docs/objaverse-1.0/)
- [allenai/objaverse on Hugging Face](https://huggingface.co/datasets/allenai/objaverse)
- [Objaverse Subsets & Metadata guide](https://objaverse-xl.com/guides/subsets-metadata.html)

**Smithsonian**
- [Smithsonian Open Access FAQ](https://www.si.edu/openaccess/faq) — CC0 terms, 2.8M+ items, formats, api.data.gov
- [Smithsonian 3D Open Source Resources](https://3d.si.edu/open-source-resources)
- `api.si.edu/openaccess/api/v1.0/search` probed live with `DEMO_KEY` 2026-07-28 → 200
