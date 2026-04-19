import os
import logging
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parent.parent.parent  # server/
PROJECT_ROOT = SERVER_DIR.parent


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _split_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class AppSettings:
    environment: str
    log_level: str
    api_host: str
    api_port: int
    secret_key: str
    cors_origins: list[str]

    mongodb_uri: str
    mongodb_database: str
    upload_folder: str

    redis_url: str

    ollama_model_option: str
    ollama_base_url: str
    blip2_model_name: str

    cuda_launch_blocking: str
    pytorch_use_cuda_dsa: str


def load_app_settings() -> AppSettings:
    # Prefer a shared root-level .env, fallback to server/.env for compatibility.
    root_env_file = PROJECT_ROOT / ".env"
    server_env_file = SERVER_DIR / ".env"
    if root_env_file.exists():
        load_dotenv(root_env_file)
    elif server_env_file.exists():
        load_dotenv(server_env_file)
    else:
        load_dotenv()

    return AppSettings(
        environment=os.getenv("ENVIRONMENT", "dev"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8080")),
        secret_key=os.getenv("SECRET_KEY", "local-dev-secret-key-change-in-production"),
        cors_origins=_split_csv(
            os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"),
            ["http://localhost:3000", "http://127.0.0.1:3000"],
        ),
        mongodb_uri=os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017"),
        mongodb_database=os.getenv("MONGODB_DATABASE", "tanc_database"),
        upload_folder=os.getenv("UPLOAD_FOLDER", "/cache"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        ollama_model_option=os.getenv("OLLAMA_MODEL_OPTION", "gemma3:27b"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        blip2_model_name=os.getenv("BLIP2_MODEL_NAME", "Salesforce/blip2-opt-2.7b"),
        cuda_launch_blocking=os.getenv("CUDA_LAUNCH_BLOCKING", "1"),
        pytorch_use_cuda_dsa=os.getenv("PYTORCH_USE_CUDA_DSA", "1"),
    )


app_settings = load_app_settings()


def configure_app_logging() -> None:
    level = getattr(logging, app_settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
