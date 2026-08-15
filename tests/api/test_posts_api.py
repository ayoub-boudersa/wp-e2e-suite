import json
import jsonschema
import pytest
from pages.api.posts_api import PostsAPI


# ---------------------------------------------------------------------------
# P0 — Happy path
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.smoke
def test_get_all_posts_return_200(api_credentials):
    api = PostsAPI(api_credentials["base_url"], api_credentials["auth"])
    response = api.get_all_posts()
    assert response.status_code == 200


@pytest.mark.api
@pytest.mark.smoke
def test_create_and_delete_post(post_factory):
    response = post_factory(title="Automated Test Post", content="content", status="draft")
    assert response.status_code == 201
    assert response.json()["title"]["rendered"] == "Automated Test Post"


@pytest.mark.api
@pytest.mark.smoke
def test_post_schema_validation(post_factory):
    response = post_factory(title="Schema Check Post", content="content", status="publish")
    data = response.json()

    with open("schemas/post_schema.json") as f:
        schema = json.load(f)
    jsonschema.validate(instance=data, schema=schema)


# ---------------------------------------------------------------------------
# P0 — Negative / auth
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.smoke
def test_create_post_without_auth_returns_401(unauthenticated_api_credentials):
    api = PostsAPI(unauthenticated_api_credentials["base_url"], unauthenticated_api_credentials["auth"])
    response = api.create_post(title="Should Not Be Created", content="content")
    assert response.status_code == 401


@pytest.mark.api
@pytest.mark.smoke
def test_create_post_with_invalid_auth_returns_401(invalid_api_credentials):
    api = PostsAPI(invalid_api_credentials["base_url"], invalid_api_credentials["auth"])
    response = api.create_post(title="Should Not Be Created", content="content")
    assert response.status_code == 401


@pytest.mark.api
@pytest.mark.smoke
def test_get_nonexistent_post_returns_404(api_credentials):
    api = PostsAPI(api_credentials["base_url"], api_credentials["auth"])
    response = api.get_post(999999999)
    assert response.status_code == 404


@pytest.mark.api
@pytest.mark.smoke
def test_create_post_with_invalid_status_is_rejected(post_factory):
    response = post_factory(title="Bad Status Post", content="content", status="not_a_real_status")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# P1 — Equivalence classes (status values)
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize("status", ["draft", "publish", "pending", "private"])
def test_create_post_with_each_valid_status(status, post_factory):
    response = post_factory(title=f"Status Test - {status}", content="content", status=status)
    assert response.status_code == 201
    assert response.json()["status"] == status


# ---------------------------------------------------------------------------
# P1 — State / sequence
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
def test_deleted_post_returns_404_on_subsequent_get(api_credentials):
    api = PostsAPI(api_credentials["base_url"], api_credentials["auth"])
    create_response = api.create_post(title="Temp Post For Deletion", content="content", status="draft")
    post_id = create_response.json()["id"]

    api.delete_post(post_id)
    get_response = api.get_post(post_id)
    assert get_response.status_code == 404


@pytest.mark.api
@pytest.mark.regression
def test_update_post_persists_new_field_values(api_credentials, post_factory):
    create_response = post_factory(title="Original Title", content="Original content", status="draft")
    post_id = create_response.json()["id"]

    api = PostsAPI(api_credentials["base_url"], api_credentials["auth"])
    update_response = api.update_post(post_id, title="Updated Title")
    assert update_response.status_code == 200

    fetched = api.get_post(post_id).json()
    assert fetched["title"]["rendered"] == "Updated Title"


@pytest.mark.api
@pytest.mark.regression
def test_duplicate_titles_get_unique_slugs(post_factory):
    first = post_factory(title="Duplicate Slug Test", content="content", status="publish")
    second = post_factory(title="Duplicate Slug Test", content="content", status="publish")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["slug"] != second.json()["slug"]


# ---------------------------------------------------------------------------
# P1 — Combinatorics (status x auth)
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
def test_draft_post_not_visible_to_unauthenticated_request(post_factory, unauthenticated_api_credentials):
    create_response = post_factory(title="Hidden Draft Post", content="content", status="draft")
    post_id = create_response.json()["id"]

    public_api = PostsAPI(unauthenticated_api_credentials["base_url"], unauthenticated_api_credentials["auth"])
    response = public_api.get_post(post_id)

    # Exact code varies by WP version/config (401 rest_forbidden is typical
    # on current core) — the invariant that matters is: a draft must never
    # come back as a 200 to an unauthenticated caller.
    assert response.status_code != 200


@pytest.mark.api
@pytest.mark.regression
def test_published_post_visible_to_unauthenticated_request(post_factory, unauthenticated_api_credentials):
    create_response = post_factory(title="Visible Published Post", content="content", status="publish")
    post_id = create_response.json()["id"]

    public_api = PostsAPI(unauthenticated_api_credentials["base_url"], unauthenticated_api_credentials["auth"])
    response = public_api.get_post(post_id)
    assert response.status_code == 200


@pytest.mark.api
@pytest.mark.regression
def test_draft_post_excluded_from_unauthenticated_list(post_factory, unauthenticated_api_credentials):
    post_factory(title="Should Not Appear In Public List", content="content", status="draft")

    public_api = PostsAPI(unauthenticated_api_credentials["base_url"], unauthenticated_api_credentials["auth"])
    response = public_api.get_all_posts()
    titles = [p["title"]["rendered"] for p in response.json()]

    assert "Should Not Appear In Public List" not in titles


# ---------------------------------------------------------------------------
# P1 — Negative (injection)
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
def test_script_tag_in_title_is_not_reflected_unescaped(post_factory):
    payload = "<script>alert('xss')</script>Malicious Title"
    response = post_factory(title=payload, content="content", status="publish")
    assert response.status_code == 201

    rendered_title = response.json()["title"]["rendered"]
    assert "<script>" not in rendered_title


# ---------------------------------------------------------------------------
# P2 — Boundary
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
def test_create_post_with_very_long_title(post_factory):
    long_title = "A" * 5000
    response = post_factory(title=long_title, content="content", status="draft")
    assert response.status_code in (201, 400)


@pytest.mark.api
@pytest.mark.regression
def test_create_post_with_empty_title_and_content(post_factory):
    """WordPress core permits empty title/content — it just falls back to
    '(no title)' in the admin list. This must not 500."""
    response = post_factory(title="", content="", status="draft")
    assert response.status_code == 201
