<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


# I was confidently wrong about the eHydro carve — the user was right

**2026-07-29.** I wrote a long, well-evidenced verdict that the v2 lagoon needed **no**
eHydro carve, and pre-registered `wave-cora+bed-ehydro` as an expected null with the reason
"quantified in advance." The user said run it anyway. It came back the **best arm on HWM
bias, RMSE and CSI simultaneously**, and fixed the barnegat_bay basin bias −0.215 → +0.005.
The lever I recommended in its place (`bed-baymanning`, lagoon friction) was the **worst arm
in the campaign** (CSI 0.672 → 0.613). Full numbers in [[reference_ehydro_district_sign]].

**Why:** the individual facts were right and the inference was wrong. I measured `z_zmin`
(a cell's deepest point) — 0.87% of cells, median Δ −0.003 m — and read "the bed barely
changed." The quantity that actually drives the flow is **storage**: `z_volmax` moved by a
median **+5.45** over ~1% of cells. A carve doesn't just lower bed, it restores sub-cell
channel/bank RELIEF the coarse stack averaged away. One edit, two diagnostics, opposite
verdicts — and I picked the one that agreed with the argument I had already committed to,
then presented the agreement as independent confirmation ("this table says *why* in
advance").

**How to apply:**
1. **Choose the diagnostic before you know which side it lands on.** The tell here was that
   I reached for `z_zmin` only *after* writing the no-carve verdict. When a metric is
   selected post-hoc, say so and check at least one metric that could falsify.
2. **For any bed/elevation edit, diff `z_volmax` and `z_zmax`, never `z_zmin` alone.**
   Subgrid models respond to storage and relief, not to the minimum.
3. **Quantifying a prediction is not evidence for it.** "Null, and here is the table saying
   why" felt rigorous and was just a confident restatement of the same wrong assumption.
4. **When the user overrules an argument of mine and asks to settle it empirically, that is
   usually the right call** — it costs one 3 h run and the reasoning above is exactly the
   kind that survives scrutiny while being wrong. Run it without relitigating.

Related: [[reference_ehydro_district_sign]], [[project_domain_expansion_v2]],
[[feedback_scoring_criterion]], [[project_handoff_2026_07_30]].
