"""Shared pytest fixtures: a moto-mocked DynamoDB table matching the
Terraform schema (infra/apis/resume-api/dynamodb.tf in the operations repo),
and a helper for building synthetic API Gateway v2 (payload 2.0) events.
"""

import os

import boto3
import pytest
from moto import mock_aws

os.environ.setdefault("TABLE_NAME", "resume-api-test")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")


@pytest.fixture(autouse=True)
def dynamodb_table():
    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        client.create_table(
            TableName=os.environ["TABLE_NAME"],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield


def make_event(
    method: str,
    path: str,
    *,
    user_id: str = "user-123",
    body: str | None = None,
    query: str = "",
) -> dict:
    """Build a synthetic API Gateway HTTP API (v2) event, as if the JWT
    authorizer already verified the caller and attached `sub` to the
    request context — matching what infra/apis/resume-api/apigateway.tf
    produces for a real request."""
    return {
        "version": "2.0",
        "routeKey": "ANY /{proxy+}",
        "rawPath": path,
        "rawQueryString": query,
        "headers": {"content-type": "application/json"},
        "queryStringParameters": (
            dict(pair.split("=") for pair in query.split("&")) if query else None
        ),
        "requestContext": {
            "stage": "$default",
            "http": {"method": method, "path": path},
            "authorizer": {"jwt": {"claims": {"sub": user_id}}},
        },
        "body": body,
        "isBase64Encoded": False,
    }
