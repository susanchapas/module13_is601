import pytest
from pydantic import ValidationError

from app.schemas.calculation import CalculationBase, CalculationUpdate
from app.schemas.user import UserCreate

BASE_USER = {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com",
    "username": "ada",
}


def test_password_mismatch_is_rejected():
    with pytest.raises(ValidationError, match="Passwords do not match"):
        UserCreate(**BASE_USER, password="SecurePass123!", confirm_password="OtherPass123!")


@pytest.mark.parametrize(
    "password,message",
    [
        ("nouppercase1!", "uppercase letter"),
        ("NOLOWERCASE1!", "lowercase letter"),
        ("NoDigitsHere!", "one digit"),
        ("NoSpecials1234", "special character"),
    ],
)
def test_password_strength_rules_are_enforced(password, message):
    with pytest.raises(ValidationError, match=message):
        UserCreate(**BASE_USER, password=password, confirm_password=password)


def test_password_length_guard_backs_up_the_field_constraint():
    """min_length=8 rejects first, so exercise the validator's own guard directly."""
    short = UserCreate.model_construct(password="Shor1!", confirm_password="Shor1!")
    with pytest.raises(ValueError, match="at least 8 characters long"):
        short.validate_password_strength()


def test_division_by_zero_is_rejected():
    with pytest.raises(ValidationError, match="Cannot divide by zero"):
        CalculationBase(type="division", inputs=[10, 0])


def test_calculation_base_length_guard_backs_up_the_field_constraint():
    too_few = CalculationBase.model_construct(type="addition", inputs=[5.0])
    with pytest.raises(ValueError, match="At least two numbers are required"):
        too_few.validate_inputs()


def test_calculation_update_length_guard_backs_up_the_field_constraint():
    too_few = CalculationUpdate.model_construct(inputs=[5.0])
    with pytest.raises(ValueError, match="At least two numbers are required"):
        too_few.validate_inputs()
