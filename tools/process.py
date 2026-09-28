import json, gzip, base64, os, numpy as np
os.environ['OFFLINE']='1'
from shapely.geometry import Polygon, LineString, box, Point
from shapely.ops import polygonize, unary_union
from shapely.validation import make_valid
from convertbng.util import convert_bng
from levels import LEVELS
from cog import fine_grid, coarse_grid
from fetch_fine import osm
HALF=750; CLIP=box(-900,-900,900,900); MAPB=box(-760,-760,760,760)

def xz(geom, L):
    lons=[p['lon'] for p in geom]; lats=[p['lat'] for p in geom]
    E,N=convert_bng(lons,lats)
    return [(e-L['Ec'], L['Nc']-n) for e,n in zip(E,N)]

def polys_of(el, L):
    out=[]
    if el['type']=='way':
        pts=xz(el['geometry'],L)
        if len(pts)>=4 and pts[0]==pts[-1] or (len(pts)>=4 and np.hypot(pts[0][0]-pts[-1][0],pts[0][1]-pts[-1][1])<0.01):
            out.append(make_valid(Polygon(pts)))
    else:
        outer=[];inner=[]
        for m in el.get('members',[]):
            if m['type']!='way' or 'geometry' not in m: continue
            ls=LineString(xz(m['geometry'],L))
            (inner if m.get('role')=='inner' else outer).append(ls)
        o=unary_union(list(polygonize(unary_union(outer)))) if outer else None
        if o is None or o.is_empty: return []
        if inner:
            i=unary_union(list(polygonize(unary_union(inner))))
            o=o.difference(i)
        out.append(o)
    return out

def flat_polys(g):
    if g.is_empty: return []
    if g.geom_type=='Polygon': return [g]
    if hasattr(g,'geoms'): return [p for x in g.geoms for p in flat_polys(x)]
    return []
def flat_lines(g):
    if g.is_empty: return []
    if g.geom_type=='LineString': return [g]
    if hasattr(g,'geoms'): return [p for x in g.geoms for p in flat_lines(x)]
    return []
def ring(c): return [v for p in list(c)[:-1] for v in (round(p[0]),round(p[1]))]
def line(c): return [v for p in c for v in (round(p[0]),round(p[1]))]
def enc_poly(p, tol=1.5):
    p=p.simplify(tol)
    if p.is_empty or p.geom_type!='Polygon': return None
    r=[ring(p.exterior.coords)]+[ring(i.coords) for i in p.interiors if Polygon(i).area>50]
    return r if len(r[0])>=6 else None

FIX={'Cadair Idris':'Penygadair','Carnedd Y Filiast':'Carnedd y Filiast','Pen Yr Ole Wen':'Pen yr Ole Wen','Castell Y Gwynt':'Castell y Gwynt','Pen Y Bigil':'Pen y Bigil','Y Lliwedd (West Peak)':'Y Lliwedd','Y Lliwedd (East Peak)':'Lliwedd Dwyreiniol','Carreg Blaen-Llym':'Carreg Blaen-llym','Mynydd Drws-Y-Coed':'Mynydd Drws-y-coed'}
import re
def welsh(t):
    n=t.get('name:cy') or t.get('name')
    if not n: return n
    n=FIX.get(n,n)
    return re.sub(r'(?<=[ -])(Y|Yr)(?=[ -])',lambda m:m.group(1).lower(),n)   # Trum Y Ddysgl -> Trum y Ddysgl
_EX='cache/bfed0f20bf55463429ed03e0b72cd23c.json'
EXTRA=[e for e in json.load(open(_EX))['elements'] if e.get('tags',{}).get('natural')=='peak'] if os.path.exists(_EX) else []

def grid_at(g,x,z,half=750,step=7.5):
    n=g.shape[0]; fx=(x+half)/step; fz=(z+half)/step
    i=int(np.clip(round(fx),0,n-1)); j=int(np.clip(round(fz),0,n-1)); return float(g[j,i])

def deltas(arr, scale):
    v=np.round(arr*scale).astype(np.int64).ravel()
    d=np.diff(v,prepend=0)
    return d.tolist()

def cached_osm(L):
    fn=os.path.join(os.path.dirname(os.path.abspath(__file__)),'osm_local',L['id']+'.json')
    if os.path.exists(fn): return json.load(open(fn))   # static extract (osm_local.py) wins
    import hashlib, fetch_fine
    from op import q
    try:
        r=osm_cache_only(L)
        if r: return r
    except Exception: pass
    els=[]
    for p in 'abcde':
        fn=f'cache/split_{L["id"]}_{p}.json'
        if os.path.exists(fn): els+=json.load(open(fn))['elements']
    seen=set(); out=[]
    for e in els:
        k=(e['type'],e['id'])
        if k not in seen: seen.add(k); out.append(e)
    return {'elements':out} if out else None
def osm_cache_only(L):
    import op
    orig=op.EPS; op.EPS=[]
    try: return osm(L,budget=1)
    finally: op.EPS=orig


import shapely
def rle(a):
    v=a.ravel(); out=[]; i=0
    while i<len(v):
        j=i
        while j<len(v) and v[j]==v[i]: j+=1
        out+= [int(v[i]), j-i]; i=j
    return out

def surround(L,cg,flat,half=6000):
    """Lakes (1), conifer (2) and broadleaf (3) woods on the coarse 12 km grid, from the OSM extract.
    Each lake is flattened to its own level so it reads as water from the fine area."""
    n=cg.shape[0]; step=2*half/(n-1)
    xs=np.arange(n)*step-half; X,Z=np.meshgrid(xs,xs)
    m=np.zeros((n,n),np.uint8); m[flat]=1
    fn=os.path.join(os.path.dirname(os.path.abspath(__file__)),'osm_local',L['id']+'_wide.json')
    if not os.path.exists(fn): return cg,m
    els=json.load(open(fn))['elements']; cg=cg.copy()
    def cells(P):
        a,b,c,d=P.bounds
        if c<-half or a>half or d<-half or b>half: return None
        i0,i1=max(0,int((a+half)//step)),min(n-1,int((c+half)//step)+1)
        j0,j1=max(0,int((b+half)//step)),min(n-1,int((d+half)//step)+1)
        sub=shapely.contains_xy(P,X[j0:j1+1,i0:i1+1],Z[j0:j1+1,i0:i1+1])
        if not sub.any(): return None
        full=np.zeros((n,n),bool); full[j0:j1+1,i0:i1+1]=sub; return full
    water=[];wood=[]
    for el in els:
        t=el.get('tags',{})
        if (t.get('natural')=='water' and t.get('water') not in ('river','stream','canal','ditch','drain','wastewater')) or t.get('landuse')=='reservoir': water.append(el)
        elif t.get('natural')=='wood' or t.get('landuse')=='forest': wood.append(el)
    for el in wood:
        t=el['tags']; k=2 if t.get('leaf_type')=='needleleaved' or (t.get('landuse')=='forest' and t.get('leaf_type')!='broadleaved') else 3
        for P in polys_of(el,L):
            for p in flat_polys(P):
                c=cells(p)
                if c is not None: m[c&(m==0)]=k
    nl=0
    for el in water:
        for P in polys_of(el,L):
            for p in flat_polys(P):
                if p.area<4000: continue
                c=cells(p)
                if c is None: continue
                lvl=float(np.percentile(cg[c],30)); cg[c]=np.minimum(cg[c],lvl); m[c]=1; nl+=1
    return cg,m

def do_level(L):
    fg,_=fine_grid(L['Ec'],L['Nc'])
    cg,_=coarse_grid(L['Ec'],L['Nc'],half=6000,step=50)
    # coarse flat-water mask: exactly flat 3x3 neighbourhoods (lakes, reservoirs, sea)
    from scipy.ndimage import maximum_filter, minimum_filter, binary_opening
    rng=maximum_filter(cg,3)-minimum_filter(cg,3)
    flat=binary_opening(rng<0.05, iterations=1)&(cg<=1.0)   # sea / beyond the LiDAR edge
    cg,cmask=surround(L,cg,flat)
    D=dict(id=L['id'],name=L['name'],sub=L['sub'],Ec=L['Ec'],Nc=L['Nc'],half=750,n=fg.shape[0],
           hmin=round(float(fg.min()),1), h=deltas(fg-round(float(fg.min()),1),10),
           c=dict(half=6000,n=cg.shape[0],hmin=round(float(cg.min()),1),h=deltas(cg-round(float(cg.min()),1),10),
                  m=rle(cmask)),
           lakes=[],streams=[],paths=[],roads=[],rails=[],walls=[],woods=[],buildings=[],cliffs=[],rock=[],peaks=[],trigs=[],places=[])
    j=cached_osm(L)
    if j is None:
        print(L['id'],'heights only'); return D
    ids={e['id'] for e in j['elements']}
    for el in j['elements']+[dict(e,type='node',lat=e.get('lat') or e['center']['lat'],lon=e.get('lon') or e['center']['lon']) for e in EXTRA if e['id'] not in ids]:
        t=el.get('tags',{})
        if el['type']=='node':
            x,z=xz([el],L)[0]
            if abs(x)>740 or abs(z)>740: continue
            if t.get('natural')=='peak' and welsh(t):
                ele=t.get('ele'); 
                try: ele=float(str(ele).replace('m','').split(';')[0])
                except: ele=None
                D['peaks'].append(dict(n=welsh(t),x=round(x),z=round(z),e=round(ele if ele else grid_at(fg,x,z))))
            elif t.get('man_made')=='survey_point' and t.get('survey_point:structure','pillar') in ('pillar','beacon'):
                D['trigs'].append([round(x),round(z)])
            elif t.get('place') in ('village','hamlet','town','locality','isolated_dwelling') and welsh(t):
                if t.get('place') in ('village','hamlet','town'): D['places'].append(dict(n=welsh(t),x=round(x),z=round(z)))
            continue
        nat=t.get('natural'); 
        if (nat=='water' and t.get('water') not in ('river','stream','canal','ditch','drain','wastewater')) or t.get('landuse')=='reservoir':
            for P in polys_of(el,L):
                for p in flat_polys(P.intersection(CLIP)):
                    if p.area<150: continue
                    # water level: median of grid heights at cell centres inside
                    xs=np.arange(fg.shape[0])*7.5-750
                    minx,minz,maxx,maxz=p.bounds
                    hs=[fg[jj,ii] for jj,zz in enumerate(xs) if minz<=zz<=maxz for ii,xx in enumerate(xs) if minx<=xx<=maxx and p.contains(Point(xx,zz))]
                    if len(hs)<3:
                        c=p.representative_point(); hs=[grid_at(fg,c.x,c.y)]
                    lvl=float(np.percentile(hs,30))
                    r=enc_poly(p,1.0)
                    if not r: continue
                    lab=p.intersection(box(-700,-700,700,700))
                    lp=None
                    if not lab.is_empty and lab.area>3000:
                        pp=max(flat_polys(lab),key=lambda a:a.area).representative_point(); lp=[round(pp.x),round(pp.y)]
                    D['lakes'].append(dict(n=welsh(t),l=round(lvl,1),r=r,lp=lp,a=round(p.area)))
            continue
        if el['type']=='way' and t.get('waterway'):
            for ls in flat_lines(LineString(xz(el['geometry'],L)).intersection(CLIP)):
                c=ls.simplify(1.5).coords
                if len(c)>=2: D['streams'].append(dict(w=6 if t['waterway']=='river' else 2,p=line(c)))
            continue
        if el['type']=='way' and t.get('highway'):
            hw=t['highway']
            if hw in ('proposed','construction','abandoned','platform','bus_stop'): continue
            tgt='paths' if hw in ('path','footway','bridleway','track','steps','cycleway','pedestrian') else 'roads'
            if tgt=='roads' and hw=='service' and t.get('service') in ('parking_aisle','driveway'): continue
            for ls in flat_lines(LineString(xz(el['geometry'],L)).intersection(CLIP)):
                c=ls.simplify(1.0).coords
                if len(c)>=2: D[tgt].append(line(c))
            continue
        if el['type']=='way' and t.get('railway') in ('rail','narrow_gauge','light_rail','preserved','funicular'):
            for ls in flat_lines(LineString(xz(el['geometry'],L)).intersection(CLIP)):
                c=ls.simplify(1.0).coords
                if len(c)>=2: D['rails'].append(line(c))
            continue
        if el['type']=='way' and t.get('barrier')=='wall':
            for ls in flat_lines(LineString(xz(el['geometry'],L)).intersection(box(-755,-755,755,755))):
                c=ls.simplify(1.0).coords
                if len(c)>=2: D['walls'].append(line(c))
            continue
        if t.get('landuse')=='forest' or nat=='wood':
            kind='c' if t.get('leaf_type')=='needleleaved' or (t.get('landuse')=='forest' and t.get('leaf_type')!='broadleaved') else 'd'
            for P in polys_of(el,L):
                for p in flat_polys(P.intersection(CLIP)):
                    if p.area<200: continue
                    r=enc_poly(p,2.0)
                    if r: D['woods'].append(dict(t=kind,r=r))
            continue
        if t.get('building'):
            for P in polys_of(el,L):
                for p in flat_polys(P):
                    c=p.centroid
                    if abs(c.x)>748 or abs(c.y)>748 or p.area<6: continue
                    mr=p.minimum_rotated_rectangle; cs=list(mr.exterior.coords)
                    e1=np.subtract(cs[1],cs[0]); e2=np.subtract(cs[2],cs[1])
                    l1,l2=np.hypot(*e1),np.hypot(*e2)
                    if l1<l2: e1,e2,l1,l2=e2,e1,l2,l1
                    th=float(np.arctan2(e1[1],e1[0]))
                    lv=t.get('building:levels'); 
                    try: hh=3+2.8*float(lv)
                    except: hh=6 if l1>9 else 4.5
                    D['buildings'].append([round(c.x,1),round(c.y,1),round(l1,1),round(l2,1),round(th,3),round(min(hh,14),1)])
            continue
        if nat=='cliff' and el['type']=='way':
            for ls in flat_lines(LineString(xz(el['geometry'],L)).intersection(CLIP)):
                c=ls.simplify(1.5).coords
                if len(c)>=2: D['cliffs'].append(line(c))
            continue
        if nat in ('scree','bare_rock','shingle'):
            for P in polys_of(el,L):
                for p in flat_polys(P.intersection(CLIP)):
                    if p.area<300: continue
                    r=enc_poly(p,2.5)
                    if r: D['rock'].append(r)
            continue
    # de-dup peaks with same name
    seen=set(); pk=[]
    for p in sorted(D['peaks'],key=lambda p:-p['e']):
        if p['n'] in seen: continue
        seen.add(p['n']); pk.append(p)
    D['peaks']=pk
    print(L['id'], {k:len(v) for k,v in D.items() if isinstance(v,list) and k!='h'})
    return D

if __name__=='__main__':
    out=[do_level(L) for L in LEVELS]
    js=json.dumps(out,separators=(',',':'),ensure_ascii=False).encode()
    gz=gzip.compress(js,9)
    open('eryri.b64','w').write(base64.b64encode(gz).decode())
    json.dump(out,open('eryri.json','w'),ensure_ascii=False)
    print('json',len(js),'gz',len(gz),'b64',len(base64.b64encode(gz)))
