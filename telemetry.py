"""Explicit PostHog relay. Local learning works without credentials/network."""
import json
import os
from urllib.request import Request, urlopen
from engine import connect, now

HOSTS = {'https://us.i.posthog.com', 'https://eu.i.posthog.com'}

def payload(row, token):
    return {'token': token, 'event': row['name'], 'uuid': row['id'], 'timestamp': row['ts'],
            'properties': {**json.loads(row['properties']), 'distinct_id': row['learner_id'],
                           'journey_id': row['journey_id'], '$process_person_profile': False,
                           'variant': row['variant'], 'source': row['source']}}

def flush(path, opener=urlopen):
    token = os.environ.get('POSTHOG_PROJECT_TOKEN', '')
    host = os.environ.get('POSTHOG_HOST', 'https://us.i.posthog.com').rstrip('/')
    if not token:
        return {'sent': 0, 'status': 'disabled: no project token'}
    if host not in HOSTS:
        raise ValueError('Use a supported US or EU PostHog ingestion host')
    sent = failed = 0
    with connect(path) as db:
        rows = db.execute('SELECT e.*,l.variant FROM outbox o JOIN events e ON e.id=o.event_id JOIN learners l ON l.id=e.learner_id WHERE o.sent_at IS NULL AND l.consent=1 AND e.source=\'local\' LIMIT 100').fetchall()
        for row in rows:
            request = Request(host+'/i/v0/e/', data=json.dumps(payload(row,token)).encode(), headers={'Content-Type':'application/json'}, method='POST')
            try:
                with opener(request,timeout=5) as response:
                    if not 200<=response.status<300:
                        raise OSError('Ingestion rejected')
                    response.read(1024)
                db.execute('UPDATE outbox SET tries=tries+1,sent_at=?,last_error=NULL WHERE event_id=?', (now(),row['id']))
                sent+=1
            except Exception:
                # Do not persist raw exception text: it can contain credentials/URLs.
                db.execute("UPDATE outbox SET tries=tries+1,last_error='transport_failed' WHERE event_id=?", (row['id'],))
                failed+=1
        return {'sent':sent,'failed':failed,'status':'processed'}
