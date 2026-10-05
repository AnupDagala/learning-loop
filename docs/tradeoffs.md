# Decisions and tradeoffs

| Decision | Why | Cost / next step |
|---|---|---|
| Python standard library + SQLite | Zero-install application runtime and inspectable SQL | Development server; public deployment needs a production stack |
| Vanilla HTML/CSS/JS | Small surface, easy browser inspection, fast loading | Manual rendering; larger product would benefit from component structure |
| Fixed explanations instead of live LLM | Source-linked, deterministic feedback and offline demo | Limited content; does not demonstrate live model quality |
| Two small lessons | Enough to exercise product flow and analytics | Not a full preparation product; editorial review and transfer questions needed |
| Stable anonymous variant | Experiment machinery without accounts | Cookie resets and cross-device users bias analysis |
| Durable local events first | Learning does not wait for analytics network | Explicit relay; not a real-time PostHog dashboard |
| Consent-gated pseudonymous telemetry | Minimal data, no contact information or raw answers forwarded | Requires consent UI and remote deletion procedures |
| Same-journey funnel and mature calendar cohorts | Avoids false completion and immature retention zeroes | Must align definitions when comparing to third-party analytics |
| No notifications | Isolates feedback-plan hypothesis | Saved plans may not cause returns; discovery could favor reminders |

## What I would explain in an interview

Why plan-save is a weak proxy for learning; why the synthetic treatment cannot establish uplift; why repeated identical questions test recognition; how mature-cohort filtering changes retention; how server-side deduplication protects metrics during retries; and why adding a generic LLM before discovery would enlarge the scope without answering the core product question.

## Release boundaries

Browser activity is not authenticated identity. Same-origin checks protect common browser cross-site requests but are not a complete CSRF/security design. There are no public rate limits, deletion API, account model or production hosting. Session creation and dashboard are intentionally local. The PostHog relay is manually invoked with a bounded batch and no exponential scheduler. Process restarts retain SQLite state, but backups and multi-worker operations need a separate design.
