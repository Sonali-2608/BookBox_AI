from datetime import timedelta

from app.utils.jwt import create_access_token, decode_access_token


def test_create_and_decode_token_roundtrip():
    token = create_access_token({"sub": "42"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"


def test_expired_token_returns_none():
    token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
    assert decode_access_token(token) is None


def test_tampered_token_returns_none():
    token = create_access_token({"sub": "1"})
    tampered = token[:-2] + ("aa" if token[-2:] != "aa" else "bb")
    assert decode_access_token(tampered) is None
