"""Aggregate resume endpoint: GET /me/resume?format=json|markdown.

The only query this API ever needs to assemble a full resume: one Query by
pk (see db.py for the pk/sk schema), grouped by entity_type in Python.
"""

from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler.api_gateway import Router
from boto3.dynamodb.conditions import Key

from resume_api.auth import current_user_id
from resume_api.db import clean_decimals, get_table, user_pk
from resume_api.markdown import render_markdown

router = Router()

_COLLECTION_KEY_BY_ENTITY_TYPE = {
    "EXPERIENCE": "experience",
    "EDUCATION": "education",
    "SKILL": "skills",
    "CERTIFICATION": "certifications",
    "HOBBY": "hobbies",
    "GOAL": "goals",
}
_CHRONOLOGICAL_DESC = {"EXPERIENCE", "EDUCATION"}


@router.get("/")
def get_resume():
    user_id = current_user_id(router)
    response = get_table().query(KeyConditionExpression=Key("pk").eq(user_pk(user_id)))
    items = clean_decimals(response.get("Items", []))

    profile = None
    grouped: dict[str, list[dict]] = {key: [] for key in _COLLECTION_KEY_BY_ENTITY_TYPE.values()}

    for item in items:
        entity_type = item.get("entity_type")
        if entity_type == "PROFILE":
            profile = item
        elif entity_type in _COLLECTION_KEY_BY_ENTITY_TYPE:
            grouped[_COLLECTION_KEY_BY_ENTITY_TYPE[entity_type]].append(item)

    for entity_type, plural in _COLLECTION_KEY_BY_ENTITY_TYPE.items():
        if entity_type in _CHRONOLOGICAL_DESC:
            grouped[plural].sort(key=lambda item: item.get("start_date") or "", reverse=True)
        else:
            grouped[plural].sort(key=lambda item: item.get("created_at") or "")

    resume = {"profile": profile, **grouped}

    query_params = router.current_event.query_string_parameters or {}
    fmt = (query_params.get("format") or "json").lower()

    if fmt == "markdown":
        return Response(status_code=200, content_type="text/markdown", body=render_markdown(resume))

    return resume
