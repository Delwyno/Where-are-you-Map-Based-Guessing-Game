import requests, json, time, hashlib, os
EPS=['http://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter']
UA={'User-Agent':'where-are-you-game-data-prep/1.0 (personal map game; delwyno.github.io)'}
def q(query, budget=250):
    h=hashlib.md5(query.encode()).hexdigest(); fn=f'cache/{h}.json'
    os.makedirs('cache',exist_ok=True)
    if os.path.exists(fn): return json.load(open(fn))
    if os.environ.get('OFFLINE'): return None
    t0=time.time(); last=None
    while time.time()-t0<budget:
        for ep in EPS:
            left=budget-(time.time()-t0)
            if left<15: break
            try:
                r=requests.post(ep,data={'data':query},timeout=min(90 if 'overpass-api' in ep else 45,left),headers=UA)
                if r.status_code==200 and r.text.lstrip().startswith('{'):
                    j=r.json(); json.dump(j,open(fn,'w')); return j
                last=f'{ep} {r.status_code} {r.text[:150]}'
            except Exception as e: last=f'{ep} {type(e).__name__}'
            print('retry:',last[:160],flush=True)
        time.sleep(4)
    raise RuntimeError(last)
