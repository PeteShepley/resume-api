"""Extract the caller's Clerk user id from the already-verified JWT claims
API Gateway's JWT authorizer attaches to the request. The authorizer has
already validated the token's signature, issuer, and audience before this
code ever runs — this is claim extraction, not verification.

No handler in this service ever takes a person id from a URL or request
body; the verified `sub` claim is the only identity used to key every
DynamoDB operation.
"""

from aws_lambda_powertools.event_handler.api_gateway import BaseRouter
from aws_lambda_powertools.event_handler.exceptions import UnauthorizedError


def current_user_id(router: BaseRouter) -> str:
    claims = router.current_event.request_context.authorizer.jwt_claim
    user_id = claims.get("sub")
    if not user_id:
        raise UnauthorizedError("Missing verified identity")
    return user_id
