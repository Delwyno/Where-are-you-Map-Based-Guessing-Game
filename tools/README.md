# Eryri data tools for "Where are you?"

These scripts build the real-terrain levels embedded in `index.html`.

## What you need
- Python 3 with: `pip install rasterio shapely pyproj convertbng scipy numpy osmium requests`
- Heights: read straight from the Welsh Government LiDAR COG (no download needed):
  https://dmwproductionblob.blob.core.windows.net/cogs/lidar/wales_dtm_16bit_cog.tif (OGL v3.0)
- Map data: a static OpenStreetMap extract, e.g. https://download.geofabrik.de/europe/united-kingdom/wales-latest.osm.pbf (ODbL)

## Steps
1. `python3 osm_local.py wales-latest.osm.pbf` - cuts per-level OSM data into `osm_local/` (no Overpass needed).
2. `python3 process.py` - reads LiDAR + OSM, writes `eryri.json` and `eryri.b64`.
3. `python3 inject.py index.html eryri.b64` - puts the new data into the game file.
4. Optional: `python3 browser_test.py <level> shot.png` (needs Playwright + three.min.js) to screenshot a level.

## Adding a level
- Add a centre to `LEVELS` in `levels.py` (easting/northing ending in 50, so the 1.5 km square lines up with the 100 m grid).
- Add a matching entry (spots, weather, difficulty) to the `ERY` list inside `index.html`, in the same position.
- Progress is saved by place id (`way-eryri2` in the browser), so adding or reordering levels is safe. A place is playable once the one before it is solved.

## Files
- `cog.py` LiDAR reading (1 m DTM smoothed to a 7.5 m grid; coarse 12 km surround at 50 m)
- `osm_local.py` offline OSM extraction; `op.py`, `fetch_fine.py`, `fetch_split.py` old Overpass fallback
- `process.py` turns everything into level data, including lakes (flattened to their own level) and conifer/broadleaf woods on the 12 km surround; `levels.py` the twenty level centres, easiest to hardest
