#!/usr/bin/env python
"""Render the notebook animations out to real GIF files.

WHY THIS EXISTS
---------------
``animate.animate_field`` returns a matplotlib ``FuncAnimation`` that the notebooks show
inline via ``HTML(anim.to_jshtml())`` — every frame base64-embedded in the notebook's
output JSON. That is why those notebooks are 38-42 MB on disk, and it means the animations
existed ONLY inside notebook outputs: five of them, and exactly one GIF file had ever been
written in the project's history.

With ``nbstripout`` active (as ``.gitattributes`` has always intended), outputs are removed
on commit — so the committed/GitHub/nbviewer copy of a notebook carries no animation at
all. Rendering them to files here keeps them shareable at a few MB instead of paying
~40 MB per notebook commit forever.

Writes ``reports/<domain>/animations/<run>_<var>_<window>.gif``.

Run (one domain at a time — the run dirs are domain-scoped)::

    NJ_DOMAIN=v1_monmouth PYTHONPATH=$PWD python scripts/export_animations.py
    NJ_DOMAIN=v2_barnegat PYTHONPATH=$PWD python scripts/export_animations.py

``--list`` shows what would be written without reading a run. GIF writing goes through
pillow (the env has no ffmpeg), which is why these are GIFs and not mp4.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import nj_sfincs  # noqa: F401  (PROJ primer — must precede hydromt_sfincs)
from nj_sfincs import animate, domain
from nj_sfincs.config import ROOT, exp_root

#: The animations the viz notebooks build, per domain: (run, var, window).
#: Keep in step with the notebooks — these are transcribed from the `animate_field`
#: calls in notebooks/sfincs-nj-barnegat-viz-cora.ipynb and
#: notebooks/v1_monmouth/sfincs-nj-sandy-viz-premier.ipynb.
WANTED: dict[str, tuple[tuple[str, str, str], ...]] = {
    "v1_monmouth": (
        ("faber-waves-premier", "depth", "shrewsbury"),
        ("faber-waves-premier", "hm0", "sandy_hook"),
        ("faber-waves-premier", "depth", "shark"),
    ),
    "v2_barnegat": (
        ("wave-cora+bed-ehydro+mask-inlet", "depth", "barnegat_inlet"),
        ("wave-cora+bed-ehydro+mask-inlet", "depth", "mantoloking"),
    ),
}


def out_path(dom: str, run: str, var: str, window: str) -> Path:
    return ROOT / "reports" / dom / "animations" / f"{run}_{var}_{window}.gif"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true",
                    help="show what would be written; read-only, touches no run")
    ap.add_argument("--fps", type=int, default=6)
    ap.add_argument("--force", action="store_true",
                    help="re-render even if the GIF already exists")
    args = ap.parse_args()

    dom = domain.active().name
    jobs = WANTED.get(dom, ())
    if not jobs:
        print(f"no animations registered for domain {dom!r}; known: {sorted(WANTED)}")
        return 0

    for run, var, window in jobs:
        dst = out_path(dom, run, var, window)
        run_dir = exp_root() / run
        status = "exists" if dst.exists() else "would write"
        if args.list:
            missing = "" if run_dir.exists() else "   ** RUN DIR MISSING **"
            print(f"  [{status}] {dst.relative_to(ROOT)}{missing}")
            continue
        if dst.exists() and not args.force:
            print(f"  [skip] {dst.relative_to(ROOT)} (pass --force to re-render)")
            continue
        if not run_dir.exists():
            print(f"  [SKIP] {run}: run dir missing ({run_dir})", file=sys.stderr)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        print(f"  [render] {run} {var}/{window} -> {dst.relative_to(ROOT)} ...",
              flush=True)
        anim = animate.animate_field(run, var, window=window, fps=args.fps)
        # pillow, not ffmpeg — the env has none. See animate_field's docstring.
        anim.save(str(dst), writer="pillow", fps=args.fps)
        mb = dst.stat().st_size / (1 << 20)
        print(f"           {mb:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
