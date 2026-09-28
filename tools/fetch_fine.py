import sys, json
from op import q
from levels import LEVELS
from convertbng.util import convert_lonlat
def bbox(Ec,Nc,h):
    es=[Ec-h,Ec+h,Ec-h,Ec+h]; ns=[Nc-h,Nc-h,Nc+h,Nc+h]
    lo,la=convert_lonlat(es,ns)
    return f'{min(la):.5f},{min(lo):.5f},{max(la):.5f},{max(lo):.5f}'
def osm(L,budget=240):
    bb=bbox(L['Ec'],L['Nc'],900)
    return q(f'''[out:json][timeout:100];
(way["natural"="water"]({bb}); relation["natural"="water"]({bb}); way["landuse"="reservoir"]({bb});
 way["waterway"~"^(stream|river|canal|drain|ditch)$"]({bb});
 way["highway"]({bb}); way["railway"]({bb});
 way["barrier"="wall"]({bb});
 way["landuse"="forest"]({bb}); relation["landuse"="forest"]({bb}); way["natural"="wood"]({bb}); relation["natural"="wood"]({bb});
 way["building"]({bb});
 way["natural"~"^(cliff|scree|bare_rock|shingle)$"]({bb}); relation["natural"~"^(scree|bare_rock)$"]({bb});
 node["natural"~"^(peak|cliff)$"]({bb}); node["man_made"="survey_point"]({bb}); node["place"]({bb});
);
out geom;''', budget=budget)
if __name__=='__main__':
    for L in LEVELS:
        if sys.argv[1:] and L['id'] not in sys.argv[1:]: continue
        j=osm(L); print(L['id'], len(j['elements']), flush=True)
