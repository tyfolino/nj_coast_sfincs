<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `reference_infragravity_closed`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** ⛔ IG is a NULL lever on this domain, NOT an instability — that verdict is SUPERSEDED. On the sealed domain `wave-ig` (premier + snapwave_igwaves 0->1) moved every metric by <=0.01 m and ran stably even while forced hard (hm0ig 3.023 m warning). The 'IG explodes' memory came from a PRE-sealed run whose blow-up traced to a Faber IG source-term bug. Run dir deleted 2026-07-28; record lives in reports/shrewsbury_investigation.md Workstream E + reports/wave-ig_archived.csv.


# Infragravity waves — CLOSED as a null, not as an instability

## ⚠️ THE COMMON RECOLLECTION IS THE SUPERSEDED ONE

"We found that IG waves introduced instabilities" is the **old** verdict. It was earned on a
pre-sealed-domain run that exploded to billions of metres, and **Workstream F traced that
blow-up to an IG source-term bug in Faber — the engine the premier already runs.** That
removed the excuse for dismissing IG, so it was given a fair test on the sealed domain.

## ✅ THE FAIR TEST: `wave-ig` = premier + EXACTLY ONE FLAG (`snapwave_igwaves 0 → 1`)

Mesh, subgrid, forcing, support points and tuned physics byte-identical (inputs hard-linked
from `_template_sealed`), so any difference is IG and only IG.

| | premier | IG on | Δ |
|---|---|---|---|
| Shrewsbury gauge (obs 2.94) | 2.837 | 2.827 | −0.010 |
| HWM bias | 0.318 | 0.317 | −0.001 |
| HWM RMSE | 0.480 | 0.480 | ~0 |
| MOTF CSI | 0.706 | 0.704 | −0.002 |
| Shark frac-rising | 0.458 | 0.458 | 0 |

**Every number inside the noise, and it ran STABLY.** It even logged
`computed hm0ig at boundary exceeds 3 meter: 3.023` at ~60% of the run — i.e. IG was forced
*hard*, arguably too hard, and still did nothing to water levels. **That strengthens the
null; it is not evidence of instability.**

⇒ Do not re-open IG expecting either a fix or a crash. It is a null lever here. The
back-bay-filling-by-IG-overtopping hypothesis is dead, and after the leak fix it was never
load-bearing anyway — the estuary fills because the hole is plugged.

## 🔻 AND THE ONE "INTERESTING THREAD" IT LEFT OPEN IS ALSO DEAD

`reports/shrewsbury_investigation.md` flags that IG **halves peak Sandy Hook Bay wave height
(hm0 max 7.44 → 3.98 m)** while leaving every water level alone, and calls that "the more
interesting thread of the two." **It isn't** — that was written before the 2026-07-26/27
finding in [[project_snapwave_decoupling]]: **`shb_hm0_max` is a WETTING TRANSIENT.**
`tide-shift`, a pure tide-TIMING change that cannot touch wave physics, drops the same max to
**4.01 m with a flat mean (0.884 → 0.890)**. So a halved hm0 *max* is what any arm that
changes when cells wet produces, and it cannot rank arms. **Quote the hm0 MEAN.**

✅ **CONFIRMED on the scrape, not inferred: `wave-ig` has `shb_hm0_max` 3.977 with
`shb_hm0_mean` 0.8928 — against the premier's 7.44 / 0.884.** The max halves while the mean
moves **+0.009 m**, the exact signature `tide-shift` shows. **The "interesting thread" is a
wetting transient and is now closed too.** (The scrape also reproduces the report exactly:
bias 0.3170, RMSE 0.4797, CSI 0.7042 — so `reports/wave-ig_archived.csv` is a faithful
substitute for the deleted dir.)

## 🗑️ Run dir deleted 2026-07-28 (user's call). Where the evidence lives now
- **`reports/shrewsbury_investigation.md`, Workstream E** — the full narrative, the table
  above, both caveats, and the "closed" verdict. Richer than any CSV.
- **`reports/wave-ig_archived.csv`** — metrics scraped before deletion (it had no CSV row,
  which is why it survived the first cleanup pass).
- ⚠️ Named **`sealed_igwaves_wind`** in that report; `wave-ig` is the post-rename name. See
  [[reference_naming_convention]] — a name search must try both.

Related: [[project_snapwave_root_cause]] (the X1/X2 crashes that were NOT IG),
[[project_shrewsbury_reinvestigation]], [[reference_disk_quota_dedupe]] (the deletion guard).
