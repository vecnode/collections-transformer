#!/usr/bin/env python3
"""Local smoke test: direct TrOCR inference on a printed-text image."""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_DIR = REPO_ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def _add_local_venv_site_packages() -> None:
    py_major = sys.version_info.major
    py_minor = sys.version_info.minor
    site_packages = REPO_ROOT / "venv" / "lib" / f"python{py_major}.{py_minor}" / "site-packages"
    if site_packages.exists() and str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))


def _import_trocr_backend_class():
    try:
        from app.providers.provider_trocr import TrOcrTransformersBackend  # noqa: PLC0415

        return TrOcrTransformersBackend
    except ModuleNotFoundError as exc:
        if exc.name in {"dotenv", "transformers", "torch", "PIL"}:
            _add_local_venv_site_packages()
            try:
                from app.providers.provider_trocr import TrOcrTransformersBackend  # noqa: PLC0415

                return TrOcrTransformersBackend
            except ModuleNotFoundError as retry_exc:
                fail(
                    "Missing dependency: "
                    f"{retry_exc.name}. "
                    "Install project requirements or run with local venv, for example: "
                    "uv pip install -r requirements.txt"
                )
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run direct TrOCR inference on a printed-text image")
    parser.add_argument(
        "--image",
        required=True,
        help="Path to local image file for OCR inference.",
    )
    parser.add_argument(
        "--expected",
        default=None,
        help="Optional expected OCR phrase (case-insensitive, punctuation-insensitive).",
    )
    parser.add_argument(
        "--force-cpu",
        action="store_true",
        help="Force TrOCR to run on CPU",
    )
    return parser.parse_args()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", text.lower())).strip()


def main() -> None:
    args = parse_args()
    image_path = Path(args.image)
    if not image_path.exists():
        fail(f"Image file not found: {image_path}")

    print(f"-> image={image_path}")
    print(f"-> expected={repr(args.expected)}, force_cpu={args.force_cpu}")

    started = time.perf_counter()

    try:
        TrOcrTransformersBackend = _import_trocr_backend_class()
        backend = TrOcrTransformersBackend()
        backend.init(force_cpu=args.force_cpu)
        text = backend.recognize_text(image=image_path.read_bytes(), max_words=64)
    except Exception as exc:
        fail(f"TrOCR inference failed: {exc}")

    if not text or not text.strip():
        fail("TrOCR returned empty output")

    if not re.search(r"[A-Za-z0-9]", text):
        fail(f"TrOCR returned low-signal output: '{text}'")

    if args.expected:
        normalized_output = _normalize(text)
        expected_tokens = [tok for tok in _normalize(args.expected).split(" ") if tok]
        missing = [tok for tok in expected_tokens if tok not in normalized_output]
        if missing:
            fail(f"Missing expected tokens {missing}. OCR output='{text}'")

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    print("RESULT:")
    print(text.strip())
    print(f"PASS: TrOCR inference completed ({elapsed_ms} ms)")


if __name__ == "__main__":
    main()
