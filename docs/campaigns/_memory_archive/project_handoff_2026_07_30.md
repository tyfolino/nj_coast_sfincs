<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


# Handoff — 2026-07-30

## 🚀 RUNNING: two arms on the repaired mask, submitted ~2026-07-30

Both 12 h / 128 G / 48c on Faber (`sfincs-desktop.sif`), prior v2 arms ran 3:24–4:00.

| SLURM | arm | its control |
|---|---|---|
| **59693619** | `wave-cora+bed-ehydro+mask-inlet` | `wave-cora+bed-ehydro` (direction only — different domain) |
| **59693621** | `wave-cora+bed-ehydro+mask-inlet+tide-shift` | **59693619** |

Why they are separate arms and not one: `tide-shift`'s only recorded cost was ~8 min of
added BAY phase error, scored against a bay whose phase **was the clamp**. Folding both
changes together would destroy exactly the measurement that says whether that cost is
real. See [[reference_inlet_waterlevel_clamp]].

**Pre-flight was clean on every axis:** `sfincs.inp` **0-key diff** A-vs-B *and*
A-vs-`wave-cora+bed-ehydro`; A's surge forcing byte-identical to that arm's
(`778a1f6383ea`) so **the only difference is the mask**; wave boundary identical A-vs-B;
**X1 hazard 0** on both; eHydro subgrid carried through (`z_volmax` == the ehydro
template, != the sealed one); `z` byte-identical to the old arm; Cape May trap held
(2 support points).

Score with `scripts/score_v2.py --estimator median`. **Check for truncation first** —
73 map / 433 his steps reaching tstop 2012-10-31; `sacct` says COMPLETED even when a
quota-truncated map is garbage.

## 📌 PRE-REGISTERED PREDICTIONS — read BEFORE the numbers

**`mask-inlet`:**
- Barnegat Light range **1.368 m (wet-channel) → down toward 0.707 observed**;
  phase **−43 min → toward 0 or LATE**.
- Mantoloking range 0.401 → down; −58 min → later.
- Along-bay gradient (obs +0.518 m, model −0.410 m) → **toward observed**: the clamp is
  what has been holding the southern end up.
- ⚠️ **THE FALSIFIER, chosen in advance:** `barnegat_bay` HWM bias is **+0.005** on
  `bed-ehydro` and some of that may be the clamp propping the bay up. **Expect it to go
  NEGATIVE and bay CSI to drop.** If it does, that is a real trade to weigh — an
  inadmissible BC that scores well is still inadmissible — **not** a reason to revert.

**`+tide-shift`:** coast should keep tide-shift's win (Sandy Hook ~0 min,
Shrewsbury/Shark ~15–19 min). **The bay is the open question**: if its phase error is
LATE after the repair, this arm improves it; if still EARLY, it worsens it ~8 min again.
Either answer is informative and is the reason to run it.

## ✅ Scored 2026-07-29 — ⚠️ ALL ON THE PRE-REPAIR DOMAIN (`9ccbab0bc7a9fc0d`)

| arm | HWM bias | RMSE | CSI |
|---|---|---|---|
| `faber-waves-premier` | −0.250 | 0.494 | 0.688 |
| `wave-cora` | −0.293 | 0.507 | 0.672 |
| `tide-shift` | −0.266 | 0.501 | 0.683 |
| `wave-cora+bed-baymanning` | −0.335 | 0.543 | 0.613 |
| `wave-cora+bed-ehydro` | **−0.244** | **0.493** | **0.701** |

Persisted in `reports/v2_native95.csv` + `reports/v2_bridge31.csv`. **Read them as the
pre-repair baseline, not as the current model.** `tide-shift` gave Sandy Hook
17.8 → 0.2 min, Shrewsbury 35.1 → 15.2, Shark 35.2 → 19.1.

## 🗑️ Disk — cleared with the user's authorisation 2026-07-30

Deleted `experiments/{wave-cora+bed-baymanning, tide-shift, _template_baymanning}`
(6.7 G; repo 28 G → 21 G, home ~92 G of ~110 G). All five arms' metrics were already in
`reports/*.csv` first. Still present: `faber-waves-premier`, `wave-cora`,
`wave-cora+bed-ehydro`, `_template_sealed`, `_template_ehydro_south`, and the new
`_template_ehydro_inletmask`.

## 🧾 NOTHING IS COMMITTED — the user commits, Claude may `git add`

New/changed in `~/nj_coast_sfincs` on 2026-07-30 (all staged with `git add -A`… ⚠️ which
**failed: `git` is not on PATH on the compute node** — stage from a login node):
- `nj_sfincs/domain.py` — `NoWaterLevelBox`, `_BARNEGAT_INLET_GORGE_LL`,
  `_NO_WL_BARNEGAT_INLET`, both wired into `V2_BARNEGAT`
- `nj_sfincs/model.py` — `_inactive_components`, `_fill_inactive_holes`, invariants 3+4
- `nj_sfincs/premier.py` — v2 fingerprint → `3b1356b9590c59ff`, `V2_BARNEGAT_PREMASK`
- `nj_sfincs/config.py` — the two new arms
- `scripts/setup_inlet_mask_template.py` (new)

Plus the 2026-07-28 work listed in the previous handoff (plots/config/model/catalog +
the baymanning/ehydro build scripts and their data artifacts).

## ⭐ PENDING DECISION — promote the premier once 59693619 lands

The user proposed making **`wave-cora+bed-ehydro` the premier** and I asked to wait ~4 h. The
reasoning to re-use, not re-derive:
- It is the right **configuration** (CORA wave boundary + the southern eHydro carve).
- But the copy on disk was run with the ocean level clamped inside Barnegat Inlet, so promoting
  it enshrines an inadmissible BC as the reference.
- **59693619 is that same configuration on the repaired domain** ⇒ promoting after it lands is
  a one-line `PREMIER_NAME` change done once instead of twice.
- ⚠️ If the pre-registered falsifier fires (`barnegat_bay` bias goes negative), that is a
  conversation about the level/extent trade — **not** a reason to keep the old mask.

## 🔓 Still open (unchanged)
1. **Fold the interior gauges into `validate.evaluate()`** — Barnegat Light and
   Mantoloking are still figure-path only. Now MORE valuable: the repair's whole story
   is bay phase + range. ⚠️ Barnegat Light's his point is a **dry bank** (`point_zb`
   +0.988) so it needs the `_wet_channel_cells` treatment, and peak searches must be
   floored at 2012-10-29 or argmax picks the spin-up transient.
2. The Rt 37 causeway sill (~39.95) still needs a trustworthy bay mask.
3. `scripts/audit_paved_channels.py` cannot run on v2 (v1-hardcoded `MODEL`, wants
   `cudem_nj_clip.tif`, carries the eHydro sign bug).
4. The notebook `sfincs-nj-barnegat-viz-cora.ipynb` has 6 cleared cells; its figures now
   also predate the mask repair.

Related: [[reference_inlet_waterlevel_clamp]], [[project_domain_expansion_v2]],
[[project_tidal_phase_lag]], [[feedback_ehydro_prediction_miss]],
[[reference_disk_quota_dedupe]].
