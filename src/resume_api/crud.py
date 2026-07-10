"""Generic CRUD router factory for the six owned-collection entity types.

Each collection (experience, education, skills, certifications, hobbies,
goals) registers via build_collection_router() instead of hand-writing five
near-identical handlers — the only per-entity difference is the entity
type string, its Pydantic model, and (for experience/education) sort order.
The profile singleton and the resume aggregate are hand-written instead
(routers/profile.py, routers/resume.py) since neither fits this shape.
"""

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.exceptions import BadRequestError, NotFoundError
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel, ValidationError

from resume_api.auth import current_user_id
from resume_api.db import clean_decimals, entity_sk, get_table, user_pk


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_dynamo_item(model: BaseModel) -> dict:
    """Pydantic -> plain dict with DynamoDB-safe numerics (Decimal, not
    float — boto3's DynamoDB resource layer rejects native floats)."""
    return json.loads(model.model_dump_json(), parse_float=Decimal)


def _validate(model: type[BaseModel], body: dict | None) -> BaseModel:
    try:
        return model.model_validate(body or {})
    except ValidationError as exc:
        raise BadRequestError(exc.json()) from exc


def build_collection_router(
    entity_type: str,
    model: type[BaseModel],
    sort_by: str = "created_at",
    reverse: bool = False,
) -> Router:
    router = Router()

    @router.get("/")
    def list_items():
        user_id = current_user_id(router)
        response = get_table().query(
            KeyConditionExpression=Key("pk").eq(user_pk(user_id))
            & Key("sk").begins_with(f"{entity_type}#")
        )
        items = clean_decimals(response.get("Items", []))
        items.sort(key=lambda item: item.get(sort_by) or "", reverse=reverse)
        return {"items": items}

    @router.post("/")
    def create_item():
        user_id = current_user_id(router)
        payload = _validate(model, router.current_event.json_body)

        item_id = str(uuid.uuid4())
        now = _now()
        item = {
            "pk": user_pk(user_id),
            "sk": entity_sk(entity_type, item_id),
            "id": item_id,
            "entity_type": entity_type,
            "created_at": now,
            "updated_at": now,
            **_to_dynamo_item(payload),
        }
        get_table().put_item(Item=item)
        return Response(
            status_code=201,
            content_type="application/json",
            body=json.dumps(clean_decimals(item)),
        )

    @router.get("/<item_id>")
    def get_item(item_id: str):
        user_id = current_user_id(router)
        key = {"pk": user_pk(user_id), "sk": entity_sk(entity_type, item_id)}
        item = get_table().get_item(Key=key).get("Item")
        if item is None:
            raise NotFoundError()
        return clean_decimals(item)

    @router.put("/<item_id>")
    def update_item(item_id: str):
        user_id = current_user_id(router)
        key = {"pk": user_pk(user_id), "sk": entity_sk(entity_type, item_id)}
        existing = get_table().get_item(Key=key).get("Item")
        if existing is None:
            raise NotFoundError()

        payload = _validate(model, router.current_event.json_body)
        item = {
            **key,
            "id": item_id,
            "entity_type": entity_type,
            "created_at": existing["created_at"],
            "updated_at": _now(),
            **_to_dynamo_item(payload),
        }
        get_table().put_item(Item=item)
        return clean_decimals(item)

    @router.delete("/<item_id>")
    def delete_item(item_id: str):
        user_id = current_user_id(router)
        key = {"pk": user_pk(user_id), "sk": entity_sk(entity_type, item_id)}
        existing = get_table().get_item(Key=key).get("Item")
        if existing is None:
            raise NotFoundError()
        get_table().delete_item(Key=key)
        return Response(status_code=204, content_type="application/json", body=None)

    return router
