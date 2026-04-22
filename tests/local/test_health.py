#!/usr/bin/env python3
"""Local test: GET /api/v1/health."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080/api/v1").rstrip("/")
TIMEOUT_SECONDS = float(os.getenv("API_TEST_TIMEOUT", "10"))


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> None:
    start = time.perf_counter()
    url = f"{BASE_URL}/health"
    print(f"-> GET {url}")
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            status = response.status
            raw_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        fail(f"{url} returned HTTP {exc.code}: {error_body}")
    except Exception as exc:
        fail(f"Could not reach {url}: {exc}")

    require(status == 200, f"Expected status 200, got {status}")

    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        fail(f"Response is not valid JSON: {exc}")

    require(isinstance(body, dict), f"Expected JSON object, got: {type(body).__name__}")
    require(body.get("ok") is True, f"Expected ok=true, got: {body}")
    require(body.get("status_code") == 200, f"Expected status_code=200 in JSON body, got: {body}")

    data = body.get("data") or {}
    require(isinstance(data, dict), f"Expected data object, got: {data}")
    require(data.get("status") == "ok", f"Expected data.status='ok', got: {body}")

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    print(f"PASS: health endpoint is healthy ({elapsed_ms} ms)")


if __name__ == "__main__":
    main()
