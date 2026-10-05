# Verification report — 2026-10-05

## Verified locally

- **38 Python domain and HTTP tests passed.** Coverage includes concurrent idempotent submissions, invalid inputs, session ownership, payload limits, same-origin checks, cross-journey/out-of-order funnel exclusion, 24-hour funnel limits, mature D1 cohorts, synthetic isolation, and mocked PostHog success/failure/consent behavior.
- **13 frontend/API smoke checks passed.** Shipped JavaScript ran in a Node VM with a minimal DOM adapter against the real local HTTP server. It bootstrapped lessons, collected answers, rendered server feedback, saved/reopened a plan, completed revision, switched datasets, and excluded immature retention. This is not browser verification.
- Python compilation and JavaScript syntax checks passed.
- Versioned SQL executed against a synthetic cohort of 120 learners: 54 plan saves and 30 D1 returns, intentionally constructed.

Evidence: `docs/evidence/backend-tests.txt`, `frontend-smoke.txt`, `analytics-snapshot.json`.

## Verified in GitHub Actions

Commit `c23c6bf` passed both jobs: 38 backend tests and **23 Chromium browser checks** covering desktop/mobile learning, server grading, saved plans, revision, dataset separation, consent save/revocation, mobile overflow and absence of browser/CSP errors. The consent checks wait for the completed save rather than racing the request.

[Verified run](https://github.com/AnupDagala/learning-loop/actions/runs/37316791557). Screenshots and browser-results JSON are available in its browser-evidence artifact.

## Unverified

- A full accessibility audit and visual review of every possible state. Chromium could not be downloaded locally; the browser harness was instead executed successfully in GitHub Actions. No video is claimed.
- Live PostHog ingestion/deduplication, external model calls and public application deployment.
- Interviews, actual learner behavior, retention improvement, transfer learning gains or demand.

## Reproduce

Run `python -m unittest discover -s tests -v`. Start a seeded server at port 8765 and run `node tests/frontend-smoke.cjs`. See README for Playwright setup and `tests/browser.cjs`. Use a fresh database for browser checks: the script expects no mature local retention cohorts.

The source is published publicly; the linked CI run verifies the application and browser harness before this documentation update. No secrets or local SQLite database are included in the source package.
