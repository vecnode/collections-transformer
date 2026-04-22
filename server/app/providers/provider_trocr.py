from __future__ import annotations

import base64
import io
import logging
import os
import tempfile
import threading
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor

from app.core.config import app_settings as settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GlmOcrConfig:
    """Configuration for the local Transformers GLM-OCR backend."""

    model_name: str = settings.trocr_model_name
    timeout_seconds: float = 300.0
    default_prompt: str = "Text Recognition:"


class GlmOcrTransformersBackend:
    """High-level wrapper around GLM-OCR for printed text extraction."""

    def __init__(self, config: GlmOcrConfig | None = None) -> None:
        self.config = config or GlmOcrConfig()
        self._resolved_model_name = self.config.model_name
        self._processor = None
        self._model = None
        self._device: str | None = None
        self._init_lock = threading.Lock()

    @property
    def model_name(self) -> str:
        return self._resolved_model_name

    @property
    def processor(self):
        return self._processor

    @property
    def model(self):
        return self._model

    def init(self, force_cpu: bool = False) -> None:
        """Load processor and model once, preferring CUDA if available unless forced to CPU."""
        if self._processor is not None and self._model is not None:
            return

        with self._init_lock:
            if self._processor is not None and self._model is not None:
                return

            import torch

            device = "cpu" if force_cpu else ("cuda" if torch.cuda.is_available() else "cpu")
            model_name = self.config.model_name
            self._resolved_model_name = model_name

            logger.info("Initializing GLM-OCR model '%s' on %s", model_name, device)

            processor = AutoProcessor.from_pretrained(
                model_name,
                trust_remote_code=True,
            )
            if force_cpu:
                model = AutoModelForImageTextToText.from_pretrained(
                    pretrained_model_name_or_path=model_name,
                    torch_dtype=torch.float32,
                    trust_remote_code=True,
                ).to("cpu")
            else:
                model = AutoModelForImageTextToText.from_pretrained(
                    pretrained_model_name_or_path=model_name,
                    torch_dtype="auto",
                    device_map="auto",
                    trust_remote_code=True,
                )

            model.eval()

            self._processor = processor
            self._model = model
            self._device = device

            logger.info("GLM-OCR model initialized successfully")

    @staticmethod
    def _decode_image(image_data: str | bytes | Image.Image) -> Image.Image:
        if isinstance(image_data, Image.Image):
            return image_data.convert("RGB")
        if isinstance(image_data, str):
            payload = image_data.split(",", 1)[1] if image_data.startswith("data:image") else image_data
            image_bytes = base64.b64decode(payload)
        else:
            image_bytes = image_data
        return Image.open(io.BytesIO(image_bytes)).convert("RGB")

    def _prepare_inputs(
        self,
        image: Image.Image,
        prompt: str,
        max_words: int | None = None,
    ) -> tuple[dict[str, Any], int, int]:

        if self._model is None or self._device is None:
            raise RuntimeError("GLM-OCR backend not initialized")
        if self._processor is None:
            raise RuntimeError("GLM-OCR processor not initialized")

        with tempfile.NamedTemporaryFile(prefix="glm-ocr-", suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        image.save(tmp_path, format="PNG")

        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "url": tmp_path},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]

            inputs = self._processor.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt",
            )
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        if hasattr(self._model, "device"):
            model_device = self._model.device
        else:
            model_device = next(self._model.parameters()).device

        inputs = inputs.to(model_device)
        inputs.pop("token_type_ids", None)

        max_new_tokens = max(64, int(max_words * 1.3)) if max_words else 1024
        prompt_length = int(inputs["input_ids"].shape[1]) if "input_ids" in inputs else 0
        return inputs, max_new_tokens if max_new_tokens > 0 else 1024, prompt_length

    def recognize_text(self, image: str | bytes | Image.Image, max_words: int | None = None, prompt: str | None = None) -> str:
        import torch

        if self._model is None or self._device is None:
            raise RuntimeError("GLM-OCR backend not initialized")

        image_obj = self._decode_image(image)
        effective_prompt = prompt or self.config.default_prompt
        inputs, max_new_tokens, prompt_length = self._prepare_inputs(image_obj, effective_prompt, max_words=max_words)

        with torch.no_grad():
            generated_ids = self._model.generate(**inputs, max_new_tokens=max_new_tokens)

        if self._processor is None:
            raise RuntimeError("GLM-OCR processor not initialized")

        output_text = self._processor.decode(
            generated_ids[0][prompt_length:],
            skip_special_tokens=True,
        ).strip()

        del generated_ids, inputs
        if self._device == "cuda":
            torch.cuda.empty_cache()

        return output_text

    def recognize_texts(self, images: list[str | bytes | Image.Image], max_words: int | None = None) -> list[str]:
        responses: list[str] = []
        for image_data in images:
            responses.append(self.recognize_text(image=image_data, max_words=max_words))
        return responses


_backend: GlmOcrTransformersBackend | None = None
trocr_processor = None
trocr_model = None
trocr_model_name = None


def _get_backend() -> GlmOcrTransformersBackend:
    global _backend
    if _backend is None:
        _backend = GlmOcrTransformersBackend()
    return _backend


def _sync_legacy_globals() -> None:
    global trocr_processor, trocr_model, trocr_model_name
    backend = _get_backend()
    trocr_processor = backend.processor
    trocr_model = backend.model
    trocr_model_name = backend.model_name


def init_trocr(force_cpu: bool = False):
    """Initialize OCR model (legacy-compatible wrapper name)."""
    try:
        backend = _get_backend()
        backend.init(force_cpu=force_cpu)
        _sync_legacy_globals()
    except Exception:
        logger.error("Error initializing TrOCR model", exc_info=True)
        raise


def get_trocr_ocr_response(images, max_words=None):
    """Handle OCR requests using the GLM-OCR backend (legacy-compatible wrapper name)."""
    try:
        backend = _get_backend()
        backend.init()
        _sync_legacy_globals()

        responses = backend.recognize_texts(images=images, max_words=max_words)
        response_text = responses[0] if len(responses) == 1 else "\n\n".join(
            [f"Image {idx + 1}: {text}" for idx, text in enumerate(responses)]
        )

        llm_end_time_ms = round(datetime.now().timestamp() * 1000)
        estimated_tokens = len(response_text.split()) * 1.3
        token_usage = {
            "prompt_tokens": int(estimated_tokens * 0.3),
            "completion_tokens": int(estimated_tokens * 0.7),
            "total_tokens": int(estimated_tokens),
        }

        return {
            "status": "200",
            "res": response_text,
            "end": llm_end_time_ms,
            "token": token_usage,
        }
    except Exception as exc:
        logger.error("Error in OCR response: %s", exc)
        logger.debug(traceback.format_exc())
        return {
            "status": "400",
            "error": str(exc),
        }


# Backward-compatible alias used by tests and older imports.
TrOcrTransformersBackend = GlmOcrTransformersBackend
