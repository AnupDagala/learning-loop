# Learning Loop: from answer feedback to a return session

## Problem hypothesis

A learner finishes a quiz, sees the right answer, and leaves without knowing what to revisit. The opportunity to investigate is the transition from explanation to an actionable return plan. This is a hypothesis about learning workflows, not a diagnosed SuperKalam issue.

The published SuperKalam Founding Product Manager role focuses on activation, engagement, retention and conversion, plus SQL, PostHog, UX, AI-assisted building and product judgment. This prototype demonstrates a narrow measurable journey relevant to that scope. Source: https://www.ycombinator.com/companies/superkalam/jobs/W6Eoh7m-founding-product-manager (reviewed 2026-10-05).

## Intended user and job

A competitive-exam learner with little time who wants to distinguish similar ideas, understand mistakes and leave with one manageable next step. Research must establish whether this need is common and consequential.

## MVP and prioritization

| Candidate | Decision | Reason |
|---|---|---|
| Explain mistakes and identify the exact concept | Build | Directly addresses the hypothesized decision gap |
| Save a short next-session plan | Build | Turns feedback into an observable next action |
| Funnel and mature D1 cohorts | Build | Measures the journey without conflating immature cohorts with churn |
| Generic generative chat | Defer | Adds hallucination and evaluation burden before discovery validates the need |
| Push notifications | Defer | Would confound return intent with reminder effects; no notification infrastructure |
| Full exam syllabus and payments | Defer | Does not help validate the narrow learning loop |

## Delivered journey

Read a three-card lesson → answer three questions → receive server-graded feedback → save a next-session plan → return for practice. Control shows standard explanations with a generic return prompt. Recovery adds the relevant lesson excerpt and named revision targets. Both have the same quiz and answer correctness.

## Measurement and decision

Primary operational metric: proportion of started journeys that save a plan through the ordered 24-hour funnel. Secondary: next UTC calendar-day return among fully observed cohorts. A meaningful experiment also needs actual revision completion and comprehension guardrails: a plan save alone is not a learning outcome.

The synthetic dataset has 60 learners per variant, with constructed saves of 20 and 34, and constructed D1 returns of 12 and 18. These values are fixtures. They cannot support a causal claim, a confidence interval about real users or a hiring claim of improved retention.

Before a live test: complete discovery, agree experiment eligibility and success threshold, calculate a sample size for a meaningful effect, set a duration and stopping rule, check assignment balance and instrumentation, and assess novelty and reminder effects. Do not stop early because the dashboard looks favorable.

## What this demonstrates

A vague idea was reduced to a shippable product decision, implemented with a coherent UX, and instrumented with explicit SQL contracts and failure tests. The application story is ownership, product reasoning and verifiable engineering—not validated market demand or production impact.

## Honest resume wording (after publication)

Built Learning Loop, a study-feedback prototype that converts quiz mistakes into saved revision plans; implemented stable experiment assignment, SQL activation/retention analysis, and a consent-gated PostHog event relay to make the proposed UX improvement measurable.

Avoid claiming increased retention, conducted interviews, production adoption or live PostHog verification.
