# Local test bridge into Fusion (add-in): lets a tool on this PC run Python inside Fusion,
# e.g. Claude Code testing tools/fusion/KeyboardCase without the dialogs.
#   - Listens on 127.0.0.1 only (port 8765, the next free one if taken).
#   - Every request needs the token written at start to ~/.fusion_bridge (JSON with port and
#     token, a new random token each start); the file is deleted on stop.
#   - POST /run  body {"code": "..."}: the code runs on Fusion's main thread (custom event)
#     with app, ui, adsk in scope; whatever it assigns to `result` (JSON-able) and prints is
#     returned: {"ok": true/false, "stdout": ..., "result": ..., "error": traceback}.
#   - GET /ping: {"ok": true, "version": Fusion's version}.
# It can run any code inside Fusion: start it only for a test session, stop it in
# Scripts and Add-Ins (Stop) when done. Not started on Fusion start-up.
import adsk.core, adsk.fusion, traceback, threading, json, os, io, uuid, secrets, contextlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

EVENT_ID = 'KeyboardWorkshopBridgeRun'
INFO = os.path.join(os.path.expanduser('~'), '.fusion_bridge')
TIMEOUT = 900                                    # s per request
app = ui = server = event = None
handlers, jobs = [], {}
token = None


class RunHandler(adsk.core.CustomEventHandler):
    def notify(self, args):                      # main thread
        job = jobs.get(args.additionalInfo)
        if not job: return
        out = io.StringIO()
        scope = {'adsk': adsk, 'app': app, 'ui': ui, 'result': None, '__name__': '__bridge__'}
        try:
            with contextlib.redirect_stdout(out):
                exec(compile(job['code'], '<bridge>', 'exec'), scope)
            job['reply'] = {'ok': True, 'result': scope.get('result')}
        except Exception:
            job['reply'] = {'ok': False, 'error': traceback.format_exc()}
        job['reply']['stdout'] = out.getvalue()
        job['done'].set()


class Http(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send(self, code, obj):
        try: body = json.dumps(obj, default=repr).encode()
        except Exception: body = json.dumps({'ok': False, 'error': 'result not JSON-able'}).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorised(self):
        if self.headers.get('Origin'):           # no browser pages
            self.send(403, {'ok': False, 'error': 'forbidden'}); return False
        if not secrets.compare_digest(self.headers.get('X-Token', ''), token):
            self.send(401, {'ok': False, 'error': 'bad token'}); return False
        return True

    def do_GET(self):
        if not self.authorised(): return
        if self.path == '/ping': self.send(200, {'ok': True, 'version': app.version})
        else: self.send(404, {'ok': False})

    def do_POST(self):
        if not self.authorised(): return
        if self.path != '/run': self.send(404, {'ok': False}); return
        try:
            code = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))['code']
        except Exception:
            self.send(400, {'ok': False, 'error': 'body must be {"code": "..."}'}); return
        jid = uuid.uuid4().hex
        jobs[jid] = {'code': code, 'done': threading.Event()}
        app.fireCustomEvent(EVENT_ID, jid)
        if jobs[jid]['done'].wait(TIMEOUT): self.send(200, jobs.pop(jid)['reply'])
        else: self.send(504, {'ok': False, 'error': 'timed out (still running in Fusion)'})


def run(context):
    global app, ui, server, event, token
    app = adsk.core.Application.get(); ui = app.userInterface
    try:
        event = app.registerCustomEvent(EVENT_ID)
        h = RunHandler(); event.add(h); handlers.append(h)
        token = secrets.token_hex(24)
        for port in range(8765, 8785):
            try: server = ThreadingHTTPServer(('127.0.0.1', port), Http); break
            except OSError: continue
        threading.Thread(target=server.serve_forever, daemon=True).start()
        with open(INFO, 'w') as f: json.dump({'port': port, 'token': token}, f)
        ui.messageBox('Bridge listening on 127.0.0.1:%d (token in %s).\nStop it in Scripts and Add-Ins when done.' % (port, INFO))
    except Exception:
        ui.messageBox('Bridge failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    global server
    try:
        if server: server.shutdown(); server.server_close(); server = None
        if event:
            for h in handlers: event.remove(h)
        app.unregisterCustomEvent(EVENT_ID)
        if os.path.exists(INFO): os.remove(INFO)
    except Exception:
        pass
