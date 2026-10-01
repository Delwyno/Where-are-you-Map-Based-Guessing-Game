# Where are you? · Ble wyt ti?

A map-reading game. Study a 3D view of the hills, then work out where on the contour map you're standing. It includes real Eryri (Snowdonia) terrain, an orienteering mode and a full Welsh-language version.

https://github.com/user-attachments/assets/c6e6f1f3-2b33-4516-b605-4f21acb957e7

**Play:** https://delwyno.github.io/Where-are-you-Map-Based-Guessing-Game/
**Chwarae yn Gymraeg:** https://delwyno.github.io/Where-are-you-Map-Based-Guessing-Game/cy.html

It works on phones and computers, and plays offline once it has been opened once.

**Install it like an app:** on iPhone, open the link in Safari, tap Share, then **Add to Home Screen**. On Android, use Chrome's menu, then **Install app**. It opens full screen with its own icon and name.

## Ways to play

| Tab | What it is |
|---|---|
| **Levels** | Made-up hills that get harder each level: more spots, look-alike views, fog and timers. |
| **Eryri** | 33 real places in Eryri, picked at random. Choose lettered **Spots** or **Anywhere** (drop a pin, scored by distance), and a difficulty from Easy to Expert. |
| **Orienteering** | 20 courses on made-up hills. Visit the controls in order by tapping the ground in the 3D view to move (up to 150 m per jump). Your time comes from a hill-walking pace model, so route choice matters. You get stars against par, split times, and your route drawn on the map at the end. |
| **Daily** | Five rounds, the same for everyone each day, with a shareable result. |
| **Unlimited** | Made-up hills with your own settings. |

### Orienteering

- Controls sit on features you can find from the map: path junctions, summits, knolls, wall corners, stream junctions, stream crossings and path bends. Each control has a written clue.
- You punch a control by getting within 8 m of its orange-and-white kite. Passing that close during a jump also counts.
- You can't jump across water, through buildings, up ground steeper than about 50°, or further than 150 m.
- **My position:** show your position *by course* (shown on courses 1–5, hidden from 6), *always* or *never*. When it's hidden, "Where am I?" shows it for 5 seconds at a 30-second penalty.
- Weather gets harder through the ladder, from clear days to thick mist.

## Controls

| | Phone | Computer |
|---|---|---|
| Look around | Drag the 3D view (up/down tilts) | Drag, or arrow keys |
| Move (Orienteering) | Tap the ground | Click the ground |
| Zoom the map | Pinch, or **+ / −** | Ctrl/⌘ + scroll, trackpad pinch, **+ / −** |
| Pan the zoomed map | Drag | Drag |
| Compass: measure a bearing | Compass button, then tap two points | Same, or **C** |
| Choose a spot | Tap a letter | **A**–**F**, **Enter** to confirm |
| New round | Button under the title | **N** |

After a guess, the 3D view names the summits and lakes you can see. The **Names** button hides them. With the compass on, each name shows its bearing.

## What's in this repo

```
index.html                English version (built from tools/src/page_en.html)
cy.html                   Welsh version (built from tools/src/page_cy.html)
eryri/                    one data file per Eryri place (33), loaded when needed
sw.js                     service worker: saves everything for offline play
manifest.webmanifest      app details for "Add to Home Screen" (English)
manifest-cy.webmanifest   app details for "Add to Home Screen" (Cymraeg)
icon-192.png, icon-512.png
og-image.jpg              the picture shown when the link is shared (WhatsApp, Facebook, X, iMessage…)
tools/                    scripts that make the Eryri place data and build the site (see tools/README.md)
```

Everything runs in the browser, with no server code. [three.js](https://threejs.org/) r128 draws the 3D view and is loaded from cdnjs.

### Offline and updates

On the first visit the service worker saves the pages, three.js and all 33 Eryri places in the background (about 3.5 MB to download). After that the game works with no signal, which is handy on the hill.

When you upload new files, open the site once with signal and phones will pick up the new version.

### What you'll see

- **Terrain:** real LiDAR heights for Eryri. Rain-eroded made-up hills for the other modes. Lighting, shading and shadows from the sun on clear, hazy and evening rounds.
- **Ground:** bare rock on steep ground, and patches of bracken and heather.
- **Water and tracks:** streams in cut channels, worn gravel footpaths and tarmac roads.
- **Weather:** clear, evening, haze, overcast, low cloud and mist.

### Sharing the link

The pages carry link-preview tags, so a shared link shows `og-image.jpg` with a title and description. The Welsh page (`cy.html`) previews in Welsh. Apps keep previews they've already fetched for a while. To force a fresh one, add something to the end of the link, for example `?v=2`. To refresh Facebook and Messenger, use Meta's Sharing Debugger.

### Running it locally

Open the folder through a local web server rather than double-clicking `index.html`, because browsers block loading the `eryri/` files from `file://`:

```
python -m http.server 8000
```

Then go to http://localhost:8000/.

### Changing the game or adding places

Edit the pages in `tools/src/`, not the built `index.html` and `cy.html`. Then run `python tools/build_site.py` from the top of the repo. How to add an Eryri place is in [tools/README.md](tools/README.md).

## Place data

Each Eryri place is a 1.5 km square of detailed terrain inside a 12 km surround:

- **Heights:** Welsh Government LiDAR 1 m terrain model, resampled for the game.
- **Map detail:** OpenStreetMap, from the Geofabrik Wales extract. This covers lakes, streams, paths, roads, walls, woods, buildings, crags, cliffs, scree and named summits.
- **Names:** Welsh first, with English OpenStreetMap qualifiers turned into Welsh.

## Credits and licences

- Heights: Welsh Government LiDAR. Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
- Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), available under the Open Database Licence.
- 3D rendering: [three.js](https://github.com/mrdoob/three.js) (MIT licence).

---

## Yn Gymraeg

Gêm darllen map. Astudia’r olygfa 3D, yna gweithia allan ble ar y map cyfuchliniau rwyt ti’n sefyll. Mae’r gêm yn cynnwys bryniau dychmygol a thir go iawn Eryri. Mae pum ffordd o chwarae: **Lefelau**, **Eryri** (33 o lefydd go iawn), **Cyfeiriannu** (20 cwrs), **Dyddiol** a **Diderfyn**.

Mae’n gweithio ar ffôn a chyfrifiadur, a heb signal ar ôl ei hagor unwaith. I’w gosod fel ap, agor y ddolen yn Safari, tapio Rhannu ac yna **Ychwanegu at y Sgrin Gartref**. Chwarae: https://delwyno.github.io/Where-are-you-Map-Based-Guessing-Game/cy.html
