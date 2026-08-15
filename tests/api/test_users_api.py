import json
import random
import jsonschema
import pytest
from pages.api.users_api import UsersAPI


def _unique_suffix():
    return random.randint(100000, 999999)


# ---------------------------------------------------------------------------
# P0 — Happy path
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.smoke
def test_create_and_delete_user(user_factory):
    suffix = _unique_suffix()
    response = user_factory(
        username=f"testuser{suffix}",
        email=f"testuser{suffix}@test.com",
        password="TestPass123!",
    )
    assert response.status_code == 201


@pytest.mark.api
@pytest.mark.smoke
def test_user_schema_validation(api_credentials):
    api = UsersAPI(api_credentials["base_url"], api_credentials["auth"])
    response = api.get_current_user()
    data = response.json()

    with open("schemas/user_schema.json") as f:
        schema = json.load(f)
    jsonschema.validate(instance=data, schema=schema)


@pytest.mark.api
@pytest.mark.smoke
def test_get_current_user_matches_authenticated_credentials(api_credentials):
    api = UsersAPI(api_credentials["base_url"], api_credentials["auth"])
    response = api.get_current_user()
    assert response.status_code == 200
    # Assumes a simple ASCII admin username (e.g. "admin") whose sanitized
    # slug is just the lowercased username — true for the common case, but
    # would need adjusting for usernames with spaces/special characters.
    assert response.json()["slug"] == api_credentials["auth"][0].lower()


# ---------------------------------------------------------------------------
# P0 — Negative / auth
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.smoke
def test_create_user_without_auth_returns_401(unauthenticated_api_credentials):
    api = UsersAPI(unauthenticated_api_credentials["base_url"], unauthenticated_api_credentials["auth"])
    suffix = _unique_suffix()
    response = api.create_user(
        username=f"shouldnotexist{suffix}",
        email=f"shouldnotexist{suffix}@test.com",
        password="TestPass123!",
    )
    assert response.status_code == 401


@pytest.mark.api
@pytest.mark.smoke
def test_create_user_with_invalid_auth_returns_401(invalid_api_credentials):
    api = UsersAPI(invalid_api_credentials["base_url"], invalid_api_credentials["auth"])
    suffix = _unique_suffix()
    response = api.create_user(
        username=f"shouldnotexist{suffix}",
        email=f"shouldnotexist{suffix}@test.com",
        password="TestPass123!",
    )
    assert response.status_code == 401


@pytest.mark.api
@pytest.mark.smoke
def test_create_user_with_invalid_email_format_is_rejected(api_credentials):
    api = UsersAPI(api_credentials["base_url"], api_credentials["auth"])
    response = api.create_user(
        username=f"bademail{_unique_suffix()}",
        email="not-a-valid-email",
        password="TestPass123!",
    )
    assert response.status_code == 400


@pytest.mark.api
@pytest.mark.smoke
def test_get_nonexistent_user_returns_404(api_credentials):
    api = UsersAPI(api_credentials["base_url"], api_credentials["auth"])
    response = api.get_user(999999999)
    assert response.status_code == 404


@pytest.mark.api
@pytest.mark.smoke
def test_delete_nonexistent_user_returns_404(api_credentials):
    api = UsersAPI(api_credentials["base_url"], api_credentials["auth"])
    response = api.delete_user(999999999)
    assert response.status_code == 404


@pytest.mark.api
@pytest.mark.smoke
def test_create_user_missing_required_fields_returns_400(api_credentials):
    api = UsersAPI(api_credentials["base_url"], api_credentials["auth"])
    response = api.post(UsersAPI.ENDPOINT, {"username": f"incomplete{_unique_suffix()}"})
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# P1 — Equivalence classes (roles)
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize("role", ["subscriber", "contributor", "author", "editor"])
def test_create_user_with_each_standard_role(role, user_factory):
    suffix = _unique_suffix()
    response = user_factory(
        username=f"role{role}{suffix}",
        email=f"role{role}{suffix}@test.com",
        password="TestPass123!",
        role=role,
    )
    assert response.status_code == 201
    assert role in response.json()["roles"]


@pytest.mark.api
@pytest.mark.regression
def test_create_user_with_invalid_role_is_rejected(api_credentials):
    api = UsersAPI(api_credentials["base_url"], api_credentials["auth"])
    response = api.create_user(
        username=f"badrole{_unique_suffix()}",
        email=f"badrole{_unique_suffix()}@test.com",
        password="TestPass123!",
        role="not_a_real_role",
    )
    assert response.status_code != 201


# ---------------------------------------------------------------------------
# P1 — State / sequence
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
def test_deleted_user_returns_404_on_subsequent_get(api_credentials):
    api = UsersAPI(api_credentials["base_url"], api_credentials["auth"])
    suffix = _unique_suffix()
    create_response = api.create_user(
        username=f"tempuser{suffix}",
        email=f"tempuser{suffix}@test.com",
        password="TestPass123!",
    )
    user_id = create_response.json()["id"]

    api.delete_user(user_id)
    get_response = api.get_user(user_id)
    assert get_response.status_code == 404


# ---------------------------------------------------------------------------
# P1 — Combinatorics (duplicate identity fields)
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
def test_creating_duplicate_username_is_rejected(user_factory):
    suffix = _unique_suffix()
    username = f"dupeuser{suffix}"

    first = user_factory(username=username, email=f"first{suffix}@test.com", password="TestPass123!")
    second = user_factory(username=username, email=f"second{suffix}@test.com", password="TestPass123!")

    assert first.status_code == 201
    assert second.status_code == 400


@pytest.mark.api
@pytest.mark.regression
def test_creating_duplicate_email_is_rejected(user_factory):
    suffix = _unique_suffix()
    email = f"dupeemail{suffix}@test.com"

    first = user_factory(username=f"firstuser{suffix}", email=email, password="TestPass123!")
    second = user_factory(username=f"seconduser{suffix}", email=email, password="TestPass123!")

    assert first.status_code == 201
    assert second.status_code == 400


# ---------------------------------------------------------------------------
# P2 — Boundary
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
def test_create_user_with_username_at_column_length_boundary(user_factory):
    """wp_users.user_login is varchar(60) — checks the app degrades
    gracefully (accept-and-store, or a clean 400) right at that limit,
    rather than throwing a raw database error."""
    suffix = _unique_suffix()
    username_60_chars = (("u" * 54) + str(suffix))[:60]
    response = user_factory(
        username=username_60_chars,
        email=f"boundary{suffix}@test.com",
        password="TestPass123!",
    )
    assert response.status_code in (201, 400)
