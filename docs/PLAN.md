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

## Changes during work (2026-10-29)

Added during the work. The plan above is unchanged.

- **00:50–01:06, setup:** building CVAT from source (`docker-compose.dev.yml --build`) crashed WSL.
  At that time WSL had 2 vCPUs and 5.8 GB. The first try also failed earlier, because the Docker
  Desktop credential helper timed out through WSL interop. Evidence:
  `docs/evidence/source_build_attempt.txt`. WSL was then raised to 10 GB / 4 CPUs and the approach
  changed:
  - prebuilt `cvat/server:dev` images, with only the changed backend files bind-mounted from the
    repo through a compose override kept outside the repo. The image's code matches
    `4a09e27ff` for every file compared (`docs/evidence/environment.txt`);
  - the cvat-ui webpack dev server runs natively in WSL against `localhost:8080`;
  - 200 COCO images instead of more, downloaded one by one rather than the whole `val2017.zip`.
- **01:44, counts:** CVAT's COCO import turns a COCO object whose segmentation has several polygons
  into several polygon shapes that share a `group` id. The endpoint counts shapes: 1635 for
  1460 COCO objects. Re-joining grouped shapes matches the COCO counts for 80/80 categories, so the
  data is correct and the gap is explained (`docs/evidence/count_verification.txt`). The endpoint
  keeps counting shapes, as planned, and the UI says "shapes".
- **01:50, MO-1:** missed under basic auth (median 907.5 ms), because Django's per-request PBKDF2
  password check takes 955 ms. With session auth, as cvat-ui uses, the median is 65.0 ms.
  Details in `OBJECTIVES.md`.
- **02:12, UI:** `/tasks/:id/analytics` and the task page's "Actions → View analytics" link already
  existed in CVAT. For tasks, they showed only a paid-feature placeholder. The chart was added to that
  page's default content instead of adding a second route with the same path.
- **02:13–02:42, WebSocket:** items 1–7 were done at 02:13, before the 04:00 cut-off, so WebSocket
  live updates and reconnect were built. CVAT has no Django Channels, so the socket is a small ASGI
  router in `cvat/apps/test/live.py`, hooked in `cvat/asgi.py`. `asgi.py` was added to the mounted
  files. The dev-server proxy got a WebSocket entry that keeps the browser's Host, so the backend's
  Origin check works in development.
- **Actual timeline** (commit times): docs 01:26, endpoint 01:44, grouping 01:48, MO-1 01:50,
  core + UI 02:12, schema/changelog 02:13, WebSocket + reconnect 02:42, evidence 02:45.

## Decision record

**Approach taken:** count on the server with one aggregate query, in a new `test` app endpoint:
`LabeledShape` filtered by `job__segment__task_id`, grouped by label name, `COUNT(id)`. Access is
decided by the existing `TaskPermission` OPA rules, mapping the action to `view:annotations`.

**Approach rejected:** count in the browser from the existing `GET /api/tasks/<id>/annotations`,
which needs no backend change. The engine's permission checks would have applied automatically.

**Why:** for this 200-image task, the existing annotations endpoint returns 867,994 bytes in
0.42–0.65 s per load. The new endpoint returns 2,311 bytes in 0.06–0.23 s (session auth, 5 runs
each, `docs/evidence/decision_record.txt`). Both numbers grow with the task: the annotations payload
grows with every shape, while the aggregate's response grows only with the number of labels. Live
updates would multiply the difference, since each push would re-download all annotations.

**What rejecting it cost:**

- New backend surface to own and review: the `test` app (7 Python files), a URL include, an
  `INSTALLED_APPS` entry, an OpenAPI schema update and a `cvat/asgi.py` hook. In total, 25 files
  and 733 added lines in code, schema and changelog (`git diff --stat` in the same evidence file).
- A permission mapping that has to stay in sync with the task scopes
  (`AnnotationAnalyticsPermission`).
- The counts mean "shapes", not "objects", and that needs explaining (multi-part COCO polygons).
  The client-side approach would have had the same issue, but it could have grouped shapes in the
  browser without a server change.
- The WebSocket re-checks every 2 s per open page, each time with a full auth + OPA permission
  check and the aggregate query. That is about the cost of one HTTP call to the endpoint (median
  65.0 ms with session auth, `docs/evidence/mo1_timing.txt`).
