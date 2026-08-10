import pytest
from uuid import uuid4
from fastapi import HTTPException, status

from app.auth.dependencies import get_current_user, get_current_active_user
from app.models.user import User
from app.schemas.token import TokenType


def test_get_current_user_returns_database_row(db_session, test_user):
    token = User.create_access_token({"sub": str(test_user.id)})

    current_user = get_current_user(token=token, db=db_session)

    assert current_user.id == test_user.id
    assert current_user.username == test_user.username
    assert current_user.is_active is True


def test_get_current_user_invalid_token(db_session):
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="invalid.token.string", db=db_session)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_current_user_refresh_token_rejected(db_session, test_user):
    token = User.create_refresh_token({"sub": str(test_user.id)})

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token, db=db_session)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_deleted_user(db_session):
    token = User.create_access_token({"sub": str(uuid4())})

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token, db=db_session)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_active_user_active(test_user):
    assert get_current_active_user(current_user=test_user) is test_user


def test_get_current_active_user_inactive(db_session, test_user):
    test_user.is_active = False
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        get_current_active_user(current_user=test_user)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Inactive user"


def test_verify_token_wrong_type(test_user):
    access = User.create_access_token({"sub": str(test_user.id)})

    assert User.verify_token(access, TokenType.ACCESS) == test_user.id
    assert User.verify_token(access, TokenType.REFRESH) is None
