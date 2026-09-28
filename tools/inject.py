"""Put freshly built Eryri data (eryri.b64 from process.py) into the finished game file.
Usage: python3 inject.py index.html eryri.b64 [out.html]"""
import re, sys
html, b64 = sys.argv[1], sys.argv[2]; out = sys.argv[3] if len(sys.argv) > 3 else html
s = open(html, encoding='utf-8').read(); data = open(b64).read().strip()
pat = re.compile(r'(<script[^>]*id="eryriData"[^>]*>)(.*?)(</script>)', re.S)
assert len(pat.findall(s)) == 1, 'eryriData block not found exactly once'
s = pat.sub(lambda m: m.group(1) + data + m.group(3), s)
open(out, 'w', encoding='utf-8').write(s); print('wrote', out, len(s.encode()), 'bytes')
