import os

class BasePage:
    def __init__(self, page):
        self.page = page
        self.base_url = os.getenv("WP_BASE_URL")

    def navigate(self, path=""):
        url = f"{self.base_url}{path}"
        self.page.goto(url)

    def is_visible(self, selector):
        return self.page.locator(selector).is_visible()

    def click(self, selector):
        self.page.locator(selector).click()

    def fill(self, selector, text=""):
        self.page.locator(selector).fill(text)

    def get_frame(self):
        return self.page.frame_locator("iframe")

    def fill_in_frame(self, selector, text):
        self.get_frame().locator(selector).fill(text)

    def click_in_frame(self, selector):
        self.get_frame().locator(selector).click()