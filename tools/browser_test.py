import sys, time
from playwright.sync_api import sync_playwright
three=open('node_modules/three/build/three.min.js','rb').read()
lv=sys.argv[1] if len(sys.argv)>1 else 'padarn'   # level id from levels.py
out=sys.argv[2] if len(sys.argv)>2 else 'shot.png'
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
    pg=b.new_page(viewport={'width':1280,'height':900})
    logs=[]; pg.on('console',lambda m:logs.append(m.type+': '+m.text)); pg.on('pageerror',lambda e:logs.append('PAGEERROR '+str(e)))
    pg.route('**/three.min.js',lambda r:r.fulfill(body=three,content_type='application/javascript'))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.abort()); pg.route('**/fonts.gstatic.com/**',lambda r:r.abort())
    pg.add_init_script(f"localStorage.setItem('way-settings',JSON.stringify({{play:'eryri',mode:'spots',level:'medium'}}));localStorage.setItem('way-eryri2',JSON.stringify({{cur:'{lv}',attempt:0,done:{{}},open:{{'{lv}':1}}}}));")
    t=time.time(); import os; pg.goto('file://'+os.path.abspath(sys.argv[3] if len(sys.argv)>3 else '../index.html'))
    pg.wait_for_function("document.querySelectorAll('#choices .choice').length>0",timeout=90000)
    print('ready',round(time.time()-t,1),'s')
    pg.wait_for_timeout(800)
    print("PICK",pg.evaluate("JSON.stringify(window.__pick)"))
    print(pg.inner_text("#modeInfo").replace('\n',' | '), '||', pg.inner_text('#status'), '||', pg.inner_text('#wxTag'), pg.inner_text('#facingTxt'))
    pg.screenshot(path=out,full_page=True)
    for l in logs: print(l)
    b.close()
