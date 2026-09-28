import sys, json
from op import q
from levels import LEVELS
from fetch_fine import bbox
L=[l for l in LEVELS if l['id']==sys.argv[1]][0]; part=sys.argv[2]
bb=bbox(L['Ec'],L['Nc'],900)
parts={
'a':f'(way["natural"="water"]({bb}); relation["natural"="water"]({bb}); way["landuse"="reservoir"]({bb}); way["waterway"~"^(stream|river|canal|drain|ditch)$"]({bb}););',
'b':f'(way["highway"]({bb}); way["railway"]({bb}); way["barrier"="wall"]({bb}); way["building"]({bb}););',
'c':f'(way["landuse"="forest"]({bb}); relation["landuse"="forest"]({bb}); way["natural"="wood"]({bb}); relation["natural"="wood"]({bb}); way["natural"~"^(cliff|scree|bare_rock|shingle)$"]({bb}); relation["natural"~"^(scree|bare_rock)$"]({bb}); node["natural"~"^(peak|cliff)$"]({bb}); node["man_made"="survey_point"]({bb}); node["place"]({bb}););',
'd':f'(node["natural"~"^(peak|cliff)$"]({bb}); node["man_made"="survey_point"]({bb}); node["place"]({bb}););',
'e':f'(way["natural"~"^(cliff|scree|bare_rock|shingle)$"]({bb}); way["landuse"="forest"]({bb}); way["natural"="wood"]({bb}););',
}
j=q(f'[out:json][timeout:60];{parts[part]}out geom;',budget=180)
json.dump(j,open(f'cache/split_{L["id"]}_{part}.json','w')); print(part,len(j['elements']))
