# Verification report — 2026-10-05

## Verified locally

- **38 Python domain and HTTP tests passed.** Coverage includes concurrent idempotent submissions, invalid inputs, session ownership, payload limits, same-origin checks, cross-journey/out-of-order funnel exclusion, 24-hour funnel limits, mature D1 cohorts, synthetic isolation, and mocked PostHog success/failure/consent behavior.
- **13 frontend/API smoke checks passed.** Shipped JavaScript ran in a Node VM with a minimal DOM adapter against the real local HTTP server. It bootstrapped lessons, collected answers, rendered server feedback, saved/reopened a plan, completed revision, switched datasets, and excluded immature retention. This is not browser verification.
- Python compilation and JavaScript syntax checks passed.
- Versioned SQL executed against a synthetic cohort of 120 learners: 54 plan saves and 30 D1 returns, intentionally constructed.

Evidence: `docs/evidence/backend-tests.txt`, `frontend-smoke.txt`, `analytics-snapshot.json`.

## Unverified

- Actual browser layout, keyboard/accessibility behavior and CSP execution. `tests/browser.cjs` supplies the complete browser harness; execution was blocked because no Chromium binary was installed and download attempts did not return a valid archive. No browser screenshots or video are claimed.
- Live PostHog ingestion/deduplication, external model calls, public deployment and remote CI execution.
- Interviews, actual learner behavior, retention improvement, transfer learning gains or demand.

## Reproduce

Run `python -m unittest discover -s tests -v`. Start a seeded server at port 8765 and run `node tests/frontend-smoke.cjs`. See README for Playwright setup and `tests/browser.cjs`. Use a fresh database for browser checks: the script expects no mature local retention cohorts.

The GitHub workflow is included but publication/remote status must be confirmed separately. No secrets or local SQLite database are included in the source package.
