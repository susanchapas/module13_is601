from typing import Optional
from uuid import uuid4

import pytest
import requests
from playwright.sync_api import Page, expect

VALID_PASSWORD = "SecurePass123!"


@pytest.fixture
def base_url(fastapi_server: str) -> str:
    return fastapi_server.rstrip("/")


def new_user() -> dict:
    suffix = uuid4().hex[:10]
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": f"user_{suffix}@example.com",
        "username": f"user_{suffix}",
        "password": VALID_PASSWORD,
        "confirm_password": VALID_PASSWORD,
    }


def fill_registration_form(
    page: Page, user: dict, password: Optional[str] = None, confirm: Optional[str] = None
) -> None:
    page.fill("#username", user["username"])
    page.fill("#email", user["email"])
    page.fill("#first_name", user["first_name"])
    page.fill("#last_name", user["last_name"])
    page.fill("#password", password if password is not None else user["password"])
    page.fill("#confirm_password", confirm if confirm is not None else user["password"])


def register_via_api(base_url: str, user: dict) -> None:
    response = requests.post(f"{base_url}/auth/register", json=user)
    assert response.status_code == 201, f"Setup registration failed: {response.text}"


@pytest.mark.e2e
def test_register_valid_data_shows_success(page: Page, base_url: str):
    user = new_user()
    page.goto(f"{base_url}/register")

    fill_registration_form(page, user)
    with page.expect_response(lambda r: r.url.endswith("/auth/register")) as response_info:
        page.click("#registrationForm button[type=submit]")

    assert response_info.value.status == 201
    expect(page.locator("#successAlert")).to_be_visible()
    expect(page.locator("#successMessage")).to_contain_text("Registration successful")
    expect(page.locator("#errorAlert")).to_be_hidden()

    page.wait_for_url("**/login", timeout=5000)


@pytest.mark.e2e
def test_login_valid_credentials_stores_token(page: Page, base_url: str):
    user = new_user()
    register_via_api(base_url, user)

    page.goto(f"{base_url}/login")
    page.fill("#username", user["username"])
    page.fill("#password", user["password"])
    with page.expect_response(lambda r: r.url.endswith("/auth/login")) as response_info:
        page.click("#loginForm button[type=submit]")

    assert response_info.value.status == 200
    expect(page.locator("#successAlert")).to_be_visible()
    expect(page.locator("#successMessage")).to_contain_text("Login successful")

    access_token = page.evaluate("() => localStorage.getItem('access_token')")
    assert access_token, "Access token was not stored in localStorage"
    assert page.evaluate("() => localStorage.getItem('username')") == user["username"]

    page.wait_for_url("**/dashboard", timeout=5000)


@pytest.mark.e2e
def test_register_short_password_shows_error(page: Page, base_url: str):
    user = new_user()
    page.goto(f"{base_url}/register")

    fill_registration_form(page, user, password="Ab1!", confirm="Ab1!")
    page.click("#registrationForm button[type=submit]")

    expect(page.locator("#errorAlert")).to_be_visible()
    expect(page.locator("#errorMessage")).to_contain_text("at least 8 characters")
    expect(page.locator("#successAlert")).to_be_hidden()

    # The user must not exist: the client blocked the request before it reached the API.
    login = requests.post(
        f"{base_url}/auth/login",
        json={"username": user["username"], "password": VALID_PASSWORD},
    )
    assert login.status_code == 401


@pytest.mark.e2e
def test_register_mismatched_passwords_shows_error(page: Page, base_url: str):
    user = new_user()
    page.goto(f"{base_url}/register")

    fill_registration_form(page, user, confirm="DifferentPass123!")
    page.click("#registrationForm button[type=submit]")

    expect(page.locator("#errorAlert")).to_be_visible()
    expect(page.locator("#errorMessage")).to_contain_text("Passwords do not match")


@pytest.mark.e2e
def test_register_invalid_email_shows_error(page: Page, base_url: str):
    user = new_user()
    user["email"] = "user@example"  # passes native input[type=email], fails app validation
    page.goto(f"{base_url}/register")

    fill_registration_form(page, user)
    page.click("#registrationForm button[type=submit]")

    expect(page.locator("#errorAlert")).to_be_visible()
    expect(page.locator("#errorMessage")).to_contain_text("valid email address")


@pytest.mark.e2e
def test_register_duplicate_username_shows_server_error(page: Page, base_url: str):
    user = new_user()
    register_via_api(base_url, user)

    duplicate = new_user()
    duplicate["username"] = user["username"]
    page.goto(f"{base_url}/register")

    fill_registration_form(page, duplicate)
    with page.expect_response(lambda r: r.url.endswith("/auth/register")) as response_info:
        page.click("#registrationForm button[type=submit]")

    assert response_info.value.status == 400
    expect(page.locator("#errorAlert")).to_be_visible()
    expect(page.locator("#successAlert")).to_be_hidden()


@pytest.mark.e2e
def test_login_wrong_password_shows_error(page: Page, base_url: str):
    user = new_user()
    register_via_api(base_url, user)

    page.goto(f"{base_url}/login")
    page.fill("#username", user["username"])
    page.fill("#password", "WrongPass123!")
    with page.expect_response(lambda r: r.url.endswith("/auth/login")) as response_info:
        page.click("#loginForm button[type=submit]")

    assert response_info.value.status == 401
    expect(page.locator("#errorAlert")).to_be_visible()
    expect(page.locator("#errorMessage")).to_contain_text("Invalid username or password")
    expect(page.locator("#successAlert")).to_be_hidden()
    assert page.evaluate("() => localStorage.getItem('access_token')") is None


@pytest.mark.e2e
def test_login_unknown_username_shows_error(page: Page, base_url: str):
    page.goto(f"{base_url}/login")
    page.fill("#username", f"ghost_{uuid4().hex[:8]}")
    page.fill("#password", VALID_PASSWORD)
    with page.expect_response(lambda r: r.url.endswith("/auth/login")) as response_info:
        page.click("#loginForm button[type=submit]")

    assert response_info.value.status == 401
    expect(page.locator("#errorAlert")).to_be_visible()
    expect(page.locator("#errorMessage")).to_contain_text("Invalid username or password")


@pytest.mark.e2e
def test_login_empty_fields_blocked_client_side(page: Page, base_url: str):
    page.goto(f"{base_url}/login")
    page.click("#loginForm button[type=submit]")

    # Native `required` validation stops the submit; no request reaches the API.
    expect(page.locator("#errorAlert")).to_be_hidden()
    expect(page.locator("#successAlert")).to_be_hidden()
    assert page.evaluate("() => document.getElementById('loginForm').checkValidity()") is False
