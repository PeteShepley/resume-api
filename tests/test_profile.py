import json

from conftest import make_event

from resume_api.app import handler


def test_profile_not_found_initially():
    response = handler(make_event("GET", "/me/profile"), {})
    assert response["statusCode"] == 404


def test_profile_upsert_and_get():
    put_response = handler(
        make_event(
            "PUT",
            "/me/profile",
            body=json.dumps({"name": "Ada Lovelace", "headline": "Mathematician"}),
        ),
        {},
    )
    assert put_response["statusCode"] == 200
    body = json.loads(put_response["body"])
    assert body["name"] == "Ada Lovelace"
    assert body["entity_type"] == "PROFILE"

    get_response = handler(make_event("GET", "/me/profile"), {})
    assert get_response["statusCode"] == 200
    assert json.loads(get_response["body"])["headline"] == "Mathematician"


def test_profile_scoped_per_user():
    handler(
        make_event("PUT", "/me/profile", user_id="user-a", body=json.dumps({"name": "A"})),
        {},
    )
    response = handler(make_event("GET", "/me/profile", user_id="user-b"), {})
    assert response["statusCode"] == 404


def test_profile_update_keeps_original_created_at():
    first = handler(
        make_event("PUT", "/me/profile", body=json.dumps({"name": "Ada"})),
        {},
    )
    created_at = json.loads(first["body"])["created_at"]

    second = handler(
        make_event("PUT", "/me/profile", body=json.dumps({"name": "Ada Lovelace"})),
        {},
    )
    body = json.loads(second["body"])
    assert body["created_at"] == created_at
    assert body["name"] == "Ada Lovelace"
