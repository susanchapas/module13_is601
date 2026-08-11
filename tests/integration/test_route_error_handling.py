import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.main import create_calculation, register
from app.models.user import User
from app.schemas.calculation import CalculationBase
from app.schemas.user import UserCreate


def test_register_translates_integrity_error(monkeypatch, db_session, fake_user_data):
    """A duplicate slipping past the pre-check surfaces as a 400, not a 500."""
    def _raise_integrity_error(cls, db, user_data):
        raise IntegrityError("INSERT INTO users", {}, Exception("duplicate key"))

    monkeypatch.setattr(User, "register", classmethod(_raise_integrity_error))
    user_create = UserCreate(
        **fake_user_data, confirm_password=fake_user_data["password"]
    )

    with pytest.raises(HTTPException) as exc_info:
        register(user_create, db=db_session)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Username or email already exists"


def test_create_calculation_rejects_uncomputable_inputs(db_session, test_user):
    """A payload that bypasses schema validation still fails as a 400."""
    calculation_data = CalculationBase.model_construct(type="addition", inputs=[5.0])

    with pytest.raises(HTTPException) as exc_info:
        create_calculation(calculation_data, current_user=test_user, db=db_session)

    assert exc_info.value.status_code == 400
    assert "at least two numbers" in exc_info.value.detail
