"""Read a static OpenStreetMap extract (e.g. Geofabrik wales-latest.osm.pbf) and return
Overpass-style JSON for one level, so process.py never needs the Overpass servers.
Needs: pip install osmium"""
import osmium, json, os
from convertbng.util import convert_lonlat

def keep(t):
    g = t.get
    return (g('natural') in ('water', 'wood', 'cliff', 'scree', 'bare_rock', 'shingle', 'peak')
            or g('landuse') in ('reservoir', 'forest')
            or g('waterway') in ('stream', 'river', 'canal', 'drain', 'ditch')
            or 'highway' in t or 'railway' in t or g('barrier') == 'wall' or 'building' in t
            or g('man_made') == 'survey_point' or 'place' in t)

def bbox_ll(Ec, Nc, h):
    lo, la = convert_lonlat([Ec-h, Ec+h, Ec-h, Ec+h], [Nc-h, Nc-h, Nc+h, Nc+h])
    return min(lo), min(la), max(lo), max(la)

def extract(pbf, boxes):
    """boxes: {level_id: (minlon,minlat,maxlon,maxlat)} -> {level_id: {'elements':[...]}}"""
    G = (min(b[0] for b in boxes.values()), min(b[1] for b in boxes.values()),
         max(b[2] for b in boxes.values()), max(b[3] for b in boxes.values()))
    def inside(lon, lat):
        if not (G[0] <= lon <= G[2] and G[1] <= lat <= G[3]): return []
        return [k for k, (a, b, c, d) in boxes.items() if a <= lon <= c and b <= lat <= d]
    # pass 1: relations we care about and their member way ids
    rels, want_ways = {}, set()
    for o in osmium.FileProcessor(pbf, osmium.osm.RELATION):
        t = dict(o.tags)
        if t.get('type') == 'multipolygon' and keep(t):
            mem = [(m.type, m.ref, m.role) for m in o.members]
            rels[o.id] = (t, mem); want_ways.update(r for ty, r, _ in mem if ty == 'w')
    # pass 2: ways with node locations
    out = {k: [] for k in boxes}; wgeom = {}
    fp = osmium.FileProcessor(pbf, osmium.osm.NODE | osmium.osm.WAY).with_locations()
    for o in fp:
        if o.is_node():
            t = dict(o.tags)
            if t and keep(t) and o.location.valid():
                for k in inside(o.location.lon, o.location.lat):
                    out[k].append({'type': 'node', 'id': o.id, 'lat': o.location.lat, 'lon': o.location.lon, 'tags': t})
            continue
        t = dict(o.tags); member = o.id in want_ways
        if not (member or (t and keep(t))): continue
        try: geom = [{'lat': n.location.lat, 'lon': n.location.lon} for n in o.nodes]
        except Exception: continue
        if member: wgeom[o.id] = geom
        if t and keep(t):
            lo=[p['lon'] for p in geom]; la=[p['lat'] for p in geom]
            if max(lo) < G[0] or min(lo) > G[2] or max(la) < G[1] or min(la) > G[3]: continue
            hit = set(k for p in geom for k in inside(p['lon'], p['lat']))
            for k in hit: out[k].append({'type': 'way', 'id': o.id, 'tags': t, 'geometry': geom})
    for rid, (t, mem) in rels.items():
        members = [{'type': 'way', 'ref': r, 'role': role, 'geometry': wgeom[r]} for ty, r, role in mem if ty == 'w' and r in wgeom]
        hit = set(k for m in members for p in m['geometry'] for k in inside(p['lon'], p['lat']))
        for k in hit: out[k].append({'type': 'relation', 'id': rid, 'tags': t, 'members': members})
    return {k: {'elements': v} for k, v in out.items()}

if __name__ == '__main__':
    import sys
    from levels import LEVELS
    pbf = sys.argv[1]; os.makedirs('osm_local', exist_ok=True)
    boxes = {L['id']: bbox_ll(L['Ec'], L['Nc'], 900) for L in LEVELS}
    boxes.update({L['id'] + '_wide': bbox_ll(L['Ec'], L['Nc'], 6000) for L in LEVELS})
    res = extract(pbf, boxes)
    for k, j in res.items():
        if k.endswith('_wide'):  # only water + forest for the 12 km surround
            j['elements'] = [e for e in j['elements'] if (e['type'] != 'node' and (e['tags'].get('natural') in ('water', 'wood') or e['tags'].get('landuse') in ('forest', 'reservoir')))
                             or (e['type'] == 'node' and e['tags'].get('natural') == 'peak' and e['tags'].get('name'))]   # named peaks label the view
        json.dump(j, open(f'osm_local/{k}.json', 'w')); print(k, len(j['elements']))
