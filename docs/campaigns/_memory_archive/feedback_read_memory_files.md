<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


# Read the memory files. Search both repos.

Two corrections from the user in one session on 2026-08-04, both from the same root cause:
**I treated a one-line index entry as if it were the content.**

1. **"You seriously don't remember the plan from yesterday?"** I told them no plan document
   existed, having had a subagent search the repo and find only the stale
   `hpc/claude_memory/*.md` import. The actual plan was
   [[project_handoff_2026_08_03]] — in the live memory store, listed in the MEMORY.md index
   that was already in my context. I had the pointer and never opened it. The whole bracket
   campaign ("testing the water level boundary on the southern end / back bay vs. wind") was
   in there, scored, with a fired pre-registered rule.

2. **"Our v1 stuff lives in nj_sandy_sfincs, not this directory."** I reported "there is no
   v1 artifact of any kind" and let a domain decision be made on it. v1 lives in the *other*
   repo — `experiments/faber-waves-premier`, `experiments/_template_sealed`,
   `data/frozen_mesh_sealed`. [[reference_shared_memory_symlink]] already says the two repos
   share memory; that should have prompted searching both.

**Why:** the MEMORY.md index is a routing table, not a summary. Its entries are deliberately
compressed and lossy — an entry like "📌 START HERE — HANDOFF" is an instruction to open the
file, not a description of its contents. Acting on the index alone produces confident,
specific, wrong claims, which is worse than saying "let me check."

**How to apply:**
- At the start of any session that continues prior work, **Read the files the index flags as
  live threads** (🔴 / ⭐ / "START HERE") before making any claim about project state.
- Before asserting something does not exist, check **both** `nj_coast_sfincs` and
  `nj_sandy_sfincs`, and the memory store — not just the repo that happens to be open.
- When briefing a subagent to search for something, tell it about the second repo and the
  memory store explicitly. A subagent scoped to one directory will faithfully report
  "not found" for something that exists next door.

Related: [[feedback_ehydro_prediction_miss]], [[reference_naming_convention]]
