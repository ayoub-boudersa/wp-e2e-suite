import json
import random
import jsonschema
import pytest
from pages.api.categories_api import CategoriesAPI


# ---------------------------------------------------------------------------
# P0 — Happy path
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.smoke
def test_create_and_delete_category(category_factory):
    response = category_factory(name="Automated Test Category")
    assert response.status_code == 201


@pytest.mark.api
@pytest.mark.smoke
def test_get_all_categories_returns_200(api_credentials):
    api = CategoriesAPI(api_credentials["base_url"], api_credentials["auth"])
    response = api.get_all_categories()
    assert response.status_code == 200


@pytest.mark.api
@pytest.mark.smoke
def test_category_schema_validation(category_factory):
    response = category_factory(name="Schema Check Category")
    data = response.json()

    with open("schemas/category_schema.json") as f:
        schema = json.load(f)
    jsonschema.validate(instance=data, schema=schema)


# ---------------------------------------------------------------------------
# P0 — Negative / auth
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.smoke
def test_create_category_without_auth_returns_401(unauthenticated_api_credentials):
    api = CategoriesAPI(unauthenticated_api_credentials["base_url"], unauthenticated_api_credentials["auth"])
    response = api.create_category(name="Should Not Be Created")
    assert response.status_code == 401


@pytest.mark.api
@pytest.mark.smoke
def test_create_category_with_invalid_auth_returns_401(invalid_api_credentials):
    api = CategoriesAPI(invalid_api_credentials["base_url"], invalid_api_credentials["auth"])
    response = api.create_category(name="Should Not Be Created")
    assert response.status_code == 401


@pytest.mark.api
@pytest.mark.smoke
def test_create_category_without_name_is_rejected(api_credentials):
    api = CategoriesAPI(api_credentials["base_url"], api_credentials["auth"])
    response = api.post(CategoriesAPI.ENDPOINT, {"description": "Missing the required name field"})
    assert response.status_code == 400


@pytest.mark.api
@pytest.mark.smoke
def test_get_nonexistent_category_returns_404(api_credentials):
    api = CategoriesAPI(api_credentials["base_url"], api_credentials["auth"])
    response = api.get_category(999999999)
    assert response.status_code == 404


@pytest.mark.api
@pytest.mark.smoke
def test_delete_nonexistent_category_returns_404(api_credentials):
    api = CategoriesAPI(api_credentials["base_url"], api_credentials["auth"])
    response = api.delete_category(999999999)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# P1 — State / sequence
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
def test_deleted_category_returns_404_on_subsequent_get(api_credentials):
    api = CategoriesAPI(api_credentials["base_url"], api_credentials["auth"])
    create_response = api.create_category(name="Temp Category For Deletion")
    category_id = create_response.json()["id"]

    api.delete_category(category_id)
    get_response = api.get_category(category_id)
    assert get_response.status_code == 404


@pytest.mark.api
@pytest.mark.regression
def test_creating_duplicate_category_name_is_rejected(category_factory):
    """WordPress enforces unique term names within the same taxonomy/parent
    — the second create must fail with term_exists, not silently create a
    second identical category."""
    unique_name = f"Duplicate Category {random.randint(10000, 99999)}"
    first = category_factory(name=unique_name)
    second = category_factory(name=unique_name)

    assert first.status_code == 201
    assert second.status_code == 400
    assert second.json().get("code") == "term_exists"


# ---------------------------------------------------------------------------
# P1 — Combinatorics (hierarchy)
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
def test_child_category_reports_correct_parent(category_factory):
    parent = category_factory(name=f"Parent Category {random.randint(10000, 99999)}")
    parent_id = parent.json()["id"]

    child = category_factory(name=f"Child Category {random.randint(10000, 99999)}", parent=parent_id)

    assert child.status_code == 201
    assert child.json()["parent"] == parent_id


@pytest.mark.api
@pytest.mark.regression
def test_deleting_parent_category_does_not_error_with_child_present(api_credentials, category_factory):
    """Default WP behavior re-parents orphaned children to top-level (0)
    rather than cascading the delete or erroring."""
    api = CategoriesAPI(api_credentials["base_url"], api_credentials["auth"])
    parent = category_factory(name=f"Doomed Parent {random.randint(10000, 99999)}")
    parent_id = parent.json()["id"]
    child = category_factory(name=f"Surviving Child {random.randint(10000, 99999)}", parent=parent_id)
    child_id = child.json()["id"]

    delete_response = api.delete_category(parent_id)
    assert delete_response.status_code == 200

    fetched_child = api.get_category(child_id).json()
    assert fetched_child["parent"] == 0


# ---------------------------------------------------------------------------
# P2 — Boundary
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
def test_create_category_with_very_long_name(category_factory):
    long_name = "B" * 2000
    response = category_factory(name=long_name)
    assert response.status_code in (201, 400)
