"""Verifies Clerk-issued session JWTs against Clerk's published JWKS.

This is the app's own trust boundary: it never assumes a caller's identity
has already been checked by something in front of it (an API Gateway
authorizer, a proxy, etc). The same verification runs whether a request
arrives through API Gateway or the local dev server, so behavior never
depends on infrastructure this repo can't see.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from urllib.error import URLError

import jwt
from aws_lambda_powertools.event_handler.exceptions import UnauthorizedError
from jwt.algorithms import RSAAlgorithm

_JWKS_TTL_SECONDS = 3600
_jwks_cache: dict[str, dict] = {}
_jwks_fetched_at: float = 0.0


def _issuer() -> str:
    issuer = os.environ.get("CLERK_ISSUER_URL")
    if not issuer:
        raise UnauthorizedError("CLERK_ISSUER_URL is not configured")
    return issuer.rstrip("/")


def _fetch_jwks(issuer: str) -> dict:
    try:
        with urllib.request.urlopen(f"{issuer}/.well-known/jwks.json", timeout=5) as resp:
            return json.load(resp)
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise UnauthorizedError("Could not fetch signing keys") from exc


def _get_signing_key(kid: str):
    global _jwks_fetched_at

    stale = time.time() - _jwks_fetched_at > _JWKS_TTL_SECONDS
    if stale or kid not in _jwks_cache:
        jwks = _fetch_jwks(_issuer())
        _jwks_cache.clear()
        _jwks_cache.update({key["kid"]: key for key in jwks.get("keys", [])})
        _jwks_fetched_at = time.time()

    jwk = _jwks_cache.get(kid)
    if jwk is None:
        raise UnauthorizedError("Unknown signing key")
    return RSAAlgorithm.from_jwk(json.dumps(jwk))


def verify_session_token(token: str) -> dict:
    """Verify a Clerk session JWT's signature, issuer, audience, and
    expiry, returning its claims. Raises UnauthorizedError on any failure."""
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Malformed token") from exc

    kid = header.get("kid")
    if not kid:
        raise UnauthorizedError("Malformed token")

    key = _get_signing_key(kid)
    audience = os.environ.get("CLERK_AUDIENCE")

    try:
        return jwt.decode(
            token,
            key=key,
            algorithms=["RS256"],
            issuer=_issuer(),
            audience=audience,
            leeway=5,
            options={"require": ["exp", "sub"], "verify_aud": audience is not None},
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid token") from exc
