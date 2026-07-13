"""DynamoDB table handle and pk/sk key-building helpers.

Single-table schema: every item is keyed by `pk=USER#<clerk_user_id>` and
an `sk` that distinguishes what it is -- `PROFILE` for the profile
singleton, `<ENTITY_TYPE>#<uuid>` (e.g. `EXPERIENCE#<uuid>`) for each item
in the six owned collections (see models.py for entity types, crud.py for
how collection items are built).
"""

from __future__ import annotations

import os
from decimal import Decimal

import boto3

PROFILE_SK = "PROFILE"


def clean_decimals(value):
    """DynamoDB Decimals -> plain int/float for JSON responses. Without
    this, Powertools' encoder stringifies Decimals (e.g. 2.75 -> "2.75"),
    which isn't the numeric type a client expects back."""
    if isinstance(value, list):
        return [clean_decimals(v) for v in value]
    if isinstance(value, dict):
        return {k: clean_decimals(v) for k, v in value.items()}
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


def get_table():
    """Fresh table handle per call — cheap (no network call), and keeps
    tests free to set TABLE_NAME / mock DynamoDB without import-order
    caching surprises."""
    table_name = os.environ.get("TABLE_NAME", "resume-api")
    return boto3.resource("dynamodb").Table(table_name)


def user_pk(user_id: str) -> str:
    return f"USER#{user_id}"


def entity_sk(entity_type: str, entity_id: str) -> str:
    return f"{entity_type}#{entity_id}"
