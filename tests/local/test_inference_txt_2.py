#!/usr/bin/env python3
"""Local smoke test: extract the main topic of a text file using Ollama (single sentence)."""

from __future__ import annotations

import argparse
import sys
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


def _import_ollama_provider():
    try:
        from app.providers import provider_ollama  # noqa: PLC0415

        return provider_ollama
    except ModuleNotFoundError as exc:
        if exc.name in {"dotenv", "requests"}:
            _add_local_venv_site_packages()
            try:
                from app.providers import provider_ollama  # noqa: PLC0415

                return provider_ollama
            except ModuleNotFoundError as retry_exc:
                fail(
                    f"Missing dependency: {retry_exc.name}. "
                    "Install project requirements: uv pip install -r requirements.txt"
                )
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract the main topic of a text file in one sentence using Ollama."
    )
    parser.add_argument(
        "--text",
        default=str(REPO_ROOT / "assets" / "test_txt_1.txt"),
        help="Path to a local text file (default: assets/test_txt_1.txt).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    text_path = Path(args.text)

    if not text_path.exists():
        fail(f"Text file not found: {text_path}")

    text_content = text_path.read_text(encoding="utf-8").strip()
    if not text_content:
        fail("Text file is empty.")

    print(f"Text file : {text_path}")
    print(f"Characters: {len(text_content)}")
    print()

    provider_ollama = _import_ollama_provider()
    provider_ollama.init_ollama()

    system_prompt = (
        "You are a topic-extraction assistant. "
        "Identify and state the main topic of the provided text in exactly one sentence. "
        "Do not add commentary, headings, or bullet points — return only that single sentence."
    )
    user_message = f"Text:\n\n{text_content}"

    print("Sending to Ollama...")
    result = provider_ollama.get_ollama_gpt_response(
        primer_message=system_prompt,
        user_message=user_message,
        max_words=40,
    )

    if result.get("status") != "200":
        fail(f"Ollama error: {result.get('error', 'unknown error')}")

    topic = result.get("res", "").strip()
    if not topic:
        fail("Ollama returned an empty response.")

    print("Topic (1 sentence):")
    print("-" * 40)
    print(topic)
    print("-" * 40)
    print()

    token_usage = result.get("token", {})
    print(
        f"Tokens — prompt: {token_usage.get('prompt_tokens', '?')}, "
        f"completion: {token_usage.get('completion_tokens', '?')}, "
        f"total: {token_usage.get('total_tokens', '?')}"
    )
    print("PASS")


if __name__ == "__main__":
    main()
