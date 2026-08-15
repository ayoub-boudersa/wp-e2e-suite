from pages.ui.base_page import BasePage

class DashboardPage(BasePage):
    ADMIN_MENU = "#adminmenu"
    LOGOUT_LINK = "#wp-admin-bar-logout > a"

    def open(self):
        self.navigate("/wp-admin/")

    def is_loaded(self):
        return self.is_visible(self.ADMIN_MENU)

    def logout(self):
        # The logout link lives in a hover-only admin bar flyout, which
        # Playwright won't reliably "click" headless without simulating
        # hover state. It's present in the DOM regardless, so we read its
        # href (contains the required nonce) and navigate to it directly.
        logout_url = self.page.locator(self.LOGOUT_LINK).get_attribute("href")
        self.page.goto(logout_url)
        self.page.wait_for_load_state("networkidle")