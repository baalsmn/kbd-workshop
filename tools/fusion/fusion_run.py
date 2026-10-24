# Client for the Fusion test bridge (tools/fusion/Bridge, started in Fusion): runs a Python
# file or snippet inside Fusion and prints its output and `result`.
# Usage: python tools/fusion/fusion_run.py <file.py> | -c "<code>" | --ping
import sys, os, json, urllib.request

info = json.load(open(os.path.join(os.path.expanduser('~'), '.fusion_bridge')))
base = 'http://127.0.0.1:%d' % info['port']

def call(path, body=None):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'X-Token': info['token'], 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=960) as r: return json.load(r)
    except urllib.error.HTTPError as e: return json.load(e)

if sys.argv[1] == '--ping':
    print(call('/ping')); sys.exit()
code = sys.argv[2] if sys.argv[1] == '-c' else open(sys.argv[1], encoding='utf-8').read()
r = call('/run', {'code': code})
if r.get('stdout'): print(r['stdout'], end='')
if r.get('result') is not None: print(json.dumps(r['result'], indent=1))
if not r.get('ok'): print(r.get('error'), file=sys.stderr); sys.exit(1)
