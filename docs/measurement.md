# Measurement contract

## Events

| Event | Server trigger | Properties | Deduplication |
|---|---|---|---|
| lesson_started | Valid lesson opened | lesson_id | UUID derived from learner + journey |
| quiz_submitted | Answers graded and saved atomically | lesson_id, score, total | Attempt UUID is immutable; conflicting retry rejected |
| feedback_viewed | Owning learner opens saved feedback | lesson_id | UUID derived from attempt |
| plan_saved | Owning learner saves plan after feedback | lesson_id | UUID derived from attempt |
| review_completed | Saved plan's quiz completed | lesson_id, score | Once per saved plan/attempt |

Events use server UTC timestamps. The server can confirm successful requests, not attention or cognition. `feedback_viewed` means the UI requested the feedback view; it does not prove the learner read it. Attempt and journey UUIDs remain stable during request retries. A newly started lesson is a new journey.

## Funnel

`sql/funnel.sql`: ordered same-learner, same-journey steps within 24 hours of first lesson start. The unit is **journeys**, so one learner can start several journeys. Equality of timestamps is permitted. Do not combine stages from separate sessions. The dashboard never merges synthetic and local events.

## Retention

`sql/retention.sql`: cohort is the UTC calendar date of a learner's first lesson start within the selected dataset. D1 counts a lesson start or revision completion on the next UTC calendar date. Eligible only once the full next-day window has elapsed. This is calendar-day retention, not a rolling 24–48h window and not necessarily the learner's local day. Same-day practice is not D1. Cookie loss or a new browser can create a new identity and bias retention.

## Assignment and interpretation

A random anonymous learner UUID is hashed to choose a stable control/recovery variant. This is an experiment mechanism, not a completed randomized trial. Synthetic fixtures have manually selected trajectories; their differences are illustrative.

Dashboard aggregate rates weight counts rather than averaging variant percentages. No p-values, uplift badges or real-world confidence claims are shown.

## Relay and consent

Only future local events produced while consent is enabled enter the outbox. Synthetic events cannot enter. Relay rereads consent and sends anonymous PostHog payloads with stable UUID and `$process_person_profile=false`. No answer arrays or contact information are forwarded. Success marks delivered, failure preserves the event and increments attempts. Delivery is at least once, not exactly once. A crash after remote acceptance can cause a retry; stable UUIDs are supplied for downstream deduplication, but live behavior is unverified.

Revocation drops pending events; it cannot recall data already accepted remotely. Do not run overlapping relay workers in this prototype. API and database state are local trusted-demo tools, not hardened public analytics infrastructure.
