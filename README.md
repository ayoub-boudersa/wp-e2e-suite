# wp-e2e-suite

End-to-end test suite for WordPress admin, combining **UI tests** (Playwright) and **REST API tests** (pytest + `requests`) in a single Page Object–driven framework.

## What it covers

- **UI (Playwright + pytest)** — login/auth, dashboard, pages, posts, and settings screens in `wp-admin`, driven through Page Object classes.
- **REST API (`requests` + `jsonschema`)** — posts, categories, and users endpoints, including auth/negative-path checks (missing auth, invalid app password) and response-schema validation.
- **Self-contained HTML report** on every run, with an automatic screenshot attached to the report for any failing UI test.

**82 tests** across 8 files:

| Area | File | Tests |
|---|---|---|
| API — Posts | `tests/api/test_posts_api.py` | 17 |
| API — Users | `tests/api/test_users_api.py` | 15 |
| API — Categories | `tests/api/test_categories_api.py` | 13 |
| UI — Auth | `tests/ui/test_auth.py` | 19 |
| UI — Posts | `tests/ui/test_posts.py` | 6 |
| UI — Pages | `tests/ui/test_pages.py` | 5 |
| UI — Settings | `tests/ui/test_settings.py` | 4 |
| UI — Dashboard | `tests/ui/test_dashboard.py` | 3 |

## Test design process

Every test file in this suite was built the same way, not by writing tests as they came to mind. Each feature (login, posts, pages, settings, and each REST resource) went through a fixed 7-step process before a single test was written:

1. Draw a 7-row table: Happy path / Equivalence classes / Boundary values / Negative & error cases / State & sequence / Combinatorics / Non-functional smell test.
2. Fill every row mechanically for the feature under test — no filtering yet, just generate cases.
3. Apply a priority filter to every case: **P0 / P1 / P2 / Skip**.
4. Write and run the P0 tests first, so the suite is useful from commit one.
5. Add the P1 tests.
6. Research domain-specific edge cases (e.g. WordPress-specific login/REST quirks) and fold in whatever the generated table missed.
7. Add P2 tests if there's time left.

The **7 techniques** behind row 2:

| Technique | What it means | Example in this repo |
|---|---|---|
| Happy path | The feature works as intended, once | `test_successful_login_redirects_to_dashboard` |
| Equivalence partitioning | One representative per input class | `test_create_post_with_each_valid_status`, `test_create_user_with_each_standard_role` |
| Boundary value analysis | min / max / min-1 / max+1 / empty / at-limit | `test_create_user_with_username_at_column_length_boundary`, `test_login_handles_very_long_username_gracefully` |
| Negative / error cases | Wrong input, missing field, wrong type, injection | `test_login_rejects_injection_attempts_safely`, `test_script_tag_in_title_is_not_reflected_unescaped` |
| State / sequence | Does order matter? | `test_back_button_after_logout_does_not_show_cached_dashboard`, `test_double_submit_login_does_not_error`, `test_deleted_post_returns_404_on_subsequent_get` |
| Combinatorics | Two conditions interacting | `test_remember_me_without_correct_password_does_not_set_auth_cookie`, `test_draft_post_not_visible_to_unauthenticated_request` |
| Non-functional smell test | Slow network, concurrency, refresh mid-action | flagged during design; explicit coverage tracked as a P2/backlog item (see [Known gaps](#known-gaps)) |

After generating each feature's own table, I diffed it against 2–3 published checklists (Ministry of Testing–style login/CRUD checklists) rather than starting from them. That diffing step is what surfaced the misses below — reading a checklist first doesn't force the same recall, generating your own list and then comparing does.

What the diff caught that my own table missed, now covered in `test_auth.py`:

- Tab order through username → password → submit (`test_tab_order_reaches_username_then_password_then_submit`)
- Password-manager-friendly `autocomplete` attributes (`test_login_fields_have_password_manager_friendly_autocomplete`)
- Paste-into-password-field not being blocked (`test_paste_into_password_field_is_not_blocked`)

### Priority tiers, applied

| Priority | Rule | Runs | Roughly in this suite |
|---|---|---|---|
| **P0** | Happy path + auth failures + critical negative cases | Every commit (`pytest -m smoke`) | ~39 tests — login success/failure, unauthenticated access, 401s, required-field validation, core CRUD happy paths |
| **P1** | Equivalence classes + key boundaries + state sequences | Before every release (`pytest -m regression`) | ~32 tests — role/status equivalence classes, logout/back-button/double-submit sequences, remember-me combinations, duplicate-identity checks |
| **P2** | Combinatorics + edge boundaries + non-functional | Weekly, or when the area changes | ~5 tests — very long titles/usernames, column-length boundaries |
| **Skip** | Duplicates + cases implicitly covered by others | Not written | e.g. re-testing "empty password" separately from "both fields empty" once the latter is covered |

Every test file mirrors this with inline section headers, e.g.:

```python
# ---------------------------------------------------------------------------
# P0 — Negative / auth
# ---------------------------------------------------------------------------
def test_create_post_without_auth_returns_401(unauthenticated_api_credentials):
    ...

# ---------------------------------------------------------------------------
# P1 — Combinatorics (status x auth)
# ---------------------------------------------------------------------------
def test_draft_post_not_visible_to_unauthenticated_request(post_factory, unauthenticated_api_credentials):
    ...
```

so the priority of any given test — and the technique it exercises — is visible without having to run it.

## Project structure

```
.
├── conftest.py              # fixtures: browser/page, authenticated_page,
│                             #   api_credentials, post/category/user factories,
│                             #   screenshot-on-failure hook
├── pytest.ini                # test paths, HTML report output, custom markers
├── requirements.txt
├── .env.example               # copy to .env and fill in your test-site credentials
├── pages/
│   ├── ui/                    # Page Object classes (login, dashboard, pages, posts, settings)
│   └── api/                   # thin REST clients (base + posts/categories/users)
├── schemas/                    # JSON Schemas used to validate API responses
└── tests/
    ├── ui/                     # Playwright-driven UI tests
    └── api/                     # pytest + requests API tests
```

### Design notes

- **Page Object Model** — every UI screen and REST resource is wrapped in a class (`pages/ui`, `pages/api`), so selectors and endpoints live in one place and tests stay focused on behavior.
- **Factory fixtures with guaranteed cleanup** — `post_factory`, `category_factory`, and `user_factory` create records via the API and delete them in teardown, even if the test fails partway through, so failed assertions don't leak data on the target site.
- **Auth coverage** — API tests include no-auth and wrong-app-password fixtures (`unauthenticated_api_credentials`, `invalid_api_credentials`) to verify the API correctly rejects both cases.
- **Screenshot-on-failure** — a `pytest_runtest_makereport` hook in `conftest.py` grabs a screenshot from the active Playwright page whenever a UI test fails and embeds it in the HTML report. Filenames are sanitized so test IDs built from `parametrize` (including ones containing special characters) can't break the report.
- **Markers** — tests are tagged `smoke` (quick, critical — run before every commit), `regression` (full suite — run before release), `ui`, and `api`, so you can run subsets as needed.

## Requirements

- Python 3.9+
- A WordPress site you're allowed to test against (a local/staging install is strongly recommended — these tests create, modify, and delete real content)
- Admin credentials and a WordPress [Application Password](https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/) for that admin user

## Setup

1. **Clone and install dependencies**

   ```bash
   git clone https://github.com/ayoub-boudersa/wp-e2e-suite.git
   cd wp-e2e-suite
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configure environment variables**

   Copy the example file and fill in your test site's details:

   ```bash
   cp .env.example .env
   ```

   ```ini
   WP_BASE_URL=https://your-wordpress-site.test
   WP_API_URL=https://your-wordpress-site.test/wp-json/wp/v2
   WP_ADMIN_USERNAME=admin
   WP_ADMIN_PASSWORD=your-wp-admin-password
   WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
   ```

   - `WP_ADMIN_USERNAME` / `WP_ADMIN_PASSWORD` — used to log in through the `wp-admin` UI.
   - `WP_APP_PASSWORD` — used to authenticate REST API requests (generate one under **Users → Profile → Application Passwords**).

## Running the tests

Run the full suite:

```bash
pytest
```

Run only UI or only API tests:

```bash
pytest -m ui
pytest -m api
```

Run just the smoke suite (fast, pre-commit) or the full regression suite:

```bash
pytest -m smoke
pytest -m regression
```

Run a single file or test:

```bash
pytest tests/ui/test_auth.py
pytest tests/api/test_posts_api.py::test_create_and_delete_post
```

## Test reports

Every run produces a self-contained HTML report at `reports/report.html` (configured in `pytest.ini`). Failing UI tests automatically get a screenshot embedded in the report. Screenshots, reports, and traces are git-ignored and regenerated on each run.

## Known gaps

Called out honestly rather than silently skipped:

- **Non-functional smell tests** (slow network, concurrent requests, refresh mid-action) were identified during test design but aren't automated yet — they need infrastructure (network throttling, concurrent runners) beyond this suite's current scope.
- **CAPS LOCK warning** on the login form was flagged in the checklist diff but not implemented — WordPress core doesn't render this by default, so it was marked Skip for this target rather than a false negative.

## Notes

- This suite is designed to run against a **local or staging** WordPress installation — it creates, edits, and deletes posts, categories, and users. Do not point it at a production site.
- There is currently no CI workflow in this repo; the suite is intended to be run locally against an installed WordPress environment.
