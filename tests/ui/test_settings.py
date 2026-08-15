import pytest
from pages.ui.settings_page import SettingsPage

# ---------------------------------------------------------------------------
# P0 — Happy path
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.smoke
def test_settings_page_loads(authenticated_page):
    settings = SettingsPage(authenticated_page)
    settings.open()
    assert settings.get_site_title() != "" or settings.is_visible(settings.SITE_TITLE_INPUT)


@pytest.mark.ui
@pytest.mark.smoke
def test_update_site_title_and_tagline_persists(authenticated_page):
    settings = SettingsPage(authenticated_page)
    settings.open()
    original_title = settings.get_site_title()
    original_tagline = settings.get_tagline()

    try:
        settings.set_site_title("Automated Test Site Title")
        settings.set_tagline("Automated Test Tagline")
        settings.save()

        assert settings.is_save_confirmed()
        settings.open()
        assert settings.get_site_title() == "Automated Test Site Title"
        assert settings.get_tagline() == "Automated Test Tagline"
    finally:
        # Restore original values so this test doesn't corrupt site state
        # for every other test/run that follows it.
        settings.open()
        settings.set_site_title(original_title)
        settings.set_tagline(original_tagline)
        settings.save()


# ---------------------------------------------------------------------------
# P1 — Boundary / negative
# ---------------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.regression
def test_site_title_accepts_empty_value_without_error(authenticated_page):
    """WP core doesn't enforce a required, non-empty blogname server-side —
    this should save cleanly, not error."""
    settings = SettingsPage(authenticated_page)
    settings.open()
    original_title = settings.get_site_title()

    try:
        settings.set_site_title("")
        settings.save()
        assert settings.is_save_confirmed()
    finally:
        settings.open()
        settings.set_site_title(original_title)
        settings.save()


@pytest.mark.ui
@pytest.mark.regression
def test_script_tag_in_tagline_is_not_executed(authenticated_page):
    settings = SettingsPage(authenticated_page)
    settings.open()
    original_tagline = settings.get_tagline()

    try:
        settings.set_tagline("<script>alert('xss')</script>")
        settings.save()
        assert settings.is_save_confirmed()

        settings.open()
        page_content = authenticated_page.content()
        assert "<script>alert('xss')</script>" not in page_content
    finally:
        settings.open()
        settings.set_tagline(original_tagline)
        settings.save()
