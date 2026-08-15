import random
import re
import pytest
from pages.ui.pages_page import PagesPage

# ---------------------------------------------------------------------------
# P0 — Happy path
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.smoke
def test_pages_list_loads(authenticated_page):
    pages = PagesPage(authenticated_page)
    pages.open()
    assert pages.get_page_count() >= 0


@pytest.mark.ui
@pytest.mark.smoke
def test_create_new_page(authenticated_page):
    pages = PagesPage(authenticated_page)
    pages.create_page("Test Page From Automation", "Some content")
    assert pages.is_page_published()

    match = re.search(r"[?&]post=(\d+)", authenticated_page.url)
    assert match, "Could not determine page ID from editor URL after publish"
    pages.trash_page(int(match.group(1)))


# ---------------------------------------------------------------------------
# P0 — Boundary / negative
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.regression
def test_create_page_with_empty_title_still_publishes(authenticated_page):
    """Gutenberg doesn't block publishing a page without a title, same as posts."""
    pages = PagesPage(authenticated_page)
    pages.open_new_page()
    pages.click_in_frame(pages.CONTENT_AREA)
    authenticated_page.keyboard.type("Page content with no title")
    pages.click(pages.PUBLISH_BUTTON)
    pages.click(pages.CONFIRM_PUBLISH_BUTTON)
    authenticated_page.locator(pages.PUBLISHED_MESSAGE).wait_for(timeout=10000)

    assert pages.is_page_published()
    match = re.search(r"[?&]post=(\d+)", authenticated_page.url)
    assert match
    pages.trash_page(int(match.group(1)))


# ---------------------------------------------------------------------------
# P1 — State / sequence
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.regression
def test_search_finds_created_page_by_title(authenticated_page):
    pages = PagesPage(authenticated_page)
    unique_title = f"Searchable Page {random.randint(100000, 999999)}"
    pages.create_page(unique_title, "content")
    match = re.search(r"[?&]post=(\d+)", authenticated_page.url)
    page_id = int(match.group(1))

    pages.search(unique_title)
    assert pages.is_page_row_visible(page_id)

    pages.trash_page(page_id)


@pytest.mark.ui
@pytest.mark.regression
def test_trash_page_removes_it_from_default_list(authenticated_page):
    pages = PagesPage(authenticated_page)
    unique_title = f"To Be Trashed {random.randint(100000, 999999)}"
    pages.create_page(unique_title, "content")
    match = re.search(r"[?&]post=(\d+)", authenticated_page.url)
    page_id = int(match.group(1))

    pages.trash_page(page_id)
    pages.open()

    assert not pages.is_page_row_visible(page_id)
