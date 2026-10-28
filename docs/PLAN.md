# Plan: annotation analytics for CVAT tasks

Base: CVAT `develop` at SHA `4a09e27ff869b7aebbfdb07b29c4a34904a0221d`, branch `dev-test01`,
PR into `main` of the fork `ialisyed8/cvat` (never `cvat-ai/cvat`).

Machine: Intel Core i7-6600U (2 cores / 4 threads), 16 GB host RAM, WSL2 limited to 10 GB / 4 CPUs,
Windows 10 Pro 22H2, Ubuntu on WSL2, Docker 29.8.0.

Data: first 200 images of COCO val2017 (sorted by file name) with their `instances_val2017.json`
annotations, all 80 categories, imported into one task as "COCO 1.0".

## Steps (in order, rough minutes)

| # | Step | Min |
|---|------|-----|
| 1 | Docs first: this plan, objective MO-1 with target, unticked Definition of Done | 20 |
| 2 | New Django app `cvat/apps/test`, registered in `INSTALLED_APPS`, wired in `cvat/urls.py` | 15 |
| 3 | `GET /api/annotation-analytics/tasks/<task_id>/label-counts`: one DB aggregate over `LabeledShape` filtered by `job__segment__task_id`, grouped by label name with `Count` | 30 |
| 4 | Access control by reusing `TaskPermission` (scope `view:annotations`, existing OPA rules); curl proofs 401 / 403 / 404 / 200 | 30 |
| 5 | Verify counts against `../coco-data/expected_counts.txt` | 15 |
| 6 | `group_by=shape_type` query parameter (counts per label and shape type) | 20 |
| 7 | cvat-core request function + cvat-ui page `/tasks/:id/analytics`, link from the task page | 60 |
| 8 | Bar chart (plain SVG), empty state "No annotations yet", error state with Retry; checked in the browser | 45 |
| 9 | MO-1 measurement: 5 timed curl runs after a discarded warm-up, median and spread | 15 |
| 10 | Linters on changed files, docs and DoD ticked with evidence, push, one PR into the fork's `main` | 40 |

Each step that works becomes its own commit. Raw command output goes to `docs/evidence/*.txt`.

## Skipped and why

- WebSocket live updates and reconnect (items 8–9 of the assignment): only attempted if items 1–7
  are done before 04:00; otherwise reported as "not reached".
- Tracks (`LabeledTrack`) and tags (`LabeledImage`) are not counted: the endpoint counts shapes
  only, which is what a COCO import creates. This is stated in the API description.
- No new OPA/Rego rules: access is decided by the existing task rules.
- No new database models, migrations or caching: counts are computed on request.

## Timebox

Feature work stops at 04:30 at the latest; the rest of the time goes to docs, evidence and the PR.
Deadline 08:07.
