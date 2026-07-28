"""Re-fetch the USGS STN metadata that data/validation/sandy_hwms.geojson drops.

`download_sandy_hwms.py` keeps only (hwm_id, elev_m, quality, environment,
description). The fields that actually constrain the HWM SEARCH RADIUS are
discarded:

  hcollect_method_id  horizontal survey method -> positional accuracy
                      1 Handheld GPS | 2 Static-GNSS | 3 Phone/Car GPS
                      4 Map (digital or paper) | 5 Other
  height_above_gnd    metres above ground -> is the mark on a structure?
  hwm_type_id         mud/seed/debris/wash line -> which are runup-contaminated
  stillwater          flagged as stillwater (no wave setup/runup) or not
  vcollect_method_id  vertical method, pairs with `quality`
  site_id / waterbody which hydraulic feature the mark belongs to

`quality` (the one field that IS kept) is the VERTICAL accuracy only -- +/-0.05 ft
for q=1. It says nothing about where the mark is, which is the axis the
max-over-window estimator is sensitive to.

Writes reports/hwm_metadata.csv.
"""
import os
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

ROOT = Path(os.environ.get("NJ_ROOT", Path(__file__).resolve().parents[1]))
BASE = "https://stn.wim.usgs.gov/STNServices/"
EVENT_ID = 24  # 2012 Sandy
OUT = ROOT / "reports" / "hwm_metadata.csv"


def lookup(endpoint, key, val):
    r = requests.get(BASE + endpoint, timeout=60)
    r.raise_for_status()
    return {x[key]: x[val] for x in r.json()}


def main():
    hwm = gpd.read_file(ROOT / "data" / "validation" / "sandy_hwms.geojson")
    want = set(hwm["hwm_id"].astype(int))
    print(f"local mark file: {len(want)} marks")

    r = requests.get(f"{BASE}Events/{EVENT_ID}/HWMs.json", timeout=120)
    r.raise_for_status()
    api = {x["hwm_id"]: x for x in r.json()}
    print(f"STN event {EVENT_ID}: {len(api)} marks; matched {len(want & set(api))}")

    hmeth = lookup("HorizontalMethods.json", "hcollect_method_id", "hcollect_method")
    vmeth = lookup("VerticalMethods.json", "vcollect_method_id", "vcollect_method")
    htype = lookup("HWMTypes.json", "hwm_type_id", "hwm_type")
    hqual = lookup("HWMQualities.json", "hwm_quality_id", "hwm_quality")
    hdat = lookup("HorizontalDatums.json", "datum_id", "datum_name")

    rows = []
    for i in sorted(want):
        x = api.get(i)
        if x is None:
            rows.append(dict(hwm_id=i, missing_from_api=True))
            continue
        rows.append(dict(
            hwm_id=i,
            elev_m=round(x["elev_ft"] * 0.3048, 3),
            quality=x.get("hwm_quality_id"),
            quality_txt=hqual.get(x.get("hwm_quality_id")),
            hwm_type=htype.get(x.get("hwm_type_id")),
            hcollect=hmeth.get(x.get("hcollect_method_id")),
            hcollect_id=x.get("hcollect_method_id"),
            hdatum=hdat.get(x.get("hdatum_id")),
            vcollect=vmeth.get(x.get("vcollect_method_id")),
            height_above_gnd=x.get("height_above_gnd"),
            stillwater=x.get("stillwater"),
            environment=x.get("hwm_environment"),
            waterbody=x.get("waterbody"),
            site_id=x.get("site_id"),
            lon=x.get("longitude_dd"), lat=x.get("latitude_dd"),
            description=x.get("hwm_locationdescription"),
        ))

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT}  ({len(df)} rows)")

    pd.set_option("display.width", 220)
    print("\n--- horizontal collection method (the positional-accuracy axis) ---")
    print(df["hcollect"].value_counts(dropna=False).to_string())
    print("\n--- q<=2 only ---")
    print(df[df.quality <= 2]["hcollect"].value_counts(dropna=False).to_string())
    print("\n--- hwm_type ---")
    print(df["hwm_type"].value_counts(dropna=False).to_string())
    print("\n--- height above ground (m) ---")
    print(df["height_above_gnd"].describe().to_string())
    print("\n--- stillwater flag ---")
    print(df["stillwater"].value_counts(dropna=False).to_string())
    print("\n--- environment ---")
    print(df["environment"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
