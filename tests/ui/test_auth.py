import os
import pytest
from pages.ui.login_page import LoginPage
from pages.ui.dashboard_page import DashboardPage

ADMIN_USERNAME = os.getenv("WP_ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("WP_ADMIN_PASSWORD")


# ---------------------------------------------------------------------------
# P0 — Happy path
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.smoke
def test_login_page_loads(page):
    login = LoginPage(page)
    login.open()
    assert login.is_form_visible()


@pytest.mark.ui
@pytest.mark.smoke
def test_successful_login_redirects_to_dashboard(page):
    login = LoginPage(page)
    login.open()
    login.login(ADMIN_USERNAME, ADMIN_PASSWORD)

    dashboard = DashboardPage(page)
    assert dashboard.is_loaded()
    assert "wp-admin" in page.url


# ---------------------------------------------------------------------------
# P0 — Negative / error cases
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.smoke
def test_login_fails_with_wrong_password(page):
    login = LoginPage(page)
    login.open()
    login.login(ADMIN_USERNAME, "definitely-the-wrong-password")

    assert login.is_error_visible()
    assert not DashboardPage(page).is_loaded()


@pytest.mark.ui
@pytest.mark.smoke
def test_login_fails_with_unknown_username(page):
    login = LoginPage(page)
    login.open()
    login.login("no_such_user_exists", "SomePassword123!")

    assert login.is_error_visible()


@pytest.mark.ui
@pytest.mark.smoke
def test_login_fails_with_empty_username(page):
    login = LoginPage(page)
    login.open()
    login.fill(login.PASSWORD_INPUT, ADMIN_PASSWORD)
    login.submit_empty_form()

    assert login.is_error_visible()


@pytest.mark.ui
@pytest.mark.smoke
def test_login_fails_with_empty_password(page):
    login = LoginPage(page)
    login.open()
    login.fill(login.USERNAME_INPUT, ADMIN_USERNAME)
    login.submit_empty_form()

    assert login.is_error_visible()


@pytest.mark.ui
@pytest.mark.smoke
def test_login_fails_with_both_fields_empty(page):
    login = LoginPage(page)
    login.open()
    login.submit_empty_form()

    assert login.is_error_visible()


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.parametrize("malicious_input", [
    "' OR '1'='1",
    "admin'--",
    "<script>alert('xss')</script>",
    "\"; DROP TABLE wp_users; --",
])
def test_login_rejects_injection_attempts_safely(page, malicious_input):
    """Injection strings in the username field must be treated as literal,
    invalid usernames — no auth bypass, no script execution, no server error."""
    login = LoginPage(page)
    login.open()
    login.login(malicious_input, "irrelevant-password")

    # Must fail like any other bad login, not error out or authenticate.
    assert login.is_error_visible()
    assert not DashboardPage(page).is_loaded()

    # The payload must not have been reflected unescaped into the page
    # (a naive implementation could render it back inside the error message).
    page_content = page.content()
    assert "<script>alert('xss')</script>" not in page_content


# ---------------------------------------------------------------------------
# P0 — Access control (state)
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.smoke
def test_unauthenticated_user_redirected_from_dashboard_to_login(page):
    dashboard = DashboardPage(page)
    dashboard.open()

    login = LoginPage(page)
    assert login.is_form_visible()
    assert "wp-login.php" in page.url


# ---------------------------------------------------------------------------
# P1 — Equivalence classes
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.regression
def test_login_succeeds_with_email_as_username(page, api_credentials):
    """WordPress core allows logging in with the account's email address
    in place of the username."""
    from pages.api.users_api import UsersAPI
    api = UsersAPI(api_credentials["base_url"], api_credentials["auth"])
    current_user = api.get_current_user().json()
    admin_email = current_user.get("email")

    if not admin_email:
        pytest.skip("Admin email not exposed by /users/me with current auth scope")

    login = LoginPage(page)
    login.open()
    login.login(admin_email, ADMIN_PASSWORD)

    assert DashboardPage(page).is_loaded()


# ---------------------------------------------------------------------------
# P1 — State / sequence
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.regression
def test_already_authenticated_user_visiting_login_page_sees_notice_not_blank_form(authenticated_page):
    """An already-logged-in user hitting /wp-login.php should be told they're
    logged in (WP shows a login-info notice), not silently dropped into a
    fresh anonymous-looking form."""
    login = LoginPage(authenticated_page)
    login.open()

    assert login.is_already_logged_in_notice_visible() or "wp-admin" in authenticated_page.url


@pytest.mark.ui
@pytest.mark.regression
def test_back_button_after_logout_does_not_show_cached_dashboard(authenticated_page):
    dashboard = DashboardPage(authenticated_page)
    dashboard.open()
    assert dashboard.is_loaded()

    dashboard.logout()

    authenticated_page.go_back()
    authenticated_page.wait_for_load_state("networkidle")

    # wp-admin sends no-cache headers specifically to prevent this; the
    # back button must not resurrect an authenticated view.
    assert not dashboard.is_loaded()


@pytest.mark.ui
@pytest.mark.regression
def test_double_submit_login_does_not_error(page):
    """Rapid double-click on submit shouldn't produce a broken/duplicate
    session or an unhandled error page."""
    login = LoginPage(page)
    login.open()
    login.fill(login.USERNAME_INPUT, ADMIN_USERNAME)
    login.fill(login.PASSWORD_INPUT, ADMIN_PASSWORD)

    login.click(login.SUBMIT_BUTTON)
    login.click(login.SUBMIT_BUTTON)  # second click races the first
    page.wait_for_load_state("networkidle")

    assert DashboardPage(page).is_loaded()


# ---------------------------------------------------------------------------
# P1 — Combinatorics
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.regression
def test_remember_me_sets_persistent_cookie(page):
    login = LoginPage(page)
    login.open()
    login.login(ADMIN_USERNAME, ADMIN_PASSWORD, remember_me=True)

    cookies = page.context.cookies()
    auth_cookies = [c for c in cookies if c["name"].startswith("wordpress_logged_in_")]
    assert auth_cookies, "Expected a wordpress_logged_in_ cookie after login"

    # A "remembered" session cookie carries a real future expiry rather
    # than -1 (browser-session-only).
    assert all(c["expires"] > 0 for c in auth_cookies)


@pytest.mark.ui
@pytest.mark.regression
def test_remember_me_without_correct_password_does_not_set_auth_cookie(page):
    login = LoginPage(page)
    login.open()
    login.login(ADMIN_USERNAME, "still-the-wrong-password", remember_me=True)

    assert login.is_error_visible()
    cookies = page.context.cookies()
    auth_cookies = [c for c in cookies if c["name"].startswith("wordpress_logged_in_")]
    assert not auth_cookies


# ---------------------------------------------------------------------------
# P1 — Accessibility / UX
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.regression
def test_login_fields_have_password_manager_friendly_autocomplete(page):
    login = LoginPage(page)
    login.open()

    username_autocomplete = page.locator(login.USERNAME_INPUT).get_attribute("autocomplete")
    password_autocomplete = page.locator(login.PASSWORD_INPUT).get_attribute("autocomplete")

    assert username_autocomplete == "username"
    assert password_autocomplete == "current-password"


@pytest.mark.ui
@pytest.mark.regression
def test_tab_order_reaches_username_then_password_then_submit(page):
    """Doesn't assume adjacency (WP core adds a password show/hide toggle
    button in between) — only that the three key controls are reachable
    via Tab in the correct relative order."""
    login = LoginPage(page)
    login.open()

    focused_ids = []
    page.locator("body").click(position={"x": 0, "y": 0})
    for _ in range(8):
        page.keyboard.press("Tab")
        focused_id = page.evaluate("document.activeElement && document.activeElement.id")
        focused_ids.append(focused_id)

    def index_of(element_id):
        return next((i for i, fid in enumerate(focused_ids) if fid == element_id), None)

    username_index = index_of("user_login")
    password_index = index_of("user_pass")
    submit_index = index_of("wp-submit")

    assert username_index is not None, "username field never received focus via Tab"
    assert password_index is not None, "password field never received focus via Tab"
    assert submit_index is not None, "submit button never received focus via Tab"
    assert username_index < password_index < submit_index


@pytest.mark.ui
@pytest.mark.regression
def test_paste_into_password_field_is_not_blocked(page):
    login = LoginPage(page)
    login.open()

    page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    page.evaluate("navigator.clipboard.writeText('PastedPassword123!')")

    page.locator(login.PASSWORD_INPUT).click()
    page.keyboard.press("Control+v")

    value = page.locator(login.PASSWORD_INPUT).input_value()
    assert value == "PastedPassword123!"


# ---------------------------------------------------------------------------
# P2 — Boundary (long input robustness)
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.regression
def test_login_handles_very_long_username_gracefully(page):
    long_username = "a" * 500
    login = LoginPage(page)
    login.open()
    login.login(long_username, "irrelevant-password")

    # Should degrade to a normal failed-login error, not a 500 or a hang.
    assert login.is_error_visible()
