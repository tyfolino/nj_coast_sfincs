<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `reference_inlet_waterlevel_clamp`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** 🔴 THE OCEAN LEVEL WAS CLAMPED 2.6 km INSIDE BARNEGAT INLET in every v2 run to 2026-07-29. mask_zmin=-10 makes the -10 m isobath the water-level boundary, and that isobath reaches through a scoured inlet. Fixed 2026-07-30; the v2 fingerprint changed 9ccbab0bc7a9fc0d -> 3b1356b9590c59ff, so the whole 07-26..29 campaign is non-comparable.


# A depth threshold is a statement about elevation; the mask it makes is about topology

`BaseConfig.mask_zmin = -10` makes every cell deeper than −10 m INACTIVE, so the active
domain's seaward limit is the −10 m isobath and `create_boundary(waterlevel, zmax=-1)`
lays the imposed open-ocean level along it. That is the intended construction **on the
open coast**. It is a disaster wherever that isobath reaches *inside* the model.

Barnegat Inlet is scoured to **−14.8 m**. Measured on the frozen v2 mesh (2026-07-30):

- **153 inactive cells formed 18 islands INSIDE the model** — 145 in the inlet throat,
  3 in the Navesink, 1 at Manasquan.
- `create_boundary` rimmed them: **155 `mask==2` + 28 `mask==3` cells touched an island**,
  and **193 `mask==2` cells ran up to 2.6 km inside the mouth**.
- The **Barnegat Light gauge sits 75 m** from an imposed-level cell; the SSS sensor 168 m.

**The measurement that settles it** (`wave-cora+bed-ehydro`, pre-storm range):

| | range |
|---|---|
| inlet-throat `mask==2` cells | **1.465 m** |
| open-coast BC off Sandy Hook | 1.461 m |
| bay cells 3 km west | 0.521 m |
| **observed, Barnegat Light** | **0.707 m** |

The full ocean tide was clamped inside the inlet. `z` and `mask` were byte-identical
across `faber-waves-premier`, `wave-cora` and `wave-cora+bed-ehydro`, so **this was in
every v2 run**. eHydro did not cause it (that carve is subgrid-only, `z` untouched) but
would deepen it in any future mesh rebuild — which is how the user found it.

## ⚠️ WHAT THIS RETROSPECTIVELY EXPLAINS — do not keep quoting these as physics

The two headline bay defects are very likely ARTEFACTS of this clamp:
- **"The bay tide arrives EARLY (−43 / −58 min)"** — −43 min is *zero lag*. It was the
  ocean's own phase, not a propagation result. The sign-flip-vs-the-coast story was
  built on it. See [[project_domain_expansion_v2]].
- **"Barnegat Light is 1.9× over-amplified"** (1.368 m wet-channel vs 0.707 observed) —
  the clamp bleeding out; 1.368 sits between the imposed 1.465 and the bay's 0.521.
- ⚠️ **`bed-ehydro`'s `barnegat_bay` bias +0.005** may have been propped up by it. That
  is the pre-registered falsifier for the repair. See [[feedback_ehydro_prediction_miss]].

## The fix (2026-07-30) — three parts, all in the repo

1. **`model._fill_inactive_holes`** — topological, no geometry: any inactive component
   not connected to the main inactive mass becomes active, **before** `create_boundary`.
   Keeps working when the domain moves south, when a carve deepens a channel, or when
   `mask_zmin` changes. Cannot fix an intrusion that stays CONNECTED to the sea.
2. **`always_active_boxes_ll` entry `(-74.1163, 39.7538, -74.0860, 39.7850)`** — the
   connected part (the gorge). ⭐ **The east edge is the whole design**: extend it to
   touch ocean-connected deep water and the box's own seaward rim just becomes the new
   `mask==2` line. Tuned to the last longitude containing ZERO ocean-connected inactive
   cells, **after reprojecting the lon/lat box exactly as the code does** — UTM
   convergence here is ~0.6°, worth ~35 m, which is 1–3 cells at 12.5 m.
3. **`domain.NoWaterLevelBox` + two new build-time invariants** — no interior inactive
   islands, and no `mask==2` inside a declared zone. ⚠️ Its east edge is a DIFFERENT
   number (575,600–**578,150**): the −10 m isobath must become the boundary *somewhere*,
   and off Barnegat that alongshore line runs ragged between x 578,222 and 578,465 — at
   578,400 the invariant condemned 11 perfectly ordinary open-coast cells.

Result: islands **153 → 0**, in-throat BC cells **114 → 0**, active **+334**,
water-level BC **3,064 → 2,911**. `z` and the subgrid untouched, so the eHydro carve
carries through intact.

## 🔑 Cost, and the thing to remember operationally

**The mask is half the domain fingerprint**, so this is a NEW DOMAIN:
`9ccbab0bc7a9fc0d` → **`3b1356b9590c59ff`** (faces and boundary edges unchanged at
1,143,357 / 2,164 — the sha is what moved). The old value is registered as
`premier.V2_BARNEGAT_PREMASK` so old dirs audit as "PRE-REPAIR" rather than
"UNRECOGNISED". **Every arm in the 2026-07-26..29 campaign is on it and is no longer
comparable** — which is why the repair ships with its own control.

⭐ **Re-deriving a mask is CHEAP and needs no subgrid rebuild**: the tables cover all
1,143,357 faces and 2,307,638 uv points, so a newly-activated cell already has its
table. `model.apply_mask_and_boundary` runs on a copy of a built template in minutes
(`scripts/setup_inlet_mask_template.py`).

⚠️ **`build_static` short-circuits on `frozen_mesh`** — it copies and returns early, so
the domain.py/model.py repairs do NOT reach a fresh build from the frozen mesh. They
only take effect through the template-rebuild path.

This is the **third instance of one defect class**: Navesink (free outflow on a tidal
river), Manahawkin (waterlevel across an interior bay), Barnegat Inlet (waterlevel
inside the throat). All three ran clean and produced numbers nobody could tell were
wrong. Related: [[project_shrewsbury_reinvestigation]], [[project_domain_expansion_v2]],
[[reference_premier_domain_guard]], [[project_handoff_2026_07_30]].
