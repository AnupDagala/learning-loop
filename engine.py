"""SQLite domain layer. Atomic grading, event deduplication, consent-gated outbox."""
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from content import LESSONS

ROOT = Path(__file__).parent
NAMES = {'lesson_started', 'quiz_submitted', 'feedback_viewed', 'plan_saved', 'review_completed', 'explanation_requested'}

def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')

def connect(path):
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db

def init(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.executescript((ROOT / 'sql/schema.sql').read_text())

def learner(db, lid=None):
    row = db.execute('SELECT * FROM learners WHERE id=?', (lid,)).fetchone()
    if row:
        return dict(row)
    lid = str(uuid.uuid4())
    variant = 'recovery' if int(hashlib.sha256(lid.encode()).hexdigest(), 16) % 2 else 'control'
    db.execute('INSERT INTO learners VALUES (?,?,0,?)', (lid, variant, now()))
    return {'id': lid, 'variant': variant, 'consent': 0}

def event(db, lid, journey, name, properties=None, eid=None, ts=None, source='local'):
    if name not in NAMES:
        raise ValueError('Unknown event')
    eid = eid or str(uuid.uuid4())
    properties = properties or {}
    cur = db.execute('INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?,?)',
                     (eid, lid, journey, name, ts or now(), source, json.dumps(properties)))
    if cur.rowcount and source == 'local' and db.execute('SELECT consent FROM learners WHERE id=?', (lid,)).fetchone()[0]:
        db.execute('INSERT INTO outbox(event_id) VALUES (?)', (eid,))
    return eid

def submit(db, lid, attempt_id, lesson_id, journey, answers):
    old = db.execute('SELECT * FROM attempts WHERE id=?', (attempt_id,)).fetchone()
    if old:
        if old['learner_id'] != lid:
            raise ValueError('Attempt identifier unavailable')
        if old['lesson_id'] != lesson_id or old['journey_id'] != journey or json.loads(old['answers']) != answers:
            raise ValueError('Attempt identifier reused with different input')
        return json.loads(old['result'])
    lesson = LESSONS.get(lesson_id)
    if not lesson or not isinstance(answers, list) or len(answers) != len(lesson['questions']):
        raise ValueError('Choose one answer for every question')
    if any(type(a) is not int or a < 0 or a >= len(q['options']) for a, q in zip(answers, lesson['questions'])):
        raise ValueError('Invalid answer')
    if not db.execute("SELECT 1 FROM events WHERE learner_id=? AND journey_id=? AND name='lesson_started' AND json_extract(properties,'$.lesson_id')=?", (lid, journey, lesson_id)).fetchone():
        raise ValueError('Start this lesson first')
    results = [{**q, 'chosen': a, 'correct': a == q['answer']} for q, a in zip(lesson['questions'], answers)]
    result = {'attempt_id': attempt_id, 'lesson_id': lesson_id, 'journey_id': journey,
              'score': sum(r['correct'] for r in results), 'total': len(results), 'results': results,
              'weak_concepts': [r['concept'] for r in results if not r['correct']]}
    db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?)',
               (attempt_id, lid, lesson_id, journey, json.dumps(answers), json.dumps(result), now()))
    event(db, lid, journey, 'quiz_submitted', {'lesson_id': lesson_id, 'score': result['score'], 'total': result['total']})
    return result

def owned_attempt(db, lid, aid):
    row = db.execute('SELECT * FROM attempts WHERE id=? AND learner_id=?', (aid, lid)).fetchone()
    if not row:
        raise ValueError('Attempt not found')
    return dict(row)

def save_plan(db, lid, aid):
    attempt = owned_attempt(db, lid, aid)
    if not db.execute("SELECT 1 FROM events WHERE learner_id=? AND journey_id=? AND name='feedback_viewed'", (lid, attempt['journey_id'])).fetchone():
        raise ValueError('Open feedback before saving a plan')
    old = db.execute('SELECT * FROM plans WHERE learner_id=?', (lid,)).fetchone()
    if old and old['attempt_id'] == aid:
        return dict(old)
    due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(timespec='microseconds')
    db.execute('INSERT INTO plans VALUES (?,?,?,?,NULL) ON CONFLICT(learner_id) DO UPDATE SET attempt_id=excluded.attempt_id,lesson_id=excluded.lesson_id,due_at=excluded.due_at,completed_at=NULL', (lid, aid, attempt['lesson_id'], due))
    event(db, lid, attempt['journey_id'], 'plan_saved', {'lesson_id': attempt['lesson_id']}, eid=str(uuid.uuid5(uuid.NAMESPACE_URL, aid + '/plan')))
    return dict(db.execute('SELECT * FROM plans WHERE learner_id=?', (lid,)).fetchone())

def review(db, lid, answers):
    plan = db.execute('SELECT * FROM plans WHERE learner_id=?', (lid,)).fetchone()
    if not plan:
        raise ValueError('Save a revision plan first')
    lesson = LESSONS[plan['lesson_id']]
    if not isinstance(answers, list) or len(answers) != len(lesson['questions']) or any(type(a) is not int or a<0 or a>=len(q['options']) for a,q in zip(answers,lesson['questions'])):
        raise ValueError('Choose one valid answer for every question')
    score = sum(a == q['answer'] for a,q in zip(answers,lesson['questions']))
    if not plan['completed_at']:
        db.execute('UPDATE plans SET completed_at=? WHERE learner_id=?', (now(), lid))
        event(db, lid, plan['attempt_id'], 'review_completed', {'lesson_id': plan['lesson_id'], 'score': score}, eid=str(uuid.uuid5(uuid.NAMESPACE_URL, plan['attempt_id']+'/review')))
    return {'score': score, 'total': len(answers), 'already_completed': bool(plan['completed_at'])}

def analytics(db, source='synthetic', as_of=None):
    if source not in ('local','synthetic'):
        raise ValueError('Unknown dataset')
    params = {'source': source, 'as_of': as_of or now()}
    funnel = [dict(r) for r in db.execute((ROOT/'sql/funnel.sql').read_text(), params)]
    retention = [dict(r) for r in db.execute((ROOT/'sql/retention.sql').read_text(), params)]
    events = db.execute('SELECT COUNT(*) FROM events WHERE source=?', (source,)).fetchone()[0]
    return {'source': source, 'funnel': funnel, 'retention': retention, 'events': events,
            'outbox_pending': db.execute('SELECT COUNT(*) FROM outbox WHERE sent_at IS NULL').fetchone()[0],
            'as_of': params['as_of'], 'unit': 'journeys', 'retention_definition': 'Next UTC calendar day; fully elapsed D1 cohorts only',
            'notice': 'Synthetic illustration, not research or measured product uplift.' if source=='synthetic' else 'Anonymous activity on this local instance; no causal conclusion.'}

def seed(path):
    """Idempotent explicit CLI-only fixture; never sends synthetic data to PostHog."""
    init(path)
    with connect(path) as db:
        if db.execute("SELECT 1 FROM events WHERE source='synthetic' LIMIT 1").fetchone():
            return
        base = datetime.now(timezone.utc).replace(hour=9,minute=0,second=0,microsecond=0)-timedelta(days=7)
        for v in ('control','recovery'):
            for i in range(60):
                lid=f'demo-{v}-{i:03}'; j=lid+'/journey'
                db.execute('INSERT INTO learners VALUES (?,?,0,?)', (lid,v,base.isoformat(timespec='microseconds')))
                counts = (60,45,38,20) if v=='control' else (60,48,44,34)
                for step,(name,count) in enumerate(zip(['lesson_started','quiz_submitted','feedback_viewed','plan_saved'], counts)):
                    if i<count:
                        event(db,lid,j,name,{'lesson_id':'rights'},ts=(base+timedelta(minutes=step)).isoformat(timespec='microseconds'),source='synthetic')
                if i < (12 if v=='control' else 18):
                    event(db,lid,j+'/return','review_completed',{'lesson_id':'rights'},ts=(base+timedelta(days=1)).isoformat(timespec='microseconds'),source='synthetic')
