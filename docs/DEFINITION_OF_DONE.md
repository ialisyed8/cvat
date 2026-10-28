# Definition of Done

Each line is ticked only with evidence: a number, a commit hash, or a path under `docs/evidence/`.

## Backend

- [ ] New Django app `test` at `cvat/apps/test`, in `INSTALLED_APPS`, wired in `cvat/urls.py` like other apps
- [ ] `GET /api/annotation-analytics/tasks/<task_id>/label-counts` returns per-label counts read from the database with one aggregate query
- [ ] Counts match `../coco-data/expected_counts.txt` for the 200-image task (comparison saved)
- [ ] No login → 401 (curl output saved)
- [ ] Logged-in user without access to the task ("outsider") → 403 (curl output saved)
- [ ] Missing task → 404 (curl output saved)
- [ ] Admin → 200 (curl output saved)
- [ ] Access check reuses the existing `TaskPermission` / OPA task rules, with no new rules
- [ ] `group_by=shape_type` returns counts per label and shape type; invalid value → 400
- [ ] Docs state that only shapes are counted, not tracks or tags

## Frontend

- [ ] cvat-core function calls the endpoint through the existing server proxy request mechanism
- [ ] Route `/tasks/:id/analytics` renders a page, reachable from a link on the task page
- [ ] Counts are shown as a bar chart
- [ ] Empty task shows "No annotations yet"
- [ ] Failed request shows an error with a working Retry button
- [ ] Page checked in the browser (screenshots or notes saved)

## Objective

- [ ] MO-1 measured: raw output of 5 runs, median, min–max, met or missed with the reason

## Process

- [ ] First commit contains only the three docs
- [ ] Small step-by-step commits with descriptive messages
- [ ] Repo linters pass on the changed files (output saved)
- [ ] No dead code, commented-out blocks, stray files or debug prints
- [ ] Decision record written in `PLAN.md`
- [ ] `dev-test01` pushed and one PR opened into `main` of `ialisyed8/cvat`

## Not finished

To be filled in at the end.
