from pages.ui.base_page import BasePage

class LoginPage(BasePage):
    USERNAME_INPUT = "#user_login"
    PASSWORD_INPUT = "#user_pass"
    SUBMIT_BUTTON = "#wp-submit"
    LOGIN_FORM = "#loginform"
    ERROR_MESSAGE = "#login_error"
    REMEMBER_ME_CHECKBOX = "#rememberme"
    ALREADY_LOGGED_IN_NOTICE = ".login-info"

    def open(self):
        self.navigate("/wp-login.php")

    def is_form_visible(self):
        return self.is_visible(self.LOGIN_FORM)

    def login(self, username, password, remember_me=False):
        self.fill(self.USERNAME_INPUT, username)
        self.fill(self.PASSWORD_INPUT, password)
        if remember_me:
            self.click(self.REMEMBER_ME_CHECKBOX)
        self.click(self.SUBMIT_BUTTON)
        self.page.wait_for_load_state("networkidle")

    def submit_empty_form(self):
        self.click(self.SUBMIT_BUTTON)
        self.page.wait_for_load_state("networkidle")

    def is_error_visible(self):
        return self.is_visible(self.ERROR_MESSAGE)

    def get_error_text(self):
        return self.page.locator(self.ERROR_MESSAGE).inner_text()

    def is_already_logged_in_notice_visible(self):
        return self.is_visible(self.ALREADY_LOGGED_IN_NOTICE)