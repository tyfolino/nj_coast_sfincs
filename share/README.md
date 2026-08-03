# Sandy (2012) maximum flood depth — practice raster

`sandy_hmax_v1_monmouth_faber-waves-premier_EPSG32618.tif`

Modelled maximum water depth during Hurricane Sandy, Monmouth County / Raritan Bay,
New Jersey. SFINCS hindcast. **This is a practice dataset, not a validated hazard
layer** — see the caveats at the bottom before drawing any conclusion from it.

## Reading the file

| | |
|---|---|
| Format | GeoTIFF, single band, float32, DEFLATE-compressed, tiled, with overviews |
| **CRS** | **EPSG:32618 (EPSG:32618)** — UTM zone 18N, coordinates in **metres**, *not* degrees |
| Resolution | 6.249 m |
| Size | 11300 x 6596 px, 11.1 MB |
| NoData | NaN (tagged in the header) — dry land and areas outside the model |
| Units | metres of water depth above the ground surface |

The CRS is the one thing most likely to trip you up. Opening this expecting
lat/lon gives corner coordinates like `561434, 4444626`; that is not corruption,
it is UTM in metres. QGIS/ArcGIS/rasterio all reproject on the fly. If you need
degrees (EPSG:4326) say so and I will ship a reprojected copy — better that than
resampling it yourself twice.

Extent: `(561433.7, 4444626.3, 632052.8, 4485847.9)` in UTM, which is `(-74.2787, 40.1416, -73.4413, 40.5211)` as (west, south, east, north) in degrees.

```python
import rioxarray
da = rioxarray.open_rasterio("sandy_hmax_v1_monmouth_faber-waves-premier_EPSG32618.tif", masked=True).squeeze()
da = da.where(da >= 0.15)          # see "wet threshold" below
da.rio.reproject("EPSG:4326")      # only if you actually need degrees
```

## What the values mean

- **Depth above ground**, not water-surface elevation. No datum conversion needed
  to use it as depth; it is already ground-relative.
- **Maximum over the whole simulation**, not a snapshot. Different cells peak at
  different times, so the map is not a state the system was ever in at one instant.
  That is normally what a damage model wants, but it is worth knowing.
- **Permanent water is masked out.** Bay, river and ocean cells are NaN, so the
  raster shows flooding on land rather than the full water column. Without this the
  file would report ~10 m "depths" over the Navesink and you would compute damages
  to the seabed.

Depth range in the file: 0.05 to 10.27 m. 1,700,625 wet cells
(2.28% of the grid). Median depth over the 0.15 m threshold is
1.30 m, 99th percentile 3.73 m.

### Wet threshold

The raster floor is **0.05 m** (an artifact of how the downscale is built). Our own
scoring treats a cell as wet only at **>= 0.15 m**, which is 1,583,681 cells.
Below that you are looking at numerical damp rather than flooding, and most damage
curves will happily assign losses to it. **Threshold at 0.15 m** unless you have a
specific reason not to. I left the 0.05 m values in the file rather than silently
deleting data, so the choice stays yours.

## Caveats — please read before trusting a number

1. **Known low bias.** Against surveyed high-water marks this model runs about
   **0.25 m low** on average (median estimator, 50 m search window). Damages
   computed from it will be *under*-estimates, and non-linearly so, because damage
   curves are steep near the low end.
2. **Hindcast, not a design event.** This is one storm reconstructed after the fact.
   It is not a return-period product and must not be read as one.
3. **Model still in development.** The domain, bathymetry and boundary conditions
   are actively being revised; this file is a snapshot from a frozen configuration
   kept for reference, not the current best model.
4. **Depth only.** No velocity, no duration, no wave action, no debris — all of
   which matter for real damage estimation.

Questions to Ty.
