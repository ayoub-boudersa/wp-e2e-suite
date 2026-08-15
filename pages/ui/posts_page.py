from pages.ui.base_page import BasePage

class PostsPage(BasePage):
    POST_ROW = "#the-list tr"
    ADD_NEW_BUTTON = "a.page-title-action"
    TITLE_INPUT = "[aria-label='Add title']"
    CONTENT_AREA = "[aria-label='Add default block']"
    PUBLISH_BUTTON = ".editor-post-publish-button__button"
    CONFIRM_PUBLISH_BUTTON = ".editor-post-publish-panel__header-publish-button button"
    PUBLISHED_MESSAGE = ".components-snackbar"
    SEARCH_INPUT = "#post-search-input"
    SEARCH_SUBMIT = "#search-submit"

    def open(self):
        self.navigate("/wp-admin/edit.php")

    def open_new_post(self):
        self.navigate("/wp-admin/post-new.php")

    def get_post_count(self):
        return self.page.locator(self.POST_ROW).count()

    def create_post(self, title, content):
        self.open_new_post()
        self.fill_in_frame(self.TITLE_INPUT, title)
        self.click_in_frame(self.CONTENT_AREA)
        self.page.keyboard.type(content)
        self.click(self.PUBLISH_BUTTON)
        self.click(self.CONFIRM_PUBLISH_BUTTON)
        self.page.locator(self.PUBLISHED_MESSAGE).wait_for(timeout=10000)

    def is_post_published(self):
        return self.is_visible(self.PUBLISHED_MESSAGE)

    def search(self, query):
        self.open()
        self.fill(self.SEARCH_INPUT, query)
        self.click(self.SEARCH_SUBMIT)
        self.page.wait_for_load_state("networkidle")

    def is_post_row_visible(self, post_id):
        return self.page.locator(f"#post-{post_id}").count() > 0

    def trash_post(self, post_id):
        # Same rationale as DashboardPage.logout: the row-action "Trash"
        # link only becomes visually reachable on hover, so we read its
        # href (it carries the required nonce) and navigate directly
        # instead of simulating a hover in headless Chromium.
        self.open()
        trash_link = self.page.locator(f"#post-{post_id} .row-actions .trash > a")
        href = trash_link.get_attribute("href")
        self.page.goto(href)
        self.page.wait_for_load_state("networkidle")