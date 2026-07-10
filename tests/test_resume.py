import json

from conftest import make_event

from resume_api.app import handler


def _seed_full_resume(user_id: str = "user-123") -> None:
    handler(
        make_event(
            "PUT",
            "/me/profile",
            user_id=user_id,
            body=json.dumps({"name": "Ada Lovelace", "headline": "Mathematician"}),
        ),
        {},
    )
    handler(
        make_event(
            "POST",
            "/me/experience",
            user_id=user_id,
            body=json.dumps(
                {
                    "organization": "Analytical Engines Ltd",
                    "title": "Lead Programmer",
                    "start_date": "2020-01-01",
                }
            ),
        ),
        {},
    )
    handler(
        make_event(
            "POST",
            "/me/skills",
            user_id=user_id,
            body=json.dumps({"name": "Algorithms", "category": "soft-skill"}),
        ),
        {},
    )


def test_resume_json_aggregates_all_collections():
    _seed_full_resume()
    response = handler(make_event("GET", "/me/resume"), {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["profile"]["name"] == "Ada Lovelace"
    assert len(body["experience"]) == 1
    assert len(body["skills"]) == 1
    assert body["education"] == []


def test_resume_markdown_format():
    _seed_full_resume()
    response = handler(make_event("GET", "/me/resume", query="format=markdown"), {})
    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "text/markdown"
    assert "# Ada Lovelace" in response["body"]
    assert "## Experience" in response["body"]


def test_resume_scoped_per_user():
    _seed_full_resume(user_id="user-a")
    response = handler(make_event("GET", "/me/resume", user_id="user-b"), {})
    body = json.loads(response["body"])
    assert body["profile"] is None
    assert body["experience"] == []
