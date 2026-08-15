from pages.ui.posts_page import PostsPage
from pages.api.posts_api import PostsAPI
import random
import re
import pytest

@pytest.mark.ui
@pytest.mark.smoke
def test_posts_list_loads(authenticated_page):
    posts = PostsPage(authenticated_page)
    posts.open()
    assert posts.get_post_count() > 0

@pytest.mark.ui
@pytest.mark.regression
def test_create_new_post(authenticated_page, api_credentials):
    posts = PostsPage(authenticated_page)
    posts.create_post("Test Post From Automation", "Some content")
    assert posts.is_post_published()

    api = PostsAPI(api_credentials["base_url"], api_credentials["auth"])
    created_post = api.find_post_by_title("Test Post From Automation")
    assert created_post is not None
    api.delete_post(created_post["id"])


@pytest.mark.parametrize("title", [
    "Short",
    "A Much Longer Post Title For Testing",
    "Post 123",
])
def test_create_post_with_various_titles(authenticated_page, title, api_credentials):
    posts = PostsPage(authenticated_page)
    posts.create_post(title, "content")
    assert posts.is_post_published()

    api = PostsAPI(api_credentials["base_url"], api_credentials["auth"])
    created_post = api.find_post_by_title(title)
    assert created_post is not None
    api.delete_post(created_post["id"])


# ---------------------------------------------------------------------------
# P0 — Boundary / negative (empty title)
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.regression
def test_create_post_with_empty_title_still_publishes(authenticated_page, api_credentials):
    """Gutenberg doesn't block publishing without a title — it just falls
    back to an empty rendered title (shown as '(no title)' in wp-admin)."""
    posts = PostsPage(authenticated_page)
    posts.open_new_post()
    posts.click_in_frame(posts.CONTENT_AREA)
    authenticated_page.keyboard.type("Content with no title")
    posts.click(posts.PUBLISH_BUTTON)
    posts.click(posts.CONFIRM_PUBLISH_BUTTON)
    authenticated_page.locator(posts.PUBLISHED_MESSAGE).wait_for(timeout=10000)

    assert posts.is_post_published()

    # Read the post ID back out of the editor URL (?post=<id>) rather than
    # searching by empty title, which could collide with pre-existing
    # untitled posts on a real site.
    match = re.search(r"[?&]post=(\d+)", authenticated_page.url)
    assert match, "Could not determine post ID from editor URL after publish"
    post_id = int(match.group(1))

    api = PostsAPI(api_credentials["base_url"], api_credentials["auth"])
    fetched = api.get_post(post_id)
    assert fetched.status_code == 200
    assert fetched.json()["title"]["rendered"] == ""
    api.delete_post(post_id)


# ---------------------------------------------------------------------------
# P1 — State / sequence
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.regression
def test_search_finds_created_post_by_title(authenticated_page, api_credentials):
    api = PostsAPI(api_credentials["base_url"], api_credentials["auth"])
    unique_title = f"Searchable Post {random.randint(100000, 999999)}"
    create_response = api.create_post(title=unique_title, content="content", status="publish")
    post_id = create_response.json()["id"]

    try:
        posts = PostsPage(authenticated_page)
        posts.search(unique_title)
        assert posts.is_post_row_visible(post_id)
    finally:
        api.delete_post(post_id)


@pytest.mark.ui
@pytest.mark.regression
def test_trash_post_removes_it_from_default_list(authenticated_page, api_credentials):
    api = PostsAPI(api_credentials["base_url"], api_credentials["auth"])
    unique_title = f"To Be Trashed {random.randint(100000, 999999)}"
    create_response = api.create_post(title=unique_title, content="content", status="publish")
    post_id = create_response.json()["id"]

    posts = PostsPage(authenticated_page)
    posts.trash_post(post_id)
    posts.open()

    assert not posts.is_post_row_visible(post_id)

    api.delete_post(post_id)  # permanently delete from trash to clean up
