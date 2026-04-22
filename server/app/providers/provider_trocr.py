from __future__ import annotations

import base64
import io
import logging
import threading
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from app.core.config import app_settings as settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrOcrConfig:
    """Configuration for the local Transformers TrOCR backend."""

    model_name: str = settings.trocr_model_name
    timeout_seconds: float = 300.0
    repetition_penalty: float = 1.1


class TrOcrTransformersBackend:
    """High-level wrapper around a local TrOCR Transformers model for printed text OCR."""

    def __init__(self, config: TrOcrConfig | None = None) -> None:
        self.config = config or TrOcrConfig()
        self._processor: TrOCRProcessor | None = None
        self._model: VisionEncoderDecoderModel | None = None
        self._device: str | None = None
        self._dtype: Any | None = None
        self._init_lock = threading.Lock()

    @property
    def model_name(self) -> str:
        return self.config.model_name

    @property
    def processor(self) -> TrOCRProcessor | None:
        return self._processor

    @property
    def model(self) -> VisionEncoderDecoderModel | None:
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
            logger.info("Initializing TrOCR model '%s' on %s", self.config.model_name, device)

            processor = TrOCRProcessor.from_pretrained(self.config.model_name)
            model_dtype = torch.float32

            if device == "cuda":
                try:
                    model = VisionEncoderDecoderModel.from_pretrained(
                        self.config.model_name,
                        torch_dtype=torch.float16,
                    ).to(device)
                    model_dtype = torch.float16
                    logger.info("Loaded TrOCR with float16 on CUDA")
                except Exception:
                    logger.warning(
                        "Failed float16 TrOCR load on CUDA, retrying float32",
                        exc_info=True,
                    )
                    model = VisionEncoderDecoderModel.from_pretrained(self.config.model_name).to(device)
                    model_dtype = torch.float32
            else:
                model = VisionEncoderDecoderModel.from_pretrained(self.config.model_name).to(device)

            model.eval()
            if device == "cuda":
                torch.cuda.empty_cache()

            self._processor = processor
            self._model = model
            self._device = device
            self._dtype = model_dtype

            logger.info("TrOCR model initialized successfully")

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

    def _prepare_inputs(self, image: Image.Image) -> dict[str, Any]:
        import torch

        if self._processor is None or self._model is None or self._device is None:
            raise RuntimeError("TrOCR backend not initialized")

        inputs = self._processor(images=image, return_tensors="pt")
        converted: dict[str, Any] = {}
        for key, value in inputs.items():
            if isinstance(value, torch.Tensor):
                if value.dtype.is_floating_point:
                    converted[key] = value.to(device=self._device, dtype=self._dtype)
                else:
                    converted[key] = value.to(device=self._device)
            else:
                converted[key] = value
        return converted

    def recognize_text(self, image: str | bytes | Image.Image, max_words: int | None = None) -> str:
        import torch

        if self._model is None or self._device is None:
            raise RuntimeError("TrOCR backend not initialized")

        image_obj = self._decode_image(image)
        inputs = self._prepare_inputs(image_obj)

        max_new_tokens = max(16, int(max_words * 1.3)) if max_words else 128
        generate_kwargs: dict[str, Any] = {
            "max_new_tokens": max_new_tokens,
            "num_beams": 4 if self._device == "cpu" else 3,
            "do_sample": False,
            "repetition_penalty": self.config.repetition_penalty,
            "early_stopping": True,
        }

        with torch.no_grad():
            generated_ids = self._model.generate(**inputs, **generate_kwargs)

        if self._processor is None:
            raise RuntimeError("TrOCR processor not initialized")

        text = self._processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

        del generated_ids, inputs
        if self._device == "cuda":
            torch.cuda.empty_cache()

        return text

    def recognize_texts(self, images: list[str | bytes | Image.Image], max_words: int | None = None) -> list[str]:
        responses: list[str] = []
        for image_data in images:
            responses.append(self.recognize_text(image=image_data, max_words=max_words))
        return responses


_backend: TrOcrTransformersBackend | None = None
trocr_processor = None
trocr_model = None
trocr_model_name = None


def _get_backend() -> TrOcrTransformersBackend:
    global _backend
    if _backend is None:
        _backend = TrOcrTransformersBackend()
    return _backend


def _sync_legacy_globals() -> None:
    global trocr_processor, trocr_model, trocr_model_name
    backend = _get_backend()
    trocr_processor = backend.processor
    trocr_model = backend.model
    trocr_model_name = backend.model_name


def init_trocr(force_cpu: bool = False):
    """Initialize TrOCR model (legacy-compatible wrapper)."""
    try:
        backend = _get_backend()
        backend.init(force_cpu=force_cpu)
        _sync_legacy_globals()
    except Exception:
        logger.error("Error initializing TrOCR model", exc_info=True)
        raise


def get_trocr_ocr_response(images, max_words=None):
    """Handle OCR requests using the TrOCR Transformers backend."""
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
        logger.error("Error in TrOCR response: %s", exc)
        logger.debug(traceback.format_exc())
        return {
            "status": "400",
            "error": str(exc),
        }
