-- Ordered steps, same learner AND journey, at most 24 hours from first lesson.
-- :source is always bound by the server: 'local' or 'synthetic'.
WITH starts AS (
 SELECT learner_id,journey_id,MIN(ts) AS started FROM events
 WHERE source=:source AND name='lesson_started' GROUP BY learner_id,journey_id
), quizzes AS (
 SELECT s.*, (SELECT MIN(e.ts) FROM events e WHERE e.source=:source
 AND e.learner_id=s.learner_id AND e.journey_id=s.journey_id
 AND e.name='quiz_submitted' AND e.ts>=s.started
 AND julianday(e.ts)-julianday(s.started)<=1) AS quiz FROM starts s
), feedback AS (
 SELECT q.*, (SELECT MIN(e.ts) FROM events e WHERE e.source=:source
 AND e.learner_id=q.learner_id AND e.journey_id=q.journey_id
 AND e.name='feedback_viewed' AND e.ts>=q.quiz
 AND julianday(e.ts)-julianday(q.started)<=1) AS feedback FROM quizzes q
), saved AS (
 SELECT f.*, (SELECT MIN(e.ts) FROM events e WHERE e.source=:source
 AND e.learner_id=f.learner_id AND e.journey_id=f.journey_id
 AND e.name='plan_saved' AND e.ts>=f.feedback
 AND julianday(e.ts)-julianday(f.started)<=1) AS saved FROM feedback f
)
SELECT l.variant, COUNT(*) AS started, COUNT(quiz) AS quiz,
 COUNT(feedback) AS feedback, COUNT(saved) AS saved
FROM saved JOIN learners l ON l.id=saved.learner_id GROUP BY l.variant;
