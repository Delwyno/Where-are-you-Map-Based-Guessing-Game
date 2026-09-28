// Offline support for "Where are you?" / "Ble wyt ti?"
// Keeps the pages, three.js and every Eryri place in the browser cache, so the game works with no signal.
const V='way-39712161';   // change this (the build does) to make phones pick up a new version
const CORE=['./','index.html','cy.html','manifest.webmanifest','manifest-cy.webmanifest','icon-192.png','icon-512.png',
  'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'];
const PLACES=["padarn", "gwynant", "crafnant", "beddgelert", "ogwen", "idwal", "cwmbychan", "llydaw", "rhydddu", "stwlan", "siabod", "cnicht", "ygarn", "cau", "nantlle", "glyderfach", "wyddfa", "aran", "cribgoch", "carneddau", "rhinogfawr", "llynhywel", "bodlyn", "arenig", "moelhebog", "cwmsilyn", "moeleilio", "dinas", "llagi", "glyderfawr", "dafydd", "cowlyd", "eigiau"];
self.addEventListener('install',e=>{
  e.waitUntil(caches.open(V).then(c=>Promise.allSettled(CORE.concat(PLACES.map(id=>'eryri/'+id+'.json'),PLACES.map(id=>id+'.json')).map(u=>c.add(u)))));   // one failure doesn't stop the rest
  self.skipWaiting();
});
self.addEventListener('activate',e=>{
  e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',e=>{
  const req=e.request; if(req.method!=='GET') return;
  if(req.mode==='navigate'){   // pages: try the network first so updates arrive, fall back to the saved copy
    e.respondWith(fetch(req).then(r=>{ const cp=r.clone(); caches.open(V).then(c=>c.put(req,cp)); return r; })
      .catch(()=>caches.match(req,{ignoreSearch:true}).then(r=>r||caches.match('index.html'))));
    return;
  }
  e.respondWith(caches.match(req).then(r=>r||fetch(req).then(res=>{   // everything else: saved copy first
    if(res.ok||res.type==='opaque'){ const cp=res.clone(); caches.open(V).then(c=>c.put(req,cp)); }
    return res;
  })));
});
