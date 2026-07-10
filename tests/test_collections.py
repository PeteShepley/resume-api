import json

import pytest
from conftest import make_event

from resume_api.app import handler

VALID_PAYLOADS = {
    "experience": {
        "organization": "Acme Corp",
        "title": "Engineer",
        "start_date": "2020-01-01",
    },
    "education": {
        "institution": "State University",
        "degree": "B.S. Computer Science",
        "start_date": "2016-09-01",
        "end_date": "2020-05-01",
    },
    "skills": {"name": "Python", "category": "language", "years_experience": 5.5},
    "certifications": {
        "name": "AWS Certified",
        "issuing_organization": "AWS",
        "issue_date": "2023-01-01",
    },
    "hobbies": {"name": "Woodworking"},
    "goals": {"description": "Learn Rust", "category": "learning"},
}


@pytest.mark.parametrize("path", VALID_PAYLOADS.keys())
def test_collection_crud_roundtrip(path):
    base = f"/me/{path}"
    payload = VALID_PAYLOADS[path]

    create_response = handler(make_event("POST", base, body=json.dumps(payload)), {})
    assert create_response["statusCode"] == 201
    created = json.loads(create_response["body"])
    item_id = created["id"]
    for key, value in payload.items():
        assert created[key] == value
    assert created["created_at"] == created["updated_at"]

    list_response = handler(make_event("GET", base), {})
    assert list_response["statusCode"] == 200
    items = json.loads(list_response["body"])["items"]
    assert len(items) == 1
    assert items[0]["id"] == item_id

    get_response = handler(make_event("GET", f"{base}/{item_id}"), {})
    assert get_response["statusCode"] == 200
    assert json.loads(get_response["body"])["id"] == item_id

    update_response = handler(
        make_event("PUT", f"{base}/{item_id}", body=json.dumps(payload)), {}
    )
    assert update_response["statusCode"] == 200
    updated = json.loads(update_response["body"])
    assert updated["created_at"] == created["created_at"]
    assert updated["updated_at"] != created["updated_at"]

    delete_response = handler(make_event("DELETE", f"{base}/{item_id}"), {})
    assert delete_response["statusCode"] == 204

    get_after_delete = handler(make_event("GET", f"{base}/{item_id}"), {})
    assert get_after_delete["statusCode"] == 404


@pytest.mark.parametrize("path", VALID_PAYLOADS.keys())
def test_get_missing_item_404(path):
    response = handler(make_event("GET", f"/me/{path}/does-not-exist"), {})
    assert response["statusCode"] == 404


def test_create_invalid_payload_400():
    response = handler(make_event("POST", "/me/experience", body=json.dumps({})), {})
    assert response["statusCode"] == 400


def test_decimal_field_round_trips_as_number():
    payload = {"name": "Python", "category": "language", "years_experience": 5.5}
    create_response = handler(make_event("POST", "/me/skills", body=json.dumps(payload)), {})
    created = json.loads(create_response["body"])
    assert created["years_experience"] == 5.5
    assert isinstance(created["years_experience"], float)


def test_collections_scoped_per_user():
    handler(
        make_event(
            "POST",
            "/me/hobbies",
            user_id="user-a",
            body=json.dumps({"name": "Chess"}),
        ),
        {},
    )
    response = handler(make_event("GET", "/me/hobbies", user_id="user-b"), {})
    assert json.loads(response["body"])["items"] == []


def test_experience_lists_most_recent_first():
    handler(
        make_event(
            "POST",
            "/me/experience",
            body=json.dumps({"organization": "Old Co", "title": "Jr", "start_date": "2015-01-01"}),
        ),
        {},
    )
    handler(
        make_event(
            "POST",
            "/me/experience",
            body=json.dumps({"organization": "New Co", "title": "Sr", "start_date": "2022-01-01"}),
        ),
        {},
    )
    response = handler(make_event("GET", "/me/experience"), {})
    items = json.loads(response["body"])["items"]
    assert [item["organization"] for item in items] == ["New Co", "Old Co"]
