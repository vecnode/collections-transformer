#!/usr/bin/env python3
"""Local smoke test: upload text CSV datasets through the real API."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080/api/v1").rstrip("/")
TEST_USER_ID = os.getenv("TEST_USER_ID", "local-smoke-user")
TIMEOUT_SECONDS = float(os.getenv("API_TEST_TIMEOUT", "30"))

REPO_ROOT = Path(__file__).resolve().parents[2]
CSV_BY_MODE = {
    "single": REPO_ROOT / "assets" / "test_csv_1.csv",
    "chunked": REPO_ROOT / "assets" / "test_csv_2.csv",
}
EXPECTED_ROWS_BY_MODE = {
    "single": 10,
    "chunked": 9,
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def build_multipart_form_data(fields: dict[str, str], file_field: str, file_path: Path) -> tuple[bytes, str]:
    boundary = f"----ct-boundary-{int(time.time() * 1_000_000)}"
    lines: list[bytes] = []

    for key, value in fields.items():
        lines.extend(
            [
                f"--{boundary}".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"'.encode("utf-8"),
                b"",
                str(value).encode("utf-8"),
            ]
        )

    file_bytes = file_path.read_bytes()
    lines.extend(
        [
            f"--{boundary}".encode("utf-8"),
            f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"'.encode("utf-8"),
            b"Content-Type: text/csv",
            b"",
            file_bytes,
        ]
    )
    lines.append(f"--{boundary}--".encode("utf-8"))
    lines.append(b"")

    body = b"\r\n".join(lines)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def http_json(request: urllib.request.Request) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                fail(f"Non-JSON response: {exc}. Body={raw[:240]}")
            return response.status, parsed
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        fail(f"HTTP {exc.code} for {request.method} {request.full_url}: {error_body}")
    except Exception as exc:
        fail(f"Could not reach {request.method} {request.full_url}: {exc}")


def upload_dataset(mode: str) -> str:
    csv_path = CSV_BY_MODE[mode]
    require(csv_path.exists(), f"CSV file not found: {csv_path}")

    dataset_name = f"smoke-{mode}-{int(time.time())}"
    query = urllib.parse.urlencode({"owner_id": TEST_USER_ID, "dataset_type": "text"})
    url = f"{BASE_URL}/backend/dataset_new?{query}"

    body, content_type = build_multipart_form_data(
        fields={"dataset_name": dataset_name},
        file_field="text_file",
        file_path=csv_path,
    )

    print(f"-> POST {url}")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Accept": "application/json", "Content-Type": content_type},
    )
    status, payload = http_json(request)

    require(status == 201, f"Expected HTTP 201, got {status}. body={payload}")
    require(payload.get("ok") is True, f"Expected ok=true, got: {payload}")
    require(payload.get("status_code") == 201, f"Expected status_code=201, got: {payload}")

    data = payload.get("data") or {}
    dataset_id = data.get("dataset_id")
    require(dataset_id, f"Missing dataset_id in response: {payload}")
    print(f"   created dataset_id={dataset_id}, name={dataset_name}")
    return dataset_id


def verify_dataset(dataset_id: str, mode: str) -> None:
    query = urllib.parse.urlencode({"dataset_id": dataset_id})
    url = f"{BASE_URL}/backend/dataset?{query}"

    print(f"-> GET {url}")
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    status, payload = http_json(request)

    require(status == 200, f"Expected HTTP 200, got {status}. body={payload}")
    require(payload.get("ok") is True, f"Expected ok=true, got: {payload}")

    data = payload.get("data") or {}
    require(data.get("type") == "text", f"Expected dataset type='text', got: {data}")
    expected_rows = EXPECTED_ROWS_BY_MODE[mode]
    require(
        data.get("artwork_count") == expected_rows,
        f"Expected artwork_count={expected_rows}, got: {data.get('artwork_count')} (data={data})",
    )
    print(f"   verified artwork_count={expected_rows}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload text CSV smoke test")
    parser.add_argument(
        "--mode",
        choices=["single", "chunked"],
        default="single",
        help="Choose which CSV fixture to upload",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started = time.perf_counter()

    dataset_id = upload_dataset(args.mode)
    verify_dataset(dataset_id, args.mode)

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    print(f"PASS: uploaded and verified text dataset mode={args.mode} ({elapsed_ms} ms)")


if __name__ == "__main__":
    main()
