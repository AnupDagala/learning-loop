# Learning Loop

**A small learning product that makes the step after a wrong answer concrete—and makes its effectiveness measurable.**

Independent proof of work for an early-career product role. Built with AI-assisted development; not an AI-generated tutoring service, not affiliated with SuperKalam, and not a claim that their product needs this feature.



## Try it in two minutes

Requires Python 3.11+; **no application dependencies, API keys or paid services**.

```sh
python server.py --seed
python server.py
```

Open **http://127.0.0.1:8000**. Start a lesson, deliberately miss a question, open feedback, save tomorrow's revision, and switch to **Product insights**. Choose **This instance's activity** to see your actual events separately from the demonstration.

On Windows, use `py` instead of `python` if necessary. Run from this repository's root. `--seed` exits after creating the fixture; it does not start the server. Progress survives server restarts because it is in SQLite. The server binds to localhost.

## What works

- Two original mini lessons, six server-graded questions, named knowledge gaps and source references.
- Standard versus focused recovery feedback, with stable per-learner random assignment.
- Saved return plans, repeat practice and restored feedback after reload.
- Ordered, same-journey activation funnel with a 24-hour window; next UTC calendar-day retention with mature cohorts only.
- Distinct synthetic and local datasets. Synthetic charts demonstrate the system, not measured uplift.
- SQLite event store and opt-in durable PostHog outbox; retries preserve event UUIDs.
- Responsive UI, keyboard-accessible forms, server ownership checks, atomic grading and duplicate protection.

## The product argument

The hypothesis is that a learner may understand an answer explanation yet still lack a clear next action. The treatment pairs each mistake with a specific distinction to revisit. This is **unvalidated**, and competing explanations include poor question quality, fatigue, motivation, or unclear goals.

Read the [product case study](docs/product-case-study.md), [research plan](docs/research-plan.md), [measurement contract](docs/measurement.md), [tradeoffs](docs/tradeoffs.md), and [verification report](docs/verification.md).



## Tests

Verified here: **38 backend/HTTP tests and 13 frontend/API smoke checks**. GitHub Actions also passed **23 Chromium browser checks** on desktop and mobile. [Verified CI run](https://github.com/AnupDagala/learning-loop/actions/runs/37316791557) at commit `c23c6bf`. Live PostHog ingestion remains unverified.

```sh
python -m unittest discover -s tests -v
python -m compileall -q content.py engine.py server.py telemetry.py
```

Browser checks (Node 22+):

```sh
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install chromium
python server.py --db data/browser.sqlite3 --seed
python server.py --db data/browser.sqlite3 --port 8765
# In another terminal:
node tests/browser.cjs
```

With the server ready, `node tests/frontend-smoke.cjs` runs the dependency-free JavaScript/API smoke checks (minimal DOM adapter; not a browser).

`TEST_URL` can override the URL. `RECORD_VIDEO=1` enables recording. GitHub Actions defines both test jobs; backend and browser jobs passed at `c23c6bf`.

## Optional PostHog relay

Events are always local by default. Opt in under **Analytics preferences**, then export your PostHog **project token** and approved ingestion host, and run:

```sh
python server.py --flush-posthog
```

Configure `POSTHOG_PROJECT_TOKEN` and optional `POSTHOG_HOST` (`https://us.i.posthog.com` or `https://eu.i.posthog.com`). The command sends up to 100 queued events, with a five-second timeout per request. It runs explicitly rather than on every learner action. `.env.example` documents variables; `.env` is **not automatically loaded**. No personal API key is required. Each run rechecks consent. Unsent items remain durable after failure. Revoking consent removes pending events for that learner. Already delivered data must be deleted in PostHog itself.

The relay payload and retries were tested with mocked transport. **Live PostHog ingestion is unverified.** To configure a PostHog funnel, use `lesson_started → quiz_submitted → feedback_viewed → plan_saved`, group/filter by `variant`, and match `journey_id` across steps. Use `source=local`; match the 24-hour window. Local retention uses UTC calendar days; configure equivalent timezone/definition before comparing to PostHog.

References: [PostHog event ingestion](https://posthog.com/docs/getting-started/install), [anonymous events](https://posthog.com/docs/data/anonymous-vs-identified-events).

## Boundaries

No learner interviews have been conducted, no production traffic is included, no measured retention improvement is claimed, and no live LLM is called. This is a localhost portfolio demo, **not a production deployment**: public hosting needs authentication, secure cookies/TLS, rate limits, lifecycle management, a protected analytics dashboard and data deletion/export controls. The anonymous cookie is a bearer credential; do not share it. Reset local progress by stopping the server and deleting the chosen demo database.

MIT licensed. Original educational content is intentionally limited; verify it before using it for instruction.
