from pages.ui.base_page import BasePage

class SettingsPage(BasePage):
    SITE_TITLE_INPUT = "#blogname"
    TAGLINE_INPUT = "#blogdescription"
    TIMEZONE_SELECT = "#timezone_string"
    SAVE_BUTTON = "#submit"
    SUCCESS_NOTICE = "#setting-error-settings_updated"

    def open(self):
        self.navigate("/wp-admin/options-general.php")

    def get_site_title(self):
        return self.page.locator(self.SITE_TITLE_INPUT).input_value()

    def set_site_title(self, title):
        self.fill(self.SITE_TITLE_INPUT, title)

    def get_tagline(self):
        return self.page.locator(self.TAGLINE_INPUT).input_value()

    def set_tagline(self, tagline):
        self.fill(self.TAGLINE_INPUT, tagline)

    def save(self):
        self.click(self.SAVE_BUTTON)
        self.page.wait_for_load_state("networkidle")

    def is_save_confirmed(self):
        return self.is_visible(self.SUCCESS_NOTICE)
