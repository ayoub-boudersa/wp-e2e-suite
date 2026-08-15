import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_PASSWORD = os.getenv("WP_ADMIN_PASSWORD")
ADMIN_USERNAME = os.getenv("WP_ADMIN_USERNAME")
BASE_URL = os.getenv("WP_BASE_URL")
API_URL = os.getenv("WP_API_URL")
APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser_instance):
    context = browser_instance.new_context()
    page = context.new_page()
    yield page
    context.close()

from pages.ui.login_page import LoginPage

@pytest.fixture(scope="function")
def authenticated_page(page):
    login = LoginPage(page)
    login.open()
    login.login(ADMIN_USERNAME, ADMIN_PASSWORD)
    return page

@pytest.fixture(scope="session")
def api_credentials():
    return {
        "base_url": API_URL,
        "auth": (ADMIN_USERNAME, APP_PASSWORD)
    }

@pytest.fixture(scope="session")
def invalid_api_credentials():
    """Correct username, wrong application password — for testing bad-auth
    (as opposed to no-auth) rejection paths."""
    return {
        "base_url": API_URL,
        "auth": (ADMIN_USERNAME, "wrong-app-password-00000000")
    }

@pytest.fixture(scope="session")
def unauthenticated_api_credentials():
    return {
        "base_url": API_URL,
        "auth": None
    }

@pytest.fixture
def post_factory(api_credentials):
    """Creates posts and guarantees cleanup even if the test fails partway
    through. The original inline create/assert/delete pattern leaked data
    on a failed assertion, since the delete call never ran."""
    from pages.api.posts_api import PostsAPI
    api = PostsAPI(api_credentials["base_url"], api_credentials["auth"])
    created_ids = []

    def _create(**kwargs):
        response = api.create_post(**kwargs)
        if response.status_code == 201:
            created_ids.append(response.json()["id"])
        return response

    yield _create

    for post_id in created_ids:
        api.delete_post(post_id)

@pytest.fixture
def category_factory(api_credentials):
    from pages.api.categories_api import CategoriesAPI
    api = CategoriesAPI(api_credentials["base_url"], api_credentials["auth"])
    created_ids = []

    def _create(**kwargs):
        response = api.create_category(**kwargs)
        if response.status_code == 201:
            created_ids.append(response.json()["id"])
        return response

    yield _create

    for category_id in created_ids:
        api.delete_category(category_id)

@pytest.fixture
def user_factory(api_credentials):
    from pages.api.users_api import UsersAPI
    api = UsersAPI(api_credentials["base_url"], api_credentials["auth"])
    created_ids = []

    def _create(**kwargs):
        response = api.create_user(**kwargs)
        if response.status_code == 201:
            created_ids.append(response.json()["id"])
        return response

    yield _create

    for user_id in created_ids:
        api.delete_user(user_id)