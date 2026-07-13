"""Shared pytest fixtures: an in-memory DynamoDB table (via moto) using the
same pk/sk single-table schema the app uses, a throwaway RSA keypair
standing in for Clerk's signing key (JWKS fetches are monkeypatched to
return it, so tests exercise the app's real signature verification without
any network calls), and helpers for building synthetic API Gateway v2
(payload 2.0) events.
"""

import os
import time

import boto3
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm
from moto import mock_aws

os.environ.setdefault("TABLE_NAME", "resume-api-test")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("CLERK_ISSUER_URL", "https://clerk.test")
os.environ.setdefault("CLERK_AUDIENCE", "https://api.test")

TEST_KID = "test-key"
_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_JWKS = {"keys": [{**RSAAlgorithm.to_jwk(_PRIVATE_KEY.public_key(), as_dict=True), "kid": TEST_KID}]}


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


@pytest.fixture(autouse=True)
def fake_clerk_jwks(monkeypatch):
    """Stand in for Clerk's JWKS endpoint with our own throwaway key --
    verification logic itself (clerk.verify_session_token) runs for real."""
    monkeypatch.setattr("resume_api.clerk._fetch_jwks", lambda issuer: _JWKS)


def make_token(
    user_id: str = "user-123",
    *,
    kid: str | None = TEST_KID,
    key=_PRIVATE_KEY,
    **claim_overrides,
) -> str:
    """Sign a Clerk-shaped test JWT. Pass a different `key` (or omit `sub`,
    `exp`, etc. via claim_overrides) to build tokens for negative tests."""
    now = int(time.time())
    claims = {
        "sub": user_id,
        "iss": os.environ["CLERK_ISSUER_URL"],
        "aud": os.environ["CLERK_AUDIENCE"],
        "iat": now,
        "exp": now + 3600,
        **claim_overrides,
    }
    headers = {"kid": kid} if kid is not None else None
    return jwt.encode(claims, key, algorithm="RS256", headers=headers)


_NO_AUTH_GIVEN = object()


def make_event(
    method: str,
    path: str,
    *,
    user_id: str = "user-123",
    body: str | None = None,
    query: str = "",
    authorization: str | None = _NO_AUTH_GIVEN,
) -> dict:
    """Build a synthetic API Gateway HTTP API (v2) event carrying a real,
    signed bearer token for user_id by default -- this exercises the app's
    own JWT verification rather than standing in for it. Pass
    authorization=None to omit the header, or a raw string to test
    malformed/expired/wrong-key tokens directly."""
    if authorization is _NO_AUTH_GIVEN:
        authorization = f"Bearer {make_token(user_id)}"

    headers = {"content-type": "application/json"}
    if authorization is not None:
        headers["authorization"] = authorization

    return {
        "version": "2.0",
        "routeKey": "ANY /{proxy+}",
        "rawPath": path,
        "rawQueryString": query,
        "headers": headers,
        "queryStringParameters": (
            dict(pair.split("=") for pair in query.split("&")) if query else None
        ),
        "requestContext": {
            "stage": "$default",
            "http": {"method": method, "path": path},
        },
        "body": body,
        "isBase64Encoded": False,
    }
