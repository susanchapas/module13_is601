from uuid import uuid4

import pytest
import requests


@pytest.fixture
def base_url(fastapi_server: str) -> str:
    """Returns the FastAPI server base URL without a trailing slash."""
    return fastapi_server.rstrip("/")


@pytest.fixture
def auth_headers(base_url: str, fake_user_data: dict) -> dict:
    """Register a fresh user, log in, and return an Authorization header."""
    payload = {**fake_user_data, "confirm_password": fake_user_data["password"]}
    register = requests.post(f"{base_url}/auth/register", json=payload)
    assert register.status_code == 201, f"Registration failed: {register.text}"

    login = requests.post(
        f"{base_url}/auth/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert login.status_code == 200, f"Login failed: {login.text}"
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_index_page_is_served(base_url: str):
    response = requests.get(f"{base_url}/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_form_login_wrong_password_returns_401(base_url: str, fake_user_data: dict):
    payload = {**fake_user_data, "confirm_password": fake_user_data["password"]}
    assert requests.post(f"{base_url}/auth/register", json=payload).status_code == 201

    response = requests.post(
        f"{base_url}/auth/token",
        data={"username": payload["username"], "password": "WrongPass123!"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


@pytest.mark.parametrize(
    "method,body",
    [
        ("get", None),
        ("put", {"inputs": [4, 2]}),
        ("delete", None),
    ],
)
def test_malformed_calculation_id_returns_400(base_url: str, auth_headers: dict, method, body):
    response = getattr(requests, method)(
        f"{base_url}/calculations/not-a-uuid", headers=auth_headers, json=body
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid calculation id format."


@pytest.mark.parametrize(
    "method,body",
    [
        ("put", {"inputs": [4, 2]}),
        ("delete", None),
    ],
)
def test_unknown_calculation_id_returns_404(base_url: str, auth_headers: dict, method, body):
    response = getattr(requests, method)(
        f"{base_url}/calculations/{uuid4()}", headers=auth_headers, json=body
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Calculation not found."
