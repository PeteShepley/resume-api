"""Singleton profile: GET /me/profile, PUT /me/profile (upsert).

Not built on the generic crud factory — there's exactly one profile per
person (no id, no list, no delete), a different shape than the six owned
collections.
"""

from datetime import datetime, timezone

from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.exceptions import BadRequestError, NotFoundError
from pydantic import ValidationError

from resume_api.auth import current_user_id
from resume_api.db import PROFILE_SK, get_table, user_pk
from resume_api.models import Profile

router = Router()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/")
def get_profile():
    user_id = current_user_id(router)
    key = {"pk": user_pk(user_id), "sk": PROFILE_SK}
    item = get_table().get_item(Key=key).get("Item")
    if item is None:
        raise NotFoundError()
    return item


@router.put("/")
def put_profile():
    user_id = current_user_id(router)
    try:
        payload = Profile.model_validate(router.current_event.json_body or {})
    except ValidationError as exc:
        raise BadRequestError(exc.json()) from exc

    key = {"pk": user_pk(user_id), "sk": PROFILE_SK}
    existing = get_table().get_item(Key=key).get("Item")
    now = _now()
    item = {
        **key,
        "entity_type": "PROFILE",
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
        **payload.model_dump(mode="json"),
    }
    get_table().put_item(Item=item)
    return item
