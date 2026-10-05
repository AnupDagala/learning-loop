PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS learners (
 id TEXT PRIMARY KEY, variant TEXT NOT NULL CHECK(variant IN ('control','recovery')),
 consent INTEGER NOT NULL DEFAULT 0 CHECK(consent IN (0,1)), created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
 id TEXT PRIMARY KEY, learner_id TEXT NOT NULL REFERENCES learners(id),
 journey_id TEXT NOT NULL, name TEXT NOT NULL,
 ts TEXT NOT NULL, source TEXT NOT NULL CHECK(source IN ('local','synthetic')),
 properties TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS events_flow ON events(source,learner_id,journey_id,name,ts);
CREATE TABLE IF NOT EXISTS attempts (
 id TEXT PRIMARY KEY, learner_id TEXT NOT NULL REFERENCES learners(id),
 lesson_id TEXT NOT NULL, journey_id TEXT NOT NULL, answers TEXT NOT NULL,
 result TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plans (
 learner_id TEXT PRIMARY KEY REFERENCES learners(id), attempt_id TEXT NOT NULL REFERENCES attempts(id),
 lesson_id TEXT NOT NULL, due_at TEXT NOT NULL, completed_at TEXT
);
CREATE TABLE IF NOT EXISTS outbox (
 event_id TEXT PRIMARY KEY REFERENCES events(id), tries INTEGER NOT NULL DEFAULT 0,
 sent_at TEXT, last_error TEXT
);
