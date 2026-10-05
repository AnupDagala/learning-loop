"""Local portfolio demo. Python 3.11+, standard library only."""
import argparse
import json
import os
import uuid
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from content import LESSONS, public_lessons
from engine import analytics, connect, event, init, learner, owned_attempt, review, save_plan, seed, submit

ROOT = Path(__file__).parent

def identifier(value):
    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise ValueError('Expected a UUID identifier')

class Handler(BaseHTTPRequestHandler):
    server_version = 'LearningLoop/1'

    def log_message(self, fmt, *args):
        pass  # No learner identifiers or answer bodies in request logs.

    def send(self, status, body, content_type='application/json', cookie=None):
        raw = json.dumps(body).encode() if content_type=='application/json' else body
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if cookie:
            self.send_header('Set-Cookie',cookie)
        self.end_headers()
        self.wfile.write(raw)

    def identity(self, db):
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get('Cookie',''))
        except Exception:
            pass
        lid = cookies['ll_session'].value if 'll_session' in cookies else None
        if lid and db.execute('SELECT 1 FROM learners WHERE id=?', (lid,)).fetchone():
            return learner(db,lid)
        if self.command!='GET' or urlsplit(self.path).path!='/api/session':
            raise ValueError('Start a session first')
        return learner(db)

    def do_GET(self):
        parsed=urlsplit(self.path)
        if parsed.path.startswith('/api/'):
            try:
                with connect(self.server.db_path) as db:
                    if parsed.path=='/api/analytics':
                        data=analytics(db,parse_qs(parsed.query).get('source',['synthetic'])[0])
                        data['posthog_configured']=bool(os.environ.get('POSTHOG_PROJECT_TOKEN'))
                        return self.send(200,data)
                    if parsed.path=='/api/health':
                        db.execute('SELECT 1')
                        return self.send(200,{'status':'ok','mode':'local demo'})
                    user=self.identity(db)
                    if parsed.path=='/api/session':
                        plan=db.execute('SELECT * FROM plans WHERE learner_id=?',(user['id'],)).fetchone()
                        latest=db.execute('SELECT result FROM attempts WHERE learner_id=? ORDER BY created_at DESC LIMIT 1',(user['id'],)).fetchone()
                        data={**user,'lessons':public_lessons(),'plan':dict(plan) if plan else None,'latest':json.loads(latest[0]) if latest else None}
                    else:
                        return self.send(404,{'error':'Route not found'})
                # Commit session creation before returning its cookie.
                return self.send(200,data,cookie=f"ll_session={user['id']}; HttpOnly; SameSite=Strict; Path=/; Max-Age=2592000")
            except ValueError as exc:
                return self.send(400,{'error':str(exc)})
        mapping={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
        name=mapping.get(parsed.path)
        if not name:
            return self.send(404,{'error':'Route not found'})
        types={'html':'text/html; charset=utf-8','js':'text/javascript; charset=utf-8','css':'text/css; charset=utf-8'}
        self.send(200,(ROOT/'web'/name).read_bytes(),types[name.split('.')[-1]])

    def do_POST(self):
        # Reject cross-site requests even on localhost; no CORS exposure.
        origin=self.headers.get('Origin')
        if origin and urlsplit(origin).netloc!=self.headers.get('Host'):
            return self.send(403,{'error':'Cross-site request rejected'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<1 or length>16384:
                return self.send(413,{'error':'Request must be 1–16384 bytes'})
            if self.headers.get_content_type()!='application/json':
                return self.send(415,{'error':'Send JSON'})
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict):
                raise ValueError('Expected a JSON object')
            path=urlsplit(self.path).path
            with connect(self.server.db_path) as db:
                db.execute('BEGIN IMMEDIATE')
                user=self.identity(db); lid=user['id']
                if path=='/api/start':
                    lesson=data.get('lesson_id'); journey=identifier(data.get('journey_id'))
                    if lesson not in LESSONS:
                        raise ValueError('Unknown lesson')
                    previous=db.execute("SELECT properties FROM events WHERE learner_id=? AND journey_id=? AND name='lesson_started'",(lid,journey)).fetchone()
                    if previous and json.loads(previous[0])['lesson_id']!=lesson:
                        raise ValueError('Journey already belongs to another lesson')
                    event(db,lid,journey,'lesson_started',{'lesson_id':lesson},eid=str(uuid.uuid5(uuid.NAMESPACE_URL,lid+journey+'/start')))
                    result={'journey_id':journey}
                elif path=='/api/submit':
                    result=submit(db,lid,identifier(data.get('attempt_id')),data.get('lesson_id'),identifier(data.get('journey_id')),data.get('answers'))
                elif path=='/api/feedback':
                    aid=identifier(data.get('attempt_id')); a=owned_attempt(db,lid,aid)
                    event(db,lid,a['journey_id'],'feedback_viewed',{'lesson_id':a['lesson_id']},eid=str(uuid.uuid5(uuid.NAMESPACE_URL,aid+'/feedback')))
                    result={'ok':True}
                elif path=='/api/plan':
                    result=save_plan(db,lid,identifier(data.get('attempt_id')))
                elif path=='/api/review':
                    result=review(db,lid,data.get('answers'))
                elif path=='/api/consent':
                    if type(data.get('enabled')) is not bool:
                        raise ValueError('Consent must be true or false')
                    db.execute('UPDATE learners SET consent=? WHERE id=?',(int(data['enabled']),lid))
                    if not data['enabled']:
                        db.execute('DELETE FROM outbox WHERE event_id IN (SELECT id FROM events WHERE learner_id=?) AND sent_at IS NULL',(lid,))
                    result={'consent':data['enabled']}
                else:
                    return self.send(404,{'error':'Route not found'})
            return self.send(200,result)
        except (ValueError, json.JSONDecodeError) as exc:
            return self.send(400,{'error':str(exc)})
        except Exception:
            return self.send(500,{'error':'Unable to save. Retry with the same action identifier.'})

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,db_path):
        init(db_path)
        self.db_path=db_path
        super().__init__(address,Handler)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--db',default=os.environ.get('LEARNING_LOOP_DB','data/learning-loop.sqlite3'))
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--seed',action='store_true')
    parser.add_argument('--flush-posthog',action='store_true')
    args=parser.parse_args()
    init(args.db)
    if args.seed:
        seed(args.db)
        print('Synthetic demo seeded (idempotent); not sent to PostHog.')
    elif args.flush_posthog:
        from telemetry import flush
        print(json.dumps(flush(args.db)))
    else:
        print(f'Learning Loop: http://127.0.0.1:{args.port}',flush=True)
        Server(('127.0.0.1',args.port),args.db).serve_forever()
