#!/usr/bin/env python3
"""Local smoke test: direct TrOCR inference on a printed-text image."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
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
        default=None,
        help="Path to local image file. If omitted, the script generates a temporary printed-text image.",
    )
    parser.add_argument(
        "--text",
        default="HELLO OCR",
        help="Printed text used when generating a temporary test image.",
    )
    parser.add_argument(
        "--expected",
        default="hello ocr",
        help="Expected OCR phrase (case-insensitive, punctuation-insensitive).",
    )
    parser.add_argument(
        "--force-cpu",
        action="store_true",
        help="Force TrOCR to run on CPU",
    )
    return parser.parse_args()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", text.lower())).strip()


def _create_test_image(text: str, image_path: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415
    except ModuleNotFoundError as exc:
        if exc.name == "PIL":
            _add_local_venv_site_packages()
            from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415
        else:
            raise

    image = Image.new("RGB", (960, 280), color="white")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 72)
    except Exception:
        font = ImageFont.load_default()

    draw.text((40, 90), text, fill="black", font=font)
    image.save(image_path)


def main() -> None:
    args = parse_args()

    with tempfile.TemporaryDirectory(prefix="trocr-test-") as tmp_dir:
        tmp_image_path = Path(tmp_dir) / "ocr_printed.png"

        if args.image:
            image_path = Path(args.image)
            if not image_path.exists():
                fail(f"Image file not found: {image_path}")
        else:
            _create_test_image(args.text, tmp_image_path)
            image_path = tmp_image_path

        print(f"-> image={image_path}")
        print(f"-> expected='{args.expected}', force_cpu={args.force_cpu}")

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
