"""Build the website and the two single-file versions from the page sources and the place data.

Run from the top of the repo, after tools/process.py has written tools/eryri.json:
    python tools/build_site.py
Writes (at the top of the repo):  index.html, cy.html, sw.js, the two manifests, eryri/<place>.json
Writes (in tools/out/):           artefact-en.html, artefact-cy.html  (everything embedded, no offline worker)
"""
import re, json, os, gzip, base64, hashlib
T=os.path.dirname(os.path.abspath(__file__)); R=os.path.dirname(T)
places=json.load(open(os.path.join(T,'eryri.json'),encoding='utf-8'))
ids=[d['id'] for d in places]
os.makedirs(os.path.join(R,'eryri'),exist_ok=True)
for d in places: open(os.path.join(R,'eryri',d['id']+'.json'),'w',encoding='utf-8').write(json.dumps(d,separators=(',',':'),ensure_ascii=False))
b64=base64.b64encode(gzip.compress(json.dumps(places,separators=(',',':'),ensure_ascii=False).encode(),9)).decode()
def load(f): return open(f,encoding='utf-8').read()
def setdata(s,data):
    m=re.search(r'(<script[^>]*id="eryriData"[^>]*>)(.*?)(</script>)',s,re.S); return s[:m.start(2)]+data+s[m.end(2):]
os.makedirs(os.path.join(T,'out'),exist_ok=True)
EN_ART='https://claude.ai/artifact/CCNWB9qVWF4JzWYMbUSqbw'; CY_ART='https://claude.ai/artifact/1sbjgZ519oEFfjEYQXtsua'
srcs=''
for src,out,lang in (('page_en.html','index.html','en'),('page_cy.html','cy.html','cy')):
    s=load(os.path.join(T,'src',src)); srcs+=s
    open(os.path.join(R,out),'w',encoding='utf-8').write(setdata(s,''))
    a=setdata(s,b64); a=re.sub(r'<!--pwa-->.*?<!--/pwa-->\n?','',a,flags=re.S).replace('const PWA=true;','const PWA=false;')
    if lang=='en':
        a=a.replace('<a class="lang" id="langLink" href="cy.html" hreflang="cy" lang="cy">','<a class="lang" id="langLink" href="%s" hreflang="cy" lang="cy" target="_blank" rel="noopener">'%CY_ART)
        a=a.replace("try{ if(true&&!localStorage.getItem('way-lang')","try{ if(false&&!localStorage.getItem('way-lang')")
    else:
        a=a.replace('<a class="lang" id="langLink" href="index.html" hreflang="en" lang="en">','<a class="lang" id="langLink" href="%s" hreflang="en" lang="en" target="_blank" rel="noopener">'%EN_ART)
    open(os.path.join(T,'out','artefact-'+lang+'.html'),'w',encoding='utf-8').write(a)
V='way-'+hashlib.sha1((b64+srcs).encode()).hexdigest()[:8]
sw=f"""// Offline support for "Where are you?" / "Ble wyt ti?"
// Keeps the pages, three.js and every Eryri place in the browser cache, so the game works with no signal.
const V='{V}';   // change this (the build does) to make phones pick up a new version
const CORE=['./','index.html','cy.html','manifest.webmanifest','manifest-cy.webmanifest','icon-192.png','icon-512.png',
  'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'];
const PLACES={json.dumps(ids)};
self.addEventListener('install',e=>{{
  e.waitUntil(caches.open(V).then(c=>Promise.allSettled(CORE.concat(PLACES.map(id=>'eryri/'+id+'.json'),PLACES.map(id=>id+'.json')).map(u=>c.add(u)))));   // one failure doesn't stop the rest
  self.skipWaiting();
}});
self.addEventListener('activate',e=>{{
  e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
}});
self.addEventListener('fetch',e=>{{
  const req=e.request; if(req.method!=='GET') return;
  if(req.mode==='navigate'){{   // pages: try the network first so updates arrive, fall back to the saved copy
    e.respondWith(fetch(req).then(r=>{{ const cp=r.clone(); caches.open(V).then(c=>c.put(req,cp)); return r; }})
      .catch(()=>caches.match(req,{{ignoreSearch:true}}).then(r=>r||caches.match('index.html'))));
    return;
  }}
  e.respondWith(caches.match(req).then(r=>r||fetch(req).then(res=>{{   // everything else: saved copy first
    if(res.ok||res.type==='opaque'){{ const cp=res.clone(); caches.open(V).then(c=>c.put(req,cp)); }}
    return res;
  }})));
}});
"""
open(os.path.join(R,'sw.js'),'w').write(sw)
for fn,name,short,start,lang in (('manifest.webmanifest','Where are you? Contour map challenge','Where are you?','index.html','en'),('manifest-cy.webmanifest','Ble wyt ti? Her map cyfuchliniau','Ble wyt ti?','cy.html','cy')):
    json.dump({'name':name,'short_name':short,'lang':lang,'start_url':start,'scope':'./','display':'standalone','background_color':'#eef0ea','theme_color':'#1c2833',
      'icons':[{'src':'icon-192.png','sizes':'192x192','type':'image/png'},{'src':'icon-512.png','sizes':'512x512','type':'image/png','purpose':'any maskable'}]},open(os.path.join(R,fn),'w'),ensure_ascii=False,indent=1)
print('built',V,len(ids),'places')
