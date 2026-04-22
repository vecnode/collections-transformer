#!/usr/bin/env python3
"""Local smoke test: direct BLIP-2 inference on a local image file."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_DIR = REPO_ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))


DEFAULT_IMAGE_PATH = REPO_ROOT / "assets" / "test_img_1.jpg"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def _add_local_venv_site_packages() -> None:
    py_major = sys.version_info.major
    py_minor = sys.version_info.minor
    site_packages = REPO_ROOT / "venv" / "lib" / f"python{py_major}.{py_minor}" / "site-packages"
    if site_packages.exists() and str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))


def _import_blip_backend_class():
    try:
        from app.providers.provider_blip2 import Blip2TransformersBackend  # noqa: PLC0415

        return Blip2TransformersBackend
    except ModuleNotFoundError as exc:
        # When `uv run` uses an isolated env without requirements, borrow local venv deps.
        if exc.name in {"dotenv", "transformers", "torch", "PIL"}:
            _add_local_venv_site_packages()
            try:
                from app.providers.provider_blip2 import Blip2TransformersBackend  # noqa: PLC0415

                return Blip2TransformersBackend
            except ModuleNotFoundError as retry_exc:
                fail(
                    "Missing dependency: "
                    f"{retry_exc.name}. "
                    "Install project requirements or run with local venv, for example: "
                    "uv pip install -r requirements.txt"
                )
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run direct BLIP-2 inference on a local image")
    parser.add_argument(
        "--image",
        default=os.getenv("TEST_IMAGE_PATH", str(DEFAULT_IMAGE_PATH)),
        help="Path to local image file",
    )
    parser.add_argument(
        "--mode",
        choices=["caption", "long-description"],
        default="caption",
        help="Inference style preset",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=None,
        help="Override max words for generation",
    )
    parser.add_argument(
        "--force-cpu",
        action="store_true",
        help="Force BLIP-2 to run on CPU",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image_path = Path(args.image)

    if not image_path.exists():
        fail(f"Image file not found: {image_path}")

    if args.mode == "caption":
        prompt = None
        preset_max_words = 20
    else:
        prompt = "Question: Describe this image in detail, including subject, setting, and visible context. Answer:"
        preset_max_words = 220

    max_words = args.max_words if args.max_words is not None else preset_max_words

    print(f"-> image={image_path}")
    print(f"-> mode={args.mode}, max_words={max_words}, force_cpu={args.force_cpu}")

    started = time.perf_counter()

    try:
        Blip2TransformersBackend = _import_blip_backend_class()
        backend = Blip2TransformersBackend()
        backend.init(force_cpu=args.force_cpu)
        text = backend.describe_image(
            image=image_path.read_bytes(),
            prompt=prompt,
            max_words=max_words,
        )
    except Exception as exc:
        fail(f"BLIP-2 inference failed: {exc}")

    if not text or not text.strip():
        fail("BLIP-2 returned empty output")

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    print("RESULT:")
    print(text.strip())
    print(f"PASS: BLIP-2 {args.mode} inference completed ({elapsed_ms} ms)")


if __name__ == "__main__":
    main()
