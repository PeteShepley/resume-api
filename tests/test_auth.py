import time

from conftest import make_event, make_token
from cryptography.hazmat.primitives.asymmetric import rsa

from resume_api.app import handler


def test_missing_authorization_header_401():
    response = handler(make_event("GET", "/me/profile", authorization=None), {})
    assert response["statusCode"] == 401


def test_malformed_token_401():
    response = handler(make_event("GET", "/me/profile", authorization="Bearer not-a-jwt"), {})
    assert response["statusCode"] == 401


def test_expired_token_401():
    token = make_token(exp=int(time.time()) - 10)
    response = handler(make_event("GET", "/me/profile", authorization=f"Bearer {token}"), {})
    assert response["statusCode"] == 401


def test_wrong_audience_401():
    token = make_token(aud="https://wrong-audience.example")
    response = handler(make_event("GET", "/me/profile", authorization=f"Bearer {token}"), {})
    assert response["statusCode"] == 401


def test_wrong_issuer_401():
    token = make_token(iss="https://someone-else.example")
    response = handler(make_event("GET", "/me/profile", authorization=f"Bearer {token}"), {})
    assert response["statusCode"] == 401


def test_untrusted_signing_key_401():
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = make_token(key=other_key)
    response = handler(make_event("GET", "/me/profile", authorization=f"Bearer {token}"), {})
    assert response["statusCode"] == 401


def test_unknown_signing_key_id_401():
    token = make_token(kid="some-other-kid")
    response = handler(make_event("GET", "/me/profile", authorization=f"Bearer {token}"), {})
    assert response["statusCode"] == 401


def test_null_sub_claim_401():
    token = make_token(sub=None)
    response = handler(make_event("GET", "/me/profile", authorization=f"Bearer {token}"), {})
    assert response["statusCode"] == 401
