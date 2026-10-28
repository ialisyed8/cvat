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

## Results

To be filled in from `docs/evidence/` after measuring.
