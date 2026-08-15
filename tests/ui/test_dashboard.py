import pytest
from pages.ui.dashboard_page import DashboardPage

@pytest.mark.ui
@pytest.mark.smoke
def test_dashboard_loads_when_authenticated(authenticated_page):
    dashboard = DashboardPage(authenticated_page)
    dashboard.open()
    assert dashboard.is_loaded()


@pytest.mark.ui
@pytest.mark.smoke
def test_admin_menu_contains_core_wordpress_sections(authenticated_page):
    dashboard = DashboardPage(authenticated_page)
    dashboard.open()
    menu_text = authenticated_page.locator(dashboard.ADMIN_MENU).inner_text()

    for expected_section in ["Posts", "Pages", "Users", "Settings"]:
        assert expected_section in menu_text


@pytest.mark.ui
@pytest.mark.regression
def test_dashboard_redirects_unauthenticated_user(page):
    dashboard = DashboardPage(page)
    dashboard.open()
    assert not dashboard.is_loaded()
    assert "wp-login.php" in page.url
