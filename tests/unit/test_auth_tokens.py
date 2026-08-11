from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from jose import jwt as jose_jwt

from app.auth import jwt as jwt_module
from app.core.config import get_settings
from app.models.calculation import Calculation
from app.models.user import User
from app.schemas.token import TokenType

settings = get_settings()


def test_create_token_honours_explicit_expiry():
    token = jwt_module.create_token(
        str(uuid4()), TokenType.ACCESS, expires_delta=timedelta(minutes=5)
    )
    payload = jose_jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    assert payload["type"] == TokenType.ACCESS.value


def test_create_token_stringifies_uuid_subject():
    user_id = uuid4()
    token = jwt_module.create_token(user_id, TokenType.REFRESH)
    payload = jose_jwt.decode(
        token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    assert payload["sub"] == str(user_id)


def test_create_token_wraps_encoding_failure(monkeypatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("no encoder available")

    monkeypatch.setattr(jwt_module.jwt, "encode", _raise)

    with pytest.raises(HTTPException) as exc_info:
        jwt_module.create_token(str(uuid4()), TokenType.ACCESS)

    assert exc_info.value.status_code == 500
    assert "Could not create token" in exc_info.value.detail


def test_verify_token_rejects_mismatched_token_type():
    token = jose_jwt.encode(
        {"sub": str(uuid4()), "type": TokenType.REFRESH.value},
        settings.JWT_SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    assert User.verify_token(token, TokenType.ACCESS) is None


def test_verify_token_rejects_non_uuid_subject():
    token = jose_jwt.encode(
        {"sub": "not-a-uuid", "type": TokenType.ACCESS.value},
        settings.JWT_SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    assert User.verify_token(token, TokenType.ACCESS) is None


def test_user_accepts_hashed_password_keyword():
    user = User(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        username="ada",
        hashed_password="already-hashed",
    )
    assert user.password == "already-hashed"
    assert user.hashed_password == "already-hashed"


def test_user_update_sets_attributes_and_timestamp():
    user = User(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        username="ada",
        password="hashed",
    )
    assert user.updated_at is None

    updated = user.update(first_name="Grace")

    assert updated is user
    assert user.first_name == "Grace"
    assert user.updated_at is not None


def test_base_calculation_has_no_operation():
    calculation = Calculation(user_id=uuid4(), type="calculation", inputs=[1.0, 2.0])
    with pytest.raises(NotImplementedError):
        calculation.get_result()


def test_calculation_repr_shows_type_and_inputs():
    calculation = Calculation(user_id=uuid4(), type="calculation", inputs=[1.0, 2.0])
    assert repr(calculation) == "<Calculation(type=calculation, inputs=[1.0, 2.0])>"
