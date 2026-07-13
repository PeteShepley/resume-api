"""Extracts and verifies the caller's identity from the Authorization
header on every request. The app verifies the token itself against
Clerk's published JWKS (see clerk.py) -- it never trusts a claim that
something in front of it (API Gateway, a proxy) says it already checked.

No handler in this service ever takes a person id from a URL or request
body; the verified `sub` claim is the only identity used to key every
DynamoDB operation.
"""

from aws_lambda_powertools.event_handler.api_gateway import BaseRouter
from aws_lambda_powertools.event_handler.exceptions import UnauthorizedError

from resume_api.clerk import verify_session_token


def current_user_id(router: BaseRouter) -> str:
    header = router.current_event.headers.get("Authorization")
    if not header or not header.lower().startswith("bearer "):
        raise UnauthorizedError("Missing bearer token")

    token = header.split(" ", 1)[1].strip()
    claims = verify_session_token(token)
    user_id = claims.get("sub")
    if not user_id:
        raise UnauthorizedError("Missing verified identity")
    return user_id
