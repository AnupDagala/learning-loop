import concurrent.futures
import http.cookiejar
import json
import tempfile
import threading
import unittest
import uuid
from urllib.error import HTTPError
from urllib.request import build_opener,HTTPCookieProcessor,Request
from server import Server
from engine import connect

class HTTPTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=self.tmp.name+'/db';self.server=Server(('127.0.0.1',0),self.path)
  self.t=threading.Thread(target=self.server.serve_forever,daemon=True);self.t.start();self.base='http://127.0.0.1:'+str(self.server.server_port)
  self.client=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
  self.user=self.req('/api/session')[1];self.j=str(uuid.uuid4());self.a=str(uuid.uuid4())
 def tearDown(self):self.server.shutdown();self.server.server_close();self.t.join();self.tmp.cleanup()
 def req(self,path,data=None,headers=None,client=None):
  req=Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers or ({'Content-Type':'application/json'} if data is not None else {}))
  try:
   with (client or self.client).open(req,timeout=3) as r:return r.status,json.loads(r.read())
  except HTTPError as e:return e.code,json.loads(e.read())
 def start(self):return self.req('/api/start',{'lesson_id':'rights','journey_id':self.j})
 def submission(self):return {'lesson_id':'rights','journey_id':self.j,'attempt_id':self.a,'answers':[1,0,2]}
 def test_full_journey_and_restart_state(self):
  self.start();self.assertEqual(self.req('/api/submit',self.submission())[0],200)
  self.req('/api/feedback',{'attempt_id':self.a});self.req('/api/plan',{'attempt_id':self.a})
  self.assertEqual(self.req('/api/session')[1]['plan']['attempt_id'],self.a)
  self.assertEqual(self.req('/api/review',{'answers':[1,0,2]})[1]['score'],3)
 def test_public_questions_have_no_answer_keys(self):
  for l in self.user['lessons']:
   for q in l['questions']:self.assertNotIn('answer',q);self.assertNotIn('explanation',q)
 def test_cross_origin_rejected(self):
  self.assertEqual(self.req('/api/start',{'lesson_id':'rights','journey_id':self.j},{'Content-Type':'application/json','Origin':'https://evil.example'})[0],403)
 def test_missing_session_rejected(self):
  self.assertEqual(self.req('/api/start',{'lesson_id':'rights','journey_id':self.j},client=build_opener())[0],400)
 def test_invalid_uuid_and_unknown_lesson(self):
  self.assertEqual(self.req('/api/start',{'lesson_id':'rights','journey_id':'bad'})[0],400)
  self.assertEqual(self.req('/api/start',{'lesson_id':'unknown','journey_id':self.j})[0],400)
 def test_large_payload_rejected(self):
  self.assertEqual(self.req('/api/start',{'junk':'x'*17000})[0],413)
 def test_concurrent_retries_grade_once(self):
  self.start()
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
   results=list(pool.map(lambda _:self.req('/api/submit',self.submission()),range(4)))
  self.assertTrue(all(s==200 for s,_ in results))
  with connect(self.path) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0],1)
 def test_journey_lesson_cannot_change(self):
  self.start();self.assertEqual(self.req('/api/start',{'lesson_id':'inflation','journey_id':self.j})[0],400)
 def test_revocation_removes_pending_outbox(self):
  self.req('/api/consent',{'enabled':True});self.start();self.req('/api/consent',{'enabled':False})
  with connect(self.path) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM outbox').fetchone()[0],0)
 def test_consent_requires_boolean(self):
  self.assertEqual(self.req('/api/consent',{'enabled':'yes'})[0],400)
 def test_other_session_cannot_access_feedback(self):
  self.start();self.req('/api/submit',self.submission());other=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()));self.req('/api/session',client=other)
  self.assertEqual(self.req('/api/feedback',{'attempt_id':self.a},client=other)[0],400)
 def test_analytics_source_rejected(self):
  self.assertEqual(self.req('/api/analytics?source=all')[0],400)
 def test_no_path_traversal(self):
  self.assertEqual(self.req('/../engine.py')[0],404)

if __name__=='__main__':unittest.main()
