import json
import os
import tempfile
import unittest
import uuid
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
from engine import analytics,connect,event,init,learner,save_plan,seed,submit,review,now
from telemetry import flush

class DomainTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=self.tmp.name+'/db.sqlite3';init(self.path)
  self.db=connect(self.path);self.l=learner(self.db);self.id=self.l['id'];self.j=str(uuid.uuid4());self.a=str(uuid.uuid4())
  event(self.db,self.id,self.j,'lesson_started',{'lesson_id':'rights'});self.db.commit()
 def tearDown(self):self.db.close();self.tmp.cleanup()
 def submit(self,answers=None):return submit(self.db,self.id,self.a,'rights',self.j,answers or [0,0,2])
 def plan(self):
  r=self.submit();event(self.db,self.id,self.j,'feedback_viewed');return save_plan(self.db,self.id,self.a)
 def test_server_grades_and_names_gaps(self):
  r=self.submit();self.assertEqual(r['score'],2);self.assertEqual(r['weak_concepts'],['Reasonable classification'])
 def test_perfect_score_has_no_gaps(self):
  self.assertEqual(self.submit([1,0,2])['weak_concepts'],[])
 def test_submit_retry_does_not_duplicate(self):
  self.assertEqual(self.submit(),self.submit());self.assertEqual(self.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0],1)
 def test_retry_conflicting_payload_rejected(self):
  self.submit()
  with self.assertRaises(ValueError):self.submit([1,0,2])
 def test_other_learner_cannot_read_attempt(self):
  self.submit();other=learner(self.db)
  with self.assertRaises(ValueError):save_plan(self.db,other['id'],self.a)
 def test_no_submission_without_started_lesson(self):
  with self.assertRaises(ValueError):submit(self.db,self.id,str(uuid.uuid4()),'inflation',self.j,[0,1,2])
 def test_invalid_answers(self):
  for answers in ([True,0,2],[3,0,2],[-1,0,2],[0,2],['1',0,2]):
   with self.subTest(answers=answers),self.assertRaises(ValueError):self.submit(answers)
 def test_feedback_required_before_plan(self):
  self.submit()
  with self.assertRaises(ValueError):save_plan(self.db,self.id,self.a)
 def test_plan_retry_preserves_due_time(self):
  p=self.plan();self.assertEqual(p,save_plan(self.db,self.id,self.a))
 def test_revision_once_only(self):
  self.plan();self.assertFalse(review(self.db,self.id,[1,0,2])['already_completed']);self.assertTrue(review(self.db,self.id,[1,0,2])['already_completed'])
  self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events WHERE name='review_completed'").fetchone()[0],1)
 def test_revision_rejects_invalid_answers(self):
  self.plan()
  with self.assertRaises(ValueError):review(self.db,self.id,[True,0,2])
 def test_ordered_funnel_rejects_early_feedback(self):
  self.db.execute('DELETE FROM events');t=datetime(2026,1,1,tzinfo=timezone.utc)
  for step,name in [(0,'feedback_viewed'),(1,'lesson_started'),(2,'quiz_submitted'),(3,'plan_saved')]:
   event(self.db,self.id,self.j,name,ts=(t+timedelta(seconds=step)).isoformat(timespec='microseconds'))
  r=analytics(self.db,'local')['funnel'][0];self.assertEqual((r['started'],r['quiz'],r['feedback'],r['saved']),(1,1,0,0))
 def test_funnel_cannot_mix_journeys(self):
  event(self.db,self.id,'other','quiz_submitted');r=analytics(self.db,'local')['funnel'][0];self.assertEqual(r['quiz'],0)
 def test_funnel_has_24h_window(self):
  event(self.db,self.id,self.j,'quiz_submitted',ts=(datetime.now(timezone.utc)+timedelta(days=2)).isoformat(timespec='microseconds'))
  self.assertEqual(analytics(self.db,'local')['funnel'][0]['quiz'],0)
 def test_immature_cohorts_excluded(self):
  self.assertEqual(analytics(self.db,'local')['retention'],[])
 def test_d1_exact_calendar_day(self):
  self.db.execute('DELETE FROM events');base=datetime(2026,1,1,9,tzinfo=timezone.utc)
  event(self.db,self.id,self.j,'lesson_started',ts=base.isoformat(timespec='microseconds'))
  event(self.db,self.id,self.j,'review_completed',ts=(base+timedelta(days=2)).isoformat(timespec='microseconds'))
  r=analytics(self.db,'local','2026-01-04T00:00:00+00:00')['retention'][0];self.assertEqual(r['returned'],0)
  event(self.db,self.id,'d1','lesson_started',ts=(base+timedelta(days=1)).isoformat(timespec='microseconds'))
  self.assertEqual(analytics(self.db,'local','2026-01-04T00:00:00+00:00')['retention'][0]['returned'],1)
 def test_event_uuid_deduplicates(self):
  x=str(uuid.uuid4());event(self.db,self.id,self.j,'feedback_viewed',eid=x);event(self.db,self.id,self.j,'feedback_viewed',eid=x)
  self.assertEqual(self.db.execute('SELECT COUNT(*) FROM events WHERE id=?',(x,)).fetchone()[0],1)
 def test_synthetic_seed_is_separate_and_idempotent(self):
  self.db.commit();seed(self.path);seed(self.path);r=analytics(self.db,'synthetic');self.assertEqual(sum(x['started'] for x in r['funnel']),120);self.assertEqual(sum(x['saved'] for x in r['funnel']),54);self.assertEqual(sum(x['returned'] for x in r['retention']),30);self.assertEqual(self.db.execute('SELECT COUNT(*) FROM outbox').fetchone()[0],0)
 def test_no_external_outbox_without_consent(self):
  self.submit();self.assertEqual(self.db.execute('SELECT COUNT(*) FROM outbox').fetchone()[0],0)
 def queue(self):
  self.db.execute('UPDATE learners SET consent=1 WHERE id=?',(self.id,));self.submit();self.db.commit()
 def test_posthog_disabled_without_token(self):
  self.queue()
  with patch.dict(os.environ,{'POSTHOG_PROJECT_TOKEN':''}):self.assertIn('disabled',flush(self.path)['status'])
 def test_posthog_mock_payload_and_success(self):
  self.queue();captured=[]
  class Response:
   status=200
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self,*a):return b'ok'
  def opener(req,timeout):captured.append(json.loads(req.data));return Response()
  with patch.dict(os.environ,{'POSTHOG_PROJECT_TOKEN':'test-token','POSTHOG_HOST':'https://us.i.posthog.com'}):self.assertEqual(flush(self.path,opener)['sent'],1)
  self.assertFalse(captured[0]['properties']['$process_person_profile']);self.assertEqual(captured[0]['event'],'quiz_submitted');self.assertEqual(captured[0]['properties']['distinct_id'],self.id)
 def test_posthog_failure_retries_without_losing_event(self):
  self.queue()
  def fail(*a,**k):raise OSError('mock secret not logged')
  with patch.dict(os.environ,{'POSTHOG_PROJECT_TOKEN':'test-token','POSTHOG_HOST':'https://us.i.posthog.com'}):
   self.assertEqual(flush(self.path,fail)['failed'],1);self.assertEqual(flush(self.path,fail)['failed'],1)
  r=self.db.execute('SELECT * FROM outbox').fetchone();self.assertEqual(r['tries'],2);self.assertEqual(r['last_error'],'transport_failed');self.assertIsNone(r['sent_at'])
 def test_posthog_revoke_blocks_queued_send(self):
  self.queue();self.db.execute('UPDATE learners SET consent=0 WHERE id=?',(self.id,));self.db.commit()
  with patch.dict(os.environ,{'POSTHOG_PROJECT_TOKEN':'test-token','POSTHOG_HOST':'https://us.i.posthog.com'}):self.assertEqual(flush(self.path,lambda *a: self.fail('Should not send'))['sent'],0)
 def test_posthog_host_allowlist(self):
  with patch.dict(os.environ,{'POSTHOG_PROJECT_TOKEN':'test','POSTHOG_HOST':'http://localhost:1'}),self.assertRaises(ValueError):flush(self.path)
 def test_domain_transaction_rolls_back(self):
  try:
   with self.db:
    self.submit();raise RuntimeError('fail after mutation')
  except RuntimeError:pass
  self.assertEqual(self.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0],0)

if __name__=='__main__':unittest.main()
