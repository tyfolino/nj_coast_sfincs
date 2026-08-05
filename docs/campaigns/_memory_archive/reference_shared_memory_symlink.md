<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


Claude Code keys auto-memory to the **working directory**, so opening a different
repo would normally start from a blank memory. Set up 2026-07-30 so it doesn't:

The live store is `/home/tpj8/.claude/nj-sfincs-memory/` (a neutral location — neither
repo owns it). Both project dirs are symlinks to it:

- `~/.claude/projects/-cache-home-tpj8-nj-sandy-sfincs/memory` → shared store
- `~/.claude/projects/-cache-home-tpj8-nj-coast-sfincs/memory` → shared store

Write-through was verified in both directions. ⇒ **It does not matter which of the two
repos VSCode is opened in — memory is identical and edits from either side land in the
same files.** Adding a third repo = one more `ln -s` to the same target.

## What does NOT travel

- **Conversation transcripts.** The `*.jsonl` session files stay per-project, so `/resume`
  in `nj_coast_sfincs` will not list sessions started in `nj_sandy_sfincs`.
- **Permissions.** `settings.local.json` is repo-local; `nj_coast_sfincs` has no `.claude/`
  at all, so tool-permission prompts start from scratch there.

## ⚠️ THE v1 REPO IS A PRE-DOMAIN-REGISTRY CODEBASE (measured 2026-08-04)

Going "back to v1" is **not** a checkout — it is working in a codebase that predates weeks
of development. `nj_sandy_sfincs/nj_sfincs/` has **no `domain.py`, no `provenance.py`, no
`wind.py`, no `gdaltools.py`**; its artifacts date 2026-07-14→21
(`experiments/faber-waves-premier`, `experiments/_template_sealed`,
`data/frozen_mesh_sealed` — note the OLD name, not `frozen_mesh_v1_monmouth`). So it has no
domain registry, no bracket machinery, no interior-gauge scoring.

⇒ **Prefer v2 for anything northern.** `v2_barnegat` geographically CONTAINS `v1_monmouth`
(39.70–40.52 vs 40.15–40.52, same lon span), with two more interior gauges and ~19 more
scored HWM marks. The only thing v1 buys is ~half the solve time, which is irrelevant for
an overnight run.

⚠️ And when searching for "does X exist", **search both repos** — a subagent scoped to one
directory will faithfully report "not found" for something sitting next door. See
[[feedback_read_memory_files]].

## ⚠️ The stale git-tracked mirror

`nj_sandy_sfincs/.claude/memory/` is a **git-tracked mirror**, synced by
`scripts/sync_claude_memory.sh backup|restore` (see that dir's `README.md`). It was last
synced **2026-06-25** and is badly out of date — it predates the domain rebuild, the
estimator artifact, and the whole v2 campaign. Do not read it as current; treat the
shared store as the only source of truth. The script targets the munged path, which is now
a symlink, so `backup` still resolves correctly — but note it would write the mirror into
the **v1** repo even for work done in v2.

Related: [[reference_naming_convention]], [[project_handoff_2026_07_30]]
