# Eryri tools

Scripts that build the place data for the **Eryri** tab and then build the website. Orienteering doesn't need them: its courses are on generated hills.

## What's here

| File | Job |
|---|---|
| `levels.py` | The list of Eryri places: id, Welsh name and centre (British National Grid). |
| `osm_local.py` | Cuts each place, plus a 12 km surround, out of the Geofabrik Wales OpenStreetMap extract into `osm_local/`. |
| `cog.py`, `fetch_fine.py`, `fetch_split.py`, `op.py` | Read Welsh Government LiDAR heights (fine 1.5 km square and coarse 12 km surround). |
| `process.py` | Turns heights and map data into the game's place data, `eryri.json`. |
| `build_site.py` | Builds `index.html`, `cy.html`, `sw.js`, the manifests and `eryri/<place>.json` at the top of the repo, plus single-file versions in `tools/out/`. |
| `src/page_en.html`, `src/page_cy.html` | The game pages (English and Welsh) without place data. Edit these, not the built pages. |

## Setting up

Python 3.10 or later, then:

```
pip install numpy scipy shapely rasterio osmium convertbng requests
```

Download the Wales extract into `tools/osm/`:
https://download.geofabrik.de/europe/united-kingdom/wales-latest.osm.pbf

## Adding a place

1. Add a line to `levels.py` with an id, name and centre (easting and northing ending in 50).
2. From inside `tools/`:
   ```
   python osm_local.py osm/wales-latest.osm.pbf
   python process.py
   ```
   `process.py` reads the LiDAR over the internet and takes a few minutes for all places.
3. Add the place to the `ERY` list in both `src/page_en.html` and `src/page_cy.html` (id and name).
4. From the top of the repo:
   ```
   python tools/build_site.py
   ```
5. Commit the changed `index.html`, `cy.html`, `sw.js` and the new file in `eryri/`.

`sw.js` gets a new version name on every build, which tells phones to refresh their offline copy.

The large downloaded and generated files (`osm/`, `osm_local/`, `eryri.json`, `out/`) are left out of the repo by `.gitignore`.
