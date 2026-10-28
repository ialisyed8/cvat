# Definition of Done

Each line is ticked only with evidence: a number, a commit hash, or a path under `docs/evidence/`.

## Backend

- [x] New Django app `test` at `cvat/apps/test`, in `INSTALLED_APPS`, wired in `cvat/urls.py` like other apps
  (`35d3343a6`; `cvat/settings/base.py`, `cvat/urls.py`)
- [x] `GET /api/annotation-analytics/tasks/<task_id>/label-counts` returns per-label counts read from the database with one aggregate query
  (`35d3343a6`; the single SQL statement is in `docs/evidence/mo1_timing.txt`; total 1635 for task 1)
- [ ] Counts match `../coco-data/expected_counts.txt` for the 200-image task (comparison saved).
  The comparison is saved (`docs/evidence/count_verification.txt`), but the endpoint's shape counts
  match for only 48/80 labels: 1635 shapes vs 1460 COCO objects. Re-joining CVAT's grouped
  multi-part polygons matches 80/80, and 1327 + 292 + 16 = 1635 is derived from the source JSON.
  See "Not finished".
- [x] No login → 401 (curl output saved) (`docs/evidence/access_control.txt`, `docs/evidence/unit_tests.txt`)
- [x] Logged-in user without access to the task ("outsider") → 403 (curl output saved)
  (`docs/evidence/access_control.txt`; the engine's `/api/tasks/1` also gives 403)
- [x] Missing task → 404 (curl output saved) (`docs/evidence/access_control.txt`)
- [x] Admin → 200 (curl output saved) (`docs/evidence/access_control.txt`)
- [x] Access check reuses the existing `TaskPermission` / OPA task rules, with no new rules
  (`35d3343a6`, `cvat/apps/test/permissions.py`: a subclass that maps the action to `view:annotations`; no `rules/` folder)
- [x] `group_by=shape_type` returns counts per label and shape type; invalid value → 400
  (`597e52669`, `docs/evidence/group_by_shape_type.txt`: 80 rows, 16 masks; `group_by=color` → 400)
- [x] Docs state that only shapes are counted, not tracks or tags
  (`PLAN.md` "Skipped and why"; API description in `cvat/schema.yml`; UI text "Total: 1635 shapes (tracks and tags are not counted)")

## Frontend

- [x] cvat-core function calls the endpoint through the existing server proxy request mechanism
  (`51ea565cd`, `core.analytics.labelCounts` → `serverProxy.analytics.labelCounts` → Axios)
- [x] Route `/tasks/:id/analytics` renders a page, reachable from a link on the task page
  (`743389a35`; the route and "Actions → View analytics" already existed; `docs/evidence/ui_browser_check.txt`
  shows the click from `/tasks/1` landing on `/tasks/1/analytics`)
- [x] Counts are shown as a bar chart (`docs/evidence/ui_label_counts.png`: 75 bars, person = 571)
- [x] Empty task shows "No annotations yet" (`docs/evidence/ui_label_counts_empty.png`, task 2)
- [x] Failed request shows an error with a working Retry button
  (`docs/evidence/ui_label_counts_error.png`; the log shows 500 → Retry → 200 and 75 bars)
- [x] Page checked in the browser (screenshots or notes saved)
  (`docs/evidence/ui_browser_check.txt`, headless Chromium against the dev server)

## Objective

- [x] MO-1 measured: raw output of 5 runs, median, min–max, met or missed with the reason
  (`docs/evidence/mo1_timing.txt`, `OBJECTIVES.md`: median 907.5 ms, 841.8–1075.2 ms, **missed**:
  per-request PBKDF2 under basic auth; 65.0 ms with session auth)

## Process

- [x] First commit contains only the three docs (`807aa774b`, `docs/evidence/commits.txt`)
- [x] Small step-by-step commits with descriptive messages (`docs/evidence/commits.txt`)
- [x] Repo linters pass on the changed files (output saved)
  (`docs/evidence/lint.txt`: black, isort, bandit, pylint 10.00/10, typos, changelog check, ESLint
  0 errors and none on changed lines, tsc, stylelint)
- [x] No dead code, commented-out blocks, stray files or debug prints
  (`docs/evidence/hygiene.txt`: 0 matches; every added comment listed)
- [x] Decision record written in `PLAN.md` (numbers in `docs/evidence/decision_record.txt`)
- [x] `dev-test01` pushed and one PR opened into `main` of `ialisyed8/cvat`
  (PR URL in `docs/evidence/commits.txt`)

## Added during work

Not in the first checklist; added because the work happened.

- [x] WebSocket live updates (assignment item 8): `759345a09`, `28cf48c78`;
  `docs/evidence/ws_check.txt` (4401/4403/4404, foreign Origin → 4403, add/delete pushed, no pushes
  without changes); `docs/evidence/ui_live_check.txt` and `ui_live_update.png` (chart 571 → 572 in
  2.8 s without reload)
- [x] Reconnect (assignment item 9): `docs/evidence/ui_live_check.txt` and `ui_live_reconnecting.png`
  (server restarted → "Reconnecting" → "Live" again after 63.5 s, 7 socket attempts with backoff,
  later updates still arrive)
- [x] Django tests for the endpoint: `756be27e9`, `docs/evidence/unit_tests.txt` (6 tests OK; the
  mutation check fails as expected)
- [x] API schema and changelog kept in sync: `c9029920a`, `2caba7e0b`

## Not finished

- **COCO object counts.** The endpoint counts CVAT shapes, as planned ("LabeledShape … Count"). CVAT
  imports a multi-part COCO polygon as several shapes that share a `group`, so 32 of 80 labels show
  more shapes than `expected_counts.txt` has objects. Counting objects would mean also counting
  distinct `(frame, group)` pairs for grouped shapes. That was not done: CVAT users also use `group`
  for their own grouping, so it would change what the number means. The difference is fully
  explained in `docs/evidence/count_verification.txt`.
- **MO-1 is missed** as defined (basic auth). The fix is on the client side: use session or token
  auth, as cvat-ui does. The objective was not redefined.
- **WebSocket is polling-based:** each open page costs one authenticated request every 2 s on the
  server. There is no push from the annotation save path, because CVAT has no Channels or broker
  for that, and adding one was out of scope.
- **Organization tasks:** access was checked only for sandbox tasks (no organization). The code
  reuses the task OPA rules that already handle organizations, but no organization case was
  measured.
- **No UI unit or e2e test in the repo suite:** the UI was checked with throwaway Playwright scripts
  outside the repo (logs and screenshots in `docs/evidence/`).
