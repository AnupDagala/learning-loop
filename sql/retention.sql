-- D1 = an active event on the next UTC calendar day after first lesson start.
-- Exclude cohorts whose full D1 has not elapsed at :as_of (no immature zeroes).
WITH firsts AS (
 SELECT learner_id, date(MIN(ts)) AS cohort FROM events
 WHERE source=:source AND name='lesson_started' GROUP BY learner_id
), eligible AS (
 SELECT * FROM firsts WHERE date(cohort,'+2 days')<=date(:as_of)
)
SELECT cohort, l.variant, COUNT(*) AS eligible,
 SUM(EXISTS(SELECT 1 FROM events e WHERE e.learner_id=f.learner_id
 AND e.source=:source AND e.name IN ('lesson_started','review_completed')
 AND date(e.ts)=date(f.cohort,'+1 day'))) AS returned
FROM eligible f JOIN learners l ON l.id=f.learner_id
GROUP BY cohort,l.variant ORDER BY cohort,l.variant;
