"""Thin HTTP client for the Social Media API FastAPI backend.

Every backend call lives here so the rest of the Streamlit app never
constructs a URL, attaches an auth header, or parses an error response
by hand. Authentication and authorization are enforced entirely by the
backend (JWT bearer tokens checked on every protected route) - this
client only carries the token, it doesn't make any security decisions.
"""
import base64
import json
import os

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 15


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _headers(token: str | None) -> dict:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _handle(response: requests.Response):
    if not response.ok:
        try:
            detail = response.json().get("detail", f"Request failed ({response.status_code})")
        except ValueError:
            detail = f"Request failed ({response.status_code})"
        raise ApiError(response.status_code, str(detail))
    if response.status_code == 204:
        return None
    return response.json()


def ping() -> dict:
    response = requests.get(BACKEND_URL, timeout=REQUEST_TIMEOUT)
    return _handle(response)


def register(email: str, password: str) -> dict:
    response = requests.post(
        f"{BACKEND_URL}/users/", json={"email": email, "password": password}, timeout=REQUEST_TIMEOUT
    )
    return _handle(response)


def login(email: str, password: str) -> dict:
    # The backend's /login route expects OAuth2PasswordRequestForm - a
    # form-encoded body, not JSON, with "username" holding the email.
    response = requests.post(
        f"{BACKEND_URL}/login",
        data={"username": email, "password": password},
        timeout=REQUEST_TIMEOUT,
    )
    return _handle(response)


def get_posts(token: str, search: str = "", limit: int = 50, skip: int = 0) -> list[dict]:
    response = requests.get(
        f"{BACKEND_URL}/posts/",
        headers=_headers(token),
        params={"search": search, "limit": limit, "skip": skip},
        timeout=REQUEST_TIMEOUT,
    )
    return _handle(response)


def create_post(token: str, title: str, content: str, published: bool = True) -> dict:
    response = requests.post(
        f"{BACKEND_URL}/posts/",
        headers=_headers(token),
        json={"title": title, "content": content, "published": published},
        timeout=REQUEST_TIMEOUT,
    )
    return _handle(response)


def update_post(token: str, post_id: int, title: str, content: str, published: bool = True) -> dict:
    response = requests.put(
        f"{BACKEND_URL}/posts/{post_id}",
        headers=_headers(token),
        json={"title": title, "content": content, "published": published},
        timeout=REQUEST_TIMEOUT,
    )
    return _handle(response)


def delete_post(token: str, post_id: int) -> None:
    response = requests.delete(
        f"{BACKEND_URL}/posts/{post_id}", headers=_headers(token), timeout=REQUEST_TIMEOUT
    )
    return _handle(response)


def vote(token: str, post_id: int, direction: int) -> dict:
    response = requests.post(
        f"{BACKEND_URL}/vote/",
        headers=_headers(token),
        json={"post_id": post_id, "dir": direction},
        timeout=REQUEST_TIMEOUT,
    )
    return _handle(response)


def decode_user_id(token: str) -> int | None:
    """Read the user_id claim out of the JWT payload without verifying
    the signature - the backend independently verifies every real
    request, so this is only ever used to decide what the UI shows
    (e.g. which posts are "mine"), never as a security check.
    """
    try:
        payload_b64 = token.split(".")[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        return payload.get("user_id")
    except Exception:
        return None
