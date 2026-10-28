# Objectives

## MO-1: label-counts response time

| ID | What is measured | How | Target | Conditions | Not included |
|----|------------------|-----|--------|------------|--------------|
| MO-1 | Server response time of `GET /api/annotation-analytics/tasks/<task_id>/label-counts` for the 200-image COCO task | `curl -s -o /dev/null -w '%{time_total}'` with admin basic auth against `http://localhost:8080`; first request discarded as warm-up; then 5 runs; report the median | Median of 5 runs ≤ 200 ms | Local Docker stack on the machine in `PLAN.md`, prebuilt `cvat/server:dev` image, no other load generated on purpose; plain count (no `group_by`) | Browser rendering time of the UI page; `group_by=shape_type` variant; cold start of the server process; behaviour on tasks much larger than 200 images |

Why 200 ms: the endpoint backs a page a person opens and waits for. About 200 ms is still felt as
"immediate" when the chart appears. The query itself is one indexed aggregate over roughly 1–2
thousand shapes, which should take a few milliseconds. Most of the budget is the fixed per-request
cost in CVAT: authentication, a call to the OPA service to check permissions, and DRF rendering. All
of this runs on a 2-core laptop inside WSL2. A tighter target (for example 50 ms) would mostly
measure that fixed cost on this hardware rather than the feature.

## Results (measured 2026-10-29, raw output in `docs/evidence/mo1_timing.txt`)

Code at commit `597e52669`, task 1 (200 images, 1635 shapes), 1 warm-up discarded, 5 runs.

As written (admin basic auth):

| Run | 1 | 2 | 3 | 4 | 5 |
|-----|---|---|---|---|---|
| `time_total` (s) | 0.841764 | 0.907520 | 0.946493 | 1.075170 | 0.899143 |

Median **907.5 ms**, spread 841.8–1075.2 ms. **MO-1 missed** (target ≤ 200 ms).

Honest reason: the time is spent authenticating, not counting. HTTP basic auth makes Django check
the password on every request: PBKDF2 with 1,000,000 iterations, which takes 955 ms per
`check_password()` call on this CPU. `GET /api/users/self` with basic auth, which runs no analytics
code, takes 0.90–1.05 s too. The aggregate query on its own takes 9.9–28.2 ms.

Same protocol with a session cookie, the way cvat-ui calls the endpoint after login:

| Run | 1 | 2 | 3 | 4 | 5 |
|-----|---|---|---|---|---|
| `time_total` (s) | 0.053658 | 0.052867 | 0.078532 | 0.065039 | 0.070024 |

Median **65.0 ms**, spread 52.9–78.5 ms, which would meet the 200 ms target. This is reported as
extra information only. MO-1 was defined with basic auth and it stays **missed**. The lesson for the
next objective is to name the auth method the real client uses (session or token) in "How".
