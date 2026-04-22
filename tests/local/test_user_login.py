#!/usr/bin/env python3
"""Local test: basic user login flow via record_connection."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080/api/v1").rstrip("/")
TEST_USER_ID = os.getenv("TEST_USER_ID", "local-smoke-user")
TIMEOUT_SECONDS = float(os.getenv("API_TEST_TIMEOUT", "10"))


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def http_json(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    url = f"{BASE_URL}{path}"
    headers = {"Accept": "application/json"}
    body = None

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=body, method=method, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                fail(f"{method} {url} returned non-JSON response: {exc}. Body={raw[:240]}")
            return response.status, parsed
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        fail(f"{method} {url} returned HTTP {exc.code}: {error_body}")
    except Exception as exc:
        fail(f"Could not reach {method} {url}: {exc}")


def main() -> None:
    start = time.perf_counter()
    print(f"-> POST {BASE_URL}/backend/user/record_connection")
    status, login_body = http_json(
        "POST",
        "/backend/user/record_connection",
        payload={"user_id": TEST_USER_ID, "event_type": "login"},
    )

    require(status == 200, f"Unexpected login HTTP status: {status}, body={login_body}")
    require(login_body.get("ok") is True, f"Expected ok=true for login, got: {login_body}")

    message = login_body.get("message", "")
    require("Connection recorded: login" in message, f"Unexpected login message: {login_body}")

    query = urllib.parse.urlencode({"user_id": TEST_USER_ID})
    print(f"-> GET {BASE_URL}/backend/user/last_connection?user_id={TEST_USER_ID}")
    status, last_connection_body = http_json("GET", f"/backend/user/last_connection?{query}")

    require(status == 200, f"Unexpected last_connection HTTP status: {status}, body={last_connection_body}")
    require(
        last_connection_body.get("ok") is True,
        f"Expected ok=true for last_connection, got: {last_connection_body}",
    )

    data = last_connection_body.get("data") or {}
    require(isinstance(data, dict), f"Expected data object, got: {data}")
    require(data.get("last_event_type") == "login", f"Expected last_event_type='login', got: {last_connection_body}")
    require(data.get("last_event_time") is not None, f"Expected last_event_time to be set, got: {last_connection_body}")

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    print(f"PASS: user login connection flow works ({elapsed_ms} ms)")


if __name__ == "__main__":
    main()
